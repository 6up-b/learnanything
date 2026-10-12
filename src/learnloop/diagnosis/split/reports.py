"""End-of-M2 report: E5, E7 and the §12.3 learner signals (Slice 1 §13).

Reads only receipts and ledgers - no model, no embedding call - and reports
aggregates only (no learner text, no statements). There are no thresholds in
this slice (O10): every rate carries a Wilson interval and its n, so the owner
reads it against the run-to-run spread at the S1.5 exit review.
"""

from __future__ import annotations

import json
import statistics
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

from learnloop.clock import parse_utc
from learnloop.db.repositories import Repository
from learnloop.diagnosis.offline_review.report import wilson
from learnloop.vault.models import LoadedVault

REPORT_VERSION = "slice1-m2-report-v1"


def _seconds(start: str | None, end: str | None) -> float | None:
    a = parse_utc(start) if start else None
    b = parse_utc(end) if end else None
    if a is None or b is None:
        return None
    return max(0.0, (b - a).total_seconds())


def _quantiles(values: Sequence[float]) -> dict[str, Any]:
    clean = sorted(value for value in values if value is not None)
    if not clean:
        return {"n": 0, "p50": None, "p95": None}

    def at(q: float) -> float:
        index = min(len(clean) - 1, max(0, int(round(q * (len(clean) - 1)))))
        return round(clean[index], 3)

    return {"n": len(clean), "p50": at(0.5), "p95": at(0.95)}


def _rows(repository: Repository, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(sql, tuple(params))]


def _e5(repository: Repository) -> dict[str, Any]:
    """Would-merge (shadow): do validated citations / kNN neighbours find
    recurrences exact strings split, and are they right when audited?"""

    logs = repository.would_merge_rows()
    top1_same: list[float] = []
    top1_other: list[float] = []
    exact_splits_nominated = 0
    pairs: set[tuple[str, str]] = set()
    for row in logs:
        neighbors = row.get("neighbors") or []
        if not neighbors:
            continue
        top = neighbors[0]
        cosine = float(top.get("cosine") or 0.0)
        (top1_same if top.get("same_exact_key") else top1_other).append(cosine)
        if not top.get("same_exact_key"):
            exact_splits_nominated += 1
        for neighbor in neighbors:
            if neighbor.get("attempt_id"):
                pairs.add((str(row["hypothesis_id"]), str(neighbor.get("hypothesis_id"))))
    verdicts = _rows(
        repository,
        "SELECT judge, verdict, left_id, right_id FROM judgment_ledger WHERE task = 'same_cause'",
    )
    by_judge: dict[str, Counter] = {}
    for row in verdicts:
        by_judge.setdefault(str(row["judge"]), Counter())[str(row["verdict"])] += 1
    learner = by_judge.get("learner_card", Counter())
    owner_or_llm = Counter()
    for judge in ("owner", "llm"):
        owner_or_llm.update(by_judge.get(judge, Counter()))
    return {
        "hypotheses_logged": len(logs),
        "with_neighbors": sum(1 for row in logs if row.get("neighbors")),
        "top1_cosine_same_exact_key": _quantiles(top1_same),
        "top1_cosine_different_exact_key": _quantiles(top1_other),
        "exact_key_splits_nominated_by_knn": exact_splits_nominated,
        "same_cause_verdicts_by_judge": {judge: dict(counter) for judge, counter in sorted(by_judge.items())},
        "audited_merge_precision": wilson(owner_or_llm.get("same", 0), owner_or_llm.get("same", 0) + owner_or_llm.get("different", 0)),
        "learner_not_same_on_cited": learner.get("different", 0),
        "note": "shadow only: no would-merge pair groups anything; T1 reads these as evaluation data",
    }


def _e7(repository: Repository) -> dict[str, Any]:
    grading_runs = _rows(
        repository,
        "SELECT started_at, completed_at, status, prompt_version FROM agent_runs "
        "WHERE purpose = 'grading' AND prompt_version LIKE 'mvp-2.%'",
    )
    diagnoses = repository.all_attempt_diagnoses()
    attempts = {
        row["id"]: row
        for row in _rows(repository, "SELECT id, created_at FROM practice_attempts")
    }
    delays = [
        _seconds(attempts.get(row["attempt_id"], {}).get("created_at"), row.get("created_at"))
        for row in diagnoses
        if row["mode"] == "live" and row["status"] == "completed"
    ]
    waits = repository.diagnosis_wait_receipts()
    jobs = repository.post_attempt_job_counts()
    # The diagnoser's receipts: one root row per logical call; a Codex root
    # carries no usage itself, its physical turns (children, including any
    # JSON-repair turn) do. Embedding calls made for a diagnosis are counted
    # with the embeddings below, not here.
    diagnosis_rows = _rows(
        repository,
        "SELECT id, parent_call_id, purpose, input_tokens, output_tokens FROM model_call_receipts "
        "WHERE owner_kind = 'attempt_diagnosis' AND purpose NOT LIKE 'embedding%'",
    )
    calls = [row for row in diagnosis_rows if row.get("parent_call_id") is None]
    children: dict[str, list[dict[str, Any]]] = {}
    for row in diagnosis_rows:
        if row.get("parent_call_id") is not None:
            children.setdefault(str(row["parent_call_id"]), []).append(row)

    def _usage(row: Mapping[str, Any]) -> int:
        own = [row] if row.get("input_tokens") is not None or row.get("output_tokens") is not None else []
        rows = own or children.get(str(row["id"]), [])
        return sum(int(item.get("input_tokens") or 0) + int(item.get("output_tokens") or 0) for item in rows)

    repair_turns = sum(
        1 for row in diagnosis_rows
        if row.get("parent_call_id") is not None
        and ("_json_repair" in str(row["purpose"]) or "_json_regenerate" in str(row["purpose"]))
    )
    embed_calls = _rows(
        repository,
        "SELECT input_tokens, cost FROM model_call_receipts WHERE purpose = 'embedding' AND parent_call_id IS NULL",
    )
    diagnosed_attempts = {row["attempt_id"] for row in diagnoses}
    diagnose_jobs = jobs.get("diagnose", {})
    total_settled = sum(diagnose_jobs.get(state, 0) for state in ("done", "failed", "skipped"))
    return {
        "blind_grade_call_seconds": _quantiles(
            [_seconds(row["started_at"], row["completed_at"]) for row in grading_runs if row["status"] == "completed"]
        ),
        "diagnosis_completion_delay_seconds": _quantiles([value for value in delays if value is not None]),
        "diagnosis_model_latency_seconds": _quantiles(
            [float(row["latency_seconds"]) for row in diagnoses if row.get("latency_seconds") is not None]
        ),
        # Population: every item SERVED after a diagnosis-bearing answer in
        # its session (one receipt per serve, written at the serve), so a
        # serve whose diagnosis had already landed counts as served with it.
        "served_without_diagnosis": wilson(
            sum(1 for row in waits if row["served_without_diagnosis"]), len(waits)
        ),
        "served_without_diagnosis_population": "serves after a diagnosis-bearing answer in the session",
        "wait_seconds": _quantiles([float(row["waited_seconds"]) for row in waits]),
        "diagnoses_by_status": dict(Counter(f"{row['mode']}:{row['status']}" for row in diagnoses)),
        "jobs": jobs,
        "diagnose_job_failure_rate": wilson(diagnose_jobs.get("failed", 0), total_settled),
        "diagnosis_calls": len(calls),
        "diagnosis_repair_turns": repair_turns,
        "diagnosis_tokens_per_attempt": (
            round(sum(_usage(row) for row in calls) / max(1, len(diagnosed_attempts)), 1)
            if calls
            else None
        ),
        "diagnosis_cost_basis": "estimated_only on subscription routes (Codex); reported elsewhere",
        "embedding_calls": len(embed_calls),
        "embedding_cost_usd": round(sum(float(row.get("cost") or 0.0) for row in embed_calls), 6),
    }


def _signals(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    feedback = repository.diagnosis_feedback_rows()
    main = [row for row in feedback if row["response"] != "not_same_mistake"]
    citations = [row for row in feedback if row["response"] == "not_same_mistake"]
    completed = [
        row for row in repository.all_attempt_diagnoses() if row["mode"] == "live" and row["status"] == "completed"
    ]
    cited_total = 0
    for row in completed:
        receipt = repository.diagnosis_context_receipt(str(row["id"])) or {}
        cited_total += len({str(c.get("attempt_id")) for c in receipt.get("validated_citations") or []})
    # Repair uptake: a primed attempt on the same item after the diagnosis.
    attempts = _rows(
        repository,
        "SELECT id, practice_item_id, created_at, primed FROM practice_attempts ORDER BY created_at, id",
    )
    by_id = {row["id"]: row for row in attempts}
    with_repairs = 0
    taken_up = 0
    for row in completed:
        proposal = row.get("proposal") or {}
        if not proposal.get("repair_suggestions"):
            continue
        with_repairs += 1
        source = by_id.get(row["attempt_id"]) or {}
        if any(
            later["practice_item_id"] == source.get("practice_item_id")
            and later["primed"]
            and str(later["created_at"]) >= str(row["created_at"])
            for later in attempts
        ):
            taken_up += 1
    blind = repository.blind_graded_attempt_ids()
    regrades = _rows(
        repository,
        "SELECT DISTINCT attempt_id FROM grading_evidence WHERE superseded_at IS NOT NULL",
    )
    regraded = {str(row["attempt_id"]) for row in regrades}
    joint_ids = set(by_id) - blind
    return {
        "card_responses": dict(Counter(row["response"] for row in main)),
        "card_response_rate": wilson(len({row["diagnosis_id"] for row in main}), len(completed)),
        "diagnosis_wrong_share": wilson(sum(1 for row in main if row["response"] == "diagnosis_wrong"), len(main)),
        "unsure_share": wilson(sum(1 for row in main if row["response"] == "unsure"), len(main)),
        "not_same_mistake_per_citation": wilson(len(citations), cited_total),
        "repair_uptake": wilson(taken_up, with_repairs),
        "regrade_rate_blind": wilson(len(regraded & blind), len(blind)),
        "regrade_rate_joint": wilson(len(regraded & joint_ids), len(joint_ids)),
        "taps_forwarded_to_factor": sum(1 for row in feedback if row.get("forwarded_factor_id")),
        "note": "taps are eval-only learner reports, never evidence (invariant 12)",
    }


def m2_report(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    from learnloop.ai.execution import content_key
    from learnloop.diagnosis.split.settings import DIAGNOSIS_PROMPT_VERSION

    config = getattr(vault.config, "diagnosis", None)
    blind = repository.blind_graded_attempt_ids()
    return {
        "report_version": REPORT_VERSION,
        "manifest": {
            "algorithm_version": vault.config.algorithms.algorithm_version,
            "diagnosis_prompt_version": DIAGNOSIS_PROMPT_VERSION,
            "history_mode": getattr(config, "history_mode", None),
            "split_enabled": getattr(config, "split_enabled", None),
            "embedding_model": vault.config.embedding.model if vault.config.embedding.enabled else None,
            "config_hash": content_key(vault.config.model_dump(mode="json")),
            "blind_graded_attempts": len(blind),
            "grading_prompt_versions": dict(
                Counter(
                    str(row["grading_prompt_version"])
                    for row in _rows(repository, "SELECT grading_prompt_version FROM blind_grade_records")
                )
            ),
        },
        "e5_recurrence_shadow": _e5(repository),
        "e7_operational": _e7(repository),
        "learner_signals": _signals(vault, repository),
        "thresholds": "none in Slice 1 (O10); compare against run-to-run spread",
    }


def _fmt(rate: Mapping[str, Any] | None) -> str:
    if not rate or rate.get("rate") is None:
        return "n/a (n=0)"
    return f"{rate['rate']:.2f} [{rate['low']:.2f}, {rate['high']:.2f}] (n={rate['n']})"


def render_markdown(report: Mapping[str, Any]) -> str:
    e5 = report["e5_recurrence_shadow"]
    e7 = report["e7_operational"]
    signals = report["learner_signals"]
    manifest = report["manifest"]
    lines = [
        "# Slice 1 M2 report (E5, E7, learner signals)",
        "",
        f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} - {report['report_version']}. "
        "Aggregates only; no learner text. No thresholds (O10).",
        "",
        "## Manifest",
        "",
        f"- algorithm {manifest['algorithm_version']}, history mode {manifest['history_mode']}, "
        f"split enabled {manifest['split_enabled']}, embedding model {manifest['embedding_model']}",
        f"- blind-graded attempts {manifest['blind_graded_attempts']}; grading prompts "
        f"{json.dumps(manifest['grading_prompt_versions'], sort_keys=True)}",
        "",
        "## E5 recurrence (shadow)",
        "",
        f"- hypotheses logged {e5['hypotheses_logged']}, with neighbours {e5['with_neighbors']}",
        f"- top-1 cosine, same exact key {e5['top1_cosine_same_exact_key']}; different key {e5['top1_cosine_different_exact_key']}",
        f"- exact-key splits nominated by kNN: {e5['exact_key_splits_nominated_by_knn']}",
        f"- audited merge precision {_fmt(e5['audited_merge_precision'])}",
        f"- same_cause verdicts by judge {json.dumps(e5['same_cause_verdicts_by_judge'], sort_keys=True)}",
        "",
        "## E7 operational",
        "",
        f"- blind grade call seconds {e7['blind_grade_call_seconds']}",
        f"- diagnosis completion delay seconds {e7['diagnosis_completion_delay_seconds']}",
        f"- served without diagnosis {_fmt(e7['served_without_diagnosis'])}; waits {e7['wait_seconds']}",
        f"- diagnoses {json.dumps(e7['diagnoses_by_status'], sort_keys=True)}; job failure rate {_fmt(e7['diagnose_job_failure_rate'])}",
        f"- diagnosis calls {e7['diagnosis_calls']} (JSON-repair turns {e7['diagnosis_repair_turns']}), "
        f"tokens per diagnosed attempt {e7['diagnosis_tokens_per_attempt']} ({e7['diagnosis_cost_basis']})",
        f"- embedding calls {e7['embedding_calls']}, cost ${e7['embedding_cost_usd']}",
        "",
        "## Learner signals (§12.3)",
        "",
        f"- card responses {json.dumps(signals['card_responses'], sort_keys=True)}; response rate {_fmt(signals['card_response_rate'])}",
        f"- 'that's wrong' share {_fmt(signals['diagnosis_wrong_share'])}; 'not sure' share {_fmt(signals['unsure_share'])}",
        f"- cited answers marked not the same mistake {_fmt(signals['not_same_mistake_per_citation'])}",
        f"- repair uptake {_fmt(signals['repair_uptake'])}",
        f"- regrades: blind {_fmt(signals['regrade_rate_blind'])} vs joint {_fmt(signals['regrade_rate_joint'])}",
        "",
    ]
    return "\n".join(lines)


__all__ = ["REPORT_VERSION", "m2_report", "render_markdown"]
