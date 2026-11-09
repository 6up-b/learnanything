"""scripts/refactor_measures.py counts by the map's definitions (refactor S0, Z2).

Only the pure counting helpers: the whole sweep reads every tracked file and
belongs to S0 and Z2, not the suite."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _measures():
    spec = importlib.util.spec_from_file_location("refactor_measures", ROOT / "scripts" / "refactor_measures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE = '''"""Module docstring naming mvp-0.9."""

# a comment naming mvp-0.43 and mvp-0.44
TAG = "mvp-0.50"


def f(x):
    """Docstring, mvp-0.12."""
    text = f"""multi mvp-0.13 {x}"""
    return x in SOME_VERSIONS and text
'''


def test_python_facts_splits_tags_and_counts_code(tmp_path):
    path = tmp_path / "sample.py"
    path.write_text(SOURCE, encoding="utf-8")
    facts = _measures().python_facts(path)
    assert facts["tags"] == {"comment": 2, "docstring": 3, "code": 1}
    # TAG =, def, text =, return: comments, blanks and docstrings aren't code.
    assert facts["code"] == 4
    assert facts["functions"] == 1


def test_frozen_sets_and_latest_pins_are_found():
    measures = _measures()
    tree = ast.parse(
        'assert X_VERSIONS == frozenset({"mvp-0.24", "mvp-0.25"})\n'
        'assert Y_VERSIONS == {"mvp-0.30"}\n'
        'assert Z_VERSIONS == set(SUCCESSOR_CHAIN[3:])\n'
        'assert SUCCESSOR_CHAIN[-1] == LATEST == "mvp-0.54"\n'
    )
    assert measures._frozen_set_assertions(tree) == 2
    assert measures._latest_pin(tree)
    assert not measures._latest_pin(ast.parse("assert LATEST == SUCCESSOR_CHAIN[-1]\n"))
