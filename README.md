# ai-rag-template

RAG-сервис на FastAPI + LlamaIndex. Часть портфолио AI Engineer
(трек из Obsidian Vault → `AI Engineering Manual`).

## Запуск локально
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# положи .md/.pdf в data/
uvicorn app:app --port 8000
curl -X POST localhost:8000/ask -H 'Content-Type: application/json' \
  -d '{"question":"как создать VPC?"}'
```

## Eval gate
```bash
python eval.py   # faithfulness >= 0.8 иначе exit 1 (CI не пустит деплой)
```

## Docker
```bash
docker build -t rag-app . && docker run -p 8000:8000 rag-app
```

## CI
GitHub Actions (`.github/workflows/ci.yml`) гоняет pytest + eval.py на каждый push.
