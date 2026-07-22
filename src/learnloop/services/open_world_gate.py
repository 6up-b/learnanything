"""P4 open-world expansion -- the §14.1 DEPENDENCY GATE (executable check only).

Open-world HypothesisCard expansion is intentionally LAST (§10, §15 steps 8-10): more
hypotheses amplify every measurement, exposure, and controller error below them. The
spec therefore forbids enabling any expansion worker or successor-set UI until SIX
dependency conditions all pass (§14.1). The schema may land earlier; behaviour does not.

This module implements those six conditions as executable, queryable predicates over the
landed state and reports each truthfully. Open-world itself is NOT implemented in this
package -- there is no HypothesisCard schema, no triggers, no retrieve/generate/validate,
no successor episodes, no Journey-8 UI. The gate exists so the deferral is *inspectable*
and so enabling expansion later is a checked event, not a silent flip.

Current evaluation: the gate is **NOT MET**. Conditions 1-5 (the P0-P4 substrates the
suite exercises) evaluate MET by their landed capability; condition 6's kernel-shadow
audit is NOT MET because the descoped soft-kinship feature is deliberately kept behind
its admission gate (firewall: computed + logged, consulted by nothing) and has not been
admitted -- so the last dependency has not cleared. The gate additionally reports that
the open-world SUBSTRATE is absent, an independent reason expansion cannot be enabled.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any, Callable

from learnloop.db.repositories import Repository


@dataclass(frozen=True)
class Condition:
    key: str
    spec_ref: str
    description: str
    met: bool
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "spec_ref": self.spec_ref,
            "description": self.description,
            "met": self.met,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class GateReport:
    conditions: tuple[Condition, ...]
    open_world_schema_present: bool
    met: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "gate": "open_world_dependency_gate",
            "spec_ref": "spec_p4_controller_and_scale.md §14.1",
            "met": self.met,
            "open_world_schema_present": self.open_world_schema_present,
            "enablement": (
                "expansion workers + successor-set UI may be enabled"
                if self.met and self.open_world_schema_present
                else "expansion workers + successor-set UI REMAIN DISABLED"
            ),
            "conditions": [c.as_dict() for c in self.conditions],
            "blocking": [c.key for c in self.conditions if not c.met],
        }


def _has_attrs(module_name: str, attrs: tuple[str, ...]) -> tuple[bool, str]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - importability is the check
        return False, f"import failed: {type(exc).__name__}"
    missing = [a for a in attrs if not hasattr(module, a)]
    if missing:
        return False, f"missing {missing} in {module_name}"
    return True, f"{module_name} present with {list(attrs)}"


def _table_exists(repository: Repository, name: str) -> bool:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
    return row is not None


# ---------------------------------------------------------------------------
# The six §14.1 conditions as predicates.
# ---------------------------------------------------------------------------


def _c1_p0(repository: Repository) -> Condition:
    ok_r, detail_r = _has_attrs(
        "learnloop.services.robust_composition",
        ("build_ensemble", "robust_quantile", "evaluate_selection"),
    )
    ok_o, detail_o = _has_attrs(
        "learnloop.services.effective_observation",
        ("build_effective_observation", "shared_certainty_lcb"),
    )
    met = ok_r and ok_o
    return Condition(
        key="p0_calibrated_reliability_robust_bounds",
        spec_ref="§14.1(1)",
        description="P0 calibrated-event/reliability and robust-bound APIs pass",
        met=met,
        detail="; ".join([detail_r, detail_o]),
    )


def _c2_p1(repository: Repository) -> Condition:
    ok_f, detail_f = _has_attrs(
        "learnloop.services.familiarity",
        ("familiarity_projection_v1", "HARD_NAMESPACES", "record_memberships"),
    )
    ok_a, detail_a = _has_attrs(
        "learnloop.services.administration_adapters", ("__name__",)
    )
    ledger = _table_exists(repository, "activity_exposure_events")
    met = ok_f and ok_a and ledger
    return Condition(
        key="p1_exposure_hard_groups_lineage_purpose",
        spec_ref="§14.1(2)",
        description="P1 global exposure/hard groups/card lineage/purpose adapters pass",
        met=met,
        detail=f"{detail_f}; adapters={ok_a}; activity_exposure_events={ledger}",
    )


def _c3_p2(repository: Repository) -> Condition:
    ok, detail = _has_attrs("learnloop.services.golden_path_assessment", ("__name__",))
    ok2, detail2 = _has_attrs("learnloop.services.pattern_ladder", ("__name__",))
    met = ok and ok2
    return Condition(
        key="p2_end_to_end_held_out_journey",
        spec_ref="§14.1(3)",
        description="P2 end-to-end held-out journey passes",
        met=met,
        detail=f"golden_path_assessment={ok}; pattern_ladder={ok2}",
    )


def _c4_p3(repository: Repository) -> Condition:
    ok, detail = _has_attrs("learnloop.services.annotations", ("__name__",))
    ok2, detail2 = _has_attrs("learnloop.services.salience_firewall", ("__name__",))
    met = ok and ok2
    return Condition(
        key="p3_local_hypothesis_seed_provenance",
        spec_ref="§14.1(4)",
        description="P3 local hypothesis-seed/provenance path passes",
        met=met,
        detail=f"annotations={ok}; salience_firewall={ok2}",
    )


def _c5_controller(repository: Repository) -> Condition:
    ok_s, detail_s = _has_attrs("learnloop.services.constraint_engine", ("evaluate", "manifest"))
    ok_p, detail_p = _has_attrs("learnloop.services.staged_policy", ("decide",))
    ok_t, detail_t = _has_attrs(
        "learnloop.services.predictive_targets", ("__name__",)
    )
    shadow = _table_exists(repository, "controller_shadow_predictions")
    met = ok_s and ok_p and ok_t and shadow
    return Condition(
        key="controller_constraints_target_eig_shadow_logging",
        spec_ref="§14.1(5)",
        description="controller constraint/staged policy, target-distribution EIG, and shadow logging pass",
        met=met,
        detail=f"constraint_engine={ok_s}; staged_policy={ok_p}; "
        f"predictive_targets={ok_t}; controller_shadow_predictions={shadow}",
    )


def _c6_dispersion_kernel(repository: Repository) -> Condition:
    ok_d, _ = _has_attrs("learnloop.services.dispersion", ("__name__",))
    ok_i, _ = _has_attrs("learnloop.services.interleaving", ("__name__",))
    # The kernel-shadow audit "passes" only once the descoped soft-kinship feature has
    # cleared its planted-learner admission gate (status simulation_validated). It is
    # deliberately kept un-admitted (firewall): consulted by nothing until an owner-
    # reviewed admission. So this sub-condition is honestly NOT MET today.
    from learnloop.services import kinship_feature

    kernel_admitted = kinship_feature.is_admitted(repository)
    met = ok_d and ok_i and kernel_admitted
    return Condition(
        key="dispersion_interleaving_kernel_shadow_audit",
        spec_ref="§14.1(6)",
        description="dispersion/interleaving and kernel shadow audits pass",
        met=met,
        detail=f"dispersion={ok_d}; interleaving={ok_i}; "
        f"kinship_kernel_admitted={kernel_admitted} "
        f"({'admitted' if kernel_admitted else 'behind admission gate (firewall)'})",
    )


_CONDITIONS: tuple[Callable[[Repository], Condition], ...] = (
    _c1_p0, _c2_p1, _c3_p2, _c4_p3, _c5_controller, _c6_dispersion_kernel,
)


def evaluate_gate(vault: Any, repository: Repository) -> GateReport:
    """Evaluate the six §14.1 conditions and return a truthful per-condition report.
    ``vault`` is accepted for symmetry with other services; the predicates read landed
    code + the vault's schema/kernel state through ``repository``."""

    conditions = tuple(check(repository) for check in _CONDITIONS)
    schema_present = _table_exists(repository, "hypothesis_cards")
    met = all(c.met for c in conditions)
    return GateReport(
        conditions=conditions,
        open_world_schema_present=schema_present,
        met=met,
    )
