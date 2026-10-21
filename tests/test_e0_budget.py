"""The one E0 spend admission (spec §6): $25 across every paid call, reserved first."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import multiprocessing

import pytest

from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEstimate, spend_envelopes
from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.budget import E0BudgetExceeded, E0Ledger, LedgerEnvelope, Request
from learnloop.experiments.contextual_embeddings.callers import E0RequestGate


def _request(usd, category="embeddings", billing="metered", **extra):
    return Request(category=category, provider="voyage", route="voyage-context-4", purpose="t",
                   billing=billing, estimated_usd=usd, **extra)


def test_the_cap_and_allocations_are_the_specs(tmp_path):
    ledger = E0Ledger(tmp_path)
    assert ledger.report()["cap_usd"] == 25.0
    assert {key: value["allocation_usd"] for key, value in ledger.report()["by_category"].items()} == \
        pins.ALLOCATION_USD
    with pytest.raises(ValueError):
        E0Ledger(tmp_path / "x", cap_usd=10.0)  # allocations would exceed the cap


def test_admission_counts_outstanding_reservations_and_unknown_billing_stays_reserved(tmp_path):
    ledger = E0Ledger(tmp_path)
    first = ledger.reserve(_request(1.5))
    with pytest.raises(E0BudgetExceeded):
        ledger.reserve(_request(0.6))  # 1.5 outstanding + 0.6 > the $2 embeddings allocation
    ledger.settle(first, actual_usd=None)  # unknown billing: still 1.5
    with pytest.raises(E0BudgetExceeded):
        ledger.reserve(_request(0.6))
    second = ledger.reserve(_request(0.4))
    ledger.settle(second, actual_usd=0.1)
    report = ledger.report()
    assert report["committed_usd"] == pytest.approx(1.6)
    assert report["outstanding_reservations_usd"] == pytest.approx(1.5)
    assert report["refusals"] == 2


def test_a_failed_request_keeps_its_whole_reservation(tmp_path):
    ledger = E0Ledger(tmp_path)
    with pytest.raises(RuntimeError):
        with ledger.admit(_request(0.25)):
            raise RuntimeError("provider down")
    assert ledger.report()["committed_usd"] == pytest.approx(0.25)


def test_the_global_cap_binds_across_categories(tmp_path):
    ledger = E0Ledger(tmp_path, cap_usd=3.0, allocation={key: 3.0 / 4 for key in pins.ALLOCATION_USD})
    for category in pins.ALLOCATION_USD:
        ledger.reserve(_request(0.7, category=category))
    with pytest.raises(E0BudgetExceeded):
        ledger.reserve(_request(0.2, category="embeddings"))


def test_subscription_requests_are_admitted_at_zero_and_count_requests(tmp_path):
    ledger = E0Ledger(tmp_path, max_requests=3)
    for _ in range(3):
        reservation = ledger.reserve(_request(5.0, category="labels_audits", billing="subscription"))
        ledger.settle(reservation, actual_usd=None, usage={"input_tokens": 100, "output_tokens": 10})
    assert ledger.report()["committed_usd"] == 0.0
    with pytest.raises(E0BudgetExceeded, match="request cap"):
        ledger.reserve(_request(0.0, billing="subscription"))


def test_concurrent_threads_never_overshoot(tmp_path):
    ledger = E0Ledger(tmp_path)

    def attempt(_index):
        try:
            reservation = ledger.reserve(_request(0.03))
        except E0BudgetExceeded:
            return 0
        ledger.settle(reservation, actual_usd=0.03)
        return 1

    with ThreadPoolExecutor(max_workers=16) as pool:
        admitted = sum(pool.map(attempt, range(200)))
    assert admitted == 66  # floor(2.00 / 0.03)
    assert Decimal(str(ledger.report()["committed_usd"])) <= Decimal("2.00")


def _process_worker(directory, count, queue):
    ledger = E0Ledger(directory)
    admitted = 0
    for _ in range(count):
        try:
            ledger.reserve(_request(0.05))
            admitted += 1
        except E0BudgetExceeded:
            pass
    queue.put(admitted)


def test_concurrent_processes_share_one_envelope(tmp_path):
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    workers = [context.Process(target=_process_worker, args=(str(tmp_path), 20, queue)) for _ in range(4)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(60)
    admitted = sum(queue.get(timeout=10) for _ in workers)
    assert admitted == 40  # $2.00 / $0.05, whatever the interleaving
    assert E0Ledger(tmp_path).report()["committed_usd"] == pytest.approx(2.0)


def test_the_ledger_is_a_spend_envelope_for_reused_production_paths(tmp_path):
    ledger = E0Ledger(tmp_path)
    envelope = LedgerEnvelope(ledger, category="embeddings", provider="openrouter", route="qwen")
    budget = SpendBudget(SpendCaps(max_estimated_usd=None))
    with spend_envelopes(envelope):
        with budget.request(SpendEstimate(calls=1, total_tokens=10, estimated_usd=1.5)) as charge:
            charge.reconcile(estimated_usd=0.5)
        with pytest.raises(Exception):
            with budget.request(SpendEstimate(calls=1, total_tokens=10, estimated_usd=1.6)):
                pass
    assert ledger.report()["committed_usd"] == pytest.approx(0.5)


def test_the_request_gate_admits_every_physical_request(tmp_path):
    ledger = E0Ledger(tmp_path)
    gate = E0RequestGate(ledger, pins.ROLE_PINS["adjudicator"], arm="labels")
    admission = gate.admit(None, purpose="label", prompt="x" * 3000, budget=None)
    gate.settle(admission, {"input_tokens": 1200, "output_tokens": 300})
    second = gate.admit(None, purpose="label", prompt="y", budget=None)
    gate.settle(second, {})  # no usage: the reservation stands
    report = ledger.report()
    assert report["requests"] == 2
    pin = pins.ROLE_PINS["adjudicator"]
    assert report["committed_usd"] > (1200 * pin.input_price_per_million + 300 * pin.output_price_per_million) / 1e6
    assert report["by_category"]["labels_audits"]["committed_usd"] == report["committed_usd"]
