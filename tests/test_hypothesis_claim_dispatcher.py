"""B1 dispatcher policy matrix (spec §2.4): budget, hot-slot reservation,
cooldown, debounce, changed-version re-presentation, cold re-ask limits."""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.hypothesis_claims import (
    HypothesisClaimError,
    present_claims,
    record_response,
)

from tests.helpers import NOW, create_basic_vault


def _candidate(ref, *, temperature="cold", claim_type="ready_estimate", version="v1", **extra):
    claim_class = {
        "ready_estimate": "estimate",
        "forecast": "estimate",
        "misconception": "diagnosis",
        "schedule_choice": "policy",
        "regrade": "ledger_fact",
    }[claim_type]
    return {
        "claim_class": claim_class,
        "claim_type": claim_type,
        "claim_ref": ref,
        "claim_version": version,
        "producer_version": "mvp-0.7",
        "surface": "today",
        "temperature": temperature,
        **extra,
    }


def _repository(tmp_path) -> Repository:
    paths = create_basic_vault(tmp_path / "vault")
    return Repository(paths.sqlite_path)


def test_cold_claims_never_take_the_reserved_hot_slot(tmp_path):
    repository = _repository(tmp_path)
    results = present_claims(
        repository,
        [_candidate("c1"), _candidate("c2"), _candidate("c3")],
        session_id="s1",
        clock=FrozenClock(NOW),
    )
    enabled = [r for r in results if r["affordances_enabled"]]
    suppressed = [r for r in results if not r["affordances_enabled"]]
    # Budget 2 with one slot reserved for temperature='hot': cold claims can
    # occupy at most one slot even when nothing hot has arrived yet.
    assert len(enabled) == 1
    assert len(suppressed) == 2
    assert {r["suppression_reason"] for r in suppressed} == {"session_card_budget"}


def test_hot_claim_lands_after_cold_budget_is_exhausted(tmp_path):
    repository = _repository(tmp_path)
    present_claims(
        repository,
        [_candidate("c1"), _candidate("c2")],
        session_id="s1",
        clock=FrozenClock(NOW),
    )
    hot = present_claims(
        repository,
        [_candidate("m1", temperature="hot", claim_type="misconception")],
        session_id="s1",
        clock=FrozenClock(NOW),
    )[0]
    assert hot["affordances_enabled"] is True

    # The full budget (2) is now spent; a second hot claim is over budget and
    # renders as plain text with a suppression_reason.
    second_hot = present_claims(
        repository,
        [_candidate("m2", temperature="hot", claim_type="misconception")],
        session_id="s1",
        clock=FrozenClock(NOW),
    )[0]
    assert second_hot["affordances_enabled"] is False
    assert second_hot["suppression_reason"] == "session_card_budget"


def test_hot_claims_win_priority_within_one_dispatch(tmp_path):
    repository = _repository(tmp_path)
    results = present_claims(
        repository,
        [
            _candidate("cold_estimate"),
            _candidate("hot_diagnosis", temperature="hot", claim_type="misconception"),
        ],
        session_id="s1",
        clock=FrozenClock(NOW),
    )
    by_ref = {r["claim_ref"]: r for r in results}
    assert by_ref["hot_diagnosis"]["affordances_enabled"] is True


def test_responded_claim_cools_down_for_seven_days(tmp_path):
    repository = _repository(tmp_path)
    presented = present_claims(
        repository, [_candidate("c1")], session_id="s1", clock=FrozenClock(NOW)
    )[0]
    assert presented["affordances_enabled"] is True
    record_response(
        repository,
        presented["presentation_id"],
        {"response": "about_right"},
        clock=FrozenClock(NOW),
    )

    # Any response starts the per-claim cooldown (default 7 days): a fresh
    # session inside the window re-presents without affordances.
    inside = present_claims(
        repository, [_candidate("c1")], session_id="s2", clock=FrozenClock(NOW + timedelta(days=6))
    )[0]
    assert inside["affordances_enabled"] is False
    assert inside["suppression_reason"] == "claim_cooldown"

    after = present_claims(
        repository, [_candidate("c1")], session_id="s3", clock=FrozenClock(NOW + timedelta(days=8))
    )[0]
    assert after["affordances_enabled"] is True


def test_debounce_same_version_and_re_presentation_of_changed_version(tmp_path):
    repository = _repository(tmp_path)
    first = present_claims(
        repository, [_candidate("c1", version="v1")], session_id="s1", clock=FrozenClock(NOW)
    )[0]
    repeat = present_claims(
        repository, [_candidate("c1", version="v1")], session_id="s1", clock=FrozenClock(NOW)
    )[0]
    # Same (claim_ref, claim_version, surface, session): the existing
    # presentation row is returned, no second event is logged.
    assert repeat["debounced"] is True
    assert repeat["presentation_id"] == first["presentation_id"]
    presented_events = [
        event for event in repository.list_hypothesis_events() if event["event_type"] == "presented"
    ]
    assert len(presented_events) == 1

    # A materially changed claim_version is a NEW presentation within the same
    # session, not a suppressed duplicate (spec §2.2).
    changed = present_claims(
        repository, [_candidate("c1", version="v2")], session_id="s1", clock=FrozenClock(NOW)
    )[0]
    assert changed["debounced"] is False
    assert changed["presentation_id"] != first["presentation_id"]
    # v1 already holds the session's only cold slot, so the re-presentation is
    # budget-suppressed — but it is logged as a new presentation, never as a
    # debounced duplicate.
    assert changed["suppression_reason"] == "session_card_budget"
    presented_versions = [
        event["claim_version"]
        for event in repository.list_hypothesis_events()
        if event["event_type"] == "presented"
    ]
    assert sorted(presented_versions) == ["v1", "v2"]


def test_at_most_one_cold_reask_per_log_visit(tmp_path):
    repository = _repository(tmp_path)
    # Both diagnosis claims were answered hot, so both are inside cooldown.
    for ref in ("m1", "m2"):
        presented = present_claims(
            repository,
            [_candidate(ref, temperature="hot", claim_type="misconception")],
            session_id=f"s_{ref}",
            clock=FrozenClock(NOW),
        )[0]
        record_response(
            repository, presented["presentation_id"], {"response": "doesnt_fit"}, clock=FrozenClock(NOW)
        )

    visit_clock = FrozenClock(NOW + timedelta(days=1))
    first = present_claims(
        repository,
        [_candidate("m1", claim_type="misconception", cold_reask=True)],
        visit_id="visit1",
        clock=visit_clock,
    )[0]
    # The §2.3 cold re-ask bypasses the response cooldown.
    assert first["affordances_enabled"] is True

    second = present_claims(
        repository,
        [_candidate("m2", claim_type="misconception", cold_reask=True)],
        visit_id="visit1",
        clock=visit_clock,
    )[0]
    assert second["affordances_enabled"] is False
    assert second["suppression_reason"] == "cold_reask_visit_limit"

    # A later visit gets its own single re-ask.
    next_visit = present_claims(
        repository,
        [_candidate("m2", claim_type="misconception", cold_reask=True)],
        visit_id="visit2",
        clock=FrozenClock(NOW + timedelta(days=2)),
    )[0]
    assert next_visit["affordances_enabled"] is True


def test_suppressed_presentation_rejects_responses(tmp_path):
    repository = _repository(tmp_path)
    results = present_claims(
        repository,
        [_candidate("c1"), _candidate("c2")],
        session_id="s1",
        clock=FrozenClock(NOW),
    )
    suppressed = next(r for r in results if not r["affordances_enabled"])
    assert suppressed["suppression_reason"] == "session_card_budget"
    with pytest.raises(HypothesisClaimError):
        record_response(repository, suppressed["presentation_id"], {"response": "seems_low"})
