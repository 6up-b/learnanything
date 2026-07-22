"""P4 step 4 -- dispersion + stage-aware interleaving as feasible-set constraints
(spec_p4 §9.1/§9.2, §16.4). They shape the feasible set; they never rank.

Covers: no back-to-back same-facet/near-kin fresh evidence; lapse-retry exemption earns
no independent evidence; non-fresh blocks are not dispersed; acquisition stays coherent
while discrimination interleaves; assessment follows the frozen distribution.
"""

from __future__ import annotations

from learnloop.services import constraint_engine as ce
from learnloop.services import controller_snapshot as cs
from learnloop.services import dispersion as D
from learnloop.services import interleaving as I
from learnloop.services import staged_policy as sp


def _snapshot(*, candidates, last_fresh_evidence=None):
    return cs.ControllerSnapshot(
        snapshot_hash="h", session_id="s", available_minutes=None, energy=None,
        remaining_minutes=None, conservative_duration_minutes=cs.CONSERVATIVE_DURATION_MINUTES,
        candidates=tuple(candidates), exposure_by_hash={}, exposure_by_fingerprint={},
        reserved_assessment_surface_ids=frozenset(), commitments=(), affect_by_commitment={},
        param_manifest_hash="p", projection_versions={}, last_fresh_evidence=last_fresh_evidence,
    )


def _block(action, *, stage=None, commitment_id=None, neighborhood=None):
    return sp.AttentionBlock(
        action=action, subtype=None, commitment_id=commitment_id, budget_minutes=10.0,
        compatible_purposes=sp._ACTION_PURPOSES.get(action, ()), stage=stage,
        neighborhood=neighborhood or {},
    )


# --- dispersion (§9.1) -----------------------------------------------------------

def test_same_facet_fresh_evidence_not_back_to_back():
    cand = cs.Candidate(candidate_ref="c", surface_hash="H1", purpose="diagnostic",
                        facet_id="facet_svd")
    snap = _snapshot(candidates=[cand],
                     last_fresh_evidence={"facet_id": "facet_svd", "intervening_administrations": 0})
    feas = ce.evaluate(cand, snap, _block("measure_diagnostic"))
    assert not feas.eligible
    reasons = {(e.constraint_key, e.reason, e.kind) for e in feas.exclusions}
    assert ("same_facet_dispersion", "same_facet_back_to_back", "defer") in reasons


def test_near_kin_fingerprint_dispersion():
    cand = cs.Candidate(candidate_ref="c", surface_hash="H1", purpose="diagnostic",
                        fingerprint="fp_1")
    snap = _snapshot(candidates=[cand],
                     last_fresh_evidence={"fingerprint": "fp_1", "intervening_administrations": 0})
    feas = ce.evaluate(cand, snap, _block("measure_diagnostic"))
    assert not feas.eligible


def test_lapse_retry_is_exempt_but_earns_no_independent_evidence():
    cand = cs.Candidate(candidate_ref="c", surface_hash="H1", purpose="diagnostic",
                        facet_id="facet_svd", is_lapse_retry=True)
    snap = _snapshot(candidates=[cand],
                     last_fresh_evidence={"facet_id": "facet_svd", "intervening_administrations": 0})
    # Exempt from the dispersion exclusion (it lives inside its linked episode).
    v = D.same_facet_violation(cand, snap, _block("measure_diagnostic"))
    assert v is None


def test_dispersion_inert_when_enough_intervening_administrations():
    cand = cs.Candidate(candidate_ref="c", surface_hash="H1", purpose="diagnostic",
                        facet_id="facet_svd")
    snap = _snapshot(candidates=[cand],
                     last_fresh_evidence={"facet_id": "facet_svd", "intervening_administrations": 3})
    assert ce.evaluate(cand, snap, _block("measure_diagnostic")).eligible


def test_practice_block_is_not_dispersed():
    cand = cs.Candidate(candidate_ref="c", surface_hash="H1", purpose="practice",
                        facet_id="facet_svd")
    snap = _snapshot(candidates=[cand],
                     last_fresh_evidence={"facet_id": "facet_svd", "intervening_administrations": 0})
    # A non-fresh-evidence block does not disperse (practice can repeat a facet).
    assert ce.evaluate(cand, snap, _block("practice")).eligible


# --- interleaving (§9.2) ---------------------------------------------------------

def test_acquisition_stays_coherent():
    same = cs.Candidate(candidate_ref="same", purpose="practice", neighborhood_id="nb1")
    other = cs.Candidate(candidate_ref="other", purpose="practice", neighborhood_id="nb2")
    snap = _snapshot(candidates=[same, other])
    block = _block("practice", stage="acquisition", neighborhood={"neighborhood_id": "nb1"})
    assert ce.evaluate(same, snap, block).eligible
    feas = ce.evaluate(other, snap, block)
    assert not feas.eligible
    assert feas.exclusions[0].reason == "acquisition_coherence_required"


def test_discrimination_allows_interleaving():
    other = cs.Candidate(candidate_ref="other", purpose="practice", neighborhood_id="nb2")
    snap = _snapshot(candidates=[other])
    block = _block("practice", stage="discrimination", neighborhood={"neighborhood_id": "nb1"})
    # Interleaving confusable families is the OBJECTIVE at this stage -> never excluded.
    assert I.stage_violation(other, snap, block) is None
    assert ce.evaluate(other, snap, block).eligible


def test_assessment_follows_frozen_distribution():
    out = cs.Candidate(candidate_ref="out", surface_hash="H2", purpose="assessment",
                       in_frozen_target=False)
    snap = _snapshot(candidates=[out])
    block = _block("assess_terminal", stage="assessment")
    feas = ce.evaluate(out, snap, block)
    assert not feas.eligible
    assert any(e.reason == "outside_frozen_assessment_distribution" for e in feas.exclusions)


def test_unstaged_block_leaves_interleaving_inert():
    cand = cs.Candidate(candidate_ref="c", purpose="practice", neighborhood_id="nb2")
    snap = _snapshot(candidates=[cand])
    assert I.stage_violation(cand, snap, _block("practice")) is None
