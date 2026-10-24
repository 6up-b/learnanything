"""``learnloop grading method-phrasing``: criteria phrased by method, and their repairs.

Owner rule 2026-10-13: a rubric criterion names the FACT a step establishes,
not the METHOD used; a method is required only when the item's target IS that
method, and then the item's own statement says so ("Use {method} in your
answer.", ``PracticeItem.required_method``). This report reads the existing
items' criteria against the rule and drafts repairs; it rewrites nothing.

**The judge** (the report says which ran, ``judge.kind``):

1. **the Decider** (``decider``): one typed ``choice`` question per criterion
   (fact / method), on ``ai.routing.rubric_phrasing_judge`` when it names a
   decider profile; when the route is unset, the Tier-1 Decider (the profile
   ``ai.routing.tier1_decider`` names, else the code-default
   ``openrouter_decider`` profile) when that profile is ready;
2. else **the LLM judge** (``llm``): one structured call per item on the
   chat route (the route's chat profile; when the route is unset or names a
   decider, the serving chat provider: ``LEARNLOOP_AI_PROVIDER``, else
   ``ai.active_provider``) that also writes each method-phrased criterion's
   fact phrasing;
3. else **the conservative heuristic** (``heuristic``,
   :func:`learnloop.vault.required_method.method_phrase`): an explicit method
   verb with a method noun. It misses criteria that presuppose a method
   without naming it ("computes each 2x2 minor").

``--judge`` forces one. After the Decider, the same chat route (the
**writer**, resolved apart from the judge and required to serve isolated
structured completions, so a Decider is never the writer; review F4) reads the
flagged items again and writes the fact phrasings. A reading must cover
exactly the item's criteria, once each; anything else is an incomplete
judgment, never a fact verdict (review F5). Every Decider and LLM verdict,
the writer's included (its own model, prompt version and input hash; review
F6), is appended to ``judgment_ledger`` (task ``rubric_method_phrasing``); a
required method's own criteria are fact by design and are not judged. Every
paid request is admitted against the caps before it is sent and leaves a
receipt; a writer that fails or is refused leaves the Decider's paid flags
with labelled deterministic drafts. ``--dry-run`` plans the classification
and every possible rewrite from configuration alone, with their estimated
cost (review F7).

**The repairs** (``--propose``) go through the normal proposal/confirm path:
one ``update`` proposal per item (``learnloop proposals ...`` lists, accepts or
rejects it; an update is never auto-applied), purpose
``rubric_phrasing_repair``. For each method-phrased criterion either

* **add the required method**: the item's target really is that method (its
  learning object's concept is a ``procedure``, or one of its facets is a
  ``procedure_contract``, and the criterion's method names it) and its
  prompt is not a source statement: the proposal sets ``required_method``
  (that method, this criterion), whose instruction ("Use {name} in your
  answer.") is then rendered after the statement wherever the item is shown
  or sent (the statement itself is never edited); or
* **rephrase by fact**: the criterion's new description names the fact it
  establishes: the LLM judge's rewrite, else the LLM route's rewrite of the
  flagged criteria (when the Decider judged), else a deterministic DRAFT that
  strips the method clause (labelled ``deterministic_draft``: edit it before
  accepting).

No practised item is rewritten silently: nothing is applied until the owner
accepts the proposal. Each update carries the item's content hash
(``expected_target_hash``): an item changed after the report (a criterion's
weight, a dependency) is refused at acceptance, never overwritten with the
stale rubric; run the report again (review F3). An accepted repair changes
the item's rubric (and required method) and so its assessment
contract: its next presentation snapshots a new one, and attempts already
graded keep the contract (and required method) they were graded against.
Nothing reads the prompt to decide a repair (redesign 2026-10-14), and
nothing writes it (round 3): the instruction is rendered from the field, an
advisory flag
labels a prompt that may negate it or leave it optional, and a source
statement never gains a required method here (rephrased by fact instead).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Sequence

from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendCaps, SpendEstimate, SpendLimitExceeded, is_subscription_transport
from learnloop.ai.transport import (
    ISOLATED_TURN,
    STRUCTURED_COMPLETION,
    execute_structured_operation,
    render_structured_prompt,
)
from learnloop.clock import Clock, utc_now_iso
from learnloop.config.schema import DECIDER_PROFILE_TYPE, DEFAULT_DECIDER_PROVIDER
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.diagnosis.offline_review.spend import ReviewSpend, RouteInfo
from learnloop.diagnosis.recurrence.judging import receipt_sink
from learnloop.ids import new_ulid
from learnloop.vault.models import LoadedVault, PracticeItem
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import vault_repository
from learnloop.vault.required_method import (
    CRITERIA_BY_FACT_GUIDANCE,
    MethodTarget,
    advisory_statement_flag,
    best_target,
    is_source_statement,
    method_phrase,
    method_targets,
    names_match,
)

REPORT_VERSION = "method-phrasing-report-v1"
#: v2 (review F14 reopened): the shared guidance it carries leaves the
#: instruction sentence to LearnLoop.
JUDGE_PROMPT_VERSION = "rubric-phrasing-judge-v2"
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
LLM_OUTPUT_TOKENS = 2_000


def default_caps(items: int) -> SpendCaps:
    """Two requests per item at most (a reading and a rewrite), and $0.50."""

    calls = max(1, 2 * items)
    return SpendCaps(max_candidates=0, max_pairs=0, max_retries=max(4, items), max_calls=calls,
                     max_total_tokens=calls * 20_000, max_estimated_usd=0.50)


def _estimate_tokens(text: str) -> int:
    """An upper bound on the input tokens of ``text``: its UTF-8 bytes (the
    PF convention, ``learnloop.ops.pf_calls.estimate_tokens``).

    Admission and the dry run both use it, so an estimate bounds what a
    request may cost. The earlier bytes/4 estimate under-ran the
    provider-reported usage on the 2026-10-13 live run on a linear-algebra
    copy (review F7): the Haiku 5.5 writer reported 1,638 input tokens per
    call against 783 estimated, the Decider 42,866 for 59 requests against
    26,377.
    """

    return len(text.encode("utf-8"))


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
    #: The profile the writer was resolved from.
    writer_provider: str | None = None
    tried: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        out = {"kind": self.kind, "provider": self.provider, "model": self.model, "reason": self.reason,
               "rewrites": "llm" if (self.kind == "llm" or self.writer is not None) else "deterministic_draft",
               "tried": list(self.tried)}
        if self.kind == "decider":
            out["writer"] = self.writer_provider if self.writer is not None else None
            out["writer_model"] = getattr(self.writer, "model", None) if self.writer is not None else None
        return out


def _route_names(vault: LoadedVault) -> tuple[str | None, str | None]:
    """(decider profile, chat profile) the judge route names, or would default to.

    An unset route defaults to the Tier-1 Decider (merge onto mvp-0.24's
    main): the profile ``ai.routing.tier1_decider`` names, else the
    code-default ``openrouter_decider`` profile, so the Decider is configured
    in one place, as every Tier-1 judgment resolves it."""

    from learnloop.ai.routing import is_decider_profile

    configured = (getattr(vault.config.ai.routing, ROUTE, None) or "").strip() or None
    if configured is None:
        tier1 = (getattr(vault.config.ai.routing, "tier1_decider", None) or "").strip()
        return tier1 or DEFAULT_DECIDER_PROVIDER, None
    if is_decider_profile(vault.config, configured):
        return configured, None
    return None, configured


def writer_name(vault: LoadedVault) -> str | None:
    """The chat profile that judges as the LLM judge and writes fact phrasings.

    The route's own chat profile when it names one; when it is unset or names
    a decider, the serving chat provider (``LEARNLOOP_AI_PROVIDER``, else
    ``ai.active_provider``), resolved apart from the judge so a Decider on the
    route is never the writer (review F4). A decider or embedding profile is
    never a writer (None).
    """

    from learnloop.ai.routing import is_generation_profile

    _decider, chat = _route_names(vault)
    name = chat or (os.environ.get("LEARNLOOP_AI_PROVIDER") or "").strip() or (
        vault.config.ai.active_provider or "").strip()
    if not name or not is_generation_profile(vault.config, name):
        return None
    return name


def writer_names(vault: LoadedVault) -> list[str]:
    """Every chat profile a run may write with, in the order it tries them
    (re-review F11): :func:`writer_name`, then ``ai.fallback_provider``
    exactly where :func:`_ready_writer` falls back to it (an unset route
    without an environment override and with a serving provider, as the task
    route resolves; a route naming a decider). A route naming a chat profile,
    an environment override on an unset route, and an unset route with no
    serving provider (empty or manual: the manual path) have no fallback
    writer.
    """

    from learnloop.ai.routing import MANUAL_PROVIDER, configured_fallback, is_generation_profile

    primary = writer_name(vault)
    names = [primary] if primary else []
    configured = (getattr(vault.config.ai.routing, ROUTE, None) or "").strip()
    _decider, chat = _route_names(vault)
    # Routing's one rule for the setting (review F6): never Codex, never a
    # silent metered fallback for the ChatGPT plan.
    fallback = configured_fallback(vault.config, primary) or ""
    if chat is not None or not fallback or fallback in names or fallback == MANUAL_PROVIDER:
        return names
    if not is_generation_profile(vault.config, fallback):
        return names
    if configured:
        names.append(fallback)
    elif not (os.environ.get("LEARNLOOP_AI_PROVIDER") or "").strip() and (
            vault.config.ai.active_provider or "").strip() not in {"", MANUAL_PROVIDER}:
        names.append(fallback)
    return names


def can_write(client: Any) -> bool:
    """Can ``client`` serve the writer's call (an isolated structured completion)?"""

    supports = getattr(client, "supports", None)
    return (
        client is not None
        and getattr(client, "provider_type", None) != DECIDER_PROFILE_TYPE
        and callable(supports)
        and bool(supports(STRUCTURED_COMPLETION))
        and bool(supports(ISOLATED_TURN))
    )


def _ready(vault: LoadedVault, name: str | None) -> Any | None:
    from learnloop.ai.routing import ready_client_for_task

    if name is None:
        return None
    resolved = ready_client_for_task(vault.root, vault.config, ROUTE, explicit=name)
    return resolved.client if resolved.ready else None


def _ready_writer(vault: LoadedVault, injected: Mapping[str, Any]) -> tuple[Any | None, str | None]:
    """(the writer client, its profile), or (None, profile) when none can write.

    An unset route resolves as the task route always did (the serving chat
    provider, with ``ai.fallback_provider``); a route naming a chat profile
    uses that profile; a route naming a decider uses the serving chat
    provider explicitly, then the fallback provider when that is not ready.
    """

    from learnloop.ai.routing import configured_fallback, is_generation_profile, ready_client_for_task

    name = writer_name(vault)
    if "llm" in injected:
        client = injected.get("llm")
    else:
        configured = (getattr(vault.config.ai.routing, ROUTE, None) or "").strip()
        _decider, chat = _route_names(vault)
        if not configured:
            resolved = ready_client_for_task(vault.root, vault.config, ROUTE)
            client = resolved.client if resolved.ready else None
        elif chat is not None:
            client = _ready(vault, chat)
        else:
            client = _ready(vault, name)
            # Routing's one rule for the setting (review F6).
            fallback = configured_fallback(vault.config, name) or ""
            if client is None and fallback and fallback != name and is_generation_profile(vault.config, fallback):
                client, name = _ready(vault, fallback), fallback
    if not can_write(client):
        return None, name
    return client, getattr(client, "provider_name", None) or name


def decider_profile_name(vault: LoadedVault) -> str | None:
    """The decider profile ``ai.routing.rubric_phrasing_judge`` names, or the
    Tier-1 Decider's (``ai.routing.tier1_decider``, else the code default)
    when the route is unset; None when it names a chat profile."""

    return _route_names(vault)[0]


def ready_profile_client(vault: LoadedVault, name: str | None) -> Any | None:
    """A ready client for the profile ``name`` on the judge route, or None."""

    return _ready(vault, name)


def ready_writer(vault: LoadedVault, injected: Mapping[str, Any] | None = None) -> tuple[Any | None, str | None]:
    """The LLM judge (and writer) on the judge route: (client, profile), or
    (None, profile) when none can serve an isolated structured completion."""

    return _ready_writer(vault, dict(injected or {}))


def resolve_judge(vault: LoadedVault, requested: str = "auto", *, clients: Mapping[str, Any] | None = None) -> JudgeRoute:
    """Decider, else the LLM judge, else the heuristic (or the one ``requested``)."""

    if requested not in JUDGE_CHOICES:
        raise ValueError(f"--judge must be one of {', '.join(JUDGE_CHOICES)}")
    injected = dict(clients or {})
    tried: list[dict[str, Any]] = []
    if requested == "heuristic":
        return JudgeRoute("heuristic", reason="requested", tried=tried)
    decider_name, _chat_name = _route_names(vault)
    if requested in ("auto", "decider"):
        client = injected.get("decider")
        if client is None and decider_name is not None and "decider" not in injected:
            client = _ready(vault, decider_name)
        tried.append({"judge": "decider", "provider": decider_name, "ready": client is not None})
        if client is not None:
            # The writer is resolved apart from the judge (review F4): the
            # route's chat profile, else the serving chat provider; never the
            # Decider the route names.
            writer, writer_provider = _ready_writer(vault, injected)
            return JudgeRoute("decider", provider=getattr(client, "provider_name", None) or decider_name,
                              model=getattr(client, "model", None), client=client,
                              reason="requested" if requested == "decider" else "the Decider is ready",
                              writer=writer, writer_provider=writer_provider, tried=tried)
        if requested == "decider":
            raise RuntimeError(f"the Decider ({decider_name or 'no decider profile on ai.routing.rubric_phrasing_judge'}) is not ready")
    client, provider = _ready_writer(vault, injected)
    tried.append({"judge": "llm", "provider": provider or "ai.active_provider", "ready": client is not None})
    if client is not None:
        return JudgeRoute("llm", provider=provider, model=getattr(client, "model", None), client=client,
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
    #: The writer's own verdict in ``judgment_ledger`` (review F6).
    writer_judgment_id: str | None = None
    #: Why the writer gave no reading (its call failed or was refused): the
    #: Decider's flag stands, with a deterministic draft.
    writer_error: str | None = None
    #: ``required_method``: the item's required method's own criterion, fact
    #: by design and never judged (so never ledgered as a verdict).
    rule: str | None = None
    #: The item's capability, for the owner's context (a method-selection
    #: item measures the choice, so its criteria deserve a careful look).
    capability: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items() if value is not None}

    def judgment_ids(self) -> list[str]:
        return [value for value in (self.judgment_id, self.writer_judgment_id) if value]


class IncompleteJudgment(ValueError):
    """A judge's reading that does not cover exactly the item's criteria, once each."""


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


def _ledger(repository: Repository, readings: Sequence[CriterionReading], *, judge: str, judge_model: Any,
            prompt_version: str, input_hash: str, now: str, writer: bool = False) -> None:
    """Append each JUDGED reading's verdict and keep its id (a required
    method's own criterion, fact by design, is not a verdict). ``writer``
    marks the writer's verdicts after a Decider (review F6)."""

    from learnloop.db.stores.judgments import append_judgment

    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            for reading in readings:
                if reading.rule is not None:
                    continue
                verdict = {"phrased_by": reading.phrased_by, "method": reading.method,
                           "fact_phrasing": reading.fact_phrasing}
                judgment_id = append_judgment(
                    connection, task=LEDGER_TASK, left_kind=LEDGER_LEFT_KIND,
                    left_id=f"{reading.item_id}#{reading.criterion_id}", judge=judge,
                    judge_model=str(judge_model or "unknown"), prompt_version=prompt_version,
                    input_hash=input_hash, verdict=json.dumps(verdict, sort_keys=True),
                    score=reading.probability, rationale=(
                        f"{judge}{' (writer)' if writer else ''}: {reading.phrased_by}"
                        + (f" ({reading.method})" if reading.method else "")
                    ),
                    created_at=now,
                )
                reading.judgment_id = judgment_id


def _check_coverage(item: PracticeItem, returned: Sequence[str]) -> None:
    """Exactly the item's criteria, once each (review F5): a missing,
    duplicated or unknown id is an incomplete judgment, never a verdict."""

    expected = [criterion.id for criterion in item.grading_rubric.criteria]
    counts = Counter(str(value) for value in returned)
    missing = [cid for cid in expected if cid not in counts]
    duplicated = sorted(cid for cid, count in counts.items() if count > 1)
    unknown = sorted(set(counts) - set(expected))
    if missing or duplicated or unknown:
        raise IncompleteJudgment(
            f"{item.id}: the reading must cover each criterion once "
            f"(missing {missing}, duplicated {duplicated}, unknown {unknown})"
        )


def llm_readings(item: PracticeItem, targets: Sequence[MethodTarget], client: Any, budget: _Budget,
                 *, only: set[str] | None = None) -> tuple[list[CriterionReading], str]:
    """One structured call: every criterion's phrasing (and the rewrites).

    Raises :class:`IncompleteJudgment` unless the reading covers exactly the
    item's criteria, once each (review F5). A required method's own criteria
    are read as ``fact`` by design (``rule = required_method``), whatever the
    model said.
    """

    prompt = judge_prompt(item, item.grading_rubric, targets)
    budget.register_llm(client)
    with budget.spend.collector.observing():
        with budget.spend.request(ROUTE, LLM_PURPOSE, input_tokens=_llm_tokens(prompt),
                                  output_tokens=LLM_OUTPUT_TOKENS):
            result = execute_structured_operation(
                client, purpose=LLM_PURPOSE, prompt=prompt, result_model=RubricPhrasingReading, isolated=True,
            )
    _check_coverage(item, [row.criterion_id for row in result.criteria])
    by_id = {row.criterion_id: row for row in result.criteria}
    readings: list[CriterionReading] = []
    for criterion in item.grading_rubric.criteria:
        if only is not None and criterion.id not in only:
            continue
        if criterion.id in _required_ids(item):
            readings.append(CriterionReading(item.id, criterion.id, criterion.description, "fact", "llm",
                                             rule="required_method"))
            continue
        row = by_id[criterion.id]
        method = row.phrased_by == "method"
        phrasing = " ".join(str(row.fact_phrasing or "").split()) or None
        readings.append(CriterionReading(
            item.id, criterion.id, criterion.description, row.phrased_by, "llm",
            method=(row.method or None) if method else None,
            fact_phrasing=phrasing if method else None, rewrite="llm" if method and phrasing else None,
        ))
    return readings, _input_hash({"prompt": prompt})


def decider_readings(item: PracticeItem, client: Any, budget: _Budget) -> tuple[list[CriterionReading], str]:
    """One Decider request: a choice question per criterion (a required
    method's own criteria are not asked: fact by design)."""

    criteria = [criterion for criterion in item.grading_rubric.criteria if criterion.id not in _required_ids(item)]
    state = decider_state(item, item.grading_rubric)
    readings = [
        CriterionReading(item.id, criterion.id, criterion.description, "fact", "decider", rule="required_method")
        for criterion in item.grading_rubric.criteria if criterion.id in _required_ids(item)
    ]
    if not criteria:
        return readings, _input_hash({"state": state})
    questions = {f"c{index}": decider_question(criterion) for index, criterion in enumerate(criteria)}
    budget.register_decider(client)
    tokens = _decider_tokens(item)
    with budget.spend.collector.observing():
        with budget.spend.request(DECIDER_ROUTE, LLM_PURPOSE, input_tokens=tokens, output_tokens=0):
            result = client.decide(state, questions, purpose=LLM_PURPOSE)
    missing = [key for key in questions if key not in result.answers]
    if missing:
        raise IncompleteJudgment(f"{item.id}: the Decider answered no question for {missing}")
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


def _judged_criteria(item: PracticeItem) -> int:
    return sum(1 for criterion in item.grading_rubric.criteria if criterion.id not in _required_ids(item))


def _decider_tokens(item: PracticeItem) -> int:
    """The input tokens one Decider request for ``item`` is admitted with (an
    upper bound: the state and every question's instructions and options)."""

    questions = [decider_question(criterion) for criterion in item.grading_rubric.criteria
                 if criterion.id not in _required_ids(item)]
    return _estimate_tokens(decider_state(item, item.grading_rubric)) + sum(
        _estimate_tokens(question.instructions + json.dumps(question.options, sort_keys=True)) for question in questions
    )


def _llm_tokens(prompt: str) -> int:
    """The input tokens one LLM judge or writer request is admitted with (an
    upper bound: the prompt and the result schema the transport sends)."""

    return _estimate_tokens(prompt) + _estimate_tokens(json.dumps(RubricPhrasingReading.model_json_schema()))


# -- repairs ------------------------------------------------------------------------


def _source_statement(item: PracticeItem) -> bool:
    """A source-authored statement: never rewritten, and its required method
    is decided once at import (or by the owner), never by a repair."""

    return is_source_statement(item)


def _teach_back(item: PracticeItem) -> bool:
    return item.teach_back_source is not None or item.practice_mode == "teach_back"


def repair_plan(vault: LoadedVault, item: PracticeItem, readings: Sequence[CriterionReading]) -> dict[str, Any] | None:
    """One item's repair: the updated rubric (and required method).

    Each method-phrased criterion becomes the item's required method's
    criterion when the item's target really is that method (by metadata, and
    the criterion's method names the target: ``names_match``), else is
    rephrased by fact. At most one required method per item; an item that
    already has one only gains criteria naming that method. The required
    method takes the target's own name (or alias); the statement is never
    edited (the canonical sentence, "Use {name} in your answer.", is
    rendered from the field wherever the item is shown or sent, round 3).
    Nothing here reads the prompt to decide (redesign 2026-10-14): the
    advisory heuristic only labels an action whose prompt may negate the
    method or leave it optional (``statement_may_disagree``) for the owner's
    review. A teach-back item never gains a required method (it explains,
    it does not execute), and a source statement never gains one from a
    repair (its wording is never rewritten; whether it requires a method was
    decided once at import, and the owner changes that with ``learnloop
    grading required-method``): its criterion is rephrased by fact, labelled
    ``source_statement``.

    The payload carries the item's content hash (``expected_target_hash``,
    review F3): acceptance refuses it if the item changed after this report.
    Each action lists the ledger verdicts it rests on (``judgment_ids``:
    the Decider's, then the writer's; review F6).
    """

    from learnloop.content.proposals.patches import compute_target_hash

    flagged = [reading for reading in readings if reading.phrased_by == "method"]
    if not flagged:
        return None
    existing = item.required_method
    # A source-authored statement (its own field says so, or the item is one
    # and has no field yet) never gains a required method from a repair.
    source = (getattr(existing, "statement", "instruction") == "source") if existing is not None \
        else _source_statement(item)
    targets = [] if _teach_back(item) else method_targets(
        vault, learning_object_id=item.learning_object_id, facet_ids=item.evidence_facets,
        capability=item.capability,
    )
    method_name: str | None = existing.name if existing is not None else None
    method_target: MethodTarget | None = best_target(method_name, targets) if method_name else None
    method_criteria: list[str] = list(existing.criterion_ids) if existing is not None else []
    actions: list[dict[str, Any]] = []
    rubric = item.grading_rubric.model_dump(mode="json", exclude_none=True)
    for reading in flagged:
        named = reading.method or ""
        target = best_target(named, targets) if named else None
        held_back = None
        if target is not None and (method_name is None or names_match(named, method_name)):
            # The target's own name (or alias), never a model's long paraphrase.
            candidate = method_name or target.matching_name(named) or target.name
            if source and existing is None:
                held_back = candidate
            else:
                if method_name is None:
                    method_name, method_target = candidate, target
                if reading.criterion_id not in method_criteria:
                    method_criteria.append(reading.criterion_id)
                action = {"criterion_id": reading.criterion_id, "action": "add_required_method",
                          "method": method_name, "target": target.as_context()}
                flag = advisory_statement_flag(item.prompt, method_name)
                if flag is not None:
                    # Advisory only (the field decides): the owner reads it.
                    action["statement_may_disagree"] = flag
                if reading.judgment_ids():
                    action["judgment_ids"] = reading.judgment_ids()
                actions.append(action)
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
        if reading.writer_error:
            # The writer's call failed or was refused: the Decider's flag
            # stands with a deterministic draft.
            action["writer_error"] = reading.writer_error
        if held_back is not None:
            # The target is this method, but the statement is source-authored:
            # its requirement is decided at import or by the owner, never here.
            action["source_statement"] = held_back
        if reading.judgment_ids():
            action["judgment_ids"] = reading.judgment_ids()
        actions.append(action)
    payload: dict[str, Any] = {"id": item.id, "learning_object_id": item.learning_object_id, "grading_rubric": rubric}
    if method_name is not None and method_criteria and method_target is not None and (
        existing is None or method_criteria != list(existing.criterion_ids)
    ):
        if existing is not None and getattr(existing, "statement", "instruction") == "source":
            # A source item's own decision stands; only its criteria grow.
            payload["required_method"] = {**existing.model_dump(mode="json"), "criterion_ids": method_criteria}
        else:
            # The statement is left as it is: the instruction is rendered
            # from the field wherever the item is shown or sent (round 3).
            payload["required_method"] = {"name": method_name, "criterion_ids": method_criteria,
                                          **method_target.link()}
    current = compute_target_hash(vault, "practice_item", item.id)
    if current is not None:
        payload["expected_target_hash"] = current
    return {"item_id": item.id, "actions": actions, "payload": payload}


def persist_repairs(vault: LoadedVault, repository: Repository, plans: Sequence[Mapping[str, Any]], *,
                    judge: JudgeRoute, clock: Clock | None = None) -> str | None:
    """One pending proposal batch (never auto-applied): an update per item.

    Each row's audit (``rubric_phrasing``) names the ledger verdicts its
    repair rests on (review F6).
    """

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
        judgment_ids = [value for action in plan["actions"] for value in action.get("judgment_ids") or ()]
        rows.append({
            "id": new_ulid(), "client_item_id": f"method_phrasing:{plan['item_id']}",
            "item_type": "practice_item", "operation": "update",
            "target_entity_type": "practice_item", "target_entity_id": plan["item_id"],
            "payload": plan["payload"], "source_ref_ids": [],
            "audit": {"rubric_phrasing": {
                "report_version": REPORT_VERSION, "judge": judge.kind, "judgment_ids": judgment_ids,
                "actions": [dict(action) for action in plan["actions"]],
            }},
            "decision": "pending",
            "validation_status": "valid", "validation_errors": [], "created_at": now, "updated_at": now,
        })
    summary = (
        f"Rubric criteria phrased by method ({judge.kind} judge): {len(plans)} item(s). Each update rephrases a "
        "criterion by the fact it establishes, or makes the method the item's required method with the explicit "
        "instruction when its target is that method. Review and accept or reject; nothing is applied until then. "
        "An item changed after this report is refused at acceptance: run the report again."
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


def _profile(vault: LoadedVault, name: str | None) -> Any | None:
    return vault.config.ai.providers.get(name) if name else None


def plan_dry_run(
    vault: LoadedVault,
    items: Sequence[PracticeItem],
    *,
    judge: str,
    caps: SpendCaps,
    price_per_million: float | None = None,
) -> dict[str, Any]:
    """What a run would send and cost, from configuration alone (review F7).

    No client is built. Each judge the run may use is planned with every
    request it could send: the Decider's classification (one request per item
    with a judged criterion, at its profile's listed input price) and the
    writer's rewrites (at most one per such item: any item may be flagged),
    or the LLM judge's one call per item. A writer's step is priced on every
    writer the run may select (:func:`writer_names`: the primary and its
    configured fallback; re-review F11), and bounded by the dearest of them.
    A metered route is priced at
    ``price_per_million`` (an owner upper bound); without one its price is
    unknown, the estimate is never rendered as zero and the plan is
    ``refused`` (the run would refuse those requests). A subscription route
    (Codex, the ChatGPT plan) has no marginal dollar cost: its tokens, and an
    API-equivalent cost at ``price_per_million``, are ``estimated_only``.
    """

    spend = ReviewSpend(caps, price_per_million=price_per_million, config=vault.config)
    decider_name, _chat = _route_names(vault)
    writers = writer_names(vault)
    judged = [item for item in items if _judged_criteria(item)]
    refused: list[str] = []

    def targets_of(item: PracticeItem) -> list[MethodTarget]:
        return method_targets(vault, learning_object_id=item.learning_object_id, facet_ids=item.evidence_facets,
                              capability=item.capability)

    def llm_steps(step: str, count_key: str) -> list[dict[str, Any]]:
        """The step priced on every writer the run may select (re-review F11):
        the primary, then each fallback (``fallback_for``), only one of which
        runs; an unknown metered price on any of them is refused."""

        if not writers:
            return [{"step": step, "route": ROUTE, "provider": None, count_key: 0,
                     "note": "no chat profile can write: the Decider's flags get deterministic drafts"}]
        population = judged if step == "rewrite" else list(items)
        input_tokens = sum(_llm_tokens(judge_prompt(item, item.grading_rubric, targets_of(item)))
                           for item in population)
        steps = []
        for name in writers:
            profile = _profile(vault, name)
            info = spend.register_profile(
                ROUTE, provider=name, model=getattr(profile, "model", None),
                subscription=is_subscription_transport(profile=profile) if profile is not None else False,
                max_tokens=getattr(profile, "max_tokens", None),
            )
            priced = _priced_step(spend, info, step, count_key, len(population), input_tokens,
                                  LLM_OUTPUT_TOKENS * len(population), price_per_million, refused)
            if steps:
                priced["fallback_for"] = writers[0]
                priced["note"] = ((priced.get("note") + "; ") if priced.get("note") else "") + (
                    f"the fallback writer: used only when {writers[0]} is not ready")
            steps.append(priced)
        return steps

    scenarios: list[dict[str, Any]] = []
    if judge in ("auto", "decider") and decider_name is not None:
        profile = _profile(vault, decider_name)
        price = getattr(profile, "price_per_million_input", None)
        info = RouteInfo(DECIDER_ROUTE, decider_name, getattr(profile, "model", None), "metered",
                         float(price) if price is not None else None,
                         "listed_input_price" if price is not None else "unknown", 0)
        spend.routes[DECIDER_ROUTE] = info
        classify = _priced_step(spend, info, "classify", "requests", len(judged),
                                sum(_decider_tokens(item) for item in judged), 0, price_per_million, refused)
        scenarios.append({"judge": "decider", "steps": [classify, *llm_steps("rewrite", "requests_at_most")]})
    if judge in ("auto", "llm"):
        scenarios.append({"judge": "llm", "steps": llm_steps("classify_and_rewrite", "requests")})
    for scenario in scenarios:
        # One writer runs per step: a step's bound is its dearest writer.
        by_step: dict[str, list[dict[str, Any]]] = {}
        for step in scenario["steps"]:
            by_step.setdefault(step["step"], []).append(step)
        costs = [step.get("estimated_usd") for step in scenario["steps"] if "estimated_usd" in step]
        scenario["estimated_usd"] = None if any(cost is None for cost in costs) else sum(
            max(float(step.get("estimated_usd") or 0.0) for step in options) for options in by_step.values())
        calls = sum(max(step.get("requests", step.get("requests_at_most", 0)) for step in options)
                    for options in by_step.values())
        tokens = sum(max(step.get("metered_tokens", 0) for step in options) for options in by_step.values())
        if scenario["estimated_usd"] is None:
            scenario["within_caps"] = None  # an unknown price is refused per step, above
            continue
        try:
            spend.check(SpendEstimate(calls=calls, total_tokens=tokens, estimated_usd=scenario["estimated_usd"]))
            scenario["within_caps"] = True
        except SpendLimitExceeded as exc:
            scenario["within_caps"] = False
            refused.append(f"{scenario['judge']}: {exc}")
    totals = [scenario["estimated_usd"] for scenario in scenarios]
    subscription = [step["provider"] for scenario in scenarios for step in scenario["steps"]
                    if step.get("billing") == "subscription"]
    estimate = {
        # Only one judge runs; the bound is the dearest one this run may use.
        "estimated_usd_upper_bound": None if any(total is None for total in totals) else max(totals, default=0.0),
        "max_estimated_usd": caps.max_estimated_usd,
        "refused": list(dict.fromkeys(refused)),
    }
    if subscription:
        estimate["subscription"] = (
            f"{', '.join(sorted(set(subscription)))} runs on the ChatGPT subscription: no marginal dollar cost; "
            "its tokens (and an API-equivalent cost with --price-per-million) are estimated_only, and the token "
            "and dollar caps are not enforced on it"
        )
    return {
        "status": "refused" if refused else "dry_run",
        "judge_plan": [*scenarios, {"judge": "heuristic", "requests": 0}],
        "estimate": estimate,
    }


def _priced_step(spend: ReviewSpend, info: RouteInfo, step: str, count_key: str, count: int, input_tokens: int,
                 output_tokens: int, owner_price: float | None, refused: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "step": step, "route": info.route, "provider": info.provider, "model": info.model, "billing": info.billing,
        "price_per_million": info.price_per_million, "price_source": info.price_source, count_key: count,
        "input_tokens": input_tokens, "output_tokens": output_tokens,
    }
    if not count:
        out["estimated_usd"] = 0.0
        return out
    if info.billing == "subscription":
        out.update(
            estimated_usd=0.0, marginal_usd=0.0, cost_basis="estimated_only",
            api_equivalent_usd=(input_tokens + output_tokens) * owner_price / 1_000_000 if owner_price else None,
            note="runs on the ChatGPT subscription: no marginal dollar cost; tokens are estimated_only",
        )
        return out
    estimate = spend.estimate(info.route, calls=count, input_tokens=input_tokens, output_tokens=output_tokens)
    out["estimated_usd"] = estimate.estimated_usd
    out["metered_tokens"] = estimate.total_tokens
    if estimate.estimated_usd is None:
        out["refused"] = (f"unknown price for {info.route} ({info.provider}, {info.model}): pass "
                          "--price-per-million (an upper bound); the run refuses these requests")
        refused.append(out["refused"])
    return out


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

    if judge not in JUDGE_CHOICES:
        raise ValueError(f"--judge must be one of {', '.join(JUDGE_CHOICES)}")
    items = candidate_items(vault, item_ids)
    caps = caps or default_caps(len(items))
    paths = VaultPaths(vault.root, vault.config)
    criteria = sum(len(item.grading_rubric.criteria) for item in items)
    report: dict[str, Any] = {
        "version": REPORT_VERSION, "status": "dry_run" if dry_run else "pending",
        "items": len(items), "criteria": criteria, "caps": caps.as_dict(),
    }
    if dry_run:
        report.update(plan_dry_run(vault, items, judge=judge, caps=caps, price_per_million=price_per_million))
        report["note"] = ("auto tries the Decider, then the LLM judge, then the heuristic, whichever is ready first; "
                          "a dry run builds no client and sends nothing")
        heuristic = [reading for item in items for reading in heuristic_readings(item) if reading.phrased_by == "method"]
        report["heuristic_flags"] = [reading.as_dict() for reading in heuristic]
        return report

    route = resolve_judge(vault, judge, clients=clients)
    report["judge"] = route.as_dict()
    repository = vault_repository(paths)
    run_id = new_ulid()
    spend = ReviewSpend(caps, cancelled=cancelled, price_per_million=price_per_million, config=vault.config)
    spend.collector.sink = receipt_sink(repository, owner_kind=RECEIPT_OWNER_KIND, owner_id=run_id)
    budget = _Budget(spend)
    now = utc_now_iso(clock)
    readings: list[CriterionReading] = []
    failures: Counter = Counter()
    writer_failures: Counter = Counter()
    writer = route.writer
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
                _ledger(repository, item_readings, judge="llm", judge_model=route.model,
                        prompt_version=JUDGE_PROMPT_VERSION, input_hash=input_hash, now=now)
            else:
                item_readings, input_hash = decider_readings(item, route.client, budget)
                _ledger(repository, item_readings, judge="decider", judge_model=route.model,
                        prompt_version=DECIDER_QUESTION_SET, input_hash=input_hash, now=now)
        except Exception as exc:  # noqa: BLE001 - one item's failure is counted, never a crashed run
            if type(exc).__name__ in {"SpendLimitExceeded", "SpendCancelled", "AIInterrupted"}:
                raise
            failures[type(exc).__name__] += 1
            report.setdefault("failed_items", []).append({"item_id": item.id, "error": type(exc).__name__})
            continue
        flagged_readings = [reading for reading in item_readings if reading.phrased_by == "method"]
        if route.kind == "decider" and flagged_readings and writer is not None:
            # The Decider judged; the LLM route writes the fact phrasings (and
            # names the method) of the criteria it flagged. Its verdicts are
            # ledgered under its own model, prompt version and input hash
            # (review F6); a failed or refused call leaves the Decider's paid
            # flags with labelled deterministic drafts (review F4).
            try:
                rewrites, writer_hash = llm_readings(
                    item, targets, writer, budget, only={reading.criterion_id for reading in flagged_readings},
                )
            except Exception as exc:  # noqa: BLE001 - the writer's failure never drops the Decider's flags
                if type(exc).__name__ in {"SpendCancelled", "AIInterrupted"}:
                    raise
                writer_failures[type(exc).__name__] += 1
                for reading in flagged_readings:
                    reading.writer_error = type(exc).__name__
                if isinstance(exc, SpendLimitExceeded):
                    # Refused before sending: no further rewrite is attempted.
                    report["writer_stopped"] = str(exc)
                    writer = None
            else:
                _ledger(repository, rewrites, judge="llm", judge_model=getattr(writer, "model", None),
                        prompt_version=JUDGE_PROMPT_VERSION, input_hash=writer_hash, now=now, writer=True)
                by_id = {row.criterion_id: row for row in rewrites}
                for reading in flagged_readings:
                    row = by_id.get(reading.criterion_id)
                    if row is None:
                        continue
                    reading.writer_reading = row.phrased_by
                    reading.writer_judgment_id = row.judgment_id
                    reading.method = row.method or reading.method
                    reading.fact_phrasing = row.fact_phrasing
                    reading.rewrite = "llm" if row.fact_phrasing else None
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
    if writer_failures:
        report["writer_failures"] = dict(writer_failures)
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
    "IncompleteJudgment",
    "DECIDER_QUESTION_SET",
    "JUDGE_PROMPT_VERSION",
    "JudgeRoute",
    "LEDGER_TASK",
    "PROPOSAL_PURPOSE",
    "REPORT_VERSION",
    "RubricPhrasingReading",
    "candidate_items",
    "decider_readings",
    "decider_profile_name",
    "default_caps",
    "deterministic_fact_draft",
    "heuristic_readings",
    "judge_prompt",
    "llm_readings",
    "persist_repairs",
    "plan_dry_run",
    "ready_profile_client",
    "ready_writer",
    "repair_plan",
    "resolve_judge",
    "run_method_phrasing",
    "can_write",
    "write_report",
    "writer_name",
    "writer_names",
]
