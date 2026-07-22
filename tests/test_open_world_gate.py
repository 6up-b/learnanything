"""P4 open-world §14.1 DEPENDENCY GATE (spec_p4 §14.1, §10; design §B open-world).

Open-world expansion is intentionally last and is NOT implemented. This asserts the
executable gate enumerates the six conditions, reports each truthfully, currently
evaluates NOT MET (the kernel shadow audit / admission has not cleared -- firewall), and
that no expansion is enabled while the substrate is absent.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import kinship_feature as kf
from learnloop.services import open_world_gate as owg
from learnloop.services import parameter_registry as pr
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault

CLOCK = FrozenClock(NOW)


@pytest.fixture
def wired(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repo = Repository(paths.sqlite_path)
    pr.refresh(vault, repo, clock=CLOCK)
    return vault, repo


def test_gate_enumerates_the_six_conditions(wired):
    vault, repo = wired
    report = owg.evaluate_gate(vault, repo)
    assert len(report.conditions) == 6
    keys = [c.key for c in report.conditions]
    assert keys == [
        "p0_calibrated_reliability_robust_bounds",
        "p1_exposure_hard_groups_lineage_purpose",
        "p2_end_to_end_held_out_journey",
        "p3_local_hypothesis_seed_provenance",
        "controller_constraints_target_eig_shadow_logging",
        "dispersion_interleaving_kernel_shadow_audit",
    ]
    # Every condition names its spec clause and carries a truthful detail string.
    for condition in report.conditions:
        assert condition.spec_ref.startswith("§14.1")
        assert condition.detail


def test_gate_is_currently_not_met_blocked_by_kernel_admission(wired):
    vault, repo = wired
    report = owg.evaluate_gate(vault, repo)
    assert report.met is False
    # The open-world substrate is absent (schema not landed) -> expansion stays disabled.
    assert report.open_world_schema_present is False
    assert "REMAIN DISABLED" in report.as_dict()["enablement"]
    # The blocking condition is the descoped kernel-shadow audit: the soft-kinship
    # feature is behind its admission gate (firewall), the last dependency to clear.
    blocking = report.as_dict()["blocking"]
    assert blocking == ["dispersion_interleaving_kernel_shadow_audit"]
    # The upstream P0-P4 substrates are landed and evaluate MET.
    met = {c.key: c.met for c in report.conditions}
    assert met["p0_calibrated_reliability_robust_bounds"]
    assert met["controller_constraints_target_eig_shadow_logging"]
    assert not met["dispersion_interleaving_kernel_shadow_audit"]


def test_condition_six_clears_only_after_kernel_admission(wired):
    vault, repo = wired
    kf.run_admission_gate(repo, clock=CLOCK)  # admit the soft-kinship feature
    report = owg.evaluate_gate(vault, repo)
    met = {c.key: c.met for c in report.conditions}
    assert met["dispersion_interleaving_kernel_shadow_audit"] is True
    # All six substrate conditions now pass; the gate still gates ENABLEMENT on the
    # (absent) open-world schema, so expansion is still not turned on.
    assert report.met is True
    assert report.open_world_schema_present is False
    assert "REMAIN DISABLED" in report.as_dict()["enablement"]
