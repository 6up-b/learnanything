"""textual is the optional `tui` extra, not a core dependency (refactor C7a).

Only `learnloop today` loads the old terminal app (`learnloop.app_launch.launch_tui`),
so the base install imports and runs without textual, and `today` says how to add
the extra instead of failing with a traceback. The venv here has textual (the gates
sync `--extra tui`), so a subprocess hides it behind an import hook.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

from typer.testing import CliRunner

import learnloop.app_launch as app_launch
from learnloop.cli import app

HINT = "uv sync --extra tui"
PIP_HINT = "pip install 'learnloop[tui]'"

# Any import of textual fails as it would on an install without the extra.
_NO_TEXTUAL = textwrap.dedent(
    """
    import sys

    class _NoTextual:
        def find_spec(self, name, path=None, target=None):
            if name == "textual" or name.startswith("textual."):
                raise ModuleNotFoundError(f"No module named {name!r}", name=name)
            return None

    sys.meta_path.insert(0, _NoTextual())
    """
)


def _without_textual(body: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", _NO_TEXTUAL + textwrap.dedent(body)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_the_base_install_imports_and_runs_help_without_textual():
    result = _without_textual(
        """
        import learnloop
        import learnloop.app_launch
        import learnloop.cli.app
        import learnloop_sidecar.handlers
        from learnloop.cli import app

        assert "textual" not in sys.modules
        sys.argv = ["learnloop", "--help"]
        app()
        """
    )

    assert result.returncode == 0, result.stderr
    assert "today" in result.stdout
    assert "Traceback" not in result.stderr


def test_today_without_textual_prints_the_install_hint_and_exits_cleanly(tmp_path):
    result = _without_textual(
        f"""
        from learnloop.cli import app

        sys.argv = ["learnloop", "today", "--vault", {str(tmp_path)!r}]
        app()
        """
    )

    assert result.returncode == 1
    assert HINT in result.stderr
    assert PIP_HINT in result.stderr
    assert "Traceback" not in result.stderr


def test_today_names_the_extra_only_for_textual(monkeypatch, tmp_path):
    def missing(name):
        def launch(_root):
            raise ModuleNotFoundError(f"No module named {name!r}", name=name)

        return launch

    monkeypatch.setattr(app_launch, "launch_tui", missing("textual.widgets"))
    result = CliRunner().invoke(app, ["today", "--vault", str(tmp_path)])
    assert result.exit_code == 1
    assert HINT in result.output

    # Any other missing module is a real bug, so it is not dressed up as the hint.
    monkeypatch.setattr(app_launch, "launch_tui", missing("somethingelse"))
    result = CliRunner().invoke(app, ["today", "--vault", str(tmp_path)])
    assert isinstance(result.exception, ModuleNotFoundError)
    assert HINT not in result.output
