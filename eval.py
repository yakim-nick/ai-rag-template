"""Automated faithfulness evaluation gate for the RAG service.

Runs the RAG answers against a golden dataset and blocks the CI deploy when
the faithfulness score drops below a threshold.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from ragas import evaluate
from ragas.metrics import faithfulness

# Faithfulness below this value means the model is hallucinating too much to
# ship — the CI gate blocks the deploy.
FAITHFULNESS_THRESHOLD = 0.8

# Replace with your real golden dataset:
# each item needs question, answer, contexts (list), ground_truth
GOLDEN_DATASET: list[dict[str, Any]] = [
    {
        "question": "Как создать VPC в terraform?",
        "answer": "Опиши ресурс aws_vpc с cidr_block и тегами.",
        "contexts": ["aws_vpc { cidr_block = '10.0.0.0/16' }"],
        "ground_truth": "Через ресурс aws_vpc с cidr_block.",
    }
]


def evaluate_faithfulness(dataset: list[dict[str, Any]]) -> float:
    """Score ``dataset`` with the RAGAS faithfulness metric.

    Faithfulness measures how well each answer is grounded in the retrieved
    contexts — a low score means the model is inventing facts.
    """
    score = evaluate(dataset, metrics=[faithfulness])
    return float(score["faithfulness"])


def enforce_faithfulness_gate(
    score: float, threshold: float = FAITHFULNESS_THRESHOLD
) -> None:
    """Exit non-zero when ``score`` is below ``threshold``.

    This is the CI gate: a failing faithfulness score must block the deploy,
    so we terminate the process with a non-zero exit code.
    """
    if score < threshold:
        print(f"FAIL: faithfulness < {threshold} — CI gate blocks deploy")
        sys.exit(1)
    print("PASS: faithfulness OK")


def main() -> None:
    """Run the faithfulness gate and report the score as JSON."""
    score = evaluate_faithfulness(GOLDEN_DATASET)
    print(json.dumps({"faithfulness": score}))
    enforce_faithfulness_gate(score)


if __name__ == "__main__":
    main()
