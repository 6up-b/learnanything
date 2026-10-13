"""Registry review (spec_source_ingestion_v2 §5.7; spec_knowledge_model §3.4, §12.2).

Facet-contract cards for a subject, and the owner's merge: since facet locks
were removed (owner, 2026-10-12) it applies live through the facet-identity
merge, with the same one-tap undo as a judge's merge. (It used to file a facet
``deactivate`` review item that proposal apply could not compile.)
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.content.synthesis.source_set_synthesis import create_study_map
from learnloop.curriculum.subject_registry import (
    RegistryReviewError,
    build_subject_registry,
    propose_facet_merge,
)
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_facet

from tests.helpers import set_algorithm_version
from tests.test_source_set_synthesis import FakeSynthesisClient, _setup

_CLOCK = FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC))


def _applied_vault(tmp_path: Path):
    root, repo = _setup(tmp_path)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), brief={"depth": "intro"},
                     repository=repo, clock=_CLOCK, apply=True)
    return load_vault(root), repo, root


def test_subject_registry_facet_contract_cards(tmp_path):
    vault, repo, _root = _applied_vault(tmp_path)
    registry = build_subject_registry(vault, repo, "linear-algebra")

    assert registry["subject_id"] == "linear-algebra"
    assert registry["facet_count"] >= 1
    by_id = {card["facet_id"]: card for card in registry["facets"]}
    assert "facet_symmetry_definition" in by_id
    card = by_id["facet_symmetry_definition"]
    # The card carries the full facet contract for review.
    for key in ("claim", "kind", "conditions", "examples", "non_goals",
                "error_signatures", "instructional_repairs", "status"):
        assert key in card
    assert set(card["conditions"]) == {"preconditions", "postconditions", "applicability"}
    # This LO carries probe episodes, which used to lock the facet and disable
    # its merge; facet locks were removed, so the card carries no lock state.
    for retired_key in ("locked", "lock_reasons", "can_merge"):
        assert retired_key not in card
    assert card["version"] == 1
    assert "locked_count" not in registry
    assert "identifiability_warnings" in registry


def test_the_owner_merges_a_facet_that_used_to_be_locked_and_can_undo_it(tmp_path):
    from learnloop.content.facet_identity.actions import list_actions, undo_action

    vault, repo, root = _applied_vault(tmp_path)
    result = propose_facet_merge(vault, repo, subject_id="linear-algebra",
                                 retired_facet_id="facet_spectral_applicability",
                                 surviving_facet_id="facet_symmetry_definition",
                                 rationale="One skill.", clock=_CLOCK)
    assert result["status"] == "applied"
    merged = load_vault(root)
    assert merged.canonical_facet_id("facet_spectral_applicability") == "facet_symmetry_definition"
    (record,) = list_actions(repo)
    assert record["origin"] == "registry" and record["judge"] == "owner"
    assert result["action_id"] == record["id"] and result["undo"].endswith(record["id"])
    undo_action(root, repo, record["id"], clock=_CLOCK)
    assert "facet_spectral_applicability" in load_vault(root).evidence_facets


def test_unknown_subject_raises(tmp_path):
    vault, repo, _root = _applied_vault(tmp_path)
    try:
        build_subject_registry(vault, repo, "does-not-exist")
        raise AssertionError("expected RegistryReviewError")
    except RegistryReviewError as exc:
        assert exc.code == "unknown_subject"


def _unlocked_vault(tmp_path: Path):
    """A vault with two unlocked facets (no LO membership, no evidence) so a
    pre-lock merge is legal-with-review."""

    root = tmp_path / "vault"
    init_vault(root, clock=_CLOCK)
    add_subject(root, "topology", "Topology", clock=_CLOCK)
    set_algorithm_version(VaultPaths(root, load_vault(root).config), "mvp-0.7")
    for fid, claim in [("facet_open_set", "A set is open iff every point is interior."),
                       ("facet_open_cover", "An open cover is a family of open sets covering X.")]:
        upsert_facet(root, {"id": fid, "kind": "definition", "claim": claim,
                            "positive_examples": ["ex"], "status": "reviewed"}, clock=_CLOCK)
    return load_vault(root), Repository(root / "state.sqlite"), root


def test_propose_facet_merge_applies_live_and_records_the_owners_verdict(tmp_path):
    import sqlite3

    vault, repo, root = _unlocked_vault(tmp_path)
    before = len(repo.proposal_batches())

    result = propose_facet_merge(
        vault, repo,
        subject_id="topology",
        retired_facet_id="facet_open_cover",
        surviving_facet_id="facet_open_set",
        rationale="Confusable in review.",
    )

    assert result["status"] == "applied"
    assert result["retired_facet_id"] == "facet_open_cover"
    assert result["action"]["origin"] == "registry" and result["action"]["undoable"] is True
    # No review proposal: the merge applied, with its undo.
    assert len(repo.proposal_batches()) == before
    after = load_vault(root)
    assert "facet_open_cover" not in after.evidence_facets
    assert "facet_open_cover" in after.evidence_facets["facet_open_set"].aliases
    rows = sqlite3.connect(repo.sqlite_path).execute(
        "SELECT task, left_id, right_id, judge, verdict FROM judgment_ledger").fetchall()
    assert rows == [("same_facet", "facet_open_cover", "facet_open_set", "owner", "same")]


def test_propose_facet_merge_still_holds_back_a_shared_graded_criterion(tmp_path, monkeypatch):
    import learnloop.content.facet_identity.actions as actions

    vault, repo, root = _unlocked_vault(tmp_path)
    monkeypatch.setattr(actions, "graded_shared_criteria", lambda _vault, _repo, facets: [{
        "contract_version_id": "c1", "practice_item_id": "pi_x", "criterion_id": "k",
        "capability": "retrieval", "facets": sorted(facets),
    }])
    try:
        propose_facet_merge(vault, repo, subject_id="topology", retired_facet_id="facet_open_cover",
                            surviving_facet_id="facet_open_set")
        raise AssertionError("expected RegistryReviewError")
    except RegistryReviewError as exc:
        assert exc.code == "shared_graded_criterion"
    assert "facet_open_cover" in load_vault(root).evidence_facets


def test_coarsen_acceptance_resolves_generation_need(tmp_path):
    vault, repo, root = _unlocked_vault(tmp_path)
    need_id = repo.upsert_synthesis_generation_need(
        subject_id="topology", need_kind="coarsen_distinction",
        target_key="open_set|open_cover", missing_capability="schema_interpretation",
        facet_ids=["facet_open_set", "facet_open_cover"], clock=_CLOCK,
    )
    assert repo.synthesis_generation_needs(subject_id="topology", status="pending")

    result = propose_facet_merge(
        vault, repo, subject_id="topology",
        retired_facet_id="facet_open_cover", surviving_facet_id="facet_open_set",
        need_id=need_id,
    )
    assert result["resolved_need"] is True
    # Accepting the coarsening review item resolves the generation-need.
    assert repo.synthesis_generation_needs(subject_id="topology", status="pending") == []


def test_propose_facet_merge_rejects_self_merge(tmp_path):
    vault, repo, root = _unlocked_vault(tmp_path)
    try:
        propose_facet_merge(vault, repo, subject_id="topology",
                            retired_facet_id="facet_open_set",
                            surviving_facet_id="facet_open_set")
        raise AssertionError("expected RegistryReviewError")
    except RegistryReviewError as exc:
        assert exc.code == "invalid_merge"
