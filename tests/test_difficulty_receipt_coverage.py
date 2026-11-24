"""H3's owner-copy counts (scripts/difficulty_receipt_coverage.py; the design note's §10) on a synthetic vault: read-only,
counts only, the same receipt rule as the replay's arms (e) and (f)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from learnloop.db.copies import copy_tree_with_databases
from learnloop.vault.loader import load_vault

from tests.difficulty_replay_helpers import HISTORY, LLM_LABELLED, UNBOUND, build_vault, file_digests, \
    forbid_model_clients, load_script


@pytest.fixture(scope="module")
def script():
    return load_script("difficulty_receipt_coverage")


@pytest.fixture(scope="module")
def served(tmp_path_factory):
    return build_vault(tmp_path_factory.mktemp("coverage") / "vault", served=True)


def test_the_counts(script, served, monkeypatch):
    forbid_model_clients(monkeypatch)
    before = file_digests(served.root)
    report = script.coverage(served.root)
    assert file_digests(served.root) == before and report["input_databases_unchanged"] is True
    covered = len(HISTORY) - len(UNBOUND) - 1
    everything = report["receipt_coverage"]["all"]
    assert everything["attempts"] == len(HISTORY)
    # The primed retry answered a presentation already answered: the live door recorded it unbound.
    assert everything["bound"] == covered
    assert everything["with_receipt"] == covered and everything["with_receipt_primed"] == 0
    assert everything["fallback:unbound"] == len(UNBOUND) + 1
    assert set(report["receipt_coverage"]["by_attempt_type"]) == {"independent_attempt"}
    assert report["item_parameter_state_rows"] == 0
    assert report["exam_pools"] == {"available": True, "unreleased_by_stratum": {}, "unreleased_goals": 0,
                                    "released": 0}
    gate = report["gate_records"]
    assert gate["available"] is True and gate["rows"] == len(HISTORY)
    assert report["label"]["items_by_source"].get("llm_estimate") == len(LLM_LABELLED)
    assert report["label"]["items"] == sum(report["label"]["items_by_source"].values())
    assert report["config"]["mastery.irt.eb_difficulty_enabled"] is False
    assert report["config"]["mastery.irt.difficulty_default"] == 0.0
    assert report["integrity_check"] == ["ok"] and report["foreign_key_violations"] == 0


def test_an_unserved_vault_counts_every_attempt_unbound(script, tmp_path, monkeypatch):
    forbid_model_clients(monkeypatch)
    paths = build_vault(tmp_path / "plain")
    everything = script.coverage(paths.root)["receipt_coverage"]["all"]
    assert everything == {"attempts": len(HISTORY), "bound": 0, "fallback:unbound": len(HISTORY)}


def test_stdout_is_counts_only_and_a_live_vault_or_an_out_inside_is_refused(script, served, tmp_path, capsys,
                                                                             monkeypatch):
    forbid_model_clients(monkeypatch)
    copy = tmp_path / "copy"
    copy_tree_with_databases(served.root, copy)
    assert script.main([str(copy), "--out", str(tmp_path / "private" / "counts.json")]) == 0
    printed = capsys.readouterr().out
    assert json.loads(printed) == json.loads((tmp_path / "private" / "counts.json").read_text(encoding="utf-8"))
    vault = load_vault(copy, load_environment=False)
    with __import__("contextlib").closing(__import__("sqlite3").connect(served.sqlite_path)) as connection:
        attempt_ids = {row[0] for row in connection.execute("SELECT id FROM practice_attempts")}
    forbidden = attempt_ids | set(vault.practice_items) | set(vault.learning_objects)
    forbidden |= {item.prompt for item in vault.practice_items.values()} | {"pp_h3_", "blk_h3_"}
    assert attempt_ids and not [token for token in forbidden if token in printed]
    with pytest.raises(SystemExit):
        script.main([str(copy), "--out", str(copy / "inside.json")])
    assert not (copy / "inside.json").exists()
    home = tmp_path / "home"
    live = home / "learnloop-vaults" / "v"
    copy_tree_with_databases(served.root, live)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    with pytest.raises(SystemExit):
        script.coverage(live)
