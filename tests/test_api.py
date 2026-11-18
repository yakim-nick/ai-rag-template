"""HTTP-level tests for POST /ask with a fake engine (no API key, no network)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app as app_module
from app import app, engine_provider


class FakeEngine:
    """Mimics a LlamaIndex query engine: ``query(q).response`` is the answer."""

    def __init__(self, answer: str = "Use the aws_vpc resource.", fail: bool = False) -> None:
        self.answer, self.fail = answer, fail
        self.questions: list[str] = []

    def query(self, question: str) -> SimpleNamespace:
        self.questions.append(question)
        if self.fail:
            raise RuntimeError("secret upstream detail sk-123")
        return SimpleNamespace(response=self.answer)


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


def use_engine(engine: FakeEngine) -> None:
    app.dependency_overrides[engine_provider] = lambda: lambda: engine


def test_ask_returns_the_engine_answer(client):
    engine = FakeEngine()
    use_engine(engine)
    res = client.post("/ask", json={"question": "  How do I create a VPC?  "})
    assert res.status_code == 200
    assert res.json() == {"answer": "Use the aws_vpc resource."}
    assert engine.questions == ["How do I create a VPC?"]  # trimmed before use


@pytest.mark.parametrize("question", ["", "   ", "x" * 1001])
def test_invalid_questions_are_rejected_before_the_engine_is_used(client, question):
    engine = FakeEngine()
    use_engine(engine)
    res = client.post("/ask", json={"question": question})
    assert res.status_code == 422
    assert engine.questions == []


def test_missing_question_field_is_rejected(client):
    use_engine(FakeEngine())
    assert client.post("/ask", json={}).status_code == 422


def test_llm_failure_returns_502_without_leaking_details(client):
    use_engine(FakeEngine(fail=True))
    res = client.post("/ask", json={"question": "hello"})
    assert res.status_code == 502
    assert "sk-123" not in res.text and "secret" not in res.text


def test_engine_build_failure_returns_503(client, monkeypatch):
    def boom():
        raise RuntimeError("no api key")

    app_module._build_cached_engine.cache_clear()
    monkeypatch.setattr(app_module, "_build_cached_engine", boom)
    res = client.post("/ask", json={"question": "hello"})
    assert res.status_code == 503
    assert "OPENAI_API_KEY" in res.json()["detail"]


def test_invalid_question_is_rejected_before_the_engine_is_built(client, monkeypatch):
    """A bad request must not trigger the expensive index build (regression test)."""
    built = []
    app_module._build_cached_engine.cache_clear()
    monkeypatch.setattr(app_module, "_build_cached_engine", lambda: built.append(1))
    res = client.post("/ask", json={"question": "   "})
    assert res.status_code == 422
    assert built == []
