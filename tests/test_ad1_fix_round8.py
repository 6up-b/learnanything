"""Adaptive difficulty AD1: AD's start receipt fails closed, fix round 8
(docs/reviews/adaptive-difficulty-ad1-codex-review.md, "Fix round 8").

Any exception at AD's start receipt stops the dispatch: a lease lost at the
receipt (``stale``), a storage error writing it (``failed``), the last
confirmation's refusal (its own status), and an error closing the receipt
after a refusal (logged; the refusal stands). Fakes only: no network, no paid
call.
"""

from __future__ import annotations

import sqlite3

import pytest

from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import AuditDecider, ForecastLLM, rows
from tests.test_ad1_codex_rereview_fixes import _served_with_history
from tests.test_ad1_fix_round6 import _Moving

INJECTIONS = {
    # the verify's first: a reload before dispatch (StaleSnapshot), then closing the receipt fails
    "finish_fails_after_stale": "stale",
    # the verify's second: the claim's lease is lost at the start receipt
    "lease_lost_at_start": "stale",
    # a storage error writing the start receipt
    "storage_error_at_start": "failed",
}


def _targets(path: str, event: dict) -> bool:
    return (event.get("judge") == "decider") == (path == "decider")


@pytest.mark.parametrize("path", ["llm", "decider"])
@pytest.mark.parametrize("injection", sorted(INJECTIONS))
def test_any_failure_at_ads_start_receipt_stops_the_dispatch(tmp_path, monkeypatch, path, injection):
    """On 7ee922e29 the Decider's ``UsageCollector`` swallowed a lost lease, a
    storage error, and a cleanup error that had replaced the refusal, so the
    Decider request was sent anyway; on the LLM path the cleanup error
    replaced the refusal's ``stale`` with ``failed``."""

    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation
    from learnloop.hints.map_builder import _LeaseLost

    paths, step = _served_with_history(tmp_path)
    vault = load_vault(paths.root)
    provider = _Moving(vault)
    record = Repository.record_model_event
    hit = {"start": False}

    def injected(self, action, event, **kwargs):
        if action == "start" and not hit["start"] and _targets(path, event):
            hit["start"] = True
            if injection == "finish_fails_after_stale":
                provider.current += 1  # a harmless reload before dispatch
            elif injection == "lease_lost_at_start":
                raise _LeaseLost("another worker took the claim")
            else:
                raise sqlite3.OperationalError("database is locked")
        if action == "finish" and injection == "finish_fails_after_stale" and event.get("status") == "interrupted":
            raise sqlite3.OperationalError("database is locked")
        return record(self, action, event, **kwargs)

    monkeypatch.setattr(Repository, "record_model_event", injected)
    llm, decider = ForecastLLM(p_correct=0.4), AuditDecider(p_yes=0.6)
    outcomes = {outcome.forecaster: outcome for outcome in forecast_presentation(
        vault, Repository(paths.sqlite_path), step["presentation_id"], clients=Clients(llm=llm, decider=decider),
        live_vault=provider)}
    assert hit["start"], "the injection reached the targeted start receipt"
    target = "llm_v3:llm" if path == "llm" else "llm_v3:decider"
    sent = llm.prompts if path == "llm" else decider.calls
    assert sent == [], "zero transport calls"
    assert outcomes[target].status == INJECTIONS[injection]
    if path == "decider":
        assert outcomes["llm_v3:llm"].status == "ok" and len(llm.prompts) == 1


def test_a_cleanup_failure_after_a_refusal_is_logged_and_the_refusal_stands(tmp_path, monkeypatch, caplog):
    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation

    paths, step = _served_with_history(tmp_path)
    vault = load_vault(paths.root)
    provider = _Moving(vault)
    record = Repository.record_model_event

    def injected(self, action, event, **kwargs):
        if action == "start" and event.get("judge") == "decider":
            provider.current += 1
        if action == "finish" and event.get("status") == "interrupted":
            raise sqlite3.OperationalError("database is locked")
        return record(self, action, event, **kwargs)

    monkeypatch.setattr(Repository, "record_model_event", injected)
    decider = AuditDecider()
    with caplog.at_level("WARNING"):
        outcomes = {outcome.forecaster: outcome for outcome in forecast_presentation(
            vault, Repository(paths.sqlite_path), step["presentation_id"],
            clients=Clients(llm=ForecastLLM(), decider=decider), live_vault=provider)}
    assert decider.calls == [] and outcomes["llm_v3:decider"].status == "stale"
    assert "could not close the refused request's receipt" in caplog.text
    started = rows(paths.sqlite_path, "SELECT status FROM model_call_receipts WHERE judge = 'decider'")
    assert [row["status"] for row in started] == ["started"], "the close failed: the honest record is a start"


@pytest.mark.parametrize("injection", sorted(INJECTIONS))
def test_the_item_forecasts_start_receipt_fails_closed_with_the_right_status(tmp_path, monkeypatch, injection):
    """The LLM item path (``llm_v1:item``): on 7ee922e29 a cleanup error after
    the refusal escaped ``forecast_item`` instead of returning ``stale``."""

    from learnloop.adaptive_difficulty.outside import Clients, forecast_item
    from learnloop.hints.map_builder import _LeaseLost

    from tests.ad_fakes import ad_plan_vault

    paths = ad_plan_vault(tmp_path)
    vault = load_vault(paths.root)
    provider = _Moving(vault)
    record = Repository.record_model_event
    hit = {"start": False}

    def injected(self, action, event, **kwargs):
        if action == "start" and not hit["start"]:
            hit["start"] = True
            if injection == "finish_fails_after_stale":
                provider.current += 1
            elif injection == "lease_lost_at_start":
                raise _LeaseLost("another worker took the claim")
            else:
                raise sqlite3.OperationalError("database is locked")
        if action == "finish" and injection == "finish_fails_after_stale" and event.get("status") == "interrupted":
            raise sqlite3.OperationalError("database is locked")
        return record(self, action, event, **kwargs)

    monkeypatch.setattr(Repository, "record_model_event", injected)
    llm = ForecastLLM(p_correct=0.5)
    outcome = forecast_item(vault, Repository(paths.sqlite_path), vault.practice_items["pi_m1a"],
                            clients=Clients(llm=llm), live_vault=provider)
    assert hit["start"] and llm.prompts == []
    assert outcome.status == INJECTIONS[injection]
