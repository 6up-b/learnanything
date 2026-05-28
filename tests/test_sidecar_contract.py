from __future__ import annotations

import io
import json
import shutil
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop_sidecar.server import serve

from tests.helpers import ALGORITHM_VERSION, add_followup_item, create_basic_vault, seed_due_item

FIXTURE_VAULT = Path(__file__).resolve().parents[1] / "fixtures" / "linear_algebra"


def test_sidecar_loads_linear_algebra_fixture_vault(tmp_path):
    # The dev fixture vault the Tauri sidecar loads by default. Copy it to a temp
    # dir first so loading (which creates state.sqlite) never mutates the tracked
    # fixture.
    vault_root = tmp_path / "vault"
    shutil.copytree(FIXTURE_VAULT, vault_root)

    init = _rpc(
        [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}}]
    )[0]["result"]
    loaded = load_vault(vault_root)
    assert init["vault"]["algorithmVersion"] == ALGORITHM_VERSION
    assert init["vault"]["counts"]["practiceItems"] == len(loaded.practice_items)
    assert init["vault"]["counts"]["learningObjects"] == len(loaded.learning_objects)
    assert init["health"]["ai"]["activeProvider"] == loaded.config.ai.active_provider
    assert "ready" in init["health"]["ai"]
    assert init["vault"]["counts"]["practiceItems"] >= 3
    assert init["vault"]["counts"]["learningObjects"] >= 4
    assert init["vault"]["issueCount"] == len(loaded.issues)

    queue = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_today_queue", "params": {"availableMinutes": 25}},
        ]
    )[1]["result"]
    queued_items = [item for section in queue["sections"] for item in section["items"]]
    assert queue["totalItems"] == len(queued_items)
    assert queue["totalItems"] >= 3


def test_sidecar_initialize_start_session_and_queue(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "start_session",
                "params": {"energy": "medium", "availableMinutes": 25},
            },
        ]
    )

    init = responses[0]["result"]
    session = responses[1]["result"]
    assert "get_today_queue" in init["capabilities"]["methods"]
    assert init["vault"]["counts"]["practiceItems"] == 1
    assert init["vault"]["algorithmVersion"] == ALGORITHM_VERSION
    assert session["energy"] == "medium"

    queue = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "get_today_queue",
                "params": {"sessionId": session["sessionId"], "availableMinutes": 25, "energy": "medium"},
            },
        ]
    )[1]["result"]

    assert queue["version"] == 1
    assert queue["totalItems"] == 1
    assert queue["sections"][0]["items"][0]["practiceItemId"] == "pi_svd_define_001"


def test_sidecar_checkpoint_patch_preserves_omitted_fields_and_hints(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)

    first = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "start_session", "params": {"energy": "high"}},
        ]
    )
    session_id = first[1]["result"]["sessionId"]

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "update_session_checkpoint",
                "params": {
                    "sessionId": session_id,
                    "currentPracticeItemId": "pi_svd_define_001",
                    "currentAnswer": "draft",
                    "readiness": {"energy": "high"},
                    "hintsUsed": 1,
                },
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "save_practice_draft",
                "params": {
                    "sessionId": session_id,
                    "practiceItemId": "pi_svd_define_001",
                    "answerMd": "new draft",
                    "hintsUsed": 2,
                },
            },
            {"jsonrpc": "2.0", "id": 4, "method": "get_session", "params": {"sessionId": session_id}},
        ]
    )

    checkpoint = responses[3]["result"]["checkpoint"]
    assert checkpoint["currentAnswer"] == "new draft"
    assert checkpoint["hintsUsed"] == 2
    assert checkpoint["readiness"] == {"energy": "high"}

    cleared = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "update_session_checkpoint",
                "params": {
                    "sessionId": session_id,
                    "currentAnswer": None,
                    "hintsUsed": None,
                },
            },
            {"jsonrpc": "2.0", "id": 3, "method": "get_session", "params": {"sessionId": session_id}},
        ]
    )[2]["result"]["checkpoint"]

    assert cleared["currentPracticeItemId"] == "pi_svd_define_001"
    assert cleared["currentAnswer"] is None
    assert cleared["hintsUsed"] == 0
    assert cleared["readiness"] == {"energy": "high"}


def test_sidecar_load_vault_returns_resumable_checkpoint(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "start_session", "params": {"energy": "low"}},
        ]
    )
    session_id = responses[1]["result"]["sessionId"]

    snapshot = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "save_practice_draft",
                "params": {
                    "sessionId": session_id,
                    "practiceItemId": "pi_svd_define_001",
                    "answerMd": "half remembered",
                    "hintsUsed": 1,
                },
            },
            {"jsonrpc": "2.0", "id": 3, "method": "load_vault"},
        ]
    )[2]["result"]

    assert snapshot["activeSession"]["sessionId"] == session_id
    assert snapshot["activeSession"]["checkpoint"]["currentPracticeItemId"] == "pi_svd_define_001"
    assert snapshot["activeSession"]["checkpoint"]["currentAnswer"] == "half remembered"
    assert snapshot["activeSession"]["checkpoint"]["hintsUsed"] == 1


def test_sidecar_end_session_clears_checkpoint_and_blocks_future_writes(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    started = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "start_session", "params": {"energy": "medium"}},
        ]
    )
    session_id = started[1]["result"]["sessionId"]

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "save_practice_draft",
                "params": {
                    "sessionId": session_id,
                    "practiceItemId": "pi_svd_define_001",
                    "answerMd": "done for now",
                    "hintsUsed": 0,
                },
            },
            {"jsonrpc": "2.0", "id": 3, "method": "end_session", "params": {"sessionId": session_id}},
            {"jsonrpc": "2.0", "id": 4, "method": "load_vault"},
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "save_practice_draft",
                "params": {
                    "sessionId": session_id,
                    "practiceItemId": "pi_svd_define_001",
                    "answerMd": "late write",
                    "hintsUsed": 0,
                },
            },
        ]
    )

    ended = responses[2]["result"]
    assert ended["sessionId"] == session_id
    assert ended["endedAt"] is not None
    assert ended["attemptsRecorded"] == 0
    assert ended["itemsReviewed"] == 0
    assert ended["followupsQueued"] == 0
    assert responses[3]["result"]["activeSession"] is None
    assert responses[4]["error"]["data"]["code"] == "validation_error"


def test_sidecar_submit_attempt_persists_feedback_bundle(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "start_session", "params": {"energy": "medium"}},
        ]
    )
    session_id = responses[1]["result"]["sessionId"]

    submitted = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "submit_attempt",
                "params": {
                    "sessionId": session_id,
                    "practiceItemId": "pi_svd_define_001",
                    "answerMd": "SVD is U Sigma V transpose.",
                    "attemptType": "independent_attempt",
                    "hintsUsed": 0,
                    "selfGrade": {
                        "criterionPoints": {"correctness": 4},
                        "confidence": 5,
                        "notes": "Complete.",
                    },
                },
            },
        ]
    )[1]["result"]

    attempt_id = submitted["attemptId"]
    repository = Repository(paths.sqlite_path)
    assert repository.fetch_attempt_feedback_metadata(attempt_id)["feedback_md"] == "Complete."

    feedback = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_feedback", "params": {"attemptId": attempt_id}},
        ]
    )[1]["result"]

    assert feedback["attemptId"] == attempt_id
    assert feedback["gradingSource"] == "self"
    assert feedback["feedbackMd"] == "Complete."
    assert feedback["criterionEvidence"][0]["criterionId"] == "correctness"
    # Belief-update panel needs both endpoints populated; mastery_before is
    # reconstructed from the surprise posterior_delta (not hard-coded None) so
    # the before→after bars and surprise badge render.
    assert feedback["masteryAfter"] is not None
    assert feedback["masteryBefore"] is not None
    assert set(feedback["masteryBefore"]) >= {"mean", "variance"}
    # The surprise-badge threshold τ travels with the bundle (sourced from
    # config.scheduler.followup.tau_followup_nats) rather than being hard-coded
    # in the frontend.
    tau = feedback["surprise"]["followupThresholdNats"]
    assert isinstance(tau, (int, float)) and tau > 0


def test_sidecar_submit_attempt_falls_back_to_codex_when_routed_ai_unavailable(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    checkout = tmp_path / "codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")
    server = _GradingServer()
    server.start()
    try:
        _configure_ai_fallback_to_codex(vault_root, checkout, server.base_url)
        session_id = _rpc(
            [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
                {"jsonrpc": "2.0", "id": 2, "method": "start_session", "params": {"energy": "medium"}},
            ]
        )[1]["result"]["sessionId"]

        submitted = _rpc(
            [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "submit_attempt",
                    "params": {
                        "sessionId": session_id,
                        "practiceItemId": "pi_svd_define_001",
                        "answerMd": "SVD is U Sigma V transpose.",
                        "attemptType": "independent_attempt",
                        "hintsUsed": 0,
                    },
                },
            ]
        )[1]["result"]
    finally:
        server.stop()

    assert submitted["gradingSource"] == "codex"
    assert submitted["rubricScore"] == 4
    assert server.requests[0]["path"] == "/grading-proposal"


def test_sidecar_grading_unavailable_uses_provider_neutral_error(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)

    session_id = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "start_session", "params": {"energy": "medium"}},
        ]
    )[1]["result"]["sessionId"]

    response = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "submit_attempt",
                "params": {
                    "sessionId": session_id,
                    "practiceItemId": "pi_svd_define_001",
                    "answerMd": "SVD is U Sigma V transpose.",
                    "attemptType": "independent_attempt",
                    "hintsUsed": 0,
                },
            },
        ]
    )[1]

    assert response["error"]["data"]["code"] == "grading_fallback_required"
    assert response["error"]["message"] == "AI grading is unavailable. Grade your answer to continue."


def test_sidecar_self_grade_error_attribution_round_trips(tmp_path):
    # The self-grade form attributes errors to specific rubric criteria. The
    # camelCase wire payload (errorAttributions / criterionId) must round-trip
    # through the sidecar and write an error event mirroring AI grading.
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)

    session_id = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "start_session", "params": {"energy": "medium"}},
        ]
    )[1]["result"]["sessionId"]

    # The practice-item detail advertises the selectable error types to the UI.
    detail = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "get_practice_item",
                "params": {"practiceItemId": "pi_svd_define_001"},
            },
        ]
    )[1]["result"]
    assert any(candidate["id"] == "conceptual_slip" for candidate in detail["candidateErrorTypes"])

    submitted = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "submit_attempt",
                "params": {
                    "sessionId": session_id,
                    "practiceItemId": "pi_svd_define_001",
                    "answerMd": "A partial definition.",
                    "attemptType": "independent_attempt",
                    "hintsUsed": 0,
                    "selfGrade": {
                        "criterionPoints": {"correctness": 2},
                        "confidence": 4,
                        "errorAttributions": [{"errorType": "conceptual_slip", "criterionId": "correctness"}],
                    },
                },
            },
        ]
    )[1]["result"]

    assert submitted["errorEventIds"]
    repository = Repository(paths.sqlite_path)
    events = repository.error_events_for_attempt(submitted["attemptId"])
    assert [event["error_type"] for event in events] == ["conceptual_slip"]
    assert "correctness" in (events[0]["repair_plan"] or {}).get("evidence", "")


def test_sidecar_uses_full_intervention_followup_policy(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)

    started = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "start_session",
                "params": {"energy": "medium", "availableMinutes": 25},
            },
        ]
    )[1]["result"]
    session_id = started["sessionId"]

    _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "submit_dont_know",
                "params": {"sessionId": session_id, "practiceItemId": "pi_svd_define_001"},
            },
        ]
    )
    second = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "submit_dont_know",
                "params": {"sessionId": session_id, "practiceItemId": "pi_svd_define_001"},
            },
        ]
    )[1]["result"]

    repository = Repository(paths.sqlite_path)
    surprise = repository.latest_attempt_surprise(second["attemptId"])
    assert any("repeated_same_item_failure" in action for action in surprise["triggered_actions"])
    assert repository.pending_intervention_needs("lo_svd_definition")[0]["trigger_reason"] in {
        "severe_error_event",
        "repeated_same_item_failure",
    }


def test_sidecar_feedback_exposes_probe_intervention_need(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    session_id = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "start_session",
                "params": {"energy": "medium", "availableMinutes": 25},
            },
        ]
    )[1]["result"]["sessionId"]
    submitted = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "submit_dont_know",
                "params": {"sessionId": session_id, "practiceItemId": "pi_svd_define_001"},
            },
        ]
    )[1]["result"]

    bundle = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_feedback", "params": {"attemptId": submitted["attemptId"]}},
        ]
    )[1]["result"]

    need = bundle["interventionNeed"]
    assert bundle["followupQueued"] is False
    assert need is not None
    assert need["attemptId"] == submitted["attemptId"]
    assert need["learningObjectId"] == "lo_svd_definition"
    assert need["status"] == "pending"
    assert need["blockedReason"] == "no_suitable_item"
    assert "recall" in need["targetFacets"]
    assert any("high_unfamiliar_posterior" in action for action in bundle["surprise"]["triggeredActions"])


def test_sidecar_counts_queued_intervention_followups_in_session_summary(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root)
    seed_due_item(paths)

    session_id = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "start_session",
                "params": {"energy": "medium", "availableMinutes": 25},
            },
        ]
    )[1]["result"]["sessionId"]

    submitted = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "submit_dont_know",
                "params": {"sessionId": session_id, "practiceItemId": "pi_svd_define_001"},
            },
        ]
    )[1]["result"]

    feedback = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_feedback", "params": {"attemptId": submitted["attemptId"]}},
            {"jsonrpc": "2.0", "id": 3, "method": "end_session", "params": {"sessionId": session_id}},
        ]
    )

    bundle = feedback[1]["result"]
    summary = feedback[2]["result"]
    assert bundle["followupQueued"] is True
    assert "intervention_followup:queued:pi_svd_define_002" in bundle["surprise"]["triggeredActions"]
    assert bundle["surprise"]["suppressedActions"] == []
    assert summary["followupsQueued"] == 1


def test_sidecar_inspect_practice_item_includes_attempt_history(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)

    session_id = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "start_session", "params": {"energy": "medium"}},
        ]
    )[1]["result"]["sessionId"]

    # A first-touch item has no attempt history yet.
    fresh = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "inspect_entity", "params": {"id": "pi_svd_define_001"}},
        ]
    )[1]["result"]
    assert fresh["kind"] == "practice_item"
    assert fresh["detail"]["attempts"] == []

    attempt_id = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "submit_attempt",
                "params": {
                    "sessionId": session_id,
                    "practiceItemId": "pi_svd_define_001",
                    "answerMd": "SVD factorizes a matrix.",
                    "attemptType": "independent_attempt",
                    "hintsUsed": 0,
                    "selfGrade": {"criterionPoints": {"correctness": 3}, "confidence": 4},
                },
            },
        ]
    )[1]["result"]["attemptId"]

    detail = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "inspect_entity", "params": {"id": "pi_svd_define_001"}},
        ]
    )[1]["result"]["detail"]

    assert len(detail["attempts"]) == 1
    row = detail["attempts"][0]
    assert row["id"] == attempt_id
    assert row["attemptType"] == "independent_attempt"
    assert row["rubricScore"] == 3
    assert isinstance(row["maxPoints"], int) and row["maxPoints"] >= row["rubricScore"]
    assert row["hintsUsed"] == 0
    assert "createdAt" in row
    assert "surpriseDirection" in row  # present even when no surprise was recorded


def test_sidecar_get_concept_graph_serializes_concepts_and_rollups(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    graph = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_concept_graph"},
        ]
    )[1]["result"]

    assert graph["version"] == 1
    svd = next(concept for concept in graph["concepts"] if concept["id"] == "singular_value_decomposition")
    assert svd["type"] == "procedure"
    assert svd["practiceItemCount"] == 1
    assert [lo["id"] for lo in svd["learningObjects"]] == ["lo_svd_definition"]
    assert graph["counts"]["concepts"] == len(graph["concepts"])
    assert isinstance(graph["edges"], list)


def test_sidecar_run_cli_command_uses_selected_vault_and_can_propose(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    proposal_file = tmp_path / "proposal.json"
    proposal_file.write_text(json.dumps(_proposal_payload()), encoding="utf-8")

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "run_cli_command", "params": {"argv": ["proposals", "--json"]}},
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "run_cli_command",
                "params": {"argv": ["propose", "--file", str(proposal_file)]},
            },
        ]
    )

    result = responses[1]["result"]
    assert result["exitCode"] == 0
    assert result["argv"][-2:] == ["--vault", str(vault_root)]
    assert json.loads(result["stdout"])["proposals"] == []
    proposed = responses[2]["result"]
    assert proposed["exitCode"] == 0
    assert "Persisted proposal" in proposed["stdout"]
    assert Repository(paths.sqlite_path).proposal_batches()


def _proposal_payload(suffix: str = "imported") -> dict:
    entity_id = f"lo_svd_{suffix}"
    client_item_id = f"lo_{suffix}"
    return {
        "summary": f"Imported SVD proposal {suffix}",
        "source_refs": [{"ref_type": "manual_context", "ref_id": "manual_svd"}],
        "items": [
            {
                "client_item_id": client_item_id,
                "item_type": "learning_object",
                "operation": "create",
                "proposed_entity_id": entity_id,
                "source_ref_ids": ["manual_svd"],
                "rationale": "Add an application LO.",
                "review_route": "review_required",
                "payload": {
                    "title": f"Imported SVD use {suffix}",
                    "subjects": ["linear-algebra"],
                    "concept_id": "singular_value_decomposition",
                    "knowledge_type": "application",
                    "summary": "SVD compresses matrices via low-rank approximation.",
                },
            }
        ],
    }


def test_sidecar_vault_tree_and_file_read(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_vault_tree"},
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "read_vault_file",
                "params": {"path": "subjects/linear-algebra/learning-objects/lo_svd_definition.yaml"},
            },
            {"jsonrpc": "2.0", "id": 4, "method": "read_vault_file", "params": {"path": "../escape.txt"}},
        ]
    )

    tree = responses[1]["result"]
    top_level = {node["name"] for node in tree["tree"]}
    assert "subjects" in top_level

    file = responses[2]["result"]
    assert file["kind"] == "yaml"
    assert file["binary"] is False
    assert "id: lo_svd_definition" in file["body"]

    # Path traversal outside the vault root is refused.
    assert responses[3]["error"]["data"]["code"] == "invalid_path"


def test_sidecar_write_vault_file_round_trips_and_guards(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    lo_path = "subjects/linear-algebra/learning-objects/lo_svd_definition.yaml"

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "read_vault_file", "params": {"path": lo_path}},
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "write_vault_file",
                "params": {"path": lo_path, "body": "schema_version: 1\nid: lo_svd_definition\ntitle: edited\n"},
            },
            {"jsonrpc": "2.0", "id": 4, "method": "read_vault_file", "params": {"path": lo_path}},
            {"jsonrpc": "2.0", "id": 5, "method": "write_vault_file", "params": {"path": "state.sqlite", "body": "x"}},
            {"jsonrpc": "2.0", "id": 6, "method": "write_vault_file", "params": {"path": "../escape.txt", "body": "x"}},
        ]
    )

    assert responses[1]["result"]["editable"] is True
    saved = responses[2]["result"]
    assert saved["body"].endswith("title: edited\n")
    assert "title: edited" in responses[3]["result"]["body"]  # persisted to disk
    assert responses[4]["error"]["data"]["code"] == "not_editable"  # binary
    assert responses[5]["error"]["data"]["code"] == "invalid_path"  # traversal


def test_sidecar_proposals_get_accept_reject_undo(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    accept_file = tmp_path / "accept-proposal.json"
    reject_file = tmp_path / "reject-proposal.json"
    accept_file.write_text(json.dumps(_proposal_payload("queued_accept")), encoding="utf-8")
    reject_file.write_text(json.dumps(_proposal_payload("queued_reject")), encoding="utf-8")

    seeded = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "run_cli_command",
                "params": {"argv": ["propose", "--file", str(accept_file)]},
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "run_cli_command",
                "params": {"argv": ["propose", "--file", str(reject_file)]},
            },
            {"jsonrpc": "2.0", "id": 4, "method": "get_proposals"},
        ]
    )
    assert seeded[1]["result"]["exitCode"] == 0
    assert seeded[2]["result"]["exitCode"] == 0
    listed = seeded[3]["result"]

    assert listed["version"] == 1
    assert {"pending", "accepted", "rejected"} <= set(listed["totals"])
    assert listed["batchCount"] == len(listed["batches"])
    assert listed["totals"]["pending"] >= 2
    first_batch = listed["batches"][0]
    assert {"agentRun", "items", "counts", "summary"} <= set(first_batch)
    # Payload preview keeps the on-disk field names (snake_case survives camel-casing).
    sample = next(item for batch in listed["batches"] for item in batch["items"])
    assert all(isinstance(line, list) and len(line) == 2 for line in sample["payloadLines"])

    accept_batch, accept_item = _pending_valid_item(listed)
    accepted = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "accept_proposal_items",
                "params": {"patchId": accept_batch, "itemIds": [accept_item]},
            },
        ]
    )[1]["result"]
    accepted_item = _find_proposal_item(accepted, accept_item)
    assert accepted_item["decision"] == "accepted"
    assert accepted_item["applied"] is True
    assert accepted["totals"]["accepted"] == listed["totals"]["accepted"] + 1

    reject_batch, reject_item = _pending_valid_item(accepted, skip={accept_item})
    rejected = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "reject_proposal_items",
                "params": {"patchId": reject_batch, "itemIds": [reject_item]},
            },
        ]
    )[1]["result"]
    rejected_item = _find_proposal_item(rejected, reject_item)
    assert rejected_item["decision"] == "rejected"
    assert rejected_item["applied"] is False

    # Undo the rejection: a never-applied item goes back to pending.
    undone = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "reset_proposal_items",
                "params": {"patchId": reject_batch, "itemIds": [reject_item]},
            },
        ]
    )[1]["result"]
    assert _find_proposal_item(undone, reject_item)["decision"] == "pending"

    # Undo is scoped: it must NOT resurrect an accepted item already written to disk.
    noop = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "reset_proposal_items",
                "params": {"patchId": accept_batch, "itemIds": [accept_item]},
            },
        ]
    )[1]["result"]
    assert _find_proposal_item(noop, accept_item)["decision"] == "accepted"


def _pending_valid_item(snapshot: dict, skip: set[str] = frozenset()) -> tuple[str, str]:
    for batch in snapshot["batches"]:
        for item in batch["items"]:
            if item["decision"] == "pending" and item["validationStatus"] == "valid" and item["id"] not in skip:
                return batch["id"], item["id"]
    raise AssertionError("expected a pending, valid proposal item")


def _find_proposal_item(snapshot: dict, item_id: str) -> dict:
    for batch in snapshot["batches"]:
        for item in batch["items"]:
            if item["id"] == item_id:
                return item
    raise AssertionError(f"proposal item {item_id} missing from snapshot")


def test_sidecar_create_vault_file_creates_note_and_guards(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "create_vault_file",
                "params": {"path": "notes/idea.md", "body": "# Idea\n\n$e^{i\\pi}+1=0$\n"},
            },
            {"jsonrpc": "2.0", "id": 3, "method": "read_vault_file", "params": {"path": "notes/idea.md"}},
            # Re-creating an existing path is refused.
            {"jsonrpc": "2.0", "id": 4, "method": "create_vault_file", "params": {"path": "notes/idea.md"}},
            # Creating a database/binary as text is refused.
            {"jsonrpc": "2.0", "id": 5, "method": "create_vault_file", "params": {"path": "fresh.sqlite"}},
            # Escaping the vault root is refused.
            {"jsonrpc": "2.0", "id": 6, "method": "create_vault_file", "params": {"path": "../escape.md"}},
        ]
    )

    created = responses[1]["result"]
    assert created["kind"] == "md" and created["editable"] is True
    assert (vault_root / "notes" / "idea.md").read_text(encoding="utf-8").startswith("# Idea")
    assert responses[2]["result"]["body"].startswith("# Idea")
    assert responses[3]["error"]["data"]["code"] == "already_exists"
    assert responses[4]["error"]["data"]["code"] == "not_editable"
    assert responses[5]["error"]["data"]["code"] == "invalid_path"


def test_sidecar_sqlite_browse_and_edit(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    # The database file surfaces as kind=sqlite (not editable as text) and routes to
    # the dedicated browser. We exercise the browser against a self-contained table.
    setup = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "read_vault_file", "params": {"path": "state.sqlite"}},
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "sqlite_exec",
                "params": {"path": "state.sqlite", "sql": "CREATE TABLE t_demo (a TEXT, b INTEGER)"},
            },
            {"jsonrpc": "2.0", "id": 4, "method": "sqlite_insert_row", "params": {"path": "state.sqlite", "table": "t_demo"}},
        ]
    )
    descriptor = setup[1]["result"]
    assert descriptor["kind"] == "sqlite" and descriptor["database"] is True
    assert descriptor["editable"] is False and descriptor["body"] is None
    assert setup[2]["result"]["kind"] == "write"
    rowid = setup[3]["result"]["rowid"]
    assert isinstance(rowid, int)

    edited = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "sqlite_update_cell",
                "params": {"path": "state.sqlite", "table": "t_demo", "rowid": rowid, "column": "b", "value": "42"},
            },
            {"jsonrpc": "2.0", "id": 3, "method": "sqlite_table", "params": {"path": "state.sqlite", "table": "t_demo"}},
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "sqlite_exec",
                "params": {"path": "state.sqlite", "sql": "SELECT a, b FROM t_demo"},
            },
            {"jsonrpc": "2.0", "id": 5, "method": "sqlite_delete_row", "params": {"path": "state.sqlite", "table": "t_demo", "rowid": rowid}},
            {"jsonrpc": "2.0", "id": 6, "method": "sqlite_table", "params": {"path": "state.sqlite", "table": "t_demo"}},
            # A non-database path is refused by the browser.
            {"jsonrpc": "2.0", "id": 7, "method": "sqlite_tables", "params": {"path": "learnloop.toml"}},
        ]
    )

    table = edited[2]["result"]
    assert table["editable"] is True and table["rowCount"] == 1
    assert [col["name"] for col in table["columns"]] == ["a", "b"]
    assert table["rows"][0]["cells"] == [None, 42]  # "42" coerced to INTEGER affinity
    select = edited[3]["result"]
    assert select["kind"] == "rows" and select["columns"] == ["a", "b"]
    assert select["rows"] == [[None, 42]]
    assert edited[4]["result"]["ok"] is True  # delete_row
    assert edited[5]["result"]["rowCount"] == 0
    assert edited[6]["error"]["data"]["code"] == "not_found"


def test_sidecar_edit_and_delete_proposal_item(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    proposal_file = tmp_path / "proposal.json"
    proposal_file.write_text(json.dumps(_proposal_payload()), encoding="utf-8")

    seeded = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "run_cli_command", "params": {"argv": ["propose", "--file", str(proposal_file)]}},
            {"jsonrpc": "2.0", "id": 3, "method": "get_proposals"},
        ]
    )
    listed = seeded[2]["result"]
    batch_id, item_id = _find_pending(listed)
    item = _find_proposal_item(listed, item_id)
    # The raw payload travels as a JSON string with on-disk (snake_case) field names.
    payload = json.loads(item["payloadJson"])
    assert payload["title"] == "Imported SVD use imported"

    payload["title"] = "Edited via Library"
    edited = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "edit_proposal_item",
                "params": {"patchId": batch_id, "itemId": item_id, "payloadJson": json.dumps(payload)},
            },
        ]
    )[1]["result"]
    edited_item = _find_proposal_item(edited, item_id)
    assert edited_item["edited"] is True
    assert json.loads(edited_item["payloadJson"])["title"] == "Edited via Library"

    Repository(paths.sqlite_path).update_proposal_item_validation(
        item_id,
        validation_status="invalid",
        validation_errors=["missing_required:title", "unresolved_source_ref:manual_svd"],
    )
    refreshed = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "refresh_proposal_item_validation",
                "params": {"patchId": batch_id, "itemId": item_id},
            },
        ]
    )[1]["result"]
    refreshed_item = _find_proposal_item(refreshed, item_id)
    assert refreshed_item["validationStatus"] == "valid"
    assert refreshed_item["validationErrors"] == []
    assert json.loads(refreshed_item["payloadJson"])["title"] == "Edited via Library"

    # Invalid JSON is rejected without mutating the item.
    bad = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "edit_proposal_item",
                "params": {"patchId": batch_id, "itemId": item_id, "payloadJson": "{not json"},
            },
        ]
    )[1]
    assert bad["error"]["data"]["code"] == "invalid_payload"

    # Hard delete removes the item from the inbox entirely.
    after_delete = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "delete_proposal_item", "params": {"patchId": batch_id, "itemId": item_id}},
        ]
    )[1]["result"]
    assert all(
        candidate["id"] != item_id for batch in after_delete["batches"] for candidate in batch["items"]
    )


def _find_pending(snapshot: dict) -> tuple[str, str]:
    for batch in snapshot["batches"]:
        for item in batch["items"]:
            if item["decision"] == "pending":
                return batch["id"], item["id"]
    raise AssertionError("expected a pending proposal item")


def _configure_ai_fallback_to_codex(vault_root, checkout, base_url: str) -> None:
    config_path = vault_root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace('provider = "sdk"', 'provider = "http"')
    text = text.replace('checkout_path = "../codex"', f'checkout_path = "{checkout.as_posix()}"')
    text = text.replace('revision = "<pinned-commit>"', 'revision = "abc123"')
    text = text.replace('base_url = "http://127.0.0.1:8765"', f'base_url = "{base_url}"')
    text = text.replace('fallback_provider = ""', 'fallback_provider = "codex"')
    text = text.replace('grading = "codex"', 'grading = "deepseek_flash"')
    config_path.write_text(text, encoding="utf-8")


class _GradingServer:
    def __init__(self):
        self.requests: list[dict] = []
        self._server = HTTPServer(("127.0.0.1", 0), self._handler())
        self.base_url = f"http://127.0.0.1:{self._server.server_port}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._thread.join(timeout=5)
        self._server.server_close()

    def _handler(self):
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                if self.path == "/health":
                    self._json({"status": "ready"})
                    return
                self.send_response(404)
                self.end_headers()

            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                owner.requests.append({"path": self.path, "body": body})
                if self.path == "/grading-proposal":
                    self._json(
                        {
                            "attempt_id": body["context"]["attempt_id"],
                            "practice_item_id": "pi_svd_define_001",
                            "rubric_score": 4,
                            "criterion_evidence": [
                                {"criterion_id": "correctness", "points_awarded": 4, "evidence": "Correct."}
                            ],
                            "grader_confidence": 0.95,
                        }
                    )
                    return
                self.send_response(404)
                self.end_headers()

            def log_message(self, *_args):
                return

            def _json(self, payload: dict) -> None:
                raw = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        return Handler


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]
