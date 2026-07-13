"""§5.9 remainder, §6.5 re-probe triggers, and §7.1 answer confidence
(spec_probe_eig_redesign.md)."""

from __future__ import annotations

import io
import json
from datetime import timedelta

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.calibration_sessions import (
    episode_priority_disagreement,
    graph_propagated_prior,
)
from learnloop.services.probe_episodes import (
    commit_presentation,
    eligible_instruments,
    enter_episode,
    enter_stale_uncertainty_reprobes,
    episode_hypothesis_set,
    maybe_reprobe_for_predictive_failure,
    serve_presentation,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop_sidecar.server import serve

from tests.helpers import NOW, NOW_ISO, admit_probe_instrument_card, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
CLOCK = FrozenClock(NOW)


def _setup(tmp_path, *, with_card: bool = True):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    if with_card:
        admit_probe_instrument_card(repository)
    return vault_root, loaded, repository


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


def _submit(loaded, repository, *, score=4, attempt_type="independent_attempt",
            presentation_id=None, answer_confidence=None, session_id=None, clock=CLOCK):
    attempt_id = new_ulid()
    result = apply_attempt(
        loaded,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=ITEM_ID,
                learner_answer_md="answer",
                attempt_type=attempt_type,
                session_id=session_id,
                probe_presentation_id=presentation_id,
                answer_confidence=answer_confidence,
            ),
            attempt_id=attempt_id,
            grade=_grade(score),
            grading_source="ai",
        ),
        clock=clock,
    )
    return attempt_id, result


# --- §6.5 re-probe: repeated prediction errors --------------------------------------


def test_repeated_prediction_errors_reopen_probing(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode_config = loaded.config.probe.episode
    episode_config.reprobe_predictive_surprise_threshold = 0.0
    episode_config.reprobe_prediction_error_count = 2

    # A never-probed LO never re-enters through this trigger.
    assert maybe_reprobe_for_predictive_failure(loaded, repository, LO_ID, clock=CLOCK) is None

    first = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    repository.update_probe_episode_status(
        first.id, status="complete", completion_reason="decision_stable",
        completed_at=NOW_ISO, clock=CLOCK,
    )

    # A confident model of the learner: failures below are prediction errors.
    from learnloop.db.repositories import MasteryState

    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id=LO_ID,
            logit_mean=2.5,
            logit_variance=0.05,
            evidence_count=12,
            last_evidence_at=NOW_ISO,
            algorithm_version=loaded.config.algorithms.algorithm_version,
            updated_at=NOW_ISO,
        )
    )

    # Build up prediction errors: failed attempts against a healthy prior.
    negatives = 0
    for _ in range(4):
        attempt_id, _result = _submit(loaded, repository, score=0)
        surprise = repository.latest_attempt_surprise(attempt_id) or {}
        if surprise.get("surprise_direction") == "negative":
            negatives += 1
    assert negatives >= 2, "fixture did not produce negative prediction errors"

    reopened = maybe_reprobe_for_predictive_failure(loaded, repository, LO_ID, clock=CLOCK)
    assert reopened is not None
    assert reopened.trigger == "stale_uncertainty"
    assert reopened.id != first.id

    # Idempotent while the new episode is open.
    assert maybe_reprobe_for_predictive_failure(loaded, repository, LO_ID, clock=CLOCK) is None


# --- §6.5 re-probe: stale uncertainty ------------------------------------------------


def test_stale_uncertainty_reprobe_after_configured_days(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    sync_vault_state(loaded, repository, clock=CLOCK)  # seeds mastery states
    episode = repository.open_probe_episode(LO_ID) or enter_episode(
        loaded, repository, LO_ID, clock=CLOCK
    )
    repository.update_probe_episode_status(
        episode.id, status="complete", completion_reason="decision_stable",
        completed_at=NOW_ISO, clock=CLOCK,
    )

    # Not yet stale: nothing reopens.
    soon = FrozenClock(NOW + timedelta(days=3))
    assert enter_stale_uncertainty_reprobes(loaded, repository, clock=soon) == []

    later = FrozenClock(NOW + timedelta(days=40))
    opened = enter_stale_uncertainty_reprobes(loaded, repository, clock=later)
    assert [entry.learning_object_id for entry in opened] == [LO_ID]
    assert opened[0].trigger == "stale_uncertainty"
    assert opened[0].id != episode.id

    # Re-running does not stack episodes.
    assert enter_stale_uncertainty_reprobes(loaded, repository, clock=later) == []


def test_stale_uncertainty_respects_variance_floor(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    sync_vault_state(loaded, repository, clock=CLOCK)
    episode = repository.open_probe_episode(LO_ID) or enter_episode(
        loaded, repository, LO_ID, clock=CLOCK
    )
    repository.update_probe_episode_status(
        episode.id, status="complete", completion_reason="decision_stable",
        completed_at=NOW_ISO, clock=CLOCK,
    )
    loaded.config.probe.episode.reprobe_stale_uncertainty_variance = 99.0
    later = FrozenClock(NOW + timedelta(days=40))
    assert enter_stale_uncertainty_reprobes(loaded, repository, clock=later) == []


# --- §5.9/§6.4 planner disagreement ---------------------------------------------------


def test_disagreement_between_claim_and_observed_evidence(tmp_path):
    _, loaded, repository = _setup(tmp_path, with_card=False)
    sync_vault_state(loaded, repository, clock=CLOCK)

    # No claim yet: at most one signal exists.
    baseline = episode_priority_disagreement(loaded, repository, LO_ID)

    repository.insert_learner_claim(
        {
            "id": "claim_svd_confident",
            "claim_type": "self_rating",
            "scope_type": "learning_object",
            "scope_id": LO_ID,
            "evidence_family": "recall",
            "claimed_level": 0.95,
            "prior_pseudo_count": 4.0,
            "source": "manual_cli",
        },
        clock=CLOCK,
    )
    # Observed evidence that contradicts the confident claim.
    for _ in range(3):
        _submit(loaded, repository, score=0)

    disagreement = episode_priority_disagreement(loaded, repository, LO_ID)
    assert disagreement > baseline
    assert disagreement > 0.2


def test_graph_prior_absent_without_evidence_bearing_neighbors(tmp_path):
    _, loaded, repository = _setup(tmp_path, with_card=False)
    assert graph_propagated_prior(loaded, repository, LO_ID) is None


# --- §5.9 time-to-first-ordinary-practice ceiling (sidecar enforcement) --------------


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _probe_contract(vault_root) -> dict:
    return _rpc(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(vault_root)}},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "get_probe_contract",
                "params": {"practiceItemId": ITEM_ID},
            },
        ]
    )[1]["result"]


def test_onboarding_ceiling_deactivates_probes_until_practice_starts(tmp_path):
    vault_root, loaded, repository = _setup(tmp_path)
    config_path = vault_root / "learnloop.toml"
    config_path.write_text(
        config_path.read_text().replace(
            "onboarding_practice_ceiling_observations = 4",
            "onboarding_practice_ceiling_observations = 1",
        )
    )

    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    assert episode.status == "in_progress"
    hypothesis_set = episode_hypothesis_set(repository, episode)
    eligible = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)[0]
    presentation = commit_presentation(loaded, repository, episode, eligible, clock=CLOCK)
    serve_presentation(repository, presentation.id, clock=CLOCK)
    _submit(
        loaded, repository, score=4, attempt_type="diagnostic_probe",
        presentation_id=presentation.id,
    )
    assert repository.qualifying_probe_observation_count() == 1
    assert repository.ordinary_practice_attempt_count() == 0

    # Ceiling reached with zero ordinary practice: probes deactivate so the
    # learner reaches ordinary practice (§5.9).
    result = _probe_contract(vault_root)
    assert result["active"] is False
    assert result["reason"] == "onboarding_practice_ceiling"

    # Once ordinary practice has started the ceiling no longer applies (the
    # contract then proceeds to the grading-provider requirement).
    _submit(loaded, repository, score=3, attempt_type="independent_attempt")
    assert repository.ordinary_practice_attempt_count() == 1
    result = _probe_contract(vault_root)
    assert result.get("reason") != "onboarding_practice_ceiling"


# --- §5.9 routine per-session qualifying-observation cap (§16 test 36) ---------------


def test_session_cap_blocks_further_probe_serving(tmp_path):
    """The routine per-session cap gates serving on every surface: once a
    session has spent its qualifying observations, the shared gate returns
    session_cap_reached; other sessions and capless callers are unaffected."""

    from learnloop.services.probe_episodes import probe_serving_block_reason

    _, loaded, repository = _setup(tmp_path)
    loaded.config.probe.episode.session_qualifying_observation_cap = 1
    # Ordinary practice exists, so the onboarding ceiling is not in play.
    _submit(loaded, repository, score=3, attempt_type="independent_attempt")

    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    hypothesis_set = episode_hypothesis_set(repository, episode)
    eligible = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)[0]
    presentation = commit_presentation(loaded, repository, episode, eligible, clock=CLOCK)
    serve_presentation(repository, presentation.id, clock=CLOCK)
    _submit(
        loaded, repository, score=4, attempt_type="diagnostic_probe",
        presentation_id=presentation.id, session_id="sess_cap",
    )
    assert repository.qualifying_probe_observation_count_for_session("sess_cap") == 1

    assert (
        probe_serving_block_reason(loaded, repository, session_id="sess_cap")
        == "session_cap_reached"
    )
    # A different session has its own budget; a capless caller (no session)
    # and a lifted calibration session are not blocked.
    assert probe_serving_block_reason(loaded, repository, session_id="sess_other") is None
    assert probe_serving_block_reason(loaded, repository, session_id=None) is None
    assert (
        probe_serving_block_reason(loaded, repository, session_id="sess_cap", cap_lifted=True)
        is None
    )


# --- §5.9 routine planner, shadow mode (§13.3) ----------------------------------------


def _add_second_lo(vault_root):
    from learnloop.vault.paths import VaultPaths
    from tests.helpers import NOW_ISO, write_yaml

    loaded = load_vault(vault_root)
    paths = VaultPaths(loaded.root, loaded.config)
    write_yaml(
        paths.learning_object_path("linear-algebra", "lo_eigen_definition"),
        {
            "schema_version": 1,
            "id": "lo_eigen_definition",
            "title": "Eigendecomposition definition",
            "subjects": ["linear-algebra"],
            "concept": "singular_value_decomposition",
            "knowledge_type": "definition",
            "status": "active",
            "contradicts": None,
            "summary": "Eigendecomposition factorizes a matrix using its eigenvectors.",
            "prerequisites": [],
            "confusables": [],
            "difficulty_prior": 0.55,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_eigen_define_001"),
        {
            "schema_version": 1,
            "id": "pi_eigen_define_001",
            "learning_object_id": "lo_eigen_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Define eigendecomposition.",
            "expected_answer": "A factorization into eigenvectors and eigenvalues.",
            "difficulty": 0.55,
            "tags": [],
            "hints": [],
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [
                    {"id": "conceptual_slip", "description": "Confuses decompositions.", "max_grade": 1}
                ],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    return load_vault(vault_root)


def test_routine_planner_shadow_ranks_open_episodes(tmp_path):
    from learnloop.services.calibration_sessions import routine_planner_shadow
    from tests.helpers import admit_probe_instrument_card

    vault_root, loaded, repository = _setup(tmp_path)
    episode_one = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    # A single rankable episode is not a planning decision: no shadow logged.
    assert routine_planner_shadow(loaded, repository, episode_one.id) is None

    loaded = _add_second_lo(vault_root)
    admit_probe_instrument_card(
        repository,
        learning_object_id="lo_eigen_definition",
        card_id="card_eigen_contrast",
        items=("pi_eigen_define_001",),
    )
    episode_two = enter_episode(loaded, repository, "lo_eigen_definition", clock=CLOCK)
    assert episode_two.status == "in_progress"

    shadow = routine_planner_shadow(loaded, repository, episode_one.id)
    assert shadow is not None
    assert shadow["open_in_progress_episodes"] == 2
    assert 1 <= shadow["episode_rank_plain"] <= 2
    assert 1 <= shadow["episode_rank_boosted"] <= 2
    assert shadow["disagreement_weight"] == loaded.config.probe.calibration.disagreement_weight


def test_planner_shadow_report_summarizes_logged_components(tmp_path):
    from learnloop.services.probe_audit import planner_shadow_report
    from learnloop.services.probe_episodes import commit_item_presentation

    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    hypothesis_set = episode_hypothesis_set(repository, episode)
    item = loaded.practice_items[ITEM_ID]
    presentation = commit_item_presentation(
        loaded,
        repository,
        episode,
        item,
        hypothesis_set,
        extra_selection_components={
            "shadow_planner": {
                "episode_rank_plain": 1,
                "episode_rank_boosted": 2,
                "disagreement": 0.4,
                "disagreement_weight": 0.5,
                "open_in_progress_episodes": 2,
            }
        },
        clock=CLOCK,
    )
    _submit(
        loaded, repository, score=4, attempt_type="diagnostic_probe",
        presentation_id=presentation.id,
    )

    report = planner_shadow_report(repository)
    assert report["observations_with_planner_shadow"] == 1
    assert report["plain_top_rate"] == 1.0
    assert report["boosted_agreement_rate"] == 0.0
    assert report["mean_realized_when_boosted_differed"] is not None


# --- §7.1 answer confidence (logged-only) ---------------------------------------------


def test_answer_confidence_is_logged_on_attempt_and_observation(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    hypothesis_set = episode_hypothesis_set(repository, episode)
    eligible = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)[0]
    presentation = commit_presentation(loaded, repository, episode, eligible, clock=CLOCK)
    serve_presentation(repository, presentation.id, clock=CLOCK)

    attempt_id, _result = _submit(
        loaded, repository, score=4, attempt_type="diagnostic_probe",
        presentation_id=presentation.id, answer_confidence=2,
    )
    attempt = repository.fetch_practice_attempt(attempt_id)
    assert attempt["answer_confidence"] == 2

    observation = repository.probe_observation_for_attempt(attempt_id)
    assert observation is not None
    features = observation.features or {}
    assert features.get("answer_confidence") == 2
    # Latency is derivable from presentation timestamps (§7.1).
    assert "presentation_latency_seconds" in features


def test_answer_confidence_out_of_range_is_rejected(tmp_path):
    _, loaded, repository = _setup(tmp_path)
    import pytest
    from learnloop.services.attempts import AttemptValidationError

    with pytest.raises(AttemptValidationError):
        apply_attempt(
            loaded,
            repository,
            ApplyAttemptInput(
                draft=AttemptDraft(
                    practice_item_id=ITEM_ID,
                    learner_answer_md="answer",
                    attempt_type="independent_attempt",
                    answer_confidence=9,
                ),
                attempt_id=new_ulid(),
                grade=_grade(4),
                grading_source="ai",
            ),
            clock=CLOCK,
        )
