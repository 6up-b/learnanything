"""The learner already said OK to AI on this machine, for every test that is not about the OK.

Production sends nothing to a model before the learner's one OK (``learnloop.ai.model_use``): every client the
factory builds carries the live lookup, and the jobs and RPCs that use a model wait for it. A test that is not about
that OK runs as an established learner's machine would, where it was given once: :func:`begin` makes this computer's
record (``model_use.machine_acceptance``, otherwise read from the isolated config dir's ``ai_defaults.toml``) report
one, whatever ``LEARNLOOP_CONFIG_DIR`` a test points at. A test about the OK carries ``@pytest.mark.no_ai_ok`` and
reads the real files: its library's ``learnloop.toml`` and ``ai_defaults.toml`` in a config directory of its own,
empty when it starts (another test's OK in the session's shared directory never reaches it; a fixture of the test
may still point the variable elsewhere).

A process a test spawns reads the real files too (nothing here reaches it).
"""
from __future__ import annotations

import os
from pathlib import Path
import tempfile

from learnloop.ai import model_use

_REAL = model_use.machine_acceptance
SAID = model_use.Acceptance(
    key=model_use.MODEL_USE_KEY,
    granted_at="2026-10-12T00:00:00+00:00",
    data_flow=model_use.MODEL_USE_FLOW,
    disclosure_version=model_use.DISCLOSURE_VERSION,
    where="machine",
)


def _said() -> model_use.Acceptance:
    return SAID


_CONFIG_ENV = "LEARNLOOP_CONFIG_DIR"
_saved_config_dir: list[str | None] = []


def begin(item, temp_root: Path) -> None:  # noqa: ANN001 - a pytest item
    if item.get_closest_marker("no_ai_ok") is None:
        model_use.machine_acceptance = _said
        return
    model_use.machine_acceptance = _REAL
    _saved_config_dir.append(os.environ.get(_CONFIG_ENV))
    temp_root.mkdir(parents=True, exist_ok=True)
    os.environ[_CONFIG_ENV] = tempfile.mkdtemp(prefix="no-ai-ok-", dir=temp_root)


def end() -> None:
    model_use.machine_acceptance = _REAL
    while _saved_config_dir:
        previous = _saved_config_dir.pop()
        if previous is None:
            os.environ.pop(_CONFIG_ENV, None)
        else:
            os.environ[_CONFIG_ENV] = previous
