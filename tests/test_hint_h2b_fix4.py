"""Adaptive hints H2b, fix round 4 (docs/reviews/hints-h2b-codex-review.md): the orchestrator's rulings on F12-F14.

F12: a hint delivered while a workbench submit is being graded is counted
and taken by the attempt's transactional refold. The submit's admission time
goes with the fold, so that row gets its ``submitted_at`` too (the first
stamp stays, no latency). F13: an interrupted placement stops the vault-open
pass at once, and a failure that may follow a model call counts against
``RECONCILE_LIMIT``. F14: a placement judges each hint against the map
recorded on its own row, never against today's map. When that map cannot
judge it (the item was revised since), the hint gets a terminal ``unknown``
(``map_changed``) and no call is made. Fakes only.
"""

from __future__ import annotations

import json
import time

from learnloop.ai.errors import AIInterrupted
from learnloop.db.repositories import Repository
from learnloop.hints import map_builder, outcome
from learnloop.hints.outcome import place_outcome
from learnloop.vault.loader import load_vault
from learnloop_sidecar.handlers import practice
from tests.approach_map_fakes import write_item
from tests.hint_fakes import ITEM, WORK, assists, judgments, receipts, store_map
from tests.test_hint_h2a_review_round2 import _two_sidecars
from tests.test_hint_h2b_review import (  # noqa: F401 - ``grader`` is a fixture
    _attempt,
    _call,
    _hinted_wrong_attempt,
    _report,
    _sidecar,
    grader,
)
from tests.test_hint_outcome import OutcomeFake


# -- F12: a hint delivered during grading keeps its submit time ----------------------------------


def test_f12_a_hint_delivered_during_a_workbench_grade_is_stamped_when_the_attempt_takes_it(
        tmp_path, grader, monkeypatch):
    # Sidecar B wrote a hint under the answer box's key (not yet read); A
    # opens the problem and submits it.
    paths, a, b, session, job = _two_sidecars(tmp_path, "next_step@L3")
    view = _call(a, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                       "stemMd": "Find P."})["session"]
    _call(a, "workbench.save_step", {"sessionId": view["sessionId"], "clientIdempotencyKey": "s1", "op": "add",
                                     "bodyMd": WORK})
    stamp = practice._stamp_window_hints
    delivered: dict = {}

    def stamp_then_deliver(*args, **kwargs):
        stamp(*args, **kwargs)
        # Admitted and stamped; while it is graded, B delivers the hint.
        delivered["result"] = _call(b, "practice.hint_job", {"jobId": job})["result"]

    monkeypatch.setattr(practice, "_stamp_window_hints", stamp_then_deliver)
    attempt = _attempt(paths, _call(a, "workbench.submit", {
        "sessionId": view["sessionId"], "practiceSessionId": session})["attempt"]["attemptId"])
    assert delivered["result"]["shown"] is True
    assert attempt["hints_used"] == 1
    [row] = assists(paths.sqlite_path)
    assert row["attempt_id"] == attempt["id"]
    # The refold took it, and stamped it with the submit's admission time.
    assert row["submitted_at"] is not None
    assert row["submitted_at"] <= attempt["created_at"]
    assert row["submit_latency_seconds"] is None
    [kind] = [entry for entry in _report(paths)["kinds"] if entry["hint_kind"] == "next_step"]
    assert kind["timing_unknown"] == 0
    assert kind["seconds_into_attempt_unknown"]["no_submit_latency"] == 1


# -- F13: the vault-open pass and interrupted or failed placements --------------------------------


def _backlog(tmp_path, count):
    paths, ctx, session = _sidecar(tmp_path)
    attempts = []
    for index in range(count):
        if index:
            time.sleep(1.05)  # a later second: the next hint is not closed by this attempt
        attempts.append(_hinted_wrong_attempt(ctx, session, f"k{index}"))
    assert outcome.unplaced_attempts(paths.sqlite_path, since="2000-01-01T00:00:00Z") == attempts
    return paths


def _reconcile(paths, *, limit):
    registry = map_builder.BackgroundBuilds(drain_seconds=5.0)
    registry.bind(paths.sqlite_path)
    results: list = []
    thread = outcome.reconcile_outcome_placements(load_vault(paths.root), paths.sqlite_path, client=OutcomeFake(),
                                                  builds=registry, limit=limit, on_done=results.append)
    assert thread is not None
    thread.join(30)
    return results


def test_f13_an_interrupted_placement_stops_the_pass_at_once(tmp_path, monkeypatch):
    paths = _backlog(tmp_path, 3)
    calls: list[str] = []

    def interrupted(vault, repository, attempt_id, **kwargs):
        calls.append(attempt_id)
        raise AIInterrupted("the turn was interrupted")

    monkeypatch.setattr(outcome, "place_outcome", interrupted)
    results = _reconcile(paths, limit=20)
    assert len(calls) == 1
    assert [result.status for result in results] == ["interrupted"]


def test_f13_failures_that_may_follow_a_call_never_exceed_the_bound(tmp_path, monkeypatch):
    paths = _backlog(tmp_path, 4)
    calls: list[str] = []

    def failing(vault, repository, attempt_id, **kwargs):
        calls.append(attempt_id)
        raise RuntimeError("after the call")

    monkeypatch.setattr(outcome, "place_outcome", failing)
    results = _reconcile(paths, limit=2)
    assert len(calls) == 2
    assert [result.status for result in results] == ["failed", "failed"]


# -- F14: the map recorded on the hint ----------------------------------------------------------


def _revise_and_rebuild(paths):
    write_item(paths, prompt="X has density f(x) = 2x on [0, 1]. Find P(X ≤ 1/2) exactly.")
    return store_map(paths)


def test_f14_reconcile_after_a_revision_never_judges_a_hint_against_the_new_map(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    # The placement after this submit never ran (a process that ended).
    attempt_id = _hinted_wrong_attempt(ctx, session, "k1")
    [hint] = [row for row in assists(paths.sqlite_path) if row["shown"]]
    new_map = _revise_and_rebuild(paths)
    assert new_map != hint["map_id"]
    fake = OutcomeFake()
    registry = map_builder.BackgroundBuilds(drain_seconds=5.0)
    registry.bind(paths.sqlite_path)
    results: list = []
    thread = outcome.reconcile_outcome_placements(load_vault(paths.root), paths.sqlite_path, client=fake,
                                                  builds=registry, on_done=results.append)
    assert thread is not None
    thread.join(30)
    # No call, and no verdict computed against the new map: a terminal unknown.
    assert fake.calls == 0 and receipts(paths.sqlite_path, "hint_outcome") == []
    assert [result.status for result in results] == ["map_changed"]
    [verdict] = judgments(paths.sqlite_path, "hint_outcome")
    rationale = json.loads(verdict["rationale"])
    assert (verdict["verdict"], verdict["judge"], verdict["right_id"]) == ("unknown", "verifier", attempt_id)
    assert rationale["reason"] == "map_changed" and rationale["map_id"] is None
    assert rationale["hint_map_id"] == hint["map_id"]
    # Terminal: the next open has nothing left to look at.
    assert outcome.unplaced_attempts(paths.sqlite_path, since="2000-01-01T00:00:00Z") == []


def test_f14_the_immediate_placement_follows_the_same_rule(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    attempt_id = _hinted_wrong_attempt(ctx, session, "k1")
    _revise_and_rebuild(paths)
    fake = OutcomeFake()
    result = place_outcome(load_vault(paths.root), Repository.attach(paths.sqlite_path), attempt_id, client=fake)
    assert (result.status, fake.calls) == ("map_changed", 0)
    [verdict] = judgments(paths.sqlite_path, "hint_outcome")
    assert json.loads(verdict["rationale"])["reason"] == "map_changed"


def test_f14_a_hint_is_placed_on_its_own_map_when_a_newer_one_exists_for_another_revision(tmp_path):
    # The item revised and back: the hint's own map is still the current
    # revision's, though a newer version (of the other revision) exists.
    paths, ctx, session = _sidecar(tmp_path)
    attempt_id = _hinted_wrong_attempt(ctx, session, "k1")
    [hint] = [row for row in assists(paths.sqlite_path) if row["shown"]]
    _revise_and_rebuild(paths)
    write_item(paths)  # the original revision again
    fake = OutcomeFake()
    result = place_outcome(load_vault(paths.root), Repository.attach(paths.sqlite_path), attempt_id, client=fake)
    assert (result.status, fake.calls) == ("placed", 1)
    [verdict] = judgments(paths.sqlite_path, "hint_outcome")
    assert json.loads(verdict["rationale"])["map_id"] == hint["map_id"]
