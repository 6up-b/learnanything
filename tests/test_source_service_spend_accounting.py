"""The sources daily cap counts every request exactly once (sources-spend-accounting).

Codex's verification of ee3115d5 left two findings in the shared daily cap
(``source_service.max_daily_cost_usd``):

* F2 (reopened): a receipt that names its reservation was left out of the
  total even when the reservation had never been reconciled with it. A worker
  that dies after its $0.90 receipt is written but before ``PaidCalls._reconcile``
  leaves the reservation at its $0.15 estimate, and the next $0.20 request was
  admitted under a $1 cap ($1.10 spent).
* F14: after the upgrade, a request settled before receipts named their
  reservation was counted twice: by its ledger row and by its unlinked receipt.

One accounting function now serves admission, recovery and reports: a
reservation counts the larger of its own charge and what its receipts show
while its owner lives, what its receipts show once reconciled, and nothing
once released with no receipt; a receipt that names no reservation counts
once by its own cost. Every test uses fakes and no network.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import multiprocessing
import os
from pathlib import Path
import signal
import threading
import time
from types import SimpleNamespace

import pytest

from learnloop.ai.execution import model_call, observe_model_calls, record_model_calls
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEstimate, SpendLimitExceeded, spend_envelopes
from learnloop.db.connection import connect
from learnloop.db.migrate import apply_migrations, default_migrations_dir
from learnloop.db.repositories import Repository
from learnloop.source_retrieval import service_spend as SS

PRICE = 10.0  # dollars per million tokens


def _vault(cap: float = 1.0, *, providers: dict | None = None) -> SimpleNamespace:
    """The vault configuration the daily cap reads (its cap, price and providers)."""

    return SimpleNamespace(config=SimpleNamespace(
        source_service=SimpleNamespace(max_daily_cost_usd=cap, llm_price_per_million=PRICE),
        ai=SimpleNamespace(providers=providers or {})))


def _database(tmp_path, cap: float = 1.0):
    SS._DAILY.clear()
    return _vault(cap), Repository(tmp_path / "state.sqlite")


def _process(vault, repository) -> SS.SharedDailyEnvelope:
    """A process's own daily envelope (another process shares only the database)."""

    return SS.SharedDailyEnvelope(vault, repository, day=SS.midnight(), cap=float(vault.config.source_service.max_daily_cost_usd))


def _dies(repository, handle: str) -> None:
    """The owning process dies: nothing renews its reservation's lease any more."""

    leases = getattr(SS, "_LEASES", None)
    if leases is not None:
        leases.drop(repository, handle)


def _owner_terminal(repository, handle: str) -> None:
    """The dead owner's lease has run out."""

    with connect(repository.sqlite_path) as connection:
        connection.execute("UPDATE source_service_spend SET lease_expires_at='2000-01-01T00:00:00Z' WHERE id=?",
                           (handle,))
        connection.commit()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _receipt(repository, receipt_id: str, *, cost: float | None, reservation: str | None = None,
             owner_kind: str = "source_exercise_import", status: str = "completed",
             started_at: str | None = None) -> None:
    """A durable root receipt (as ``record_model_event`` writes it), naming its reservation."""

    budget: dict[str, object] = {"billing": "metered"}
    if reservation is not None:
        budget["envelope_reservations"] = [reservation]
    with connect(repository.sqlite_path) as connection:
        connection.execute(
            "INSERT INTO model_call_receipts(id, owner_kind, owner_id, purpose, provider, status, started_at, "
            "input_tokens, output_tokens, cost, budget_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (receipt_id, owner_kind, "x", "p", "openrouter", status, started_at or _now(), None, None, cost,
             json.dumps(budget)))
        connection.commit()


def _finish(repository, receipt_id: str, cost: float) -> None:
    with connect(repository.sqlite_path) as connection:
        connection.execute("UPDATE model_call_receipts SET status='completed', cost=? WHERE id=?", (cost, receipt_id))
        connection.commit()


def _row(repository, handle: str) -> dict:
    with connect(repository.sqlite_path, read_only=True) as connection:
        return dict(connection.execute("SELECT * FROM source_service_spend WHERE id=?", (handle,)).fetchone())


def _admits(envelope, usd: float) -> bool:
    try:
        handle = envelope.reserve(Decimal(str(usd)))
    except SpendLimitExceeded:
        return False
    envelope.settle(handle, Decimal(str(usd)))  # paid exactly its estimate
    return True


# -- F2 (reopened): a linked receipt counts until its reservation is reconciled with it -----------------


def test_a_receipt_written_before_reconciliation_counts_its_cost(tmp_path):
    """Codex's reproduction: reserve $0.15 under a $1 cap, persist a completed
    $0.90 receipt naming that reservation, leave the reservation unreconciled
    (the worker died between the receipt and ``PaidCalls._reconcile``), then
    ask for $0.20. Before the fix the total was $0.15 and the request was
    admitted: $1.10 of actual spend plus reservation under a $1 cap."""

    vault, repository = _database(tmp_path)
    worker = _process(vault, repository)
    handle = worker.reserve(Decimal("0.15"))
    _receipt(repository, "r_paid", cost=0.90, reservation=handle)
    _dies(repository, handle)
    other = _process(vault, repository)
    assert not _admits(other, 0.20)
    # The reports read the same total.
    assert SS.service_spend_today(vault, repository)["usd"] == pytest.approx(0.90)
    assert other.report()["metered_usd"] == pytest.approx(0.90)
    assert _admits(other, 0.10)  # $0.90 + $0.10 fits


def test_a_request_settled_without_its_reported_cost_counts_its_receipt(tmp_path):
    """The same window inside one process: the receipt recorded the provider's
    $0.90, reconciliation never ran (it raised, or was skipped), and the
    request settled at its $0.15 estimate. The receipt is durable; it counts."""

    vault, repository = _database(tmp_path)
    worker = _process(vault, repository)
    client = SimpleNamespace(provider_name="openrouter", model="metered-fake-model")
    budget = SpendBudget(SpendCaps(max_calls=10, max_estimated_usd=10.0))
    with record_model_calls(repository, owner_kind="source_compare", owner_id="cmp_1"), spend_envelopes(worker), \
            budget.request(SpendEstimate(calls=1, total_tokens=10, estimated_usd=0.15)):
        with model_call(client, purpose="SourceComparison") as metadata:
            metadata.update(cost=0.90, input_tokens=0, output_tokens=0)
    other = _process(vault, repository)
    assert not _admits(other, 0.20)
    assert SS.service_spend_today(vault, repository)["usd"] == pytest.approx(0.90)


def test_a_finished_request_counts_its_reported_cost_once(tmp_path):
    """A reconciled request counts what its receipt shows, once: neither its
    estimate nor its receipt and its reservation together."""

    vault, repository = _database(tmp_path)
    worker = _process(vault, repository)
    client = SimpleNamespace(provider_name="openrouter", model="metered-fake-model")
    budget = SpendBudget(SpendCaps(max_calls=10, max_estimated_usd=10.0))
    with record_model_calls(repository, owner_kind="source_compare", owner_id="cmp_1"), spend_envelopes(worker), \
            budget.request(SpendEstimate(calls=1, total_tokens=10, estimated_usd=0.30)) as charge:
        with model_call(client, purpose="SourceComparison") as metadata:
            metadata.update(cost=0.05, input_tokens=0, output_tokens=0)
        charge.reconcile(estimated_usd=0.05)
    spent = SS.service_spend_today(vault, repository)
    assert spent["usd"] == pytest.approx(0.05)
    assert spent["reservations_usd"] == pytest.approx(0.05) and spent["unlinked_receipts_usd"] == 0
    assert spent["metered"]["linked_requests"] == 1
    assert _admits(_process(vault, repository), 0.95)



def test_a_request_settled_without_its_cost_counts_a_lower_reported_cost(tmp_path):
    """Reconciled with its receipt: a request whose receipt reported $0.05
    counts $0.05, not its $0.30 estimate, even when its owner settled without
    the cost (reconciliation skipped)."""

    vault, repository = _database(tmp_path)
    worker = _process(vault, repository)
    client = SimpleNamespace(provider_name="openrouter", model="metered-fake-model")
    budget = SpendBudget(SpendCaps(max_calls=10, max_estimated_usd=10.0))
    with record_model_calls(repository, owner_kind="source_compare", owner_id="cmp_1"), spend_envelopes(worker), \
            budget.request(SpendEstimate(calls=1, total_tokens=10, estimated_usd=0.30)):
        with model_call(client, purpose="SourceComparison") as metadata:
            metadata.update(cost=0.05, input_tokens=0, output_tokens=0)
    assert SS.service_spend_today(vault, repository)["usd"] == pytest.approx(0.05)
    assert _admits(_process(vault, repository), 0.95)

# -- recovery: orphaned reservations are reconciled with their receipts, or released -------------


def test_recovery_reconciles_an_orphan_with_its_receipt(tmp_path):
    """Once the dead owner's lease runs out, admission reconciles its
    reservation with the receipt it left: the receipt's cost from then on,
    higher or lower than the estimate."""

    vault, repository = _database(tmp_path)
    worker = _process(vault, repository)
    over = worker.reserve(Decimal("0.15"))
    _receipt(repository, "r_over", cost=0.60, reservation=over)
    under = worker.reserve(Decimal("0.30"))
    _receipt(repository, "r_under", cost=0.05, reservation=under)
    for handle in (over, under):
        _dies(repository, handle)
        _owner_terminal(repository, handle)
    other = _process(vault, repository)
    assert not _admits(other, 0.36)  # $0.60 + $0.05 + $0.36 passes $1
    assert _row(repository, over)["state"] == "settled" and _row(repository, over)["resolved_by"] == "recovery"
    assert _row(repository, over)["charged_usd"] == pytest.approx(0.60)
    assert _row(repository, under)["charged_usd"] == pytest.approx(0.05)
    assert _admits(other, 0.35)
    assert SS.service_spend_today(vault, repository)["usd"] == pytest.approx(1.0)


def test_an_orphan_whose_request_never_finished_keeps_its_estimate(tmp_path):
    """The owner died while its request was in flight: the receipt says
    ``started`` with no usage. The provider may have charged; the request is
    bounded by its admitted estimate, never counted as free."""

    vault, repository = _database(tmp_path)
    worker = _process(vault, repository)
    handle = worker.reserve(Decimal("0.50"))
    _receipt(repository, "r_started", cost=None, reservation=handle, status="started")
    _dies(repository, handle)
    _owner_terminal(repository, handle)
    other = _process(vault, repository)
    assert not _admits(other, 0.51)
    assert _row(repository, handle)["state"] == "settled"
    assert _row(repository, handle)["charged_usd"] == pytest.approx(0.50)
    assert _admits(other, 0.50)


def test_recovery_releases_an_unsent_reservation_only_after_its_owner_is_terminal(tmp_path):
    """A reservation with no receipt was never sent (a request writes its
    receipt before it is sent). While its owner lives it stays counted; once
    the owner's lease has run out it is released."""

    vault, repository = _database(tmp_path)
    worker = _process(vault, repository)
    handle = worker.reserve(Decimal("0.60"))
    other = _process(vault, repository)
    assert not _admits(other, 0.50)  # the owner is alive: its request may be about to be sent
    assert _row(repository, handle)["state"] == "in_flight"
    _dies(repository, handle)
    _owner_terminal(repository, handle)
    assert _admits(other, 0.50)
    row = _row(repository, handle)
    assert (row["state"], row["resolved_by"], row["charged_usd"]) == ("released", "recovery", 0.0)


def test_a_released_reservation_cannot_start_its_request(tmp_path):
    """Fencing: an owner presumed dead (its lease ran out while it was
    suspended between its reservation and its request) wakes up after
    recovery released the reservation. Its receipt cannot start, so the
    request is refused before it is sent, and the release stands."""

    vault, repository = _database(tmp_path)
    worker = _process(vault, repository)
    client = SimpleNamespace(provider_name="openrouter", model="metered-fake-model")
    budget = SpendBudget(SpendCaps(max_calls=10, max_estimated_usd=10.0))
    sent: list[bool] = []
    with pytest.raises(SpendLimitExceeded, match="released by recovery"):
        with record_model_calls(repository, owner_kind="source_compare", owner_id="cmp_1"), \
                spend_envelopes(worker), budget.request(SpendEstimate(calls=1, total_tokens=10, estimated_usd=0.30)):
            with connect(repository.sqlite_path, read_only=True) as connection:
                (handle,) = [row[0] for row in connection.execute("SELECT id FROM source_service_spend")]
            _owner_terminal(repository, handle)  # suspended past its lease
            assert _admits(_process(vault, repository), 0.01)  # another process's admission releases it
            with model_call(client, purpose="SourceComparison"):  # the owner wakes up and sends
                sent.append(True)
    assert sent == []
    with connect(repository.sqlite_path, read_only=True) as connection:
        assert connection.execute("SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind='source_compare'"
                                  ).fetchone()[0] == 0
    assert _row(repository, handle)["state"] == "released"
    assert SS.service_spend_today(vault, repository)["usd"] == pytest.approx(0.01)


def test_a_receipt_naming_a_released_reservation_still_counts(tmp_path):
    """Defense in depth: a receipt that names a released reservation (written
    by a path outside the fenced recorder) counts, bounded by the estimate
    until it finishes; the heartbeat never revives the released row; the
    owner's settlement records what it paid, once."""

    vault, repository = _database(tmp_path)
    worker = _process(vault, repository)
    handle = worker.reserve(Decimal("0.30"))
    _owner_terminal(repository, handle)
    other = _process(vault, repository)
    assert _admits(other, 0.01)  # recovery releases the reservation
    assert _row(repository, handle)["state"] == "released"
    SS._LEASES.renew_now()  # the owner's heartbeat renews nothing
    assert _row(repository, handle)["state"] == "released"
    _receipt(repository, "r_late", cost=None, reservation=handle, status="started")
    assert SS.service_spend_today(vault, repository)["usd"] == pytest.approx(0.31)
    _finish(repository, "r_late", 0.05)
    assert SS.service_spend_today(vault, repository)["usd"] == pytest.approx(0.06)
    worker.charge(Decimal("0.40"), handle)  # an in-flight charge does not apply to a released row
    worker.settle(handle, Decimal("0.05"))
    row = _row(repository, handle)
    assert (row["state"], row["resolved_by"], row["charged_usd"]) == ("settled", "owner", 0.05)
    assert SS.service_spend_today(vault, repository)["usd"] == pytest.approx(0.06)


def test_a_live_owner_renews_its_lease(tmp_path):
    vault, repository = _database(tmp_path)
    worker = _process(vault, repository)
    handle = worker.reserve(Decimal("0.10"))
    _owner_terminal(repository, handle)
    SS._LEASES.renew_now()  # the heartbeat of a live process
    assert _row(repository, handle)["lease_expires_at"] > SS.utc_now_iso()
    other = _process(vault, repository)
    assert not _admits(other, 0.95)  # still in flight, still counted
    assert _row(repository, handle)["state"] == "in_flight"
    worker.settle(handle, Decimal("0.10"))
    assert _admits(other, 0.90)



def test_the_heartbeat_keeps_a_live_owners_lease(tmp_path, monkeypatch):
    """The process's heartbeat thread renews the leases it holds, so a live
    owner's unsent reservation is never taken for an orphan."""

    import time

    keeper = SS._Leases()
    monkeypatch.setattr(SS, "_LEASES", keeper)
    monkeypatch.setattr(SS, "HEARTBEAT_SECONDS", 0.05)
    vault, repository = _database(tmp_path)
    worker = _process(vault, repository)
    handle = worker.reserve(Decimal("0.60"))
    _owner_terminal(repository, handle)  # as if a beat were overdue
    deadline = time.monotonic() + 10
    while _row(repository, handle)["lease_expires_at"] < SS.utc_now_iso() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert _row(repository, handle)["lease_expires_at"] > SS.utc_now_iso()
    assert not _admits(_process(vault, repository), 0.50)
    worker.settle(handle, Decimal("0.60"))
    deadline = time.monotonic() + 10
    while keeper._thread is not None and time.monotonic() < deadline:
        time.sleep(0.05)
    assert keeper._thread is None  # nothing held: the heartbeat stops


# -- a receipt counts once, on its reservation's day ------------------------------------------------


def test_a_receipt_naming_a_reservation_that_is_gone_counts_by_its_own_cost(tmp_path):
    vault, repository = _database(tmp_path)
    _receipt(repository, "r_dangling", cost=0.30, reservation="ssp_gone", owner_kind="practice_rerank")
    spent = SS.service_spend_today(vault, repository)
    assert spent["usd"] == pytest.approx(0.30) and spent["unlinked_receipts_usd"] == pytest.approx(0.30)


def test_a_request_reserved_yesterday_counts_on_yesterdays_cap(tmp_path):
    """A reservation made before midnight whose receipt started after it is
    counted by that day's reservation, not again today."""

    vault, repository = _database(tmp_path)
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    with connect(repository.sqlite_path) as connection:
        connection.execute(
            "INSERT INTO source_service_spend (id, envelope, day, reserved_usd, charged_usd, state, legacy, process, "
            "lease_expires_at, resolved_by, created_at, updated_at) VALUES "
            "('ssp_yesterday', ?, ?, 0.2, 0.4, 'settled', 0, 'proc_old', NULL, 'owner', ?, ?)",
            (SS.DAILY_ENVELOPE, yesterday, yesterday + "T23:59:59Z", SS.utc_now_iso()))
        connection.commit()
    _receipt(repository, "r_after_midnight", cost=0.40, reservation="ssp_yesterday")
    assert SS.service_spend_today(vault, repository)["usd"] == pytest.approx(0.0)

# -- concurrent admission -------------------------------------------------------------------------


@pytest.mark.durability
def test_concurrent_admission_counts_the_unreconciled_receipt(tmp_path):
    """Eight threads, each with its own envelope and connections (one process
    token: the separate-process race is the next test), race for $0.125 each
    under a $1 cap while a dead worker's $0.50 receipt is unreconciled
    ($0.125 reserved). Exactly four fit; before the fix seven were admitted
    ($1.375 spent)."""

    vault, repository = _database(tmp_path)
    worker = _process(vault, repository)
    handle = worker.reserve(Decimal("0.125"))
    _receipt(repository, "r_dead", cost=0.50, reservation=handle)
    _dies(repository, handle)
    barrier = threading.Barrier(8)
    admitted: list[bool] = []
    lock = threading.Lock()

    def process() -> None:
        envelope = _process(vault, repository)
        barrier.wait()
        try:
            envelope.reserve(Decimal("0.125"))
            outcome = True
        except SpendLimitExceeded:
            outcome = False
        with lock:
            admitted.append(outcome)

    threads = [threading.Thread(target=process) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert admitted.count(True) == 4, admitted
    assert SS.service_spend_today(vault, repository)["usd"] == pytest.approx(1.0)


# Separate OS processes (spawned: each its own interpreter, connections, heartbeat
# and owner token). Module-level, so a spawned child can import them.


def _child_admission(sqlite_path: str, usd: str, ready, go, results) -> None:
    """A separate process asking for ``usd`` under the shared $1 cap."""

    repository = Repository.attach(Path(sqlite_path))
    envelope = _process(_vault(1.0), repository)
    ready.set()
    go.wait(60)
    try:
        envelope.reserve(Decimal(usd))
        results.put((SS.PROCESS, True))
    except SpendLimitExceeded:
        results.put((SS.PROCESS, False))


def _child_owner(sqlite_path: str, usd: str, receipt_cost: float | None, lease_seconds: float,
                 heartbeat_seconds: float, die: bool, release, results) -> None:
    """A separate process that reserves ``usd`` and writes its request's receipt.
    It then dies before reconciling (SIGKILL), or stays alive (its heartbeat
    renewing its lease) until released, and settles."""

    SS.LEASE_SECONDS, SS.HEARTBEAT_SECONDS = lease_seconds, heartbeat_seconds
    repository = Repository.attach(Path(sqlite_path))
    envelope = _process(_vault(1.0), repository)
    handle = envelope.reserve(Decimal(usd))
    if receipt_cost is not None:
        _receipt(repository, "r_" + handle, cost=receipt_cost, reservation=handle)
    results.put((SS.PROCESS, handle))
    if die:
        results.close()
        results.join_thread()  # the queue's feeder has written the handle
        os.kill(os.getpid(), signal.SIGKILL)
    release.wait(120)
    envelope.settle(handle, Decimal(usd))


@pytest.mark.durability
def test_separate_processes_race_for_the_shared_cap(tmp_path):
    """The same race as above between eight OS processes: exactly four fit,
    and each admitted reservation carries its own process's owner token."""

    vault, repository = _database(tmp_path)
    worker = _process(vault, repository)
    handle = worker.reserve(Decimal("0.125"))
    _receipt(repository, "r_dead", cost=0.50, reservation=handle)
    _dies(repository, handle)
    context = multiprocessing.get_context("spawn")
    go, results = context.Event(), context.Queue()
    ready = [context.Event() for _ in range(8)]
    children = [context.Process(target=_child_admission,
                                args=(str(repository.sqlite_path), "0.125", ready[index], go, results))
                for index in range(8)]
    try:
        for child in children:
            child.start()
        assert all(event.wait(120) for event in ready)
        go.set()
        outcomes = [results.get(timeout=120) for _ in children]
        for child in children:
            child.join(timeout=60)
            assert child.exitcode == 0
    finally:
        for child in children:
            if child.is_alive():
                child.kill()
                child.join(timeout=10)
    admitted = [token for token, outcome in outcomes if outcome]
    assert len(admitted) == 4, outcomes
    assert len({token for token, _outcome in outcomes} | {SS.PROCESS}) == 9  # nine owner tokens
    with connect(repository.sqlite_path, read_only=True) as connection:
        owners = [row[0] for row in connection.execute(
            "SELECT process FROM source_service_spend WHERE id != ? AND state='in_flight'", (handle,))]
    assert sorted(owners) == sorted(admitted)
    assert SS.service_spend_today(vault, repository)["usd"] == pytest.approx(1.0)
    worker.settle(handle, Decimal("0.125"))


@pytest.mark.durability
def test_a_killed_owner_process_is_recovered_while_a_live_ones_lease_holds(tmp_path):
    """Two owner processes with short leases: one is killed after writing its
    $0.60 receipt and before reconciling its $0.30 reservation; the other
    stays alive with $0.20 reserved. Until the killed owner's lease runs out
    its reservation counts its receipt; then this process's admission
    reconciles it with that receipt, while the live process's heartbeat keeps
    its own reservation in flight."""

    vault, repository = _database(tmp_path)
    context = multiprocessing.get_context("spawn")
    release, results = context.Event(), context.Queue()
    lease, beat = 5.0, 0.25
    dead = context.Process(target=_child_owner,
                           args=(str(repository.sqlite_path), "0.30", 0.60, lease, beat, True, release, results))
    live = context.Process(target=_child_owner,
                           args=(str(repository.sqlite_path), "0.20", None, lease, beat, False, release, results))
    try:
        dead.start()
        dead_token, dead_handle = results.get(timeout=120)
        dead.join(timeout=60)
        assert dead.exitcode == -signal.SIGKILL
        live.start()
        live_token, live_handle = results.get(timeout=120)
        assert len({dead_token, live_token, SS.PROCESS}) == 3
        # Live or orphaned, the killed owner's request counts its receipt.
        assert SS.service_spend_today(vault, repository)["usd"] == pytest.approx(0.80)
        deadline = datetime.now(timezone.utc) + timedelta(seconds=120)
        while _row(repository, dead_handle)["lease_expires_at"] >= SS.utc_now_iso():
            assert datetime.now(timezone.utc) < deadline
            time.sleep(0.2)
        here = _process(vault, repository)
        assert _admits(here, 0.20)  # $0.60 + $0.20 + $0.20 fits $1; recovery ran in this admission
        row = _row(repository, dead_handle)
        assert (row["state"], row["resolved_by"], row["charged_usd"]) == ("settled", "recovery", pytest.approx(0.60))
        row = _row(repository, live_handle)
        assert row["state"] == "in_flight" and row["lease_expires_at"] > SS.utc_now_iso(), row
        assert not _admits(here, 0.01)
        release.set()
        live.join(timeout=60)
        assert live.exitcode == 0
    finally:
        for child in (dead, live):
            if child.is_alive():
                child.kill()
                child.join(timeout=10)
    row = _row(repository, live_handle)
    assert (row["state"], row["resolved_by"], row["process"]) == ("settled", "owner", live_token)
    assert SS.service_spend_today(vault, repository)["usd"] == pytest.approx(1.0)


# -- subscription requests are never refused ---------------------------------------------------------


def test_subscription_requests_are_never_refused_by_the_shared_daily_cap(tmp_path):
    vault, repository = _database(tmp_path, cap=0.0)
    envelope = _process(vault, repository)
    budget = SpendBudget(SpendCaps(max_calls=10), subscription=True)
    with spend_envelopes(envelope):
        for _ in range(3):
            with budget.request(SpendEstimate(calls=1, total_tokens=0, estimated_usd=0.0)) as charge:
                charge.note_estimated_only(total_tokens=1000, estimated_usd=0.01)
    with connect(repository.sqlite_path, read_only=True) as connection:
        assert connection.execute("SELECT COUNT(*) FROM source_service_spend").fetchone()[0] == 0
    assert envelope.report()["estimated_only"]["tokens"] == 3000


# -- F14: the upgrade counts each request recorded before reservation links once -------------------


def _at(midnight: datetime, seconds: float) -> str:
    return (midnight + timedelta(seconds=seconds)).isoformat()


def _stamp(midnight: datetime, seconds: int) -> str:
    return (midnight + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_an_upgrade_counts_every_request_and_reports_the_unprovable_overlap(tmp_path):
    """A vault at migration 194 has today's service receipts from before the
    ledger ($0.30), requests whose ledger rows were settled before receipts
    named their reservation (a $0.20 import whose receipt names nothing, and
    a $0.05 query embedding outside the service's receipt kinds), and a
    linked $0.10 request. The linked request counts once. The $0.20 import's
    receipt cannot be tied to its legacy row by anything durable (only its
    amount and a second-resolution window match), so both count: $0.85, with
    the receipt's $0.20 reported as possibly counted twice. (This test used to
    expect $0.65, which relied on matching the receipt to the row by amount;
    the Codex verify 20261013-125339-TBEVSp showed amount matching can
    suppress another request's receipt and undercount, so the rule is now
    conservative: never less than was spent.)"""

    before = tmp_path / "migrations_194"
    before.mkdir()
    for path in sorted(default_migrations_dir().glob("*.sql")):
        if int(path.name.split("_", 1)[0]) <= 194:
            (before / path.name).write_bytes(path.read_bytes())
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path, migrations_dir=before)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    midnight = datetime.fromisoformat(day + "T00:00:00+00:00")
    rows = [  # id, reserved, charged, created, updated
        ("ssp_import", 0.25, 0.20, 10, 12),
        ("ssp_embed", 0.06, 0.05, 20, 21),
        ("ssp_linked", 0.15, 0.10, 30, 32),
    ]
    with connect(sqlite_path) as connection:
        for handle, reserved, charged, created, updated in rows:
            connection.execute(
                "INSERT INTO source_service_spend (id, envelope, day, reserved_usd, charged_usd, state, process, "
                "created_at, updated_at) VALUES (?,?,?,?,?,'settled','proc_old',?,?)",
                (handle, SS.DAILY_ENVELOPE, day, reserved, charged, _stamp(midnight, created),
                 _stamp(midnight, updated)))
        receipts = [  # id, owner kind, cost, started (seconds after midnight), budget
            ("r_pre", "source_exercise_import", 0.30, 1, {"billing": "metered"}),
            ("r_import", "source_exercise_import", 0.20, 11.4, {"billing": "metered"}),
            ("r_embed", "source_query_embedding", 0.05, 20.5, {"billing": "metered"}),
            ("r_linked", "source_compare", 0.10, 30.7, {"billing": "metered", "envelope_reservations": ["ssp_linked"]}),
        ]
        for receipt_id, owner_kind, cost, started, budget in receipts:
            connection.execute(
                "INSERT INTO model_call_receipts(id, owner_kind, owner_id, purpose, provider, status, started_at, "
                "input_tokens, output_tokens, cost, budget_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (receipt_id, owner_kind, "x", "p", "openrouter", "completed", _at(midnight, started), 0, 0, cost,
                 json.dumps(budget)))
        connection.commit()
    vault = _vault(1.0)
    # Read before migrating, the same rule applies (a row no receipt names is legacy).
    from learnloop.db.stores.source_service import service_spend_accounting

    with connect(sqlite_path, read_only=True) as connection:
        unmigrated = service_spend_accounting(connection, envelope=SS.DAILY_ENVELOPE, day=day,
                                              since=day + "T00:00:00", now=SS.utc_now_iso(), price_per_million=PRICE)
    assert unmigrated["usd"] == pytest.approx(0.85), unmigrated
    assert unmigrated["legacy"]["uncertain_usd"] == pytest.approx(0.20)
    SS._DAILY.clear()
    repository = _upgraded(sqlite_path)  # the upgrade
    with connect(sqlite_path, read_only=True) as connection:
        legacy = dict(connection.execute("SELECT id, legacy FROM source_service_spend").fetchall())
    assert legacy == {"ssp_import": 1, "ssp_embed": 1, "ssp_linked": 0}
    spent = SS.service_spend_today(vault, repository)
    assert spent["usd"] == pytest.approx(0.85), spent
    assert spent["legacy"]["uncertain_usd"] == pytest.approx(0.20)
    envelope = _process(vault, repository)
    assert not _admits(envelope, 0.16)
    assert _admits(envelope, 0.15)


# -- Codex review of this stage, F1, and its verify (20261013-125339-TBEVSp): a legacy row covers no receipt ------


def _database_at_194(tmp_path):
    """A vault database at migration 194 (before migration 195 marked rows legacy)."""

    before = tmp_path / "migrations_194"
    before.mkdir()
    for path in sorted(default_migrations_dir().glob("*.sql")):
        if int(path.name.split("_", 1)[0]) <= 194:
            (before / path.name).write_bytes(path.read_bytes())
    sqlite_path = tmp_path / "state.sqlite"
    apply_migrations(sqlite_path, migrations_dir=before)
    return sqlite_path


def _today() -> tuple[str, datetime]:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return day, datetime.fromisoformat(day + "T00:00:00+00:00")


def _legacy_era(sqlite_path, rows, receipts) -> None:
    """Ledger rows written before receipts named their reservation (id, reserved,
    charged, created and updated as the ledger stamps them: to the second, ``Z``),
    and receipts (id, owner kind, cost, started, tokens, root budget)."""

    day, _midnight = _today()
    with connect(sqlite_path) as connection:
        for handle, reserved, charged, created, updated in rows:
            connection.execute(
                "INSERT INTO source_service_spend (id, envelope, day, reserved_usd, charged_usd, state, process, "
                "created_at, updated_at) VALUES (?,?,?,?,?,'settled','proc_old',?,?)",
                (handle, SS.DAILY_ENVELOPE, day, reserved, charged, created, updated))
        for receipt_id, owner_kind, cost, started, tokens, budget in receipts:
            connection.execute(
                "INSERT INTO model_call_receipts(id, owner_kind, owner_id, purpose, provider, status, started_at, "
                "input_tokens, output_tokens, cost, budget_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (receipt_id, owner_kind, "x", "p", "openrouter", "completed", started, tokens, 0, cost,
                 json.dumps(budget)))
        connection.commit()


def _upgraded(sqlite_path) -> Repository:
    """The upgrade of a database outside any vault: applied directly, as
    only the vault's coordinator may upgrade a vault's database."""

    from learnloop.db.migrate import apply_migrations

    apply_migrations(sqlite_path)
    return Repository.attach(sqlite_path)


def _unmigrated_and_upgraded(sqlite_path) -> tuple[dict, dict, Repository]:
    """The day's accounting read before migrating, then after the upgrade."""

    from learnloop.db.stores.source_service import service_spend_accounting

    day, _midnight = _today()
    with connect(sqlite_path, read_only=True) as connection:
        unmigrated = service_spend_accounting(connection, envelope=SS.DAILY_ENVELOPE, day=day,
                                              since=day + "T00:00:00", now=SS.utc_now_iso(), price_per_million=PRICE)
    SS._DAILY.clear()
    repository = _upgraded(sqlite_path)  # the upgrade
    return unmigrated, SS.service_spend_today(_vault(1.0), repository), repository


def test_a_same_second_pre_ledger_receipt_is_not_a_legacy_requests_own(tmp_path):
    """Codex's reproduction: a pre-ledger $0.80 receipt starts at …50.100; a
    $0.10 reservation is made later that second (stamped …50Z, to the second)
    and its own receipt starts at …50.600. Migration 195 marks the reservation
    legacy. Before the first fix both receipts fell in its lifetime window and
    were taken for its own: the day counted $0.10, not $0.90, and admitted
    $0.20 more under a $1 cap. The first fix then took the $0.10 receipt for
    the row's own by its amount; the verify's rule takes nothing by amount,
    so the row's charge and both receipts count ($1.00, never less than the
    $0.90 spent) and the two receipts in its window are reported uncertain."""

    sqlite_path = _database_at_194(tmp_path)
    _day, midnight = _today()
    _legacy_era(sqlite_path, rows=[("ssp_legacy", 0.15, 0.10, _stamp(midnight, 50), _stamp(midnight, 51))],
                receipts=[
                    ("r_pre", "source_exercise_import", 0.80, _at(midnight, 50.1), 0, {"billing": "metered"}),
                    ("r_own", "source_exercise_import", 0.10, _at(midnight, 50.6), 0, {"billing": "metered"}),
                ])
    unmigrated, spent, repository = _unmigrated_and_upgraded(sqlite_path)
    for accounting in (unmigrated, spent):
        assert accounting["usd"] == pytest.approx(1.00), accounting
        assert accounting["legacy"]["covered_requests"] == 0 and accounting["legacy"]["uncertain_requests"] == 2
        assert accounting["legacy"]["uncertain_usd"] == pytest.approx(0.90)
    envelope = _process(_vault(1.0), repository)
    assert not _admits(envelope, 0.01)  # the $1 cap is reached (conservatively)
    wider = _process(_vault(1.2), repository)
    assert not _admits(wider, 0.21)
    assert _admits(wider, 0.20)


def test_overlapping_legacy_requests_cover_no_receipt(tmp_path):
    """Two legacy requests overlap in time, and a receipt from another path
    starts while both are in flight. Before the first fix all three receipts
    were covered ($0.50, not the $0.65 spent); the first fix let each row
    cover the one receipt whose cost it settled at. That was amount matching,
    which the verify (20261013-125339-TBEVSp) showed can suppress another
    request's receipt, so no row covers any: both rows' charges and all
    three receipts count ($1.10, never less than was spent), and the three
    receipts in their windows are reported uncertain ($0.60)."""

    sqlite_path = _database_at_194(tmp_path)
    _day, midnight = _today()
    priced = {"billing": "metered", "practice_index": {"billing": "metered", "price_per_million": PRICE}}
    _legacy_era(sqlite_path, rows=[("ssp_first", 0.25, 0.20, _stamp(midnight, 10), _stamp(midnight, 15)),
                                   ("ssp_second", 0.35, 0.30, _stamp(midnight, 12), _stamp(midnight, 14))],
                receipts=[
                    ("r_first", "source_exercise_import", 0.20, _at(midnight, 11.2), 0, {"billing": "metered"}),
                    ("r_second", "source_compare", 0.25, _at(midnight, 12.5), 30_000, priced),
                    ("r_other", "source_solution_match", 0.15, _at(midnight, 13.1), 0, {"billing": "metered"}),
                ])
    unmigrated, spent, _repository = _unmigrated_and_upgraded(sqlite_path)
    for accounting in (unmigrated, spent):
        assert accounting["usd"] == pytest.approx(1.10), accounting
        legacy = accounting["legacy"]
        assert (legacy["correlated"], legacy["covered_requests"], legacy["uncertain_requests"]) == (0, 0, 3)
        assert legacy["uncertain_usd"] == pytest.approx(0.60)


def test_an_ambiguous_legacy_request_counts_conservatively_and_says_so(tmp_path):
    """Two receipts of the same cost start during one legacy request: either
    could be its own, or neither. Nothing is covered (the day may count up to
    $0.20 twice, never less than it spent), and the report says how much is
    uncertain."""

    sqlite_path = _database_at_194(tmp_path)
    _day, midnight = _today()
    _legacy_era(sqlite_path, rows=[("ssp_legacy", 0.15, 0.10, _stamp(midnight, 40), _stamp(midnight, 45))],
                receipts=[
                    ("r_a", "source_exercise_import", 0.10, _at(midnight, 41), 0, {"billing": "metered"}),
                    ("r_b", "source_compare", 0.10, _at(midnight, 43), 0, {"billing": "metered"}),
                ])
    unmigrated, spent, _repository = _unmigrated_and_upgraded(sqlite_path)
    for accounting in (unmigrated, spent):
        assert accounting["usd"] == pytest.approx(0.30), accounting
        legacy = accounting["legacy"]
        assert (legacy["correlated"], legacy["uncorrelated"], legacy["covered_requests"]) == (0, 1, 0)
        assert legacy["uncertain_requests"] == 2 and legacy["uncertain_usd"] == pytest.approx(0.20)


def test_a_legacy_row_never_suppresses_a_receipt_it_only_matches_by_amount(tmp_path):
    """Codex verify (20261013-125339-TBEVSp): a legacy embedding reservation
    settled at its $0.10 estimate; its own receipt (a practice_query_embedding,
    outside the service's receipt kinds) reports $0.09; an unrelated service
    receipt in the same legacy window reports $0.10. Before the fix that
    receipt was the row's unique dollar-matching candidate and was suppressed:
    the day counted $0.10, not $0.19, with nothing uncertain, and admitted
    another $0.85 under a $1 cap ($1.04 spent). A legacy row has no durable
    identity link to any receipt, so it suppresses none: both count ($0.20,
    never less than was spent), and the overlap is reported as uncertain."""

    sqlite_path = _database_at_194(tmp_path)
    _day, midnight = _today()
    _legacy_era(sqlite_path, rows=[("ssp_embed", 0.10, 0.10, _stamp(midnight, 60), _stamp(midnight, 61))],
                receipts=[
                    ("r_own", "practice_query_embedding", 0.09, _at(midnight, 60.2), 0, {"billing": "metered"}),
                    ("r_other", "source_compare", 0.10, _at(midnight, 60.7), 0, {"billing": "metered"}),
                ])
    unmigrated, spent, repository = _unmigrated_and_upgraded(sqlite_path)
    for accounting in (unmigrated, spent):
        assert accounting["usd"] == pytest.approx(0.20), accounting
        assert accounting["usd"] >= 0.19
        legacy = accounting["legacy"]
        assert (legacy["correlated"], legacy["covered_requests"]) == (0, 0)
        assert legacy["uncertain_requests"] == 1 and legacy["uncertain_usd"] == pytest.approx(0.10)
    envelope = _process(_vault(1.0), repository)
    assert not _admits(envelope, 0.85)
    assert _admits(envelope, 0.80)


# -- Codex review of this stage, F2: a reported cost is never repriced ---------------------------------


def _embedding_request(repository, envelope, *, cost: float | None, tokens: int, recorded_price: float) -> None:
    """A query embedding as ``embed_queries`` sends it: the root receipt records
    the request's own rate, and the reservation settles without a reconciled
    cost (the embedding path does not reconcile)."""

    def observe(action: str, event: dict) -> None:
        if action == "start" and event.get("parent_call_id") is None:
            declared = json.loads(event.get("budget_json") or "{}")
            declared["practice_index"] = {"task": "embedding", "billing": "metered",
                                          "price_per_million": recorded_price}
            event = {**event, "budget_json": json.dumps(declared)}
        repository.record_model_event(action, event, owner_kind="practice_query_embedding", owner_id="q")

    client = SimpleNamespace(provider_name="openrouter_embedding", model="embedding-fake-model")
    budget = SpendBudget(SpendCaps(max_calls=10, max_estimated_usd=10.0))
    estimate = SpendEstimate(calls=1, total_tokens=tokens, estimated_usd=tokens * recorded_price / 1_000_000)
    with observe_model_calls(observe), spend_envelopes(envelope), budget.request(estimate):
        with model_call(client, purpose="QueryEmbedding") as metadata:
            metadata.update(cost=cost, input_tokens=tokens, output_tokens=0)


def test_a_settled_embedding_counts_its_reported_cost_not_its_tokens_at_the_service_rate(tmp_path):
    """Codex's reproduction: a settled embedding reports 10,000 tokens and
    $0.001. Before the fix the day took the larger of that and the tokens at
    the service's generic $10 per million ($0.10), and refused a $0.95 request
    under a $1 cap."""

    vault, repository = _database(tmp_path)
    _embedding_request(repository, _process(vault, repository), cost=0.001, tokens=10_000, recorded_price=0.02)
    spent = SS.service_spend_today(vault, repository)
    assert spent["usd"] == pytest.approx(0.001), spent
    assert spent["pricing"]["reported"] == 1
    assert _admits(_process(vault, repository), 0.95)


def test_a_receipt_without_a_cost_is_priced_at_its_requests_recorded_rate(tmp_path):
    """No reported cost: a request's tokens are priced at the rate it recorded
    when it was admitted (here an embedding's $0.02 per million), not at the
    service's generic rate; only a receipt that recorded none falls back to
    the service's rate, and the report says which basis each used. A reported
    cost alongside nonzero tokens counts as reported."""

    vault, repository = _database(tmp_path)
    _embedding_request(repository, _process(vault, repository), cost=None, tokens=10_000, recorded_price=0.02)
    _receipt(repository, "r_reported", cost=0.004, owner_kind="source_compare")
    _receipt(repository, "r_recorded", cost=None, owner_kind="source_compare")
    _receipt(repository, "r_fallback", cost=None, owner_kind="source_compare")
    with connect(repository.sqlite_path) as connection:
        connection.execute("UPDATE model_call_receipts SET input_tokens=1000 WHERE id IN ('r_reported', 'r_recorded', "
                           "'r_fallback')")
        connection.execute("UPDATE model_call_receipts SET budget_json=? WHERE id='r_recorded'",
                           (json.dumps({"billing": "metered", "pf": {"price_per_million": 2.0}}),))
        connection.commit()
    spent = SS.service_spend_today(vault, repository)
    expected = 10_000 * 0.02 / 1e6 + 0.004 + 1000 * 2.0 / 1e6 + 1000 * PRICE / 1e6
    assert spent["usd"] == pytest.approx(expected), spent
    assert spent["pricing"] == {"reported": 1, "recorded_rate": 2, "owner_rate": 1, "unpriced": 0}
    # The service's rate changing later reprices only the request that recorded none.
    cheaper = _vault(1.0)
    cheaper.config.source_service.llm_price_per_million = 1.0
    assert SS.service_spend_today(cheaper, repository)["usd"] == pytest.approx(expected - 1000 * (PRICE - 1.0) / 1e6)


def test_spend_since_counts_a_reported_cost_alongside_tokens(tmp_path):
    """A batch's receipts-only report uses the same rule."""

    from learnloop.db.stores.source_service import spend_since

    _vault_, repository = _database(tmp_path)
    _receipt(repository, "r_cheap", cost=0.001, owner_kind="source_compare")
    with connect(repository.sqlite_path) as connection:
        connection.execute("UPDATE model_call_receipts SET input_tokens=10000 WHERE id='r_cheap'")
        connection.commit()
    with connect(repository.sqlite_path, read_only=True) as connection:
        assert spend_since(connection, "2000-01-01", price_per_million=PRICE)["usd"] == pytest.approx(0.001)


# -- the shared envelope's report carries the accounting --------------------------------------------


def test_the_shared_envelopes_report_carries_the_accounting(tmp_path):
    vault, repository = _database(tmp_path)
    worker = _process(vault, repository)
    live = worker.reserve(Decimal("0.20"))
    dead = worker.reserve(Decimal("0.30"))
    _receipt(repository, "r_dead", cost=0.40, reservation=dead)
    _dies(repository, dead)
    _owner_terminal(repository, dead)
    report = _process(vault, repository).report()
    assert report["metered_usd"] == pytest.approx(0.60)
    accounting = report["accounting"]
    assert accounting["usd"] == pytest.approx(0.60) and accounting["reservations_usd"] == pytest.approx(0.60)
    assert accounting["unlinked_receipts_usd"] == 0
    assert accounting["reservations"]["in_flight"] == 1 and accounting["reservations"]["orphaned"] == 1
    assert accounting["recovery"] == [{"id": dead, "action": "reconcile", "charged_usd": pytest.approx(0.40)}]
    assert {"legacy", "pricing", "metered", "estimated_only"} <= set(accounting)
    worker.settle(live, Decimal("0.20"))
