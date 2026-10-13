"""The typed tool interface (spec_source_practice_and_probes_v1 §10; S4).

Five tools, each with a strict argument model (``extra="forbid"``) and a
published JSON schema. None has a policy field: the dispatcher derives the
policy from the caller on the server (§5.2, SC2), refuses everything during a
cold administration, drops unknown ids (and records what it dropped), runs the
operation under that caller and returns compact records a model may read
(§5.3): never an expected answer, rubric, hint, profile answer or solution
block, and nothing that reproduces the bound item's answer.

Receipts (``source_tool_calls``, append-only): a validated request writes a
``request`` row (plus a ``judgment_ledger`` row, task ``source_tool_request``,
when a model wrote it); running it writes a ``run`` row naming the request.
``run_requested_tool`` re-reads the stored caller context, so the policy
cannot change between a tutor's answer and the run (it can only narrow, when
a cold administration opened since).

Tools propose; serving paths serve (SC1). Nothing here writes attempts,
evidence, mastery, FSRS, scheduler state or plan items (G1).
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import time
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from learnloop.ai.execution import content_key
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores.judgments import append_judgment
from learnloop.db.stores.source_service import insert_tool_call, tool_call, tool_calls
from learnloop.ids import new_ulid
from learnloop.instructional.exercises import exercise_region_count
from learnloop.instructional.policy import caller_for_question_event, cold_administration_open
from learnloop.instructional.practice import propose_practice
from learnloop.instructional.sources import propose_comparison, propose_sources
from learnloop.instructional.valuation import named_gaps_available
from learnloop.practice_index.retrieval import (
    INTENTS as PRACTICE_INTENTS,
    IntentUnavailable,
    PracticeConstraints,
    admissible_corpus,
    facet_shortlist,
)
from learnloop.source_retrieval.corpus import MODEL_WITHHELD_ROLES, model_reader_withheld
from learnloop.source_retrieval.find_sources import INTENTS as SOURCE_INTENTS
from learnloop.source_retrieval.policy import CallerContext, PolicyRefused, derive_policy
from learnloop.tutor.tutor_qa import answer_leaks_expected, span_leaks_expected
from learnloop.vault.models import LoadedVault

TOOL_REQUEST_TASK = "source_tool_request"
#: Callers whose requests are recorded in ``source_tool_calls`` (§10.4).
RECORDED_CALLERS = ("tutor", "router", "agent")
#: Callers whose requests a model wrote (a ``judgment_ledger`` row each).
MODEL_CALLERS = ("tutor", "router")
#: Run when the offer is shown (cheap, time-boxed); the rest run when tapped.
EAGER_TOOLS = frozenset({"find_practice", "find_sources", "find_facets", "practice_availability"})
PROMPT_CHARS = 400
STATEMENT_CHARS = 1200
PASSAGE_CHARS = 900
HYPOTHESIS_KINDS = ("misconception", "named_gap", "causal_hypothesis", "lo", "facet")


class ToolArgumentsInvalid(ValueError):
    def __init__(self, code: str, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details


class _Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HypothesisRefArg(_Args):
    kind: Literal["misconception", "named_gap", "causal_hypothesis", "lo", "facet"]
    id: str = Field(min_length=1, max_length=200)


class FindPracticeArgs(_Args):
    query: str = Field(min_length=1, max_length=2000, description="What to practise, in natural language.")
    intent: Literal["practice", "discriminate", "retention", "remediate"] = "practice"
    facet_ids: list[str] = Field(default_factory=list, max_length=40)
    learning_object_ids: list[str] = Field(default_factory=list, max_length=40)
    target_hypotheses: list[HypothesisRefArg] = Field(default_factory=list, max_length=40)
    kinds: Literal["items", "source_exercises", "both"] | None = None
    unattempted_only: bool = False
    max_estimated_minutes: float | None = Field(default=None, gt=0, le=240)
    reason: str = Field(default="", max_length=300, description="One line for the learner; never the answer.")


class FindSourcesArgs(_Args):
    query: str = Field(min_length=1, max_length=2000)
    intent: Literal["explain", "remediate", "alternative", "worked_example", "compare"] = "explain"
    facet_ids: list[str] = Field(default_factory=list, max_length=40)
    target_hypotheses: list[HypothesisRefArg] = Field(default_factory=list, max_length=40)
    roles: list[str] = Field(default_factory=list, max_length=12)
    reason: str = Field(default="", max_length=300)


class CompareSourcesArgs(_Args):
    query: str = Field(min_length=1, max_length=2000)
    facet_ids: list[str] = Field(default_factory=list, max_length=40)
    requested_perspectives: list[str] = Field(default_factory=list, max_length=8)
    reason: str = Field(default="", max_length=300)


class FindFacetsArgs(_Args):
    query: str = Field(min_length=1, max_length=2000)


class PracticeAvailabilityArgs(_Args):
    facet_ids: list[str] = Field(default_factory=list, max_length=40)
    intents: list[Literal["practice", "discriminate", "retention", "remediate"]] = Field(
        default_factory=lambda: ["practice"], min_length=1, max_length=4)


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    arguments: type[_Args]
    model_call: str


TOOLS: dict[str, Tool] = {tool.name: tool for tool in (
    Tool("find_practice", "Practice questions and textbook exercises for a request, ranked; for the value "
         "intents (discriminate, retention) ranked by LearnLoop's value-of-information estimate. Proposes only.",
         FindPracticeArgs, "the relevance rerank; the discrimination screen for discriminate"),
    Tool("find_sources", "Verbatim passages from the learner's own sources for an intent (explain, remediate, "
         "alternative, worked_example, compare), verified to fit it.", FindSourcesArgs, "verification"),
    Tool("compare_sources", "How the learner's sources treat one question: each source's contribution with "
         "quotes verified in its own passage; no consensus is claimed.", CompareSourcesArgs, "one comparison"),
    Tool("find_facets", "A shortlist of facets for a phrase, by keyword and stored vectors. The caller decides.",
         FindFacetsArgs, "none"),
    Tool("practice_availability", "Per intent, how many admissible candidates exist on these facets, their "
         "expected minutes and their kinds. Recall and admission only.", PracticeAvailabilityArgs, "none"),
)}

assert set(PRACTICE_INTENTS) >= {"practice", "discriminate", "retention", "remediate"}
assert set(SOURCE_INTENTS) >= {"explain", "remediate", "alternative", "worked_example", "compare"}


def tool_schemas() -> list[dict[str, Any]]:
    """Every tool's declaration, as ``FIND_PRACTICE_TOOL`` publishes one."""

    return [{"name": tool.name, "description": tool.description,
             "input_schema": tool.arguments.model_json_schema(), "model_call": tool.model_call}
            for tool in TOOLS.values()]


def validate_arguments(name: str, arguments: Mapping[str, Any]) -> _Args:
    tool = TOOLS.get(name)
    if tool is None:
        raise ToolArgumentsInvalid("unknown_tool", f"Unknown tool {name!r}; tools: {', '.join(TOOLS)}")
    try:
        return tool.arguments.model_validate(dict(arguments))
    except ValidationError as exc:
        raise ToolArgumentsInvalid("invalid_arguments", f"Invalid arguments for {name}",
                                   details=exc.errors(include_url=False, include_context=False)) from exc


def drop_unknown_ids(vault: LoadedVault, repository: Repository,
                     args: _Args) -> tuple[_Args, list[dict[str, Any]]]:
    """Unknown facet, LO and hypothesis ids are dropped; each drop is reported."""

    dropped: list[dict[str, Any]] = []
    values = args.model_dump()
    if "facet_ids" in values:
        kept = []
        for facet in values["facet_ids"]:
            canonical = vault.canonical_facet_id(str(facet))
            if canonical in vault.evidence_facets:
                kept.append(canonical)
            else:
                dropped.append({"field": "facet_ids", "id": facet, "why": "unknown facet"})
        values["facet_ids"] = list(dict.fromkeys(kept))
    if "learning_object_ids" in values:
        kept = []
        for lo_id in values["learning_object_ids"]:
            if lo_id in vault.learning_objects:
                kept.append(lo_id)
            else:
                dropped.append({"field": "learning_object_ids", "id": lo_id, "why": "unknown learning object"})
        values["learning_object_ids"] = kept
    if "target_hypotheses" in values:
        kept_refs = []
        gaps = None
        for ref in values["target_hypotheses"]:
            kind, ref_id = ref["kind"], ref["id"]
            known = True
            if kind == "misconception":
                known = repository.misconception(ref_id) is not None
            elif kind == "causal_hypothesis":
                known = repository.fetch_hypothesis_set(ref_id) is not None
            elif kind == "lo":
                known = ref_id in vault.learning_objects
            elif kind == "facet":
                known = vault.canonical_facet_id(ref_id) in vault.evidence_facets
            elif kind == "named_gap":
                gaps = named_gaps_available(repository) if gaps is None else gaps
                if not gaps:
                    dropped.append({"field": "target_hypotheses", "id": ref_id,
                                    "why": "unavailable: learner-text gaps not merged"})
                    continue
            if known:
                kept_refs.append(ref)
            else:
                dropped.append({"field": "target_hypotheses", "id": ref_id, "why": f"unknown {kind}"})
        values["target_hypotheses"] = kept_refs
    return type(args).model_validate(values), dropped


# -- model-reader views (§5.3) -----------------------------------------------------------


def _clip(text: Any, limit: int) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


class _Withhold:
    """Drops any record whose text reproduces the bound item's answer (G3)."""

    def __init__(self, vault: LoadedVault, caller: CallerContext) -> None:
        item = vault.practice_items.get(caller.item_id) if caller.item_id else None
        self.expected = item.expected_answer if item is not None else None
        self.withheld = 0
        #: Spans dropped for every caller: ``solution`` and ``assessment_lane``.
        self.by_reason: dict[str, int] = {}

    def keep(self, *texts: Any) -> bool:
        if self.expected is None:
            return True
        if any(span_leaks_expected(str(text or ""), self.expected) for text in texts):
            self.withheld += 1
            return False
        return True


def _practice_view(vault: LoadedVault, result: Mapping[str, Any], withhold: _Withhold) -> dict[str, Any]:
    items = []
    for entry in result.get("items") or ():
        item = vault.practice_items.get(entry["practice_item_id"])
        if item is None or not withhold.keep(item.prompt):
            continue
        canonical = getattr(item, "canonical_exercise", None)
        minutes = None
        for valued in entry.get("valuation") or ():
            minutes = valued.get("expected_minutes", minutes)
        items.append({
            "practice_item_id": item.id, "learning_object_id": item.learning_object_id,
            "facet_ids": list(entry.get("facet_ids") or ()), "practice_mode": item.practice_mode,
            "prompt": _clip(item.prompt, PROMPT_CHARS), "difficulty": item.difficulty,
            "expected_minutes": minutes, "source_label": canonical.label if canonical is not None else None,
            "rationale": entry.get("rationale"),
        })
    exercises = []
    for entry in result.get("source_exercises") or ():
        if not withhold.keep(entry.get("statement")):
            continue
        exercises.append({
            "key": entry["key"], "span_keys": [f"{entry['extraction_id']}:{span}" for span in entry["span_ids"]],
            "source_label": entry.get("label_line"), "page": entry.get("page"),
            "statement": _clip(entry.get("statement"), STATEMENT_CHARS), "rationale": entry.get("rationale"),
        })
    view: dict[str, Any] = {"proposal_id": result.get("proposal_id"), "intent": result.get("intent"),
                            "status": result.get("status"), "items": items, "source_exercises": exercises,
                            "serves": False}
    valuation = result.get("valuation") or {}
    if valuation:
        view["valuation"] = {
            "scale": valuation.get("scale") or valuation.get("reason"),
            "problems": [{"problem": section.get("problem", {}).get("key"), "verdict": section.get("verdict"),
                          "checks": [check.get("ref") for check in section.get("checks") or ()]}
                         for section in valuation.get("problems") or ()]}
    if result.get("paging"):
        view["paging"] = {"outcome": result["paging"].get("outcome")}
    return view


def _passage(hit: Mapping[str, Any]) -> dict[str, Any]:
    return {"span_key": f"{hit['extraction_id']}:{hit['span_id']}", "source_title": hit.get("source_title"),
            "section": hit.get("section"), "page": hit.get("page"), "revision_id": hit.get("revision_id"),
            "text": _clip(hit.get("text"), PASSAGE_CHARS), "label": "source-authored"}


def _model_withheld(vault: LoadedVault, repository: Repository,
                    keys: Sequence[tuple[str, str]], withhold: _Withhold) -> dict[tuple[str, str], str]:
    """Solution regions and assessment-lane spans, for every caller (§5.3, SC3):
    a bound item's answer filter is not the only thing a model must not read."""

    withheld = model_reader_withheld(vault, repository, keys)
    for reason in withheld.values():
        withhold.by_reason[reason] = withhold.by_reason.get(reason, 0) + 1
    return withheld


def _sources_view(vault: LoadedVault, repository: Repository, hits: Any, withhold: _Withhold) -> dict[str, Any]:
    withheld = _model_withheld(vault, repository, [(hit["extraction_id"], hit["span_id"]) for hit in hits.hits],
                               withhold)
    passages = [_passage(hit) for hit in hits.hits
                if (hit["extraction_id"], hit["span_id"]) not in withheld
                and hit.get("role") not in MODEL_WITHHELD_ROLES and withhold.keep(hit.get("text"))]
    return {"intent": hits.intent, "policy": hits.policy, "status": hits.status, "passages": passages}


def _comparison_view(vault: LoadedVault, repository: Repository, comparison: Any,
                     withhold: _Withhold) -> dict[str, Any]:
    payload = comparison.as_dict()

    def key(entry: Mapping[str, Any]) -> tuple[str, str]:
        return (str(entry.get("extraction_id")), str(entry.get("span_id")))

    listed = [entry for group in ("sources", "also_discussed_in", "unverified_sources")
              for entry in payload.get(group) or ()]
    withheld = _model_withheld(vault, repository, [key(entry) for entry in listed], withhold)
    sources = [source for source in payload.get("sources") or ()
               if key(source) not in withheld
               and withhold.keep(source.get("passage"), *[c.get("quote") for c in source.get("contributions") or ()])]
    kept_refs = {source.get("ref") for source in sources}
    relations = [relation for relation in payload.get("relations") or ()
                 if relation.get("left_ref") in kept_refs and relation.get("right_ref") in kept_refs]
    return {"comparison_id": payload.get("comparison_id"), "status": payload.get("status"),
            "policy": payload.get("policy"), "sources": sources, "relations": relations,
            "missing_perspectives": payload.get("missing_perspectives"),
            "also_discussed_in": [entry for entry in payload.get("also_discussed_in") or ()
                                  if key(entry) not in withheld],
            "unverified_sources": [entry for entry in payload.get("unverified_sources") or ()
                                   if key(entry) not in withheld],
            "labels": payload.get("labels")}


# -- execution ----------------------------------------------------------------------------


def _availability(vault: LoadedVault, repository: Repository, args: PracticeAvailabilityArgs, *,
                  caller: CallerContext, estimator: Any | None) -> dict[str, Any]:
    exercises = exercise_region_count(vault, repository, list(caller.learning_object_ids))
    report = {}
    for intent in args.intents:
        constraints = PracticeConstraints(intent=intent, facet_ids=tuple(args.facet_ids),
                                          exclude_item_ids=(caller.item_id,) if caller.item_id else ())
        corpus, excluded = admissible_corpus(vault, repository, constraints, estimator=estimator)
        minutes = None
        if estimator is not None and corpus:
            values = []
            for item_id in corpus:
                item = vault.practice_items[item_id]
                try:
                    values.append(float(estimator(item_id, item.practice_mode, None).minutes))
                except Exception:  # noqa: BLE001 - an estimate is optional here
                    continue
            if values:
                values.sort()
                minutes = {"median": values[len(values) // 2], "min": values[0], "max": values[-1]}
        modes: dict[str, int] = {}
        for item_id in corpus:
            mode = vault.practice_items[item_id].practice_mode
            modes[mode] = modes.get(mode, 0) + 1
        report[intent] = {
            "admissible_items": len(corpus), "excluded": dict(excluded), "expected_minutes": minutes,
            "kinds": {"items": len(corpus), "source_exercises": exercises["regions"]},
            "practice_modes": modes,
            **({"note": "independence is checked when a candidate is valued"}
               if intent in ("discriminate", "retention") else {}),
        }
    return {"facet_ids": list(args.facet_ids), "intents": report, "model_calls": 0}


def execute_tool(vault: LoadedVault, repository: Repository, name: str, args: _Args, *,
                 caller: CallerContext, injections: Mapping[str, Any] | None = None,
                 clients: Mapping[str, Any] | None = None, clock: Clock | None = None) -> dict[str, Any]:
    """Run one validated tool under ``caller``; the model-reader view plus refs."""

    injected = dict(injections or {})
    client = dict(clients or {})
    withhold = _Withhold(vault, caller)
    policy, _reason = derive_policy(caller)
    if policy == "cold_attempt":
        raise PolicyRefused("cold_attempt", "every tool is refused during a cold administration")
    out: dict[str, Any] = {"tool": name, "policy": policy}
    if name == "find_practice":
        assert isinstance(args, FindPracticeArgs)
        constraints = {"intent": args.intent, "facet_ids": args.facet_ids,
                       "learning_object_ids": args.learning_object_ids or list(caller.learning_object_ids),
                       "target_hypotheses": [ref.model_dump() for ref in args.target_hypotheses],
                       "unattempted_only": args.unattempted_only,
                       **({"kinds": args.kinds} if args.kinds else {}),
                       **({"max_estimated_minutes": args.max_estimated_minutes}
                          if args.max_estimated_minutes is not None else {})}
        result = propose_practice(vault, repository, args.query, constraints, caller=caller, origin="tool",
                                  rerank_client=client.get("practice_rerank"), embedder=injected.get("embedder"),
                                  clock=clock, **{key: injected[key] for key in ("exercise_arm", "valuer",
                                                                                   "estimator") if key in injected})
        view = _practice_view(vault, result, withhold)
        out.update(result=view, result_ref=result.get("proposal_id"), model=result.get("rerank_model"),
                   result_keys=[entry["practice_item_id"] for entry in view["items"]]
                   + [entry["key"] for entry in view["source_exercises"]],
                   source_versions={entry["extraction_id"]: entry.get("revision_id")
                                    for entry in result.get("source_exercises") or ()})
    elif name == "find_sources":
        assert isinstance(args, FindSourcesArgs)
        hits = propose_sources(vault, repository, args.query, caller=caller, intent=args.intent,
                               learning_object_ids=list(caller.learning_object_ids), facet_ids=args.facet_ids,
                               roles=args.roles, target_hypotheses=[ref.model_dump() for ref in args.target_hypotheses],
                               verify=True, rerank_client=client.get("source_rerank"),
                               embedder=injected.get("embedder"), clock=clock)
        view = _sources_view(vault, repository, hits, withhold)
        out.update(result=view,
                   result_ref=hits.manifest.get("manifest_hash") or content_key([hits.manifest])[:32],
                   result_keys=[passage["span_key"] for passage in view["passages"]],
                   source_versions={hit["extraction_id"]: hit.get("revision_id") for hit in hits.hits},
                   model=(hits.manifest.get("verification") or {}).get("model"))
    elif name == "compare_sources":
        assert isinstance(args, CompareSourcesArgs)
        comparison = propose_comparison(vault, repository, args.query, caller=caller, facet_ids=args.facet_ids,
                                        requested_perspectives=args.requested_perspectives,
                                        client=client.get("source_compare"),
                                        verify_client=client.get("source_rerank"),
                                        embedder=injected.get("embedder"), clock=clock)
        view = _comparison_view(vault, repository, comparison, withhold)
        out.update(result=view, result_ref=comparison.comparison_id,
                   result_keys=[f"{s.get('extraction_id')}:{s.get('span_id')}" for s in view["sources"]],
                   source_versions={s.get("extraction_id"): s.get("revision_id") for s in view["sources"]},
                   model=comparison.manifest.get("model"))
    elif name == "find_facets":
        assert isinstance(args, FindFacetsArgs)
        view = facet_shortlist(vault, repository, args.query)
        out.update(result=view, result_ref=None, result_keys=[entry["facet_id"] for entry in view["facets"]],
                   source_versions={}, model=None)
    elif name == "practice_availability":
        assert isinstance(args, PracticeAvailabilityArgs)
        view = _availability(vault, repository, args, caller=caller, estimator=injected.get("estimator"))
        out.update(result=view, result_ref=None, result_keys=list(view["intents"]), source_versions={}, model=None)
    else:  # pragma: no cover - validate_arguments refuses unknown names
        raise ToolArgumentsInvalid("unknown_tool", name)
    if withhold.withheld:
        out["result"]["withheld_answer_overlap"] = withhold.withheld
    if withhold.by_reason:
        out["result"]["withheld_from_model"] = dict(sorted(withhold.by_reason.items()))
    return out


# -- receipts -----------------------------------------------------------------------------


def request_tool(vault: LoadedVault, repository: Repository, name: str, arguments: Mapping[str, Any], *,
                 caller: CallerContext, model: str | None = None, prompt_version: str | None = None,
                 refusal: tuple[str, str] | None = None, extra_dropped: Sequence[Mapping[str, Any]] = (),
                 clock: Clock | None = None) -> dict[str, Any]:
    """Validate a request and write its ``request`` row (``refused`` when it may not run)."""

    if caller.kind not in RECORDED_CALLERS:
        raise PolicyRefused("caller_refused", f"caller kind {caller.kind!r} cannot request source tools")
    if name not in TOOLS:
        raise ToolArgumentsInvalid("unknown_tool", f"Unknown tool {name!r}; tools: {', '.join(TOOLS)}")
    dropped = [dict(entry) for entry in extra_dropped]
    status, code, message = "requested", None, None
    validated: dict[str, Any] = dict(arguments)
    if refusal is not None:
        status, (code, message) = "refused", refusal
    else:
        try:
            args = validate_arguments(name, arguments)
            args, unknown = drop_unknown_ids(vault, repository, args)
            dropped.extend(unknown)
            validated = args.model_dump()
        except ToolArgumentsInvalid as exc:
            status, code, message = "refused", exc.code, str(exc)
            dropped.append({"field": "*", "why": exc.code, "details": exc.details})
    policy, derived_from = derive_policy(caller)
    if status == "requested" and policy == "cold_attempt":
        status, code, message = "refused", "cold_attempt", "every tool is refused during a cold administration"
    call_id = "stc_" + new_ulid()
    now = utc_now_iso(clock)
    with repository.connection() as connection:
        ledger_id = None
        if caller.kind in MODEL_CALLERS and model:
            reason = str(validated.get("reason") or "")
            ledger_id = append_judgment(
                connection, task=TOOL_REQUEST_TASK, left_kind="source_tool_call", left_id=call_id,
                right_kind="tool", right_id=name, judge="llm", judge_model=model,
                prompt_version=prompt_version or "unspecified", input_hash=content_key([name, validated])[:40],
                verdict=name, rationale="[withheld: the request leaked the answer]" if code == "answer_leak"
                else reason, created_at=now)
        insert_tool_call(connection, id=call_id, created_at=now, row_kind="request", caller_kind=caller.kind,
                         caller_ref=caller.ref, context={**caller.as_dict(), "policy_derived_from": derived_from},
                         policy=policy, tool=name, arguments=validated, status=status, dropped=dropped,
                         ledger_id=ledger_id, model=model, prompt_version=prompt_version)
        connection.commit()
    entry = {"tool_call_id": call_id, "tool": name, "status": status, "policy": policy, "arguments": validated,
             "dropped": dropped, "run": "eager" if name in EAGER_TOOLS else "lazy",
             "reason": validated.get("reason")}
    if status == "refused":
        entry["refusal"] = {"code": code, "message": message}
    return entry


def run_requested_tool(vault: LoadedVault, repository: Repository, request_id: str, *,
                       injections: Mapping[str, Any] | None = None, clients: Mapping[str, Any] | None = None,
                       clock: Clock | None = None) -> dict[str, Any]:
    """Run a stored request under its stored caller context; writes the ``run`` row."""

    with repository.connection() as connection:
        request = tool_call(connection, request_id)
    if request is None or request["row_kind"] != "request":
        raise ToolArgumentsInvalid("not_found", f"No tool request {request_id}")
    if request["status"] == "refused":
        raise PolicyRefused("refused", "this tool request was refused when it was made")
    context = dict(request["context"])
    context.pop("policy_derived_from", None)
    caller = CallerContext.from_dict(context)
    if not caller.cold and cold_administration_open(repository, caller.item_id):
        # A cold administration opened since: the policy narrows, never widens.
        caller = CallerContext.from_dict({**caller.as_dict(), "cold": True})
    started = time.monotonic()
    status, out, error = "ran", None, None
    try:
        args = validate_arguments(request["tool"], request["arguments"])
        out = execute_tool(vault, repository, request["tool"], args, caller=caller, injections=injections,
                           clients=clients, clock=clock)
    except (PolicyRefused, IntentUnavailable, ToolArgumentsInvalid) as exc:
        status, error = "failed", exc
    except Exception as exc:  # noqa: BLE001 - a failed run is recorded, then re-raised
        status, error = "failed", exc
    latency = int(round((time.monotonic() - started) * 1000))
    run_id = "stc_" + new_ulid()
    policy, _ = derive_policy(caller)
    with repository.connection() as connection:
        insert_tool_call(
            connection, id=run_id, parent_id=request_id, created_at=utc_now_iso(clock), row_kind="run",
            caller_kind=request["caller_kind"], caller_ref=request["caller_ref"], context=caller.as_dict(),
            policy=policy, tool=request["tool"], arguments=request["arguments"], status=status,
            result_ref=(out or {}).get("result_ref"), result_keys=(out or {}).get("result_keys") or (),
            source_versions=(out or {}).get("source_versions") or {}, model=(out or {}).get("model"),
            latency_ms=latency,
            cost=None if error is None else {"error": type(error).__name__, "code": getattr(error, "code", None)})
        connection.commit()
    if error is not None:
        raise error
    return {**(out or {}), "tool_call_id": request_id, "run_id": run_id, "latency_ms": latency}


def run_tool(vault: LoadedVault, repository: Repository, name: str, arguments: Mapping[str, Any], *,
             caller: CallerContext, injections: Mapping[str, Any] | None = None,
             clients: Mapping[str, Any] | None = None, clock: Clock | None = None) -> dict[str, Any]:
    """The dispatcher (§10.1): request row, then the run under the same caller."""

    request = request_tool(vault, repository, name, arguments, caller=caller, clock=clock)
    if request["status"] == "refused":
        refusal = request["refusal"]
        error: Exception = (PolicyRefused(refusal["code"], refusal["message"]) if refusal["code"] == "cold_attempt"
                            else ToolArgumentsInvalid(refusal["code"], refusal["message"], request["dropped"]))
        error.tool_call_id = request["tool_call_id"]  # type: ignore[attr-defined]
        raise error
    result = run_requested_tool(vault, repository, request["tool_call_id"], injections=injections,
                                clients=clients, clock=clock)
    return {**result, "dropped": request["dropped"]}


# -- the tutor's requests (§10.3) ---------------------------------------------------------


def tutor_tools_active(vault: LoadedVault) -> bool:
    config = vault.config.source_service
    return bool(config.enabled and config.tutor_tools)


def tutor_tool_requests(vault: LoadedVault, repository: Repository, *, event_id: str, requests: Sequence[Any],
                        model: str | None, prompt_version: str | None,
                        clock: Clock | None = None) -> list[dict[str, Any]]:
    """Validate a tutor answer's requests before anything is shown.

    Each ``reason`` and ``query`` passes the answer-leak check the answer
    passes; a leaking request is recorded refused and never offered. Unknown
    ids are dropped. No count cap: money and the time box bound execution.
    Returns the requests the frontend may run, each with its receipt id.
    """

    if not tutor_tools_active(vault) or not requests:
        return []
    caller = caller_for_question_event(vault, repository, event_id)
    item = vault.practice_items.get(caller.item_id) if caller.item_id else None
    offered = []
    for request in requests:
        payload = request.model_dump() if hasattr(request, "model_dump") else dict(request)
        name = str(payload.pop("tool", ""))
        refusal = None
        dropped: list[dict[str, Any]] = []
        if item is not None:
            leaking = [field for field in ("query", "reason")
                       if answer_leaks_expected(str(payload.get(field) or ""), item.expected_answer)]
            if leaking:
                refusal = ("answer_leak", "the request carried the current item's answer")
                dropped = [{"field": field, "why": "answer_leak"} for field in leaking]
                payload = {key: ("[withheld]" if key in leaking else value) for key, value in payload.items()}
        entry = request_tool(vault, repository, name, payload, caller=caller, model=model,
                             prompt_version=prompt_version, refusal=refusal, extra_dropped=dropped, clock=clock)
        if entry["status"] == "requested":
            offered.append({key: entry[key] for key in ("tool_call_id", "tool", "reason", "run", "dropped")}
                           | {"arguments": {key: value for key, value in entry["arguments"].items()
                                            if key != "reason"}})
    return offered


def offered_tool_requests(repository: Repository, event_id: str) -> list[dict[str, Any]]:
    """The offers a tutor answer carried, re-read from their request rows (a
    recovered response says what the original said)."""

    with repository.connection() as connection:
        rows = tool_calls(connection, caller_kind="tutor", caller_ref=event_id)
    return [{"tool_call_id": row["id"], "tool": row["tool"], "reason": row["arguments"].get("reason"),
             "run": "eager" if row["tool"] in EAGER_TOOLS else "lazy", "dropped": row["dropped"],
             "arguments": {key: value for key, value in row["arguments"].items() if key != "reason"}}
            for row in rows if row["row_kind"] == "request" and row["status"] == "requested"]


def tutor_request_handler(vault: LoadedVault) -> Callable[..., list[dict[str, Any]]] | None:
    """What the adapters pass to ``ask_question(tool_request_handler=...)``; None when off."""

    return tutor_tool_requests if tutor_tools_active(vault) else None


__all__ = [
    "EAGER_TOOLS",
    "HYPOTHESIS_KINDS",
    "TOOLS",
    "TOOL_REQUEST_TASK",
    "ToolArgumentsInvalid",
    "drop_unknown_ids",
    "execute_tool",
    "offered_tool_requests",
    "request_tool",
    "run_requested_tool",
    "run_tool",
    "tool_schemas",
    "tutor_request_handler",
    "tutor_tool_requests",
    "tutor_tools_active",
    "validate_arguments",
]
