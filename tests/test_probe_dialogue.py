"""Dialogue microprobes: turn persistence and shared task evidence mass
(spec §8.1, §7.7, regression test 32)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.attempts import ApplyAttemptInput, AttemptDraft, ResolvedGrade, apply_attempt
from learnloop.services.probe_dialogue import (
    DialogueBlockState,
    begin_dialogue_block,
    end_dialogue_block,
    next_dialogue_turn,
    record_turn_submitted,
)
from learnloop.services.probe_episodes import enter_episode, episode_posterior
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, admit_probe_instrument_card, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
CLOCK = FrozenClock(NOW)


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository, items=(ITEM_ID,))
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    assert episode.status == "in_progress"
    return vault_root, loaded, repository, episode


def _grade(score: int) -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=score,
        criterion_points={"correctness": float(score)},
        evidence_rows=[],
        error_attributions=[],
        grader_confidence=1.0,
        confidence=4,
        manual_review_reason=None,
    )


def _submit_turn(vault_root, repository, turn, *, score: int = 4):
    loaded = load_vault(vault_root)
    return apply_attempt(
        loaded,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=turn["practice_item_id"],
                learner_answer_md="committed answer",
                attempt_type="diagnostic_probe",
                probe_presentation_id=turn["presentation_id"],
            ),
            attempt_id=new_ulid(),
            grade=_grade(score),
            grading_source="ai",
        ),
        clock=CLOCK,
    )


def test_dialogue_turns_persist_presentation_attempt_observation(tmp_path):
    vault_root, loaded, repository, episode = _setup(tmp_path)
    state = begin_dialogue_block(loaded, repository, LO_ID, clock=CLOCK)
    assert state.planned_kinds == ["commit", "reason", "counterfactual"]
    assert 0 < state.task_evidence_share <= 1.0 / len(state.planned_kinds) + 1e-9

    served = []
    for _ in range(len(state.planned_kinds)):
        loaded = load_vault(vault_root)
        state, turn = next_dialogue_turn(loaded, repository, state, clock=CLOCK)
        assert turn is not None
        served.append(turn)
        _submit_turn(vault_root, repository, turn)
        state = record_turn_submitted(state, turn["presentation_id"])

    loaded = load_vault(vault_root)
    state, done = next_dialogue_turn(loaded, repository, state, clock=CLOCK)
    assert done is None  # planned turns exhausted

    # One presentation, one diagnostic_probe attempt, one observation per turn.
    rows = repository.probe_observations_for_episode(episode.id)
    dialogue_rows = [
        row for row in rows if (row.get("selection_components") or {}).get("dialogue_block_id")
    ]
    assert len(dialogue_rows) == len(served)
    for row in dialogue_rows:
        assert row["attempt_type"] == "diagnostic_probe"
        observation = row["observation"]
        # §7.7: each turn's likelihood is damped by its committed share of the
        # block's bounded task evidence mass.
        assert observation.independent_evidence_discount <= state.task_evidence_share + 1e-9

    # §7.7 completion accounting: the whole block is ONE independent unit, so
    # three same-block turns cannot satisfy the two-observation minimum alone.
    refreshed = repository.probe_episode(episode.id)
    assert refreshed.status == "in_progress"
    posterior = episode_posterior(loaded, repository, refreshed)
    assert posterior.qualifying_observations == len(served)


def test_end_dialogue_block_invalidates_unsubmitted_turn_and_segments(tmp_path):
    vault_root, loaded, repository, episode = _setup(tmp_path)
    state = begin_dialogue_block(loaded, repository, LO_ID, clock=CLOCK)
    state, turn = next_dialogue_turn(loaded, repository, state, clock=CLOCK)
    assert turn is not None

    loaded = load_vault(vault_root)
    end_dialogue_block(loaded, repository, state, clock=CLOCK)
    presentation = repository.probe_presentation(turn["presentation_id"])
    assert presentation.status == "ended"
    assert presentation.end_reason == "invalidated"
    segments = repository.state_segments_for_learning_object(LO_ID)
    assert segments[-1].reason == "block_end"


def test_dialogue_state_round_trips_through_json(tmp_path):
    _vault_root, loaded, repository, _episode = _setup(tmp_path)
    state = begin_dialogue_block(loaded, repository, LO_ID, clock=CLOCK)
    restored = DialogueBlockState.from_json(state.to_json())
    assert restored.block_id == state.block_id
    assert restored.planned_kinds == state.planned_kinds
    assert restored.task_evidence_share == state.task_evidence_share


def test_second_dialogue_block_on_same_lo_can_open(tmp_path):
    """Every block re-mints the same parametric turn surfaces; the §5.4
    duplication gate must exempt ephemeral dialogue instances or a second
    block on the LO could never mint a turn."""

    vault_root, loaded, repository, episode = _setup(tmp_path)
    state = begin_dialogue_block(loaded, repository, LO_ID, clock=CLOCK)
    state, turn = next_dialogue_turn(loaded, repository, state, clock=CLOCK)
    assert turn is not None
    _submit_turn(vault_root, repository, turn)
    state = record_turn_submitted(state, turn["presentation_id"])
    loaded = load_vault(vault_root)
    end_dialogue_block(loaded, repository, state, clock=CLOCK)

    assert repository.open_probe_episode(LO_ID).status == "in_progress"
    loaded = load_vault(vault_root)
    state2 = begin_dialogue_block(loaded, repository, LO_ID, clock=CLOCK)
    state2, turn2 = next_dialogue_turn(loaded, repository, state2, clock=CLOCK)
    assert turn2 is not None
    assert turn2["practice_item_id"] != turn["practice_item_id"]
    assert turn2["kind"] == "commit"


class FakeDialogueClient:
    """AI provider double exposing run_probe_dialogue_turn."""

    model = "fake-dialogue-model"

    def __init__(self, *, error=False, leaky=False):
        self._error = error
        self._leaky = leaky
        self.contexts = []

    def run_probe_dialogue_turn(self, context):
        from learnloop.codex.client import CodexUnavailable
        from learnloop.codex.schemas import ProbeDialogueTurn

        self.contexts.append(context)
        if self._error:
            raise CodexUnavailable("provider down")
        if self._leaky:
            # Prompt equals expected answer: must be gate-rejected.
            return ProbeDialogueTurn(prompt_md="Leak.", expected_answer_md="Leak.")
        prior = context.prior_turns[-1]["learner_answer_md"] if context.prior_turns else None
        prompt = (
            f'You committed to "{prior}" about {context.learning_object_title} — '
            f"what is the single decisive reason it holds?"
            if prior
            else f"Commit to an answer: what is the key idea of {context.learning_object_title}?"
        )
        return ProbeDialogueTurn(
            prompt_md=prompt,
            expected_answer_md="A robust learner names the decisive reason.",
        )


def test_adaptive_llm_turn_conditions_on_prior_answers(tmp_path):
    vault_root, loaded, repository, _episode = _setup(tmp_path)
    client = FakeDialogueClient()
    state = begin_dialogue_block(loaded, repository, LO_ID, clock=CLOCK)

    state, first = next_dialogue_turn(loaded, repository, state, ai_client=client, clock=CLOCK)
    assert first is not None
    assert client.contexts[0].prior_turns == []
    assert "key idea" in first["prompt_md"]
    _submit_turn(vault_root, repository, first)
    state = record_turn_submitted(state, first["presentation_id"])

    loaded = load_vault(vault_root)
    state, second = next_dialogue_turn(loaded, repository, state, ai_client=client, clock=CLOCK)
    assert second is not None
    # §8.1: the reason turn conditions on the learner's committed answer.
    assert client.contexts[1].turn_kind == "reason"
    assert client.contexts[1].prior_turns[0]["learner_answer_md"] == "committed answer"
    assert 'You committed to "committed answer"' in second["prompt_md"]
    # Provenance: the turn instance links to the LLM generator.
    links = repository.probe_item_family_links(second["practice_item_id"])
    assert links[0].generator_id == "probe_family_llm"
    assert links[0].instance_metadata["generator_model"] == "fake-dialogue-model"


def test_adaptive_turn_falls_back_to_parametric_on_failure_or_leak(tmp_path):
    _vault_root, loaded, repository, _episode = _setup(tmp_path)
    for client in (FakeDialogueClient(error=True), FakeDialogueClient(leaky=True)):
        state = begin_dialogue_block(loaded, repository, LO_ID, clock=CLOCK)
        state, turn = next_dialogue_turn(loaded, repository, state, ai_client=client, clock=CLOCK)
        assert turn is not None
        # Parametric template served; provenance stays parametric.
        links = repository.probe_item_family_links(turn["practice_item_id"])
        assert links[0].generator_id == "probe_family_parametric"
        # Invalidate so the next iteration can reopen a block cleanly.
        end_dialogue_block(loaded, repository, state, clock=CLOCK)
