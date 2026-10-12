"""PF-a arms on the shared learner-field harness: store-free invariants.

The memory arms and idea_hier are registered in the field arm registry and run
in the one prequential loop (``learnloop.field.evaluation.evaluate``).
"""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import numpy as np
import pytest

from learnloop.field.evaluation import evaluate, family_arms, write_reports
from learnloop.field.memory import memory_arm_name
from learnloop.field.predictors import (
    create_predictor, is_calibrated_predictor, registered_predictors, validate_active_predictor,
)
from learnloop.field.types import AttemptRow, ItemFeatures
from learnloop.scheduling.family_memory_model import FamilyMemory
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS as W, Rating, apply_review

START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def row(n=0, *, outcome=1.0, rating=4, **kwargs):
    """A graded cold same-target retrieval of a familied item, day ``n``."""
    features = ItemFeatures(
        f"item{n}", "lo", (START + timedelta(days=n)).isoformat(),
        family_id="family", variant_relation="same_target")
    feature_names = set(ItemFeatures.__dataclass_fields__)
    changes = {key: value for key, value in kwargs.items() if key in feature_names}
    rest = {key: value for key, value in kwargs.items() if key not in feature_names}
    values = dict(effective_mass=1.0, fsrs_rating=rating, retrieval_cold=True)
    values.update(rest)
    return AttemptRow(str(n), replace(features, **changes), outcome, **values)


def run(rows, arms, **kwargs):
    return evaluate(rows, arms=arms, bootstrap_samples=30, **kwargs)


def test_family_arms_are_registered_in_the_field_registry():
    names = family_arms()
    assert names[:3] == ("mastery_ekf", "lo_general", "idea_hier")
    memory = registered_predictors(group="memory")
    assert len(memory) == 12 and set(memory) <= set(names)
    assert set(names) <= set(registered_predictors())
    assert memory_arm_name("family", "defaults", True) == "memory_family/defaults/distance"
    # G11: memory arms are point predictors; idea_hier is calibrated but F1-inactive.
    for name in memory:
        assert not is_calibrated_predictor(name)
        with pytest.raises(ValueError, match="calibrated uncertainty"):
            validate_active_predictor(name)
    assert is_calibrated_predictor("idea_hier")
    with pytest.raises(ValueError, match="successor"):
        validate_active_predictor("idea_hier")


def test_memory_arm_inputs_are_frozen_and_never_a_store():
    fit = tuple(w * 1.01 for w in W)
    current = create_predictor("memory_lo/current_fit", fsrs_weights=fit)
    defaults = create_predictor("memory_lo/defaults", fsrs_weights=fit)
    assert current.weights == fit and defaults.weights == W
    assert create_predictor("memory_lo/current_fit").weights == W
    with pytest.raises(TypeError, match="does not accept"):
        create_predictor("memory_lo/defaults", repository=object())


def test_prequential_predict_all_before_observe_including_memory():
    events = []

    class Spy(FamilyMemory):
        def predict(self, features):
            events.append(("predict", self.name, features.item_id))
            return super().predict(features)

        def observe(self, r):
            events.append(("observe", self.name, getattr(r, "attempt_id", "")))
            super().observe(r)

    a, b = Spy("item", W), Spy("family", W)
    run([row(1), row(0)], [a, b])
    assert events[:4] == [("predict", a.name, "item0"), ("predict", b.name, "item0"),
                          ("observe", a.name, "0"), ("observe", b.name, "0")]


def test_prefix_predictions_do_not_change_with_future_outcomes():
    predictions = {}

    def recording(name):
        arm = create_predictor(name)
        original = arm.predict

        def predict(features):
            p = original(features)
            predictions.setdefault(name, []).append(p)
            return p
        arm.predict = predict
        return arm

    for name in ("idea_hier", "memory_family/defaults"):
        run([row(0), row(1), row(2)], [recording(name)])
        first = predictions.pop(name)
        run([row(0), row(1), row(2, outcome=0, rating=1)], [recording(name)])
        assert predictions.pop(name) == first


def test_report_splits_by_original_resolved_family_judge_models():
    report = run([row(family_judge_models=("producer-a", "producer-b"))], ["idea_hier"])
    splits = report["report1"]["arms"]["idea_hier"]["splits"]
    assert splits["family_judge_model"]["producer-a+producer-b"]["n"] == 1
    assert splits["relation"]["same_target"]["n"] == 1
    assert splits["retrieval"]["cold"]["n"] == 1


@pytest.mark.parametrize("relation,cold,revision,rating,expected", [
    ("same_target", True, "exact", 4, 1), ("isomorph", True, "exact", 4, 1),
    ("near", True, "exact", 4, 0), ("far", True, "exact", 4, 0),
    ("same_target", False, "exact", 4, 0), ("same_target", True, "excluded", 4, 0),
    # No persisted FSRS rating: quarantined, ungraded or not a graded retrieval.
    ("same_target", True, "exact", None, 0),
    ("same_target", True, "reconstructed_current", 4, 1),
])
def test_memory_coldness_and_transfer_gate(relation, cold, revision, rating, expected):
    arm = FamilyMemory("family", W)
    arm.observe(row(variant_relation=relation, retrieval_cold=cold,
                    revision_status=revision, rating=rating))
    assert len(arm.history) == expected


def test_shared_key_weights_and_elapsed_are_consistent():
    arms = [FamilyMemory(key, W) for key in ("item", "family", "lo")]
    for r in [row(0, item_id="item"), row(4, item_id="item")]:
        for arm in arms:
            arm.observe(r)
    states = [next(iter(a.history.values())).state for a in arms]
    expected = apply_review(apply_review(None, Rating.EASY, 0, W), Rating.EASY, 4, W)
    assert states == [expected] * 3


def test_unfamilied_falls_back_to_item_and_transfer_never_trains():
    item, family = FamilyMemory("item", W), FamilyMemory("family", W)
    for r in [row(0, family_id=None, variant_relation=None),
              row(1, family_id=None, variant_relation=None)]:
        item.observe(r)
        family.observe(r)
    assert item.history == family.history
    prior = dict(family.history)
    family.observe(row(3, variant_relation="near"))
    assert family.history == prior


def test_distance_arm_discounts_only_real_positive_credit():
    plain, discounted = FamilyMemory("family", W), FamilyMemory("family", W, distance_discount=True)
    plain.observe(row())
    discounted.observe(row())
    assert plain.history == discounted.history  # no fake skeleton distance
    plain.observe(row(2, variant_distance=1))
    discounted.observe(row(2, variant_distance=1))
    assert discounted.history["family:family"].state.stability < plain.history["family:family"].state.stability


def test_idea_hier_is_lo_general_with_independent_family_priors_and_no_mean_decay():
    arm = create_predictor("idea_hier")
    features = row().features
    assert arm.predict(features) == .5
    keys, _, covariance = arm._view([features])
    assert keys == ["general:default", "lo:lo", "family:family"]
    assert np.diag(covariance).tolist() == [.75, 2.25, .5]
    assert np.count_nonzero(covariance - np.diag(np.diag(covariance))) == 0
    arm.observe(row())
    assert arm.covariance[0, 2] != 0  # posteriors, not priors, correlate
    assert np.linalg.eigvalsh(arm.covariance).min() > 0
    mean = arm.mean.copy()
    arm.predict(row(10).features)
    assert np.array_equal(arm.mean, mean)  # no mean decay, and prediction is pure
    unseen = replace(row(11).features, family_id="unseen")
    arm.items = {unseen.item_id: unseen}
    estimate = arm.region_estimates()["family:unseen"]
    assert estimate.untested and estimate.variance == .5
    # Without a family the arm is exactly lo_general.
    plain, base = create_predictor("idea_hier"), create_predictor("lo_general")
    unfamilied = replace(row(0), features=replace(row(0).features, family_id=None, variant_relation=None))
    plain.observe(unfamilied)
    base.observe(unfamilied)
    assert np.array_equal(plain.mean, base.mean) and np.array_equal(plain.covariance, base.covariance)


def test_uncertainty_exclusions_counts_splits_and_aggregates_only(tmp_path):
    rows = [row(0), row(1, outcome=0, rating=1),
            row(2, revision_status="excluded", effective_mass=0, rating=None)]
    arms = ["idea_hier", "memory_family/defaults"]
    report = run(rows, arms)
    assert report["counts"]["excluded_attempts"] == 1
    assert report["counts"]["missing_variant_distance"] == 2
    assert report["counts"]["memory_scored_attempts"] == 2
    overall = report["report1"]["arms"]["idea_hier"]["overall"]
    assert overall["n"] == 2 and overall["brier"]["ci95"]
    assert report["report1"]["arms"]["idea_hier"]["splits"]["attempt_position"]["first_unseen_lo"]["n"] == 1
    assert report == run(list(reversed(rows)), arms)
    assert report["manifest"]["memory"]["weights"]["current_fit"]["is_defaults"]
    paths = write_reports(report, tmp_path, stem="families")
    text = (tmp_path / "families.json").read_text()
    assert "item0" not in text and '"family"' not in text and "learner_answer" not in text
    assert json.loads(text) == report
    assert set(paths) == {"json", "markdown"}


def test_empty_report_and_duplicate_epoch_rejection():
    report = run([], ["idea_hier", "memory_item/defaults"])
    assert report["report1"]["arms"]["idea_hier"]["overall"]["n"] == 0
    assert report["report1"]["arms"]["idea_hier"]["overall"]["log_loss"]["mean"] is None
    with pytest.raises(ValueError, match="Duplicate attempt rows"):
        run([row(), row()], ["idea_hier"])


def test_zero_ability_mass_trains_memory_but_never_idea_hier():
    memory, ability = create_predictor("memory_family/defaults"), create_predictor("idea_hier")
    before = ability.snapshot_bytes()
    report = run([replace(row(0), effective_mass=0), replace(row(1), effective_mass=0)],
                 [memory, ability])
    assert report["counts"]["zero_ability_mass"] == 2
    assert report["counts"]["ability_scored_attempts"] == 0
    arms = report["report1"]["arms"]
    assert arms[memory.name]["overall"]["n"] == 2
    assert arms[ability.name]["overall"]["n"] == 0
    assert arms[ability.name]["unscored_attempts"] == 2
    assert memory.history["family:family"].review_count == 2
    assert ability.snapshot_bytes() == before


def test_memory_arms_score_only_cold_retrievals_and_never_recommend():
    warm = row(1, retrieval_cold=False)
    report = run([row(0), warm, row(2)], ["mastery_ekf", "idea_hier", "memory_item/defaults"])
    arms = report["report1"]["arms"]
    assert arms["memory_item/defaults"]["overall"]["n"] == 2
    assert arms["memory_item/defaults"]["scores"] == "graded_cold_retrievals"
    assert arms["mastery_ekf"]["overall"]["n"] == 3
    assert "memory_item/defaults" not in report["recommendation"]["candidates"]
    assert report["report2"]["arms"]["memory_item/defaults"]["assumed_los"] == 0
    assert report["report1"]["limitations"]
