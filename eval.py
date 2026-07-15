import sys
import json

from ragas import evaluate
from ragas.metrics import faithfulness

# Replace with your real golden dataset:
# each item needs question, answer, contexts (list), ground_truth
dataset = [
    {
        "question": "Как создать VPC в terraform?",
        "answer": "Опиши ресурс aws_vpc с cidr_block и тегами.",
        "contexts": ["aws_vpc { cidr_block = '10.0.0.0/16' }"],
        "ground_truth": "Через ресурс aws_vpc с cidr_block.",
    }
]


def main():
    score = evaluate(dataset, metrics=[faithfulness])
    f = float(score["faithfulness"])
    print(json.dumps({"faithfulness": f}))
    if f < 0.8:
        print("FAIL: faithfulness < 0.8 — CI gate blocks deploy")
        sys.exit(1)
    print("PASS: faithfulness OK")


if __name__ == "__main__":
    main()
