"""Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): an accepted offer's forecast is bound to the target's first qualifying
cold outcome after the lesson; declined, ignored, an alternative chosen or a lesson not closed is censored.
"""

from __future__ import annotations

import json


from learnloop.algorithm_versions import LESSON_OFFERS_ALGORITHM_VERSION, LESSON_OPPORTUNITY_ALGORITHM_VERSION


TAG = LESSON_OFFERS_ALGORITHM_VERSION
OLD = LESSON_OPPORTUNITY_ALGORITHM_VERSION

# --- the forecast binding -----------------------------------------------------------------------------------------


def test_an_offers_forecast_is_bound_after_the_lesson_or_censored(tmp_path):
    import sqlite3

    from learnloop.router_objective import forecast_resolve as FR

    connection = sqlite3.connect(str(tmp_path / "f.sqlite"))
    connection.row_factory = sqlite3.Row
    connection.executescript(
        "CREATE TABLE router_objective_traces (id TEXT, decision_id TEXT, chosen_ref TEXT, llm_status TEXT, "
        "trace_json TEXT, decision_kind TEXT, created_at TEXT);"
        "CREATE TABLE router_suggestion_responses (decision_id TEXT, response TEXT, lesson_id TEXT);"
        "CREATE TABLE lessons (id TEXT, closed_at TEXT);"
        "CREATE TABLE plan_presentations (id TEXT, router_decision_id TEXT, served_at TEXT);")
    forecast = {"p_cold_1": 0.6, "p_cold_7": 0.5, "p_cold_30": 0.4}
    trace = {"candidates": {"lesson_offer:lo": {"main_lo": "lo", "sensors": {"llm_forecast": forecast}}},
             "policies": {"llm": {"model": "m"}}, "versions": {"llm_schema": "router_llm_choice_v3"}}
    for decision, response, lesson, closed in (("d_acc", "accepted", "les_1", "2026-11-06T10:00:00Z"),
                                                ("d_dec", "declined", None, None),
                                                ("d_open", "accepted", "les_2", None)):
        connection.execute("INSERT INTO router_objective_traces VALUES (?, ?, 'lesson_offer:lo', 'answered', ?, "
                           "'plan_block', '2026-11-06T09:00:00Z')", (f"t_{decision}", decision, json.dumps(trace)))
        connection.execute("INSERT INTO router_suggestion_responses VALUES (?, ?, ?)", (decision, response, lesson))
        if lesson:
            connection.execute("INSERT INTO lessons VALUES (?, ?)", (lesson, closed))
    groups, censored = FR.groups(connection)
    assert [group["decision_id"] for group in groups] == ["d_acc"]
    assert groups[0]["anchor_at"] == "2026-11-06T10:00:00Z"
    assert groups[0]["binding_version"] == FR.OFFER_BINDING_VERSION and "plan_presentation_id" not in groups[0]
    assert censored == {"offer_declined": 1, "offer_lesson_open": 1}
