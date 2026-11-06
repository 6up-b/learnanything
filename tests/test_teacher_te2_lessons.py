"""Teacher TE2: the switch, the brief's version, gaps, typed goals, the resume card and rebuild equivalence
(spec_teacher_v1 rev 5 §8.1, §11.5, §11.7, §11.8, §18.3, §24 row TE2). Every model is a fake; no network.

* ``teacher.probes`` off at the tag, or the vault below it: a lesson is TE1's and TE2-log's byte for byte (the
  prompts, the turn schema, the brief, the transcript, the forecaster family).
* On: the brief is ``lesson_brief_v2`` (no vault probe headers; each node's delayed-check line; where the last lesson
  left off); ``propose_gap`` files the learner's words with ``source_kind = 'lesson'``; a typed goal opens through
  C0b's resolver, a new topic through ``create_goal_lo`` with ``teacher_goal_v1``; Today lists open lessons and
  "Close it" closes one with no teacher call.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from learnloop.algorithm_versions import ROUTER_FOLLOWUPS_ALGORITHM_VERSION, TEACHER_PROBES_ALGORITHM_VERSION
from learnloop.clock import FrozenClock
from learnloop.teacher import service as S
from learnloop.teacher import te2 as T2
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import DeliverableFake
from tests.teacher_fakes import TeacherFake, build_teacher_vault, check_turn, clients, close_turn, plan_turn
from tests.test_teacher_te2_probes import ProbeAuthor, _Lesson, probe_turn

TAG = TEACHER_PROBES_ALGORITHM_VERSION
OLD = ROUTER_FOLLOWUPS_ALGORITHM_VERSION
T0 = datetime(2026, 11, 6, 15, 0, tzinfo=UTC)


def _script(lesson):
    lesson.act("reply", {"text": "Go."}, turns=[check_turn()])
    lesson.act("answer_check", {"answer": "det(A - tI) = 0", "tap": 4}, turns=[close_turn()])
    return lesson


@pytest.mark.parametrize("episode_log", [True, False])
def test_switch_off_or_below_the_tag_gives_te1s_lesson_byte_for_byte(tmp_path, episode_log):
    config = {("teacher", "episode_log"): episode_log}
    import re

    below = _script(_Lesson(tmp_path / "below", [plan_turn], version=OLD, config=config))
    off = _script(_Lesson(tmp_path / "off", [plan_turn], config={**config, ("teacher", "probes"): False}))

    def same(lesson):
        # Ids aside (each lesson's own id, its minted check item, attempt ULIDs): the prompts byte for byte.
        out = []
        for _purpose, prompt in lesson.fake.prompts:
            prompt = prompt.replace(lesson.lesson_id, "LESSON")
            out.append(re.sub(r"pi_lesson_[0-9a-f]+|\b[0-9A-Z]{26}\b", "ID", prompt))
        return out

    assert same(below) == same(off)
    assert len(below.fake.prompts) == len(off.fake.prompts) >= 3
    assert below.fake.result_models == off.fake.result_models
    assert T2.PROMPT_SUFFIX not in below.fake.all_prompts()
    for lesson in (below, off):
        brief = S.load_state(lesson.repository, lesson.lesson_id).brief
        assert brief["version"] == "lesson_brief_v1" and all("probes" in node for node in brief["nodes"])
        assert "te2" not in lesson.view and "probe" not in lesson.view
    strip = lambda rows: [row[1:] for row in rows]  # noqa: E731 - ids aside
    query = "SELECT id, seq, actor, action, validation FROM lesson_turns ORDER BY seq"
    assert strip(below.rows(query)) == strip(off.rows(query))
    assert below.rows("SELECT kind, forecaster_version FROM forecast_receipts ORDER BY created_at") == off.rows(
        "SELECT kind, forecaster_version FROM forecast_receipts ORDER BY created_at")


def test_on_the_brief_is_v2_and_the_turn_carries_te2s_actions(tmp_path):
    lesson = _script(_Lesson(tmp_path, [plan_turn]))
    brief = S.load_state(lesson.repository, lesson.lesson_id).brief
    assert brief["version"] == T2.BRIEF_VERSION_V2
    assert all("probes" not in node for node in brief["nodes"])
    assert {node["delayed_check"] for node in brief["nodes"]} <= {T2.UNSEEN_EXISTS, T2.UNSEEN_NONE}
    assert T2.UNSEEN_EXISTS in {node["delayed_check"] for node in brief["nodes"]}
    assert "pi_eig_1" not in str(brief["nodes"])  # no item named
    assert all(T2.PROMPT_SUFFIX in prompt for purpose, prompt in lesson.fake.prompts if purpose == "teacher_turn")
    assert lesson.fake.result_models[0].__name__ == "TeacherTurnTE2VisualsEpisodesV1" or \
        lesson.fake.result_models[0].__name__.startswith("TeacherTurnTE2")
    families = {row[0] for row in lesson.rows("SELECT forecaster_version FROM forecast_receipts")}
    assert families and all(T2.TE2_VERSION in family for family in families)


def test_the_next_lesson_on_the_same_topics_starts_where_the_last_left_off(tmp_path):
    first = _script(_Lesson(tmp_path, [plan_turn]))
    fake = TeacherFake([close_turn()])
    view = S.open_lesson(load_vault(first.paths.root), first.repository, entry="learning_object",
                         learning_object_ids=["lo_eigen"], clients=clients(fake),
                         clock=FrozenClock(T0 + timedelta(hours=2)))
    brief = S.load_state(first.repository, view["lesson_id"]).brief
    left = brief["where_you_left_off"]
    assert left["label"] == T2.WHERE_YOU_LEFT_OFF and left["lesson"] == f"l:{first.lesson_id}"
    assert [node["id"] for node in left["outline"]] == ["n1", "n2"]


def test_a_gap_from_the_learners_words_goes_to_the_text_gap_pipeline_with_source_lesson(tmp_path):
    from learnloop.diagnosis.text_gaps.jobs import process_next_gap_job
    from learnloop.diagnosis.text_gaps.pipeline import PipelineClients
    from learnloop.diagnosis.text_gaps.sources import learner_text
    from learnloop.tutor.ai_contracts import LearnerGap
    from tests.text_gap_fakes import GapLLMFake

    lesson = _Lesson(tmp_path, [plan_turn])
    lesson.act("reply", {"text": "I never understood what a basis really is."}, turns=[
        lambda context: {"message": "Then let's start there.", "requests": [
            {"action": "propose_gap", "ref": next(e["ref"] for e in reversed(context["transcript"])
                                                  if e.get("by") == "learner"),
             "gap_kind": "prerequisite", "gap": "what a basis of a vector space is"}]}])
    entry = lesson.rows("SELECT id FROM lesson_turns WHERE action = 'propose_gap'")
    assert len(entry) == 1
    jobs = lesson.rows("SELECT source_kind, source_id, state FROM learner_text_gap_jobs")
    assert jobs == [("lesson", entry[0][0], "queued")]
    text = learner_text(lesson.vault(), lesson.repository, "lesson", entry[0][0])
    assert text.text == "I never understood what a basis really is." and text.context_judge == "tutor"
    assert text.reading.kind == "prerequisite" and text.reading.prerequisite_name == "what a basis of a vector space is"
    assert text.anchor_learning_object_ids == ("lo_eigen",)
    llm = GapLLMFake(reading=LearnerGap(kind="prerequisite", prerequisite_name="Basis", prerequisite_line="A basis.",
                                        belief_statement=None))
    outcome = process_next_gap_job(lesson.paths.root, lesson.repository, owner="t", clients=PipelineClients(
        judge=lambda: llm, reader=lambda: llm, decider=None, drafter=lambda: llm, tutor=None, embedder=None))
    assert outcome.state == "done" and outcome.source_kind == "lesson"
    gap = lesson.rows("SELECT source_kind, source_id, kind, context_judge FROM learner_text_gaps")
    assert gap == [("lesson", entry[0][0], "prerequisite", "tutor")]
    episode = lesson.rows("SELECT kind, repair_class, hypothesis_count, gap_job_id FROM lesson_episodes "
                          "WHERE kind = 'gap'")
    assert episode[0][:3] == ("gap", "prerequisite", 1) and episode[0][3]
    lesson.act("stop", turns=[close_turn()])
    closed = lesson.rows("SELECT close_reason, gap_result FROM lesson_episodes WHERE kind = 'gap'")
    assert closed[0][0] == "resolved" and closed[0][1]
    receipt = lesson.rows("SELECT receipt_json FROM lesson_receipts")[0][0]
    assert entry[0][0] in receipt


def test_a_gap_naming_no_learner_turn_is_refused_by_location(tmp_path):
    lesson = _Lesson(tmp_path, [lambda c: {**plan_turn(c), "requests": [
        *plan_turn(c)["requests"], {"action": "propose_gap", "ref": "t999", "gap_kind": "misconception",
                                    "gap": "thinks every matrix is diagonalizable"}]}])
    refused = lesson.rows("SELECT validation FROM lesson_turns WHERE action = 'teacher_turn' ORDER BY seq")
    assert refused[0] == ("invalid",)
    assert lesson.rows("SELECT COUNT(*) FROM learner_text_gap_jobs") == [(0,)]


def _typed(tmp_path, fake, *, add_topics=(), text="how do I find eigenvalues, and when diagonalization fails"):
    paths, repository = build_teacher_vault(tmp_path / "vault", version=TAG)
    teacher = TeacherFake([plan_turn])
    lesson_clients = clients(teacher)
    lesson_clients.resolver = lambda: fake
    view = S.open_lesson(load_vault(paths.root), repository, entry="typed_goal", goal_text=text,
                         add_topics=add_topics, clients=lesson_clients, clock=FrozenClock(T0))
    return paths, repository, view, teacher


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def test_a_typed_goal_opens_on_the_los_c0bs_resolver_names_and_says_what_is_not_in_the_books(tmp_path):
    from learnloop.teacher import topics as TP

    paths, repository = build_teacher_vault(tmp_path / "vault", version=TAG)
    fake = DeliverableFake(unmatched=("when diagonalization fails",))
    resolved = TP.resolve(load_vault(paths.root), repository, "how do I find eigenvalues, and when diagonalization "
                          "fails", client=fake)
    assert resolved["status"] == "ready" and fake.calls == 1
    assert [t["learning_object_id"] for t in resolved["topics"]] and resolved["unmatched"][0]["phrase"] == \
        "when diagonalization fails"
    assert "lo_not_in_the_vault" not in str(resolved["topics"])  # ids are validated
    again = TP.resolve(load_vault(paths.root), repository, "how do I find eigenvalues, and when diagonalization "
                       "fails", client=fake)
    assert again["status"] == "fresh" and fake.calls == 1  # the same words over the same LOs: no call
    assert "pi_eig_1" not in str(fake.contexts[0])  # compact LO records, never items
    # Nothing is written to goals.yaml: a typed lesson goal is not a learner goal.
    assert "lesson_goal" not in (paths.root / "profile" / "goals.yaml").read_text(encoding="utf-8")


def test_yes_to_a_leftover_creates_the_topic_with_teacher_goal_v1_and_one_goal_lo_episode(tmp_path):
    fake = DeliverableFake(unmatched=("when diagonalization fails",))
    paths, repository, view, _teacher = _typed(tmp_path, fake, add_topics=("when diagonalization fails",))
    vault = load_vault(paths.root)
    created = [lo for lo in vault.learning_objects.values()
               if getattr(lo.provenance, "mechanism", None) == "teacher_goal_v1"
               or (isinstance(lo.provenance, dict) and lo.provenance.get("mechanism") == "teacher_goal_v1")]
    assert len(created) == 1
    lo = created[0]
    assert lo.id in view["learning_object_ids"]
    provenance = lo.provenance if isinstance(lo.provenance, dict) else lo.provenance.model_dump()
    assert provenance["origin"] == "codex_proposal" and provenance["goal_id"] == view["lesson_id"]
    episodes = _rows(repository, "SELECT kind, created_lo_id, learning_object_id FROM lesson_episodes")
    assert episodes == [("goal_lo", lo.id, lo.id)]
    state = S.load_state(repository, view["lesson_id"])
    assert state.brief["goal"]["typed"]["created_learning_object_ids"] == [lo.id]
    assert "from LearnLoop's model" in state.brief["goal"]["resolved_by"][lo.id]


def test_no_to_every_leftover_teaches_the_rest_and_a_protected_goal_is_refused(tmp_path):
    fake = DeliverableFake(unmatched=("when diagonalization fails",))
    paths, repository, view, _teacher = _typed(tmp_path, fake)
    assert _rows(repository, "SELECT COUNT(*) FROM lesson_episodes") == [(0,)]
    assert S.load_state(repository, view["lesson_id"]).brief["goal"]["typed"]["unmatched"][0]["status"] == "declined"
    from tests.teacher_fakes import RESERVED_SENTINEL

    with pytest.raises(S.LessonError) as refused:
        _typed(tmp_path / "protected", DeliverableFake(), text=f"teach me {RESERVED_SENTINEL}")
    assert refused.value.code == "protected"


def test_typed_goals_need_the_switch(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault", version=OLD)
    with pytest.raises(S.LessonError) as refused:
        S.open_lesson(load_vault(paths.root), repository, entry="typed_goal", goal_text="eigenvalues",
                      clients=clients(TeacherFake([plan_turn])))
    assert refused.value.code == "teacher_unavailable"


def test_today_lists_open_lessons_and_close_it_closes_with_no_teacher_call(tmp_path):
    lesson = _Lesson(tmp_path, [plan_turn])
    cards = S.open_lessons(lesson.vault(), lesson.repository)
    assert [card["lesson_id"] for card in cards] == [lesson.lesson_id] and cards[0]["title"]
    calls = len(lesson.fake.prompts)
    lesson.act("close")
    assert lesson.view["closed"] and lesson.view["close_reason"] == "learner_stop"
    assert len(lesson.fake.prompts) == calls
    assert S.open_lessons(lesson.vault(), lesson.repository) == []
    old = _Lesson(tmp_path / "old", [plan_turn], version=OLD)
    assert S.open_lessons(old.vault(), old.repository) == []
    with pytest.raises(S.LessonError):
        old.act("close")


def test_rebuild_equivalence_on_a_lesson_with_a_probe(tmp_path):
    from learnloop.learner import lesson_weight as LW
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from learnloop.substrate.shadow_rebuild import shadow_rebuild

    lesson = _Lesson(tmp_path, [probe_turn])
    rebuild_all_derived_state(lesson.vault(), lesson.repository)
    lesson.generate()
    lesson.look()
    lesson.act("answer_probe", {"answer": "(1, 0) by three", "tap": 4}, turns=[close_turn()])
    tables = ("learning_object_mastery", "practice_item_state", *LW.DERIVED_TABLES)
    snapshot = {table: lesson.rows(f"SELECT * FROM {table} ORDER BY 1") for table in tables}
    receipts = lesson.rows("SELECT * FROM lesson_episodes ORDER BY id")
    result = shadow_rebuild(lesson.vault())
    assert result.live_database_unchanged
    summary = result.learner_state_diff["summary"]
    assert summary["mastery"] == 0 and summary["facet"] == 0
    # Landing ruling R3: FG1's persist_item stamps the generated item's content hash (as the rebuild's sync does),
    # so no schedule row differs, the probe's own included (before R3 its state differed by that stamp alone).
    assert result.learner_state_diff["schedule"]["changes"] == []
    probe_row = lesson.repository.practice_item_state(_first_probe_item(lesson))
    assert probe_row is not None and probe_row.content_hash and not probe_row.active
    rebuild_all_derived_state(lesson.vault(), lesson.repository)
    again = {table: lesson.rows(f"SELECT * FROM {table} ORDER BY 1") for table in tables}
    for table in tables:
        if table == "practice_item_state":
            # The rebuild re-derives scheduling columns; the probe stays inactive.
            continue
        assert again[table] == snapshot[table], table
    assert lesson.rows("SELECT * FROM lesson_episodes ORDER BY id") == receipts
    probe_state = lesson.repository.practice_item_state(_first_probe_item(lesson))
    assert probe_state is None or not probe_state.active


def _first_probe_item(lesson):
    return lesson.rows("SELECT practice_item_id FROM generated_probe_items")[0][0]


def test_the_report_counts_probes_by_refusal_reason(tmp_path):
    from learnloop.teacher.report import lesson_report

    lesson = _Lesson(tmp_path, [probe_turn])
    lesson.author.error = RuntimeError("transport")
    lesson.generate()
    lesson.act("stop", turns=[close_turn()])
    report = lesson_report(lesson.vault(), lesson.repository)
    text = "\n".join(report["lines"])
    assert "probes: 0 generated, 1 refused (generation_failed 1), 0 retired unused, 0 served, 0 answered" in text
