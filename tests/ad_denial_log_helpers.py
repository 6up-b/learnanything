"""What other test files use from ``tests/test_ad_denial_log.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from learnloop.adaptive_difficulty import denial_log as D


OLD_LINE = {"epoch": "e1", "reader": "learnloop.adaptive_difficulty.replay", "table": "practice_attempts",
            "verb": "read", "why": "derived"}


def _write_log(paths, lines) -> Path:
    log = D.denial_log_path(paths.sqlite_path)
    log.write_text("".join(json.dumps(line, sort_keys=True) + "\n" for line in lines), encoding="utf-8")
    return log


def _archives(paths) -> list[Path]:
    return D.archived_logs(paths.sqlite_path)


def _upgrade(paths, to):
    from learnloop.cli import app

    return CliRunner().invoke(app, ["upgrade", "--to", to, "--vault", str(paths.root)])
