"""Health-check test for the FastAPI app."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app import app


def test_health() -> None:
    """The /health endpoint reports the service as up (no engine needed)."""
    resp = TestClient(app).get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
