"""`learnloop ai compare` against a fake Responses SSE server (two ChatGPT-plan profiles).

The comparison grades, diagnoses (snapshot, served workspace) and generates on
each profile and reports agreement, validity, latency, tokens and plan
allowance. Covered: the dry run sends nothing and estimates every call, a run
on a --copy-from copy leaves the original untouched and its receipts and
verdicts (judgment_ledger, never serving state) in the copy, agreement is
computed per pair, a usage limit stops that profile, and working vaults,
metered and unknown profiles are refused. Codex review fixes (2026-10-15):
F1 a relocated or non-``.sqlite`` database is copied and relocated, F2 the
tutor's own draft validator, F3 failures as codes (no provider prose), F4 the
frozen assessment contract, F5 comparison judgments, F6 subscription spend
accounting. No test leaves 127.0.0.1.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import json
import os
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
from tests.split_live_helpers import submit

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


def _criterion(ids, *, status="item_local", facets=()):
    return {"description": "Names the transpose.", "source_criterion_ids": list(ids),
            "measurement_status": status, "facet_ids": list(facets)}


def _author(body: dict, variant: str = "valid") -> str:
    """A teach-back authoring draft: valid under the tutor's own rules, or one way invalid."""

    context = prompt_payload(body["input"][0]["content"])["context"]
    ids = [criterion["id"] for criterion in context["source_criteria"]]
    facets = [facet["id"] for facet in context["allowed_facets"]]
    core = [_criterion(ids)]
    transfer: dict | None = _criterion(ids[:1])
    scenario = "Change one assumption and say which steps survive."
    if variant == "no_transfer":  # the shape the first fake returned (Codex review F2)
        core, transfer, scenario = [_criterion(ids[:1], status="direct", facets=facets[:1])], None, ""
    elif variant == "incomplete_coverage":  # every source criterion but the first
        core = [_criterion(ids[1:])]
    elif variant == "duplicate_coverage":
        core = [_criterion(ids), _criterion(ids[:1])]
    elif variant == "invented_facet":
        core = [_criterion(ids, status="direct", facets=["not_a_facet"])]
    elif variant == "item_local_with_facets":
        core = [_criterion(ids, status="item_local", facets=facets[:1])]
    return json.dumps({
        "prompt_md": "Explain why the SVD's last factor is transposed.",
        "expected_answer_md": "Because A = U Sigma V^T maps through V^T first.",
        "core_criteria": core, "transfer_criterion": transfer, "transfer_scenario": scenario,
        "quest_connection": "no_quest", "trace_contract": None,
    })


def refusal_events(refusal: str, *, model: str) -> list[dict]:
    """A completed response whose only output is a refusal (no text)."""

    response = {"id": "resp_refusal", "object": "response", "status": "in_progress", "model": model}
    return [{"type": "response.created", "response": response}, {"type": "response.completed", "response": {
        **response, "status": "completed", "usage": {"input_tokens": 90, "output_tokens": 12},
        "output": [{"type": "message", "role": "assistant", "content": [{"type": "refusal", "refusal": refusal}]}],
    }}]


def responder(*, limited_model: str | None = None, no_tools_model: str | None = None, author: str = "valid",
              refusing_model: str | None = None, quoting_400_model: str | None = None):
    """The fake models: grade, diagnose by reading the served export, author.

    ``refusing_model`` refuses to grade, quoting the learner's answer;
    ``quoting_400_model``'s route rejects a grading request with a message
    that quotes it (Codex review F3: neither may reach the report).
    """

    def reply(body: dict) -> Reply:
        content = body["input"][0]["content"]
        if content.startswith("learnloop blind grading proposal") and body["model"] in (refusing_model,
                                                                                        quoting_400_model):
            answer = prompt_payload(content)["context"]["learner_answer_md"]
            if body["model"] == refusing_model:
                return Reply(events=refusal_events(f"I will not grade '{answer}' (SENTINEL-REFUSAL)",
                                                   model=body["model"]))
            return Reply(status=400, body={"error": {
                "code": "invalid_request_error", "param": "input",
                "message": f"Invalid input near '{answer}' (SENTINEL-400)"}})
        if body["model"] == limited_model:
            return Reply(events=failed_events("subscription_sharing_usage_limit_exceeded"))
        if body["model"] == no_tools_model and "tools" in body:
            return Reply(status=400, body={"error": {"code": "subscription_sharing_unsupported_capability",
                                                     "message": "tools unsupported", "param": "tools"}})
        if content.startswith("learnloop blind grading proposal"):
            return Reply(events=completed_events(_grade(body), model=body["model"]))
        if content.startswith("learnloop diagnosis proposal"):
            return Reply(events=_diagnose(body))
        if content.startswith("learnloop source-item teach-back authoring"):
            return Reply(events=completed_events(_author(body, author), model=body["model"]))
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


def _rows(database: Path, query: str, *args) -> list[tuple]:
    with closing(sqlite3.connect(database)) as connection:
        return connection.execute(query, args).fetchall()


#: What the comparison may write: receipts and its own verdicts. Everything
#: else is serving state (Codex review F5: isolation).
_COMPARISON_TABLES = frozenset({"model_call_receipts", "judgment_ledger"})


def _serving_state(database: Path) -> dict[str, list[tuple]]:
    with closing(sqlite3.connect(database)) as connection:
        tables = [name for (name,) in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        return {table: sorted(connection.execute(f'SELECT * FROM "{table}"').fetchall(), key=repr)
                for table in tables if table not in _COMPARISON_TABLES}


def _set_storage(root: Path, sqlite_path: str) -> None:
    path = root / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    if "storage" not in document:
        document["storage"] = tomlkit.table()
    document["storage"]["sqlite_path"] = sqlite_path
    path.write_text(tomlkit.dumps(document), encoding="utf-8")


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
    # Codex review F6: every planned call is estimated, input and output.
    estimate = payload["estimate"]
    assert estimate["estimated_usd"] is None and estimate["estimated_total_tokens"] > 0
    for name in ("chatgpt", "chatgpt_pro"):
        profile = estimate["profiles"][name]
        assert (profile["billing"], profile["cost_basis"], profile["physical_request_bound"]) == \
            ("subscription", "estimated_only", False)
        assert profile["calls"] == 5 and profile["estimated_usd"] is None
        assert profile["caps"]["max_calls"] == 5 and profile["caps"]["cost_basis"] == "estimated_only"
        assert [planned["kind"] for planned in profile["planned"]] == ["grading"] * 3 + ["diagnosis", "generation"]
        for planned in profile["planned"]:
            assert planned["input_tokens"] > 0 and planned["output_tokens"] > 0, planned
            assert planned["total_tokens"] >= planned["input_tokens"] + planned["output_tokens"]
        diagnosis = profile["planned"][3]
        assert diagnosis["workspace_tokens"] > 0  # the snapshot export the diagnoser may read
        assert profile["estimated_total_tokens"] == sum(planned["total_tokens"] for planned in profile["planned"])
    assert server.requests == []


def test_the_text_dry_run_prints_the_estimate(source, server):
    result = CliRunner().invoke(app, ["ai", "compare", "--vault", str(source), "--profiles", "chatgpt",
                                      "--dry-run"], catch_exceptions=False)
    assert result.exit_code == 0, result.stdout
    assert "estimate (subscription: estimated_only" in result.stdout
    assert "chatgpt: 5 calls, ~" in result.stdout and "snapshot export ~" in result.stdout
    assert "generation pi_svd_compute_002: ~" in result.stdout
    assert server.requests == []


def test_a_generation_only_dry_run_estimates_its_one_call(source, server):
    result, payload = _invoke("--vault", str(source), "--profiles", "chatgpt", "--attempts", "0",
                              "--no-diagnosis", "--dry-run")
    assert result.exit_code == 0, result.stdout
    [planned] = payload["estimate"]["profiles"]["chatgpt"]["planned"]
    assert planned["kind"] == "generation" and planned["input_tokens"] > 0 and planned["output_tokens"] > 0
    assert payload["estimate"]["profiles"]["chatgpt"]["estimated_total_tokens"] == planned["total_tokens"]


def test_a_run_on_a_copy_reports_agreement_validity_latency_tokens_and_allowance(source, server, tmp_path):
    server.default_reply = responder()
    database = VaultPaths(source, load_vault(source).config).sqlite_path
    before = _digest(database)
    serving = _serving_state(database)
    copy = tmp_path / "copies" / "compare"
    reports = tmp_path / "reports"
    result, report = _invoke("--copy-from", str(source), "--vault", str(copy), "--profiles", "chatgpt",
                             "--profiles", "chatgpt_pro", "--output", str(reports))
    assert result.exit_code == 0, result.stdout
    assert Path(report["report_path"]).parent == reports
    assert json.loads(Path(report["report_path"]).read_text())["agreement"] == report["agreement"]
    assert report["copied"] and report["calls_made"] == 10 and report["run_id"]
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
        assert row["generation"]["valid"] and "rejection" not in row["generation"]
        assert row["allowance_before"]["state"] == row["allowance_after"]["state"] == "ready"
        assert row["grading"]["att_03_svd_pass"]["physical_requests"] == 1
        # Codex review F6: each call admitted by the profile's subscription
        # budget and reconciled with the reported usage.
        spend = row["spend"]
        assert (spend["billing"], spend["cost_basis"], spend["physical_request_bound"]) == \
            ("subscription", "estimated_only", False)
        assert spend["used"]["calls"] == 5 and spend["caps"]["max_calls"] == 5
        assert spend["reported_total_tokens"] == summary["input_tokens"] + summary["output_tokens"]
        for call in [*row["grading"].values(), row["diagnosis"], row["generation"]]:
            assert call["spend"]["cost_basis"] == "estimated_only"
            assert call["spend"]["estimated_token_source"] == "reported_usage"
            assert call["spend"]["estimated_total_tokens"] == call["input_tokens"] + call["output_tokens"]
            assert call["spend"]["planned_total_tokens"] > 0 and call["receipt_ids"]
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
    rows = _rows(copied, "SELECT provider, purpose, status FROM model_call_receipts WHERE purpose = 'responses_request'")
    assert {provider for provider, _purpose, _status in rows} == {"chatgpt", "chatgpt_pro"}
    assert len(rows) == 2 * (3 + 3 + 1)
    assert _rows(database, "SELECT COUNT(*) FROM model_call_receipts") == [(0,)]
    # F6: every operation's root receipt records the caps in force and what it was.
    roots = _rows(copied, "SELECT id, budget_json FROM model_call_receipts WHERE parent_call_id IS NULL")
    assert len(roots) == 10
    for _id, budget_json in roots:
        declared = json.loads(budget_json)
        assert (declared["billing"], declared["cost_basis"], declared["physical_request_bound"]) == \
            ("subscription", "estimated_only", False)
        assert declared["ai_compare"]["run_id"] == report["run_id"]
        assert declared["ai_compare"]["planned_total_tokens"] > 0
    linked = {call_id for row in report["results"]
              for call in [*row["grading"].values(), row["diagnosis"], row["generation"]]
              for call_id in call["receipt_ids"]}
    assert linked == {call_id for call_id, _budget in roots}

    # F5: every verdict is in the copy's judgment_ledger under the comparison's
    # own tasks, linked from the report; none in the original; serving state untouched.
    judgments = {row[0]: row[1:] for row in _rows(
        copied, "SELECT id, task, left_kind, left_id, right_kind, right_id, judge, judge_model, prompt_version, "
                "input_hash, verdict, rationale FROM judgment_ledger WHERE task LIKE 'ai_compare_%'")}
    assert len(judgments) == 10
    for row in report["results"]:
        for attempt_id, call in row["grading"].items():
            (task, left_kind, left_id, right_kind, right_id, judge, model, version, input_hash, verdict,
             rationale) = judgments[call["judgment_id"]]
            assert (task, left_kind, left_id, right_kind, right_id, judge) == (
                "ai_compare_grading", "attempt", attempt_id, "ai_profile", row["provider"], "llm")
            assert model == row["model"] and version and input_hash
            assert json.loads(verdict)["rubric_score"] == call["rubric_score"]
            assert json.loads(rationale) == {"authority": "none", "compare_run_id": report["run_id"],
                                             "compare_version": 2}
        task, _kind, left_id, _rk, right_id, judge, *_rest = judgments[row["diagnosis"]["judgment_id"]]
        assert (task, left_id, right_id, judge) == ("ai_compare_diagnosis", "att_07_svd_future", row["provider"],
                                                    "diagnoser")
        task, kind, left_id, *_rest = judgments[row["generation"]["judgment_id"]]
        assert (task, kind, left_id) == ("ai_compare_generation", "practice_item", "pi_svd_compute_002")
    assert _rows(database, "SELECT COUNT(*) FROM judgment_ledger") == [(0,)]
    assert _serving_state(copied) == serving


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
    assert first["error"] == "ChatGPTPlanUsageExhausted" and "chatgpt.com/settings/usage" in first["failure"]["hint"]
    assert first["failure"]["code"] == "subscription_sharing_usage_limit_exceeded"
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


def test_without_git_only_a_fresh_copy_is_compared(source, server, tmp_path, monkeypatch):
    """No git to ask: a vault of unknown standing is treated as a working vault
    (the check fails closed); the copy --copy-from just made is the exception."""

    from learnloop.cli import ai_compare

    monkeypatch.setattr(ai_compare.shutil, "which", lambda _name: None)
    assert "git is not available" in ai_compare.tracked_database_reason(load_vault(source))
    result, payload = _invoke("--vault", str(source), "--profiles", "chatgpt", "--dry-run")
    assert result.exit_code == 1 and payload["error"] == "working_vault"
    result, payload = _invoke("--copy-from", str(source), "--vault", str(tmp_path / "fresh"), "--profiles", "chatgpt",
                              "--dry-run")
    assert result.exit_code == 0 and payload["copied"], result.stdout
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
    failure = diagnosis["failure"]
    assert (failure["code"], failure["http_status"], failure["param"]) == (
        "subscription_sharing_unsupported_capability", 400, "tools")
    assert 'workspace_mode = "inline" on [ai.providers.chatgpt_pro]' in failure["hint"]
    assert "tools unsupported" not in json.dumps(report)  # the provider's own message stays out
    assert "judgment_id" not in diagnosis  # no verdict, no judgment
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


# -- Codex review F1: the configured database, wherever it is ----------------------------------


@pytest.mark.parametrize("layout", ["absolute", "parent"])
def test_copy_from_relocates_a_database_configured_outside_the_vault(source, server, tmp_path, layout):
    """``storage.sqlite_path`` outside the vault (absolute, or ``..``): the copy
    gets a backup of that database and names its own; the original database
    is never opened for writing, migrated or given a receipt."""

    database = VaultPaths(source, load_vault(source).config).sqlite_path
    shared = tmp_path / "shared"
    shared.mkdir()
    external = shared / "learner.db"
    database.rename(external)
    _set_storage(source, str(external) if layout == "absolute" else os.path.relpath(external, source))
    assert VaultPaths(source, load_vault(source).config).sqlite_path.resolve() == external
    before = _digest(external)
    copy = tmp_path / "copies" / "relocated"
    result, payload = _invoke("--copy-from", str(source), "--vault", str(copy), "--profiles", "chatgpt", "--dry-run")
    assert result.exit_code == 0, result.stdout
    config = load_vault(copy).config
    assert config.storage.sqlite_path == "learner.db"
    assert payload["copied"] == [str(copy / "learner.db")]
    server.default_reply = responder()
    result, report = _invoke("--vault", str(copy), "--profiles", "chatgpt", "--attempts", "1", "--no-diagnosis",
                             "--no-generation", "--output", str(tmp_path / "reports"))
    assert result.exit_code == 0, result.stdout
    assert report["results"][0]["summary"]["valid"] == 1
    assert _digest(external) == before
    assert _rows(external, "SELECT COUNT(*) FROM model_call_receipts") == [(0,)]
    assert _rows(copy / "learner.db", "SELECT COUNT(*) FROM model_call_receipts")[0][0] > 0


def test_copy_from_backs_up_a_wal_database_not_named_sqlite(source, tmp_path):
    """A database named ``state.db`` with commits still in its ``-wal``: copied
    through the backup API (one consistent snapshot), never byte-copied with
    its companions."""

    from learnloop.cli.ai_compare import copy_vault

    database = VaultPaths(source, load_vault(source).config).sqlite_path
    renamed = database.with_name("state.db")
    database.rename(renamed)
    _set_storage(source, "state.db")
    writer = sqlite3.connect(renamed)
    try:
        assert writer.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
        writer.execute("PRAGMA wal_autocheckpoint=0")
        writer.execute("CREATE TABLE compare_wal_probe(value TEXT)")
        writer.execute("INSERT INTO compare_wal_probe VALUES ('committed')")
        writer.commit()
        assert (source / "state.db-wal").stat().st_size > 0
        copy = tmp_path / "copies" / "wal"
        copied = copy_vault(source, copy)
    finally:
        writer.close()
    assert copied == [copy / "state.db"]
    assert not (copy / "state.db-wal").exists() and not (copy / "state.db-shm").exists()
    assert _rows(copy / "state.db", "SELECT value FROM compare_wal_probe") == [("committed",)]
    assert load_vault(copy).config.storage.sqlite_path == "state.db"


def test_a_vault_whose_database_lies_outside_it_is_refused(source, server, tmp_path):
    database = VaultPaths(source, load_vault(source).config).sqlite_path
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    database.rename(elsewhere / "state.sqlite")
    _set_storage(source, str(elsewhere / "state.sqlite"))
    before = _digest(elsewhere / "state.sqlite")
    result, payload = _invoke("--vault", str(source), "--profiles", "chatgpt", "--dry-run")
    assert result.exit_code == 1 and payload["error"] == "database_outside_vault"
    assert "--copy-from" in payload["message"]
    assert _digest(elsewhere / "state.sqlite") == before and server.requests == []


# -- Codex review F2: generation validity is the tutor's own ------------------------------------


@pytest.mark.parametrize("variant", ["no_transfer", "incomplete_coverage", "duplicate_coverage", "invented_facet",
                                     "item_local_with_facets"])
def test_a_draft_the_tutor_would_reject_is_invalid(source, server, tmp_path, variant):
    server.default_reply = responder(author=variant)
    result, report = _invoke("--vault", str(source), "--profiles", "chatgpt", "--attempts", "0", "--no-diagnosis",
                             "--output", str(tmp_path / "reports"))
    assert result.exit_code == 0, result.stdout
    generation = report["results"][0]["generation"]
    assert (generation["parsed"], generation["valid"], generation["error"]) == (True, False, "TeachBackError")
    assert generation["rejection"] and generation["failure"]["hint"].startswith("The draft failed the tutor's")
    verdicts = _rows(VaultPaths(source, load_vault(source).config).sqlite_path,
                     "SELECT verdict FROM judgment_ledger WHERE id = ?", generation["judgment_id"])
    assert json.loads(verdicts[0][0])["valid"] is False


# -- Codex review F3: failures as codes, never the provider's prose ---------------------------


def test_refusals_and_rejections_quoting_the_learner_never_reach_the_report(source, server, tmp_path):
    server.default_reply = responder(refusing_model=FAST, quoting_400_model=PRO)
    reports = tmp_path / "reports"
    args = ["--vault", str(source), "--profiles", "chatgpt,chatgpt_pro", "--attempt", "att_06_svd_fail",
            "--no-diagnosis", "--no-generation", "--output", str(reports)]
    result, report = _invoke(*args)
    assert result.exit_code == 0, result.stdout
    fast, pro = (row["grading"]["att_06_svd_fail"] for row in report["results"])
    assert fast["error"] == "AIInvalidOutput" and fast["failure"]["hint"].startswith("The model refused")
    assert pro["error"] == "ChatGPTPlanRequestRejected"
    assert (pro["failure"]["code"], pro["failure"]["http_status"], pro["failure"]["param"]) == (
        "invalid_request_error", 400, "input")
    text = CliRunner().invoke(app, ["ai", "compare", *args], catch_exceptions=False)
    assert text.exit_code == 0, text.stdout
    written = [path.read_text(encoding="utf-8") for path in reports.glob("*.json")]
    assert len(written) == 2
    for output in (result.stdout, text.stdout, text.stderr, *written):
        assert "U Sigma V again" not in output and "SENTINEL" not in output


# -- Codex review F4: the frozen assessment contract -----------------------------------------


def test_grading_reads_the_contract_the_answer_was_graded_under(tmp_path):
    """A method-explicit answer, then the item's statement and method
    criterion edited: the comparison grades (and estimates) the statement,
    rubric and method the answer was graded under, as production regrading
    does, never today's item."""

    from learnloop.attempts.blind_grading import blind_grading_prompt
    from learnloop.cli import ai_compare
    from learnloop.diagnosis.split.live import live_history_store
    from tests.test_required_method_grading import ITEM, METHOD, _edit_item, _method_vault
    from tests.test_route_rules_in_grader import ALTERNATIVE, DivergentGrader

    paths, vault, repository = _method_vault(tmp_path)
    presented = vault.practice_items[ITEM].prompt
    result = submit(vault, repository, DivergentGrader(), item_id=ITEM, answer=ALTERNATIVE)
    _edit_item(paths, prompt="Write the SVD of A. Use row reduction in your answer.",
               setup_description="Edited after the answer.")
    vault = load_vault(paths.root)
    attempt = live_history_store(vault, repository).attempt(result.attempt_id)
    grader = DivergentGrader()
    record = ai_compare._grade(vault, repository, grader, attempt)
    assert record["parsed"]
    [prompt] = grader.prompts
    assert presented in prompt and "row reduction" not in prompt and "Edited after the answer." not in prompt
    assert f"Use {METHOD} in your answer." in prompt
    # The dry-run estimate reads exactly the prompt the call sends.
    _item, _rubric, context = ai_compare._grading_context(vault, repository, attempt)
    assert blind_grading_prompt(context) == prompt
