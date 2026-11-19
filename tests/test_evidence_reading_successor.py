"""The evidence reading fixes, mvp-0.61 (refactor bug ledger G3-1, ER-2, K5-3, K5-11, K5-12;
``docs/reviews/algorithm-mvp-0.61.md``).

Each fix is on at mvp-0.61 and later and exactly mvp-0.60's below it, and each has a test that runs the same stored
history at both tags: the mvp-0.61 arm is the fix (it failed before the fix), the mvp-0.60 arm pins today's result.
ER-2's pair is in ``tests/test_causal_trace_consistency_p2.py`` beside the strict xfail it replaces. The upgrade test
at the end builds one vault holding every case at mvp-0.60, upgrades it and rebuilds it again. Fakes only; no model
call.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import timedelta

import pytest

from learnloop.ai.runtime import AIRuntimeReport
from learnloop.algorithm_versions import (
    EVIDENCE_READING_FIX_ALGORITHM_VERSION,
    GRADE_CHANNEL_FIX_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
    evidence_reading_fixes_on,
)
from learnloop.attempts.ai_contracts import CriterionEvidence, GradingContext, GradingProposal
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    SelfGradeInput,
    apply_attempt,
    complete_attempt_with_ai_fallback,
    complete_self_graded_attempt,
)
from learnloop.attempts.regrade import regrade_attempt, run_deferred_ai_regrades
from learnloop.attempts.post_attempt import run_post_attempt_pipeline
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.probe_episodes import effective_episode_observations, episode_posterior
from learnloop.followup_serve import workflow as wf
from learnloop.goals.certification_cold_probe import (
    current_certificate,
    false_certification_rate,
    resolve_cold_probe_parameters,
    schedule_certification_cold_probes,
)
from learnloop.goals.exam_seeding import seed_exam_attempts
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop_sidecar.context import SidecarContext

from tests.certification_cold_probe_helpers import HELD_OUT_ITEM, LO_ID, _attempt, _certify
from tests.exam_seeding_helpers import _exam_vault, _outcomes
from tests.followup_journey_helpers import _Runtime, _call, _generate
from tests.followup_serve_helpers import CLOCK as PROBE_CLOCK
from tests.followup_serve_helpers import miss_with_rivals, rival_causes_vault
from tests.helpers import NOW, create_basic_vault, set_algorithm_version
from tests.structured_ai import JointGraderAlsoBlind, StructuredClientFake

TAG = EVIDENCE_READING_FIX_ALGORITHM_VERSION
BELOW = GRADE_CHANNEL_FIX_ALGORITHM_VERSION
BOTH_TAGS = pytest.mark.parametrize("tag", [BELOW, TAG])
ITEM_ID = "pi_svd_define_001"
CLOCK = FrozenClock(NOW)


def test_the_successor_is_one_constant_after_the_grade_channel_fixes():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == BELOW == "mvp-0.60"
    assert TAG == "mvp-0.61" == SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION
    assert not evidence_reading_fixes_on(_Config(BELOW)) and evidence_reading_fixes_on(_Config(TAG))


class _Config:
    def __init__(self, tag):
        self.algorithms = type("Algorithms", (), {"algorithm_version": tag})()


def _vault(tmp_path, tag, name="vault"):
    paths = create_basic_vault(tmp_path / name)
    set_algorithm_version(paths, tag)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    return paths, vault, repository


def _rows(paths, sql, *args):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, args).fetchall()]


def _rebuild(paths):
    vault = load_vault(paths.root)
    rebuild_all_derived_state(vault, Repository(paths.sqlite_path), clock=FrozenClock(NOW + timedelta(days=1)))


class _Grader(JointGraderAlsoBlind, StructuredClientFake):
    """A model grader that answers ``points`` on ``correctness`` with ``confidence``."""

    provider_name = "deepseek_flash"
    provider_type = "openai_chat"
    model = "deepseek-v4-flash"

    def __init__(self, *, points: float, confidence: float = 0.9):
        self.points = points
        self.confidence = confidence

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        return GradingProposal(
            attempt_id=context.attempt_id,
            practice_item_id=context.practice_item_id,
            rubric_score=int(self.points),
            criterion_evidence=[
                CriterionEvidence(criterion_id="correctness", points_awarded=self.points, evidence="Graded.")
            ],
            grader_confidence=self.confidence,
        )


def _ready_runtime() -> AIRuntimeReport:
    return AIRuntimeReport(status="ready", active_provider="deepseek_flash", provider_type="openai_chat",
                           model="deepseek-v4-flash")


def _model_graded(vault, repository, *, points, confidence, clock=CLOCK):
    return complete_attempt_with_ai_fallback(
        vault, repository,
        AttemptDraft(practice_item_id=ITEM_ID, learner_answer_md="SVD factors a matrix as U Sigma V transpose."),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=3),
        runtime=_ready_runtime(), ai_client=_Grader(points=points, confidence=confidence), clock=clock,
    )


def _raw_events(paths, attempt_id):
    return _rows(paths, "SELECT grader_provider, model_confidence, raw_output_json FROM raw_grade_events "
                        "WHERE attempt_id = ? ORDER BY created_at, id", attempt_id)


# -- K5-12: a grader confidence of 0.0 is legal and stays 0.0 on replay -------------------------------------------


@BOTH_TAGS
def test_k5_12_a_zero_confidence_survives_a_rebuild(tmp_path, tag):
    paths, vault, repository = _vault(tmp_path, tag)
    result = _model_graded(vault, repository, points=4, confidence=0.0)
    attempt_id = result.attempt_id
    assert repository.fetch_practice_attempt(attempt_id)["grader_confidence"] == 0.0
    assert [row["model_confidence"] for row in _raw_events(paths, attempt_id)] == [0.0]

    _rebuild(paths)
    _rebuild(paths)

    stored = repository.fetch_practice_attempt(attempt_id)["grader_confidence"]
    confidences = [row["model_confidence"] for row in _raw_events(paths, attempt_id)]
    if tag == TAG:
        # The live grade's 0.0 is what replay reads: nothing to append, so the grade channel is the live one.
        assert stored == 0.0
        assert confidences == [0.0]
    else:
        # mvp-0.60, today: replay read 0.0 as missing and wrote 1.0 back to the attempt; its first rebuild took the
        # changed confidence for a regrade and appended a raw grade event at 1.0 (ledger K5-12).
        assert stored == 1.0
        assert confidences == [0.0, 1.0]


@BOTH_TAGS
def test_k5_12_a_missing_confidence_still_reads_as_full(tmp_path, tag):
    paths, vault, repository = _vault(tmp_path, tag)
    result = _model_graded(vault, repository, points=4, confidence=0.7)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET grader_confidence = NULL WHERE id = ?", (result.attempt_id,))
        connection.commit()

    _rebuild(paths)

    # A legacy NULL is the one value replay fills, at both tags.
    assert repository.fetch_practice_attempt(result.attempt_id)["grader_confidence"] == 1.0


# -- K5-11: a replacement grade replays under its own source; a replaced exam answer reaches the exam channel ------


def _self_graded(vault, repository, *, points=0, clock=CLOCK, item_id=ITEM_ID):
    return complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="SVD is U Sigma V^T."),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=4),
        clock=clock,
    )


def _ai_regrade_pending(vault, repository, *, points=4):
    result = run_deferred_ai_regrades(
        vault, repository, runtime=_ready_runtime(), ai_client=_Grader(points=points), clock=CLOCK,
    )
    assert result.regraded >= 1


@BOTH_TAGS
def test_k5_11_an_ai_regrade_of_a_self_grade_replays_as_the_ai(tmp_path, tag):
    paths, vault, repository = _vault(tmp_path, tag)
    attempt_id = _self_graded(vault, repository).attempt_id
    assert [row["grader_provider"] for row in _raw_events(paths, attempt_id)] == ["self"]

    _ai_regrade_pending(vault, repository)
    live = [row["grader_provider"] for row in _raw_events(paths, attempt_id)]
    _rebuild(paths)
    _rebuild(paths)
    rebuilt = [row["grader_provider"] for row in _raw_events(paths, attempt_id)]

    # The regrade's own replay appends the new grade to the answer's observation (the grade channel fixes); which
    # source it names is the fix. Two rebuilds append nothing more at either tag.
    expected = ["self", "ai"] if tag == TAG else ["self", "self"]
    assert live == rebuilt == expected


def _exam_vault_at(tmp_path, tag):
    vault_root, _vault_unused, _repository = _exam_vault(tmp_path)
    paths = VaultPaths(vault_root, load_vault(vault_root).config)
    set_algorithm_version(paths, tag)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    return paths, vault, repository


def _seed_exam_answer(vault, repository):
    seeded = seed_exam_attempts(
        vault, repository,
        outcomes=_outcomes(outcomes={"3": {"score": 0.25, "answer_md": "SVD factors a matrix into U, Sigma, V^T."}}),
        clock=CLOCK,
    )
    (entry,) = [entry for entry in seeded.entries if entry.status == "seeded"]
    return entry.attempt_id


def _exam_channel(paths, attempt_id):
    """The attempt's grade channel: (administration purpose, grader provider, rubric score) per raw grade event."""

    rows = _rows(
        paths,
        "SELECT a.purpose, r.grader_provider, r.raw_output_json FROM raw_grade_events r "
        "JOIN activity_observations o ON o.id = r.observation_id "
        "JOIN activity_administrations a ON a.id = o.administration_id "
        "WHERE r.attempt_id = ? ORDER BY r.created_at, r.id",
        attempt_id,
    )
    return [(row["purpose"], row["grader_provider"], json.loads(row["raw_output_json"]).get("rubric_score"))
            for row in rows]


@BOTH_TAGS
def test_k5_11_a_regraded_exam_answer_reaches_the_exam_channel(tmp_path, tag):
    paths, vault, repository = _exam_vault_at(tmp_path, tag)
    attempt_id = _seed_exam_answer(vault, repository)
    assert _exam_channel(paths, attempt_id) == []

    regrade_attempt(vault, repository, repository.fetch_practice_attempt(attempt_id), runtime=_ready_runtime(),
                    client=_Grader(points=4), grading_source="ai", clock=CLOCK)
    live = _exam_channel(paths, attempt_id)
    _rebuild(paths)
    _rebuild(paths)

    # mvp-0.60, today: an exam answer's channel is written by the exam path alone, so its replacement never reached
    # one. From mvp-0.61 the replacement is written on the exam channel's (assessment-purpose) administration, once.
    expected = [("assessment", "ai", 4)] if tag == TAG else []
    assert live == _exam_channel(paths, attempt_id) == expected


# -- K5-3: a certificate probe whose every criterion is unassessed abstains -------------------------------------------


def _unassessed_answer(vault, repository, item_id, *, clock, attempt_id="att_unassessed_probe"):
    """A full-marks answer whose every criterion the valid-alternative gate left unassessed (PF-c's verified answer:
    correctness 1.0 for scheduling, no measurement)."""

    rubric = vault.rubric_for_item(vault.practice_items[item_id])
    points = {criterion.id: float(criterion.points) for criterion in rubric.criteria}
    return apply_attempt(
        vault, repository,
        ApplyAttemptInput(
            draft=AttemptDraft(practice_item_id=item_id, learner_answer_md="U Sigma V transpose, another route."),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=int(rubric.max_points), criterion_points=points,
                evidence_rows=[{
                    "id": f"ge_{attempt_id}_{criterion}", "criterion_id": criterion, "points_awarded": awarded,
                    "evidence": "A valid alternative route; not verified.", "notes": None,
                    "local_grader_id": "test", "grader_tier": 1, "created_at": clock.now().isoformat(),
                } for criterion, awarded in points.items()],
                error_attributions=[], grader_confidence=0.9, confidence=4, manual_review_reason=None,
            ),
            unverified_criterion_ids=tuple(points),
        ),
        clock=clock,
    )


def _certified_at(tmp_path, tag):
    paths, vault, repository, certificate = _certify(tmp_path)
    set_algorithm_version(paths, tag)
    vault = load_vault(paths.root)
    assert current_certificate(vault, repository, vault.learning_objects[LO_ID]) == certificate
    schedule_certification_cold_probes(vault, repository, clock=CLOCK)
    due = FrozenClock(NOW + timedelta(days=resolve_cold_probe_parameters(repository).horizon_days))
    return paths, vault, repository, due


@BOTH_TAGS
def test_k5_3_a_probe_answer_with_every_criterion_unassessed_abstains(tmp_path, tag):
    _paths, vault, repository, due = _certified_at(tmp_path, tag)
    result = _unassessed_answer(vault, repository, HELD_OUT_ITEM, clock=due)
    outcome = repository.certification_cold_probe_outcome_for_attempt(result.attempt_id)

    recorded = (outcome["verdict"], outcome["indeterminate_reason"], outcome["success"], outcome["correctness"],
                outcome["policy_version"])
    if tag == TAG:
        assert recorded == ("indeterminate", "grade_unavailable", None, None, "certification_cold_probe_policy_v2")
        assert false_certification_rate(repository).denominator == 0
    else:
        # mvp-0.60, today: the scheduling stand-in scored as a held certificate (ledger K5-3).
        assert recorded == ("held", None, True, 1.0, "certification_cold_probe_policy_v1")
        assert false_certification_rate(repository).denominator == 1


@BOTH_TAGS
def test_k5_3_an_assessed_probe_answer_is_scored_at_both_tags(tmp_path, tag):
    _paths, vault, repository, due = _certified_at(tmp_path, tag)
    result = _attempt(vault, repository, HELD_OUT_ITEM, points=4, clock=due)
    outcome = repository.certification_cold_probe_outcome_for_attempt(result.attempt_id)
    policy = "certification_cold_probe_policy_v2" if tag == TAG else "certification_cold_probe_policy_v1"
    assert (outcome["verdict"], outcome["correctness"], outcome["policy_version"]) == ("held", 1.0, policy)
    # The scheduling stamps did not change: the task was scheduled under v1 at both tags.
    assert repository.followup_task(outcome["followup_task_id"])["context"]["policy_version"] == (
        "certification_cold_probe_policy_v1"
    )


# -- G3-1: a probe answer given after its feedback was shown, or after a reveal, is contaminated in its episode -------


class _ProbeGrader(JointGraderAlsoBlind, StructuredClientFake):
    """A model grader for a generated probe: ``points`` per criterion, every criterion graded."""

    provider_name = "deepseek_flash"
    provider_type = "openai_chat"
    model = "deepseek-v4-flash"

    def __init__(self, points, *, confidence=0.9, full=False):
        self.points = dict(points)
        self.confidence = confidence
        self.full = full  # every criterion at its full points

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        criteria = {str(criterion["id"]): float(criterion["points"]) for criterion in context.rubric.get("criteria") or []}
        awarded = {criterion: (maximum if self.full else float(self.points.get(criterion, 0.0)))
                   for criterion, maximum in criteria.items()}
        return GradingProposal(
            attempt_id=context.attempt_id,
            practice_item_id=context.practice_item_id,
            rubric_score=int(sum(awarded.values())),
            criterion_evidence=[
                CriterionEvidence(criterion_id=criterion, points_awarded=points, evidence="Graded.")
                for criterion, points in awarded.items()
            ],
            grader_confidence=self.confidence,
        )


def _probe_journey(tmp_path, monkeypatch, tag):
    """The follow-up journey (a miss with two rival causes, its generated probe ready) at ``tag``."""

    monkeypatch.setattr(
        "learnloop_sidecar.handlers.practice.ready_grading_provider",
        lambda *_args, **_kw: ("fake", _Runtime(), object()),
    )
    _vault_unused, _repository, paths = rival_causes_vault(tmp_path, version=tag)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    vault, repository = ctx.require_vault()
    result, outcome = miss_with_rivals(vault, repository)
    _generate(ctx, repository)
    row = wf.get(repository, outcome.workflow_id)
    assert row["presentation_id"], row
    return paths, ctx, vault, repository, result, row


def _expose(ctx, repository, result, row, exposure):
    if exposure == "shown_anyway":
        _call(ctx, "followup_show_anyway", {"attemptId": result.attempt_id})
    elif exposure == "reveal":
        # A tutor answer on the missed item, an hour before the probe's answer: material exposure for every item of
        # its learning object (the reveal ledger's window), the probe's included, without priming the probe item.
        source = repository.fetch_practice_attempt(row["source_attempt_id"])
        repository.insert_reveal_event(
            {"practice_item_id": source["practice_item_id"], "learning_object_id": source["learning_object_id"],
             "source_kind": "tutor_answer", "amount": 1.0, "basis": "tutor_answer"},
            clock=FrozenClock(PROBE_CLOCK.now() - timedelta(hours=1)),
        )


def _answer_probe(ctx, repository, row):
    """The probe answered through the model grader (an approved source, so the episode records an observation) and
    the post-attempt pipeline (which writes the discriminating observation)."""

    _call(ctx, "followup_status", {"attemptId": row["source_attempt_id"]})  # this process's vault reads the new item
    _call(ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
    _call(ctx, "get_probe_contract", {"practiceItemId": row["practice_item_id"]})
    vault, _ = ctx.require_vault()
    probe = complete_attempt_with_ai_fallback(
        vault, repository,
        AttemptDraft(practice_item_id=row["practice_item_id"], learner_answer_md="An answer.",
                     attempt_type="diagnostic_probe", probe_presentation_id=row["presentation_id"]),
        SelfGradeInput(criterion_points={}, confidence=3),
        runtime=_ready_runtime(), ai_client=_ProbeGrader({"fact_0": 0, "fact_1": 2}), clock=PROBE_CLOCK,
    )
    run_post_attempt_pipeline(vault, repository, result=probe, followup_surface="desktop", clock=PROBE_CLOCK)
    return probe.attempt_id


def _episode_reading(vault, repository, probe_attempt_id):
    """(stored observation, effective observation, the episode's qualifying count) for the probe answer."""

    stored = repository.probe_observation_for_attempt(probe_attempt_id)
    presentation = repository.probe_presentation(str(repository.fetch_practice_attempt(probe_attempt_id)
                                                     ["probe_presentation_id"]))
    episode = repository.probe_episode(presentation.probe_episode_id)
    (effective,) = [row["observation"] for row in effective_episode_observations(vault, repository, episode.id)
                    if row["observation"].attempt_id == probe_attempt_id]
    posterior = episode_posterior(vault, repository, episode)
    return stored, effective, posterior.qualifying_observations


EXPOSURES = pytest.mark.parametrize(
    ("exposure", "reason"),
    [("shown_anyway", "followup_feedback_shown_anyway"), ("reveal", "post_reveal_not_independent")],
)


@EXPOSURES
@BOTH_TAGS
def test_g3_1_an_exposed_probe_answer_is_contaminated_in_its_episode(tmp_path, monkeypatch, tag, exposure, reason):
    paths, ctx, vault, repository, result, row = _probe_journey(tmp_path, monkeypatch, tag)
    _expose(ctx, repository, result, row, exposure)
    probe_attempt_id = _answer_probe(ctx, repository, row)

    (discriminating,) = repository.causal_discriminating_observations(factor_id=row["factor_id"])
    assert (discriminating["admissible_as_independent"], discriminating["inadmissibility_reason"]) == (0, reason)
    stored, effective, qualifying = _episode_reading(vault, repository, probe_attempt_id)
    weight = vault.config.probe.episode.contaminated_evidence_weight
    if tag == TAG:
        # The episode applies the discriminating observation's test: contaminated, damped to the configured weight,
        # qualifying nothing, and written so at submission.
        for observation in (stored, effective):
            assert observation.contamination == {"answer_exposed": reason}
            assert observation.independent_evidence_discount == weight
            assert observation.eligible_for_completion is False and observation.updates_belief is True
        assert qualifying == 0
    else:
        # mvp-0.60, today: the same answer counted at full weight and qualified (ledger G3-1).
        for observation in (stored, effective):
            assert observation.contamination is None
            assert observation.independent_evidence_discount == 1.0
            assert observation.eligible_for_completion is True
        assert qualifying == 1


def test_g3_1_a_clean_probe_answer_is_unchanged_at_the_tag(tmp_path, monkeypatch):
    _paths, ctx, vault, repository, _result, row = _probe_journey(tmp_path, monkeypatch, TAG)
    probe_attempt_id = _answer_probe(ctx, repository, row)
    (discriminating,) = repository.causal_discriminating_observations(factor_id=row["factor_id"])
    assert discriminating["admissible_as_independent"] == 1
    stored, effective, qualifying = _episode_reading(vault, repository, probe_attempt_id)
    assert stored == effective
    assert (stored.contamination, stored.independent_evidence_discount, stored.eligible_for_completion) == (
        None, 1.0, True)
    assert qualifying == 1


@EXPOSURES
def test_g3_1_an_exposed_answer_recorded_below_the_tag_reads_contaminated_after_the_upgrade(
    tmp_path, monkeypatch, exposure, reason,
):
    """A stored observation keeps its row; the episode reads it through the same test once the vault is at the tag,
    and its posterior then moves by the damped weight, not the full one."""

    paths, ctx, vault, repository, result, row = _probe_journey(tmp_path, monkeypatch, BELOW)
    _expose(ctx, repository, result, row, exposure)
    probe_attempt_id = _answer_probe(ctx, repository, row)
    _stored, _effective, before_qualifying = _episode_reading(vault, repository, probe_attempt_id)
    presentation = repository.probe_presentation(row["presentation_id"])
    episode = repository.probe_episode(presentation.probe_episode_id)
    full = episode_posterior(vault, repository, episode).posterior

    set_algorithm_version(paths, TAG)
    vault = load_vault(paths.root)
    stored, effective, qualifying = _episode_reading(vault, repository, probe_attempt_id)
    damped = episode_posterior(vault, repository, episode).posterior

    assert (stored.contamination, stored.eligible_for_completion) == (None, True)  # the receipt is untouched
    assert effective.contamination == {"answer_exposed": reason}
    assert effective.independent_evidence_discount == vault.config.probe.episode.contaminated_evidence_weight
    assert (before_qualifying, qualifying) == (1, 0)
    prior = episode_posterior(vault, repository, episode).prior
    # Damped: the exposed answer moves each hypothesis less than it did at full weight, in the same direction.
    for label in prior:
        assert abs(damped[label] - prior[label]) <= abs(full[label] - prior[label]) + 1e-12

