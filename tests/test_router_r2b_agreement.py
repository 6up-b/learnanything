"""Router R2b: the agreement-report adapter, and G6 (replay never asks a model).

The Decider migration's report (``learnloop decider agreement``) reads the
router's own decisions through an adapter: each decision both models answered
becomes ledger-shaped rows (``router_choose_block``, the sensors, the
restraint), never duplicated into ``judgment_ledger``. Rebuilding
``router_outcomes`` over mixture decisions calls no model and is
deterministic.
"""

from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.ai.agreement import agreement_report
from learnloop.cli import app
from learnloop.db.connection import connect
from learnloop.router.agreement import router_agreement_rows, router_decision_rows_for_agreement
from learnloop.router.outcomes import rebuild_router_outcomes

from tests.router_mixture_helpers import mixture_env, rows, run
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime, first_option


def test_the_router_decisions_feed_the_agreement_report(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(choice=first_option), llm=FakeLLM()))
    run(env)
    with connect(env.repository.sqlite_path, read_only=True) as connection:
        decisions = router_decision_rows_for_agreement(connection)
    assert decisions
    report = agreement_report(router_agreement_rows(decisions))
    choose = report["tasks"]["router_choose_block"]
    assert choose["pairs"] == len(decisions) and choose["decider_answers"] == len(decisions)
    assert 0.0 <= choose["agreement"] <= 1.0
    assert "router_teach_first" in report["tasks"] and "router_will_pass_next" in report["tasks"]
    # Nothing was copied into the judgment ledger.
    with env.repository.connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM judgment_ledger WHERE task LIKE 'router_%'").fetchone()[0] == 0
    result = CliRunner().invoke(app, ["decider", "agreement", "--vault", str(env.vault.root), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["tasks"]["router_choose_block"]["pairs"] == len(decisions)


def test_a_failed_decider_is_a_fallback_in_the_report(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(error=RuntimeError("down")), llm=FakeLLM()))
    run(env)
    with connect(env.repository.sqlite_path, read_only=True) as connection:
        report = agreement_report(router_agreement_rows(router_decision_rows_for_agreement(connection)))
    choose = report["tasks"]["router_choose_block"]
    assert choose["pairs"] == 0 and choose["decider_failures"] == {"failed": choose["fallbacks"]}
    assert choose["fallbacks"] > 0


def test_replay_never_asks_a_model_and_is_deterministic(tmp_path, monkeypatch):
    from learnloop.daily_plan import router_runtime

    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM()))
    run(env)
    assert any(row["policy"] == "router_mixture_v1" for row in rows(env))

    def forbidden(*_args, **_kwargs):
        raise AssertionError("a rebuild asked a model")

    monkeypatch.setattr(router_runtime, "call_decider", forbidden)
    monkeypatch.setattr(router_runtime, "call_llm", forbidden)
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", forbidden)

    def rebuilt():
        with env.repository.atomic(), env.repository.connection() as connection:
            rebuild_router_outcomes(connection)
            return [dict(row) for row in connection.execute("SELECT * FROM router_outcomes ORDER BY decision_id")]

    first = rebuilt()
    assert first and rebuilt() == first
    assert {row["outcome_version"] for row in first} == {"router_outcomes_v2"}
