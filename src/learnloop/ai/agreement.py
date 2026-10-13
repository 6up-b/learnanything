"""``learnloop decider agreement``: the Decider against the LLM on real pairs; never a model call.

The evidence for a later Tier-2 migration (owner, 2026-10-13). It reads
``judgment_ledger`` rows only, and makes no shadow call (the owner rules out
shadow stages): it reports what the ordinary course already produced.

* A **pair** is one input (one task, the same two entities in either order and
  the same input hash) that both the Decider and an LLM-family judge (``llm``
  or ``diagnoser``) answered: learner-text gaps before mvp-0.20, where the
  Decider was a logged second opinion; the context model's gap kind beside
  the Decider's; an LLM fallback beside the Decider's failure row; an LLM
  batch that answered every link of a review target after the Decider failed
  one (a review run's ``same_cause`` links). T1's own same-cause judge
  (recurrence live, backlog, guard, ``embeddings adjudicate``) asks only the
  LLM, so it adds no pair. The latest answer of each judge counts, never the
  product of retries.
* A **fallback** is a Decider row holding no answer (``unavailable``,
  ``refused``, ``failed``, or ``tied`` top options) whose input an LLM-family
  judge then answered.
* A **label** is an owner or verifier verdict: bound to a Decider row by an
  explicit ``label_for`` (the span-support card's confirm, keep or undo) or a
  ``supersedes_id`` chain, else by the same input, else by the same question
  (the task and its two entities), except for a task whose entities do not
  name what was judged (:data:`UNNAMED_CONTENT_TASKS`: one facet's checks of
  different wordings, one learning object's different statements), where a
  label binds only explicitly or by the same input (review F3).
  Calibration (the multiclass Brier score and top-probability bins) is
  computed only where the Decider's full distribution and an option-valued
  label exist; with no such label it is ``null``, never zero.

Rows are counted once by id: a review run's scratch ledger is a backup copy
of the vault database, so it repeats every vault row (review F4).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
import json
import math
import re
from typing import Any

#: A Decider row's verdict when it holds no answer (``decider_judgments.FAILURE_VERDICTS``).
FAILURES = frozenset({"unavailable", "refused", "failed", "tied"})
LLM_JUDGES = frozenset({"llm", "diagnoser"})
LABEL_JUDGES = frozenset({"owner", "verifier"})
#: Tasks whose ledger entities do not identify the judged content: a facet's
#: span-support checks (``facet:<id>``, whatever the wording) and a learning
#: object's misconception matches (whatever the statement). A label binds to
#: one of their rows only explicitly or on the same input hash.
UNNAMED_CONTENT_TASKS = frozenset({"facet_span_support", "misconception_match"})
_TEXT_PROBABILITIES = re.compile(r"([^,]+?) ([01](?:\.\d+)?)(?:,|$)")


def _metadata(row: Mapping[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(row.get("rationale") or "{}")
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def probabilities(row: Mapping[str, Any]) -> dict[str, float]:
    """A Decider row's option distribution, or ``{}`` when it holds none that sums to about 1."""

    found = _metadata(row).get("probabilities")
    if not found:
        # T1 / text-gap executors render it: "... probabilities: same 0.800, different 0.150, ..."
        tail = str(row.get("rationale") or "").split("probabilities: ", 1)
        if len(tail) == 2:
            found = {key.strip(): float(value) for key, value in _TEXT_PROBABILITIES.findall(tail[1])}
    if not isinstance(found, dict) or not found:
        return {}
    values = list(found.values())
    if any(isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1
           for p in values) or abs(sum(values) - 1) > 0.02:
        return {}
    return {str(option): float(value) for option, value in found.items()}


def _endpoints(row: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    ends = [(str(row["left_kind"]), str(row["left_id"]))]
    if row.get("right_kind") is not None:
        ends.append((str(row["right_kind"]), str(row["right_id"])))
    return tuple(sorted(ends))


def _new_task() -> dict[str, Any]:
    return {"decider_answers": 0, "pairs": 0, "agreements": 0, "confusion": {}, "fallbacks": 0,
            "decider_failures": {}, "labels": 0, "brier_sum": 0.0, "calibration_bins": {}}


def agreement_report(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Per-task pairs, agreement, confusion (Decider by LLM), fallbacks and labelled calibration."""

    # One row per id: the vault's ledger and a review run's copy of it repeat rows.
    by_id: dict[Any, dict[str, Any]] = {}
    for row in rows:
        by_id.setdefault(row["id"], dict(row))
    ordered = sorted(by_id.values(), key=lambda row: (str(row["created_at"]), str(row["id"])))
    inputs: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    question_labels: dict[tuple[Any, ...], dict[str, Any]] = {}
    explicit: dict[str, dict[str, Any]] = {}
    for row in ordered:
        question = (row["task"], _endpoints(row))
        inputs[(*question, row["input_hash"])].append(row)
        if row["judge"] not in LABEL_JUDGES:
            continue
        question_labels[question] = row  # the latest
        target = _metadata(row).get("label_for") or row.get("supersedes_id")
        seen: set[str] = set()
        while target in by_id and target not in seen:
            seen.add(target)
            explicit[target] = row
            target = by_id[target].get("supersedes_id")
    tasks: dict[str, dict[str, Any]] = {}
    for (task_name, ends, _input), group in inputs.items():
        deciders = [row for row in group if row["judge"] == "decider"]
        if not deciders:
            continue
        task = tasks.setdefault(task_name, _new_task())
        llms = [row for row in group if row["judge"] in LLM_JUDGES]
        for failure in (row for row in deciders if row["verdict"] in FAILURES):
            status = str(failure["verdict"])
            task["decider_failures"][status] = task["decider_failures"].get(status, 0) + 1
            task["fallbacks"] += bool(llms)
        answers = [row for row in deciders if row["verdict"] not in FAILURES]
        if not answers:
            continue
        decider = answers[-1]
        task["decider_answers"] += 1
        if llms:
            llm = llms[-1]
            task["pairs"] += 1
            task["agreements"] += decider["verdict"] == llm["verdict"]
            cell = task["confusion"].setdefault(str(decider["verdict"]), {})
            cell[str(llm["verdict"])] = cell.get(str(llm["verdict"]), 0) + 1
        group_labels = [row for row in group if row["judge"] in LABEL_JUDGES]
        label = (explicit.get(decider["id"]) or (group_labels[-1] if group_labels else None)
                 or (None if task_name in UNNAMED_CONTENT_TASKS else question_labels.get((task_name, ends))))
        distribution = probabilities(decider)
        if label is None or label["verdict"] not in distribution:
            continue
        task["labels"] += 1
        task["brier_sum"] += sum((p - (option == label["verdict"])) ** 2 for option, p in distribution.items())
        confidence = max(distribution.values())
        bucket = task["calibration_bins"].setdefault(
            f"{min(9, int(confidence * 10)) / 10:.1f}", {"count": 0, "confidence_sum": 0.0, "correct": 0})
        bucket["count"] += 1
        bucket["confidence_sum"] += confidence
        bucket["correct"] += decider["verdict"] == label["verdict"]
    for task in tasks.values():
        task["agreement"] = task["agreements"] / task["pairs"] if task["pairs"] else None
        brier_sum = task.pop("brier_sum")
        task["brier_score"] = brier_sum / task["labels"] if task["labels"] else None
        for bucket in task["calibration_bins"].values():
            bucket["mean_confidence"] = bucket.pop("confidence_sum") / bucket["count"]
            bucket["accuracy"] = bucket["correct"] / bucket["count"]
        task["calibration_bins"] = dict(sorted(task["calibration_bins"].items()))
    return {
        "tasks": dict(sorted(tasks.items())),
        "pairing": "the latest answer of each judge on one task, entity pair and input hash",
        "labels": ("owner or verifier verdicts: explicit link, else the same input, else the same question "
                   "(never the same question for " + ", ".join(sorted(UNNAMED_CONTENT_TASKS)) + ")"),
        "shadow_calls": 0,
    }


def ledger_rows(connection: Any) -> list[dict[str, Any]]:
    """Every ``judgment_ledger`` row of one database (none when it has no ledger)."""

    if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'judgment_ledger'"
    ).fetchone() is None:
        return []
    cursor = connection.execute("SELECT * FROM judgment_ledger ORDER BY created_at, id")
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor]


__all__ = ["FAILURES", "LABEL_JUDGES", "LLM_JUDGES", "UNNAMED_CONTENT_TASKS", "agreement_report", "ledger_rows",
           "probabilities"]
