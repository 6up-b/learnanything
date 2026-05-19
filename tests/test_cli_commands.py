from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app

from tests.helpers import create_basic_vault, seed_due_item

runner = CliRunner()


def _no_placeholder(result) -> None:
    lowered = result.output.lower()
    assert "not implemented" not in lowered
    assert "placeholder" not in lowered


def test_init_add_subject_add_note(tmp_path):
    vault_root = tmp_path / "fresh"
    init = runner.invoke(app, ["init", str(vault_root)])
    assert init.exit_code == 0, init.output
    _no_placeholder(init)

    sub = runner.invoke(app, ["add-subject", "linear-algebra", "Linear Algebra", "--vault", str(vault_root)])
    assert sub.exit_code == 0, sub.output

    note = runner.invoke(
        app,
        ["add-note", "linear-algebra", "note_svd", "SVD overview", "--body", "Notes.", "--vault", str(vault_root)],
    )
    assert note.exit_code == 0, note.output


def test_core_workflow_commands_succeed(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    v = ["--vault", str(vault_root)]

    doctor = runner.invoke(app, ["doctor", "--json", *v])
    assert doctor.exit_code == 0, doctor.output
    assert json.loads(doctor.output)["clean"] is True

    review = runner.invoke(app, ["review", "--json", *v])
    assert review.exit_code == 0, review.output
    assert json.loads(review.output)["items"]

    attempt = runner.invoke(
        app,
        ["attempt", "pi_svd_define_001", "--answer", "x", "--criterion-points", "correctness=3", "--confidence", "4", "--json", *v],
    )
    assert attempt.exit_code == 0, attempt.output
    _no_placeholder(attempt)

    why = runner.invoke(app, ["why", "pi_svd_define_001", "--json", *v])
    assert why.exit_code == 0, why.output

    show = runner.invoke(app, ["show", "pi_svd_define_001", "--json", *v])
    assert show.exit_code == 0, show.output
    assert json.loads(show.output)["type"] == "practice_item"

    proposals = runner.invoke(app, ["proposals", "--json", *v])
    assert proposals.exit_code == 0, proposals.output


def test_propose_accept_reject(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    v = ["--vault", str(vault_root)]
    proposal_file = tmp_path / "proposal.json"
    proposal_file.write_text(json.dumps(_proposal_payload()), encoding="utf-8")

    first = runner.invoke(app, ["propose", "--file", str(proposal_file), "--json", *v])
    assert first.exit_code == 0, first.output
    patch_id = json.loads(first.output)["proposal_id"]

    accept = runner.invoke(app, ["accept", patch_id, *v])
    assert accept.exit_code == 0, accept.output

    second = runner.invoke(app, ["propose", "--file", str(proposal_file), "--json", *v])
    second_id = json.loads(second.output)["proposal_id"]
    reject = runner.invoke(app, ["reject", second_id, *v])
    assert reject.exit_code == 0, reject.output


def test_today_help_is_available():
    result = runner.invoke(app, ["today", "--help"])
    assert result.exit_code == 0
    _no_placeholder(result)


def _proposal_payload() -> dict:
    return {
        "summary": "Imported SVD proposal",
        "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
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
                    "summary": "SVD compresses matrices via low-rank approximation.",
                },
            }
        ],
    }
