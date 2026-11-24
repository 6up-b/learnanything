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

from learnloop import activation_journal
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
    GradeAttribution,
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
from learnloop.diagnosis.causal_attribution import causal_episode_for_attempt
from learnloop.diagnosis.probe_episodes import effective_episode_observations, episode_posterior
from learnloop.followup_serve import workflow as wf
from learnloop.goals.certification_cold_probe import (
    current_certificate,
    false_certification_rate,
    resolve_cold_probe_parameters,
    schedule_certification_cold_probes,
)
from learnloop.goals.exam_seeding import seed_exam_attempts
from learnloop.ops import upgrades
from learnloop.ops.upgrades import upgrade
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_practice_item
from learnloop_sidecar.context import SidecarContext

from tests.certain_grade_helpers import make_grade_certain
from tests.certification_cold_probe_helpers import HELD_OUT_ITEM, LO_ID, _attempt, _blueprint, _certify
from tests.exam_seeding_helpers import _exam_vault, _outcomes
from tests.followup_journey_helpers import _Runtime, _call, _generate
from tests.followup_serve_helpers import CLOCK as PROBE_CLOCK
from tests.followup_serve_helpers import AuthorFake, miss_with_rivals, rival_causes_vault
from tests.helpers import NOW, add_followup_item, create_basic_vault, set_algorithm_version
from tests.structured_ai import JointGraderAlsoBlind, StructuredClientFake

TAG = EVIDENCE_READING_FIX_ALGORITHM_VERSION
BELOW = GRADE_CHANNEL_FIX_ALGORITHM_VERSION
BOTH_TAGS = pytest.mark.parametrize("tag", [BELOW, TAG])
ITEM_ID = "pi_svd_define_001"
CLOCK = FrozenClock(NOW)


def test_the_successor_is_one_constant_after_the_grade_channel_fixes():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == BELOW == "mvp-0.60"
    assert TAG == "mvp-0.61" == SUCCESSOR_CHAIN[-9] and SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.69"
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


class _Rows:
    """A grading-evidence row's two fields the source rule reads."""

    def __init__(self, run_id, tier=3):
        self.agent_run_id, self.grader_tier = run_id, tier


class _Runs:
    """The repository reads ``replayed_grading_source`` makes: the first grade's feedback and the runs by id."""

    def __init__(self, runs):
        self.runs = runs

    def raw_attempt_feedback_metadata(self, _attempt_id):
        return {"grading_source": "self", "agent_run_id": None}

    def agent_run(self, run_id):
        return self.runs.get(run_id)


@pytest.mark.parametrize(("runs", "rows", "expected"), [
    ({"run_a": {"purpose": "grading", "provider": "deepseek_flash"}}, [_Rows("run_a")], "ai"),
    ({}, [_Rows("run_missing")], "self"),
    ({"run_a": {"purpose": "tutor_qa", "provider": "deepseek_flash"}}, [_Rows("run_a")], "self"),
    ({"run_a": {"purpose": "grading", "provider": "deepseek_flash"},
      "run_b": {"purpose": "grading", "provider": "codex_cli"}}, [_Rows("run_a"), _Rows("run_b")], "self"),
], ids=["one_grading_run", "missing_run", "run_of_another_purpose", "two_candidate_runs"])
def test_r4_a_replacements_source_is_never_invented(monkeypatch, runs, rows, expected):
    """Only one existing grading run on the current rows names a replaced self-grade's source; a missing, unrelated
    or ambiguous run keeps the recorded one (the review's T61-4)."""

    from learnloop.attempts import replay_reading

    monkeypatch.setattr(replay_reading, "_graded_more_than_once", lambda _repository, _attempt_id: True)
    vault = type("Vault", (), {"config": _Config(TAG)})()
    assert replay_reading.replayed_grading_source(vault, _Runs(runs), {"id": "att"}, rows) == expected


@BOTH_TAGS
def test_r4_a_regrade_whose_run_is_gone_replays_under_its_recorded_source(tmp_path, tag):
    """The review's pruned history: a self-grade regraded by a model below the tag (its channel ``self, self``), the
    regrade's run no longer on record. Read at ``tag``, nothing says which provider graded the replacement, so the
    recorded source stands and nothing is appended (before, the missing run read as ``ai``)."""

    paths, vault, repository = _vault(tmp_path, BELOW)
    attempt_id = _self_graded(vault, repository).attempt_id
    _ai_regrade_pending(vault, repository)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("DELETE FROM agent_runs WHERE id IN (SELECT agent_run_id FROM grading_evidence "
                           "WHERE attempt_id = ? AND agent_run_id IS NOT NULL)", (attempt_id,))
        connection.commit()
    set_algorithm_version(paths, tag)
    _rebuild(paths)
    _rebuild(paths)

    assert [row["grader_provider"] for row in _raw_events(paths, attempt_id)] == ["self", "self"]


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


def _legacy_same_second(paths, attempt_id):
    """Make the attempt's grading rows revision-less (``legacy:<created_at>`` epoch keys) and stamped in one second
    (the exam import's original is stamped at the exam's date): the original and its replacement share one key."""

    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE grading_evidence SET grading_revision = NULL, created_at = (SELECT MIN(created_at) "
                           "FROM grading_evidence WHERE attempt_id = ?) WHERE attempt_id = ?", (attempt_id, attempt_id))
        connection.commit()
    keys = _rows(paths, "SELECT DISTINCT created_at FROM grading_evidence WHERE attempt_id = ?", attempt_id)
    assert len(keys) == 1, keys  # one second, one legacy key


@BOTH_TAGS
def test_r5_a_same_second_legacy_regrade_of_a_self_grade_replays_as_the_ai(tmp_path, tag):
    paths, vault, repository = _vault(tmp_path, BELOW)
    attempt_id = _self_graded(vault, repository).attempt_id
    _ai_regrade_pending(vault, repository)
    _legacy_same_second(paths, attempt_id)
    set_algorithm_version(paths, tag)
    _rebuild(paths)
    _rebuild(paths)

    # The superseded original says a second write came: at the tag the replacement replays under its run's source.
    expected = ["self", "self", "ai"] if tag == TAG else ["self", "self"]
    assert [row["grader_provider"] for row in _raw_events(paths, attempt_id)] == expected


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


@BOTH_TAGS
def test_r5_a_same_second_legacy_regrade_of_an_exam_answer_reaches_the_exam_channel(tmp_path, tag):
    paths, vault, repository = _exam_vault_at(tmp_path, BELOW)
    attempt_id = _seed_exam_answer(vault, repository)
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(attempt_id), runtime=_ready_runtime(),
                    client=_Grader(points=4), grading_source="ai", clock=CLOCK)
    _legacy_same_second(paths, attempt_id)
    set_algorithm_version(paths, tag)
    _rebuild(paths)
    _rebuild(paths)

    assert _exam_channel(paths, attempt_id) == ([("assessment", "ai", 4)] if tag == TAG else [])


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


# -- G3-1: a probe answer given after its feedback was shown, or after a reveal, updates no belief in its episode ------


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


def _answer_probe(ctx, repository, row, *, hints_used=0):
    """The probe answered through the model grader (an approved source, so the episode records an observation) and
    the post-attempt pipeline (which writes the discriminating observation)."""

    _call(ctx, "followup_status", {"attemptId": row["source_attempt_id"]})  # this process's vault reads the new item
    _call(ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
    _call(ctx, "get_probe_contract", {"practiceItemId": row["practice_item_id"]})
    vault, _ = ctx.require_vault()
    probe = complete_attempt_with_ai_fallback(
        vault, repository,
        AttemptDraft(practice_item_id=row["practice_item_id"], learner_answer_md="An answer.",
                     attempt_type="diagnostic_probe", probe_presentation_id=row["presentation_id"],
                     hints_used=hints_used),
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


class _DiscriminatingInstrument:
    """The journey's generated probe reads every outcome alike for its two causes (its likelihoods are flat), so no
    answer moves the episode posterior and a belief update could not be seen. Installed, the instrument separates the
    causes, live and on replay alike; ``on = False`` makes it flat again (the answer then carries no information)."""

    def __init__(self, monkeypatch):
        from learnloop.diagnosis import probe_episodes, probe_evidence

        self.on = True
        self._original = probe_episodes.instrument_observation_likelihoods
        monkeypatch.setattr(probe_episodes, "instrument_observation_likelihoods", self)
        monkeypatch.setattr(probe_evidence, "instrument_observation_likelihoods", self)

    def __call__(self, instrument, slot_map, outcome):
        likelihoods = self._original(instrument, slot_map, outcome)
        if not likelihoods:
            return likelihoods
        labels = sorted(likelihoods)
        if not self.on:
            return {label: 0.5 for label in labels}
        return dict(zip(labels, [0.9, 0.2] + [0.5] * (len(labels) - 2), strict=False))


EXPOSURES = pytest.mark.parametrize(
    ("exposure", "reason"),
    [("shown_anyway", "followup_feedback_shown_anyway"), ("reveal", "post_reveal_not_independent")],
)


@EXPOSURES
@BOTH_TAGS
def test_g3_1_an_exposed_probe_answer_updates_no_belief_in_its_episode(tmp_path, monkeypatch, tag, exposure, reason):
    _DiscriminatingInstrument(monkeypatch)
    paths, ctx, vault, repository, result, row = _probe_journey(tmp_path, monkeypatch, tag)
    _expose(ctx, repository, result, row, exposure)
    probe_attempt_id = _answer_probe(ctx, repository, row)

    (discriminating,) = repository.causal_discriminating_observations(factor_id=row["factor_id"])
    assert (discriminating["admissible_as_independent"], discriminating["inadmissibility_reason"]) == (0, reason)
    stored, effective, qualifying = _episode_reading(vault, repository, probe_attempt_id)
    if tag == TAG:
        # The episode applies the discriminating observation's test, and an exposed answer reads as a held grade
        # does: no belief update, nothing qualifying, the reason recorded; written so at submission.
        for observation in (stored, effective):
            assert observation.contamination == {"answer_exposed": reason}
            assert observation.independent_evidence_discount == 0.0
            assert observation.updates_belief is False and observation.eligible_for_completion is False
        assert stored.posterior_after == stored.posterior_before
        assert stored.realized_information_gain == 0.0
        assert qualifying == 0
    else:
        # mvp-0.60, today: the same answer counted at full weight and qualified (ledger G3-1).
        for observation in (stored, effective):
            assert observation.contamination is None
            assert observation.independent_evidence_discount == 1.0
            assert observation.updates_belief is True and observation.eligible_for_completion is True
        assert stored.posterior_after != stored.posterior_before
        assert qualifying == 1


@BOTH_TAGS
def test_g3_1_a_hinted_answer_that_was_also_exposed_is_exposed(tmp_path, monkeypatch, tag):
    _DiscriminatingInstrument(monkeypatch)
    paths, ctx, vault, repository, result, row = _probe_journey(tmp_path, monkeypatch, tag)
    _expose(ctx, repository, result, row, "shown_anyway")
    probe_attempt_id = _answer_probe(ctx, repository, row, hints_used=1)

    stored, effective, qualifying = _episode_reading(vault, repository, probe_attempt_id)
    assert qualifying == 0
    if tag == TAG:
        # Exposed wins over the hint's damping: no update at all.
        for observation in (stored, effective):
            assert observation.contamination == {"hints_used": 1, "answer_exposed": "followup_feedback_shown_anyway"}
            assert (observation.independent_evidence_discount, observation.updates_belief) == (0.0, False)
        assert stored.posterior_after == stored.posterior_before
    else:
        # mvp-0.60, today: a hinted answer, damped to the contaminated weight.
        weight = vault.config.probe.episode.contaminated_evidence_weight
        for observation in (stored, effective):
            assert observation.contamination == {"hints_used": 1}
            assert (observation.independent_evidence_discount, observation.updates_belief) == (weight, True)
        assert stored.posterior_after != stored.posterior_before


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
def test_g3_1_an_exposed_answer_recorded_below_the_tag_updates_no_belief_after_the_upgrade(
    tmp_path, monkeypatch, exposure, reason,
):
    """A stored observation keeps its row; the episode reads it through the same test once the vault is at the tag,
    and its posterior then is the posterior before that answer."""

    instrument = _DiscriminatingInstrument(monkeypatch)
    paths, ctx, vault, repository, result, row = _probe_journey(tmp_path, monkeypatch, BELOW)
    _expose(ctx, repository, result, row, exposure)
    probe_attempt_id = _answer_probe(ctx, repository, row)
    _stored, _effective, before_qualifying = _episode_reading(vault, repository, probe_attempt_id)
    presentation = repository.probe_presentation(row["presentation_id"])
    episode = repository.probe_episode(presentation.probe_episode_id)
    full = episode_posterior(vault, repository, episode).posterior
    instrument.on = False
    before = episode_posterior(vault, repository, episode).posterior  # the episode without what the answer says
    instrument.on = True

    set_algorithm_version(paths, TAG)
    vault = load_vault(paths.root)
    stored, effective, qualifying = _episode_reading(vault, repository, probe_attempt_id)
    after = episode_posterior(vault, repository, episode).posterior

    # The receipt is untouched: it still records the full-weight update.
    assert (stored.contamination, stored.eligible_for_completion, stored.updates_belief) == (None, True, True)
    assert stored.posterior_after != stored.posterior_before
    assert effective.contamination == {"answer_exposed": reason}
    assert (effective.independent_evidence_discount, effective.updates_belief) == (0.0, False)
    assert (before_qualifying, qualifying) == (1, 0)
    # Below the tag the answer moved the posterior; read at the tag, the posterior after it equals the one before it.
    assert full != pytest.approx(before)
    assert after == pytest.approx(before)


# -- R1 (the tag's review): a stored answer's exposure is a function of persisted rows only -------------------------


def _feedback_display(repository, *, attempt_id, item_id, clock):
    """A routine full-answer display on a feedback screen, linked to ``attempt_id`` (``reveal_ledger``)."""

    from learnloop.attempts.reveal_ledger import record_feedback_answer_display_reveal

    record_feedback_answer_display_reveal(repository, attempt_id=attempt_id, practice_item_id=item_id,
                                          display_id=f"display_{attempt_id}_{clock.now().isoformat()}", clock=clock)


def _effective_reason(vault, repository, probe_attempt_id):
    _stored, effective, _qualifying = _episode_reading(vault, repository, probe_attempt_id)
    return (effective.contamination or {}).get("answer_exposed")


def test_r1_a_stored_answer_reads_the_same_at_any_reading_time(tmp_path, monkeypatch):
    """A routine display stamped two minutes after the answer (a clock that ran ahead when it was written) counted
    against the answer only while the READER's clock was behind its stamp: the same database read exposed at 12:01
    and clean at 12:03. At the tag the reading instant is the stored observation's own writing."""

    from learnloop.attempts import reveal_ledger

    _DiscriminatingInstrument(monkeypatch)
    paths, ctx, vault, repository, _result, row = _probe_journey(tmp_path, monkeypatch, BELOW)
    probe_attempt_id = _answer_probe(ctx, repository, row)
    _feedback_display(repository, attempt_id=row["source_attempt_id"], item_id=row["practice_item_id"],
                      clock=FrozenClock(PROBE_CLOCK.now() + timedelta(minutes=2)))
    set_algorithm_version(paths, TAG)
    vault = load_vault(paths.root)

    readings = []
    for minutes in (1, 3):
        reading_time = (PROBE_CLOCK.now() + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")
        monkeypatch.setattr(reveal_ledger, "utc_now_iso", lambda clock=None, at=reading_time: at)
        presentation = repository.probe_presentation(row["presentation_id"])
        posterior = episode_posterior(vault, repository, repository.probe_episode(presentation.probe_episode_id))
        readings.append((_effective_reason(vault, repository, probe_attempt_id), posterior.posterior))
    assert readings[0] == readings[1]
    assert readings[0][0] == "post_reveal_not_independent"  # as of the answer's own record: fail closed


@pytest.mark.parametrize("recorded", ["below_the_tag", "at_the_tag"])
def test_r1_an_answers_own_feedback_in_its_second_never_exposes_it(tmp_path, monkeypatch, recorded):
    """The answer's own feedback is linked to it by attempt id and shown after it, in the same second at the ledger's
    precision: it never exposes that answer, whether the row was recorded below the tag (judged on reading) or at it
    (its stored verdict)."""

    paths, ctx, vault, repository, _result, row = _probe_journey(
        tmp_path, monkeypatch, BELOW if recorded == "below_the_tag" else TAG)
    probe_attempt_id = _answer_probe(ctx, repository, row)
    _feedback_display(repository, attempt_id=probe_attempt_id, item_id=row["practice_item_id"], clock=PROBE_CLOCK)
    set_algorithm_version(paths, TAG)
    vault = load_vault(paths.root)

    stored, effective, qualifying = _episode_reading(vault, repository, probe_attempt_id)
    assert stored.contamination is None and effective.contamination is None
    assert (effective.updates_belief, effective.eligible_for_completion, qualifying) == (True, True, 1)
    if recorded == "at_the_tag":
        assert stored.features["answer_exposure_judged"] is True


@pytest.mark.parametrize("recorded", ["below_the_tag", "at_the_tag"])
def test_r1_causes_shown_in_the_answers_own_second_expose_it(tmp_path, monkeypatch, recorded):
    """A display of the causes stamped in the answer's own second, written before the answer: the stamps give no finer
    order, and the display existed when the answer was recorded, so it counts as before it (fail closed)."""

    from learnloop.db.stores import hypothesis_marks as marks_store

    paths, ctx, vault, repository, _result, row = _probe_journey(
        tmp_path, monkeypatch, BELOW if recorded == "below_the_tag" else TAG)
    stamp = PROBE_CLOCK.now().isoformat().replace("+00:00", "Z")
    with repository.atomic(), repository.connection() as connection:
        assert marks_store.insert_exposure(connection, {
            "attempt_id": row["source_attempt_id"], "factor_id": row["factor_id"], "workflow_id": row["id"],
            "surface": "why", "hypothesis_version_ids_json": json.dumps(["h1"]), "probe_answered": 0,
            "shown_at": stamp, "created_at": stamp,
        })
    probe_attempt_id = _answer_probe(ctx, repository, row)
    set_algorithm_version(paths, TAG)
    vault = load_vault(paths.root)

    _stored, effective, qualifying = _episode_reading(vault, repository, probe_attempt_id)
    assert effective.contamination == {"answer_exposed": "followup_causes_shown_before_probe"}
    assert (effective.updates_belief, qualifying) == (False, 0)


# -- R2 (the tag's review): the router reads an episode's effective posterior, not the stored full-weight one -------


def _router_readings(vault, repository, row, now_iso):
    """(the miss-cause sensor's probe posterior, the decision-state snapshot's episode posteriors) for the journey's
    miss, each read with the caller's effective reader as the router's callers pass it."""

    from learnloop.diagnosis.probe_episodes import effective_posterior_reader
    from learnloop.router_objective import decision_state
    from learnloop.router_objective import miss_cause as MC

    effective = effective_posterior_reader(vault, repository)
    source = repository.fetch_practice_attempt(row["source_attempt_id"])
    with repository.connection() as connection:
        sensed = MC.probe_posterior(connection, row["source_attempt_id"], now_iso, effective)
        snapshot = decision_state._lo_rows(connection, [source["learning_object_id"]], {}, now_iso, effective)
    episodes = snapshot[source["learning_object_id"]].get("episodes") or []
    return sensed, {episode["id"]: episode["posterior"] for episode in episodes}


@BOTH_TAGS
def test_r2_the_router_reads_an_exposed_answer_as_no_update(tmp_path, monkeypatch, tag):
    _DiscriminatingInstrument(monkeypatch)
    paths, ctx, vault, repository, result, row = _probe_journey(tmp_path, monkeypatch, BELOW)
    _expose(ctx, repository, result, row, "shown_anyway")
    probe_attempt_id = _answer_probe(ctx, repository, row)
    stored = repository.probe_observation_for_attempt(probe_attempt_id)
    assert stored.posterior_after != stored.posterior_before  # recorded below the tag: a full-weight update
    set_algorithm_version(paths, tag)
    vault = load_vault(paths.root)
    now_iso = (PROBE_CLOCK.now() + timedelta(hours=1)).isoformat().replace("+00:00", "Z")

    sensed, snapshot = _router_readings(vault, repository, row, now_iso)
    presentation = repository.probe_presentation(row["presentation_id"])
    episode = repository.probe_episode(presentation.probe_episode_id)
    assert sensed is not None and sensed["episode_id"] == episode.id
    if tag == TAG:
        # The exposed answer contributes nothing: the posterior before it, as recorded.
        assert sensed["source"] == "effective"
        expected = stored.posterior_before
    else:
        # mvp-0.60: the stored full-weight posterior (the answer's own receipt, or the completion's).
        assert sensed["source"] in ("observation", "completion")
        expected = stored.posterior_after
    assert _by_class(repository, stored.posterior_before) != pytest.approx(_by_class(repository, stored.posterior_after))
    assert sensed["p"] == pytest.approx(_by_class(repository, expected))
    # The episode completed on that answer: its status and completion stay as recorded (nothing reopens it), and the
    # sensor names the same instant either way, so a decision's identity marks do not move.
    assert episode.status == "complete" and episode.id not in snapshot
    assert sensed["at"] == str(episode.completed_at)

    # The decision-state snapshot lists open episodes: the same episode, read as if it were still open.
    with repository.connection() as connection:
        connection.execute("UPDATE probe_episodes SET status = 'in_progress' WHERE id = ?", (episode.id,))
    _sensed, snapshot = _router_readings(vault, repository, row, now_iso)
    assert snapshot[episode.id] == pytest.approx(dict(expected), abs=1e-5)  # the snapshot rounds its values


def _by_class(repository, posterior):
    from learnloop.router_objective import miss_cause as MC

    with repository.connection() as connection:
        scopes = {str(row[0]): MC._class(row[1]) for row in connection.execute(
            "SELECT id, cause_scope FROM causal_hypotheses")}
    totals = {name: 0.0 for name in MC.CLASSES}
    for key, mass in posterior.items():
        totals[scopes.get(str(key), MC.UNKNOWN)] += float(mass)
    total = sum(totals.values())
    return {name: value / total for name, value in totals.items()}


# -- R3 (the tag's review): the remaining readers of the stored flags read the effective view ----------------------


def _exposed_below_then(tmp_path, monkeypatch, tag):
    """A probe answer exposed ("Show anyway") and recorded below the tag, the vault then at ``tag``."""

    paths, ctx, vault, repository, result, row = _probe_journey(tmp_path, monkeypatch, BELOW)
    _expose(ctx, repository, result, row, "shown_anyway")
    probe_attempt_id = _answer_probe(ctx, repository, row)
    set_algorithm_version(paths, tag)
    return paths, ctx, load_vault(paths.root), repository, row, probe_attempt_id


@BOTH_TAGS
def test_r3_the_serving_counts_leave_out_an_exposed_answer(tmp_path, monkeypatch, tag):
    from learnloop.diagnosis.probe_episodes import effective_qualifying_total
    from learnloop.diagnosis.probe_presentations import probe_serving_block_reason

    paths, ctx, vault, repository, row, probe_attempt_id = _exposed_below_then(tmp_path, monkeypatch, tag)
    session_id = repository.fetch_practice_attempt(probe_attempt_id)["session_id"]
    expected = 0 if tag == TAG else 1
    assert effective_qualifying_total(vault, repository) == expected
    if session_id is not None:
        assert effective_qualifying_total(vault, repository, session_id=session_id) == expected
    # The onboarding ceiling at one observation, before any ordinary practice: an exposed answer no longer spends it.
    monkeypatch.setattr(vault.config.probe.episode, "onboarding_practice_ceiling_observations", 1)
    monkeypatch.setattr(repository, "ordinary_practice_attempt_count", lambda: 0)
    reason = probe_serving_block_reason(vault, repository, session_id=None)
    assert reason == (None if tag == TAG else "onboarding_practice_ceiling")


@BOTH_TAGS
def test_r3_the_inspector_shows_the_effective_flags(tmp_path, monkeypatch, tag):
    paths, ctx, vault, repository, row, probe_attempt_id = _exposed_below_then(tmp_path, monkeypatch, tag)
    ctx.load(paths.root)  # this process's vault reads the tag
    episode_id = repository.probe_presentation(row["presentation_id"]).probe_episode_id
    (shown,) = _call(ctx, "inspect_entity", {"id": episode_id})["detail"]["observations"]
    flags = (shown["eligibleForCompletion"], shown["updatesBelief"], shown["exposureReason"])  # the wire's camelCase
    assert flags == ((False, False, "followup_feedback_shown_anyway") if tag == TAG else (True, True, None))
    stored = repository.probe_observation_for_attempt(probe_attempt_id)
    assert shown["recordedEntropyAfter"] == stored.entropy_after  # what was recorded when it was written


@BOTH_TAGS
def test_r3_the_baseline_projection_reads_the_effective_view(tmp_path, monkeypatch, tag):
    from learnloop.diagnosis import diagnostic_pack as DP

    paths, ctx, vault, repository, row, probe_attempt_id = _exposed_below_then(tmp_path, monkeypatch, tag)
    episode_id = repository.probe_presentation(row["presentation_id"]).probe_episode_id
    (stored_row,) = repository.probe_observations_for_episode(episode_id)
    facet = (stored_row.get("target_facets") or ["recall"])[0]
    monkeypatch.setattr(repository, "diagnostic_pack_pin_for_run", lambda _run_id: {"probe_episode_id": episode_id})
    spec = {"rubric": {"max_points": 4}, "solution_recipes": [{"all_of": [{"facet": facet, "capability": facet}]}]}
    projection = DP._baseline_evidence_projection(repository, {"id": "run"}, spec, vault)
    status = projection[(facet, facet)]["status"]
    # At the tag the exposed answer is no clean evidence: the cell is contested (linked to its receipt).
    assert (status == "contested") is (tag == TAG)


# -- K5-8: a request for an easier or harder variant is no review of its source item --------------------------------


def _day(days):
    return FrozenClock(NOW + timedelta(days=days))


class _ReviewLog:
    """Every FSRS review the grade core applies, as (memory before, rating, elapsed days)."""

    def __init__(self, monkeypatch):
        from learnloop.attempts import attempts as attempts_module

        self.reviews = []
        self._original = attempts_module.apply_review
        monkeypatch.setattr(attempts_module, "apply_review", self)

    def __call__(self, memory, rating, elapsed_days, weights):
        self.reviews.append((memory, rating, round(float(elapsed_days), 9)))
        return self._original(memory, rating, elapsed_days, weights)


def _item_clock(repository, item_id=ITEM_ID):
    state = repository.practice_item_state(item_id)
    return (state.stability, state.difficulty, state.retrievability, state.due_at, state.last_attempt_at)


def _clock_history(tmp_path, monkeypatch, tag, *, between):
    """Day 0 an answer on the item, day 4 ``between`` (a variant request, an ordinary self-report, or nothing), day 7
    an answer: (the reviews and the item's state live, the same after a rebuild, the attempt ``between`` wrote)."""

    from learnloop.content.authoring.rung_variants import request_rung_variant

    log = _ReviewLog(monkeypatch)
    paths, vault, repository = _vault(tmp_path, tag, name=f"vault_{between}")
    _self_graded(vault, repository, points=4, clock=_day(0))
    attempt_id = None
    if between == "variant_request":
        attempt_id = request_rung_variant(vault, repository, practice_item_id=ITEM_ID, direction="easier",
                                          clock=_day(4))["attempt_id"]
    elif between == "self_report":
        attempt_id = complete_self_graded_attempt(
            vault, repository,
            AttemptDraft(practice_item_id=ITEM_ID, learner_answer_md="I think I know this.",
                         attempt_type="self_report"),
            SelfGradeInput(criterion_points={"correctness": 2}, confidence=3), clock=_day(4),
        ).attempt_id
    _self_graded(vault, repository, points=4, clock=_day(7))
    live = (list(log.reviews), _item_clock(repository))
    log.reviews.clear()
    rebuild_all_derived_state(load_vault(paths.root), Repository(paths.sqlite_path), clock=_day(8))
    return live, (list(log.reviews), _item_clock(repository)), attempt_id


@BOTH_TAGS
def test_k5_8_a_variant_request_is_no_review_of_its_source_item(tmp_path, monkeypatch, tag):
    without_live, without_rebuilt, _ = _clock_history(tmp_path, monkeypatch, tag, between="nothing")
    live, rebuilt, attempt_id = _clock_history(tmp_path, monkeypatch, tag, between="variant_request")

    assert live == rebuilt  # live and replay agree at both tags
    assert without_live == without_rebuilt
    reviews, state = live
    if tag == TAG:
        # The request applies no review and leaves the clock, memory and due date as they were: the day-7 review
        # reads 7 days from the day-0 answer and its memory, as if the request had not been made.
        assert (reviews, state) == without_live
        assert [elapsed for _memory, _rating, elapsed in reviews] == [0.0, 7.0]
    else:
        # mvp-0.60, today: the request is a review of the source item (a soft failure on day 4), so day 7 reads 3
        # days from the request and the request's memory, and the due date follows (ledger K5-8).
        assert [elapsed for _memory, _rating, elapsed in reviews] == [0.0, 4.0, 3.0]
        assert state != without_live[1]
        assert state[4] == without_live[1][4]  # day 7 is the last attempt either way
    assert attempt_id is not None


@BOTH_TAGS
def test_k5_8_an_ordinary_self_report_is_still_a_review(tmp_path, monkeypatch, tag):
    live, rebuilt, _ = _clock_history(tmp_path, monkeypatch, tag, between="self_report")
    assert live == rebuilt
    assert [elapsed for _memory, _rating, elapsed in live[0]] == [0.0, 4.0, 3.0]


@BOTH_TAGS
def test_k5_8_a_quarantined_answer_kept_its_review_live_and_keeps_it_on_replay(tmp_path, monkeypatch, tag):
    """Case B of the inventory, checked rather than changed: no stored fact says such an answer got no review live.

    The attempt path applies its review from fixed practice inputs, so every answer's observation is written
    ``practice``-eligible (none carries a before-response condition), and a quarantine is appended later, to the
    grade channel only: the answer was reviewed at submission, and replay reviews it again. Live and replay agree."""

    from learnloop.attempts.grade_resolution import quarantine_observation

    log = _ReviewLog(monkeypatch)
    paths, vault, repository = _vault(tmp_path, tag)
    _self_graded(vault, repository, points=4, clock=_day(0))
    quarantined = _self_graded(vault, repository, points=2, clock=_day(4)).attempt_id
    observation = repository.observation_by_attempt(quarantined)
    assert observation["evidence_eligibility"] == "practice"
    assert quarantine_observation(repository, observation_id=observation["id"], surface_id=None,
                                  reason="learner_contested", clock=_day(5))
    _self_graded(vault, repository, points=4, clock=_day(7))
    live = (list(log.reviews), _item_clock(repository))
    log.reviews.clear()
    rebuild_all_derived_state(load_vault(paths.root), Repository(paths.sqlite_path), clock=_day(8))

    assert (list(log.reviews), _item_clock(repository)) == live
    assert [elapsed for _memory, _rating, elapsed in live[0]] == [0.0, 4.0, 3.0]


def test_k5_8_a_variant_request_writes_the_same_belief_at_both_tags(tmp_path):
    from learnloop.content.authoring.rung_variants import request_rung_variant

    written = {}
    for tag in (BELOW, TAG):
        paths, vault, repository = _vault(tmp_path, tag, name=f"vault_{tag}")
        _self_graded(vault, repository, points=4, clock=_day(0))
        attempt_id = request_rung_variant(vault, repository, practice_item_id=ITEM_ID, direction="harder",
                                          clock=_day(4))["attempt_id"]
        attempt = repository.fetch_practice_attempt(attempt_id)
        assert repository.rung_variant_request_for_attempt(attempt_id) is not None
        written[tag] = (
            attempt["attempt_type"], attempt["rubric_score"], attempt["correctness"],
            _rows(paths, "SELECT logit_mean, logit_variance, evidence_count FROM learning_object_mastery "
                         "WHERE learning_object_id = ?", attempt["learning_object_id"]),
            _rows(paths, "SELECT facet_id, capability_key, recall_mean, recall_variance FROM facet_recall_state "
                         "ORDER BY facet_id, capability_key, practice_item_id"),
        )
    assert written[BELOW] == written[TAG]
    assert written[TAG][0] == "self_report"


# -- the upgrade: one vault holding every case at mvp-0.60, upgraded to mvp-0.61, then rebuilt again -----------------


def _at(hours):
    return FrozenClock(NOW + timedelta(hours=hours))


def _exam_item(root):
    upsert_practice_item(
        root,
        {
            "id": "pi_exam_q3", "learning_object_id": "lo_svd_definition", "subjects": None,
            "practice_mode": "constructed_response", "attempt_types_allowed": ["independent_attempt", "dont_know"],
            "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
            "prompt": "Exam question 3 about SVD.", "expected_answer": "Model solution.",
            "tags": ["exam_question", "exam_q:3"],
            "grading_rubric": {"max_points": 4, "criteria": [{"id": "correctness", "points": 4,
                                                                "description": "Correct."}], "fatal_errors": []},
            "created_at": "2026-05-19T12:00:00Z", "updated_at": "2026-05-19T12:00:00Z",
        },
        clock=CLOCK,
    )


def _unassessed_diagnosed_attempt(vault, repository, *, clock):
    """A diagnosed miss whose one hypothesis claims its one criterion fell short, the criterion left unassessed."""

    attempt_id = "att_unassessed_diagnosed"
    return apply_attempt(
        vault, repository,
        ApplyAttemptInput(
            draft=AttemptDraft(practice_item_id="pi_svd_apply_001", learner_answer_md="U Sigma V, by another route."),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=0, criterion_points={"uses_factorization": 0.0},
                evidence_rows=[{
                    "id": f"ge_{attempt_id}", "criterion_id": "uses_factorization", "points_awarded": 0.0,
                    "evidence": "Not located on this route.", "notes": None, "local_grader_id": "test",
                    "grader_tier": 1, "created_at": clock.now().isoformat(),
                }],
                error_attributions=[GradeAttribution(
                    error_type="conceptual_slip", severity=0.7, evidence="The factorization is not used.",
                    is_misconception=True, misconception_statement="Treats V and V transpose as one.",
                    resolution_status="unresolved", cause_scope="learner_state", operation="transpose_confusion",
                    model_reported_causal_confidence=0.65,
                    candidate_causes=[{"statement": "Treats V and V transpose as one.", "cause_scope": "learner_state",
                                       "target_ref": {"kind": "criterion", "criterion_id": "uses_factorization"}}],
                    postdictive_claims=[{"criterion_id": "uses_factorization", "must": "not_full_credit"}],
                )],
                grader_confidence=0.9, confidence=4, manual_review_reason=None,
                feedback_md="Use the factorization.", repair_suggestions=[],
            ),
            unverified_criterion_ids=("uses_factorization",),
        ),
        clock=clock,
    )


VARIANT_SOURCE = "pi_svd_clone_001"


def _every_case_vault(tmp_path, monkeypatch):
    """The follow-up journey's vault at mvp-0.60, holding every case the tag reads differently; the attempt id of
    each."""

    paths, ctx, vault, repository, result, row = _probe_journey(tmp_path, monkeypatch, BELOW)
    cases = {}
    _expose(ctx, repository, result, row, "shown_anyway")
    cases["probe_shown_anyway"] = _answer_probe(ctx, repository, row)
    cases["miss_probe_shown_anyway"] = result.attempt_id
    vault, _ = ctx.require_vault()
    second, outcome = miss_with_rivals(vault, repository, attempt_id="att_second_miss")
    author = AuthorFake()
    author.calls = 1  # its question and surface are the second ones, not a copy of the first probe's
    _generate(ctx, repository, fake=author)
    second_row = wf.get(repository, outcome.workflow_id)
    assert second_row["presentation_id"] and second_row["presentation_id"] != row["presentation_id"]
    _expose(ctx, repository, second, second_row, "reveal")
    cases["probe_reveal"] = _answer_probe(ctx, repository, second_row)
    cases["miss_probe_reveal"] = second.attempt_id

    vault, _ = ctx.require_vault()
    cases["unassessed_diagnosed"] = _unassessed_diagnosed_attempt(vault, repository, clock=_at(2)).attempt_id
    # On a learning object no regrade below replays, so the live 0.0 is still on the attempt at the upgrade (a
    # replay at mvp-0.60 writes 1.0 over it: test_k5_12_a_zero_an_earlier_rebuild_wrote_over_is_not_restored).
    cases["zero_confidence"] = complete_attempt_with_ai_fallback(
        vault, repository,
        AttemptDraft(practice_item_id="pi_svd_clone_001", learner_answer_md="SVD factors a matrix."),
        SelfGradeInput(criterion_points={}, confidence=3), runtime=_ready_runtime(),
        ai_client=_ProbeGrader({}, confidence=0.0, full=True), clock=_at(3),
    ).attempt_id
    # A request for a harder variant of the item just answered: below the tag a review of it.
    from learnloop.content.authoring.rung_variants import request_rung_variant

    cases["clone_state_before_request"] = _item_clock(repository, VARIANT_SOURCE)
    cases["variant_request"] = request_rung_variant(vault, repository, practice_item_id=VARIANT_SOURCE,
                                                    direction="harder", clock=_at(3.5))["attempt_id"]
    cases["regraded_self_grade"] = _self_graded(vault, repository, clock=_at(4)).attempt_id
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(cases["regraded_self_grade"]),
                    runtime=_ready_runtime(), client=_Grader(points=4), grading_source="ai", clock=_at(5))

    _exam_item(paths.root)
    _blueprint(paths)
    add_followup_item(paths.root)
    add_followup_item(paths.root, "pi_svd_cert_001")  # the certifying surface, on the recipe's recall cell
    vault = load_vault(paths.root)
    sync_vault_state(vault, repository, clock=_at(6))
    cases["regraded_exam_answer"] = _seed_exam_answer(vault, repository)
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(cases["regraded_exam_answer"]),
                    runtime=_ready_runtime(), client=_Grader(points=4), grading_source="ai", clock=_at(7))

    certifying = _attempt(vault, repository, "pi_svd_cert_001", points=4, clock=_at(8))
    make_grade_certain(vault, repository, certifying.attempt_id, clock=_at(8))
    assert current_certificate(vault, repository, vault.learning_objects[LO_ID]) is not None
    schedule_certification_cold_probes(vault, repository, clock=_at(8))
    due = FrozenClock(NOW + timedelta(hours=8, days=resolve_cold_probe_parameters(repository).horizon_days))
    (task,) = [task for task in repository.followup_tasks_of_kind("certification_cold_probe")
               if task["status"] == "pending"]
    cases["unassessed_certificate_probe"] = _unassessed_answer(
        vault, repository, str(task["selected_item_id"]), clock=due).attempt_id
    assert repository.certification_cold_probe_outcome_for_attempt(cases["unassessed_certificate_probe"])
    return paths, cases


#: The grade channel and derived tables an idempotent second rebuild must leave as they are (row counts).
_COUNTED = ("activity_observations", "raw_grade_events", "grade_interpretations", "measurement_events",
            "probe_observations", "causal_discriminating_observations", "certification_cold_probe_outcomes")


def _reading(paths, cases):
    """What the five fixes read, per case, at the vault's tag now."""

    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    reading = {}
    from learnloop.diagnosis.probe_episodes import effective_posterior_reader
    from learnloop.router_objective import miss_cause as MC

    reader = effective_posterior_reader(vault, repository)
    now_iso = (NOW + timedelta(days=60)).isoformat().replace("+00:00", "Z")
    for name in ("probe_shown_anyway", "probe_reveal"):
        stored, effective, qualifying = _episode_reading(vault, repository, cases[name])
        presentation = repository.probe_presentation(str(repository.fetch_practice_attempt(cases[name])
                                                         ["probe_presentation_id"]))
        episode = repository.probe_episode(presentation.probe_episode_id)
        with repository.connection() as connection:
            sensed = MC.probe_posterior(connection, cases[f"miss_{name}"], now_iso, reader)
        reading[name] = {
            "stored": (stored.contamination, stored.independent_evidence_discount, stored.updates_belief,
                       stored.eligible_for_completion),
            "effective": (effective.contamination, effective.independent_evidence_discount, effective.updates_belief,
                          effective.eligible_for_completion),
            "qualifying": qualifying,
            # What the episode believes now, and what the router's miss-cause sensor reads of it.
            "posterior": {key: round(value, 9) for key, value in episode_posterior(vault, repository, episode)
                          .posterior.items()},
            "sensor": (sensed["source"], {key: round(value, 9) for key, value in sensed["p"].items()})
            if sensed is not None else None,
            "posterior_before_answer": {key: round(value, 9) for key, value in stored.posterior_before.items()},
        }
    episode = causal_episode_for_attempt(repository, cases["unassessed_diagnosed"])
    receipt = episode["receipt"]
    (claiming,) = [key for key, row in receipt["trace_consistency_detail"]["by_hypothesis"].items()
                   if row["claims_attributed"] == 1]
    (outcome,) = receipt["criterion_outcomes"]
    reading["unassessed_diagnosed"] = (receipt["trace_consistency"][claiming], outcome["assessable"],
                                       outcome["passed"])
    reading["zero_confidence"] = (
        repository.fetch_practice_attempt(cases["zero_confidence"])["grader_confidence"],
        [row["model_confidence"] for row in _raw_events(paths, cases["zero_confidence"])],
    )
    reading["regraded_self_grade"] = [row["grader_provider"]
                                      for row in _raw_events(paths, cases["regraded_self_grade"])]
    reading["regraded_exam_answer"] = _exam_channel(paths, cases["regraded_exam_answer"])
    probe = repository.certification_cold_probe_outcome_for_attempt(cases["unassessed_certificate_probe"])
    reading["unassessed_certificate_probe"] = (probe["verdict"], probe["policy_version"])
    reading["variant_request"] = _item_clock(repository, VARIANT_SOURCE)
    return reading


def _derived(paths):
    """The derived state a rebuild writes (its write times aside) and the ledgers' row counts."""

    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        mastery = connection.execute(
            "SELECT learning_object_id, logit_mean, logit_variance, evidence_count FROM learning_object_mastery "
            "ORDER BY learning_object_id").fetchall()
        recall = connection.execute(
            "SELECT facet_id, capability_key, practice_item_id, recall_mean, recall_variance, consecutive_failures "
            "FROM facet_recall_state ORDER BY facet_id, capability_key, practice_item_id").fetchall()
        items = connection.execute(
            "SELECT practice_item_id, due_at, stability, difficulty FROM practice_item_state "
            "ORDER BY practice_item_id").fetchall()
        cells = connection.execute(
            "SELECT facet_id, capability, direct_positive_mass, direct_negative_mass, embedded_positive_mass, "
            "embedded_negative_mass, certification_credit, independent_surface_groups_json "
            "FROM facet_capability_evidence ORDER BY facet_id, capability").fetchall()
        counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in _COUNTED}
    return {"mastery": mastery, "recall": recall, "items": items, "cells": cells, "counts": counts}


def test_the_upgrade_moves_every_case_once_and_a_second_rebuild_moves_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(activation_journal, "_COMPLETER", upgrades.complete_interrupted_activation)
    _DiscriminatingInstrument(monkeypatch)  # so a probe answer's update can be seen in the posteriors
    paths, cases = _every_case_vault(tmp_path, monkeypatch)
    before = _reading(paths, cases)
    before_derived = _derived(paths)

    result = upgrade(paths.root, to=TAG, clock=FrozenClock(NOW + timedelta(days=40)))
    assert result.upgraded and (result.from_version, result.to_version) == (BELOW, TAG)
    assert Repository(paths.sqlite_path).has_whole_vault_rebuild(algorithm_version=TAG)
    after = _reading(paths, cases)
    derived = _derived(paths)
    # What the upgrade moved in this vault's derived state: the regraded exam answer reaches its channel (one
    # observation, a raw grade event, an interpretation, measurement events) and with it the recall cell it
    # exercises, the regraded self-grade appends its "ai" raw grade event and interpretation, and the learning
    # object both regrades replayed moves its mastery; the variant request's source item loses that request's review
    # (its state goes back to the answer before it). The probe, receipt and certificate cases store nothing derived.
    moved = {key for key in derived if derived[key] != before_derived[key]}
    assert moved == {"mastery", "recall", "cells", "counts", "items"}
    assert [row for row in derived["items"] if row not in before_derived["items"]] == [
        row for row in derived["items"] if row[0] == VARIANT_SOURCE]
    assert {name: derived["counts"][name] - before_derived["counts"][name] for name in _COUNTED} == {
        "activity_observations": 1, "raw_grade_events": 2, "grade_interpretations": 2, "measurement_events": 6,
        "probe_observations": 0, "causal_discriminating_observations": 0, "certification_cold_probe_outcomes": 0,
    }

    rebuild_all_derived_state(load_vault(paths.root), Repository(paths.sqlite_path),
                              clock=FrozenClock(NOW + timedelta(days=41)))
    assert _reading(paths, cases) == after
    assert _derived(paths) == derived

    exposed = {"probe_shown_anyway": "followup_feedback_shown_anyway", "probe_reveal": "post_reveal_not_independent"}
    for name, reason in exposed.items():
        assert {key: before[name][key] for key in ("stored", "effective", "qualifying")} == {
            "stored": (None, 1.0, True, True), "effective": (None, 1.0, True, True), "qualifying": 1}
        moved = {key: after[name][key] for key in ("stored", "effective", "qualifying")}
        assert moved == {"stored": (None, 1.0, True, True),
                         "effective": ({"answer_exposed": reason}, 0.0, False, False), "qualifying": 0}
        # The episode's belief and the router's sensor no longer carry the exposed answer: the sensor reads the
        # episode's effective posterior (the posterior before that answer), where before the upgrade it read the
        # stored full-weight one.
        assert after[name]["posterior"] != before[name]["posterior"]
        assert before[name]["sensor"][0] in ("observation", "completion") and after[name]["sensor"][0] == "effective"
        assert after[name]["sensor"][1] != before[name]["sensor"][1]
    assert before["unassessed_diagnosed"] == ("consistent_with_claims", True, False)
    assert after["unassessed_diagnosed"] == ("unknown", False, False)
    assert before["zero_confidence"] == after["zero_confidence"] == (0.0, [0.0])
    assert before["regraded_self_grade"] == ["self", "self"]
    assert after["regraded_self_grade"] == ["self", "self", "ai"]
    assert before["regraded_exam_answer"] == []
    assert after["regraded_exam_answer"] == [("assessment", "ai", 4)]
    # The outcome store is append-only and a rebuild records no probe again: the verdict keeps its rule.
    assert before["unassessed_certificate_probe"] == after["unassessed_certificate_probe"] == (
        "held", "certification_cold_probe_policy_v1")
    # Below the tag the request was a review of its source (its clock at the request); at the tag the item's clock,
    # memory and due date are those of the answer before the request, exactly.
    assert before["variant_request"] != cases["clone_state_before_request"]
    assert before["variant_request"][4] == _at(3.5).now().isoformat().replace("+00:00", "Z")
    assert after["variant_request"] == cases["clone_state_before_request"]


def test_k5_12_a_zero_an_earlier_rebuild_wrote_over_is_not_restored(tmp_path):
    """The fix stops replay from turning 0.0 into 1.0; it cannot read back a 0.0 a rebuild below the tag already wrote
    over on the attempt row (the first raw grade event still holds it)."""

    paths, vault, repository = _vault(tmp_path, BELOW)
    attempt_id = _model_graded(vault, repository, points=4, confidence=0.0).attempt_id
    _rebuild(paths)
    set_algorithm_version(paths, TAG)
    _rebuild(paths)
    assert repository.fetch_practice_attempt(attempt_id)["grader_confidence"] == 1.0
    assert [row["model_confidence"] for row in _raw_events(paths, attempt_id)] == [0.0, 1.0]
