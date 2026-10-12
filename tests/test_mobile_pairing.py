from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import sqlite3

import pytest

from learnloop.capture import (
    CaptureError, authenticate_device, create_pairing, exchange_pairing,
    list_devices, log_request, prune_request_log, revoke_device, touch_device,
)
from learnloop.db.repositories import Repository
from tests.helpers import NOW, create_basic_vault


@pytest.fixture
def repo(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return Repository.attach(paths.sqlite_path)


def test_pairing_hash_only_scopes_revoke(repo):
    pairing = create_pairing(repo, label="phone", scope="capture", now=NOW)
    with repo.connection() as conn:
        row = dict(conn.execute("SELECT * FROM mobile_pairings").fetchone())
    assert pairing["secret"] not in row.values()
    assert pairing["code"] not in row.values()
    device = exchange_pairing(repo, code=pairing["code"], now=NOW)
    assert authenticate_device(repo, device["token"], now=NOW)["scope"] == "capture"
    with pytest.raises(CaptureError) as denied:
        authenticate_device(repo, device["token"], scope="app", now=NOW)
    assert denied.value.status == 403
    with repo.connection() as conn:
        assert device["token"] not in dict(conn.execute("SELECT * FROM mobile_devices").fetchone()).values()
    revoke_device(repo, device["device_id"], now=NOW)
    with pytest.raises(CaptureError, match="valid device"):
        authenticate_device(repo, device["token"], now=NOW)
    assert "token_hash" not in list_devices(repo, now=NOW)[0]


@pytest.mark.durability
def test_pairing_concurrent_exchange_one_winner(repo):
    pairing = create_pairing(repo, scope="app", now=NOW)

    def exchange(_):
        try:
            return exchange_pairing(Repository.attach(repo.sqlite_path), secret=pairing["secret"], now=NOW)
        except CaptureError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(exchange, range(8)))
    winners = [r for r in results if isinstance(r, dict)]
    assert len(winners) == 1
    assert authenticate_device(repo, winners[0]["token"], scope="app", now=NOW)
    assert len(list_devices(repo, now=NOW)) == 1


def test_failed_attempt_limits_survive_reattach_and_time(repo):
    pairing = create_pairing(repo, now=NOW)
    for _ in range(5):
        with pytest.raises(CaptureError):
            exchange_pairing(Repository.attach(repo.sqlite_path), code="BAD", now=NOW)
    with pytest.raises(CaptureError):
        exchange_pairing(repo, secret=pairing["secret"], now=NOW)
    for _ in range(14):
        with pytest.raises(CaptureError):
            exchange_pairing(repo, code="BAD", now=NOW)
    with pytest.raises(CaptureError) as locked:
        exchange_pairing(repo, code="BAD", now=NOW + timedelta(hours=1))
    assert locked.value.code == "pairing_locked"
    new_pair = create_pairing(repo, now=NOW + timedelta(hours=1))
    assert exchange_pairing(repo, secret=new_pair["secret"], now=NOW + timedelta(hours=1))


def test_expiry_and_unclaimed_device_revocation(repo):
    pairing = create_pairing(repo, now=NOW)
    with pytest.raises(CaptureError):
        exchange_pairing(repo, code=pairing["code"], now=NOW + timedelta(minutes=5))
    pairing = create_pairing(repo, now=NOW)
    device = exchange_pairing(repo, secret=pairing["secret"], now=NOW)
    with pytest.raises(CaptureError):
        authenticate_device(repo, device["token"], now=NOW + timedelta(hours=24))
    assert list_devices(repo, now=NOW + timedelta(hours=24))[0]["revoked_at"]


def test_exchange_failure_rolls_back_consumption(repo):
    pairing = create_pairing(repo, now=NOW)
    with repo.connection() as conn:
        conn.execute("""CREATE TRIGGER reject_device BEFORE INSERT ON mobile_devices
                        BEGIN SELECT RAISE(ABORT,'injected'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        exchange_pairing(repo, secret=pairing["secret"], now=NOW)
    with repo.connection() as conn:
        assert conn.execute("SELECT consumed_at FROM mobile_pairings").fetchone()[0] is None
        conn.execute("DROP TRIGGER reject_device")
    assert exchange_pairing(repo, secret=pairing["secret"], now=NOW)


def test_log_redaction_and_pruning(repo):
    log_request(repo, endpoint="/pair", status=200, duration_ms=1, now=NOW)
    log_request(repo, endpoint="/pair#s=SECRET", status=200, duration_ms=1, now=NOW)
    log_request(repo, endpoint="/api/v1/status", status=200, duration_ms=1, now=NOW)
    with repo.connection() as conn:
        assert conn.execute("SELECT count(*) FROM mobile_request_log").fetchone()[0] == 1
    assert prune_request_log(repo, now=NOW + timedelta(days=91)) == 1


def test_authentication_and_device_listing_are_read_only(repo):
    pairing = create_pairing(repo, now=NOW)
    device = exchange_pairing(repo, secret=pairing["secret"], tailscale_login="owner", now=NOW)
    reader = Repository.attach(repo.sqlite_path, read_only=True)
    assert authenticate_device(reader, device["token"], now=NOW)
    assert list_devices(reader, now=NOW)
    with pytest.raises(CaptureError):
        authenticate_device(reader, "bad", now=NOW)
    touch_device(repo, device["device_id"], now=NOW)
    with repo.connection() as conn:
        row = conn.execute("SELECT * FROM mobile_devices").fetchone()
        assert row["tailscale_login"] == "owner"
        assert row["claimed_at"] == NOW.isoformat()
        before = row["last_seen_at"]
    touch_device(repo, device["device_id"], now=NOW + timedelta(seconds=30))
    with repo.connection() as conn:
        assert conn.execute("SELECT last_seen_at FROM mobile_devices").fetchone()[0] == before
    assert authenticate_device(reader, device["token"], now=NOW + timedelta(hours=25))
