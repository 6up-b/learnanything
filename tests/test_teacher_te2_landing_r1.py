"""Teacher TE2 landing ruling R1: a regrade publishes the replacement grade's own calibration identity.

Codex's final verify (job ``20261106-055937-v8K8dy``) reopened F7 on regrades: a regrade's new blind record names the
grader that produced the replacement grade, but the attempt's active grade interpretation kept the original grader's
identity and calibration, and replay preserved it. Its two reproductions are the first two tests here:

- a lesson probe answered with split grading off (the joint grader), split switched on, then regraded blind;
- a lesson probe in a split vault (graded blind under the mvp-2.0 identity), regraded blind under the practice
  door's newer reference-policy prompt (the "ordinary blind regrade" of the verify).

After the fix the regrade's publication appends and activates a raw grade event and interpretation carrying the
replacement grade's identity (prompt, schema, grader identity hash and calibration model); ordinary replay mints no
duplicate. The third test is R1's check on an ordinary, non-probe regrade (no such defect: it passes on the pre-fix
source). The fourth is FG1's presentation path (which shares ``_dual_write_probe_grade``): its first write carries
the submission's identity, and its regrade the replacement's. Fakes only; no model call.
"""

from __future__ import annotations

import json

from learnloop.attempts import grader_calibration as gc
from learnloop.attempts.blind_grading import BLIND_CALIBRATION_PROMPT_VERSION, BLIND_GRADER_OUTPUT_SCHEMA_VERSION
from learnloop.attempts.regrade import regrade_attempt
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from tests.split_live_helpers import ReadyRuntime
from tests.teacher_fakes import close_turn
from tests.teacher_te2_probes_helpers import _Lesson, _probe, probe_turn
from tests.teacher_te2_review_fixes_helpers import _cells, _identity_model
from tests.ux_phase1_support import set_config


def _regrade_identity(vault) -> str:
    """The calibration prompt identity a blind regrade in ``vault`` grades under (reference policy + route rules)."""

    from learnloop.attempts.grading_support import (
        REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION,
        route_rules_suffix,
        route_rules_version,
    )

    rules = route_rules_version(vault)
    return f"{REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION}{route_rules_suffix(rules)}" if rules else (
        REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION)


def _active(repository, attempt_id):
    """(prompt, schema, grader identity hash, contributing model ids) of the attempt's active interpretation."""

    with repository.connection() as connection:
        row = connection.execute(
            "SELECT r.grading_prompt_version, r.grader_output_schema_version, r.grader_identity_hash, "
            "i.reference_prior_ids_json, i.calibration_model_id FROM activity_observations o "
            "JOIN grade_interpretations i ON i.id = o.active_interpretation_id "
            "JOIN raw_grade_events r ON r.id = i.raw_grade_event_id "
            "WHERE r.attempt_id = ? ORDER BY r.rowid DESC LIMIT 1", (attempt_id,)).fetchone()
    assert row is not None, "no active interpretation"
    return row[0], row[1], row[2], json.loads(row[3] or "[]"), row[4]


def _events(repository, attempt_id) -> int:
    with repository.connection() as connection:
        return connection.execute("SELECT COUNT(*) FROM raw_grade_events WHERE attempt_id = ?",
                                  (attempt_id,)).fetchone()[0]


def _regrade(vault, repository, attempt_id, clock):
    row = repository.fetch_practice_attempt(attempt_id)
    from tests.diagnosis_fakes import ReviewFakeClient  # a fake blind grader answering from the context it is sent

    return regrade_attempt(vault, repository, row, runtime=ReadyRuntime(), client=ReviewFakeClient(),
                           grading_source="ai", clock=clock)


def test_a_lesson_probe_regraded_blind_after_split_is_switched_on_carries_the_blind_calibration(tmp_path):
    lesson = _Lesson(tmp_path, [probe_turn], config={("diagnosis", "split_enabled"): False})
    lesson.generate()
    lesson.look()
    probe = _probe(lesson)
    joint_gih, joint_model = _identity_model(lesson.repository, prompt=gc.GRADING_PROMPT_VERSION,
                                             schema=gc.GRADER_OUTPUT_SCHEMA_VERSION, tag="joint")
    lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    assert _active(lesson.repository, probe.attempt_id)[:3] == (
        gc.GRADING_PROMPT_VERSION, gc.GRADER_OUTPUT_SCHEMA_VERSION, joint_gih)
    set_config(lesson.paths.root, {("diagnosis", "split_enabled"): True})
    vault = load_vault(lesson.paths.root)
    prompt = _regrade_identity(vault)
    blind_gih, blind_model = _identity_model(lesson.repository, prompt=prompt, schema=BLIND_GRADER_OUTPUT_SCHEMA_VERSION,
                                             tag="blind-regrade")
    _regrade(vault, lesson.repository, probe.attempt_id, lesson.clock())
    record = lesson.repository.latest_blind_grade_record(probe.attempt_id)["record"]
    assert record["calibration_prompt_version"] == prompt
    active_prompt, active_schema, active_gih, contributing, _model = _active(lesson.repository, probe.attempt_id)
    assert (active_prompt, active_schema, active_gih) == (prompt, BLIND_GRADER_OUTPUT_SCHEMA_VERSION, blind_gih)
    assert blind_model in contributing and joint_model not in contributing
    # The original grade event and the replacement's: the regrade appended one.
    assert _events(lesson.repository, probe.attempt_id) == 2
    live = _cells(lesson)
    rebuild_all_derived_state(load_vault(lesson.paths.root), lesson.repository)
    assert _events(lesson.repository, probe.attempt_id) == 2  # ordinary replay mints no duplicate
    assert _active(lesson.repository, probe.attempt_id)[:3] == (prompt, BLIND_GRADER_OUTPUT_SCHEMA_VERSION, blind_gih)
    assert _cells(lesson) == live


def test_a_lesson_probe_regraded_blind_under_a_newer_prompt_carries_the_newer_calibration(tmp_path):
    """Codex's second reproduction, split on throughout: the probe's first grade is the mvp-2.0 blind identity
    (``vault_grading_calibration_identity``), its regrade the practice door's reference-policy prompt."""

    lesson = _Lesson(tmp_path, [probe_turn])
    lesson.generate()
    lesson.look()
    probe = _probe(lesson)
    first_gih, first_model = _identity_model(lesson.repository, prompt=BLIND_CALIBRATION_PROMPT_VERSION,
                                             schema=BLIND_GRADER_OUTPUT_SCHEMA_VERSION, tag="blind-v2")
    lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    assert _active(lesson.repository, probe.attempt_id)[:3] == (
        BLIND_CALIBRATION_PROMPT_VERSION, BLIND_GRADER_OUTPUT_SCHEMA_VERSION, first_gih)
    vault = load_vault(lesson.paths.root)
    prompt = _regrade_identity(vault)
    assert prompt != BLIND_CALIBRATION_PROMPT_VERSION
    new_gih, new_model = _identity_model(lesson.repository, prompt=prompt, schema=BLIND_GRADER_OUTPUT_SCHEMA_VERSION,
                                         tag="blind-reference-policy")
    _regrade(vault, lesson.repository, probe.attempt_id, lesson.clock())
    active_prompt, active_schema, active_gih, contributing, _model = _active(lesson.repository, probe.attempt_id)
    assert (active_prompt, active_schema, active_gih) == (prompt, BLIND_GRADER_OUTPUT_SCHEMA_VERSION, new_gih)
    assert new_model in contributing and first_model not in contributing
    assert _events(lesson.repository, probe.attempt_id) == 2
    live = _cells(lesson)
    rebuild_all_derived_state(load_vault(lesson.paths.root), lesson.repository)
    assert _events(lesson.repository, probe.attempt_id) == 2
    assert _active(lesson.repository, probe.attempt_id)[:3] == (prompt, BLIND_GRADER_OUTPUT_SCHEMA_VERSION, new_gih)
    assert _cells(lesson) == live


def test_an_ordinary_practice_regrade_already_carries_the_newer_calibration(tmp_path):
    """R1's check on an ordinary, non-probe regrade: no such defect. Its replay re-applies the attempt, and
    ``_dual_write_grade_channel`` re-mints the grade event under the identity the new blind record names, so the
    active interpretation is the replacement grade's before and after a rebuild (passes on the pre-fix source).
    That re-mint happens on every replay, so a rebuild appends one more event each time: recorded for the
    follow-up batch (docs/reviews/teacher-te2.md, Landing onto main), not pinned here."""

    from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
    from learnloop.clock import FrozenClock
    from tests.diagnosis_fakes import ReviewFakeClient
    from tests.diagnosis_split_helpers import at
    from tests.split_live_helpers import split_vault, submit

    paths, vault, repository = split_vault(tmp_path, version=LATEST_ALGORITHM_VERSION)
    set_config(paths.root, {("diagnosis", "grading_support"): False})  # the mvp-2.0 blind prompt
    vault = load_vault(paths.root)
    old_gih, old_model = _identity_model(repository, prompt=BLIND_CALIBRATION_PROMPT_VERSION,
                                         schema=BLIND_GRADER_OUTPUT_SCHEMA_VERSION, tag="blind-v2")
    attempt = submit(vault, repository, ReviewFakeClient(), item_id="pi_svd_compute_001", when=at(1))
    assert _active(repository, attempt.attempt_id)[:3] == (
        BLIND_CALIBRATION_PROMPT_VERSION, BLIND_GRADER_OUTPUT_SCHEMA_VERSION, old_gih)
    set_config(paths.root, {("diagnosis", "grading_support"): True})  # the newer reference-policy prompt
    vault = load_vault(paths.root)
    prompt = _regrade_identity(vault)
    assert prompt != BLIND_CALIBRATION_PROMPT_VERSION
    new_gih, new_model = _identity_model(repository, prompt=prompt, schema=BLIND_GRADER_OUTPUT_SCHEMA_VERSION,
                                         tag="blind-reference-policy")
    row = repository.fetch_practice_attempt(attempt.attempt_id)
    regrade_attempt(vault, repository, row, runtime=ReadyRuntime(), client=ReviewFakeClient(), grading_source="ai",
                    clock=FrozenClock(at(2)))
    active_prompt, active_schema, active_gih, contributing, _model = _active(repository, attempt.attempt_id)
    assert (active_prompt, active_schema, active_gih) == (prompt, BLIND_GRADER_OUTPUT_SCHEMA_VERSION, new_gih)
    assert new_model in contributing and old_model not in contributing
    rebuild_all_derived_state(load_vault(paths.root), repository)
    assert _active(repository, attempt.attempt_id)[:3] == (prompt, BLIND_GRADER_OUTPUT_SCHEMA_VERSION, new_gih)


def test_fg1s_presentation_path_stamps_the_submissions_identity_and_its_regrade_the_replacements(tmp_path):
    """The re-review's open question: FG1's presentation path passed no identity to ``_dual_write_probe_grade``, so
    a blind grade was stamped (and calibrated) as the joint grader's. Its first write now carries the submission's
    ``grader_identity``; a regrade of it publishes the replacement's, as the lesson probe's does."""

    from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
    from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, ResolvedGrade, apply_attempt
    from learnloop.diagnosis.probe_episodes import (
        commit_presentation,
        eligible_instruments,
        enter_episode,
        episode_hypothesis_set,
        serve_presentation,
    )
    from learnloop.ids import new_ulid
    from tests.probe_robust_cutover_helpers import CLOCK, ITEM_ID, LO_ID, _load

    loaded, repository = _load(tmp_path, version=LATEST_ALGORITHM_VERSION)
    first_gih, first_model = _identity_model(repository, prompt=BLIND_CALIBRATION_PROMPT_VERSION,
                                             schema=BLIND_GRADER_OUTPUT_SCHEMA_VERSION, tag="fg1-blind-v2")
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    eligible = next(entry for entry in eligible_instruments(
        loaded, repository, episode, hypothesis_set=episode_hypothesis_set(repository, episode))
        if entry.item.id == ITEM_ID)
    presentation = commit_presentation(loaded, repository, episode, eligible, clock=CLOCK)
    serve_presentation(repository, presentation.id, clock=CLOCK)
    attempt_id = new_ulid()
    apply_attempt(loaded, repository, ApplyAttemptInput(
        draft=AttemptDraft(practice_item_id=ITEM_ID, learner_answer_md="answer", attempt_type="diagnostic_probe",
                           probe_presentation_id=presentation.id),
        attempt_id=attempt_id,
        grade=ResolvedGrade(rubric_score=4, criterion_points={"correctness": 4.0}, evidence_rows=[],
                            error_attributions=[], grader_confidence=1.0, confidence=4, manual_review_reason=None),
        grading_source="ai",
        grader_identity=(BLIND_CALIBRATION_PROMPT_VERSION, BLIND_GRADER_OUTPUT_SCHEMA_VERSION),
    ), clock=CLOCK)
    assert _events(repository, attempt_id) == 1
    assert _active(repository, attempt_id)[:3] == (
        BLIND_CALIBRATION_PROMPT_VERSION, BLIND_GRADER_OUTPUT_SCHEMA_VERSION, first_gih)
    # (The card's signature outcome schema is not the coarse one the seeded models name, so the calibration lineage
    # is the identity's backoff; the identity hash is what decides which grader's models it may read.)
    del first_model
    # Its regrade (the practice door's blind reference-policy prompt) publishes the replacement's identity.
    vault = load_vault(loaded.root)
    prompt = _regrade_identity(vault)
    new_gih = gc.grader_identity_hash(provider="ai", model_revision=None, prompt_version=prompt,
                                      output_schema_version=BLIND_GRADER_OUTPUT_SCHEMA_VERSION)
    from datetime import timedelta

    from learnloop.clock import FrozenClock

    _regrade(vault, repository, attempt_id, FrozenClock(CLOCK.now() + timedelta(hours=1)))
    assert _active(repository, attempt_id)[:3] == (prompt, BLIND_GRADER_OUTPUT_SCHEMA_VERSION, new_gih)
    assert _events(repository, attempt_id) == 2
    rebuild_all_derived_state(load_vault(loaded.root), repository)
    assert _events(repository, attempt_id) == 2
    assert _active(repository, attempt_id)[:3] == (prompt, BLIND_GRADER_OUTPUT_SCHEMA_VERSION, new_gih)
