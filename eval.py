"""Manual faithfulness check for the RAG service (not run in CI).

It asks the real query engine a few English questions about the documents in
``data/``, then scores each answer with the RAGAS ``faithfulness`` metric: how
much of the answer is supported by the chunks that were retrieved for it. The
process exits non-zero when the average score is below ``FAITHFULNESS_THRESHOLD``.

Needs ``OPENAI_API_KEY`` (the engine and the RAGAS judge both call OpenAI), so it
costs a little money and is run by hand: ``python eval.py``.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import Any

from llama_index.core.base.base_query_engine import BaseQueryEngine

# Below this average the answers are not grounded enough to trust.
FAITHFULNESS_THRESHOLD = 0.8

JUDGE_MODEL = "gpt-4o-mini"

# Questions whose answers are in data/terraform-vpc.md. Add questions that match
# the documents you actually index; faithfulness needs no reference answers.
GOLDEN_QUESTIONS: list[str] = [
    "Which Terraform resource creates a VPC?",
    "Which argument of aws_vpc is required?",
    "Which commands do I run to preview and apply a Terraform change?",
]

Sample = dict[str, Any]
Scorer = Callable[[list[Sample]], float]


def collect_samples(engine: BaseQueryEngine, questions: list[str]) -> list[Sample]:
    """Run each question through the engine and keep the answer plus its source chunks."""
    samples: list[Sample] = []
    for question in questions:
        result = engine.query(question)
        samples.append(
            {
                "user_input": question,
                "response": str(result.response),
                "retrieved_contexts": [
                    node.node.get_content() for node in getattr(result, "source_nodes", [])
                ],
            }
        )
    return samples


def score_faithfulness(samples: list[Sample]) -> float:
    """Average RAGAS faithfulness over ``samples`` (calls the OpenAI judge model)."""
    # Imported here so the pure helpers above stay importable without RAGAS/OpenAI set up.
    from openai import OpenAI
    from ragas import EvaluationDataset, evaluate
    from ragas.llms import llm_factory
    from ragas.metrics import Faithfulness

    judge = llm_factory(JUDGE_MODEL, client=OpenAI())
    result = evaluate(
        EvaluationDataset.from_list(samples),
        metrics=[Faithfulness(llm=judge)],
        raise_exceptions=True,
    )
    scores = [row["faithfulness"] for row in result.scores]
    return sum(scores) / len(scores)


def enforce_faithfulness_gate(score: float, threshold: float = FAITHFULNESS_THRESHOLD) -> None:
    """Exit non-zero when ``score`` is below ``threshold``."""
    if score < threshold:
        print(f"FAIL: faithfulness {score:.2f} < {threshold}")
        sys.exit(1)
    print(f"PASS: faithfulness {score:.2f} >= {threshold}")


def run(
    engine: BaseQueryEngine,
    questions: list[str] = GOLDEN_QUESTIONS,
    scorer: Scorer = score_faithfulness,
) -> float:
    """Evaluate ``engine`` on ``questions`` and return the score (scorer is injectable for tests)."""
    return scorer(collect_samples(engine, questions))


def main() -> None:
    """Build the engine over ``data/``, score it, print JSON, apply the threshold."""
    from rag import build_engine

    score = run(build_engine("data/"))
    print(json.dumps({"faithfulness": round(score, 4), "questions": len(GOLDEN_QUESTIONS)}))
    enforce_faithfulness_gate(score)


if __name__ == "__main__":
    main()
