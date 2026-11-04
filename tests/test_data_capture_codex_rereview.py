"""Data capture A1-A6: the Codex re-review's findings, each reproduced first.

F1 (reopened) with AD's forecast logging off, ordinary Reader activity supplied no exposure, so a warm answer got a
cold label; F9 decisions sharing a check got a replacement question each; F10 a re-offered measurement stayed
unavailable. Fakes only; no network.
"""

from __future__ import annotations

from datetime import timedelta
import json

import pytest

from learnloop.daily_plan import measurement as M
from learnloop.data_capture import reading_exposures as RE
from learnloop.db.stores import data_capture as store
from learnloop.ops import capture_report as CR
from learnloop.router import outcomes as RO
from learnloop.router.first_delayed_success import trajectories

from tests.test_data_capture_a2_measurement import _answer, _arranged_wait, _due_measurement, _events, _objectives, _outcomes
from tests.test_data_capture_codex_review import _due_hint, _hint_instant, _second_decision, _warm_answer
from tests.test_router_g4_restraint import DECIDER_ONLY

AD_OFF = "[adaptive_difficulty]\nenabled = false\n"
RECEIPTS_OFF = "[data_capture]\nreceipts = false\nserving = false\n"


def _count(env, table):
    with env.repository.connection() as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def _complete_section(env, extraction="x", section="sec"):
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO reader_section_progress(extraction_id, section_id, completed_at, updated_at) VALUES (?,?,?,?)",
            (extraction, section, env.now_iso(), env.now_iso()))


def _map_sections(monkeypatch, lo):
    monkeypatch.setattr(RE, "_section_los", lambda _vault, _repo, _extraction, _section: [lo])


def _other_item(env, objective):
    lo = objective["learning_object_id"]
    return next(item.id for item in env.vault.practice_items.values()
                if item.learning_object_id == lo and item.id != objective["practice_item_id"])


# -- F1: the exposure is captured whatever AD's forecast logging says ------------------------------------------------


def _practice_read_answer(tmp_path, monkeypatch, *, toml=DECIDER_ONLY + AD_OFF, read_after_days=2):
    """Monday's practice, Wednesday's completed section, a correct answer 30 minutes later."""

    env, decision_id, objective = _arranged_wait(tmp_path, toml=toml)
    lo = objective["learning_object_id"]
    _map_sections(monkeypatch, lo)
    env.clock.advance(1)
    _answer(env, _other_item(env, objective), lo, correctness=0.4)
    env.clock.instant = env.clock.instant + timedelta(days=read_after_days)
    _complete_section(env)
    env.clock.advance(30)
    _answer(env, objective["practice_item_id"], lo)
    env.clock.advance(1)
    return env, decision_id, objective


def test_f1_a_completed_section_is_an_exposure_with_ad_off(tmp_path, monkeypatch):
    """Reproduced first: no reading receipt with AD off: ``observed``, 1.0, and the time metric's success."""

    env, decision_id, objective = _practice_read_answer(tmp_path, monkeypatch)
    assert not env.vault.config.adaptive_difficulty.enabled
    M.settle(env.vault, env.repository, clock=env.clock)
    assert _count(env, "ad_reading_opportunities") == 0, "AD's own receipt stays AD's"
    assert _count(env, "reading_exposure_receipts") == 1
    outcome = _outcomes(env)[decision_id]
    assert outcome["r_cold_status"] != "observed" and outcome["r_cold_value"] is None
    # The answer a minute after the decision, and the one 30 minutes after the reading.
    assert json.loads(outcome["detail_json"])["r_cold_skip_reasons"] == {"insufficient_delay": 2}
    with env.repository.connection() as connection:
        found, _facts = trajectories(connection, env.vault, success_correctness=0.8, as_of=env.now_iso(),
                                     reader_exposures=RE.read(connection, env.vault, env.repository))
    metric = next(row for row in found if row.learning_object_id == objective["learning_object_id"])
    assert not metric.reached, "the warm answer is no first delayed success"


def test_f1_the_check_answered_after_reading_is_not_the_measurement(tmp_path, monkeypatch):
    env, decision_id, _objective = _practice_read_answer(tmp_path, monkeypatch, read_after_days=30)
    M.settle(env.vault, env.repository, clock=env.clock)
    assert "answered" not in {event["state"] for event in _events(env)[decision_id]}
    assert M.ANSWER_NOT_DELAYED in {event["reason"] for event in _events(env)[decision_id]}


def test_f1_reading_long_before_the_answer_leaves_it_delayed(tmp_path, monkeypatch):
    env, decision_id, objective = _arranged_wait(tmp_path, toml=DECIDER_ONLY + AD_OFF)
    lo = objective["learning_object_id"]
    _map_sections(monkeypatch, lo)
    env.clock.advance(1)
    _complete_section(env)
    M.settle(env.vault, env.repository, clock=env.clock)
    env.clock.instant = env.clock.instant + timedelta(days=30)
    _answer(env, objective["practice_item_id"], lo)
    env.clock.advance(1)
    M.settle(env.vault, env.repository, clock=env.clock)
    assert _outcomes(env)[decision_id]["r_cold_status"] == "observed"


def test_f1_the_sweep_records_each_exposure_once_at_its_source_time(tmp_path, monkeypatch):
    env, _decision_id, objective = _arranged_wait(tmp_path, toml=DECIDER_ONLY + AD_OFF)
    _map_sections(monkeypatch, objective["learning_object_id"])
    _complete_section(env)
    read_at = env.now_iso()
    env.clock.advance(120)
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 1
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 0, "idempotent"
    with env.repository.connection() as connection:
        (row,) = [dict(found) for found in connection.execute("SELECT * FROM reading_exposure_receipts")]
    assert (row["kind"], row["subkind"], row["learning_object_id"]) == ("reading", "section_read", objective["learning_object_id"])
    assert row["source_written_at"].startswith(read_at[:19]) and row["swept_at"] == env.now_iso()


def test_f1_a_section_read_after_the_last_sweep_is_found_by_the_next(tmp_path, monkeypatch):
    env, _decision_id, objective = _arranged_wait(tmp_path, toml=DECIDER_ONLY + AD_OFF)
    _map_sections(monkeypatch, objective["learning_object_id"])
    _complete_section(env, section="one")
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 1
    env.clock.instant = env.clock.instant + timedelta(days=3)
    _complete_section(env, section="two")
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 1
    assert _count(env, "reading_exposure_receipts") == 2


def test_f1_a_span_view_a_tutor_exchange_and_an_in_passage_question_are_exposures_too(tmp_path, monkeypatch):
    env, _decision_id, objective = _arranged_wait(tmp_path, toml=DECIDER_ONLY + AD_OFF)
    lo = objective["learning_object_id"]
    _map_sections(monkeypatch, lo)
    monkeypatch.setattr("learnloop.section_map.learning_objects_for_span",
                        lambda _vault, _repo, **_kwargs: [lo])
    at = env.now_iso()
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_exposure_events(id, extraction_id, span_id, source_id, context, created_at)"
            " VALUES ('e1', 'x', 'sp', 'src', 'reader', ?)", (at,))
        connection.execute(
            "INSERT INTO reader_authored_questions(id, extraction_id, section_id, question_style, status, question_md,"
            " expected_answer_md, prompt_version, anchor_span_ids_json, answered_at, created_at, updated_at)"
            " VALUES ('q1', 'x', 'sec', 'recall', 'answered', 'q', 'a', 'v', '[]', ?, ?, ?)", (at, at, at))
    env.clock.advance(1)
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 2
    with env.repository.connection() as connection:
        kinds = {tuple(row) for row in connection.execute(
            "SELECT kind, subkind FROM reading_exposure_receipts WHERE learning_object_id = ?", (lo,))}
    assert kinds == {("reading", "passage_viewed"), ("in_passage_question", "recall")}


def test_f1_no_receipt_with_both_switches_off(tmp_path, monkeypatch):
    env, _decision_id, objective = _arranged_wait(tmp_path, toml=DECIDER_ONLY + AD_OFF)
    _map_sections(monkeypatch, objective["learning_object_id"])
    _complete_section(env)
    env.vault.config.data_capture.receipts = False
    env.vault.config.data_capture.serving = False
    assert RE.sweep(env.vault, env.repository, clock=env.clock) == 0
    assert _count(env, "reading_exposure_receipts") == 0


def test_f1_a_failed_sweep_never_stops_the_states(tmp_path, monkeypatch):
    env, decision_id, _objective = _due_measurement(tmp_path)

    def boom(*_args, **_kwargs):
        raise RuntimeError("unreadable")

    monkeypatch.setattr(RE, "_events", boom)
    assert M.settle(env.vault, env.repository, clock=env.clock) >= 1
    assert "due" in {event["state"] for event in _events(env)[decision_id]}


def test_f1_the_report_counts_the_exposures_on_record(tmp_path, monkeypatch):
    env, _decision_id, objective = _practice_read_answer(tmp_path, monkeypatch)
    M.settle(env.vault, env.repository, clock=env.clock)
    with env.repository.connection() as connection:
        section = CR.outcome_section(connection, env.vault, env.repository)
    assert section["reading_exposure_receipts"] == 1 and section["ad_reading_receipts"] == 0


# -- F9: a replacement is shared ---------------------------------------------------------------------------------------


def _shared_then_warm(tmp_path):
    env, first_id, objective = _arranged_wait(tmp_path)
    second = _second_decision(env, first_id)
    assert second["measurement"] == M.SHARED and second["commitment_id"] == objective["commitment_id"]
    env.clock.instant = env.clock.instant + timedelta(days=30)
    _warm_answer(env, objective, warm_item=_other_item(env, objective))
    return env, first_id, objective


def _replacements(env, decision_id):
    early = next(event for event in _events(env)[decision_id] if event["reason"] == M.ANSWER_NOT_DELAYED)
    return json.loads(early["detail_json"])


def _open_measurement_commitments(env):
    with env.repository.connection() as connection:
        return connection.execute("SELECT COUNT(*) FROM commitments WHERE created_action = 'test_me_later'").fetchone()[0]


def test_f9_two_decisions_on_one_warm_check_share_one_replacement(tmp_path):
    """Reproduced first: two replacement commitments on different questions of the same LO."""

    env, first_id, _objective = _shared_then_warm(tmp_path)
    M.settle(env.vault, env.repository, clock=env.clock)
    one, other = _replacements(env, first_id), _replacements(env, "d2")
    assert one["replacement_commitment_id"] and one["replacement_commitment_id"] == other["replacement_commitment_id"]
    assert one["practice_item_id"] == other["practice_item_id"]
    assert _open_measurement_commitments(env) == 2, "the answered check and one replacement"


def test_f9_the_one_replacement_answered_cold_measures_both(tmp_path):
    env, first_id, objective = _shared_then_warm(tmp_path)
    M.settle(env.vault, env.repository, clock=env.clock)
    item = _replacements(env, first_id)["practice_item_id"]
    env.clock.instant = env.clock.instant + timedelta(days=30)
    M.settle(env.vault, env.repository, clock=env.clock)
    _answer(env, item, objective["learning_object_id"])
    env.clock.advance(1)
    M.settle(env.vault, env.repository, clock=env.clock)
    for decision_id in (first_id, "d2"):
        assert "answered" in {event["state"] for event in _events(env)[decision_id]}
        assert _outcomes(env)[decision_id]["r_cold_status"] == "observed"


def test_f9_a_later_settlement_reads_the_pending_replacement_from_serving(tmp_path):
    """The next pass has no memory of this one: serving shows the replacement, and it opens past the window."""

    env, first_id, objective = _due_measurement(tmp_path)
    _warm_answer(env, objective, warm_item=_other_item(env, objective))
    M.settle(env.vault, env.repository, clock=env.clock)
    replacement = _replacements(env, first_id)["replacement_commitment_id"]
    later = M._replacement_check(
        env.vault, env.repository, "d_later", objective["learning_object_id"], answered_item=None,
        serving=_stale_serving(env, objective), now=env.clock.now(), clock=env.clock, fresh={})
    assert later.measurement == M.SHARED and later.commitment_id == replacement
    assert _open_measurement_commitments(env) == 2


def test_f9_a_pending_check_due_too_soon_is_not_the_replacement(tmp_path):
    """The window still rules: one that can't measure this decision is left to its own, and another item is asked."""

    env, first_id, objective = _due_measurement(tmp_path)
    arranged = M._replacement_check(
        env.vault, env.repository, first_id, objective["learning_object_id"], answered_item=None,
        serving=_stale_serving(env, objective), now=env.clock.now(), clock=env.clock, fresh={})
    assert arranged.measurement == M.ARRANGED and arranged.commitment_id != objective["commitment_id"]
    assert arranged.practice_item_id != objective["practice_item_id"]
    assert _hint_instant(_due_hint(env, arranged.commitment_id)) >= env.clock.now() + timedelta(seconds=M.DC.MIN_DELAY_SECONDS)


def _stale_serving(env, _objective):
    from learnloop.scheduling.intent.serving import intent_serving

    return intent_serving(env.vault, env.repository, now=env.clock.now(), force=True)


# -- F10: distinct availability transitions ----------------------------------------------------------------------------


def _present(env, item, key):
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, short_circuit_reason, content_hash, created_at)"
                           " VALUES (?, 'practice', 1, '', ?, ?)", (f"b{key}", f"h{key}", env.now_iso()))
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at)"
                           " VALUES (?, ?, ?, 'requested', ?)", (f"p{key}", f"b{key}", item, env.now_iso()))


def _plan_could_not_hold(env, commitment_id, reason="plan_minutes_exhausted"):
    today = env.clock.now().astimezone().date().isoformat()
    split = {"checks_unplanned": [{"commitment_id": commitment_id, "reason": reason}]}
    with env.repository.atomic(), env.repository.connection() as connection:
        connection.execute("UPDATE daily_plans SET local_date = ?, split_json = ?", (today, json.dumps(split)))


def _state(env, decision_id, objective):
    with env.repository.connection() as connection:
        return RO.measurement_state(objective, store.measurement_events(connection)[decision_id])["state"]


def test_f10_an_offer_after_a_postponement_and_a_lost_plan_restores_it(tmp_path):
    """Reproduced first: the second ``offered`` hit the state and reason pair: ``unavailable`` stayed."""

    env, decision_id, objective = _due_measurement(tmp_path)
    item, lo = objective["practice_item_id"], objective["learning_object_id"]
    _present(env, item, 1)
    env.clock.advance(1)
    M.settle(env.vault, env.repository, clock=env.clock)
    assert _state(env, decision_id, objective) == "offered"
    # Assisted practice: it answers nothing and dates the check again.
    _answer(env, item, lo, hints=1)
    env.clock.instant = env.clock.instant + timedelta(days=30)
    _plan_could_not_hold(env, objective["commitment_id"])
    M.settle(env.vault, env.repository, clock=env.clock)
    assert _state(env, decision_id, objective) == "unavailable"
    env.clock.advance(60)
    _present(env, item, 2)
    env.clock.advance(1)
    M.settle(env.vault, env.repository, clock=env.clock)
    assert _state(env, decision_id, objective) == "offered"
    offers = [event for event in _events(env)[decision_id] if event["state"] == "offered"]
    assert [json.loads(event["detail_json"])["presentation_id"] for event in offers] == ["p1", "p2"]


def test_f10_the_same_reason_after_another_offer_is_a_new_transition(tmp_path):
    env, decision_id, objective = _due_measurement(tmp_path)
    item, commitment = objective["practice_item_id"], objective["commitment_id"]
    for key in (1, 2):
        _plan_could_not_hold(env, commitment)
        M.settle(env.vault, env.repository, clock=env.clock)
        assert _state(env, decision_id, objective) == "unavailable", f"lost {key}"
        env.clock.instant = env.clock.instant + timedelta(days=1)
        _present(env, item, key)
        env.clock.advance(1)
        M.settle(env.vault, env.repository, clock=env.clock)
        assert _state(env, decision_id, objective) == "offered", f"restored {key}"
        env.clock.instant = env.clock.instant + timedelta(days=1)
    lost = [event for event in _events(env)[decision_id] if event["state"] == "unavailable"]
    assert len(lost) == 2 and len({event["episode"] for event in lost}) == 2


def test_f10_settling_again_writes_nothing_new(tmp_path):
    env, decision_id, objective = _due_measurement(tmp_path)
    _plan_could_not_hold(env, objective["commitment_id"])
    M.settle(env.vault, env.repository, clock=env.clock)
    env.clock.advance(5)
    assert M.settle(env.vault, env.repository, clock=env.clock) == 0
    env.clock.instant = env.clock.instant + timedelta(days=1)
    _plan_could_not_hold(env, objective["commitment_id"])
    assert M.settle(env.vault, env.repository, clock=env.clock) == 0, "still the same episode"
    assert len([event for event in _events(env)[decision_id] if event["state"] == "unavailable"]) == 1


def test_f10_an_offer_today_outranks_todays_unplanned_reason(tmp_path):
    env, decision_id, objective = _due_measurement(tmp_path)
    _present(env, objective["practice_item_id"], 1)
    env.clock.advance(1)
    _plan_could_not_hold(env, objective["commitment_id"])
    M.settle(env.vault, env.repository, clock=env.clock)
    assert _state(env, decision_id, objective) == "offered"
    assert "unavailable" not in {event["state"] for event in _events(env)[decision_id]}


def test_f10_a_postponed_check_comes_due_again_as_its_own_transition(tmp_path):
    env, decision_id, objective = _due_measurement(tmp_path)
    item, lo = objective["practice_item_id"], objective["learning_object_id"]
    M.settle(env.vault, env.repository, clock=env.clock)
    _answer(env, item, lo, hints=1)
    env.clock.instant = env.clock.instant + timedelta(days=30)
    M.settle(env.vault, env.repository, clock=env.clock)
    assert len([event for event in _events(env)[decision_id] if event["state"] == "due"]) == 2
    assert _state(env, decision_id, objective) == "due"


def test_f10_a_check_answered_between_settles_keeps_one_due_and_is_terminal(tmp_path):
    from learnloop.intent.checks import settle_answered_checks

    env, decision_id, objective = _due_measurement(tmp_path)
    M.settle(env.vault, env.repository, clock=env.clock)
    env.clock.advance(1)
    _answer(env, objective["practice_item_id"], objective["learning_object_id"])
    env.clock.advance(1)
    settle_answered_checks(env.vault, env.repository)
    M.settle(env.vault, env.repository, clock=env.clock)
    events = _events(env)[decision_id]
    assert [event["state"] for event in events] == ["due", "answered"]


@pytest.mark.parametrize("episode", ["", "p1"])
def test_f10_the_store_keeps_one_row_per_episode(tmp_path, episode):
    env, decision_id, _objective = _arranged_wait(tmp_path)
    with env.repository.atomic(), env.repository.connection() as connection:
        write = lambda: store.insert_measurement_event(  # noqa: E731
            connection, decision_id=decision_id, state="offered", episode=episode, at=env.now_iso())
        assert write() is True
        assert write() is False
