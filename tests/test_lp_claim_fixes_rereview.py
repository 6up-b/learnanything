"""LP-min (a) Codex re-review (docs/reviews/lp-claim-fixes-codex-review.md, "Re-review").

F2 an interrupted activation is completed by every opener that may write the
vault, and every other attach refuses it, so nothing serves the successor's
label over the predecessor's state; F7 a claim keeps its place among the
attempts it was applied between, also when an attempt's id was reserved before
the claim and its grade committed after it; F8 a zero-evidence LO keeps the
variance its earlier claims left, in a rebuild as live; F9 the review a
diagnosis timeout resolves carries its claim line when reopened after the
deadline.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.algorithm_versions import CLAIM_FIXES_ALGORITHM_VERSION as TAG
from learnloop.clock import FrozenClock
from learnloop.ids import new_ulid
from learnloop.learner.mastery import reanchor_mastery_from_claim

from tests.helpers import NOW
from tests.assumed_known_helpers import _answer
from tests.lp_claim_fixes_review_helpers import (
    ITEM,
    LO,
    _gap,
    _gap_claims,
    _iso,
    _mastery,
    _rebuild,
    _vault,
)

# ── F2: completed at every opener that may write; refused by every other ────


# ── F7: the claim's place is where it was applied, not its id ───────────────


def _answer_with_reserved_id(vault, repository, monkeypatch, reserved, points, *, minutes):
    """An attempt whose id was minted before grading (production reserves it
    before the model call) and whose grade commits at ``minutes``."""

    import learnloop.attempts.attempts as attempts

    real = attempts.new_ulid
    handed = {"done": False}

    def reserved_first():
        if not handed["done"]:
            handed["done"] = True
            return reserved
        return real()

    monkeypatch.setattr(attempts, "new_ulid", reserved_first)
    try:
        result = _answer(vault, repository, ITEM, points, minutes=minutes)
    finally:
        monkeypatch.setattr(attempts, "new_ulid", real)
    assert result.attempt_id == reserved
    return result


def test_f7_an_attempt_reserved_before_a_gap_and_graded_after_it_replays_after_it(tmp_path, monkeypatch):
    paths, vault, repository = _vault(tmp_path)
    reserved = new_ulid()  # the attempt's id, minted when grading started
    _gap(paths.root, repository, minutes=5)  # the gap commits while grading runs
    _answer_with_reserved_id(vault, repository, monkeypatch, reserved, 1.0, minutes=5)

    (claim,) = _gap_claims(repository)
    (attempt,) = repository.list_attempts_by_learning_object(LO)
    # The order the review describes: one stamp, the attempt's id first.
    assert claim["created_at"] == attempt["created_at"] and attempt["id"] < claim["id"]
    live = _mastery(repository)

    assert _mastery(_rebuild(paths)) == pytest.approx(live, rel=1e-12, abs=1e-12)


def test_f7_the_claim_records_how_many_of_its_los_attempts_it_was_applied_after(tmp_path, monkeypatch):
    """With an earlier attempt: the raced vault rebuilds as the unraced one does.

    (Two attempts on one LO do not rebuild to their live row in this harness
    whatever the claims, so the raced rebuild is compared with the rebuild of
    the same history whose second attempt's id was minted after the gap.)"""

    rebuilt = {}
    for race in (True, False):
        paths, vault, repository = _vault(tmp_path, f"race_{race}")
        _answer(vault, repository, ITEM, 4.0, minutes=1)
        reserved = new_ulid()
        _gap(paths.root, repository, minutes=5)
        if race:
            _answer_with_reserved_id(vault, repository, monkeypatch, reserved, 1.0, minutes=5)
        else:
            _answer(vault, repository, ITEM, 1.0, minutes=5)
        (claim,) = _gap_claims(repository)
        assert claim["applied_after_attempts"] == 1
        rebuilt[race] = _mastery(_rebuild(paths))

    assert rebuilt[True] == pytest.approx(rebuilt[False], rel=1e-12, abs=1e-12)


@pytest.mark.parametrize("writer", ["too_easy_report", "rung_variant_request"])
def test_f7_every_reanchoring_writer_records_its_point(tmp_path, writer):
    paths, vault, repository = _vault(tmp_path)
    _answer(vault, repository, ITEM, 4.0, minutes=1)
    item = vault.practice_items[ITEM]
    clock = FrozenClock(NOW + timedelta(minutes=2))
    if writer == "too_easy_report":
        from learnloop.content.authoring.item_authoring import _apply_difficulty_report as report

        report(vault, repository, item, reason="too_easy", clock=clock)
        source = "learner_report"
    else:
        from learnloop.content.authoring.rung_variants import CLAIM_SOURCE

        _request_rung_variant(paths, vault, repository, item, clock)
        source = CLAIM_SOURCE
    (claim,) = [row for row in repository.learner_claims() if row["source"] == source]
    assert claim["applied_after_attempts"] == 1


def _request_rung_variant(paths, vault, repository, item, clock):
    from learnloop.content.authoring.rung_variants import request_rung_variant

    request_rung_variant(vault, repository, practice_item_id=item.id, direction="harder", clock=clock)


def test_f7_off_the_claim_records_nothing(tmp_path):
    paths, _vault_, repository = _vault(tmp_path, toml="[mastery]\nclaim_fixes_enabled = false\n")
    _gap(paths.root, repository, minutes=5)
    (claim,) = _gap_claims(repository)
    assert claim["applied_after_attempts"] is None


# ── F8: a zero-evidence LO keeps the variance its earlier claims left ───────


def _claim(vault, repository, *, source, pseudo_count, minutes, level=0.3):
    claim_id = repository.insert_learner_claim({
        "claim_type": "self_rating", "scope_type": "learning_object", "scope_id": LO, "evidence_family": "recall",
        "claimed_level": level, "prior_pseudo_count": pseudo_count, "source": source, "created_at": _iso(minutes),
    })
    return reanchor_mastery_from_claim(
        vault, repository, LO, claimed_level=level, prior_pseudo_count=pseudo_count, now_iso=_iso(minutes),
        claim_id=claim_id,
    )


def test_f8_two_claims_with_differing_pseudo_counts_keep_the_weak_claims_variance_in_a_rebuild(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    weak = _claim(vault, repository, source="learner_report", pseudo_count=0.25, minutes=1)
    assert weak.logit_variance == pytest.approx(4.0)
    later = _claim(vault, repository, source="rung_variant_request", pseudo_count=2.0, minutes=2, level=0.7)
    assert later.logit_variance == pytest.approx(4.0)  # live keeps the retained uncertainty
    live = _mastery(repository)

    assert _mastery(_rebuild(paths)) == pytest.approx(live, rel=1e-12, abs=1e-12)


def test_f8_the_first_replayed_attempt_starts_from_the_retained_variance(tmp_path):
    paths, vault, repository = _vault(tmp_path)
    _claim(vault, repository, source="learner_report", pseudo_count=0.25, minutes=1)
    _claim(vault, repository, source="rung_variant_request", pseudo_count=2.0, minutes=2, level=0.7)
    _answer(vault, repository, ITEM, 4.0, minutes=5)
    live = _mastery(repository)

    assert _mastery(_rebuild(paths)) == pytest.approx(live, rel=1e-12, abs=1e-12)


# ── F9: a timeout-resolved review carries its line when reopened ────────────


def test_f9_a_miss_the_diagnosis_timeout_decides_carries_its_line_reopened_after_the_deadline(tmp_path, monkeypatch):
    import learnloop.clock as clock_module
    from learnloop.placement.claim_check import claim_check
    from learnloop.placement.decisions import record_self_report
    from learnloop.placement.rules import DIAGNOSIS_WAIT_DAYS
    from learnloop.placement.state import load_placement_state

    from tests.diagnosis_split_helpers import at
    from tests.split_live_helpers import drain_jobs, split_vault
    from tests.placement_diagnosis_decides_helpers import DUE_HOURS, LO as SPLIT_LO, _Diagnosed, _miss

    _paths, vault, repository = split_vault(tmp_path, version=TAG, seed=False)
    record_self_report(vault, repository, learning_object_ids=[SPLIT_LO], report="know_this", clock=FrozenClock(at(0)))
    miss = _miss(vault, repository, _Diagnosed(), drain=False)
    # The provider never comes: the diagnose job stays queued.
    drain_jobs(vault, repository, None, clock=FrozenClock(at(DUE_HOURS + 2)))
    deadline_hours = DUE_HOURS + 1 + 24 * DIAGNOSIS_WAIT_DAYS

    def now(hours):
        monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: at(hours))

    now(deadline_hours - 1)
    assert claim_check(vault, repository, miss.attempt_id) is None  # still waiting on the diagnosis

    now(deadline_hours + 1)
    (assumption,) = load_placement_state(vault, repository).assumptions
    assert (assumption.status, assumption.resolving_attempt_id) == ("failed", miss.attempt_id)
    assert claim_check(vault, repository, miss.attempt_id) == {
        "claim": "marked_known", "check": "missed", "line": "You marked this as known; this check: missed.",
    }
