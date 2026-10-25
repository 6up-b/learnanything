"""Daily-loop DL2: per-intent recall targets at serving time (§5.3, Q8, G4).

The ratio, identity at 0.90, the kill switches, the anchor rule and its
fallbacks, and (on backup-API copies of the tracked fixtures) the anchor
reproducing every stored ``due_at``: anchor + stability x that attempt's
``fsrs_interval_factor`` equals ``due_at`` within one second, which catches
any drift between the anchor rule and the attempt path.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock, parse_utc
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.scheduling.intent.recall_targets import (
    FALLBACK_ANCHOR_NOT_BEFORE_DUE,
    FALLBACK_NO_ANCHOR,
    FALLBACK_NO_DUE,
    FALLBACK_NO_STATE,
    anchors_from_attempts,
    effective_due,
    load_anchors,
    ratio,
)
from learnloop.scheduling.intent.serving import intent_serving
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS, interval_for_retention
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.vault.loader import load_vault
from tests.owner_vaults import owner_vault, working_vault_params
from tests.daily_plan_fakes import iso
from tests.helpers import append_config_toml
from tests.intent_fakes import NOW, make_intent_vault

# The owner's working vaults: backup-API copies in the owner_vaults lane (S0).
WORKING_FIXTURES = working_vault_params()
W = FSRS6_DEFAULT_WEIGHTS


def test_the_ratio_is_the_fsrs_interval_ratio_and_exactly_one_at_090():
    assert ratio(0.90, W) == 1.0
    for target in (0.80, 0.85, 0.92):
        for stability in (0.7, 3.0, 41.0):
            expected = interval_for_retention(stability, target, W) / interval_for_retention(stability, 0.9, W)
            assert ratio(target, W) == pytest.approx(expected, rel=1e-12)
    assert ratio(0.80, W) > ratio(0.85, W) > 1.0 > ratio(0.92, W)


def test_effective_due_scales_the_interval_from_the_anchor():
    anchor, due = "2026-10-01T00:00:00Z", "2026-10-11T00:00:00Z"
    result = effective_due(due_at=due, anchor_at=anchor, target=0.80, weights=W)
    assert result.fallback is None
    expected = parse_utc(anchor) + (parse_utc(due) - parse_utc(anchor)) * ratio(0.80, W)
    assert result.due == expected
    assert effective_due(due_at=due, anchor_at=anchor, target=0.90, weights=W).due == parse_utc(due)


def test_fallbacks_no_state_null_due_no_anchor_and_anchor_not_before_due():
    assert effective_due(due_at=None, anchor_at=None, target=0.8, weights=W, has_state=False).fallback == FALLBACK_NO_STATE
    assert effective_due(due_at=None, anchor_at=None, target=0.8, weights=W).fallback == FALLBACK_NO_DUE
    unscaled = effective_due(due_at="2026-10-11T00:00:00Z", anchor_at=None, target=0.8, weights=W)
    assert (unscaled.due, unscaled.fallback) == (parse_utc("2026-10-11T00:00:00Z"), FALLBACK_NO_ANCHOR)
    late = effective_due(due_at="2026-10-11T00:00:00Z", anchor_at="2026-10-11T00:00:00Z", target=0.8, weights=W)
    assert (late.due, late.fallback) == (parse_utc("2026-10-11T00:00:00Z"), FALLBACK_ANCHOR_NOT_BEFORE_DUE)


def _row(attempt_id, at, attempt_type="independent_attempt", primed=0, hints=0):
    return {"id": attempt_id, "practice_item_id": "pi", "created_at": at, "attempt_type": attempt_type,
            "primed": primed, "hints_used": hints}


def test_the_anchor_skips_primed_retries_and_diagnostic_attempts_but_an_ordinary_review_moves_it():
    first = _row("a1", "2026-10-01T00:00:00Z")
    primed = _row("a2", "2026-10-03T00:00:00Z", primed=1)
    diagnostic = _row("a3", "2026-10-04T00:00:00Z", attempt_type="diagnostic_probe")
    assert anchors_from_attempts([first, primed, diagnostic])["pi"] == ("2026-10-01T00:00:00Z", "a1")
    review = _row("a4", "2026-10-06T00:00:00Z")
    assert anchors_from_attempts([first, primed, diagnostic, review])["pi"] == ("2026-10-06T00:00:00Z", "a4")


@dataclass
class _State:
    due_at: str | None
    last_attempt_at: str | None
    stability: float | None = 5.0
    active: bool = True


def _insert(repository, attempt_id, item_id, lo_id, at, *, attempt_type="independent_attempt", primed=0):
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "primed, created_at) VALUES (?, ?, ?, 'short_answer', ?, ?, ?)",
            (attempt_id, item_id, lo_id, attempt_type, primed, iso(at)),
        )
        connection.commit()


def test_a_primed_retry_and_a_diagnostic_between_reviews_leave_the_effective_due_unchanged(tmp_path):
    iv = make_intent_vault(tmp_path / "vault")
    iv.choose("practice_item", "pi_b1", "light_touch", NOW)
    state = iv.repository.practice_item_states()["pi_b1"]
    first = iv.serving(NOW).effective("pi_b1", state)
    assert first.fallback is None and first.due > parse_utc(state.due_at)
    _insert(iv.repository, "att_primed", "pi_b1", "lo_b", NOW - timedelta(days=2), primed=1)
    _insert(iv.repository, "att_diag", "pi_b1", "lo_b", NOW - timedelta(days=1), attempt_type="diagnostic_probe")
    assert iv.serving(NOW).effective("pi_b1", state).due == first.due
    _insert(iv.repository, "att_review", "pi_b1", "lo_b", NOW - timedelta(hours=30))
    moved = iv.serving(NOW).effective("pi_b1", state)
    assert moved.due != first.due


def test_identity_at_090_uncommitted_items_are_served_exactly_as_with_intent_off(tmp_path):
    on = make_intent_vault(tmp_path / "on")
    off = make_intent_vault(tmp_path / "off")
    append_config_toml(off.root, "[intent]\nenabled = false\n")
    off.reload()
    for iv in (on, off):
        iv.choose("learning_object", "lo_b", "light_touch", NOW)
        iv.choose("learning_object", "lo_c", "pause", NOW + timedelta(seconds=1))
    at = NOW + timedelta(minutes=5)
    with_intent = {s.practice_item_id: (s.priority, s.components) for s in build_due_queue(
        on.vault, on.repository, clock=FrozenClock(at), persist_explanations=False)}
    without = {s.practice_item_id: (s.priority, s.components) for s in build_due_queue(
        off.vault, off.repository, clock=FrozenClock(at), persist_explanations=False)}
    uncommitted = [item_id for item_id in without if item_id not in {"pi_b1", "pi_c1", "pi_c2"}]
    assert uncommitted
    for item_id in uncommitted:
        assert with_intent[item_id] == without[item_id], item_id
    serving = on.serving(at)
    states = on.repository.practice_item_states()
    for item_id in uncommitted:
        if item_id in states and states[item_id].due_at is not None:
            assert serving.effective(item_id, states[item_id]).due == parse_utc(states[item_id].due_at)


def test_the_kill_switches(tmp_path):
    iv = make_intent_vault(tmp_path / "vault", reviewed_days_ago=2)
    # Reviewed two days ago, due tomorrow at 0.90: a Master target (0.92)
    # brings it forward, Light touch (0.80) pushes it out.
    for item_id in ("pi_a1", "pi_b1"):
        iv.repository.upsert_practice_item_state(
            item_id, difficulty=5.0, stability=3.0, due_at=iso(NOW + timedelta(hours=2)),
            last_attempt_at=iso(NOW - timedelta(days=2)), active=True,
        )
    iv.choose("practice_item", "pi_a1", "master", NOW)
    iv.choose("practice_item", "pi_b1", "pause", NOW)
    at = NOW + timedelta(minutes=1)
    assert "pi_b1" not in iv.queue(at)
    serving = iv.serving(at)
    assert serving.due("pi_a1", iv.repository.practice_item_states()["pi_a1"])
    assert "pi_a1" in iv.queue(at)
    append_config_toml(iv.root, "[intent]\nrecall_targets_enabled = false\n")
    iv.reload()
    assert not iv.serving(at).due("pi_a1", iv.repository.practice_item_states()["pi_a1"])
    assert "pi_b1" not in iv.queue(at)  # exclusion stays
    toml = iv.root / "learnloop.toml"
    toml.write_text(toml.read_text().replace("recall_targets_enabled = false", "recall_targets_enabled = false\nenabled = false"))
    iv.reload()
    assert iv.serving(at) is None
    assert "pi_b1" in iv.queue(at)


def test_stored_due_at_never_changes(tmp_path):
    iv = make_intent_vault(tmp_path / "vault")
    before = {item_id: (s.due_at, s.stability, s.last_attempt_at) for item_id, s in iv.repository.practice_item_states().items()}
    for minute, (kind, scope_id, choice) in enumerate(
        [("learning_object", "lo_a", "master"), ("learning_object", "lo_b", "light_touch"),
         ("practice_item", "pi_c1", "check_once"), ("learning_object", "lo_c", "pause")]
    ):
        iv.choose(kind, scope_id, choice, NOW + timedelta(minutes=minute))
        iv.queue(NOW + timedelta(minutes=minute, seconds=30))
    after = {item_id: (s.due_at, s.stability, s.last_attempt_at) for item_id, s in iv.repository.practice_item_states().items()}
    assert after == before


@pytest.mark.parametrize("fixture", WORKING_FIXTURES)
def test_the_anchor_reproduces_every_stored_due_at_on_fixture_copies(tmp_path, fixture):
    if not (owner_vault(fixture) / "state.sqlite").exists():
        pytest.skip(f"{fixture} fixture absent")
    root = tmp_path / fixture
    copy_tree_with_databases(owner_vault(fixture), root)
    # Read-only on the copy at whatever migration it is (no upgrade).
    connection = sqlite3.connect(f"file:{root / 'state.sqlite'}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        anchors = load_anchors(connection)
        factors = {
            str(row["attempt_id"]): float(row["fsrs_interval_factor"])
            for row in connection.execute(
                "SELECT attempt_id, fsrs_interval_factor FROM attempt_surprise WHERE fsrs_interval_factor IS NOT NULL"
            ).fetchall()
        }
        states = connection.execute(
            "SELECT practice_item_id, due_at, stability FROM practice_item_state WHERE due_at IS NOT NULL"
        ).fetchall()
    finally:
        connection.close()
    checked = 0
    drift: list[tuple[str, float]] = []
    for state in states:
        item_id = str(state["practice_item_id"])
        if state["stability"] is None or item_id not in anchors:
            continue
        anchor_at, attempt_id = anchors[item_id]
        if attempt_id not in factors:
            continue
        expected = parse_utc(anchor_at) + timedelta(days=float(state["stability"]) * factors[attempt_id])
        seconds = abs((expected - parse_utc(state["due_at"])).total_seconds())
        checked += 1
        if seconds > 1.0:
            drift.append((item_id, seconds))
    assert checked > 0
    assert drift == []
