from types import SimpleNamespace

import pytest

from learnloop.curriculum.confusable_concepts import learner_observed_confusable_concepts
from learnloop.diagnosis.probes import Hypothesis


class _Repository:
    def probe_episodes_for_learning_object(self, learning_object_id):
        assert learning_object_id == "lo_target"
        return [
            SimpleNamespace(
                id="episode_1",
                completed_at="2026-07-14T12:00:00Z",
                updated_at="2026-07-14T12:00:00Z",
                created_at="2026-07-14T11:00:00Z",
            )
        ]


def test_repeated_probe_evidence_promotes_learner_observed_confusable(monkeypatch):
    vault = SimpleNamespace(
        learning_objects={"lo_target": SimpleNamespace(concept="concept_target")},
        concepts={"concept_target": object(), "concept_neighbor": object()},
    )
    hypothesis = Hypothesis(
        label="confuses_with:concept_neighbor",
        source_concept_id="concept_neighbor",
    )
    posterior = SimpleNamespace(
        hypothesis_set=SimpleNamespace(hypotheses=[hypothesis]),
        posterior={hypothesis.label: 0.72},
        prior={hypothesis.label: 0.30},
        qualifying_observations=3,
    )
    monkeypatch.setattr(
        "learnloop.curriculum.confusable_concepts.episode_posterior",
        lambda _vault, _repository, _episode: posterior,
    )

    observed = learner_observed_confusable_concepts(vault, _Repository(), "lo_target")

    assert len(observed) == 1
    assert observed[0].concept_id == "concept_neighbor"
    assert observed[0].probability == pytest.approx(0.72)
    assert observed[0].prior_probability == pytest.approx(0.30)
    assert observed[0].evidence_count == 3


def test_single_observation_does_not_promote_confusable(monkeypatch):
    vault = SimpleNamespace(
        learning_objects={"lo_target": SimpleNamespace(concept="concept_target")},
        concepts={"concept_target": object(), "concept_neighbor": object()},
    )
    hypothesis = Hypothesis(
        label="confuses_with:concept_neighbor",
        source_concept_id="concept_neighbor",
    )
    posterior = SimpleNamespace(
        hypothesis_set=SimpleNamespace(hypotheses=[hypothesis]),
        posterior={hypothesis.label: 0.90},
        prior={hypothesis.label: 0.30},
        qualifying_observations=1,
    )
    monkeypatch.setattr(
        "learnloop.curriculum.confusable_concepts.episode_posterior",
        lambda _vault, _repository, _episode: posterior,
    )

    assert learner_observed_confusable_concepts(vault, _Repository(), "lo_target") == []
