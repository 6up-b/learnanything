"""Checkpoint-3 sim validation: planted latent hypothesis types drive the real
episode policy end to end (spec §14 Checkpoint 3.9, regression test 37)."""

from __future__ import annotations

import copy
import pytest

from learnloop.clock import FrozenClock
from learnloop.sim.diagnostic_validation import ValidationReport, run_probe_validation
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_learning_object

from tests.helpers import NOW, create_basic_vault

CLOCK = FrozenClock(NOW)


def _vault_with_confusable(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    payload = loaded.learning_objects["lo_svd_definition"].model_dump()
    payload["confusables"] = ["eigendecomposition"]
    upsert_learning_object(vault_root, payload, clock=CLOCK)
    return vault_root


@pytest.fixture(scope="module")
def validation_report(tmp_path_factory):
    root = tmp_path_factory.mktemp("planted-validation")
    vault_root = _vault_with_confusable(root)
    return run_probe_validation(vault_root, root / "runs", seeds=(11, 12, 13, 14, 15))


def test_planted_confuses_with_is_diagnosed_within_budget(validation_report):
    """Spec regression test 37: a planted confuses_with student is diagnosed
    within the observation budget with the matching instructional action."""

    report = ValidationReport(results=copy.deepcopy([row for row in validation_report.results if row.planted == "confuses_with" and row.seed in (11, 12, 13)]))
    summary = report.by_planted()["confuses_with"]
    assert summary["completed"] == 3
    assert summary["label_accuracy"] >= 2 / 3
    assert summary["action_accuracy"] >= 2 / 3
    assert summary["mean_observations"] <= 4.0
    for result in report.results:
        if result.label_matched:
            assert result.diagnosed_action == "contrastive_repair"


def test_planted_types_pass_the_checkpoint_gate(validation_report):
    """Checkpoint 4 entry gate: every planted type classified at or above the
    configured accuracy within the observation budget, with matching actions."""

    report = copy.deepcopy(validation_report)
    assert report.passes(label_accuracy_threshold=0.6, action_accuracy_threshold=0.6), (
        report.as_dict()["by_planted"]
    )
    # Selection, stopping, and accounting: every episode completed within its
    # observation budget through qualifying observations only.
    for result in report.results:
        assert result.completed
        assert result.observations_used <= 4
