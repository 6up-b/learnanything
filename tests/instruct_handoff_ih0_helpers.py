"""What other test files use from ``tests/test_instruct_handoff_ih0.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime
import sqlite3
import time
from typing import Any

import pytest
from starlette.testclient import TestClient

import learnloop.clock as clock_module
from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION as ALGORITHM_VERSION
from learnloop.daily_plan import router_runtime
from learnloop.db.repositories import Repository
from learnloop.db.stores import router_objective as store
from learnloop_mobile.host import create_app

from tests.helpers import append_config_toml, create_daily_plan_vault
from tests.mobile_host_helpers import HOSTNAME, CountingGrader, Phone, config_for, install_grader, pair
from tests.router_model_fakes import FakeDecider, FakeLLM, block_drawing_seed, fake_runtime
from tests.ro4_objective_serving_helpers import policy_answer


DAY = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
ITEMS = {"lo_a": [("pi_a1", 2.0), ("pi_a2", 2.0)], "lo_b": [("pi_b1", 2.0), ("pi_b2", 2.0)],
         "lo_c": [("pi_c1", 2.0), ("pi_c2", 2.0)]}
#: What else a call leaves behind, neither of them a decision and neither written by its read-only path: the job's model
#: receipts (on its own connection, as every model call's), and the host's request log.
JOB_AND_HOST_TABLES = frozenset({"model_call_receipts", "mobile_request_log"})
DECISION_TABLES = ("router_decisions", "attention_blocks", "attention_block_events", "plan_presentations",
                   "router_objective_traces", "router_decision_payloads", "daily_plans")


class World:
    def __init__(self, phone: Phone, host: Any, repository: Repository, paths: Any, runtime: Any, llm: FakeLLM):
        self.phone, self.host, self.repository, self.paths = phone, host, repository, paths
        self.runtime, self.llm = runtime, llm
        self.session = phone.rpc("start_session", {"availableMinutes": 30})["sessionId"]
        self._keys = 0

    def key(self, prefix: str) -> str:
        self._keys += 1
        return f"{prefix}_{self._keys}"

    def next(self) -> dict[str, Any]:
        return self.phone.rpc("next_plan_item", {"sessionId": self.session, "serve": True}, request_id=self.key("next"))

    def answer(self, step: dict[str, Any]) -> None:
        key = self.key("dk")
        response = self.phone.post("submit_dont_know", {
            "sessionId": self.session, "practiceItemId": step["practiceItemId"], "submissionId": key, "hintsUsed": 0,
            "planPresentationId": step.get("presentationId"),
        }, request_id=key)
        assert response.status_code == 200, response.text

    def prefetch(self) -> dict[str, Any]:
        return self.phone.rpc("plan_prefetch", {"sessionId": self.session})

    def wait_for_job(self) -> None:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if all(entry.complete for entry in self.runtime._entries.values()):
                return
            time.sleep(0.01)
        raise AssertionError("the router's job did not finish")

    def answer_to_boundary(self, step: dict[str, Any]) -> dict[str, Any]:
        """Answer ``step``, then serve and answer until the prefetch's reply says the next step is a boundary."""

        for _ in range(12):
            self.answer(step)
            reply = self.prefetch()
            if reply["reason"] != "not_a_boundary":
                return reply
            step = self.next()["step"]
            assert step["kind"] == "item", step
        raise AssertionError("no boundary reached")

    def to_boundary(self) -> dict[str, Any]:
        return self.answer_to_boundary(self.next()["step"])

    def counts(self) -> dict[str, int]:
        with sqlite3.connect(self.paths.sqlite_path) as connection:
            tables = [row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
            return {table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] for table in tables}

    def quiet_counts(self) -> dict[str, int]:
        """Every table's rows once the answer's background work (its diagnosis and follow-up workflow, on the job
        context) has stopped writing, so a change across a call is the call's own."""

        deadline = time.monotonic() + 20
        last = self.counts()
        while time.monotonic() < deadline:
            time.sleep(0.3)
            current = self.counts()
            if current == last:
                return current
            last = current
        raise AssertionError("the answer's background work did not settle")

    def last_trace(self) -> dict[str, Any]:
        with self.repository.connection() as connection:
            rows = store.traces(connection)
            return store.trace(connection, rows[-1]["decision_id"])["trace"]


@pytest.fixture
def make_world(tmp_path, monkeypatch):
    clients: list[Any] = []
    now = {"at": DAY}

    def make(*, llm: FakeLLM | None = None, inline: bool = True, toml: str | None = None,
             models: bool = True) -> World:
        monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: now["at"])
        paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=ITEMS, version=ALGORITHM_VERSION)
        if toml:
            append_config_toml(paths.root, toml)
        repository = Repository(paths.sqlite_path)
        install_grader(monkeypatch, CountingGrader())
        device = pair(repository)
        model = (llm or FakeLLM(answer=policy_answer)) if models else None
        runtime = fake_runtime(decider=FakeDecider() if models else None, llm=model, inline=inline, seed=block_drawing_seed())
        monkeypatch.setattr(router_runtime, "_DEFAULT", runtime)
        app = create_app(config_for(paths.root))
        client = TestClient(app, base_url=f"https://{HOSTNAME}")
        client.__enter__()
        clients.append(client)
        world = World(Phone(client, device), app.state.host, repository, paths, runtime, model)
        world.now = now
        return world

    yield make
    for client in clients:
        client.__exit__(None, None, None)
