from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated

Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class RepoRequest(BaseModel):
    github_url: str = Field(min_length=1, max_length=250)


class ChatRequest(BaseModel):
    repo_id: UUID
    question: Question
