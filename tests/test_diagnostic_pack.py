"""P2 DIAGNOSTIC track -- pre-authored diagnostic pack (spec_p2 §5, §12.2; design B.4)."""

from __future__ import annotations

import pytest

from learnloop.db.repositories import Repository
from learnloop.services import diagnostic_pack as DP
from learnloop.services import golden_path_run as GPR
from learnloop.services.golden_path_fixture import (
    LO_ID,
    build_golden_path_fixture,
    stub_diagnostic_pack,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths


@pytest.fixture
def fixture(tmp_path):
    root = tmp_path / "vault"
    fx = build_golden_path_fixture(root)
    vault = load_vault(root)
    repo = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    return vault, repo, fx


def _assemble(repo, fx):
    stub = stub_diagnostic_pack()
    return DP.assemble_pack(
        repo,
        pack_slug=stub["pack_slug"],
        blueprint_version_id=fx.blueprint_version_id,
        cards=stub["cards"],
    )


def _admit_and_review(repo, pack):
    for card in pack.cards:
        DP.admit_pack_card(repo, pack_id=pack.pack_id, card_slug=card.card_slug)
    return DP.review_pack(repo, pack_id=pack.pack_id)


def test_pack_assembly_is_deterministic_and_idempotent(fixture):
    _vault, repo, fx = fixture
    p1 = _assemble(repo, fx)
    p2 = _assemble(repo, fx)
    assert p1.content_hash == p2.content_hash
    assert p1.pack_id == p2.pack_id
    assert p1.minted is True and p2.minted is False  # second re-assembly reuses the row


def test_pack_uses_only_stub_cards_within_2_to_4(fixture):
    _vault, repo, fx = fixture
    pack = _assemble(repo, fx)
    assert 2 <= len(pack.cards) <= 4
    assert {c.card_slug for c in pack.cards} == {c["card_slug"] for c in stub_diagnostic_pack()["cards"]}


def test_pack_rejects_wrong_card_count(fixture):
    _vault, repo, fx = fixture
    with pytest.raises(DP.InvalidPack):
        DP.assemble_pack(repo, pack_slug="p", blueprint_version_id=fx.blueprint_version_id,
                         cards=[{"card_slug": "solo", "coverage": ["x"]}])


def test_pack_rejects_unstable_repair_without_disclosure(fixture):
    _vault, repo, fx = fixture
    with pytest.raises(DP.InvalidPack):
        DP.assemble_pack(
            repo, pack_slug="p", blueprint_version_id=fx.blueprint_version_id,
            cards=[
                {"card_slug": "a", "coverage": ["x"], "repair_unstable": True},
                {"card_slug": "b", "coverage": ["y"]},
            ],
        )


def test_cards_enter_candidate_and_review_requires_admission(fixture):
    _vault, repo, fx = fixture
    pack = _assemble(repo, fx)
    assert all(c.admission_status == "candidate" for c in pack.cards)
    # review before admission fails closed (§5.1 nothing enters unreviewed).
    with pytest.raises(DP.InvalidPack):
        DP.review_pack(repo, pack_id=pack.pack_id)
    reviewed = _admit_and_review(repo, pack)
    assert reviewed.status == "reviewed"
    assert all(c.admission_status == "admitted" for c in reviewed.cards)
    # admission + review events are append-only artifacts (U-028 provenance).
    kinds = [e["kind"] for e in repo.diagnostic_pack_events_for(pack.pack_id)]
    assert kinds.count("admitted") == len(pack.cards)
    assert "reviewed" in kinds and "registered" in kinds


def test_pin_binds_pack_to_run_and_goal_contract_version(fixture):
    _vault, repo, fx = fixture
    pack = _admit_and_review(repo, _assemble(repo, fx))
    pin = DP.pin_pack_to_run(repo, run_id=fx.receipt.run_id, pack_id=pack.pack_id)
    run = repo.golden_path_run(fx.receipt.run_id)
    assert pin["goal_contract_version_id"] == run["goal_contract_version_id"]
    assert pin["pack_id"] == pack.pack_id
    # one pin per run -- a re-pin returns the same pin, never a second.
    again = DP.pin_pack_to_run(repo, run_id=fx.receipt.run_id, pack_id=pack.pack_id)
    assert again["id"] == pin["id"]


def test_pin_requires_reviewed_pack(fixture):
    _vault, repo, fx = fixture
    pack = _assemble(repo, fx)  # draft, un-admitted
    with pytest.raises(DP.InvalidPack):
        DP.pin_pack_to_run(repo, run_id=fx.receipt.run_id, pack_id=pack.pack_id)


def test_visible_cap_is_clamped_into_the_2_to_4_band(fixture):
    _vault, repo, fx = fixture
    assert DP.clamp_visible_cap(None) == 4
    assert DP.clamp_visible_cap(1) == 2
    assert DP.clamp_visible_cap(9) == 4
    assert DP.clamp_visible_cap(3) == 3


def test_enter_baseline_composes_probe_episode_and_pins(fixture):
    vault, repo, fx = fixture
    pack = _admit_and_review(repo, _assemble(repo, fx))
    result = DP.enter_baseline(
        vault, repo, run_id=fx.receipt.run_id, learning_object_id=LO_ID, pack_id=pack.pack_id
    )
    # P2 orchestrates the LANDED probe episode -- it mints no second posterior.
    assert result["episode_id"]
    pin = repo.diagnostic_pack_pin_for_run(fx.receipt.run_id)
    assert pin is not None and pin["probe_episode_id"] == result["episode_id"]
    assert pin["visible_cap"] == 4


def test_boundary_view_projects_blueprint_cells_as_untested(fixture):
    _vault, repo, fx = fixture
    view = DP.boundary_view(repo, run_id=fx.receipt.run_id)
    assert view["cells"]  # facet x capability cells from the blueprint's solution recipe
    assert all(c["status"] in DP.BOUNDARY_CELL_STATES for c in view["cells"])
    # baseline projection: every declared cell is 'untested' (not 'cannot'), no mastery table.
    assert all(c["status"] == "untested" for c in view["cells"])
