"""Mobile v2 stage V1: ``GET /api/v1/meta`` and the round-trip measurements (spec §4.5, §5.2).

The meta endpoint is what a stale cached app compares its build against; ``Server-Timing`` is on
every ``/rpc`` reply, and the phone's own round trip comes back on its next request into the
request log, where ``learnloop-mobile report`` reads p50/p95 per method.
"""

from __future__ import annotations

import re

import pytest

pytest.importorskip("starlette")
from starlette.testclient import TestClient

from learnloop.capture import log_request, mobile_report
from learnloop.capture.report import round_trips
from learnloop.db.migrate import discover_migrations
from learnloop_mobile.allowlist import ALLOWLIST, API_VERSION, allowlist_digest
from learnloop_mobile.host import CLIENT_TIMING_HEADER, HOST_VERSION, client_timing, create_app, server_timing

from tests.mobile_host_helpers import (
    HOSTNAME, CountingGrader, Phone, bearer, config_for, identity, install_grader, pair, rows, seeded_vault,
)

_TIMING = re.compile(r"(?:(?:queue|handler|job);dur=[0-9.]+, )*total;dur=[0-9.]+")


@pytest.fixture
def world(tmp_path, monkeypatch):
    paths, repository = seeded_vault(tmp_path / "vault")
    install_grader(monkeypatch, CountingGrader())
    device = pair(repository)
    app = create_app(config_for(paths.root))
    with TestClient(app, base_url=f"https://{HOSTNAME}") as client:
        yield Phone(client, device), app.state.host, repository


# -- GET /api/v1/meta ------------------------------------------------------------


def test_meta_names_the_allowlist_the_host_enforces(world):
    phone, host, _repository = world
    response = phone.get("/api/v1/meta")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "host_version": HOST_VERSION, "api_version": API_VERSION, "allowlist_digest": allowlist_digest(),
        "schema_version": max(migration.version for migration in discover_migrations()),
        # Mobile v2 V2: whether Today is the shared plan (the host's kill switch, mobile.toml).
        "phone_plan": True,
        # Mobile v2 V3: whether the phone answers probes (the host's kill switch, mobile.toml).
        "phone_probes": True,
        # Mobile v2 V4: whether the phone's Reader is on (the host's kill switch, mobile.toml).
        "phone_reader": True,
    }
    assert host.schema_version == response.json()["schema_version"]


def test_meta_needs_an_app_token(world):
    phone, _host, repository = world
    client = phone.client
    assert client.get("/api/v1/meta").status_code == 403
    assert client.get("/api/v1/meta", headers=identity()).status_code == 401
    assert client.get("/api/v1/meta", headers=bearer(pair(repository, scope="capture"))).status_code == 403


def test_meta_is_not_logged(world):
    phone, _host, repository = world
    phone.get("/api/v1/meta")
    assert rows(repository, "SELECT endpoint FROM mobile_request_log") == []


def test_the_digest_moves_with_a_method_its_kind_or_its_retry_policy(monkeypatch):
    import learnloop_mobile.allowlist as allowlist
    from dataclasses import replace
    from types import MappingProxyType

    before = allowlist_digest()
    entries = dict(ALLOWLIST)
    entries["get_session"] = replace(entries["get_session"], retry_safe=False)
    monkeypatch.setattr(allowlist, "ALLOWLIST", MappingProxyType(entries))
    assert allowlist.allowlist_digest() != before
    entries.pop("get_session")
    monkeypatch.setattr(allowlist, "ALLOWLIST", MappingProxyType(entries))
    assert allowlist.allowlist_digest() != before
    monkeypatch.setattr(allowlist, "ALLOWLIST", ALLOWLIST)
    assert allowlist.allowlist_digest() == before


# -- Server-Timing ----------------------------------------------------------------


def test_every_rpc_reply_carries_server_timing(world):
    phone, _host, _repository = world
    session = phone.start()
    short = phone.post("get_session", {"sessionId": session["sessionId"]})
    assert short.status_code == 200
    header = short.headers["server-timing"]
    assert _TIMING.fullmatch(header), header
    assert header.startswith("queue;dur=") and ", handler;dur=" in header
    # Refusals carry it too: the allowlist, the constraints, the model, an unknown body.
    for response in (
        phone.post("not_a_method"),
        phone.post("submit_attempt", {"selfGrade": 1, "submissionId": "k"}, request_id="k"),
        phone.post("get_session", {"nope": 1}),
        phone.client.post("/rpc", content=b"[]", headers={**phone.headers, "Content-Type": "application/json"}),
        phone.client.post("/rpc", json={"method": "get_session"}, headers=identity()),
    ):
        assert response.status_code >= 400
        assert _TIMING.fullmatch(response.headers["server-timing"]), response.headers["server-timing"]


def test_a_long_method_reports_its_wait(world):
    phone, _host, _repository = world
    session = phone.start()
    item = phone.queue_items(session["sessionId"])[0]["practiceItemId"]
    phone.rpc("get_practice_item", {"practiceItemId": item, "sessionId": session["sessionId"]})
    response = phone.submit(session["sessionId"], "sub_timing", item=item)
    assert response.status_code in (200, 202)
    assert "job;dur=" in response.headers["server-timing"]


def test_other_endpoints_carry_no_server_timing(world):
    phone, _host, _repository = world
    assert "server-timing" not in phone.get("/api/v1/queue-revision").headers
    assert "server-timing" not in phone.get("/api/v1/meta").headers


def test_server_timing_formats_what_was_measured():
    assert server_timing(None, 0.0125) == "total;dur=12.5"
    assert server_timing({"submitted": 1.0, "started": 1.002, "finished": 1.010}, 0.02) == (
        "queue;dur=2.0, handler;dur=8.0, total;dur=20.0"
    )
    assert server_timing({"job_from": 1.0, "job_to": 16.0}, 15.1) == "job;dur=15000.0, total;dur=15100.0"


# -- the phone's round trip ---------------------------------------------------------


@pytest.mark.parametrize("value,expected", [
    ("get_session;status=200;dur=84.5;host=12.25", ("get_session", 200, 84.5, 12.25)),
    ("get_session;status=503;dur=40", ("get_session", 503, 40.0, None)),
    ("get_session;status=200;dur=10;host=20", ("get_session", 200, 10.0, None)),
    ("run_cli_command;status=200;dur=10", None),
    ("get_session;status=200;dur=-1", None),
    ("get_session;status=200;dur=1e9", None),
    ("get_session;status=99;dur=1", None),
    ("get_session;status=200;dur=1;extra=2", None),
    ("", None),
    (None, None),
])
def test_a_timing_header_parses_only_an_allowlisted_sample(value, expected):
    assert client_timing(value) == expected


def test_the_phones_round_trip_is_logged_on_its_next_request(world):
    phone, _host, repository = world
    session = phone.start()
    headers = {**phone.headers, CLIENT_TIMING_HEADER: "start_session;status=200;dur=140.5;host=40.5"}
    response = phone.client.post("/rpc", json={"method": "get_session", "params": {"sessionId": session["sessionId"]}},
                                 headers=headers)
    assert response.status_code == 200
    logged = rows(repository, "SELECT endpoint, status, duration_ms FROM mobile_request_log ORDER BY rowid")
    assert [row["endpoint"] for row in logged] == [
        "rpc:start_session", "rpc:get_session", "client:start_session", "network:start_session",
    ]
    assert logged[2]["duration_ms"] == 140.5 and logged[2]["status"] == 200
    assert logged[3]["duration_ms"] == 100.0


def test_a_bad_timing_header_costs_the_request_nothing(world):
    phone, _host, repository = world
    session = phone.start()
    for value in ("drop table;status=200;dur=1", "run_cli_command;status=200;dur=1", "x" * 300):
        headers = {**phone.headers, CLIENT_TIMING_HEADER: value}
        response = phone.client.post(
            "/rpc", json={"method": "get_session", "params": {"sessionId": session["sessionId"]}}, headers=headers)
        assert response.status_code == 200
    endpoints = {row["endpoint"] for row in rows(repository, "SELECT endpoint FROM mobile_request_log")}
    assert endpoints == {"rpc:start_session", "rpc:get_session"}


def test_an_unauthenticated_request_logs_no_timing(world):
    phone, _host, repository = world
    phone.client.post("/rpc", json={"method": "get_session", "params": {}},
                      headers={**identity(), CLIENT_TIMING_HEADER: "get_session;status=200;dur=1"})
    assert rows(repository, "SELECT endpoint FROM mobile_request_log") == []


# -- the report -----------------------------------------------------------------------


def test_round_trips_are_p50_and_p95_per_method_with_the_network_share():
    samples = (
        [{"endpoint": "rpc:get_session", "duration_ms": value} for value in (10, 20, 30, 40)]
        + [{"endpoint": "client:get_session", "duration_ms": value} for value in (100, 200, 300, 400)]
        + [{"endpoint": "network:get_session", "duration_ms": value} for value in (90, 180, 270, 360)]
        + [{"endpoint": "rpc:submit_attempt", "duration_ms": 5000}, {"endpoint": "/pair", "duration_ms": 3}]
    )
    table = round_trips(samples, short_methods=frozenset({"get_session"}))
    session = table["methods"]["get_session"]
    assert session["host_ms"] == {"count": 4, "p50": 20.0, "p95": 40.0}
    assert session["round_trip_ms"] == {"count": 4, "p50": 200.0, "p95": 400.0}
    assert session["network_ms"]["p50"] == 180.0
    assert session["network_share"] == 0.9
    assert session["within_short_read_budget"] is True
    submit = table["methods"]["submit_attempt"]
    assert submit["round_trip_ms"] == {"count": 0, "p50": None, "p95": None}
    assert submit["network_share"] is None and "within_short_read_budget" not in submit
    assert set(table["methods"]) == {"get_session", "submit_attempt"}


def test_the_report_carries_the_round_trips(world):
    phone, _host, repository = world
    log_request(repository, endpoint="client:get_session", status=200, duration_ms=1500.0)
    report = mobile_report(repository, short_methods=frozenset({"get_session"}))
    session = report["round_trips"]["methods"]["get_session"]
    assert session["round_trip_ms"]["p50"] == 1500.0
    assert session["within_short_read_budget"] is False
