"""Contextual question-event telemetry and the §13.4 channel split (Checkpoint 4.6)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.schemas import TutorAnswer
from learnloop.db.repositories import Repository
from learnloop.services.question_signal import _apply_question_channels, apply_question_observation
from learnloop.services.tutor_qa import ask_question
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, create_basic_vault

CLOCK = FrozenClock(NOW)


class FakeTutorClient:
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-model"

    def __init__(self, *, question_channel="epistemic", question_type="mechanism"):
        self.question_channel = question_channel
        self.question_type = question_type

    def run_tutor_qa(self, context):
        return TutorAnswer(
            answer_md="Think about the factor shapes.",
            question_type=self.question_type,
            facets=list(context.candidate_facets),
            question_channel=self.question_channel,
        )


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    return vault, repository


def test_question_context_fields_persist(tmp_path):
    vault, repository = _setup(tmp_path)
    result = ask_question(
        vault,
        repository,
        FakeTutorClient(),
        context="practice",
        question_md="Why are the singular vectors orthogonal?",
        practice_item_id="pi_svd_define_001",
        session_id="sess_1",
        seconds_into_attempt=42.0,
        question_context={
            "preceding_tutor_move": "elicit_reasoning",
            "scaffold_level": "minimal",
            "warning_state": "none",
            "learner_mode": "practice",
            "question_opportunity": "mid_attempt",
            "hints_used_before": 1,
            "direct_explanation_request": False,
            "attempt_progress": "drafting",
        },
        clock=CLOCK,
    )
    event = repository.question_event(result["event_id"])
    assert event["preceding_tutor_move"] == "elicit_reasoning"
    assert event["scaffold_level"] == "minimal"
    assert event["warning_state"] == "none"
    assert event["learner_mode"] == "practice"
    assert event["question_opportunity"] == "mid_attempt"
    assert event["hints_used_before"] == 1
    assert event["direct_explanation_request"] is False
    assert event["attempt_progress"] == "drafting"
    assert event["signal_channel"] == "epistemic"
    assert result["signal_channel"] == "epistemic"


def test_classifier_channel_is_persisted(tmp_path):
    vault, repository = _setup(tmp_path)
    result = ask_question(
        vault,
        repository,
        FakeTutorClient(question_channel="interaction_preference", question_type="other"),
        context="practice",
        question_md="Can you explain it more simply?",
        practice_item_id="pi_svd_define_001",
        session_id="sess_1",
        clock=CLOCK,
    )
    assert repository.question_event(result["event_id"])["signal_channel"] == "interaction_preference"


def test_direct_explanation_request_forces_preference_channel(tmp_path):
    vault, repository = _setup(tmp_path)
    result = ask_question(
        vault,
        repository,
        FakeTutorClient(question_channel="epistemic"),  # classifier disagrees
        context="practice",
        question_md="Just tell me the answer.",
        practice_item_id="pi_svd_define_001",
        session_id="sess_1",
        question_context={"direct_explanation_request": True},
        clock=CLOCK,
    )
    assert repository.question_event(result["event_id"])["signal_channel"] == "interaction_preference"


def test_preference_channel_gets_damped_mastery_likelihood():
    """§13.4: a preference question moves the facet marginal less than an
    epistemic one; damping 0 removes the mastery effect entirely."""

    marginal = {"facet_solid:recall": 0.5, "facet_absent:recall": 0.5}
    ratio = 0.45

    epistemic = _apply_question_channels(
        dict(marginal), [{"signal_channel": "epistemic"}], [], ratio, 1.0, preference_damping=0.4
    )
    preference = _apply_question_channels(
        dict(marginal),
        [{"signal_channel": "interaction_preference"}],
        [],
        ratio,
        1.0,
        preference_damping=0.4,
    )
    disabled = _apply_question_channels(
        dict(marginal),
        [{"signal_channel": "interaction_preference"}],
        [],
        ratio,
        1.0,
        preference_damping=0.0,
    )

    assert epistemic["facet_solid:recall"] < preference["facet_solid:recall"] < 0.5
    assert disabled == pytest.approx(marginal)
    # The damped ratio composes exactly: ratio' = 1 - (1 - ratio) * damping.
    expected = apply_question_observation(
        dict(marginal), solid_likelihood_ratio=1.0 - (1.0 - ratio) * 0.4
    )
    assert preference == pytest.approx(expected)


def test_unclassified_events_keep_full_likelihood():
    marginal = {"facet_solid:recall": 0.5, "facet_absent:recall": 0.5}
    legacy = _apply_question_channels(
        dict(marginal), [{}], [], 0.45, 1.0, preference_damping=0.4
    )
    expected = apply_question_observation(dict(marginal), solid_likelihood_ratio=0.45)
    assert legacy == pytest.approx(expected)
