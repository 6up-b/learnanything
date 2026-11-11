"""``learnloop data-capture report`` gains RO0's coverage per row and measured bytes per day (read-only)."""

from __future__ import annotations

from learnloop.daily_plan.engine import advance, build_plan
from learnloop.ops.capture_report import build_report, lines
from learnloop.router_objective import ask_availability as AA, goal_lifecycle as GL, sessions as S
from learnloop.vault.yaml_io import write_yaml
from learnloop.vault.paths import VaultPaths
from tests.helpers import NOW_ISO
from tests.router_mixture_helpers import mixture_env, run
from tests.router_model_fakes import fake_runtime
from tests.question_context_helpers import FakeTutorClient

GOAL = {"id": "g1", "title": "A goal", "status": "active", "priority": 0.5, "due_at": None, "created_at": NOW_ISO,
        "updated_at": NOW_ISO, "facet_scope": {"concepts": []}, "target_recall": 0.8}


def _report(env):
    from learnloop.vault.loader import load_vault

    vault = load_vault(env.vault.root)
    with env.repository.connection() as connection:
        return build_report(connection, vault, env.repository, as_of=env.now_iso(), success_correctness=0.8)


def test_an_empty_vault_reports_no_coverage_and_no_size(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), toml="[router_objective]\nreceipts = false\n")
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    section = _report(env)["router_objective"]
    assert section["receipts"] is False and section["available"] is True
    assert section["stored_bytes"] == 0 and section["bytes_per_active_day"] is None
    assert section["rows"]["9_13_decision_state"]["written"] == 0
    assert section["rows"]["9_13_decision_state"]["coverage"] is None


def test_each_row_reports_what_was_written_and_measured_bytes(tmp_path):
    from learnloop.tutor.tutor_qa import ask_question

    env = mixture_env(tmp_path, fake_runtime())
    S.record_availability(env.vault, env.repository, "s1", available_minutes=25, clock=env.clock)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    run(env, steps=3)
    record, step = advance(env, serve=True)
    assert step["kind"] == "item"
    AA.record_change(env.vault, env.repository, session_id=env.session_id, practice_item_id=step["practice_item_id"],
                     available=False, clock=env.clock)
    item = step["practice_item_id"]
    ask_question(env.vault, env.repository, FakeTutorClient(), context="practice", question_md="Why?",
                 practice_item_id=item, session_id=env.session_id, clock=env.clock)
    env.repository.insert_source_exposure_event({
        "context": "reader", "extraction_id": "e", "span_id": "s", "initiator": "plan",
        "initiator_session_id": env.session_id})
    write_yaml(VaultPaths(env.vault.root, env.vault.config).goals_path, {"schema_version": 2, "goals": [GOAL]})
    from learnloop.vault.loader import load_vault

    GL.sweep(load_vault(env.vault.root), env.repository, clock=env.clock)
    S.record_end(env.vault, env.repository, "s1", clock=env.clock)
    report = _report(env)
    section = report["router_objective"]
    assert section["receipts"] is True and section["available"]
    rows = section["rows"]
    assert set(rows) == {"1_disclosure_state", "2_generating_process", "3_question_opportunity", "4_exposure_initiator",
                         "5_event_times", "7_session_end", "8_availability", "9_13_decision_state", "10_cold_check_timing",
                         "11_goal_lifecycle", "12_trajectory"}, "every row but 6, the sibling's"
    assert rows["1_disclosure_state"]["coverage"] == 1.0 and rows["1_disclosure_state"]["stored_bytes"] > 0
    assert rows["2_generating_process"]["written"] == 1
    assert rows["3_question_opportunity"]["coverage"] == 1.0 and rows["3_question_opportunity"]["later_changes"] == 1
    assert rows["3_question_opportunity"]["questions_with_an_opportunity"] == 1
    assert rows["4_exposure_initiator"]["by_initiator"] == {"plan": 1}
    assert rows["8_availability"]["written"] == 1 and rows["8_availability"]["missing"] == 0
    assert rows["7_session_end"]["by_reason"] == {"unprompted_stop/explicit": 1}
    state = rows["9_13_decision_state"]
    assert state["coverage"] == 1.0 and state["by_decision_kind"]["plan_block"]["receipts"] >= 1
    assert 0 < state["stored_bytes"] < state["uncompressed_bytes"], "measured, and compressed"
    assert rows["11_goal_lifecycle"]["coverage"] == 1.0 and rows["11_goal_lifecycle"]["by_event"] == {"created": 1}
    assert rows["12_trajectory"]["written"] >= 1 and rows["12_trajectory"]["return_censored"] >= 1
    assert section["active_days"] >= 1 and section["bytes_per_active_day"] > 0
    assert section["per_row_bytes_per_active_day"]["9_13_decision_state"] > 0
    pages = section["new_table_pages_bytes"]
    assert pages["decision_state_receipts"] is None or pages["decision_state_receipts"] > 0
    text = "\n".join(lines(report))
    assert "Router objective receipts:" in text and "row 9_13_decision_state" in text and "bytes per active day" in text


def test_the_report_writes_nothing(tmp_path):
    env = mixture_env(tmp_path, fake_runtime())
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")

    def counts():
        with env.repository.connection() as connection:
            return [connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    for table in ("decision_state_receipts", "session_receipts", "goal_lifecycle_events")]

    before = counts()
    _report(env)
    assert counts() == before
