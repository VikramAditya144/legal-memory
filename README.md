# AI Legal Memory — Approach A Prototype

Semantic search over your firm's WhatsApp chats and PDF documents.
Upload once, search forever. This is the laptop-demo prototype — no cloud,
no auth, no accounts. Runs entirely on your machine.

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker Desktop (running)
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### 2. Clone & install

```bash
git clone <this-repo>
cd cambridge

pip install -r requirements.txt
```

### 3. Set your API key

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 4. Start Qdrant (vector database)

```bash
docker compose up -d
```

Qdrant runs at `http://localhost:6333`. Data persists in a Docker volume.

### 5. Run the app

```bash
streamlit run main.py
```

Opens at `http://localhost:8501`.

---

## How to Export WhatsApp Chats

### Android
1. Open the WhatsApp chat
2. Tap ⋮ (menu) → **More** → **Export chat**
3. Choose **Without media**
4. Share the `.txt` file to yourself (email, Drive, etc.)

### iOS
1. Open the WhatsApp chat
2. Tap the contact/group name at the top
3. Scroll down → **Export Chat**
4. Choose **Without Media**
5. Share the `.txt` file to yourself

---

## Demo Script (for the first firm visit)

1. Ask the lawyer: **"Can I have your last 6 months of WhatsApp for one active
   matter, plus 10-15 related PDFs?"**
2. Upload them in the sidebar
3. Wait for indexing (~2-3 minutes depending on document size)
4. Ask the senior partner: **"What's a question you've had to re-research
   recently?"**
5. Type their exact question into the search box
6. Show them the answer from their own documents

If they say **"how much?"** — you have a customer.

---

## Architecture

```
Streamlit UI (main.py)
    │
    ├── Ingest (app/ingest.py)
    │       ├── WhatsApp parser (app/parsers/whatsapp.py)
    │       └── PDF parser (app/parsers/pdf.py)
    │
    ├── Embeddings (app/embeddings.py)
    │       └── OpenAI text-embedding-3-small
    │
    └── Storage (app/store.py)
            └── Qdrant (Docker, localhost:6333)
```

**Chunking strategy:**
- WhatsApp: 5-message sliding windows, 1-message overlap
- PDF: ~500-token word-count windows, 50-token overlap

---

## What's Not Built (Approach B — after first customers)

- User authentication and multi-tenancy
- Cloud deployment (AWS Mumbai ap-south-1)
- AI-generated summaries of retrieved chunks
- Entity extraction (client names, judges, courts)
- Matter tagging and case organisation UI
- Email ingestion

---

## Data & Privacy

All data stays on your machine (or your Docker host). Nothing is sent anywhere
except to OpenAI for embedding generation. OpenAI does not train on API inputs
by default.

For firm deployments: switch to a self-hosted embedding model
(`intfloat/multilingual-e5-large` via HuggingFace) to keep everything fully
local, including Hindi/regional language content.

---

## Cost Estimate

`text-embedding-3-small` costs $0.02 per 1M tokens.

| Documents | Approx tokens | Approx cost |
|-----------|--------------|-------------|
| 50 PDFs (~20 pages each) | ~2M | $0.04 |
| 6 months WhatsApp (1 matter) | ~500K | $0.01 |
| Full firm onboarding (200 docs) | ~8M | $0.16 |

Search queries cost ~$0.0001 each. Effectively free.
