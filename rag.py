from llama_index.core import VectorStoreIndex, SimpleDirectoryReader


def build_engine(path: str):
    docs = SimpleDirectoryReader(path).load_data()
    return VectorStoreIndex.from_documents(docs).as_query_engine()
