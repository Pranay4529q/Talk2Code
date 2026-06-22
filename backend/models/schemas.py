from pydantic import BaseModel


class RepoRequest(BaseModel):
    github_url: str


class ChatRequest(BaseModel):
    repo_id: str
    question: str