# ai-rag-template

A Retrieval-Augmented Generation (RAG) service built with FastAPI and
LlamaIndex. Part of an AI Engineering learning track.

## What it does
Ingests documents (`.md` / `.pdf`), indexes them into a vector store, and answers
questions strictly from that data — reducing model hallucination by grounding
responses in retrieved context.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# drop .md/.pdf files into data/
uvicorn app:app --port 8000
curl -X POST localhost:8000/ask -H 'Content-Type: application/json' \
  -d '{"question":"how do I create a VPC?"}'
```

## Evaluation gate
```bash
python eval.py   # exits non-zero if faithfulness < 0.8 (CI blocks bad deploys)
```

## Docker
```bash
docker build -t rag-app . && docker run -p 8000:8000 rag-app
```

## CI
GitHub Actions (`.github/workflows/ci.yml`) runs syntax checks + `pytest` on
every push, with least-privilege permissions and pinned action versions.

## Author
Nick Yakim — github.com/yakim-nick
