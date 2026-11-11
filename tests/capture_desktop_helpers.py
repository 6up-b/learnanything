"""What other test files use from ``tests/test_capture_desktop.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from pathlib import Path

from learnloop.capture import create_capture
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop_sidecar.context import SidecarContext


def _capture(root: Path, *, url: str | None = None) -> tuple[Repository, str]:
    repository = Repository(root / "state.sqlite")
    receipt = create_capture(
        repository, root=root, client_capture_id=new_ulid(),
        kind="url" if url else "text", url=url, text=None if url else "Why eigenvectors?",
    )
    return repository, receipt["capture_id"]


def _context(root: Path) -> SidecarContext:
    ctx = SidecarContext()
    ctx.load(root, maintenance=False)
    return ctx
