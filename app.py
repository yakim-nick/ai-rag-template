"""FastAPI service exposing the RAG query engine over HTTP."""

from __future__ import annotations

from fastapi import FastAPI
from llama_index.core.base.base_query_engine import BaseQueryEngine
from pydantic import BaseModel

from rag import build_engine
from services import generate_answer

app = FastAPI()


def get_engine() -> BaseQueryEngine:
    """Return the lazily-built RAG query engine, cached on the app instance.

    Building the index is expensive (chunking + embedding), so we build it
    once and reuse it for every request.
    """
    if not hasattr(app, "_engine"):
        app._engine = build_engine("data/")
    return app._engine


class AskRequest(BaseModel):
    """Request body for the ``/ask`` endpoint."""

    question: str


@app.post("/ask")
def ask_question(request: AskRequest) -> dict[str, str]:
    """Answer a question using the RAG engine."""
    return {"answer": generate_answer(get_engine(), request.question)}


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe: returns OK when the service is up."""
    return {"status": "ok"}
