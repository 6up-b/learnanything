"""PF-a store-free harness invariants, plus the read-only vault boundary."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import numpy as np
import pytest

from learnloop.evaluation.harness import OutcomeRow, PredictionRow, replay
from learnloop.evaluation.predictors import FamilyMemory, IdeaHier
from learnloop.evaluation.report import evaluate, write_report
from learnloop.scheduling.fsrs import FSRS6_DEFAULT_WEIGHTS as W, Rating, apply_review


def row(n=0, **kwargs):
    features = PredictionRow(
        str(n), datetime(2026, 1, 1, tzinfo=timezone.utc)+timedelta(days=n),
        f"item{n}", "lo", family_id="family", variant_relation="same_target")
    feature_names = set(PredictionRow.__dataclass_fields__)
    changes = {key: value for key, value in kwargs.items() if key in feature_names}
    rest = {key: value for key, value in kwargs.items() if key not in feature_names}
    return replace(OutcomeRow(replace(features, **changes), 1.0, 4), **rest)


def test_prequential_predict_all_before_observe_and_no_outcome():
    events = []

    class Spy:
        granularity, version_hash = "attempt", "v1"

        def __init__(self, name):
            self.name = name

        def predict(self, f):
            assert not hasattr(f, "outcome")
            events.append(("predict", self.name, f.attempt_id))
            return .5

        def observe(self, r):
            events.append(("observe", self.name, r.features.attempt_id))

    replay([row(1), row(0)], [Spy("a"), Spy("b")])
    assert events[:4] == [("predict", "a", "0"), ("predict", "b", "0"),
                          ("observe", "a", "0"), ("observe", "b", "0")]


def test_prefix_predictions_do_not_change_with_future_outcomes():
    class Recording(IdeaHier):
        def __init__(self):
            super().__init__()
            self.predictions = []

        def predict(self, f):
            p = super().predict(f)
            self.predictions.append(p)
            return p

    a, b = Recording(), Recording()
    replay([row(0), row(1), row(2)], [a])
    replay([row(0), row(1), row(2, outcome=0, rating=1)], [b])
    assert a.predictions == b.predictions


def test_report_splits_by_original_resolved_family_judge_models():
    report = replay([row(family_judge_models=("producer-a", "producer-b"))], [IdeaHier()])
    splits = report["arms"]["idea_hier"]
    assert splits["family_judge_model:producer-a"]["count"] == 1
    assert splits["family_judge_model:producer-b"]["count"] == 1


@pytest.mark.parametrize("relation,cold,exclusion,mass,expected", [
    ("same_target", True, None, 1, 1), ("isomorph", True, None, 1, 1),
    ("near", True, None, 1, 0), ("far", True, None, 1, 0),
    ("same_target", False, None, 1, 0), ("same_target", True, "quarantined", 1, 0),
    ("same_target", True, None, 0, 1),
])
def test_memory_coldness_and_transfer_gate(relation, cold, exclusion, mass, expected):
    arm = FamilyMemory("family", W)
    arm.observe(row(variant_relation=relation, cold=cold, exclusion=exclusion, effective_mass=mass))
    assert len(arm.history) == expected


def test_shared_key_weights_and_elapsed_are_consistent():
    arms = [FamilyMemory(key, W) for key in ("item", "family", "lo")]
    for r in [row(0, item_id="item"), row(4, item_id="item")]:
        for arm in arms:
            arm.observe(r)
    states = [next(iter(a.history.values())).state for a in arms]
    expected = apply_review(apply_review(None, Rating.EASY, 0, W), Rating.EASY, 4, W)
    assert states == [expected]*3


def test_unfamilied_falls_back_to_item_and_transfer_never_trains():
    item, family = FamilyMemory("item", W), FamilyMemory("family", W)
    for r in [row(0, family_id=None), row(1, family_id=None)]:
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


def test_idea_hier_independent_priors_joint_update_and_no_mean_decay():
    arm = IdeaHier(sigma2_drift=.01)
    assert arm.predict(row().features) == .5
    assert np.diag(arm.cov).tolist() == [.75, 2.25, .5]
    assert np.count_nonzero(arm.cov-np.diag(np.diag(arm.cov))) == 0
    arm.observe(row())
    assert arm.cov[0, 2] != 0  # posterior, not priors, correlate
    assert np.linalg.eigvalsh(arm.cov).min() > 0
    mean = arm.mean.copy()
    old_variance = arm.cov[0, 0]
    arm.predict(row(10).features)
    assert np.array_equal(arm.mean, mean)
    assert arm.cov[0, 0] > old_variance
    arm.predict(row(11, family_id="unseen").features)
    estimate = next(r for r in arm.region_estimates() if r["id"] == "unseen")
    assert estimate["untested"] and estimate["variance"] == .5


def test_uncertainty_exclusions_counts_splits_and_aggregates_only(tmp_path):
    report = replay([row(0), row(1, outcome=0, rating=1), row(2, exclusion="quarantined")],
                    [IdeaHier(), FamilyMemory("family", W)])
    assert report["counts"]["excluded"] == {"quarantined": 1}
    assert report["counts"]["missing_skeleton_distance"] == 2
    overall = report["arms"]["idea_hier"]["overall"]
    assert overall["count"] == 2 and overall["intervals"]["brier"]
    assert report["arms"]["idea_hier"]["lo_history:first"]["count"] == 1
    assert report == replay([row(2, exclusion="quarantined"), row(1, outcome=0, rating=1), row(0)],
                            [IdeaHier(), FamilyMemory("family", W)])
    paths = write_report(report, tmp_path)
    text = paths[0].read_text()
    assert "item0" not in text and "family_id" not in text and "learner_answer" not in text
    assert json.loads(text) == report


def test_empty_report_and_duplicate_epoch_rejection():
    report = replay([], [IdeaHier()])
    assert report["arms"]["idea_hier"]["overall"]["count"] == 0
    assert report["arms"]["idea_hier"]["overall"]["log_loss"] is None
    with pytest.raises(ValueError, match="epoch"):
        replay([row(), row()], [IdeaHier()])


def test_zero_ability_mass_trains_memory_but_never_idea_hier():
    memory, ability = FamilyMemory("family", W), IdeaHier()
    report = replay([row(0, effective_mass=0), row(1, effective_mass=0)],
                    [memory, ability])
    assert report["counts"]["zero_ability_mass"] == 2
    assert report["arms"][memory.name]["overall"]["count"] == 2
    assert report["arms"][ability.name]["overall"]["count"] == 0
    assert memory.history["family:family"].review_count == 2
    assert ability.keys == [] and ability.direct == {}


def test_real_legacy_grades_produce_memory_report_without_ability_evidence(tmp_path):
    from tests.test_family_memory_projection import _attempt, _family, _vault

    vault, repo = _vault(tmp_path)
    _family(vault)
    _attempt(repo, 0)
    _attempt(repo, 2)
    before = repo.list_all_attempts()
    report = evaluate(vault, repo, legacy_fallback="current_content")
    for name, metrics in report["arms"].items():
        assert metrics["overall"]["count"] == (0 if name == "idea_hier" else 2)
    assert report["counts"]["memory_eligible"] == 2
    assert repo.list_all_attempts() == before


def test_vault_report_no_models_no_compatibility_cache(tmp_path, monkeypatch):
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path/"vault")
    vault = load_vault(paths.root)
    repo = Repository.attach(paths.sqlite_path, read_only=True)

    def forbidden(*args, **kwargs):
        raise AssertionError("offline replay must not read live memory or invoke a model")

    monkeypatch.setattr(repo, "practice_item_state", forbidden)
    monkeypatch.setattr(repo, "activity_card_state", forbidden)
    monkeypatch.setattr(repo, "item_parameter_state", forbidden)
    first = evaluate(vault, repo)
    second = evaluate(vault, repo)
    assert first == second
    assert len(first["arms"]) == 13
    assert first["manifest"]["weights"]["defaults"] == first["manifest"]["weights"]["current_fit"]
    assert first["manifest"]["current_fit_is_defaults"]
