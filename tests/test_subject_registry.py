"""Registry review (spec_source_ingestion_v2 §5.7; spec_knowledge_model §3.4, §12.2).

Facet-contract cards for a subject, lock state, and a pre-lock merge that creates
a REVIEW proposal (never auto-merge).
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
    # This LO carries probe episodes, so the facet identity is locked; the card
    # surfaces the lock and disables pre-lock merge with the reason.
    assert card["locked"] is True
    assert card["can_merge"] is False
    assert card["lock_reasons"] and card["lock_reasons"][0]["source"] == "probe"
    assert "identifiability_warnings" in registry


def test_propose_merge_refused_when_facet_identity_locked(tmp_path):
    vault, repo, _root = _applied_vault(tmp_path)
    try:
        propose_facet_merge(vault, repo, subject_id="linear-algebra",
                            retired_facet_id="facet_spectral_applicability",
                            surviving_facet_id="facet_symmetry_definition")
        raise AssertionError("expected RegistryReviewError")
    except RegistryReviewError as exc:
        assert exc.code == "facet_identity_locked"


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


def test_propose_facet_merge_creates_review_item_never_auto_merges(tmp_path):
    vault, repo, root = _unlocked_vault(tmp_path)
    before = len(repo.proposal_batches())

    result = propose_facet_merge(
        vault, repo,
        subject_id="topology",
        retired_facet_id="facet_open_cover",
        surviving_facet_id="facet_open_set",
        rationale="Confusable in review.",
    )

    assert result["proposal_id"] is not None
    assert result["retired_facet_id"] == "facet_open_cover"
    # A NEW review proposal was created — the merge was NOT auto-applied.
    assert len(repo.proposal_batches()) == before + 1
    # The facet is still present in the vault (retirement only happens on accept).
    assert "facet_open_cover" in load_vault(root).evidence_facets

    # The proposal item is a pending facet deactivate carrying the survivor.
    batch = next(b for b in repo.proposal_batches() if b["id"] == result["proposal_id"])
    assert batch["purpose"] == "facet_merge"
    item = repo.proposal_items(result["proposal_id"])[0]
    assert item["item_type"] == "facet"
    assert item["operation"] == "deactivate"
    assert item["target_entity_id"] == "facet_open_cover"
    assert item["decision"] == "pending"


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
