"""Slice 3 of the remediation redesign: joint candidate drafting, the question
join, post-reveal admissibility, and eliciting repair.

The unifying claim under test is an epistemic one, not a plumbing one: WHO
produced a piece of evidence, and WHEN relative to what we showed them, decides
what it may be used for. Free-text candidate causes may say anything; verbalized
weights are priors and never measurements; a production after a reveal is not
independent; a question the learner typed before the answer existed still is.
"""

from __future__ import annotations

import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.schemas import (
    ELICITING_REVEAL_BUDGET_DEFAULT,
    CandidateCause,
    GradingProposal,
    RepairSuggestion,
    TutorAnswer,
)
from learnloop.db.repositories import (
    OBSERVATION_CHANNEL_LEARNER_QUESTION,
    Repository,
)
from learnloop.services.causal_attribution import (
    ELICITING_RESPONSE_REASON,
    append_dialogue_candidate,
    hypothesis_mechanism_projection,
    normalized_prior_weights,
    record_eliciting_response,
)
from learnloop.services.causal_orchestrator import (
    record_learner_embedded_prediction,
)
from learnloop.services.causal_probe_coherence import build_causal_hypothesis_set
from learnloop.services.error_taxonomy_map import project_mechanism
from learnloop.services.reveal_ledger import production_admissibility, record_reveal
from learnloop.services.tutor_qa import ask_question
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault


# --- wire schema: additive, legacy-tolerant ---------------------------------


def test_candidate_cause_round_trips_new_fields_and_accepts_legacy_payloads():
    rich = CandidateCause.model_validate(
        {
            "statement": "believes the transpose is optional in the factorization",
            "cause_scope": "learner_state",
            "prior_weight": 3.0,
            "discriminating_predictions": [
                "if true, we'd see the same omission on a 2x2 item",
            ],
            "mechanism": "conceptual_error",
        }
    )
    assert rich.prior_weight == 3.0
    assert len(rich.discriminating_predictions) == 1
    assert rich.model_dump(mode="json")["mechanism"] == "conceptual_error"

    # A payload from before slice 3 — no weight, no predictions, no label.
    legacy = CandidateCause.model_validate(
        {"statement": "mixed up the two conventions", "cause_scope": "unknown"}
    )
    assert legacy.prior_weight is None
    assert legacy.discriminating_predictions == []
    assert legacy.mechanism is None


def test_tutor_answer_round_trips_extraction_fields_and_legacy_payloads():
    rich = TutorAnswer.model_validate(
        {
            "answer_md": "Because the sum is unchanged by that substitution.",
            "embedded_prediction": (
                "learner expects replacing (x+y)e2 with ((x+y)/2)e2 to change the sum"
            ),
            "new_candidate_cause": {
                "statement": "thinks scaling one basis coefficient rescales the vector",
                "cause_scope": "learner_state",
            },
        }
    )
    assert rich.new_candidate_cause is not None
    assert rich.new_candidate_cause.statement.startswith("thinks scaling")

    legacy = TutorAnswer.model_validate({"answer_md": "Here is the idea."})
    assert legacy.embedded_prediction is None
    assert legacy.new_candidate_cause is None


def test_grading_proposal_accepts_a_candidate_set_with_weights():
    proposal = GradingProposal.model_validate(
        {
            "attempt_id": "att_gp",
            "practice_item_id": "pi_svd_define_001",
            "rubric_score": 0.0,
            "grader_confidence": 0.9,
            "diagnosis_md": "The final factor is not transposed.",
            "error_attributions": [
                {
                    "error_type": "conceptual_slip",
                    "evidence": "Q appears where Q^T was required.",
                    "candidate_causes": [
                        {
                            "statement": "believes Q and Q^T are interchangeable here",
                            "cause_scope": "learner_state",
                            "prior_weight": 0.6,
                            "discriminating_predictions": ["would also drop it on 2x2"],
                        },
                        {
                            "statement": "copied the formula from a source that omits it",
                            "cause_scope": "interaction_context",
                            "prior_weight": 0.4,
                        },
                    ],
                }
            ],
        }
    )
    causes = proposal.error_attributions[0].candidate_causes
    assert [cause.prior_weight for cause in causes] == [0.6, 0.4]


# --- weights are priors, normalized server-side ------------------------------


def test_prior_weights_normalize_and_absent_weights_fall_back_to_uniform():
    stated, basis = normalized_prior_weights(
        [{"prior_weight": 3.0}, {"prior_weight": 1.0}]
    )
    assert basis == "model_verbalized"
    assert stated == pytest.approx([0.75, 0.25])
    assert sum(stated) == pytest.approx(1.0)

    # Every pre-slice-3 payload lands here, and behaves exactly as before.
    absent, absent_basis = normalized_prior_weights([{}, {}, {}])
    assert absent_basis == "uniform_no_weights"
    assert absent == pytest.approx([1 / 3, 1 / 3, 1 / 3])

    # A silent candidate takes the MEAN of the stated ones: neutral, neither
    # promoted nor buried by the grader's failure to rank it.
    partial, partial_basis = normalized_prior_weights(
        [{"prior_weight": 3.0}, {"prior_weight": 1.0}, {}]
    )
    assert partial_basis == "model_verbalized_partial"
    assert partial[2] == pytest.approx(2.0 / 6.0)
    assert sum(partial) == pytest.approx(1.0)

    # All-zero is "no opinion", not "everything is impossible".
    zeros, zero_basis = normalized_prior_weights(
        [{"prior_weight": 0.0}, {"prior_weight": 0.0}]
    )
    assert zero_basis == "uniform_no_weights"
    assert zeros == pytest.approx([0.5, 0.5])
    assert normalized_prior_weights([]) == ([], "uniform_no_weights")


# --- mechanism projection is post-hoc and never a gate -----------------------


def test_mechanism_projection_prefers_the_model_label_then_falls_open_set():
    assert project_mechanism(declared="conceptual_error") == (
        "conceptual_schema_error",
        "model_declared",
    )
    # No label from the model: fall back to the hosting event's error type.
    assert project_mechanism(error_type="arithmetic_slip") == (
        "local_slip",
        "error_event_type",
    )
    # A vault-specific id is not in the canonical nine and does not become one.
    assert project_mechanism(error_type="vault_specific_thing") == (None, "open_set")
    assert project_mechanism() == (None, "open_set")


def test_a_nonsense_candidate_statement_is_never_rejected(tmp_path):
    """The load-bearing negative. Free text means free text.

    A candidate whose statement fits no taxonomy, names no facet and reads like
    noise must still be stored, weighted and probeable. The projection reports
    that it could not name a mechanism; it does not get a vote on whether the
    candidate exists.
    """

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _insert_attempt(repository, attempt_id="att_nonsense")

    hypothesis = append_dialogue_candidate(
        vault,
        repository,
        attempt_id="att_nonsense",
        candidate={
            "statement": "the wobbulator was set to purple on tuesdays",
            "cause_scope": "unknown",
            "prior_weight": 2.0,
            "discriminating_predictions": ["would recur only on tuesdays"],
        },
        question_event_id="qe_nonsense",
        remediation_episode_id="ep_nonsense",
        clock=FrozenClock(NOW),
    )

    assert hypothesis is not None
    assert hypothesis["statement"] == "the wobbulator was set to purple on tuesdays"
    assert hypothesis_mechanism_projection(hypothesis) == (None, "open_set")
    # Open-set projection is NOT the open-set hypothesis ARM: the candidate is a
    # concrete claim about the learner, and conflating the two would delete it
    # from every consumer that projects only concrete heads.
    assert hypothesis["status"] == "candidate"
    assert hypothesis["evidence"]["discriminating_predictions"] == [
        "would recur only on tuesdays"
    ]


# --- the probe lane seeds its prior from the verbalized weights --------------


def _seed_weighted_factor(
    repository: Repository, *, weights: tuple[float | None, float | None]
) -> tuple[str, str, str]:
    common = {
        "attempt_id": "att_weighted",
        "learning_object_id": "lo_svd_definition",
        "cause_scope": "learner_state",
        "target_ref": {"kind": "criterion", "criterion_id": "correctness"},
        "applicability": {"practice_item_id": "pi_svd_define_001"},
        "postdictive_claims": [],
        "status": "candidate",
        "clock": FrozenClock(NOW),
    }
    first = repository.append_causal_hypothesis(
        **common,
        episode_key="att_weighted:first",
        statement="The transpose rule was not available.",
        statement_normalized="the transpose rule was not available",
        operation="recall_omission",
        repair_class_id="repair:recall",
        evidence=({} if weights[0] is None else {"prior_weight": weights[0]}),
    )
    second = repository.append_causal_hypothesis(
        **common,
        episode_key="att_weighted:second",
        statement="The learner selected the wrong factorization convention.",
        statement_normalized="the learner selected the wrong factorization convention",
        operation="method_selection",
        repair_class_id="repair:method",
        evidence=({} if weights[1] is None else {"prior_weight": weights[1]}),
    )
    factor_id = repository.insert_unresolved_cause_factor(
        attempt_id="att_weighted",
        candidate_causes=[
            {"hypothesis_id": first["id"], "version": first["version"]},
            {"hypothesis_id": second["id"], "version": second["version"]},
            {"hypothesis_id": "H_OTHER", "open_set": True},
        ],
        algorithm_version="causal_attribution_p2",
        clock=FrozenClock(NOW),
    )
    return factor_id, str(first["id"]), str(second["id"])


def test_hypothesis_set_prior_seeds_from_verbalized_weights(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    factor_id, first_id, second_id = _seed_weighted_factor(
        repository, weights=(0.8, 0.2)
    )

    plan = build_causal_hypothesis_set(repository, factor_id)
    assert plan.prior_basis == "model_verbalized_prior"
    assert plan.prior[first_id] > plan.prior[second_id]
    assert sum(plan.prior.values()) == pytest.approx(1.0)

    # A MEASURED support score still outranks a stated one: the grader's
    # ranking is a claim, and evidence beats a claim.
    measured = build_causal_hypothesis_set(
        repository, factor_id, support_scores={first_id: 0.1, second_id: 0.9}
    )
    assert measured.prior_basis == "support_weighted"
    assert measured.prior[second_id] > measured.prior[first_id]


def test_hypothesis_set_prior_stays_uniform_without_weights(tmp_path):
    """Backward compatibility: hypotheses drafted before slice 3."""

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    factor_id, first_id, second_id = _seed_weighted_factor(
        repository, weights=(None, None)
    )

    plan = build_causal_hypothesis_set(repository, factor_id)
    assert plan.prior_basis == "uniform_fallback"
    assert plan.prior[first_id] == pytest.approx(plan.prior[second_id])


# --- the question join -------------------------------------------------------


class _JoinTutorClient:
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-model"

    def __init__(self, **answer_kwargs):
        self.answer_kwargs = answer_kwargs

    def run_tutor_qa(self, context):
        return TutorAnswer(
            answer_md="Consider what the substitution does to the sum.",
            question_type="mechanism",
            facets=[],
            **self.answer_kwargs,
        )


def _insert_attempt(repository: Repository, *, attempt_id: str, primed: int = 0) -> None:
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO practice_attempts(
              id, practice_item_id, learning_object_id, practice_mode, attempt_type,
              learner_answer_md, hints_used, created_at, session_id, primed
            )
            VALUES (?, 'pi_svd_define_001', 'lo_svd_definition', 'short_answer',
                    'independent_attempt', 'my answer', 0, ?, 'sess_join', ?)
            """,
            (attempt_id, NOW_ISO, primed),
        )
        connection.commit()


def _open_factor(repository: Repository, attempt_id: str) -> str:
    hypothesis = repository.append_causal_hypothesis(
        episode_key=f"{attempt_id}:seed",
        attempt_id=attempt_id,
        learning_object_id="lo_svd_definition",
        cause_scope="learner_state",
        statement="The transpose rule was not available.",
        statement_normalized="the transpose rule was not available",
        applicability={"practice_item_id": "pi_svd_define_001"},
        status="candidate",
        clock=FrozenClock(NOW),
    )
    return repository.insert_unresolved_cause_factor(
        attempt_id=attempt_id,
        candidate_causes=[
            {"hypothesis_id": hypothesis["id"], "version": hypothesis["version"]},
            {"hypothesis_id": "H_OTHER", "open_set": True},
        ],
        algorithm_version="causal_attribution_p2",
        clock=FrozenClock(NOW),
    )


def _ask(tmp_path, monkeypatch, client, attempt_id="att_join"):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _insert_attempt(repository, attempt_id=attempt_id)
    factor_id = _open_factor(repository, attempt_id)
    # The join keys on the question being asked INSIDE a repair episode. Pinning
    # the attribution here keeps this test about the join rather than about the
    # episode-binding rules, which `test_reveal_ledger` already covers.
    import learnloop.services.tutor_qa as tutor_qa

    monkeypatch.setattr(tutor_qa, "reveal_episode_id", lambda *a, **k: "ep_join")
    result = ask_question(
        vault,
        repository,
        client,
        context="feedback",
        question_md="Doesn't halving that coefficient change the sum?",
        attempt_id=attempt_id,
        clock=FrozenClock(NOW),
    )
    return vault, repository, factor_id, result


def test_question_join_records_prediction_and_appends_a_dialogue_hypothesis(
    tmp_path, monkeypatch
):
    client = _JoinTutorClient(
        embedded_prediction=(
            "learner expects halving one basis coefficient to change the sum"
        ),
        new_candidate_cause=CandidateCause(
            statement="thinks basis coefficients scale the vector's magnitude",
            cause_scope="learner_state",
            prior_weight=1.0,
        ),
    )
    vault, repository, factor_id, _ = _ask(tmp_path, monkeypatch, client)

    observations = repository.causal_discriminating_observations(factor_id=factor_id)
    assert len(observations) == 1
    observation = observations[0]
    assert observation["channel"] == OBSERVATION_CHANNEL_LEARNER_QUESTION
    assert observation["feature_source"] == "learner_declared"
    assert observation["observed_features"]["embedded_prediction"].startswith(
        "learner expects halving"
    )
    # Recorded, never admitted: nothing was classified, so it grants no
    # authority and closes nothing.
    assert observation["admitted"] is False
    assert observation["resolved_factor"] is False
    assert observation["admission_reason"] == "learner_question_embedded_prediction"
    # ...and yet admissible as INDEPENDENT: the question predates the answer.
    assert observation["admissible_as_independent"] is True
    assert observation["detail"]["cost_free"] is True

    # A probe-channel reader must not see it at all.
    assert (
        repository.causal_discriminating_observations(probe_channel_only=True) == []
    )

    hypotheses = repository.causal_hypotheses_for_attempt("att_join")
    dialogue = [
        value for value in hypotheses if ":question:" in str(value["episode_key"])
    ]
    assert len(dialogue) == 1
    assert dialogue[0]["statement"].startswith("thinks basis coefficients")
    assert dialogue[0]["evidence"]["channel"] == "learner_question_dialogue"
    # The `mechanism` COLUMN belongs to the learned taxonomy and stays untouched.
    assert dialogue[0]["mechanism"] is None


def test_question_join_is_silent_when_the_tutor_extracts_nothing(tmp_path, monkeypatch):
    vault, repository, factor_id, _ = _ask(tmp_path, monkeypatch, _JoinTutorClient())

    assert repository.causal_discriminating_observations(factor_id=factor_id) == []
    assert not [
        value
        for value in repository.causal_hypotheses_for_attempt("att_join")
        if ":question:" in str(value["episode_key"])
    ]


def test_question_join_never_fails_the_learners_answer(tmp_path, monkeypatch):
    """Best-effort means best-effort: bookkeeping cannot cost an answer."""

    import learnloop.services.causal_orchestrator as orchestrator

    def _boom(*args, **kwargs):
        raise RuntimeError("ledger exploded")

    monkeypatch.setattr(
        orchestrator, "record_learner_embedded_prediction", _boom
    )
    client = _JoinTutorClient(embedded_prediction="learner expects X")
    _, repository, factor_id, result = _ask(tmp_path, monkeypatch, client)

    assert result["answer_md"]
    assert repository.causal_discriminating_observations(factor_id=factor_id) == []


def test_embedded_prediction_is_idempotent_per_question(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _insert_attempt(repository, attempt_id="att_idem")
    factor_id = _open_factor(repository, "att_idem")

    for _ in range(2):
        record_learner_embedded_prediction(
            repository,
            factor_id=factor_id,
            prediction="learner expects the sum to change",
            question_event_id="qe_idem",
            attempt_id="att_idem",
            clock=FrozenClock(NOW),
        )
    assert len(repository.causal_discriminating_observations(factor_id=factor_id)) == 1


# --- post-reveal admissibility ----------------------------------------------


def test_a_production_after_a_reveal_is_not_independent(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)

    clean = production_admissibility(
        repository,
        practice_item_id="pi_svd_define_001",
        learning_object_id="lo_svd_definition",
        produced_at="2026-05-19T12:00:00Z",
    )
    assert clean.admissible is True
    assert clean.reason is None

    reveal_id = record_reveal(
        repository,
        practice_item_id="pi_svd_define_001",
        learning_object_id="lo_svd_definition",
        source_kind="repair_display",
        amount=0.6,
        clock=FrozenClock(NOW),
    )
    contaminated = production_admissibility(
        repository,
        practice_item_id="pi_svd_define_001",
        learning_object_id="lo_svd_definition",
        produced_at="2026-05-19T12:00:00Z",
    )
    assert contaminated.admissible is False
    assert contaminated.reason == "post_reveal_not_independent"
    assert contaminated.reveal_event_id == reveal_id
    assert contaminated.reveal_amount == pytest.approx(0.6)

    # A production BEFORE the reveal is untouched by it.
    earlier = production_admissibility(
        repository,
        practice_item_id="pi_svd_define_001",
        learning_object_id="lo_svd_definition",
        produced_at="2026-05-17T12:00:00Z",
    )
    assert earlier.admissible is True


def test_a_reveal_on_a_sibling_item_of_the_same_lo_still_contaminates(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    record_reveal(
        repository,
        practice_item_id="pi_some_sibling",
        learning_object_id="lo_svd_definition",
        source_kind="tutor_answer",
        amount=0.4,
        clock=FrozenClock(NOW),
    )
    result = production_admissibility(
        repository,
        practice_item_id="pi_svd_define_001",
        learning_object_id="lo_svd_definition",
        produced_at="2026-05-19T12:00:00Z",
    )
    assert result.admissible is False


def test_an_embedded_prediction_stays_admissible_after_a_reveal(tmp_path):
    """The asymmetry that makes the whole channel worth having."""

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _insert_attempt(repository, attempt_id="att_after_reveal")
    factor_id = _open_factor(repository, "att_after_reveal")
    record_reveal(
        repository,
        practice_item_id="pi_svd_define_001",
        learning_object_id="lo_svd_definition",
        source_kind="repair_display",
        amount=0.9,
        clock=FrozenClock(NOW),
    )

    observation = record_learner_embedded_prediction(
        repository,
        factor_id=factor_id,
        prediction="learner expects the two factorizations to agree",
        question_event_id="qe_after_reveal",
        attempt_id="att_after_reveal",
        clock=FrozenClock(NOW),
    )
    assert observation is not None
    assert observation["admissible_as_independent"] is True
    assert observation["inadmissibility_reason"] is None


# --- eliciting repair --------------------------------------------------------


def test_eliciting_operator_validation_is_structural_only():
    # Structural: an elicit_* operator must carry the question it promises.
    with pytest.raises(ValueError):
        RepairSuggestion(
            practice_mode="targeted_review",
            rationale="Make the belief speak.",
            operator="elicit_belief_contrast",
        )

    elicited = RepairSuggestion(
        practice_mode="targeted_review",
        rationale="Make the belief speak.",
        operator="elicit_belief_contrast",
        eliciting_question="What happens to the sum if you halve that coefficient?",
        expected_response_contract="Names the sum as unchanged and says why.",
    )
    assert elicited.answer_reveal_budget == ELICITING_REVEAL_BUDGET_DEFAULT
    assert "answer_reveal_budget" in elicited.model_fields_set

    # An explicit budget is the grader's to set; the default never overrides it.
    explicit = RepairSuggestion(
        practice_mode="targeted_review",
        rationale="Make the belief speak.",
        operator="elicit_belief_contrast",
        eliciting_question="Why?",
        answer_reveal_budget=0.3,
    )
    assert explicit.answer_reveal_budget == 0.3

    # NOTHING enforces the mechanism -> shape mapping. A spliced repair for a
    # conceptual error is legal, and so is an eliciting question for a slip:
    # the prompt states the default, the grader decides.
    spliced = RepairSuggestion(
        practice_mode="targeted_review",
        rationale="Just fix the sign.",
        operator="insert_transpose",
        eliciting_question=None,
    )
    assert spliced.eliciting_question is None


def test_submit_eliciting_response_records_a_factor_response(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _insert_attempt(repository, attempt_id="att_elicit")
    factor_id = _open_factor(repository, "att_elicit")

    result = record_eliciting_response(
        vault,
        repository,
        attempt_id="att_elicit",
        suggestion_index=0,
        response_md="The sum is unchanged because e2's coefficient is halved twice.",
        clock=FrozenClock(NOW),
    )

    assert result["factor_id"] == factor_id
    assert result["admissible_as_independent"] is True
    reports = repository.causal_attribution_reports_for_factor(factor_id)
    assert len(reports) == 1
    assert reports[0]["response"] == ELICITING_RESPONSE_REASON
    payload = json.loads(reports[0]["payload_json"])
    assert payload["suggestion_index"] == 0
    assert payload["response_md"].startswith("The sum is unchanged")
    assert payload["admissible_as_independent"] is True


def test_an_eliciting_response_after_a_reveal_is_recorded_but_not_independent(
    tmp_path,
):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _insert_attempt(repository, attempt_id="att_elicit_dirty")
    factor_id = _open_factor(repository, "att_elicit_dirty")
    record_reveal(
        repository,
        practice_item_id="pi_svd_define_001",
        learning_object_id="lo_svd_definition",
        source_kind="repair_display",
        amount=0.7,
        clock=FrozenClock(NOW),
    )

    result = record_eliciting_response(
        vault,
        repository,
        attempt_id="att_elicit_dirty",
        suggestion_index=1,
        response_md="It stays the same.",
        clock=FrozenClock(NOW),
    )
    assert result["admissible_as_independent"] is False
    assert result["inadmissibility_reason"] == "post_reveal_not_independent"
    # Contamination does not erase the learner's engagement.
    assert len(repository.causal_attribution_reports_for_factor(factor_id)) == 1


def test_an_empty_eliciting_response_is_refused(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _insert_attempt(repository, attempt_id="att_elicit_empty")
    _open_factor(repository, "att_elicit_empty")

    with pytest.raises(ValueError):
        record_eliciting_response(
            vault,
            repository,
            attempt_id="att_elicit_empty",
            suggestion_index=0,
            response_md="   ",
            clock=FrozenClock(NOW),
        )


# --- the sidecar seam --------------------------------------------------------


def _call(ctx, name: str, params: dict):
    import learnloop_sidecar.handlers  # noqa: F401 - register methods
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def test_submit_eliciting_response_sidecar_method(tmp_path):
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.errors import SidecarError

    root = create_basic_vault(tmp_path / "vault").root
    ctx = SidecarContext()
    ctx.load(root)
    _vault, repository = ctx.require_vault()
    _insert_attempt(repository, attempt_id="att_rpc")
    factor_id = _open_factor(repository, "att_rpc")

    result = _call(
        ctx,
        "submit_eliciting_response",
        {
            "attemptId": "att_rpc",
            "suggestionIndex": 0,
            "responseMd": "The sum does not change.",
        },
    )
    assert result["factorId"] == factor_id
    assert result["admissibleAsIndependent"] is True
    # The feedback bundle rides along so the screen can re-render in one call.
    assert "feedback" in result
    assert len(repository.causal_attribution_reports_for_factor(factor_id)) == 1

    with pytest.raises(SidecarError) as missing:
        _call(
            ctx,
            "submit_eliciting_response",
            {
                "attemptId": "att_nope",
                "suggestionIndex": 0,
                "responseMd": "anything",
            },
        )
    assert missing.value.code == "not_found"
