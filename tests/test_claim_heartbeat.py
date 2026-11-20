"""The shared claim heartbeat owns and joins its renewal thread."""
from contextlib import nullcontext
import threading
from types import SimpleNamespace

import pytest

from learnloop.db.stores import judgment_claims as claims


@pytest.mark.parametrize("lost", [False, True])
@pytest.mark.parametrize("body_error", [False, True])
def test_heartbeat_retries_then_stops_and_joins(monkeypatch, lost, body_error):
    renewed = threading.Event()
    calls = []
    claim = SimpleNamespace(key="question", owner="worker", epoch=3)
    connection = object()
    repository = SimpleNamespace(atomic=nullcontext, connection=lambda: connection)
    monkeypatch.setattr(claims, "utc_now_iso", lambda: "2001-01-01T00:00:00Z")

    def renew(actual, **kwargs):
        assert actual is connection
        calls.append((threading.current_thread(), kwargs))
        if len(calls) == 1:
            raise RuntimeError("transient renewal failure")
        renewed.set()
        return not lost

    monkeypatch.setattr(claims, "renew_claim", renew)
    with pytest.raises(ValueError, match="body failed") if body_error else nullcontext():
        with claims.claim_heartbeat(repository, claim, lease_seconds=47, interval=0.001):
            assert renewed.wait(10)
            if body_error:
                raise ValueError("body failed")
    assert len(calls) >= 2
    for thread, kwargs in calls:
        assert not thread.is_alive()
        assert kwargs == dict(claim_key="question", owner="worker", epoch=3,
                              now="2001-01-01T00:00:00Z", lease_seconds=47)
    if lost:
        assert len(calls) == 2


def test_no_claim_starts_no_thread(monkeypatch):
    def start(_thread):
        pytest.fail("a missing claim started a thread")

    monkeypatch.setattr(threading.Thread, "start", start)
    with claims.claim_heartbeat(None, None, lease_seconds=47, interval=1):
        pass
