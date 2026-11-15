"""FastAPI service exposing the RAG query engine over HTTP."""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException
from llama_index.core.base.base_query_engine import BaseQueryEngine
from pydantic import BaseModel, Field, field_validator

from rag import build_engine
from services import generate_answer

logger = logging.getLogger(__name__)

DATA_DIR = "data/"
MAX_QUESTION_CHARS = 1000

app = FastAPI(title="ai-rag-template")


@lru_cache(maxsize=1)
def _build_cached_engine() -> BaseQueryEngine:
    """Build the query engine once and reuse it.

    Building the index is expensive (chunking + embedding). ``lru_cache`` does
    not cache exceptions, so a failed build (for example a missing API key) is
    retried on the next request.
    """
    return build_engine(DATA_DIR)


def get_engine() -> BaseQueryEngine:
    """FastAPI dependency returning the engine, or a clear 503 when it cannot be built."""
    try:
        return _build_cached_engine()
    except Exception as exc:
        logger.exception("Could not build the RAG engine")
        raise HTTPException(
            status_code=503,
            detail="RAG engine unavailable: check OPENAI_API_KEY and the data/ folder",
        ) from exc


def engine_provider() -> Callable[[], BaseQueryEngine]:
    """Dependency returning the *function* that gets the engine.

    The engine is fetched inside the handler, after the request body has been
    validated. If it were a direct dependency, FastAPI would build the (costly)
    index before reporting a 422 for a bad question.
    """
    return get_engine


class AskRequest(BaseModel):
    """Request body for the ``/ask`` endpoint."""

    question: str = Field(max_length=MAX_QUESTION_CHARS)

    @field_validator("question")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be blank")
        return value


@app.post("/ask")
def ask_question(
    request: AskRequest,
    provider: Callable[[], BaseQueryEngine] = Depends(engine_provider),  # noqa: B008
) -> dict[str, str]:
    """Answer a question using the RAG engine."""
    engine = provider()
    try:
        return {"answer": generate_answer(engine, request.question)}
    except Exception as exc:
        logger.exception("Answer generation failed")
        raise HTTPException(status_code=502, detail="The language model call failed") from exc


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe: returns OK when the service is up."""
    return {"status": "ok"}
