"""P3 slice 3 -- learner Q+A authoring, coach, and in-review maintenance (§9, §15.5)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import activities as A
from learnloop.services import card_lineage as CL
from learnloop.services import reader_authoring as AUTH

from tests.helpers import NOW

CLOCK = FrozenClock(NOW)


@pytest.fixture
def repo(tmp_path):
    return Repository(tmp_path / "state.sqlite")


def _contract_of(repo, card_version_id):
    with repo.connection() as c:
        row = c.execute("SELECT contract_json FROM activity_card_versions WHERE id = ?",
                        (card_version_id,)).fetchone()
    import json
    return json.loads(row["contract_json"])


def test_qa_persists_verbatim_before_ai_and_pins_under_commitment(repo):
    result = AUTH.author_qa(
        repo, question="Why do symmetric matrices have real eigenvalues?",
        answer="Because A = A^T makes the quadratic form real.",
        source_id="src1", revision_id="rev1", client_idempotency_key="qa1", clock=CLOCK,
    )
    assert result["authored_before_ai"] is True
    assert result["authorship"] == "learner" and result["pinned"] is True
    # The learner's EXACT surface is preserved on the durable card contract.
    contract = _contract_of(repo, result["card_version_id"])
    assert contract["prompt"] == "Why do symmetric matrices have real eigenvalues?"
    assert contract["expected_answer"] == "Because A = A^T makes the quadratic form real."
    assert contract["authorship"] == "learner"
    # A durable commitment + genesis lineage exist (composed P1 substrate).
    assert result["commitment_id"] and result["lineage_id"]
    assert repo.commitment(result["commitment_id"]) is not None  # commitment durably persisted


def test_qa_confirms_once_idempotently(repo):
    a = AUTH.author_qa(repo, question="q?", answer="a", client_idempotency_key="k", clock=CLOCK)
    b = AUTH.author_qa(repo, question="q?", answer="a", client_idempotency_key="k", clock=CLOCK)
    assert a["commitment_id"] == b["commitment_id"]  # one confirmation, no duplicate commitment


def test_qa_requires_both_question_and_answer(repo):
    with pytest.raises(AUTH.AuthoringError):
        AUTH.author_qa(repo, question="q?", answer="   ", clock=CLOCK)


def test_coach_lint_is_dismissible_and_never_blocks(repo):
    for level in AUTH.COACH_LEVELS:
        out = AUTH.coach_lint(question="x", answer="y", level=level)
        assert out["blocking"] is False
        assert isinstance(out["suggestions"], list)


def test_coach_response_is_corpus_only_salience(repo):
    out = AUTH.record_coach_response(repo, commitment_id="c1", level="expert", response="dismiss", clock=CLOCK)
    assert out["corpus_only"] is True
    # It is a salience-only event; the firewall rejects it as evidence.
    from learnloop.services.salience_firewall import reject_salience, SalienceEvidenceRejected
    ev = repo.reader_interaction_events(kind="reader_action_invoked")[0]
    with pytest.raises(SalienceEvidenceRejected):
        reject_salience(ev)


def test_ai_sibling_never_impersonates_learner_authorship(repo):
    authored = AUTH.author_qa(repo, question="q?", answer="a", family_title="fam", clock=CLOCK)
    sibling = AUTH.mint_ai_sibling(
        repo, family_id=authored["family_id"],
        predecessor_card_version_id=authored["card_version_id"],
        question="transfer variant?", answer="a2", clock=CLOCK,
    )
    assert sibling["authorship"] == "ai"
    contract = _contract_of(repo, sibling["card_version_id"])
    assert contract["authorship"] == "ai"
    assert _contract_of(repo, authored["card_version_id"])["authorship"] == "learner"


# ── fluid maintenance (§9.3) ──────────────────────────────────────────────────

def _cv(repo, contract, title):
    fam = repo.ensure_activity_family(purpose="practice", legacy_kind=None, title=title, clock=CLOCK)
    card = repo.ensure_activity_card(family_id=fam, clock=CLOCK)
    cv = repo.ensure_activity_card_version(card_id=card, version=1,
                                           card_contract_hash=A._canonical_hash(contract),
                                           contract_json=A._json(contract), schema_version=1, clock=CLOCK)
    return fam, card, cv


def test_cosmetic_edit_retains_state_only_through_classifier(repo):
    prev = {"target": "svd", "capability": "retrieval", "prompt": "What is the SVD?"}
    new = {"target": "svd", "capability": "retrieval", "prompt": "Define the SVD."}
    fam, card, v1 = _cv(repo, prev, "e")
    _, _, v2 = _cv(repo, new, "e2")
    lineage = CL.start_lineage(repo, genesis_card_version_id=v1, family_id=fam, card_id=card, clock=CLOCK)
    out = AUTH.maintain(repo, action="edit", lineage_id=lineage, from_card_version_id=v1,
                        to_card_version_id=v2, prev_contract=prev, new_contract=new, clock=CLOCK)
    assert out["verdict"] == "surface_preserving" and out["retains_state"] is True


def test_material_edit_forks_without_blind_transfer(repo):
    prev = {"target": "svd", "capability": "retrieval"}
    new = {"target": "svd", "capability": "procedure_execution"}
    fam, card, v1 = _cv(repo, prev, "m")
    _, _, v2 = _cv(repo, new, "m2")
    out = AUTH.maintain(repo, action="edit", from_card_version_id=v1, to_card_version_id=v2,
                        prev_contract=prev, new_contract=new, clock=CLOCK)
    assert out["verdict"] == "fork_required" and out["retains_state"] is False
    assert out["fork"]["lineage_id"]


def test_split_merge_spawn_create_lineage(repo):
    c = {"target": "svd", "capability": "retrieval"}
    fam, card, v1 = _cv(repo, c, "s")
    _, _, v2 = _cv(repo, c, "s2")
    split = AUTH.maintain(repo, action="split", from_card_version_id=v1, split_card_version_id=v2, clock=CLOCK)
    assert split["new_lineage_id"]
    into = CL.start_lineage(repo, genesis_card_version_id=v1, family_id=fam, card_id=card, clock=CLOCK)
    merge = AUTH.maintain(repo, action="merge", into_lineage_id=into, from_card_version_id=v2,
                          merged_card_version_id=v1, clock=CLOCK)
    assert merge["merge_edge_id"]
    spawn = AUTH.maintain(repo, action="spawn", from_card_version_id=v1, forked_card_version_id=v2, clock=CLOCK)
    assert spawn["lineage_id"]


def test_retirement_preserves_commitment_and_evidence(repo):
    authored = AUTH.author_qa(repo, question="q?", answer="a", clock=CLOCK)
    out = AUTH.maintain(repo, action="retire", commitment_id=authored["commitment_id"], clock=CLOCK)
    assert out["evidence_preserved"] is True
    # The commitment still exists (retirement is a disposition event, not a delete).
    from learnloop.services import commitments as C
    assert C.resolve_head(repo, authored["commitment_id"]) is not None
