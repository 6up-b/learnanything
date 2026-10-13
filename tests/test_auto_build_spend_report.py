"""Automatic book preparation's spend is visible (docs/reviews/reading-hardening.md, part 4).

The owner observes real spend before setting caps (2026-10-13). ``learnloop
sources report`` showed the source service's spend only; it now also shows
automatic builds' per-day metered spend under their own daily guard
(``ingest.cost_pause.daily_cap_usd``, $5 by default), reserved (the estimate a
metered build was planned with) vs settled (what its receipts cost), and the
largest builds. No new UI. Receipts are synthetic rows; no model is called.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.content.pipeline.add_source import auto_build_spend_report, latest_auto_outcome
from learnloop.vault.loader import load_vault

from tests.test_ux_phase1_review_fixes import _add, _build_batches, _jobs, _metered, _receipt
from tests.ux_phase1_support import CLOCK, fake_services, fresh_library, set_config, write_book


def _built_book(tmp_path):
    """A book whose first automatic build ran on a metered route ($1 per
    million tokens), with its plan's estimate kept on the build."""

    root = fresh_library(tmp_path)
    authoring = _metered(root, 1.0)
    set_config(root, {("ingest", "cost_pause", "threshold_usd"): 100.0})
    repo, jobs = _jobs(root, fake_services(authoring))
    item = _add(root, jobs, write_book(tmp_path))
    outcome = latest_auto_outcome(repo, item["source_id"])
    assert outcome["outcome"] == "building" and outcome["estimate_usd"] > 0
    build = _build_batches(repo)[0]
    job_ids = [job["id"] for job in repo.ingest_jobs_for_batch(build["id"])]
    return root, repo, item["source_id"], build, job_ids, outcome


def test_the_report_shows_automatic_builds_daily_spend_under_their_guard(tmp_path):
    root, repo, source_id, build, job_ids, outcome = _built_book(tmp_path)
    today = CLOCK.now()
    yesterday = (today - timedelta(days=1)).isoformat()
    # The house fakes' own calls (free) are receipts of the build too.
    baseline = auto_build_spend_report(load_vault(root), repo, days=2, now=today)
    fake_receipts = baseline["days"][-1]["auto_builds"]["metered_receipts"]
    fake_estimated = baseline["days"][-1]["auto_builds"]["estimated_only"]
    assert baseline["days"][-1]["auto_builds"]["settled_usd"] == 0.0
    # The build's own requests: a reported cost, one priced from its tokens
    # (300k tokens at $1/M), and one yesterday; a subscription request; and a
    # metered request that is not an automatic build's (Ask, grading).
    _receipt(repo, provider="openrouter", cost=0.30, owner_kind="ingest_job", owner_id=job_ids[0])
    _receipt(repo, provider="openrouter", input_tokens=200_000, output_tokens=100_000, owner_kind="ingest_job",
             owner_id=job_ids[-1])
    _receipt(repo, provider="openrouter", cost=0.10, owner_kind="ingest_job", owner_id=job_ids[0],
             started_at=yesterday)
    _receipt(repo, provider="codex_medium", input_tokens=50_000, owner_kind="ingest_job", owner_id=job_ids[-1])
    _receipt(repo, provider="openrouter", cost=0.50, owner_id="tutor_1")

    report = auto_build_spend_report(load_vault(root), repo, days=2, now=today)

    guard = report["daily_guard"]
    assert guard["cap_usd"] == 5.0  # ingest.cost_pause.daily_cap_usd
    assert guard["counted_usd"] == round(0.30 + 0.30 + 0.50, 4)  # every metered receipt today
    assert guard["auto_build_usd"] == round(0.30 + 0.30, 4)
    assert guard["reserved_usd"] == 0.0  # the build finished: nothing held back
    assert guard["remaining_usd"] == round(5.0 - 1.10, 4)
    assert guard["threshold_usd"] == 100.0

    before, now = report["days"]
    assert (before["day"], now["day"]) == ((today - timedelta(days=1)).date().isoformat(), today.date().isoformat())
    assert before["auto_builds"]["settled_usd"] == 0.10 and before["auto_builds"]["metered_receipts"] == 1
    assert now["auto_builds"]["settled_usd"] == 0.60
    assert now["auto_builds"]["metered_receipts"] == fake_receipts + 2
    assert now["auto_builds"]["estimated_only"] == {"receipts": fake_estimated["receipts"] + 1,
                                                    "tokens": fake_estimated["tokens"] + 50_000}
    assert now["all_metered_usd"] == 1.10
    # Reserved: the estimate the metered build was planned with, on its day.
    assert now["reserved_usd"] == round(outcome["estimate_usd"], 4)

    [largest] = report["largest_builds"]
    assert largest["batch_id"] == build["id"] and largest["source_id"] == source_id
    assert largest["settled_usd"] == 0.70 and largest["reserved_usd"] == round(outcome["estimate_usd"], 4)
    assert largest["receipts"] == fake_receipts + fake_estimated["receipts"] + 4
    assert largest["estimated_only_tokens"] == fake_estimated["tokens"] + 50_000
    assert largest["status"] == "completed" and largest["chapters"] and largest["title"]


def test_a_build_still_running_is_held_back_by_the_guard(tmp_path):
    root, repo, _source_id, build, job_ids, outcome = _built_book(tmp_path)
    with repo.connection() as connection:  # the build is still running
        connection.execute("UPDATE ingest_batches SET status = 'running' WHERE id = ?", (build["id"],))
        connection.commit()
    _receipt(repo, provider="openrouter", cost=0.05, owner_kind="ingest_job", owner_id=job_ids[0])

    guard = auto_build_spend_report(load_vault(root), repo, days=1, now=CLOCK.now())["daily_guard"]

    held = round(max(outcome["estimate_usd"] - 0.05, 0.0), 4)
    assert guard["counted_usd"] == 0.05
    assert guard["reserved_usd"] == held
    assert guard["remaining_usd"] == round(5.0 - 0.05 - held, 4)


def test_sources_report_shows_it_beside_the_source_services(tmp_path):
    root, repo, _source_id, build, job_ids, _outcome = _built_book(tmp_path)
    _receipt(repo, provider="openrouter", cost=0.25, owner_kind="ingest_job", owner_id=job_ids[0],
             started_at=datetime.now(UTC).isoformat())

    result = CliRunner().invoke(app, ["sources", "report", "--vault", str(root), "--json", "--spend-days", "1"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert "service_spend" in report
    spend = report["auto_build_spend"]
    assert spend["daily_guard"]["cap_usd"] == 5.0
    assert spend["days"][-1]["auto_builds"]["settled_usd"] == 0.25
    assert spend["largest_builds"][0]["batch_id"] == build["id"]

    text = CliRunner().invoke(app, ["sources", "report", "--vault", str(root), "--spend-days", "1"])
    assert text.exit_code == 0, text.output
    assert "automatic book preparation spend" in text.output
    assert "largest builds:" in text.output and build["id"] in text.output

    none = CliRunner().invoke(app, ["sources", "report", "--vault", str(root), "--json", "--spend-days", "0"])
    assert "auto_build_spend" not in json.loads(none.output)
