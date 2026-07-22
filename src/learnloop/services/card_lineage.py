"""P1 step 4 -- edit classification, durable card-lineage state, and the
authoritative card-level scheduling projection (spec_p1_shared_substrate §3.7, §3.8).

Three concerns land here, all keyed to the P0 (migration 065) immutable card
versions but never altering them (owner decision A.1):

  * :func:`classify_edit` -- the §3.7 normalized-component comparator returning
    ``surface_preserving`` / ``fork_required`` / ``review_required``. It is
    deterministic and CONSERVATIVE: an unprovable edit is parked for review and
    NEVER defaults to preserving scheduling state (§3.7, §9.2).
  * lineage identity + append-only edges (minor_successor / semantic_fork /
    split_from / merged_from). A ``minor_successor`` retains the lineage's
    scheduling state; a ``semantic_fork`` starts a NEW lineage + NEW
    ``activity_card_state`` with an evidence-informed prior but **no inherited
    certification or stability** (§3.7).
  * :func:`rebuild_card_state` -- the card-state projection is rebuildable from
    its authoritative review-event stream (standing rule: every projection is
    rebuildable from events). Corrupting the legacy ``practice_item_state`` cache
    cannot alter an authoritative rebuild (§9.5).

    B8 -- authoritative store: the review-event stream stored in
    ``activity_card_state.projection_head_json.reviews`` IS the authoritative store
    for the FSRS replay, not a mere cache. This is the deliberately smaller choice
    over re-sourcing every rebuild from the P0 observation ledger: the scheduling
    fields (difficulty/stability/retrievability/due) are the disposable projection,
    while ``projection_head.reviews`` is the durable, append-grown event list the
    projection is folded from. A rebuild reads those events and never trusts the
    scheduling fields; a corrupted legacy ``practice_item_state`` cache is therefore
    irrelevant to the rebuild's result.

This REPLACES the ``state_sync.py`` FSRS-preserving placeholder for new
administrations; ``state_sync`` remains the legacy compatibility path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.fsrs import (
    FSRS6_DEFAULT_WEIGHTS,
    MemoryState,
    Rating,
    apply_review,
)

# Classifier identity pin (structural version, not a decision knob).
LINEAGE_CLASSIFIER_VERSION = "lineage_classifier_v1"

# Card-contract components whose change is a MATERIAL contract change -> fork
# (§3.7 fork_required list). Compared after normalization.
SEMANTIC_COMPONENTS: tuple[str, ...] = (
    "target",
    "capability",
    "response_contract",
    "rubric_semantics",
    # B8: the answer key / worked solution is a material contract component -- changing
    # what counts as correct is a semantic change, never a cosmetic one.
    "answer_key",
    "solution",
    "task_feature_bounds",
    "difficulty",
    "tools",
    "span",
    "feedback_eligibility",
    "evidence_eligibility",
)

# Components whose change CANNOT change classification (§3.7 surface_preserving
# list): wording/formatting cleanup, equivalent diagram, parameter-pool
# adjustment inside declared bounds, generator bug fix, rubric clarification.
COSMETIC_COMPONENTS: tuple[str, ...] = (
    "prompt",
    "wording",
    "formatting",
    "diagram",
    "media",
    "parameter_pool",
    "generator_version",
    "generator_bugfix",
    "rubric_clarification",
)


@dataclass(frozen=True)
class EditClassification:
    verdict: str  # surface_preserving | fork_required | review_required
    changed_semantic: tuple[str, ...]
    changed_unknown: tuple[str, ...]
    classifier_version: str = LINEAGE_CLASSIFIER_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "changed_semantic": list(self.changed_semantic),
            "changed_unknown": list(self.changed_unknown),
            "classifier_version": self.classifier_version,
        }


def _normalized_components(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Extract the comparable contract components. Missing keys read as ``None`` so
    an added/removed component is a real difference, not silently ignored."""

    return {key: contract.get(key) for key in (*SEMANTIC_COMPONENTS, *COSMETIC_COMPONENTS)}


def classify_edit(
    prev_contract: Mapping[str, Any], new_contract: Mapping[str, Any]
) -> EditClassification:
    """Classify a proposed card edit (§3.7).

    - any changed SEMANTIC component -> ``fork_required``;
    - only cosmetic components (or nothing) changed AND every non-cosmetic key is
      recognized -> ``surface_preserving``;
    - a changed key the classifier does not recognize as either cosmetic or
      semantic -> ``review_required`` (the service cannot prove either case; it
      never defaults to preserving state).
    """

    prev = dict(prev_contract)
    new = dict(new_contract)

    changed_semantic = tuple(
        key for key in SEMANTIC_COMPONENTS if prev.get(key) != new.get(key)
    )

    known = set(SEMANTIC_COMPONENTS) | set(COSMETIC_COMPONENTS)
    all_keys = set(prev) | set(new)
    changed_unknown = tuple(
        sorted(key for key in all_keys - known if prev.get(key) != new.get(key))
    )

    # B8: a purported rubric CLARIFICATION (cosmetic) cannot ride along with a real
    # rubric_semantics delta -- that combination is ambiguous and unprovable, so it is
    # parked for review rather than silently forked or preserved (§3.7, §9.2).
    if prev.get("rubric_clarification") != new.get("rubric_clarification") and (
        prev.get("rubric_semantics") != new.get("rubric_semantics")
    ):
        return EditClassification("review_required", changed_semantic, changed_unknown)

    if changed_semantic:
        return EditClassification("fork_required", changed_semantic, changed_unknown)
    if changed_unknown:
        # An unrecognized differing component cannot be proven cosmetic -> park.
        return EditClassification("review_required", changed_semantic, changed_unknown)
    return EditClassification("surface_preserving", (), ())


# ---------------------------------------------------------------------------
# Lineage identity + append-only edges.
# ---------------------------------------------------------------------------

def start_lineage(
    repository: Repository,
    *,
    genesis_card_version_id: str,
    family_id: str | None = None,
    card_id: str | None = None,
    clock: Clock | None = None,
) -> str:
    """Create a durable lineage and record its genesis edge (from_ = NULL)."""

    lineage_id = repository.create_card_lineage(card_id=card_id, family_id=family_id, clock=clock)
    repository.append_card_lineage_edge(
        lineage_id=lineage_id,
        from_card_version_id=None,
        to_card_version_id=genesis_card_version_id,
        edge_kind="minor_successor",
        classifier_version=LINEAGE_CLASSIFIER_VERSION,
        rationale={"reason": "genesis"},
        clock=clock,
    )
    return lineage_id


def append_minor_successor(
    repository: Repository,
    *,
    lineage_id: str,
    from_card_version_id: str,
    to_card_version_id: str,
    rationale: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    """Append a surface-preserving successor version INSIDE the lineage; scheduling
    state is retained on the same lineage (§3.7)."""

    return repository.append_card_lineage_edge(
        lineage_id=lineage_id,
        from_card_version_id=from_card_version_id,
        to_card_version_id=to_card_version_id,
        edge_kind="minor_successor",
        classifier_version=LINEAGE_CLASSIFIER_VERSION,
        rationale=rationale,
        clock=clock,
    )


def fork_card(
    repository: Repository,
    *,
    predecessor_card_version_id: str,
    forked_card_version_id: str,
    scheduler_algorithm_version: str,
    family_id: str | None = None,
    card_id: str | None = None,
    model_label: str = "fsrs",
    learner_id: str = "local",
    informed_difficulty_prior: float | None = None,
    predecessor_lineage_id: str | None = None,
    rationale: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Fork: a NEW lineage + a NEW ``activity_card_state`` row that inherits an
    evidence-informed *difficulty* prior at most, and NEVER inherits stability or
    certification (§3.7). Returns the new lineage id + state id.

    ``predecessor_lineage_id`` (if given) records provenance via a semantic_fork
    edge into the new lineage; the predecessor lineage's state is untouched.
    """

    new_lineage = repository.create_card_lineage(card_id=card_id, family_id=family_id, clock=clock)
    repository.append_card_lineage_edge(
        lineage_id=new_lineage,
        from_card_version_id=predecessor_card_version_id,
        to_card_version_id=forked_card_version_id,
        edge_kind="semantic_fork",
        classifier_version=LINEAGE_CLASSIFIER_VERSION,
        rationale=dict(rationale or {"reason": "semantic_fork"}),
        clock=clock,
    )
    # Fresh scheduling state: informed prior on difficulty at most; NO stability.
    state_id = repository.upsert_activity_card_state(
        card_lineage_id=new_lineage,
        scheduler_algorithm_version=scheduler_algorithm_version,
        model_label=model_label,
        learner_id=learner_id,
        difficulty=informed_difficulty_prior,
        stability=None,
        retrievability=None,
        due_at=None,
        projection_head={"reviews": [], "forked_from_version": predecessor_card_version_id},
        clock=clock,
    )
    return {"lineage_id": new_lineage, "state_id": state_id}


def split_lineage(
    repository: Repository,
    *,
    from_card_version_id: str,
    split_card_version_id: str,
    family_id: str | None = None,
    card_id: str | None = None,
    rationale: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    """Split a new lineage off an existing version (append-only ``split_from`` edge)."""

    new_lineage = repository.create_card_lineage(card_id=card_id, family_id=family_id, clock=clock)
    repository.append_card_lineage_edge(
        lineage_id=new_lineage,
        from_card_version_id=from_card_version_id,
        to_card_version_id=split_card_version_id,
        edge_kind="split_from",
        classifier_version=LINEAGE_CLASSIFIER_VERSION,
        rationale=rationale,
        clock=clock,
    )
    return new_lineage


def merge_lineage(
    repository: Repository,
    *,
    into_lineage_id: str,
    from_card_version_id: str,
    merged_card_version_id: str,
    rationale: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    """Record a ``merged_from`` edge folding another lineage's version in."""

    return repository.append_card_lineage_edge(
        lineage_id=into_lineage_id,
        from_card_version_id=from_card_version_id,
        to_card_version_id=merged_card_version_id,
        edge_kind="merged_from",
        classifier_version=LINEAGE_CLASSIFIER_VERSION,
        rationale=rationale,
        clock=clock,
    )


# ---------------------------------------------------------------------------
# Card-state projection (rebuildable from the authoritative review-event stream).
# ---------------------------------------------------------------------------

def _rating(value: Any) -> Rating:
    return Rating(int(value)) if not isinstance(value, Rating) else value


def replay_review_events(
    review_events: Sequence[Mapping[str, Any]],
    *,
    weights: tuple[float, ...] = FSRS6_DEFAULT_WEIGHTS,
) -> MemoryState | None:
    """Deterministically replay an ordered stream of eligible review events into an
    FSRS memory state. Each event carries ``rating`` and ``elapsed_days``."""

    memory: MemoryState | None = None
    for event in review_events:
        memory = apply_review(
            memory, _rating(event["rating"]), float(event.get("elapsed_days", 0.0)), weights
        )
    return memory


def rebuild_card_state(
    repository: Repository,
    *,
    card_lineage_id: str,
    scheduler_algorithm_version: str,
    review_events: Sequence[Mapping[str, Any]] | None = None,
    model_label: str = "fsrs",
    learner_id: str = "local",
    due_at: str | None = None,
    weights: tuple[float, ...] = FSRS6_DEFAULT_WEIGHTS,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Rebuild ``activity_card_state`` from its authoritative review-event stream.

    When ``review_events`` is not supplied it is read from the stored projection
    head (``projection_head_json.reviews``) -- the events are authoritative, the
    scheduling fields are the projection. This is independent of the legacy
    ``practice_item_state`` cache (§9.5).
    """

    if review_events is None:
        existing = repository.activity_card_state(
            card_lineage_id=card_lineage_id,
            scheduler_algorithm_version=scheduler_algorithm_version,
            learner_id=learner_id,
        )
        if existing is None:
            return None
        import json as _json_mod

        head = _json_mod.loads(existing["projection_head_json"] or "{}")
        review_events = head.get("reviews", [])

    memory = replay_review_events(review_events, weights=weights)
    difficulty = memory.difficulty if memory is not None else None
    stability = memory.stability if memory is not None else None
    retrievability = memory.retrievability if memory is not None else None
    repository.upsert_activity_card_state(
        card_lineage_id=card_lineage_id,
        scheduler_algorithm_version=scheduler_algorithm_version,
        model_label=model_label,
        learner_id=learner_id,
        difficulty=difficulty,
        stability=stability,
        retrievability=retrievability,
        due_at=due_at,
        projection_head={"reviews": list(review_events)},
        clock=clock,
    )
    return repository.activity_card_state(
        card_lineage_id=card_lineage_id,
        scheduler_algorithm_version=scheduler_algorithm_version,
        learner_id=learner_id,
    )
