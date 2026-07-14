from __future__ import annotations

from learnloop.db.repositories import Repository

from tests.helpers import create_basic_vault
from tests.test_sidecar_contract import _rpc


def _initialize(vault_root, request_id: int = 1) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "initialize",
        "params": {"vaultPath": str(vault_root)},
    }


def test_claim_rpc_round_trip_preserves_presentation_linkage(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    presented = _rpc(
        [
            _initialize(vault_root),
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "present_claims",
                "params": {
                    "visitId": "visit-contract",
                    "claims": [
                        {
                            "claimClass": "estimate",
                            "claimType": "ready_estimate",
                            "claimRef": {"facet": "recall"},
                            "claimVersion": "claim-v1",
                            "producerVersion": "producer-v1",
                            "surface": "contract-test",
                            "temperature": "cold",
                            "visibleAt": "2026-07-14T12:00:00Z",
                        }
                    ],
                },
            },
        ]
    )[1]["result"]["claims"][0]
    assert presented["affordancesEnabled"] is True
    assert presented["presentationId"]

    responses = _rpc(
        [
            _initialize(vault_root),
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "respond_claim",
                "params": {
                    "presentationId": presented["presentationId"],
                    "responsePayload": {"response": "about_right"},
                },
            },
            {"jsonrpc": "2.0", "id": 3, "method": "export_claims"},
        ]
    )
    response = responses[1]["result"]["event"]
    assert response["presentationId"] == presented["presentationId"]
    assert response["responsePayload"] == {"response": "about_right"}
    assert [event["eventType"] for event in responses[2]["result"]["events"]] == [
        "presented",
        "responded",
    ]


def test_review_remediation_and_track_record_rpcs_are_frontend_ready(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    misconception_id = repository.insert_misconception(
        learning_object_id="lo_svd_definition",
        statement="Confuses the left and right singular-vector roles.",
        correction_statement="U acts in the output space; V acts in the input space.",
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        mechanism="selection_error",
        severity=0.8,
    )

    responses = _rpc(
        [
            _initialize(vault_root),
            {"jsonrpc": "2.0", "id": 2, "method": "get_review_log"},
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "start_remediation",
                "params": {"misconceptionId": misconception_id},
            },
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "get_forecast_track_record",
                "params": {},
            },
            {"jsonrpc": "2.0", "id": 5, "method": "get_answer_calibration"},
        ]
    )
    review = responses[1]["result"]
    assert review["workingHypotheses"][0]["id"] == misconception_id
    assert review["workingHypotheses"][0]["correctionStatement"]

    remediation = responses[2]["result"]
    episode_id = remediation["episode"]["id"]
    assert remediation["case"]["correctionStatement"]
    assert remediation["episode"]["state"] == "diagnosis"

    track_record = responses[3]["result"]["trackRecord"]
    assert set(track_record["byKind"]) == {"decay", "pace", "plan"}
    calibration = responses[4]["result"]
    assert calibration["items"]["minimumN"] > 0
    assert calibration["items"]["curveAvailable"] is False
    assert calibration["duel"] == {
        "n": 0,
        "learnerBrier": None,
        "modelBrier": None,
    }

    prescribed = _rpc(
        [
            _initialize(vault_root),
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "prescribe_remediation",
                "params": {"episodeId": episode_id},
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "start_remediation_treatment",
                "params": {"episodeId": episode_id},
            },
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "get_remediation",
                "params": {"episodeId": episode_id},
            },
        ]
    )
    assert prescribed[1]["result"]["episode"]["state"] == "prescribed"
    assert prescribed[2]["result"]["episode"]["state"] == "treatment"
    assert prescribed[2]["result"]["practiceItem"]["id"]
    assert prescribed[3]["result"]["episode"]["id"] == episode_id


def test_session_end_contract_includes_learning_diff(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    started = _rpc(
        [
            _initialize(vault_root),
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "start_session",
                "params": {"energy": "medium"},
            },
        ]
    )[1]["result"]
    ended = _rpc(
        [
            _initialize(vault_root),
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "end_session",
                "params": {"sessionId": started["sessionId"]},
            },
        ]
    )[1]["result"]
    assert ended["facetsDemonstrated"] == 0
    assert ended["predictionsMoved"] == {"up": 0, "down": 0}
    assert ended["corrections"] == 0
    assert ended["misconceptionsTouched"] == {"resolved": 0, "returned": 0}
