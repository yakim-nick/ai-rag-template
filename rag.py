from __future__ import annotations

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter


def build_engine(
    path: str,
    chunk_size: int = 1024,
    chunk_overlap: int = 200,
    embed_model: str | None = None,
    similarity_top_k: int = 2,
):
    transformations = [
        SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    ]

    if embed_model is not None:
        from llama_index.embeddings.openai import OpenAIEmbedding

        embed_instance = OpenAIEmbedding(model=embed_model)
    else:
        embed_instance = None

    docs = SimpleDirectoryReader(path).load_data()
    index = VectorStoreIndex.from_documents(
        docs,
        transformations=transformations,
        embed_model=embed_instance,
    )
    return index.as_query_engine(similarity_top_k=similarity_top_k)
