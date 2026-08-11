# Contributing to ai-rag-template

Thanks for contributing! This is a RAG service with an automated faithfulness
evaluation gate, so retrieval and evaluation changes must keep answer quality
above the CI threshold.

## Getting started

```sh
make install     # install dev + runtime dependencies
make dev         # run the service locally (see Makefile targets)
```

## Before you open a PR

- Run the tests: `make test` (or `pytest`, including `conftest.py` fixtures).
- Run `make lint` and `make format` (ruff), and keep `pre-commit` passing.
- If you change retrieval, chunking, or the evaluation prompts, run the
  faithfulness evaluation and confirm the accuracy metric stays above the
  CI gate (0.8). Share the numbers in the PR.
- Never commit real API keys or dataset secrets — use environment variables
  or a secret manager.

## Commits

Use conventional-commits style, e.g. `feat(retrieval): ...`,
`fix(eval): ...`, `docs(security): ...`.

## Reaching out

Open an issue to discuss bugs, feature ideas, or large changes before
submitting a PR.
