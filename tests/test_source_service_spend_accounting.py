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
import threading
from types import SimpleNamespace

import pytest

from learnloop.ai.execution import model_call, record_model_calls
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
    """Eight processes race for $0.125 each under a $1 cap while a dead
    worker's $0.50 receipt is unreconciled ($0.125 reserved). Exactly four
    fit; before the fix seven were admitted ($1.375 spent)."""

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


def test_an_upgrade_counts_each_request_recorded_before_reservation_links_once(tmp_path):
    """A vault at migration 191 has today's service receipts from before the
    ledger ($0.30), requests whose ledger rows were settled before receipts
    named their reservation (a $0.20 import whose receipt names nothing, and
    a $0.05 query embedding outside the service's receipt kinds), and a
    linked $0.10 request. After the upgrade the day's total is $0.65: before
    the fix the $0.20 import was counted by its row and again by its receipt
    ($0.85)."""

    before = tmp_path / "migrations_191"
    before.mkdir()
    for path in sorted(default_migrations_dir().glob("*.sql")):
        if int(path.name.split("_", 1)[0]) <= 191:
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
    assert unmigrated["usd"] == pytest.approx(0.65), unmigrated
    SS._DAILY.clear()
    repository = Repository(sqlite_path)  # the upgrade
    with connect(sqlite_path, read_only=True) as connection:
        legacy = dict(connection.execute("SELECT id, legacy FROM source_service_spend").fetchall())
    assert legacy == {"ssp_import": 1, "ssp_embed": 1, "ssp_linked": 0}
    spent = SS.service_spend_today(vault, repository)
    assert spent["usd"] == pytest.approx(0.65), spent
    envelope = _process(vault, repository)
    assert not _admits(envelope, 0.36)
    assert _admits(envelope, 0.35)
