import logging
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from models.schemas import ChatRequest, RepoRequest
from services.file_service import FileService
from services.github_service import GithubService
from services.rag_service import RAGService
from services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)
app = FastAPI(title="Talk2Code")
WEB = Path(__file__).resolve().parent / "web"
app.mount("/assets", StaticFiles(directory=WEB), name="assets")


@app.get("/", include_in_schema=False)
def root():
    return FileResponse(WEB / "index.html")


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/ingest")
def ingest_repository(request: RepoRequest):
    try:
        url = GithubService.normalize_url(request.github_url)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    repo_id = str(uuid4())
    try:
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / "repo"
            commit = GithubService.clone_repo(url, path)
            chunks, file_count, limited = FileService.load_documents(path)
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(504, "GitHub download timed out.") from exc
    except subprocess.CalledProcessError as exc:
        raise HTTPException(422, "Couldn't clone that repository. Check the URL and public access.") from exc
    except OSError as exc:
        logger.exception("Git or local repository storage unavailable")
        raise HTTPException(503, "Repository ingestion is unavailable.") from exc
    if not chunks:
        raise HTTPException(422, "No readable Python source files were found within the indexing limits.")
    try:
        VectorStoreService.save(repo_id, {"url": url, "commit": commit, "chunks": chunks})
    except Exception as exc:
        logger.exception("Index creation failed")
        raise HTTPException(503, "The embedding model or index storage is unavailable.") from exc
    return {
        "status": "success", "repo_id": repo_id, "commit": commit,
        "documents_indexed": file_count, "chunks_indexed": len(chunks),
        "limited": limited,
    }


@app.post("/chat")
def chat(request: ChatRequest):
    try:
        index = VectorStoreService.load(str(request.repo_id))
    except FileNotFoundError as exc:
        raise HTTPException(404, "Repository index not found. Index the repository first.") from exc
    try:
        return RAGService.ask_question(index, request.question)
    except RuntimeError as exc:
        logger.warning("Answer generation unavailable: %s", type(exc).__name__)
        raise HTTPException(503, "Answer generation is unavailable. Check the backend configuration.") from exc
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
        logger.warning("Answer generation failed: %s", type(exc).__name__)
        raise HTTPException(502, "Couldn't generate an answer. Try again shortly.") from exc
