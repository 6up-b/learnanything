"""Residual-dependence diagnostics (knowledge-model §8.4).

Report-only, deterministic structure hints derived from the observation ledger
and the canonical capability ledger. Residual dependence is *diagnostic*, never
permission for opaque propagation: this module proposes reviewed graph/recipe
mutations, it NEVER rewrites authored structure (§8.4). Per §8.4 it flags:

* positive residual dependence between facets sharing tasks -> a missing facet
  or testlet factor;
* systematic combined-task failure with strong components -> a missing
  integration factor;
* context-specific residuals (capability-sliced or surface-sliced divergence) ->
  a transfer / capability-divergence hint;
* indistinguishable facet response signatures -> an identifiability referral
  (hand off to the §11.3 doctor).

The report feeds review; it mutates nothing. Deterministic: a pure fold over
persisted evidence, so re-running yields the same suggestions.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.services.assessment_contracts import (
    CANONICAL_STATE_VERSIONS,
    KM_ALGORITHM_VERSION,
)
from learnloop.services.canonical_projection import FAILURE_THRESHOLD, surface_group_id
from learnloop.services.capability_mapping import compile_criterion_targets
from learnloop.vault.models import LoadedVault

# Minimum co-tasked attempts before a residual-dependence claim is made.
MIN_JOINT_ATTEMPTS = 4
# Residual co-failure above independence that counts as positive dependence.
RESIDUAL_DEPENDENCE_THRESHOLD = 0.15
# Combined-task failure that is "systematic" while components look strong.
COMBINED_FAILURE_THRESHOLD = 0.5
COMPONENT_STRONG_THRESHOLD = 0.35  # solo failure rate below this = strong component
# Capability / surface belief spread that reads as a context-specific residual.
CONTEXT_DIVERGENCE_THRESHOLD = 0.25


def _facet_outcomes_per_attempt(
    vault: LoadedVault, repository: Repository, scoped_los: set[str] | None
) -> list[dict[str, Any]]:
    """Per-attempt facet pass/fail + surface group (deterministic, ledger order)."""

    rows: list[dict[str, Any]] = []
    for attempt in repository.canonical_observation_ledger():
        item = vault.practice_items.get(attempt["practice_item_id"])
        if item is None:
            continue
        if scoped_los is not None and item.learning_object_id not in scoped_los:
            continue
        rubric = vault.rubric_for_item(item)
        if rubric is None or not rubric.criteria:
            continue
        evidence_by_criterion = {row["criterion_id"]: row for row in attempt["evidence"]}
        facet_pass: dict[str, bool] = {}
        for criterion in rubric.criteria:
            row = evidence_by_criterion.get(criterion.id)
            fraction = 0.0
            if row is not None and criterion.points > 0:
                fraction = max(0.0, min(1.0, float(row["points_awarded"]) / criterion.points))
            passed = fraction >= FAILURE_THRESHOLD
            for target in compile_criterion_targets(item, criterion, resolved_rubric=rubric):
                facet = vault.canonical_facet_id(target.facet)
                # A facet passes the attempt only if every observing criterion passed.
                facet_pass[facet] = facet_pass.get(facet, True) and passed
        if facet_pass:
            rows.append(
                {
                    "attempt_id": attempt["attempt_id"],
                    "learning_object_id": item.learning_object_id,
                    "surface_group": surface_group_id(item),
                    "facet_pass": facet_pass,
                    "joint": len(facet_pass) > 1,
                }
            )
    return rows


def _residual_dependence_suggestions(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Positive residual co-failure between co-tasked facets (missing factor)."""

    joint_fail: dict[tuple[str, str], int] = defaultdict(int)
    a_fail: dict[tuple[str, str], int] = defaultdict(int)
    b_fail: dict[tuple[str, str], int] = defaultdict(int)
    n_joint: dict[tuple[str, str], int] = defaultdict(int)
    for row in rows:
        facets = sorted(row["facet_pass"])
        for i in range(len(facets)):
            for j in range(i + 1, len(facets)):
                a, b = facets[i], facets[j]
                pair = (a, b)
                n_joint[pair] += 1
                fa = not row["facet_pass"][a]
                fb = not row["facet_pass"][b]
                a_fail[pair] += int(fa)
                b_fail[pair] += int(fb)
                joint_fail[pair] += int(fa and fb)

    suggestions: list[dict[str, Any]] = []
    for pair in sorted(n_joint):
        n = n_joint[pair]
        if n < MIN_JOINT_ATTEMPTS:
            continue
        fa = a_fail[pair] / n
        fb = b_fail[pair] / n
        co = joint_fail[pair] / n
        residual = co - fa * fb
        if residual >= RESIDUAL_DEPENDENCE_THRESHOLD:
            suggestions.append(
                {
                    "kind": "missing_facet_or_testlet_factor",
                    "facet_ids": list(pair),
                    "capability": "",
                    "message": (
                        f"facets {pair[0]} and {pair[1]} share tasks and fail together more than "
                        f"independence predicts (residual {round(residual, 3)}); review for a missing "
                        "shared facet or testlet factor"
                    ),
                    "detail": "positive_residual_dependence",
                    "evidence": {"joint_attempts": n, "residual": round(residual, 4)},
                }
            )
    return suggestions, len(n_joint)


def _integration_suggestions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Systematic combined-task failure with strong components (missing integration)."""

    # Per-facet solo failure rate (attempts where the facet is the only target).
    solo_fail: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        if row["joint"]:
            continue
        for facet, passed in row["facet_pass"].items():
            solo_fail[facet].append(0 if passed else 1)

    # Per-LO combined-task failure over multi-facet items.
    combined: dict[str, list[tuple[frozenset[str], bool]]] = defaultdict(list)
    for row in rows:
        if not row["joint"]:
            continue
        combined[row["learning_object_id"]].append(
            (frozenset(row["facet_pass"]), all(row["facet_pass"].values()))
        )

    suggestions: list[dict[str, Any]] = []
    for lo_id in sorted(combined):
        outcomes = combined[lo_id]
        if len(outcomes) < MIN_JOINT_ATTEMPTS:
            continue
        combined_fail = sum(0 if ok else 1 for _, ok in outcomes) / len(outcomes)
        facets = sorted({f for fs, _ in outcomes for f in fs})
        component_rates = [
            sum(solo_fail[f]) / len(solo_fail[f]) for f in facets if solo_fail.get(f)
        ]
        if not component_rates:
            continue
        if combined_fail >= COMBINED_FAILURE_THRESHOLD and max(component_rates) <= COMPONENT_STRONG_THRESHOLD:
            suggestions.append(
                {
                    "kind": "missing_integration_factor",
                    "facet_ids": facets,
                    "capability": "coordination",
                    "message": (
                        f"{lo_id}: components are individually strong but their combined tasks fail "
                        f"systematically ({round(combined_fail, 3)}); review for a missing integration "
                        "(coordination) factor"
                    ),
                    "detail": "systematic_combined_task_failure",
                    "evidence": {"combined_failure_rate": round(combined_fail, 4), "joint_attempts": len(outcomes)},
                }
            )
    return suggestions


def _context_divergence_suggestions(
    vault: LoadedVault, repository: Repository, scoped_facets: set[str] | None
) -> list[dict[str, Any]]:
    """Capability-sliced belief spread within a facet (transfer / capability hint)."""

    by_facet: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for cell in repository.facet_capability_evidence_all():
        if scoped_facets is not None and cell.facet_id not in scoped_facets:
            continue
        pos = cell.direct_positive_mass + cell.embedded_positive_mass
        neg = cell.direct_negative_mass + cell.embedded_negative_mass
        mean = (1.0 + pos) / (2.0 + pos + neg)
        by_facet[cell.facet_id].append((cell.capability, mean))

    suggestions: list[dict[str, Any]] = []
    for facet in sorted(by_facet):
        slices = by_facet[facet]
        if len(slices) < 2:
            continue
        means = [m for _, m in slices]
        spread = max(means) - min(means)
        if spread >= CONTEXT_DIVERGENCE_THRESHOLD:
            caps = sorted(cap for cap, _ in slices)
            suggestions.append(
                {
                    "kind": "transfer_or_capability_divergence",
                    "facet_ids": [facet],
                    "capability": ",".join(caps),
                    "message": (
                        f"facet {facet} shows context-specific residuals across capabilities {caps} "
                        f"(spread {round(spread, 3)}); review for transfer / capability divergence "
                        "(a §4.2 residual may be warranted)"
                    ),
                    "detail": "context_specific_residual",
                    "evidence": {"capability_spread": round(spread, 4)},
                }
            )
    return suggestions


def _identifiability_referrals(
    vault: LoadedVault, repository: Repository, subject_id: str | None
) -> list[dict[str, Any]]:
    """Indistinguishable response signatures -> hand off to the §11.3 doctor."""

    from learnloop.services.identifiability import analyze_identifiability, build_registry_view

    scoped_los = {
        lo.id
        for lo in vault.learning_objects.values()
        if subject_id is None or (lo.subjects and subject_id in lo.subjects)
    }
    records: list[Any] = []
    reader = getattr(repository, "misconceptions_for_learning_object", None)
    if reader is not None:
        for lo_id in sorted(scoped_los or set(vault.learning_objects)):
            records.extend(reader(lo_id))
    view = build_registry_view(vault, subject_id, misconception_records=records)
    findings = analyze_identifiability(view)
    referrals: list[dict[str, Any]] = []
    for finding in findings:
        referrals.append(
            {
                "kind": "identifiability_referral",
                "facet_ids": list(finding.facet_ids),
                "capability": finding.capability,
                "message": (
                    f"indistinguishable response signatures ({finding.detail}); refer to "
                    "`learnloop graph-identifiability` (§11.3): " + finding.message
                ),
                "detail": finding.detail,
                "evidence": {"check": finding.check, "target_key": finding.target_key},
            }
        )
    return referrals


def residual_dependence_report(
    vault: LoadedVault, repository: Repository, *, subject_id: str | None = None
) -> dict[str, Any]:
    """The §8.4 residual-dependence diagnostics report (report-only, deterministic)."""

    if vault.config.algorithms.algorithm_version not in CANONICAL_STATE_VERSIONS:
        return {
            "version": 1,
            "subject": subject_id,
            "suggestions": [],
            "totals": {"suggestions": 0, "facet_pairs": 0},
            "note": "residual diagnostics run only under the canonical model (mvp-0.7/mvp-0.8)",
        }

    scoped_los: set[str] | None = None
    scoped_facets: set[str] | None = None
    if subject_id is not None:
        scoped_los = {
            lo.id for lo in vault.learning_objects.values() if lo.subjects and subject_id in lo.subjects
        }
        scoped_facets = set()
        from learnloop.vault.models import recipe_components as _recipe_components

        for lo in vault.learning_objects.values():
            if lo.id not in scoped_los:
                continue
            for blueprint in lo.blueprints:
                for recipe in blueprint.recipes:
                    for component in _recipe_components(recipe):
                        scoped_facets.add(component.facet)

    rows = _facet_outcomes_per_attempt(vault, repository, scoped_los)
    if scoped_facets is not None:
        # Blueprint-referenced facets miss legacy items and no-blueprint LOs, so
        # also scope by facets actually observed under this subject's attempts.
        for row in rows:
            scoped_facets.update(row["facet_pass"].keys())
    dependence, facet_pairs = _residual_dependence_suggestions(rows)
    suggestions: list[dict[str, Any]] = []
    suggestions.extend(dependence)
    suggestions.extend(_integration_suggestions(rows))
    suggestions.extend(_context_divergence_suggestions(vault, repository, scoped_facets))
    suggestions.extend(_identifiability_referrals(vault, repository, subject_id))

    return {
        "version": 1,
        "subject": subject_id,
        "suggestions": suggestions,
        "totals": {"suggestions": len(suggestions), "facet_pairs": facet_pairs},
    }
