# ai-rag-template

[![CI](https://github.com/yakim-nick/ai-rag-template/actions/workflows/ci.yml/badge.svg)](https://github.com/yakim-nick/ai-rag-template/actions/workflows/ci.yml)

A small Retrieval-Augmented Generation (RAG) API: put `.md`, `.pdf`, `.txt` or
`.csv` files in `data/`, ask questions over HTTP (FastAPI) or in a Streamlit UI,
and get answers that LlamaIndex builds from the retrieved document chunks.

It is a learning project, not a production service. See
[Known limitations](#known-limitations).

## How it works

```mermaid
flowchart LR
  subgraph IDX["Indexing (on first request)"]
    D["data/ files"] --> CH["Split: 1024-token chunks, 200 overlap"]
    CH --> EM["Embed (OpenAI by default)"]
    EM --> VS[("In-memory vector index")]
  end
  subgraph Q["Query (POST /ask)"]
    U["Question"] --> QE["Embed question"]
    QE --> RT["Retrieve top 2 chunks"]
    VS --> RT
    RT --> LLM["LLM answers from the chunks"]
    LLM --> ANS["Answer"]
  end
```

- The index is built lazily on the first `/ask` and kept in memory. It is **not
  persisted**, so it is rebuilt (and re-embedded, which costs API calls) after
  every restart.
- Embeddings and the LLM are LlamaIndex's defaults, which use OpenAI. You need
  `OPENAI_API_KEY`.

## Components

- `app.py`: FastAPI service. `POST /ask`, `GET /health`. The engine is injected as a
  dependency, so tests run with a fake engine.
- `rag.py`: builds the LlamaIndex query engine from a directory.
- `services.py`: `generate_answer(engine, question)`.
- `eval.py`: manual RAGAS faithfulness check on real engine answers (see [Evaluation](#evaluation)).
- `ui/app.py`: Streamlit chat UI with document upload.
- `data/`: documents to index. `data/terraform-vpc.md` is a small sample.
- `tests/`: 34 tests, no network or API key needed.

## Run (API)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then put your real key in .env
export OPENAI_API_KEY=sk-...    # the API reads the environment, not .env
uvicorn app:app --port 8000
curl -X POST localhost:8000/ask -H 'Content-Type: application/json' \
  -d '{"question":"How do I create a VPC with Terraform?"}'
```

Responses: `200 {"answer": ...}`, `422` for a blank or over-long (> 1000 chars)
question, `503` if the engine cannot be built (missing key, unreadable `data/`),
`502` if the model call fails. Error bodies do not include upstream details.

## Streamlit UI

```bash
streamlit run ui/app.py         # http://localhost:8501
```

Upload `.md/.pdf/.txt/.csv` files (max 10 MB, file names are sanitised so they
stay inside `data/`), browse indexed documents and chat. The UI builds its own
engine in-process; it does not call the API.

## Docker

```bash
docker compose up --build       # api on :8000, ui on :8501, reads .env
# Images run as a non-root user and report health (docker ps shows 'healthy').
```

## Evaluation

`python eval.py` asks the real engine a few English questions about `data/`
(`GOLDEN_QUESTIONS`), then scores each answer with RAGAS **faithfulness** (how
much of the answer is supported by the chunks retrieved for it) using
`gpt-4o-mini` as the judge. It prints the average and exits non-zero below 0.8.

- It is a **manual** script: it needs `OPENAI_API_KEY`, costs a little money,
  and is **not run in CI**.
- The questions only cover the sample document. Add questions for your own files.
- The unit tests cover collecting answers and contexts, the dataset shape RAGAS
  accepts, and the pass/fail gate. The RAGAS scoring call itself needs a real key
  and has not been run against OpenAI by the author yet; with a fake key it
  reaches the OpenAI call and fails there with an authentication error.

## Tests and CI

```bash
pip install -r requirements-dev.txt && ruff check . && python -m pytest -q
```

CI (`.github/workflows/ci.yml`) runs `ruff` and `pytest` only, with a read-only
token and actions pinned to commit SHAs. Dependabot is enabled.

## Known limitations

- No authentication or rate limiting on `/ask`: anyone who can reach it spends
  your OpenAI credits. Do not expose it publicly as is.
- The index is in memory only and is built on the first request (slow first call).
- Answers are not checked for faithfulness at runtime or in CI (see Evaluation).
- Direct dependencies are pinned but transitive ones are not (no lock file).
- Docker images run as uid 1000 with a healthcheck, but `./data` is bind-mounted:
  if your host user has another uid, fix the folder permissions for UI uploads.

## Roadmap

- Run the eval on a schedule or on demand in CI with a repository secret.
- Persist the index (for example with Chroma) so restarts do not re-embed.
- API key auth and rate limiting on `/ask`; a lock file for transitive dependencies.

## Author

Nick Yakim: [github.com/yakim-nick](https://github.com/yakim-nick)
