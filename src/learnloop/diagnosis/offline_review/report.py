"""The M1 report: E1-E4 and E6 from one run's scratch copy (Slice 1 §12.1, §13).

Reads only the run directory. Contains aggregates and ids, never learner text
(Slice A §5 rule 11). There are no thresholds (O10): every comparison is shown
next to its noise floor - the (b) vs (b') repeat for the diagnoser, the joint
grader vs its own repeat for grading - and the owner decides what is clearly
outside it.
"""

from __future__ import annotations

import json
import math
import statistics
from collections import Counter, defaultdict
from contextlib import closing
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from learnloop.attempts.grading import resolved_rubric
from learnloop.db.connection import connect
from learnloop.db.stores.diagnosis_review import review_rows
from learnloop.diagnosis.offline_review import judge as judging
from learnloop.diagnosis.offline_review.judge import PAIRS_OF_INTEREST, RATINGS
from learnloop.diagnosis.offline_review.runner import MAIN_ARMS, RUN_FILE, SCRATCH_FILE

REPORT_VERSION = "slice1-m1-report-v1"
ARM_LABELS = {
    "a": "(a) joint grader (stored; rerun on planted)",
    "b": "(b) exact",
    "b_prime": "(b') exact, repeat",
    "b0": "(b0) no history",
    "c": "(c) hybrid kNN",
    "d": "(d) full",
    "e": "(e) snapshot",
}


def wilson(successes: int, total: int, z: float = 1.96) -> dict[str, Any]:
    if total <= 0:
        return {"rate": None, "n": 0, "low": None, "high": None}
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return {"rate": round(p, 4), "n": total, "k": successes, "low": round(max(0.0, centre - half), 4), "high": round(min(1.0, centre + half), 4)}


def cohen_kappa(pairs: Sequence[tuple[bool, bool]]) -> float | None:
    if not pairs:
        return None
    n = len(pairs)
    observed = sum(1 for left, right in pairs if left == right) / n
    left_true = sum(1 for left, _ in pairs if left) / n
    right_true = sum(1 for _, right in pairs if right) / n
    expected = left_true * right_true + (1 - left_true) * (1 - right_true)
    if expected >= 1.0:
        return 1.0 if observed == 1.0 else None
    return round((observed - expected) / (1 - expected), 4) + 0.0


def _percentile(values: Sequence[float], q: float) -> float | None:
    values = sorted(value for value in values if value is not None)
    if not values:
        return None
    index = min(len(values) - 1, max(0, math.ceil(q * len(values)) - 1))
    return round(values[index], 3)


def _ledger(connection, task: str) -> list[dict[str, Any]]:
    cursor = connection.execute(
        "SELECT id, left_kind, left_id, right_kind, right_id, judge, judge_model, prompt_version, verdict, rationale "
        "FROM judgment_ledger WHERE task = ? ORDER BY created_at, id",
        (task,),
    )
    columns = [description[0] for description in cursor.description]
    rows = []
    for row in cursor.fetchall():
        payload = dict(zip(columns, row))
        try:
            payload["rationale"] = json.loads(payload["rationale"]) if payload["rationale"] else {}
        except ValueError:
            payload["rationale"] = {}
        rows.append(payload)
    return rows


def load_run(run_dir: Path) -> dict[str, Any]:
    run_dir = Path(run_dir)
    meta = json.loads((run_dir / RUN_FILE).read_text(encoding="utf-8"))
    run_id = meta["run_id"]
    scratch = run_dir / SCRATCH_FILE
    data: dict[str, Any] = {"meta": meta, "run_id": run_id}
    with closing(connect(scratch, read_only=True)) as connection:
        for table in (
            "review_runs",
            "review_targets",
            "review_planted_cases",
            "review_blind_grades",
            "review_diagnoses",
            "review_calls",
            "review_probes",
            "review_judgments",
        ):
            where = {"id": run_id} if table == "review_runs" else {"run_id": run_id}
            data[table] = review_rows(connection, table, where=where)
        data["review_context_receipts"] = {
            row["diagnosis_id"]: row for row in review_rows(connection, "review_context_receipts")
        }
        for task in (
            "diagnosis_rating",
            "diagnosis_pairwise",
            "diagnosis_best",
            "same_cause",
            "planted_cause_match",
        ):
            data[f"ledger:{task}"] = _ledger(connection, task)
        data["superseded_judgments"] = _keep_current_revisions(data)
        real_ids = [row["attempt_id"] for row in data["review_targets"] if row["kind"] == "real"]
        evidence: dict[str, dict[str, float]] = defaultdict(dict)
        misconceptions: dict[str, list[str | None]] = defaultdict(list)
        adjudicated: dict[str, Any] = {}
        if real_ids:
            placeholders = ",".join("?" for _ in real_ids)
            for row in connection.execute(
                f"SELECT attempt_id, criterion_id, points_awarded FROM grading_evidence "
                f"WHERE superseded_at IS NULL AND attempt_id IN ({placeholders})",
                real_ids,
            ):
                evidence[str(row[0])][str(row[1])] = float(row[2] or 0.0)
            for row in connection.execute(
                f"SELECT attempt_id, misconception_id FROM error_events WHERE attempt_id IN ({placeholders}) ORDER BY created_at, id",
                real_ids,
            ):
                misconceptions[str(row[0])].append(row[1])
            for row in connection.execute(
                f"SELECT attempt_id, adjudicated_anchor_json FROM diagnosis_adjudications "
                f"WHERE attempt_id IN ({placeholders}) AND supersedes_id IS NULL",
                real_ids,
            ):
                try:
                    adjudicated[str(row[0])] = json.loads(row[1]) if row[1] else None
                except ValueError:
                    adjudicated[str(row[0])] = None
            fatal = {
                str(row[0]): json.loads(row[1] or "[]")
                for row in connection.execute(
                    f"SELECT attempt_id, fatal_errors_json FROM attempt_feedback_metadata WHERE attempt_id IN ({placeholders})",
                    real_ids,
                )
            }
            scores = {
                str(row[0]): row[1]
                for row in connection.execute(
                    f"SELECT id, rubric_score FROM practice_attempts WHERE id IN ({placeholders})", real_ids
                )
            }
        else:
            fatal, scores = {}, {}
        data["stored_evidence"] = dict(evidence)
        data["stored_misconceptions"] = dict(misconceptions)
        data["stored_adjudicated_anchor"] = adjudicated
        data["stored_fatal"] = fatal
        data["stored_score"] = scores
    return data


def current_revisions(diagnosis_rows: Sequence[Mapping[str, Any]], targets: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, str]]:
    """Per target, the judgment revision of its CURRENT candidates (F10).

    ``diagnosis`` and ``planted`` are keyed by target id, ``links`` by the
    target's attempt id (the ``same_cause`` rows' left side).
    """

    by_target: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in diagnosis_rows:
        by_target[row["target_id"]].append(row)
    revisions: dict[str, dict[str, str]] = {"diagnosis": {}, "links": {}, "planted": {}}
    for target in targets:
        rows = by_target.get(target["id"], [])
        revisions["diagnosis"][target["id"]] = judging.diagnosis_judgment_revision(judging.judged_arm_rows(rows))
        revisions["links"][target["attempt_id"]] = judging.link_judgment_revision(judging.cited_links(rows))
        revisions["planted"][target["id"]] = judging.planted_judgment_revision(judging.planted_statements(rows))
    return revisions


def _keep_current_revisions(data: dict[str, Any]) -> dict[str, int]:
    """Drop judge rows whose inputs are no longer the target's candidates."""

    revisions = current_revisions(data["review_diagnoses"], data["review_targets"])
    target_of = {row["id"]: row["target_id"] for row in data["review_diagnoses"]}

    def keep(task: str, row: Mapping[str, Any]) -> bool:
        revision = (row.get("rationale") or {}).get("revision")
        if task in {"diagnosis_rating", "diagnosis_pairwise"}:
            return revision == revisions["diagnosis"].get(target_of.get(row["left_id"], ""))
        if task == "diagnosis_best":
            return revision == revisions["diagnosis"].get(row["left_id"])
        if task == "same_cause":
            return revision == revisions["links"].get(row["left_id"])
        if task == "planted_cause_match":
            return revision == revisions["planted"].get(target_of.get(row["left_id"], ""))
        return True

    superseded: dict[str, int] = {}
    for task in ("diagnosis_rating", "diagnosis_pairwise", "diagnosis_best", "same_cause", "planted_cause_match"):
        rows = data[f"ledger:{task}"]
        kept = [row for row in rows if keep(task, row)]
        superseded[task] = len(rows) - len(kept)
        data[f"ledger:{task}"] = kept
    return superseded


def _passes(rows: Iterable[Mapping[str, Any]]) -> dict[int, list[Mapping[str, Any]]]:
    grouped: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int((row.get("rationale") or {}).get("pass", 0))].append(row)
    return grouped


def _arm_section(data: Mapping[str, Any]) -> dict[str, Any]:
    by_arm: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in data["review_diagnoses"]:
        by_arm[row["arm"]].append(row)
    calls_by_arm: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in data["review_calls"]:
        if row["route"] == "diagnosis" and row.get("arm"):
            calls_by_arm[row["arm"]].append(row)
    receipts = data["review_context_receipts"]
    section = {}
    for arm, rows in sorted(by_arm.items()):
        statuses = Counter(row["status"] for row in rows)
        completed = [row for row in rows if row["status"] == "completed"]
        unknown = [int(row.get("unknown_id_count") or 0) for row in completed]
        tokens = [
            (receipts.get(row["id"], {}).get("retrieval") or {}).get("context_tokens")
            for row in completed
        ]
        calls = calls_by_arm.get(arm, [])
        section[arm] = {
            "label": ARM_LABELS.get(arm, arm),
            "statuses": dict(statuses),
            "errors": dict(Counter(str(row.get("error")) for row in rows if row.get("error"))),
            "unknown_id_count": {
                "total": sum(unknown),
                "mean": round(statistics.mean(unknown), 3) if unknown else None,
                "diagnoses_with_any": sum(1 for value in unknown if value),
            },
            "anchoring_suspect": wilson(sum(1 for row in completed if row.get("anchoring_suspect")), len(completed)),
            "context_tokens_mean": round(statistics.mean([value for value in tokens if value]), 1) if any(tokens) else None,
            "validated_citations": sum(
                len(receipts.get(row["id"], {}).get("validated_citations") or []) for row in completed
            ),
            "pattern_claims": sum(len((row.get("proposal") or {}).get("pattern_claims") or []) for row in completed),
            "calls": len(calls),
            "input_tokens": sum(int(row.get("input_tokens") or 0) for row in calls),
            "output_tokens": sum(int(row.get("output_tokens") or 0) for row in calls),
            "cached_input_tokens": sum(int(row.get("cached_input_tokens") or 0) for row in calls),
            "estimated_usd": (
                round(sum(float(row["estimated_usd"]) for row in calls if row.get("estimated_usd") is not None), 6)
                if any(row.get("estimated_usd") is not None for row in calls) else None
            ),
            "cost_basis": sorted({row["cost_basis"] for row in calls}),
            "latency_p50": _percentile([row.get("latency_seconds") for row in calls], 0.5),
            "latency_p95": _percentile([row.get("latency_seconds") for row in calls], 0.95),
        }
    return section


def _judge_section(data: Mapping[str, Any]) -> dict[str, Any]:
    arm_of = {row["id"]: row["arm"] for row in data["review_diagnoses"]}
    target_of = {row["id"]: row["target_id"] for row in data["review_diagnoses"]}
    kind_of = {row["id"]: row["kind"] for row in data["review_targets"]}
    ratings = data["ledger:diagnosis_rating"]
    per_arm: dict[str, dict[str, Any]] = {}
    by_key: dict[tuple[str, int], str] = {}
    for row in ratings:
        arm = arm_of.get(row["left_id"])
        if arm is None:
            continue
        pass_index = int(row["rationale"].get("pass", 0))
        by_key[(row["left_id"], pass_index)] = row["verdict"]
        bucket = per_arm.setdefault(arm, {"counts": Counter(), "real": Counter(), "planted": Counter()})
        bucket["counts"][row["verdict"]] += 1
        bucket[kind_of.get(target_of.get(row["left_id"], ""), "real")][row["verdict"]] += 1
    rating_section = {}
    for arm, bucket in sorted(per_arm.items()):
        total = sum(bucket["counts"].values())
        rating_section[arm] = {
            "label": ARM_LABELS.get(arm, arm),
            "distribution": {rating: bucket["counts"].get(rating, 0) for rating in RATINGS},
            "right": wilson(bucket["counts"].get("right", 0), total),
            "right_or_partly": wilson(bucket["counts"].get("right", 0) + bucket["counts"].get("partly", 0), total),
            "real_right": wilson(bucket["real"].get("right", 0), sum(bucket["real"].values())),
            "planted_right": wilson(bucket["planted"].get("right", 0), sum(bucket["planted"].values())),
        }
    agree = [
        by_key[(diagnosis_id, 0)] == by_key[(diagnosis_id, 1)]
        for (diagnosis_id, pass_index) in by_key
        if pass_index == 0 and (diagnosis_id, 1) in by_key
    ]
    pairwise: dict[str, Any] = {}
    pair_rows: dict[tuple[str, str], dict[int, Counter]] = defaultdict(lambda: defaultdict(Counter))
    pair_by_question: dict[tuple[str, str, str], dict[int, str]] = defaultdict(dict)
    for row in data["ledger:diagnosis_pairwise"]:
        first, second = row["rationale"].get("pair") or [arm_of.get(row["left_id"]), arm_of.get(row["right_id"])]
        pass_index = int(row["rationale"].get("pass", 0))
        verdict = {"left": first, "right": second}.get(row["verdict"], "tie")
        pair_rows[(first, second)][pass_index][verdict] += 1
        pair_by_question[(first, second, row["left_id"])][pass_index] = verdict
    for (first, second), passes in sorted(pair_rows.items()):
        combined = Counter()
        for counter in passes.values():
            combined.update(counter)
        decided = combined[first] + combined[second]
        both = [verdicts for (left, right, _), verdicts in pair_by_question.items() if (left, right) == (first, second) and len(verdicts) == 2]
        pairwise[f"{first}_vs_{second}"] = {
            "first": ARM_LABELS.get(first, first),
            "second": ARM_LABELS.get(second, second),
            "first_wins": combined[first],
            "second_wins": combined[second],
            "ties": combined["tie"],
            "first_win_share_of_decided": wilson(combined[first], decided),
            "pass_agreement": wilson(sum(1 for verdicts in both if verdicts[0] == verdicts[1]), len(both)),
        }
    best = Counter()
    best_total = 0
    for row in data["ledger:diagnosis_best"]:
        best_total += 1
        best[arm_of.get(row["verdict"], "none") if row["verdict"] != "none" else "none"] += 1
    noise = pairwise.get("b_vs_b_prime")
    return {
        "superseded_judgment_rows": dict(data.get("superseded_judgments") or {}),
        "ratings": rating_section,
        "rating_pass_agreement": wilson(sum(agree), len(agree)),
        "pairwise": pairwise,
        "best_picks": {"total": best_total, "by_arm": dict(best)},
        "noise_floor": {
            "b_vs_b_prime_decided_share": (
                wilson(noise["first_wins"] + noise["second_wins"], noise["first_wins"] + noise["second_wins"] + noise["ties"])
                if noise else None
            ),
            "note": "How often the judge prefers one of two runs of the SAME configuration. A real difference between arms should clearly exceed this.",
        },
    }


def _planted_section(data: Mapping[str, Any]) -> dict[str, Any]:
    cases = {row["target_attempt_id"]: row for row in data["review_planted_cases"]}
    if not cases:
        return {"cases": 0, "note": data["review_runs"][0].get("manifest", {}).get("notes", {}).get("planted", "no planted cases")}
    target_of = {row["id"]: row for row in data["review_targets"]}
    matches = {row["left_id"]: row["verdict"] for row in data["ledger:planted_cause_match"]}
    receipts = data["review_context_receipts"]
    per: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    sweep: dict[str, dict[str, Any]] = defaultdict(lambda: {"n": 0, "target_cause": 0, "expected_cited": 0, "expected_total": 0, "unknown_ids": 0, "tokens": []})
    for row in data["review_diagnoses"]:
        target = target_of.get(row["target_id"])
        if target is None or target["kind"] != "planted":
            continue
        case = cases.get(target["attempt_id"])
        if case is None:
            continue
        truth = case.get("truth") or {}
        shape = case["shape"]
        arm = row["arm"]
        bucket = per[arm][shape]
        bucket["n"] += 1
        if row["status"] != "completed":
            bucket["not_completed"] += 1
            continue
        verdict = matches.get(row["id"])
        if verdict:
            bucket[f"cause:{verdict}"] += 1
        proposal = row.get("proposal") or {}
        cited = {
            str(citation.get("attempt_id"))
            for claim in proposal.get("pattern_claims") or []
            if claim.get("relation") != "disconfirming"
            for citation in claim.get("cited") or []
        }
        validated = {str(value.get("attempt_id")) for value in (receipts.get(row["id"], {}).get("validated_citations") or [])}
        expected = set(truth.get("expected_link_attempt_ids") or [])
        forbidden = set(truth.get("forbidden_link_attempt_ids") or [])
        receipt = receipts.get(row["id"], {})
        shown = set(receipt.get("failure_attempt_ids") or []) | set(receipt.get("history_attempt_ids") or [])
        bucket["expected_links_total"] += len(expected)
        bucket["expected_links_present"] += len(expected & shown)
        bucket["expected_links_cited"] += len(expected & cited)
        bucket["expected_links_validated"] += len(expected & validated)
        bucket["forbidden_link_cited"] += 1 if forbidden & cited else 0
        bucket["changed_flag"] += 1 if any(
            (event.get("history_changed_cause") or {}).get("changed") for event in proposal.get("event_diagnoses") or []
        ) else 0
        bucket["anchoring_suspect"] += 1 if row.get("anchoring_suspect") else 0
        if arm.startswith("d_sweep_"):
            point = sweep[arm[len("d_sweep_"):]]
            point["n"] += 1
            point["target_cause"] += 1 if verdict == "target_cause" else 0
            point["expected_cited"] += len(expected & cited)
            point["expected_total"] += len(expected)
            point["unknown_ids"] += int(row.get("unknown_id_count") or 0)
            tokens = (receipts.get(row["id"], {}).get("retrieval") or {}).get("context_tokens")
            if tokens:
                point["tokens"].append(tokens)
    arms = {}
    for arm, shapes in sorted(per.items()):
        arms[arm] = {}
        for shape, bucket in sorted(shapes.items()):
            judged = sum(bucket[f"cause:{value}"] for value in ("target_cause", "other_planted_cause", "neither"))
            arms[arm][shape] = {
                "n": bucket["n"],
                "cause_recovered": wilson(bucket["cause:target_cause"], judged),
                "cause_is_other_planted": wilson(bucket["cause:other_planted_cause"], judged),
                "history_changed_cause_flagged": bucket["changed_flag"],
                "anchoring_suspect": bucket["anchoring_suspect"],
                "expected_links": {
                    "total": bucket["expected_links_total"],
                    "present_inline": bucket["expected_links_present"],
                    "cited": bucket["expected_links_cited"],
                    "validated": bucket["expected_links_validated"],
                },
                "kept_apart": wilson(bucket["n"] - bucket["not_completed"] - bucket["forbidden_link_cited"], bucket["n"] - bucket["not_completed"]),
            }
    return {
        "cases": len(cases),
        "shapes": dict(Counter(row["shape"] for row in cases.values())),
        "by_arm": arms,
        "context_length_sweep": {
            budget: {
                "diagnoses": point["n"],
                "context_tokens_mean": round(statistics.mean(point["tokens"]), 1) if point["tokens"] else None,
                "cause_recovered": point["target_cause"],
                "expected_links_cited": f"{point['expected_cited']}/{point['expected_total']}",
                "unknown_ids": point["unknown_ids"],
            }
            for budget, point in sorted(sweep.items(), key=lambda item: int(item[0]))
        },
    }


def _links_section(data: Mapping[str, Any]) -> dict[str, Any]:
    planted_ids = {row["attempt_id"] for row in data["review_targets"] if row["kind"] == "planted"}
    by_link: dict[tuple[str, str], dict[int, str]] = defaultdict(dict)
    arms_of: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in data["ledger:same_cause"]:
        key = (row["left_id"], row["right_id"])
        by_link[key][int(row["rationale"].get("pass", 0))] = row["verdict"]
        arms_of[key].update(row["rationale"].get("arms") or [])
    validated: dict[tuple[str, str], bool] = {}
    target_of = {row["id"]: row["attempt_id"] for row in data["review_targets"]}
    for row in data["review_diagnoses"]:
        for citation in data["review_context_receipts"].get(row["id"], {}).get("validated_citations") or []:
            validated[(target_of.get(row["target_id"], ""), str(citation.get("attempt_id")))] = True
    per_arm: dict[str, Counter] = defaultdict(Counter)
    confirmed_by_arm: dict[str, set[tuple[str, str]]] = defaultdict(set)
    agreement = []
    for key, passes in by_link.items():
        verdicts = list(passes.values())
        final = verdicts[0] if len(set(verdicts)) == 1 else "split"
        if len(verdicts) == 2:
            agreement.append(verdicts[0] == verdicts[1])
        for arm in arms_of[key]:
            per_arm[arm][final] += 1
            per_arm[arm]["validated" if validated.get(key) else "unvalidated"] += 1
            if final == "same":
                confirmed_by_arm[arm].add(key)
    unique = {
        arm: len(keys - set().union(*(other for name, other in confirmed_by_arm.items() if name != arm)))
        for arm, keys in confirmed_by_arm.items()
    }
    return {
        "links_judged": len(by_link),
        "real_links": sum(1 for key in by_link if key[0] not in planted_ids),
        "pass_agreement": wilson(sum(agreement), len(agreement)),
        "by_arm": {
            arm: {
                "label": ARM_LABELS.get(arm, arm),
                "judged_same_both_passes": counts["same"],
                "judged_different": counts["different"],
                "not_sure": counts["not_sure"],
                "split_between_passes": counts["split"],
                "same_share": wilson(counts["same"], sum(counts[value] for value in ("same", "different", "not_sure", "split"))),
                "validated_citations": counts["validated"],
                "unvalidated_citations": counts["unvalidated"],
                "confirmed_links_unique_to_arm": unique.get(arm, 0),
            }
            for arm, counts in sorted(per_arm.items())
        },
    }


def _knn_section(data: Mapping[str, Any]) -> dict[str, Any]:
    rows = [row for row in data["review_diagnoses"] if row["arm"] == "c"]
    methods = Counter()
    knn_only_cited = 0
    knn_only_validated = 0
    for row in rows:
        receipt = data["review_context_receipts"].get(row["id"], {})
        retrieval = receipt.get("retrieval") or {}
        methods[retrieval.get("method") or row["status"]] += 1
        knn_only = set(retrieval.get("knn_only_attempt_ids") or [])
        proposal = row.get("proposal") or {}
        cited = {str(value) for value in proposal.get("evidence_attempt_ids") or []}
        cited |= {
            str(citation.get("attempt_id"))
            for claim in proposal.get("pattern_claims") or []
            for citation in claim.get("cited") or []
        }
        validated = {str(value.get("attempt_id")) for value in receipt.get("validated_citations") or []}
        knn_only_cited += len(knn_only & cited)
        knn_only_validated += len(knn_only & validated)
    return {
        "diagnoses": len(rows),
        "retrieval_methods": dict(methods),
        "knn_only_traces_cited": knn_only_cited,
        "knn_only_citations_validated": knn_only_validated,
    }


def _grade_summary(record: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not record:
        return None
    return {
        "score": record.get("rubric_score"),
        "max": record.get("max_points"),
        "criteria": {str(row.get("criterion_id")): float(row.get("points_awarded") or 0.0) for row in record.get("criteria") or []},
        "fatal": sorted(record.get("fatal_errors") or []),
    }


def _grader_section(data: Mapping[str, Any]) -> dict[str, Any]:
    grades: dict[str, dict[str, Any]] = defaultdict(dict)
    for row in data["review_blind_grades"]:
        if row["status"] == "completed":
            grades[row["attempt_id"]][row["purpose"]] = row.get("record")
    real = [row for row in data["review_targets"] if row["kind"] == "real"]

    def compare(first: str, second: str) -> dict[str, Any]:
        criterion_pairs: list[tuple[bool, bool]] = []
        exact = 0
        diffs = []
        fatal_agree = 0
        n = 0
        for target in real:
            attempt_id = target["attempt_id"]
            left = _stored(data, attempt_id) if first == "stored" else _grade_summary(grades[attempt_id].get(first))
            right = _stored(data, attempt_id) if second == "stored" else _grade_summary(grades[attempt_id].get(second))
            if not left or not right or left.get("score") is None or right.get("score") is None:
                continue
            n += 1
            maximum = float(left.get("max") or right.get("max") or 1.0) or 1.0
            exact += 1 if float(left["score"]) == float(right["score"]) else 0
            diffs.append(abs(float(left["score"]) - float(right["score"])) / maximum)
            fatal_agree += 1 if left["fatal"] == right["fatal"] else 0
            maxima = data["criterion_max"].get(attempt_id, {})
            for criterion, maximum_points in maxima.items():
                if criterion in left["criteria"] and criterion in right["criteria"]:
                    criterion_pairs.append(
                        (left["criteria"][criterion] + 1e-9 >= maximum_points, right["criteria"][criterion] + 1e-9 >= maximum_points)
                    )
        return {
            "attempts": n,
            "exact_score_agreement": wilson(exact, n),
            "mean_abs_score_diff_fraction": round(statistics.mean(diffs), 4) if diffs else None,
            "criterion_pass_kappa": cohen_kappa(criterion_pairs),
            "criterion_pairs": len(criterion_pairs),
            "fatal_error_agreement": wilson(fatal_agree, n),
        }

    anchors_scored = 0
    anchors_right = 0
    for target in real:
        adjudicated = data["stored_adjudicated_anchor"].get(target["attempt_id"])
        record = grades[target["attempt_id"]].get("primary")
        if not adjudicated or not record:
            continue
        quotes = {
            " ".join(str((row.get("first_divergence") or {}).get("quote") or "").split()).casefold()
            for row in record.get("error_attributions") or []
        }
        wanted = " ".join(str(adjudicated.get("quote") or "").split()).casefold()
        if wanted:
            anchors_scored += 1
            anchors_right += 1 if wanted in quotes else 0
    probes: dict[str, Any] = {}
    by_probe: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in data["review_probes"]:
        by_probe[row["probe"]].append(row)
    valid = [row for row in by_probe.get("valid_alternative", []) if row["status"] == "graded"]
    probes["valid_alternative"] = {
        "statuses": dict(Counter(row["status"] for row in by_probe.get("valid_alternative", []))),
        "false_rejection": wilson(sum(1 for row in valid if float(row["blind_score"]) < float(row["max_points"])), len(valid)),
    }
    synthetic = [row for row in by_probe.get("synthetic_error", []) if row["status"] == "graded"]
    synthetic_errors = [abs(float(row["blind_score"]) - float(row["known_score"])) / float(row["max_points"] or 1) for row in synthetic]
    real_errors = _owner_grade_errors(data, grades)
    probes["real_vs_synthetic"] = {
        "statuses": dict(Counter(row["status"] for row in by_probe.get("synthetic_error", []))),
        "synthetic_mean_abs_error_fraction": round(statistics.mean(synthetic_errors), 4) if synthetic_errors else None,
        "synthetic_n": len(synthetic_errors),
        "real_mean_abs_error_fraction": round(statistics.mean(real_errors), 4) if real_errors else None,
        "real_n": len(real_errors),
        "gap": (
            round(statistics.mean(real_errors) - statistics.mean(synthetic_errors), 4)
            if real_errors and synthetic_errors else None
        ),
        "real_source": "owner spot-check grade verdicts (screen 3)",
    }
    paraphrase = [row for row in by_probe.get("paraphrase", []) if row["status"] == "graded"]
    flips = sum(
        1 for row in paraphrase
        if (float(row["blind_score"]) >= float(row["max_points"])) != (float(row["known_score"]) >= float(row["max_points"]))
    )
    probes["paraphrase"] = {
        "statuses": dict(Counter(row["status"] for row in by_probe.get("paraphrase", []))),
        "grade_flip_rate": wilson(flips, len(paraphrase)),
        "mean_abs_score_change_fraction": (
            round(statistics.mean(abs(float(row["blind_score"]) - float(row["known_score"])) / float(row["max_points"] or 1) for row in paraphrase), 4)
            if paraphrase else None
        ),
    }
    return {
        "blind_vs_stored_joint": compare("primary", "stored"),
        "joint_repeat_vs_stored_joint": compare("joint_repeat", "stored"),
        "blind_vs_joint_repeat": compare("primary", "joint_repeat"),
        "first_divergence_anchor_accuracy_vs_adjudicated": wilson(anchors_right, anchors_scored),
        "probes": probes,
    }


def _stored(data: Mapping[str, Any], attempt_id: str) -> dict[str, Any] | None:
    criteria = data["stored_evidence"].get(attempt_id)
    if criteria is None:
        return None
    maxima = data["criterion_max"].get(attempt_id, {})
    return {
        "score": data["stored_score"].get(attempt_id),
        "max": sum(maxima.values()) or None,
        "criteria": dict(criteria),
        "fatal": sorted(data["stored_fatal"].get(attempt_id) or []),
    }


def _owner_grade_errors(data: Mapping[str, Any], grades: Mapping[str, Mapping[str, Any]]) -> list[float]:
    errors = []
    for row in data["review_judgments"]:
        if row["task"] != "grade_disagreement" or row["judge"] != "owner":
            continue
        record = grades.get(row["subject_id"], {}).get("primary")
        stored = _stored(data, row["subject_id"])
        if not record or not stored or stored.get("score") is None:
            continue
        maximum = float(record.get("max_points") or 1.0) or 1.0
        if row["verdict"] == "blind_right":
            errors.append(0.0)
        elif row["verdict"] == "stored_right":
            errors.append(abs(float(record["rubric_score"]) - float(stored["score"])) / maximum)
    return errors


def _registry_section(data: Mapping[str, Any]) -> dict[str, Any]:
    target_of = {row["id"]: row for row in data["review_targets"]}
    out: dict[str, Any] = {}
    for arm in ("b", "c", "d", "e"):
        agree = 0
        compared = 0
        both_abstain = 0
        disagreements = []
        for row in data["review_diagnoses"]:
            if row["arm"] != arm or row["status"] != "completed":
                continue
            target = target_of.get(row["target_id"])
            if target is None or target["kind"] != "real":
                continue
            stored = data["stored_misconceptions"].get(target["attempt_id"]) or []
            for event in (row.get("proposal") or {}).get("event_diagnoses") or []:
                index = int(event.get("event_index", -1))
                if index < 0 or index >= len(stored):
                    continue
                legacy = stored[index]
                match = event.get("registry_match") or {}
                proposed = match.get("id") if match.get("kind") in {"durable", "candidate"} else None
                if not legacy and not proposed:
                    # Neither linked a registry row: not evidence of agreement.
                    both_abstain += 1
                    continue
                compared += 1
                if legacy == proposed:
                    agree += 1
                else:
                    disagreements.append({"target_id": row["target_id"], "event_index": index, "legacy_id": legacy, "proposed_kind": match.get("kind"), "proposed_id": proposed})
        out[arm] = {
            "agreement_where_either_linked": wilson(agree, compared),
            "both_unlinked": both_abstain,
            "disagreements": disagreements,
        }
    return out


def _spot_check_section(data: Mapping[str, Any]) -> dict[str, Any]:
    owner = [row for row in data["review_judgments"] if row["judge"] == "owner"]
    if not owner:
        return {"ran": False, "note": "The optional owner spot-check was not run; the LLM judge is unvalidated against the learner's own recognition."}
    arm_of = {row["id"]: row["arm"] for row in data["review_diagnoses"]}
    ratings = Counter()
    per_arm: dict[str, Counter] = defaultdict(Counter)
    judge_by_diagnosis: dict[str, list[str]] = defaultdict(list)
    for row in data["ledger:diagnosis_rating"]:
        judge_by_diagnosis[row["left_id"]].append(row["verdict"])
    agree = 0
    compared = 0
    for row in owner:
        if row["task"] == "diagnosis_rating":
            arm = arm_of.get(row["subject_id"], "?")
            per_arm[arm][row["verdict"]] += 1
            ratings[row["verdict"]] += 1
            verdicts = judge_by_diagnosis.get(row["subject_id"]) or []
            if verdicts and row["verdict"] != "not_sure":
                compared += 1
                agree += 1 if Counter(verdicts).most_common(1)[0][0] == row["verdict"] else 0
    tasks = Counter(row["task"] for row in owner)
    return {
        "ran": True,
        "verdicts_by_task": dict(tasks),
        "owner_ratings_by_arm": {arm: dict(counts) for arm, counts in sorted(per_arm.items())},
        "judge_owner_rating_agreement": wilson(agree, compared),
        "link_verdicts": dict(Counter(row["verdict"] for row in owner if row["task"] == "same_cause")),
        "grade_verdicts": dict(Counter(row["verdict"] for row in owner if row["task"] == "grade_disagreement")),
        "best_picks": dict(Counter(arm_of.get(row["verdict"], row["verdict"]) for row in owner if row["task"] == "diagnosis_best")),
    }


def offline_review_report(run_dir: Path, *, vault: Any | None = None) -> dict[str, Any]:
    data = load_run(run_dir)
    run = data["review_runs"][0] if data["review_runs"] else {}
    manifest = run.get("manifest") or {}
    criterion_max: dict[str, dict[str, float]] = {}
    if vault is not None:
        for target in data["review_targets"]:
            item = vault.practice_items.get(target["practice_item_id"])
            if item is not None:
                criterion_max[target["attempt_id"]] = {
                    criterion.id: float(criterion.points) for criterion in resolved_rubric(vault, item).criteria
                }
    data["criterion_max"] = criterion_max
    targets = Counter(row["kind"] for row in data["review_targets"])
    return {
        "report_version": REPORT_VERSION,
        "run": {
            "run_id": data["run_id"],
            "status": run.get("status"),
            "targets": dict(targets),
            "manifest": {
                key: manifest.get(key)
                for key in ("review_version", "algorithm_version", "prompt_versions", "settings", "spend", "notes", "client_notes", "read_only_workspace_supported")
            },
        },
        "arms": _arm_section(data),
        "judge": _judge_section(data),
        "planted": _planted_section(data),
        "links": _links_section(data),
        "knn": _knn_section(data),
        "grader": _grader_section(data),
        "registry_match": _registry_section(data),
        "spot_check": _spot_check_section(data),
    }


def _fmt_rate(value: Mapping[str, Any] | None) -> str:
    if not value or value.get("rate") is None:
        return "n/a"
    return f"{value['rate']:.2f} (n={value['n']}, 95% {value['low']:.2f}–{value['high']:.2f})"


def render_markdown(report: Mapping[str, Any]) -> str:
    """The owner-facing report: aggregates only, no learner text."""

    run = report["run"]
    lines = [
        "# Slice 1 M1 offline review report",
        "",
        f"- run: `{run['run_id']}` ({run['status']})",
        f"- targets: {run['targets'].get('real', 0)} real, {run['targets'].get('planted', 0)} planted (unlabelled to the judge)",
        f"- algorithm version: {run['manifest'].get('algorithm_version')}",
        f"- prompt versions: {json.dumps(run['manifest'].get('prompt_versions') or {}, sort_keys=True)}",
        "",
        "No thresholds are set in this slice. Read each difference against its noise floor: "
        "(b) vs its repeat (b') for the diagnoser, the joint grader vs its own repeat for grading.",
        "",
        "## Skipped or degraded",
        "",
    ]
    notes = {**(run["manifest"].get("client_notes") or {}), **(run["manifest"].get("notes") or {})}
    lines += [f"- {key}: {json.dumps(value) if not isinstance(value, str) else value}" for key, value in sorted(notes.items())] or ["- none"]
    lines += ["", "## Arms", "", "| arm | completed | other | unknown ids (total / with any) | anchoring suspect | validated citations | calls | tokens in/out | est. USD | latency p50/p95 s |", "|---|---|---|---|---|---|---|---|---|---|"]
    for arm, row in report["arms"].items():
        statuses = dict(row["statuses"])
        completed = statuses.pop("completed", 0)
        lines.append(
            f"| {row['label']} | {completed} | {statuses or '-'} | {row['unknown_id_count']['total']} / {row['unknown_id_count']['diagnoses_with_any']} "
            f"| {_fmt_rate(row['anchoring_suspect'])} | {row['validated_citations']} | {row['calls']} "
            f"| {row['input_tokens']}/{row['output_tokens']} | {row['estimated_usd'] if row['estimated_usd'] is not None else 'n/a'} {','.join(row['cost_basis'])} "
            f"| {row['latency_p50']}/{row['latency_p95']} |"
        )
    judge = report["judge"]
    lines += ["", "## Is the history-aware diagnoser better? (LLM judge, two passes)", "", "| arm | right | right or partly | real: right | planted: right |", "|---|---|---|---|---|"]
    for arm, row in judge["ratings"].items():
        lines.append(f"| {row['label']} | {_fmt_rate(row['right'])} | {_fmt_rate(row['right_or_partly'])} | {_fmt_rate(row['real_right'])} | {_fmt_rate(row['planted_right'])} |")
    lines += [
        "",
        f"Rating agreement between passes: {_fmt_rate(judge['rating_pass_agreement'])}. "
        f"Best picks: {json.dumps(judge['best_picks'], sort_keys=True)}.",
        "",
        "| pair | first wins | second wins | ties | first's share of decided | pass agreement |",
        "|---|---|---|---|---|---|",
    ]
    for key, row in judge["pairwise"].items():
        lines.append(f"| {row['first']} vs {row['second']} | {row['first_wins']} | {row['second_wins']} | {row['ties']} | {_fmt_rate(row['first_win_share_of_decided'])} | {_fmt_rate(row['pass_agreement'])} |")
    lines += ["", f"Noise floor ((b) vs (b') decided share): {_fmt_rate(judge['noise_floor']['b_vs_b_prime_decided_share'])}. {judge['noise_floor']['note']}"]
    planted = report["planted"]
    lines += ["", "## Planted truth (E2, E3, E6)", ""]
    if not planted.get("cases"):
        lines.append(f"- {planted.get('note')}")
    else:
        lines += [f"- cases: {planted['cases']} {json.dumps(planted['shapes'], sort_keys=True)}", "", "| arm | shape | cause recovered | other planted cause | changed flagged | expected links present/cited/validated/total | kept apart |", "|---|---|---|---|---|---|---|"]
        for arm, shapes in planted["by_arm"].items():
            for shape, row in shapes.items():
                links = row["expected_links"]
                lines.append(
                    f"| {ARM_LABELS.get(arm, arm)} | {shape} | {_fmt_rate(row['cause_recovered'])} | {_fmt_rate(row['cause_is_other_planted'])} "
                    f"| {row['history_changed_cause_flagged']} | {links['present_inline']}/{links['cited']}/{links['validated']}/{links['total']} | {_fmt_rate(row['kept_apart'])} |"
                )
        if planted["context_length_sweep"]:
            lines += ["", "Context-length sweep, (d) on planted cases:", "", "| budget | diagnoses | mean context tokens | cause recovered | expected links cited | unknown ids |", "|---|---|---|---|---|---|"]
            for budget, row in planted["context_length_sweep"].items():
                lines.append(f"| {budget} | {row['diagnoses']} | {row['context_tokens_mean']} | {row['cause_recovered']} | {row['expected_links_cited']} | {row['unknown_ids']} |")
    links = report["links"]
    lines += ["", "## Are \"same mistake\" links trustworthy?", "", f"Links judged: {links['links_judged']} ({links['real_links']} on real attempts). Pass agreement: {_fmt_rate(links['pass_agreement'])}.", "", "| arm | same (both passes) | different | not sure | split | same share | validated / unvalidated citations | confirmed links unique to arm |", "|---|---|---|---|---|---|---|---|"]
    for arm, row in links["by_arm"].items():
        lines.append(f"| {row['label']} | {row['judged_same_both_passes']} | {row['judged_different']} | {row['not_sure']} | {row['split_between_passes']} | {_fmt_rate(row['same_share'])} | {row['validated_citations']} / {row['unvalidated_citations']} | {row['confirmed_links_unique_to_arm']} |")
    knn = report["knn"]
    lines += ["", "## Retrieval value, (c) only", "", f"- retrieval methods: {json.dumps(knn['retrieval_methods'], sort_keys=True)}", f"- traces only kNN surfaced that were cited: {knn['knn_only_traces_cited']} (validated: {knn['knn_only_citations_validated']})"]
    grader = report["grader"]
    lines += ["", "## Is the blind grader at least as good? (E1)", "", "| comparison | attempts | exact score agreement | mean abs score diff | criterion κ | fatal agreement |", "|---|---|---|---|---|---|"]
    for key in ("blind_vs_stored_joint", "joint_repeat_vs_stored_joint", "blind_vs_joint_repeat"):
        row = grader[key]
        lines.append(f"| {key.replace('_', ' ')} | {row['attempts']} | {_fmt_rate(row['exact_score_agreement'])} | {row['mean_abs_score_diff_fraction']} | {row['criterion_pass_kappa']} | {_fmt_rate(row['fatal_error_agreement'])} |")
    probes = grader["probes"]
    lines += [
        "",
        f"- first-divergence anchor accuracy vs adjudicated anchors: {_fmt_rate(grader['first_divergence_anchor_accuracy_vs_adjudicated'])}",
        f"- valid-alternative false rejection: {_fmt_rate(probes['valid_alternative']['false_rejection'])} (statuses {json.dumps(probes['valid_alternative']['statuses'], sort_keys=True)})",
        f"- real-vs-synthetic: synthetic error {probes['real_vs_synthetic']['synthetic_mean_abs_error_fraction']} (n={probes['real_vs_synthetic']['synthetic_n']}), "
        f"real error {probes['real_vs_synthetic']['real_mean_abs_error_fraction']} (n={probes['real_vs_synthetic']['real_n']}, from {probes['real_vs_synthetic']['real_source']}), gap {probes['real_vs_synthetic']['gap']}",
        f"- grade flips under paraphrase: {_fmt_rate(probes['paraphrase']['grade_flip_rate'])}",
    ]
    lines += ["", "## Registry match vs the legacy misconception match (E4)", ""]
    for arm, row in report["registry_match"].items():
        lines.append(
            f"- {ARM_LABELS.get(arm, arm)}: agreement where either linked a registry row {_fmt_rate(row['agreement_where_either_linked'])}; "
            f"both unlinked {row['both_unlinked']}; disagreements to audit {len(row['disagreements'])} (ids in report.json)"
        )
    spot = report["spot_check"]
    lines += ["", "## Owner spot-check", ""]
    if not spot["ran"]:
        lines.append(f"- {spot['note']}")
    else:
        lines += [
            f"- verdicts: {json.dumps(spot['verdicts_by_task'], sort_keys=True)}",
            f"- owner ratings by arm: {json.dumps(spot['owner_ratings_by_arm'], sort_keys=True)}",
            f"- judge-owner rating agreement: {_fmt_rate(spot['judge_owner_rating_agreement'])}",
            f"- link verdicts: {json.dumps(spot['link_verdicts'], sort_keys=True)}; grade verdicts: {json.dumps(spot['grade_verdicts'], sort_keys=True)}",
        ]
    spend = run["manifest"].get("spend") or {}
    lines += ["", "## Spend", "", "```json", json.dumps(spend, indent=2, sort_keys=True), "```", ""]
    return "\n".join(lines)


__all__ = [
    "REPORT_VERSION",
    "cohen_kappa",
    "load_run",
    "offline_review_report",
    "render_markdown",
    "wilson",
]
