"""Adaptive difficulty AD1: the paid routes' spend framework, the background jobs and the owner commands.

Spec §8.2, §11.4, §14 AD1; orchestrator note 3: the outside forecasters and
the feature audit run behind their switches, inside
``adaptive_difficulty.daily_spend_cap_usd`` (a metered LLM route needs
``adaptive_difficulty.price_per_million``; a refused call is a
``refused_spend`` receipt), in the background (never on the serve's request
path), and ``learnloop ad data-check`` / ``ad backfill --dry-run`` read only.
Fakes only.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from typer.testing import CliRunner

from learnloop.clock import FrozenClock
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import ForecastLLM, AuditDecider, ad_plan_vault, ad_receipts, plan_env, rows


class MeteredLLM(ForecastLLM):
    provider_name = "fake_metered"
    provider_type = "openrouter"


def _serve(paths):
    env, clock = plan_env(paths)
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")
    _record, step = advance(env, serve=True)
    return env, clock, step


def test_a_metered_llm_route_without_a_price_is_refused_before_sending(tmp_path):
    from learnloop.adaptive_difficulty.outside import Clients, forecast_item

    paths = ad_plan_vault(tmp_path)
    vault = load_vault(paths.root)
    llm = MeteredLLM()
    outcome = forecast_item(vault, Repository(paths.sqlite_path), vault.practice_items["pi_m1a"],
                            clients=Clients(llm=llm))
    assert outcome.status == "refused_spend" and llm.prompts == []
    receipt = ad_receipts(paths.sqlite_path)[0]
    assert receipt["status"] == "refused_spend" and receipt["p"] is None
    # A refused forecast never blocks a later one for the revision.
    priced = ad_plan_vault(tmp_path / "priced", config="[adaptive_difficulty]\nprice_per_million = 1.0\n")
    vault = load_vault(priced.root)
    ok = forecast_item(vault, Repository(priced.sqlite_path), vault.practice_items["pi_m1a"],
                       clients=Clients(llm=MeteredLLM(p_correct=0.3)))
    assert ok.status == "ok"


def test_the_daily_cap_refuses_a_metered_call_once_spent(tmp_path):
    from learnloop.adaptive_difficulty.outside import Clients, forecast_item

    paths = ad_plan_vault(tmp_path, config="[adaptive_difficulty]\nprice_per_million = 1.0\ndaily_spend_cap_usd = 0.0\n")
    vault = load_vault(paths.root)
    llm = MeteredLLM()
    outcome = forecast_item(vault, Repository(paths.sqlite_path), vault.practice_items["pi_m1a"],
                            clients=Clients(llm=llm))
    assert outcome.status == "refused_spend" and llm.prompts == []
    assert "adaptive_difficulty.daily_spend_cap_usd" in (outcome.reason or "")


def test_the_feature_audit_respects_the_cap_and_falls_back_honestly(tmp_path):
    from learnloop.adaptive_difficulty.feature_audit import audit_revision

    paths = ad_plan_vault(tmp_path, config="[adaptive_difficulty]\nprice_per_million = 1.0\ndaily_spend_cap_usd = 0.0\n")
    vault = load_vault(paths.root)
    llm = MeteredLLM(audit={"complexity": "1"})
    outcome = audit_revision(vault, Repository(paths.sqlite_path), vault.practice_items["pi_m1a"],
                             decider_factory=lambda: AuditDecider(), llm_client=llm)
    # The Decider is priced at its listed input price: a zero cap refuses it,
    # and the metered fallback too; nothing answered, every refusal ledgered.
    assert outcome.decider_status == "refused" and outcome.llm_status == "refused"
    assert outcome.status == "failed" and llm.prompts == []
    ledger = rows(paths.sqlite_path, "SELECT verdict, judge FROM judgment_ledger WHERE task = 'ad_feature_audit'")
    assert {(row["verdict"], row["judge"]) for row in ledger} == {("refused", "decider")}


def test_background_jobs_run_off_the_request_path_once_each(tmp_path):
    from learnloop.adaptive_difficulty.background import schedule_item_preparation, schedule_presentation_forecasts
    from learnloop.adaptive_difficulty.outside import Clients
    from learnloop.hints.map_builder import BackgroundBuilds

    paths = ad_plan_vault(tmp_path)
    _env, _clock, step = _serve(paths)
    vault = load_vault(paths.root)
    builds = BackgroundBuilds()
    builds.bind(paths.sqlite_path)
    clients = Clients(llm=ForecastLLM(audit={"complexity": "1"}), decider=AuditDecider())
    thread = schedule_presentation_forecasts(vault, paths.sqlite_path, step["presentation_id"], clients=clients,
                                             builds=builds)
    assert thread is not None
    thread.join(30)
    forecasters = {receipt["forecaster"] for receipt in ad_receipts(paths.sqlite_path)}
    assert {"llm_v3:llm", "llm_v3:decider"} <= forecasters
    prepared = schedule_item_preparation(vault, paths.sqlite_path, ["pi_m1b"], clients=clients, builds=builds)
    assert prepared is not None
    prepared.join(30)
    assert rows(paths.sqlite_path, "SELECT COUNT(*) AS n FROM judgment_ledger WHERE task = 'ad_feature_audit'")[0]["n"]
    assert [receipt for receipt in ad_receipts(paths.sqlite_path) if receipt["scope"] == "item"]
    # Prepared to the end in this process: a later plan read schedules nothing.
    assert schedule_item_preparation(vault, paths.sqlite_path, ["pi_m1b"], clients=clients, builds=builds) is None
    builds.close()


def test_without_an_injected_client_the_test_suite_starts_no_ad_job(tmp_path):
    from learnloop.adaptive_difficulty.background import schedule_item_preparation, schedule_presentation_forecasts

    paths = ad_plan_vault(tmp_path)
    _env, _clock, step = _serve(paths)
    vault = load_vault(paths.root)
    assert schedule_presentation_forecasts(vault, paths.sqlite_path, step["presentation_id"]) is None
    assert schedule_item_preparation(vault, paths.sqlite_path, ["pi_m1a"]) is None


def test_ad_data_check_is_read_only_and_reports_the_tables(tmp_path):
    from learnloop.cli import app

    paths = ad_plan_vault(tmp_path)
    _serve(paths)
    before = paths.sqlite_path.read_bytes()
    result = CliRunner().invoke(app, ["ad", "data-check", "--vault", str(paths.root), "--json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    vault = load_vault(paths.root)
    assert report["items"] == len(vault.practice_items)
    assert report["difficulty_source"]["llm_estimate"] == 3
    assert report["items_with_task_features"] == 3
    assert {"latency", "answer_confidence", "hints", "primed", "difficulty_rating"} <= set(report["coverage"])
    assert report["ad1_receipts"]["item_serve_inputs"] == 1
    assert "historical_revision_status" in report and "first_surface_attempts_per_cell" in report
    assert paths.sqlite_path.read_bytes() == before


def test_ad_backfill_dry_run_plans_and_writes_nothing(tmp_path):
    from learnloop.cli import app

    paths = ad_plan_vault(tmp_path)
    before = paths.sqlite_path.read_bytes()
    result = CliRunner().invoke(app, ["ad", "backfill", "--vault", str(paths.root), "--audit", "--llm-v1",
                                      "--reading", "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    plan = json.loads(result.output)
    active = len([item for item in load_vault(paths.root).practice_items.values() if item.status == "active"])
    assert plan["dry_run"] is True
    assert plan["audit"]["status"] == "planned" and plan["audit"]["revisions"] == active
    assert plan["audit"]["dimensions"] == 5 * active
    assert plan["llm_v1"] == {"status": "planned", "items": active, "calls": active,
                              "estimated_input_tokens": plan["llm_v1"]["estimated_input_tokens"]}
    assert plan["reading"] == {"status": "planned", "model_calls": 0}
    assert paths.sqlite_path.read_bytes() == before
    refused = CliRunner().invoke(app, ["ad", "backfill", "--vault", str(paths.root), "--dry-run"])
    assert refused.exit_code == 1 and "name at least one" in refused.output


def test_a_real_reading_backfill_sweeps_the_history_with_no_model(tmp_path):
    from learnloop.adaptive_difficulty.backfill import backfill

    paths = ad_plan_vault(tmp_path)
    vault = load_vault(paths.root)
    result = backfill(vault, Repository(paths.sqlite_path), audit=False, llm_v1=False, reading=True, dry_run=False,
                      clock=FrozenClock(datetime(2026, 10, 12, 9, 0, tzinfo=UTC)))
    assert result["reading"]["status"] == "done" and result["reading"]["written"] == 0
