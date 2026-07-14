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

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.assessment_contracts import KM_ALGORITHM_VERSION
from learnloop.services.capability_mapping import (
    CriterionOutcome,
    allocate_success_mass,
    cap_certification_by_group,
    certification_credit,
    compile_criterion_targets,
    criterion_pseudo_mass,
    localize_criterion_outcomes,
)
from learnloop.services.evidence import attempt_evidence_mass
from learnloop.vault.models import LoadedVault, PracticeItem

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


def _repeat_discount(vault: LoadedVault) -> float:
    extra = getattr(vault.config.evidence.correlation, "__pydantic_extra__", None) or {}
    value = extra.get("repeat_surface_discount")
    if value is None:
        return DEFAULT_REPEAT_SURFACE_DISCOUNT
    return float(value)


def project_canonical_facet_state(
    vault: LoadedVault, repository: Repository, *, clock: Clock | None = None
) -> None:
    """Recompute and persist the canonical belief cache (mvp-0.7 only)."""

    if vault.config.algorithms.algorithm_version != KM_ALGORITHM_VERSION:
        return

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

    for attempt in repository.canonical_observation_ledger():
        item = vault.practice_items.get(attempt["practice_item_id"])
        if item is None:
            continue
        rubric = vault.rubric_for_item(item)
        if rubric is None or not rubric.criteria:
            continue
        evidence_by_criterion = {
            row["criterion_id"]: row for row in attempt["evidence"]
        }
        rubric_total = sum(max(c.points, 0.0) for c in rubric.criteria) or 1.0
        emass = attempt_evidence_mass(attempt["attempt_type"], vault.config.evidence)
        group_key = surface_group_id(item)
        assisted = (
            attempt["attempt_type"] in ASSISTED_ATTEMPT_TYPES
            or int(attempt["hints_used"]) > 0
        )
        assistance = "hinted" if assisted else "unassisted"
        created_at = attempt["created_at"]

        outcomes: list[CriterionOutcome] = []
        for criterion in rubric.criteria:
            row = evidence_by_criterion.get(criterion.id)
            fraction = 0.0
            if row is not None and criterion.points > 0:
                fraction = max(0.0, min(1.0, float(row["points_awarded"]) / criterion.points))
            outcomes.append(
                CriterionOutcome(
                    criterion_id=criterion.id,
                    passed=fraction >= FAILURE_THRESHOLD,
                    depends_on=tuple(criterion.depends_on),
                )
            )
        localized = {c.criterion_id: c for c in localize_criterion_outcomes(outcomes)}
        criteria_by_id = {c.id: c for c in rubric.criteria}

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
            if row is not None and criterion.points > 0:
                fraction = max(0.0, min(1.0, float(row["points_awarded"]) / criterion.points))
            targets = compile_criterion_targets(item, criterion, resolved_rubric=rubric)
            if not targets:
                continue
            pmass = criterion_pseudo_mass(criterion.points, rubric_total, emass)
            corr_group = criterion.correlation_group or group_key

            # Ambiguous localized failure over several candidate targets with no
            # resolving attribution -> unresolved joint cause set, never marginal
            # damage to every listed facet (§5.3).
            attribution = row.get("attribution_json") if row is not None else None
            if local.first_error and len(targets) > 1 and not attribution:
                unresolved.append(
                    {
                        "attempt_id": attempt["attempt_id"],
                        "observation_id": f"{attempt['attempt_id']}:{criterion.id}:0",
                        "candidate_causes": [
                            {"facet": resolve(t.facet), "capability": t.capability}
                            for t in targets
                        ],
                    }
                )
                continue

            allocations = allocate_success_mass(targets, pmass)
            for alloc in allocations:
                facet = resolve(alloc.facet)
                capability = alloc.capability
                key = (facet, capability)
                is_new_group = group_key not in cap[key].groups
                discount = 1.0 if is_new_group else repeat_discount
                w = alloc.pseudo_mass * discount
                positive = w * fraction
                negative = w * (1.0 - fraction)
                # relationship: a declared criterion target is direct evidence.
                cap[key].direct_positive_mass += positive
                cap[key].direct_negative_mass += negative
                if is_new_group:
                    cap[key].groups.add(group_key)
                credit = certification_credit(
                    positive, relationship="direct", assistance=assistance
                )
                staged_credit[corr_group][key] += credit

                for scope in (None, item.id):
                    acc = recall[(facet, capability, scope)]
                    if acc.created_at is None:
                        acc.created_at = created_at
                    acc.alpha += positive
                    acc.beta += negative
                    acc.independent_mass += w if is_new_group else 0.0
                    acc.raw_mass += alloc.pseudo_mass
                    acc.last_observed_at = created_at
                    if fraction < FAILURE_THRESHOLD:
                        acc.last_error_at = created_at
                        acc.consecutive_failures += 1
                    else:
                        acc.consecutive_failures = 0

        # Apply per-group budget + attempt-wide ceiling, then bank the credit.
        group_totals = {
            group: sum(cells.values()) for group, cells in staged_credit.items()
        }
        capped = cap_certification_by_group(
            group_totals,
            attempt_type=attempt["attempt_type"],
            evidence_mass=emass,
            overrides=overrides,
            max_groups_per_attempt=max_groups,
        )
        for group, cells in staged_credit.items():
            raw_total = group_totals[group]
            if raw_total <= 0:
                continue
            scale = capped[group] / raw_total
            for key, credit in cells.items():
                cap[key].certification_credit += credit * scale

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
        algorithm_version=KM_ALGORITHM_VERSION,
        clock=clock,
    )
    _sync_unresolved_cause_factors(repository, unresolved, clock=clock)


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
