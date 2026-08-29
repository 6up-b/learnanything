"""Conjunctive instruments — item shape, the two A1 guards, and the posterior
rule that decides which shape to serve.

Spec: ``spec_measurement_efficiency_v1.md`` §3.A1 (conjunctive items with
authored supporting targets); implementation plan item 6.1.

**What A1 changes.** §2 F2 measured that a generated practice item can only ever
fill one column: ``RubricCriterionPayload`` had no ``targets`` field, so
``compile_criterion_targets`` fell back to every criterion -> ``primary`` at the
item's single declared capability, and the ``supporting`` role (weight 0.3,
banked as *embedded* credit, already honoured by the ledger) was structurally
unreachable from the practice-expansion path. Item 6.1 adds the field. This
module owns everything that follows from a criterion now being able to say "this
step *consumes* facet F" rather than only "this step *is* facet F".

**The asymmetry, and why it is safe.** A pass credits every cell — primary at
1.0, supporting at 0.3 as embedded. A failure localizes through first-divergence
(``localize_criterion_outcomes``) and only the diverged facet takes the
negative. Success on a conjunction is strong evidence for every conjunct;
failure is weak evidence about any particular one. The passed-facet write
barrier (causal §1 principle 5) is what makes the negative direction safe, and
A1 depends on that barrier rather than negotiating with it.

**The new exposure is positive smearing**, which the firewall does not cover:
crediting a facet the learner never exercised is a harmful write in the other
sign, and it is more dangerous than the negative kind because nothing contests
it. §3.A1 names three guards; two of them live here and the third is a statement
about §5.3:

1. :func:`partition_supporting_targets` — supporting credit requires trace
   evidence that the facet was actually exercised. Absent that observation the
   target is *recorded* as an ``unexercised_supporting_target`` and confers
   nothing. The observation channel is A6 (item 6.2,
   ``learnloop.attempts.trace_evidence``); before A6 has run on an attempt this
   partition returns every supporting target as unexercised, which is the
   correct reading of "no evidence it was exercised".
2. :func:`cap_embedded_credit` — no cell may take more than
   ``[evidence.certification].max_embedded_credit_share`` of its certification
   credit from embedded observations. A cell whose entire history is supporting
   credit is not demonstrated; it is inferred, and Part II already has an honest
   label for that.
3. Certification is unaffected: embedded credit feeds mass and Ready, and
   whether it may certify is governed by §5.3, never by A1. Nothing here touches
   ``goal_certification``.

**The shape rule (plan item 6.1's amendment to §3.A1).** The measurement spec
asks for ``_BLUEPRINT_SPREAD_RULE`` to be *inverted* — cover the blueprint in as
few honest items as possible. The plan deliberately does not adopt that: a pool
holding only conjunctive items starves diagnosis, because a conjunctive failure
localizes to one facet only when the learner got far enough to diverge somewhere
specific, and a weak learner fails at step 1 of every capstone. So authoring
produces **both** shapes and *selection* picks between them from the posterior:
:func:`conjunctive_fit` prefers a capstone when the learner is predicted to pass
(a pass is what clears several cells at once) and prefers the decomposed item
when they are not (localizing is what a struggling learner's next attempt is
for). The spread rule survives as the authoring rule for the decomposed half.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from learnloop.numeric import clamp

if TYPE_CHECKING:  # pragma: no cover - typing only
    from learnloop.vault.models import CriterionTarget

#: Typed marker for a supporting target that earned nothing because no trace
#: evidence showed the facet exercised (§3.A1 guard 1). Recorded, never silent.
UNEXERCISED_SUPPORTING_TARGET = "unexercised_supporting_target"

#: An item counts as *conjunctive* once its rubric observes this many distinct
#: primary ``(facet, capability)`` cells. Two is the smallest number for which
#: "conjunction" means anything; it is a definition, not a tuning knob.
MIN_CONJUNCTIVE_CELLS = 2

#: Distinct primary cells at which :attr:`ItemShape.conjunctive_strength`
#: saturates. Beyond four conjuncts the marginal cell says little about whether
#: the item is a capstone, and letting the term grow without bound would make
#: shape dominate every other selection component.
CONJUNCTIVE_STRENGTH_CEILING = 4


@dataclass(frozen=True)
class ItemShape:
    """How many independent cells one item's rubric actually observes.

    Derived from the compiled criterion targets rather than stored on the item:
    an authored flag would drift the moment a rubric is edited, and the compile
    path (``capability_mapping.compile_criterion_targets``) is already the one
    authority on what a criterion observes.
    """

    primary_cells: tuple[tuple[str, str], ...]
    supporting_cells: tuple[tuple[str, str], ...]
    criterion_count: int
    has_dependency_chain: bool
    #: Whether the rubric AUTHORED its targets, rather than having them compiled
    #: from the legacy fallback. Load-bearing, and the Stage 6 review is why:
    #: ``compile_criterion_targets`` maps each legacy criterion to its own facet,
    #: so any pre-A1 rubric whose criteria name different facets already yields
    #: two or more primary cells. On ``fixtures/linear_algebra`` -- a vault
    #: authored entirely before A1 -- that was 6 of 55 items, five with no
    #: authored targets at all. Treating those as capstones perturbed
    #: ``selection_reward`` on ordinary content and blinded the calibration
    #: sweep to a genuinely decision-relevant scheduler parameter.
    has_authored_targets: bool = False

    @property
    def is_conjunctive(self) -> bool:
        """Whether this item was AUTHORED as a conjunction.

        Two conditions, not one. The cell count alone describes what the rubric
        happens to observe; the authored flag is what says someone wrote it as a
        single task requiring several components -- which is the claim §3.A1's
        shape rule is about. A legacy rubric with one criterion per facet
        observes several cells and is not a capstone.
        """

        return (
            self.has_authored_targets
            and len(self.primary_cells) >= MIN_CONJUNCTIVE_CELLS
        )

    @property
    def conjunctive_strength(self) -> float:
        """0.0 for a single-cell or unauthored item, rising to 1.0 at the ceiling."""

        if not self.has_authored_targets:
            return 0.0
        extra = len(self.primary_cells) - 1
        if extra <= 0:
            return 0.0
        span = CONJUNCTIVE_STRENGTH_CEILING - 1
        return clamp(extra / span) if span > 0 else 1.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "primary_cells": [list(cell) for cell in self.primary_cells],
            "supporting_cells": [list(cell) for cell in self.supporting_cells],
            "criterion_count": self.criterion_count,
            "has_dependency_chain": self.has_dependency_chain,
            "has_authored_targets": self.has_authored_targets,
            "is_conjunctive": self.is_conjunctive,
            "conjunctive_strength": self.conjunctive_strength,
        }


def classify_item_shape(item, rubric, *, canonical_facet_id=None) -> ItemShape:
    """Compile ``item``'s rubric into an :class:`ItemShape`.

    ``canonical_facet_id`` is the vault's alias resolver when one is available;
    without it the raw authored ids are used, which is correct for callers that
    only need the cell *count*.
    """

    from learnloop.learner.capability_mapping import compile_criterion_targets

    resolve = canonical_facet_id or (lambda facet: facet)
    primary: list[tuple[str, str]] = []
    supporting: list[tuple[str, str]] = []
    criteria = list(getattr(rubric, "criteria", ()) or ()) if rubric is not None else []
    has_dependency = any(getattr(criterion, "depends_on", None) for criterion in criteria)
    authored = any(getattr(criterion, "targets", None) for criterion in criteria)
    for criterion in criteria:
        for target in compile_criterion_targets(item, criterion, resolved_rubric=rubric):
            cell = (str(resolve(target.facet)), str(target.capability))
            bucket = supporting if target.role == "supporting" else primary
            if cell not in bucket:
                bucket.append(cell)
    # A cell observed both ways is a primary cell: the stronger observation wins,
    # exactly as ``precedence`` works for measurement-state labels.
    supporting = [cell for cell in supporting if cell not in primary]
    return ItemShape(
        primary_cells=tuple(sorted(primary)),
        supporting_cells=tuple(sorted(supporting)),
        criterion_count=len(criteria),
        has_dependency_chain=has_dependency,
        has_authored_targets=authored,
    )


# -- Guard 1: supporting credit requires trace evidence ------------------------


@dataclass(frozen=True)
class SupportingPartition:
    """Which of a criterion's supporting targets earned credit, and which did not."""

    exercised: tuple["CriterionTarget", ...]
    unexercised: tuple["CriterionTarget", ...]

    @property
    def unexercised_cells(self) -> tuple[tuple[str, str], ...]:
        return tuple((target.facet, target.capability) for target in self.unexercised)


def supporting_unexercised(target, exercised_facets, *, resolve=None) -> bool:
    """Whether ``target`` is a supporting claim the trace did not support.

    The per-target predicate behind :func:`partition_supporting_targets`, split
    out so the projection can call it inline over an allocation without building
    a partition per criterion. A ``primary`` target is never "unexercised" — the
    criterion outcome *is* its evidence.
    """

    if getattr(target, "role", "primary") != "supporting":
        return False
    facet = str((resolve or (lambda value: value))(target.facet))
    return facet not in exercised_facets


def partition_supporting_targets(
    targets,
    exercised_facets,
    *,
    canonical_facet_id=None,
) -> SupportingPartition:
    """Split supporting targets by whether the trace showed the facet exercised.

    ``exercised_facets`` is the set of canonical facet ids A6 observed in this
    attempt's trace
    (``learnloop.attempts.trace_evidence.exercised_facets_for_attempt``).
    Primary targets are not partitioned — they are the step the criterion owns,
    and the criterion outcome IS their evidence.

    Matching is on the **facet**, not the ``(facet, capability)`` cell: A6's
    observation is "the trace shows this facet being used", and the capability
    at which that use counts is decided by the criterion's own authored target,
    not by the grader. Letting the grader pick the capability would hand a
    model-reported field authority over the ledger cell, which is standing
    constraint 8 inverted.
    """

    resolve = canonical_facet_id or (lambda facet: facet)
    seen = {str(resolve(facet)) for facet in (exercised_facets or ())}
    exercised: list[Any] = []
    unexercised: list[Any] = []
    for target in targets:
        if getattr(target, "role", "primary") != "supporting":
            continue
        # One predicate, shared with the projection and the receipt fold. Two
        # copies of a safety guard is exactly the kind of thing that drifts.
        if supporting_unexercised(target, seen, resolve=resolve):
            unexercised.append(target)
        else:
            exercised.append(target)
    return SupportingPartition(exercised=tuple(exercised), unexercised=tuple(unexercised))


# -- Guard 2: the embedded-share cap -------------------------------------------


def cap_embedded_credit(
    direct_credit: float,
    embedded_credit: float,
    *,
    max_embedded_share: float,
) -> float:
    """Total certification credit for a cell, with embedded credit capped.

    Returns ``direct + min(embedded, allowance)`` where ``allowance`` is the
    largest embedded contribution whose share of the total stays at or below
    ``max_embedded_share``.

    Two boundary cases carry the guard's meaning and both are deliberate:

    * ``direct_credit == 0`` with ``max_embedded_share < 1`` yields **0**. A cell
      whose entire history is supporting credit is not demonstrated. It is not
      zero *evidence* — the mass is still in the ledger and Part II may label the
      cell ``inferred`` — it is zero *certification credit*, which is the only
      quantity ``capability_grid`` reads for Demonstrated.
    * ``max_embedded_share >= 1`` disables the cap entirely, for a vault that
      wants A1's throughput before the delayed cold probe (§5.7) has enough
      cohorts to detect positive smearing.
    """

    direct = max(0.0, float(direct_credit))
    embedded = max(0.0, float(embedded_credit))
    share = float(max_embedded_share)
    if share >= 1.0:
        return direct + embedded
    if share <= 0.0:
        return direct
    # embedded / (direct + embedded) <= share  <=>  embedded <= direct*share/(1-share)
    allowance = direct * share / (1.0 - share)
    return direct + min(embedded, allowance)


# -- The shape rule: which shape to serve, from the posterior -------------------


def conjunctive_fit(shape: ItemShape, predicted_correctness: float, *, localizing: bool) -> float:
    """Selection preference for ``shape`` given the current posterior.

    Returns a value in ``[-1, 1]`` scaled by :attr:`ItemShape.conjunctive_strength`,
    so a single-cell item always scores exactly 0 and the term can never move a
    pool that has no conjunctive items at all.

    * ``localizing`` (the REPAIR intent): a flat **penalty** proportional to
      conjunctive strength. Repair exists to find out which step is broken, and a
      capstone answers that question worst — a learner who fails at step 1 tells
      you nothing about steps 2-4, which is the same first-error localization the
      projection already applies.
    * otherwise: ``(2p - 1)`` scaled by strength. Above 50% predicted success a
      capstone is the efficient instrument (a pass clears every conjunct); below
      it the decomposed item is, because the likely outcome is a failure that
      localizes to one facet.

    The PROBE intent deliberately does not call this: probe selection is already
    ranked by expected information gain over a hypothesis set, and adding a
    second shape term there would double-count the same argument.
    """

    strength = shape.conjunctive_strength
    if strength <= 0.0:
        return 0.0
    if localizing:
        return -strength
    return clamp(2.0 * float(predicted_correctness) - 1.0, -1.0, 1.0) * strength
