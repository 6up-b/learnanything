"""G6b: the desktop and the host, two real processes on one fresh vault (durability lane).

Production pragmas and WAL. The child runs the real host, its two secondary workers and a fake
grader; the parent is the primary desktop sidecar. They submit, read and sync at the same time,
with a leased job beside them, and nothing is lost or run twice.
"""

from __future__ import annotations

import multiprocessing
from pathlib import Path
import threading
import traceback

import pytest

pytestmark = pytest.mark.durability

pytest.importorskip("starlette")

ITEMS = [f"pi_two_process_{index}" for index in range(8)]


def _host_process(root: str, token: str, device_id: str, sessions: list[str], pipe) -> None:
    try:
        import learnloop_sidecar.handlers.practice as practice
        from starlette.testclient import TestClient
        from learnloop_mobile.host import create_app
        from tests.helpers import allow_below_floor
        from tests.mobile_host_helpers import CountingGrader, Phone, config_for, ReadyRuntime

        # The parent's registration of its vault below the floor does not cross into this process.
        allow_below_floor(Path(root))
        grader = CountingGrader()
        practice.ready_grading_provider = lambda vault, override=None: ("fake", ReadyRuntime(), grader)
        app = create_app(config_for(Path(root)))
        with TestClient(app, base_url="https://desktop.tail.ts.net") as client:
            phone = Phone(client, {"token": token, "device_id": device_id})
            pipe.send(("started",))
            while True:
                command = pipe.recv()
                if command == "stop":
                    break
                kind, payload = command
                if kind == "start":
                    pipe.send(("session", phone.start()))
                elif kind == "submit":
                    session_id, submission_id, item = payload
                    response = phone.submit(session_id, submission_id, item=item)
                    # A real interleaving, read as the phone reads: the queue beside its own submit.
                    phone.rpc("get_session", {"sessionId": session_id})
                    pipe.send(("submitted", response.status_code, response.json()))
                elif kind == "adopt":
                    session_id, generation = payload
                    phone.rpc("adopt_session", {"sessionId": session_id, "expectedGeneration": generation})
                    pipe.send(("adopted",))
                elif kind == "plan_step":
                    # Mobile v2 V2: the phone's Next on the shared plan, then its answer.
                    session_id, key = payload
                    reply = phone.rpc("next_plan_item", {"sessionId": session_id, "serve": True},
                                      request_id=f"next_{key}")
                    step = reply["step"]
                    if step and step["kind"] == "item":
                        response = phone.post("submit_dont_know", {
                            "sessionId": session_id, "practiceItemId": step["practiceItemId"],
                            "submissionId": f"dk_{key}", "hintsUsed": 0,
                            "planPresentationId": step.get("presentationId"),
                        }, request_id=f"dk_{key}")
                        assert response.status_code == 200, response.text
                    pipe.send(("stepped", step))
                elif kind == "workers":
                    runtime = app.state.host.runtime
                    pipe.send(("workers", runtime.rpc_worker.context.secondary, runtime.job_worker.context.secondary,
                               grader.grades))
        pipe.send(("stopped",))
    except BaseException:
        pipe.send(("error", traceback.format_exc()))
    finally:
        pipe.close()


def _receive(pipe, timeout: float = 120):
    assert pipe.poll(timeout), "the host process did not reply"
    result = pipe.recv()
    assert result[0] != "error", result[1]
    return result


def test_the_desktop_and_the_host_coexist_with_no_lost_writes(tmp_path):
    from learnloop.content.pipeline.runner import IngestRunner, JobSpec
    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop.vault.loader import load_vault
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY
    import learnloop_sidecar.handlers  # noqa: F401
    from tests.helpers import add_followup_item
    from tests.mobile_host_helpers import pair, rows, seeded_vault

    paths, repository = seeded_vault(tmp_path / "vault", fresh=True)
    for item in ITEMS:
        add_followup_item(paths.root, item)
        repository.upsert_practice_item_state(
            item, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
            last_attempt_at="2026-05-16T12:00:00Z", active=True,
        )
    device = pair(repository)

    # A leased job of the desktop's, older than anything the host does: never run twice.
    runner = IngestRunner(repository, vault_root=paths.root, worker_id="desktop")
    runner.enqueue_batch("legacy_ingest", [JobSpec("fake")])
    lease = repository.claim_next_ingest_job(
        worker_id="desktop", now_iso="2099-01-01T00:00:00Z", lease_cutoff_iso="2098-12-31T23:58:00Z",
    )
    assert lease is not None

    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe()
    process = context.Process(
        target=_host_process, args=(str(paths.root), device["token"], device["device_id"], [], child)
    )
    process.start()
    child.close()
    desktop = SidecarContext()
    stop_sync = threading.Event()
    sync_errors: list[BaseException] = []
    try:
        assert _receive(parent) == ("started",)
        parent.send(("start", None))
        session = _receive(parent)[1]
        sid = session["sessionId"]

        def keep_syncing() -> None:
            # The desktop's content sync, interleaved with the phone's attempts (PR-2).
            vault = load_vault(paths.root)
            try:
                while not stop_sync.is_set():
                    sync_vault_state(vault, repository)
            except BaseException as error:  # noqa: BLE001 - reported on the test's thread
                sync_errors.append(error)

        syncer = threading.Thread(target=keep_syncing)
        syncer.start()
        # The primary's reads and its token, while the host writes.
        desktop.load(paths.root, maintenance=False)
        codes = []
        for index, item in enumerate(ITEMS):
            parent.send(("submit", (sid, f"sub{index}", item)))
            spec = METHOD_REGISTRY["get_session"]
            read = spec.handler(desktop, spec.params_model.model_validate({"sessionId": sid}))
            assert read["sessionId"] == sid
            repository.bump_queue_revision()
            reply = _receive(parent)
            codes.append(reply[1])
        stop_sync.set()
        syncer.join(timeout=60)
        assert sync_errors == []
        assert codes == [200] * len(ITEMS), codes

        attempts = rows(repository, "SELECT submission_id, entry_surface, practice_item_id FROM practice_attempts")
        assert sorted(row["submission_id"] for row in attempts) == sorted(f"sub{index}" for index in range(len(ITEMS)))
        assert {row["entry_surface"] for row in attempts} == {"phone_practice"}
        # PR-2: every attempt's scheduling fields survived the sync beside it.
        for item in ITEMS:
            state = repository.practice_item_state(item)
            assert state.last_attempt_at != "2026-05-16T12:00:00Z", item
        jobs = rows(repository, "SELECT state, boot_attempts FROM mobile_jobs")
        assert jobs == [{"state": "completed", "boot_attempts": 0}] * len(ITEMS)
        parent.send(("workers", None))
        reply = _receive(parent)
        assert reply[1:3] == (True, True)
        assert reply[3] == len(ITEMS)  # one provider call each
        # The desktop's leased job was left alone.
        assert repository.claim_next_ingest_job(
            worker_id="host-would-steal", now_iso="2099-01-01T00:00:30Z", lease_cutoff_iso="2098-12-31T23:58:00Z",
        ) is None
        parent.send("stop")
        assert _receive(parent) == ("stopped",)
        process.join(timeout=30)
        assert process.exitcode == 0
    finally:
        stop_sync.set()
        desktop.close()
        if process.is_alive():
            process.terminate()
            process.join(timeout=10)
        parent.close()


def test_the_phone_and_the_desktop_take_turns_on_one_plan(tmp_path):
    """Mobile v2 V2 (§5.6): one stored plan, read by both, its steps committed atomically. The session is
    handed over each turn (PR-4), each device serves the plan's next step and answers it; no item is
    served twice, every answer is recorded once, and each boundary records its device's surface."""

    from learnloop.db.repositories import Repository
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY
    import learnloop_sidecar.handlers  # noqa: F401
    from tests.helpers import create_daily_plan_vault
    from tests.mobile_host_helpers import pair, rows

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={
        f"lo_turn_{index}": [(f"pi_turn_{index}_a", 2.0), (f"pi_turn_{index}_b", 2.0)] for index in range(3)
    })
    repository = Repository(paths.sqlite_path)
    device = pair(repository)

    def call(name: str, params: dict):
        spec = METHOD_REGISTRY[name]
        return spec.handler(desktop, spec.params_model.model_validate(params))

    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe()
    process = context.Process(
        target=_host_process, args=(str(paths.root), device["token"], device["device_id"], [], child)
    )
    process.start()
    child.close()
    desktop = SidecarContext()
    try:
        assert _receive(parent) == ("started",)
        desktop.load(paths.root, maintenance=False)
        desktop.grading_provider_override = "manual"
        parent.send(("start", None))
        sid = _receive(parent)[1]["sessionId"]
        steps: list[tuple[str, dict | None]] = []
        for turn in range(8):
            phone_turn = turn % 2 == 0
            generation = repository.fetch_session(sid).get("owner_generation") or 0
            if phone_turn:
                if turn:
                    parent.send(("adopt", (sid, generation)))
                    assert _receive(parent) == ("adopted",)
                parent.send(("plan_step", (sid, str(turn))))
                step = _receive(parent)[1]
            else:
                call("adopt_session", {"sessionId": sid, "expectedGeneration": generation})
                step = call("next_plan_item", {"sessionId": sid, "serve": True})["step"]
                if step and step["kind"] == "item":
                    call("submit_dont_know", {"sessionId": sid, "practiceItemId": step["practiceItemId"],
                                              "hintsUsed": 0, "planPresentationId": step.get("presentationId")})
            steps.append(("phone" if phone_turn else "desktop", step))
            if step is None or step["kind"] == "done":
                break
        served = [step["practiceItemId"] for _who, step in steps if step and step["kind"] == "item"]
        assert served and len(served) == len(set(served)), steps
        assert {who for who, step in steps if step and step["kind"] == "item"} == {"phone", "desktop"}
        events = rows(repository, "SELECT block_id, json_extract(detail_json, '$.practice_item_id') AS item "
                                  "FROM attention_block_events WHERE kind = 'item_served'")
        assert len(events) == len({(row["block_id"], row["item"]) for row in events})
        attempts = rows(repository, "SELECT practice_item_id, entry_surface FROM practice_attempts")
        assert sorted(row["practice_item_id"] for row in attempts) == sorted(served)
        surfaces = {row["surface"] for row in rows(
            repository, "SELECT surface FROM router_decisions WHERE decision_kind = 'plan_block'")}
        assert surfaces <= {"daily_plan", "phone_plan"}
        parent.send("stop")
        assert _receive(parent) == ("stopped",)
        process.join(timeout=30)
        assert process.exitcode == 0
    finally:
        desktop.close()
        if process.is_alive():
            process.terminate()
            process.join(timeout=10)
        parent.close()
