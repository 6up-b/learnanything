"""Unresolved-cause-set probe targeting (knowledge-model §11.1).

Implements the §11.1 probe/episode priority order over the task graph, capability
ledger, and observation provenance, so a diagnostic targets what actually needs
discriminating instead of re-establishing settled facts. Priority (rough order):

1. an unresolved failure **cause set** whose candidates imply different
   episode repair classes -> select an instrument that DISCRIMINATES the candidate
   causes (KM4 contrast bindings / compositional records);
2. capability-direct-vs-prior disagreement -> stays SHADOW (§11.1 item 2;
   `episode_priority_disagreement` earns live authority only on held-out data);
3. the least-certain **bottleneck** requirement shared across at-risk blueprints;
4. the **integration condition** — components strong AND direct integrated
   performance weak -> probe coordination/selection, NOT the components again;
5. **transfer** to a new independent surface family.

Plus the suppression rule: if strong downstream `embedded` evidence already
demonstrates a prerequisite facet, early probes MUST NOT re-establish it.

This is the diagnostic instrument-choice path (already "diagnostic", not routine
scheduling); it is conservative and leaves the live EIG ranking untouched except
to prefer a discriminating instrument when an episode targets a cause set.

P2 (spec_causal_attribution_v1 §5.3, principle 8): once a cause set carries P1
hypothesis references, **repair classes are authoritative and there is no facet
fallback**. Facets are the vocabulary under indictment (§0 root cause 8), so
reverting to "two distinct facets ⇒ probe" would reintroduce exactly the
attribution defect the causal spec exists to remove. A P1 cause set whose
hypotheses do not resolve to repair classes is not "not divergent" either — it
is :data:`CAUSE_SET_INCOMPLETE_MAPPING`, a *machine-side backfill* obligation
that must be discharged with machine effort before any learner probe.

Where repair classes come from
------------------------------

``causal_attribution._resolve_repair_mapping`` maps a P1 hypothesis onto a repair
class by matching the hypothesis's OWN authored declarations (``target_ref``, and
its declared criterion ids) against an authored repair suggestion's OWN targets.
Both sides are authored; nothing derives a repair class from a facet, because
"two causes sit on different facets" is exactly the inference §5.3 removes.

The consequence, verified end to end on the mvp-0.7 fixture: a **self-graded**
attempt produces no repair suggestion at all, so every hypothesis it mints is
unmapped with reason ``no_repair_authored`` and the cause set is
``incomplete_repair_mapping``. That is not a bug in this module and it must not
be "fixed" by synthesizing a repair class per target ref — a synthetic class per
facet-capability target would make divergence equivalent to facet difference and
resurrect the removed fallback under a new name. It is a real, typed authoring
gap, carried on every unmapped hypothesis as
:data:`causal_attribution.REPAIR_MAPPING_UNRESOLVED_REASONS` and surfaced through
``unmapped_reasons`` so the backfill knows which remedy it owes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.services.causal_attribution import OPEN_SET_CAUSE_ID
from learnloop.services.goal_certification import (
    demonstrated_capabilities_for_facet,
    lo_certification,
)
from learnloop.vault.models import LearningObject, LoadedVault


# --- cause-set repair-mapping states ----------------------------------------
#
# Vocabulary parity with `causal_probe_coherence.rung_divergence_gate`, which
# publishes the same tri-state under its own names
# ("common_cover" | "divergent" | "insufficient_mapping"). The third state means
# the same thing in both modules: BACKFILL machine-side, never buy the missing
# mapping with learner effort (spec principle 8). `COHERENCE_GATE_STATE` is the
# machine-checkable bridge between the two spellings.

CAUSE_SET_COMMON_COVER = "common_cover"
CAUSE_SET_DIVERGENT = "divergent"
CAUSE_SET_INCOMPLETE_MAPPING = "incomplete_repair_mapping"

CAUSE_SET_STATES = (
    CAUSE_SET_COMMON_COVER,
    CAUSE_SET_DIVERGENT,
    CAUSE_SET_INCOMPLETE_MAPPING,
)

COHERENCE_GATE_STATE = {
    CAUSE_SET_COMMON_COVER: "common_cover",
    CAUSE_SET_DIVERGENT: "divergent",
    CAUSE_SET_INCOMPLETE_MAPPING: "insufficient_mapping",
}

# How a cause set's divergence was decided.
MAPPING_BASIS_REPAIR_CLASS = "repair_class"
MAPPING_BASIS_LEGACY_FACET = "legacy_facet"

# Where one candidate cause's repair class came from.
REPAIR_BASIS_CAUSE_ROW = "cause_row"
REPAIR_BASIS_HYPOTHESIS_RECORD = "hypothesis_record"
REPAIR_BASIS_UNRESOLVED = "unresolved"

# Statuses that take a candidate cause out of the active (still-plausible) set.
_INACTIVE_CAUSE_STATUSES = frozenset(
    {"retired", "demoted", "refuted", "ruled_out", "resolved"}
)


# --- suppression (§11.1 final clause) ---------------------------------------


def prerequisite_already_demonstrated(
    vault: LoadedVault, repository: Repository, facet: str, capability: str
) -> bool:
    """True when a facet-capability already has direct/embedded certification.

    Reads the capability ledger (embedded evidence carries certification credit),
    so a prerequisite demonstrated downstream is not re-probed (§11.1)."""

    return capability in demonstrated_capabilities_for_facet(vault, repository, facet)


def should_suppress_prerequisite_probe(
    vault: LoadedVault, repository: Repository, prerequisite: dict[str, str]
) -> bool:
    facet = str(prerequisite.get("facet") or "")
    capability = str(prerequisite.get("capability") or "")
    if not facet or not capability:
        return False
    return prerequisite_already_demonstrated(vault, repository, facet, capability)


# --- cause-set discrimination (§11.1 priority 1) ----------------------------


@dataclass(frozen=True)
class CauseSetTargeting:
    """One open cause set plus its typed repair-mapping state.

    ``state`` is the tri-state above. Only :data:`CAUSE_SET_DIVERGENT` is a
    learner-probe target; :data:`CAUSE_SET_INCOMPLETE_MAPPING` is a machine-side
    backfill obligation and :data:`CAUSE_SET_COMMON_COVER` needs no probe at all.
    """

    causes: list[dict[str, Any]]
    state: str
    basis: str
    repair_class_ids: tuple[str, ...] = ()
    unmapped_hypothesis_ids: tuple[str, ...] = ()
    #: hypothesis_id -> P1's typed reason it carries no repair class. Names the
    #: machine-side remedy the backfill owes; empty when nothing is unmapped.
    unmapped_reasons: tuple[tuple[str, str], ...] = ()
    facets: tuple[str, ...] = ()
    factor_id: str | None = None
    attempt_id: str | None = None
    reason: str = ""

    @property
    def probe_worthy(self) -> bool:
        """True only for a genuinely divergent set — never for missing data."""

        return self.state == CAUSE_SET_DIVERGENT

    @property
    def needs_machine_backfill(self) -> bool:
        return self.state == CAUSE_SET_INCOMPLETE_MAPPING

    @property
    def coherence_gate_state(self) -> str:
        """The same state spelled in `causal_probe_coherence`'s vocabulary."""

        return COHERENCE_GATE_STATE[self.state]

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "coherence_gate_state": self.coherence_gate_state,
            "basis": self.basis,
            "probe_worthy": self.probe_worthy,
            "repair_class_ids": list(self.repair_class_ids),
            "unmapped_hypothesis_ids": list(self.unmapped_hypothesis_ids),
            "unmapped_reasons": dict(self.unmapped_reasons),
            "facets": list(self.facets),
            "factor_id": self.factor_id,
            "attempt_id": self.attempt_id,
            "reason": self.reason,
            "candidate_causes": self.causes,
        }


def _is_open_set(cause: Any) -> bool:
    # ``open_set`` is the load-bearing flag; the id check catches a pre-P1 row
    # that carries the placeholder without it. The comparison is against
    # :data:`OPEN_SET_CAUSE_ID` -- the value ``canonical_projection`` actually
    # writes -- not ``probe_hypotheses.H_OTHER``, which lives in the probe-set
    # LABEL namespace and can never appear on a cause row.
    return isinstance(cause, dict) and (
        cause.get("open_set") is True
        or cause.get("hypothesis_id") == OPEN_SET_CAUSE_ID
    )


def concrete_candidate_causes(causes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The closed-world arms of a cause set (the open-set arm is never one)."""

    return [c for c in causes if isinstance(c, dict) and not _is_open_set(c)]


def active_candidate_causes(causes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Concrete causes still in play — retired/refuted arms cannot be probed."""

    active: list[dict[str, Any]] = []
    for cause in concrete_candidate_causes(causes):
        if cause.get("active") is False:
            continue
        if str(cause.get("status") or "").lower() in _INACTIVE_CAUSE_STATUSES:
            continue
        active.append(cause)
    return active


def _resolve_repair_class(
    cause: dict[str, Any],
    repository: Repository | None,
    memo: dict[str, tuple[str | None, str | None]],
) -> tuple[str | None, str, str | None]:
    """Repair class for one cause: inline first, then the hypothesis record.

    The stored `causal_hypotheses` row is a machine-side source; consulting it
    IS the cheap backfill check that must run before a learner probe is even
    considered. Only when it too is empty is the mapping genuinely incomplete.

    Returns ``(repair_class_id, basis, unresolved_reason)``. The third value is
    P1's typed ``causal_attribution.REPAIR_MAPPING_UNRESOLVED_REASONS`` member
    saying WHY no class was authored for this hypothesis, so the backfill this
    routes to knows which remedy it owes instead of receiving a bare id list.
    """

    explicit = cause.get("repair_class_id")
    if explicit:
        return str(explicit), REPAIR_BASIS_CAUSE_ROW, None
    reason = cause.get("repair_class_unresolved_reason")
    reason = str(reason) if reason else None
    hypothesis_id = cause.get("hypothesis_id")
    if hypothesis_id and repository is not None:
        key = str(hypothesis_id)
        if key not in memo:
            record = repository.causal_hypothesis(key) or {}
            value = record.get("repair_class_id")
            stored_reason = record.get("repair_class_unresolved_reason")
            memo[key] = (
                str(value) if value else None,
                str(stored_reason) if stored_reason else None,
            )
        resolved, stored_reason = memo[key]
        if resolved:
            return resolved, REPAIR_BASIS_HYPOTHESIS_RECORD, None
        reason = reason or stored_reason
    return None, REPAIR_BASIS_UNRESOLVED, reason


def classify_cause_set(
    causes: list[dict[str, Any]],
    *,
    repository: Repository | None = None,
    factor_id: str | None = None,
    attempt_id: str | None = None,
    memo: dict[str, tuple[str | None, str | None]] | None = None,
) -> CauseSetTargeting:
    """Type one cause set as common-cover / divergent / incomplete mapping.

    P1 cause sets (any concrete arm carrying a ``hypothesis_id``) are decided by
    repair classes ONLY. There is deliberately no facet fallback: a P1 arm with
    no resolvable repair class yields ``incomplete_repair_mapping`` so the gap is
    closed machine-side, never by asking the learner to discriminate causes the
    system cannot yet act on differently (§5.3, principle 8).

    Pre-P1 legacy rows carry no hypothesis references and keep the historical
    distinct-facet rule, labelled ``legacy_facet`` so the weaker basis is
    visible rather than silent.
    """

    memo = memo if memo is not None else {}
    merged: list[dict[str, Any]] = []
    concrete: list[dict[str, Any]] = []
    repair_classes: set[str] = set()
    unmapped: list[str] = []
    unmapped_reasons: dict[str, str] = {}
    p1_refs = False
    for cause in causes:
        if not isinstance(cause, dict) or _is_open_set(cause):
            merged.append(cause)
            continue
        if cause.get("hypothesis_id"):
            p1_refs = True
        repair_class_id, basis, unresolved_reason = _resolve_repair_class(
            cause, repository, memo
        )
        if repair_class_id:
            repair_classes.add(repair_class_id)
            if basis == REPAIR_BASIS_HYPOTHESIS_RECORD:
                # Annotate (on a copy) so the pure downstream ranking sees the
                # machine-resolved class without re-querying.
                cause = {
                    **cause,
                    "repair_class_id": repair_class_id,
                    "repair_class_basis": basis,
                }
        elif cause.get("hypothesis_id"):
            hypothesis_id = str(cause["hypothesis_id"])
            unmapped.append(hypothesis_id)
            unmapped_reasons[hypothesis_id] = (
                unresolved_reason or "unrecorded_repair_mapping_gap"
            )
        merged.append(cause)
        concrete.append(cause)

    facets = tuple(
        sorted({str(c.get("facet")) for c in concrete if c.get("facet")})
    )
    classes = tuple(sorted(repair_classes))

    if p1_refs:
        basis = MAPPING_BASIS_REPAIR_CLASS
        if unmapped:
            state = CAUSE_SET_INCOMPLETE_MAPPING
            reason = (
                "P1 hypotheses without a resolvable repair class: "
                + ", ".join(
                    f"{value} ({unmapped_reasons.get(value, 'unknown')})"
                    for value in sorted(set(unmapped))
                )
            )
        elif len(classes) >= 2:
            state = CAUSE_SET_DIVERGENT
            reason = "candidate causes imply different episode repair classes"
        else:
            state = CAUSE_SET_COMMON_COVER
            reason = "one repair class covers every plausible cause"
    else:
        basis = MAPPING_BASIS_LEGACY_FACET
        if len(facets) >= 2:
            state = CAUSE_SET_DIVERGENT
            reason = "legacy pre-P1 cause set spans distinct facets"
        else:
            state = CAUSE_SET_COMMON_COVER
            reason = "legacy pre-P1 cause set has no facet-level divergence"

    return CauseSetTargeting(
        causes=merged,
        state=state,
        basis=basis,
        repair_class_ids=classes,
        unmapped_hypothesis_ids=tuple(sorted(set(unmapped))),
        unmapped_reasons=tuple(sorted(unmapped_reasons.items())),
        facets=facets,
        factor_id=factor_id,
        attempt_id=attempt_id,
        reason=reason,
    )


def open_cause_set_states_for_learning_object(
    vault: LoadedVault, repository: Repository, learning_object_id: str
) -> list[CauseSetTargeting]:
    """Every open, open-world cause set on this LO with its typed state.

    Unlike :func:`open_cause_sets_for_learning_object` this does NOT drop the
    non-probe-worthy sets: ``incomplete_repair_mapping`` in particular has to
    reach a caller that can enqueue the machine-side backfill.
    """

    lo_attempts: set[str] = set()
    for attempt in repository.canonical_observation_ledger():
        item = vault.practice_items.get(attempt["practice_item_id"])
        if item is not None and item.learning_object_id == learning_object_id:
            lo_attempts.add(str(attempt["attempt_id"]))

    states: list[CauseSetTargeting] = []
    seen: set[tuple[str, ...]] = set()
    memo: dict[str, str | None] = {}
    for attempt_id in sorted(lo_attempts):
        for factor in repository.unresolved_cause_factors_for_attempt(attempt_id, status="open"):
            causes = [
                (
                    {
                        **dict(cause),
                        "causal_hypothesis_id": cause.get("hypothesis_id"),
                        "hypothesis_id": "H_OTHER",
                    }
                    if isinstance(cause, dict) and cause.get("open_set") is True
                    else cause
                )
                for cause in factor.get("candidate_causes") or []
            ]
            # P0-era authored cause sets are not safe probe targets until they
            # carry the explicit open-world arm. Otherwise learner effort would
            # be spent discriminating between an accidentally closed pair.
            if not any(_is_open_set(cause) for cause in causes):
                continue
            targeting = classify_cause_set(
                causes,
                repository=repository,
                factor_id=str(factor.get("id")) if factor.get("id") else None,
                attempt_id=attempt_id,
                memo=memo,
            )
            key = tuple(
                sorted(
                    (
                        f"repair:{c.get('repair_class_id')}"
                        if c.get("repair_class_id")
                        else (
                            f"hypothesis:{c.get('hypothesis_id')}"
                            if c.get("hypothesis_id")
                            else f"{c.get('facet')}#{c.get('capability')}"
                        )
                    )
                    for c in concrete_candidate_causes(targeting.causes)
                )
            )
            if key in seen:
                continue
            seen.add(key)
            states.append(targeting)
    return states


def open_cause_sets_for_learning_object(
    vault: LoadedVault, repository: Repository, learning_object_id: str
) -> list[list[dict[str, Any]]]:
    """Probe-worthy candidate-cause sets from open factors on this LO.

    Only cause sets whose candidates imply *different episode repair classes*
    qualify. Pre-P1 legacy rows have no repair-class ids and retain their
    distinct-facet compatibility rule; P1 hypothesis refs never fall back to
    facets, and an unmapped P1 arm is withheld here (it surfaces through
    :func:`open_cause_set_states_for_learning_object` /
    :func:`repair_mapping_backfills` as a machine-side check instead).
    """

    return [
        targeting.causes
        for targeting in open_cause_set_states_for_learning_object(
            vault, repository, learning_object_id
        )
        if targeting.probe_worthy
    ]


def repair_mapping_backfills(
    vault: LoadedVault, repository: Repository, learning_object_id: str
) -> list[dict[str, Any]]:
    """Machine-side checks owed before any probe on this LO can be offered."""

    return [
        {
            "kind": "repair_class_mapping_backfill",
            "state": targeting.state,
            "coherence_gate_state": targeting.coherence_gate_state,
            "factor_id": targeting.factor_id,
            "attempt_id": targeting.attempt_id,
            "hypothesis_ids": list(targeting.unmapped_hypothesis_ids),
            # Which remedy each gap owes (author a repair / re-target it /
            # disambiguate rivals / localize the hypothesis). Without this the
            # check is an id list a consumer cannot act on.
            "unmapped_reasons": dict(targeting.unmapped_reasons),
            "repair_class_ids": list(targeting.repair_class_ids),
            "reason": targeting.reason,
            "learner_actionable": False,
        }
        for targeting in open_cause_set_states_for_learning_object(
            vault, repository, learning_object_id
        )
        if targeting.needs_machine_backfill
    ]


# --- repair-aware instrument ranking ----------------------------------------


@dataclass(frozen=True)
class RankedInstrument:
    eligible: Any
    scores: dict[str, Any] = field(default_factory=dict)

    @property
    def item_id(self) -> str:
        return str(getattr(getattr(self.eligible, "item", None), "id", ""))


@dataclass(frozen=True)
class InstrumentRanking:
    """Ranked eligible instruments plus the rationale that ordered them."""

    ranked: tuple[RankedInstrument, ...]
    cause_set_state: str
    basis: str
    legacy_facet_fallback: bool = False
    unmapped_hypothesis_ids: tuple[str, ...] = ()

    @property
    def selected(self) -> Any | None:
        return self.ranked[0].eligible if self.ranked else None

    def as_dict(self) -> dict[str, Any]:
        return {
            "cause_set_state": self.cause_set_state,
            "basis": self.basis,
            # Facet coverage is a pre-P1 heuristic kept only for legacy cause
            # sets; when it decides, the receipt says so out loud.
            "facet_coverage_status": "legacy_fallback",
            "legacy_facet_fallback": self.legacy_facet_fallback,
            "unmapped_hypothesis_ids": list(self.unmapped_hypothesis_ids),
            "ranked": [
                {"item_id": entry.item_id, **entry.scores} for entry in self.ranked
            ],
        }


def _candidate_labels(cause: dict[str, Any]) -> tuple[str, ...]:
    """Episode hypothesis labels this candidate cause could be observed under."""

    labels: list[str] = []
    for key in ("probe_label", "hypothesis_label", "episode_label"):
        value = cause.get(key)
        if value:
            labels.append(str(value))
    target_ref = cause.get("target_ref")
    misconception_id = cause.get("misconception_id")
    if isinstance(target_ref, dict) and target_ref.get("kind") == "misconception":
        misconception_id = misconception_id or target_ref.get("misconception_id")
    if misconception_id:
        labels.append(f"misconception:{misconception_id}")
    confused = cause.get("confused_with_concept") or cause.get("confusable_concept")
    if confused:
        labels.append(f"confuses_with:{confused}")
    return tuple(dict.fromkeys(labels))


def _candidate_slots(cause: dict[str, Any], eligible: Any) -> frozenset[str]:
    """Instrument rows this candidate cause can land on, if any are resolvable."""

    slot_map = dict(getattr(eligible, "slot_map", None) or {})
    if not slot_map:
        return frozenset()
    labels = _candidate_labels(cause)
    slots = {slot_map[label] for label in labels if label in slot_map}
    if slots:
        return frozenset(slots)
    reason = cause.get("triage_reason")
    if not reason:
        return frozenset()
    from learnloop.services.probe_hypotheses import triage_reason_for_label

    return frozenset(
        slot
        for label, slot in slot_map.items()
        if triage_reason_for_label(label) == str(reason)
    )


def _instrument_action(eligible: Any, keys: frozenset[str] | tuple[str, ...]) -> str | None:
    actions = dict(
        getattr(getattr(eligible, "instrument", None), "instructional_actions", None) or {}
    )
    for key in keys:
        if actions.get(key):
            return str(actions[key])
    return None


def _score_instrument(
    eligible: Any,
    actives: list[dict[str, Any]],
    cause_facets: set[str],
) -> dict[str, Any]:
    slots = [_candidate_slots(cause, eligible) for cause in actives]
    actions = [
        _instrument_action(eligible, slots[index] | frozenset(_candidate_labels(cause)))
        for index, cause in enumerate(actives)
    ]
    separated_pairs = 0
    repair_pairs: set[tuple[str, str]] = set()
    action_pairs = 0
    separated_actions: set[str] = set()
    for left, right in combinations(range(len(actives)), 2):
        slots_left, slots_right = slots[left], slots[right]
        if not slots_left or not slots_right or slots_left & slots_right:
            continue
        separated_pairs += 1
        repair_left = actives[left].get("repair_class_id")
        repair_right = actives[right].get("repair_class_id")
        if repair_left and repair_right and str(repair_left) != str(repair_right):
            repair_pairs.add(
                tuple(sorted((str(repair_left), str(repair_right))))  # type: ignore[arg-type]
            )
        action_left, action_right = actions[left], actions[right]
        if action_left and action_right and action_left != action_right:
            action_pairs += 1
            separated_actions.update({action_left, action_right})
    target_facets = set(getattr(getattr(eligible, "instrument", None), "target_facets", ()) or ())
    return {
        # Action-relevant discrimination first: separating two causes that would
        # be repaired the same way changes nothing.
        "repair_class_pairs_separated": len(repair_pairs),
        "expected_action_change": action_pairs,
        "distinct_actions": sorted(separated_actions),
        "active_candidate_pairs_separated": separated_pairs,
        # Legacy pre-P1 heuristic, retained only as the last discriminating key.
        "facet_coverage": len(cause_facets & target_facets),
        "predictive_information_rate": float(
            getattr(eligible, "predictive_information_rate", 0.0) or 0.0
        ),
        "expected_information_gain": float(
            getattr(eligible, "expected_information_gain", 0.0) or 0.0
        ),
    }


def rank_discriminating_instruments(
    candidate_causes: list[dict[str, Any]],
    eligible: list[Any],
    *,
    repository: Repository | None = None,
) -> InstrumentRanking:
    """Rank eligible instruments for a cause set, repair-class first.

    Ordering keys, highest priority first:

    1. active-candidate pairs separated into **different repair classes**;
    2. expected action change (distinct instructional actions across the
       separated candidates);
    3. active-candidate discrimination irrespective of action;
    4. facet coverage — LEGACY FALLBACK ONLY, labelled as such in
       :meth:`InstrumentRanking.as_dict` so it never decides silently;
    5. the pre-ranked EIG order (predictive rate, then hypothesis EIG).
    """

    targeting = classify_cause_set(candidate_causes, repository=repository)
    if not eligible:
        return InstrumentRanking(
            ranked=(),
            cause_set_state=targeting.state,
            basis="no_eligible_instrument",
            unmapped_hypothesis_ids=targeting.unmapped_hypothesis_ids,
        )
    if not targeting.probe_worthy:
        # Not a discriminating context: keep the plain EIG order and say why.
        return InstrumentRanking(
            ranked=tuple(RankedInstrument(eligible=item) for item in eligible),
            cause_set_state=targeting.state,
            basis="eig_order",
            unmapped_hypothesis_ids=targeting.unmapped_hypothesis_ids,
        )

    actives = active_candidate_causes(targeting.causes)
    cause_facets = set(targeting.facets)
    scored = [
        RankedInstrument(eligible=item, scores=_score_instrument(item, actives, cause_facets))
        for item in eligible
    ]
    scored.sort(
        key=lambda entry: (
            -entry.scores["repair_class_pairs_separated"],
            -entry.scores["expected_action_change"],
            -entry.scores["active_candidate_pairs_separated"],
            -entry.scores["facet_coverage"],
            -entry.scores["predictive_information_rate"],
            -entry.scores["expected_information_gain"],
            entry.item_id,
        )
    )
    top = scored[0].scores
    if top["repair_class_pairs_separated"]:
        basis = "repair_class_discrimination"
    elif top["expected_action_change"]:
        basis = "expected_action_change"
    elif top["active_candidate_pairs_separated"]:
        basis = "active_candidate_discrimination"
    elif top["facet_coverage"]:
        basis = "legacy_facet_coverage"
    else:
        basis = "eig_order"
    return InstrumentRanking(
        ranked=tuple(scored),
        cause_set_state=targeting.state,
        basis=basis,
        legacy_facet_fallback=basis == "legacy_facet_coverage",
        unmapped_hypothesis_ids=targeting.unmapped_hypothesis_ids,
    )


def select_discriminating_instrument(
    candidate_causes: list[dict[str, Any]],
    eligible: list[Any],
    *,
    repository: Repository | None = None,
) -> Any | None:
    """Pick the eligible instrument that best discriminates the candidate causes.

    Thin wrapper over :func:`rank_discriminating_instruments` — see there for the
    ordering. Callers that need the rationale for a receipt should use the
    ranking directly.
    """

    return rank_discriminating_instruments(
        candidate_causes, eligible, repository=repository
    ).selected


def next_cause_set_instrument(
    vault: LoadedVault,
    repository: Repository,
    episode: Any,
    *,
    candidate_causes: list[dict[str, Any]] | None = None,
) -> Any | None:
    """Serve the discriminating instrument for a cause-set diagnostic episode.

    Entering a diagnostic for a cause set selects instruments that discriminate
    between the candidate causes (§11.1) rather than the plain top-EIG instrument.
    """

    from learnloop.services.probe_episodes import eligible_instruments

    if candidate_causes is None:
        cause_sets = open_cause_sets_for_learning_object(vault, repository, episode.learning_object_id)
        candidate_causes = cause_sets[0] if cause_sets else []
    eligible = eligible_instruments(vault, repository, episode)
    if not candidate_causes:
        return eligible[0] if eligible else None
    return select_discriminating_instrument(
        candidate_causes, eligible, repository=repository
    )


# --- integration condition (§11.1 priority 4) -------------------------------


def integration_condition_target(
    vault: LoadedVault, repository: Repository, learning_object: LearningObject
) -> dict[str, Any] | None:
    """Components strong AND integration weak -> probe coordination, not components.

    Returns the integration (coordination) target when every component is
    demonstrated but an integration factor is not — never a component target.
    """

    cert = lo_certification(vault, repository, learning_object)
    if cert.integration_gaps and not cert.component_gaps:
        return {
            "facet": cert.integration_gaps[0],
            "capability": "coordination",
            "reason": "integration_condition",
            "integration_gaps": list(cert.integration_gaps),
        }
    return None


# --- §11.1 priority orchestrator --------------------------------------------


def probe_priority(
    vault: LoadedVault,
    repository: Repository,
    learning_object: LearningObject,
    *,
    bottleneck: dict[str, Any] | None = None,
    transfer_target: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve the §11.1 priority order into one selected diagnostic target.

    Higher-priority signals win. Capability-direct-vs-prior disagreement (item 2)
    is reported under ``shadow`` only — it never becomes the live selected target
    until it earns held-out validation.

    A cause set with an unresolved P1 repair mapping is reported as a
    ``incomplete_repair_mapping`` entry (``learner_actionable: False``) and under
    ``machine_checks``. It is never ``selected``: the missing mapping is bought
    with machine effort, not with a learner probe (principle 8).
    """

    lo_id = learning_object.id
    considered: list[dict[str, Any]] = []
    machine_checks: list[dict[str, Any]] = []

    # Drop candidate causes whose prerequisite is already demonstrated downstream,
    # then RE-classify: suppression can collapse a divergent set.
    filtered: list[CauseSetTargeting] = []
    for targeting in open_cause_set_states_for_learning_object(vault, repository, lo_id):
        kept = [
            cause
            for cause in targeting.causes
            if not should_suppress_prerequisite_probe(vault, repository, cause)
        ]
        filtered.append(
            classify_cause_set(
                kept,
                repository=repository,
                factor_id=targeting.factor_id,
                attempt_id=targeting.attempt_id,
            )
        )
    probe_worthy = [entry for entry in filtered if entry.probe_worthy]
    if probe_worthy:
        considered.append(
            {
                "priority": 1,
                "kind": "cause_set_discrimination",
                "learner_actionable": True,
                "candidate_causes": probe_worthy[0].causes,
                "cause_set": probe_worthy[0].as_dict(),
            }
        )
    for entry in filtered:
        if not entry.needs_machine_backfill:
            continue
        check = {
            "kind": "repair_class_mapping_backfill",
            "state": entry.state,
            "coherence_gate_state": entry.coherence_gate_state,
            "factor_id": entry.factor_id,
            "attempt_id": entry.attempt_id,
            "hypothesis_ids": list(entry.unmapped_hypothesis_ids),
            "unmapped_reasons": dict(entry.unmapped_reasons),
            "repair_class_ids": list(entry.repair_class_ids),
            "reason": entry.reason,
            "learner_actionable": False,
        }
        machine_checks.append(check)
        considered.append(
            {
                "priority": 1,
                "kind": CAUSE_SET_INCOMPLETE_MAPPING,
                # Machine-side obligation: visible to callers, never selectable
                # as a learner probe target.
                "learner_actionable": False,
                "machine_check": check,
                "cause_set": entry.as_dict(),
            }
        )

    if bottleneck is not None and not should_suppress_prerequisite_probe(vault, repository, bottleneck):
        considered.append(
            {
                "priority": 3,
                "kind": "bottleneck",
                "learner_actionable": True,
                "target": bottleneck,
            }
        )

    integration = integration_condition_target(vault, repository, learning_object)
    if integration is not None:
        considered.append(
            {
                "priority": 4,
                "kind": "integration_condition",
                "learner_actionable": True,
                "target": integration,
            }
        )

    if transfer_target is not None:
        considered.append(
            {
                "priority": 5,
                "kind": "transfer",
                "learner_actionable": True,
                "target": transfer_target,
            }
        )

    considered.sort(key=lambda entry: (entry["priority"], not entry["learner_actionable"]))
    selected = next(
        (entry for entry in considered if entry["learner_actionable"]), None
    )
    return {
        "learning_object_id": lo_id,
        "selected": selected,
        "considered": considered,
        "machine_checks": machine_checks,
        # §11.1 item 2 stays shadow; surfaced for logging, never selected live.
        "shadow": {"capability_disagreement": "shadow_only"},
    }
