"""A6 opportunistic trace evidence — the elicitation boundary and the reports.

Spec: ``spec_measurement_efficiency_v1.md`` §3.A6; implementation plan item 6.2.

A6 has two halves with very different costs, and conflating them is how the item
goes wrong:

* **Reporting** — the grader already reads the whole natural-language trace, so
  let it say which facets it saw *exercised* beyond the item's declared set.
  Zero learner cost. That half lives on the grading path
  (``learnloop.attempts.ai_contracts.ExercisedFacetObservation`` ->
  ``grading._validated_exercised_facets`` -> ``attempts._record_exercised_facets``
  -> ``trace_exercised_facets``) and is what discharges A1 guard 1.
* **Eliciting** — asking the learner to write one more line so there is more
  trace to read. This costs learner time, and standing constraint 10 makes that
  a first-class regression: an instrument that raises information per question
  but raises annoyance faster is a regression, and
  ``problems_to_cold_success`` is the metric that catches it.

This module owns the second half's bounds, and the reports that watch the
first's revert criterion.

**The elicitation discriminator already existed: ``trace_contract``.** A worked
derivation is self-documenting — the steps *are* the explanation, and demanding
prose beside them produces filler and pollutes the trace. The genuinely
ambiguous cases are the three the spec names: a correct answer with skipped
steps, a choice among methods, and an applicability judgment. All three are
items whose *answer underdetermines the reasoning*, which is exactly what "no
reliable decomposition, or a rung whose whole content is a judgment" means in
this vault's vocabulary.

Four rules, all enforced here rather than described in a prompt:

1. **Elicit where the answer underdetermines the reasoning, nowhere else.**
2. **One line at a decision point, not a paragraph at every step.** The prompt
   this module returns is one question; there is no per-step variant to reach
   for.
3. **Rewarded, never required.** :func:`elicitation_reward` is what the feedback
   surface says afterwards ("this also demonstrated N facets"). Nothing in the
   attempt path treats a missing answer as anything at all — an unelicited or
   declined line is not a skip, not a hint, and not a failure.
4. **A per-session budget**, so it cannot creep.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from learnloop.content.authoring.conjunctive_items import UNEXERCISED_SUPPORTING_TARGET

#: Capabilities whose answer routinely underdetermines the reasoning: choosing a
#: method and judging applicability are decisions whose *result* is short and
#: whose *grounds* are the whole measurement. ``procedure_execution`` and
#: ``coordination`` are deliberately absent — their work IS the explanation.
UNDERDETERMINED_CAPABILITIES: frozenset[str] = frozenset(
    {"method_selection", "schema_interpretation"}
)

ElicitationReason = Literal[
    "answer_underdetermines_reasoning",
    "self_documenting_trace",
    "capability_shows_its_work",
    "session_budget_exhausted",
    "disabled",
]


@dataclass(frozen=True)
class ElicitationDecision:
    """Whether to offer the one-line justification field on this item."""

    elicit: bool
    reason: ElicitationReason
    prompt: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"elicit": self.elicit, "reason": self.reason, "prompt": self.prompt}


#: Deliberately a *question about the decision*, never "explain your working".
#: "Why this method?" is one line and enormously informative; "explain each
#: algebra step" is annoying and tells you nothing.
_DECISION_POINT_PROMPT = "Optional, one line: why this approach rather than another?"
_APPLICABILITY_PROMPT = "Optional, one line: what made this case fit?"

#: The heading that marks the volunteered line inside the composed trace. A
#: delimiter for the *reader*: the grader must receive ONE trace rather than two
#: fields, because "the grader already reads the whole natural-language trace" is
#: the entire reason the extra line is worth anything.
#:
#: It is not a wire contract and no client may reproduce it. The volunteered line
#: crosses the RPC boundary as its own submission field
#: (``submit_attempt.explanationMd``); this module is the only place that knows
#: how the two are joined, via the :func:`compose_learner_trace` /
#: :func:`volunteered_explanation` inverse pair below. It used to be duplicated
#: as a literal in ``PracticeScreen.tsx`` with a comment asking two languages to
#: stay in sync by hand, which is a synchronization requirement no test could
#: state and no reviewer could see break.
#:
#: Nothing branches on its absence, per rule 3: an answer without it is an
#: answer, not a decline, not a skip, not a failure.
ELICITATION_ANSWER_HEADING = "[Why this approach]"


def compose_learner_trace(answer_md: str, explanation_md: str | None) -> str:
    """Join the answer and the volunteered line into the one trace the grader reads.

    The ONLY writer of :data:`ELICITATION_ANSWER_HEADING`. A blank or absent
    explanation returns the answer byte-identically, so a learner who was offered
    the field and ignored it submits exactly what a learner who was never offered
    it submits — rule 3 made structural, with no representation for "declined".
    """

    line = (explanation_md or "").strip()
    if not line:
        return answer_md
    return f"{answer_md}\n\n{ELICITATION_ANSWER_HEADING} {line}"


def volunteered_explanation(trace_md: str | None) -> str | None:
    """The volunteered line inside a composed trace, or None — the exact inverse.

    Read path only, for callers holding a *persisted* attempt rather than a live
    submission. ``practice_attempts`` has no column of its own for the line (its
    schema and repository belong elsewhere), so the composed
    ``learner_answer_md`` is the only durable record there is. Pairing the
    extractor with the composer in one module is what keeps the delimiter an
    implementation detail: both sides change together or neither does.
    """

    if not trace_md:
        return None
    _, marker, tail = trace_md.partition(ELICITATION_ANSWER_HEADING)
    if not marker:
        return None
    return tail.strip() or None


def elicited_explanations_in(traces) -> int:
    """How many of ``traces`` carry a volunteered explanation.

    Rule 4's budget is only a bound if it is checked against the number of lines
    the learner actually *wrote*. An offer that was declined is deliberately not
    an event anywhere in this system — recording one would make "we asked and
    they said nothing" a fact about the learner, which is exactly the reading
    rule 3 forbids — so the submitted traces are the only honest ledger.

    Counts through :func:`volunteered_explanation` rather than by matching a
    string the caller supplies, so the budget cannot drift from what the
    submission path actually writes.
    """

    return sum(
        1 for trace in (traces or ()) if volunteered_explanation(trace) is not None
    )


def decide_elicitation(
    item,
    *,
    config,
    elicitations_this_session: int,
) -> ElicitationDecision:
    """Whether to offer a one-line justification alongside ``item``.

    Never raises and never blocks: the caller renders an optional field when
    ``elicit`` is true and does nothing otherwise. Every arm is typed, because
    "we did not ask" has four different meanings and the revert criterion needs
    to tell them apart.
    """

    if not getattr(config, "elicitation_enabled", True):
        return ElicitationDecision(False, "disabled")
    budget = int(getattr(config, "max_elicitations_per_session", 0) or 0)
    if elicitations_this_session >= budget:
        return ElicitationDecision(False, "session_budget_exhausted")

    contract = getattr(item, "trace_contract", None)
    if contract is not None and getattr(contract, "status", None) == "available":
        # The item declares its own decomposition, so the learner's steps are
        # already the explanation. Asking for prose beside them is pure friction.
        return ElicitationDecision(False, "self_documenting_trace")

    capability = str(getattr(item, "capability", "") or "")
    if capability not in UNDERDETERMINED_CAPABILITIES:
        return ElicitationDecision(False, "capability_shows_its_work")
    prompt = (
        _DECISION_POINT_PROMPT if capability == "method_selection" else _APPLICABILITY_PROMPT
    )
    return ElicitationDecision(True, "answer_underdetermines_reasoning", prompt=prompt)


def elicitation_reward(
    exercised_facets,
    *,
    explanation_md: str | None = None,
    learner_answer_md: str | None = None,
) -> str | None:
    """The visible reward for a volunteered explanation, or None.

    "Voluntary and visibly rewarded self-selects for learners with something to
    say; mandatory trains people to write filler." This is the visible half —
    the feedback surface saying what the extra line bought. It counts only
    ``opportunistic`` observations: telling a learner their explanation
    demonstrated the facet the item was already grading them on is not a reward,
    it is noise.

    THE GATE. ``observation_scope`` separates declared from opportunistic, which
    is a statement about the item's contract — not about whether the learner
    volunteered anything. Ungated, an attempt that was never offered elicitation,
    on which the grader happened to see an extra facet in the ordinary working,
    is told "your explanation also demonstrated…" about an explanation that does
    not exist. That is a small lie in a system whose headline outcome is not
    telling people false things, and it would also corrupt the incentive the
    reward exists to create.

    ``explanation_md`` is the structured field a live submission carries and is
    preferred whenever given. ``learner_answer_md`` is the fallback for callers
    reading a *persisted* attempt, whose only durable record of the line is the
    composed trace; it is recovered with :func:`volunteered_explanation` rather
    than by matching a delimiter at the call site. Passing neither keeps the old
    ungated behaviour, for callers that genuinely have no trace at all.
    """

    if explanation_md is not None:
        if not explanation_md.strip():
            return None
    elif learner_answer_md is not None:
        if volunteered_explanation(learner_answer_md) is None:
            return None
    count = sum(
        1
        for row in (exercised_facets or ())
        if str(_field(row, "observation_scope")) == "opportunistic"
    )
    if count <= 0:
        return None
    noun = "facet" if count == 1 else "facets"
    return f"Your explanation also demonstrated {count} additional {noun}."


def _field(row: Any, key: str) -> Any:
    if isinstance(row, dict):
        return row.get(key)
    return getattr(row, key, None)


# -- Reports: A6's revert criterion, and A1 guard 1's typed record --------------


def trace_evidence_report(repository) -> dict[str, Any]:
    """Concentration + volume of A6 observations, and unexercised supporting mass.

    A6's revert criterion has two arms and this report measures the second:
    "``problems_to_cold_success`` rises" is the scoreboard's job, and
    "opportunistic credit concentrates on a few facets, which indicates the
    grader is pattern-matching the vocabulary rather than reading the work" is
    this one.

    ``concentration`` is the share of opportunistic observations landing on the
    single most-reported facet. It is deliberately a *share*, not a
    Herfindahl-style index: the failure mode is one or two favourite facets
    absorbing everything, and the simplest statistic that catches it is the one
    a reader can check by hand against the counts printed beside it. It abstains
    (``None``) below a handful of observations rather than reporting 1.0 from a
    single row, which would be the confident wrongness the whole program exists
    to prevent.

    ``unexercised_supporting_mass`` is A1 guard 1's typed record read back: mass
    that supporting targets would have earned had the trace shown their facets
    exercised. A cell accumulating it is an item claiming to consume a facet it
    never touches, which is an authoring defect the author can see and fix.
    """

    observations = repository.all_trace_exercised_facets()
    by_facet: dict[str, int] = {}
    declared = 0
    opportunistic = 0
    for rows in observations.values():
        for row in rows:
            if str(row.get("observation_scope")) == "opportunistic":
                opportunistic += 1
                facet = str(row.get("facet_id"))
                by_facet[facet] = by_facet.get(facet, 0) + 1
            else:
                declared += 1
    concentration: float | None = None
    if opportunistic >= 5 and by_facet:
        concentration = max(by_facet.values()) / opportunistic

    unexercised: list[dict[str, Any]] = []
    for cell in repository.facet_capability_evidence_all():
        mass = float(getattr(cell, "unexercised_supporting_mass", 0.0) or 0.0)
        if mass <= 0.0:
            continue
        unexercised.append(
            {
                "facet_id": cell.facet_id,
                "capability": cell.capability,
                # The typed marker §3.A1 guard 1 asks for, carried on the record
                # rather than only implied by a nonzero float.
                "reason": UNEXERCISED_SUPPORTING_TARGET,
                "unexercised_supporting_mass": mass,
                "embedded_certification_credit": float(
                    getattr(cell, "embedded_certification_credit", 0.0) or 0.0
                ),
                "direct_certification_credit": float(
                    getattr(cell, "direct_certification_credit", 0.0) or 0.0
                ),
            }
        )
    unexercised.sort(key=lambda row: (-row["unexercised_supporting_mass"], row["facet_id"]))

    return {
        "attempts_with_observations": len(observations),
        "declared_observations": declared,
        "opportunistic_observations": opportunistic,
        "distinct_opportunistic_facets": len(by_facet),
        "opportunistic_concentration": concentration,
        "top_opportunistic_facets": sorted(
            ({"facet_id": facet, "count": count} for facet, count in by_facet.items()),
            key=lambda row: (-row["count"], row["facet_id"]),
        )[:10],
        "unexercised_supporting_cells": unexercised[:20],
        "unexercised_supporting_cell_count": len(unexercised),
    }
