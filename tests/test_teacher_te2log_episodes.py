"""Teacher TE2-log, part 2: the episode log's detours and ``note_detour`` (spec_teacher_v1 §9, §11.7, §11.9).

Every model is ``TeacherFake``; no network. A detour is one ``lesson_episodes`` row opened by the teacher's
``note_detour`` (or ``unlogged`` for a plan that inserts a foundation with no note), with item 5's fields as ids
and numbers, closed once at its re-check or with the lesson. ``teacher.episode_log`` off keeps TE1's prompt, turn
schema, forecaster family and ledger exactly; a refused row rolls back alone; no protected text is in any row.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.ai.transport import render_structured_prompt
from learnloop.clock import FrozenClock
from learnloop.teacher import episodes as E
from learnloop.teacher import service as S
from learnloop.teacher.contracts import PROMPT_VERSION, TeacherTurnEpisodesV1, TeacherTurnV1
from learnloop.teacher.doctrines import doctrine_hash, doctrine_text
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import (
    ITEMS,
    TeacherFake,
    build_teacher_vault,
    check_turn,
    clients,
    close_turn,
    context_of,
    landed_turn,
    plan_turn,
)
from tests.test_reader_rw5d_p4b_teacher_visuals import TE1_DOCTRINE_SHA256, TE1_SCHEMA_SHA256, _schema_sha

T0 = datetime(2026, 11, 5, 15, 0, tzinfo=UTC)
HYPOTHESIS = "WOMBATHYPOTHESIS treats the eigenvalue as the eigenvector"


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _episodes(repository):
    with repository.connection() as connection:
        cursor = connection.execute("SELECT * FROM lesson_episodes ORDER BY opened_at, id")
        return [{d[0]: v for d, v in zip(cursor.description, row, strict=True)} for row in cursor.fetchall()]


def detour_turn(node="n1", repair="reteach", p=0.7, hypothesis=HYPOTHESIS, message="Let's look at it another way."):
    return {"message": message, "requests": [
        {"action": "note_detour", "node": node, "hypothesis": hypothesis, "repair": repair, "p": p}]}


def foundation_plan(context, *, note=False):
    """A revised plan that steps back to a foundation inserted before n1."""

    turn = plan_turn(context)
    anchor = turn["requests"][0]["plan"][0]["anchors"]
    turn["requests"][0]["plan"].insert(0, {"id": "n0", "statement": "A determinant measures how a map scales area.",
                                           "lo_id": "lo_det", "anchors": anchor, "premises": []})
    turn["message"] = "First a foundation: what a determinant measures."
    if note:
        turn["requests"].append({"action": "note_detour", "node": "n1", "hypothesis": HYPOTHESIS,
                                 "repair": "insert_foundation", "p": 0.55})
    return turn


class _Lesson:
    """One scripted lesson on a synthetic vault, every step at a frozen minute."""

    def __init__(self, tmp_path, turns, *, config=None, minute=0, prepare=None):
        from tests.ux_phase1_support import set_config

        self.paths, self.repository = build_teacher_vault(tmp_path / "vault")
        if config:
            set_config(self.paths.root, config)
        if prepare is not None:
            prepare(self.paths, self.repository)
        self.fake = TeacherFake(turns)
        self.minute = minute
        self.view = S.open_lesson(load_vault(self.paths.root), self.repository, entry="learning_object",
                                  learning_object_ids=["lo_eigen"], clients=clients(self.fake), clock=self.clock())
        self.lesson_id = self.view["lesson_id"]

    def clock(self):
        self.minute += 1
        return FrozenClock(T0 + timedelta(minutes=self.minute))

    def act(self, action, payload=None, *, turns=None, right=None):
        if turns is not None:
            self.fake.turns = list(turns)
        if right is not None:
            self.fake.full = right
        self.view = S.take_turn(load_vault(self.paths.root), self.repository, lesson_id=self.lesson_id, action=action,
                                payload=payload or {}, clients=clients(self.fake), clock=self.clock())
        return self.view


def _detour_lesson(tmp_path, **kwargs):
    lesson = _Lesson(tmp_path, [plan_turn], **kwargs)
    lesson.act("reply", {"text": "Go."}, turns=[check_turn()])
    lesson.act("answer_check", {"answer": "the eigenvector itself", "tap": 5}, turns=[detour_turn()], right=False)
    return lesson


# --- the rows -------------------------------------------------------------------------------------


def test_a_detour_is_one_row_with_item_5s_fields_closed_once_at_its_recheck(tmp_path):
    lesson = _detour_lesson(tmp_path)
    (row,) = _episodes(lesson.repository)
    assert row["kind"] == "detour" and row["repair_class"] == "reteach" and row["node_id"] == "n1"
    assert row["learning_object_id"] == "lo_eigen" and row["lesson_id"] == lesson.lesson_id
    assert row["teacher_p"] == pytest.approx(0.7) and row["teacher_forecast_receipt_id"] is None
    # The hypothesis: count, hash and the payload holding the words (the row holds none of them).
    assert row["hypothesis_count"] == 1 and row["hypothesis_hash"] == E.text_hash([HYPOTHESIS])
    payload = _rows(lesson.repository, "SELECT payload_json FROM lesson_turn_payloads WHERE turn_id = ?",
                    (row["hypothesis_payload_id"],))
    assert json.loads(payload[0][0])["hypothesis"] == HYPOTHESIS
    assert _rows(lesson.repository, "SELECT action FROM lesson_turns WHERE id = ?", (row["opened_by"],)) == \
        [("note_detour",)]
    # The prior belief at the opening: the brief's prediction for the node's LO, the LO's mastery after the miss,
    # the open misconceptions and hypotheses (counts, ids apart).
    brief_node = next(n for n in S.load_state(lesson.repository, lesson.lesson_id).brief["nodes"]
                      if n["id"] == "lo_eigen")
    assert row["predicted_success"] == pytest.approx(brief_node["prediction"]["p"])
    assert [row["predicted_low"], row["predicted_high"]] == pytest.approx(brief_node["prediction"]["interval"])
    assert row["predicted_source"] == brief_node["prediction"]["source"] == "mastery_ekf"
    mastery = lesson.repository.mastery_state("lo_eigen")
    assert row["mastery_mean"] == pytest.approx(mastery.logit_mean)
    assert row["mastery_variance"] == pytest.approx(mastery.logit_variance)
    assert row["open_misconceptions"] == 0 and row["open_hypotheses"] == 0
    assert json.loads(row["open_ids_json"]) == {"misconceptions": [], "hypotheses": []}
    assert row["origin"] == "learner_pick" and row["origin_decision_id"] is None
    assert row["episode_version"] == E.EPISODE_ROW_VERSION and row["closed_at"] is None
    # Logging only: the detour changed no plan, evidence or schedule.
    assert len(_rows(lesson.repository, "SELECT 1 FROM lesson_plans")) == 1
    assert {entry["kind"] for entry in lesson.view["feed"]} >= {"message", "check", "check_result"}
    # The re-check on the node closes it once, with its attempt, its grade and its minutes.
    lesson.act("reply", {"text": "ok"}, turns=[check_turn()])
    lesson.act("answer_check", {"answer": "det(A - tI) = 0", "tap": 4}, turns=[landed_turn()], right=True)
    (row,) = _episodes(lesson.repository)
    recheck = _rows(lesson.repository, "SELECT attempt_id, correctness FROM lesson_checks ORDER BY created_at")[-1]
    assert row["close_reason"] == "rechecked" and row["recheck_attempt_id"] == recheck[0]
    assert row["outcome_correctness"] == pytest.approx(recheck[1]) == 1.0
    assert row["elapsed_seconds"] == pytest.approx(
        (datetime.fromisoformat(row["closed_at"].replace("Z", "+00:00"))
         - datetime.fromisoformat(row["opened_at"].replace("Z", "+00:00"))).total_seconds())
    # No interval arrived: active time is unknown (missing), never filled in from the elapsed clock.
    assert row["active_seconds"] is None and row["minutes_source"] == "no_intervals"
    assert row["unreported_seconds"] == pytest.approx(row["elapsed_seconds"])
    # The transcript tells the teacher it was logged.
    assert any("detour_noted" in entry for entry in S.transcript(S.load_state(lesson.repository, lesson.lesson_id)))


def test_an_open_detour_closes_with_the_lesson(tmp_path):
    lesson = _detour_lesson(tmp_path)
    lesson.act("reply", {"text": "Let's stop."}, turns=[close_turn()])
    (row,) = _episodes(lesson.repository)
    assert lesson.view["closed"] and row["close_reason"] == "lesson_closed" and row["recheck_attempt_id"] is None


def test_a_plan_that_inserts_a_foundation_with_no_note_is_an_unlogged_detour(tmp_path):
    lesson = _Lesson(tmp_path, [plan_turn])
    lesson.act("reply", {"text": "I'm lost on determinants."}, turns=[foundation_plan])
    (row,) = _episodes(lesson.repository)
    assert row["kind"] == "detour" and row["repair_class"] == E.UNLOGGED and row["node_id"] == "n0"
    assert row["learning_object_id"] == "lo_det" and row["hypothesis_count"] == 0
    assert row["hypothesis_hash"] is None and row["teacher_p"] is None
    assert _rows(lesson.repository, "SELECT action FROM lesson_turns WHERE id = ?", (row["opened_by"],)) == \
        [("write_plan",)]


def test_a_foundation_noted_in_the_same_turn_is_one_logged_detour(tmp_path):
    lesson = _Lesson(tmp_path, [plan_turn])
    lesson.act("reply", {"text": "I'm lost on determinants."}, turns=[lambda c: foundation_plan(c, note=True)])
    (row,) = _episodes(lesson.repository)
    assert row["repair_class"] == "insert_foundation" and row["teacher_p"] == pytest.approx(0.55)


def test_appending_nodes_or_a_first_plan_is_no_detour(tmp_path):
    def appended(context):
        turn = plan_turn(context)
        turn["requests"][0]["plan"].append({"id": "n3", "statement": "Diagonalize with eigenvectors.",
                                            "lo_id": "lo_eigen", "anchors": [], "premises": ["n2"]})
        return turn

    lesson = _Lesson(tmp_path, [plan_turn])
    lesson.act("reply", {"text": "more"}, turns=[appended])
    assert _episodes(lesson.repository) == []


def test_a_note_detour_needs_its_fields_and_is_refused_back_otherwise(tmp_path):
    lesson = _Lesson(tmp_path, [plan_turn])
    bad = {"message": "Hm.", "requests": [{"action": "note_detour", "node": "n1", "p": 0.5}]}
    lesson.act("reply", {"text": "?"}, turns=[bad, {"message": "Fine."}])
    refused = _rows(lesson.repository, "SELECT validation FROM lesson_turns WHERE action = 'teacher_turn'")
    assert ("invalid",) in refused and _episodes(lesson.repository) == []


def test_the_rows_origin_ids_name_the_days_ro5_assignments(tmp_path):
    from learnloop.router_objective import assignments as A

    lesson = _Lesson(tmp_path, [plan_turn])
    with lesson.repository.atomic():
        connection = lesson.repository.connection()
        today = A.insert(connection, experiment_id=A.STOP_COIN, unit_id="rd_1", variant="policy", propensity=0.9,
                         seed="s", draw=0.5, at=(T0 + timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ"))
        A.insert(connection, experiment_id=A.CHECK, unit_id="check-day:old", variant="day", propensity=1.0,
                 seed="s", draw=None, at=(T0 - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ"))
        A.insert(connection, experiment_id=A.PICK, unit_id="later", variant="open", propensity=0.1,
                 seed="s", draw=0.0, at=(T0 + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    lesson.act("reply", {"text": "Go."}, turns=[check_turn()])
    lesson.act("answer_check", {"answer": "no idea"}, turns=[detour_turn()], right=False)
    (row,) = _episodes(lesson.repository)
    # Made on the opening's local day and no later than it: the other day's and the later one are not in force.
    local_start = (T0 + timedelta(minutes=3)).astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    expected = [today] if local_start <= (T0 + timedelta(seconds=30)).astimezone() else []
    assert json.loads(row["experiment_assignment_ids_json"]) == expected


# --- the switch -----------------------------------------------------------------------------------


def test_switch_off_keeps_te1s_lesson_byte_identical(tmp_path):
    assert _schema_sha(TeacherTurnV1) == TE1_SCHEMA_SHA256 and doctrine_hash() == TE1_DOCTRINE_SHA256
    lesson = _Lesson(tmp_path, [plan_turn], config={("teacher", "episode_log"): False})
    lesson.act("reply", {"text": "Go."}, turns=[check_turn()])
    lesson.act("answer_check", {"answer": "the eigenvector itself", "tap": 5}, right=False,
               turns=[{"message": "Let's look at it another way."}])
    # A revised plan that inserts a foundation: no unlogged detour is written with the switch off.
    lesson.act("reply", {"text": "ok"}, turns=[foundation_plan, close_turn()])
    lesson.act("reply", {"text": "done"}, turns=[close_turn()])
    fake = lesson.fake
    # TE1's schema on every call, and TE1's prompt byte for byte.
    assert fake.result_models and set(fake.result_models) == {TeacherTurnV1}
    for purpose, prompt in fake.prompts:
        if purpose != "teacher_turn":
            continue
        rebuilt = render_structured_prompt("LearnLoop lesson: you are the teacher", PROMPT_VERSION,
                                           {"instructions": doctrine_text(), "context": context_of(prompt)},
                                           context_tail_fields=("transcript",))
        assert prompt == rebuilt and "note_detour" not in prompt and "p_held" not in prompt
    # TE1's schema has no note_detour (the fake validates its turns against the schema the lesson asked for).
    with pytest.raises(Exception):
        TeacherTurnV1.model_validate(detour_turn())
    assert lesson.view["closed"]
    assert _rows(lesson.repository, "SELECT COUNT(*) FROM lesson_turns WHERE action = 'note_detour'") == [(0,)]
    assert _rows(lesson.repository, "SELECT COUNT(*) FROM lesson_episodes") == [(0,)]
    assert _rows(lesson.repository, "SELECT COUNT(*) FROM lesson_activity_intervals") == [(0,)]
    payloads = [json.loads(row[0]) for row in _rows(lesson.repository, "SELECT payload_json FROM lesson_turn_payloads")]
    assert all("episodes" not in p for p in payloads)
    assert all(fam == S._family_of("fake-teacher-model") for (fam,) in _rows(
        lesson.repository, "SELECT forecaster_version FROM forecast_receipts WHERE kind LIKE 'lesson_%'"))
    receipt = json.loads(_rows(lesson.repository, "SELECT receipt_json FROM lesson_receipts")[0][0])
    assert "episodes" not in receipt and "minutes" not in receipt
    assert "activity_log" not in lesson.view


def test_switch_on_offers_the_paragraph_the_schema_and_its_own_forecaster(tmp_path):
    lesson = _Lesson(tmp_path, [plan_turn, landed_turn()])
    lesson.act("reply", {"text": "Go."})
    assert set(lesson.fake.result_models) == {TeacherTurnEpisodesV1}
    _purpose, prompt = lesson.fake.prompts[0]
    assert f"{PROMPT_VERSION}{E.PROMPT_SUFFIX}" in prompt and "Keep a log of your detours" in prompt
    rebuilt = render_structured_prompt("LearnLoop lesson: you are the teacher", f"{PROMPT_VERSION}{E.PROMPT_SUFFIX}",
                                       {"instructions": E.instructions(doctrine_text(), True),
                                        "context": context_of(prompt)}, context_tail_fields=("transcript",))
    assert prompt == rebuilt
    # §12.2: a new doctrine version is a new forecaster family, so its λ starts from the seeded prior.
    (family,) = {row[0] for row in _rows(lesson.repository, "SELECT forecaster_version FROM forecast_receipts "
                                                             "WHERE kind = 'lesson_step_retained'")}
    assert family == f"{S.DOCTRINE_VERSION}+{E.EPISODES_VERSION}:fake-teacher-model" != S._family_of("fake-teacher-model")
    from learnloop.learner import lesson_weight as LW

    state = LW.replay_state(load_vault(lesson.paths.root), lesson.repository)
    assert family not in state.pools and state.pool_lambda(family) == state.pool_lambda("a-family-never-seen")


# --- refusals and protection ----------------------------------------------------------------------


def test_a_refused_episode_row_rolls_back_alone_and_never_blocks_the_turn(tmp_path, monkeypatch, caplog):
    from learnloop.db.stores import lessons as store

    def refuse(connection, row):
        connection.execute("INSERT INTO lesson_episodes(id) VALUES (NULL)")  # a write that the CHECKs refuse
        raise AssertionError("unreachable")

    monkeypatch.setattr(store, "insert_episode", refuse)
    lesson = _Lesson(tmp_path, [plan_turn])
    lesson.act("reply", {"text": "Go."}, turns=[check_turn()])
    with caplog.at_level(logging.WARNING, logger="learnloop.teacher.episodes"):
        lesson.act("answer_check", {"answer": "no"}, right=False,
                   turns=[{**detour_turn(), "requests": [*detour_turn()["requests"],
                                                         {"action": "forecast", "forecast_kind": "lesson_step_retained",
                                                          "node": "n2", "p": 0.4}]}])
    assert "episode log" in caplog.text
    assert _rows(lesson.repository, "SELECT COUNT(*) FROM lesson_episodes") == [(0,)]
    # Everything else of the turn stands: the accepted turn, its note, the other request's forecast, the marker.
    actions = [row[0] for row in _rows(lesson.repository, "SELECT action FROM lesson_turns ORDER BY seq")]
    last = len(actions) - 1 - actions[::-1].index("teacher_turn")
    assert actions[last:last + 4] == ["teacher_turn", "note_detour", "forecast", "turn_executed"]
    assert not lesson.view["closed"] and lesson.view["feed"][-1]["kind"] == "message"


def test_a_hypothesis_giving_an_answer_away_is_withheld_and_never_stored(tmp_path):
    key = ITEMS["pi_eig_1"][2]
    lesson = _Lesson(tmp_path, [plan_turn])
    lesson.act("reply", {"text": "Go."}, turns=[check_turn()])
    lesson.act("answer_check", {"answer": "no"}, right=False,
               turns=[detour_turn(hypothesis=f"thinks the answer is {key}"), detour_turn()])
    withheld = _rows(lesson.repository, "SELECT validation FROM lesson_turns WHERE action = 'teacher_turn' "
                                        "AND validation = 'withheld'")
    assert withheld and len(_episodes(lesson.repository)) == 1
    notes = [json.loads(row[0]) for row in _rows(
        lesson.repository, "SELECT p.payload_json FROM lesson_turns t JOIN lesson_turn_payloads p ON p.turn_id = t.id "
                           "WHERE t.action = 'note_detour'")]
    assert [n["hypothesis"] for n in notes] == [HYPOTHESIS]


def test_no_row_holds_any_text(tmp_path):
    """Ids, numbers, enums and hashes only: no hypothesis word, no answer key, no sentinel in any column."""

    from tests.teacher_fakes import SENTINELS

    lesson = _detour_lesson(tmp_path)
    lesson.act("reply", {"text": "lost"}, turns=[foundation_plan, close_turn()])
    rows = _episodes(lesson.repository)
    assert len(rows) == 2
    words = {"WOMBATHYPOTHESIS", "eigenvector", "determinant", *SENTINELS, *(v[2] for v in ITEMS.values())}
    for row in rows:
        for column, value in row.items():
            if isinstance(value, str):
                assert not any(word in value for word in words), (column, value)


def _log_texts(repository):
    """Every text value in the TE2-log rows: the episodes and the forecast receipts."""

    out = []
    with repository.connection() as connection:
        for table in ("lesson_episodes", "forecast_receipts"):
            cursor = connection.execute(f"SELECT * FROM {table}")
            out.extend((table, d[0], v) for row in cursor.fetchall() for d, v in zip(cursor.description, row, strict=True)
                       if isinstance(v, str))
    return out


def _no_reserved_text(repository):
    leaked = [(t, c, v) for t, c, v in _log_texts(repository) if "RESERVEDSENTINEL" in v or "forty-two" in v]
    assert not leaked, leaked


def test_a_note_detour_on_a_node_the_plan_lacks_is_refused_back_and_never_logged(tmp_path):
    """Codex review F1: a note's ``node`` must name a node of the plan (or a brief LO); reserved text there never
    reaches a row, and an unknown node is not filed under the goal LO."""

    from tests.teacher_fakes import RESERVED_SENTINEL

    lesson = _Lesson(tmp_path, [plan_turn])
    lesson.act("reply", {"text": "Go."}, turns=[check_turn()])
    lesson.act("answer_check", {"answer": "no"}, right=False,
               turns=[detour_turn(node=RESERVED_SENTINEL), detour_turn(node="n_unknown"), detour_turn()])
    refused = _rows(lesson.repository, "SELECT validation FROM lesson_turns WHERE action = 'teacher_turn' "
                                       "AND validation != 'ok'")
    assert len(refused) == 2
    (row,) = _episodes(lesson.repository)
    assert row["node_id"] == "n1" and row["learning_object_id"] == "lo_eigen"
    _no_reserved_text(lesson.repository)


def test_a_note_on_a_node_its_own_turns_plan_introduces_is_logged_in_either_order(tmp_path):
    def note_first(context):
        turn = foundation_plan(context)
        turn["requests"].insert(0, {"action": "note_detour", "node": "n0", "hypothesis": HYPOTHESIS,
                                    "repair": "insert_foundation", "p": 0.5})
        return turn

    lesson = _Lesson(tmp_path, [plan_turn])
    lesson.act("reply", {"text": "I'm lost on determinants."}, turns=[note_first])
    (row,) = _episodes(lesson.repository)
    assert row["node_id"] == "n0" and row["learning_object_id"] == "lo_det"
    assert row["repair_class"] == "insert_foundation"


def test_reserved_text_in_a_plan_node_id_never_reaches_a_row(tmp_path):
    from tests.teacher_fakes import RESERVED_SENTINEL

    def reserved_id(context):
        turn = foundation_plan(context)
        turn["requests"][0]["plan"][0]["id"] = RESERVED_SENTINEL
        turn["requests"][0]["plan"][0]["p_held"] = 0.6
        return turn

    lesson = _Lesson(tmp_path, [plan_turn])
    lesson.act("reply", {"text": "I'm lost on determinants."}, turns=[reserved_id, {"message": "Fine."}])
    withheld = _rows(lesson.repository, "SELECT validation FROM lesson_turns WHERE action = 'teacher_turn' "
                                        "AND validation = 'withheld'")
    assert withheld
    _no_reserved_text(lesson.repository)


def test_a_plan_lo_id_that_is_no_vault_lo_never_reaches_a_row(tmp_path):
    # An lo_id carrying reserved text is withheld by the identifier guard (landing ruling R1, tested below); one that
    # is merely no vault LO is accepted and copied nowhere.
    def unknown_lo(context):
        turn = foundation_plan(context)
        turn["requests"][0]["plan"][0]["lo_id"] = "lo_not_in_the_vault"
        turn["requests"][0]["plan"][0]["p_held"] = 0.6
        return turn

    lesson = _Lesson(tmp_path, [plan_turn])
    lesson.act("reply", {"text": "I'm lost on determinants."}, turns=[unknown_lo])
    # The foundation is still an unlogged detour, on no LO (never the goal's by default).
    (row,) = _episodes(lesson.repository)
    assert row["node_id"] == "n0" and row["learning_object_id"] is None
    assert not [v for _t, _c, v in _log_texts(lesson.repository) if "lo_not_in_the_vault" in v]
    _no_reserved_text(lesson.repository)


# --- landing ruling R1: the identifier guard across the vault; refusals by location --------------------------

#: The answer key of a reserved item on a vault LO the lesson's brief does not name (Codex's verify, path 1).
OTHER_SENTINEL = "OTHERSENTINEL the reserved orthogonal answer is ninety-one"


def _reserve_on_another_lo(paths, repository):
    """``lo_else`` on its own concept (so no brief of ``lo_eigen`` names it), with an exam-reserved item whose key is
    :data:`OTHER_SENTINEL`."""

    from learnloop.vault.writer import upsert_concept
    from learnloop.vault.yaml_io import write_yaml
    from tests.practice_index_fakes import _learning_object
    from tests.teacher_fakes import NOW, _item

    upsert_concept(paths.root, "orthogonality_c", {
        "title": "Orthogonality", "type": "concept", "aliases": [], "description": "Orthogonal vectors.",
        "tags": [], "created_at": NOW, "updated_at": NOW})
    lo = _learning_object("lo_else", "Orthogonality")
    lo["concept"] = "orthogonality_c"
    write_yaml(paths.learning_object_path("linear-algebra", "lo_else"), lo)
    write_yaml(paths.practice_item_path("linear-algebra", "pi_else_reserved"),
               _item("pi_else_reserved", "lo_else", "Which of these vectors are orthogonal?", OTHER_SENTINEL))
    with repository.connection() as connection:
        (goal,) = connection.execute("SELECT goal_id FROM exam_pool_items WHERE id = 'epi_te1'").fetchone()
    repository.insert_exam_pool_items([{"id": "epi_else", "goal_id": goal, "practice_item_id": "pi_else_reserved",
                                        "reserved_at": "2026-10-30T00:00:00Z"}])


def _no_text(repository, *words):
    """No TE2-log row, receipt or stored plan holds any of ``words``."""

    texts = list(_log_texts(repository))
    with repository.connection() as connection:
        texts.extend(("lesson_plans", "outline_json", row[0]) for row in connection.execute(
            "SELECT outline_json FROM lesson_plans").fetchall())
    leaked = [(t, c, v) for t, c, v in texts if any(word in v for word in words)]
    assert not leaked, leaked


def _refusals(lesson):
    """The refused turns as the teacher reads them (the transcript's ``refused`` entries)."""

    return [entry for entry in S.transcript(S.load_state(lesson.repository, lesson.lesson_id)) if "refused" in entry]


def test_a_plan_node_carrying_another_los_reserved_key_is_withheld_by_location(tmp_path):
    """Ruling R1 (a), Codex's verify path 1: the brief names only ``lo_eigen`` (and its prerequisite); a revised plan
    inserts a node whose id is the reserved key of ``lo_else``, with ``lo_id`` ``lo_else`` and ``p_held``. The guard
    checks every key the vault records, so the turn is withheld and no row, receipt, prompt or screen holds the key."""

    def other_lo_node(context):
        turn = plan_turn(context)
        turn["requests"][0]["plan"].insert(0, {"id": OTHER_SENTINEL, "statement": "First, a neighbouring idea.",
                                               "lo_id": "lo_else", "anchors": [], "premises": [], "p_held": 0.6})
        return turn

    lesson = _Lesson(tmp_path, [plan_turn], prepare=_reserve_on_another_lo)
    assert "lo_else" not in S.load_state(lesson.repository, lesson.lesson_id).los
    lesson.act("reply", {"text": "Go on."}, turns=[other_lo_node, {"message": "Fine."}])
    (refusal,) = _refusals(lesson)
    assert refusal["refused"] == "answer_key" and refusal["detail"].startswith("requests[0].plan[0].id: ")
    assert _episodes(lesson.repository) == []
    _no_text(lesson.repository, "OTHERSENTINEL", "ninety-one")
    assert "OTHERSENTINEL" not in lesson.fake.all_prompts() and "OTHERSENTINEL" not in str(lesson.view)


def test_a_plan_lo_id_carrying_a_reserved_key_is_withheld_by_location(tmp_path):
    """Ruling R1 (a): a plan node's ``lo_id`` passes the same guard (it reaches a row only as a vault LO, but the
    guard does not rely on that)."""

    def reserved_lo(context):
        turn = plan_turn(context)
        turn["requests"][0]["plan"][1]["lo_id"] = OTHER_SENTINEL
        return turn

    lesson = _Lesson(tmp_path, [plan_turn], prepare=_reserve_on_another_lo)
    lesson.act("reply", {"text": "Go on."}, turns=[reserved_lo, {"message": "Fine."}])
    (refusal,) = _refusals(lesson)
    assert refusal["refused"] == "answer_key" and refusal["detail"].startswith("requests[0].plan[1].lo_id: ")
    _no_text(lesson.repository, "OTHERSENTINEL", "ninety-one")
    assert "OTHERSENTINEL" not in lesson.fake.all_prompts()


def test_a_contract_refusal_names_the_field_by_location_never_by_its_text(tmp_path):
    """Ruling R1 (b), Codex's verify path 2: a plan node whose id is reserved text and whose anchor does not resolve
    is refused at the contract check, before the guard; the refusal names the node by its index, so neither the
    id nor the anchor enters the transcript the teacher reads next."""

    from tests.teacher_fakes import RESERVED_SENTINEL

    def reserved_id_bad_anchor(context):
        turn = plan_turn(context)
        turn["requests"][0]["plan"][0]["id"] = RESERVED_SENTINEL
        turn["requests"][0]["plan"][0]["anchors"] = ["S999"]
        return turn

    lesson = _Lesson(tmp_path, [plan_turn])
    lesson.act("reply", {"text": "Go on."}, turns=[reserved_id_bad_anchor, {"message": "Fine."}])
    (refusal,) = _refusals(lesson)
    assert refusal["refused"] == "contract"
    assert refusal["detail"].startswith("requests[0].plan[0].anchors[0]: ") and "S999" not in refusal["detail"]
    assert "RESERVEDSENTINEL" not in lesson.fake.all_prompts() and "RESERVEDSENTINEL" not in str(lesson.view)
    _no_text(lesson.repository, "RESERVEDSENTINEL", "forty-two")


def test_a_schema_refusal_names_fields_by_location_never_by_their_input(tmp_path):
    """Ruling R1 (b): a turn the schema refuses (a node id over its length, carrying reserved text) is refused back
    with the failing fields' locations and messages only, never their input."""

    from pydantic import ValidationError

    from learnloop.ai.errors import AIInvalidOutput
    from learnloop.ai.schemas import describe_wire_validation_error
    from tests.teacher_fakes import RESERVED_SENTINEL

    def invalid(context):
        # As a provider reports it: AIInvalidOutput with pydantic's description, chained from the ValidationError.
        try:
            TeacherTurnEpisodesV1.model_validate({"message": "Hm.", "requests": [
                {"action": "note_detour", "node": f"{RESERVED_SENTINEL} {RESERVED_SENTINEL}", "hypothesis": "h",
                 "repair": "reteach", "p": 0.5}]})
        except ValidationError as exc:
            raise AIInvalidOutput("Codex returned invalid TeacherTurnEpisodesV1 JSON: "
                                  f"{describe_wire_validation_error(TeacherTurnEpisodesV1, exc)}") from exc
        raise AssertionError("the turn was meant to fail its schema")

    lesson = _Lesson(tmp_path, [plan_turn])
    lesson.act("reply", {"text": "Go on."}, turns=[invalid, {"message": "Fine."}])
    (refusal,) = _refusals(lesson)
    assert refusal["refused"] == "schema" and refusal["detail"].startswith("requests[0].node: ")
    assert "RESERVEDSENTINEL" not in refusal["detail"]
    assert "RESERVEDSENTINEL" not in lesson.fake.all_prompts() and "RESERVEDSENTINEL" not in str(lesson.view)


# --- landing ruling R2: TE1's forecast action resolves and guards its node ----------------------------------


def test_te1s_forecast_node_is_resolved_and_guarded_with_the_switch_off(tmp_path):
    """Ruling R2: TE1's ``forecast`` copies its ``node`` (and the node's LO) into its receipt's key and inputs. With
    ``teacher.episode_log`` off, an unknown node is refused by location, and a plan node whose id or ``lo_id`` carries
    a reserved key is refused by the identifier guard; no receipt holds the key. A plan is now guarded when it is
    written, so the reserved plan here is one stored before this landing (inserted directly)."""

    from learnloop.db.stores import lessons as store

    lesson = _Lesson(tmp_path, [plan_turn], config={("teacher", "episode_log"): False},
                     prepare=_reserve_on_another_lo)
    outline = S.load_state(lesson.repository, lesson.lesson_id).plans[-1]["outline"]
    outline = [*outline, {**outline[0], "id": OTHER_SENTINEL, "lo_id": "lo_eigen"}]
    outline[1] = {**outline[1], "lo_id": OTHER_SENTINEL}
    with lesson.repository.atomic():
        store.insert_plan(lesson.repository.connection(), lesson_id=lesson.lesson_id, outline=outline,
                          created_at="2026-11-05T15:01:30Z")
    # Two refusals and an accepted turn per action (three refusals in a row would end the lesson).
    lesson.act("reply", {"text": "Go."}, turns=[landed_turn(node="n_unknown"), landed_turn(node=OTHER_SENTINEL),
                                                landed_turn(node="n1")])
    lesson.act("reply", {"text": "And?"}, turns=[landed_turn(node="n2"), {"message": "Fine."}])
    refusals = _refusals(lesson)
    assert [(r["refused"], r["detail"].split(": ")[0]) for r in refusals] == [
        ("contract", "requests[0].node"), ("answer_key", "requests[0].node"),
        ("answer_key", "requests[0].node's lo_id")]
    assert all("OTHERSENTINEL" not in r["detail"] and "n_unknown" not in r["detail"] for r in refusals)
    rows = _rows(lesson.repository, "SELECT receipt_key, inputs_json, learning_object_id FROM forecast_receipts "
                                    "WHERE kind = 'lesson_step_retained'")
    assert len(rows) == 1 and ":n1:" in rows[0][0] and rows[0][2] == "lo_eigen"
    assert not [row for row in _rows(lesson.repository, "SELECT * FROM forecast_receipts")
                if any(isinstance(v, str) and ("OTHERSENTINEL" in v or "ninety-one" in v) for v in row)]
    # The refused turns' forecasts were never recorded, so the transcript names none of them either.
    forecasts = [e for e in S.transcript(S.load_state(lesson.repository, lesson.lesson_id)) if "forecast_recorded" in e]
    assert [e["forecast_recorded"]["node"] for e in forecasts] == ["n1"]


def test_te1s_plan_ids_reaching_the_lesson_receipt_are_guarded_with_the_switch_off(tmp_path):
    """Rulings R1 (a), R2, found at the landing's smoke: with ``teacher.episode_log`` off, TE1's plan node ids and
    ``lo_id`` reach the lesson receipt's ``nodes`` (and ``lesson_plans``); a posed check's node reaches a visual's
    record. Each is guarded on every turn, so a reserved key there is withheld by location and the closed lesson's
    receipt and plans hold none of it."""

    def reserved_lo_plan(context):
        turn = plan_turn(context)
        turn["requests"][0]["plan"][1]["lo_id"] = OTHER_SENTINEL
        return turn

    def reserved_check(context):
        turn = check_turn()
        turn["check"]["node"] = OTHER_SENTINEL
        turn["requests"] = []
        return turn

    lesson = _Lesson(tmp_path, [plan_turn], config={("teacher", "episode_log"): False},
                     prepare=_reserve_on_another_lo)
    lesson.act("reply", {"text": "Go."}, turns=[reserved_lo_plan, reserved_check, {"message": "Fine."}])
    lesson.act("reply", {"text": "done"}, turns=[close_turn()])
    assert lesson.view["closed"]
    assert [(r["refused"], r["detail"].split(": ")[0]) for r in _refusals(lesson)] == [
        ("answer_key", "requests[0].plan[1].lo_id"), ("answer_key", "check.node")]
    _no_text(lesson.repository, "OTHERSENTINEL", "ninety-one")
    receipts = [row[0] for row in _rows(lesson.repository, "SELECT receipt_json FROM lesson_receipts")]
    assert receipts and not [r for r in receipts if "OTHERSENTINEL" in r]
    assert "OTHERSENTINEL" not in lesson.fake.all_prompts()


def test_te1s_forecast_on_a_known_node_is_unchanged_with_the_switch_off(tmp_path):
    """Ruling R2: a forecast on a plan node (or a brief LO) is written exactly as TE1 wrote it."""

    lesson = _Lesson(tmp_path, [plan_turn], config={("teacher", "episode_log"): False})
    lesson.act("reply", {"text": "Go."}, turns=[landed_turn(node="n2")])
    lesson.act("reply", {"text": "And?"}, turns=[landed_turn(node="lo_det")])
    assert _refusals(lesson) == []
    rows = _rows(lesson.repository, "SELECT receipt_key, learning_object_id FROM forecast_receipts "
                                    "WHERE kind = 'lesson_step_retained' ORDER BY created_at, receipt_key")
    assert [(key.split(":")[2], lo) for key, lo in rows] == [("n2", "lo_eigen"), ("lo_det", "lo_det")]


def test_teacher_episode_log_is_classified_and_on_by_default():
    from learnloop.config.schema import TeacherConfig
    from learnloop.params.parameter_registry import classify_config_path

    assert TeacherConfig().episode_log is True
    rule = classify_config_path("teacher.episode_log")
    assert rule is not None and rule.kind == "structural" and rule.param_class == "operational"
