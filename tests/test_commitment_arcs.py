"""P3 slice 3 -- commitment arcs + depth authorization (spec §10, §15.6.1).

Arcs compose the LANDED P1 commitment/depth substrate: they record achieved stages
and request AT MOST ONE reviewed inside-envelope transition, never creating an edge,
widening an envelope, or transferring scheduling state across a fork. hold/suggest
never auto-activate; auto_within_envelope (U-018 gate on) activates exactly one edge.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import commitment_arcs as ARC
from learnloop.services import commitments as C
from learnloop.services import depth_transition as DT

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)
RECEIPT = {"qualifies": True, "evidence_receipt": "run1", "decision_id": "d1"}


@pytest.fixture
def repo(tmp_path):
    return Repository(tmp_path / "state.sqlite")


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setattr(DT, "LIVE_ACTIVATION_ENABLED", True)


def _commitment(repo, *, policy="auto_within_envelope", edges=None):
    cm = C.create_commitment(
        repo, action="help_me_remember", intent_text="learn spectral theorem",
        targets=[{"target_kind": "source_locator", "target_ref": "s1", "role": "required"}],
        depth_preset="remember_key_ideas", clock=CLOCK,
    )
    reviewed = edges if edges is not None else [
        {"edge_id": "e1", "reviewed": True, "predecessor_milestone": "comprehend", "milestone_slug": "complete"},
        {"edge_id": "e2", "reviewed": True, "predecessor_milestone": "complete", "milestone_slug": "retrieve"},
    ]
    C.change_depth_envelope(repo, commitment_id=cm.id, bounds={"capability_additions": ["procedure_execution"]},
                            reviewed_edges=reviewed, allow_widen=True, clock=CLOCK)
    C.change_depth_policy(repo, commitment_id=cm.id, policy=policy, clock=CLOCK)
    return cm.id


def test_arc_pins_depth_and_maps_stages(repo):
    cid = _commitment(repo)
    arc = ARC.create_arc(repo, commitment_id=cid, source_id="src1", clock=CLOCK)
    head = C.resolve_head(repo, cid)
    assert arc["depth_policy_version_id"] == head.depth_policy_version_id
    assert arc["depth_envelope_version_id"] == head.depth_envelope_version_id
    assert arc["stage_milestone_map"]["comprehend"] == "e1"
    assert arc["stages"][0] == "comprehend"


def test_project_arc_rebuilds_deterministically(repo):
    # F7: a real §15.10 rebuild -- corrupt the durable arc log with spurious rows and
    # assert the re-projection equals the pre-corruption head (not f(x) == f(x)).
    cid = _commitment(repo)
    arc = ARC.create_arc(repo, commitment_id=cid, source_id="src1", clock=CLOCK)
    arc_id = arc["arc_id"]
    ARC.advance_arc(repo, arc_id=arc_id, stage="comprehend",
                    evidence_receipt={"evidence_receipt": "e1", "decision_id": "d1"}, clock=CLOCK)
    pre = ARC.project_arc(repo, arc_id=arc_id)
    assert "comprehend" in pre["reached_stages"]

    with repo.connection() as c:
        # A duplicate of an already-reached stage + an unknown-kind row: a pure
        # dedup-fold over the event log must ignore both on rebuild.
        c.execute(
            "INSERT INTO commitment_arc_events(id, arc_id, event_ordinal, kind, "
            "detail_json, receipt_key, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("junk_dup", arc_id, 900, "stage_reached", '{"stage": "comprehend"}', None,
             "2099-01-01T00:00:00Z"),
        )
        c.execute(
            "INSERT INTO commitment_arc_events(id, arc_id, event_ordinal, kind, "
            "detail_json, receipt_key, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("junk_kind", arc_id, 901, "prime_offered", '{"stage": "transfer"}', None,
             "2099-01-01T00:00:00Z"),
        )
        c.commit()

    assert ARC.project_arc(repo, arc_id=arc_id) == pre  # rebuilt from the corrupted log


def test_hold_and_suggest_never_auto_activate(repo):
    for policy in ("hold_at_target", "suggest_next"):
        cid = _commitment(repo, policy=policy)
        arc = ARC.create_arc(repo, commitment_id=cid, clock=CLOCK)
        out = ARC.advance_arc(repo, arc_id=arc["arc_id"], stage="comprehend",
                              evidence_receipt=RECEIPT, live_activation_enabled=True, clock=CLOCK)
        assert out["committed"] is False
        # The stage is still recorded (arc time advances) but no edge activated.
        assert ARC.project_arc(repo, arc_id=arc["arc_id"])["reached_stages"] == ["comprehend"]


def test_auto_within_envelope_activates_exactly_one_edge_and_prior_stays_reached(repo, live):
    cid = _commitment(repo)
    arc = ARC.create_arc(repo, commitment_id=cid, clock=CLOCK)
    out = ARC.advance_arc(repo, arc_id=arc["arc_id"], stage="comprehend",
                          evidence_receipt=RECEIPT, live_activation_enabled=True, clock=CLOCK)
    assert out["committed"] is True
    kinds = [e["kind"] for e in repo.commitment_arc_events(arc["arc_id"])]
    assert kinds.count("transition_committed") == 1  # exactly one
    # Prior milestone stays visibly reached after progression (§15.6.1).
    proj = ARC.project_arc(repo, arc_id=arc["arc_id"])
    assert "comprehend" in proj["reached_stages"]
    cevents = [e["kind"] for e in repo.commitment_events_for(cid)]
    assert cevents.count("depth_transition_committed") == 1


def _card_version(repo, *, contract, title):
    from learnloop.services import activities as A
    fam = repo.ensure_activity_family(purpose="practice", legacy_kind=None, title=title, clock=CLOCK)
    card = repo.ensure_activity_card(family_id=fam, clock=CLOCK)
    cv = repo.ensure_activity_card_version(
        card_id=card, version=1, card_contract_hash=A._canonical_hash(contract),
        contract_json=A._json(contract), schema_version=1, clock=CLOCK,
    )
    return fam, card, cv


def test_material_fork_has_no_fsrs_or_certification_inheritance(repo, live):
    cid = _commitment(repo)
    arc = ARC.create_arc(repo, commitment_id=cid, clock=CLOCK)
    fam, card, prev_cv = _card_version(repo, contract={"target": "svd", "capability": "retrieval"}, title="prev")
    _, _, new_cv = _card_version(repo, contract={"target": "svd", "capability": "procedure_execution"}, title="new")
    fork_edit = {
        "prev_contract": {"target": "svd", "capability": "retrieval"},
        "new_contract": {"target": "svd", "capability": "procedure_execution"},
        "predecessor_card_version_id": prev_cv, "forked_card_version_id": new_cv,
        "family_id": fam, "card_id": card, "shrunk_family_stage_prior": 0.4,
    }
    out = ARC.advance_arc(repo, arc_id=arc["arc_id"], stage="comprehend", evidence_receipt=RECEIPT,
                          fork_edit=fork_edit, live_activation_enabled=True, clock=CLOCK)
    assert out["committed"] is True
    forked_state_id = out["transition"]["forked_state_id"]
    assert forked_state_id is not None
    with repo.connection() as c:
        row = c.execute("SELECT stability, retrievability, difficulty FROM activity_card_state WHERE id = ?",
                        (forked_state_id,)).fetchone()
    assert row["stability"] is None and row["retrievability"] is None  # no inheritance
    assert row["difficulty"] == 0.4  # only the explicitly shrunk difficulty prior


def test_pause_before_next_administration_prevents_transition(repo, live):
    cid = _commitment(repo)
    arc = ARC.create_arc(repo, commitment_id=cid, clock=CLOCK)
    ARC.pause_arc(repo, arc_id=arc["arc_id"], reason="learner_paused", clock=CLOCK)
    out = ARC.advance_arc(repo, arc_id=arc["arc_id"], stage="comprehend",
                          evidence_receipt=RECEIPT, live_activation_enabled=True, clock=CLOCK)
    assert out["committed"] is False and out["reason"] == "arc_paused"
    # Arc stays intact; disposition is paused.
    assert ARC.project_arc(repo, arc_id=arc["arc_id"])["paused"] is True


def test_shrink_envelope_allowed_widen_requires_confirmed_successor(repo):
    cid = _commitment(repo)
    arc = ARC.create_arc(repo, commitment_id=cid, clock=CLOCK)
    # Shrinking (removing edges) is always allowed -- it never widens authorization.
    ARC.shrink_envelope(repo, arc_id=arc["arc_id"], bounds={}, reviewed_edges=[], clock=CLOCK)
    proj = ARC.project_arc(repo, arc_id=arc["arc_id"])
    assert proj["next_reviewed_edge"] is None  # the reviewed edge was shrunk away
    # There is NO arc method that widens an envelope; growth is a commitment concern.
    assert not hasattr(ARC, "widen_envelope")


def test_prime_is_salience_only_no_cold_credit(repo):
    cid = _commitment(repo)
    arc = ARC.create_arc(repo, commitment_id=cid, clock=CLOCK)
    offer = ARC.offer_prime(repo, arc_id=arc["arc_id"], question_ref="q1", section="N", clock=CLOCK)
    assert offer["source_hidden"] is True and offer["cold_credit"] is False
    ans = ARC.answer_prime(repo, arc_id=arc["arc_id"], question_ref="q1", clock=CLOCK)
    assert ans["cold_credit"] is False and ans["satisfies_certification"] is False


def test_advance_is_idempotent_on_decision_receipt(repo, live):
    cid = _commitment(repo)
    arc = ARC.create_arc(repo, commitment_id=cid, clock=CLOCK)
    ARC.advance_arc(repo, arc_id=arc["arc_id"], stage="comprehend", evidence_receipt=RECEIPT,
                    live_activation_enabled=True, clock=CLOCK)
    ARC.advance_arc(repo, arc_id=arc["arc_id"], stage="comprehend", evidence_receipt=RECEIPT,
                    live_activation_enabled=True, clock=CLOCK)
    events = repo.commitment_arc_events(arc["arc_id"])
    stage_events = [e for e in events if e["kind"] == "stage_reached"]
    assert len(stage_events) == 1  # replayed decision receipt is a no-op
    # F5: the transition event is receipt-keyed too -- replay appends nothing new.
    transition_events = [e for e in events if e["kind"] in ("transition_committed", "transition_requested")]
    assert len(transition_events) == 1


def test_shrink_envelope_rejects_widening(repo):
    # F4 regression: a "shrink" that actually adds authorization on a dimension
    # is rejected, naming the offending dimension. The _commitment helper
    # establishes {capability_additions: [procedure_execution]} via a confirmed
    # (allow_widen) successor; attempting to add a NEW capability through shrink
    # must fail.
    cid = _commitment(repo)
    arc = ARC.create_arc(repo, commitment_id=cid, clock=CLOCK)
    with pytest.raises(C.EnvelopeWideningRejected) as excinfo:
        ARC.shrink_envelope(
            repo, arc_id=arc["arc_id"],
            bounds={"capability_additions": ["procedure_execution", "proof_construction"]},
            reviewed_edges=[], clock=CLOCK,
        )
    assert excinfo.value.dimension == "capability_additions"


def test_shrink_envelope_allows_genuine_contraction(repo):
    # F4 regression (shrink direction): a real contraction still succeeds.
    cid = _commitment(repo)
    arc = ARC.create_arc(repo, commitment_id=cid, clock=CLOCK)
    out = ARC.shrink_envelope(
        repo, arc_id=arc["arc_id"], bounds={}, reviewed_edges=[], clock=CLOCK
    )
    assert out["shrunk"] is True
