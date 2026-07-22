"""Characterization tests (P0.0, spec_p0_measurement_correctness.md §2): pin current behavior;
these tests document reality, not desired behavior. When P0.x intentionally changes behavior,
update these tests in the same commit and note the change.

Target: probe-family real-learner calibration in
``learnloop.services.probe_families.record_real_observation_counts`` and its readers
``real_calibration_counts`` / ``shrunk_item_calibration_counts``.

What this pins (current EM-style fractional-count behavior):
  * A posterior-weighted latent label is folded into the family-version Dirichlet
    posterior as a FRACTIONAL ``real_learner`` count (not an integer 1), and multiple
    labels mapping to the same hypothesis slot are SUMMED before folding.
  * Negative posterior weights are clamped to 0 (``max(prob, 0.0)``).
  * The exact update arithmetic, sample_size, and effective_sample_size for constructed cases.
  * Promotion/status behavior: recording real observations writes ONLY under
    ``evidence_source='real_learner'`` — it never touches the ``synthetic_gate`` row and
    never changes the family template ``status`` (no promotion). It DOES flow into the
    operative read path (``shrunk_item_calibration_counts``) consumed when instruments compile.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.probe_families import (
    CONTRAST_CONFUSABLE_V1,
    real_calibration_counts,
    record_real_observation_counts,
    shrunk_item_calibration_counts,
)
from tests.helpers import NOW, admit_probe_instrument_card, create_basic_vault

FAMILY = CONTRAST_CONFUSABLE_V1.id
VERSION = CONTRAST_CONFUSABLE_V1.version
GRADER = CONTRAST_CONFUSABLE_V1.grader_policy
ITEM = "pi_svd_define_001"
OUTCOME = "correct_target_reason"


def _repo(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository, items=(ITEM,))
    return repository


def _clock():
    return FrozenClock(NOW)


def test_posterior_weight_is_folded_as_fractional_real_learner_count(tmp_path):
    """A single observation with a split posterior lands as fractional per-slot counts.

    The observed outcome is a single symbol, but the latent hypothesis is
    posterior-weighted: 0.7 of the observation credits ``robust_initial_grasp`` and
    0.3 credits ``confuses_with_neighbor``. This is only observable BECAUSE the counts
    are fractional — an integer-count treatment would be indistinguishable here.
    """

    repository = _repo(tmp_path)
    record_real_observation_counts(
        repository,
        family_template_id=FAMILY,
        family_template_version=VERSION,
        posterior_after={"robust_initial_grasp": 0.7, "confuses_with_neighbor": 0.3},
        slot_map={
            "robust_initial_grasp": "robust_initial_grasp",
            "confuses_with_neighbor": "confuses_with_neighbor",
        },
        observed_outcome=OUTCOME,
        grader_version=GRADER,
        clock=_clock(),
    )

    counts = real_calibration_counts(repository, FAMILY, VERSION, grader_version=GRADER)
    assert counts == {
        "robust_initial_grasp": {OUTCOME: pytest.approx(0.7)},
        "confuses_with_neighbor": {OUTCOME: pytest.approx(0.3)},
    }

    row = repository.probe_family_calibration(
        FAMILY, VERSION, evidence_source="real_learner", grader_version=GRADER
    )
    # One physical observation -> sample_size 1; the fractional mass sums to 1.0.
    assert row["sample_size"] == 1
    assert row["effective_sample_size"] == pytest.approx(1.0)


def test_labels_sharing_a_slot_are_summed_and_negatives_clamped(tmp_path):
    """Multiple posterior labels mapping to one slot are summed; negative weight -> 0."""

    repository = _repo(tmp_path)
    record_real_observation_counts(
        repository,
        family_template_id=FAMILY,
        family_template_version=VERSION,
        # a + b -> slot "S" (0.6 + 0.1 = 0.7); c has negative weight, clamped to 0.
        posterior_after={"a": 0.6, "b": 0.1, "c": -0.5},
        slot_map={"a": "S", "b": "S", "c": "S"},
        observed_outcome=OUTCOME,
        grader_version=GRADER,
        clock=_clock(),
    )

    counts = real_calibration_counts(repository, FAMILY, VERSION, grader_version=GRADER)
    assert counts == {"S": {OUTCOME: pytest.approx(0.7)}}

    row = repository.probe_family_calibration(
        FAMILY, VERSION, evidence_source="real_learner", grader_version=GRADER
    )
    assert row["sample_size"] == 1
    assert row["effective_sample_size"] == pytest.approx(0.7)


def test_repeated_observations_accumulate_fractional_counts(tmp_path):
    """A second identical observation doubles the counts; sample_size increments by one."""

    repository = _repo(tmp_path)
    for _ in range(2):
        record_real_observation_counts(
            repository,
            family_template_id=FAMILY,
            family_template_version=VERSION,
            posterior_after={"a": 0.6, "b": 0.1},
            slot_map={"a": "S", "b": "S"},
            observed_outcome=OUTCOME,
            grader_version=GRADER,
            clock=_clock(),
        )

    counts = real_calibration_counts(repository, FAMILY, VERSION, grader_version=GRADER)
    assert counts == {"S": {OUTCOME: pytest.approx(1.4)}}

    row = repository.probe_family_calibration(
        FAMILY, VERSION, evidence_source="real_learner", grader_version=GRADER
    )
    assert row["sample_size"] == 2
    assert row["effective_sample_size"] == pytest.approx(1.4)


def test_real_learner_write_does_not_promote_or_touch_synthetic_gate(tmp_path):
    """Self-fit real data updates only the ``real_learner`` channel and leaves status alone.

    Pinned promotion behavior: recording never writes the ``synthetic_gate`` row and
    never changes the family template ``status`` (it stays whatever admission set it to,
    ``provisional`` for the built-in card). The real counts DO reach the operative read
    path used at instrument-compile time (``shrunk_item_calibration_counts``).
    """

    repository = _repo(tmp_path)
    status_before = repository.probe_family_template(FAMILY, VERSION).status

    record_real_observation_counts(
        repository,
        family_template_id=FAMILY,
        family_template_version=VERSION,
        posterior_after={"robust_initial_grasp": 0.7, "confuses_with_neighbor": 0.3},
        slot_map={
            "robust_initial_grasp": "robust_initial_grasp",
            "confuses_with_neighbor": "confuses_with_neighbor",
        },
        observed_outcome=OUTCOME,
        grader_version=GRADER,
        practice_item_id=ITEM,
        clock=_clock(),
    )

    # No synthetic_gate row is created by the real-learner path (§9.6 separation).
    assert (
        repository.probe_family_calibration(
            FAMILY, VERSION, evidence_source="synthetic_gate", grader_version=GRADER
        )
        is None
    )
    # Family status is untouched: recording does not promote.
    assert repository.probe_family_template(FAMILY, VERSION).status == status_before == "provisional"

    # Operative read path DOES reflect the real counts. With family total mass (1.0)
    # below the shrinkage pseudo-count (25), the family direction passes through at full
    # strength and the item's own residual adds on top -> exactly 2x the recorded mass.
    shrunk = shrunk_item_calibration_counts(
        repository, FAMILY, VERSION, practice_item_id=ITEM, grader_version=GRADER
    )
    assert shrunk == {
        "robust_initial_grasp": {OUTCOME: pytest.approx(1.4)},
        "confuses_with_neighbor": {OUTCOME: pytest.approx(0.6)},
    }
