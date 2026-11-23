"""The notebook runtime against a real sandbox: a sandboxed marimo server on a synthetic notebook, reached through
the frame proxy as a browser frame would (no browser): an edit round trip, a held cell the frame cannot release and
the sidecar can, a crash restart with the UI values replayed, a vault switch, and nothing left running after a stop.
Skipped where bubblewrap or the notebook extra is missing."""

from __future__ import annotations

import asyncio
import os
import signal
from pathlib import Path

import pytest

from learnloop.notebook_runtime.sandbox import missing_requirements
from tests.notebook_runtime_helpers import LIMITS, SYNTHETIC_NOTEBOOK, frame_round_trip, short_base_dir, wait_state

pytestmark = [pytest.mark.notebook_sandbox,
              pytest.mark.skipif(bool(missing_requirements()), reason="; ".join(missing_requirements()) or "ok")]


@pytest.fixture
def runtime():
    from learnloop.notebook_runtime.runtime import NotebookRuntime

    with short_base_dir() as base:
        made = NotebookRuntime(base_dir=base)
        try:
            yield made
        finally:
            made.close()


def _open(runtime, vault="/v1", owner="pad:p1"):
    view = runtime.open(vault_key=vault, owner=owner, source=SYNTHETIC_NOTEBOOK.encode(), view="app", limits=LIMITS,
                        idle_minutes=10, max_sessions=4)
    return wait_state(runtime, vault, view["session_id"], "ready")


def _group_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    return True


def _processes_naming(text: str) -> list[int]:
    found = []
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            try:
                if text.encode() in (entry / "cmdline").read_bytes():
                    found.append(int(entry.name))
            except OSError:
                pass
    return found


def test_an_edit_round_trip_through_the_proxy_and_a_stop_leaves_nothing(runtime):
    view = _open(runtime)
    session = runtime.sessions()[0]
    pgid = session.process.pid
    result = asyncio.run(frame_round_trip(view["frame_url"], marimo_session="s_frame1", wanted=["square=9"],
                                          set_value=("controls", 4), then_wanted=("square=16",)))
    assert result["page_status"] == 200 and result["instantiate_status"] == 200 and result["set_status"] == 200
    assert "'wasm-unsafe-eval'" in result["page_csp"] and "frame-ancestors" in result["page_csp"]
    assert not result["page_set_cookie"] and result["bridge_injected"]
    assert result["round_trip_seconds"] < 5
    assert session.ui_values == {f"{result['cells']['controls']}-0": 4}
    assert set(runtime.status(vault_key="/v1", session_id=view["session_id"])["cells"]) == {
        "imports", "controls", "square", "reveal"}
    runtime.close_session(vault_key="/v1", session_id=view["session_id"])
    assert not _group_alive(pgid)
    assert _processes_naming(str(session.layout.socket)) == []
    assert not session.layout.socket.exists()


def test_the_frame_cannot_release_a_held_cell_and_the_sidecar_can(runtime):
    import httpx

    view = _open(runtime)
    base = view["frame_url"].split("?")[0].rstrip("/")

    def as_the_frame_then_the_sidecar():
        cells = runtime.sessions()[0].cell_ids
        refused = httpx.post(f"{base}/api/kernel/set_cell_config", headers={"Marimo-Session-Id": "s_frame2"},
                             json={"configs": {cells["reveal"]: {"disabled": False}}}).status_code
        released = runtime.release(vault_key="/v1", session_id=view["session_id"], names=["reveal"])
        return refused, released

    result = asyncio.run(frame_round_trip(view["frame_url"], marimo_session="s_frame2", wanted=["square=9"],
                                          during=as_the_frame_then_the_sidecar, then_wanted=("revealed=3",)))
    refused, released = result["during"]
    assert refused == 403 and released["released"] == ["reveal"]
    assert "revealed=3" in result["seen"]


def test_a_crashed_server_restarts_and_a_fresh_page_gets_the_recorded_values(runtime):
    view = _open(runtime)
    asyncio.run(frame_round_trip(view["frame_url"], marimo_session="s_frame3", wanted=["square=9"],
                                 set_value=("controls", 7), then_wanted=("square=49",)))
    session = runtime.sessions()[0]
    old = session.process.pid
    os.killpg(old, signal.SIGKILL)
    after = wait_state(runtime, "/v1", view["session_id"], "ready", timeout=30)
    while after["restarts"] < 1:
        after = wait_state(runtime, "/v1", view["session_id"], "ready", timeout=30)
    assert after["restarts"] == 1 and session.process.pid != old and not _group_alive(old)
    assert after["frame_url"] == view["frame_url"]  # the same proxy, the same URL
    result = asyncio.run(frame_round_trip(view["frame_url"], marimo_session="s_frame4", wanted=["square=49"]))
    assert "square=49" in result["seen"]


def test_a_vault_switch_stops_the_other_vaults_server(runtime):
    from learnloop.notebook_runtime.runtime import SessionNotFound

    gone = _open(runtime, vault="/v1")
    kept = _open(runtime, vault="/v2", owner="pad:p2")
    by_vault = {session.vault_key: session for session in runtime.sessions()}
    gone_group, kept_group = by_vault["/v1"].process.pid, by_vault["/v2"].process.pid
    runtime.switch_vault("/v2")
    assert not _group_alive(gone_group) and _group_alive(kept_group)
    with pytest.raises(SessionNotFound):
        runtime.status(vault_key="/v1", session_id=gone["session_id"])
    assert runtime.status(vault_key="/v2", session_id=kept["session_id"])["state"] == "ready"
    runtime.close()
    assert not _group_alive(kept_group)
