from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
from math import exp, log

from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.config import ProbeIRTConfig, ProbeSelfTagConfig
from learnloop.db.repositories import (
    ActiveErrorEvent,
    ItemMisconceptionDiscrimination,
    MisconceptionRecord,
    ProbeStateRecord,
    Repository,
)
from learnloop.services.mastery import (
    covering_learner_claim,
    initial_mastery_state_for_learning_object,
    item_irt_params,
    sigmoid,
)
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric

SCORE_BUCKETS = ("low", "mid", "high")

# Concept-graph closeness decay per hop for the self-tag trust weight and the
# error-type picker ranking (spec §12.3). Formerly read from the now-retired
# [cross_lo_propagation] config block (knowledge-model §8.3); this is a fixed
# UI-ranking constant, not belief propagation.
_CONCEPT_CLOSENESS_HOP_DECAY = 0.5
Outcome = tuple[str, str | None]

# Crockford base32 ULID (26 chars, excludes I, L, O, U). See spec §1.4.
_ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


def parse_misconception_label(label: str) -> tuple[str, bool]:
    """Split a ``misconception:<suffix>`` hypothesis label (spec §1.4).

    Returns ``(suffix, is_registry_id)`` where ``is_registry_id`` is True iff the
    suffix is a 26-char Crockford ULID (a registry misconception id). A non-ULID
    suffix is a legacy error-type-keyed hypothesis and takes the back-compat path.
    The suffix is empty when the label is not a ``misconception:`` label.
    """

    prefix = "misconception:"
    if not label.startswith(prefix):
        return "", False
    suffix = label[len(prefix) :]
    return suffix, bool(_ULID_RE.match(suffix))


@dataclass(frozen=True)
class Hypothesis:
    label: str
    error_type: str | None = None
    source_error_event_id: str | None = None
    source_concept_id: str | None = None
    severity_at_entry: float = 0.0
    # spec §3: registry-keyed hypotheses carry a misconception id instead of an
    # error type; `misconception:<ulid>`. Legacy hypotheses leave this None.
    misconception_id: str | None = None

    @property
    def channel_key(self) -> str | None:
        """The error-dimension key this hypothesis owns in the outcome space (§3).

        Legacy hypotheses key on ``error_type``; registry hypotheses key on
        ``misconception_id`` (the fire channel for their keyed fatal error).
        """

        return self.error_type if self.error_type is not None else self.misconception_id

    def as_record(self) -> dict[str, object]:
        return {
            "label": self.label,
            "error_type": self.error_type,
            "source_error_event_id": self.source_error_event_id,
            "source_concept_id": self.source_concept_id,
            "severity_at_entry": self.severity_at_entry,
            "misconception_id": self.misconception_id,
        }


@dataclass(frozen=True)
class HypothesisSet:
    learning_object_id: str
    hypotheses: list[Hypothesis]
    prior: dict[str, float]
    id: str | None = None

    @property
    def known_error_types(self) -> list[str]:
        """Error-channel keys across the set: legacy error types and registry ids (§3)."""

        seen: list[str] = []
        for hypothesis in self.hypotheses:
            key = hypothesis.channel_key
            if key is not None and key not in seen:
                seen.append(key)
        return sorted(seen)

    @classmethod
    def from_record(cls, record: dict) -> "HypothesisSet":
        hypotheses = [
            Hypothesis(
                label=entry["label"],
                error_type=entry.get("error_type"),
                source_error_event_id=entry.get("source_error_event_id"),
                source_concept_id=entry.get("source_concept_id"),
                severity_at_entry=float(entry.get("severity_at_entry", 0.0)),
                misconception_id=entry.get("misconception_id"),
            )
            for entry in record.get("hypotheses", [])
        ]
        prior = {key: float(value) for key, value in record.get("prior", {}).items()}
        return cls(
            learning_object_id=record.get("learning_object_id", ""),
            hypotheses=hypotheses,
            prior=prior,
            id=record.get("id"),
        )


def build_hypothesis_set(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    clock: Clock | None = None,
) -> HypothesisSet:
    learning_object = vault.learning_objects[learning_object_id]
    now = (clock or SystemClock()).now().astimezone(UTC)
    mastery = repository.mastery_state(learning_object_id) or initial_mastery_state_for_learning_object(
        vault,
        repository,
        learning_object_id,
        utc_now_iso(clock),
    )
    mastery_mean = sigmoid(mastery.logit_mean)

    hypotheses: list[Hypothesis] = [
        Hypothesis(label="mastered", severity_at_entry=mastery_mean),
        Hypothesis(label="unfamiliar", severity_at_entry=1.0 - mastery_mean),
    ]
    prior: dict[str, float] = {
        "mastered": max(mastery_mean, 1e-6),
        "unfamiliar": max(1.0 - mastery_mean, 1e-6),
    }

    misconceptions: list[tuple[float, Hypothesis, float]] = []  # (decayed_weight, hypothesis, severity)
    seen_error_types: set[str] = set()
    seen_misconception_ids: set[str] = set()

    # spec §3: registry rows first — each active/resolving belief becomes a
    # `misconception:<id>` hypothesis with its own severity and decay. Two
    # distinct conceptual slips coexist rather than collapsing to one error type.
    for record in repository.misconceptions_for_learning_object(
        learning_object_id, statuses=("active", "resolving")
    ):
        if record.id in seen_misconception_ids:
            continue
        seen_misconception_ids.add(record.id)
        weight = record.severity * _decay(record.updated_at or record.created_at, now)
        misconceptions.append(
            (
                weight,
                Hypothesis(
                    label=f"misconception:{record.id}",
                    error_type=None,
                    misconception_id=record.id,
                    severity_at_entry=record.severity,
                ),
                record.severity,
            )
        )

    # Registry rows on confusable-neighbor concepts, mastery-gated like the legacy
    # neighbor path (spec §3 neighbor propagation).
    for neighbor_concept, record in _neighbor_registry_misconceptions(
        vault, repository, learning_object.concept, now
    ):
        if record.id in seen_misconception_ids:
            continue
        seen_misconception_ids.add(record.id)
        weight = record.severity * _decay(record.updated_at or record.created_at, now)
        misconceptions.append(
            (
                weight,
                Hypothesis(
                    label=f"misconception:{record.id}",
                    error_type=None,
                    misconception_id=record.id,
                    source_concept_id=neighbor_concept,
                    severity_at_entry=record.severity,
                ),
                record.severity,
            )
        )

    # Legacy raw error-event path: only misconception events with NO registry link
    # (old vaults). Events already normalized into a registry row above are skipped.
    for error in repository.active_errors_by_learning_object(learning_object_id):
        if not error.is_misconception:
            continue
        if error.misconception_id is not None:
            continue
        if error.error_type in seen_error_types:
            continue
        seen_error_types.add(error.error_type)
        weight = error.severity * _decay(error.created_at, now)
        misconceptions.append(
            (
                weight,
                Hypothesis(
                    label=f"misconception:{error.error_type}",
                    error_type=error.error_type,
                    source_error_event_id=error.id,
                    severity_at_entry=error.severity,
                ),
                error.severity,
            )
        )

    for neighbor_concept, neighbor_error in _neighbor_misconceptions(vault, repository, learning_object.concept, now):
        if neighbor_error.misconception_id is not None:
            continue
        if neighbor_error.error_type in seen_error_types:
            continue
        seen_error_types.add(neighbor_error.error_type)
        weight = neighbor_error.severity * _decay(neighbor_error.created_at, now)
        misconceptions.append(
            (
                weight,
                Hypothesis(
                    label=f"misconception:{neighbor_error.error_type}",
                    error_type=neighbor_error.error_type,
                    source_error_event_id=neighbor_error.id,
                    source_concept_id=neighbor_concept,
                    severity_at_entry=neighbor_error.severity,
                ),
                neighbor_error.severity,
            )
        )

    # Cap at hypothesis_set_max_size; drop lowest-severity misconceptions first.
    max_size = vault.config.probe.hypothesis_set_max_size
    misconceptions.sort(key=lambda entry: (-entry[2], entry[1].label))
    misconceptions = misconceptions[: max(0, max_size - len(hypotheses))]

    for decayed_weight, hypothesis, _severity in misconceptions:
        hypotheses.append(hypothesis)
        prior[hypothesis.label] = max(decayed_weight, 1e-6)

    total = sum(prior.values())
    prior = {label: value / total for label, value in prior.items()}
    return HypothesisSet(learning_object_id=learning_object_id, hypotheses=hypotheses, prior=prior)


def enter_probe(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    claimed_level: float | None = None,
    clock: Clock | None = None,
) -> HypothesisSet:
    algorithm_version = vault.config.algorithms.algorithm_version
    hypothesis_set = build_hypothesis_set(vault, repository, learning_object_id, clock=clock)
    probe_phase_id = f"probe_{learning_object_id}"
    hypothesis_set_id = repository.insert_hypothesis_set(
        learning_object_id=learning_object_id,
        probe_phase_id=probe_phase_id,
        hypotheses=[hypothesis.as_record() for hypothesis in hypothesis_set.hypotheses],
        prior=hypothesis_set.prior,
        algorithm_version=algorithm_version,
        clock=clock,
    )
    target = vault.config.probe.attempts_target_default
    if claimed_level is None:
        claim = covering_learner_claim(vault, repository, learning_object_id)
        claimed_level = float(claim["claimed_level"]) if claim is not None else None
    if claimed_level is not None and claimed_level >= vault.config.probe.claim_skip_threshold:
        target = vault.config.probe.attempts_target_with_strong_claim
    from learnloop.clock import utc_now_iso

    now = utc_now_iso(clock)
    repository.upsert_probe_state(
        learning_object_id=learning_object_id,
        status="in_progress",
        algorithm_version=algorithm_version,
        probe_phase_id=probe_phase_id,
        hypothesis_set_id=hypothesis_set_id,
        probe_attempts_completed=0,
        probe_attempts_target=target,
        entered_at=now,
        clock=clock,
    )
    return HypothesisSet(
        learning_object_id=hypothesis_set.learning_object_id,
        hypotheses=hypothesis_set.hypotheses,
        prior=hypothesis_set.prior,
        id=hypothesis_set_id,
    )


def resolve_item_irt(vault: LoadedVault, item: PracticeItem) -> tuple[float, float, ProbeIRTConfig]:
    """``(a, b, ProbeIRTConfig)`` for an item — the same ``(a, b)`` Channel 1 uses.

    ``(a, b)`` is derived from the static authored/LLM difficulty (spec §4.3) so the
    probe and mastery channels share a consistent difficulty treatment (§5.1).
    """

    learning_object = vault.learning_object_for_item(item)
    item_a, item_b = item_irt_params(item, learning_object, vault.config.mastery)
    return item_a, item_b, vault.config.probe.irt


def _concept_graph_adjacency(vault: LoadedVault) -> dict[str, set[str]]:
    """Undirected adjacency over the concept graph (all relation types)."""

    adjacency: dict[str, set[str]] = {}
    for edge in vault.edges:
        adjacency.setdefault(edge.source, set()).add(edge.target)
        adjacency.setdefault(edge.target, set()).add(edge.source)
    return adjacency


def _concept_closeness(
    adjacency: dict[str, set[str]],
    source_concept: str | None,
    related_concepts: list[str],
    hop_decay: float,
) -> float:
    """Hop-decay closeness from ``source_concept`` to its nearest related concept (§12.3).

    ``1.0`` if ``source_concept`` is itself a related concept; ``hop_decay ** h`` for
    the shortest ``h``-hop path along concept edges; ``0`` if disconnected (or if
    either endpoint is missing).
    """

    targets = set(related_concepts)
    if not targets or source_concept is None:
        return 0.0
    if source_concept in targets:
        return 1.0
    visited = {source_concept}
    frontier: deque[tuple[str, int]] = deque([(source_concept, 0)])
    while frontier:
        node, depth = frontier.popleft()
        for neighbor in adjacency.get(node, ()):  # undirected
            if neighbor in visited:
                continue
            if neighbor in targets:
                return hop_decay ** (depth + 1)
            visited.add(neighbor)
            frontier.append((neighbor, depth + 1))
    return 0.0


def _mean_concept_degree(adjacency: dict[str, set[str]], concept_count: int) -> float:
    if concept_count <= 0:
        return 0.0
    total_degree = sum(len(neighbors) for neighbors in adjacency.values())
    return total_degree / concept_count


def self_tag_weight(
    vault: LoadedVault,
    item: PracticeItem,
    error_type: str,
    bucket: str,
    config: ProbeSelfTagConfig | None = None,
) -> float:
    """Trust weight ``w_self`` for a learner self-attached misconception (spec §12.3).

    ``w_self = 𝟙_consistent · min(w_max, w_base · c_eff)`` where ``c_eff`` blends the
    concept-graph closeness toward neutral (1.0, no penalty) when the graph is too
    sparse to inform us — so a fresh vault falls back to ``w_base`` and trust sharpens
    only as edges accrue. ``𝟙_consistent`` zeroes the weight when a high score
    contradicts a score-capping misconception.
    """

    config = config or ProbeSelfTagConfig()
    # Hard score<->label consistency gate (§12.3): a score-capping misconception
    # cannot coexist with a high score, so an attached label there is ignored.
    if bucket == "high":
        return 0.0

    error = vault.error_types.get(error_type)
    related = list(error.related_concepts) if error is not None else []
    learning_object = vault.learning_object_for_item(item)
    item_concept = learning_object.concept if learning_object is not None else None

    adjacency = _concept_graph_adjacency(vault)
    hop_decay = _CONCEPT_CLOSENESS_HOP_DECAY
    c_raw = _concept_closeness(adjacency, item_concept, related, hop_decay)

    # rho: how much a *missing* link should be trusted (§12.3). A missing link only
    # means "unrelated" once the graph is dense enough and both endpoints are linkable.
    rho_local = 1.0 if (related and item_concept is not None and adjacency.get(item_concept)) else 0.0
    mean_degree = _mean_concept_degree(adjacency, len(vault.concepts))
    rho_global = min(1.0, mean_degree / config.target_degree) if config.target_degree > 0 else 0.0
    rho = rho_global * rho_local

    c_eff = rho * c_raw + (1.0 - rho) * 1.0
    return min(config.w_max, config.w_base * c_eff)


@dataclass(frozen=True)
class ErrorTypeCandidate:
    """A ranked error-type suggestion for the self-grade misconception picker (§12.5)."""

    error_type: str
    title: str
    is_misconception: bool
    closeness: float
    score: float


def _fuzzy_match(query: str, text: str) -> float:
    normalized_query = query.strip().lower()
    normalized_text = (text or "").lower()
    if not normalized_query:
        return 0.0
    if normalized_query in normalized_text:
        return 1.0
    return SequenceMatcher(None, normalized_query, normalized_text).ratio()


def rank_error_type_candidates(
    vault: LoadedVault,
    *,
    item: PracticeItem | None = None,
    learning_object_id: str | None = None,
    query: str | None = None,
    limit: int = 10,
) -> list[ErrorTypeCandidate]:
    """Rank the error-type taxonomy for the self-grade misconception picker (spec §12.5).

    Concept-relevant misconceptions sort to the top by the §12.3 hop-decay closeness
    to the item's (or LO's) concept; a fuzzy match over title/id reranks as the
    learner types. The service is surface-agnostic (CLI / sidecar / GUI).
    """

    learning_object = None
    if item is not None:
        learning_object = vault.learning_object_for_item(item)
    elif learning_object_id is not None:
        learning_object = vault.learning_objects.get(learning_object_id)
    item_concept = learning_object.concept if learning_object is not None else None

    adjacency = _concept_graph_adjacency(vault)
    hop_decay = _CONCEPT_CLOSENESS_HOP_DECAY

    candidates: list[ErrorTypeCandidate] = []
    for error in vault.error_types.values():
        closeness = _concept_closeness(adjacency, item_concept, error.related_concepts, hop_decay)
        relevance = max(_fuzzy_match(query, error.title), _fuzzy_match(query, error.id)) if query else closeness
        # Misconceptions are what this picker attaches, so nudge them up; closeness
        # breaks ties so a genuine concept link still wins among equal matches.
        score = relevance + (0.15 if error.is_misconception else 0.0)
        candidates.append(
            ErrorTypeCandidate(
                error_type=error.id,
                title=error.title,
                is_misconception=error.is_misconception,
                closeness=closeness,
                score=score,
            )
        )
    candidates.sort(key=lambda candidate: (-candidate.score, -candidate.closeness, candidate.title))
    return candidates[:limit]


def _graded_marginals(eta: float, cut_mid: float, cut_high: float) -> tuple[float, float, float]:
    """Fixed 3-level graded score-bucket marginals (spec §5.2): ``(low, mid, high)``."""

    s_mid = sigmoid(eta - cut_mid)
    s_high = sigmoid(eta - cut_high)
    return 1.0 - s_mid, s_mid - s_high, s_high


def conditional_distribution(
    hypothesis: Hypothesis,
    *,
    item_a: float = 1.0,
    item_b: float = 0.0,
    irt: ProbeIRTConfig | None = None,
    fatal_error_ids: set[str],
    known_error_types: list[str],
    discrimination: dict[str, ItemMisconceptionDiscrimination] | None = None,
    discriminated_ids: set[str] | None = None,
) -> dict[Outcome, float]:
    """``P(score_bucket, error_type | h, item)`` under the difficulty-aware model.

    The no-error score-bucket marginals are difficulty-aware via the graded mapping
    of §5.2; the error-type overlay of §5.3 attaches the error channel.

    The ability anchor depends on whether the item *probes* the hypothesis's error
    (spec §5.1, corrected): a ``misconception:E`` learner on an item whose fatal
    errors include ``E`` triggers that error and is **capped to a low score**, so its
    score is anchored low (``theta_unfamiliar``) and routed onto the ``E`` channel —
    making ``(low, E)`` the diagnostic outcome that confirms the misconception. On an
    item that does *not* probe ``E`` the misconception is not elicited, so the learner
    performs capably (``theta_mastered``, null errors), like ``mastered`` here.

    Registry-keyed hypotheses (spec §3): when the item carries a discrimination row
    (or a bridge fatal link) for a registry misconception, the ``(low, <mc_id>)``
    fire outcome takes ``E[sens]`` mass under the belief that owns it and
    ``1 − E[spec]`` under every clean hypothesis, so EIG prefers genuinely
    discriminating items over coverage lookalikes. An item with no discrimination
    for a registry belief contributes coverage only (unfamiliar-anchored base).
    """

    irt = irt or ProbeIRTConfig()
    discrimination = discrimination or {}
    discriminated_ids = set(discriminated_ids or ())
    error_types: list[str | None] = [None, *known_error_types]
    distribution: dict[Outcome, float] = {
        (bucket, error_type): 0.0 for bucket in SCORE_BUCKETS for error_type in error_types
    }

    # spec §3: discriminating item — overlay the registry fire channel on every
    # hypothesis (belief holder vs clean learner separate on the fire outcome).
    if discriminated_ids:
        return _fire_overlay_distribution(
            hypothesis,
            distribution,
            discriminated_ids=discriminated_ids,
            discrimination=discrimination,
            item_a=item_a,
            item_b=item_b,
            irt=irt,
        )

    # spec §3: registry belief on an item with no discrimination link — the item
    # does not probe the belief, so its holder performs capably (the motivating
    # paraphrase is answerable perfectly while holding the belief). No separation
    # from `mastered`: a non-discriminating item earns no EIG against the belief
    # and a clean success on it is not evidence the belief is gone.
    if hypothesis.misconception_id is not None:
        low, mid, high = _graded_marginals(
            item_a * (irt.theta_mastered - item_b), irt.cut_mid, irt.cut_high
        )
        distribution[("low", None)] = low
        distribution[("mid", None)] = mid
        distribution[("high", None)] = high
        return distribution

    probes_item = hypothesis.error_type is not None and hypothesis.error_type in fatal_error_ids

    # `mastered`, and any misconception this item does not probe, perform capably.
    if hypothesis.label == "mastered" or (hypothesis.error_type is not None and not probes_item):
        low, mid, high = _graded_marginals(item_a * (irt.theta_mastered - item_b), irt.cut_mid, irt.cut_high)
        distribution[("low", None)] = low
        distribution[("mid", None)] = mid
        distribution[("high", None)] = high
        return distribution

    # `unfamiliar` and `misconception:E (probing)` both score low; the error channel
    # is what separates them.
    low, mid, high = _graded_marginals(item_a * (irt.theta_unfamiliar - item_b), irt.cut_mid, irt.cut_high)

    if hypothesis.label == "unfamiliar":
        # Mostly null low scores, with a small leak across the known error channels
        # (an unfamiliar wrong answer occasionally resembles a known error).
        distribution[("mid", None)] = mid
        distribution[("high", None)] = high
        known_low = [("low", error_type) for error_type in known_error_types]
        if known_low:
            distribution[("low", None)] = low * (1.0 - irt.unfamiliar_error_leak)
            share = low * irt.unfamiliar_error_leak / len(known_low)
            for outcome in known_low:
                distribution[outcome] = share
        else:
            distribution[("low", None)] = low
        return distribution

    # misconception:E where E probes the item: the low/mid score mass carries E.
    error_type = hypothesis.error_type
    distribution[("low", error_type)] = low * irt.err_low_frac
    distribution[("low", None)] = low * (1.0 - irt.err_low_frac)
    distribution[("mid", error_type)] = mid * irt.err_mid_frac
    distribution[("mid", None)] = mid * (1.0 - irt.err_mid_frac)
    distribution[("high", None)] = high
    return distribution


# Bridge default (spec §3): an item whose rubric fatal error links a misconception
# but has no estimated discrimination row yet is treated as a mild discriminator.
_BRIDGE_SENSITIVITY = 0.6
_BRIDGE_SPECIFICITY = 0.9


def _fire_probabilities(
    fire_channel: str,
    discrimination: dict[str, ItemMisconceptionDiscrimination],
) -> tuple[float, float]:
    """``(E[sens], E[spec])`` for the item's fire channel, with the bridge default."""

    row = discrimination.get(fire_channel)
    if row is None:
        return _BRIDGE_SENSITIVITY, _BRIDGE_SPECIFICITY
    return row.sensitivity_mean, row.specificity_mean


def _fire_overlay_distribution(
    hypothesis: Hypothesis,
    distribution: dict[Outcome, float],
    *,
    discriminated_ids: set[str],
    discrimination: dict[str, ItemMisconceptionDiscrimination],
    item_a: float,
    item_b: float,
    irt: ProbeIRTConfig,
) -> dict[Outcome, float]:
    """Overlay the registry fire channel for a discriminating item (spec §3).

    A single fire channel drives the split (the lexically-first discriminated
    misconception when an item catches several — real diagnostics catch one). The
    belief that owns the channel fires with ``E[sens]``; every other (clean)
    hypothesis false-fires with ``1 − E[spec]``. The remaining mass follows the
    hypothesis's own graded distribution: the belief holder and ``unfamiliar``
    anchor low, ``mastered``/``facet_solid``/other beliefs anchor at mastery.
    """

    fire_channel = sorted(discriminated_ids)[0]
    sens, spec = _fire_probabilities(fire_channel, discrimination)
    is_belief = hypothesis.misconception_id == fire_channel
    if is_belief:
        p_fire = sens
        anchor = irt.theta_unfamiliar
    else:
        p_fire = 1.0 - spec
        anchor = irt.theta_unfamiliar if hypothesis.label == "unfamiliar" else irt.theta_mastered
    low, mid, high = _graded_marginals(item_a * (anchor - item_b), irt.cut_mid, irt.cut_high)
    scale = 1.0 - p_fire
    distribution[("low", fire_channel)] = p_fire
    distribution[("low", None)] = low * scale
    distribution[("mid", None)] = mid * scale
    distribution[("high", None)] = high * scale
    return distribution


def item_registry_discrimination(
    repository: Repository,
    vault: LoadedVault,
    item: PracticeItem,
    rubric: Rubric | None,
    hypothesis_set: HypothesisSet,
) -> tuple[dict[str, ItemMisconceptionDiscrimination], set[str]]:
    """``(discrimination_rows, discriminated_ids)`` for an item vs the set (spec §3).

    ``discriminated_ids`` are the registry misconception ids the item catches —
    those with a discrimination row, plus a bridge for a rubric fatal error linking
    a registry belief in the set that has no row yet (so old links aren't lost).
    """

    from learnloop.vault.models import discriminates

    registry_ids = {h.misconception_id for h in hypothesis_set.hypotheses if h.misconception_id is not None}
    if not registry_ids:
        return {}, set()
    rows: dict[str, ItemMisconceptionDiscrimination] = {}
    discriminated: set[str] = set()
    for mc_id in registry_ids:
        row = repository.discrimination_row(item.id, mc_id)
        if row is not None:
            rows[mc_id] = row
            discriminated.add(mc_id)
    bridge = discriminates(item, rubric)
    for mc_id in bridge:
        if mc_id in registry_ids:
            discriminated.add(mc_id)  # row absent -> bridge default in _fire_probabilities
    return rows, discriminated


def expected_information_gain(
    hypothesis_set: HypothesisSet,
    item: PracticeItem,
    rubric: Rubric | None = None,
    *,
    item_a: float = 1.0,
    item_b: float = 0.0,
    irt: ProbeIRTConfig | None = None,
    discrimination: dict[str, ItemMisconceptionDiscrimination] | None = None,
    discriminated_ids: set[str] | None = None,
) -> float:
    fatal_error_ids = _fatal_error_ids(item, rubric)
    known_error_types = hypothesis_set.known_error_types
    conditionals = {
        hypothesis.label: conditional_distribution(
            hypothesis,
            item_a=item_a,
            item_b=item_b,
            irt=irt,
            fatal_error_ids=fatal_error_ids,
            known_error_types=known_error_types,
            discrimination=discrimination,
            discriminated_ids=discriminated_ids,
        )
        for hypothesis in hypothesis_set.hypotheses
    }
    prior = hypothesis_set.prior
    outcomes = next(iter(conditionals.values())).keys()
    mixture: dict[Outcome, float] = {outcome: 0.0 for outcome in outcomes}
    for hypothesis in hypothesis_set.hypotheses:
        weight = prior.get(hypothesis.label, 0.0)
        for outcome, probability in conditionals[hypothesis.label].items():
            mixture[outcome] += weight * probability

    eig = 0.0
    for hypothesis in hypothesis_set.hypotheses:
        weight = prior.get(hypothesis.label, 0.0)
        if weight <= 0:
            continue
        conditional = conditionals[hypothesis.label]
        kl = 0.0
        for outcome, probability in conditional.items():
            mixture_probability = mixture[outcome]
            if probability > 0 and mixture_probability > 0:
                kl += probability * log(probability / mixture_probability)
        eig += weight * kl
    return max(eig, 0.0)


def facet_conditional_distribution(
    hypothesis_label: str,
    *,
    facet_id: str,
    candidate_facet_support: set[str],
    fatal_error_ids: set[str],
    known_error_types: list[str],
    item_a: float = 1.0,
    item_b: float = 0.0,
    irt: ProbeIRTConfig | None = None,
) -> dict[Outcome, float]:
    """Per-facet diagnostic outcome model for v0.3 follow-up selection.

    This deliberately uses the static candidate facet support available before
    an attempt is served. It does not depend on attempt-time covered facets.
    """

    irt = irt or ProbeIRTConfig()
    error_types: list[str | None] = [None, *known_error_types]
    distribution: dict[Outcome, float] = {
        (bucket, error_type): 0.0 for bucket in SCORE_BUCKETS for error_type in error_types
    }
    probes_facet = facet_id in candidate_facet_support
    hypothesis_error = hypothesis_label.split(":", 1)[1] if hypothesis_label.startswith("misconception:") else None
    probes_misconception = hypothesis_error is not None and hypothesis_error in fatal_error_ids

    if not probes_facet:
        low, mid, high = _graded_marginals(item_a * (irt.theta_mastered - item_b), irt.cut_mid, irt.cut_high)
        distribution[("low", None)] = low
        distribution[("mid", None)] = mid
        distribution[("high", None)] = high
        return distribution

    if hypothesis_label == f"facet_solid:{facet_id}" or (hypothesis_error is not None and not probes_misconception):
        low, mid, high = _graded_marginals(item_a * (irt.theta_mastered - item_b), irt.cut_mid, irt.cut_high)
        distribution[("low", None)] = low
        distribution[("mid", None)] = mid
        distribution[("high", None)] = high
        return distribution

    low, mid, high = _graded_marginals(item_a * (irt.theta_unfamiliar - item_b), irt.cut_mid, irt.cut_high)
    if hypothesis_label == f"facet_absent:{facet_id}" or hypothesis_error is None:
        distribution[("low", None)] = low
        distribution[("mid", None)] = mid
        distribution[("high", None)] = high
        return distribution

    distribution[("low", hypothesis_error)] = low * irt.err_low_frac
    distribution[("low", None)] = low * (1.0 - irt.err_low_frac)
    distribution[("mid", hypothesis_error)] = mid * irt.err_mid_frac
    distribution[("mid", None)] = mid * (1.0 - irt.err_mid_frac)
    distribution[("high", None)] = high
    return distribution


def facet_expected_information_gain(
    hypothesis_marginal: dict[str, float],
    *,
    facet_id: str,
    candidate_facet_support: set[str],
    fatal_error_ids: set[str],
    item_a: float = 1.0,
    item_b: float = 0.0,
    irt: ProbeIRTConfig | None = None,
) -> float:
    """Expected entropy drop for one facet marginal, in nats.

    This is the facet-objective counterpart to ``expected_information_gain``.
    It uses per-facet score buckets and must not call the global outcome EIG.
    """

    prior = _normalized_prior(hypothesis_marginal)
    if len(prior) <= 1:
        return 0.0
    known_error_types = sorted(
        label.split(":", 1)[1]
        for label in prior
        if label.startswith("misconception:")
    )
    conditionals = {
        label: facet_conditional_distribution(
            label,
            facet_id=facet_id,
            candidate_facet_support=candidate_facet_support,
            fatal_error_ids=fatal_error_ids,
            known_error_types=known_error_types,
            item_a=item_a,
            item_b=item_b,
            irt=irt,
        )
        for label in prior
    }
    outcomes = next(iter(conditionals.values())).keys()
    mixture: dict[Outcome, float] = {outcome: 0.0 for outcome in outcomes}
    for label, weight in prior.items():
        for outcome, probability in conditionals[label].items():
            mixture[outcome] += weight * probability

    eig = 0.0
    for label, weight in prior.items():
        conditional = conditionals[label]
        kl = 0.0
        for outcome, probability in conditional.items():
            mixture_probability = mixture[outcome]
            if probability > 0 and mixture_probability > 0:
                kl += probability * log(probability / mixture_probability)
        eig += weight * kl
    return max(eig, 0.0)


def apply_facet_observation(
    hypothesis_marginal: dict[str, float],
    *,
    facet_id: str,
    candidate_facet_support: set[str],
    fatal_error_ids: set[str],
    observed_bucket: str,
    observed_error_type: str | None,
    item_a: float = 1.0,
    item_b: float = 0.0,
    irt: ProbeIRTConfig | None = None,
) -> dict[str, float]:
    prior = _normalized_prior(hypothesis_marginal)
    if not prior:
        return prior
    known_error_types = sorted(
        label.split(":", 1)[1]
        for label in prior
        if label.startswith("misconception:")
    )
    updated: dict[str, float] = {}
    for label, probability in prior.items():
        conditional = facet_conditional_distribution(
            label,
            facet_id=facet_id,
            candidate_facet_support=candidate_facet_support,
            fatal_error_ids=fatal_error_ids,
            known_error_types=known_error_types,
            item_a=item_a,
            item_b=item_b,
            irt=irt,
        )
        likelihood = conditional.get((observed_bucket, observed_error_type), 0.0)
        if likelihood <= 0 and observed_error_type is not None:
            likelihood = sum(
                p for (bucket, _error), p in conditional.items() if bucket == observed_bucket
            )
        updated[label] = probability * likelihood
    total = sum(updated.values())
    if total <= 0:
        return prior
    return {label: value / total for label, value in updated.items()}


def probe_eig_component(
    hypothesis_set: HypothesisSet,
    item: PracticeItem,
    rubric: Rubric | None = None,
    *,
    item_a: float = 1.0,
    item_b: float = 0.0,
    irt: ProbeIRTConfig | None = None,
) -> float:
    size = len(hypothesis_set.hypotheses)
    if size <= 1:
        return 0.0
    eig = expected_information_gain(
        hypothesis_set, item, rubric, item_a=item_a, item_b=item_b, irt=irt
    )
    return eig / log(size)


@dataclass(frozen=True)
class ProbePosterior:
    """The hypothesis-set belief after replaying observed probe attempts.

    `prior` is the locked entry prior from the `hypothesis_sets` row; `posterior`
    is that prior conditioned on every probe-phase attempt's observed outcome.
    `realized_information_gain` is `H(prior) - H(posterior)` in nats (the actual
    IG redeemed against the same hypothesis set that EIG is computed over).
    """

    hypothesis_set: HypothesisSet
    prior: dict[str, float]
    posterior: dict[str, float]
    attempts: int
    realized_information_gain: float
    normalized_information_gain: float

    @property
    def top_probability(self) -> float:
        return max(self.posterior.values(), default=0.0)


def score_bucket(rubric_score: int) -> str:
    """Bucketize a rubric score per spec §14.4: {0,1}->low, {2,3}->mid, {4}->high."""

    if rubric_score <= 1:
        return "low"
    if rubric_score <= 3:
        return "mid"
    return "high"


def _entropy(distribution: dict[str, float]) -> float:
    return -sum(p * log(p) for p in distribution.values() if p > 0)


def _normalized_prior(distribution: dict[str, float]) -> dict[str, float]:
    cleaned = {str(label): max(float(probability), 0.0) for label, probability in distribution.items()}
    total = sum(cleaned.values())
    if total <= 0:
        return {}
    return {label: probability / total for label, probability in cleaned.items()}


def _observation_likelihoods(
    hypothesis_set: HypothesisSet,
    item: PracticeItem,
    rubric: Rubric | None,
    bucket: str,
    error_type: str | None,
    *,
    item_a: float = 1.0,
    item_b: float = 0.0,
    irt: ProbeIRTConfig | None = None,
    self_tag_weight: float | None = None,
    discrimination: dict[str, ItemMisconceptionDiscrimination] | None = None,
    discriminated_ids: set[str] | None = None,
    fired_channel: str | None = None,
) -> dict[str, float]:
    """`P(observed | h, item)` per hypothesis for one attempt outcome.

    When the observed `(bucket, error_type)` is not represented in the
    conditional (an unknown error type, or a joint with zero mass under every
    hypothesis such as `(high, E)`), the observation degrades to the score-bucket
    marginal so a single attempt can never zero out the whole posterior.

    When ``self_tag_weight`` is supplied the error label is a *learner-attached*
    misconception the item's rubric does not assert (spec §12.2): the likelihood
    becomes the trust-weighted mixture ``w·P_probe + (1−w)·P_marg`` so the score
    bucket is taken at face value while the label is only partially trusted.

    Registry channels (spec §7 first bullet): on a discriminating item the fire is
    observed from the attempt's error events (``fired_channel``), not the score
    bucket, so a fired keyed fatal reads ``(low, <mc_id>)`` and a clean attempt
    reads the null channel at its bucket. Items with no discrimination link leave
    the fire channel untouched — registry beliefs get only bucket-marginal evidence.
    """

    fatal_error_ids = _fatal_error_ids(item, rubric)
    known_error_types = hypothesis_set.known_error_types
    discriminated_ids = set(discriminated_ids or ())
    if discriminated_ids:
        return _registry_observation_likelihoods(
            hypothesis_set,
            bucket,
            fired_channel,
            discrimination=discrimination or {},
            discriminated_ids=discriminated_ids,
            item_a=item_a,
            item_b=item_b,
            irt=irt,
        )
    if self_tag_weight is not None and error_type is not None:
        return _self_tag_likelihoods(
            hypothesis_set,
            bucket,
            error_type,
            fatal_error_ids,
            known_error_types,
            item_a=item_a,
            item_b=item_b,
            irt=irt,
            weight=self_tag_weight,
        )
    likelihoods: dict[str, float] = {}
    conditionals: dict[str, dict[Outcome, float]] = {}
    for hypothesis in hypothesis_set.hypotheses:
        conditional = conditional_distribution(
            hypothesis,
            item_a=item_a,
            item_b=item_b,
            irt=irt,
            fatal_error_ids=fatal_error_ids,
            known_error_types=known_error_types,
        )
        conditionals[hypothesis.label] = conditional
        if error_type is not None and (bucket, error_type) in conditional:
            likelihoods[hypothesis.label] = conditional[(bucket, error_type)]
        else:
            likelihoods[hypothesis.label] = sum(
                probability for (outcome_bucket, _), probability in conditional.items() if outcome_bucket == bucket
            )
    return likelihoods


def _registry_observation_likelihoods(
    hypothesis_set: HypothesisSet,
    bucket: str,
    fired_channel: str | None,
    *,
    discrimination: dict[str, ItemMisconceptionDiscrimination],
    discriminated_ids: set[str],
    item_a: float,
    item_b: float,
    irt: ProbeIRTConfig | None,
) -> dict[str, float]:
    """Fire-keyed observation on a discriminating item (spec §7).

    The fire is read from the attempt's error events: a keyed fatal on the item's
    fire channel takes the ``(low, <channel>)`` mass of the §3 overlay; otherwise
    the null-channel mass at the observed bucket carries the (informative) clean
    signal. Both are computed straight from ``conditional_distribution`` so EIG,
    the mixture, and this update stay internally consistent.
    """

    fire_channel = sorted(discriminated_ids)[0]
    observed_fire = fired_channel is not None and fired_channel in discriminated_ids
    likelihoods: dict[str, float] = {}
    for hypothesis in hypothesis_set.hypotheses:
        conditional = conditional_distribution(
            hypothesis,
            item_a=item_a,
            item_b=item_b,
            irt=irt,
            fatal_error_ids=set(),
            known_error_types=hypothesis_set.known_error_types,
            discrimination=discrimination,
            discriminated_ids=discriminated_ids,
        )
        if observed_fire:
            likelihoods[hypothesis.label] = conditional.get((bucket, fire_channel), 0.0) or conditional.get(
                ("low", fire_channel), 0.0
            )
        else:
            likelihoods[hypothesis.label] = conditional.get((bucket, None), 0.0)
    return likelihoods


def _self_tag_likelihoods(
    hypothesis_set: HypothesisSet,
    bucket: str,
    error_type: str,
    fatal_error_ids: set[str],
    known_error_types: list[str],
    *,
    item_a: float,
    item_b: float,
    irt: ProbeIRTConfig | None,
    weight: float,
) -> dict[str, float]:
    """Trust-weighted *label* mixture ``L(h) = w·P_probe(s,E|h) + (1−w)·P_marg(s|h)`` (§12.2).

    ``P_probe`` is the §5 conditional computed *as if the item probes E* (E added to
    the effective fatal set), so ``misconception:E`` is low-anchored and ``(low, E)``
    confirms it. ``P_marg`` is the score-bucket marginal under the item's *actual*
    rubric probing status — the current label-ignoring update. At ``w=1`` this equals
    the rubric-fatal path; at ``w=0`` it is bit-for-bit the current no-label update,
    so ``mastered`` is only *softly* downweighted by an uncertain attribution.
    """

    probe_fatal = fatal_error_ids | {error_type}
    likelihoods: dict[str, float] = {}
    for hypothesis in hypothesis_set.hypotheses:
        probe_conditional = conditional_distribution(
            hypothesis,
            item_a=item_a,
            item_b=item_b,
            irt=irt,
            fatal_error_ids=probe_fatal,
            known_error_types=known_error_types,
        )
        marginal_conditional = conditional_distribution(
            hypothesis,
            item_a=item_a,
            item_b=item_b,
            irt=irt,
            fatal_error_ids=fatal_error_ids,
            known_error_types=known_error_types,
        )
        p_probe = probe_conditional.get((bucket, error_type), 0.0)
        p_marg = sum(
            probability for (outcome_bucket, _), probability in marginal_conditional.items() if outcome_bucket == bucket
        )
        likelihoods[hypothesis.label] = weight * p_probe + (1.0 - weight) * p_marg
    return likelihoods


def _resolve_self_tag_weight(
    vault: LoadedVault,
    item: PracticeItem,
    rubric: Rubric | None,
    hypothesis_set: HypothesisSet,
    error_type: str | None,
    bucket: str,
) -> float | None:
    """``w_self`` for a self-attached misconception, or ``None`` for the standard path.

    Returns ``None`` (keep existing behavior) when the observed error is rubric-fatal
    (``w=1``, the §5 path) or is not one of the locked hypotheses (effect 2 only,
    §12.1 — the label seeds the *next* set and the score bucket carries this attempt).
    Deterministic in ``(vault, attempt, locked set)``, so the replay stays idempotent.
    """

    if not error_type:
        return None
    if error_type in _fatal_error_ids(item, rubric):
        return None
    if error_type not in hypothesis_set.known_error_types:
        return None
    return self_tag_weight(vault, item, error_type, bucket, vault.config.probe.self_tag)


def probe_posterior(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    probe_state: ProbeStateRecord | None = None,
    hypothesis_set: HypothesisSet | None = None,
) -> ProbePosterior | None:
    """Replay probe-phase attempts into the hypothesis-set posterior.

    Returns ``None`` when the Learning Object has no probe phase or no locked
    hypothesis set. Stateless: the posterior is recomputed from `practice_attempts`
    so it is idempotent and never drifts from the recorded evidence.
    """

    probe_state = probe_state if probe_state is not None else repository.probe_state(learning_object_id)
    if probe_state is None or probe_state.hypothesis_set_id is None:
        return None
    if hypothesis_set is None:
        record = repository.fetch_hypothesis_set(probe_state.hypothesis_set_id)
        if record is None:
            return None
        hypothesis_set = HypothesisSet.from_record(record)
    if not hypothesis_set.hypotheses:
        return None

    prior = dict(hypothesis_set.prior)
    posterior = dict(prior)
    attempts = _probe_phase_attempts(repository, learning_object_id, probe_state.entered_at)
    for attempt in attempts:
        item = vault.practice_items.get(attempt.get("practice_item_id"))
        if item is None:
            continue
        rubric = vault.rubric_for_item(item)
        bucket = score_bucket(int(attempt.get("rubric_score") or 0))
        error_type = attempt.get("error_type")
        item_a, item_b, probe_irt = resolve_item_irt(vault, item)
        tag_weight = _resolve_self_tag_weight(vault, item, rubric, hypothesis_set, error_type, bucket)
        discrimination, discriminated_ids = item_registry_discrimination(
            repository, vault, item, rubric, hypothesis_set
        )
        fired_channel = None
        if discriminated_ids:
            fired = {
                str(evt.get("misconception_id"))
                for evt in repository.error_events_for_attempt(str(attempt.get("id")))
                if evt.get("misconception_id")
            } & discriminated_ids
            fired_channel = sorted(fired)[0] if fired else None
        posterior = _apply_observation(
            hypothesis_set,
            item,
            rubric,
            bucket,
            error_type,
            posterior,
            item_a=item_a,
            item_b=item_b,
            irt=probe_irt,
            self_tag_weight=tag_weight,
            discrimination=discrimination,
            discriminated_ids=discriminated_ids,
            fired_channel=fired_channel,
        )

    size = len(hypothesis_set.hypotheses)
    normalizer = log(size) if size > 1 else 1.0
    realized = max(_entropy(prior) - _entropy(posterior), 0.0)
    return ProbePosterior(
        hypothesis_set=hypothesis_set,
        prior=prior,
        posterior=posterior,
        attempts=len(attempts),
        realized_information_gain=realized,
        normalized_information_gain=realized / normalizer,
    )


def _apply_observation(
    hypothesis_set: HypothesisSet,
    item: PracticeItem,
    rubric: Rubric | None,
    bucket: str,
    error_type: str | None,
    posterior: dict[str, float],
    *,
    item_a: float = 1.0,
    item_b: float = 0.0,
    irt: ProbeIRTConfig | None = None,
    self_tag_weight: float | None = None,
    discrimination: dict[str, ItemMisconceptionDiscrimination] | None = None,
    discriminated_ids: set[str] | None = None,
    fired_channel: str | None = None,
) -> dict[str, float]:
    likelihoods = _observation_likelihoods(
        hypothesis_set,
        item,
        rubric,
        bucket,
        error_type,
        item_a=item_a,
        item_b=item_b,
        irt=irt,
        self_tag_weight=self_tag_weight,
        discrimination=discrimination,
        discriminated_ids=discriminated_ids,
        fired_channel=fired_channel,
    )
    updated = {label: posterior[label] * likelihoods.get(label, 0.0) for label in posterior}
    total = sum(updated.values())
    if total <= 0 and error_type is not None:
        # Outcome impossible under every hypothesis when conditioned on the error
        # type; retry on the score bucket alone before giving up.
        likelihoods = _observation_likelihoods(
            hypothesis_set, item, rubric, bucket, None, item_a=item_a, item_b=item_b, irt=irt
        )
        updated = {label: posterior[label] * likelihoods.get(label, 0.0) for label in posterior}
        total = sum(updated.values())
    if total <= 0:
        return posterior
    return {label: value / total for label, value in updated.items()}


def _probe_phase_attempts(
    repository: Repository,
    learning_object_id: str,
    entered_at: str | None,
) -> list[dict[str, object]]:
    rows = repository.list_recent_attempts_by_learning_object(learning_object_id, limit=100)
    entered = parse_utc(entered_at)
    selected: list[dict[str, object]] = []
    for row in rows:
        created = parse_utc(row.get("created_at"))
        if entered is not None and created is not None and created < entered:
            continue
        selected.append(row)
    selected.sort(key=lambda row: (str(row.get("created_at") or ""), str(row.get("id") or "")))
    return selected


def current_hypothesis_set(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    probe_state: ProbeStateRecord | None = None,
) -> HypothesisSet | None:
    """The locked hypothesis set with its prior replaced by the live posterior.

    Used by the scheduler so probe-EIG reflects accumulated evidence instead of
    re-using the entry prior on every elicitation.
    """

    posterior = probe_posterior(vault, repository, learning_object_id, probe_state=probe_state)
    if posterior is None:
        return None
    hypothesis_set = posterior.hypothesis_set
    return HypothesisSet(
        learning_object_id=hypothesis_set.learning_object_id,
        hypotheses=hypothesis_set.hypotheses,
        prior=posterior.posterior,
        id=hypothesis_set.id,
    )


def persist_probe_beliefs(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    posterior: ProbePosterior,
    *,
    clock: Clock | None = None,
) -> None:
    """Persist the misconception marginals of the posterior to `learner_state_beliefs`.

    Both legacy `misconception:<error_type>` and registry `misconception:<id>`
    hypotheses persist under scope_type `misconception`; the registry rows key the
    belief on their misconception id (spec §3/§7). The `mastered`/`unfamiliar` base
    hypotheses carry no channel and are skipped.
    """

    now = utc_now_iso(clock)
    learning_object = vault.learning_objects.get(learning_object_id)
    subject = learning_object.subjects[0] if learning_object is not None and learning_object.subjects else None
    algorithm_version = vault.config.algorithms.algorithm_version
    for hypothesis in posterior.hypothesis_set.hypotheses:
        scope_id = hypothesis.channel_key
        if scope_id is None:
            continue
        probability = posterior.posterior.get(hypothesis.label, 0.0)
        prior_probability = posterior.prior.get(hypothesis.label, 0.0)
        repository.upsert_state_belief(
            scope_type="misconception",
            scope_id=scope_id,
            belief_key=learning_object_id,
            mean=probability,
            variance=max(probability * (1.0 - probability), 0.0),
            evidence_count=posterior.attempts,
            subject=subject,
            last_surprise=probability - prior_probability,
            last_evidence_at=now,
            algorithm_version=algorithm_version,
            clock=clock,
        )


def record_probe_attempt(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    clock: Clock | None = None,
) -> None:
    """Advance an in-progress probe after an attempt on its Learning Object.

    No-op when the Learning Object is not currently in a probe phase. The
    hypothesis set stays locked; this updates progress, refreshes the persisted
    hypothesis posterior, and decides completion.

    Completion fires when either the attempt target is reached, the mastery latent
    variance falls to `variance_convergence_threshold` (the "mastery" family), or
    the hypothesis posterior concentrates so its residual mass is within the same
    threshold (the "hypothesis" family). The threshold is read against the
    *logit* variance, not the sigmoid-compressed display variance — the latter
    starts at ~0.0625 even with zero evidence and would converge spuriously.
    """

    probe_state = repository.probe_state(learning_object_id)
    if probe_state is None or probe_state.status != "in_progress":
        return

    completed = probe_state.probe_attempts_completed + 1
    threshold = vault.config.probe.variance_convergence_threshold
    families_converged = list(probe_state.families_converged)

    posterior = probe_posterior(vault, repository, learning_object_id, probe_state=probe_state)
    if posterior is not None:
        persist_probe_beliefs(vault, repository, learning_object_id, posterior, clock=clock)
        if posterior.posterior and (1.0 - posterior.top_probability) <= threshold:
            if "hypothesis" not in families_converged:
                families_converged.append("hypothesis")

    mastery = repository.mastery_state(learning_object_id)
    if mastery is not None and mastery.logit_variance <= threshold and "mastery" not in families_converged:
        families_converged.append("mastery")

    converged = bool(families_converged)
    status = "in_progress"
    completed_at = None
    if completed >= probe_state.probe_attempts_target or converged:
        status = "complete"
        completed_at = utc_now_iso(clock)
    repository.upsert_probe_state(
        learning_object_id=learning_object_id,
        status=status,
        algorithm_version=vault.config.algorithms.algorithm_version,
        probe_phase_id=probe_state.probe_phase_id,
        hypothesis_set_id=probe_state.hypothesis_set_id,
        probe_attempts_completed=completed,
        probe_attempts_target=probe_state.probe_attempts_target,
        families_converged=families_converged,
        entered_at=probe_state.entered_at,
        completed_at=completed_at,
        clock=clock,
    )


def _fatal_error_ids(item: PracticeItem, rubric: Rubric | None = None) -> set[str]:
    effective_rubric = rubric or item.grading_rubric
    if effective_rubric is None:
        return set()
    return {fatal_error.id for fatal_error in effective_rubric.fatal_errors}


def _decay(created_at: str | None, now: datetime) -> float:
    created = parse_utc(created_at)
    if created is None:
        return 1.0
    days_since = max(0.0, (now - created).total_seconds() / 86400)
    return exp(-days_since / 7)


def _neighbor_misconceptions(
    vault: LoadedVault,
    repository: Repository,
    concept_id: str,
    now: datetime,
) -> list[tuple[str, ActiveErrorEvent]]:
    neighbors: list[str] = []
    for edge in vault.edges:
        if edge.relation_type != "confusable_with":
            continue
        if edge.source == concept_id:
            neighbors.append(edge.target)
        elif edge.target == concept_id:
            neighbors.append(edge.source)
    if not neighbors:
        return []

    mastery_states = repository.mastery_states()
    active_errors = repository.active_error_events()
    concept_to_los: dict[str, list[str]] = {}
    for lo_id, learning_object in vault.learning_objects.items():
        concept_to_los.setdefault(learning_object.concept, []).append(lo_id)

    results: list[tuple[str, ActiveErrorEvent]] = []
    for neighbor in neighbors:
        neighbor_los = concept_to_los.get(neighbor, [])
        neighbor_mastery = 0.0
        for lo_id in neighbor_los:
            state = mastery_states.get(lo_id)
            if state is not None:
                neighbor_mastery = max(neighbor_mastery, sigmoid(state.logit_mean))
        if neighbor_mastery < 0.7:
            continue
        neighbor_lo_set = set(neighbor_los)
        candidate_errors = [
            error
            for error in active_errors
            if error.learning_object_id in neighbor_lo_set and error.is_misconception
        ]
        if not candidate_errors:
            continue
        most_severe = max(candidate_errors, key=lambda error: error.severity)
        results.append((neighbor, most_severe))
    return results


def _neighbor_registry_misconceptions(
    vault: LoadedVault,
    repository: Repository,
    concept_id: str,
    now: datetime,
) -> list[tuple[str, "MisconceptionRecord"]]:
    """Registry rows on confusable-neighbor concepts, gated by neighbor mastery ≥ 0.7.

    Mirrors ``_neighbor_misconceptions`` (spec §3 neighbor propagation) but over the
    normalized registry rather than raw error events; ``source_concept_id`` is set
    on the resulting hypotheses so telemetry can attribute the propagation.
    """

    neighbors: list[str] = []
    for edge in vault.edges:
        if edge.relation_type != "confusable_with":
            continue
        if edge.source == concept_id:
            neighbors.append(edge.target)
        elif edge.target == concept_id:
            neighbors.append(edge.source)
    if not neighbors:
        return []

    mastery_states = repository.mastery_states()
    concept_to_los: dict[str, list[str]] = {}
    for lo_id, learning_object in vault.learning_objects.items():
        concept_to_los.setdefault(learning_object.concept, []).append(lo_id)

    results: list[tuple[str, "MisconceptionRecord"]] = []
    seen: set[str] = set()
    for neighbor in neighbors:
        neighbor_los = concept_to_los.get(neighbor, [])
        neighbor_mastery = 0.0
        for lo_id in neighbor_los:
            state = mastery_states.get(lo_id)
            if state is not None:
                neighbor_mastery = max(neighbor_mastery, sigmoid(state.logit_mean))
        if neighbor_mastery < 0.7:
            continue
        for record in repository.misconceptions_for_concepts([neighbor], statuses=("active", "resolving")):
            if record.id in seen:
                continue
            seen.add(record.id)
            results.append((neighbor, record))
    return results
