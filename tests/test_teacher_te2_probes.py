"""Teacher TE2: probes inside a lesson (spec_teacher_v1 rev 5 §11.3, §9 serve_probe, §9.1, §24 row TE2).

Every model is a fake (``TeacherFake`` for the teacher and the blind grader; a recording FG1 author); no network. A
lesson probe is generated once through FG1's path, served cold with the teacher silent, and never served again
after serve, rebuild, sync, remint or any FG1 §4.2 door; it is retired at the close or on "Teach it anyway"; a
reserved-question match gives no probe; an answer after the lesson showed text on its topic is not independent; the
forecast is written before the serve; protected material never reaches the generator.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import TEACHER_PROBES_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.followup_run.jobs import process_next_job
from learnloop.followup_serve import identity
from learnloop.teacher import probes as PR
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.structured_ai import StructuredClientFake
from tests.teacher_fakes import (
    EXAM_QUESTION,
    RESERVED_SENTINEL,
    SENTINELS,
    TeacherFake,
    build_teacher_vault,
    clients,
    close_turn,
    plan_turn,
)

TAG = TEACHER_PROBES_ALGORITHM_VERSION
T0 = datetime(2026, 11, 6, 15, 0, tzinfo=UTC)
READING = "treats the eigenvector as if it were the eigenvalue"


class ProbeAuthor(StructuredClientFake):
    """FG1's frontier author, faked: two criteria, one failing prediction per reading; counts its calls."""

    model = "fake-frontier"
    provider_name = "fake_author"
    provider_type = "fake"

    def __init__(self, *, prompt: str = "For the map [[3,0],[0,7]], name a vector it only stretches, and by how much.",
                 error: Exception | None = None) -> None:
        self.calls = 0
        self.contexts: list = []
        self.prompt = prompt
        self.error = error

    def run_followup_probe_authoring(self, context):
        from learnloop.diagnosis.ai_contracts import (
            FollowupProbeAuthored,
            FollowupProbeCriterion,
            FollowupProbeManipulation,
            FollowupProbePrediction,
        )

        self.calls += 1
        self.contexts.append(context)
        if self.error is not None:
            raise self.error
        refs = [row["hypothesis_ref"] for row in context.hypotheses]
        return FollowupProbeAuthored(
            prompt_md=f"On {context.learning_object_title}: {self.prompt} (#{self.calls})",
            expected_answer_md="ibis heron: (1, 0) by three",
            surface_suffix=f"lesson_{self.calls}",
            criteria=[FollowupProbeCriterion(id="names_vector", description="Names an eigenvector.", points=2),
                      FollowupProbeCriterion(id="names_factor", description="Names its eigenvalue.", points=2)],
            predictions=[FollowupProbePrediction(hypothesis_ref=ref, fails_criteria=[("names_factor", "names_vector")[i % 2]])
                         for i, ref in enumerate(refs)],
            intended_manipulations=[FollowupProbeManipulation(axis=axis, rationale="A fresh question.")
                                    for axis in ("surface_wording", "answer_contract", "rubric")],
        )


def probe_turn(context, *, readings=(READING,), p=0.4, node="n1", message="Before we start, one quick question."):
    turn = plan_turn(context)
    turn["message"] = message
    turn["requests"].append({"action": "serve_probe", "node": node, "readings": list(readings), "p": p})
    return turn


class _Lesson:
    def __init__(self, tmp_path, turns, *, version=TAG, config=None):
        from tests.ux_phase1_support import set_config

        self.paths, self.repository = build_teacher_vault(tmp_path / "vault", version=version)
        if config:
            set_config(self.paths.root, config)
        self.paths.root.joinpath("learnloop.toml")
        self.fake = TeacherFake(turns)
        self.author = ProbeAuthor()
        self.minute = 0
        self.view = S.open_lesson(self.vault(), self.repository, entry="learning_object",
                                  learning_object_ids=["lo_eigen"], clients=clients(self.fake), clock=self.clock())
        self.lesson_id = self.view["lesson_id"]

    def vault(self):
        return load_vault(self.paths.root)

    def clock(self):
        self.minute += 1
        return FrozenClock(T0 + timedelta(minutes=self.minute))

    def generate(self):
        outcomes = []
        while True:
            outcome = process_next_job(self.vault(), self.repository, owner="test",
                                       clients=SimpleNamespace(author=self.author), clock=self.clock())
            if outcome is None:
                return outcomes
            outcomes.append(outcome)

    def look(self):
        self.view = S.view_lesson(self.vault(), self.repository, self.lesson_id, clock=self.clock())
        return self.view

    def act(self, action, payload=None, *, turns=None, right=None):
        if turns is not None:
            self.fake.turns = list(turns)
        if right is not None:
            self.fake.full = right
        self.view = S.take_turn(self.vault(), self.repository, lesson_id=self.lesson_id, action=action,
                                payload=payload or {}, clients=clients(self.fake), clock=self.clock())
        return self.view

    def rows(self, sql, params=()):
        with self.repository.connection() as connection:
            return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _probe(lesson):
    from learnloop.db.stores import lessons as store

    with lesson.repository.connection() as connection:
        return PR.probes(store.turns(connection, lesson.lesson_id))[0]


def test_a_probe_is_generated_once_served_cold_and_never_again(tmp_path):
    lesson = _Lesson(tmp_path, [probe_turn])
    assert lesson.view["probe"]["status"] == "preparing" and lesson.view["probe"]["label"] == PR.PREPARING
    # One job, of kind lesson, deduplicated on (lesson, node); the teacher was asked once.
    assert lesson.rows("SELECT kind, dedupe_key, state FROM followup_generation_jobs") == [
        ("lesson", f"lesson:{lesson.lesson_id}:n1", "queued")]
    teacher_calls = len(lesson.fake.prompts)
    outcomes = lesson.generate()
    assert [o.state for o in outcomes] == ["done"] and lesson.author.calls == 1
    probe = _probe(lesson)
    assert probe.status == "ready" and probe.item_id
    assert lesson.rows("SELECT source, workflow_id FROM generated_probe_items") == [("lesson", None)]
    # Reserved for its lesson: every door refuses it before it is served.
    assert identity.door_refusal(lesson.repository, probe.item_id) == identity.GENERATED_PROBE_RESERVED
    closed, reserved = identity.door_sets(lesson.repository)
    assert probe.item_id in reserved and probe.item_id not in closed
    view = lesson.look()
    assert view["probe"]["status"] == "open" and "[[3,0],[0,7]]" in view["probe"]["question"]
    assert "ibis heron" not in str(view)  # the key never leaves
    burns = lesson.rows("SELECT kind, surface FROM generated_probe_burns WHERE practice_item_id = ?", (probe.item_id,))
    assert burns == [("served", "lesson")]
    # Re-shown on the same surface is the same administration; any other door is refused.
    assert lesson.look()["probe"]["probe_ref"] == probe.ref
    assert identity.claim_serve(lesson.repository, probe.item_id, surface="desktop", presentation_id=None).granted is False
    # §9.1 cold_attempt: a reply is refused while the probe is open, and no teacher call is made.
    with pytest.raises(S.LessonError) as refused:
        lesson.act("reply", {"text": "can I have a hint?"})
    assert refused.value.code == "probe_open"
    assert len(lesson.fake.prompts) == teacher_calls
    lesson.act("answer_probe", {"answer": "(1, 0), stretched by three", "tap": 4}, turns=[close_turn()])
    attempts = lesson.rows("SELECT id, attempt_type, entry_surface, evidence_origin FROM practice_attempts "
                           "WHERE practice_item_id = ?", (probe.item_id,))
    assert attempts == [(probe.attempt_id, "diagnostic_probe", "lesson", "lesson_probe")]
    assert {row[0] for row in lesson.rows("SELECT kind FROM generated_probe_burns WHERE practice_item_id = ?",
                                          (probe.item_id,))} == {"served", "retired"}
    # Never again: every door, rebuild, sync and remint.
    assert identity.door_refusal(lesson.repository, probe.item_id) == identity.GENERATED_PROBE_CLOSED
    assert probe.item_id in identity.door_sets(lesson.repository)[0]
    assert identity.claim_serve(lesson.repository, probe.item_id, surface="lesson", presentation_id=None).granted is False
    from learnloop.scheduling.serving_exclusions import routine_serving_exclusions

    assert probe.item_id in routine_serving_exclusions(lesson.vault(), lesson.repository).item_ids
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from learnloop.substrate.state_sync import sync_vault_state

    rebuild_all_derived_state(lesson.vault(), lesson.repository)
    sync_vault_state(lesson.vault(), lesson.repository)
    state = lesson.repository.practice_item_state(probe.item_id)
    assert state is None or not state.active
    from learnloop.diagnosis.probe_remint import ProbeRemintError, remint_probe_as_practice_item

    with pytest.raises(ProbeRemintError) as remint:
        remint_probe_as_practice_item(lesson.paths.root, lesson.vault(), lesson.repository,
                                      attempt_id=probe.attempt_id)
    assert remint.value.code == "generated_probe_single_use"
    # The probe's answer reached the teacher; the item is in no brief and no delayed check.
    assert lesson.view["closed"] and lesson.view["close_reason"] == "goal_reached"
    receipt = lesson.rows("SELECT receipt_json FROM lesson_receipts")[0][0]
    assert probe.item_id in receipt and '"probes"' in receipt


def test_the_forecast_is_written_before_the_serve_and_bound_to_the_probes_attempt(tmp_path):
    lesson = _Lesson(tmp_path, [probe_turn])
    probe = _probe(lesson)
    receipts = lesson.rows("SELECT receipt_key, created_at, inputs_json, binding_kind FROM forecast_receipts "
                           "WHERE kind = 'lesson_probe_correct'")
    assert len(receipts) == 1 and receipts[0][3] == "lesson_probe_attempt"
    assert probe.attempt_id in receipts[0][2] and receipts[0][0] == probe.forecast_key
    lesson.generate()
    lesson.look()
    burned = lesson.rows("SELECT created_at FROM generated_probe_burns WHERE kind = 'served'")[0][0]
    assert receipts[0][1] < burned
    lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    from learnloop.evsi_calibration.forecast_report import resolved_receipts

    resolved = [(r, res) for r, res in resolved_receipts(lesson.vault()) if r["kind"] == "lesson_probe_correct"]
    assert resolved[0][1]["state"] == "resolved" and resolved[0][1]["emission"] == "success"
    probe = _probe(lesson)
    episode = lesson.rows("SELECT kind, close_reason, teacher_p, teacher_forecast_receipt_id, generation_job_id, "
                          "generated_item_id, outcome_attempt_id, outcome_correctness FROM lesson_episodes "
                          "WHERE kind = 'probe'")
    assert episode == [("probe", "answered", 0.4, probe.forecast_key, episode[0][4], probe.item_id, probe.attempt_id,
                        1.0)]


def test_teach_it_anyway_retires_the_probe_unused_and_a_late_generator_never_serves_it(tmp_path):
    lesson = _Lesson(tmp_path, [probe_turn])
    lesson.act("teach_anyway", turns=[close_turn()])
    probe = _probe(lesson)
    assert probe.status == "retired" and probe.reason == "teach_anyway"
    assert lesson.rows("SELECT state FROM followup_generation_jobs") == [("skipped",)]
    assert lesson.generate() == [] and lesson.author.calls == 0
    assert lesson.rows("SELECT close_reason FROM lesson_episodes WHERE kind = 'probe'") == [("retired",)]


def test_a_late_question_is_retired_as_it_lands(tmp_path):
    lesson = _Lesson(tmp_path, [probe_turn])
    item_id = "pi_late"
    identity.register(lesson.repository, practice_item_id=item_id, revision="r", source="lesson")
    lesson.act("teach_anyway", turns=[close_turn()])
    assert not PR.record_ready(lesson.vault(), lesson.repository, lesson_id=lesson.lesson_id, node_id="n1",
                               item_id=item_id, receipt={})
    assert identity.door_refusal(lesson.repository, item_id) == identity.GENERATED_PROBE_CLOSED


def test_a_probe_still_preparing_is_retired_at_the_close(tmp_path):
    lesson = _Lesson(tmp_path, [probe_turn])
    lesson.generate()
    probe = _probe(lesson)
    lesson.act("stop", turns=[close_turn()])
    assert _probe(lesson).status == "retired"
    assert identity.door_refusal(lesson.repository, probe.item_id) == identity.GENERATED_PROBE_CLOSED
    assert lesson.rows("SELECT kind FROM generated_probe_burns WHERE practice_item_id = ?", (probe.item_id,)) == [
        ("retired",)]


def test_a_reserved_question_match_gives_no_probe(tmp_path):
    from learnloop.db.stores import lessons as store

    lesson = _Lesson(tmp_path, [plan_turn])
    # The worker's own check (the output guards would already withhold a turn quoting a reserved key).
    with lesson.repository.atomic():
        store.append_turn(lesson.repository.connection(), lesson_id=lesson.lesson_id, actor="teacher",
                          action=PR.REQUEST, validation="ok", refs={},
                          payload={"probe_ref": "p1", "node": "n1", "learning_object_id": "lo_eigen",
                                   "readings": [f"thinks {RESERVED_SENTINEL}"], "p": 0.5, "attempt_id": "a1"},
                          created_at="2026-11-06T15:05:00Z")
    from learnloop.followup_serve import queue

    queue.enqueue_lesson(lesson.repository, lesson.lesson_id, "n1")
    lesson.generate()
    assert lesson.author.calls == 0
    assert _probe(lesson).status == "refused" and _probe(lesson).reason == "reserved_match"
    assert lesson.rows("SELECT COUNT(*) FROM generated_probe_items") == [(0,)]


def test_a_reading_quoting_protected_text_is_withheld_before_anything_is_written(tmp_path):
    lesson = _Lesson(tmp_path, [lambda c: probe_turn(c, readings=(f"thinks {RESERVED_SENTINEL}",))])
    assert lesson.rows("SELECT COUNT(*) FROM followup_generation_jobs") == [(0,)]
    assert lesson.rows("SELECT validation FROM lesson_turns WHERE action = 'teacher_turn' ORDER BY seq")[0] == (
        "withheld",)


def test_protected_material_never_reaches_the_generator(tmp_path):
    lesson = _Lesson(tmp_path, [probe_turn])
    lesson.generate()
    context = str(lesson.author.contexts[0])
    for sentinel in SENTINELS:
        assert sentinel not in context
    assert EXAM_QUESTION not in context
    assert lesson.author.contexts[0].router_decision["origin"] == "lesson"


def test_two_readings_are_rivals_and_one_is_held_or_not(tmp_path):
    lesson = _Lesson(tmp_path, [lambda c: probe_turn(c, readings=("confuses A with its transpose",
                                                                  "can't change basis at all"))])
    lesson.generate()
    rows = lesson.author.contexts[0].hypotheses
    assert [row["statement"] for row in rows] == ["confuses A with its transpose", "can't change basis at all"]
    single = _Lesson(tmp_path / "single", [probe_turn])
    single.generate()
    assert single.author.contexts[0].hypotheses[0]["statement"].startswith("does not hold this yet:")


def test_an_answer_after_teaching_on_its_topic_is_not_independent(tmp_path):
    from learnloop.attempts.reveal_ledger import record_reveal

    lesson = _Lesson(tmp_path, [probe_turn])
    lesson.generate()
    lesson.look()
    # The lesson showed text on the probe's topic (a reveal row on the LO, as its teaching text writes them).
    record_reveal(lesson.repository, practice_item_id="pi_eig_1", source_kind="tutor_answer", amount=0.2,
                  learning_object_id="lo_eigen", basis=f"lesson:{lesson.lesson_id}", clock=lesson.clock())
    lesson.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    result = next(e for e in lesson.view["feed"] if e["kind"] == "probe_result")
    assert result["result"] == "right"
    stored = lesson.rows("SELECT payload_json FROM lesson_turn_payloads p JOIN lesson_turns t ON t.id = p.turn_id "
                         "WHERE t.action = 'probe_result'")
    assert '"independent": false' in stored[0][0] and "post_reveal_not_independent" in stored[0][0]
    # A lesson that probes before any text on the topic: the same answer is independent.
    def quiet(context):
        turn = probe_turn(context, message="One quick question first.")
        for number, node in enumerate(turn["requests"][0]["plan"], start=1):
            node["statement"] = f"Step {number}."
        return turn

    clean = _Lesson(tmp_path / "clean", [quiet])
    assert clean.rows("SELECT COUNT(*) FROM reveal_events") == [(0,)]
    clean.generate()
    clean.look()
    clean.act("answer_probe", {"answer": "(1, 0) by three"}, turns=[close_turn()])
    stored = clean.rows("SELECT payload_json FROM lesson_turn_payloads p JOIN lesson_turns t ON t.id = p.turn_id "
                        "WHERE t.action = 'probe_result'")
    assert '"independent": true' in stored[0][0]


def test_a_generation_that_fails_twice_is_refused_and_the_teacher_is_told(tmp_path):
    lesson = _Lesson(tmp_path, [probe_turn])
    lesson.author.error = RuntimeError("transport")
    # FG1's bound: the first run and one retry after its backoff (each step a minute on this clock), then no more.
    outcomes = lesson.generate()
    assert [o.state for o in outcomes] == ["retry", "failed"] and lesson.author.calls == 2
    probe = _probe(lesson)
    assert probe.status == "refused" and probe.reason == "generation_failed"
    assert lesson.rows("SELECT close_reason, refusal_reason FROM lesson_episodes WHERE kind = 'probe'") == [
        ("refused", "generation_failed")]
    lesson.act("reply", {"text": "ok"}, turns=[close_turn()])
    assert "couldn't prepare that question" in lesson.fake.all_prompts()


def test_the_cap_and_one_question_per_node(tmp_path):
    lesson = _Lesson(tmp_path, [probe_turn], config={("teacher", "placement", "max_probes"): 1})
    lesson.generate()
    lesson.look()
    lesson.act("answer_probe", {"answer": "x"}, turns=[lambda c: {"message": "again", "requests": [
        {"action": "serve_probe", "node": "n2", "readings": ["r"], "p": 0.5}]}])
    refused = lesson.rows("SELECT validation FROM lesson_turns WHERE action = 'teacher_turn' ORDER BY seq")
    assert ("invalid",) in refused[1:]
    assert lesson.rows("SELECT COUNT(*) FROM followup_generation_jobs") == [(1,)]
