"""P3 slice 3 reader sidecar RPC: authoring + coach + maintenance, arcs + depth +
primes, and restoration (spec §9-§11). Drives serve() end-to-end in-process."""

from __future__ import annotations

from pathlib import Path

from tests.test_sidecar_reader_p3 import _rpc, _setup

_SEL = {"nodes": [{"spanId": "s1", "quote": "Symmetric"}]}


def test_author_qa_persists_before_ai_and_coach_is_non_blocking(tmp_path: Path) -> None:
    root = _setup(tmp_path)
    out = _rpc(root, [
        ("reader.author_qa", {
            "question": "Why real eigenvalues?", "answer": "Because A = A^T.",
            "sourceId": "src1", "revisionId": "rev1", "clientIdempotencyKey": "qa1",
        }),
        ("reader.coach_lint", {"question": "Why real eigenvalues?", "answer": "Because A = A^T.",
                               "level": "expert"}),
    ])
    authored = out[1]["result"]
    assert authored["authoredBeforeAi"] is True
    assert authored["authorship"] == "learner" and authored["pinned"] is True
    assert authored["commitmentId"] and authored["cardVersionId"]
    assert out[2]["result"]["blocking"] is False


def test_arc_lifecycle_over_rpc(tmp_path: Path) -> None:
    root = _setup(tmp_path)
    out = _rpc(root, [
        ("reader.invoke_preset", {
            "preset": "help_me_remember", "sourceId": "src1", "revisionId": "rev1",
            "extractionId": "ext1", "clientIdempotencyKey": "c1", "rawSelection": _SEL, "subjectId": "s1",
        }),
    ])
    receipt = out[1]["result"]
    arc_id = receipt["arcId"]
    assert arc_id and receipt["arc"]["currentStage"] == "comprehend"
    out2 = _rpc(root, [
        ("reader.arc", {"arcId": arc_id}),
        ("reader.set_depth_policy", {"arcId": arc_id, "policy": "auto_within_envelope"}),
        ("reader.pause_arc", {"arcId": arc_id, "reason": "later"}),
        ("reader.prime", {"arcId": arc_id, "questionRef": "q1", "section": "N"}),
        ("reader.prime", {"arcId": arc_id, "questionRef": "q1", "answer": True}),
    ])
    # arc create in the first serve() persisted; re-open and project.
    assert out2[1]["result"]["arcId"] == arc_id
    assert out2[2]["result"]["policy"] == "auto_within_envelope"
    assert out2[3]["result"]["paused"] is True
    assert out2[4]["result"]["coldCredit"] is False
    assert out2[5]["result"]["satisfiesCertification"] is False


def test_shrink_envelope_rpc_rejects_widening(tmp_path: Path) -> None:
    # F4 regression over the RPC path: a "shrink" that widens the envelope on a
    # dimension is surfaced as a validation_error, not an internal crash.
    root = _setup(tmp_path)
    out = _rpc(root, [
        ("reader.invoke_preset", {
            "preset": "help_me_remember", "sourceId": "src1", "revisionId": "rev1",
            "extractionId": "ext1", "clientIdempotencyKey": "c1", "rawSelection": _SEL, "subjectId": "s1",
        }),
    ])
    arc_id = out[1]["result"]["arcId"]
    # The preset commitment starts with an empty envelope, so adding any bound widens.
    out2 = _rpc(root, [
        ("reader.shrink_envelope", {
            "arcId": arc_id,
            "bounds": {"capability_additions": ["procedure_execution"]},
            "reviewedEdges": [],
        }),
    ])
    assert out2[1]["error"]["data"]["code"] == "validation_error"

    # A genuine contraction over the same RPC still succeeds.
    out3 = _rpc(root, [
        ("reader.shrink_envelope", {"arcId": arc_id, "bounds": {}, "reviewedEdges": []}),
    ])
    assert out3[1]["result"]["shrunk"] is True


def test_maintain_retire_preserves_evidence(tmp_path: Path) -> None:
    root = _setup(tmp_path)
    out = _rpc(root, [
        ("reader.author_qa", {"question": "q?", "answer": "a", "clientIdempotencyKey": "m1"}),
    ])
    commitment_id = out[1]["result"]["commitmentId"]
    out2 = _rpc(root, [
        ("reader.maintain", {"action": "retire", "commitmentId": commitment_id}),
    ])
    assert out2[1]["result"]["evidencePreserved"] is True


def test_restore_returns_annotation_heads(tmp_path: Path) -> None:
    root = _setup(tmp_path)
    out = _rpc(root, [
        ("reader.capture", {
            "sourceId": "src1", "revisionId": "rev1", "extractionId": "ext1",
            "action": "interpretation", "clientIdempotencyKey": "cap1", "rawSelection": _SEL,
            "learnerText": "my note",
        }),
        ("reader.restore", {"sourceId": "src1", "extractionId": "ext1"}),
    ])
    restored = out[2]["result"]
    assert restored["observationMutated"] is False
    assert restored["annotations"] and restored["annotations"][0]["learnerText"] == "my note"


def test_slice3_methods_gated_when_disabled(tmp_path: Path) -> None:
    root = _setup(tmp_path, reader_enabled=False)
    out = _rpc(root, [("reader.author_qa", {"question": "q?", "answer": "a"})])
    assert out[1]["error"]["data"]["code"] == "reader_disabled"
