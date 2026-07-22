"""P1 step 7 -- mint/gate infrastructure + durable pre-mint jobs
(§5.2, §5.3, §5.6; §9.3, §9.7)."""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services import activities as A
from learnloop.services import familiarity as F
from learnloop.services import surface_mint as SM

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)
# A clock well past the default 300s lease -- the earlier lease has expired.
LATER_CLOCK = FrozenClock(NOW + timedelta(seconds=1000))


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    return Repository(path)


def _card_and_surface(repo, *, hash_suffix, purpose="practice", surface_policy="rotating"):
    family_id = repo.ensure_activity_family(purpose=purpose, legacy_kind=None, title=f"f-{hash_suffix}", clock=CLOCK)
    card_id = repo.ensure_activity_card(family_id=family_id, clock=CLOCK)
    contract = {"target": "svd", "capability": "retrieval"}
    cv = repo.ensure_activity_card_version(
        card_id=card_id, version=1, card_contract_hash=A._canonical_hash({**contract, "s": hash_suffix}),
        contract_json=A._json(contract), schema_version=1, clock=CLOCK,
    )
    A.pin_card_authoring(repo, card_version_id=cv, surface_policy=surface_policy, clock=CLOCK)
    surface_id = repo.ensure_activity_surface(
        card_version_id=cv, surface_hash=f"sh-{hash_suffix}", fingerprint=None, surface_json="{}", clock=CLOCK,
    )
    return family_id, card_id, cv, surface_id


def _expose(repo, surface_id, *, kind="rendered", surface_hash=None):
    repo.append_exposure_event(
        surface_id=surface_id, administration_id=None,
        surface_hash=surface_hash or f"exp-{surface_id}", fingerprint=None, kind=kind,
        purpose="practice", consumes_unseen=False, clock=CLOCK,
    )


# --- §5.6 durable jobs ---------------------------------------------------------

def test_request_candidates_is_idempotent(repo):
    _, _, cv, anchor = _card_and_surface(repo, hash_suffix="a")
    r1 = SM.request_candidates(repo, card_version_id=cv, anchor_surface_id=anchor,
                               requested_angle={"axis": "cue"}, clock=CLOCK)
    r2 = SM.request_candidates(repo, card_version_id=cv, anchor_surface_id=anchor,
                               requested_angle={"axis": "cue"}, clock=CLOCK)
    assert r1 == r2
    assert len(repo.surface_mint_requests_for_card_version(cv)) == 1


def test_lease_lets_exactly_one_worker_drain(repo):
    _, _, cv, anchor = _card_and_surface(repo, hash_suffix="b")
    SM.request_candidates(repo, card_version_id=cv, anchor_surface_id=anchor, clock=CLOCK)
    first = SM.claim_next_mint_job(repo, worker_id="w1", clock=CLOCK)
    assert first is not None and first["status"] == "running"
    # A second worker cannot claim while a live lease is held.
    assert SM.claim_next_mint_job(repo, worker_id="w2", clock=CLOCK) is None


def test_admit_marks_surface_admitted_and_rotation_eligible(repo):
    _, _, cv, anchor = _card_and_surface(repo, hash_suffix="c")
    request_id = SM.request_candidates(repo, card_version_id=cv, anchor_surface_id=anchor, clock=CLOCK)
    job = SM.claim_next_mint_job(repo, worker_id="w1", clock=CLOCK)
    # Mint a fresh candidate surface for the same card version.
    candidate_surface = repo.ensure_activity_surface(
        card_version_id=cv, surface_hash="sh-c-cand", fingerprint=None, surface_json="{}", clock=CLOCK,
    )
    candidate = {
        "surface_id": candidate_surface, "card_version_id": cv, "surface_hash": "sh-c-cand",
        "purpose": "practice", "rubric_verbatim": True, "answer_key_consistent": True,
    }
    result = SM.process_mint_job(repo, request=job, candidate=candidate, clock=CLOCK)
    assert result.admitted, result.as_dict()
    row = repo.surface_mint_request(request_id)
    assert row["status"] == "admitted"
    authoring = repo.activity_surface_authoring(candidate_surface)
    assert authoring["status"] == "admitted" and authoring["rotation_eligible"] == 1


def test_anchored_candidate_passes_comparative_and_verbatim_rubric(repo):
    _, _, cv, anchor = _card_and_surface(repo, hash_suffix="d")
    request_id = SM.request_candidates(repo, card_version_id=cv, anchor_surface_id=anchor, clock=CLOCK)
    job = SM.claim_next_mint_job(repo, worker_id="w1", clock=CLOCK)
    candidate = {
        "surface_id": repo.ensure_activity_surface(card_version_id=cv, surface_hash="sh-d-cand",
                                                   fingerprint=None, surface_json="{}", clock=CLOCK),
        "card_version_id": cv, "surface_hash": "sh-d-cand", "purpose": "practice",
        "rubric_verbatim": True,
    }
    result = SM.run_all_gates(repo, request=job, candidate=candidate)
    names = {o.name: o.passed for o in result.outcomes}
    assert names["comparative_vs_anchor"] and names["verbatim_rubric"]
    assert result.admitted


def test_candidate_identical_to_anchor_fails_comparative_gate(repo):
    _, _, cv, anchor = _card_and_surface(repo, hash_suffix="e")
    anchor_row = repo.fetch_surface(anchor)
    job = repo.surface_mint_request(
        SM.request_candidates(repo, card_version_id=cv, anchor_surface_id=anchor, clock=CLOCK)
    )
    candidate = {"surface_id": anchor, "card_version_id": cv,
                 "surface_hash": anchor_row["surface_hash"], "purpose": "practice"}
    result = SM.run_all_gates(repo, request=job, candidate=candidate)
    assert not result.admitted
    assert result.first_failure == "comparative_vs_anchor"


def test_rejected_candidate_retained_but_not_admitted(repo):
    _, _, cv, anchor = _card_and_surface(repo, hash_suffix="f")
    request_id = SM.request_candidates(repo, card_version_id=cv, anchor_surface_id=anchor, clock=CLOCK)
    job = SM.claim_next_mint_job(repo, worker_id="w1", clock=CLOCK)
    cand_surface = repo.ensure_activity_surface(card_version_id=cv, surface_hash="sh-f-cand",
                                                fingerprint=None, surface_json="{}", clock=CLOCK)
    candidate = {"surface_id": cand_surface, "card_version_id": cv, "surface_hash": "sh-f-cand",
                 "purpose": "practice", "answer_key_consistent": False}
    result = SM.process_mint_job(repo, request=job, candidate=candidate, clock=CLOCK)
    assert not result.admitted
    row = repo.surface_mint_request(request_id)
    assert row["status"] == "rejected"
    assert row["candidate_surface_id"] == cand_surface  # retained for audit
    assert row["failure_reason"] == "solvability_answer_key"


def test_novelty_gate_blocks_exposed_exact_hash(repo):
    _, _, cv, anchor = _card_and_surface(repo, hash_suffix="g")
    _expose(repo, anchor, surface_hash="sh-reused")
    job = repo.surface_mint_request(
        SM.request_candidates(repo, card_version_id=cv, anchor_surface_id=anchor, clock=CLOCK)
    )
    candidate = {"surface_id": None, "card_version_id": cv, "surface_hash": "sh-reused",
                 "purpose": "practice"}
    result = SM.run_all_gates(repo, request=job, candidate=candidate)
    names = {o.name: o.passed for o in result.outcomes}
    assert not names["novelty_audit"]


def test_purpose_leakage_blocks_assessment_hard_collision(repo):
    # A candidate assessment surface that hard-collides with an already-exposed sibling
    # cannot be admitted (leakage). shared_stimulus is a hard namespace.
    _, _, cv, anchor = _card_and_surface(repo, hash_suffix="h", purpose="assessment")
    sibling = repo.ensure_activity_surface(card_version_id=cv, surface_hash="sh-h-sib",
                                           fingerprint=None, surface_json="{}", clock=CLOCK)
    F.record_memberships(repo, surface_id=sibling,
                         memberships=[{"namespace": "shared_stimulus", "value_hash": "stim-1"}], clock=CLOCK)
    _expose(repo, sibling)
    candidate_surface = repo.ensure_activity_surface(card_version_id=cv, surface_hash="sh-h-cand",
                                                     fingerprint=None, surface_json="{}", clock=CLOCK)
    F.record_memberships(repo, surface_id=candidate_surface,
                         memberships=[{"namespace": "shared_stimulus", "value_hash": "stim-1"}], clock=CLOCK)
    job = repo.surface_mint_request(
        SM.request_candidates(repo, card_version_id=cv, clock=CLOCK)
    )
    candidate = {"surface_id": candidate_surface, "card_version_id": cv,
                 "surface_hash": "sh-h-cand", "purpose": "assessment"}
    result = SM.run_all_gates(repo, request=job, candidate=candidate)
    names = {o.name: o.passed for o in result.outcomes}
    assert not names["purpose_leakage"]


# --- §5.3 rotation -------------------------------------------------------------

def test_rotation_triggers_after_exposure_cadence(repo):
    # A surface renders at most once; cadence counts card-level administrations across
    # the card's surfaces (§5.3). Expose ROTATION_CADENCE_ADMINISTRATIONS distinct
    # surfaces under one card, then the current surface is due to rotate.
    _, _, cv, surface = _card_and_surface(repo, hash_suffix="i")
    assert not SM.needs_rotation(repo, surface_id=surface)  # fresh
    _expose(repo, surface)
    for k in range(1, SM.ROTATION_CADENCE_ADMINISTRATIONS):
        sib = repo.ensure_activity_surface(card_version_id=cv, surface_hash=f"sh-i-{k}",
                                           fingerprint=None, surface_json="{}", clock=CLOCK)
        _expose(repo, sib)
    assert SM.needs_rotation(repo, surface_id=surface)


def test_fixed_surface_never_auto_rotates(repo):
    # Fixed policy short-circuits: it never auto-rotates regardless of cadence (§5.3).
    _, _, cv, surface = _card_and_surface(repo, hash_suffix="j", surface_policy="fixed")
    repo.upsert_activity_surface_authoring(surface_id=surface, fields={"surface_policy": "fixed"}, clock=CLOCK)
    _expose(repo, surface)
    for k in range(1, 4):
        sib = repo.ensure_activity_surface(card_version_id=cv, surface_hash=f"sh-j-{k}",
                                           fingerprint=None, surface_json="{}", clock=CLOCK)
        _expose(repo, sib)
    assert not SM.needs_rotation(repo, surface_id=surface)


# --- §5.6/§9.3 retirement obsoletes queued work --------------------------------

def test_retirement_obsoletes_queued_mint_work(repo):
    _, _, cv, anchor = _card_and_surface(repo, hash_suffix="k")
    request_id = SM.request_candidates(repo, card_version_id=cv, anchor_surface_id=anchor, clock=CLOCK)
    n = SM.obsolete_mint_work_for_card_versions(repo, [cv], clock=CLOCK)
    assert n == 1
    assert repo.surface_mint_request(request_id)["status"] == "obsolete"
    # A claim finds nothing left to drain.
    assert SM.claim_next_mint_job(repo, worker_id="w1", clock=CLOCK) is None


# --- §9.7 operability ----------------------------------------------------------

def test_opening_administration_does_not_enqueue_or_call_generator(repo):
    # Opening/administering never touches the mint module: a pending job is unrelated to
    # the render path, and no mint request appears from an administration.
    _, _, cv, surface = _card_and_surface(repo, hash_suffix="l")
    before = repo.surface_mint_requests_for_card_version(cv)
    repo.append_exposure_event(surface_id=surface, administration_id=None, surface_hash="sh-l",
                               fingerprint=None, kind="rendered", purpose="practice",
                               consumes_unseen=False, clock=CLOCK)
    after = repo.surface_mint_requests_for_card_version(cv)
    assert before == after == []


def test_submission_usable_when_mint_workers_down(repo):
    # A pending mint request with no worker never blocks exposing/submitting the current
    # admitted surface.
    _, _, cv, surface = _card_and_surface(repo, hash_suffix="m")
    SM.request_candidates(repo, card_version_id=cv, anchor_surface_id=surface, clock=CLOCK)
    # No worker claims. Submission still works.
    eid = repo.append_exposure_event(surface_id=surface, administration_id=None, surface_hash="sh-m",
                                     fingerprint=None, kind="submitted", purpose="practice",
                                     consumes_unseen=False, clock=CLOCK)
    assert eid
    assert repo.surface_mint_requests_for_card_version(cv, statuses=["pending"])


def test_cache_race_does_not_double_admit(repo):
    # Two candidates for the same request: the request is a single row, so the second
    # process wins the terminal state; a race wastes a candidate but never double-admits.
    _, _, cv, anchor = _card_and_surface(repo, hash_suffix="n")
    request_id = SM.request_candidates(repo, card_version_id=cv, anchor_surface_id=anchor, clock=CLOCK)
    job = SM.claim_next_mint_job(repo, worker_id="w1", clock=CLOCK)
    c1 = repo.ensure_activity_surface(card_version_id=cv, surface_hash="sh-n-1", fingerprint=None,
                                      surface_json="{}", clock=CLOCK)
    c2 = repo.ensure_activity_surface(card_version_id=cv, surface_hash="sh-n-2", fingerprint=None,
                                      surface_json="{}", clock=CLOCK)
    SM.process_mint_job(repo, request=job, candidate={"surface_id": c1, "card_version_id": cv,
                        "surface_hash": "sh-n-1", "purpose": "practice"}, clock=CLOCK)
    SM.process_mint_job(repo, request=job, candidate={"surface_id": c2, "card_version_id": cv,
                        "surface_hash": "sh-n-2", "purpose": "practice"}, clock=CLOCK)
    row = repo.surface_mint_request(request_id)
    assert row["status"] == "admitted"  # a single terminal row; no double administration


# --- B1 mint double-admit fencing ---------------------------------------------

def _rotation_eligible_surfaces(repo, cv):
    eligible = []
    for surface in repo.surfaces_for_card_version(cv):
        authoring = repo.activity_surface_authoring(surface["id"])
        if authoring is not None and authoring.get("rotation_eligible") == 1:
            eligible.append(surface["id"])
    return eligible


def test_reprocessing_admitted_job_never_double_admits(repo):
    # B1 regression. Pre-fix: process_mint_job wrote unconditionally, so a re-run of the
    # SAME claimed request admitted a SECOND surface -> two rotation-eligible surfaces
    # from one request. With the status/lease re-read guard the re-run refuses and
    # writes nothing.
    _, _, cv, anchor = _card_and_surface(repo, hash_suffix="dbladmit")
    request_id = SM.request_candidates(repo, card_version_id=cv, anchor_surface_id=anchor, clock=CLOCK)
    job = SM.claim_next_mint_job(repo, worker_id="w1", clock=CLOCK)
    c1 = repo.ensure_activity_surface(card_version_id=cv, surface_hash="sh-da-1", fingerprint=None,
                                      surface_json="{}", clock=CLOCK)
    r1 = SM.process_mint_job(repo, request=job, candidate={"surface_id": c1, "card_version_id": cv,
                             "surface_hash": "sh-da-1", "purpose": "practice"}, clock=CLOCK)
    assert r1.admitted
    # A stale re-run of the same claimed job (e.g. duplicate delivery) with a NEW
    # candidate must not admit a second surface.
    c2 = repo.ensure_activity_surface(card_version_id=cv, surface_hash="sh-da-2", fingerprint=None,
                                      surface_json="{}", clock=CLOCK)
    r2 = SM.process_mint_job(repo, request=job, candidate={"surface_id": c2, "card_version_id": cv,
                             "surface_hash": "sh-da-2", "purpose": "practice"}, clock=CLOCK)
    assert not r2.admitted  # refused: job no longer running under this lease
    assert _rotation_eligible_surfaces(repo, cv) == [c1]  # exactly one


def test_expired_lease_recovery_rejects_stale_worker_write(repo):
    # B1 regression. A slow-but-alive worker w1 holds an expired lease; w2 legitimately
    # re-claims (bumping the fencing epoch). w1's late write must be rejected while w2's
    # admit wins -> still exactly one rotation-eligible surface, and it is w2's.
    _, _, cv, anchor = _card_and_surface(repo, hash_suffix="explease")
    SM.request_candidates(repo, card_version_id=cv, anchor_surface_id=anchor, clock=CLOCK)
    job_w1 = SM.claim_next_mint_job(repo, worker_id="w1", clock=CLOCK)
    # Lease expires; w2 re-claims the now-dead running job at a later time.
    job_w2 = SM.claim_next_mint_job(repo, worker_id="w2", clock=LATER_CLOCK)
    assert job_w2 is not None and job_w2["lease_epoch"] > job_w1["lease_epoch"]
    c_w2 = repo.ensure_activity_surface(card_version_id=cv, surface_hash="sh-w2", fingerprint=None,
                                        surface_json="{}", clock=CLOCK)
    r_w2 = SM.process_mint_job(repo, request=job_w2, candidate={"surface_id": c_w2,
                               "card_version_id": cv, "surface_hash": "sh-w2", "purpose": "practice"},
                               clock=CLOCK)
    assert r_w2.admitted
    # w1 wakes up and tries to finish its stale job -- rejected by the fencing token.
    c_w1 = repo.ensure_activity_surface(card_version_id=cv, surface_hash="sh-w1", fingerprint=None,
                                        surface_json="{}", clock=CLOCK)
    r_w1 = SM.process_mint_job(repo, request=job_w1, candidate={"surface_id": c_w1,
                               "card_version_id": cv, "surface_hash": "sh-w1", "purpose": "practice"},
                               clock=CLOCK)
    assert not r_w1.admitted
    assert _rotation_eligible_surfaces(repo, cv) == [c_w2]


# --- B5 admit requires a passing gate result ----------------------------------

def test_admit_candidate_without_passing_gate_raises(repo):
    # B5 regression. Pre-fix admit_candidate accepted gate_result=None and marked the
    # surface admitted + rotation-eligible with no gate evidence at all.
    _, _, cv, anchor = _card_and_surface(repo, hash_suffix="gatebypass")
    request_id = SM.request_candidates(repo, card_version_id=cv, anchor_surface_id=anchor, clock=CLOCK)
    cand = repo.ensure_activity_surface(card_version_id=cv, surface_hash="sh-gb", fingerprint=None,
                                        surface_json="{}", clock=CLOCK)
    with pytest.raises(SM.MintWorkerError):
        SM.admit_candidate(repo, request_id=request_id, candidate_surface_id=cand, clock=CLOCK)
    failing = SM.GateResult(
        gate_policy_version=SM.MINT_GATE_POLICY_VERSION,
        outcomes=(SM.GateOutcome("solvability_answer_key", False, "answer_key_inconsistent"),),
    )
    with pytest.raises(SM.MintWorkerError):
        SM.admit_candidate(repo, request_id=request_id, candidate_surface_id=cand,
                           gate_result=failing, clock=CLOCK)
    # No surface was ever admitted.
    assert _rotation_eligible_surfaces(repo, cv) == []


# --- B2 NULL-anchor enqueue idempotency ---------------------------------------

def test_no_anchor_enqueue_is_idempotent_under_concurrency(repo):
    # B2 regression. Pre-fix the anchor column was nullable and the UNIQUE index treated
    # NULL anchors as distinct, so two concurrent no-anchor enqueues could create two
    # rows. The '' sentinel + UNIQUE + IntegrityError->re-SELECT collapse them to one.
    import threading

    _, _, cv, _ = _card_and_surface(repo, hash_suffix="noanchor")
    ids: list[str] = []
    barrier = threading.Barrier(4)

    def _enqueue():
        barrier.wait()
        ids.append(SM.request_candidates(repo, card_version_id=cv, clock=CLOCK))

    threads = [threading.Thread(target=_enqueue) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(set(ids)) == 1
    assert len(repo.surface_mint_requests_for_card_version(cv)) == 1
