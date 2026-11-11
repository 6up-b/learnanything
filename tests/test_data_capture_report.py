"""``learnloop data-capture report``: read-only counts and coverage for each new record."""

from __future__ import annotations

import json
import hashlib

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.ops.capture_report import build_report, lines

from tests.router_mixture_helpers import mixture_env, run
from tests.router_model_fakes import FakeDecider, fake_runtime, first_option, seed_with_first_uniform
from tests.router_g4_restraint_helpers import DECIDER_ONLY, PAST_THE_FLOOR, _followup_env
from tests.helpers import create_basic_vault

TAG = "mvp-0.44"


def _report(env):
    with env.repository.connection() as connection:
        return build_report(connection, env.vault, env.repository, as_of=env.now_iso(), success_correctness=0.8)


def test_the_report_lists_each_record_with_counts_and_coverage(tmp_path):
    runtime = fake_runtime(decider=FakeDecider(choice=first_option, p_yes=0.0),
                           seed=seed_with_first_uniform(at_least=PAST_THE_FLOOR))
    env = _followup_env(tmp_path, runtime, version=TAG, toml=DECIDER_ONLY)
    advance(env, serve=True)
    report = _report(env)
    assert report["algorithm_version"] == TAG and report["switches"] == {"receipts": True, "serving": True}
    pre = report["prefilter_receipts"]
    assert pre["available"] and pre["receipts"] >= 2
    assert pre["by_decision_kind"]["plan_interrupt"]["coverage"] == 1.0
    assert pre["by_decision_kind"]["plan_block"]["receipts"] >= 1
    size = pre["size"]
    assert size["parts_stored"] <= size["parts_referenced"] and size["bytes_stored"] > 0
    assert size["rows_per_active_day"] > 0 and size["bytes_per_active_day"] > 0
    measured = report["measurements"]
    assert measured["objectives"] >= 1 and measured["by_arrangement"].get("arranged", 0) >= 1
    assert "wait" in measured["states_by_arm"]
    assert report["outcomes"]["outcome_version"] == "router_outcomes_v3"
    assert report["outcomes"]["r_cold_by_arm"]["wait"] == {"pending": 1}
    assert "not goal attainment" in report["first_delayed_success"]["label"]
    assert report["floor_and_picks"]["delayed_picks"]["checks"] >= 1
    text = "\n".join(lines(report))
    for needle in ("Prefilter receipts:", "Measurements:", "Outcomes (router_outcomes_v3)", "Time (", "Not-ready floor:"):
        assert needle in text


def test_the_not_ready_floor_is_counted(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), version=TAG)
    run(env)
    floor = _report(env)["floor_and_picks"]["not_ready_floor"]
    assert floor["decisions"] >= 1 and floor["drawn"] >= 1


def test_below_the_tag_the_outcomes_are_v2_and_receipts_are_still_counted(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(), version="mvp-0.43")
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    report = _report(env)
    assert report["switches"] == {"receipts": True, "serving": False}
    assert report["outcomes"]["outcome_version"] == "router_outcomes_v2"
    assert report["prefilter_receipts"]["receipts"] >= 1
    assert report["measurements"]["objectives"] == 0


def test_the_command_is_read_only_and_says_each_section(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    runner = CliRunner()
    result = runner.invoke(app, ["data-capture", "report", "--vault", str(paths.root), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert {"prefilter_receipts", "measurements", "outcomes", "first_delayed_success", "floor_and_picks"} <= set(payload)
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before
    text = runner.invoke(app, ["data-capture", "report", "--vault", str(paths.root)])
    assert text.exit_code == 0 and "Prefilter receipts:" in text.output


def test_a_bad_vault_is_a_plain_refusal(tmp_path):
    result = CliRunner().invoke(app, ["data-capture", "report", "--vault", str(tmp_path)])
    assert result.exit_code == 1 and "learnloop.toml" in result.output


