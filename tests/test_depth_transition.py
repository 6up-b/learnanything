"""P1 step 8 -- the deterministic one-edge depth-transition service
(§5.7, §3.1.1, §10; invariants 12; §9.1, §9.2, §9.6)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.migrate import apply_migrations
from learnloop.db.repositories import Repository
from learnloop.services import commitments as C
from learnloop.services import depth_transition as DT

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)
RECEIPT = {"qualifies": True, "evidence_receipt": {"groups": ["g1", "g2"]}}


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    return Repository(path)


@pytest.fixture
def live(monkeypatch):
    """U-018 belt-and-suspenders (B4): live activation needs the module gate constant
    ON, not just the argument. The acceptance harness patches the constant explicitly."""

    monkeypatch.setattr(DT, "LIVE_ACTIVATION_ENABLED", True)


def _auto_commitment(repo, *, policy="auto_within_envelope", edges=None):
    commitment = C.create_commitment(
        repo, action="select_exemplar", intent_text="master SVD",
        targets=[{"target_kind": "canonical_facet", "target_ref": "svd", "role": "required"}],
        depth_preset="master_tasks_like_these", clock=CLOCK,
    )
    C.change_depth_policy(repo, commitment_id=commitment.id, policy=policy, clock=CLOCK)
    reviewed_edges = edges if edges is not None else [
        {"edge_id": "e1", "from_milestone": "m0", "to_milestone": "m1", "reviewed": True},
        {"edge_id": "e2", "from_milestone": "m1", "to_milestone": "m2", "reviewed": True},
    ]
    C.change_depth_envelope(repo, commitment_id=commitment.id, bounds={"capability_additions": ["procedure_execution"]},
                            reviewed_edges=reviewed_edges, allow_widen=True, clock=CLOCK)
    return commitment.id


def _events(repo, commitment_id):
    return [e["kind"] for e in repo.commitment_events_for(commitment_id)]


# --- §3.1.1 / §9.1 policy gating ----------------------------------------------

def test_hold_at_target_cannot_auto_activate(repo):
    cid = _auto_commitment(repo, policy="hold_at_target")
    out = DT.commit_one_edge(repo, commitment_id=cid, milestone="m1", selected_edge_id="e1",
                             evidence_receipt=RECEIPT, live_activation_enabled=True, clock=CLOCK)
    assert not out.committed
    assert "policy_not_auto_within_envelope" in out.reason


def test_suggest_next_policy_cannot_auto_activate(repo):
    cid = _auto_commitment(repo, policy="suggest_next")
    out = DT.commit_one_edge(repo, commitment_id=cid, milestone="m1", selected_edge_id="e1",
                             evidence_receipt=RECEIPT, live_activation_enabled=True, clock=CLOCK)
    assert not out.committed and out.kind == "suggest_next"


# --- U-018 structural gate: OFF in prod, ON in acceptance ---------------------

def test_gate_off_stores_intent_and_behaves_as_suggest_next(repo):
    cid = _auto_commitment(repo)
    out = DT.commit_one_edge(repo, commitment_id=cid, milestone="m1", selected_edge_id="e1",
                             evidence_receipt=RECEIPT, live_activation_enabled=False, clock=CLOCK)
    assert not out.committed
    assert out.kind == "suggest_next" and out.detail["intent_stored"] is True
    # It activated nothing: no milestone/transition events appended.
    assert "depth_milestone_reached" not in _events(repo, cid)


def test_module_default_gate_is_off(repo):
    assert DT.LIVE_ACTIVATION_ENABLED is False
    cid = _auto_commitment(repo)
    out = DT.commit_one_edge(repo, commitment_id=cid, milestone="m1", selected_edge_id="e1",
                             evidence_receipt=RECEIPT, clock=CLOCK)  # no explicit flag -> module default
    assert not out.committed and out.kind == "suggest_next"


# --- §5.7 one-edge activation (acceptance harness) ----------------------------

def test_auto_within_envelope_activates_exactly_one_reviewed_edge(repo, live):
    cid = _auto_commitment(repo)
    out = DT.commit_one_edge(repo, commitment_id=cid, milestone="m1", selected_edge_id="e1",
                             evidence_receipt=RECEIPT, live_activation_enabled=True, clock=CLOCK)
    assert out.committed
    assert out.selected_edge_id == "e1" and out.milestone_slug == "m1"
    kinds = _events(repo, cid)
    assert kinds.count("depth_milestone_reached") == 1
    assert kinds.count("depth_transition_committed") == 1


def test_unreviewed_or_missing_edge_is_refused(repo):
    cid = _auto_commitment(repo, edges=[{"edge_id": "e1", "from_milestone": "m0",
                                         "to_milestone": "m1", "reviewed": False}])
    out = DT.commit_one_edge(repo, commitment_id=cid, milestone="m1", selected_edge_id="e1",
                             evidence_receipt=RECEIPT, live_activation_enabled=True, clock=CLOCK)
    assert not out.committed and out.reason == "no_reviewed_edge"


def test_outside_envelope_edge_needs_authoring(repo):
    cid = _auto_commitment(repo, edges=[{"edge_id": "e1", "from_milestone": "m0", "to_milestone": "m1",
                                         "reviewed": True, "outside_envelope": True}])
    out = DT.commit_one_edge(repo, commitment_id=cid, milestone="m1", selected_edge_id="e1",
                             evidence_receipt=RECEIPT, live_activation_enabled=True, clock=CLOCK)
    assert not out.committed and out.kind == "authoring_needed"


def test_insufficient_evidence_is_refused(repo):
    cid = _auto_commitment(repo)
    out = DT.commit_one_edge(repo, commitment_id=cid, milestone="m1", selected_edge_id="e1",
                             evidence_receipt={"qualifies": False}, live_activation_enabled=True, clock=CLOCK)
    assert not out.committed and out.reason == "insufficient_evidence"


def test_achieved_milestone_stays_when_a_deeper_one_activates(repo, live):
    cid = _auto_commitment(repo)
    DT.commit_one_edge(repo, commitment_id=cid, milestone="m1", selected_edge_id="e1",
                       evidence_receipt=RECEIPT, live_activation_enabled=True, clock=CLOCK)
    DT.commit_one_edge(repo, commitment_id=cid, milestone="m2", selected_edge_id="e2",
                       evidence_receipt=RECEIPT, live_activation_enabled=True, clock=CLOCK)
    milestones = [
        __import__("json").loads(e["detail_json"])["milestone_slug"]
        for e in repo.commitment_events_for(cid) if e["kind"] == "depth_milestone_reached"
    ]
    # Both achievements are preserved; the earlier one is never cleared (§3.1.1).
    assert milestones == ["m1", "m2"]


# --- §9.2 fork on capability/regime change; surface-only does not fork --------

def _card_version(repo, *, contract, title="fam"):
    from learnloop.services import activities as A
    family_id = repo.ensure_activity_family(purpose="practice", legacy_kind=None, title=title, clock=CLOCK)
    card_id = repo.ensure_activity_card(family_id=family_id, clock=CLOCK)
    cv = repo.ensure_activity_card_version(card_id=card_id, version=1,
        card_contract_hash=A._canonical_hash(contract), contract_json=A._json(contract),
        schema_version=1, clock=CLOCK)
    return family_id, card_id, cv


def test_capability_change_forks_with_no_inherited_stability(repo, live):
    cid = _auto_commitment(repo)
    fam, card, prev_cv = _card_version(repo, contract={"target": "svd", "capability": "retrieval"}, title="prev")
    _, _, new_cv = _card_version(repo, contract={"target": "svd", "capability": "procedure_execution"}, title="new")
    out = DT.commit_one_edge(
        repo, commitment_id=cid, milestone="m1", selected_edge_id="e1", evidence_receipt=RECEIPT,
        fork_edit={
            "prev_contract": {"target": "svd", "capability": "retrieval"},
            "new_contract": {"target": "svd", "capability": "procedure_execution"},
            "predecessor_card_version_id": prev_cv, "forked_card_version_id": new_cv,
            "family_id": fam, "card_id": card, "shrunk_family_stage_prior": 0.2,
        },
        scheduler_algorithm_version="fsrs6", live_activation_enabled=True, clock=CLOCK,
    )
    assert out.committed and out.forked_lineage_id is not None
    state = repo.activity_card_state(card_lineage_id=out.forked_lineage_id, scheduler_algorithm_version="fsrs6")
    assert state["stability"] is None  # no inherited FSRS stability
    assert state["difficulty"] == 0.2  # only an explicitly shrunk family-stage prior


def test_surface_only_change_does_not_fork(repo, live):
    cid = _auto_commitment(repo)
    fam, card, prev_cv = _card_version(repo, contract={"target": "svd", "capability": "retrieval", "prompt": "a"}, title="pa")
    _, _, new_cv = _card_version(repo, contract={"target": "svd", "capability": "retrieval", "prompt": "b"}, title="pb")
    out = DT.commit_one_edge(
        repo, commitment_id=cid, milestone="m1", selected_edge_id="e1", evidence_receipt=RECEIPT,
        fork_edit={
            "prev_contract": {"target": "svd", "capability": "retrieval", "prompt": "a"},
            "new_contract": {"target": "svd", "capability": "retrieval", "prompt": "b"},
            "predecessor_card_version_id": prev_cv, "forked_card_version_id": new_cv,
        },
        live_activation_enabled=True, clock=CLOCK,
    )
    assert out.committed and out.forked_lineage_id is None  # surface-preserving -> no fork


# --- B3: review_required parks; never a state-preserving commit ---------------

def test_review_required_edit_parks_without_committing(repo, live):
    # B3 regression. An edit with a differing key the classifier recognizes as neither
    # cosmetic nor semantic -> review_required. Pre-fix this fell through to a
    # state-preserving commit (a transition was recorded). It must park instead.
    cid = _auto_commitment(repo)
    fam, card, prev_cv = _card_version(
        repo, contract={"target": "svd", "capability": "retrieval", "mystery_field": "a"}, title="mp")
    _, _, new_cv = _card_version(
        repo, contract={"target": "svd", "capability": "retrieval", "mystery_field": "b"}, title="mq")
    out = DT.commit_one_edge(
        repo, commitment_id=cid, milestone="m1", selected_edge_id="e1", evidence_receipt=RECEIPT,
        fork_edit={
            "prev_contract": {"target": "svd", "capability": "retrieval", "mystery_field": "a"},
            "new_contract": {"target": "svd", "capability": "retrieval", "mystery_field": "b"},
            "predecessor_card_version_id": prev_cv, "forked_card_version_id": new_cv,
        },
        live_activation_enabled=True, clock=CLOCK,
    )
    assert not out.committed
    assert out.kind == "authoring_needed" and out.reason == "edit_requires_review"
    kinds = _events(repo, cid)
    assert "depth_transition_committed" not in kinds
    assert "depth_milestone_reached" not in kinds


# --- B4: U-018 belt-and-suspenders + retry idempotency ------------------------

def test_argument_alone_cannot_activate_while_constant_off(repo):
    # B4 regression. No `live` fixture: LIVE_ACTIVATION_ENABLED stays False. Pre-fix the
    # live=True ARGUMENT alone activated; now it is AND-ed with the module constant, so
    # the argument alone can never activate.
    cid = _auto_commitment(repo)
    out = DT.commit_one_edge(repo, commitment_id=cid, milestone="m1", selected_edge_id="e1",
                             evidence_receipt=RECEIPT, live_activation_enabled=True, clock=CLOCK)
    assert not out.committed and out.kind == "suggest_next"
    assert "depth_milestone_reached" not in _events(repo, cid)


def test_commit_one_edge_retry_is_idempotent(repo, live):
    # B4 regression. Pre-fix the step-7 milestone/transition writes were separate
    # self-committing calls, so replaying the same decision appended a SECOND
    # milestone + transition. Dedup on the decision receipt makes the retry a no-op.
    cid = _auto_commitment(repo)
    r1 = DT.commit_one_edge(repo, commitment_id=cid, milestone="m1", selected_edge_id="e1",
                            evidence_receipt=RECEIPT, live_activation_enabled=True, clock=CLOCK)
    r2 = DT.commit_one_edge(repo, commitment_id=cid, milestone="m1", selected_edge_id="e1",
                            evidence_receipt=RECEIPT, live_activation_enabled=True, clock=CLOCK)
    assert r1.committed and r2.committed
    kinds = _events(repo, cid)
    assert kinds.count("depth_milestone_reached") == 1
    assert kinds.count("depth_transition_committed") == 1
    assert r1.events[1] == r2.events[1]  # same transition event id on replay


def test_fork_retry_does_not_duplicate_lineage(repo, live):
    # B4 regression. A fork + its step-7 events are one transaction and idempotent on
    # the receipt, so a retry neither double-commits events nor mints a second lineage.
    cid = _auto_commitment(repo)
    fam, card, prev_cv = _card_version(repo, contract={"target": "svd", "capability": "retrieval"}, title="fp")
    _, _, new_cv = _card_version(repo, contract={"target": "svd", "capability": "procedure_execution"}, title="fn")
    fork_edit = {
        "prev_contract": {"target": "svd", "capability": "retrieval"},
        "new_contract": {"target": "svd", "capability": "procedure_execution"},
        "predecessor_card_version_id": prev_cv, "forked_card_version_id": new_cv,
        "family_id": fam, "card_id": card, "shrunk_family_stage_prior": 0.2,
    }
    r1 = DT.commit_one_edge(repo, commitment_id=cid, milestone="m1", selected_edge_id="e1",
                            evidence_receipt=RECEIPT, fork_edit=fork_edit,
                            scheduler_algorithm_version="fsrs6", live_activation_enabled=True, clock=CLOCK)
    r2 = DT.commit_one_edge(repo, commitment_id=cid, milestone="m1", selected_edge_id="e1",
                            evidence_receipt=RECEIPT, fork_edit=fork_edit,
                            scheduler_algorithm_version="fsrs6", live_activation_enabled=True, clock=CLOCK)
    assert r1.forked_lineage_id == r2.forked_lineage_id
    kinds = _events(repo, cid)
    assert kinds.count("depth_transition_committed") == 1
    state = repo.activity_card_state(card_lineage_id=r1.forked_lineage_id, scheduler_algorithm_version="fsrs6")
    assert state["stability"] is None and state["difficulty"] == 0.2
