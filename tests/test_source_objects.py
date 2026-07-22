"""Source objects, relations, and canonical mapping proposals (spec §7, §15.2)."""

from __future__ import annotations

from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.services import source_objects as SO
from tests.test_source_inventory import _register_revision


def _repo(tmp_path: Path) -> Repository:
    repo = Repository(tmp_path / "s.sqlite")
    _register_revision(repo, source_id="src1", revision_id="rev1")
    return repo


def test_author_begins_proposed_and_review_is_append_only(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    obj = SO.author_source_object(
        repo, source_id="src1", revision_id="rev1", object_type="definition",
        exact_text="A symmetric matrix equals its transpose.",
        citations=[{"span_id": "s1", "revision_id": "rev1"}],
    )
    assert obj["status"] == "proposed"
    head = repo.source_object_head(obj["source_object_id"])
    assert head["version"]["status"] == "proposed"
    assert len(head["citations"]) == 1
    # Review appends a successor; the prior version remains for audit.
    SO.review_source_object(repo, source_object_id=obj["source_object_id"], status="reviewed")
    assert repo.source_object_head(obj["source_object_id"])["version"]["status"] == "reviewed"


def test_connect_it_relation_defaults_to_learner_connects_proposal(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    a = SO.author_source_object(repo, source_id="src1", revision_id="rev1", object_type="claim", exact_text="A")
    b = SO.author_source_object(repo, source_id="src1", revision_id="rev1", object_type="claim", exact_text="B")
    rel = SO.link_relation(
        repo, source_object_id=a["source_object_id"], related_object_id=b["source_object_id"],
        learner_text="these say the same thing",
    )
    assert rel["relation_type"] == "learner_connects"  # never a canonical edge
    assert rel["review_status"] == "proposed"


def test_mapping_proposal_accept_and_reject_are_non_destructive(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    obj = SO.author_source_object(repo, source_id="src1", revision_id="rev1", object_type="claim", exact_text="A")
    p = SO.propose_mapping(repo, target_kind="facet", source_object_id=obj["source_object_id"],
                           annotation_id="ann1", confidence=0.7, rationale="candidate facet")
    accepted = SO.accept_mapping(repo, proposal_id=p["proposal_id"])
    assert accepted["status"] == "accepted"
    # Accepting a mapping does not overwrite the source object (§7.3).
    assert repo.source_object_head(obj["source_object_id"])["version"]["status"] == "proposed"
    q = SO.propose_mapping(repo, target_kind="lo", source_object_id=obj["source_object_id"], annotation_id="ann1")
    SO.reject_mapping(repo, proposal_id=q["proposal_id"])
    # Rejecting one mapping leaves other proposals + the source object intact.
    assert repo.source_object_head(obj["source_object_id"])["version"]["status"] == "proposed"
    inbox = SO.proposal_inbox(repo, status="accepted")
    assert any(pr["id"] == p["proposal_id"] for pr in inbox["proposals"])
