"""P3 slice 2 reader sidecar RPC contract: palette + demand-paged synthesis +
source objects (spec §5-§7, §15.2/§15.3). Drives serve() end-to-end in-process."""

from __future__ import annotations

from pathlib import Path

from tests.test_sidecar_reader_p3 import _rpc, _setup


def test_invoke_preset_commit_enqueues_synthesis_and_proposes(tmp_path: Path) -> None:
    root = _setup(tmp_path)
    sel = {"nodes": [{"spanId": "s1", "quote": "Symmetric"}]}
    out = _rpc(root, [
        ("reader.set_mode", {"mode": "anchor", "extractionId": "ext1"}),
        ("reader.invoke_preset", {
            "preset": "help_me_remember", "sourceId": "src1", "revisionId": "rev1",
            "extractionId": "ext1", "clientIdempotencyKey": "p1", "rawSelection": sel,
            "subjectId": "s1", "learnerText": "keep this",
        }),
        ("reader.drain_outbox", {}),
        ("reader.source_requests", {"sourceId": "src1"}),
        ("reader.drain_requests", {}),
        ("reader.source_objects", {"sourceId": "src1"}),
        ("reader.proposal_inbox", {"status": "proposed"}),
    ])
    assert out[1]["result"]["mode"] == "anchor"
    assert out[1]["result"]["presentsOwnerQuestions"] == "at_boundaries"
    receipt = out[2]["result"]
    assert receipt["receipt"] == "acknowledged"
    assert receipt["preset"] == "help_me_remember"
    assert receipt["commitmentId"]  # commit preset created a commitment
    assert out[3]["result"]["drained"]
    requests = out[4]["result"]["requests"]
    assert len(requests) == 1 and requests[0]["preset"] == "help_me_remember"
    drain = out[5]["result"]
    assert len(drain["completed"]) == 1
    assert len(out[6]["result"]["sourceObjects"]) == 1
    assert len(out[7]["result"]["proposals"]) >= 1  # reviewable, not auto-admitted


def test_ask_and_mark_presets_create_no_commitment(tmp_path: Path) -> None:
    root = _setup(tmp_path)
    sel = {"nodes": [{"spanId": "s1", "quote": "Symmetric"}]}
    out = _rpc(root, [
        ("reader.invoke_preset", {"preset": "ask", "sourceId": "src1", "revisionId": "rev1",
                                  "extractionId": "ext1", "clientIdempotencyKey": "a1",
                                  "rawSelection": sel, "subjectId": "s1"}),
        ("reader.invoke_preset", {"preset": "mark_confusing", "sourceId": "src1", "revisionId": "rev1",
                                  "extractionId": "ext1", "clientIdempotencyKey": "m1",
                                  "rawSelection": sel, "subjectId": "s1"}),
        ("reader.invoke_preset", {"preset": "not_worth_remembering", "sourceId": "src1", "revisionId": "rev1",
                                  "extractionId": "ext1", "clientIdempotencyKey": "n1",
                                  "rawSelection": sel, "subjectId": "s1"}),
    ])
    assert out[1]["result"]["commitmentId"] is None
    assert out[2]["result"]["commitmentId"] is None
    assert out[3]["result"]["commitmentId"] is None
    assert out[3]["result"]["suppressesProposals"] is True


def test_enqueue_request_dedupes_and_shows_scope_and_caps(tmp_path: Path) -> None:
    root = _setup(tmp_path)
    out = _rpc(root, [
        ("reader.enqueue_request", {"sourceId": "src1", "revisionId": "rev1", "extractionId": "ext1",
                                    "spanId": "s1", "preset": "worked_example"}),
        ("reader.enqueue_request", {"sourceId": "src1", "revisionId": "rev1", "extractionId": "ext1",
                                    "spanId": "s1", "preset": "worked_example"}),
    ])
    first = out[1]["result"]
    assert first["deduplicated"] is False
    assert "spanIds" in first["scope"]
    assert first["tokenCap"] > 0 and "capRemaining" in first
    # Same contract -> same request key -> reused standing request (§15.3).
    assert out[2]["result"]["deduplicated"] is True
    assert out[2]["result"]["requestKey"] == first["requestKey"]


def test_question_control_i_dont_understand_routes_to_restoration(tmp_path: Path) -> None:
    root = _setup(tmp_path)
    out = _rpc(root, [
        ("reader.question_control", {"control": "i_dont_understand", "subjectId": "s1"}),
        ("reader.question_control", {"control": "too_easy", "subjectId": "s1"}),
    ])
    assert out[1]["result"]["routesTo"] == "source_restoration"
    assert out[1]["result"]["signal"] == "interaction_policy"
    assert out[2]["result"]["routesTo"] is None


def test_reading_usable_with_synthesis_worker_down(tmp_path: Path) -> None:
    # §15.3 / §1.1.1: open, render, capture, and enqueue all succeed WITHOUT ever
    # draining the synthesis worker. The request simply stays queued.
    root = _setup(tmp_path)
    sel = {"nodes": [{"spanId": "s1", "quote": "Symmetric"}]}
    out = _rpc(root, [
        ("reader.render_view", {"extractionId": "ext1"}),
        ("reader.invoke_preset", {"preset": "help_me_remember", "sourceId": "src1", "revisionId": "rev1",
                                  "extractionId": "ext1", "clientIdempotencyKey": "d1",
                                  "rawSelection": sel, "subjectId": "s1"}),
        ("reader.drain_outbox", {}),
        ("reader.source_requests", {"sourceId": "src1"}),
    ])
    assert len(out[1]["result"]["blocks"]) == 1
    assert out[2]["result"]["receipt"] == "acknowledged"
    # Worker never ran -> request is durably queued, reading still fully worked.
    assert out[4]["result"]["requests"][0]["status"] == "queued"
