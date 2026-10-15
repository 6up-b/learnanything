"""`learnloop ai compare` against a fake Responses SSE server (two ChatGPT-plan profiles).

The comparison grades, diagnoses (snapshot, served workspace) and generates on
each profile and reports agreement, validity, latency, tokens and plan
allowance. Covered: the dry run sends nothing, a run on a --copy-from copy
leaves the original untouched and its receipts in the copy, agreement is
computed per pair, a usage limit stops that profile, and working vaults,
metered and unknown profiles are refused. No test leaves 127.0.0.1.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess

import pytest
import tomlkit
from typer.testing import CliRunner

from learnloop.ai.chatgpt_plan.session import PlanSession
from learnloop.attempts.blind_grading import BlindGradingProposal
from learnloop.ai.transport import StructuredRequest
from learnloop.cli import app
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.chatgpt_plan_fakes import (
    Reply,
    completed_events,
    failed_events,
    fake_chatgpt,
    served_outputs,
    sign_in,
    tool_call_events,
)
from tests.diagnosis_fakes import ReviewFakeClient, prompt_payload
from tests.diagnosis_split_helpers import build_diagnosis_vault, seed_history

FAST, PRO = "gpt-test-fast", "gpt-test-pro"


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    monkeypatch.setattr("learnloop.ai.providers.chatgpt_plan._sleep", lambda _seconds: None)


def _grade(body: dict) -> str:
    content = body["input"][0]["content"]
    proposal = ReviewFakeClient().complete(StructuredRequest(
        purpose="blind_grading", prompt=content, result_model=BlindGradingProposal))
    data = proposal.model_dump(mode="json")
    if body["model"] == PRO and data["rubric_score"] and data["criterion_evidence"]:
        # The second profile docks a full-credit answer's last criterion.
        data["criterion_evidence"][-1]["points_awarded"] = 0.0
        data["rubric_score"] = int(sum(row["points_awarded"] for row in data["criterion_evidence"]))
    return json.dumps(data)


def _diagnose(body: dict) -> list[dict]:
    outputs = served_outputs(body)
    if not outputs:
        return tool_call_events([("read_entry", {"path": "INDEX.md", "start_line": None, "max_lines": None})],
                                response_id="d1")
    if len(outputs) == 1:
        path = next(line[2:].split(":")[0] for line in outputs[0].splitlines()
                    if line.startswith("- attempts/") and "att_02_svd_fail" in line)
        return tool_call_events([("read_entry", {"path": path, "start_line": None, "max_lines": None})],
                                response_id="d2")
    cited = outputs[-1].splitlines()[1].replace("# Attempt ", "").strip()
    context = prompt_payload(body["input"][0]["content"])["context"]
    events = [{
        "event_index": row.get("index", index),
        "first_divergence_quote": (row.get("first_divergence") or {}).get("quote"),
        "causal_class": "learner_state",
        "candidate_causes": [{"statement": "The learner leaves V untransposed.", "cause_scope": "learner_state",
                              "prior_weight": 1.0}],
        "registry_match": {"kind": "abstain"}, "history_changed_cause": {"changed": False, "note": ""},
    } for index, row in enumerate(context["current_attempt"]["blind_grade"]["error_attributions"])]
    return completed_events(json.dumps({
        "evidence_attempt_ids": [cited], "analysis_md": "The same untransposed factor as before.",
        "event_diagnoses": events, "repair_suggestions": [], "pattern_claims": [],
        "prerequisite_gap_hypotheses": [], "abstentions": [],
    }))


def _author(body: dict) -> str:
    context = prompt_payload(body["input"][0]["content"])["context"]
    criterion = context["source_criteria"][0]
    facets = [facet["id"] for facet in context["allowed_facets"]][:1]
    return json.dumps({
        "prompt_md": "Explain why the SVD's last factor is transposed.",
        "expected_answer_md": "Because A = U Sigma V^T maps through V^T first.",
        "core_criteria": [{"description": "Names the transpose.", "source_criterion_ids": [criterion["id"]],
                           "measurement_status": "direct", "facet_ids": facets}],
        "transfer_criterion": None, "transfer_scenario": "", "quest_connection": "no_quest",
        "trace_contract": None,
    })


def responder(*, limited_model: str | None = None, no_tools_model: str | None = None):
    """The fake models: grade, diagnose by reading the served export, author."""

    def reply(body: dict) -> Reply:
        if body["model"] == limited_model:
            return Reply(events=failed_events("subscription_sharing_usage_limit_exceeded"))
        if body["model"] == no_tools_model and "tools" in body:
            return Reply(status=400, body={"error": {"code": "subscription_sharing_unsupported_capability",
                                                     "message": "tools unsupported", "param": "tools"}})
        content = body["input"][0]["content"]
        if content.startswith("learnloop blind grading proposal"):
            return Reply(events=completed_events(_grade(body), model=body["model"]))
        if content.startswith("learnloop diagnosis proposal"):
            return Reply(events=_diagnose(body))
        if content.startswith("learnloop source-item teach-back authoring"):
            return Reply(events=completed_events(_author(body), model=body["model"]))
        raise AssertionError(content[:80])

    return reply


@pytest.fixture
def server():
    with fake_chatgpt() as fake:
        sign_in(PlanSession(), fake)
        yield fake


@pytest.fixture
def source(tmp_path, server):
    paths = build_diagnosis_vault(tmp_path / "source")
    seed_history(paths)
    document = tomlkit.parse((paths.root / "learnloop.toml").read_text(encoding="utf-8"))
    for name, model in (("chatgpt", FAST), ("chatgpt_pro", PRO)):
        table = tomlkit.table()
        for key, value in {"type": "chatgpt_plan", "model": model, "base_url": server.base_url,
                           "timeout_seconds": 30}.items():
            table[key] = value
        document["ai"]["providers"][name] = table
    (paths.root / "learnloop.toml").write_text(tomlkit.dumps(document), encoding="utf-8")
    return paths.root


def _invoke(*args: str):
    result = CliRunner().invoke(app, ["ai", "compare", *args, "--json"], catch_exceptions=False)
    return result, json.loads(result.stdout)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_the_dry_run_names_the_plan_and_sends_nothing(source, server):
    result, payload = _invoke("--vault", str(source), "--profiles", "chatgpt,chatgpt_pro", "--dry-run")
    assert result.exit_code == 0, result.stdout
    assert payload["dry_run"] is True
    assert [(row["provider"], row["ready"], row["read_only_workspace"], row["billing"])
            for row in payload["profiles"]] == [("chatgpt", True, True, "subscription"),
                                                ("chatgpt_pro", True, True, "subscription")]
    targets = payload["targets"]
    # The latest non-pass and pass attempts first, then the latest others.
    assert targets["grading"] == ["att_03_svd_pass", "att_06_svd_fail", "att_07_svd_future"]
    assert targets["diagnosis"] == "att_07_svd_future"
    assert targets["generation_item"] == "pi_svd_compute_002"
    assert (payload["calls_per_profile"], payload["max_calls"]) == (5, 10)
    assert all(tokens > 0 for tokens in payload["estimate"]["grading_input_tokens"])
    assert server.requests == []


def test_a_run_on_a_copy_reports_agreement_validity_latency_tokens_and_allowance(source, server, tmp_path):
    server.default_reply = responder()
    database = VaultPaths(source, load_vault(source).config).sqlite_path
    before = _digest(database)
    copy = tmp_path / "copies" / "compare"
    reports = tmp_path / "reports"
    result, report = _invoke("--copy-from", str(source), "--vault", str(copy), "--profiles", "chatgpt",
                             "--profiles", "chatgpt_pro", "--output", str(reports))
    assert result.exit_code == 0, result.stdout
    assert Path(report["report_path"]).parent == reports
    assert json.loads(Path(report["report_path"]).read_text())["agreement"] == report["agreement"]
    assert report["copied"] and report["calls_made"] == 10
    for row in report["results"]:
        summary = row["summary"]
        assert (summary["calls"], summary["valid"], summary["parsed"]) == (5, 5, 5), row
        assert summary["errors"] == [] and summary["allowance_errors"] == 0
        assert summary["input_tokens"] > 0 and summary["output_tokens"] > 0 and summary["tokens_per_call"] > 0
        assert summary["seconds_median"] is not None
        diagnosis = row["diagnosis"]
        assert diagnosis["valid"] and diagnosis["unknown_id_count"] == 0
        assert diagnosis["evidence_attempt_ids"] == ["att_02_svd_fail"]
        assert (diagnosis["workspace_rounds"], diagnosis["workspace_served_files"], diagnosis["physical_requests"]) \
            == (3, 2, 3)
        assert diagnosis["snapshot"]["opened_reported"] and diagnosis["snapshot"]["opened_count"] == 2
        assert row["generation"]["valid"] and all(row["generation"]["checks"].values())
        assert row["allowance_before"]["state"] == row["allowance_after"]["state"] == "ready"
        assert row["grading"]["att_03_svd_pass"]["physical_requests"] == 1
    fast, pro = (row["grading"]["att_03_svd_pass"] for row in report["results"])
    assert (fast["rubric_score"], pro["rubric_score"]) == (4, 2)
    (pair,) = report["agreement"]
    assert pair["profiles"] == ["chatgpt", "chatgpt_pro"]
    grading = pair["grading"]
    assert grading["compared"] == 3 and grading["exact_rate"] == round(2 / 3, 4)
    assert grading["criterion_agreement"] == round((1 + 1 + 0.5) / 3, 4)
    assert grading["full_credit_agreement"] == round(2 / 3, 4)
    assert pair["diagnosis"] == {"both_valid": True, "same_causal_classes": True, "evidence_jaccard": 1.0,
                                 "unknown_ids": [0, 0]}
    assert pair["generation"]["both_valid"] is True
    # The vault recorded 2/4 on the two failed attempts; the fake grader gives 0.
    assert report["results"][0]["vs_recorded_grade"]["exact_rate"] == round(1 / 3, 4)
    # Ids and numbers only: no learner answer or model prose in the report.
    text = json.dumps(report)
    assert "U Sigma V again" not in text and "untransposed" not in text and "Explain why" not in text

    # The original is only read; the receipts land in the copy.
    assert _digest(database) == before
    copied = VaultPaths(copy, load_vault(copy).config).sqlite_path
    with closing(sqlite3.connect(copied)) as connection:
        rows = connection.execute(
            "SELECT provider, purpose, status FROM model_call_receipts WHERE purpose = 'responses_request'"
        ).fetchall()
    assert {provider for provider, _purpose, _status in rows} == {"chatgpt", "chatgpt_pro"}
    assert len(rows) == 2 * (3 + 3 + 1)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM model_call_receipts").fetchone()[0] == 0


def test_a_usage_limit_stops_that_profile_and_shows_in_its_allowance(source, server, tmp_path):
    server.default_reply = responder(limited_model=PRO)
    result, report = _invoke("--vault", str(source), "--profiles", "chatgpt,chatgpt_pro",
                             "--output", str(tmp_path / "reports"), "--no-generation")
    assert result.exit_code == 0, result.stdout
    fast, pro = report["results"]
    assert fast["summary"]["valid"] == 4 and fast["stopped"] is None
    assert pro["stopped"] == "ChatGPTPlanUsageExhausted"
    assert pro["summary"]["allowance_errors"] == 1 and pro["summary"]["calls"] == 1
    assert pro["summary"]["physical_requests"] == 1  # the failed request; nothing after the pause
    assert pro["grading"]["att_06_svd_fail"]["error"] == "not_run: ChatGPTPlanUsageExhausted"
    first = pro["grading"]["att_03_svd_pass"]
    assert first["error"] == "ChatGPTPlanUsageExhausted" and "chatgpt.com/settings/usage" in first["detail"]
    assert pro["allowance_before"]["state"] == "ready"
    assert pro["allowance_after"]["state"] == "usage_exhausted"
    assert pro["allowance_after"]["usage_limit_code"] == "subscription_sharing_usage_limit_exceeded"
    assert report["agreement"][0]["grading"]["compared"] == 0


def test_a_working_vault_is_refused(source, server):
    database = VaultPaths(source, load_vault(source).config).sqlite_path
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    subprocess.run(["git", "-C", str(source), "add", "-f", str(database.relative_to(source))], check=True)
    result, payload = _invoke("--vault", str(source), "--profiles", "chatgpt", "--dry-run")
    assert result.exit_code == 1
    assert payload["error"] == "working_vault" and "--copy-from" in payload["message"]
    assert server.requests == []


def test_the_working_vault_check_fails_closed(source, server, monkeypatch):
    from learnloop.cli import ai_compare

    loaded = load_vault(source)

    def answering(returncode: int, stderr: str = ""):
        return lambda args, **_kwargs: subprocess.CompletedProcess(args, returncode, "", stderr)

    def timing_out(args, **_kwargs):
        raise subprocess.TimeoutExpired(args, 20)

    # Only git's "untracked" and "not a git repository" let a vault through.
    monkeypatch.setattr(ai_compare.subprocess, "run", answering(1, "error: pathspec did not match"))
    assert ai_compare.tracked_database_reason(loaded) is None
    monkeypatch.setattr(ai_compare.subprocess, "run", answering(128, "fatal: not a git repository (or any parent)"))
    assert ai_compare.tracked_database_reason(loaded) is None
    # A check that cannot finish refuses, and the command refuses before opening the database.
    for run in (timing_out, answering(128, "fatal: detected dubious ownership in repository")):
        monkeypatch.setattr(ai_compare.subprocess, "run", run)
        assert "treated as a working vault" in ai_compare.tracked_database_reason(loaded)
        result, payload = _invoke("--vault", str(source), "--profiles", "chatgpt", "--dry-run")
        assert result.exit_code == 1 and payload["error"] == "working_vault"
    assert server.requests == []


@pytest.mark.parametrize(("profiles", "code"), [("openrouter", "metered_profile"), ("nope", "unknown_profile"),
                                                ("openrouter_embedding", "not_generation")])
def test_metered_unknown_and_non_generation_profiles_are_refused(source, profiles, code):
    result, payload = _invoke("--vault", str(source), "--profiles", profiles, "--dry-run")
    assert result.exit_code == 1 and payload["error"] == code


def test_a_dry_run_may_make_the_copy_and_copy_from_needs_a_new_directory(source, server, tmp_path):
    database = VaultPaths(source, load_vault(source).config).sqlite_path
    before = _digest(database)
    result, payload = _invoke("--copy-from", str(source), "--vault", str(tmp_path / "new"), "--profiles", "chatgpt",
                              "--dry-run")
    assert result.exit_code == 0 and payload["dry_run"] is True and payload["copied"]
    assert (tmp_path / "new" / "learnloop.toml").exists() and server.requests == []
    assert _digest(database) == before
    result, payload = _invoke("--copy-from", str(source), "--vault", str(tmp_path / "new"), "--profiles", "chatgpt")
    assert result.exit_code == 1 and payload["error"] == "copy_destination_exists"
    result, payload = _invoke("--copy-from", str(source), "--vault", str(source / "inner"), "--profiles", "chatgpt")
    assert result.exit_code == 1 and payload["error"] == "copy_inside_source"


def test_a_failed_diagnosis_keeps_its_reason_in_the_report(source, server, tmp_path):
    server.default_reply = responder(no_tools_model=PRO)
    result, report = _invoke("--vault", str(source), "--profiles", "chatgpt,chatgpt_pro", "--attempts", "1",
                             "--no-generation", "--output", str(tmp_path / "reports"))
    assert result.exit_code == 0, result.stdout
    fast, pro = report["results"]
    assert fast["diagnosis"]["valid"] is True
    diagnosis = pro["diagnosis"]
    assert (diagnosis["status"], diagnosis["error"]) == ("failed", "ChatGPTPlanRequestRejected")
    assert 'workspace_mode = "inline"' in diagnosis["detail"] and len(diagnosis["detail"]) <= 500
    assert report["agreement"][0]["diagnosis"]["both_valid"] is False


def test_the_meter_counts_only_requests_that_were_sent():
    from learnloop.cli.ai_compare import _Meter

    refused = _Meter()  # the operation's own receipt only, no usage: nothing was sent
    refused("start", {"id": "root", "parent_call_id": None})
    refused("finish", {"id": "root", "status": "failed"})
    assert refused.summary()["physical_requests"] == 0
    reported = _Meter()  # a transport that reports usage on the operation itself
    reported("start", {"id": "root", "parent_call_id": None})
    reported("finish", {"id": "root", "status": "completed", "input_tokens": 10, "output_tokens": 2})
    assert (reported.summary()["physical_requests"], reported.summary()["input_tokens"]) == (1, 10)
