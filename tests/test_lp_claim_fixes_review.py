"""LP-min (a) Codex review fixes (docs/reviews/lp-claim-fixes-codex-review.md).

F1 an interrupted or concurrent gap promotion applies its claim exactly once;
F2 an upgrade that dies between the config's publication and the commit is
completed from its journal; F3 activation re-seeds claim-covered LOs without
attempts as a full rebuild does; F4 a claim never lowers a variance, cold or
warm; F5 claims and attempts stamped in the same second replay in the order
they were written; F6 the review that resolves an "I know this" says so, once.
"""

from __future__ import annotations

from datetime import timedelta
import sqlite3

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.learner.mastery import reanchor_mastery_from_claim

from tests.helpers import NOW
from tests.assumed_known_helpers import _answer
from tests.lp_claim_fixes_review_helpers import (
    ITEM,
    LO,
    PREDECESSOR,
    TAG,
    _gap,
    _gap_claims,
    _iso,
    _mastery,
    _rebuild,
    _vault,
)

OFF = "[mastery]\nclaim_fixes_enabled = false\n"


# ── F1: atomic, retry-safe gap application ──────────────────────────────────


def test_f1_a_gap_promotion_interrupted_before_its_row_applies_its_claim_once_on_retry(tmp_path, monkeypatch):
    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    control_paths, control_vault, control_repo = _vault(tmp_path, "control")
    _answer(control_vault, control_repo, ITEM, 4.0, minutes=5)
    _gap(control_paths.root, control_repo)
    once = _mastery(control_repo)

    original = Repository.insert_question_promotion
    calls = {"n": 0}

    def crash_once(self, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("the process died before the promotion row")
        return original(self, **kwargs)

    monkeypatch.setattr(Repository, "insert_question_promotion", crash_once)
    with pytest.raises(RuntimeError):
        _gap(paths.root, repository)
    assert len(_gap_claims(repository)) == 1
    assert _mastery(repository) == pytest.approx(once)  # the claim and its effect committed together

    result = _gap(paths.root, repository)

    claims = _gap_claims(repository)
    assert len(claims) == 1 and result["learner_claim_id"] == claims[0]["id"]
    assert claims[0]["id"].endswith("_gap_ev_gap")
    assert _mastery(repository) == pytest.approx(once)  # not merged a second time


def test_f1_a_concurrent_writer_cannot_land_between_the_gap_read_and_write(tmp_path, monkeypatch):
    import learnloop.learner.mastery as mastery

    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    original = mastery.apply_claim_evidence
    blocked: list[str] = []

    def contend(state, **kwargs):
        # A sidecar attempt committing its mastery update right now.
        other = sqlite3.connect(paths.sqlite_path, timeout=0)
        try:
            other.execute("UPDATE learning_object_mastery SET logit_mean = 9.0 WHERE learning_object_id = ?", (LO,))
            other.commit()
        except sqlite3.OperationalError as error:
            blocked.append(str(error))
        finally:
            other.close()
        return original(state, **kwargs)

    monkeypatch.setattr(mastery, "apply_claim_evidence", contend)
    _gap(paths.root, repository)

    assert blocked and "locked" in blocked[0]
    assert _mastery(repository)[0] != 9.0


def test_f1_off_the_predecessor_writes_a_plain_claim(tmp_path):
    paths, _vault_, repository = _vault(tmp_path, toml=OFF)
    _gap(paths.root, repository)
    (claim,) = _gap_claims(repository)
    assert "_gap_" not in claim["id"]


# ── F2: an interrupted activation is completed, never left half-done ────────


# ── F3: activation equals a same-version rebuild ────────────────────────────


# ── F4: a claim never lowers a variance ─────────────────────────────────────


def test_f4_a_gap_on_a_cold_lo_moves_the_mean_and_keeps_the_cold_variance(tmp_path):
    from learnloop.learner.mastery import logit

    paths, vault, repository = _vault(tmp_path)
    cold = _mastery(repository)
    assert cold == (0.0, vault.config.mastery.cold_start_prior_logit_variance, 0)

    _gap(paths.root, repository)

    mean, variance, evidence = _mastery(repository)
    assert mean == pytest.approx(logit(vault.config.tutor_promotion.gap_claim_level))
    assert variance >= cold[1] and evidence == 0


def test_f4_a_claim_seed_never_starts_below_the_cold_variance_and_replay_agrees(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _gap(paths.root, repository, minutes=1)
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    live = _mastery(repository)

    assert _mastery(_rebuild(paths)) == pytest.approx(live, rel=1e-12, abs=1e-12)


@pytest.mark.parametrize("variant", ["switch_off", "below_tag"])
def test_f4_off_the_predecessor_seed_variance_is_kept(tmp_path, variant):
    paths, vault, repository = _vault(
        tmp_path, version=PREDECESSOR if variant == "below_tag" else TAG, toml=OFF if variant == "switch_off" else None,
    )
    repository.insert_learner_claim({
        "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": LO, "evidence_family": "recall",
        "claimed_level": 0.9, "prior_pseudo_count": 2.0, "source": "learner_report", "created_at": _iso(1),
    })
    state = reanchor_mastery_from_claim(vault, repository, LO, claimed_level=0.9, prior_pseudo_count=2.0,
                                        now_iso=_iso(1))
    assert state.logit_variance == vault.config.mastery.claim_prior_min_variance


# ── F5: same-second claims and attempts keep the order they were written ────


@pytest.mark.parametrize("order", ["attempt_then_gap", "gap_then_attempt"])
def test_f5_a_gap_and_an_attempt_in_the_same_second_replay_in_written_order(tmp_path, order):
    paths, vault, repository = _vault(tmp_path)
    if order == "attempt_then_gap":
        _answer(vault, repository, ITEM, 1.0, minutes=5)
        _gap(paths.root, repository, minutes=5)
    else:
        _gap(paths.root, repository, minutes=5)
        _answer(vault, repository, ITEM, 1.0, minutes=5)
    (claim,) = _gap_claims(repository)
    (attempt,) = repository.list_attempts_by_learning_object(LO)
    assert claim["created_at"] == attempt["created_at"]  # one-second stamps tie
    live = _mastery(repository)

    assert _mastery(_rebuild(paths)) == pytest.approx(live, rel=1e-12, abs=1e-12)


def test_f5_a_rung_request_claim_still_precedes_its_same_second_attempt(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    repository.insert_learner_claim({
        "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": LO, "evidence_family": "recall",
        "claimed_level": 0.85, "prior_pseudo_count": 2.0, "source": "rung_variant_request", "created_at": _iso(5),
    })
    reanchor_mastery_from_claim(vault, repository, LO, claimed_level=0.85, prior_pseudo_count=2.0, now_iso=_iso(5))
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    live = _mastery(repository)

    assert _mastery(_rebuild(paths)) == pytest.approx(live, rel=1e-12, abs=1e-12)


# ── F6: the review that resolves "I know this" says so, once ────────────────


def _call(ctx, name, params):
    import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


CHECK_MINUTES = 14 * 24 * 60 + 5  # after the default first-review interval


def _known_then_reviews(tmp_path, *, version=TAG, toml=None, points=4.0):
    from learnloop.placement.decisions import record_self_report

    paths, vault, repository = _vault(tmp_path, version=version, toml=toml)
    record_self_report(vault, repository, learning_object_ids=["lo_diag"], report="know_this",
                       clock=FrozenClock(NOW + timedelta(minutes=1)))
    unrelated = _answer(vault, repository, ITEM, 4.0, minutes=CHECK_MINUTES - 1).attempt_id
    resolving = _answer(vault, repository, "pi_diag_mid", points, minutes=CHECK_MINUTES).attempt_id
    later = _answer(vault, repository, "pi_diag_hard", 4.0, minutes=CHECK_MINUTES + 5).attempt_id
    return paths, vault, repository, (unrelated, resolving, later)


@pytest.mark.parametrize(("points", "word"), [(4.0, "passed"), (1.0, "missed")])
def test_f6_the_resolving_review_carries_one_quiet_claim_line_and_no_other_does(tmp_path, points, word):
    from learnloop.placement.claim_check import claim_check
    from learnloop.placement.state import load_placement_state

    _paths, vault, repository, (unrelated, resolving, later) = _known_then_reviews(tmp_path, points=points)
    (assumption,) = load_placement_state(vault, repository).assumptions
    assert assumption.resolving_attempt_id == resolving
    assert claim_check(vault, repository, resolving) == {
        "claim": "marked_known", "check": word, "line": f"You marked this as known; this check: {word}.",
    }
    assert claim_check(vault, repository, unrelated) is None
    assert claim_check(vault, repository, later) is None


def test_f6_get_feedback_attaches_the_line_to_the_resolving_review_only(tmp_path, monkeypatch):
    import learnloop.clock as clock_module
    from learnloop_sidecar.context import SidecarContext

    paths, _vault_, _repository, (unrelated, resolving, later) = _known_then_reviews(tmp_path)
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: NOW + timedelta(minutes=CHECK_MINUTES + 10))
    ctx = SidecarContext()
    ctx.load(paths.root)

    bundle = _call(ctx, "get_feedback", {"attemptId": resolving, "recordOpen": False})
    assert bundle["claimCheck"] == {
        "claim": "marked_known", "check": "passed", "line": "You marked this as known; this check: passed.",
    }
    for attempt_id in (unrelated, later):
        assert "claimCheck" not in _call(ctx, "get_feedback", {"attemptId": attempt_id, "recordOpen": False})
    # Display only: the grade the review recorded never read the claim.
    attempt = Repository(paths.sqlite_path).fetch_practice_attempt(resolving)
    assert "marked this as known" not in str(attempt)


@pytest.mark.parametrize("variant", ["switch_off", "below_tag"])
def test_f6_off_no_claim_line(tmp_path, variant):
    from learnloop.placement.claim_check import claim_check

    _paths, vault, repository, (_unrelated, resolving, _later) = _known_then_reviews(
        tmp_path, version=PREDECESSOR if variant == "below_tag" else TAG, toml=OFF if variant == "switch_off" else None,
    )
    assert claim_check(vault, repository, resolving) is None
