"""P0.5 sensitivity certificates + promotion evidence (spec §6, U-022 v2, design §3).

The owner-approved v2 of U-022 splits the single "sensitivity certificate" concept
into two artifacts, both sim-sweep-derived and both stored as rows in
``parameter_sensitivity_certificates`` (the referencing registry column names their
role):

  * **Coverage certificate** (descriptive, not pass/fail) -- keyed to (parameter
    path, effective value hash, swept plausible range). It documents *where in the
    range* decisions flip. Finding flip points does NOT invalidate it -- that is
    precisely its purpose. Required for EVERY ``active`` decision parameter
    regardless of calibration status. Linking one satisfies the audit's coverage
    obligation and NEVER changes status. A value change outside the covered hash
    invalidates it (needs a re-sweep). Produced by :func:`certify` /
    :func:`certificate_from_sweep_report`, linked by :func:`link_coverage_certificate`.

  * **Promotion evidence** (normative) -- the gate for status promotion beyond
    ``heuristic``. Sim evidence (including the ``decision_stable`` refusal logic,
    formerly F4, which lives HERE now) gates ``heuristic -> simulation_validated``;
    the activated real-outcome evidence manifest gates ``-> live_calibrated`` (§6).
    Produced by :func:`promotion_evidence_from_sweep_report` (it MAY wrap a coverage
    certificate), consumed by :func:`promote`.

The producers are split so tests stay fast and deterministic: the pure
``*_from_sweep_report`` helpers derive from any ``SweepReport``; :func:`certify`
runs the sweep to obtain one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.activities import _canonical_hash


@dataclass
class Certificate:
    path: str
    covered_value_hash: str
    plausible_range: dict[str, Any]
    flip_points: list[Any]
    decision_stable: bool
    scenario: dict[str, Any]
    sim_report_hash: str
    id: str | None = None
    produced_at: str | None = None

    def as_entry(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "covered_value_hash": self.covered_value_hash,
            "plausible_range": self.plausible_range,
            "flip_points": self.flip_points,
            "decision_stable": self.decision_stable,
            "scenario": self.scenario,
            "sim_report_hash": self.sim_report_hash,
            "produced_at": self.produced_at,
        }


def certificate_from_sweep_report(
    *,
    path: str,
    covered_value: Any,
    plausible_range: Mapping[str, Any],
    scenario: Mapping[str, Any],
    sweep_report: Any,
) -> Certificate:
    """Derive a certificate from a ``SweepReport``. A grid point is a *flip point*
    when the sweep verdict is ``decision-relevant`` (the queue/counts/beliefs/goals
    moved vs the shipped-value baseline). ``decision_stable`` iff no flip in range."""

    flip_points: list[Any] = []
    for result in getattr(sweep_report, "results", []) or []:
        if result.get("param_path") != path:
            continue
        if result.get("verdict") == "decision-relevant":
            flip_points.append(result.get("value"))
    return Certificate(
        path=path,
        covered_value_hash=_canonical_hash(
            list(covered_value) if isinstance(covered_value, (list, tuple)) else covered_value
        ),
        plausible_range=dict(plausible_range),
        flip_points=flip_points,
        decision_stable=not flip_points,
        scenario=dict(scenario),
        sim_report_hash=_canonical_hash(sweep_report.as_dict()),
    )


def _value_grid(low: float, high: float, points: int, covered: Any) -> list[Any]:
    if points < 2:
        points = 2
    step = (high - low) / (points - 1)
    grid = [round(low + step * i, 6) for i in range(points)]
    if isinstance(covered, (int, float)) and not isinstance(covered, bool):
        if covered not in grid:
            grid.append(covered)
    return sorted(set(grid))


def certify(
    *,
    path: str,
    covered_value: Any,
    low: float,
    high: float,
    vault_root: Path,
    profile: Any,
    work_dir: Path,
    scenario: Mapping[str, Any] | None = None,
    grid_points: int = 5,
    days: int = 12,
    items_per_day: int = 4,
    seed: int = 42,
) -> Certificate:
    """Run a fine value-grid sweep across ``[low, high]`` on the fixed scenario and
    build a certificate. ``path`` must be a config path the sweep can override."""

    from learnloop.sim.sweep import SweepEntry, run_sweep

    grid = _value_grid(low, high, grid_points, covered_value)
    report = run_sweep(
        Path(vault_root),
        profile,
        sweep_spec=[SweepEntry(param_path=path, values=grid)],
        days=days,
        items_per_day=items_per_day,
        seed=seed,
        work_dir=Path(work_dir),
    )
    scenario_meta = dict(scenario or {})
    scenario_meta.setdefault("profile", getattr(profile, "name", None))
    scenario_meta.setdefault("seed", seed)
    scenario_meta.setdefault("days", days)
    scenario_meta.setdefault("grid", grid)
    return certificate_from_sweep_report(
        path=path,
        covered_value=covered_value,
        plausible_range={"low": low, "high": high},
        scenario=scenario_meta,
        sweep_report=report,
    )


def store_certificate(
    repository: Repository, certificate: Certificate, *, clock: Clock | None = None
) -> str:
    cert_id = repository.insert_sensitivity_certificate(
        certificate=certificate.as_entry(), clock=clock
    )
    certificate.id = cert_id
    return cert_id


# ---------------------------------------------------------------------------
# Coverage linking (audit rule (a) -- descriptive, never changes status).
# ---------------------------------------------------------------------------

@dataclass
class CoverageLinkOutcome:
    """Result of :func:`link_coverage_certificate`. ``linked`` is the success flag;
    ``reason`` names why a non-link happened (inspectable + testable). Truthy iff
    linked. Linking NEVER changes status -- coverage is descriptive, not a gate."""

    linked: bool
    reason: str | None = None

    def __bool__(self) -> bool:
        return self.linked


def link_coverage_certificate(
    repository: Repository,
    certificate: Certificate,
    *,
    clock: Clock | None = None,
) -> CoverageLinkOutcome:
    """Link a stored COVERAGE certificate to its registry entry, satisfying the
    audit's coverage obligation for an ``active`` decision parameter (rule (a)).

    This never changes ``status``: a coverage certificate is descriptive. Even one
    whose sweep found the decision *flips* somewhere in the plausible range
    (``decision_stable=False`` / non-empty ``flip_points``) is a valid coverage
    certificate -- documenting flip points is its purpose (U-022 v2). The only
    validity requirement is that it covers the entry's *current* effective value
    hash; a stale certificate (value moved) does not link."""

    entry = repository.parameter_registry_entry(certificate.path)
    if entry is None:
        return CoverageLinkOutcome(False, "no_registry_entry")
    if certificate.id is None:
        store_certificate(repository, certificate, clock=clock)
    if certificate.covered_value_hash != entry["effective_value_hash"]:
        return CoverageLinkOutcome(False, "certificate_does_not_cover_current_value")
    entry["sensitivity_certificate_id"] = certificate.id
    entry["effective_value"] = _loads(entry["effective_value_json"])
    repository.upsert_parameter_registry_entry(entry=entry, clock=clock)
    return CoverageLinkOutcome(True, None)


# ---------------------------------------------------------------------------
# Promotion evidence (audit rule (b) -- normative gate beyond heuristic).
# ---------------------------------------------------------------------------

@dataclass
class PromotionEvidence:
    """Sim-derived evidence that gates ``heuristic -> simulation_validated``. Shares
    the ``parameter_sensitivity_certificates`` storage shape with coverage
    certificates (:meth:`as_entry`); the registry ``promotion_evidence_id`` column
    is what marks a row as *this* role. ``decision_stable`` is the normative content:
    only a stable-in-range promotion evidence promotes (the refusal that used to live
    in ``link_and_promote``). ``wraps_certificate_id`` records an optional coverage
    certificate this evidence was derived from."""

    path: str
    covered_value_hash: str
    plausible_range: dict[str, Any]
    flip_points: list[Any]
    decision_stable: bool
    scenario: dict[str, Any]
    sim_report_hash: str
    source: str = "sim"
    wraps_certificate_id: str | None = None
    id: str | None = None
    produced_at: str | None = None

    def as_entry(self) -> dict[str, Any]:
        scenario = dict(self.scenario)
        scenario.setdefault("evidence_role", "promotion_evidence")
        scenario.setdefault("evidence_source", self.source)
        if self.wraps_certificate_id is not None:
            scenario.setdefault("wraps_certificate_id", self.wraps_certificate_id)
        return {
            "id": self.id,
            "path": self.path,
            "covered_value_hash": self.covered_value_hash,
            "plausible_range": self.plausible_range,
            "flip_points": self.flip_points,
            "decision_stable": self.decision_stable,
            "scenario": scenario,
            "sim_report_hash": self.sim_report_hash,
            "produced_at": self.produced_at,
        }


def promotion_evidence_from_sweep_report(
    *,
    path: str,
    covered_value: Any,
    plausible_range: Mapping[str, Any],
    scenario: Mapping[str, Any],
    sweep_report: Any,
) -> PromotionEvidence:
    """Derive sim promotion evidence from a ``SweepReport`` (same flip-point rule as
    a coverage certificate; here the ``decision_stable`` verdict is the normative gate
    :func:`promote` enforces)."""

    cert = certificate_from_sweep_report(
        path=path,
        covered_value=covered_value,
        plausible_range=plausible_range,
        scenario=scenario,
        sweep_report=sweep_report,
    )
    return promotion_evidence_from_certificate(cert)


def promotion_evidence_from_certificate(
    certificate: Certificate, *, source: str = "sim"
) -> PromotionEvidence:
    """Wrap a coverage certificate as promotion evidence (U-022 v2: promotion
    evidence MAY wrap a coverage certificate). The stability verdict carries over
    unchanged; :func:`promote` applies the normative refusal."""

    return PromotionEvidence(
        path=certificate.path,
        covered_value_hash=certificate.covered_value_hash,
        plausible_range=dict(certificate.plausible_range),
        flip_points=list(certificate.flip_points),
        decision_stable=certificate.decision_stable,
        scenario=dict(certificate.scenario),
        sim_report_hash=certificate.sim_report_hash,
        source=source,
        wraps_certificate_id=certificate.id,
    )


def store_promotion_evidence(
    repository: Repository, evidence: PromotionEvidence, *, clock: Clock | None = None
) -> str:
    evidence_id = repository.insert_sensitivity_certificate(
        certificate=evidence.as_entry(), clock=clock
    )
    evidence.id = evidence_id
    return evidence_id


@dataclass
class PromotionOutcome:
    """Result of :func:`promote`. ``promoted`` is the success flag; ``refusal_reason``
    names why a non-promotion happened (inspectable + testable). Truthy iff promoted."""

    promoted: bool
    refusal_reason: str | None = None

    def __bool__(self) -> bool:
        return self.promoted


def promote(
    repository: Repository,
    evidence: PromotionEvidence,
    *,
    clock: Clock | None = None,
) -> PromotionOutcome:
    """Consume PROMOTION EVIDENCE and, when it covers the entry's current effective
    value AND proves the decision stable across the plausible range, promote status
    to ``simulation_validated`` (never further -- §6; ``live_calibrated`` still
    requires an activated real-outcome evidence manifest).

    Evidence whose sweep found the decision *flips* somewhere in the plausible range
    (``decision_stable=False`` / non-empty ``flip_points``) does NOT discharge the
    calibration obligation for the covered value -- promoting on it would claim
    validated authority a knife-edge value cannot support (§3.2/§6). It is refused
    with a reason, not promoted. This is the normative gate; a coverage certificate
    with the same flip points is still perfectly valid coverage (rule (a))."""

    from learnloop.services import parameter_registry as pr

    entry = repository.parameter_registry_entry(evidence.path)
    if entry is None:
        return PromotionOutcome(False, "no_registry_entry")
    if evidence.covered_value_hash != entry["effective_value_hash"]:
        return PromotionOutcome(False, "certificate_does_not_cover_current_value")
    if not evidence.decision_stable or evidence.flip_points:
        return PromotionOutcome(False, "decision_unstable_in_plausible_range")
    if evidence.id is None:
        store_promotion_evidence(repository, evidence, clock=clock)
    entry["effective_value"] = _loads(entry["effective_value_json"])
    entry["status"] = "simulation_validated"
    entry["last_review_at"] = evidence.produced_at
    repository.upsert_parameter_registry_entry(entry=entry, clock=clock)
    pr.set_promotion_evidence_id(repository, evidence.path, evidence.id, clock=clock)
    return PromotionOutcome(True, None)


def _loads(value: str) -> Any:
    import json

    return json.loads(value)


@dataclass
class DeletionCandidateReport:
    deletion_candidates: list[str] = field(default_factory=list)
    dormant_constraints: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "deletion_candidates": self.deletion_candidates,
            "dormant_constraints": self.dormant_constraints,
        }


def classify_inert_parameters(paths_stable: Mapping[str, bool]) -> DeletionCandidateReport:
    """Class-asymmetric disposition of sweep-proven-inert parameters (§6/design §3).

    ``paths_stable`` maps a registered path -> whether a certificate proved it
    ``decision_stable`` across its whole plausible range. An inert *shaping weight*
    is a deletion candidate (needs a redundancy proof before actual deletion); an
    inert *constraint* defaults to dormant-with-monitoring (it may bind under a
    distribution shift)."""

    from learnloop.services.parameter_registry import REGISTRY

    report = DeletionCandidateReport()
    for path, stable in paths_stable.items():
        if not stable:
            continue
        spec = REGISTRY.get(path)
        if spec is None:
            continue
        if spec.param_class == "shaping_weight":
            report.deletion_candidates.append(path)
        elif spec.param_class == "constraint":
            report.dormant_constraints.append(path)
    return report
