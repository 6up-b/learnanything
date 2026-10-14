"""``learnloop grading method-phrasing``: criteria phrased by method, and their repairs.

Owner rule 2026-10-13: a rubric criterion names the FACT a step establishes,
not the METHOD used; a method is required only when the item's target IS that
method, and then the item's own statement says so ("Use {method} in your
answer.", ``PracticeItem.required_method``). This report reads the existing
items' criteria against the rule and drafts repairs; it rewrites nothing.

**The judge** (the report says which ran, ``judge.kind``):

1. **the Decider** (``decider``): one typed ``choice`` question per criterion
   (fact / method), on ``ai.routing.rubric_phrasing_judge`` when it names a
   decider profile, or the code-default ``openrouter_decider`` profile when
   the route is unset and that profile is ready;
2. else **the LLM judge** (``llm``): one structured call per item on the same
   route (a chat profile, or ``ai.active_provider`` when unset) that also
   writes each method-phrased criterion's fact phrasing;
3. else **the conservative heuristic** (``heuristic``,
   :func:`learnloop.vault.required_method.method_phrase`): an explicit method
   verb with a method noun. It misses criteria that presuppose a method
   without naming it ("computes each 2x2 minor").

``--judge`` forces one. Every Decider and LLM verdict is appended to
``judgment_ledger`` (task ``rubric_method_phrasing``); every paid request is
admitted against the caps before it is sent and leaves a receipt.

**The repairs** (``--propose``) go through the normal proposal/confirm path:
one ``update`` proposal per item (``learnloop proposals ...`` lists, accepts or
rejects it; an update is never auto-applied), purpose
``rubric_phrasing_repair``. For each method-phrased criterion either

* **add the required method**: the item's target really is that method (its
  learning object's concept is a ``procedure``, or one of its facets is a
  ``procedure_contract``, and the criterion's method names it): the proposal
  sets ``required_method`` (that method, this criterion) and appends the
  explicit instruction to the prompt; or
* **rephrase by fact**: the criterion's new description names the fact it
  establishes: the LLM judge's rewrite, else the LLM route's rewrite of the
  flagged criteria (when the Decider judged), else a deterministic DRAFT that
  strips the method clause (labelled ``deterministic_draft``: edit it before
  accepting).

No practised item is rewritten silently: nothing is applied until the owner
accepts the proposal. An accepted repair changes the item's rubric (and
prompt) hash, so its next presentation snapshots a new assessment contract;
attempts already graded keep the contract they were graded against.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from collections import Counter
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Sequence

from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendCaps
from learnloop.ai.transport import execute_structured_operation, render_structured_prompt
from learnloop.clock import Clock, utc_now_iso
from learnloop.config.schema import DEFAULT_DECIDER_PROVIDER
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.diagnosis.offline_review.spend import ReviewSpend, RouteInfo
from learnloop.diagnosis.recurrence.judging import receipt_sink
from learnloop.ids import new_ulid
from learnloop.vault.models import LoadedVault, PracticeItem
from learnloop.vault.paths import VaultPaths
from learnloop.vault.required_method import (
    CRITERIA_BY_FACT_GUIDANCE,
    MethodTarget,
    best_target,
    ensure_method_instruction,
    method_phrase,
    method_targets,
    names_match,
    prompt_states_method,
)

REPORT_VERSION = "method-phrasing-report-v1"
JUDGE_PROMPT_VERSION = "rubric-phrasing-judge-v1"
DECIDER_QUESTION_SET = "rubric-phrasing-decider-v1"
LEDGER_TASK = "rubric_method_phrasing"
LEDGER_LEFT_KIND = "rubric_criterion"
PROPOSAL_PURPOSE = "rubric_phrasing_repair"
RECEIPT_OWNER_KIND = "rubric_phrasing_report"
ROUTE = "rubric_phrasing_judge"
DECIDER_ROUTE = "rubric_phrasing_decider"
LLM_PURPOSE = "rubric_phrasing_judgment"
JudgeKind = Literal["decider", "llm", "heuristic"]
JUDGE_CHOICES = ("auto", "decider", "llm", "heuristic")
#: The Decider's question per criterion.
DECIDER_OPTIONS = {
    "fact": "It names a fact or result a step establishes; any valid method that establishes it meets it.",
    "method": "It names or presupposes a particular method, so a correct answer by another valid method fails it as written.",
}
#: A Decider answer counts as method phrasing at this probability or more.
DECIDER_METHOD_THRESHOLD = 0.5
#: Tokens one Decider question adds to the state (instructions and options).
DECIDER_QUESTION_TOKENS = 120
LLM_OUTPUT_TOKENS = 2_000


def default_caps(items: int) -> SpendCaps:
    """Two requests per item at most (a reading and a rewrite), and $0.50."""

    calls = max(1, 2 * items)
    return SpendCaps(max_candidates=0, max_pairs=0, max_retries=max(4, items), max_calls=calls,
                     max_total_tokens=calls * 20_000, max_estimated_usd=0.50)


def _estimate_tokens(text: str) -> int:
    return (len(text.encode("utf-8")) + 3) // 4


# -- the LLM judge's contract -------------------------------------------------------


class CriterionPhrasingReading(WireModel):
    criterion_id: str
    phrased_by: Literal["fact", "method"]
    method: str | None = Field(default=None, description="The method the criterion names or presupposes, when phrased by method.")
    fact_phrasing: str | None = Field(
        default=None,
        description="When phrased by method: the criterion rewritten to name the fact the step establishes, "
        "same scope, any valid method able to meet it. Null otherwise.",
    )


class RubricPhrasingReading(WireModel):
    criteria: list[CriterionPhrasingReading] = Field(default_factory=list)


_JUDGE_TASK = (
    "Read each rubric criterion of ONE practice item against this rule. "
    + CRITERIA_BY_FACT_GUIDANCE
    + " For each criterion in `criteria` (skip none, invent none) return `phrased_by`: `fact` when it "
    "names a fact or result a step establishes (any valid route that establishes it can meet it), "
    "`method` when it names or presupposes a particular method so that a correct answer by another "
    "valid method fails it as written (for example 'uses cofactor expansion', 'computes each 2x2 "
    "minor' on a determinant item, 'by the complement rule'). A criterion listed in "
    "`required_method.criterion_ids` grades use of the item's required method by design: read it as "
    "`fact`. For a `method` criterion, name the method in `method` and write `fact_phrasing`: the same "
    "criterion naming the fact its step establishes, with the same scope, in one sentence."
)


def judge_prompt(item: PracticeItem, rubric: Any, targets: Sequence[MethodTarget]) -> str:
    method = item.required_method
    context = {
        "practice_item_id": item.id,
        "prompt": item.prompt,
        "expected_answer": item.expected_answer,
        "criteria": [{"id": c.id, "description": c.description, "points": c.points} for c in rubric.criteria],
        "required_method": method.model_dump(mode="json") if method is not None else None,
        "required_method_targets": [target.as_context() for target in targets],
    }
    return render_structured_prompt(
        "learnloop rubric phrasing judgment", JUDGE_PROMPT_VERSION, {"task": _JUDGE_TASK, "context": context},
    )


def decider_state(item: PracticeItem, rubric: Any) -> str:
    """What the Decider reads: the item and its criteria."""

    lines = [
        "A practice item and its grading rubric. Rule: a rubric criterion should name the FACT a step "
        "establishes, not the METHOD used to establish it.",
        f"Item prompt: {item.prompt}",
        f"Expected answer: {item.expected_answer if isinstance(item.expected_answer, str) else json.dumps(item.expected_answer, sort_keys=True)}",
        "Criteria:",
    ]
    lines += [f"- {c.id}: {c.description}" for c in rubric.criteria]
    return "\n".join(lines)


def decider_question(criterion: Any) -> Any:
    from learnloop.ai.decisions import ChoiceQuestion

    return ChoiceQuestion(
        instructions=(
            f"Criterion {criterion.id}: \"{criterion.description}\". Is it phrased by the fact a step "
            "establishes, or by the method used to establish it?"
        ),
        options=dict(DECIDER_OPTIONS),
    )


# -- the judge's route --------------------------------------------------------------


@dataclass
class JudgeRoute:
    kind: JudgeKind
    provider: str | None = None
    model: str | None = None
    client: Any | None = None
    reason: str = ""
    #: The LLM client that writes fact phrasings for a Decider's flags, if any.
    writer: Any | None = None
    tried: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "provider": self.provider, "model": self.model, "reason": self.reason,
                "rewrites": "llm" if (self.kind == "llm" or self.writer is not None) else "deterministic_draft",
                "tried": list(self.tried)}


def _route_names(vault: LoadedVault) -> tuple[str | None, str | None]:
    """(decider profile, chat profile) the judge route names, or would default to."""

    from learnloop.ai.routing import is_decider_profile

    configured = (getattr(vault.config.ai.routing, ROUTE, None) or "").strip() or None
    if configured is None:
        return DEFAULT_DECIDER_PROVIDER, None
    if is_decider_profile(vault.config, configured):
        return configured, None
    return None, configured


def _ready(vault: LoadedVault, name: str | None) -> Any | None:
    from learnloop.ai.routing import ready_client_for_task

    resolved = ready_client_for_task(vault.root, vault.config, ROUTE, explicit=name)
    return resolved.client if resolved.ready else None


def resolve_judge(vault: LoadedVault, requested: str = "auto", *, clients: Mapping[str, Any] | None = None) -> JudgeRoute:
    """Decider, else the LLM judge, else the heuristic (or the one ``requested``)."""

    if requested not in JUDGE_CHOICES:
        raise ValueError(f"--judge must be one of {', '.join(JUDGE_CHOICES)}")
    injected = dict(clients or {})
    tried: list[dict[str, Any]] = []
    if requested == "heuristic":
        return JudgeRoute("heuristic", reason="requested", tried=tried)
    decider_name, chat_name = _route_names(vault)
    if requested in ("auto", "decider"):
        client = injected.get("decider")
        if client is None and decider_name is not None and "decider" not in injected:
            client = _ready(vault, decider_name)
        tried.append({"judge": "decider", "provider": decider_name, "ready": client is not None})
        if client is not None:
            writer = injected.get("llm")
            if writer is None and "llm" not in injected:
                writer = _ready(vault, chat_name)
            return JudgeRoute("decider", provider=getattr(client, "provider_name", None) or decider_name,
                              model=getattr(client, "model", None), client=client,
                              reason="requested" if requested == "decider" else "the Decider is ready",
                              writer=writer, tried=tried)
        if requested == "decider":
            raise RuntimeError(f"the Decider ({decider_name or 'no decider profile on ai.routing.rubric_phrasing_judge'}) is not ready")
    client = injected.get("llm")
    if client is None and "llm" not in injected:
        client = _ready(vault, chat_name)
    tried.append({"judge": "llm", "provider": chat_name or "ai.active_provider", "ready": client is not None})
    if client is not None:
        return JudgeRoute("llm", provider=getattr(client, "provider_name", None) or chat_name,
                          model=getattr(client, "model", None), client=client,
                          reason="requested" if requested == "llm" else "no Decider is ready; the LLM judge is",
                          tried=tried)
    if requested == "llm":
        raise RuntimeError("the LLM judge route (ai.routing.rubric_phrasing_judge or ai.active_provider) is not ready")
    return JudgeRoute("heuristic", reason="neither the Decider nor an LLM judge is ready", tried=tried)


# -- readings -----------------------------------------------------------------------


@dataclass
class CriterionReading:
    item_id: str
    criterion_id: str
    description: str
    phrased_by: Literal["fact", "method"]
    judge: JudgeKind
    method: str | None = None
    fact_phrasing: str | None = None
    rewrite: str | None = None  # llm | deterministic_draft
    probability: float | None = None
    judgment_id: str | None = None
    #: When the Decider flagged it, the LLM writer's own reading (``fact``
    #: means the two judges disagree; its repair is then only a draft).
    writer_reading: str | None = None
    #: The item's capability, for the owner's context (a method-selection
    #: item measures the choice, so its criteria deserve a careful look).
    capability: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items() if value is not None}


def candidate_items(vault: LoadedVault, item_ids: Sequence[str] | None = None) -> list[PracticeItem]:
    """Active items with their own rubric (the default rubrics are doctor's), sorted."""

    wanted = set(item_ids or ())
    unknown = sorted(wanted - set(vault.practice_items))
    if unknown:
        raise ValueError(f"unknown practice item(s): {', '.join(unknown)}")
    return [
        item for item in sorted(vault.practice_items.values(), key=lambda entry: entry.id)
        if item.status == "active" and item.grading_rubric is not None and item.grading_rubric.criteria
        and (not wanted or item.id in wanted)
    ]


def _required_ids(item: PracticeItem) -> set[str]:
    return set(item.required_method.criterion_ids) if item.required_method is not None else set()


def heuristic_readings(item: PracticeItem) -> list[CriterionReading]:
    out = []
    for criterion in item.grading_rubric.criteria:
        phrase = None if criterion.id in _required_ids(item) else method_phrase(criterion.description)
        out.append(CriterionReading(
            item.id, criterion.id, criterion.description, "method" if phrase else "fact", "heuristic",
            method=phrase.method if phrase else None,
        ))
    return out


_THIRD = {"do": "does", "go": "goes", "have": "has"}


def _third_person(verb: str) -> str:
    lower = verb.lower()
    if lower in _THIRD:
        word = _THIRD[lower]
    elif lower.endswith(("s", "sh", "ch", "x", "z")):
        word = lower + ("es" if not lower.endswith("s") else "")
    elif lower.endswith("y") and len(lower) > 2 and lower[-2] not in "aeiou":
        word = lower[:-1] + "ies"
    else:
        word = lower + "s"
    return word[:1].upper() + word[1:]


def deterministic_fact_draft(description: str) -> str:
    """A DRAFT fact phrasing: the criterion with its method clause removed.

    "Uses X to compute det(A)." -> "Computes det(A) (any valid method)."; "Finds
    P by the complement rule." -> "Finds P (any valid method)."; otherwise the
    description with "Any valid method that establishes this earns it."
    appended. Always labelled a draft for the owner to edit.
    """

    text = " ".join(str(description or "").split()).rstrip(".")
    phrase = method_phrase(text)
    suffix = " (any valid method)."
    if phrase is not None:
        lead = re.match(
            r"^(?:uses?|using|applies|apply|applying|employs?)\s+.+?\s+to\s+(?P<verb>[A-Za-z]+)\b(?P<rest>.*)$",
            text, re.IGNORECASE,
        )
        if lead is not None and lead.group("verb").lower() not in {"the", "a", "an"}:
            return _third_person(lead.group("verb")) + lead.group("rest").rstrip(" ,") + suffix
        trailing = re.match(
            r"^(?P<head>.+?)\s*,?\s+(?:by|via|using|with)\s+(?:the\s+|a\s+|an\s+)?" + re.escape(phrase.method)
            + r"(?P<tail>.*)$", text, re.IGNORECASE,
        )
        if trailing is not None and len(trailing.group("head").split()) >= 2:
            tail = trailing.group("tail").strip(" ,")
            return trailing.group("head").rstrip(" ,") + (f" {tail}" if tail else "") + suffix
    return f"{text}. Any valid method that establishes this earns it."


@dataclass
class _Budget:
    """Route registration and admission over one review spend."""

    spend: Any

    def register_llm(self, client: Any) -> None:
        if ROUTE not in self.spend.routes:
            self.spend.register(ROUTE, client)

    def register_decider(self, client: Any) -> None:
        if DECIDER_ROUTE in self.spend.routes:
            return
        settings = getattr(client, "settings", None)
        price = getattr(settings, "price_per_million_input", None)
        self.spend.routes[DECIDER_ROUTE] = RouteInfo(
            DECIDER_ROUTE, getattr(client, "provider_name", None), getattr(client, "model", None), "metered",
            float(price) if price is not None else None, "listed_input_price" if price is not None else "unknown", 0,
        )


def _input_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _ledger(repository: Repository, readings: Sequence[CriterionReading], *, judge: JudgeRoute,
            prompt_version: str, input_hash: str, now: str) -> None:
    from learnloop.db.stores.judgments import append_judgment

    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            for reading in readings:
                verdict = {"phrased_by": reading.phrased_by, "method": reading.method,
                           "fact_phrasing": reading.fact_phrasing}
                reading.judgment_id = append_judgment(
                    connection, task=LEDGER_TASK, left_kind=LEDGER_LEFT_KIND,
                    left_id=f"{reading.item_id}#{reading.criterion_id}", judge=judge.kind,
                    judge_model=str(judge.model or "unknown"), prompt_version=prompt_version,
                    input_hash=input_hash, verdict=json.dumps(verdict, sort_keys=True),
                    score=reading.probability, rationale=(
                        f"{judge.kind}: {reading.phrased_by}"
                        + (f" ({reading.method})" if reading.method else "")
                    ),
                    created_at=now,
                )


def llm_readings(item: PracticeItem, targets: Sequence[MethodTarget], client: Any, budget: _Budget,
                 *, only: set[str] | None = None) -> tuple[list[CriterionReading], str]:
    """One structured call: every criterion's phrasing (and the rewrites)."""

    prompt = judge_prompt(item, item.grading_rubric, targets)
    budget.register_llm(client)
    with budget.spend.collector.observing():
        with budget.spend.request(ROUTE, LLM_PURPOSE, input_tokens=_estimate_tokens(prompt),
                                  output_tokens=LLM_OUTPUT_TOKENS):
            result = execute_structured_operation(
                client, purpose=LLM_PURPOSE, prompt=prompt, result_model=RubricPhrasingReading, isolated=True,
            )
    by_id = {row.criterion_id: row for row in result.criteria}
    readings: list[CriterionReading] = []
    for criterion in item.grading_rubric.criteria:
        if only is not None and criterion.id not in only:
            continue
        row = by_id.get(criterion.id)
        if row is None or criterion.id in _required_ids(item):
            readings.append(CriterionReading(item.id, criterion.id, criterion.description, "fact", "llm"))
            continue
        method = row.phrased_by == "method"
        phrasing = " ".join(str(row.fact_phrasing or "").split()) or None
        readings.append(CriterionReading(
            item.id, criterion.id, criterion.description, row.phrased_by, "llm",
            method=(row.method or None) if method else None,
            fact_phrasing=phrasing if method else None, rewrite="llm" if method and phrasing else None,
        ))
    return readings, _input_hash({"prompt": prompt})


def decider_readings(item: PracticeItem, client: Any, budget: _Budget) -> tuple[list[CriterionReading], str]:
    """One Decider request: a choice question per criterion."""

    criteria = [criterion for criterion in item.grading_rubric.criteria if criterion.id not in _required_ids(item)]
    state = decider_state(item, item.grading_rubric)
    readings = [
        CriterionReading(item.id, criterion.id, criterion.description, "fact", "decider")
        for criterion in item.grading_rubric.criteria if criterion.id in _required_ids(item)
    ]
    if not criteria:
        return readings, _input_hash({"state": state})
    questions = {f"c{index}": decider_question(criterion) for index, criterion in enumerate(criteria)}
    budget.register_decider(client)
    tokens = _estimate_tokens(state) + DECIDER_QUESTION_TOKENS * len(questions)
    with budget.spend.collector.observing():
        with budget.spend.request(DECIDER_ROUTE, LLM_PURPOSE, input_tokens=tokens, output_tokens=0):
            result = client.decide(state, questions, purpose=LLM_PURPOSE)
    for index, criterion in enumerate(criteria):
        answer = result.answers[f"c{index}"]
        probabilities = {str(key): float(value) for key, value in dict(getattr(answer, "probabilities", {}) or {}).items()}
        p_method = probabilities.get("method")
        method = (p_method if p_method is not None else (1.0 if answer.choice == "method" else 0.0)) >= DECIDER_METHOD_THRESHOLD
        phrase = method_phrase(criterion.description) if method else None
        readings.append(CriterionReading(
            item.id, criterion.id, criterion.description, "method" if method else "fact", "decider",
            method=phrase.method if phrase else None, probability=round(p_method, 4) if p_method is not None else None,
        ))
    order = {criterion.id: index for index, criterion in enumerate(item.grading_rubric.criteria)}
    readings.sort(key=lambda reading: order.get(reading.criterion_id, 0))
    return readings, _input_hash({"state": state, "questions": sorted(questions), "set": DECIDER_QUESTION_SET})


# -- repairs ------------------------------------------------------------------------


def _source_statement(item: PracticeItem) -> bool:
    """A textbook exercise's verbatim stem: never rewritten."""

    return getattr(item, "canonical_exercise", None) is not None or item.provenance.origin == "canonical_extract"


def _teach_back(item: PracticeItem) -> bool:
    return item.teach_back_source is not None or item.practice_mode == "teach_back"


def repair_plan(vault: LoadedVault, item: PracticeItem, readings: Sequence[CriterionReading]) -> dict[str, Any] | None:
    """One item's repair: the updated rubric (and prompt and required method).

    Each method-phrased criterion becomes the item's required method's
    criterion when the item's target really is that method (by metadata, and
    the criterion's method names the target: ``names_match``), else is
    rephrased by fact. At most one required method per item; an item that
    already has one only gains criteria naming that method. The required
    method takes the target's own name (or alias). A teach-back item never
    gains one (it explains, it does not execute), and a textbook exercise
    only when its verbatim statement already names the method (the
    statement is never rewritten).
    """

    flagged = [reading for reading in readings if reading.phrased_by == "method"]
    if not flagged:
        return None
    targets = [] if _teach_back(item) else method_targets(
        vault, learning_object_id=item.learning_object_id, facet_ids=item.evidence_facets,
        capability=item.capability,
    )
    if _source_statement(item):
        # Only names the verbatim statement already states, so the repair
        # never appends an instruction to the book's text.
        stated_targets = []
        for target in targets:
            stated = [name for name in target.names() if prompt_states_method(item.prompt, name)]
            if stated:
                stated_targets.append(dataclasses.replace(target, name=stated[0], aliases=tuple(stated[1:])))
        targets = stated_targets
    existing = item.required_method
    method_name: str | None = existing.name if existing is not None else None
    method_target: MethodTarget | None = best_target(method_name, targets) if method_name else None
    method_criteria: list[str] = list(existing.criterion_ids) if existing is not None else []
    actions: list[dict[str, Any]] = []
    rubric = item.grading_rubric.model_dump(mode="json", exclude_none=True)
    for reading in flagged:
        named = reading.method or ""
        target = best_target(named, targets) if named else None
        if target is not None and (method_name is None or names_match(named, method_name)):
            if method_name is None:
                # The target's own name (or alias), never a model's long paraphrase.
                method_name, method_target = target.matching_name(named) or target.name, target
            if reading.criterion_id not in method_criteria:
                method_criteria.append(reading.criterion_id)
            actions.append({"criterion_id": reading.criterion_id, "action": "add_required_method",
                            "method": method_name, "target": target.as_context()})
            continue
        if reading.fact_phrasing:
            new, rewrite = reading.fact_phrasing, reading.rewrite or "llm"
        else:
            new, rewrite = deterministic_fact_draft(reading.description), "deterministic_draft"
        for criterion in rubric["criteria"]:
            if criterion["id"] == reading.criterion_id:
                criterion["description"] = new
        action = {"criterion_id": reading.criterion_id, "action": "rephrase_by_fact",
                  "from": reading.description, "to": new, "rewrite": rewrite}
        if reading.writer_reading == "fact":
            # The Decider flagged it; the LLM writer read it as a fact: a draft
            # the owner should look at before accepting (or reject).
            action["judges_disagree"] = True
        actions.append(action)
    payload: dict[str, Any] = {"id": item.id, "learning_object_id": item.learning_object_id, "grading_rubric": rubric}
    if method_name is not None and method_criteria and method_target is not None and (
        existing is None or method_criteria != list(existing.criterion_ids)
    ):
        payload["required_method"] = {"name": method_name, "criterion_ids": method_criteria, **method_target.link()}
        prompt = ensure_method_instruction(item.prompt, method_name)
        if prompt != item.prompt:
            payload["prompt"] = prompt
    return {"item_id": item.id, "actions": actions, "payload": payload}


def persist_repairs(vault: LoadedVault, repository: Repository, plans: Sequence[Mapping[str, Any]], *,
                    judge: JudgeRoute, clock: Clock | None = None) -> str | None:
    """One pending proposal batch (never auto-applied): an update per item."""

    if not plans:
        return None
    now = utc_now_iso(clock)
    agent_run_id = repository.insert_agent_run({
        "id": new_ulid(), "purpose": PROPOSAL_PURPOSE, "model": judge.model,
        "provider": judge.provider or judge.kind, "prompt_template": PROPOSAL_PURPOSE,
        "prompt_version": JUDGE_PROMPT_VERSION if judge.kind == "llm" else (
            DECIDER_QUESTION_SET if judge.kind == "decider" else REPORT_VERSION),
        "input_context_hash": _input_hash([plan["payload"] for plan in plans]), "output_schema": "practice_item update",
        "started_at": now, "completed_at": now, "status": "completed",
    })
    rows = []
    for plan in plans:
        rows.append({
            "id": new_ulid(), "client_item_id": f"method_phrasing:{plan['item_id']}",
            "item_type": "practice_item", "operation": "update",
            "target_entity_type": "practice_item", "target_entity_id": plan["item_id"],
            "payload": plan["payload"], "source_ref_ids": [], "audit": None, "decision": "pending",
            "validation_status": "valid", "validation_errors": [], "created_at": now, "updated_at": now,
        })
    summary = (
        f"Rubric criteria phrased by method ({judge.kind} judge): {len(plans)} item(s). Each update rephrases a "
        "criterion by the fact it establishes, or makes the method the item's required method with the explicit "
        "instruction when its target is that method. Review and accept or reject; nothing is applied until then."
    )
    return repository.persist_proposal_batch({
        "id": new_ulid(), "agent_run_id": agent_run_id, "purpose": PROPOSAL_PURPOSE, "source_refs": [],
        "summary": summary, "created_at": now, "updated_at": now,
    }, rows)


# -- the run ------------------------------------------------------------------------


def _attempted_items(repository: Repository, item_ids: Sequence[str]) -> set[str]:
    if not item_ids:
        return set()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        marks = ",".join("?" for _ in item_ids)
        return {str(row[0]) for row in connection.execute(
            f"SELECT DISTINCT practice_item_id FROM practice_attempts WHERE practice_item_id IN ({marks})",
            list(item_ids),
        )}


def run_method_phrasing(
    vault: LoadedVault,
    *,
    judge: str = "auto",
    item_ids: Sequence[str] | None = None,
    propose: bool = False,
    dry_run: bool = False,
    caps: SpendCaps | None = None,
    price_per_million: float | None = None,
    clients: Mapping[str, Any] | None = None,
    cancelled: Callable[[], bool] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Read the items' criteria, report the method-phrased ones, optionally propose repairs."""

    items = candidate_items(vault, item_ids)
    caps = caps or default_caps(len(items))
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    criteria = sum(len(item.grading_rubric.criteria) for item in items)
    report: dict[str, Any] = {
        "version": REPORT_VERSION, "status": "dry_run" if dry_run else "pending",
        "items": len(items), "criteria": criteria, "caps": caps.as_dict(),
    }
    if dry_run:
        decider_name, chat_name = _route_names(vault)
        plan = [] if judge == "heuristic" else [
            *([{"judge": "decider", "provider": decider_name, "requests": len(items),
                "input_tokens": sum(_estimate_tokens(decider_state(item, item.grading_rubric))
                                    + DECIDER_QUESTION_TOKENS * len(item.grading_rubric.criteria) for item in items)}]
              if judge in ("auto", "decider") and decider_name else []),
            *([{"judge": "llm", "provider": chat_name or "ai.active_provider", "requests": len(items),
                "input_tokens": sum(_estimate_tokens(judge_prompt(item, item.grading_rubric, ())) for item in items),
                "output_tokens": LLM_OUTPUT_TOKENS * len(items)}] if judge in ("auto", "llm") else []),
        ]
        report["judge_plan"] = [*plan, {"judge": "heuristic", "requests": 0}]
        report["note"] = ("auto tries the Decider, then the LLM judge, then the heuristic, whichever is ready first; "
                          "a dry run builds no client and sends nothing")
        heuristic = [reading for item in items for reading in heuristic_readings(item) if reading.phrased_by == "method"]
        report["heuristic_flags"] = [reading.as_dict() for reading in heuristic]
        return report

    route = resolve_judge(vault, judge, clients=clients)
    report["judge"] = route.as_dict()
    repository = Repository(sqlite_path)
    run_id = new_ulid()
    spend = ReviewSpend(caps, cancelled=cancelled, price_per_million=price_per_million, config=vault.config)
    spend.collector.sink = receipt_sink(repository, owner_kind=RECEIPT_OWNER_KIND, owner_id=run_id)
    budget = _Budget(spend)
    now = utc_now_iso(clock)
    readings: list[CriterionReading] = []
    failures: Counter = Counter()
    for item in items:
        if cancelled is not None and cancelled():
            break
        targets = method_targets(vault, learning_object_id=item.learning_object_id,
                                 facet_ids=item.evidence_facets, capability=item.capability)
        if route.kind == "heuristic":
            readings.extend(heuristic_readings(item))
            continue
        try:
            if route.kind == "llm":
                item_readings, input_hash = llm_readings(item, targets, route.client, budget)
                _ledger(repository, item_readings, judge=route, prompt_version=JUDGE_PROMPT_VERSION,
                        input_hash=input_hash, now=now)
            else:
                item_readings, input_hash = decider_readings(item, route.client, budget)
                _ledger(repository, item_readings, judge=route, prompt_version=DECIDER_QUESTION_SET,
                        input_hash=input_hash, now=now)
                flagged = {reading.criterion_id for reading in item_readings if reading.phrased_by == "method"}
                if flagged and route.writer is not None:
                    # The Decider judged; the LLM route writes the fact phrasings
                    # (and names the method) of the criteria it flagged.
                    rewrites, _ = llm_readings(item, targets, route.writer, budget, only=flagged)
                    by_id = {row.criterion_id: row for row in rewrites}
                    for reading in item_readings:
                        row = by_id.get(reading.criterion_id)
                        if reading.phrased_by == "method" and row is not None:
                            reading.writer_reading = row.phrased_by
                            reading.method = row.method or reading.method
                            reading.fact_phrasing = row.fact_phrasing
                            reading.rewrite = "llm" if row.fact_phrasing else None
        except Exception as exc:  # noqa: BLE001 - one item's failure is counted, never a crashed run
            if type(exc).__name__ in {"SpendLimitExceeded", "SpendCancelled", "AIInterrupted"}:
                raise
            failures[type(exc).__name__] += 1
            report.setdefault("failed_items", []).append({"item_id": item.id, "error": type(exc).__name__})
            continue
        readings.extend(item_readings)
    capabilities = {item.id: item.capability for item in items}
    for reading in readings:
        reading.capability = capabilities.get(reading.item_id)
    flagged = [reading for reading in readings if reading.phrased_by == "method"]
    attempted = _attempted_items(repository, sorted({reading.item_id for reading in flagged}))
    plans = []
    for item in items:
        plan = repair_plan(vault, item, [reading for reading in readings if reading.item_id == item.id])
        if plan is not None:
            plan["practised"] = item.id in attempted
            plans.append(plan)
    report.update(
        status="complete",
        flagged=[reading.as_dict() for reading in flagged],
        flagged_items=len({reading.item_id for reading in flagged}),
        repairs=plans,
        failures=dict(failures),
        spend=spend.summary(),
    )
    if propose:
        report["proposal_id"] = persist_repairs(vault, repository, plans, judge=route, clock=clock)
    return report


def write_report(report: Mapping[str, Any], output_dir: Path) -> dict[str, str]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "method-phrasing.json"
    json_path.write_text(json.dumps(report, sort_keys=True, indent=2, default=str) + "\n", encoding="utf-8")
    return {"json": str(json_path)}


__all__ = [
    "CriterionPhrasingReading",
    "CriterionReading",
    "DECIDER_QUESTION_SET",
    "JUDGE_PROMPT_VERSION",
    "JudgeRoute",
    "LEDGER_TASK",
    "PROPOSAL_PURPOSE",
    "REPORT_VERSION",
    "RubricPhrasingReading",
    "candidate_items",
    "decider_readings",
    "default_caps",
    "deterministic_fact_draft",
    "heuristic_readings",
    "judge_prompt",
    "llm_readings",
    "persist_repairs",
    "repair_plan",
    "resolve_judge",
    "run_method_phrasing",
    "write_report",
]
