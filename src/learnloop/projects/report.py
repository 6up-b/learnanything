"""The M1 probe report (spec §8.3): are the probes valid, and are they worth it?

Quality reports carry no thresholds. Every figure comes with its sample size,
and small samples are flagged rather than hidden. The report reads only the
project store; it never calls a model, git or ``state.sqlite``, and it never
renders a question that has not been served (G5).

Outcome of record: an owner adjudication when one exists, else the grade.
Accuracy is reported over graded *unassisted* answers (the measurement), with
"I looked"/"I used AI" answers and don't-know-as-zero shown alongside.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from statistics import mean, median
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.config import LearnLoopConfig
from learnloop.projects.ai_contracts import (
    CLOSED_BOOK_PROMPT_VERSION,
    PROBE_AUTHORING_PROMPT_VERSION,
    PROBE_GRADING_PROMPT_VERSION,
)
from learnloop.projects.experiment_store import STORE_SCHEMA_VERSION, ProjectStore
from learnloop.projects.redaction import SECRET_PATTERN_VERSION

SMALL_SAMPLE = 10


def _rate(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "n": denominator,
        "count": numerator,
        "rate": None if denominator == 0 else round(numerator / denominator, 4),
        "small_sample": denominator < SMALL_SAMPLE,
    }


def _mean(values: list[float]) -> dict[str, Any]:
    return {
        "n": len(values),
        "mean": None if not values else round(mean(values), 4),
        "small_sample": len(values) < SMALL_SAMPLE,
    }


def outcome_of_record(response: dict[str, Any]) -> float | None:
    if response.get("adjudicated_score") is not None:
        return float(response["adjudicated_score"])
    if response.get("grade_status") == "graded" and response.get("score") is not None:
        return float(response["score"])
    return None


def _stage(receipt: dict[str, Any]) -> str | None:
    try:
        return json.loads(receipt.get("disclosure_json") or "{}").get("stage")
    except ValueError:
        return None


def _cost_by_diff(receipts: list[dict[str, Any]], *, answer_grading: bool = False) -> dict[str, dict[str, Any]]:
    """Root-call cost per diff: generation stages, or (``answer_grading``) owner-answer grades."""

    costs: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"calls": 0, "tokens": 0, "estimated_usd": 0.0, "labels": set()}
    )
    for receipt in receipts:
        if receipt.get("parent_call_id") is not None or not receipt.get("diff_id"):
            continue
        if (_stage(receipt) == "answer_grading") != answer_grading:
            continue
        entry = costs[receipt["diff_id"]]
        entry["calls"] += 1
        children = [
            row for row in receipts
            if row.get("parent_call_id") == receipt["id"]
        ]
        source = children or [receipt]
        entry["tokens"] += sum(int(row.get("input_tokens") or 0) + int(row.get("output_tokens") or 0) for row in source)
        entry["estimated_usd"] += float(receipt.get("estimated_usd") or 0.0)
        if receipt.get("cost_label"):
            entry["labels"].add(receipt["cost_label"])
    return costs


def build_report(store: ProjectStore, config: LearnLoopConfig, *, clock: Clock | None = None) -> dict[str, Any]:
    now = utc_now_iso(clock)
    repos = store.repos()
    diffs = store.diffs()
    probes = store.all_probes()
    responses = store.responses()
    receipts = store.receipts()
    provenance = store.latest_provenance()
    probes_by_id = {probe["id"]: probe for probe in probes}
    diffs_by_id = {diff["id"]: diff for diff in diffs}

    # --- capture coverage ---------------------------------------------------------
    unattributed_all = store.unattributed(unresolved_only=False)
    unresolved = [row for row in unattributed_all if row["resolved_diff_id"] is None]
    capture = {
        "repos_enrolled": sum(repo["enabled"] for repo in repos),
        "repos_with_hook": sum(repo["hook_installed"] for repo in repos),
        "repos_with_sweep_errors": [repo["name"] for repo in repos if repo["last_sweep_error"]],
        "diffs": len(diffs),
        "by_capture_source": dict(Counter(diff["capture_source"] for diff in diffs)),
        "by_capture_timing": dict(Counter(diff["capture_timing"] for diff in diffs)),
        "by_agent": dict(Counter(diff["agent"] for diff in diffs)),
        "by_agent_source": dict(Counter(diff["agent_source"] for diff in diffs)),
        "excluded": dict(Counter(diff["excluded_reason"] for diff in diffs if diff["excluded_reason"])),
        "truncated": sum(diff["truncated"] for diff in diffs),
        "redacted_lines": sum(diff["redaction_count"] for diff in diffs),
        "unattributed_commits_seen": len(unattributed_all),
        "unattributed_unresolved": len(unresolved),
        "coverage_note": (
            "Commits from the post-commit pending list with no agent trailer are possible agent "
            "work that capture missed; mark AI-written ones with `learnloop project accept "
            "--commit <sha>`. Without the hook, missed trailer-less work is not observable."
        ),
    }

    # --- generation validity ------------------------------------------------------------
    validity = Counter(probe["validity"] for probe in probes)
    checked = [probe for probe in probes if probe["status"] in {"rejected_generic", "survivor"}]
    rejected = [probe for probe in checked if probe["status"] == "rejected_generic"]
    generated = [diff for diff in diffs if diff["probe_status"] in {"generated", "under_probed"}]
    costs = _cost_by_diff(receipts)
    generated_costs = [costs[diff["id"]] for diff in generated if diff["id"] in costs]
    grading_costs = list(_cost_by_diff(receipts, answer_grading=True).values())
    generation = {
        "diffs_by_probe_status": dict(Counter(diff["probe_status"] for diff in diffs)),
        "under_probed": sum(diff["probe_status"] == "under_probed" for diff in diffs),
        "failed": sum(diff["probe_status"] == "failed" for diff in diffs),
        "candidates": len(probes),
        "validity": dict(validity),
        "citation_resolution_failures": _rate(
            validity.get("citation_unresolved", 0) + validity.get("quote_mismatch", 0), len(probes)
        ),
        "why_without_cited_rationale": validity.get("why_uncited", 0),
        "closed_book_rejection": _rate(len(rejected), len(checked)),
        "selected": sum(probe["selected"] for probe in probes),
        "kinds_selected": dict(Counter(probe["kind"] for probe in probes if probe["selected"])),
        "rationale_labels_selected": dict(
            Counter(probe["rationale_label"] for probe in probes if probe["selected"] and probe["rationale_label"])
        ),
        "cost_per_generated_diff": {
            "n": len(generated_costs),
            "mean_calls": None if not generated_costs else round(mean(c["calls"] for c in generated_costs), 2),
            "mean_tokens": None if not generated_costs else round(mean(c["tokens"] for c in generated_costs), 1),
            "mean_estimated_usd": None if not generated_costs else round(mean(c["estimated_usd"] for c in generated_costs), 6),
            "cost_labels": sorted({label for c in generated_costs for label in c["labels"]}),
            "note": "estimated_only = Codex on the ChatGPT subscription: no marginal cost; a reference-rate estimate from reported tokens.",
        },
        "answer_grading_cost": {
            "calls": sum(c["calls"] for c in grading_costs),
            "tokens": sum(c["tokens"] for c in grading_costs),
            "estimated_usd": round(sum(c["estimated_usd"] for c in grading_costs), 6),
            "cost_labels": sorted({label for c in grading_costs for label in c["labels"]}),
        },
    }

    # --- answers -----------------------------------------------------------------------
    kinds = Counter(response["response_kind"] for response in responses)
    graded = [response for response in responses if outcome_of_record(response) is not None]
    unassisted = [r for r in graded if r["declaration"] == "unassisted"]
    assisted = [r for r in graded if r["declaration"] != "unassisted"]
    contested = [r for r in graded if r["contested"]]
    due_unanswered = len(store.due_probes(now))
    lateness_days = [r["lateness_seconds"] / 86400 for r in responses]
    with_dont_know = [outcome_of_record(r) for r in unassisted] + [
        0.0 for r in responses if r["response_kind"] == "dont_know" and r["declaration"] == "unassisted"
    ]
    answers = {
        "due_unanswered": due_unanswered,
        "responses": len(responses),
        "by_kind": dict(kinds),
        "by_declaration": dict(Counter(response["declaration"] for response in responses)),
        "grade_status": dict(Counter(response["grade_status"] for response in responses)),
        "unfair_or_ambiguous": _rate(kinds.get("unfair", 0), len(responses)),
        "contest_rate": _rate(len(contested), len(graded)),
        "accuracy_unassisted": _mean([outcome_of_record(r) for r in unassisted]),
        "accuracy_unassisted_dont_know_as_zero": _mean([value for value in with_dont_know if value is not None]),
        "accuracy_assisted": _mean([outcome_of_record(r) for r in assisted]),
        "median_lateness_days": None if not lateness_days else round(median(lateness_days), 2),
    }

    # --- by provenance (§5.3: provenance decides where probes go, never a grade) ---------
    def label_sets(response: dict[str, Any]) -> dict[str, str]:
        probe = probes_by_id.get(response["probe_id"]) or {}
        diff = diffs_by_id.get(probe.get("diff_id", "")) or {}
        tap = provenance.get(diff.get("id", ""), {})
        return {
            "agent": diff.get("agent", "unknown"),
            "capture_timing": diff.get("capture_timing", "unknown"),
            "accept_style": tap.get("accept_style", "not_reported"),
            "usage_tap": tap.get("usage_tap", "not_reported"),
        }

    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for response in responses:
        for dimension, label in label_sets(response).items():
            grouped[dimension][label].append(response)
    by_provenance = {
        dimension: {
            label: {
                "responses": len(rows),
                "accuracy_unassisted": _mean(
                    [outcome_of_record(r) for r in rows if r["declaration"] == "unassisted" and outcome_of_record(r) is not None]
                ),
                "dont_know": _rate(sum(r["response_kind"] == "dont_know" for r in rows), len(rows)),
                "skip": _rate(sum(r["response_kind"] == "skip" for r in rows), len(rows)),
            }
            for label, rows in sorted(labels.items())
        }
        for dimension, labels in sorted(grouped.items())
    }

    # Only questions already served (answered) can appear here (G5).
    unfair_examples = []
    for response in responses:
        if response["response_kind"] != "unfair":
            continue
        probe = probes_by_id.get(response["probe_id"])
        if probe is None or probe["sealed_until"] > now:
            continue
        unfair_examples.append({"probe_id": probe["id"], "kind": probe["kind"], "question": probe["question"]})

    return {
        "report": "project_understanding_m1",
        "generated_at": now,
        "manifest": {
            "store_schema_version": STORE_SCHEMA_VERSION,
            "secret_pattern_version": SECRET_PATTERN_VERSION,
            "prompt_versions": {
                "authoring": PROBE_AUTHORING_PROMPT_VERSION,
                "closed_book": CLOSED_BOOK_PROMPT_VERSION,
                "grading": PROBE_GRADING_PROMPT_VERSION,
            },
            "generator_models": sorted({probe["generator_model"] for probe in probes}),
            "closed_book_models": sorted({probe["closed_book_model"] for probe in probes if probe["closed_book_model"]}),
            "grader_models": sorted({r["grader_model"] for r in responses if r["grader_model"]}),
            "config": {
                key: getattr(config.project, key)
                for key in (
                    "probe_delay_days", "probes_per_diff", "candidates_per_diff",
                    "min_diff_lines", "context_lines", "context_token_budget",
                )
            },
            "evidence_class": "practice (never cold certification, D6)",
        },
        "capture": capture,
        "generation": generation,
        "answers": answers,
        "by_provenance": by_provenance,
        "unfair_examples": unfair_examples,
        "m2_gate_note": (
            "M2 proceeds if the probes look valid: few unfair/ambiguous taps and contests (spec §9). "
            "No numeric threshold is pre-set for M1."
        ),
    }


def render_report(report: dict[str, Any]) -> str:
    """A compact plain-text view of :func:`build_report`."""

    def pct(entry: dict[str, Any]) -> str:
        if entry.get("rate") is None:
            return f"n/a (n={entry['n']})"
        flag = " (small sample)" if entry.get("small_sample") else ""
        return f"{entry['rate'] * 100:.0f}% ({entry['count']}/{entry['n']}){flag}"

    def avg(entry: dict[str, Any]) -> str:
        if entry.get("mean") is None:
            return f"n/a (n={entry['n']})"
        flag = " (small sample)" if entry.get("small_sample") else ""
        return f"{entry['mean']:.2f} (n={entry['n']}){flag}"

    capture, generation, answers = report["capture"], report["generation"], report["answers"]
    lines = [
        "Project understanding — M1 probe report",
        f"generated {report['generated_at']}",
        "",
        "Capture",
        f"  repos enrolled: {capture['repos_enrolled']} (hook installed: {capture['repos_with_hook']})",
        f"  diffs captured: {capture['diffs']}  by source {json.dumps(capture['by_capture_source'], sort_keys=True)}",
        f"  by agent: {json.dumps(capture['by_agent'], sort_keys=True)}",
        f"  excluded: {json.dumps(capture['excluded'], sort_keys=True)}  truncated: {capture['truncated']}",
        f"  redacted lines: {capture['redacted_lines']}",
        f"  trailer-less commits awaiting a tap: {capture['unattributed_unresolved']}",
        "",
        "Probe validity",
        f"  candidates: {generation['candidates']}  selected: {generation['selected']}",
        f"  citation-resolution failures: {pct(generation['citation_resolution_failures'])}",
        f"  closed-book rejections: {pct(generation['closed_book_rejection'])}",
        f"  diffs under-probed: {generation['under_probed']}  failed: {generation['failed']}",
        f"  cost per generated diff: {json.dumps(generation['cost_per_generated_diff'], sort_keys=True)}",
        "",
        "Answers",
        f"  due and unanswered: {answers['due_unanswered']}  responses: {answers['responses']} {json.dumps(answers['by_kind'], sort_keys=True)}",
        f"  unfair/ambiguous taps: {pct(answers['unfair_or_ambiguous'])}",
        f"  contest rate: {pct(answers['contest_rate'])}",
        f"  accuracy (unassisted): {avg(answers['accuracy_unassisted'])}",
        f"  accuracy (unassisted, don't know = 0): {avg(answers['accuracy_unassisted_dont_know_as_zero'])}",
        f"  accuracy (looked / used AI): {avg(answers['accuracy_assisted'])}",
        "",
        "By provenance (decides where probes go; never changes a grade)",
    ]
    for dimension, labels in report["by_provenance"].items():
        for label, entry in labels.items():
            lines.append(
                f"  {dimension}={label}: accuracy {avg(entry['accuracy_unassisted'])}; "
                f"don't know {pct(entry['dont_know'])}; skip {pct(entry['skip'])}"
            )
    if report["unfair_examples"]:
        lines += ["", "Questions tapped unfair/ambiguous"]
        lines += [f"  [{example['kind']}] {example['question']}" for example in report["unfair_examples"]]
    lines += ["", report["m2_gate_note"]]
    return "\n".join(lines)


def build_status(
    store: ProjectStore,
    *,
    clock: Clock | None = None,
    disclosure: bool = False,
    include_diffs: bool = False,
) -> dict[str, Any]:
    """Counts per repo. Never renders a question, sealed or not (G5)."""

    now = utc_now_iso(clock)
    repos = store.repos()
    diffs = store.diffs()
    probes = store.all_probes()
    answered = {response["probe_id"] for response in store.responses()}
    selected = [probe for probe in probes if probe["selected"]]
    diff_repo = {diff["id"]: diff["repo_id"] for diff in diffs}
    rows = []
    for repo in repos:
        repo_diffs = [diff for diff in diffs if diff["repo_id"] == repo["id"]]
        repo_probes = [probe for probe in selected if diff_repo.get(probe["diff_id"]) == repo["id"]]
        sealed = [probe for probe in repo_probes if probe["sealed_until"] > now]
        due = [probe for probe in repo_probes if probe["sealed_until"] <= now and probe["id"] not in answered]
        statuses = Counter(diff["probe_status"] for diff in repo_diffs)
        rows.append(
            {
                "repo_id": repo["id"],
                "name": repo["name"],
                "path": repo["path"],
                "enabled": bool(repo["enabled"]),
                "hook_installed": bool(repo["hook_installed"]),
                "context_scope": repo["context_scope"],
                "last_swept_at": repo["last_swept_at"],
                "last_sweep_error": repo["last_sweep_error"],
                "captured": len(repo_diffs),
                "excluded": statuses.get("excluded", 0),
                "awaiting_generation": statuses.get("pending", 0),
                "generated": statuses.get("generated", 0),
                "under_probed": statuses.get("under_probed", 0),
                "generation_failed": statuses.get("failed", 0),
                "probes_sealed": len(sealed),
                "next_due_at": min((probe["sealed_until"] for probe in sealed), default=None),
                "probes_due": len(due),
                "probes_answered": sum(probe["id"] in answered for probe in repo_probes),
            }
        )
    status: dict[str, Any] = {
        "generated_at": now,
        "repos": rows,
        "pending_grades": len(store.responses(grade_status="pending")),
        "unattributed_commits": [
            {"repo_id": row["repo_id"], "sha": row["sha"], "subject": row["subject"], "committed_at": row["committed_at"]}
            for row in store.unattributed()
        ],
        "last_auto_sweep_at": store.meta("last_auto_sweep_at"),
    }
    if include_diffs:
        repo_names = {repo["id"]: repo["name"] for repo in repos}
        status["diffs"] = [
            {
                "diff_id": diff["id"],
                "repo": repo_names.get(diff["repo_id"]),
                "head_sha": diff["head_sha"],
                "snapshot_kind": diff["snapshot_kind"],
                "agent": diff["agent"],
                "agent_source": diff["agent_source"],
                "capture_source": diff["capture_source"],
                "captured_at": diff["captured_at"],
                "probe_status": diff["probe_status"],
                "excluded_reason": diff["excluded_reason"],
                "files": [entry["path"] for entry in json.loads(diff["files_json"])],
                "lines_changed": diff["lines_added"] + diff["lines_removed"],
            }
            for diff in diffs
        ]
    if disclosure:
        receipts = [row for row in store.receipts() if row["parent_call_id"] is None]
        per_repo: dict[str, dict[str, Any]] = {}
        for repo in repos:
            per_repo[repo["id"]] = {
                "name": repo["name"],
                "model_calls": 0,
                "files_sent": set(),
                "hunks_sent": 0,
                "bytes_sent": 0,
                "redacted_lines_in_captures": sum(d["redaction_count"] for d in diffs if d["repo_id"] == repo["id"]),
                "files_never_sent": Counter(),
                "context_scopes": Counter(),
                "providers": Counter(),
            }
            for diff in diffs:
                if diff["repo_id"] == repo["id"]:
                    for skipped in json.loads(diff["skipped_files_json"]):
                        per_repo[repo["id"]]["files_never_sent"][skipped["reason"]] += 1
        for receipt in receipts:
            repo_id = diff_repo.get(receipt.get("diff_id") or "")
            if repo_id not in per_repo:
                continue
            entry = per_repo[repo_id]
            record = json.loads(receipt["disclosure_json"] or "{}")
            entry["model_calls"] += 1
            entry["files_sent"].update(record.get("files_sent") or [])
            entry["hunks_sent"] += int(record.get("hunk_count") or 0)
            entry["bytes_sent"] += int(record.get("bytes_sent") or 0)
            entry["context_scopes"][record.get("context_scope") or "unknown"] += 1
            entry["providers"][f"{receipt.get('provider')}/{receipt.get('resolved_model') or receipt.get('model')}"] += 1
        status["disclosure"] = [
            {
                **{key: value for key, value in entry.items() if key not in {"files_sent", "files_never_sent", "context_scopes", "providers"}},
                "distinct_files_sent": len(entry["files_sent"]),
                "files_sent": sorted(entry["files_sent"]),
                "files_never_sent": dict(entry["files_never_sent"]),
                "context_scopes": dict(entry["context_scopes"]),
                "providers": dict(entry["providers"]),
            }
            for entry in per_repo.values()
        ]
    return status


__all__ = ["build_report", "build_status", "outcome_of_record", "render_report"]
