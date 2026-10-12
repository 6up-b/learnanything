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

    _answer(vault, repository, "pi_diag_hard", minutes=2, session_id=session_id)
    middle = _progress(vault, repository, progress, 3)
    assert middle["quick_check"]["answered"] == 1 and middle["quick_check"]["results"] is None
    assert middle["status"] == "active"

    _answer(vault, repository, "pi_diag_mid", minutes=4, session_id=session_id)
    done = _progress(vault, repository, progress, 5)
    # Early stop: the only LO is decided after two clean answers.
    assert done["status"] == "completed" and done["next_target"] is None
    quick = done["quick_check"]
    assert quick["finished"] and quick["answered"] == 2
    (result,) = quick["results"]
    assert result["verdict"] == "assumed"
    assert [answer["practice_item_id"] for answer in result["answers"]] == ["pi_diag_hard", "pi_diag_mid"]
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
    _answer(vault, repository, "pi_diag_hard", minutes=2, session_id=session_id)
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
    _answer(vault, repository, "pi_diag_hard", minutes=2, session_id=session_id)
    _answer(vault, repository, "pi_diag_mid", minutes=3, session_id=session_id)
    # The learner never reopens the check. While it runs, fast-track waits.
    assert reconcile_fast_track(vault, repository, clock=_at(4)) == []
    # Past its 8-minute budget, the next queue build records its split once.
    reconcile_fast_track(vault, repository, clock=_at(20))
    assert [d["source"] for d in _decisions(paths)] == ["quick_check"]
    assert repository.probe_calibration_session(progress["calibration_session_id"]).status == "expired"
    reconcile_fast_track(vault, repository, clock=_at(30))
    assert len(_decisions(paths)) == 1
