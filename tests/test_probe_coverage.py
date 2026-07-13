"""Hypothesis-contrast / family coverage report (spec §9.5, Checkpoint 3.3)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.probe_coverage import family_coverage_report
from learnloop.services.probe_families import MINIMAL_RECALL_V1, PERTURBATION_V1
from learnloop.services.probe_instance_generation import ensure_instrument_card
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, admit_probe_instrument_card, create_basic_vault

LO_ID = "lo_svd_definition"
CLOCK = FrozenClock(NOW)


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    return loaded, repository


def test_report_flags_uncovered_contrasts_without_bindings(tmp_path):
    loaded, repository = _setup(tmp_path)
    report = family_coverage_report(loaded, repository)
    assert report["totals"]["learning_objects"] == 1
    assert report["totals"]["learning_objects_with_bindings"] == 0
    entry = report["learning_objects"][0]
    assert entry["learning_object_id"] == LO_ID
    assert entry["contrasts"]
    assert all(not contrast["fully_covered"] for contrast in entry["contrasts"])


def test_direct_plus_shifted_bindings_cover_a_contrast(tmp_path):
    loaded, repository = _setup(tmp_path)
    # A shifted instrument alone is not §9.5 coverage...
    admit_probe_instrument_card(repository, items=("pi_svd_define_001",))
    ensure_instrument_card(loaded, repository, LO_ID, PERTURBATION_V1, clock=CLOCK)
    partial = family_coverage_report(loaded, repository)
    unfamiliar_robust = _contrast(partial, "robust_initial_grasp", "unfamiliar")
    assert unfamiliar_robust["shifted_families"]
    assert not unfamiliar_robust["fully_covered"]

    # ...adding the direct/minimal family completes the pair requirement.
    ensure_instrument_card(loaded, repository, LO_ID, MINIMAL_RECALL_V1, clock=CLOCK)
    full = family_coverage_report(loaded, repository)
    unfamiliar_robust = _contrast(full, "robust_initial_grasp", "unfamiliar")
    assert unfamiliar_robust["direct_families"] == ["minimal_recall"]
    assert unfamiliar_robust["fully_covered"]
    assert full["totals"]["contrasts_fully_covered"] >= 1


def _contrast(report, left, right):
    entry = report["learning_objects"][0]
    for contrast in entry["contrasts"]:
        if set(contrast["pair"]) == {left, right}:
            return contrast
    raise AssertionError(f"contrast {left} vs {right} not in report")
