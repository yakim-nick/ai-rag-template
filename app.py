from fastapi import FastAPI
from pydantic import BaseModel
from rag import build_engine

app = FastAPI()
engine = build_engine("data/")


class Q(BaseModel):
    question: str


@app.post("/ask")
def ask(q: Q):
    return {"answer": engine.query(q.question).response}


@app.get("/health")
def health():
    return {"status": "ok"}
