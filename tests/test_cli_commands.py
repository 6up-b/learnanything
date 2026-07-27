from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.vault.loader import load_vault

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
        [
            "add-note",
            "linear-algebra",
            "note_svd",
            "SVD overview",
            "--body",
            "Notes.",
            "--source-type",
            "canonical_source",
            "--vault",
            str(vault_root),
        ],
    )
    assert note.exit_code == 0, note.output
    loaded = load_vault(vault_root)
    assert loaded.notes["note_svd"].source_type == "canonical_source"


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
    shown = runner.invoke(app, ["show", patch_id, "--json", *v])
    item = json.loads(shown.output)["record"]["items"][0]
    edited_payload = {**item["payload"], "title": "Edited imported SVD use"}
    edit_file = tmp_path / "edited_payload.json"
    edit_file.write_text(json.dumps(edited_payload), encoding="utf-8")
    edit = runner.invoke(
        app,
        ["edit-proposal-item", patch_id, item["id"], "--file", str(edit_file), "--json", *v],
    )
    assert edit.exit_code == 0, edit.output
    assert json.loads(edit.output)["proposal_item"]["edited_payload"]["title"] == "Edited imported SVD use"

    accept = runner.invoke(app, ["accept", patch_id, *v])
    assert accept.exit_code == 0, accept.output
    assert load_vault(vault_root).learning_objects["lo_svd_imported"].title == "Edited imported SVD use"

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


def test_misconceptions_lists_and_resolves_active_error_events(tmp_path):
    from learnloop.db.repositories import Repository

    from tests.helpers import NOW_ISO

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    v = ["--vault", str(vault_root)]

    empty = runner.invoke(app, ["misconceptions", *v])
    assert empty.exit_code == 0, empty.output
    assert "No active misconceptions." in empty.output

    repository = Repository(paths.sqlite_path)
    repository.insert_error_event(
        {
            "id": "ee_misconception_1",
            "learning_object_id": "lo_svd_definition",
            "error_type": "conceptual_slip",
            "severity": 0.7,
            "is_misconception": True,
            "created_at": NOW_ISO,
        }
    )
    repository.insert_error_event(
        {
            "id": "ee_plain_error_1",
            "learning_object_id": "lo_svd_definition",
            "error_type": "recall_failure",
            "severity": 0.4,
            "is_misconception": False,
            "created_at": NOW_ISO,
        }
    )

    default = runner.invoke(app, ["misconceptions", "--json", *v])
    assert default.exit_code == 0, default.output
    rows = json.loads(default.output)["misconceptions"]
    assert [row["id"] for row in rows] == ["ee_misconception_1"]
    assert rows[0]["title"] == "Conceptual slip"
    assert rows[0]["is_misconception"] is True

    all_errors = runner.invoke(app, ["misconceptions", "--all-errors", "--json", *v])
    ids = {row["id"] for row in json.loads(all_errors.output)["misconceptions"]}
    assert ids == {"ee_misconception_1", "ee_plain_error_1"}

    human = runner.invoke(app, ["misconceptions", *v])
    assert "ee_misconception_1" in human.output
    assert "(misconception)" in human.output
    assert "Conceptual slip" in human.output

    resolve = runner.invoke(app, ["resolve-error", "ee_misconception_1", *v])
    assert resolve.exit_code == 0, resolve.output
    assert "Resolved error event ee_misconception_1." in resolve.output

    after = runner.invoke(app, ["misconceptions", "--json", *v])
    assert json.loads(after.output)["misconceptions"] == []

    again = runner.invoke(app, ["resolve-error", "ee_misconception_1", *v])
    assert again.exit_code == 1
    missing_json = runner.invoke(app, ["resolve-error", "ee_missing", "--json", *v])
    assert missing_json.exit_code == 1
    assert json.loads(missing_json.output)["resolved"] is False


def test_exam_answer_refuses_self_grade_flags(tmp_path):
    """Parity with the sidecar's ``submit_exam_answer``.

    The exam is the held-out measurement of the model's projections. The sidecar
    has always refused to self-grade one; the CLI used to prompt for criterion
    points and record the learner's own score as the exam result, which made the
    front end you picked decide whether the measurement was real.
    """

    root = create_basic_vault(tmp_path / "vault").root

    result = runner.invoke(
        app,
        [
            "exam",
            "answer",
            "pi_svd_define_001",
            "--session",
            "session_does_not_matter",
            "--answer",
            "A = U Sigma V^T",
            "--criterion-points",
            "correctness=4",
            "--json",
            "--vault",
            str(root),
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["error"] == "exam_self_grade_refused"
    assert "would not be a measurement" in payload["message"]


def test_exam_answer_refuses_when_no_ai_grader_is_configured(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root

    result = runner.invoke(
        app,
        [
            "exam",
            "answer",
            "pi_svd_define_001",
            "--session",
            "session_does_not_matter",
            "--answer",
            "A = U Sigma V^T",
            "--json",
            "--vault",
            str(root),
        ],
    )

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    # The sidecar's error code, verbatim: one refusal, one name for it.
    assert payload["error"] == "exam_grading_unavailable"
    assert "would not be a measurement" in payload["message"]
