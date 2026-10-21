"""UX Phase 2: the shell (``docs/specs/ux_learnloop_v1.md`` §5, §10 2.1–2.5, Q17).

The sidecar half of the phase is one display-only config key, ``[ui] shell``:
``"simple"`` (the default) is the four-place shell, ``"classic"`` keeps the
ten-tab shell as it was. The desktop reads it from the app snapshot; no
grading, scheduling, evidence, projection or replay path reads it, so it needs
no algorithm successor (the owner's live-behind-kill-switches ruling).

Fakes only; no network, no paid call.
"""

from __future__ import annotations

import pathlib
import re

import pytest

from learnloop.config.schema import LearnLoopConfig
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import config_dto
from tests.helpers import create_basic_vault


def test_the_shell_switch_defaults_to_simple_and_reaches_the_app(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    assert vault.config.ui.shell == "simple"
    assert config_dto(vault)["ui"] == {"practiceFeedback": "simple", "shell": "simple"}


def test_classic_keeps_the_old_shell_and_leaves_phase_4_alone(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    with open(paths.root / "learnloop.toml", "a", encoding="utf-8") as handle:
        handle.write('\n[ui]\nshell = "classic"\n')
    dto = config_dto(load_vault(paths.root))
    assert dto["ui"] == {"practiceFeedback": "simple", "shell": "classic"}


def test_the_shell_switch_accepts_only_its_two_shells():
    assert LearnLoopConfig.model_validate({"ui": {"shell": "classic"}}).ui.shell == "classic"
    with pytest.raises(ValueError):
        LearnLoopConfig.model_validate({"ui": {"shell": "tabs"}})


def test_the_shell_switch_is_display_only():
    """Only the app snapshot reads ``config.ui``: no Python path decides
    anything by the shell (so no successor, and replay never sees it). The
    parameter registry names the key only to classify it (F9)."""

    root = pathlib.Path(__file__).resolve().parents[1] / "src"
    readers = sorted(
        str(path.relative_to(root))
        for path in root.rglob("*.py")
        if re.search(r"\bui\.shell\b", path.read_text(encoding="utf-8"))
    )
    assert readers == ["learnloop/params/parameter_registry.py", "learnloop_sidecar/context.py"]
    registry = (root / "learnloop/params/parameter_registry.py").read_text(encoding="utf-8")
    assert re.findall(r"\bui\.shell\b", registry) == ["ui.shell"]


def test_the_shell_switch_is_classified_as_a_structural_display_key():
    """Codex review of ux-phase2-shell F9: every new config key has a rule in
    the parameter registry. ``ui.shell`` is a string enum, so the numeric-leaf
    audit never reaches it; it needs its own rule."""

    from learnloop.params.parameter_registry import classify_config_path

    rule = classify_config_path("ui.shell")
    assert rule is not None
    assert (rule.kind, rule.param_class) == ("structural", "operational")
    assert "display" in rule.rationale
