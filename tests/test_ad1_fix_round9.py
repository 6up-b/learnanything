"""Adaptive difficulty AD1: a dispatch stopped at an audit request stops the
audit, fix round 9 (docs/reviews/adaptive-difficulty-ad1-codex-review.md,
"Fix round 9").

A ``ReceiptWriteFailed`` at the Decider's start receipt only set the local
status: the audit then wrote five failed judgments, ran the LLM fallback and
could return ``audited``, which the queue settled. Per round 8's contract it
now returns at once: no further judgment, no fallback, ``failed`` (``stale``
for a lost lease), the dimensions unanswered, the revision kept queued. Each
test failed on 2ad80dff7. Fakes only: no network, no paid call.
"""

from __future__ import annotations

import sqlite3

import pytest

from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import AuditDecider, ForecastLLM, ad_plan_vault, rows
from tests.test_ad1_fix_round4 import _builds

FULL = {"complexity": "1", "transfer": "near", "scaffolding": "cue", "span": "single_step",
        "response": "short_constructed"}
AUDIT_ONLY = "[adaptive_difficulty]\noutside_forecasters = []\n"
EXPECTED = {"storage_error": "failed", "lease_lost": "stale"}


def _fail_the_deciders_receipt(monkeypatch, injection: str, *, times: int | None = None) -> dict:
    from learnloop.hints.map_builder import _LeaseLost

    record = Repository.record_model_event
    count = {"n": 0}

    def injected(self, action, event, **kwargs):
        if action == "start" and event.get("judge") == "decider" and (times is None or count["n"] < times):
            count["n"] += 1
            if injection == "lease_lost":
                raise _LeaseLost("another worker took the claim")
            raise sqlite3.OperationalError("database is locked")
        return record(self, action, event, **kwargs)

    monkeypatch.setattr(Repository, "record_model_event", injected)
    return count


def _audits(paths):
    return rows(paths.sqlite_path, "SELECT * FROM judgment_ledger WHERE task = 'ad_feature_audit'")


@pytest.mark.parametrize("injection", sorted(EXPECTED))
def test_a_stopped_decider_request_stops_the_audit(tmp_path, monkeypatch, injection):
    """The verify's case, through the audit."""

    from learnloop.adaptive_difficulty.feature_audit import DIMENSIONS, audit_revision

    paths = ad_plan_vault(tmp_path)
    vault = load_vault(paths.root)
    _fail_the_deciders_receipt(monkeypatch, injection)
    decider, llm = AuditDecider(), ForecastLLM(audit=FULL)
    outcome = audit_revision(vault, Repository(paths.sqlite_path), vault.practice_items["pi_m1a"],
                             decider_factory=lambda: decider, llm_client=llm)
    assert decider.calls == [] and llm.prompts == [], "nothing sent, no fallback"
    assert _audits(paths) == [], "no judgment written after the failure"
    assert outcome.status == EXPECTED[injection] and outcome.decider_status == EXPECTED[injection]
    assert sorted(outcome.unanswered) == sorted(DIMENSIONS)


def test_the_backfill_records_a_stopped_audit_as_failed(tmp_path, monkeypatch):
    """The backfill path: every revision's audit stops at its Decider request."""

    from learnloop.adaptive_difficulty.backfill import backfill
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path, config=AUDIT_ONLY)
    _fail_the_deciders_receipt(monkeypatch, "storage_error")
    decider, llm = AuditDecider(), ForecastLLM(audit=FULL)
    result = backfill(load_vault(paths.root), Repository(paths.sqlite_path), audit=True, llm_v1=False,
                      reading=False, dry_run=False, clients=Clients(llm=llm), decider_factory=lambda: decider)
    assert set(result["audit"]["by_status"]) == {"failed"}
    assert decider.calls == [] and llm.prompts == []
    assert _audits(paths) == []


def test_the_queue_keeps_a_stopped_audit_for_a_retry(tmp_path, monkeypatch):
    """The queue's settle decision: the stopped audit used to finish as
    ``audited`` through the fallback and be settled; it is now ``failed``,
    kept, and the next trigger audits it."""

    from learnloop.adaptive_difficulty.background import schedule_item_preparation
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path, config=AUDIT_ONLY)
    vault = load_vault(paths.root)
    _fail_the_deciders_receipt(monkeypatch, "storage_error", times=1)
    decider, llm = AuditDecider(), ForecastLLM(audit=FULL)
    builds, clients = _builds(paths), Clients(llm=llm, decider=decider)
    try:
        schedule_item_preparation(vault, paths.sqlite_path, ["pi_m1a"], clients=clients, builds=builds).join(30)
        assert llm.prompts == [] and _audits(paths) == []
        again = schedule_item_preparation(vault, paths.sqlite_path, ["pi_m1a"], clients=clients, builds=builds)
        assert again is not None, "failed: kept queued, never settled"
        again.join(30)
        assert len(decider.calls) == 1 and len(_audits(paths)) == 5
    finally:
        builds.close()
