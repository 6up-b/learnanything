from __future__ import annotations

import json

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from learnloop.cli import _parse_mode_mix, app
from learnloop.clock import FrozenClock
from learnloop.content.proposals.ai_contracts import (
    AuthoringProposal,
    PracticeItemPatchPayload,
    RubricCriterionPayload,
)
from learnloop.db.repositories import Repository
from learnloop.content.proposals.proposals import _practice_item_rubric_errors, persist_authoring_proposal

from tests.helpers import NOW, create_basic_vault
from tests.test_cli_generate_practice import _ProposalServer, _complete_probe, _configure_codex


# --- --los gating ---------------------------------------------------------


def test_generate_practice_los_unknown_id_errors(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _complete_probe(paths.sqlite_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["generate-practice", "--vault", str(vault_root), "--los", "lo_missing", "--dry-run", "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["error"] == "invalid_generation_request"
    assert "Unknown learning object id: lo_missing" in payload["message"]


def test_generate_practice_los_keeps_completed_probe_gate(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)  # no completed probe
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["generate-practice", "--vault", str(vault_root), "--los", "lo_svd_definition", "--dry-run", "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["error"] == "invalid_generation_request"
    assert "no completed probe" in payload["message"]


def test_generate_practice_los_bypasses_item_count_deficit_gate(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _complete_probe(paths.sqlite_path)
    runner = CliRunner()
    # target 1 item per LO and the LO already has 1 active item -> no deficit.
    base = ["generate-practice", "--vault", str(vault_root), "--target-items-per-lo", "1", "--dry-run", "--json"]

    without_los = runner.invoke(app, base)
    assert without_los.exit_code == 0, without_los.output
    assert json.loads(without_los.output)["plan"]["targets"] == []

    with_los = runner.invoke(app, [*base, "--los", "lo_svd_definition"])
    assert with_los.exit_code == 0, with_los.output
    targets = json.loads(with_los.output)["plan"]["targets"]
    assert [target["learning_object_id"] for target in targets] == ["lo_svd_definition"]
    # Past-deficit named LOs still request at least one item.
    assert targets[0]["requested_new_items"] == 1


def test_generate_practice_los_composes_with_focus_concepts_filter(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _complete_probe(paths.sqlite_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "generate-practice",
            "--vault",
            str(vault_root),
            "--los",
            "lo_svd_definition",
            "--focus-concepts",
            "other_concept",
            "--dry-run",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["plan"]["targets"] == []


# --- --mode-mix parsing ---------------------------------------------------


def test_parse_mode_mix_valid():
    assert _parse_mode_mix("teach_back=2,short_answer=3") == {"teach_back": 2, "short_answer": 3}
    assert _parse_mode_mix(" teach_back = 1 ") == {"teach_back": 1}
    assert _parse_mode_mix(None) is None
    assert _parse_mode_mix("") is None


@pytest.mark.parametrize(
    "raw",
    [
        "teach_back",  # missing =count
        "=2",  # empty mode
        "teach_back=zero",  # non-integer
        "teach_back=0",  # count < 1
        "teach_back=-1",
        "teach_back=1,teach_back=2",  # duplicate mode
        ",",  # nothing parseable
    ],
)
def test_parse_mode_mix_rejects_malformed(raw):
    with pytest.raises(ValueError):
        _parse_mode_mix(raw)


def test_generate_practice_mode_mix_parse_error_exits_with_json_error(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _complete_probe(paths.sqlite_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["generate-practice", "--vault", str(vault_root), "--mode-mix", "teach_back=0", "--dry-run", "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["error"] == "invalid_mode_mix"
    assert "teach_back" in payload["message"]


def test_generate_practice_mode_mix_drives_requested_item_counts(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _complete_probe(paths.sqlite_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "generate-practice",
            "--vault",
            str(vault_root),
            "--mode-mix",
            "teach_back=1,short_answer=2",
            "--dry-run",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    plan = json.loads(result.output)["plan"]
    assert plan["targets"][0]["requested_new_items"] == 3
    assert plan["requested_new_items"] == 3


# --- --mode-mix generation flow ------------------------------------------


def test_generate_practice_mode_mix_adds_hard_constraint_and_teach_back_guidance(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _complete_probe(paths.sqlite_path)
    checkout = tmp_path / "codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")
    server = _ProposalServer(_teach_back_proposal_payload())
    server.start()
    try:
        _configure_codex(vault_root, checkout, server.base_url)
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "generate-practice",
                "--vault",
                str(vault_root),
                "--los",
                "lo_svd_definition",
                "--mode-mix",
                "teach_back=1",
                "--json",
            ],
        )
    finally:
        server.stop()

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["proposal_id"]
    assert payload["mode_mix_warnings"] == []
    instructions = server.requests[0]["body"]["context"]["instructions"]
    assert "Hard practice-mode mix constraint" in instructions
    assert "1 item(s) with practice_mode='teach_back'" in instructions
    assert "teach_back item format" in instructions
    assert "tier='core'" in instructions
    assert "tier='transfer'" in instructions
    item = Repository(paths.sqlite_path).proposal_items(payload["proposal_id"])[0]
    assert item["validation_status"] == "valid", item["validation_errors"]


def test_generate_practice_mode_mix_teach_back_count_violation_is_hard(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _complete_probe(paths.sqlite_path)
    checkout = tmp_path / "codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")
    # Requested two teach_back items; the proposal only carries one.
    server = _ProposalServer(_teach_back_proposal_payload())
    server.start()
    try:
        _configure_codex(vault_root, checkout, server.base_url)
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "generate-practice",
                "--vault",
                str(vault_root),
                "--los",
                "lo_svd_definition",
                "--mode-mix",
                "teach_back=2",
                "--json",
            ],
        )
    finally:
        server.stop()

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["error"] == "mode_mix_violation"
    assert payload["proposal_id"]
    assert payload["mode_mix_violations"] == [
        "lo_svd_definition: requested 2 'teach_back' item(s), proposal has 1"
    ]


def test_generate_practice_mode_mix_other_mode_mismatch_soft_warns(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _complete_probe(paths.sqlite_path)
    checkout = tmp_path / "codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")
    # Proposal has zero short_answer items while two were requested.
    server = _ProposalServer(_teach_back_proposal_payload())
    server.start()
    try:
        _configure_codex(vault_root, checkout, server.base_url)
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "generate-practice",
                "--vault",
                str(vault_root),
                "--los",
                "lo_svd_definition",
                "--mode-mix",
                "teach_back=1,short_answer=2",
                "--json",
            ],
        )
    finally:
        server.stop()

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["proposal_id"]
    assert payload["mode_mix_warnings"] == [
        "lo_svd_definition: requested 2 'short_answer' item(s), proposal has 0"
    ]


# --- proposals validation --------------------------------------------------


def test_teach_back_item_without_rubric_is_invalid_despite_default_rubrics(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    payload = _teach_back_item_dict()
    del payload["payload"]["grading_rubric"]
    del payload["payload"]["criterion_facet_weights"]
    proposal = AuthoringProposal.model_validate(_proposal_wrapper([payload]))

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    item = Repository(vault_root / "state.sqlite").proposal_items(patch_id)[0]

    assert item["validation_status"] == "invalid"
    assert item["validation_errors"] == ["missing_rubric:teach_back"]


def test_teach_back_item_with_unmapped_criterion_is_invalid(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    payload = _teach_back_item_dict()
    del payload["payload"]["criterion_facet_weights"]["transfer_rank"]
    proposal = AuthoringProposal.model_validate(_proposal_wrapper([payload]))

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    item = Repository(vault_root / "state.sqlite").proposal_items(patch_id)[0]

    assert item["validation_status"] == "invalid"
    assert "teach_back_unmapped_criterion:transfer_rank" in item["validation_errors"]


def test_teach_back_item_missing_core_criterion_for_facet_is_invalid(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    payload = _teach_back_item_dict()
    # Remap the geometry core criterion onto recall: the geometry facet is now
    # only reachable through a transfer criterion.
    payload["payload"]["criterion_facet_weights"]["core_geometry"] = {"recall": 1.0}
    proposal = AuthoringProposal.model_validate(_proposal_wrapper([payload]))

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    item = Repository(vault_root / "state.sqlite").proposal_items(patch_id)[0]

    assert item["validation_status"] == "invalid"
    assert "teach_back_missing_core_criterion:geometry" in item["validation_errors"]


def test_well_formed_teach_back_item_is_valid(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal = AuthoringProposal.model_validate(_proposal_wrapper([_teach_back_item_dict()]))

    patch_id = persist_authoring_proposal(vault_root, proposal, provider="codex", clock=FrozenClock(NOW))
    item = Repository(vault_root / "state.sqlite").proposal_items(patch_id)[0]

    assert item["validation_status"] == "valid", item["validation_errors"]


def test_rubric_errors_reject_bad_tier_value():
    # Edited payloads bypass the pydantic Literal, so the dict-level validator
    # must catch bad tiers.
    payload = {
        "grading_rubric": {
            "max_points": 4,
            "criteria": [
                {"id": "core_recall", "points": 2, "description": "ok", "tier": "core"},
                {"id": "weird", "points": 2, "description": "bad tier", "tier": "bonus"},
            ],
            "fatal_errors": [],
        }
    }

    errors = _practice_item_rubric_errors(payload)

    assert errors == ["invalid_grading_rubric:criterion_tier:weird"]


# --- payload schema round-trip ---------------------------------------------


def test_rubric_criterion_payload_tier_round_trip():
    transfer = RubricCriterionPayload.model_validate(
        {"id": "transfer_rank", "points": 1, "description": "What if rank deficient?", "tier": "transfer"}
    )
    assert transfer.tier == "transfer"
    assert transfer.model_dump()["tier"] == "transfer"

    default = RubricCriterionPayload.model_validate({"id": "core_recall", "points": 1, "description": "Recall."})
    assert default.tier == "core"

    with pytest.raises(ValidationError):
        RubricCriterionPayload.model_validate(
            {"id": "bad", "points": 1, "description": "Bad tier.", "tier": "bonus"}
        )


def test_practice_item_patch_payload_accepts_tiered_rubric():
    payload = PracticeItemPatchPayload.model_validate(_teach_back_item_dict()["payload"])

    assert payload.practice_mode == "teach_back"
    assert payload.grading_rubric is not None
    tiers = {criterion.id: criterion.tier for criterion in payload.grading_rubric.criteria}
    assert tiers == {
        "core_recall": "core",
        "core_geometry": "core",
        "transfer_rank": "transfer",
        "transfer_rotation": "transfer",
    }
    dumped = payload.model_dump(mode="json", exclude_none=True)
    round_trip = PracticeItemPatchPayload.model_validate(dumped)
    assert round_trip == payload


# --- helpers ----------------------------------------------------------------


def _proposal_wrapper(items: list[dict]) -> dict:
    return {
        "summary": "Teach-back practice items",
        "source_refs": [{"ref_type": "existing_entity", "ref_id": "lo_svd_definition"}],
        "items": items,
    }


def _teach_back_item_dict(entity_id: str = "pi_svd_teach_001") -> dict:
    return {
        "client_item_id": entity_id,
        "item_type": "practice_item",
        "operation": "create",
        "proposed_entity_id": entity_id,
        "source_ref_ids": ["lo_svd_definition"],
        "rationale": "Teach-back coverage of the SVD definition.",
        "review_route": "review_required",
        "payload": {
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "teach_back",
            "attempt_types_allowed": ["teach_back"],
            "prompt": "Explain the singular value decomposition to a student who has never seen it.",
            "expected_answer": "Covers the factorization into U, Sigma, and V transpose and its geometry.",
            "evidence_facets": ["recall", "geometry"],
            "evidence_weights": {"recall": 0.5, "geometry": 0.5},
            "criterion_facet_weights": {
                "core_recall": {"recall": 1.0},
                "core_geometry": {"geometry": 1.0},
                "transfer_rank": {"recall": 1.0},
                "transfer_rotation": {"geometry": 1.0},
            },
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {"id": "core_recall", "points": 1, "description": "Names the three factors.", "tier": "core"},
                    {
                        "id": "core_geometry",
                        "points": 1,
                        "description": "Explains the rotate-scale-rotate picture.",
                        "tier": "core",
                    },
                    {
                        "id": "transfer_rank",
                        "points": 1,
                        "description": "What happens for a rank-deficient matrix?",
                        "tier": "transfer",
                    },
                    {
                        "id": "transfer_rotation",
                        "points": 1,
                        "description": "What if the matrix is already a rotation?",
                        "tier": "transfer",
                    },
                ],
                "fatal_errors": [],
            },
        },
    }


def _teach_back_proposal_payload() -> dict:
    return _proposal_wrapper([_teach_back_item_dict()])
