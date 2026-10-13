"""Tier-1 small judgments decided by the Decider (owner decision 2026-10-13).

The Decider (route ``ai.routing.tier1_decider``; empty means the code-default
``openrouter_decider`` profile, never a chat provider and never
``LEARNLOOP_AI_PROVIDER``) answers ONE typed
:class:`~learnloop.ai.decisions.ChoiceQuestion` per judgment. The option with
the highest probability decides (argmax, no hand-set threshold); the whole
distribution is logged. A Decider that is unavailable, refused for spend or
failing returns no choice, and the caller runs its existing LLM judgment, with
that route's own output-budget policy and receipts, and records which judge
decided (:func:`log_llm`). A cancellation propagates; it never falls back.

Every check appends one ``judgment_ledger`` row (judge ``decider``): its option
on success, else one of :data:`FAILURE_VERDICTS`, which no Tier-1 question
offers as an option, so a reader that compares verdicts can skip it and
``learnloop decider agreement`` counts it as a fallback. The ledger's input
hash names the judged input, not the producer, so a Decider verdict and an LLM
verdict on the same input form a real pair. Nothing here makes a shadow call.

Each judgment has its own switch under ``[decider_routes]`` (default on); a
serving judgment is live only at ``mvp-0.20`` or later
(:data:`~learnloop.algorithm_versions.DECIDER_TIER1_VERSIONS`), while the facet
span-support check, a content path, follows its switch at every version. The
action router's ``router_decider`` is never a Tier-1 judgment: :func:`enabled`
is false for it, so no generic fallback ever reaches it.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
import json
from typing import Any

from learnloop.ai.decisions import ChoiceQuestion, choice_probabilities
from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import call_labels, content_key
from learnloop.ai.spend import SpendCaps, SpendLimitExceeded
from learnloop.db.stores.judgments import append_judgment

#: The Decider's route (``ai.routing.tier1_decider``), a decider-only route.
ROUTE = "tier1_decider"
#: The question-set version of every Tier-1 Decider row (and its fallback rows).
VERSION = "tier1-decider-v1"
#: The judgments a ``[decider_routes]`` switch names, each live by default.
SERVING_TASKS = (
    "learner_gap_judge", "learner_gap_kind", "misconception_match", "diagnosis_link_judgment",
    "field_question_classification", "contamination_leak_judgment", "contamination_reveal_judgment",
)
#: The content check, switched at every algorithm version.
CONTENT_TASKS = ("facet_span_support",)
#: The verdict of a Decider row that holds no answer: never an option of any Tier-1 question.
FAILURE_VERDICTS = frozenset({"unavailable", "refused", "failed"})
#: Admits one Decider request: ``(route, purpose, input_tokens)`` -> a context.
Admit = Callable[[str, str, int], AbstractContextManager[Any]]


def enabled(config: Any, task: str) -> bool:
    """Whether the Decider decides ``task`` for this vault's config (its switch and version)."""

    if task not in SERVING_TASKS and task not in CONTENT_TASKS:
        return False
    if not bool(getattr(config.decider_routes, task, False)):
        return False
    if task in CONTENT_TASKS:
        return True
    from learnloop.algorithm_versions import DECIDER_TIER1_VERSIONS

    return config.algorithms.algorithm_version in DECIDER_TIER1_VERSIONS


def client_for(root: Any, config: Any) -> Any:
    """The ready Decider client of ``ai.routing.tier1_decider``; raises when it is not ready."""

    from learnloop.ai.routing import ready_client_for_task

    resolved = ready_client_for_task(root, config, ROUTE, allow_env=False)
    if resolved.client is None or not resolved.runtime.ready:
        raise AIProviderUnavailable("Decider unavailable")
    return resolved.client


@dataclass
class Decision:
    """One Tier-1 check: ``choice`` is the argmax option, or None (``status`` says why)."""

    task: str
    input_hash: str
    left_kind: str
    left_id: str
    right_kind: str | None = None
    right_id: str | None = None
    #: ``ok`` | ``disabled`` | ``unavailable`` | ``refused`` | ``failed``
    status: str = "disabled"
    choice: str | None = None
    probabilities: dict[str, float] = field(default_factory=dict)
    model: str = "unavailable"
    judgment_id: str | None = None

    def detail(self) -> dict[str, Any]:
        return {"status": self.status, "verdict": self.choice, "probabilities": self.probabilities,
                "judgment_id": self.judgment_id, "input_hash": self.input_hash, "judge": "decider"}


def _append(repository: Any, decision: Decision, *, judge: str, choice: str, model: str,
            rationale: Mapping[str, Any], judgment_id: str | None = None,
            prompt_version: str = VERSION) -> str:
    with repository.atomic():
        return append_judgment(
            repository.connection(), id=judgment_id, task=decision.task, left_kind=decision.left_kind,
            left_id=decision.left_id, right_kind=decision.right_kind, right_id=decision.right_id,
            judge=judge, judge_model=model, prompt_version=prompt_version, input_hash=decision.input_hash,
            verdict=choice, score=decision.probabilities.get(choice) if judge == "decider" else None,
            rationale=json.dumps(rationale, sort_keys=True),
        )


def record_failure(repository: Any, decision: Decision, *, error: str | None = None) -> Decision:
    """Ledger a check that gave no answer (``decision.status``), for a caller that asked the Decider itself.

    T1's pair judge (``matching.judge.judge_pairs``) asks the Decider through
    its own claims and reuse; a pair it failed is recorded here, so the LLM
    verdict that replaces it pairs with this row in the agreement report.
    """

    if decision.status not in FAILURE_VERDICTS:
        raise ValueError(f"not a failure status: {decision.status!r}")
    decision.judgment_id = _append(repository, decision, judge="decider", choice=decision.status,
                                   model=decision.model, rationale={**decision.detail(), "error": error})
    return decision


def log_llm(repository: Any, decision: Decision, *, choice: str, model: str, rationale: str = "") -> str:
    """The fallback LLM's verdict on the Decider's input, as a real pair for the agreement report."""

    return _append(repository, decision, judge="llm", choice=choice, model=model or "unknown",
                   rationale={"fallback": decision.status, "decider_judgment_id": decision.judgment_id,
                              "rationale": rationale})


def decide(*, root: Any, config: Any, repository: Any, task: str, state: Any, question: ChoiceQuestion,
           left_kind: str = "input", left_id: str | None = None,
           right_kind: str | None = None, right_id: str | None = None,
           client_factory: Callable[[], Any] | None = None, spend: Any = None, input_hash: str | None = None,
           ledger_task: str | None = None, question_name: str = "verdict",
           candidates: int = 0, pairs: int = 0, judgment_id: str | None = None,
           admit: Admit | None = None, rationale: Mapping[str, Any] | None = None,
           route: str = ROUTE) -> Decision:
    """Ask the Decider one typed question; a disabled judgment returns ``status='disabled'`` unasked.

    ``ledger_task`` names the ledger task when it differs from the switch's
    (a text-gap or contamination task); ``judgment_id`` is the id of the row a
    successful check appends (a caller's checkpoint id); ``admit`` admits the
    request instead of ``spend.request`` (a caller that records its own calls);
    ``rationale`` adds caller metadata to the row. ``route`` names the spend
    route of a caller that brings its own Decider (``client_factory``): the
    learner-text gaps keep ``learner_gap_decider``.
    """

    digest = input_hash or content_key({"state": state, "question": question.wire(), "task": task})
    decision = Decision(ledger_task or task, digest, left_kind, left_id or digest, right_kind, right_id)
    if not enabled(config, task):
        return decision
    try:
        client = (client_factory or (lambda: client_for(root, config)))()
        if client is None:
            raise AIProviderUnavailable("Decider unavailable")
        decision.model = str(getattr(client, "model", None) or "unknown")
        result = _ask(client, config=config, repository=repository, task=task, state=state,
                      questions={question_name: question}, owner_id=decision.left_id, spend=spend,
                      candidates=candidates, pairs=pairs, admit=admit, route=route)
        decision.probabilities = choice_probabilities(result.answers[question_name], question)
        decision.choice = max(decision.probabilities, key=decision.probabilities.__getitem__)
        decision.model = str(result.model or decision.model)
        decision.status = "ok"
    except AIInterrupted:
        raise  # a cancellation stops the caller; it is never a fallback
    except SpendLimitExceeded:
        decision.status = "refused"
    except AIProviderUnavailable:
        decision.status = "unavailable"
    except Exception:  # noqa: BLE001 - a failed small judgment hands over to its LLM
        decision.status = "failed"
    decision.judgment_id = _append(
        repository, decision, judge="decider", choice=decision.choice or decision.status, model=decision.model,
        rationale={**decision.detail(), **dict(rationale or {})},
        judgment_id=judgment_id if decision.status == "ok" else None,
    )
    return decision


def _ask(client: Any, *, config: Any, repository: Any, task: str, state: Any, questions: dict[str, Any],
         owner_id: str, spend: Any = None, candidates: int = 0, pairs: int = 0, admit: Admit | None = None,
         route: str = ROUTE) -> Any:
    from learnloop.ai.review_spend import ReviewSpend, RouteInfo

    price = getattr(getattr(client, "settings", None), "price_per_million_input", None)
    # One judgment, one admitted request at the Decider's listed input price
    # (about $0.0004 a decision); no output allowance: the Decider is exempt
    # from the LLM output-budget policy.
    spend = spend or ReviewSpend(SpendCaps(max_calls=1, max_total_tokens=1_000_000, max_estimated_usd=1.0),
                                 config=config)
    spend.routes[route] = RouteInfo(
        route, getattr(client, "provider_name", None), getattr(client, "model", None), "metered",
        float(price) if price is not None else None, "listed_input_price" if price is not None else "unknown", 0,
    )
    wire = {"state": state, "questions": {name: question.wire() for name, question in questions.items()}}
    tokens = len(json.dumps(wire, ensure_ascii=False).encode()) + 512
    previous = spend.collector.sink
    if previous is None:
        spend.collector.sink = lambda action, event: repository.record_model_event(
            action, event, owner_kind=task, owner_id=owner_id)
    try:
        admission = (admit(route, task, tokens) if admit is not None else
                     spend.request(route, task, input_tokens=tokens, output_tokens=0,
                                   candidates=candidates, pairs=pairs))
        with spend.collector.observing(), admission:
            with call_labels(judge="decider", question_set_version=VERSION, state_hash=content_key(wire)):
                return client.decide(state, questions, purpose=task)
    finally:
        spend.collector.sink = previous


def decide_many(*, root: Any, config: Any, repository: Any, task: str, state: Any,
                questions: dict[str, ChoiceQuestion], left_kind: str, left_id: str,
                spend: Any = None, candidates: int = 0) -> dict[str, Decision]:
    """One physical request for independent questions about one input; one ledger row per question.

    The batch is validated whole before any answer is accepted; a failure
    leaves every question without a choice.
    """

    from learnloop.ai.decisions import MAX_QUESTIONS

    decisions = {name: Decision(task, content_key({"state": state, "question": question.wire(), "task": task}),
                                left_kind, left_id, "metadata", name)
                 for name, question in questions.items()}
    if not enabled(config, task) or not questions or len(questions) > MAX_QUESTIONS:
        return decisions
    model = "unavailable"
    try:
        client = client_for(root, config)
        model = str(getattr(client, "model", None) or "unknown")
        result = _ask(client, config=config, repository=repository, task=task, state=state,
                      questions=questions, owner_id=left_id, spend=spend, candidates=candidates)
        distributions = {name: choice_probabilities(result.answers[name], question)
                         for name, question in questions.items()}
        for name, decision in decisions.items():
            decision.probabilities = distributions[name]
            decision.choice = max(distributions[name], key=distributions[name].__getitem__)
            decision.status, decision.model = "ok", str(result.model or model)
    except AIInterrupted:
        raise
    except Exception as exc:  # noqa: BLE001 - the batch hands over to its LLM
        status = ("refused" if isinstance(exc, SpendLimitExceeded) else
                  "unavailable" if isinstance(exc, AIProviderUnavailable) else "failed")
        for decision in decisions.values():
            decision.status, decision.model = status, model
    for decision in decisions.values():
        decision.judgment_id = _append(repository, decision, judge="decider",
                                       choice=decision.choice or decision.status, model=decision.model,
                                       rationale=decision.detail())
    return decisions


__all__ = [
    "CONTENT_TASKS",
    "FAILURE_VERDICTS",
    "ROUTE",
    "SERVING_TASKS",
    "VERSION",
    "Decision",
    "client_for",
    "decide",
    "decide_many",
    "enabled",
    "log_llm",
    "record_failure",
]
