"""Health-check tests for the FastAPI app."""

from unittest.mock import MagicMock

import rag

# Mock the RAG engine BEFORE importing ``app``: the app builds its engine
# lazily, so the mock must be installed before ``app`` is imported.
rag.build_engine = MagicMock(return_value=MagicMock())

from fastapi.testclient import TestClient  # noqa: E402  # import order matters, see above
from app import app  # noqa: E402

client = TestClient(app)


def test_health() -> None:
    """The /health endpoint reports the service as up."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
