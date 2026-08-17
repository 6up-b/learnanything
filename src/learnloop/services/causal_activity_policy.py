"""Single authority for causal activity classification (spec §7, P2).

Every consumer that needs to know "does this attempt feed FSRS / certification /
the assisted lane, and does it close the pre-intervention causal segment?" reads
it from here. Before this module the decision was hardcoded in four places
(``attempts._compute_resolved_grade_application``,
``canonical_projection.ASSISTED_ATTEMPT_TYPES`` + its ``primed`` test,
``facet_evidence_timeline``'s ``primed`` test, and
``causal_probe_coherence.classify_causal_activity``) and they had already
drifted apart.

The policy matrix
-----------------

``policy_for_class`` answers at the level of a **contamination class**:

| class                    | fsrs | certification        | assisted | closes pre-intervention segment |
|--------------------------|------|----------------------|----------|---------------------------------|
| pure_diagnostic          | no   | no                   | no       | no                              |
| instructional_diagnostic | no   | no                   | yes      | yes                             |
| repair_activity          | no   | no                   | yes      | no                              |
| verification             | yes  | yes unless near_clone| no       | no                              |

``classify_attempt_activity`` answers at the level of a **concrete attempt**. It
picks the contamination class from the attempt's signals and then unions in the
legacy assistance channels (``hinted_attempt`` / ``guided_walkthrough`` /
``reconstruction_after_walkthrough`` / ``hints_used > 0``), which are assisted
for §5.4/§6 certification purposes without being causal contamination classes.
So an attempt-level result can carry ``contamination_class == "verification"``
and ``counts_as_assisted is True`` (a hinted attempt): the class describes the
causal instrument, the flag describes the certification lane. An attempt that is
assisted never certifies, so ``eligible_for_certification`` is forced off there
too. FSRS is deliberately NOT forced off for legacy assisted types — a hinted
practice review has always scheduled, and this module does not change that.

Documented divergence from spec §7
----------------------------------

§7 says only:

    "An instructional diagnostic closes the pre-intervention causal segment and
    cannot feed certification or FSRS retention; near-clone probes never
    certify."

Read literally that implies a *pure* diagnostic MAY feed certification and FSRS.
This matrix is deliberately STRICTER: a pure diagnostic feeds neither.

Rationale — a diagnostic instrument measures the locked cause set under a
manipulation contract (§7 manipulation contracts, blind prediction bundles). Its
item is selected to maximise information about competing hypotheses, not to be a
representative retrieval trial, and its administration is under probe assistance
restrictions. Its retention signal is therefore not comparable to a practice
review, and admitting it into FSRS or certification would let instrument
selection silently steer the scheduler and the certification ledger.

This is recorded as a **named, versioned policy choice**
(``CAUSAL_ACTIVITY_POLICY_VERSION``), not an accident. Every cell of the matrix
above is pinned by a test in ``tests/test_causal_activity_policy.py``; changing
one requires editing that test and bumping the version, which is the point.

Conflicting writes
------------------

Two writers already exist for the same attempt (``attempts.apply_attempt``
records ``repair_activity`` when the draft is primed;
``probe_episodes._record_presentation_observation`` records the diagnostic
class). Classification writes are on the attempt hot path and must never raise,
so the substrate is an append-only event log and the current classification is
DERIVED by :data:`CONTAMINATION_PRECEDENCE` — most contaminated wins. See
``migrations/122_causal_activity_events.sql`` and
``Repository.causal_activity_classification``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from learnloop.vault.models import LoadedVault

CAUSAL_ACTIVITY_POLICY_VERSION = "causal_activity_v1"

# Most-contaminated wins on conflicting writes (§4.2). Order is authoritative:
# index 0 is the most contaminated.
CONTAMINATION_PRECEDENCE: tuple[str, ...] = (
    "repair_activity",  # highest
    "instructional_diagnostic",
    "pure_diagnostic",
    "verification",  # lowest
)

CONTAMINATION_CLASSES: frozenset[str] = frozenset(CONTAMINATION_PRECEDENCE)

# Assistance channels that certify nothing (§5.4/§6) but are not themselves
# causal contamination classes. Kept separate from CONTAMINATION_PRECEDENCE so
# the causal vocabulary does not absorb the legacy attempt-type vocabulary.
LEGACY_ASSISTED_ATTEMPT_TYPES: frozenset[str] = frozenset(
    {
        "hinted_attempt",
        "guided_walkthrough",
        "reconstruction_after_walkthrough",
    }
)

DIAGNOSTIC_ATTEMPT_TYPES: frozenset[str] = frozenset({"diagnostic_probe"})

# Compatibility export for readers that still want the flat attempt-type set.
# Prefer ``attempt_counts_as_assisted`` — this set alone cannot see ``primed``
# or ``hints_used`` and is therefore only ever half the decision.
ASSISTED_ATTEMPT_TYPES: frozenset[str] = (
    LEGACY_ASSISTED_ATTEMPT_TYPES | DIAGNOSTIC_ATTEMPT_TYPES
)

# near_clone bases, most specific first. Recorded on the classification so the
# certification-eligibility decision is auditable rather than invisible (§4.3).
NEAR_CLONE_BASES: tuple[str, ...] = (
    "explicit",  # the presentation declared it outright
    "no_source_item",  # nothing was cloned; not a near clone
    "distinct_surface_group",  # fingerprints differ -> not a near clone
    "shared_surface_group",  # fingerprints match -> near clone
    "unknown",  # a source was declared but no fingerprint is computable
)


@dataclass(frozen=True)
class CausalActivityPolicy:
    """The resolved policy for one attempt (or one contamination class)."""

    contamination_class: str
    near_clone: bool
    closes_pre_intervention_segment: bool
    eligible_for_fsrs: bool
    eligible_for_certification: bool
    counts_as_assisted: bool
    policy_version: str = CAUSAL_ACTIVITY_POLICY_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "contamination_class": self.contamination_class,
            "near_clone": self.near_clone,
            "closes_pre_intervention_segment": (
                self.closes_pre_intervention_segment
            ),
            "eligible_for_fsrs": self.eligible_for_fsrs,
            "eligible_for_certification": self.eligible_for_certification,
            "counts_as_assisted": self.counts_as_assisted,
            "policy_version": self.policy_version,
        }


def policy_for_class(
    contamination_class: str, *, near_clone: bool = False
) -> CausalActivityPolicy:
    """The matrix row for one contamination class.

    See the module docstring for the table this implements, including the
    deliberate divergence from spec §7 on ``pure_diagnostic``.
    """

    if contamination_class not in CONTAMINATION_CLASSES:
        raise ValueError(f"unknown contamination class {contamination_class!r}")
    verification = contamination_class == "verification"
    return CausalActivityPolicy(
        contamination_class=contamination_class,
        near_clone=bool(near_clone),
        closes_pre_intervention_segment=(
            contamination_class == "instructional_diagnostic"
        ),
        # Deliberately stricter than §7: no diagnostic administration, pure or
        # instructional, and no repair activity, feeds retention scheduling.
        eligible_for_fsrs=verification,
        # Near-clone probes never certify (§7).
        eligible_for_certification=verification and not near_clone,
        counts_as_assisted=contamination_class
        in {"instructional_diagnostic", "repair_activity"},
        policy_version=CAUSAL_ACTIVITY_POLICY_VERSION,
    )


def contamination_class_for_attempt(
    *,
    attempt_type: str,
    primed: bool = False,
    hints_used: int = 0,
) -> str:
    """The contamination class implied by an attempt's own signals.

    A diagnostic administration that took hints or was primed is instructional
    (instruction leaked into the measurement); otherwise it is pure. A primed
    non-diagnostic attempt is a repair activity — priming IS the intervention.
    Everything else is an ordinary verification-lane attempt.
    """

    assisted_now = bool(primed) or int(hints_used or 0) > 0
    if attempt_type in DIAGNOSTIC_ATTEMPT_TYPES:
        return (
            "instructional_diagnostic" if assisted_now else "pure_diagnostic"
        )
    if primed:
        return "repair_activity"
    return "verification"


def classify_attempt_activity(
    *,
    attempt_type: str,
    primed: bool = False,
    hints_used: int = 0,
    near_clone: bool = False,
    explicit_class: str | None = None,
) -> CausalActivityPolicy:
    """Resolve the full policy for one concrete attempt.

    ``explicit_class`` lets a caller that already knows the causal class (a
    probe presentation, a cold verification) pin it; the attempt signals then
    only contribute the legacy assistance union.
    """

    contamination_class = (
        explicit_class
        if explicit_class is not None
        else contamination_class_for_attempt(
            attempt_type=attempt_type, primed=primed, hints_used=hints_used
        )
    )
    policy = policy_for_class(contamination_class, near_clone=near_clone)
    legacy_assisted = (
        attempt_type in LEGACY_ASSISTED_ATTEMPT_TYPES
        or int(hints_used or 0) > 0
        or bool(primed)
    )
    if not legacy_assisted:
        return policy
    return CausalActivityPolicy(
        contamination_class=policy.contamination_class,
        near_clone=policy.near_clone,
        closes_pre_intervention_segment=(
            policy.closes_pre_intervention_segment
        ),
        eligible_for_fsrs=policy.eligible_for_fsrs,
        # Assisted attempts certify nothing (§5.4/§6).
        eligible_for_certification=False,
        counts_as_assisted=True,
        policy_version=policy.policy_version,
    )


def attempt_counts_as_assisted(
    *, attempt_type: str, primed: bool = False, hints_used: int = 0
) -> bool:
    """The canonical-projection / facet-timeline assistance test.

    One function so the projection and the timeline cannot drift apart again.
    """

    return classify_attempt_activity(
        attempt_type=attempt_type, primed=primed, hints_used=hints_used
    ).counts_as_assisted


def resolve_attempt_activity_policy(
    *,
    attempt_type: str,
    primed: bool = False,
    hints_used: int = 0,
    recorded: Mapping[str, Any] | None = None,
) -> CausalActivityPolicy:
    """Fail-closed attempt policy from immutable signals plus recorded facts.

    The attempt row is always available and is sufficient to identify pure
    diagnostics and legacy assistance.  A recorded classification can add
    richer facts learned later in the pipeline (notably an audited near-clone
    verdict).  Eligibility is therefore the intersection of both authorities,
    while assistance/segment contamination is their union: a later event may
    disqualify evidence, but it can never make an intrinsically ineligible or
    assisted attempt certify.
    """

    inferred = classify_attempt_activity(
        attempt_type=attempt_type,
        primed=primed,
        hints_used=hints_used,
    )
    if recorded is None:
        return inferred
    stored = policy_for_class(
        str(recorded.get("contamination_class") or "verification"),
        near_clone=bool(recorded.get("near_clone")),
    )
    resolved_class = min(
        (inferred.contamination_class, stored.contamination_class),
        key=CONTAMINATION_PRECEDENCE.index,
    )
    combined = policy_for_class(
        resolved_class,
        near_clone=inferred.near_clone or stored.near_clone,
    )
    return CausalActivityPolicy(
        contamination_class=combined.contamination_class,
        near_clone=combined.near_clone,
        closes_pre_intervention_segment=(
            inferred.closes_pre_intervention_segment
            or stored.closes_pre_intervention_segment
        ),
        eligible_for_fsrs=(
            inferred.eligible_for_fsrs and stored.eligible_for_fsrs
        ),
        eligible_for_certification=(
            inferred.eligible_for_certification
            and stored.eligible_for_certification
        ),
        counts_as_assisted=(
            inferred.counts_as_assisted or stored.counts_as_assisted
        ),
        policy_version=CAUSAL_ACTIVITY_POLICY_VERSION,
    )


def resolve_conflicting_classes(existing: str, incoming: str) -> str:
    """Most-contaminated wins. Never raises on a legitimate conflict.

    An unknown class still raises — that is a programming error, not a race
    between two honest writers.
    """

    if existing not in CONTAMINATION_CLASSES:
        raise ValueError(f"unknown contamination class {existing!r}")
    if incoming not in CONTAMINATION_CLASSES:
        raise ValueError(f"unknown contamination class {incoming!r}")
    return min(
        (existing, incoming), key=lambda value: CONTAMINATION_PRECEDENCE.index(value)
    )


# ---------------------------------------------------------------------------
# near_clone (§4.3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NearCloneAssessment:
    """An auditable near-clone verdict.

    The previous implementation treated "this probe was instantiated from a
    source item" as "this probe is a near clone", so every generated probe
    permanently lost certification eligibility and the certification lane read
    as if nothing ever certified. Provenance is not similarity: the verdict is
    now an explicit fingerprint comparison, and ``basis`` records how it was
    reached.
    """

    near_clone: bool
    basis: str
    source_practice_item_id: str | None = None
    surface_group: str | None = None
    source_surface_group: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "near_clone": self.near_clone,
            "near_clone_basis": self.basis,
            "source_practice_item_id": self.source_practice_item_id,
            "surface_group": self.surface_group,
            "source_surface_group": self.source_surface_group,
        }


def assess_near_clone(
    vault: "LoadedVault",
    *,
    practice_item_id: str,
    source_practice_item_id: str | None,
    explicit: bool | None = None,
) -> NearCloneAssessment:
    """Compare the administered item's surface fingerprint against its source.

    ``explicit`` (a presentation that declared ``near_clone`` outright) wins.
    With no declared source there is nothing to be a clone OF. With a declared
    source we compare ``surface_group_id`` — the existing vault-wide
    shared-stimulus / source-family / solution-recipe fingerprint that already
    collapses near clones for evidence purposes (§6). If either item cannot be
    resolved we fail CLOSED (near clone) but record ``basis="unknown"`` so the
    lost certification eligibility is visible rather than silent.
    """

    if explicit is not None:
        return NearCloneAssessment(
            near_clone=bool(explicit),
            basis="explicit",
            source_practice_item_id=source_practice_item_id,
        )
    source_id = str(source_practice_item_id) if source_practice_item_id else None
    if not source_id:
        return NearCloneAssessment(near_clone=False, basis="no_source_item")
    # Local import: canonical_projection imports this module.
    from learnloop.services.canonical_projection import surface_group_id

    item = vault.practice_items.get(str(practice_item_id))
    source_item = vault.practice_items.get(source_id)
    if item is None or source_item is None:
        return NearCloneAssessment(
            near_clone=True,
            basis="unknown",
            source_practice_item_id=source_id,
        )
    group = surface_group_id(item)
    source_group = surface_group_id(source_item)
    same = group == source_group
    return NearCloneAssessment(
        near_clone=same,
        basis="shared_surface_group" if same else "distinct_surface_group",
        source_practice_item_id=source_id,
        surface_group=group,
        source_surface_group=source_group,
    )


def near_clone_from_selection_components(
    vault: "LoadedVault",
    *,
    practice_item_id: str,
    selection_components: Mapping[str, Any] | None,
) -> NearCloneAssessment:
    """``assess_near_clone`` over a probe presentation's selection components."""

    components = dict(selection_components or {})
    declared = components.get("near_clone")
    return assess_near_clone(
        vault,
        practice_item_id=practice_item_id,
        source_practice_item_id=components.get("source_practice_item_id"),
        explicit=bool(declared) if declared is not None else None,
    )
