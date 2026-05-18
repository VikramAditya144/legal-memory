"""
FastAPI backend for Legal Memory (Supermemory-only).

Run with: uvicorn api:app --host 0.0.0.0 --port $PORT
"""

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Legal Memory API", version="2.0.0")

# CORS — allow all origins (required for Vercel → Render cross-origin requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Lazy-load heavy modules so startup never crashes ─────────────────────────

def _supermemory():
    import app.supermemory as sm
    return sm


def _ingest_pdf():
    from app.ingest import ingest_pdf
    return ingest_pdf


def _ingest_whatsapp():
    from app.ingest import ingest_whatsapp
    return ingest_whatsapp


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    try:
        available = _supermemory().is_available()
    except Exception:
        available = False
    return {"status": "ok", "supermemory": available}


@app.get("/stats")
def get_stats():
    try:
        return _supermemory().collection_stats()
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={"total_chunks": 0, "pdf_sources": [], "whatsapp_sources": [],
                     "supermemory_available": False, "error": str(e)},
        )


@app.post("/ingest/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted")

    sm = _supermemory()
    if not sm.is_available():
        raise HTTPException(503, "SUPERMEMORY_API_KEY is not configured")

    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = _ingest_pdf()(tmp_path, source_name=file.filename)
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return {"success": True, "filename": file.filename,
            "chunks": result["chunks"], "pages": result.get("pages", 0)}


@app.post("/ingest/whatsapp")
async def upload_whatsapp(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".txt"):
        raise HTTPException(400, "Only .txt WhatsApp exports are accepted")

    sm = _supermemory()
    if not sm.is_available():
        raise HTTPException(503, "SUPERMEMORY_API_KEY is not configured")

    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = _ingest_whatsapp()(tmp_path, source_name=file.filename)
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return {"success": True, "filename": file.filename,
            "chunks": result["chunks"], "messages": result.get("messages", 0)}


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@app.post("/search")
def search_documents(req: SearchRequest):
    if not req.query.strip():
        raise HTTPException(400, "Query cannot be empty")

    sm = _supermemory()
    if not sm.is_available():
        raise HTTPException(503, "SUPERMEMORY_API_KEY is not configured")

    try:
        results = sm.search(req.query.strip(), top_k=req.top_k)
    except Exception as e:
        raise HTTPException(500, str(e))

    return {"results": results, "source": "supermemory", "query": req.query}
