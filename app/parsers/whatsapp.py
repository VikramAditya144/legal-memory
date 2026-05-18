"""
WhatsApp .txt export parser.

Handles both iOS and Android export formats:
  iOS:     [DD/MM/YY, HH:MM:SS] Name: message
  Android: DD/MM/YYYY, HH:MM - Name: message
  Android: M/D/YY, H:MM AM/PM - Name: message  (US locale)

Multi-line messages (continuation lines have no timestamp prefix) are
merged into the preceding message. System messages are dropped.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Patterns ordered from most-specific to least-specific
_IOS_RE = re.compile(
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AP]M)?)\]\s+([^:]+):\s+(.*)"
)
_ANDROID_RE = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2}(?:\s?[AP]M)?)\s+-\s+([^:]+):\s+(.*)"
)

_SYSTEM_PATTERNS = [
    "Messages and calls are end-to-end encrypted",
    "joined using this group's invite link",
    "added you",
    "changed the subject",
    "changed this group",
    "left",
    "was added",
    "changed their phone number",
    "<Media omitted>",
    "This message was deleted",
    "You deleted this message",
    "missed voice call",
    "missed video call",
]


@dataclass
class WhatsAppMessage:
    timestamp: datetime | None
    sender: str
    text: str
    raw_date: str


def _is_system_message(text: str) -> bool:
    low = text.lower()
    return any(p.lower() in low for p in _SYSTEM_PATTERNS)


def _parse_timestamp(date_str: str, time_str: str) -> datetime | None:
    time_str = time_str.strip()
    date_str = date_str.strip()
    for fmt in (
        "%d/%m/%Y %I:%M %p", "%d/%m/%Y %I:%M:%S %p",
        "%d/%m/%Y %H:%M",    "%d/%m/%Y %H:%M:%S",
        "%d/%m/%y %I:%M %p", "%d/%m/%y %I:%M:%S %p",
        "%d/%m/%y %H:%M",    "%d/%m/%y %H:%M:%S",
        "%m/%d/%Y %I:%M %p", "%m/%d/%y %I:%M %p",
        "%m/%d/%y %H:%M",
    ):
        try:
            return datetime.strptime(f"{date_str} {time_str}", fmt)
        except ValueError:
            continue
    return None


def _try_match(line: str) -> tuple[str, str, str, str] | None:
    """Return (date, time, sender, text) or None."""
    for pattern in (_IOS_RE, _ANDROID_RE):
        m = pattern.match(line)
        if m:
            return m.group(1), m.group(2), m.group(3).strip(), m.group(4).strip()
    return None


def parse_whatsapp_export(path: str | Path) -> list[WhatsAppMessage]:
    """Parse a WhatsApp .txt export file into a list of WhatsAppMessage objects."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")

    messages: list[WhatsAppMessage] = []
    current: WhatsAppMessage | None = None

    for line in text.splitlines():
        match = _try_match(line)
        if match:
            # Save previous message
            if current is not None and not _is_system_message(current.text):
                messages.append(current)

            date_s, time_s, sender, body = match
            ts = _parse_timestamp(date_s, time_s)
            current = WhatsAppMessage(
                timestamp=ts,
                sender=sender,
                text=body,
                raw_date=f"{date_s} {time_s}",
            )
        elif current is not None and line.strip():
            # Skip continuation lines that are standalone system messages
            if not _is_system_message(line.strip()):
                current.text = f"{current.text}\n{line.strip()}"

    # Don't forget the last message
    if current is not None and not _is_system_message(current.text):
        messages.append(current)

    return messages


def chunk_messages(
    messages: list[WhatsAppMessage],
    window: int = 5,
    overlap: int = 1,
) -> list[dict]:
    """
    Group messages into overlapping windows for indexing.

    Each chunk contains `window` consecutive messages. Adjacent chunks
    overlap by `overlap` messages so context at boundaries is preserved.
    Returns a list of dicts with keys: text, metadata.
    """
    chunks = []
    step = max(1, window - overlap)

    for i in range(0, len(messages), step):
        batch = messages[i : i + window]
        lines = []
        for msg in batch:
            ts = msg.timestamp.strftime("%Y-%m-%d %H:%M") if msg.timestamp else msg.raw_date
            lines.append(f"[{ts}] {msg.sender}: {msg.text}")

        chunk_text = "\n".join(lines)
        first = batch[0]
        last = batch[-1]

        chunks.append({
            "text": chunk_text,
            "metadata": {
                "source_type": "whatsapp",
                "source_name": "",  # filled by ingest.py
                "start_time": first.timestamp.isoformat() if first.timestamp else first.raw_date,
                "end_time": last.timestamp.isoformat() if last.timestamp else last.raw_date,
                "senders": list({m.sender for m in batch}),
                "message_count": len(batch),
            },
        })

    return chunks
