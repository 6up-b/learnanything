from __future__ import annotations

import io
import json
import shutil
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from learnloop.db.repositories import Repository
from learnloop.services.patches import apply_accepted_items
from learnloop.vault.loader import add_note, load_vault
from learnloop.vault.writer import upsert_concept, upsert_concept_edge, upsert_learning_object
from learnloop_sidecar.server import serve

from tests.helpers import ALGORITHM_VERSION, NOW_ISO, add_followup_item, create_basic_vault, seed_due_item

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
    assert ended["streak"] == {"current": 1, "activeToday": True, "longest": 1}
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


def test_sidecar_submission_retry_returns_one_attempt_and_one_response(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    session_id = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "start_session", "params": {"energy": "medium"}},
        ]
    )[1]["result"]["sessionId"]
    payload = {
        "sessionId": session_id,
        "practiceItemId": "pi_svd_define_001",
        "answerMd": "SVD is U Sigma V transpose.",
        "attemptType": "independent_attempt",
        "submissionId": "submission-retry-001",
        "selfGrade": {"criterionPoints": {"correctness": 4}, "confidence": 5},
    }
    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "submit_attempt", "params": payload},
            {"jsonrpc": "2.0", "id": 3, "method": "submit_attempt", "params": payload},
        ]
    )
    assert responses[1]["result"] == responses[2]["result"]
    history = Repository(paths.sqlite_path).list_attempt_history()
    assert [row["id"] for row in history] == [responses[1]["result"]["attemptId"]]


def test_inspector_opens_probe_episode_drilldown(tmp_path):
    from learnloop.clock import FrozenClock
    from learnloop.services.probe_episodes import enter_episode
    from tests.helpers import NOW, admit_probe_instrument_card

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository, items=("pi_svd_define_001",))
    episode = enter_episode(
        load_vault(vault_root),
        repository,
        "lo_svd_definition",
        clock=FrozenClock(NOW),
    )

    inspected = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "inspect_entity", "params": {"id": episode.id}},
        ]
    )[1]["result"]
    assert inspected["kind"] == "probe_episode"
    assert inspected["detail"]["learningObjectId"] == "lo_svd_definition"
    assert inspected["detail"]["requiredFacets"] == ["recall"]
    assert inspected["detail"]["observations"] == []


def test_sidecar_load_vault_config_carries_display_thresholds(tmp_path):
    # The frontend reads mastery display banding and the τ fallback from the
    # config payload instead of hardcoding algorithm opinions.
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    snapshot = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "load_vault", "params": {}},
        ]
    )[1]["result"]

    config = snapshot["config"]
    assert config["mastery"]["displayStrongThreshold"] == 0.6
    assert config["mastery"]["displayDevelopingThreshold"] == 0.35
    assert config["scheduler"]["followup"]["tauFollowupNats"] == 0.05


def test_sidecar_submit_attempt_clears_session_checkpoint(tmp_path):
    # The checkpoint clear happens in the same submit_attempt call that records
    # the attempt: a lost client-side clear must never leave a submitted draft
    # behind to replay on restart.
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

    _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "update_session_checkpoint",
                "params": {
                    "sessionId": session_id,
                    "currentPracticeItemId": "pi_svd_define_001",
                    "currentAnswer": "draft in progress",
                    "hintsUsed": 1,
                },
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
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
                    },
                },
            },
        ]
    )

    repository = Repository(paths.sqlite_path)
    assert repository.fetch_session_checkpoint(session_id) is None


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


def test_sidecar_submit_attempt_uses_ai_codex_profile_when_legacy_codex_differs(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    checkout = tmp_path / "ai-codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")
    server = _GradingServer()
    server.start()
    try:
        _configure_ai_codex_only(vault_root, checkout, server.base_url)
        init = _rpc(
            [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}}]
        )[0]["result"]
        assert init["health"]["ai"]["ready"] is True
        assert init["health"]["codex"]["ready"] is False

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


def test_sidecar_rate_followup_round_trip(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    add_followup_item(vault_root)
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

    # Record an attempt, then force a follow-up via the manual trigger (stable
    # regardless of gate thresholds).
    first = _rpc(
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
    gate_attempt_id = first["attemptId"]
    _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "trigger_followup",
                "params": {"attemptId": gate_attempt_id},
            },
        ]
    )

    repository = Repository(paths.sqlite_path)
    surprise = repository.latest_attempt_surprise(gate_attempt_id)
    queued = [
        action.split(":", 2)[2]
        for action in surprise["triggered_actions"]
        if action.startswith("intervention_followup:queued:")
    ]
    assert queued, surprise["triggered_actions"]
    followup_item = queued[0]

    # Attempt the queued follow-up item, then rate it.
    followup_attempt = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "submit_dont_know",
                "params": {"sessionId": session_id, "practiceItemId": followup_item},
            },
        ]
    )[1]["result"]
    rated = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "rate_followup",
                "params": {"attemptId": followup_attempt["attemptId"], "useful": True},
            },
        ]
    )[1]["result"]

    assert rated["followupRating"] == {"useful": True, "ratedAt": rated["followupRating"]["ratedAt"]}
    assert rated["followupSource"] == {"gateAttemptId": gate_attempt_id}
    stored = repository.followup_rating(followup_attempt["attemptId"])
    assert stored["useful"] is True
    assert stored["gate_attempt_id"] == gate_attempt_id


def test_sidecar_config_carries_gate_fields(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    loaded = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "load_vault", "params": {}},
        ]
    )[1]["result"]
    followup = loaded["config"]["scheduler"]["followup"]
    assert followup["gateMode"] in ("cascade", "score")
    assert followup["gateScoreThreshold"] == 0.5
    assert followup["thresholdMode"] == "quantile"


def test_sidecar_calibration_session_lifecycle(tmp_path):
    from learnloop.clock import FrozenClock
    from tests.helpers import NOW, admit_probe_instrument_card

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository, items=("pi_svd_define_001",))

    started = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "start_calibration_session",
                "params": {
                    "sessionId": "cal-client-session",
                    "learningObjectIds": ["lo_svd_definition"],
                    "timeBudgetMinutes": 15,
                },
            },
        ]
    )[1]["result"]
    assert started["status"] == "active"
    assert started["blocksPlanned"] == 1
    assert started["nextTarget"]["learningObjectId"] == "lo_svd_definition"
    calibration_id = started["calibrationSessionId"]

    stopped = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "get_calibration_session",
                "params": {"calibrationSessionId": calibration_id},
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "stop_calibration_session",
                "params": {"calibrationSessionId": calibration_id},
            },
        ]
    )
    assert stopped[1]["result"]["status"] == "active"
    assert stopped[2]["result"]["status"] == "stopped"


def test_sidecar_dialogue_microprobe_turn_flow(tmp_path):
    from tests.helpers import admit_probe_instrument_card

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository, items=("pi_svd_define_001",))

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "begin_probe_dialogue",
                "params": {"learningObjectId": "lo_svd_definition"},
            },
        ]
    )
    begun = responses[1]["result"]
    assert begun["plannedTurns"] >= 1
    state_json = begun["dialogueState"]

    turn_responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "next_probe_dialogue_turn",
                "params": {"dialogueState": state_json},
            },
        ]
    )
    turn = turn_responses[1]["result"]["turn"]
    assert turn["kind"] == "commit"
    assert turn["presentationId"]
    assert turn["practiceItemId"].startswith("pi_dlg_")
    assert turn["promptMd"]
    presentation = Repository(paths.sqlite_path).probe_presentation(turn["presentationId"])
    assert presentation is not None
    assert presentation.selection_components["dialogue_turn_kind"] == "commit"
    assert 0 < presentation.selection_components["task_evidence_share"] <= 1.0


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


def test_sidecar_inspect_note_source_ref_with_timestamp_suffix(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    add_note(
        vault_root,
        "linear-algebra",
        "source_video",
        "Source Video",
        "Captioned explanation.",
        source_type="canonical_source",
    )

    result = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "inspect_entity",
                "params": {"id": "note_source_video:t=1.0-2.0"},
            },
        ]
    )[1]["result"]

    assert result["kind"] == "note"
    assert result["id"] == "note_source_video:t=1.0-2.0"
    assert result["detail"]["id"] == "note_source_video"
    assert result["detail"]["locator"] == "t=1.0-2.0"
    assert result["detail"]["sourceType"] == "canonical_source"
    assert "Captioned explanation" in result["detail"]["body"]


def test_sidecar_inspect_concept_and_resolve_lo_concept_references(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    upsert_concept(
        vault_root,
        "matrix_factorization",
        {
            "title": "Matrix Factorization",
            "type": "concept",
            "aliases": ["matrix factors"],
            "description": "Representing a matrix as a product of simpler factors.",
            "tags": ["linear-algebra"],
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    upsert_concept_edge(
        vault_root,
        {
            "id": "edge_svd_matrix_factorization_confusable",
            "relation_type": "confusable_with",
            "source": "singular_value_decomposition",
            "target": "matrix_factorization",
            "strength": 0.7,
            "rationale": "A learner may name the broader family instead of SVD.",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    loaded = load_vault(vault_root)
    learning_object = loaded.learning_objects["lo_svd_definition"].model_dump(mode="json")
    learning_object["prerequisites"] = ["matrix factors", "legacy free text"]
    learning_object["confusables"] = ["matrix_factorization"]
    upsert_learning_object(vault_root, learning_object)

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "inspect_entity", "params": {"id": "matrix factors"}},
            {"jsonrpc": "2.0", "id": 3, "method": "inspect_entity", "params": {"id": "lo_svd_definition"}},
        ]
    )

    concept = responses[1]["result"]
    assert concept["kind"] == "concept"
    assert concept["id"] == "matrix_factorization"
    assert concept["detail"]["title"] == "Matrix Factorization"
    assert concept["detail"]["learningObjects"] == []
    assert concept["detail"]["relations"][0]["relationType"] == "confusable_with"
    assert concept["detail"]["relations"][0]["concept"]["conceptId"] == "singular_value_decomposition"

    detail = responses[2]["result"]["detail"]
    assert detail["prerequisiteConcepts"][0] == {
        "reference": "matrix factors",
        "conceptId": "matrix_factorization",
        "title": "Matrix Factorization",
        "resolved": True,
        "source": "authored",
    }
    assert detail["prerequisiteConcepts"][1]["resolved"] is False
    assert detail["confusableConcepts"][0]["conceptId"] == "matrix_factorization"


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


def _seed_standalone_concept_proposal(repository: Repository) -> None:
    repository.insert_agent_run(
        {
            "id": "agent_run_concept_1",
            "purpose": "authoring",
            "provider": "fake",
            "output_schema": "AuthoringProposal",
            "started_at": NOW_ISO,
            "status": "completed",
            "completed_at": NOW_ISO,
        }
    )
    repository.persist_proposal_batch(
        {
            "id": "patch_concept_1",
            "agent_run_id": "agent_run_concept_1",
            "purpose": "authoring",
            "source_refs": [],
            "summary": "Create a standalone concept",
            "created_at": NOW_ISO,
        },
        [
            {
                "id": "proposal_item_concept",
                "client_item_id": "client_concept",
                "item_type": "concept",
                "operation": "create",
                "payload": {
                    "id": "new_concept",
                    "title": "New concept",
                    "type": "concept",
                    "aliases": [],
                    "description": "A standalone concept.",
                    "tags": [],
                    "created_at": NOW_ISO,
                    "updated_at": NOW_ISO,
                },
                "validation_status": "valid",
                "validation_errors": [],
                "created_at": NOW_ISO,
            }
        ],
    )


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


def test_sidecar_get_recent_ingests_lists_canonical_sources(tmp_path):
    # The arxiv fixture vault holds canonical_source notes plus the proposal
    # batches their ingests produced; copy it so loading never mutates it.
    vault_root = tmp_path / "vault"
    shutil.copytree(Path(__file__).resolve().parents[1] / "fixtures" / "arxiv", vault_root)

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_recent_ingests"},
        ]
    )

    ingests = responses[1]["result"]["ingests"]
    assert ingests, "fixture vault should expose canonical_source ingests"
    for entry in ingests:
        assert entry["noteId"]
        assert entry["path"]
        assert entry["purpose"] in {"canonical_ingest", "exam_ingest"}
    stamps = [entry["createdAt"] or entry["retrievedAt"] or "" for entry in ingests]
    assert stamps == sorted(stamps, reverse=True)
    assert any(entry["patchId"] for entry in ingests)


def test_sidecar_ingest_source_classification_and_empty_job_list(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "classify_ingest_source",
                "params": {"source": "arxiv:2401.12345v2"},
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "classify_ingest_source",
                "params": {"source": "lecture-notes.md"},
            },
            {"jsonrpc": "2.0", "id": 4, "method": "get_ingest_jobs"},
        ]
    )

    assert responses[1]["result"] == {
        "version": 1,
        "kind": "arxiv",
        "normalizedSource": "https://arxiv.org/abs/2401.12345v2",
    }
    assert responses[2]["result"]["kind"] == "textfile"
    assert responses[3]["result"] == {"version": 1, "jobs": []}


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


def test_sidecar_reject_accepted_concept_reports_reference_blocker(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    _seed_standalone_concept_proposal(repository)
    apply_accepted_items(vault_root, "patch_concept_1", ["proposal_item_concept"])
    upsert_learning_object(
        vault_root,
        {
            "schema_version": 1,
            "id": "lo_new_concept",
            "title": "New concept LO",
            "subjects": ["linear-algebra"],
            "concept": "new_concept",
            "knowledge_type": "conceptual",
            "status": "active",
            "contradicts": None,
            "summary": "A dependent learning object.",
            "prerequisites": [],
            "confusables": [],
            "difficulty_prior": 0.4,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )

    rejected = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "reject_proposal_items",
                "params": {"patchId": "patch_concept_1", "itemIds": ["proposal_item_concept"]},
            },
        ]
    )[1]

    assert rejected["error"]["data"]["code"] == "invalid_request"
    assert "still referenced" in rejected["error"]["message"]
    assert "learning_object:lo_new_concept.concept" in rejected["error"]["message"]


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
                "params": {"path": "state.sqlite", "table": "t_demo", "rowid": rowid, "column": "a", "value": ""},
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "sqlite_update_cell",
                "params": {"path": "state.sqlite", "table": "t_demo", "rowid": rowid, "column": "b", "value": "42"},
            },
            {"jsonrpc": "2.0", "id": 4, "method": "sqlite_table", "params": {"path": "state.sqlite", "table": "t_demo"}},
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "sqlite_exec",
                "params": {"path": "state.sqlite", "sql": "SELECT a, b FROM t_demo"},
            },
            {"jsonrpc": "2.0", "id": 6, "method": "sqlite_delete_row", "params": {"path": "state.sqlite", "table": "t_demo", "rowid": rowid}},
            {"jsonrpc": "2.0", "id": 7, "method": "sqlite_table", "params": {"path": "state.sqlite", "table": "t_demo"}},
            # A non-database path is refused by the browser.
            {"jsonrpc": "2.0", "id": 8, "method": "sqlite_tables", "params": {"path": "learnloop.toml"}},
        ]
    )

    table = edited[3]["result"]
    assert table["editable"] is True and table["rowCount"] == 1
    assert [col["name"] for col in table["columns"]] == ["a", "b"]
    assert table["rows"][0]["cells"] == ["", 42]  # empty TEXT is distinct from NULL; INTEGER is coerced
    select = edited[4]["result"]
    assert select["kind"] == "rows" and select["columns"] == ["a", "b"]
    assert select["rows"] == [["", 42]]
    assert edited[5]["result"]["ok"] is True  # delete_row
    assert edited[6]["result"]["rowCount"] == 0
    assert edited[7]["error"]["data"]["code"] == "not_found"


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
    text = text.replace('type = "codex_sdk"', 'type = "http_adapter"', 1)
    text = text.replace('provider = "sdk"', 'provider = "http"')
    text = text.replace('checkout_path = ""', f'checkout_path = "{checkout.as_posix()}"')
    text = text.replace('revision = "<pinned-commit>"', 'revision = "abc123"')
    text = text.replace('base_url = "http://127.0.0.1:8765"', f'base_url = "{base_url}"')
    text = text.replace('fallback_provider = ""', 'fallback_provider = "codex"')
    text = text.replace('grading = "codex_low"', 'grading = "deepseek_flash"')
    config_path.write_text(text, encoding="utf-8")


def _configure_ai_codex_only(vault_root, checkout, base_url: str) -> None:
    config_path = vault_root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    ai_prefix, legacy_codex = text.split("\n[codex]\n", 1)
    ai_prefix = ai_prefix.replace('type = "codex_sdk"', 'type = "http_adapter"', 1)
    ai_prefix = ai_prefix.replace('checkout_path = ""', f'checkout_path = "{checkout.as_posix()}"', 1)
    ai_prefix = ai_prefix.replace('revision = "<pinned-commit>"', 'revision = "abc123"', 1)
    ai_prefix = ai_prefix.replace('base_url = "http://127.0.0.1:8765"', f'base_url = "{base_url}"', 1)
    config_path.write_text(f"{ai_prefix}\n[codex]\n{legacy_codex}", encoding="utf-8")


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


def test_sidecar_get_facet_mastery_shape_on_fixture_vault(tmp_path):
    # Radar-chart rollup over the read-only linear_algebra fixture (copied to a
    # temp dir so loading never mutates the tracked fixture files).
    vault_root = tmp_path / "vault"
    shutil.copytree(FIXTURE_VAULT, vault_root)

    result = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_facet_mastery"},
        ]
    )[1]["result"]

    assert result["version"] == 1
    facets = result["facets"]
    assert facets, "fixture vault should expose at least one evidence facet"
    facet_ids = [facet["facetId"] for facet in facets]
    assert facet_ids == sorted(facet_ids)
    assert result["counts"]["facets"] == len(facets)
    assert result["counts"]["learningObjects"] >= 1
    assert result["counts"]["practiceItems"] >= 1

    loaded = load_vault(vault_root)
    item_facets = {facet for item in loaded.practice_items.values() for facet in item.evidence_facets}
    assert item_facets <= set(facet_ids)  # every evidenced facet appears as an axis

    seen_items: set[str] = set()
    seen_los: set[str] = set()
    for facet in facets:
        assert set(facet) == {"facetId", "mastery", "uncertainty", "stateCounts", "learningObjects", "practiceItems", "questionCount"}
        assert 0.0 <= facet["mastery"] <= 1.0
        assert facet["uncertainty"] >= 0.0
        assert set(facet["stateCounts"]) == {"solid", "uncertain", "knownGap", "unexamined"}
        assert sum(facet["stateCounts"].values()) == len(facet["learningObjects"])
        for lo in facet["learningObjects"]:
            assert set(lo) == {"id", "title", "state", "facetMastery"}
            assert lo["id"] in loaded.learning_objects
            assert 0.0 <= lo["facetMastery"] <= 1.0
            seen_los.add(lo["id"])
        for item in facet["practiceItems"]:
            assert set(item) == {"id", "title", "learningObjectId", "weight", "difficulty", "isProbe", "queued"}
            assert item["id"] in loaded.practice_items
            assert len(item["title"]) <= 80
            assert item["weight"] is None or isinstance(item["weight"], (int, float))
            assert item["difficulty"] is None or 0.0 <= item["difficulty"] <= 1.0
            assert isinstance(item["isProbe"], bool)
            assert isinstance(item["queued"], bool)
            if item["isProbe"]:
                assert item["queued"]  # probes surface via the due queue
            seen_items.add(item["id"])
    assert result["counts"]["learningObjects"] == len(seen_los)
    assert result["counts"]["practiceItems"] == len(seen_items)


def test_sidecar_get_knowledge_map_shape_on_fixture_vault(tmp_path):
    # 2D similarity map over the read-only fixture (copied so loading never
    # mutates the tracked fixture files).
    vault_root = tmp_path / "vault"
    shutil.copytree(FIXTURE_VAULT, vault_root)

    result = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_knowledge_map"},
        ]
    )[1]["result"]

    loaded = load_vault(vault_root)
    assert result["version"] == 1
    assert isinstance(result["stress"], float) and result["stress"] >= 0.0
    points = result["points"]
    assert [point["id"] for point in points] == sorted(loaded.practice_items)
    assert result["counts"]["items"] == len(points)
    assert result["counts"]["learningObjects"] == len({p["learningObjectId"] for p in points})
    assert result["counts"]["concepts"] == len({p["conceptId"] for p in points if p["conceptId"] is not None})
    assert result["counts"]["facets"] >= 1

    for point in points:
        assert set(point) == {
            "id",
            "title",
            "learningObjectId",
            "conceptId",
            "x",
            "y",
            "mastery",
            "variance",
            "predictedCorrect",
            "isProbe",
            "queued",
            "difficulty",
            "facets",
            "neighbors",
        }
        assert -1.0 <= point["x"] <= 1.0
        assert -1.0 <= point["y"] <= 1.0
        assert point["mastery"] is None or 0.0 <= point["mastery"] <= 1.0
        assert point["predictedCorrect"] is None or 0.0 <= point["predictedCorrect"] <= 1.0
        assert point["difficulty"] is None or 0.0 <= point["difficulty"] <= 1.0
        assert isinstance(point["isProbe"], bool)
        assert isinstance(point["queued"], bool)
        item = loaded.practice_items[point["id"]]
        assert point["learningObjectId"] == item.learning_object_id
        assert 1 <= len(point["facets"]) <= 3 or not item.evidence_facets
        assert set(point["facets"]) <= set(item.evidence_facets)
        # Neighbors: true blended distances, ranked ascending, never self.
        neighbors = point["neighbors"]
        assert len(neighbors) == min(4, len(points) - 1)
        assert all(set(n) == {"id", "distance"} for n in neighbors)
        assert all(n["id"] in loaded.practice_items and n["id"] != point["id"] for n in neighbors)
        dists = [n["distance"] for n in neighbors]
        assert all(0.0 <= d <= 1.0 for d in dists)
        assert dists == sorted(dists)


def test_sidecar_get_knowledge_map_deterministic_and_geometric(tmp_path):
    vault_root = tmp_path / "vault"
    shutil.copytree(FIXTURE_VAULT, vault_root)

    def fetch() -> dict:
        return _rpc(
            [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
                {"jsonrpc": "2.0", "id": 2, "method": "get_knowledge_map"},
            ]
        )[1]["result"]

    first = fetch()
    second = fetch()
    # Determinism across independent sidecar runs: identical coordinates,
    # identical stress — no random init, no sign flips.
    assert first == second

    loaded = load_vault(vault_root)
    by_id = {point["id"]: point for point in first["points"]}
    lo_concept = {lo_id: lo.concept for lo_id, lo in loaded.learning_objects.items()}

    def dist(a: str, b: str) -> float:
        pa, pb = by_id[a], by_id[b]
        return ((pa["x"] - pb["x"]) ** 2 + (pa["y"] - pb["y"]) ** 2) ** 0.5

    items = sorted(loaded.practice_items.values(), key=lambda item: item.id)
    same_lo_pair = next(
        (a.id, b.id)
        for i, a in enumerate(items)
        for b in items[i + 1 :]
        if a.learning_object_id == b.learning_object_id
    )
    disjoint_pair = next(
        (a.id, b.id)
        for i, a in enumerate(items)
        for b in items[i + 1 :]
        if lo_concept[a.learning_object_id] != lo_concept[b.learning_object_id]
        and not (set(a.evidence_facets) & set(b.evidence_facets))
    )
    # Sanity geometry: items testing the same LO must land closer together than
    # items with disjoint facet vocabularies in different concepts.
    assert dist(*same_lo_pair) < dist(*disjoint_pair)


def test_knowledge_field_is_recipe_topological_and_uses_pooled_ready(tmp_path):
    from learnloop.clock import FrozenClock
    from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
    from learnloop.services.state_sync import sync_vault_state
    from tests.helpers import NOW
    from tests.test_km3_projections import COMP_A, COMP_B, INTEG, build_blueprint_vault

    paths = build_blueprint_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft("pi_comp_a", "answer"),
        SelfGradeInput(criterion_points={"c1": 4}, confidence=5),
        clock=FrozenClock(NOW),
    )

    field = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(paths.root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_knowledge_map"},
        ]
    )[1]["result"]["facetField"]
    by_id = {point["id"]: point for point in field["points"]}
    assert set(by_id) == {COMP_A, COMP_B, INTEG}
    assert {
        tuple(sorted((edge["source"], edge["target"]))) for edge in field["edges"]
    } == {
        tuple(sorted(pair))
        for pair in ((COMP_A, COMP_B), (COMP_A, INTEG), (COMP_B, INTEG))
    }
    demonstrated = by_id[COMP_A]
    assert demonstrated["readyGhost"] > 0.5  # pooled capability slices, not a missing `shared` row
    assert 0.0 <= demonstrated["ready"] <= demonstrated["readyGhost"]
    assert demonstrated["demonstratedMass"] == 1.0
    assert demonstrated["demonstratedCapabilities"] == ["procedure_execution"]
    assert field["layoutVersion"].startswith("sha256:")
    assert field["layoutValid"] is True
    assert field["nextGap"] is not None


def test_sidecar_get_knowledge_map_history_empty_and_after_attempt(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)

    # Before any attempts: empty feeds, null range.
    empty = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_knowledge_map_history"},
        ]
    )[1]["result"]
    assert empty["version"] == 1
    assert empty["attempts"] == []
    assert empty["learningObjects"] == []
    assert empty["range"] is None

    session_id = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "start_session", "params": {"energy": "medium"}},
        ]
    )[1]["result"]["sessionId"]
    _rpc(
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
    )

    history = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_knowledge_map_history"},
        ]
    )[1]["result"]

    attempts = history["attempts"]
    assert len(attempts) == 1
    event = attempts[0]
    assert set(event) == {
        "id",
        "t",
        "practiceItemId",
        "learningObjectId",
        "attemptType",
        "correctness",
        "rubricScore",
        "hintsUsed",
    }
    assert event["practiceItemId"] == "pi_svd_define_001"
    assert event["attemptType"] == "independent_attempt"
    assert event["correctness"] is None or 0.0 <= event["correctness"] <= 1.0

    # The mastery update recorded a posterior delta, so the LO's trajectory has
    # a step at the attempt's timestamp with a valid display-space mastery.
    series_by_lo = {lo["id"]: lo["series"] for lo in history["learningObjects"]}
    assert event["learningObjectId"] in series_by_lo
    series = series_by_lo[event["learningObjectId"]]
    assert len(series) == 1
    assert series[0]["t"] == event["t"]
    assert 0.0 <= series[0]["mastery"] <= 1.0

    assert history["range"] == {"start": event["t"], "end": event["t"]}


def test_sidecar_set_grading_provider_switch_and_health(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_runtime_health"},
            {"jsonrpc": "2.0", "id": 3, "method": "set_grading_provider", "params": {"provider": "deepseek_flash"}},
            {"jsonrpc": "2.0", "id": 4, "method": "get_runtime_health"},
        ]
    )

    baseline = responses[1]["result"]["ai"]
    assert baseline["manualGrading"] is False
    assert baseline["gradingProviderOverride"] is None
    # Dropdown options ship with the health dto: configured providers + codex + manual.
    assert {"codex", "deepseek_flash", "deepseek_pro", "manual"} <= set(baseline["availableGradingProviders"])
    assert baseline["availableGradingProviders"][-1] == "manual"

    switched = responses[2]["result"]
    assert switched["activeProvider"] == "deepseek_flash"
    assert switched["manualGrading"] is False
    assert isinstance(switched["ready"], bool)
    assert switched["availableProviders"] == baseline["availableGradingProviders"]

    health = responses[3]["result"]["ai"]
    assert health["activeProvider"] == "deepseek_flash"
    assert health["gradingProviderOverride"] == "deepseek_flash"
    assert health["manualGrading"] is False


def test_sidecar_set_grading_provider_manual_forces_self_grade_fallback(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)

    session_id = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "start_session", "params": {"energy": "medium"}},
        ]
    )[1]["result"]["sessionId"]

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "set_grading_provider", "params": {"provider": "manual"}},
            {"jsonrpc": "2.0", "id": 3, "method": "get_runtime_health"},
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "submit_attempt",
                "params": {
                    "sessionId": session_id,
                    "practiceItemId": "pi_svd_define_001",
                    "answerMd": "SVD is U Sigma V transpose.",
                    "attemptType": "independent_attempt",
                    "hintsUsed": 0,
                },
            },
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "submit_attempt",
                "params": {
                    "sessionId": session_id,
                    "practiceItemId": "pi_svd_define_001",
                    "answerMd": "SVD is U Sigma V transpose.",
                    "attemptType": "independent_attempt",
                    "hintsUsed": 0,
                    "selfGrade": {"criterionPoints": {"correctness": 4}, "confidence": 5},
                },
            },
        ]
    )

    manual = responses[1]["result"]
    assert manual == {
        "version": 1,
        "activeProvider": "manual",
        "manualGrading": True,
        "ready": True,
        "availableProviders": manual["availableProviders"],
    }
    assert "manual" in manual["availableProviders"]

    health = responses[2]["result"]["ai"]
    assert health["activeProvider"] == "manual"
    assert health["manualGrading"] is True
    assert health["ready"] is True
    assert health["status"] == "manual"
    assert health["gradingProviderOverride"] == "manual"

    # Without a self-grade the sidecar demands the manual fallback...
    assert responses[3]["error"]["data"]["code"] == "grading_fallback_required"
    # ...and with one, the attempt records as self-graded.
    assert responses[4]["result"]["gradingSource"] == "self"


def test_sidecar_set_grading_provider_rejects_unknown_provider(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)

    response = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "set_grading_provider", "params": {"provider": "gpt99"}},
            {"jsonrpc": "2.0", "id": 3, "method": "get_runtime_health"},
        ]
    )

    error = response[1]["error"]
    assert error["data"]["code"] == "invalid_provider"
    assert "gpt99" in error["message"]
    for option in ("codex", "deepseek_flash", "deepseek_pro", "manual"):
        assert option in error["message"]
    assert "manual" in error["data"]["details"]["available_providers"]
    # A rejected switch leaves the override untouched.
    assert response[2]["result"]["ai"]["gradingProviderOverride"] is None


def test_sidecar_durable_ingest_batch_rpcs(tmp_path):
    """The Source library + Batch progress RPCs (§6.3): registration, camelCase
    envelope, and the import batch/library round-trip."""

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    source = vault_root / "notes.md"
    source.write_text("# Eigen\n\nAn eigenvector of A is a vector v with Av = lambda v.\n", encoding="utf-8")

    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "list_ingest_batches", "params": {"limit": 5}},
            {"jsonrpc": "2.0", "id": 3, "method": "start_import_batch", "params": {"sources": [str(source)]}},
            {"jsonrpc": "2.0", "id": 4, "method": "get_source_library"},
        ]
    )

    assert responses[1]["result"]["batches"] == []
    batch = responses[2]["result"]
    assert batch["status"] in {"queued", "running", "completed"}
    assert len(batch["jobs"]) == 1
    job = batch["jobs"][0]
    assert job["jobType"] == "import"
    assert isinstance(job["checkpointLadder"], list) and "extracted" in job["checkpointLadder"]
    # get_source_library returns the camelCase card envelope (may be mid-drain).
    assert "sources" in responses[3]["result"]


def test_sidecar_get_ingest_batch_not_found(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {"jsonrpc": "2.0", "id": 2, "method": "get_ingest_batch", "params": {"batchId": "batch_missing"}},
        ]
    )
    assert responses[1]["error"]["data"]["code"] == "ingest_batch_not_found"


def test_sidecar_import_rejects_incomplete_or_reversed_page_ranges(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    source = vault_root / "textbook.pdf"
    source.write_bytes(b"%PDF-placeholder")
    responses = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "start_import_batch",
                "params": {"sources": [str(source)], "pageStart": 4},
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "start_import_batch",
                "params": {"sources": [str(source)], "pageStart": 8, "pageEnd": 3},
            },
        ]
    )
    assert responses[1]["error"]["data"]["code"] == "invalid_page_range"
    assert responses[2]["error"]["data"]["code"] == "invalid_page_range"


def test_sidecar_import_rejects_page_range_for_source_outside_batch(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    source = vault_root / "textbook.pdf"
    source.write_bytes(b"%PDF-placeholder")
    response = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "start_import_batch",
                "params": {
                    "sources": [str(source)],
                    "pageRanges": [{"source": str(vault_root / "other.pdf"), "pageStart": 1, "pageEnd": 3}],
                },
            },
        ]
    )[1]
    assert response["error"]["data"]["code"] == "invalid_page_range"


def test_sidecar_multi_source_import_rejects_shared_top_level_range(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    sources = [vault_root / "one.pdf", vault_root / "two.pdf"]
    for source in sources:
        source.write_bytes(b"%PDF-placeholder")
    response = _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "start_import_batch",
                "params": {"sources": [str(source) for source in sources], "pageStart": 1, "pageEnd": 3},
            },
        ]
    )[1]
    assert response["error"]["data"]["code"] == "invalid_page_range"
    assert "separate page range" in response["error"]["message"]


def test_disjoint_pdf_page_expression_normalizes_to_exact_zero_based_pages():
    from learnloop_sidecar.handlers.ingest import _parse_page_selection

    pages = _parse_page_selection("3-27, 29-33, 36, 5-7")
    assert pages == [*range(2, 27), *range(28, 33), 35]


@pytest.mark.parametrize("expression", ["3-", "9-4", "3,,5", "0", "chapter 3"])
def test_invalid_pdf_page_expressions_are_rejected(expression):
    from learnloop_sidecar.errors import SidecarError
    from learnloop_sidecar.handlers.ingest import _parse_page_selection

    with pytest.raises(SidecarError) as exc_info:
        _parse_page_selection(expression)
    assert exc_info.value.code == "invalid_page_range"


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def test_sidecar_create_vault_initializes_fresh_vault(tmp_path):
    # create_vault needs no prior `initialize` — it scaffolds a brand-new vault
    # on disk (the NewVault wizard's first step) and returns its root + subject.
    vault_root = tmp_path / "new-vault"
    response = _rpc(
        [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "create_vault",
                "params": {"path": str(vault_root), "subject": "Linear Algebra"},
            }
        ]
    )[0]
    result = response["result"]
    assert result["vaultRoot"] == str(vault_root.resolve())
    assert result["subjectId"] == "linear-algebra"
    # Scaffolding is on disk and the vault loads cleanly with the seeded subject.
    assert (vault_root / "learnloop.toml").exists()
    loaded = load_vault(vault_root)
    assert "linear-algebra" in loaded.subjects


def test_sidecar_create_vault_is_idempotent_on_existing_vault(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    result = _rpc(
        [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "create_vault",
                "params": {"path": str(vault_root)},
            }
        ]
    )[0]["result"]
    assert result["vaultRoot"] == str(vault_root.resolve())
    assert result["subjectId"] is None
    assert (vault_root / "learnloop.toml").exists()


def test_sidecar_create_vault_refuses_populated_non_vault_dir(tmp_path):
    junk = tmp_path / "not-a-vault"
    junk.mkdir()
    (junk / "notes.txt").write_text("hello", encoding="utf-8")
    response = _rpc(
        [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "create_vault",
                "params": {"path": str(junk)},
            }
        ]
    )[0]
    assert "error" in response
    assert response["error"]["data"]["code"] == "vault_dir_not_empty"
    # The guard left the directory untouched — no vault scaffolding written.
    assert not (junk / "learnloop.toml").exists()
