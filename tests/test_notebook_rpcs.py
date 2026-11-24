"""The notebook runtime's RPCs: registered, desktop only, params refusing extra fields, replies versioned, the
notebook read from inside the vault only, every runtime refusal said as a stable error, and the context stopping
the previous vault's sessions on a switch and all of them on close. The runtime is a fake here; the real one is
tests/test_notebook_runtime_sandbox.py."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from learnloop.notebook_runtime import runtime as R
from learnloop.notebook_runtime.sandbox import Limits, RuntimeUnavailable
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.notebooks import NOTEBOOK_RPCS
from tests.helpers import create_basic_vault
from tests.reading_path_fixtures import call, context

RPCS = ("notebook.open", "notebook.status", "notebook.close", "notebook.release", "notebook.run_cells")
MINIMAL = {
    "notebook.open": {"owner": "pad:p1", "path": "notebooks/a.py"},
    "notebook.status": {"sessionId": "nbs_1"},
    "notebook.close": {"sessionId": "nbs_1"},
    "notebook.release": {"sessionId": "nbs_1", "cells": ["reveal"]},
    "notebook.run_cells": {"sessionId": "nbs_1", "cells": [{"name": "square", "code": "y = 2"}]},
}


class FakeRuntime:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[str, dict]] = []

    def _answer(self, name: str, **kwargs):
        self.calls.append((name, kwargs))
        if self.error is not None:
            raise self.error
        return {"session_id": kwargs.get("session_id", "nbs_1"), "state": "starting",
                "frame_url": "http://127.0.0.1:1/s/x/"}

    def open(self, **kwargs):
        return self._answer("open", **kwargs)

    def status(self, **kwargs):
        return self._answer("status", **kwargs)

    def close_session(self, **kwargs):
        return self._answer("close", **kwargs)

    def release(self, **kwargs):
        return self._answer("release", **kwargs)

    def run_cells(self, **kwargs):
        return self._answer("run_cells", **kwargs)

    def switch_vault(self, vault_key):
        self.calls.append(("switch_vault", {"vault_key": vault_key}))

    def close(self):
        self.calls.append(("close", {}))


@pytest.fixture
def vault_ctx(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    (root / "notebooks").mkdir()
    (root / "notebooks" / "a.py").write_text("import marimo\n", encoding="utf-8")
    ctx = context(root)
    ctx.notebook_runtime = FakeRuntime()
    yield ctx
    ctx.notebook_runtime = None


def test_the_rpcs_are_registered_and_desktop_only():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert NOTEBOOK_RPCS == RPCS
    assert all(name in METHOD_REGISTRY and name not in ALLOWLIST for name in RPCS)


@pytest.mark.parametrize("name", RPCS)
def test_params_refuse_an_extra_field(name):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    model = METHOD_REGISTRY[name].params_model
    model.model_validate(MINIMAL[name])
    with pytest.raises(ValidationError):
        model.model_validate({**MINIMAL[name], "unexpected": True})


@pytest.mark.parametrize("owner", ["desk:d1", "window:w", "pad:", "pad:a b", "lesson"])
def test_an_owner_is_a_pad_or_a_lesson(owner):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    with pytest.raises(ValidationError):
        METHOD_REGISTRY["notebook.open"].params_model.model_validate({**MINIMAL["notebook.open"], "owner": owner})


@pytest.mark.parametrize("name", RPCS)
def test_every_reply_is_versioned_and_names_the_vault_open_now(vault_ctx, name):
    reply = call(vault_ctx, name, MINIMAL[name])
    assert reply["version"] == 1 and reply["sessionId"] == "nbs_1" and reply["frameUrl"].startswith("http://127.0.0.1")
    _kind, kwargs = vault_ctx.notebook_runtime.calls[-1]
    assert kwargs["vault_key"] == str(Path(vault_ctx.vault_root).resolve())


def test_open_reads_the_notebook_snapshot_and_the_vaults_settings(vault_ctx):
    call(vault_ctx, "notebook.open", {**MINIMAL["notebook.open"], "view": "edit"})
    _kind, kwargs = vault_ctx.notebook_runtime.calls[-1]
    config = vault_ctx.vault.config.notebooks
    assert kwargs["source"] == b"import marimo\n" and kwargs["owner"] == "pad:p1" and kwargs["view"] == "edit"
    assert kwargs["limits"] == Limits(memory_mib=config.memory_max_mib, scratch_mib=config.scratch_mib)
    assert kwargs["idle_minutes"] == config.idle_minutes and kwargs["max_sessions"] == config.max_sessions


def test_run_cells_and_release_pass_names_and_code(vault_ctx):
    call(vault_ctx, "notebook.release", MINIMAL["notebook.release"])
    call(vault_ctx, "notebook.run_cells", MINIMAL["notebook.run_cells"])
    assert vault_ctx.notebook_runtime.calls[-2][1]["names"] == ["reveal"]
    assert vault_ctx.notebook_runtime.calls[-1][1]["cells"] == [("square", "y = 2")]


@pytest.mark.parametrize("path", ["../outside.py", "/etc/passwd.py", "notebooks/a.txt", "notebooks/missing.py",
                                  "notebooks"])
def test_a_notebook_outside_the_vault_or_not_a_python_file_is_refused(vault_ctx, tmp_path, path):
    (tmp_path / "outside.py").write_text("x", encoding="utf-8")
    with pytest.raises(SidecarError) as caught:
        call(vault_ctx, "notebook.open", {**MINIMAL["notebook.open"], "path": path})
    assert caught.value.code == "notebook_path_invalid"
    assert vault_ctx.notebook_runtime.calls == []


@pytest.mark.parametrize("error, code, retryable", [
    (RuntimeUnavailable("bubblewrap (bwrap) is not installed"), "notebook_runtime_unavailable", False),
    (R.SessionNotFound("nbs_1"), "notebook_session_not_found", False),
    (R.SessionsFull("6 notebook sessions are open"), "notebook_sessions_full", True),
    (R.NotConnected("no window shows the notebook"), "notebook_not_connected", True),
    (R.CellUnknown("reveal"), "notebook_cell_unknown", False),
    (R.KernelRefused("marimo refused the release (403)"), "notebook_kernel_refused", True),
    (TimeoutError(), "notebook_runtime_busy", True),
])
def test_runtime_refusals_are_stable_errors(vault_ctx, error, code, retryable):
    vault_ctx.notebook_runtime.error = error
    with pytest.raises(SidecarError) as caught:
        call(vault_ctx, "notebook.status", MINIMAL["notebook.status"])
    assert caught.value.code == code and caught.value.retryable is retryable


def test_a_vault_switch_stops_the_previous_vaults_sessions_and_close_stops_all(vault_ctx, tmp_path):
    runtime = vault_ctx.notebook_runtime
    other = create_basic_vault(tmp_path / "other").root
    vault_ctx.load(other)
    assert ("switch_vault", {"vault_key": str(Path(other).resolve())}) in runtime.calls
    vault_ctx.close()
    assert runtime.calls[-1] == ("close", {})


def test_a_context_that_never_opened_a_notebook_has_no_runtime(tmp_path):
    ctx = context(create_basic_vault(tmp_path / "vault").root)
    ctx.close()
    assert ctx.notebook_runtime is None
