"""What other test files use from ``tests/test_embedding_compare.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json


def benchmark(tmp_path, *, licence="CC-BY-4.0"):
    directory = tmp_path / "b2"
    directory.mkdir(parents=True)
    (directory / "manifest.json").write_text(json.dumps({
        "name": "b2-test", "sources": [{"name": "synthetic", "version": "1", "licence": licence}]}))
    rows = []
    for index in range(6):
        rows.append({"id": f"p{index}", "label": "positive", "category": "gsm_symbolic", "domain": "arithmetic",
                     "left": {"stem": f"Ana has {index + 2} apples and buys {index + 3} more apples. How many apples?",
                              "answer": str(2 * index + 5)},
                     "right": {"stem": f"Ana has {index + 7} apples and buys {index + 1} more apples. How many apples?",
                               "answer": str(2 * index + 8)}})
        rows.append({"id": f"n{index}", "label": "negative", "category": "math_perturb_hard", "domain": "arithmetic",
                     "left": {"stem": f"A train travels {index + 40} km in {index + 2} hours. What is its speed?",
                              "answer": "x"},
                     "right": {"stem": f"Ana has {index + 2} apples and buys {index + 3} more apples. How many apples?",
                               "answer": str(2 * index + 5)}})
    (directory / "pairs.jsonl").write_text("\n".join(json.dumps(row) for row in rows))
    return directory
