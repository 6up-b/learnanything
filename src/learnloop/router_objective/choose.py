"""RO4/RO5: the objective router's choice at a block boundary, as one pure function.

``choose(inputs)`` takes what the chooser read (each policy's answer or why it has none, the weight, the switches as
they serve, the seed, the stop coin's rate with what the coin freezes) and returns what is served with everything the
router logs about it: which policies failed and where their share went, the effective weights, the mix's draw, the
stop coin, the rule code and its sentence, the rationale guard's verdict, the why, and the decision's record. It reads
no database and no clock and draws only from the seed it is given, so the same inputs give the same choice, bit for
bit; ``daily_plan.objective_chooser`` gathers the inputs and writes what this returns.

The order of the draws is the served one: the mix's two uniforms (``mix.draw``), then the coin's own (``stop_coin``),
never the mix's, so the mix's draw and ``μ`` are the same whether or not a coin is flipped.

A leaf: the mix, the stop coin, the why's sentences and the decision record. It cannot import ``daily_plan``, so the
two component statuses it compares are repeated here (``tests/test_choose.py`` holds them equal to the runtime's).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
import math
from typing import Any

from learnloop import provenance
from learnloop.provenance import DecisionRecord
from learnloop.router import mixture as mx
from learnloop.router import why as router_why
from learnloop.router_objective import mix
from learnloop.router_objective import stop_coin as SC

#: The chooser's ``mode`` and its ``decided_by`` when its models were asked; with none set up, ``objective_no_models``.
MODE = "objective"
NO_MODELS = "objective_no_models"
#: The version of this choice's learner-facing copy (the why it returns).
WHY_VERSION = "router_why_v3"
#: ``daily_plan.router_runtime``'s statuses for a component that answered and one that was not asked.
ANSWERED = "answered"
NOT_READY = "not_ready"
#: The rule code of a served stop: an offer the learner can decline.
STOP_OFFER = "stop_offer"
PLAN_BLOCK = "plan_block"


@dataclass(frozen=True)
class OptionFacts:
    """What the rule sentence reads of one option in the support: the reason code the staged frame (or the boundary,
    for an offer or IH2's contest) gave it, and the topic or section its sentence names."""

    reason_code: str = ""
    topic: Any = None
    section: Any = None


@dataclass(frozen=True)
class ChoiceInputs:
    """Everything one boundary's choice depends on, as read before it."""

    #: The options in support order (stop among them where offered); ``staged_ref`` is staged's own pick in it.
    support: tuple[str, ...]
    staged_ref: str
    #: The support's candidates (stop has none) by ref.
    options: Mapping[str, OptionFacts]
    #: The LLM policy: its status, and its distribution, rationale and cited ids when it answered and parsed.
    llm_status: str
    llm_distribution: Mapping[str, float] | None
    rationale: str | None
    cited: tuple[str, ...]
    #: The evidence ids on the LLM policy's card: the only ones a shown rationale may cite.
    card_evidence_ids: frozenset[str]
    #: The numeric policy's status (None: no answer of any kind) and its choice.
    numeric_status: str | None
    numeric_choice: str | None
    #: ``w_i`` (the weight's posterior), where a failed policy's share goes (IH5), and the exploration floor.
    w: float
    to_other_policy: bool
    epsilon: float
    #: The decision's seed: the mix's uniforms and the coin's are all drawn from it.
    seed: str
    #: The stop coin: its rate, the session's active minutes at this decision (None: not read, or unreadable), and
    #: the availability it freezes (read only when :func:`coin_applies`).
    stop_rate: float
    session_minutes: float | None
    availability: Mapping[str, Any] | None
    #: The staged rule's own why, served when the mix's is empty.
    staged_why: str
    #: Whether no model was set up (the decision is ``objective_no_models``).
    no_models: bool
    #: What the decision's record names besides the choice.
    boundary_key: str
    algorithm_version: Any
    question_set_version: Any
    llm_schema_version: Any


@dataclass(frozen=True)
class Choice:
    """What :func:`choose` decided, as the router logs it."""

    #: The policies that failed, and the mix they leave: its effective weights and each live component's
    #: distribution (``mix.components``).
    failed: tuple[str, ...]
    effective: Mapping[str, float]
    components: Mapping[str, Mapping[str, float]]
    #: The numeric policy's choice when it entered the mix (it answered, inside the support), else None.
    numeric_choice: str | None
    #: The mix's draw and the coin (None where it does not apply).
    drawn: mx.Draw
    coin: SC.Coin | None
    #: What is served, its probability, and each option's probability as logged (under a coin the served
    #: distribution, exact; else the mix's ``μ``).
    served: str
    propensity: float
    pi: Mapping[str, float]
    #: The rule code (the record's ``why_code``) and its sentence.
    rule_code: str
    rule: str
    #: The rationale guard: the LLM's favoured option, why its rationale may not be shown (None: it may), whether it is.
    favoured: str | None
    guard: str | None
    shown: bool
    rationale_hidden: bool
    evidence_labels: tuple[str, ...]
    #: The learner-facing why and its kind.
    why: str
    why_kind: str
    decided_by: str
    fallback: str | None
    fallback_reasons: Mapping[str, str]
    #: The coin's ``policy_experiment_assignments`` row, pending (written with the decision).
    assignments: tuple[Mapping[str, Any], ...] = ()
    #: The decision's own ``plan_block`` record: what the decision knows; the container adds the block, the router
    #: row, the trace and what only it saw (``boundary_records.plan_block_records``).
    record: DecisionRecord | None = field(default=None, compare=False)


def coin_reads_minutes(stop_rate: float, support: tuple[str, ...] | list[str]) -> bool:
    """Whether the coin could apply, so the session's minutes are read for it: a positive rate and stop offered."""

    return stop_rate > 0 and SC.STOP in support


def coin_applies(stop_rate: float, support: tuple[str, ...] | list[str], session_minutes: float | None) -> bool:
    """Whether the coin is flipped (and its availability read first): a positive rate at a boundary where stop sits
    beside a block once the session holds active minutes (``stop_coin.eligible``)."""

    return stop_rate > 0 and SC.eligible(support, session_minutes=session_minutes)


def choose(inputs: ChoiceInputs) -> Choice:
    """The boundary's choice: the mix of the two policies over the support, the stop coin on its own uniform, the rule
    sentence of what is served and the why the learner sees."""

    support = list(inputs.support)
    llm_dist = inputs.llm_distribution
    numeric_ok = inputs.numeric_status == ANSWERED and inputs.numeric_choice in support
    failed = [name for name, ok in ((mix.LLM, llm_dist is not None), (mix.NUMERIC, numeric_ok)) if not ok]
    effective = mix.effective_weights(inputs.w, failed, to_other_policy=inputs.to_other_policy)
    numeric_choice = inputs.numeric_choice if numeric_ok else None
    parts = mix.components(support, inputs.staged_ref, llm=llm_dist, numeric_ref=numeric_choice)
    drawn = mix.draw(support, parts, effective, inputs.epsilon, inputs.seed)
    coin = None
    if coin_applies(inputs.stop_rate, support, inputs.session_minutes):
        if inputs.availability is None:
            raise ValueError("the stop coin applies but its availability was not read")
        coin = SC.flip(inputs.seed, inputs.stop_rate, support=support, mu=drawn.pi, drawn=drawn.chosen,
                       availability=inputs.availability)
    served = coin.served if coin is not None else drawn.chosen
    option = inputs.options.get(served)
    if option is not None:
        code = option.reason_code
        rule = router_why.sentence(code, topic=option.topic, section=option.section)
    else:
        code, rule = STOP_OFFER, router_why.sentence(STOP_OFFER)
    favoured = max(llm_dist, key=lambda ref: llm_dist[ref]) if llm_dist else None
    rationale = inputs.rationale if llm_dist is not None else None
    cited = inputs.cited if llm_dist is not None else ()
    guard = (router_why.rationale_guard(rationale, cited, inputs.card_evidence_ids) if rationale is not None
             else "absent")
    if guard is None and drawn.component == mix.LLM and drawn.chosen != favoured:
        guard = "another_option"
    shown = drawn.component == mix.LLM and guard is None
    if coin is not None and served != drawn.chosen:
        # The coin, not the mix, chose what is served: no model's rationale is shown for it.
        shown = False
    why, why_kind = router_why.objective_why(drawn.component if served == drawn.chosen else mix.STAGED, rule,
                                             option_count=len(support), rationale=rationale, rationale_shown=shown)
    if coin is not None:
        propensity = coin.served_propensity
        pi = SC.served_distribution(drawn.pi, coin.rate, support)
        assignments: tuple[Mapping[str, Any], ...] = (SC.pending_assignment(coin, seed=inputs.seed, support=support),)
    else:
        propensity = 1.0 if drawn.deterministic else drawn.propensity
        pi = dict(drawn.pi)
        assignments = ()
    decided_by = NO_MODELS if inputs.no_models else MODE
    fallback = mix.fallback_label(failed)
    choice = Choice(
        failed=tuple(failed), effective=effective, components=parts, numeric_choice=numeric_choice, drawn=drawn,
        coin=coin, served=served, propensity=propensity, pi=pi, rule_code=code, rule=rule, favoured=favoured,
        guard=guard, shown=shown, rationale_hidden=bool(drawn.component == mix.LLM and not shown),
        evidence_labels=tuple(ref for ref in cited if ref in inputs.card_evidence_ids) if shown else (),
        why=why or inputs.staged_why, why_kind=why_kind, decided_by=decided_by, fallback=fallback,
        fallback_reasons={name: (inputs.llm_status if name == mix.LLM else (inputs.numeric_status or NOT_READY))
                          for name in failed},
        assignments=assignments,
    )
    return _with_record(choice, inputs)


def _code(value: Any) -> str | None:
    return value if provenance.is_code(value) else None


def _number(value: Any) -> float | int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(float(value)) else None


def _compact(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _with_record(choice: Choice, inputs: ChoiceInputs) -> Choice:
    """The decision's ``plan_block`` record: chosen, its rule, the support's other options with their logged
    probabilities, and the draw's facts and versions. No id, time, trace or subject: the container writes the record
    in the block's transaction and adds those."""

    alternatives = []
    taken = {choice.served}
    for option in inputs.support:
        if option not in taken:
            alternatives.append(_compact({"ref": provenance.ref(option), "p": _number(choice.pi.get(option)),
                                          "lost_by": "not_drawn"}))
            taken.add(option)
    record = DecisionRecord(
        kind=PLAN_BLOCK,
        status="chosen",
        chosen_ref=provenance.ref(choice.served),
        decided_by=_code(choice.decided_by),
        rule=_code(choice.rule_code or None),
        alternatives=tuple(alternatives),
        facts=_compact({
            "propensity": _number(choice.propensity),
            "boundary_key": _code(inputs.boundary_key),
            "drawn_component": _code(choice.drawn.component),
            "mix_fallback": _code(choice.fallback),
            "option_count": _number(len(inputs.support)),
        }),
        versions=_compact({
            "algorithm_version": _code(inputs.algorithm_version),
            "policy": _code(mix.POLICY),
            "design": _code(mix.DESIGN),
            "seed": _code(inputs.seed),
            "why_version": _code(WHY_VERSION),
            "question_set_version": _code(inputs.question_set_version),
            "llm_schema_version": _code(inputs.llm_schema_version),
        }),
    )
    return replace(choice, record=record)


__all__ = ["ANSWERED", "Choice", "ChoiceInputs", "MODE", "NOT_READY", "NO_MODELS", "OptionFacts", "STOP_OFFER",
           "WHY_VERSION", "choose", "coin_applies", "coin_reads_minutes"]
