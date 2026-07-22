"""P0.5 parameter registry + audit (spec §6, §9.6 bullet 5, §9.7 item 5).

The audit is the §9.6 gate: zero unclassified numeric config fields, zero
unclassified named module constants, zero decision params without status/
provenance, comment<->registration no-drift, and (with a vault) no
active-without-certificate / dormant-constraint-without-monitoring.
"""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.clock import FrozenClock
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import Repository
from learnloop.services import parameter_registry as pr
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault

CLOCK = FrozenClock(NOW)


def _vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return load_vault(paths.root), Repository(paths.sqlite_path)


def _config_vault(mutate):
    """A stub carrying a mutated config (audit only reads ``vault.config``)."""

    data = LearnLoopConfig().model_dump()
    mutate(data)
    return SimpleNamespace(config=LearnLoopConfig.model_validate(data))


def test_no_unclassified_parameters_static():
    report = pr.audit()
    assert report.unclassified_config == []
    assert report.unclassified_constants == []
    assert report.decision_without_metadata == []
    assert report.comment_registration_drift == []
    assert report.clean


def test_audit_clean_with_vault(tmp_path):
    vault, repo = _vault(tmp_path)
    pr.refresh(vault, repo, clock=CLOCK)
    report = pr.audit(vault, repo)
    assert report.clean, report.as_dict()


def test_every_config_numeric_leaf_is_classified():
    leaves = pr.config_numeric_leaves()
    assert len(leaves) > 200
    for path in leaves:
        assert path in pr.REGISTRY, f"unclassified config leaf: {path}"


def test_every_module_constant_is_registered():
    for path in pr.module_numeric_constants():
        assert path in pr.REGISTRY, f"unregistered module constant: {path}"


def test_tagged_decision_comments_have_registered_specs():
    tagged = pr.tagged_decision_constants()
    assert tagged  # the P0.2/P0.3 breadcrumbs exist
    for path in tagged:
        assert path in pr.REGISTRY


def test_refresh_is_idempotent_projection(tmp_path):
    vault, repo = _vault(tmp_path)
    n1 = pr.refresh(vault, repo, clock=CLOCK)
    rows1 = repo.parameter_registry_entries()
    n2 = pr.refresh(vault, repo, clock=CLOCK)
    rows2 = repo.parameter_registry_entries()
    assert n1 == n2
    # value/hash/status/lifecycle stable across a re-refresh.
    key = lambda rs: {r["path"]: (r["effective_value_hash"], r["status"], r["lifecycle"]) for r in rs}
    assert key(rows1) == key(rows2)


def test_migration_069_idempotent_on_copy(tmp_path):
    # Applying migrations twice on the same vault copy is stable (§9.6 bullet 1).
    vault, repo = _vault(tmp_path)
    pr.refresh(vault, repo, clock=CLOCK)
    before = repo.parameter_registry_entries()
    Repository(repo.sqlite_path)  # re-open triggers apply_migrations again (no-op)
    after = repo.parameter_registry_entries()
    assert before == after


def test_decision_specs_carry_promotion_gate_and_rationale():
    for spec in pr.decision_specs():
        assert spec.rationale
        assert spec.promotion_gate is not None


def test_abstention_budget_is_registered_and_monitored():
    spec = pr.REGISTRY.get("robust_composition:ABSTENTION_BUDGET_FRACTION")
    assert spec is not None
    assert spec.kind == "decision"
    assert spec.param_class == "constraint"
    assert spec.default_lifecycle == "dormant"
    assert spec.bind_site  # monitored (U-021)


def test_bind_event_logging_records_and_reads(tmp_path):
    vault, repo = _vault(tmp_path)
    pr.record_bind(
        repo,
        "evidence.certification.max_groups_per_attempt",
        {"clamped_from": 5, "clamped_to": 3},
        observation_ref="obs_x",
        clock=CLOCK,
    )
    events = repo.parameter_bind_events_for_path("evidence.certification.max_groups_per_attempt")
    assert len(events) == 1
    assert events[0]["observation_ref"] == "obs_x"


def test_value_change_without_evidence_demotes_to_heuristic(tmp_path):
    import json

    vault, repo = _vault(tmp_path)
    pr.refresh(vault, repo, clock=CLOCK)
    path = "grader_calibration:PRIOR_CONCENTRATION"
    entry = repo.parameter_registry_entry(path)
    # Simulate a prior promotion to simulation_validated, then a value change with no
    # matching evidence (mismatched stored hash, as if the constant moved).
    entry["effective_value"] = json.loads(entry["effective_value_json"])
    entry["status"] = "simulation_validated"
    entry["effective_value_hash"] = "deadbeef" * 4
    repo.upsert_parameter_registry_entry(entry=entry, clock=CLOCK)
    pr.refresh(vault, repo, clock=CLOCK)
    after = repo.parameter_registry_entry(path)
    assert after["status"] == "heuristic"
    assert after["sensitivity_certificate_id"] is None


def test_demotion_clears_evidence_and_redundancy_proofs(tmp_path):
    # F10b: a value-change demotion must also drop the real-outcome evidence manifest
    # and redundancy-proof links, not just the certificate.
    import json

    vault, repo = _vault(tmp_path)
    pr.refresh(vault, repo, clock=CLOCK)
    path = "grader_calibration:PRIOR_CONCENTRATION"
    entry = repo.parameter_registry_entry(path)
    entry["effective_value"] = json.loads(entry["effective_value_json"])
    entry["status"] = "live_calibrated"
    entry["evidence_manifest_id"] = "man_x"
    entry["redundancy_proof_id"] = "proof_y"
    entry["effective_value_hash"] = "deadbeef" * 4  # value moved, no matching evidence
    repo.upsert_parameter_registry_entry(entry=entry, clock=CLOCK)
    pr.refresh(vault, repo, clock=CLOCK)
    after = repo.parameter_registry_entry(path)
    assert after["status"] == "heuristic"
    assert after["sensitivity_certificate_id"] is None
    assert after["evidence_manifest_id"] is None
    assert after["redundancy_proof_id"] is None


def test_catchall_rule_is_frozen_to_snapshot():
    # F6: the broad decision-namespace catch-all no longer silently classifies a
    # FUTURE field. A currently-owned leaf still classifies; an unseen one does not.
    assert pr.CATCHALL_SNAPSHOT
    owned = next(iter(pr.CATCHALL_SNAPSHOT))
    assert pr.classify_config_path(owned) is not None
    assert pr.classify_config_path("scheduler.some_future_knob_v99") is None
    assert pr.classify_config_path("mastery.some_future_field_v99") is None


def test_audit_flags_future_field_under_decision_namespace():
    # F6/F10a end-to-end: a numeric leaf added under a frozen decision namespace that
    # no rule covers is reported unclassified (not silently swept into "threshold").
    vault = _config_vault(
        lambda d: d["evidence"]["certification"]["group_budgets"].__setitem__(
            "future_group", 3
        )
    )
    report = pr.audit(vault)
    assert "evidence.certification.group_budgets.future_group" in report.unclassified_config
    assert not report.clean


def test_active_heuristic_without_coverage_is_pending_warning_not_failure(tmp_path):
    # U-022 v2 (a): EVERY active decision parameter needs a coverage certificate. A
    # fresh vault has zero -> they enumerate as active_pending_certificate DEBT: the
    # ordinary audit stays CLEAN (warning), but the strict release gate BLOCKS.
    vault, repo = _vault(tmp_path)
    pr.refresh(vault, repo, clock=CLOCK)
    report = pr.audit(vault, repo)
    # A fresh heuristic-active decision parameter is pending, not failing.
    path = "scheduler.short_session_minutes"
    entry = repo.parameter_registry_entry(path)
    assert entry["lifecycle"] == "active" and entry["status"] == "heuristic"
    assert path in report.active_pending_certificate
    assert report.clean  # ordinary audit: pending is a warning, not a failure
    assert not report.release_clean  # strict release gate: pending blocks


def test_dormant_parameter_needs_no_coverage_certificate(tmp_path):
    # U-022 v2 boundary: dormant parameters need only bind-event logging, never a
    # coverage certificate -- dormancy is the explicit alternative to sweeping.
    vault, repo = _vault(tmp_path)
    pr.refresh(vault, repo, clock=CLOCK)
    report = pr.audit(vault, repo)
    dormant_path = "evidence.certification.max_groups_per_attempt"
    entry = repo.parameter_registry_entry(dormant_path)
    assert entry["lifecycle"] == "dormant"
    assert dormant_path not in report.active_pending_certificate


def test_status_above_heuristic_without_promotion_evidence_is_failure(tmp_path):
    # U-022 v2 (b): a status claim above heuristic with no valid promotion evidence
    # is a hard failure (distinct from pending coverage debt).
    import json

    vault, repo = _vault(tmp_path)
    pr.refresh(vault, repo, clock=CLOCK)
    path = "scheduler.short_session_minutes"
    entry = repo.parameter_registry_entry(path)
    # Claim simulation_validated with no promotion evidence, value hash unchanged
    # (so refresh does not demote it away before the audit runs).
    entry["effective_value"] = json.loads(entry["effective_value_json"])
    entry["status"] = "simulation_validated"
    repo.upsert_parameter_registry_entry(entry=entry, clock=CLOCK)
    report = pr.audit(vault, repo)
    assert path in report.promotion_without_evidence
    assert not report.clean  # promotion-without-evidence is a failure


def test_audit_falls_back_to_rules_for_vault_added_dict_keys():
    # F10a: a vault-added dict key that a classification rule DOES cover passes the
    # audit even though it is absent from REGISTRY (built from the default config).
    vault = _config_vault(
        lambda d: d["evidence"]["attempt_types"].__setitem__(
            "custom_probe", {"evidence_mass": 0.4, "surface_exposure": None}
        )
    )
    report = pr.audit(vault)
    assert report.unclassified_config == []
