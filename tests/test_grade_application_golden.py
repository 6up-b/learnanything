"""Every grade application of one graded history, pinned live and after a rebuild (``tests/grade_application_golden_helpers.py``).

The history reaches each kind of grade the attempt step applies: self-graded, a model grade with error attributions
(one stripped by the passed-target firewall), hinted, primed, "I don't know", stuck, a model grade with a criterion
unassessed, one held for review, a repeat and a sibling on the same surface group, the real blind-grading door, a
regrade (which replays its learning object) and an adjudication's correction (read by the rebuild). The record holds
every field of every ``AttemptApplication`` the step computed, in order, live and in the rebuild, and every row each
phase added or removed, table by table. Floats keep every bit, so a change to any expression's operand order or
float type shows here.

Ids read ``<ulid:n>`` in order of first appearance (the ULID stream is also seeded and its clock held); wall-clock
stamps read ``<wall>`` and the vault's algorithm tag ``<head tag>``.

A change that means to change what an attempt writes regenerates the file and shows the diff in review:

    GRADE_APPLICATION_GOLDEN_WRITE=1 uv run pytest tests/test_grade_application_golden.py

``GRADE_APPLICATION_GOLDEN_ACTUAL=<file>`` writes the record there as well, to diff against the golden.
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path
from types import SimpleNamespace

import pytest

from learnloop.attempts import attempts as attempts_module
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

from tests.grade_application_golden_helpers import (
    REBUILD_CLOCK,
    Normalizer,
    build_graded_vault,
    plain,
    play_history,
    row_delta,
    table_rows,
)

GOLDEN = Path(__file__).parent / "goldens" / "grade_application" / "history.json"
WRITE = os.environ.get("GRADE_APPLICATION_GOLDEN_WRITE") == "1"
_ULID_MS = 1_790_000_000_000


@pytest.fixture
def seeded_ids(monkeypatch):
    from learnloop import ids

    monkeypatch.setattr(ids, "_wall_clock_ms", lambda: _ULID_MS)
    monkeypatch.setattr(ids, "secrets", SimpleNamespace(randbits=random.Random(20261114).getrandbits))
    monkeypatch.setattr(ids, "_last_timestamp_ms", -1)
    monkeypatch.setattr(ids, "_last_randomness", 0)


def _record(tmp_path, monkeypatch) -> dict:
    paths, vault, repository = build_graded_vault(tmp_path)
    applications: list[dict] = []
    compute = attempts_module.compute_attempt_application

    def recording(vault, repository, attempt, **kwargs):
        application = compute(vault, repository, attempt, **kwargs)
        applications.append({
            "attempt_id": attempt.attempt_id,
            "replay": attempt.replace_existing,
            "application": plain(application),
        })
        return application

    monkeypatch.setattr(attempts_module, "compute_attempt_application", recording)
    setup = table_rows(paths.sqlite_path)
    labels = play_history(vault, repository)
    live_applications = list(applications)
    live = table_rows(paths.sqlite_path)
    applications.clear()
    rebuild_all_derived_state(vault, repository, clock=REBUILD_CLOCK)
    rebuilt = table_rows(paths.sqlite_path)
    return {
        "labels": labels,
        "live_applications": live_applications,
        "live_rows": row_delta(setup, live),
        "rebuild_applications": list(applications),
        "rebuild_rows": row_delta(live, rebuilt),
    }


def _text(record: dict) -> str:
    return Normalizer()(json.dumps(record, indent=1, sort_keys=False)) + "\n"


def test_every_grade_application_and_row_is_unchanged(tmp_path, monkeypatch, seeded_ids):
    text = _text(_record(tmp_path, monkeypatch))
    actual = os.environ.get("GRADE_APPLICATION_GOLDEN_ACTUAL")
    if actual:
        Path(actual).write_text(text, encoding="utf-8")
    if WRITE:
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(text, encoding="utf-8")
    assert text == GOLDEN.read_text(encoding="utf-8")


def test_the_history_reaches_every_kind_of_grade(tmp_path, monkeypatch, seeded_ids):
    """The golden pins what it claims only while the history still reaches each kind."""

    record = _record(tmp_path, monkeypatch)
    live = {entry["attempt_id"]: entry["application"] for entry in record["live_applications"] if not entry["replay"]}
    labels = record["labels"]
    debug = {label: live[attempt_id]["attempt_debug_payload"] for label, attempt_id in labels.items()}
    rows = {label: live[attempt_id]["attempt_record"] for label, attempt_id in labels.items()}
    assert rows["hinted"]["hints_used"] == 1
    assert rows["primed"]["primed"] is True
    assert rows["dont_know"]["attempt_type"] == "dont_know"
    assert rows["stuck"]["declared_stuck"] is True
    assert debug["unassessed"]["unassessed_criteria"] == ["result"]
    assert debug["held"]["grade_held_for_review"] is True
    # The firewall stripped the attribution aimed at the passed criterion.
    assert debug["model"]["causal_attribution"]["firewall_events"]
    assert len(live[labels["model"]]["error_events"]) == 2
    # A model grade read the grade channel's variance.
    assert live[labels["model"]]["result"]["grading_source"] == "ai"
    # Familiarity discounted the repeats.
    assert debug["repeat"]["familiarity_trace"]["independent_evidence_discount"] < 1.0
    # The regrade and the rebuild replayed the history.
    assert any(entry["replay"] for entry in record["live_applications"])
    replayed = {entry["attempt_id"] for entry in record["rebuild_applications"]}
    assert set(labels.values()) <= replayed
