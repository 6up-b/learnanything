"""Teacher TE2, the Codex review's findings F1-F5 (docs/reviews/teacher-te2-codex-review.md). Fakes only; no network.

* F1: a lesson probe's answer is reliable canonical evidence from the first serve, live and after a rebuild (not
  merely equal on both sides at zero).
* F2: an answer after the lesson showed text on its topic is recorded as an instructional diagnostic and is no
  qualifying cold outcome for the lesson weight or a lesson forecast; a clean one stays a pure diagnostic.
* F3: the attempt, the item's retirement, the result and the episode commit together, and an answer already
  recorded is finished without a second grade or insert.
* F4: ``resume`` after a probe's result or *Teach it anyway* calls the teacher the outage left owing.
* F5: the probe author and the typed-goal resolver send nothing on a metered route.
"""

from __future__ import annotations

import pytest

from learnloop.attempts.reveal_ledger import record_reveal
from learnloop.db.stores import lessons as store
from learnloop.followup_serve import identity
from learnloop.learner import lesson_weight as LW
from learnloop.teacher import probes as PR
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import DeliverableFake
from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients, close_turn
from tests.teacher_te2_probes_helpers import TAG, _Lesson, _probe, probe_turn
from tests.teacher_te2_review_fixes_helpers import _cells, _identity_model


def _served(tmp_path, **kwargs):
    lesson = _Lesson(tmp_path, [probe_turn], **kwargs)
    lesson.generate()
    lesson.look()
    probe = _probe(lesson)
    assert probe.status == "served"
    return lesson, probe


def _probe_cells(lesson, item_id):
    return [cell for cell in lesson.repository.canonical_facet_recall_states() if cell.practice_item_id == item_id]


# -- F1 -------------------------------------------------------------------------------------------------------------


def test_f1_a_probe_answer_carries_reliable_canonical_mass_live_and_after_a_rebuild(tmp_path):
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    lesson, probe = _served(tmp_path)
    lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    cells = _probe_cells(lesson, probe.item_id)
    assert cells and all(cell.raw_coverage_mass > 0 for cell in cells), cells
    # One calibrated interpretation on a diagnostic administration, before the projection read it.
    assert lesson.rows("SELECT COUNT(*) FROM raw_grade_events WHERE attempt_id = ?", (probe.attempt_id,)) == [(1,)]
    live = _cells(lesson)
    rebuild_all_derived_state(lesson.vault(), lesson.repository)
    assert _cells(lesson) == live
    assert all(cell.raw_coverage_mass > 0 for cell in _probe_cells(lesson, probe.item_id))
    # The rebuild wrote no second grade event.
    assert lesson.rows("SELECT COUNT(*) FROM raw_grade_events WHERE attempt_id = ?", (probe.attempt_id,)) == [(1,)]


# -- F7 (re-review) -------------------------------------------------------------------------------------------------


def test_f7_a_blind_lesson_probe_grade_keeps_the_blind_calibration_identity(tmp_path):
    import json

    from learnloop.attempts import grader_calibration as gc
    from learnloop.attempts.blind_grading import (
        BLIND_CALIBRATION_PROMPT_VERSION,
        BLIND_GRADER_OUTPUT_SCHEMA_VERSION,
        split_grading_active,
    )
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    lesson, probe = _served(tmp_path)
    assert split_grading_active(lesson.vault())  # the blind grader grades this vault's probe answers
    blind_gih, blind_model = _identity_model(lesson.repository, prompt=BLIND_CALIBRATION_PROMPT_VERSION,
                                             schema=BLIND_GRADER_OUTPUT_SCHEMA_VERSION, tag="blind")
    joint_gih, joint_model = _identity_model(lesson.repository, prompt=gc.GRADING_PROMPT_VERSION,
                                             schema=gc.GRADER_OUTPUT_SCHEMA_VERSION, tag="joint")
    assert blind_gih != joint_gih
    lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    query = ("SELECT r.grading_prompt_version, r.grader_output_schema_version, r.grader_identity_hash, "
             "i.reference_prior_ids_json FROM raw_grade_events r JOIN grade_interpretations i "
             "ON i.raw_grade_event_id = r.id WHERE r.attempt_id = ?")
    [(prompt, schema, gih, contributing)] = lesson.rows(query, (probe.attempt_id,))
    assert (prompt, schema, gih) == (BLIND_CALIBRATION_PROMPT_VERSION, BLIND_GRADER_OUTPUT_SCHEMA_VERSION, blind_gih)
    assert blind_model in json.loads(contributing) and joint_model not in json.loads(contributing)
    live = _cells(lesson)
    rebuild_all_derived_state(lesson.vault(), lesson.repository)
    assert _cells(lesson) == live


# -- F2 -------------------------------------------------------------------------------------------------------------


def _class(lesson, attempt_id):
    return lesson.repository.causal_activity_classification(attempt_id)["contamination_class"]


def _qualifying(lesson):
    with lesson.repository.connection() as connection:
        return [row["id"] for row in LW.qualifying_outcomes(connection, ["lo_eigen"], "2000-01-01T00:00:00Z")]


def test_f2_an_answer_after_teaching_on_its_topic_is_instructional_and_no_cold_outcome(tmp_path):
    lesson, probe = _served(tmp_path)
    record_reveal(lesson.repository, practice_item_id="pi_eig_1", source_kind="tutor_answer", amount=0.2,
                  learning_object_id="lo_eigen", basis=f"lesson:{lesson.lesson_id}", clock=lesson.clock())
    lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    assert _class(lesson, probe.attempt_id) == "instructional_diagnostic"
    assert probe.attempt_id not in _qualifying(lesson)
    events = lesson.rows("SELECT source, contamination_class FROM causal_activity_classification_events "
                         "WHERE attempt_id = ?", (probe.attempt_id,))
    assert events == [("lesson_probe_exposed", "instructional_diagnostic")]
    # The same answer with nothing shown on the topic: a pure diagnostic and a qualifying cold outcome.
    def quiet(context):
        turn = probe_turn(context, message="One quick question first.")
        for number, node in enumerate(turn["requests"][0]["plan"], start=1):
            node["statement"] = f"Step {number}."
        return turn

    clean = _Lesson(tmp_path / "clean", [quiet])
    clean.generate()
    clean.look()
    clean.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    attempt = _probe(clean).attempt_id
    assert _class(clean, attempt) == "pure_diagnostic"
    assert attempt in _qualifying(clean)


# -- F3 -------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("boundary", ["retire", "result", "episode"])
def test_f3_a_fault_after_the_attempt_rolls_everything_back_and_the_answer_can_be_sent_again(tmp_path, monkeypatch,
                                                                                          boundary):
    lesson, probe = _served(tmp_path)
    real = {"retire": identity.retire, "result": store.append_turn, "episode": PR._close_episode}

    def fault(*args, **kwargs):
        if boundary == "result" and kwargs.get("action") != PR.RESULT:
            return real["result"](*args, **kwargs)
        raise RuntimeError(f"stopped at {boundary}")

    target = {"retire": (identity, "retire"), "result": (store, "append_turn"), "episode": (PR, "_close_episode")}
    monkeypatch.setattr(*target[boundary], fault)
    with pytest.raises(S.LessonError) as failed:
        lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    assert failed.value.code == "grading_unavailable"
    monkeypatch.undo()
    # Nothing of the answer committed: no attempt, no retirement, no result; the probe is still open.
    assert lesson.rows("SELECT COUNT(*) FROM practice_attempts WHERE id = ?", (probe.attempt_id,)) == [(0,)]
    assert lesson.rows("SELECT kind FROM generated_probe_burns WHERE practice_item_id = ?", (probe.item_id,)) == [
        ("served",)]
    assert _probe(lesson).status == "served"
    lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    assert lesson.rows("SELECT COUNT(*) FROM practice_attempts WHERE id = ?", (probe.attempt_id,)) == [(1,)]
    assert _probe(lesson).status == "answered" and lesson.view["closed"]


def _half_recorded(lesson, probe):
    """The state the pre-fix code left when it stopped after its first commit: the attempt, nothing after it."""

    from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, apply_attempt
    from learnloop.attempts.grading import vault_grading_calibration_identity
    from learnloop.teacher import checks as CK

    vault = lesson.vault()
    item = vault.practice_items[probe.item_id]
    grade, run_id = CK.grade_answer(vault, lesson.repository, lesson.fake, item=item, attempt_id=probe.attempt_id,
                                    answer="(1, 0) by three")
    apply_attempt(vault, lesson.repository, ApplyAttemptInput(
        draft=AttemptDraft(practice_item_id=item.id, learner_answer_md="(1, 0) by three",
                           attempt_type=PR.ATTEMPT_TYPE, entry_surface=PR.ENTRY_SURFACE,
                           evidence_origin=PR.EVIDENCE_ORIGIN, awaits_completion=False),
        attempt_id=probe.attempt_id, grade=grade, grading_source="ai", grading_agent_run_id=run_id,
        grader_identity=vault_grading_calibration_identity(vault)))


def test_f3_an_answer_already_recorded_is_finished_without_a_second_grade(tmp_path):
    lesson, probe = _served(tmp_path)
    _half_recorded(lesson, probe)
    graded = len(lesson.fake.grading_contexts)
    lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    assert len(lesson.fake.grading_contexts) == graded  # no second grade
    assert lesson.rows("SELECT COUNT(*) FROM practice_attempts WHERE id = ?", (probe.attempt_id,)) == [(1,)]
    done = _probe(lesson)
    assert done.status == "answered" and done.result["result"] == "right"
    assert {row[0] for row in lesson.rows("SELECT kind FROM generated_probe_burns WHERE practice_item_id = ?",
                                          (probe.item_id,))} == {"served", "retired"}


def test_f3_a_view_after_a_half_recorded_answer_delivers_its_result_instead_of_dropping_the_probe(tmp_path):
    lesson, probe = _served(tmp_path)
    _half_recorded(lesson, probe)
    identity.retire(lesson.repository, probe.item_id, reason="lesson_probe_answered")
    view = lesson.look()
    done = _probe(lesson)
    assert done.status == "answered" and done.reason is None
    assert any(entry["kind"] == "probe_result" for entry in view["feed"])
    # The teacher is owed the result: resume reads it.
    lesson.act("resume", turns=[close_turn()])
    assert "probe_result" in lesson.fake.all_prompts() and lesson.view["closed"]


def test_f3_a_second_submit_of_an_answered_probe_returns_its_result(tmp_path):
    lesson, probe = _served(tmp_path)
    lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    graded = len(lesson.fake.grading_contexts)
    again = PR.record_answer(lesson.vault(), lesson.repository, lesson.view and S.load_state(
        lesson.repository, lesson.lesson_id).lesson, probe, answer="something else", tap=None,
        grading_client=lesson.fake, grading_source="ai")
    assert again["attempt_id"] == probe.attempt_id and again["result"] == "right"
    assert len(lesson.fake.grading_contexts) == graded
    assert lesson.rows("SELECT COUNT(*) FROM lesson_turns WHERE action = 'probe_result'") == [(1,)]


# -- F4 -------------------------------------------------------------------------------------------------------------


def _down():
    raise RuntimeError("the plan is down")


def _teacher_calls(lesson):
    return sum(1 for purpose, _prompt in lesson.fake.prompts if purpose == "teacher_turn")


def test_f4_resume_after_a_probe_result_whose_teacher_call_never_ran(tmp_path):
    lesson, probe = _served(tmp_path)
    broken = clients(lesson.fake)
    broken.teacher = _down  # the client cannot even be resolved
    with pytest.raises(Exception):  # whatever the outage raises
        S.take_turn(lesson.vault(), lesson.repository, lesson_id=lesson.lesson_id, action="answer_probe",
                    payload={"answer": "(1, 0) by three"}, clients=broken, clock=lesson.clock())
    assert _probe(lesson).status == "answered"
    calls = _teacher_calls(lesson)
    lesson.act("resume", turns=[close_turn()])
    assert _teacher_calls(lesson) == calls + 1 and lesson.view["closed"]
    assert '"probe_result"' in lesson.fake.prompts[-1][1]


def test_f4_resume_after_the_follow_up_call_failed(tmp_path):
    lesson, _probe_row = _served(tmp_path)

    def outage(_context):
        raise RuntimeError("transport")

    with pytest.raises(Exception):  # whatever the outage raises
        lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[outage])
    calls = _teacher_calls(lesson)
    lesson.act("resume", turns=[close_turn()])
    assert _teacher_calls(lesson) == calls + 1 and lesson.view["closed"]


def test_f4_resume_after_teach_it_anyway_whose_teacher_call_never_ran(tmp_path):
    lesson = _Lesson(tmp_path, [probe_turn])
    broken = clients(lesson.fake)
    broken.teacher = _down
    with pytest.raises(Exception):  # whatever the outage raises
        S.take_turn(lesson.vault(), lesson.repository, lesson_id=lesson.lesson_id, action="teach_anyway",
                    payload={}, clients=broken, clock=lesson.clock())
    assert _probe(lesson).status == "retired"
    calls = _teacher_calls(lesson)
    lesson.act("resume", turns=[close_turn()])
    assert _teacher_calls(lesson) == calls + 1 and lesson.view["closed"]


# -- F6 (the review's §11.8 row) ------------------------------------------------------------------------------------


def test_f6_today_can_close_a_te1_lesson_left_open_before_te2_was_switched_on(tmp_path):
    from tests.teacher_fakes import plan_turn
    from tests.ux_phase1_support import set_config

    lesson = _Lesson(tmp_path, [plan_turn], config={("teacher", "probes"): False})
    assert S.load_state(lesson.repository, lesson.lesson_id).brief["version"] == "lesson_brief_v1"
    set_config(lesson.paths.root, {("teacher", "probes"): True})
    assert [card["lesson_id"] for card in S.open_lessons(lesson.vault(), lesson.repository)] == [lesson.lesson_id]
    calls = len(lesson.fake.prompts)
    lesson.act("close")
    assert lesson.view["closed"] and lesson.view["close_reason"] == "learner_stop"
    assert len(lesson.fake.prompts) == calls
    # The probe actions stay a TE2 lesson's only.
    other = _Lesson(tmp_path / "other", [plan_turn], config={("teacher", "probes"): False})
    set_config(other.paths.root, {("teacher", "probes"): True})
    with pytest.raises(S.LessonError):
        other.act("teach_anyway")


# -- F5 -------------------------------------------------------------------------------------------------------------


def test_f5_a_metered_probe_author_is_sent_nothing(tmp_path):
    lesson = _Lesson(tmp_path, [probe_turn])
    lesson.author.provider_type = "openai_compatible"
    lesson.generate()
    assert lesson.author.calls == 0
    probe = _probe(lesson)
    assert probe.status == "refused" and probe.reason == "route_unavailable"
    assert lesson.rows("SELECT COUNT(*) FROM generated_probe_items") == [(0,)]


class _MeteredResolver(DeliverableFake):
    provider_name = "openrouter"
    provider_type = "openai_compatible"


def test_f5_a_metered_typed_goal_resolver_is_sent_nothing(tmp_path):
    from learnloop.teacher import topics as TP
    from tests.ux_phase1_support import set_config

    paths, repository = build_teacher_vault(tmp_path / "vault", version=TAG)
    set_config(paths.root, {("source_retrieval", "llm_price_per_million"): 1.0})
    fake = _MeteredResolver()
    resolved = TP.resolve(load_vault(paths.root), repository, "how do I find eigenvalues", client=fake)
    assert resolved["status"] == "unavailable" and fake.calls == 0
    assert "ChatGPT plan" in str(resolved["message"])
    with pytest.raises(S.LessonError) as refused:
        lesson_clients = clients(TeacherFake([]))
        lesson_clients.resolver = lambda: fake
        S.open_lesson(load_vault(paths.root), repository, entry="typed_goal", goal_text="how do I find eigenvalues",
                      clients=lesson_clients)
    assert refused.value.code == "plan_unavailable" and fake.calls == 0
