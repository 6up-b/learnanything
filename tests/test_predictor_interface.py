from dataclasses import FrozenInstanceError

import pytest

from learnloop.field.predictors import (
    create_predictor, is_calibrated_predictor, registered_predictors,
    validate_active_predictor,
)
from learnloop.field.types import (
    AttemptRow, ItemFeatures, ItemPrediction, LearnerPredictor, RegionEstimate,
)
from tests.helpers import create_basic_vault


class FakePredictor:
    name = "fake"
    version_hash = "fake-v1"
    granularity = "attempt"
    calibrated_uncertainty = True

    def predict(self, features):
        return self.predict_item(features).p_success

    def predict_item(self, item):
        return ItemPrediction(0.5, 3, (("L", 1),))

    def conditional_gain(self, item, chosen, weights):
        return 0.2

    def region_estimates(self, scope=None):
        return {"L": RegionEstimate(0, 3, 0, True)}

    def observe(self, row):
        pass

    def rebuild(self, rows):
        pass


def consumer(predictor: LearnerPredictor, features: ItemFeatures):
    prediction = predictor.predict_item(features)
    gain = predictor.conditional_gain(features, [], {"L": 1})
    estimates = predictor.region_estimates()
    return prediction, gain, estimates


@pytest.mark.parametrize("name", ["fake"] + [
    name for name in registered_predictors() if is_calibrated_predictor(name)])
def test_unchanged_consumer_uses_only_interface(name):
    features = ItemFeatures("i", "L", "2026-01-01T00:00:00Z")
    model = FakePredictor() if name == "fake" else create_predictor(name, items=[features])
    assert isinstance(model, LearnerPredictor)
    prediction, gain, estimates = consumer(model, features)
    assert 0 < prediction.p_success < 1
    assert prediction.logit_variance > 0 and gain > 0
    assert estimates["L"].untested


def test_activation_eligibility_and_f1_successor_boundary():
    validate_active_predictor("mastery_ekf")
    assert is_calibrated_predictor("lo_general")
    for name in ("base_rate_lo", "facet_beta", "llm_probability", "unknown"):
        assert not is_calibrated_predictor(name)
        with pytest.raises(ValueError, match="calibrated uncertainty"):
            validate_active_predictor(name)
    with pytest.raises(ValueError, match="successor"):
        validate_active_predictor("lo_general")


def test_input_contract_is_immutable_and_excludes_outcomes():
    features = ItemFeatures("i", "L", "2026-01-01T00:00:00Z")
    row = AttemptRow("a", features, 1, 1)
    with pytest.raises(FrozenInstanceError):
        row.outcome = 0
    with pytest.raises(FrozenInstanceError):
        features.b = 10
    assert not hasattr(features, "outcome")
    assert not hasattr(features, "effective_mass")
    for name in registered_predictors():
        with pytest.raises(TypeError, match="outcome-free"):
            create_predictor(name).predict(row)


def test_incumbent_uses_explicit_vault_config_without_reading_store(tmp_path):
    # Use the fixture builder rather than constructing a vault by hand. The
    # adapter receives only immutable values; it cannot write the fixture.
    paths = create_basic_vault(tmp_path)
    from learnloop.vault.loader import load_vault
    vault = load_vault(paths.root)
    model = create_predictor("mastery_ekf", config=vault.config.mastery)
    features = ItemFeatures("i", "L", "2026-01-01T00:00:00Z")
    assert model.predict(features) == 0.5
    model.observe(AttemptRow("a", features, 1, 1))
    assert model.predict(features) > 0.5
