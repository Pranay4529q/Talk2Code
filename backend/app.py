import os

from fastapi import FastAPI

from models.schemas import (
    RepoRequest,
    ChatRequest
)

from services.github_service import (
    GithubService
)

from services.file_service import (
    FileService
)

from services.vector_store_service import (
    VectorStoreService
)

from services.rag_service import (
    RAGService
)

from config import (
    REPOSITORY_DIR,
    CHROMA_DB_DIR
)

app = FastAPI(
    title="Talk2Code AI"
)


os.makedirs(
    REPOSITORY_DIR,
    exist_ok=True
)

os.makedirs(
    CHROMA_DB_DIR,
    exist_ok=True
)


@app.get("/")
def root():

    return {
        "message": "TalkToCode AI Running"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.post("/ingest")
def ingest_repository(
    request: RepoRequest
):

    repo_id, repo_path = (
        GithubService.clone_repo(
            request.github_url
        )
    )

    documents = (
        FileService.load_documents(
            repo_path
        )
    )

    VectorStoreService.create_vector_store(
        repo_id,
        documents
    )

    return {
        "status": "success",
        "repo_id": repo_id,
        "documents_indexed": len(documents)
    }


@app.post("/chat")
def chat(
    request: ChatRequest
):

    answer = (
        RAGService.ask_question(
            request.repo_id,
            request.question
        )
    )

    return {
        "answer": answer
    }