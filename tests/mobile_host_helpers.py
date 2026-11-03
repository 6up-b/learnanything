"""The phone host under test: a real ASGI app, a fake identity-header injector, a fake grader.

No test calls Tailscale (spec §11). The identity header is what Serve would add; the
bearer token comes from the real pairing exchange.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import threading
import time
from typing import Any

import pytest

from learnloop import capture
from learnloop.db.repositories import Repository
from learnloop_mobile.config import MobileConfig
from tests.helpers import add_followup_item, create_basic_vault, seed_due_item
from tests.split_live_helpers import ReadyRuntime

ITEM = "pi_svd_define_001"
SECOND_ITEM = "pi_svd_define_002"
HOSTNAME = "desktop.tail.ts.net"
OWNER = "owner@example.com"


class CountingGrader:
    """The stuck fake, counting provider calls; ``gate`` holds a grade until a test releases it."""

    def __new__(cls, *args, **kwargs):
        from tests.test_stuck_prompt import StuckFake

        class _Counting(StuckFake):
            def __init__(self) -> None:
                super().__init__()
                self.grades = 0
                self.gate: threading.Event | None = None
                self.started = threading.Event()

            def _hold(self) -> None:
                self.grades += 1
                self.started.set()
                if self.gate is not None:
                    assert self.gate.wait(30), "the test never released the grade"

            def _blind_grading(self, request, context):
                self._hold()
                return super()._blind_grading(request, context)

            def _grading(self, request, context):
                self._hold()
                return super()._grading(request, context)

        return _Counting()


class DownRuntime(ReadyRuntime):
    ready = False


def install_grader(monkeypatch, grader) -> None:
    """Every grading route in the host's process answers with this fake."""

    import learnloop_sidecar.handlers.practice as practice

    monkeypatch.setattr(practice, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), grader))


def install_grading_outage(monkeypatch) -> None:
    import learnloop_sidecar.handlers.practice as practice

    monkeypatch.setattr(practice, "ready_grading_provider", lambda vault, override=None: ("fake", DownRuntime(), None))


def seeded_vault(root: Path, *, fresh: bool = False):
    paths = create_basic_vault(root, fresh=fresh)
    repository = seed_due_item(paths)
    add_followup_item(paths.root, SECOND_ITEM)
    repository.upsert_practice_item_state(
        SECOND_ITEM, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z", active=True,
    )
    return paths, repository


def pair(repository: Repository, *, scope: str = "app", label: str = "Phone") -> dict[str, Any]:
    pending = capture.create_pairing(repository, label=label, scope=scope)
    return capture.exchange_pairing(repository, secret=pending["secret"], device_label=label)


def config_for(root: Path) -> MobileConfig:
    return MobileConfig(enabled=True, vault=root, hostname=HOSTNAME, owner_login=OWNER)


def identity() -> dict[str, str]:
    return {"Tailscale-User-Login": OWNER}


def bearer(device: dict[str, Any]) -> dict[str, str]:
    return {**identity(), "Authorization": f"Bearer {device['token']}"}


@dataclass
class Phone:
    """One paired device talking to the host."""

    client: Any
    device: dict[str, Any]

    @property
    def headers(self) -> dict[str, str]:
        return bearer(self.device)

    def post(self, method: str, params: dict | None = None, *, request_id: str | None = None):
        body: dict[str, Any] = {"method": method, "params": params or {}}
        if request_id is not None:
            body["request_id"] = request_id
        return self.client.post("/rpc", json=body, headers=self.headers)

    def rpc(self, method: str, params: dict | None = None, *, request_id: str | None = None) -> Any:
        response = self.post(method, params, request_id=request_id)
        assert response.status_code == 200, (method, response.status_code, response.text)
        assert response.json()["ok"] is True
        return response.json()["result"]

    def error(self, method: str, params: dict | None = None, *, request_id: str | None = None) -> tuple[int, dict]:
        response = self.post(method, params, request_id=request_id)
        assert response.status_code >= 400, (method, response.status_code, response.text)
        body = response.json()
        assert body["ok"] is False
        return response.status_code, body["error"]

    def get(self, path: str):
        return self.client.get(path, headers=self.headers)

    def start(self, **params) -> dict[str, Any]:
        return self.rpc("start_session", {"availableMinutes": 25, **params})

    def queue_items(self, session_id: str | None) -> list[dict[str, Any]]:
        queue = self.rpc("get_today_queue", {"sessionId": session_id})
        return [item for section in queue["sections"] for item in section["items"]]

    def submit(self, session_id: str, submission_id: str, *, item: str = ITEM, **params):
        return self.post("submit_attempt", {
            "sessionId": session_id, "practiceItemId": item, "answerMd": "an answer",
            "attemptType": "independent_attempt", "submissionId": submission_id, **params,
        }, request_id=submission_id)


def poll_job(phone: Phone, job_id: str, *, timeout: float = 30.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = phone.get(f"/api/v1/jobs/{job_id}").json()
        if body["state"] in ("completed", "failed", "recorded"):
            return body
        time.sleep(0.02)
    pytest.fail(f"job {job_id} never finished")


def rows(repository: Repository, sql: str, *args) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(sql, args).fetchall()]
