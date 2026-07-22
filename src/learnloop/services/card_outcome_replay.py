"""P1 step 10 -- U-015 event-sufficiency replay prototype (spec §1, §9.7, §9.8).

Card psychometrics (difficulty, discrimination, rubric calibration) accrue as a
*deferred projection* over the same administration/observation events P1 already
records -- P1 adds no psychometrics schema. This module is the proof that the
projection is later buildable with **zero schema changes**: it computes per-card
outcome counts stratified by administration context using ONLY ledger events
(``activity_administrations`` + ``activity_observations`` + the ``grade_interpretations``
head), never a live projection table, and emits those counts in the exact shape the
deferred hierarchical likelihood model consumes (U-014 resume path).

Determinism (§9.7): the accumulation is a pure fold over events sorted by a stable key;
:func:`replay_event_stream` replays a synthetic 10k-event stream deterministically and
reports its algorithm/version manifest.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

# The version manifest reported by every replay (§9.7 "reports its algorithm/version
# manifest"). Bump the algorithm version if the fold semantics ever change.
REPLAY_MANIFEST: dict[str, Any] = {
    "replay_algorithm": "card_outcome_counts",
    "replay_algorithm_version": "v1",
    "context_schema_version": 1,
    "outcome_class_source": "grade_interpretation_head|raw_observed_class",
    "ledger_tables": [
        "activity_administrations",
        "activity_observations",
        "grade_interpretations",
    ],
    "reads_live_tables": False,
    "u014_resume_shape_version": "v1",
}

# The administration-context dimensions that stratify counts (§9.8 "stratified by
# administration context"). A stable, sorted subset of the §3.10 context: cold vs
# scaffolded, hint/feedback exposure, tool/source visibility, and reading phase.
_CONTEXT_DIMENSIONS: tuple[str, ...] = (
    "cold",
    "scaffolded",
    "hints_used",
    "feedback_exposed",
    "source_visible",
    "open_book",
    "reading_phase",
)


def context_key(admin_context: Mapping[str, Any] | None, reading_phase: str | None = None) -> str:
    """A canonical, deterministic stratum key over the §3.10 administration context.

    Absent dimensions collapse to a stable ``unknown`` token (never silently dropped),
    so the stratification is total and replay is order-independent."""

    ctx = dict(admin_context or {})
    if reading_phase is not None and "reading_phase" not in ctx:
        ctx["reading_phase"] = reading_phase
    parts = []
    for dim in _CONTEXT_DIMENSIONS:
        value = ctx.get(dim, "unknown")
        if isinstance(value, bool):
            value = "true" if value else "false"
        parts.append(f"{dim}={value}")
    return "|".join(parts)


def outcome_class_for_response_posterior(response_posterior: Mapping[str, Any] | None) -> str | None:
    """Argmax outcome class of a grade interpretation's response posterior ``P(Z|E)``.

    Ties break on the lexicographically smallest class for determinism. ``None`` when
    no posterior is available (the caller falls back to the raw observed class)."""

    if not response_posterior:
        return None
    items = sorted(response_posterior.items(), key=lambda kv: (-float(kv[1]), str(kv[0])))
    return str(items[0][0])


@dataclass
class ReplayResult:
    """Per-card outcome counts stratified by administration context, plus the manifest.

    ``counts[card_version_id][context_key][outcome_class] -> int``.
    ``events_replayed`` and ``administrations_missing_fields`` support the §9.8
    completeness assertions (every admin/obs pair carries card version + outcome +
    context)."""

    counts: "CountsByCardContext"
    events_replayed: int
    administrations_missing_fields: list[str] = field(default_factory=list)
    manifest: dict[str, Any] = field(default_factory=lambda: dict(REPLAY_MANIFEST))

    def as_dict(self) -> dict[str, Any]:
        return {
            "counts": {
                card: {ctx: dict(classes) for ctx, classes in strata.items()}
                for card, strata in self.counts.items()
            },
            "events_replayed": self.events_replayed,
            "administrations_missing_fields": list(self.administrations_missing_fields),
            "manifest": dict(self.manifest),
        }


# counts[card_version_id][context_key][outcome_class] -> int
CountsByCardContext = dict[str, dict[str, dict[str, int]]]


def _empty_counts() -> CountsByCardContext:
    return defaultdict(lambda: defaultdict(lambda: defaultdict(int)))


@dataclass(frozen=True)
class NormalizedEvent:
    """One administration/observation pair reduced to the fields the projection needs."""

    sort_key: str
    card_version_id: str | None
    outcome_class: str | None
    context: str


def _accumulate(events: Iterable[NormalizedEvent]) -> ReplayResult:
    """Deterministic fold. Sorting by the stable key makes the result independent of
    input order -- the property the 10k-event determinism test relies on (§9.7)."""

    ordered = sorted(events, key=lambda e: e.sort_key)
    counts = _empty_counts()
    missing: list[str] = []
    replayed = 0
    for event in ordered:
        replayed += 1
        if not event.card_version_id or not event.outcome_class:
            # §9.8: every admin/obs pair MUST carry card version id + outcome class +
            # context. A missing field is a sufficiency violation the caller asserts on.
            missing.append(event.sort_key)
            continue
        counts[event.card_version_id][event.context][event.outcome_class] += 1
    # Freeze the defaultdicts into plain dicts for a stable, serializable result.
    frozen: CountsByCardContext = {
        card: {ctx: dict(classes) for ctx, classes in strata.items()}
        for card, strata in counts.items()
    }
    return ReplayResult(counts=frozen, events_replayed=replayed, administrations_missing_fields=missing)


def replay_card_outcome_counts(repository: Any) -> ReplayResult:
    """The U-015 event-sufficiency prototype (§9.8). Compute per-card outcome counts
    stratified by administration context from ledger events ALONE.

    Reads only ``activity_administrations`` (card version id + context) and, per
    administration, its ``activity_observations`` and the active ``grade_interpretation``
    head (outcome class). No live projection table is read -- the whole point of the
    U-015 guarantee. The result is emitted in the U-014 resume shape via
    :func:`u014_resume_shape`."""

    normalized: list[NormalizedEvent] = []
    for admin in repository.all_activity_administrations():
        admin_id = admin["id"]
        card_version_id = admin.get("card_version_id")
        admin_context = _loads(admin.get("admin_context_json"))
        ctx = context_key(admin_context, admin.get("reading_phase"))
        observations = repository.observations_for_administration(admin_id)
        if not observations:
            # An administration with no response yet contributes context but no outcome.
            normalized.append(
                NormalizedEvent(sort_key=admin_id, card_version_id=card_version_id, outcome_class=None, context=ctx)
            )
            continue
        for obs in observations:
            outcome = _outcome_class_from_ledger(repository, obs)
            normalized.append(
                NormalizedEvent(
                    sort_key=f"{admin['created_at']}|{admin_id}|{obs['id']}",
                    card_version_id=card_version_id,
                    outcome_class=outcome,
                    context=ctx,
                )
            )
    return _accumulate(normalized)


def _outcome_class_from_ledger(repository: Any, observation: Mapping[str, Any]) -> str | None:
    """Outcome class from the grade-interpretation head (argmax P(Z|E)), falling back
    to the raw observed class ``G``. Both are ledger events -- never a live table."""

    interp = repository.active_interpretation_for_observation(observation["id"])
    if interp is not None:
        posterior = _loads(interp.get("response_posterior_json"))
        outcome = outcome_class_for_response_posterior(posterior)
        if outcome is not None:
            return outcome
    raw = repository.raw_grade_events_for_observation(observation["id"])
    if raw:
        return str(raw[-1].get("observed_class"))
    return None


def replay_event_stream(events: Sequence[Mapping[str, Any]]) -> ReplayResult:
    """Deterministic replay of a synthetic activity-event stream (§9.7). Each event is a
    plain dict ``{card_version_id, outcome_class, admin_context, reading_phase, seq}``.

    Pure (no DB): a fold that is a function of the multiset of events, so two runs over
    the same stream are byte-identical. Reports :data:`REPLAY_MANIFEST`."""

    normalized = [
        NormalizedEvent(
            sort_key=f"{int(event.get('seq', index)):012d}|{index:012d}",
            card_version_id=event.get("card_version_id"),
            outcome_class=event.get("outcome_class"),
            context=context_key(event.get("admin_context"), event.get("reading_phase")),
        )
        for index, event in enumerate(events)
    ]
    return _accumulate(normalized)


def u014_resume_shape(result: ReplayResult) -> dict[str, Any]:
    """Emit per-card outcome counts in the shape the deferred hierarchical likelihood
    model consumes (U-014 resume path, §9.8). Per card version: the by-context strata,
    per-context outcome totals, and the card total ``n`` -- exactly the trial/outcome
    tallies a card-psychometrics likelihood is fit over, with zero schema changes."""

    cards: dict[str, Any] = {}
    for card_version_id, strata in result.counts.items():
        totals: dict[str, int] = defaultdict(int)
        n = 0
        by_context: dict[str, Any] = {}
        for ctx, classes in strata.items():
            ctx_n = sum(classes.values())
            n += ctx_n
            for outcome, count in classes.items():
                totals[outcome] += count
            by_context[ctx] = {"outcomes": dict(classes), "n": ctx_n}
        cards[card_version_id] = {
            "contexts": by_context,
            "outcome_totals": dict(totals),
            "n": n,
        }
    return {
        "manifest": dict(result.manifest),
        "cards": cards,
        "card_count": len(cards),
        "events_replayed": result.events_replayed,
    }


def _loads(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None
