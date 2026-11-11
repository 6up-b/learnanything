"""What other test files use from ``tests/test_diagnosis_isolation.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any


def _fake_sdk(monkeypatch, captured: dict[str, Any], *, overrides_field: bool = True):
    class FakeCodex:
        def __init__(self, config):
            from tests.codex_cli_fakes import FakeSdkClient

            self._client = FakeSdkClient()
            captured["app_config"] = config.kwargs
            workspace = Path(config.kwargs["cwd"])
            captured["workspace_listing"] = sorted(path.name for path in workspace.iterdir())

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def close(self):
            return None

        def thread_start(self, **kwargs):
            captured["thread_start"] = kwargs
            return FakeThread()

    class FakeThread:
        def turn(self, prompt, **kwargs):
            captured["turn"] = kwargs
            return SimpleNamespace(run=lambda: SimpleNamespace(final_response='{"links": []}', items=[]), interrupt=lambda: None)

    if overrides_field:
        class SdkAppConfig:
            def __init__(self, *, codex_bin=None, launch_args_override=None, config_overrides=(), cwd=None, env=None, client_name="", client_title=""):
                self.kwargs = {"codex_bin": codex_bin, "launch_args_override": launch_args_override, "config_overrides": tuple(config_overrides), "cwd": cwd}
    else:
        class SdkAppConfig:
            def __init__(self, *, codex_bin=None, launch_args_override=None, cwd=None, env=None, client_name="", client_title=""):
                self.kwargs = {"codex_bin": codex_bin, "cwd": cwd}

    class ReasoningSummary:
        @classmethod
        def model_validate(cls, value):
            return value

    from enum import Enum

    class ReasoningEffort(Enum):
        low = "low"

    openai_codex = ModuleType("openai_codex")
    openai_codex.Codex = FakeCodex
    from tests.codex_cli_fakes import FakeApprovalMode
    openai_codex.ApprovalMode = FakeApprovalMode
    openai_codex.CodexConfig = SdkAppConfig
    types = ModuleType("openai_codex.types")
    types.Personality = SimpleNamespace(pragmatic="pragmatic")
    types.ReasoningEffort = ReasoningEffort
    types.ReasoningSummary = ReasoningSummary
    openai_codex.types = types
    monkeypatch.setitem(sys.modules, "openai_codex", openai_codex)
    monkeypatch.setitem(sys.modules, "openai_codex.types", types)
