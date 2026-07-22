"""P0.5 sensitivity certificates (spec §6 U-022 active, design §3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import parameter_registry as pr
from learnloop.services import sensitivity_certificates as sc
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault

CLOCK = FrozenClock(NOW)


@dataclass
class _FakeSweepReport:
    results: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {"version": 1, "results": self.results}


def _vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return load_vault(paths.root), Repository(paths.sqlite_path)


def test_certificate_is_stable_when_no_decision_flips():
    report = _FakeSweepReport(
        results=[
            {"param_path": "scheduler.goal_frontier_weight", "value": 0.1, "verdict": "inert in this scenario"},
            {"param_path": "scheduler.goal_frontier_weight", "value": 0.5, "verdict": "inert in this scenario"},
        ]
    )
    cert = sc.certificate_from_sweep_report(
        path="scheduler.goal_frontier_weight",
        covered_value=0.25,
        plausible_range={"low": 0.0, "high": 0.5},
        scenario={"profile": "novice", "seed": 42},
        sweep_report=report,
    )
    assert cert.decision_stable is True
    assert cert.flip_points == []
    assert len(cert.covered_value_hash) == 32


def test_certificate_records_flip_points():
    report = _FakeSweepReport(
        results=[
            {"param_path": "scheduler.short_session_minutes", "value": 5, "verdict": "decision-relevant"},
            {"param_path": "scheduler.short_session_minutes", "value": 20, "verdict": "inert in this scenario"},
        ]
    )
    cert = sc.certificate_from_sweep_report(
        path="scheduler.short_session_minutes",
        covered_value=20,
        plausible_range={"low": 5, "high": 40},
        scenario={},
        sweep_report=report,
    )
    assert cert.flip_points == [5]
    assert cert.decision_stable is False


def test_link_coverage_certificate_never_changes_status(tmp_path):
    # U-022 v2: linking a coverage certificate satisfies audit rule (a) and NEVER
    # changes status -- coverage is descriptive, promotion is a separate gate.
    vault, repo = _vault(tmp_path)
    pr.refresh(vault, repo, clock=CLOCK)
    path = "scheduler.short_session_minutes"
    entry = repo.parameter_registry_entry(path)
    assert entry["status"] == "heuristic"
    report = _FakeSweepReport(results=[{"param_path": path, "value": 20, "verdict": "inert in this scenario"}])
    cert = sc.certificate_from_sweep_report(
        path=path,
        covered_value=pr._resolve_config_value(path, vault.config),
        plausible_range={"low": 10, "high": 40},
        scenario={},
        sweep_report=report,
    )
    assert cert.covered_value_hash == entry["effective_value_hash"]
    sc.store_certificate(repo, cert, clock=CLOCK)
    linked = sc.link_coverage_certificate(repo, cert, clock=CLOCK)
    assert linked.linked is True
    assert linked.reason is None
    after = repo.parameter_registry_entry(path)
    assert after["status"] == "heuristic"  # coverage does not promote
    assert after["sensitivity_certificate_id"] == cert.id
    # Rule (a) satisfied: the active parameter is no longer pending a certificate.
    report_audit = pr.audit(vault, repo)
    assert path not in report_audit.active_pending_certificate


def test_coverage_certificate_with_flip_points_is_valid_coverage(tmp_path):
    # U-022 v2: a coverage certificate whose sweep found a flip in range is STILL
    # valid coverage (documenting flip points is its purpose) and satisfies rule (a).
    vault, repo = _vault(tmp_path)
    pr.refresh(vault, repo, clock=CLOCK)
    path = "scheduler.short_session_minutes"
    covered = pr._resolve_config_value(path, vault.config)
    report = _FakeSweepReport(
        results=[{"param_path": path, "value": covered, "verdict": "decision-relevant"}]
    )
    cert = sc.certificate_from_sweep_report(
        path=path, covered_value=covered, plausible_range={"low": 10, "high": 40},
        scenario={}, sweep_report=report,
    )
    assert cert.decision_stable is False and cert.flip_points  # flips in range
    sc.store_certificate(repo, cert, clock=CLOCK)
    linked = sc.link_coverage_certificate(repo, cert, clock=CLOCK)
    assert linked.linked is True  # flip points do NOT invalidate coverage
    report_audit = pr.audit(vault, repo)
    assert path not in report_audit.active_pending_certificate


def test_stale_coverage_certificate_does_not_link(tmp_path):
    vault, repo = _vault(tmp_path)
    pr.refresh(vault, repo, clock=CLOCK)
    path = "scheduler.short_session_minutes"
    cert = sc.certificate_from_sweep_report(
        path=path, covered_value=999, plausible_range={"low": 0, "high": 1},
        scenario={}, sweep_report=_FakeSweepReport(results=[]),
    )
    sc.store_certificate(repo, cert, clock=CLOCK)
    outcome = sc.link_coverage_certificate(repo, cert, clock=CLOCK)
    assert outcome.linked is False
    assert outcome.reason == "certificate_does_not_cover_current_value"


def test_promote_requires_covering_evidence(tmp_path):
    vault, repo = _vault(tmp_path)
    pr.refresh(vault, repo, clock=CLOCK)
    path = "scheduler.short_session_minutes"
    evidence = sc.promotion_evidence_from_sweep_report(
        path=path, covered_value=999, plausible_range={"low": 0, "high": 1},
        scenario={}, sweep_report=_FakeSweepReport(results=[]),
    )
    outcome = sc.promote(repo, evidence, clock=CLOCK)
    assert outcome.promoted is False
    assert outcome.refusal_reason == "certificate_does_not_cover_current_value"
    assert repo.parameter_registry_entry(path)["status"] == "heuristic"


def test_promote_refuses_decision_unstable_evidence(tmp_path):
    # F4 (re-framed): the decision_stable refusal now lives on PROMOTION EVIDENCE.
    # Both directions asserted against the same entry.
    vault, repo = _vault(tmp_path)
    pr.refresh(vault, repo, clock=CLOCK)
    path = "scheduler.short_session_minutes"
    covered = pr._resolve_config_value(path, vault.config)
    unstable = sc.promotion_evidence_from_sweep_report(
        path=path, covered_value=covered, plausible_range={"low": 10, "high": 40},
        scenario={},
        sweep_report=_FakeSweepReport(
            results=[{"param_path": path, "value": covered, "verdict": "decision-relevant"}]
        ),
    )
    assert unstable.decision_stable is False and unstable.flip_points
    refused = sc.promote(repo, unstable, clock=CLOCK)
    assert refused.promoted is False
    assert refused.refusal_reason == "decision_unstable_in_plausible_range"
    assert repo.parameter_registry_entry(path)["status"] == "heuristic"

    # Stable evidence covering the same value promotes (the other direction).
    stable = sc.promotion_evidence_from_sweep_report(
        path=path, covered_value=covered, plausible_range={"low": 10, "high": 40},
        scenario={},
        sweep_report=_FakeSweepReport(
            results=[{"param_path": path, "value": covered, "verdict": "inert in this scenario"}]
        ),
    )
    promoted = sc.promote(repo, stable, clock=CLOCK)
    assert promoted.promoted is True
    after = repo.parameter_registry_entry(path)
    assert after["status"] == "simulation_validated"
    assert after["promotion_evidence_id"] == stable.id
    # Promotion is now audit-clean for rule (b) (valid promotion evidence present).
    assert path not in pr.audit(vault, repo).promotion_without_evidence


def test_inert_classification_is_class_asymmetric():
    stable = {
        "scheduler.goal_frontier_weight": True,       # shaping_weight -> deletion candidate
        "evidence.certification.max_groups_per_attempt": True,  # constraint -> dormant
        "scheduler.short_session_minutes": False,     # not stable -> neither
    }
    report = sc.classify_inert_parameters(stable)
    assert "scheduler.goal_frontier_weight" in report.deletion_candidates
    assert "evidence.certification.max_groups_per_attempt" in report.dormant_constraints
    assert "scheduler.short_session_minutes" not in report.deletion_candidates
    assert "scheduler.short_session_minutes" not in report.dormant_constraints
