"""Service layer for the RAG API.

Routes in ``app`` stay thin and delegate business logic here, keeping the
HTTP layer free of retrieval/generation details.
"""

from __future__ import annotations

from llama_index.core.base.base_query_engine import BaseQueryEngine


def generate_answer(engine: BaseQueryEngine, question: str) -> str:
    """Generate a grounded answer for ``question`` using the RAG ``engine``.

    The engine retrieves the most relevant document chunks and feeds them to
    the LLM as context, so the answer is grounded in the indexed documents.
    """
    return engine.query(question).response
