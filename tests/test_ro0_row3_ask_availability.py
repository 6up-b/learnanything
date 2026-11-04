"""RO0 row 3 (spec_router_objective_v1 §4): whether Ask was available, per presentation and Reader visit."""

from __future__ import annotations

import json

from learnloop.db.stores import plan_presentations as presentations
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.reader import reader_inquiry as RI
from learnloop.router_objective import ask_availability as AA
from tests.router_mixture_helpers import mixture_env
from tests.router_model_fakes import fake_runtime

OFF = "[router_objective]\nreceipts = false\n"


def _served(tmp_path, *, toml=None):
    env = mixture_env(tmp_path, fake_runtime(), toml=toml)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item"
    return env, step


def _row(env, step):
    with env.repository.connection() as connection:
        found = connection.execute(
            "SELECT * FROM plan_presentations WHERE practice_item_id = ?", (step["practice_item_id"],)).fetchone()
    return dict(found)


def _events(env):
    with env.repository.connection() as connection:
        return [json.loads(row[0]) for row in connection.execute(
            "SELECT detail_json FROM attention_block_events WHERE kind = ? ORDER BY created_at, id", (AA.EVENT_KIND,))]


def test_the_presentation_holds_the_state_at_the_serve(tmp_path):
    env, step = _served(tmp_path)
    assert _row(env, step)["ask_available"] == 1


def test_the_rule_refuses_a_teach_back_and_says_nothing_of_an_unknown_item(tmp_path):
    env, step = _served(tmp_path)
    item = env.vault.practice_items[step["practice_item_id"]]

    class Teaching:
        practice_mode = "teach_back"

    class Vault:
        practice_items = {item.id: Teaching()}

    assert AA.at_serve(Vault, item.id) == 0
    assert AA.at_serve(Vault, "nothing") is None
    assert AA.at_serve(env.vault, item.id) == 1


def test_a_later_change_is_an_event_and_the_row_stands(tmp_path):
    env, step = _served(tmp_path)
    item = step["practice_item_id"]
    before = _row(env, step)
    # The same state again writes nothing.
    assert AA.record_change(env.vault, env.repository, session_id=env.session_id, practice_item_id=item, available=True) is False
    assert AA.record_change(env.vault, env.repository, session_id=env.session_id, practice_item_id=item, available=False,
                            reason="diagnostic_check") is True
    assert AA.record_change(env.vault, env.repository, session_id=env.session_id, practice_item_id=item, available=False) is False
    assert AA.record_change(env.vault, env.repository, session_id=env.session_id, practice_item_id=item, available=True) is True
    assert _row(env, step) == before, "plan_presentations stays append-only"
    assert [(event["ask_available"], event["presentation_id"]) for event in _events(env)] == [
        (0, before["id"]), (1, before["id"])]
    assert _events(env)[0]["reason"] == "diagnostic_check"


def test_an_item_the_plan_did_not_serve_has_no_presentation_to_speak_of(tmp_path):
    env, _step = _served(tmp_path)
    assert AA.record_change(env.vault, env.repository, session_id=env.session_id, practice_item_id="nope", available=False) is False
    assert AA.record_change(env.vault, env.repository, session_id=None, practice_item_id="nope", available=False) is False


def test_the_reopen_returns_the_first_row(tmp_path):
    env, step = _served(tmp_path)
    with env.repository.atomic(), env.repository.connection() as connection:
        row = _row(env, step)
        assert presentations.insert_plan_presentation(connection, {**row, "id": "other", "ask_available": 0}) == row["id"]
    assert _row(env, step)["ask_available"] == 1


def test_off_nothing_is_written(tmp_path):
    env, step = _served(tmp_path, toml=OFF)
    assert _row(env, step)["ask_available"] is None
    assert AA.record_change(env.vault, env.repository, session_id=env.session_id, practice_item_id=step["practice_item_id"],
                            available=False) is False
    assert _events(env) == []


def test_a_reader_visit_says_whether_ask_was_available_and_off_it_does_not(tmp_path):
    env, _step = _served(tmp_path)
    event = {"kind": "reader_view_opened", "payload": {"visit_id": "v1", "extraction_id": "e1", "ask_available": True}}
    RI.record_activity(env.repository, [event], config=env.vault.config)
    off, _ = _served(tmp_path / "off", toml=OFF)
    RI.record_activity(off.repository, [event], config=off.vault.config)

    def payload(target):
        with target.repository.connection() as connection:
            return json.loads(connection.execute(
                "SELECT payload_json FROM interaction_events WHERE kind = 'reader_view_opened'").fetchone()[0])

    assert payload(env)["ask_available"] is True
    assert "ask_available" not in payload(off)
