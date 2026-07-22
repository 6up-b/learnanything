"""P1 step 10 -- Journey 6 acceptance, end-to-end on a FRESH mvp-0.8 vault
(spec_p1_shared_substrate §9.6).

The nine-step arc is driven through the real services (no LLM: deterministic stub
content, the way the existing substrate tests do). Acceptance FAILS if surface
generation alone advances certification, if the same surface is represented as fresh,
or if a card fork inherits FSRS stability / certification.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services import activities as A
from learnloop.services import card_lineage as CL
from learnloop.services import commitments as C
from learnloop.services import depth_transition as DT
from learnloop.services import progression as P
from learnloop.services import substrate_cutover as SC
from learnloop.services import surface_mint as SM
from learnloop.services.activities import evaluate_held_out_eligibility
from learnloop.services.fsrs import Rating

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)
SCHED = SC.P1_SCHEDULER_ALGORITHM_VERSION
MVP08 = SC.P0_ALGORITHM_VERSION


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    return Repository(path)


def _card_version(repo, *, family_id, card_id, contract, version=1):
    return repo.ensure_activity_card_version(
        card_id=card_id, version=version, card_contract_hash=A._canonical_hash(contract),
        contract_json=A._json(contract), schema_version=1, clock=CLOCK,
    )


def _surface(repo, cv, *, tag, fingerprint=None):
    sid = repo.ensure_activity_surface(
        card_version_id=cv, surface_hash=f"sh-{tag}", fingerprint=fingerprint, surface_json="{}", clock=CLOCK,
    )
    return repo.fetch_surface(sid)


def _submit(repo, *, surface, cv, family_id, lineage_id, purpose="practice", correct=True, tag="x", context=None):
    return SC.submit_administration_response(
        repo, surface=surface, card_version_id=cv, family_id=family_id, purpose=purpose,
        card_lineage_id=lineage_id, algorithm_version=MVP08,
        review_event={"rating": Rating.GOOD if correct else Rating.AGAIN, "elapsed_days": 0.0},
        eligible=True, failed=not correct, attempt_id=f"att-{tag}",
        admin_context=context or {"cold": True, "open_book": False}, clock=CLOCK,
    )


def test_journey6_end_to_end_on_fresh_mvp08_vault(repo, monkeypatch):
    # A fresh mvp-0.8 vault: the purpose-adapter path is the LIVE scheduling authority.
    assert SC.purpose_adapters_live(MVP08) is True

    # (1) Commit from an explicit exemplar action (invariant 4: only commit-class
    # actions create a commitment).
    commitment = C.create_commitment(
        repo, action="select_exemplar", intent_text="master SVD like these",
        targets=[{"target_kind": "canonical_facet", "target_ref": "svd", "role": "required"}],
        depth_preset="master_tasks_like_these", clock=CLOCK,
    )
    assert C.resolve_disposition(repo, commitment.id) == "active"

    # One reviewed practice family; a retrieval card + its first surface.
    family_id = repo.ensure_activity_family(purpose="practice", legacy_kind=None, title="svd-practice", clock=CLOCK)
    retr_card = repo.ensure_activity_card(family_id=family_id, clock=CLOCK)
    retr_contract = {"target": "svd", "capability": "retrieval"}
    retr_cv = _card_version(repo, family_id=family_id, card_id=retr_card, contract=retr_contract)
    A.pin_card_authoring(repo, card_version_id=retr_cv, surface_policy="rotating", clock=CLOCK)
    retr_lineage = CL.start_lineage(repo, genesis_card_version_id=retr_cv, family_id=family_id, card_id=retr_card, clock=CLOCK)
    s1 = _surface(repo, retr_cv, tag="retr-1")

    # (2) Demonstrate retrieval on one surface -> eligible practice writes card state.
    r1 = _submit(repo, surface=s1, cv=retr_cv, family_id=family_id, lineage_id=retr_lineage, tag="retr-1")
    assert r1.complete and r1.card_state["stability"] is not None
    original_stability = r1.card_state["stability"]
    # ACCEPTANCE GUARD: the same surface is NOT represented as fresh once administered.
    assert not evaluate_held_out_eligibility(repo, surface=s1, purpose="practice").is_unseen

    # (3) Progress through a DIFFERENT capability/angle, not a cosmetic clone.
    # A cosmetic clone stays surface-preserving (same lineage); a capability change forks.
    assert CL.classify_edit(retr_contract, {**retr_contract, "wording": "reworded"}).verdict == "surface_preserving"
    proc_contract = {"target": "svd", "capability": "procedure_execution"}
    assert CL.classify_edit(retr_contract, proc_contract).verdict == "fork_required"
    # One card per family in the P0.1 world; the fork is a new lineage over a new
    # immutable card version (version=2) of that card.
    proc_card = retr_card
    proc_cv = _card_version(repo, family_id=family_id, card_id=proc_card, contract=proc_contract, version=2)
    fork = CL.fork_card(
        repo, predecessor_card_version_id=retr_cv, forked_card_version_id=proc_cv,
        scheduler_algorithm_version=SCHED, family_id=family_id, card_id=proc_card,
        informed_difficulty_prior=0.3, predecessor_lineage_id=retr_lineage, clock=CLOCK,
    )
    proc_lineage = fork["lineage_id"]
    # (8, asserted here) NO inherited FSRS stability / certification across the fork.
    fork_state = repo.activity_card_state(card_lineage_id=proc_lineage, scheduler_algorithm_version=SCHED)
    assert fork_state["stability"] is None
    assert fork_state["difficulty"] == 0.3  # only an explicitly shrunk prior

    # (4) Rotate a warm surface through the anchored gate. Reaching cadence on the
    # rotating card marks it due for rotation.
    s1b = _surface(repo, retr_cv, tag="retr-2")
    _submit(repo, surface=s1b, cv=retr_cv, family_id=family_id, lineage_id=retr_lineage, tag="retr-2")
    assert SM.needs_rotation(repo, surface_id=s1.id if hasattr(s1, "id") else s1["id"])
    state_before_mint = repo.activity_card_state(card_lineage_id=retr_lineage, scheduler_algorithm_version=SCHED)
    request_id = SM.request_candidates(repo, card_version_id=retr_cv, anchor_surface_id=s1["id"], clock=CLOCK)
    job = SM.claim_next_mint_job(repo, worker_id="w1", clock=CLOCK)
    candidate_surface = repo.ensure_activity_surface(
        card_version_id=retr_cv, surface_hash="sh-retr-cand", fingerprint=None, surface_json="{}", clock=CLOCK,
    )
    result = SM.process_mint_job(
        repo, request=job,
        candidate={"surface_id": candidate_surface, "card_version_id": retr_cv,
                   "surface_hash": "sh-retr-cand", "purpose": "practice",
                   "rubric_verbatim": True, "answer_key_consistent": True},
        clock=CLOCK,
    )
    assert result.admitted
    # ACCEPTANCE GUARD: surface generation ALONE never advances certification/scheduling.
    state_after_mint = repo.activity_card_state(card_lineage_id=retr_lineage, scheduler_algorithm_version=SCHED)
    assert state_after_mint["stability"] == state_before_mint["stability"]

    # (5) Lapse, retry without mutation, next-day fresh follow-up.
    s_fail = _surface(repo, proc_cv, tag="proc-fail")
    fail = _submit(repo, surface=s_fail, cv=proc_cv, family_id=family_id, lineage_id=proc_lineage,
                   tag="proc-fail", correct=False)
    episode_id = P.open_lapse_episode(repo, card_lineage_id=proc_lineage,
                                      opened_administration_id=fail.administration_id, clock=CLOCK)
    episode = repo.lapse_episode(episode_id)
    assert episode["status"] == "open"
    # The next-day follow-up is scheduled (a registered decision parameter).
    assert episode["followup_due_at"] is not None and episode["followup_due_at"] > NOW.isoformat()
    P.link_retry(repo, episode_id=episode_id, observation={"attempt_id": "retry-1", "correct": False},
                 derived_retrievability=0.4, clock=CLOCK)
    after = repo.lapse_episode(episode_id)
    # The original failure is preserved; the retry is linked, not overwritten.
    assert after["opened_administration_id"] == fail.administration_id
    assert len(__import__("json").loads(after["retry_observations_json"])) == 1

    # (6) Demonstrate delayed transfer on an INDEPENDENT surface (distinct fingerprint).
    s_transfer = _surface(repo, proc_cv, tag="proc-transfer", fingerprint="fp-transfer")
    r_transfer = _submit(repo, surface=s_transfer, cv=proc_cv, family_id=family_id, lineage_id=proc_lineage,
                         tag="proc-transfer", correct=True)
    assert r_transfer.complete
    # Full exposure is recorded under every purpose (§3.10 last column).
    assert any(e["kind"] == "submitted" for e in repo.exposures_for_surface(s_transfer["id"]))

    # (7) Record the milestone reached and auto-activate ONE reviewed inside-envelope
    # edge without another prompt. U-018 belt-and-suspenders (B4): live activation
    # requires the module gate constant, patched here explicitly (test-only) rather
    # than relying on the argument alone.
    monkeypatch.setattr(DT, "LIVE_ACTIVATION_ENABLED", True)
    C.change_depth_policy(repo, commitment_id=commitment.id, policy="auto_within_envelope", clock=CLOCK)
    C.change_depth_envelope(
        repo, commitment_id=commitment.id, bounds={"capability_additions": ["procedure_execution"]},
        reviewed_edges=[{"edge_id": "e1", "from_milestone": "m0", "to_milestone": "m1", "reviewed": True}],
        allow_widen=True, clock=CLOCK,
    )
    transition = DT.commit_one_edge(
        repo, commitment_id=commitment.id, milestone="m1", selected_edge_id="e1",
        evidence_receipt={"qualifies": True, "evidence_receipt": {"groups": ["g1", "g2"]}},
        live_activation_enabled=True, clock=CLOCK,
    )
    assert transition.committed and transition.milestone_slug == "m1"
    event_kinds = [e["kind"] for e in repo.commitment_events_for(commitment.id)]
    assert event_kinds.count("depth_milestone_reached") == 1

    # (8) Old and new lineage/scheduling traces are SEPARATE with no inheritance. The
    # fork inherited no stability at fork time (asserted above); by now the forked
    # lineage has built its OWN scheduling state from its own practice -- a distinct
    # trace, never the original's.
    assert proc_lineage != retr_lineage
    original_state = repo.activity_card_state(card_lineage_id=retr_lineage, scheduler_algorithm_version=SCHED)
    forked_state = repo.activity_card_state(card_lineage_id=proc_lineage, scheduler_algorithm_version=SCHED)
    assert original_state["stability"] == original_stability  # original retained its own state
    # Distinct state rows on distinct lineages -- no shared/inherited scheduling row.
    assert forked_state["id"] != original_state["id"]
    assert forked_state["card_lineage_id"] == proc_lineage

    # (9) Retire a bad card without losing the commitment, milestone, or prior evidence.
    obs_before = repo.observations_for_administration(r1.administration_id)
    record_id = A.retire_with_reason(
        repo, scope="card", card_version_id=proc_cv, reason="bad_underlying_explanation",
        provenance="learner_action", clock=CLOCK,
    )
    assert record_id is not None
    # Commitment intact + still active; milestone achievement preserved; evidence untouched.
    assert C.resolve_disposition(repo, commitment.id) == "active"
    assert [e["kind"] for e in repo.commitment_events_for(commitment.id)].count("depth_milestone_reached") == 1
    assert repo.observations_for_administration(r1.administration_id) == obs_before


def test_journey6_passive_action_cannot_create_commitment(repo):
    # The arc begins with a commit-class action; a passive one is rejected (invariant 4).
    with pytest.raises(C.PassiveActionCannotCommit):
        C.create_commitment(
            repo, action="highlight", intent_text="just reading",
            targets=[{"target_kind": "canonical_facet", "target_ref": "svd", "role": "required"}],
            depth_preset="keep_in_touch", clock=CLOCK,
        )
