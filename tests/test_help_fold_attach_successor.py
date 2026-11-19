"""Follow-ups Nov 2 (b) as the successor mvp-0.42 (Codex review F1; built as mvp-0.41 and renumbered
at its landing after teacher TE1's mvp-0.41, ruling R4;
docs/reviews/followups-nov2-codex-review.md; docs/algorithm-change-playbook.md,
the 2026-10-17 rule: a change to which new attempts are primed is a successor
with a kill switch even when replay is unchanged).

* the tag is ONE constant after mvp-0.41 and the latest (its kill switch went
  once every vault was past the tag);
* a keyed submit's fold counts the key's rows in any session and the attempt
  takes them in its own transaction, so the session rollover case is counted
  (levels 1-3) or primes (levels 4-5);
* replay re-applies the stored counts (a rebuild changes no attempt) and a
  shadow rebuild is 0/0/0;
* the upgrade is the chain's next journalled link (from its predecessor, or mvp-0.9
  onwards through the chain; from mvp-0.41 now), and the next command completes an interrupted
  activation.

Fakes only; no model call.
"""

from __future__ import annotations



from learnloop.algorithm_versions import (
    HELP_FOLD_ATTACH_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    TEACHER_ALGORITHM_VERSION,
)
from learnloop.vault.loader import load_vault
from tests.hint_fakes import assists
from tests.followups_nov2_help_fold_helpers import _rollover, _submit
from tests.hint_h2a_review_round2_helpers import ARGMAX, _attempt

TAG = HELP_FOLD_ATTACH_ALGORITHM_VERSION
PREDECESSOR = TEACHER_ALGORITHM_VERSION


def test_mvp042_is_one_constant_after_mvp041_and_the_latest():
    # Teacher TE1b's mvp-0.43 follows it as the latest (and keeps it).
    assert SUCCESSOR_CHAIN[-21:-19] == (PREDECESSOR, TAG) == ("mvp-0.41", "mvp-0.42")
    assert LATEST_ALGORITHM_VERSION == SUCCESSOR_CHAIN[-1] == "mvp-0.61"


def _rolled(tmp_path, *, version: str, config: str = ARGMAX, option: str = "next_step@L3"):
    """The session rollover case at ``version``: a hint shown under ``k1`` in
    an ended session, the same key submitted in a new one."""

    return _rollover(tmp_path, config=config, option=option, version=version)


def test_the_rollover_hint_is_counted_and_attached_in_the_attempts_transaction(tmp_path, monkeypatch):
    """F1: the rollover hint is counted, and the attempt takes it in its own
    transaction (H0's attach after the commit is disabled here)."""

    from learnloop_sidecar.handlers import practice as practice_handlers

    paths, ctx, _first, second = _rolled(tmp_path, version=TAG)
    monkeypatch.setattr(practice_handlers, "_attach_hint_reveals", lambda *args, **kwargs: None)
    result = _submit(ctx, second)
    [row] = assists(paths.sqlite_path)
    assert _attempt(paths, result["attemptId"])["hints_used"] == 1
    assert row["attempt_id"] == result["attemptId"]


def test_worked_help_on_the_rollover_primes(tmp_path):
    paths, ctx, _first, second = _rolled(tmp_path, version=TAG, option="worked_chunk@L4")
    result = _submit(ctx, second)
    attempt = _attempt(paths, result["attemptId"])
    [row] = assists(paths.sqlite_path)
    assert attempt["primed"] == 1 and attempt["hints_used"] == 0
    # H0's attach still binds the key's row after the commit, at every version.
    assert row["attempt_id"] == result["attemptId"]


def test_a_same_session_keyed_hint_is_counted_and_attached(tmp_path):
    from tests.hint_fakes import store_map
    from tests.followups_nov2_help_fold_helpers import _hinted_session, hint_vault
    from tests.hint_h2a_review_round2_helpers import _context

    paths = hint_vault(tmp_path / "on", config=ARGMAX)
    store_map(paths)
    ctx = _context(paths, inline=True)
    session = _hinted_session(paths, ctx)
    result = _submit(ctx, session)
    [row] = assists(paths.sqlite_path)
    assert (_attempt(paths, result["attemptId"])["hints_used"], row["attempt_id"] == result["attemptId"]) == (1, True)


def test_a_rebuild_changes_no_attempt_and_a_shadow_rebuild_is_zero(tmp_path):
    """Replay re-applies the stored ``hints_used`` and ``primed`` (it never
    folds), so the successor's counts survive a rebuild and the shadow
    rebuild shows no mastery, facet or schedule delta."""

    from learnloop.db.repositories import Repository
    from learnloop.substrate.replay import rebuild_derived_state
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    paths, ctx, _first, second = _rolled(tmp_path, version=TAG, option="worked_chunk@L4")
    result = _submit(ctx, second)
    before = dict(_attempt(paths, result["attemptId"]))
    ctx.close()
    shadow = shadow_rebuild(load_vault(paths.root))
    assert shadow.live_database_unchanged
    assert shadow.learner_state_diff["summary"] == {"mastery": 0, "facet": 0, "schedule": 0}
    rebuild_derived_state(load_vault(paths.root), Repository.attach(paths.sqlite_path))
    after = dict(_attempt(paths, result["attemptId"]))
    assert (after["hints_used"], after["primed"]) == (before["hints_used"], before["primed"])


# -- the chain and the upgrade -------------------------------------------------------------------------
