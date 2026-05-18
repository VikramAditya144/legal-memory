"""
FastAPI backend for Legal Memory (Supermemory-only).

Run with: uvicorn api:app --reload --port 8000
"""

import tempfile
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.ingest import ingest_pdf, ingest_whatsapp
import app.supermemory as supermemory

app = FastAPI(title="Legal Memory API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "supermemory": supermemory.is_available()}


@app.get("/stats")
def get_stats():
    return supermemory.collection_stats()


@app.post("/ingest/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted")
    if not supermemory.is_available():
        raise HTTPException(503, "SUPERMEMORY_API_KEY is not configured")

    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = ingest_pdf(tmp_path)
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return {
        "success": True,
        "filename": file.filename,
        "chunks": result["chunks"],
        "pages": result.get("pages", 0),
    }


@app.post("/ingest/whatsapp")
async def upload_whatsapp(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".txt"):
        raise HTTPException(400, "Only .txt WhatsApp exports are accepted")
    if not supermemory.is_available():
        raise HTTPException(503, "SUPERMEMORY_API_KEY is not configured")

    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = ingest_whatsapp(tmp_path)
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return {
        "success": True,
        "filename": file.filename,
        "chunks": result["chunks"],
        "messages": result.get("messages", 0),
    }


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@app.post("/search")
def search_documents(req: SearchRequest):
    if not req.query.strip():
        raise HTTPException(400, "Query cannot be empty")
    if not supermemory.is_available():
        raise HTTPException(503, "SUPERMEMORY_API_KEY is not configured")

    results = supermemory.search(req.query.strip(), top_k=req.top_k)
    return {"results": results, "source": "supermemory", "query": req.query}
