"""Router objective RO1 §5.5-5.6: the projection change, its snapshot, doctor, and predecessor equivalence.

* every whole-vault rebuild's receipt records the factor's switch (the projection's defaults snapshot);
  doctor warns when the vault's config and that record disagree, and the next rebuild clears it;
* below the tag, and with each switch off after the projection change (a rebuild), due dates, the
  surprise rows and the diagnoser's context are byte-identical to mvp-0.45's;
* at the tag, ``due_at`` follows ``interval_for_retention(S)`` on every eligible review after a rebuild;
  surprise values and follow-up triggers match the predecessor; a second rebuild is identical;
* all eight switch combinations: each switch moves exactly its own part.

Fakes only; no model call.
"""

from __future__ import annotations

import itertools
import json
import sqlite3
from contextlib import closing
from datetime import timedelta

import pytest

from learnloop.algorithm_versions import FOLLOWUP_SERVE_ALGORITHM_VERSION, INTERVAL_FACTOR_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.diagnosis.split.context import assemble_diagnosis_context, current_attempt_from
from learnloop.diagnosis.split.history import VaultHistoryStore
from learnloop.diagnosis.split.settings import DiagnosisSettings
from learnloop.goals.exam_seeding import seed_exam_attempts
from learnloop.ops.doctor import run_doctor
from learnloop.params.fitted_params import resolve_fsrs_weights
from learnloop.router_objective_switches import INTERVAL_FACTOR_SNAPSHOT_KEY
from learnloop.scheduling.fsrs import interval_for_retention
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.diagnosis_split_helpers import blind_record
from tests.helpers import NOW, append_config_toml, set_algorithm_version
from tests.test_ro1_interval_factor import HISTORY, _due, _play, _vault
from tests.test_ro1_self_report import picked  # noqa: F401 - the module fixture

TAG = INTERVAL_FACTOR_ALGORITHM_VERSION
PREDECESSOR = FOLLOWUP_SERVE_ALGORITHM_VERSION
SWITCH_TOML = {
    "factor": ("scheduler.surprise", "remove_interval_factor"),
    "available_at": ("router_objective", "available_at_reads"),
    "self_report": ("router_objective", "self_report_not_validated"),
}


def _toml(off: set[str]) -> str:
    sections: dict[str, list[str]] = {}
    for name in sorted(off):
        section, key = SWITCH_TOML[name]
        sections.setdefault(section, []).append(f"{key} = false")
    return "\n".join(f"[{section}]\n" + "\n".join(lines) + "\n" for section, lines in sections.items())


def _schedule(paths) -> dict:
    """Every derived schedule and surprise row, as stored (minus the version stamp)."""

    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        items = [dict(row) for row in connection.execute(
            "SELECT practice_item_id, difficulty, stability, retrievability, due_at, last_attempt_at "
            "FROM practice_item_state ORDER BY practice_item_id")]
        # In attempt order; each vault mints its own attempt ids, so the id is dropped.
        surprise = [dict(row) for row in connection.execute(
            "SELECT s.* FROM attempt_surprise s JOIN practice_attempts a ON a.id = s.attempt_id "
            "ORDER BY a.created_at, a.id")]
        mastery = [dict(row) for row in connection.execute(
            "SELECT * FROM learning_object_mastery WHERE evidence_count > 0 ORDER BY learning_object_id")]
    for row in mastery:
        row.pop("updated_at", None)
        row.pop("algorithm_version", None)
    for row in surprise:
        row.pop("algorithm_version", None)
        row.pop("created_at", None)
        row.pop("id", None)
        row.pop("attempt_id", None)
    return {"items": items, "surprise": surprise, "mastery": mastery}


def _rebuild(paths):
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    rebuild_all_derived_state(vault, repository)
    return repository


def _flip(paths, version: str, toml: str | None):
    set_algorithm_version(paths, version)
    if toml:
        append_config_toml(paths.root, toml)


def _played_at(tmp_path, version: str, toml: str | None = None):
    """The history played live at mvp-0.45, then (the projection change) the version and the switches set
    and a whole-vault rebuild."""

    paths, repository = _vault(tmp_path, PREDECESSOR)
    played = _play(paths, repository)
    _flip(paths, version, toml)
    _rebuild(paths)
    return paths, played


def _issues(paths):
    return {issue.code for issue in run_doctor(paths.root).issues}


# --- the snapshot and doctor -------------------------------------------------------------------------


def test_every_whole_vault_rebuild_records_the_factors_switch(tmp_path):
    paths, _played = _played_at(tmp_path / "on", TAG)
    marker = Repository(paths.sqlite_path).latest_whole_vault_rebuild()
    assert marker["projection_switches"] == {INTERVAL_FACTOR_SNAPSHOT_KEY: True}
    off, _ = _played_at(tmp_path / "off", TAG, _toml({"factor"}))
    assert Repository(off.sqlite_path).latest_whole_vault_rebuild()["projection_switches"] == {
        INTERVAL_FACTOR_SNAPSHOT_KEY: False}
    below, _ = _played_at(tmp_path / "below", PREDECESSOR)
    assert Repository(below.sqlite_path).latest_whole_vault_rebuild()["projection_switches"] == {
        INTERVAL_FACTOR_SNAPSHOT_KEY: False}


def test_doctor_warns_when_the_config_and_the_snapshot_disagree_until_the_next_rebuild(tmp_path):
    paths, _played = _played_at(tmp_path, TAG)
    assert "sql:projection_switches_stale" not in _issues(paths)
    append_config_toml(paths.root, _toml({"factor"}))
    assert "sql:projection_switches_stale" in _issues(paths)
    _rebuild(paths)
    assert "sql:projection_switches_stale" not in _issues(paths)


def test_doctor_compares_nothing_without_a_recorded_snapshot(tmp_path):
    paths, repository = _vault(tmp_path, TAG)
    _play(paths, repository)
    append_config_toml(paths.root, _toml({"factor"}))
    assert repository.latest_whole_vault_rebuild() is None
    assert "sql:projection_switches_stale" not in _issues(paths)


# --- predecessor equivalence after the projection change ---------------------------------------------


@pytest.fixture(scope="module")
def predecessor(tmp_path_factory):
    paths, played = _played_at(tmp_path_factory.mktemp("predecessor"), PREDECESSOR)
    return _schedule(paths), played


def test_below_the_tag_and_with_the_factor_off_the_schedule_is_byte_identical(tmp_path, predecessor):
    expected, _ = predecessor
    paths, _ = _played_at(tmp_path / "off", TAG, _toml({"factor"}))
    assert _schedule(paths) == expected
    # Live at the tag with the switch off from the start: the same.
    live, repository = _vault(tmp_path / "live_off", TAG, _toml({"factor"}))
    _play(live, repository)
    assert _schedule(live) == expected


def test_at_the_tag_a_rebuild_moves_every_eligible_due_date_to_the_unstretched_interval(tmp_path, predecessor):
    expected, played = predecessor
    paths, _ = _played_at(tmp_path, TAG)
    got = _schedule(paths)
    weights = resolve_fsrs_weights(Repository(paths.sqlite_path))
    last = {item: observed for _a, item, observed, _s, _r in played}
    for row, before in zip(got["items"], expected["items"], strict=True):
        assert (row["stability"], row["difficulty"], row["last_attempt_at"]) == (
            before["stability"], before["difficulty"], before["last_attempt_at"])
        assert row["due_at"] == _due(last[row["practice_item_id"]],
                                     interval_for_retention(row["stability"], weights=weights))
    # Surprise and its triggers match the predecessor; only the applied factor reads 1.0.
    for row, before in zip(got["surprise"], expected["surprise"], strict=True):
        assert row["fsrs_interval_factor"] == 1.0
        assert {k: v for k, v in row.items() if k != "fsrs_interval_factor"} == {
            k: v for k, v in before.items() if k != "fsrs_interval_factor"}
    assert got["mastery"] == expected["mastery"]
    assert len(got["surprise"]) == len(HISTORY)


def test_a_second_rebuild_is_identical(tmp_path):
    paths, _ = _played_at(tmp_path, TAG)
    first = _schedule(paths)
    _rebuild(paths)
    assert _schedule(paths) == first


def test_a_live_review_at_the_tag_and_its_rebuild_agree(tmp_path):
    live, repository = _vault(tmp_path / "live", TAG)
    _play(live, repository)
    before = _schedule(live)
    _rebuild(live)
    assert _schedule(live) == before


@pytest.mark.parametrize("off", [set(combo) for size in range(4) for combo in itertools.combinations(sorted(SWITCH_TOML), size)],
                         ids=lambda off: "off=" + ("+".join(sorted(off)) or "none"))
def test_every_switch_combination_moves_exactly_its_own_part(tmp_path, predecessor, off):
    expected, _ = predecessor
    paths, _ = _played_at(tmp_path, TAG, _toml(off) or None)
    got = _schedule(paths)
    factor_off = "factor" in off
    assert (got["items"] == expected["items"]) is factor_off
    assert got["mastery"] == expected["mastery"]
    config = load_vault(paths.root).config
    from learnloop.router_objective_switches import (
        available_at_reads_on,
        interval_factor_removed,
        self_report_not_validated_on,
    )

    assert interval_factor_removed(config) is not factor_off
    assert available_at_reads_on(config) is ("available_at" not in off)
    assert self_report_not_validated_on(config) is ("self_report" not in off)


# --- the diagnoser's context -------------------------------------------------------------------------


def _context(picked_paths, tmp_path, version: str, toml: str | None) -> tuple[str, str, dict]:
    root = tmp_path / f"{version}-{bool(toml)}".replace(".", "_")
    copy_tree_with_databases(picked_paths.root, root)
    paths = VaultPaths(root, picked_paths.config)
    _flip(paths, version, toml)
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    store = VaultHistoryStore(vault, repository)
    item = vault.practice_items["pi_svd_ambiguous_001"]
    current = current_attempt_from(
        vault, item, attempt_id="ctx_current", completed_at=(NOW + timedelta(days=3)).isoformat().replace("+00:00", "Z"),
        learner_answer_md="The current answer.",
        blind_grade=blind_record(score=0, max_points=item_max_points(vault, item), criteria={"whole_item": 0}),
    )
    assembled = assemble_diagnosis_context(vault, store, current, DiagnosisSettings(), mode="full")
    hypotheses = {row["id"]: row for row in assembled.blocks.get("prior_hypotheses") or []}
    return assembled.rendered(), assembled.context_hash, hypotheses


def item_max_points(vault, item):
    from learnloop.attempts.grading import resolved_rubric

    return resolved_rubric(vault, item).max_points


def test_the_diagnosers_context_is_the_predecessors_below_the_tag_and_switched_off(picked, tmp_path):
    paths, factor_id, _attempt_id = picked
    below = _context(paths, tmp_path, PREDECESSOR, None)
    off = _context(paths, tmp_path, TAG, _toml({"self_report"}))
    on = _context(paths, tmp_path, TAG, None)
    assert off[0] == below[0] and off[1] == below[1]
    # At the tag the pick is still shown (the learner's attributed opinion), counted as no validated evidence.
    assert below[2][factor_id]["validated_evidence_count"] == 1
    assert on[2][factor_id]["validated_evidence_count"] == 0
    assert on[2][factor_id]["status"] == below[2][factor_id]["status"]
    assert on[1] != below[1]


# --- exam rows: availability changes no projection --------------------------------------------------


def test_availability_moves_no_due_date_or_mastery(tmp_path):
    from tests.test_exam_seeding import _exam_vault, _outcomes

    results = {}
    for name, version, toml in (("tag", TAG, None), ("off", TAG, _toml({"available_at"})),
                                ("below", PREDECESSOR, None)):
        root, _loaded, repository = _exam_vault(tmp_path / name)
        vault = load_vault(root)
        paths = VaultPaths(vault.root, vault.config)
        _flip(paths, version, toml)
        seed_exam_attempts(load_vault(root), repository, outcomes=_outcomes(), clock=FrozenClock(NOW))
        state = _schedule(paths)
        results[name] = {"items": state["items"], "mastery": state["mastery"]}
    # The factor is on at the tag, so compare availability's own switch only: on and off agree.
    assert results["tag"] == results["off"]
    assert json.dumps(results["below"]["mastery"]) == json.dumps(results["tag"]["mastery"])
