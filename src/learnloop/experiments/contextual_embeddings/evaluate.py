"""Scoring E0: per-question metrics per arm, paired comparisons, S1-S4 inputs.

Rankings are unit ids (best first). A unit's coverage is its members'
original ``(extraction, span, start, end)``; merged units never earn extra
recall because coverage is deduplicated by span and offset. Questions with
unresolved labels are excluded from verdicts and counted (S1); unanswerable
questions have recall N/A and are scored for abstention in the answers.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from learnloop.experiments.contextual_embeddings import metrics, pins
from learnloop.experiments.contextual_embeddings.bank import BankQuestion, QuestionLabels, unit_refs
from learnloop.experiments.contextual_embeddings.corpus import CorpusSnapshot


def question_rows(snapshot: CorpusSnapshot, questions: Sequence[BankQuestion],
                  rankings: Mapping[str, Mapping[str, Sequence[str]]],
                  labels: Mapping[str, QuestionLabels], *, k: int = pins.TOP_K) -> list[dict[str, Any]]:
    """One row per question: ``{query_id, family, stratum, arm metrics...}``.
    ``rankings``: ``{arm: {query_id: [unit ids]}}``."""

    rows = []
    for question in questions:
        label = labels.get(question.query_id)
        row: dict[str, Any] = {"query_id": question.query_id, "family": question.family or "none",
                               "stratum": question.stratum, "split": question.split,
                               "unresolved": bool(label and label.unresolved),
                               "answerable": question.answerable if label is None or label.answerable is None
                               else bool(label.answerable)}
        sets = [evidence.required for evidence in question.evidence_sets]
        final = label.final if label is not None else {}
        for arm, by_question in rankings.items():
            ranked = list(by_question.get(question.query_id, []))
            if question.query_id not in by_question or row["unresolved"]:
                row[f"{arm}:ce10"] = None
                continue
            pieces = [ref for unit_id in ranked[:k] for ref in unit_refs(snapshot.unit(unit_id))]
            row[f"{arm}:ce10"] = metrics.complete_evidence(pieces, sets) if row["answerable"] else None
            row[f"{arm}:support10"] = metrics.support_recall(pieces, sets) if row["answerable"] else None
            row[f"{arm}:answer10"] = metrics.answer_recall(pieces, question.answer_spans)
            row[f"{arm}:ndcg10"] = metrics.ndcg(ranked, final, k=k)
            row[f"{arm}:mrr"] = metrics.mrr(ranked, final, k=k)
            row[f"{arm}:unknown"] = metrics.unknown_share(ranked, final, k=k)
        rows.append(row)
    return rows


def arm_summary(rows: Sequence[Mapping[str, Any]], arms: Sequence[str]) -> dict[str, dict[str, Any]]:
    summary = {}
    for arm in arms:
        entry: dict[str, Any] = {"total": len(rows)}
        for metric in ("ce10", "support10", "answer10", "ndcg10", "mrr", "unknown"):
            values = [float(row[f"{arm}:{metric}"]) for row in rows if row.get(f"{arm}:{metric}") is not None]
            entry[metric] = round(sum(values) / len(values), 4) if values else None
            if metric == "ce10":
                entry["scored"] = len(values)
        summary[arm] = entry
    return summary


def paired(rows: Sequence[Mapping[str, Any]], a: str, b: str, metric: str = "ce10") -> dict[str, Any]:
    projected = [{"family": row["family"], "a": row.get(f"{a}:{metric}"), "b": row.get(f"{b}:{metric}")}
                 for row in rows]
    return metrics.paired_bootstrap(projected, a="a", b="b")


def completion(rows: Sequence[Mapping[str, Any]], arms: Sequence[str]) -> dict[str, float]:
    """The share of answerable, resolved questions each arm scored (S1)."""

    eligible = [row for row in rows if row["answerable"] and not row["unresolved"]]
    if not eligible:
        return {arm: 0.0 for arm in arms}
    return {arm: sum(1 for row in eligible if row.get(f"{arm}:ce10") is not None) / len(eligible) for arm in arms}


def agreement(all_labels: Sequence[QuestionLabels]) -> dict[str, Any]:
    from learnloop.experiments.contextual_embeddings.bank import RELEVANCE_ORDER

    pairs = [(labels.passes[0][unit], labels.passes[1][unit]) for labels in all_labels for unit in labels.pool
             if unit in labels.passes[0] and unit in labels.passes[1]]
    result = metrics.cohen_kappa(pairs, RELEVANCE_ORDER)
    set_agreements = sum(1 for labels in all_labels if set(labels.pass_sets[0]) == set(labels.pass_sets[1]))
    return {"agreement": result, "set_agreement": round(set_agreements / len(all_labels), 4) if all_labels else None,
            "adjudicated": sum(1 for labels in all_labels if labels.adjudicated),
            "model_only": sum(1 for labels in all_labels if not labels.adjudicated),
            "unresolved": sum(1 for labels in all_labels if labels.unresolved)}
