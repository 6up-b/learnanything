"""The figure grammar's differential property test (reader workbench RW5a, fix round 3).

This is the parity contract from fix round 3 on (``tests/figure_property_corpus.py``):

* the corpus file is exactly what the seeded generator builds (so the
  Python evaluator's verdicts and values in it are today's);
* no value either evaluator shows is -0;
* ``figureGrammar.test.ts`` holds the TypeScript evaluator to the same file.

The SymPy comparison of fix rounds 3-5 went with the source check (owner scope
decision 2026-10-21; RW5c brings it back with its design).
"""

from __future__ import annotations

import json
import math

from tests import figure_property_corpus as FP

CORPUS = json.loads(FP.CORPUS_PATH.read_text(encoding="utf-8"))
CASES = CORPUS["cases"]


def _decode(value):
    if isinstance(value, str):
        return {"nan": math.nan, "inf": math.inf, "-inf": -math.inf}[value]
    return value


def test_the_property_corpus_is_the_generator_output():
    assert FP.CORPUS_PATH.read_text(encoding="utf-8") == FP.render()


def test_the_corpus_covers_its_families():
    ids = [case["id"] for case in CASES]
    assert len(ids) == len(set(ids)) and sum(1 for case_id in ids if case_id.startswith("random_")) == FP.RANDOM_CASES
    for family in ("signed_zero", "sum_range", "reserved", "comparison", "magnitude"):
        assert any(case_id.startswith(family) for case_id in ids), family
    # Every reserved-looking identifier is refused, in both parsers.
    assert all(not case["accepted"] for case in CASES
               if case["id"].startswith("reserved") and case["expr"] not in ("x2 + 1",))
    accepted = [case for case in CASES if case["accepted"]]
    assert len(accepted) > 2500
    assert any(case["expected"] == "nan" for case in accepted)
    assert sum(1 for case in accepted if "sum(" in case["expr"]) > 200
    assert sum(1 for case in accepted if "piecewise(" in case["expr"]) > 300


def test_no_value_is_negative_zero():
    for case in CASES:
        if case["accepted"] and isinstance(case["expected"], float) and case["expected"] == 0:
            assert math.copysign(1.0, case["expected"]) > 0, case


