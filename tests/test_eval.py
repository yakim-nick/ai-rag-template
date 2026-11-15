"""eval.py logic that does not need an API key: sample collection and the gate."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import eval as eval_module


class FakeEngine:
    def query(self, question: str) -> SimpleNamespace:
        node = SimpleNamespace(node=SimpleNamespace(get_content=lambda: f"context for {question}"))
        return SimpleNamespace(response=f"answer to {question}", source_nodes=[node])


def test_collect_samples_keeps_answer_and_retrieved_contexts():
    samples = eval_module.collect_samples(FakeEngine(), ["a?", "b?"])
    assert samples[0] == {
        "user_input": "a?",
        "response": "answer to a?",
        "retrieved_contexts": ["context for a?"],
    }
    assert len(samples) == 2


def test_run_passes_engine_output_to_the_scorer():
    seen = {}

    def scorer(samples):
        seen["samples"] = samples
        return 0.9

    assert eval_module.run(FakeEngine(), ["q?"], scorer) == 0.9
    assert seen["samples"][0]["response"] == "answer to q?"


def test_samples_are_valid_ragas_input():
    """The dict shape must be accepted by RAGAS (no LLM call is made here)."""
    from ragas import EvaluationDataset

    samples = eval_module.collect_samples(FakeEngine(), ["q?"])
    assert len(EvaluationDataset.from_list(samples)) == 1


def test_gate_passes_at_or_above_threshold(capsys):
    eval_module.enforce_faithfulness_gate(0.8)
    assert "PASS" in capsys.readouterr().out


def test_gate_exits_non_zero_below_threshold(capsys):
    with pytest.raises(SystemExit) as exc:
        eval_module.enforce_faithfulness_gate(0.79)
    assert exc.value.code == 1
    assert "FAIL" in capsys.readouterr().out


def test_golden_questions_are_answerable_from_the_sample_document():
    text = Path("data/terraform-vpc.md").read_text().lower()
    assert "aws_vpc" in text and "cidr_block" in text and "terraform apply" in text
    assert len(eval_module.GOLDEN_QUESTIONS) >= 3
