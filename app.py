from fastapi import FastAPI
from pydantic import BaseModel
from rag import build_engine

app = FastAPI()


def get_engine():
    if not hasattr(app, "_engine"):
        app._engine = build_engine("data/")
    return app._engine


class Q(BaseModel):
    question: str


@app.post("/ask")
def ask(q: Q):
    return {"answer": get_engine().query(q.question).response}


@app.get("/health")
def health():
    return {"status": "ok"}
