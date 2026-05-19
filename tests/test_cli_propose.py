from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault


def test_cli_propose_import_persists_and_accept_applies(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    proposal_file = tmp_path / "proposal.json"
    proposal_file.write_text(json.dumps(_proposal_payload()), encoding="utf-8")
    runner = CliRunner()

    proposed = runner.invoke(app, ["propose", "--vault", str(vault_root), "--file", str(proposal_file), "--json"])

    assert proposed.exit_code == 0, proposed.output
    patch_id = json.loads(proposed.output)["proposal_id"]

    listed = runner.invoke(app, ["proposals", "--vault", str(vault_root), "--json"])

    assert listed.exit_code == 0, listed.output
    assert json.loads(listed.output)["proposals"][0]["id"] == patch_id

    accepted = runner.invoke(app, ["accept", patch_id, "--vault", str(vault_root)])

    assert accepted.exit_code == 0, accepted.output
    loaded = load_vault(vault_root)
    assert "lo_svd_imported" in loaded.learning_objects
    assert "pi_svd_imported_001" in loaded.practice_items


def test_cli_propose_without_file_reports_codex_unavailable(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    runner = CliRunner()

    result = runner.invoke(app, ["propose", "--vault", str(vault_root), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["error"] == "codex_unavailable"


def _proposal_payload() -> dict:
    return {
        "summary": "Imported SVD proposal",
        "source_refs": [
            {
                "ref_type": "manual_context",
                "ref_id": "manual_svd",
            }
        ],
        "items": [
            {
                "client_item_id": "lo_1",
                "item_type": "learning_object",
                "operation": "create",
                "proposed_entity_id": "lo_svd_imported",
                "source_ref_ids": ["manual_svd"],
                "rationale": "Add an application LO.",
                "review_route": "review_required",
                "payload": {
                    "title": "Imported SVD use",
                    "subjects": ["linear-algebra"],
                    "concept_id": "singular_value_decomposition",
                    "knowledge_type": "application",
                    "summary": "SVD can compress matrices through low-rank approximation.",
                },
            },
            {
                "client_item_id": "pi_1",
                "item_type": "practice_item",
                "operation": "create",
                "proposed_entity_id": "pi_svd_imported_001",
                "source_ref_ids": ["manual_svd"],
                "rationale": "Practice the new application LO.",
                "review_route": "review_required",
                "payload": {
                    "learning_object_id": "lo_svd_imported",
                    "subjects": None,
                    "practice_mode": "short_answer",
                    "attempt_types_allowed": ["independent_attempt"],
                    "prompt": "What is one use of SVD?",
                    "expected_answer": "Low-rank approximation.",
                    "evidence_facets": ["application"],
                    "evidence_weights": {"application": 1.0},
                    "grading_rubric": {
                        "max_points": 4,
                        "criteria": [{"id": "correctness", "points": 4, "description": "Names a real use."}],
                        "fatal_errors": [],
                    },
                },
            },
        ],
    }
