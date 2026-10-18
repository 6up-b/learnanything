"""Adaptive hints H1's boundaries (spec_adaptive_hints_v1 H1, H2, G-H13; H2's G-H4 boundary).

* No grading or diagnosis prompt builder imports or reads ``approach_maps``:
  ``learnloop.attempts`` and ``learnloop.diagnosis`` (every grader and
  diagnoser prompt builder) never import ``learnloop.hints`` or the map
  store (the import-linter contract ``graders-never-read-approach-maps``,
  checked here by source too) and never name the table; with a map stored,
  the rendered blind-grading and joint grading prompts carry none of it, and
  rendering them reads nothing from the table.
* ``learnloop.hints`` stays under ``hints-never-write-evidence`` (its only
  reads from evidence packages are the two pure reads named in the contract).
"""
from __future__ import annotations

import ast
import sqlite3
import tomllib
from pathlib import Path

import learnloop.db.connection as db_connection
from learnloop.db.repositories import Repository
from learnloop.hints import map_builder as MB
from learnloop.vault.loader import load_vault
from tests.approach_map_fakes import ITEM, TRACE_CONTRACT, MapFake, map_vault, rows

ROOT = Path(__file__).resolve().parents[1]
PROMPT_PACKAGES = ("attempts", "diagnosis")


def _modules(package: str):
    for path in sorted((ROOT / "src" / "learnloop" / package).rglob("*.py")):
        yield path, ast.parse(path.read_text(encoding="utf-8"))


def test_no_grading_or_diagnosis_module_imports_hints_or_names_the_table():
    for package in PROMPT_PACKAGES:
        for path, tree in _modules(package):
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    names = [node.module or ""] + [f"{node.module}.{alias.name}" for alias in node.names]
                elif isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                else:
                    continue
                for name in names:
                    assert not name.startswith("learnloop.hints"), f"{path} imports {name}"
                    assert "approach_maps" not in name, f"{path} imports {name}"
            assert "approach_map" not in path.read_text(encoding="utf-8"), f"{path} names approach maps"


def test_the_import_contracts_pin_both_boundaries():
    contracts = {contract["id"]: contract for contract in
                 tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["importlinter"]["contracts"]}
    graders = contracts["graders-never-read-approach-maps"]
    assert set(graders["source_modules"]) == {"learnloop.attempts", "learnloop.diagnosis"}
    assert set(graders["forbidden_modules"]) == {"learnloop.hints", "learnloop.db.stores.approach_maps"}
    hints = contracts["hints-never-write-evidence"]
    assert hints["source_modules"] == ["learnloop.hints"]
    assert {"learnloop.attempts", "learnloop.placement", "learnloop.substrate"} <= set(hints["forbidden_modules"])
    assert set(hints["ignore_imports"]) == {
        "learnloop.hints.maps -> learnloop.attempts.answer_check",
        "learnloop.hints.map_seeds -> learnloop.placement.state",
        # Adaptive hints H2a's pure reads: the hint state's placement intent and
        # predictor, and the discriminating questions' EIG ranking.
        "learnloop.hints.state -> learnloop.placement.state",
        "learnloop.hints.state -> learnloop.placement.predictor",
        "learnloop.hints.discriminating -> learnloop.diagnosis.probe_families",
    }


def test_grading_prompts_never_carry_or_read_a_stored_map(tmp_path, monkeypatch):
    from learnloop.attempts.blind_grading import blind_grading_context, blind_grading_prompt
    from learnloop.attempts.grading import build_grading_context

    paths = map_vault(tmp_path, trace_contract=TRACE_CONTRACT)
    outcome = MB.build_map(load_vault(paths.root), Repository.attach(paths.sqlite_path), ITEM, trigger="cli",
                           client=MapFake())
    assert outcome.status == "built"
    [row] = rows(paths.sqlite_path)
    reads: list[str] = []
    original = db_connection.sqlite3.connect

    def authorize(action, first, _second, _database, _source):
        if action == sqlite3.SQLITE_READ and first == "approach_maps":
            reads.append(first)
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    def connect(*args, **kwargs):
        connection = original(*args, **kwargs)
        connection.set_authorizer(authorize)
        return connection

    monkeypatch.setattr(db_connection.sqlite3, "connect", connect)
    vault = load_vault(paths.root)
    item = vault.practice_items[ITEM]
    answer = "F(x) = x^2 on [0, 1], so P(X ≤ 1/2) = 1/4."
    blind = blind_grading_prompt(blind_grading_context(vault, item, attempt_id="att_1", learner_answer_md=answer))
    joint = build_grading_context(vault, item, attempt_id="att_1", learner_answer_md=answer)
    rendered = blind + repr(joint)
    for marker in ("Find the CDF on the support", "Read the density", "r_ref", "CDF route", row["id"],
                   "approach_map"):
        assert marker not in rendered, marker
    assert reads == []
