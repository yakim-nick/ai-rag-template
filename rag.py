"""Build a RAG query engine over a directory of documents."""

from __future__ import annotations

from typing import Any

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document


def _build_embed_model(model_name: str | None) -> Any | None:
    """Instantiate the embedding model, or ``None`` to use the default.

    The OpenAI embedding class is imported lazily so the default path does not
    require ``llama-index-embeddings-openai`` to be installed.
    """
    if model_name is None:
        return None
    from llama_index.embeddings.openai import OpenAIEmbedding

    return OpenAIEmbedding(model=model_name)


def _load_documents(documents_dir: str) -> list[Document]:
    """Load every supported document (md/pdf/txt/csv) from ``documents_dir``."""
    return SimpleDirectoryReader(documents_dir).load_data()


def build_engine(
    documents_dir: str,
    chunk_size: int = 1024,
    chunk_overlap: int = 200,
    embed_model: str | None = None,
    similarity_top_k: int = 2,
) -> BaseQueryEngine:
    """Build a query engine that retrieves from and answers over ``documents_dir``.

    Documents are split into chunks of ``chunk_size`` tokens with
    ``chunk_overlap`` overlap, embedded (optionally with ``embed_model``),
    indexed, and wrapped in a query engine that returns the top
    ``similarity_top_k`` chunks per query.
    """
    # Chunking keeps each retrieved context small enough to fit the LLM prompt
    # while the overlap preserves context across chunk boundaries.
    transformations = [
        SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    ]

    docs = _load_documents(documents_dir)
    index = VectorStoreIndex.from_documents(
        docs,
        transformations=transformations,
        embed_model=_build_embed_model(embed_model),
    )
    return index.as_query_engine(similarity_top_k=similarity_top_k)
