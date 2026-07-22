"""P4 step 1 -- the versioned feasible-set constraint engine (spec_p4 §5, §16.1;
design §F). Constraints define the feasible set; a score can never resurrect an
infeasible candidate."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import constraint_engine as ce
from learnloop.services import controller_snapshot as cs
from learnloop.services import parameter_registry as pr
from learnloop.services import staged_policy as sp

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)


def _snapshot(*, candidates, exposure_by_hash=None, reserved=frozenset(), remaining=None):
    return cs.ControllerSnapshot(
        snapshot_hash="h",
        session_id="s",
        available_minutes=remaining,
        energy=None,
        remaining_minutes=remaining,
        conservative_duration_minutes=cs.CONSERVATIVE_DURATION_MINUTES,
        candidates=tuple(candidates),
        exposure_by_hash=exposure_by_hash or {},
        exposure_by_fingerprint={},
        reserved_assessment_surface_ids=reserved,
        commitments=(),
        affect_by_commitment={},
        param_manifest_hash="p",
        projection_versions={},
    )


def _block(action, subtype=None, commitment_id=None):
    return sp.AttentionBlock(
        action=action, subtype=subtype, commitment_id=commitment_id, budget_minutes=10.0,
        compatible_purposes=sp._ACTION_PURPOSES.get(action, ()),
    )


def test_manifest_is_content_hashed_and_stable():
    m1 = ce.manifest()
    m2 = ce.manifest()
    assert m1["manifest_hash"] == m2["manifest_hash"]
    assert m1["schema_version"] == ce.CONSTRAINT_MANIFEST_VERSION
    keys = {d["key"] for d in m1["definitions"]}
    assert {"active_status", "hard_exposure_collision", "fatigue_budget"} <= keys


def test_inactive_and_quarantined_are_excluded():
    active = cs.Candidate(candidate_ref="ok", active=True)
    inactive = cs.Candidate(candidate_ref="dead", active=False)
    quar = cs.Candidate(candidate_ref="q", active=True, quarantined=True)
    snap = _snapshot(candidates=[active, inactive, quar])
    assert ce.evaluate(active, snap, _block("practice")).eligible
    r = ce.evaluate(inactive, snap, _block("practice"))
    assert not r.eligible and r.exclusions[0].reason == "card_inactive"
    assert not ce.evaluate(quar, snap, _block("practice")).eligible


def test_hard_exposure_collision_excludes_fresh_evidence_candidate():
    """Invariant 11: a hard exact collision can never be made fresh."""

    diag = cs.Candidate(candidate_ref="diag", surface_id="s1", surface_hash="H1",
                        purpose="diagnostic")
    prac = cs.Candidate(candidate_ref="prac", surface_id="s1", surface_hash="H1",
                        purpose="practice")
    snap = _snapshot(candidates=[diag, prac],
                     exposure_by_hash={"H1": ({"kind": "submitted"},)})
    # Fresh-evidence block (diagnosis): the seen surface is infeasible.
    feas = ce.evaluate(diag, snap, _block("measure_diagnostic"))
    assert not feas.eligible
    assert feas.exclusions[0].reason == "exact_surface_collision"
    # Non-fresh block (practice): the same exposure is not a barrier.
    assert ce.evaluate(prac, snap, _block("practice")).eligible


def test_freshness_unknown_blocks_unseen_claim_only_for_fresh_block():
    diag = cs.Candidate(candidate_ref="d", surface_hash=None, purpose="diagnostic")
    prac = cs.Candidate(candidate_ref="p", surface_hash=None, purpose="practice")
    snap = _snapshot(candidates=[diag, prac])
    assert not ce.evaluate(diag, snap, _block("measure_diagnostic")).eligible
    assert ce.evaluate(prac, snap, _block("practice")).eligible


def test_assessment_reservation_blocks_non_assessment_use():
    prac = cs.Candidate(candidate_ref="r", surface_id="res1", purpose="practice")
    # An assessment-purpose candidate with a fresh (unseen) surface, usable only for
    # the assess_terminal block.
    assess = cs.Candidate(candidate_ref="a", surface_id="res1", surface_hash="RS1",
                          purpose="assessment")
    snap = _snapshot(candidates=[prac, assess], reserved=frozenset({"res1"}))
    feas = ce.evaluate(prac, snap, _block("practice"))
    assert not feas.eligible and feas.exclusions[0].reason == "reserved_assessment_surface"
    assert ce.evaluate(assess, snap, _block("assess_terminal")).eligible


def test_fatigue_budget_excludes_over_budget_candidate():
    big = cs.Candidate(candidate_ref="big", expected_minutes=20.0)
    small = cs.Candidate(candidate_ref="small", expected_minutes=2.0)
    snap = _snapshot(candidates=[big, small], remaining=5.0)
    assert not ce.evaluate(big, snap, _block("practice")).eligible
    assert ce.evaluate(small, snap, _block("practice")).eligible


def test_exclusion_reasons_are_complete_all_violations_reported():
    # An inactive candidate that ALSO overflows the budget reports both reasons.
    c = cs.Candidate(candidate_ref="multi", active=False, expected_minutes=99.0)
    snap = _snapshot(candidates=[c], remaining=1.0)
    feas = ce.evaluate(c, snap, _block("practice"))
    reasons = {e.reason for e in feas.exclusions}
    assert "card_inactive" in reasons
    assert "over_remaining_minutes" in reasons


def test_dormant_fatigue_slack_guardrail_bind_logged_when_it_fires(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    over = cs.Candidate(candidate_ref="over", expected_minutes=50.0)
    snap = _snapshot(candidates=[over], remaining=1.0)
    ce.feasible_set([over], snap, _block("practice"), repository=repo, clock=CLOCK)
    events = repo.parameter_bind_events_for_path("constraint_engine:FATIGUE_BUDGET_SLACK_MINUTES")
    assert len(events) == 1


def test_feasible_set_partitions_and_reports_manifest_hash():
    ok = cs.Candidate(candidate_ref="ok")
    bad = cs.Candidate(candidate_ref="bad", active=False)
    snap = _snapshot(candidates=[ok, bad])
    report = ce.feasible_set([ok, bad], snap, _block("practice"))
    assert [c.candidate_ref for c in report.feasible] == ["ok"]
    assert report.excluded[0][0].candidate_ref == "bad"
    assert report.manifest_hash == ce.manifest()["manifest_hash"]


def test_fatigue_slack_param_is_registered_dormant_and_monitored():
    spec = pr.REGISTRY.get("constraint_engine:FATIGUE_BUDGET_SLACK_MINUTES")
    assert spec is not None
    assert spec.param_class == "constraint"
    assert spec.default_lifecycle == "dormant"
    assert spec.bind_site
