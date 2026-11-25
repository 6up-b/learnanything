"""Lesson-local context forecasts and the durable prompt projection (teacher v2 §4.3)."""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
import json
from statistics import mean
from typing import Any

from learnloop import provenance
from learnloop.ai.execution import tee_model_calls
from learnloop.db.stores import lessons as store
from learnloop.db.stores.model_calls import annotate_started_receipt
from learnloop.teacher import probes

VERSION = "lesson_context_summary_v1"


@dataclass(frozen=True)
class Projection:
    prefix: int = 0
    summary: dict[str, Any] | None = None
    decision: provenance.DecisionRecord | None = None

    def apply(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if self.summary is None:
            return history
        return [{"by": "code", "summary": self.summary}, *history[self.prefix:]]


def context_limit(config: Any, client: Any) -> int | None:
    provider = config.ingest.providers.get(getattr(client, "provider_name", None))
    return provider.context_tokens if provider else None


def forecast(repository: Any, lesson_id: str, client: Any, *, prefix: int, estimated_input: int,
             output_budget: int, estimate: Callable[[str], int]) -> dict[str, Any]:
    """Take one sample per physical send. A missing count or change of projection breaks a growth pair.
    ``estimate``: the request gate's input estimate of a prompt's text (``estimated_input`` is the current prompt's)."""
    provider, model = client.provider_name, getattr(client, "model", None)
    with repository.connection() as connection:
        rows = connection.execute("""
            WITH RECURSIVE sends(id, prefix, root) AS (
                SELECT id, json_extract(budget_json, '$.transcript_prefix'), id FROM model_call_receipts
                WHERE purpose='teacher_turn' AND json_extract(budget_json, '$.teacher_lesson_id')=?
                UNION ALL
                SELECT c.id, s.prefix, s.root FROM sends s JOIN model_call_receipts c ON c.parent_call_id=s.id
            )
            SELECT r.provider, r.model, s.prefix, r.input_tokens, r.output_tokens, r.id,
                   (SELECT t.input_text FROM model_call_receipts t WHERE t.id=s.root),
                   (SELECT json_extract(t.budget_json, '$.input_estimate') FROM model_call_receipts t WHERE t.id=s.root)
            FROM sends s JOIN model_call_receipts r ON r.id=s.id
            WHERE NOT EXISTS (SELECT 1 FROM model_call_receipts c WHERE c.parent_call_id=r.id)
            ORDER BY r.rowid
        """, (lesson_id,)).fetchall()

    samples: list[int] = []
    answers: list[int] = []
    previous = None
    for row in rows:
        route, name, cut, inputs, outputs, _, _text, _estimate = row
        if (route, name) != (provider, model) or inputs is None or outputs is None:
            previous = None
            continue
        answers.append(outputs)
        if previous is not None and previous[2] == cut:
            samples.append(max(0, inputs - previous[3] + outputs))
        previous = row

    # A changed prefix has a different input baseline. An unfinished send has no known baseline.
    last = previous if previous is not None and previous[2] == prefix else None
    baseline = last[3] if last else estimated_input
    if samples:
        centre, margin = mean(samples), max(samples)
        basis = "lesson_growth"
    else:
        # The last answer gets transcribed and another answer needs room. Before the first
        # measurement the current prompt already includes every known input byte.
        growth = last[4] if last else 0
        centre = growth + (last[4] if last else output_budget)
        margin = growth + max(growth, output_budget)
        basis = "output_allowance"
    # The current prompt is already rendered: its input is known before any allowance. Measured, the
    # last send's count plus the estimated growth of its prompt since (the estimator only measures the difference);
    # without the last prompt's text (withheld), the count alone. The answer needs at most what this lesson's answers
    # have needed (the output allowance before the first measured one). The last prompt's own estimate is recorded at
    # its request start (also for a nested or withheld prompt, whose text is not kept); a receipt from before that
    # with no text bounds the current input by the current estimate at least.
    if last is None:
        known, known_basis = estimated_input, "estimated"
    elif last[7] is not None:
        known, known_basis = last[3] + estimated_input - int(last[7]), "measured_plus_recorded_growth"
    elif last[6] is None:
        known, known_basis = max(last[3], estimated_input), "measured_or_current_estimate"
    else:
        known, known_basis = last[3] + estimated_input - estimate(last[6]), "measured_plus_estimated_growth"
    output_need = max(answers) if answers else output_budget
    return {"basis": basis, "provider": provenance.ref(provider), "model": provenance.ref(model),
            "last_request": last[5] if last else None, "input_baseline": baseline,
            "growth_samples": len(samples), "mean_need": centre, "uncertainty_tokens": margin - centre,
            "margin": margin, "current_input": known, "current_input_basis": known_basis,
            "output_need": output_need, "predicted_tokens": max(baseline + margin, known + output_need)}


def latest(repository: Any, lesson_id: str) -> Projection:
    with repository.connection() as conn:
        # Lessons predate decision records. Their ordinary closing receipt still reads on that schema.
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='decision_records'").fetchone():
            return Projection()
        row = conn.execute("""
            SELECT json_extract(r.budget_json, '$.transcript_prefix'), json_extract(r.budget_json, '$.context_summary')
            FROM decision_records d JOIN model_call_receipts r ON r.id=d.detail_id
            WHERE d.subject_kind='lesson' AND d.subject_id=? AND d.kind='lesson_context_compaction'
            ORDER BY d.rowid DESC LIMIT 1
        """, (provenance.ref(lesson_id),)).fetchone()
    return Projection(row[0], json.loads(row[1])) if row else Projection()


def record_requests(repository: Any, lesson_id: str, projection: Projection, input_estimate: int | None = None):
    """Publish the boundary and its decision together at receipt start, before the teacher can send.
    ``input_estimate``: the request gate's estimate of the prompt being sent, kept on its receipt so the next
    forecast measures growth from it even when the prompt's text is not kept (a nested or withheld call)."""
    owned: set[str] = set()
    pending = projection.decision
    operation = None

    def observe(action: str, event: dict[str, Any]) -> None:
        nonlocal pending, operation
        call_id = event["id"]
        if action == "finish":
            if call_id == operation:
                operation = None
            if call_id in owned:
                repository.record_model_event(action, event, owner_kind="lesson", owner_id=lesson_id)
                owned.remove(call_id)
            return
        with repository.atomic():
            conn = repository.connection()
            # Direct calls need a receipt too. A sidecar or CLI observer already owns its row.
            if not conn.execute("SELECT 1 FROM model_call_receipts WHERE id=?", (call_id,)).fetchone():
                repository.record_model_event(action, event, owner_kind="lesson", owner_id=lesson_id)
                owned.add(call_id)
            if event["purpose"] != "teacher_turn" or operation is not None:
                return
            notes = {"teacher_lesson_id": lesson_id, "transcript_prefix": projection.prefix}
            if input_estimate is not None:
                notes["input_estimate"] = int(input_estimate)
            if projection.summary is not None:
                notes["summary_version"] = projection.summary["version"]
            if pending is not None:
                notes["context_summary"] = projection.summary
                record = replace(pending, detail_id=call_id, created_at=event["started_at"])
                if provenance.write(conn, record) is None:
                    raise RuntimeError("Could not record the teacher context compaction")
            annotate_started_receipt(conn, call_id, notes)
        # A correction uses the same projection but starts its own receipt.
        operation = call_id
        pending = None

    return tee_model_calls(observe, require_start=True)


def recent_start(history: Sequence[Mapping[str, Any]]) -> int:
    """Preserve the last accepted teacher turn and everything since the one before it."""
    accepted = [i for i, part in enumerate(history) if part.get("by") == "teacher"]
    return accepted[-2] + 1 if len(accepted) >= 2 else 0


def selected(row: Mapping[str, Any], fields: Sequence[str]) -> dict[str, Any]:
    return {k: row[k] for k in fields if row.get(k) is not None}


def summarize(repository: Any, state: Any) -> dict[str, Any]:
    with repository.connection() as conn:
        # The live check cache can be a minimal serving view until the next reload.
        checks = store.checks(conn, state.lesson_id)
        episodes = store.episodes(conn, state.lesson_id) if store.episode_tables_present(conn) else []
    settled = {t["refs"].get("offer") for t in state.turns
               if t["action"] in ("topic_requested", "topic_refused", "topic_declined")}
    offers = [{"ref": f"t{t['seq']}", **t["payload"]} for t in state.turns if t["action"] == "topic_offer"
              and t["id"] not in settled and t["payload"]["status"] == "pending"]
    return {
        "version": VERSION, "plan_version": state.plans[-1]["version"] if state.plans else None,
        "landed": list(dict.fromkeys(state.landed)), "capabilities": sorted(state.capabilities),
        "checks": [selected(c, ("id", "check_ref", "node_id", "minted_item_id", "status", "attempt_id",
                                "correctness", "tap", "hedge")) for c in checks],
        "episodes": [selected(e, ("id", "kind", "node_id", "learning_object_id", "teacher_p", "repair_class",
                                  "hypothesis_count", "close_reason", "outcome_attempt_id", "recheck_attempt_id",
                                  "outcome_correctness", "generated_item_id", "gap_job_id", "created_lo_id"))
                     for e in episodes],
        "probes": [{"ref": p.ref, "node": p.node, "p": p.p, "status": p.status,
                    **selected(p.result, ("attempt_id", "correctness", "independent"))} for p in probes.probes(state.turns)],
        "forecasts": [selected(f, ("key", "node", "p", "kind")) for f in state.forecasts.values()],
        "open_topic_offers": offers,
    }


def decision(state: Any, prefix: int, summary: Mapping[str, Any], facts: Mapping[str, Any],
             limit: int, entries: int) -> provenance.DecisionRecord:
    return provenance.DecisionRecord(
        kind="lesson_context_compaction", status="chosen", subject_kind="lesson", subject_id=provenance.ref(state.lesson_id),
        decided_by="code", rule="predicted_need_at_context_limit", chosen_ref=VERSION,
        versions={"summary": VERSION}, detail_table="model_call_receipts",
        facts={**facts, "context_limit": limit, "replaced_entries": prefix,
               "verbatim_entries": entries - prefix, "plan_version": summary["plan_version"],
               "check_ids": [c["id"] for c in summary["checks"]], "episode_ids": [e["id"] for e in summary["episodes"]],
               "capabilities": [provenance.ref(c) for c in summary["capabilities"]],
               "open_check": (state.open_check or {}).get("check_ref"), "open_prediction": bool(state.open_prediction),
               "open_topic_refs": [o["ref"] for o in summary["open_topic_offers"]]},
    )
