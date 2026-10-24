"""Labels for the v2 arms' NEW candidates (spec §5.2 rules, E1's $5 plan).

E0 labelled every unit in its pool (each arm's top 20 and more). A v2 arm
can rank units E0 never judged; unjudged material stays unknown (§5.2), so
E1 labels only the new units in each v2 arm's top ``SUPPLEMENT_DEPTH`` (every
E1 endpoint is @10), with the same protocol:

* two independent Claude Sonnet 5.5 passes (E0's ``label_a``/``label_b``
  pins, prompt ``e1-supplement-v1``), blinded to arm and rank, each with its
  own order and refs, under E0's frozen relevance rubric (its hash is checked
  when ``bank`` loads); each pass also sees the passages E0 already accepted
  as required or helpful (labels shown as final) so a new candidate can
  complete a set with them;
* a set must contain at least one new candidate (E0's own sets stand);
* Claude Opus 5.5 (E0's ``adjudicator`` pin, ``e1-supplement-adjudicate-v1``)
  audits every disagreement, every proposed new set (each is used by the
  primary endpoint) and a seeded 20% of the rest; a malformed or unresolved
  verdict leaves the new candidates unknown and is counted;
* κ over the two passes' new-candidate labels gates E1's verdict (0.60).

Merged labels: a new candidate's final label joins ``QuestionLabels.final``,
accepted new sets join ``final_sets`` (a question with none before becomes
answerable), and the question's evidence sets are rebuilt. Every arm, E0's
included, is then rescored on the same merged labels.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
import json
from typing import Any

from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import render_structured_prompt
from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.bank import (
    RELEVANCE_ORDER,
    RELEVANCE_RUBRIC,
    BankQuestion,
    CandidateLabel,
    QuestionLabels,
    evidence_sets_from_labels,
    label_context,
    stable_order,
)
from learnloop.experiments.contextual_embeddings.budget import E0ProviderFailure, E0Stop
from learnloop.experiments.contextual_embeddings.corpus import CorpusSnapshot
from learnloop.experiments.contextual_embeddings.e1 import pins as e1_pins

SUPPORTING = ("required", "helpful")

SUPPLEMENT_RULE = (
    "The passages under 'judged' were already labelled for this question; their labels are final and shown. "
    "Label every passage under 'candidates' (and only those). Then list every SUFFICIENT evidence set that "
    "contains at least one candidate: a minimal list of refs, from either list, that together contain the "
    "answer and every condition it needs (AND within a set); give alternative sets for other valid proofs (OR "
    "across sets). Background and unrelated passages never belong to a set. Judge only from the passages shown."
)
SUPPLEMENT_INSTRUCTIONS = RELEVANCE_RUBRIC + " " + SUPPLEMENT_RULE

#: E0's pins with E1's prompt versions (same models, routes, prices, bounds).
E1_ROLE_PINS = {
    "label_a": replace(pins.ROLE_PINS["label_a"], prompt_version=e1_pins.SUPPLEMENT_PROMPT_VERSION),
    "label_b": replace(pins.ROLE_PINS["label_b"], prompt_version=e1_pins.SUPPLEMENT_PROMPT_VERSION),
    "adjudicator": replace(pins.ROLE_PINS["adjudicator"], prompt_version=e1_pins.SUPPLEMENT_ADJUDICATE_VERSION),
}


class SupplementPass(WireModel):
    labels: list[CandidateLabel]
    new_sets: list[list[str]]


class SupplementVerdict(WireModel):
    labels: list[CandidateLabel]
    new_sets: list[list[str]] = Field(default_factory=list)
    unresolved: bool


@dataclass
class Supplement:
    query_id: str
    candidates: list[str]
    passes: list[dict[str, str]] = field(default_factory=list)
    pass_sets: list[list[frozenset[str]]] = field(default_factory=list)
    malformed: list[int] = field(default_factory=list)
    final: dict[str, str] = field(default_factory=dict)
    final_sets: list[frozenset[str]] = field(default_factory=list)
    adjudicated: bool = False
    unresolved: bool = False
    audit_reason: str | None = None
    problems: list[str] = field(default_factory=list)


def new_candidates(question: BankQuestion, labels: QuestionLabels | None,
                   v2_rankings: Mapping[str, Mapping[str, Sequence[str]]], *,
                   depth: int = e1_pins.SUPPLEMENT_DEPTH) -> list[str]:
    """Units in any v2 arm's top ``depth`` that E0's labels never judged."""

    if labels is None or labels.unresolved:
        return []
    judged = set(labels.pool) | set(labels.final)
    found: list[str] = []
    for arm in sorted(v2_rankings):
        found.extend(unit for unit in list(v2_rankings[arm].get(question.query_id, []))[:depth] if unit not in judged)
    return list(dict.fromkeys(found))


def judged_support(labels: QuestionLabels) -> list[str]:
    return sorted(unit for unit, value in labels.final.items() if value in SUPPORTING)


def _refs(prefix: str, units: Sequence[str]) -> dict[str, str]:
    return {f"{prefix}{index}": unit for index, unit in enumerate(units, start=1)}


def _prompt(title: str, version: str, instructions: str, question: BankQuestion, snapshot: CorpusSnapshot,
            judged: Mapping[str, str], candidates: Mapping[str, str], final: Mapping[str, str],
            extra: Mapping[str, Any] | None = None) -> str:
    return render_structured_prompt(title, version, {
        "instructions": instructions,
        "context": {**question.context(), **dict(extra or {}),
                    "judged": [{"ref": ref, "label": final[unit], **label_context(snapshot, snapshot.unit(unit))}
                               for ref, unit in judged.items()],
                    "candidates": [{"ref": ref, **label_context(snapshot, snapshot.unit(unit))}
                                   for ref, unit in candidates.items()]},
    })


def _sets(chosen: Sequence[Sequence[str]], judged: Mapping[str, str], candidates: Mapping[str, str]
          ) -> tuple[list[frozenset[str]], int]:
    """Well-formed new sets (known refs, no repeats, at least one candidate)."""

    refs = {**judged, **candidates}
    sets, bad = [], 0
    for members in chosen:
        if (not members or len(set(members)) != len(members) or any(ref not in refs for ref in members)
                or not any(ref in candidates for ref in members)):
            bad += 1
            continue
        sets.append(frozenset(refs[ref] for ref in members))
    return sets, bad


def label_supplement(question: BankQuestion, labels: QuestionLabels, candidates: Sequence[str],
                     snapshot: CorpusSnapshot, caller: Any) -> Supplement:
    """Two blinded passes over the new candidates (see the module docstring)."""

    result = Supplement(question.query_id, list(candidates))
    support = judged_support(labels)
    for pass_index, role in enumerate(("label_a", "label_b")):
        cands = _refs("n", stable_order(list(candidates), "e1-supplement", question.query_id, pass_index))
        judged = _refs("j", stable_order(support, "e1-judged", question.query_id, pass_index))
        prompt = _prompt("E1 supplementary labels", e1_pins.SUPPLEMENT_PROMPT_VERSION, SUPPLEMENT_INSTRUCTIONS,
                         question, snapshot, judged, cands, labels.final, {"pass": pass_index + 1})
        answer = caller.call(role, prompt=prompt, result_model=SupplementPass)
        found: dict[str, str] = {}
        for item in answer.labels:
            if item.ref in cands and cands[item.ref] not in found:
                found[cands[item.ref]] = item.relevance
        sets, bad = _sets(answer.new_sets, judged, cands)
        # A set member must be supporting by its final label: the pass's own for a candidate.
        merged = {**labels.final, **found}
        kept = [chosen for chosen in sets if all(merged.get(unit) in SUPPORTING for unit in chosen)]
        result.passes.append(found)
        result.pass_sets.append(sorted(set(kept), key=sorted))
        result.malformed.append(bad + len(sets) - len(kept))
        record = getattr(caller, "record_judgment", None)
        if record is not None:
            record(task="e1_supplement_label", left_id=question.query_id, verdict=json.dumps(found, sort_keys=True),
                   details={"pass": pass_index + 1, "sets": [sorted(chosen) for chosen in kept]})
    return result


def needs_audit(item: Supplement) -> str | None:
    if any(item.passes[0].get(unit) != item.passes[1].get(unit) for unit in item.candidates):
        return "disagreement"
    if set(item.pass_sets[0]) != set(item.pass_sets[1]) or any(item.malformed):
        return "set_disagreement"
    if item.pass_sets[0]:
        return "new_set_used_by_primary_endpoint"
    return None


def audit_plan(items: Sequence[Supplement], *, share: float = pins.AUDIT_SAMPLE_SHARE) -> dict[str, str]:
    plan, rest = {}, []
    for item in items:
        reason = needs_audit(item)
        if reason:
            plan[item.query_id] = reason
        else:
            rest.append(item.query_id)
    for query_id in stable_order(rest, "e1-audit-sample")[: int(round(len(rest) * share))]:
        plan[query_id] = "seeded_sample"
    return plan


def adjudicate_supplement(question: BankQuestion, labels: QuestionLabels, item: Supplement, snapshot: CorpusSnapshot,
                          caller: Any) -> Supplement:
    cands = _refs("n", stable_order(item.candidates, "e1-adjudicate", question.query_id))
    judged = _refs("j", stable_order(judged_support(labels), "e1-adjudicate-judged", question.query_id))
    back = {unit: ref for ref, unit in {**judged, **cands}.items()}
    prompt = _prompt("E1 supplementary adjudication", e1_pins.SUPPLEMENT_ADJUDICATE_VERSION,
                     SUPPLEMENT_INSTRUCTIONS + " You are the adjudicator: decide each candidate's label and the "
                     "final new sets; set unresolved true only if the passages cannot settle sufficiency.",
                     question, snapshot, judged, cands, labels.final,
                     {"pass_1": {back[unit]: value for unit, value in item.passes[0].items()},
                      "pass_2": {back[unit]: value for unit, value in item.passes[1].items()},
                      "pass_1_sets": [sorted(back[unit] for unit in chosen) for chosen in item.pass_sets[0]],
                      "pass_2_sets": [sorted(back[unit] for unit in chosen) for chosen in item.pass_sets[1]]})
    verdict = caller.call("adjudicator", prompt=prompt, result_model=SupplementVerdict)
    problems = []
    final: dict[str, str] = {}
    for label in verdict.labels:
        if label.ref not in cands:
            problems.append("unknown_or_judged_ref_labelled")
        elif cands[label.ref] in final:
            problems.append("duplicate_label")
        else:
            final[cands[label.ref]] = label.relevance
    for unit in item.candidates:
        if unit not in final:
            if item.passes[0].get(unit) is not None and item.passes[0].get(unit) == item.passes[1].get(unit):
                final[unit] = item.passes[0][unit]
            else:
                problems.append("disputed_candidate_unlabelled")
    sets, bad = _sets(verdict.new_sets, judged, cands)
    if bad:
        problems.append("malformed_new_set")
    merged = {**labels.final, **final}
    if any(merged.get(unit) not in SUPPORTING for chosen in sets for unit in chosen):
        problems.append("set_member_not_supporting")
    item.adjudicated = True
    item.problems = sorted(set(problems))
    if item.problems or verdict.unresolved:
        item.unresolved, item.final, item.final_sets = True, {}, []
    else:
        item.final, item.final_sets = final, sorted(set(sets), key=sorted)
    record = getattr(caller, "record_judgment", None)
    if record is not None:
        record(task="e1_supplement_adjudication", left_id=question.query_id,
               verdict="unresolved" if item.unresolved else "resolved",
               details={"problems": item.problems, "sets": [sorted(chosen) for chosen in item.final_sets]})
    return item


def accept_agreed(item: Supplement) -> Supplement:
    item.final = {unit: value for unit, value in item.passes[0].items() if item.passes[1].get(unit) == value}
    item.final_sets = list(item.pass_sets[0])
    return item


def supplement_all(snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], labels: Mapping[str, QuestionLabels],
                   v2_rankings: Mapping[str, Mapping[str, Sequence[str]]], caller: Any) -> dict[str, Any]:
    """Every question's new candidates labelled and audited; a stop keeps
    what was done (the rest stays unknown and is counted)."""

    items: dict[str, Supplement] = {}
    counts = {"questions_with_new": 0, "new_candidates": 0, "failed": 0, "missing": 0, "stopped": None}
    by_id = {question.query_id: question for question in questions}
    pending = []
    for question in questions:
        found = new_candidates(question, labels.get(question.query_id), v2_rankings)
        if found:
            pending.append((question, found))
    counts["questions_with_new"] = len(pending)
    counts["new_candidates"] = sum(len(found) for _question, found in pending)
    for question, found in pending:
        if counts["stopped"]:
            counts["missing"] += 1
            continue
        try:
            items[question.query_id] = label_supplement(question, labels[question.query_id], found, snapshot, caller)
        except E0ProviderFailure as exc:
            if exc.classification in ("invalid_output", "refusal", "truncated"):
                counts["failed"] += 1
                continue
            counts["stopped"] = f"labels: {exc.classification}"
            counts["missing"] += 1
        except E0Stop as exc:
            counts["stopped"] = f"labels: {exc.kind}"
            counts["missing"] += 1
    plan = audit_plan(list(items.values()))
    audits = {"planned": len(plan), "done": 0, "mandatory_missing": 0, "sampled_missing": 0}
    for query_id, item in items.items():
        if query_id in plan:
            item.audit_reason = plan[query_id]
            if not counts["stopped"]:
                try:
                    adjudicate_supplement(by_id[query_id], labels[query_id], item, snapshot, caller)
                    audits["done"] += 1
                except E0ProviderFailure as exc:
                    if exc.classification not in ("invalid_output", "refusal", "truncated"):
                        counts["stopped"] = f"audits: {exc.classification}"
                except E0Stop as exc:
                    counts["stopped"] = f"audits: {exc.kind}"
            if not item.adjudicated:
                if plan[query_id] == "seeded_sample":
                    accept_agreed(item)
                    audits["sampled_missing"] += 1
                else:
                    item.unresolved = True
                    audits["mandatory_missing"] += 1
        else:
            accept_agreed(item)
    return {"items": items, "counts": counts, "audits": audits, "agreement": supplement_agreement(items.values())}


def supplement_agreement(items: Sequence[Supplement] | Any) -> dict[str, Any]:
    from learnloop.experiments.contextual_embeddings.metrics import cohen_kappa

    items = list(items)
    pairs = [(item.passes[0][unit], item.passes[1][unit]) for item in items for unit in item.candidates
             if unit in item.passes[0] and unit in item.passes[1]]
    return {"agreement": cohen_kappa(pairs, RELEVANCE_ORDER) if pairs else {"kappa": None, "n": 0},
            "adjudicated": sum(1 for item in items if item.adjudicated),
            "unresolved": sum(1 for item in items if item.unresolved)}


def merge(snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], labels: Mapping[str, QuestionLabels],
          items: Mapping[str, Supplement]) -> dict[str, int]:
    """Fold accepted supplementary labels into E0's (in place); returns counts."""

    counts = {"labels_added": 0, "sets_added": 0, "made_answerable": 0, "unresolved_left_unknown": 0}
    by_id = {question.query_id: question for question in questions}
    for query_id, item in items.items():
        if item.unresolved:
            counts["unresolved_left_unknown"] += 1
            continue
        target = labels[query_id]
        for unit, value in item.final.items():
            if unit not in target.final:
                target.final[unit] = value
                counts["labels_added"] += 1
        new_sets = [chosen for chosen in item.final_sets if chosen not in set(target.final_sets)]
        if new_sets:
            if not target.final_sets:
                counts["made_answerable"] += 1
            target.final_sets = [*target.final_sets, *new_sets]
            target.answerable = True
            counts["sets_added"] += len(new_sets)
        by_id[query_id].evidence_sets = evidence_sets_from_labels(target, snapshot)
    return counts
