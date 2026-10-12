"""The optional quick check, "Check what I already know" (field §5.2, D4).

A calibration session that is never prompted, serves at most k = 4 adaptive
ordinary items within 8 minutes, stops early once every LO is decided,
withholds results until it ends, and feeds the assumed/learning split.
"""

from __future__ import annotations

import json
import sqlite3

import pytest

from learnloop.diagnosis.quick_check import QuickCheckError, quick_check_progress, start_quick_check
from learnloop.diagnosis.calibration_sessions import stop_calibration_session
from learnloop.placement.decisions import reconcile_fast_track
from learnloop.placement.predictor import active_predictor
from learnloop.substrate.state_sync import sync_vault_state

from tests.test_assumed_known import LOW_Q, _answer, _at, _decisions, _queue, _setup


def _start(vault, repository, los, *, minutes=1):
    session_id = repository.create_session(available_minutes=25, clock=_at(0))
    progress = start_quick_check(
        vault, repository, session_id=session_id, learning_object_ids=los, clock=_at(minutes),
    )
    return session_id, progress


def _progress(vault, repository, progress, minutes):
    return quick_check_progress(vault, repository, progress["calibration_session_id"], clock=_at(minutes))


def _answer_target(vault, repository, session_id, progress, minutes, points=4.0):
    """Answer the item the check presented (only presented items are its answers)."""

    item_id = progress["next_target"]["practice_item_id"]
    _answer(vault, repository, item_id, points, minutes=minutes, session_id=session_id)
    return item_id


def test_quick_check_is_a_short_calibration_session_without_episodes(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    _session, progress = _start(vault, repository, ["lo_diag", "lo_eigen_basics"])

    assert repository.open_probe_episodes() == {}  # no opening probe survives it
    assert progress["status"] == "active"
    assert progress["time_budget_minutes"] == 8
    assert progress["blocks_planned"] == 0
    quick = progress["quick_check"]
    assert (quick["k"], quick["answered"], quick["remaining"], quick["finished"]) == (4, 0, 4, False)
    assert quick["results"] is None
    target = progress["next_target"]
    assert target["selection_objective"] == "conditional_gain"
    assert target["learning_object_id"] in {"lo_diag", "lo_eigen_basics"}
    assert vault.practice_items[target["practice_item_id"]].practice_mode != "diagnostic_probe"


def test_selection_is_the_largest_conditional_gain_and_deterministic(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    _session, progress = _start(vault, repository, ["lo_diag", "lo_eigen_basics"])
    predictor = active_predictor(vault, repository)
    weights = {"lo_diag": 1.0, "lo_eigen_basics": 1.0}
    candidates = sorted(
        item_id for item_id, item in vault.practice_items.items()
        if item.learning_object_id in weights
    )
    expected = sorted(candidates, key=lambda i: (-predictor.conditional_gain(i, [], weights), i))[0]
    assert progress["next_target"]["practice_item_id"] == expected
    assert _progress(vault, repository, progress, 2)["next_target"] == progress["next_target"]


def test_results_are_withheld_until_the_end_then_feed_the_split(tmp_path):
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    session_id, progress = _start(vault, repository, ["lo_diag"])

    first = _answer_target(vault, repository, session_id, progress, 2)
    middle = _progress(vault, repository, progress, 3)
    assert middle["quick_check"]["answered"] == 1 and middle["quick_check"]["results"] is None
    assert middle["status"] == "active"

    second = _answer_target(vault, repository, session_id, middle, 4)
    done = _progress(vault, repository, progress, 5)
    # Early stop: the only LO is decided after two clean answers.
    assert done["status"] == "completed" and done["next_target"] is None
    quick = done["quick_check"]
    assert quick["finished"] and quick["answered"] == 2
    (result,) = quick["results"]
    assert result["verdict"] == "assumed"
    assert [answer["practice_item_id"] for answer in result["answers"]] == [first, second]
    (decision,) = _decisions(paths)
    assert decision["source"] == "quick_check"
    assert decision["quick_check_session_id"] == progress["calibration_session_id"]
    assert json.loads(decision["inputs_json"])["answers"][0]["clean_correct"] is True
    # Finishing again is a no-op.
    assert _progress(vault, repository, progress, 6)["quick_check"]["results"] == quick["results"]
    assert len(_decisions(paths)) == 1


def test_a_wrong_answer_decides_learning_and_k_caps_the_check(tmp_path):
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    session_id, progress = _start(vault, repository, ["lo_diag", "lo_eigen_basics", "lo_spectral"])
    served = []
    for minutes in (2, 4, 6, 8, 10):
        current = _progress(vault, repository, progress, minutes)
        target = current["next_target"]
        if target is None:
            break
        served.append(target["learning_object_id"])
        # Every answer is wrong: each LO is decided as learning after one answer.
        _answer(vault, repository, target["practice_item_id"], 0.0, minutes=minutes + 1, session_id=session_id)
    assert len(served) == len(set(served)) == 3  # a decided LO is never asked again
    done = _progress(vault, repository, progress, 12)
    assert done["quick_check"]["finished"]
    assert {r["verdict"] for r in done["quick_check"]["results"]} == {"learning"}
    assert _decisions(paths) == []


def test_k_answers_end_the_check(tmp_path):
    paths, vault, repository = _setup(tmp_path)  # default q: two answers never decide
    session_id, progress = _start(vault, repository, ["lo_diag", "lo_eigen_basics", "lo_spectral"])
    for minutes in (2, 3, 4, 5):
        target = _progress(vault, repository, progress, minutes)["next_target"]
        _answer(vault, repository, target["practice_item_id"], minutes=minutes, session_id=session_id)
    done = _progress(vault, repository, progress, 6)
    assert done["quick_check"]["answered"] == 4 and done["quick_check"]["finished"]
    assert done["next_target"] is None


def test_stop_still_feeds_the_split(tmp_path):
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    session_id, progress = _start(vault, repository, ["lo_diag", "lo_eigen_basics"])
    _answer_target(vault, repository, session_id, progress, 2)
    stop_calibration_session(repository, progress["calibration_session_id"], clock=_at(3))
    done = _progress(vault, repository, progress, 4)
    assert done["status"] == "stopped" and done["quick_check"]["finished"]
    verdicts = {r["learning_object_id"]: r["verdict"] for r in done["quick_check"]["results"]}
    assert verdicts == {"lo_diag": "undecided", "lo_eigen_basics": "undecided"}


def test_fast_track_waits_for_an_open_quick_check(tmp_path):
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    session_id, progress = _start(vault, repository, ["lo_diag", "lo_eigen_basics"])
    _answer(vault, repository, "pi_diag_hard", minutes=2, session_id=session_id)
    _answer(vault, repository, "pi_diag_mid", minutes=3, session_id=session_id)
    assert reconcile_fast_track(vault, repository, clock=_at(4)) == []


def test_quick_check_is_never_prompted(tmp_path):
    paths, vault, repository = _setup(tmp_path)
    session_id = repository.create_session(available_minutes=25, clock=_at(0))
    sync_vault_state(vault, repository, clock=_at(1))
    _queue(vault, repository, 2, session_id=session_id)
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM placement_quick_checks").fetchone() == (0,)
        assert connection.execute("SELECT COUNT(*) FROM probe_calibration_sessions").fetchone() == (0,)


def test_quick_check_needs_placement(tmp_path):
    paths, vault, repository = _setup(tmp_path, version="mvp-0.9")
    with pytest.raises(QuickCheckError):
        _start(vault, repository, ["lo_diag"])


def test_an_abandoned_quick_check_still_feeds_the_split_after_its_budget(tmp_path):
    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    session_id, progress = _start(vault, repository, ["lo_diag"])
    _answer_target(vault, repository, session_id, progress, 2)
    _answer_target(vault, repository, session_id, _progress(vault, repository, progress, 2.5), 3)
    # The learner never reopens the check. While it runs, fast-track waits.
    assert reconcile_fast_track(vault, repository, clock=_at(4)) == []
    # Past its 8-minute budget, the next queue build records its split once.
    reconcile_fast_track(vault, repository, clock=_at(20))
    assert [d["source"] for d in _decisions(paths)] == ["quick_check"]
    assert repository.probe_calibration_session(progress["calibration_session_id"]).status == "expired"
    reconcile_fast_track(vault, repository, clock=_at(30))
    assert len(_decisions(paths)) == 1


# ── Codex review fixes (slice-a-phase-6): exclusions, window, atomic start ───


def _best_item(vault, repository, los):
    predictor = active_predictor(vault, repository)
    weights = {lo: 1.0 for lo in los}
    candidates = sorted(i for i, item in vault.practice_items.items() if item.learning_object_id in weights)
    return sorted(candidates, key=lambda i: (-predictor.conditional_gain(i, [], weights), i))[0]


@pytest.mark.parametrize("kind", ["reserved", "held", "owned"])
def test_quick_check_never_presents_an_item_routine_serving_excludes(tmp_path, monkeypatch, kind):
    """F4: exam reservations, pending-variant holds and staged-controller
    ownership exclude an item from the quick check as from Today."""

    from learnloop.scheduling import controller_ownership

    paths, vault, repository = _setup(tmp_path)
    best = _best_item(vault, repository, ["lo_diag"])
    if kind == "reserved":
        repository.insert_exam_pool_items([{
            "id": "reservation-1", "goal_id": "goal-held-out", "practice_item_id": best,
            "reserved_at": "2026-05-19T12:00:00Z",
        }])
    elif kind == "held":
        monkeypatch.setattr(type(repository), "rung_variant_pending_source_ids", lambda self: {best})
    else:
        monkeypatch.setattr(
            controller_ownership, "staged_owned_practice_item_ids", lambda vault, repository: {best},
        )
    # Routine serving excludes it...
    assert best not in {s.practice_item_id for s in _queue(vault, repository, 0.5, persist=False)}
    # ...and so does the quick check, at every step.
    session_id, progress = _start(vault, repository, ["lo_diag"])
    presented = []
    for minutes in (2, 4, 6, 8):
        target = progress["next_target"]
        if target is None:
            break
        presented.append(target["practice_item_id"])
        _answer(vault, repository, target["practice_item_id"], 4.0, minutes=minutes, session_id=session_id)
        progress = _progress(vault, repository, progress, minutes + 0.5)
    assert presented and best not in presented


def _iso(value):
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


@pytest.mark.parametrize("kind", ["cold_reserved", "revealed", "adoption_off"])
def test_quick_check_skips_what_find_practice_skips_outside_the_schedulers_timing(tmp_path, monkeypatch, kind):
    """Merge with main: the check picks outside the scheduler's timing, like a
    Phase 5b ``find_practice`` proposal, so it reads the same shared
    exclusions: an open cold follow-up's reserved item (a single-use
    measurement), an item revealed within the cold retrieval delay, and a
    reference-adopted card while ``tutor_qa.adopt_reference_questions`` is off."""

    from datetime import timedelta

    from learnloop.practice_index.admission import PracticeAdmission
    from learnloop.vault import lifecycle

    from tests.helpers import NOW

    paths, vault, repository = _setup(tmp_path)
    best = _best_item(vault, repository, ["lo_diag"])
    if kind == "cold_reserved":
        repository.create_followup_task(
            kind="cold_retry", case_kind="diagnosis", case_ref="case-1",
            not_before=_iso(NOW + timedelta(days=2)), selected_item_id=best, clock=_at(0),
        )
        reason = "cold_check_reserved"
    elif kind == "revealed":
        repository.insert_reveal_event({
            "practice_item_id": best, "source_kind": "tutor_answer", "amount": 1.0,
            "created_at": _iso(NOW - timedelta(hours=2)),
        })
        reason = "revealed_recently"
    else:
        monkeypatch.setattr(lifecycle, "adopted_by_reference_sweep", lambda item: item.id == best)
        vault.config.tutor_qa.adopt_reference_questions = False
        reason = "reference_adoption_disabled"
    # find_practice would not propose it...
    admission = PracticeAdmission.load(vault, repository, clock=_at(1))
    assert admission.exclusion_reason(vault, vault.practice_items[best]) == reason
    # ...and the quick check never presents it.
    session_id, progress = _start(vault, repository, ["lo_diag"])
    presented = []
    for minutes in (2, 4, 6, 8):
        target = progress["next_target"]
        if target is None:
            break
        presented.append(target["practice_item_id"])
        _answer(vault, repository, target["practice_item_id"], 4.0, minutes=minutes, session_id=session_id)
        progress = _progress(vault, repository, progress, minutes + 0.5)
    assert presented and best not in presented


def test_an_abandoned_check_ignores_later_practice_in_the_same_session(tmp_path):
    """F5: answers after the check's budget boundary are ordinary practice."""

    from learnloop.placement.decisions import finalize_stale_quick_checks, quick_check_record

    paths, vault, repository = _setup(tmp_path, placement_toml=LOW_Q)
    session_id, progress = _start(vault, repository, ["lo_diag"], minutes=1)
    target = progress["next_target"]["practice_item_id"]
    other = next(i for i in ("pi_diag_easy", "pi_diag_mid", "pi_diag_hard") if i != target)
    # The learner walks away, then practises the same LO in the same session.
    _answer(vault, repository, target, minutes=20, session_id=session_id)
    _answer(vault, repository, other, minutes=21, session_id=session_id)
    finalize_stale_quick_checks(vault, repository, clock=_at(22))

    outcome = json.loads(quick_check_record(repository, progress["calibration_session_id"])["outcome_json"])
    assert outcome["answers"] == {}
    assert outcome["split"]["lo_diag"]["verdict"] == "undecided"
    assert [d for d in _decisions(paths) if d["source"] == "quick_check"] == []


def test_only_presented_answers_count_and_k_is_enforced_server_side(tmp_path):
    paths, vault, repository = _setup(tmp_path, placement_toml="[placement]\nquick_check_k = 2\n")
    session_id, progress = _start(vault, repository, ["lo_diag", "lo_eigen_basics"])
    target = progress["next_target"]["practice_item_id"]
    stray = next(
        item_id for item_id, item in sorted(vault.practice_items.items())
        if item.learning_object_id in {"lo_diag", "lo_eigen_basics"} and item_id != target
    )
    _answer(vault, repository, stray, minutes=2, session_id=session_id)  # never presented
    current = _progress(vault, repository, progress, 3)
    assert current["quick_check"]["answered"] == 0
    assert current["next_target"]["practice_item_id"] == target

    _answer_target(vault, repository, session_id, current, 4)
    second = _progress(vault, repository, progress, 5)
    _answer_target(vault, repository, session_id, second, 6)
    done = _progress(vault, repository, progress, 7)
    assert done["quick_check"]["finished"] and done["quick_check"]["answered"] == 2
    answered = {a["practice_item_id"] for r in done["quick_check"]["results"] for a in r["answers"]}
    assert stray not in answered and len(answered) == 2
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM placement_quick_check_items").fetchone() == (2,)


def test_interrupted_creation_leaves_no_orphan_and_a_retry_recovers_the_check(tmp_path, monkeypatch):
    """F7: the calibration session and the quick-check row commit together, and
    a retried start with the same request id returns the same check."""

    from learnloop.diagnosis import quick_check as quick_check_module

    paths, vault, repository = _setup(tmp_path)
    session_id = repository.create_session(available_minutes=25, clock=_at(0))
    original = quick_check_module.insert_quick_check

    def crash(*args, **kwargs):
        raise RuntimeError("the process died between the two inserts")

    monkeypatch.setattr(quick_check_module, "insert_quick_check", crash)
    with pytest.raises(RuntimeError):
        start_quick_check(vault, repository, session_id=session_id, learning_object_ids=["lo_diag"], clock=_at(1))
    assert repository.active_probe_calibration_session(session_id) is None

    monkeypatch.setattr(quick_check_module, "insert_quick_check", original)
    first = start_quick_check(
        vault, repository, session_id=session_id, learning_object_ids=["lo_diag"], request_id="req-1", clock=_at(2),
    )
    retry = start_quick_check(
        vault, repository, session_id=session_id, learning_object_ids=["lo_diag"], request_id="req-1", clock=_at(3),
    )
    assert retry["calibration_session_id"] == first["calibration_session_id"]
    assert retry["next_target"] == first["next_target"]
    with sqlite3.connect(paths.sqlite_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM placement_quick_checks").fetchone() == (1,)
        assert connection.execute("SELECT COUNT(*) FROM probe_calibration_sessions").fetchone() == (1,)
