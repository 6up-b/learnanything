"""The probe router's owner-copy counts (``scripts/probe_router_copy_counts.py``) on the diagnosis journeys' vaults: it
reads a copy without writing anything, counts what the router decided on each lane and how, and prints no id or text.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import pytest

from tests.diagnosis_journey_helpers import run_case

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("probe_router_copy_counts",
                                                  ROOT / "scripts" / "probe_router_copy_counts.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(spec.name, None)


def _copy(case: str, root: Path, monkeypatch) -> Path:
    root.mkdir()
    journey = run_case(case, root, monkeypatch)
    return Path(journey.repository.sqlite_path).parent


def _state(vault: Path) -> tuple[str, list[str]]:
    database = vault / "state.sqlite"
    return hashlib.sha256(database.read_bytes()).hexdigest(), sorted(p.name for p in vault.iterdir())


def test_the_counts_read_a_copy_without_a_write_and_count_each_lanes_decisions(script, tmp_path, monkeypatch):
    offered = _copy("router_learner_offered", tmp_path / "offered", monkeypatch)
    before = _state(offered)
    out = script.counts(offered)
    assert _state(offered) == before
    assert out["probe_router_on"] is True
    assert out["learner_decisions_by_choice"] == {"probe": 1}
    assert out["learner_decisions_learned"] == {"False": 1}
    assert out["learner_decisions_served_by"] == {"probe_coin": 1}
    assert out["probe_coin_assignments_by_variant"] == {"ask_probe": 1}
    assert out["causal_receipts_by_decision"] == {"router_decides": 1}
    assert out["presentations_pinning_a_router_decision"] == 1
    # No id and no text: every value is a count, a flag or a tag.
    with sqlite3.connect(offered / "state.sqlite") as connection:
        ids = {str(row[0]) for row in connection.execute("SELECT id FROM router_decisions")}
    assert not any(value in json.dumps(out) for value in ids)


def test_compare_names_only_the_counts_that_moved(script, tmp_path, monkeypatch):
    offered = script.counts(_copy("router_learner_offered", tmp_path / "offered", monkeypatch))
    declined = script.counts(_copy("router_learner_not_selected", tmp_path / "declined", monkeypatch))
    moved = script.compare(offered, declined)
    assert moved["learner_decisions_by_choice.probe"] == [1, None]
    assert moved["learner_decisions_by_choice.no_probe"] == [None, 1]
    assert "algorithm_version" not in moved and "causal_receipts_by_decision.router_decides" not in moved
