"""
AI Legal Memory — Streamlit demo app (Supermemory-only).

Run with:  streamlit run main.py
"""

import tempfile
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

st.set_page_config(
    page_title="Legal Memory",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from app.ingest import ingest_pdf, ingest_whatsapp
    import app.supermemory as supermemory
    from app.summarize import summarize_results_batch
except ImportError as e:
    st.error(f"Missing dependency: {e}. Run `pip install -r requirements.txt`")
    st.stop()

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("last_results", []),
    ("ingest_log", []),
    ("last_query", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚖️ Legal Memory")
    st.caption("AI-powered retrieval from your firm's documents")

    if supermemory.is_available():
        st.success("Supermemory connected ✅")
    else:
        st.error("Supermemory not configured — add SUPERMEMORY_API_KEY to .env")

    st.divider()

    # Stats
    @st.cache_data(ttl=30, show_spinner=False)
    def load_stats():
        return supermemory.collection_stats()

    stats = load_stats()
    col1, col2 = st.columns(2)
    col1.metric("Chunks indexed", stats["total_chunks"])
    col2.metric("Documents", len(stats["pdf_sources"]) + len(stats["whatsapp_sources"]))

    if stats["pdf_sources"]:
        with st.expander(f"📄 PDFs ({len(stats['pdf_sources'])})"):
            for name in stats["pdf_sources"]:
                st.markdown(f"- {name}")

    if stats["whatsapp_sources"]:
        with st.expander(f"💬 WhatsApp chats ({len(stats['whatsapp_sources'])})"):
            for name in stats["whatsapp_sources"]:
                st.markdown(f"- {name}")

    st.divider()

    # Upload PDFs
    st.subheader("Upload Documents")
    pdf_files = st.file_uploader(
        "PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="Contracts, petitions, agreements, case notes, judgments",
    )

    if pdf_files:
        if st.button("Ingest PDFs", type="primary", use_container_width=True):
            for uploaded in pdf_files:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(uploaded.read())
                    tmp_path = tmp.name
                try:
                    bar = st.progress(0.0, text=f"Processing {uploaded.name}…")
                    def _cb(msg, pct, _bar=bar):
                        _bar.progress(pct, text=msg)
                    result = ingest_pdf(tmp_path, progress_cb=_cb)
                    bar.empty()
                    entry = f"✅ {uploaded.name} — {result['chunks']} chunks"
                    st.session_state.ingest_log.append(entry)
                    st.success(entry)
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Failed: {uploaded.name} — {e}")
                finally:
                    Path(tmp_path).unlink(missing_ok=True)

    st.divider()

    # Upload WhatsApp
    st.subheader("WhatsApp Exports")
    st.caption("Export chat → 'Without media' → share the .txt file")
    wa_files = st.file_uploader(
        "WhatsApp .txt exports",
        type=["txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if wa_files:
        if st.button("Ingest Chats", type="primary", use_container_width=True):
            for uploaded in wa_files:
                with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb") as tmp:
                    tmp.write(uploaded.read())
                    tmp_path = tmp.name
                try:
                    bar = st.progress(0.0, text=f"Processing {uploaded.name}…")
                    def _cb(msg, pct, _bar=bar):
                        _bar.progress(pct, text=msg)
                    result = ingest_whatsapp(tmp_path, progress_cb=_cb)
                    bar.empty()
                    entry = (
                        f"✅ {uploaded.name} — "
                        f"{result['messages']} messages, {result['chunks']} chunks"
                    )
                    st.session_state.ingest_log.append(entry)
                    st.success(entry)
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Failed: {uploaded.name} — {e}")
                finally:
                    Path(tmp_path).unlink(missing_ok=True)

    if st.session_state.ingest_log:
        with st.expander("Ingest log"):
            for entry in reversed(st.session_state.ingest_log):
                st.markdown(entry)

# ── Main area ─────────────────────────────────────────────────────────────────
st.header("Search your firm's memory")

example_queries = [
    "arbitration clauses in vendor agreements",
    "employment contract non-compete period",
    "payment terms for delayed invoices",
    "IP ownership clause startup agreement",
    "termination without cause notice period",
]

query = st.text_input(
    "Ask anything about your past matters",
    placeholder="e.g. 'Find arbitration clauses similar to this one'",
    label_visibility="collapsed",
)

col_search, col_clear = st.columns([1, 5])
search_btn = col_search.button("Search", type="primary")
if col_clear.button("Clear"):
    st.session_state.last_results = []
    st.rerun()

with st.expander("Example queries", expanded=stats["total_chunks"] == 0):
    for eq in example_queries:
        if st.button(eq, key=f"ex_{eq}"):
            query = eq
            search_btn = True

if search_btn and query.strip():
    if not supermemory.is_available():
        st.error("Supermemory is not configured. Add SUPERMEMORY_API_KEY to .env")
    elif stats["total_chunks"] == 0:
        st.warning("No documents indexed yet. Upload PDFs or WhatsApp exports in the sidebar.")
    else:
        with st.spinner("Searching…"):
            try:
                results = supermemory.search(query.strip(), top_k=5)
                summaries = summarize_results_batch(query.strip(), results)
                for r, s in zip(results, summaries):
                    r["summary"] = s
                st.session_state.last_results = results
                st.session_state.last_query = query.strip()
            except Exception as e:
                st.error(f"Search failed: {e}")

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.last_results:
    st.divider()
    st.subheader(f"Top {len(st.session_state.last_results)} results · Supermemory")

    for r in st.session_state.last_results:
        source_icon = "💬" if r["source_type"] == "whatsapp" else "📄"
        score_pct = int(r["score"] * 100)

        with st.container():
            header_col, score_col = st.columns([5, 1])
            with header_col:
                meta_parts = [f"{source_icon} **{r['source_name']}**"]
                if r["source_type"] == "whatsapp" and r.get("start_time"):
                    meta_parts.append(r["start_time"][:10])
                if r["source_type"] == "pdf" and r.get("pages"):
                    meta_parts.append(f"p. {r['pages']}")
                if r.get("senders"):
                    meta_parts.append(f"👤 {r['senders']}")
                st.markdown(" · ".join(meta_parts))
            with score_col:
                color = "green" if score_pct >= 70 else "orange" if score_pct >= 50 else "red"
                st.markdown(f":{color}[{score_pct}% match]")

            summary = r.get("summary", "")
            if summary:
                st.markdown(f"**{summary}**")
                excerpt = r["text"][:300].replace("\n", " ").strip()
                if len(r["text"]) > 300:
                    excerpt += "…"
                st.caption(excerpt)
            else:
                excerpt = r["text"][:400].replace("\n", " ").strip()
                if len(r["text"]) > 400:
                    excerpt += "…"
                st.markdown(f"> {excerpt}")

            with st.expander("Full text"):
                st.text(r["text"])

            st.divider()

elif not search_btn:
    if stats["total_chunks"] == 0:
        st.info(
            "👋 **Welcome.** Upload your firm's documents in the sidebar to get started.\n\n"
            "Supported: PDF contracts, petitions, agreements, case notes · WhatsApp chat exports"
        )
    else:
        st.info(
            f"**{stats['total_chunks']} chunks indexed** across "
            f"{len(stats['pdf_sources'])} PDFs and {len(stats['whatsapp_sources'])} WhatsApp chats.\n\n"
            "Type a question above to search."
        )
