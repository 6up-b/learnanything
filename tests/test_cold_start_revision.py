"""Cold-start revision: deterministic grading, soft-y lane split, claim
re-anchoring, decision-equivalence stopping primitives, stratified EIG pool."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.services.grading import deterministic_recognition_grade
from learnloop.services.mastery import (
    MasteryObservation,
    MasteryState,
    apply_claim_evidence,
    sigmoid,
    update_mastery_traced,
)
from learnloop.config import LearnLoopConfig
from learnloop.services.predictive_eig import _stratified_cap, TargetItemModel
from learnloop.services.probe_hypotheses import triage_reason_for_label
from learnloop.vault.models import PracticeItem, Rubric, RubricCriterion


def _mc_item(**overrides):
    payload = dict(
        id="pi_mc_01",
        learning_object_id="lo_x",
        practice_mode="recognition",
        prompt="Pick one.\nA. wrong thing\nB. right thing\nC. other thing",
        expected_answer="B. right thing",
        created_at="2026-07-22T00:00:00Z",
        updated_at="2026-07-22T00:00:00Z",
    )
    payload.update(overrides)
    return PracticeItem(**payload)


def _rubric():
    return Rubric(
        max_points=4,
        criteria=[RubricCriterion(id="criterion_correct_selection", points=4.0, description="d")],
    )


class TestDeterministicRecognitionGrade:
    def test_correct_selection_full_credit(self):
        proposal = deterministic_recognition_grade(
            _mc_item(), _rubric(), "B. right thing", attempt_id="a1"
        )
        assert proposal is not None
        assert proposal.rubric_score == 4
        assert proposal.grader_confidence == 1.0
        assert proposal.criterion_evidence[0].points_awarded == 4.0

    def test_wrong_selection_zero(self):
        proposal = deterministic_recognition_grade(
            _mc_item(), _rubric(), "A", attempt_id="a1"
        )
        assert proposal is not None
        assert proposal.rubric_score == 0
        assert proposal.criterion_evidence[0].points_awarded == 0.0

    def test_free_text_defers_to_model_grader(self):
        proposal = deterministic_recognition_grade(
            _mc_item(), _rubric(), "the one that scales the basis", attempt_id="a1"
        )
        assert proposal is None

    def test_non_recognition_mode_defers(self):
        item = _mc_item(practice_mode="open_text")
        assert deterministic_recognition_grade(item, _rubric(), "B", attempt_id="a1") is None

    def test_prompt_without_options_defers(self):
        item = _mc_item(prompt="Explain the concept.")
        assert deterministic_recognition_grade(item, _rubric(), "B", attempt_id="a1") is None


class TestSoftScoreLane:
    def _observation(self, **overrides):
        payload = dict(
            rubric_score=4,
            max_points=4,
            evidence_coverage=1.0,
            hint_dampening=1.0,
            grader_confidence=1.0,
            attempt_type="independent_attempt",
            observed_at=datetime(2026, 7, 22, tzinfo=UTC),
        )
        payload.update(overrides)
        return MasteryObservation(**payload)

    def _prior(self):
        return MasteryState(
            learning_object_id="lo_x",
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=0,
            last_evidence_at=None,
            algorithm_version="mvp-0.8",
            updated_at="2026-07-22T00:00:00Z",
        )

    def test_soft_score_replaces_raw_fraction(self):
        config = LearnLoopConfig().mastery
        hard, _ = update_mastery_traced(
            self._prior(), self._observation(), config, "mvp-0.8"
        )
        soft, trace = update_mastery_traced(
            self._prior(),
            self._observation(soft_score_override=0.85),
            config,
            "mvp-0.8",
        )
        assert trace.observed_y == 0.85
        assert soft.logit_mean < hard.logit_mean  # softer outcome moves less

    def test_channel_doubt_never_inverts_direction_on_easy_items(self):
        """P1 (mean-preserving lane): with y kept at the raw fraction and channel
        doubt entering only through interpretation_variance, a perfect score can
        never move mastery DOWN — not even on a very easy item where predicted
        correctness exceeds the old soft-y ceiling (the 0.75→0.74 regression)."""

        config = LearnLoopConfig().mastery
        prior = MasteryState(
            learning_object_id="lo_x",
            logit_mean=1.1,
            logit_variance=1.5,
            evidence_count=9,
            last_evidence_at=None,
            algorithm_version="mvp-0.8",
            updated_at="2026-07-22T00:00:00Z",
        )
        # b = -2.4: predicted p ~ 0.97, above the old cold-channel E[s|success] = 0.85.
        updated, trace = update_mastery_traced(
            prior,
            self._observation(interpretation_variance=0.1025),
            config,
            "mvp-0.8",
            item_a=1.0,
            item_b=-2.4,
        )
        assert trace.observed_y == 1.0
        assert trace.innovation > 0
        assert updated.logit_mean >= prior.logit_mean

    def test_interpretation_variance_broadens_not_blocks(self):
        config = LearnLoopConfig().mastery
        certain, _ = update_mastery_traced(
            self._prior(), self._observation(), config, "mvp-0.8"
        )
        uncertain, _ = update_mastery_traced(
            self._prior(),
            self._observation(interpretation_variance=0.15),
            config,
            "mvp-0.8",
        )
        # Same direction, smaller step, and still a real update.
        assert 0 < uncertain.logit_mean < certain.logit_mean
        assert uncertain.logit_variance < 1.0


class TestClaimReanchor:
    def test_zero_evidence_state_gets_full_merge_weight(self):
        state = MasteryState(
            learning_object_id="lo_x",
            logit_mean=-1.735,  # the old 0.15 anchor
            logit_variance=1.0,
            evidence_count=0,
            last_evidence_at=None,
            algorithm_version="mvp-0.8",
            updated_at="2026-07-22T00:00:00Z",
        )
        merged = apply_claim_evidence(
            state, claimed_level=0.7, prior_pseudo_count=2.0, now_iso="2026-07-22T01:00:00Z"
        )
        assert sigmoid(merged.logit_mean) > 0.4  # pulled decisively toward the claim
        assert merged.logit_variance < state.logit_variance

    def test_evidence_rich_state_moves_less(self):
        confident = MasteryState(
            learning_object_id="lo_x",
            logit_mean=-1.0,
            logit_variance=0.2,
            evidence_count=20,
            last_evidence_at=None,
            algorithm_version="mvp-0.8",
            updated_at="2026-07-22T00:00:00Z",
        )
        merged = apply_claim_evidence(
            confident, claimed_level=0.7, prior_pseudo_count=2.0, now_iso="2026-07-22T01:00:00Z"
        )
        broad = confident.logit_mean
        assert abs(merged.logit_mean - broad) < 0.6  # bounded influence vs evidence


class TestTriageBridge:
    def test_template_labels_route(self):
        assert triage_reason_for_label("unfamiliar") == "unfamiliar_or_missing_knowledge"
        assert triage_reason_for_label("procedure_without_selection") == "method_selection"
        assert triage_reason_for_label("misconception:m1") == "false_belief_or_confusion"
        assert triage_reason_for_label("confuses_with:c2") == "false_belief_or_confusion"
        assert triage_reason_for_label("something_new") == "unknown_or_ambiguous"


class TestStratifiedCap:
    def _model(self, item_id):
        return TargetItemModel(
            item_id=item_id,
            support=frozenset(),
            fatal_error_ids=frozenset(),
            item_a=1.0,
            item_b=0.0,
        )

    def test_round_robin_across_strata(self):
        models = [self._model(f"pi_{stratum}_{i}") for stratum in ("aaa", "bbb") for i in range(4)]
        strata = {
            model.item_id: (model.item_id.split("_")[1], "recognition") for model in models
        }
        picked = _stratified_cap(models, strata, cap=4)
        families = [strata[model.item_id][0] for model in picked]
        assert families.count("aaa") == 2
        assert families.count("bbb") == 2

    def test_under_cap_returns_all(self):
        models = [self._model("pi_a"), self._model("pi_b")]
        strata = {"pi_a": ("x", "m"), "pi_b": ("x", "m")}
        assert len(_stratified_cap(models, strata, cap=6)) == 2


class TestAssessmentSideErrorFiltering:
    def test_scheduler_excludes_assessment_side_errors(self):
        from learnloop.db.repositories import ActiveErrorEvent
        from learnloop.services.scheduler import _errors_by_learning_object

        events = [
            ActiveErrorEvent(
                id="e1",
                learning_object_id="lo_x",
                error_type="assessment_ambiguity",
                severity=0.9,
                is_misconception=False,
                created_at="2026-07-22T00:00:00Z",
            ),
            ActiveErrorEvent(
                id="e2",
                learning_object_id="lo_x",
                error_type="retrieval_failure",
                severity=0.4,
                is_misconception=False,
                created_at="2026-07-22T00:00:00Z",
            ),
        ]
        grouped = _errors_by_learning_object(events)
        assert [event.id for event in grouped["lo_x"]] == ["e2"]

    def test_quality_state_pays_for_assessment_side_error(self):
        from learnloop.services.mastery import MasteryState
        from learnloop.services.recall_coverage import build_quality_state_update_from_prior

        state = build_quality_state_update_from_prior(
            None,
            recent_failures=0,
            item_id="pi_x",
            prior_mastery=MasteryState(
                learning_object_id="lo_x",
                logit_mean=0.0,
                logit_variance=1.0,
                evidence_count=1,
                last_evidence_at=None,
                algorithm_version="mvp-0.8",
                updated_at="2026-07-22T00:00:00Z",
            ),
            correctness=0.0,
            grader_confidence=1.0,
            now_iso="2026-07-22T00:00:00Z",
            algorithm_version="mvp-0.8",
            assessment_side_error=True,
        )
        assert state["bad_item_suspicion"] > 0
        assert "assessment_side_error" in state["suspicion_reasons"]
