"""Adaptive difficulty AD1: the round-6 verify's two items, fix round 7
(docs/reviews/adaptive-difficulty-ad1-codex-review.md, "Fix round 7").

Each test failed on 0977c3fb5 for the reason its docstring names. Fakes only:
no network, no paid call.
"""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import AuditDecider, ForecastLLM, ad_plan_vault, rows
from tests.test_ad1_codex_rereview_fixes import _served_with_history
from tests.test_ad1_fix_round6 import _Moving


def test_a_refusal_at_the_deciders_start_receipt_stops_the_request(tmp_path, monkeypatch):
    """Medium: a reload between the Decider's gate check and its start
    receipt made the last confirmation (at the receipt) refuse, but the
    Decider's ``UsageCollector`` swallowed the sink's exception: the request
    was sent, its receipt stayed ``interrupted``, and the outer gate settled
    real usage. The refusal now propagates: no transport call, the receipt
    closed as interrupted, the outer gate settled with nothing."""

    from learnloop.adaptive_difficulty import claims
    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation
    from learnloop.ai.execution import gate_model_requests

    paths, step = _served_with_history(tmp_path)
    vault = load_vault(paths.root)
    provider = _Moving(vault)
    settled: list[tuple[object, dict]] = []

    class Outer:
        def admit(self, client, *, purpose, prompt, budget):
            return f"admission:{purpose}"

        def settle(self, admission, usage):
            settled.append((admission, dict(usage)))

    record = claims.FencedRepository.record_model_event

    def reload_before_the_deciders_receipt(self, action, event, **kwargs):
        if action == "start" and event.get("judge") == "decider":
            provider.current += 1  # a harmless reload, after the gate's check
        return record(self, action, event, **kwargs)

    monkeypatch.setattr(claims.FencedRepository, "record_model_event", reload_before_the_deciders_receipt)
    decider = AuditDecider(p_yes=0.6)
    with gate_model_requests(Outer()):
        outcomes = {outcome.forecaster: outcome for outcome in forecast_presentation(
            vault, Repository(paths.sqlite_path), step["presentation_id"],
            clients=Clients(llm=ForecastLLM(p_correct=0.4), decider=decider), live_vault=provider)}
    assert outcomes["llm_v3:llm"].status == "ok"
    assert decider.calls == [], "no transport call"
    assert outcomes["llm_v3:decider"].status == "stale"
    receipts = rows(paths.sqlite_path, "SELECT status, error_type, cost FROM model_call_receipts "
                                       "WHERE judge = 'decider'")
    assert [(row["status"], row["error_type"]) for row in receipts] == [("interrupted", "StaleSnapshot")]
    assert receipts[0]["cost"] is None
    decider_settled = [usage for admission, usage in settled if admission == "admission:ad_item_forecast"]
    assert decider_settled and all(not usage for usage in decider_settled), "the gate settled with nothing"


def test_a_refused_decider_record_labels_the_decider_status(tmp_path, monkeypatch):
    """Low: a reload after the Decider's record check refused its record
    (the audit ``stale``), but ``decider_status`` stayed ``ok``. It is now
    the refusal's status, as the LLM's handler sets it."""

    from learnloop.adaptive_difficulty import sending
    from learnloop.adaptive_difficulty.feature_audit import audit_revision

    paths = ad_plan_vault(tmp_path)
    vault = load_vault(paths.root)
    provider = _Moving(vault)
    check = sending.SendGuard.check

    def check_then_reload(self, purpose="request"):
        generation = check(self, purpose)
        if purpose.startswith("recording the Decider"):
            provider.current += 1
        return generation

    monkeypatch.setattr(sending.SendGuard, "check", check_then_reload)
    outcome = audit_revision(vault, Repository(paths.sqlite_path), vault.practice_items["pi_m1a"],
                             decider_factory=lambda: AuditDecider(), llm_client=ForecastLLM(), live_vault=provider)
    assert outcome.status == "stale"
    assert outcome.decider_status == "stale"
