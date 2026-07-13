"""Redundancy penalty and precommitted joint blocks (Checkpoint 5.2/5.3, test 29)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.probe_episodes import (
    commit_presentation,
    eligible_instruments,
    enter_episode,
    episode_hypothesis_set,
    episode_posterior,
    plan_precommitted_block,
    serve_presentation,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item
from tests.helpers import NOW, NOW_ISO, admit_probe_instrument_card, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
ITEM_2 = "pi_svd_define_002"
ITEM_3 = "pi_svd_define_003"
CLOCK = FrozenClock(NOW)


def _add_item(vault_root, item_id: str, *, surface_family: str | None = None) -> None:
    upsert_practice_item(
        vault_root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "diagnostic_probe", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": f"Fresh-surface prompt for {item_id}.",
            "expected_answer": "A matrix factorization into U, Sigma, and V transpose.",
            "surface_family": surface_family,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [
                    {
                        "id": "conceptual_slip",
                        "description": "Confuses SVD with a different decomposition.",
                        "max_grade": 1,
                    }
                ],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )


def _setup(tmp_path, *, items=(ITEM_ID, ITEM_2)):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    for item_id, surface in (
        (ITEM_2, "fresh_surface"),
        (ITEM_3, "third_surface"),
    ):
        if item_id in items:
            _add_item(vault_root, item_id, surface_family=surface)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository, items=items)
    return loaded, repository


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


def _submit(loaded, repository, *, item_id, presentation_id, score=4):
    return apply_attempt(
        loaded,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="answer",
                attempt_type="diagnostic_probe",
                hints_used=0,
                probe_presentation_id=presentation_id,
            ),
            attempt_id=new_ulid(),
            grade=_grade(score),
            grading_source="ai",
        ),
        clock=CLOCK,
    )


# --- Redundancy penalty (Checkpoint 5.2) -----------------------------------------------


def test_family_redundancy_penalty_after_observation(tmp_path):
    loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)

    before = eligible_instruments(loaded, repository, episode)
    assert all(entry.redundancy_penalty == 1.0 for entry in before)

    hypothesis_set = episode_hypothesis_set(repository, episode)
    first = next(entry for entry in before if entry.item.id == ITEM_ID)
    presentation = commit_presentation(loaded, repository, episode, first, clock=CLOCK)
    serve_presentation(repository, presentation.id, clock=CLOCK)
    _submit(loaded, repository, item_id=ITEM_ID, presentation_id=presentation.id)

    episode = repository.probe_episode(episode.id)
    if episode.status != "in_progress":
        pytest.skip("episode completed after one observation; penalty unobservable")
    after = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)
    # The remaining candidate shares the observed family: penalized once, and
    # the penalty is a separate component — the EIG value itself is unpenalized.
    penalty = loaded.config.probe.block.family_redundancy_penalty
    for entry in after:
        assert entry.redundancy_penalty == pytest.approx(penalty)
        assert entry.selection_components()["redundancy_penalty"] == pytest.approx(penalty)


# --- Precommitted joint block (Checkpoint 5.3, §16 test 29) ------------------------------


def test_precommitted_block_commits_all_before_answers(tmp_path):
    loaded, repository = _setup(tmp_path, items=(ITEM_ID, ITEM_2, ITEM_3))
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)

    block = plan_precommitted_block(loaded, repository, episode, block_size=2, clock=CLOCK)
    assert len(block) == 2
    # All committed before any answer: both selected, distinct items/surfaces.
    assert {presentation.status for presentation in block} == {"selected"}
    assert len({presentation.practice_item_id for presentation in block}) == 2
    for index, presentation in enumerate(block):
        components = presentation.selection_components
        assert components["joint_block"] is True
        assert components["block_index"] == index
        assert components["conditional_eig"] > 0
    # Later picks condition on predicted (not observed) outcomes: the second
    # pick's conditional EIG is an expectation, at most its prior EIG.
    assert block[1].selection_components["conditional_eig"] <= (
        block[0].selection_components["conditional_eig"] + 1e-9
    )

    # The block is consumable in order through the normal submission path.
    serve_presentation(repository, block[0].id, clock=CLOCK)
    _submit(loaded, repository, item_id=block[0].practice_item_id, presentation_id=block[0].id)
    episode = repository.probe_episode(episode.id)
    if episode.status == "in_progress":
        serve_presentation(repository, block[1].id, clock=CLOCK)
        result = _submit(
            loaded, repository, item_id=block[1].practice_item_id, presentation_id=block[1].id
        )
        assert repository.probe_observation_for_attempt(result.attempt_id) is not None


def test_sequential_selection_conditions_on_observed_posterior(tmp_path):
    """§16 test 29: outside a precommitted block, selection is sequential and
    conditions on the observed posterior — the live ranking reflects the first
    observation instead of the entry prior."""

    loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    hypothesis_set = episode_hypothesis_set(repository, episode)

    entry_prior_ranked = eligible_instruments(
        loaded, repository, episode, hypothesis_set=hypothesis_set, posterior=hypothesis_set.prior
    )
    first = next(entry for entry in entry_prior_ranked if entry.item.id == ITEM_ID)
    presentation = commit_presentation(loaded, repository, episode, first, clock=CLOCK)
    serve_presentation(repository, presentation.id, clock=CLOCK)
    _submit(loaded, repository, item_id=ITEM_ID, presentation_id=presentation.id)

    episode = repository.probe_episode(episode.id)
    if episode.status != "in_progress":
        pytest.skip("episode completed after one observation")
    live = episode_posterior(loaded, repository, episode)
    sequential = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)
    conditioned = eligible_instruments(
        loaded, repository, episode, hypothesis_set=hypothesis_set, posterior=live.posterior
    )
    # The default path equals explicit conditioning on the live posterior.
    assert [entry.item.id for entry in sequential] == [entry.item.id for entry in conditioned]
    assert [entry.expected_information_gain for entry in sequential] == [
        entry.expected_information_gain for entry in conditioned
    ]
