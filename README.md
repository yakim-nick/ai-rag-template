# ai-rag-template

> **Engineering report** — a Retrieval-Augmented Generation (RAG) service that answers
> questions strictly from your own documents, with a built-in evaluation gate.
> Part of the AI Engineering learning track by Nick Yakim.

## 1. Problem & goal
LLMs hallucinate when they lack context. This service grounds every answer in
retrieved documents, so responses stay factual. The goal: a small, production-shaped
RAG that proves the full pattern — ingest → index → retrieve → generate → evaluate.

## 2. Architecture

```mermaid
flowchart LR
  subgraph IDX[Indexing  once]
    D[Docs .md/.pdf] --> CH[Chunk ~800 tok]
    CH --> EM[Embed API]
    EM --> VS[(Vector Store)]
  end
  subgraph Q[Query  live]
    U[User] --> QE[Embed query]
    QE --> RT[Retrieve top-k]
    VS --> RT
    RT --> CT[Context in prompt]
    CT --> LLM[LLM]
    LLM --> ANS[Answer]
  end
  ANS --> EV[Eval: faithfulness]
  EV -->|<0.8| AL[Alert / retune]
```

```
        ┌────────────┐     ┌──────────────┐     ┌──────────────┐
 user ──▶│  FastAPI  │────▶│ Vector Store │◀────│  Ingestion   │
         │  /ask     │     │  (Chroma)    │     │  chunk+embed │
         └────┬──────┘     └──────┬───────┘     └──────────────┘
              │                   │ top-k contexts
              │                   ▼
              │            ┌──────────────┐
              └───────────▶│     LLM      │──▶ answer + eval gate
                           └──────────────┘
```

## 3. Components
- `app.py` — FastAPI service, `/ask` (POST) and `/health`.
- `rag.py` — builds the LlamaIndex query engine from `data/`.
- `eval.py` — RAGAS-style faithfulness gate; **CI fails if faithfulness < 0.8**.
- `ui/app.py` — Streamlit UI for interactive Q&A (see §7).
- `data/` — drop your `.md`/`.pdf` here to index.
- `tests/` — smoke test for the app.

## 4. Run (API)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --port 8000
curl -X POST localhost:8000/ask -H 'Content-Type: application/json' \
  -d '{"question":"how do I create a VPC?"}'
```

## 5. Evaluation & CI
`python eval.py` computes faithfulness; the GitHub Actions pipeline
(`.github/workflows/ci.yml`, least-privilege + pinned actions) blocks merges
that drop below threshold. This is what separates a demo from an engineering
artifact.

## 6. Docker (API)
```bash
docker build -t rag-app . && docker run -p 8000:8000 rag-app
```

## 7. Streamlit UI

A browsable chat interface that wraps the same RAG engine.  Upload documents,
ask questions, and see responses in real time.

### 7.1 Run locally
```bash
streamlit run ui/app.py
```

Open http://localhost:8501 in your browser.

### 7.2 Docker
```bash
docker build -t rag-ui -f ui/Dockerfile . && docker run -p 8501:8501 rag-ui
```

### 7.3 Usage

| Area     | What you can do                                          |
|----------|----------------------------------------------------------|
| Sidebar  | Upload `.md` / `.pdf` / `.txt` / `.csv` files            |
| Sidebar  | Browse currently indexed documents                       |
| Sidebar  | See engine readiness status                              |
| Main     | Type a question and press Enter                          |
| Main     | Scroll through full conversation history                 |
| Main     | Errors and warnings are displayed inline                 |

### 7.4 Environment

The UI reuses the same `rag.build_engine()` call as the API, so it respects
the same environment — set `OPENAI_API_KEY` (or whichever LLM provider your
`llama-index` configuration uses) before launching.

## Author
Nick Yakim — [github.com/yakim-nick](https://github.com/yakim-nick)
