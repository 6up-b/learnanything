"""KM2 canonical belief projection (§5.3/§5.4/§6/§7.1).

Recomputes the canonical shared facet belief state (`facet_recall_state`) and
the capability-sliced certification ledger (`facet_capability_evidence`) as a
pure, deterministic projection over the immutable observation ledger. Because
beta masses accumulate additively, the projection is order-independent for the
belief marginals; only timestamps and consecutive-failure runs depend on the
global chronological order the ledger already provides. This makes replay
byte-identical by construction, and sidesteps the shared-facet reset hazard of
incremental per-LO updates (a facet lives under many LOs).

Runs only under mvp-0.7 (`KM_ALGORITHM_VERSION`); the caller guards. The result
is derived state — not a new evidence source — consistent with "evidence, not
mastery": it is a fold over attempts + grading, exactly like every other
`rebuild_derived_state` output.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.assessment_contracts import (
    CANONICAL_STATE_VERSIONS,
    KM_ALGORITHM_VERSION,
    P0_ALGORITHM_VERSION,
)
from learnloop.services.capability_mapping import (
    CriterionOutcome,
    allocate_success_mass,
    certification_credit,
    compile_criterion_targets,
    criterion_pseudo_mass,
    localize_criterion_outcomes,
)
from learnloop.services.evidence import attempt_evidence_mass
from learnloop.services.receipt_contributions import cap_observation_contributions
from learnloop.vault.models import CriterionTarget, LoadedVault, PracticeItem

# Outcome fraction below which a criterion counts as failed (matches the legacy
# recall-coverage failure threshold so mvp-0.7 semantics stay comparable).
FAILURE_THRESHOLD = 0.40

# A repeated observation on an already-seen surface/correlation group is not
# fresh independent evidence (§6): its inference mass is discounted and it adds
# no new independent-surface group. Overridable via [evidence.correlation].
DEFAULT_REPEAT_SURFACE_DISCOUNT = 0.25

# Assistance channels that certify nothing (§5.4/§6).
ASSISTED_ATTEMPT_TYPES: frozenset[str] = frozenset(
    {"hinted_attempt", "guided_walkthrough", "reconstruction_after_walkthrough"}
)


def surface_group_id(item: PracticeItem) -> str:
    """The correlation/surface group an item's evidence belongs to (§6).

    Vault-wide: a shared stimulus/testlet, source-example family, or
    solution-template family collapses near-clones (even under different LOs)
    into one group, so a clone cannot mint a fresh independent surface group.
    Falls back to the legacy surface_family, then the item id.
    """

    fp = item.evidence_fingerprint
    for candidate in (
        fp.shared_stimulus_id,
        fp.source_family,
        fp.solution_recipe_family,
        item.surface_family,
    ):
        if candidate:
            return str(candidate)
    return f"item:{item.id}"


@dataclass
class _RecallAcc:
    alpha: float = 1.0
    beta: float = 1.0
    independent_mass: float = 0.0
    raw_mass: float = 0.0
    last_observed_at: str | None = None
    last_error_at: str | None = None
    consecutive_failures: int = 0
    created_at: str | None = None


@dataclass
class _CapAcc:
    direct_positive_mass: float = 0.0
    direct_negative_mass: float = 0.0
    embedded_positive_mass: float = 0.0
    embedded_negative_mass: float = 0.0
    certification_credit: float = 0.0
    groups: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class _HistoricalCriterion:
    id: str
    points: float
    depends_on: tuple[str, ...]
    correlation_group: str | None
    targets: tuple[CriterionTarget, ...]


def _historical_contract(
    repository: Repository, evidence: list[dict[str, Any]]
) -> Mapping[str, Any] | None:
    """Resolve the immutable assessment contract attached to this grading.

    A grading revision is expected to use one contract version across all of its
    criterion observations. Mixed/missing lineage is treated as legacy data and
    falls back to the live item below; new writes require lineage in attempts.py.
    """

    version_ids = {
        str(row["assessment_contract_version_id"])
        for row in evidence
        if row.get("assessment_contract_version_id")
    }
    if len(version_ids) != 1:
        return None
    stored = repository.fetch_assessment_contract_version(next(iter(version_ids)))
    return stored.get("contract") if stored is not None else None


def _contract_criteria(contract: Mapping[str, Any]) -> list[_HistoricalCriterion]:
    criteria: list[_HistoricalCriterion] = []
    for raw in contract.get("criteria") or []:
        targets = tuple(
            CriterionTarget(
                facet=str(target["facet"]),
                capability=str(target["capability"]),
                role=str(target.get("role") or "primary"),
            )
            for target in raw.get("targets") or []
        )
        criteria.append(
            _HistoricalCriterion(
                id=str(raw["id"]),
                points=float(raw.get("max_points") or 0.0),
                depends_on=tuple(str(value) for value in raw.get("depends_on") or []),
                correlation_group=(
                    str(raw["correlation_group"])
                    if raw.get("correlation_group") is not None
                    else None
                ),
                targets=targets,
            )
        )
    return criteria


def _contract_surface_group(contract: Mapping[str, Any], practice_item_id: str) -> str:
    fingerprint = contract.get("evidence_fingerprint") or {}
    for key in ("shared_stimulus_id", "source_family", "solution_recipe_family"):
        if fingerprint.get(key):
            return str(fingerprint[key])
    if contract.get("surface_family"):
        return str(contract["surface_family"])
    return f"item:{practice_item_id}"


def _attribution_weights(
    raw: object, targets: list[CriterionTarget]
) -> dict[tuple[str, str], float]:
    """Normalize persisted failure attribution over the criterion targets."""

    if isinstance(raw, Mapping):
        entries = raw.get("targets") or raw.get("distribution") or []
    else:
        entries = raw if isinstance(raw, list) else []
    allowed = {(target.facet, target.capability) for target in targets}
    weights: dict[tuple[str, str], float] = defaultdict(float)
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        facet = str(entry.get("facet") or "")
        capability = str(entry.get("capability") or "")
        key = (facet, capability)
        if key not in allowed:
            continue
        try:
            weight = max(0.0, float(entry.get("weight", entry.get("probability", 0.0))))
        except (TypeError, ValueError):
            continue
        weights[key] += weight
    total = sum(weights.values())
    if total <= 0:
        return {}
    return {key: weight / total for key, weight in weights.items()}


def _repeat_discount(vault: LoadedVault) -> float:
    extra = getattr(vault.config.evidence.correlation, "__pydantic_extra__", None) or {}
    value = extra.get("repeat_surface_discount")
    if value is None:
        return DEFAULT_REPEAT_SURFACE_DISCOUNT
    return float(value)


def project_canonical_facet_state(
    vault: LoadedVault, repository: Repository, *, clock: Clock | None = None
) -> None:
    """Recompute and persist the canonical belief cache.

    mvp-0.7 (``KM_ALGORITHM_VERSION``) is the byte-identical legacy compatibility
    projection: raw ``points_awarded/points`` score fractions, attempt-type mass
    only. mvp-0.8 (``P0_ALGORITHM_VERSION``, P0.3 §4.3) reads the authoritative
    events ledger and feeds a reliability-discounted EffectiveObservation: the
    calibrated ``E[true_score_fraction]`` replaces the raw fraction and the
    certainty LCB multiplies the evidence mass BEFORE the existing caps /
    localization / assistance discounts bind. Reliability never creates mass."""

    algorithm_version = vault.config.algorithms.algorithm_version
    if algorithm_version not in CANONICAL_STATE_VERSIONS:
        return
    use_p0 = algorithm_version == P0_ALGORITHM_VERSION
    p0_score_fraction: dict[str, float] = {}
    if use_p0:
        from learnloop.services.effective_observation import build_effective_observation
        from learnloop.services.outcome_schemas import (
            COARSE_RESPONSE_SLUG,
            ensure_builtin_schemas,
        )

        ensure_builtin_schemas(repository, clock=clock)
        schema_row = repository.fetch_outcome_schema_version(slug=COARSE_RESPONSE_SLUG)
        if schema_row is not None:
            import json as _json_mod

            p0_score_fraction = _json_mod.loads(schema_row["score_fraction_json"])

    merge_map = repository.facet_merge_map()
    repeat_discount = _repeat_discount(vault)
    cert_cfg = vault.config.evidence.certification
    overrides = dict(cert_cfg.group_budgets)
    max_groups = cert_cfg.max_groups_per_attempt

    recall: dict[tuple[str, str, str | None], _RecallAcc] = defaultdict(_RecallAcc)
    cap: dict[tuple[str, str], _CapAcc] = defaultdict(_CapAcc)
    unresolved: list[dict[str, object]] = []

    def resolve(facet_id: str) -> str:
        canonical = vault.canonical_facet_id(facet_id)
        # Transitive merge resolution over aliases (§7.1); no beta mass copied.
        current = canonical
        seen: set[str] = set()
        while current in merge_map and current not in seen:
            seen.add(current)
            current = merge_map[current]
        return current

    ledger_rows = (
        repository.canonical_observation_ledger_v2()
        if use_p0
        else repository.canonical_observation_ledger()
    )
    for attempt in ledger_rows:
        item = vault.practice_items.get(attempt["practice_item_id"])
        contract = _historical_contract(repository, attempt["evidence"])
        if contract is not None:
            criteria = _contract_criteria(contract)
            rubric_total = float(contract.get("rubric_total") or 0.0)
            group_key = _contract_surface_group(contract, attempt["practice_item_id"])
        else:
            # Frozen legacy/compatibility observations predate assessment-contract
            # lineage. New mvp-0.7 observations never take this branch.
            if item is None:
                continue
            rubric = vault.rubric_for_item(item)
            if rubric is None or not rubric.criteria:
                continue
            criteria = [
                _HistoricalCriterion(
                    id=criterion.id,
                    points=criterion.points,
                    depends_on=tuple(criterion.depends_on),
                    correlation_group=criterion.correlation_group,
                    targets=tuple(
                        compile_criterion_targets(item, criterion, resolved_rubric=rubric)
                    ),
                )
                for criterion in rubric.criteria
            ]
            rubric_total = sum(max(criterion.points, 0.0) for criterion in criteria)
            group_key = surface_group_id(item)
        if not criteria:
            continue
        evidence_by_criterion = {
            row["criterion_id"]: row for row in attempt["evidence"]
        }
        rubric_total = rubric_total or 1.0
        emass = attempt_evidence_mass(attempt["attempt_type"], vault.config.evidence)
        # P0.3 (§4.3): the reliability discount. certainty_LCB multiplies the mass
        # BEFORE the caps/localization below; a quarantined/uniform/missing
        # interpretation contributes zero (never silent full credit). The calibrated
        # E[true_score_fraction] replaces the raw points fraction for every criterion.
        p0_fraction: float | None = None
        if use_p0:
            effective_obs = build_effective_observation(
                repository,
                interpretation=attempt.get("active_interpretation"),
                score_fraction=p0_score_fraction,
                attempt_type_mass=emass,
            )
            emass = effective_obs.effective_mass
            p0_fraction = effective_obs.expected_true_score_fraction
        assisted = (
            attempt["attempt_type"] in ASSISTED_ATTEMPT_TYPES
            or int(attempt["hints_used"]) > 0
        )
        assistance = "hinted" if assisted else "unassisted"
        created_at = attempt["created_at"]

        outcomes: list[CriterionOutcome] = []
        for criterion in criteria:
            row = evidence_by_criterion.get(criterion.id)
            fraction = 0.0
            if p0_fraction is not None:
                fraction = p0_fraction
            elif row is not None and criterion.points > 0:
                fraction = max(0.0, min(1.0, float(row["points_awarded"]) / criterion.points))
            outcomes.append(
                CriterionOutcome(
                    criterion_id=criterion.id,
                    passed=fraction >= FAILURE_THRESHOLD,
                    depends_on=tuple(criterion.depends_on),
                )
            )
        localized = {c.criterion_id: c for c in localize_criterion_outcomes(outcomes)}
        criteria_by_id = {c.id: c for c in criteria}

        # certification credit staged per (facet, capability, correlation group)
        # so the per-group cap and attempt ceiling can be applied jointly.
        staged_credit: dict[str, dict[tuple[str, str], float]] = defaultdict(
            lambda: defaultdict(float)
        )

        for outcome in outcomes:
            local = localized[outcome.criterion_id]
            if not local.assessable:
                continue  # descendant of a first error: evidence share 0 (§5.3)
            criterion = criteria_by_id[outcome.criterion_id]
            row = evidence_by_criterion.get(criterion.id)
            fraction = 0.0
            if p0_fraction is not None:
                fraction = p0_fraction
            elif row is not None and criterion.points > 0:
                fraction = max(0.0, min(1.0, float(row["points_awarded"]) / criterion.points))
            targets = list(criterion.targets)
            if not targets:
                continue
            pmass = criterion_pseudo_mass(criterion.points, rubric_total, emass)
            corr_group = criterion.correlation_group or group_key

            attribution = _attribution_weights(
                row.get("attribution_json") if row is not None else None, targets
            )
            negative_fraction = 1.0 - fraction
            unresolved_negative = negative_fraction > 0 and len(targets) > 1 and not attribution
            if unresolved_negative:
                unresolved.append(
                    {
                        "attempt_id": attempt["attempt_id"],
                        "observation_id": (
                            row.get("observation_id")
                            if row is not None and row.get("observation_id")
                            else f"{attempt['attempt_id']}:{criterion.id}:0"
                        ),
                        "candidate_causes": [
                            {"facet": resolve(t.facet), "capability": t.capability}
                            for t in targets
                        ],
                    }
                )
            # Success mass follows authored role weights. Failure mass is handled
            # separately below from the persisted attribution distribution.
            allocations = allocate_success_mass(targets, pmass)
            criterion_discounts: dict[tuple[str, str], tuple[float, bool]] = {}
            for alloc in allocations:
                facet = resolve(alloc.facet)
                capability = alloc.capability
                key = (facet, capability)
                is_new_group = group_key not in cap[key].groups
                discount = 1.0 if is_new_group else repeat_discount
                criterion_discounts[key] = (discount, is_new_group)
                w = alloc.pseudo_mass * discount
                positive = w * fraction
                if positive <= 0:
                    continue
                relationship = "embedded" if alloc.role == "supporting" else "direct"
                if relationship == "embedded":
                    cap[key].embedded_positive_mass += positive
                else:
                    cap[key].direct_positive_mass += positive
                if is_new_group:
                    cap[key].groups.add(group_key)
                credit = certification_credit(
                    positive, relationship=relationship, assistance=assistance
                )
                staged_credit[corr_group][key] += credit

                for scope in (None, attempt["practice_item_id"]):
                    acc = recall[(facet, capability, scope)]
                    if acc.created_at is None:
                        acc.created_at = created_at
                    acc.alpha += positive
                    acc.independent_mass += w if is_new_group else 0.0
                    acc.raw_mass += alloc.pseudo_mass
                    acc.last_observed_at = created_at

            if negative_fraction <= 0 or unresolved_negative:
                continue
            if not attribution and len(targets) == 1:
                attribution = {(targets[0].facet, targets[0].capability): 1.0}
            for target in targets:
                share = attribution.get((target.facet, target.capability), 0.0)
                if share <= 0:
                    continue
                facet = resolve(target.facet)
                key = (facet, target.capability)
                discount, is_new_group = criterion_discounts.get(
                    key,
                    (
                        1.0 if group_key not in cap[key].groups else repeat_discount,
                        group_key not in cap[key].groups,
                    ),
                )
                negative = pmass * negative_fraction * share * discount
                relationship = "embedded" if target.role == "supporting" else "direct"
                if relationship == "embedded":
                    cap[key].embedded_negative_mass += negative
                else:
                    cap[key].direct_negative_mass += negative
                if is_new_group:
                    cap[key].groups.add(group_key)
                for scope in (None, attempt["practice_item_id"]):
                    acc = recall[(facet, target.capability, scope)]
                    if acc.created_at is None:
                        acc.created_at = created_at
                    acc.beta += negative
                    acc.last_observed_at = created_at
                    if fraction < FAILURE_THRESHOLD:
                        acc.last_error_at = created_at
                        acc.consecutive_failures += 1
                    else:
                        acc.consecutive_failures = 0

        # Apply the shared receipt/projection caps, then bank the credit.
        capped_cells = cap_observation_contributions(
            staged_credit,
            attempt_type=attempt["attempt_type"],
            evidence_mass=emass,
            group_budget_overrides=overrides,
            max_groups_per_attempt=max_groups,
        )
        for key, credit in capped_cells.items():
            cap[key].certification_credit += credit

    recall_rows = []
    for (facet, capability, scope), acc in recall.items():
        total = acc.alpha + acc.beta
        mean = acc.alpha / total
        variance = acc.alpha * acc.beta / (total**2 * (total + 1.0))
        recall_rows.append(
            {
                "facet_id": facet,
                "capability_key": capability,
                "practice_item_id": scope,
                "recall_alpha": acc.alpha,
                "recall_beta": acc.beta,
                "recall_mean": mean,
                "recall_variance": variance,
                "independent_evidence_mass": acc.independent_mass,
                "raw_coverage_mass": acc.raw_mass,
                "last_observed_at": acc.last_observed_at,
                "last_error_at": acc.last_error_at,
                "consecutive_failures": acc.consecutive_failures,
                "created_at": acc.created_at,
            }
        )
    capability_rows = [
        {
            "facet_id": facet,
            "capability": capability,
            "direct_positive_mass": acc.direct_positive_mass,
            "direct_negative_mass": acc.direct_negative_mass,
            "embedded_positive_mass": acc.embedded_positive_mass,
            "embedded_negative_mass": acc.embedded_negative_mass,
            "certification_credit": acc.certification_credit,
            "independent_surface_groups": sorted(acc.groups),
        }
        for (facet, capability), acc in cap.items()
    ]
    repository.replace_canonical_facet_state(
        recall_rows=recall_rows,
        capability_rows=capability_rows,
        algorithm_version=algorithm_version,
        clock=clock,
    )
    _sync_unresolved_cause_factors(repository, unresolved, clock=clock)
    # KM5 §4.2: lazy capability-residual activation is derived from the same
    # just-written ledgers (a no-op unless [capabilities].residual_activation_enabled),
    # so it runs on every path that recomputes canonical state — live attempts and
    # replay alike — and a rebuild reproduces activation deterministically.
    project_capability_residuals(vault, repository, clock=clock)


def project_capability_residuals(
    vault: LoadedVault, repository: Repository, *, clock: Clock | None = None
) -> None:
    """Derive lazy capability-residual activation state (§4.2, KM5; DEFAULT OFF).

    A pure fold over the just-written canonical ledgers (``facet_capability_evidence``
    for the capability slices, pooled into a per-facet shared parent) plus the set
    of closed diagnostic episodes. For each ``(facet, capability)`` cell it decides
    activation deterministically:

    * **persistent capability-sliced residual disagreement** — the slice diverges
      from the pooled parent by ``residual_divergence_threshold`` with at least
      ``residual_min_independent_groups`` surface groups and
      ``residual_min_independent_mass`` independent mass; or
    * a **closed diagnostic episode** on the facet demonstrated divergence (the
      episode already paid for the evidence, so a lower
      ``residual_episode_divergence_threshold`` applies).

    Activation writes learner-model state only — a row per activated
    ``(facet, capability)`` — never a curriculum mutation or lock event. The
    residual belief uses the shared parent as a shrinkage prior; genuinely
    ambiguous (no-capability) observations never reach a slice and so stay pooled
    at the parent. Because it is derived here in the projection fold (replace on
    rebuild), replay reproduces activation byte-identically.

    With the feature disabled (the default) this is a complete no-op: the table is
    never touched, so rebuild determinism is identical with the feature on OR off.
    """

    if vault.config.algorithms.algorithm_version not in CANONICAL_STATE_VERSIONS:
        return
    cfg = vault.config.capabilities
    if not getattr(cfg, "residual_activation_enabled", False):
        return

    divergence_threshold = float(getattr(cfg, "residual_divergence_threshold", 0.20))
    min_mass = float(getattr(cfg, "residual_min_independent_mass", 2.0))
    min_groups = int(getattr(cfg, "residual_min_independent_groups", 2))
    episode_threshold = float(getattr(cfg, "residual_episode_divergence_threshold", 0.12))
    shrinkage = float(getattr(cfg, "residual_shrinkage_pseudo_count", 4.0))

    merge_map = repository.facet_merge_map()

    def resolve(facet_id: str) -> str:
        canonical = vault.canonical_facet_id(facet_id)
        current = canonical
        seen: set[str] = set()
        while current in merge_map and current not in seen:
            seen.add(current)
            current = merge_map[current]
        return current

    # Facets with at least one closed diagnostic episode (lower activation bar).
    episode_facets: set[str] = set()
    for episode in repository.list_probe_episodes(statuses=("complete",)):
        for facet_id in episode.required_facets:
            episode_facets.add(resolve(facet_id))

    # Capability slices + pooled shared parent per facet.
    cells = repository.facet_capability_evidence_all()
    parent_pos: dict[str, float] = defaultdict(float)
    parent_neg: dict[str, float] = defaultdict(float)
    for cell in cells:
        parent_pos[cell.facet_id] += cell.direct_positive_mass + cell.embedded_positive_mass
        parent_neg[cell.facet_id] += cell.direct_negative_mass + cell.embedded_negative_mass

    rows: list[dict[str, object]] = []
    for cell in cells:
        facet = cell.facet_id
        capability = cell.capability
        p_alpha = 1.0 + parent_pos[facet]
        p_beta = 1.0 + parent_neg[facet]
        parent_mean = p_alpha / (p_alpha + p_beta)

        cap_pos = cell.direct_positive_mass + cell.embedded_positive_mass
        cap_neg = cell.direct_negative_mass + cell.embedded_negative_mass
        independent_mass = cap_pos + cap_neg
        independent_groups = len(cell.independent_surface_groups)
        cap_alpha = 1.0 + cap_pos
        cap_beta = 1.0 + cap_neg
        cap_mean = cap_alpha / (cap_alpha + cap_beta)
        divergence = abs(cap_mean - parent_mean)

        has_episode = facet in episode_facets
        persistent = (
            independent_groups >= min_groups
            and independent_mass >= min_mass
            and divergence >= divergence_threshold
        )
        episode_trigger = (
            has_episode and independent_mass > 0.0 and divergence >= episode_threshold
        )
        if not (persistent or episode_trigger):
            continue

        # Shared parent as a shrinkage prior over the capability slice.
        prior_alpha = shrinkage * parent_mean
        prior_beta = shrinkage * (1.0 - parent_mean)
        residual_alpha = prior_alpha + cap_pos
        residual_beta = prior_beta + cap_neg
        residual_mean = residual_alpha / (residual_alpha + residual_beta)
        reason = "persistent_residual_disagreement" if persistent else "closed_diagnostic_episode"
        rows.append(
            {
                "facet_id": facet,
                "capability": capability,
                "active": True,
                "activation_reason": reason,
                "residual_alpha": residual_alpha,
                "residual_beta": residual_beta,
                "residual_mean": residual_mean,
                "parent_alpha": p_alpha,
                "parent_beta": p_beta,
                "parent_mean": parent_mean,
                "divergence": divergence,
                "independent_groups": independent_groups,
                "independent_mass": independent_mass,
            }
        )

    repository.replace_capability_residual_state(
        rows=rows, algorithm_version=KM_ALGORITHM_VERSION, clock=clock
    )


def _sync_unresolved_cause_factors(
    repository: Repository, unresolved: list[dict[str, object]], *, clock: Clock | None
) -> None:
    """Idempotently reconcile open unresolved-cause factors with the projection.

    Keyed by observation_id (stable per grading revision), so a re-run neither
    duplicates nor loses an open cause set. Factors whose failure no longer
    appears are retired; new ambiguous failures are inserted (§5.3)."""

    existing = repository.open_unresolved_cause_observation_ids()
    wanted = {str(u["observation_id"]): u for u in unresolved}
    for observation_id, record in wanted.items():
        if observation_id not in existing:
            repository.insert_unresolved_cause_factor(
                attempt_id=str(record["attempt_id"]),
                candidate_causes=record["candidate_causes"],
                algorithm_version=KM_ALGORITHM_VERSION,
                observation_id=observation_id,
                clock=clock,
            )
    for observation_id in existing - set(wanted):
        repository.retire_unresolved_cause_factor(observation_id, clock=clock)
