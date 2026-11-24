"""Notebook runtime RPCs: ``notebook.open``, ``notebook.status``, ``notebook.close``, ``notebook.release`` and
``notebook.run_cells`` (``docs/reviews/notebook-runtime-b1-b3.md``).

Desktop only (pinned in tests/test_mobile_allowlist.py): a session is a sandboxed marimo server on this machine,
shown in a frame the desktop creates. A session is process state, never evidence or persisted meaning; these RPCs
write nothing to the vault. ``open`` answers at once (the server starts in the background) with the frame URL the
window loads once ``status`` reads ``ready``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from learnloop.notebook_runtime import runtime as R
from learnloop.notebook_runtime import settings
from learnloop.notebook_runtime.sandbox import Limits, RuntimeUnavailable
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, Verbatim, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
NOTEBOOK_RPCS: tuple[str, ...] = ("notebook.open", "notebook.status", "notebook.close", "notebook.release",
                                  "notebook.run_cells")

#: A session's owner: the pad whose cells it runs or the lesson whose notebook it shows (never a desk or a window,
#: so moving a pad keeps its kernel).
OWNER_PATTERN = r"^(pad|lesson):[A-Za-z0-9_.:-]{1,200}$"
CELL_NAME_PATTERN = r"^[A-Za-z_][A-Za-z0-9_]{0,200}$"


class NotebookOpenInput(ParamsModel):
    owner: str = Field(pattern=OWNER_PATTERN)
    #: The notebook file, relative to the vault root; the session runs a snapshot of its bytes. Left out for a
    #: pad (``pad:<id>``), whose notebook is generated from the pad's cells, and for a lesson (``lesson:<id>``),
    #: whose notebook is its own (``notebook_runtime.lessons``).
    path: str | None = Field(default=None, min_length=1, max_length=1000)
    view: Literal["app", "edit"] = "app"


class NotebookSessionInput(ParamsModel):
    session_id: str = Field(min_length=1, max_length=100)


class NotebookReleaseInput(NotebookSessionInput):
    cells: list[str] = Field(min_length=1, max_length=200)


class NotebookCell(ParamsModel):
    name: str = Field(pattern=CELL_NAME_PATTERN)
    code: str = Field(max_length=200_000)


class NotebookRunCellsInput(NotebookSessionInput):
    cells: list[NotebookCell] = Field(min_length=1, max_length=200)


def _runtime(ctx: SidecarContext) -> R.NotebookRuntime:
    if ctx.notebook_runtime is None:
        ctx.notebook_runtime = R.NotebookRuntime()
    return ctx.notebook_runtime


def _vault_key(ctx: SidecarContext) -> str:
    """The vault a session belongs to: the context's open vault, resolved."""

    return str(Path(ctx.vault_root).resolve()) if ctx.vault_root else ""


def _source(vault_root: Path, relative: str) -> bytes:
    root = vault_root.resolve()
    candidate = Path(relative)
    if candidate.is_absolute() or candidate.suffix != ".py":
        raise SidecarError("notebook_path_invalid", "Open the notebook from its lesson.")
    path = (root / candidate).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise SidecarError("notebook_path_invalid", "Couldn’t find this notebook. Reopen it from its lesson.")
    if path.stat().st_size > settings.NOTEBOOK_MAX_BYTES:
        raise SidecarError("notebook_path_invalid", "This notebook is too large to open. Choose a smaller notebook.")
    return path.read_bytes()


#: Where a pad's generated notebook is written: machine-local state under the vault (``.learnloop/``, which the
#: loader and the vault watcher leave alone), a derived file regenerated from the pad's cells on every open. It is
#: not a table, so no replayer: the pad's block versions are the only source, and deleting the file loses nothing.
PAD_NOTEBOOKS = Path(".learnloop") / "notebooks" / "pads"


def pad_notebook(vault_root: Path, repository: Any, pad_id: str) -> tuple[bytes, str, dict[str, str],
                                                                        list[tuple[str, str]]]:
    """The pad's notebook (generated from its standing cells, in pad order) and its revision: the cells' names in
    order, so an edit to a cell's code keeps the session (it reaches the kernel through ``notebook.run_cells``)
    while an inserted, removed or moved cell makes a new one. Writes the derived copy under the vault."""

    import hashlib

    from learnloop.notebook_runtime import adapter, hostfiles
    from learnloop.pads.cells import pad_cells

    cells = pad_cells(repository, pad_id)
    if cells is None:
        raise SidecarError("pad_not_found", "Couldn’t find this pad. Reopen the pad and try again.")
    if not cells:
        raise SidecarError("notebook_no_cells", "Add a Python cell to this pad first.")
    named = [(adapter.cell_name(cell["block_id"]), cell["code"]) for cell in cells]
    if len({name for name, _code in named}) != len(named):
        raise SidecarError("notebook_path_invalid", "Two cells would have the same name. Open a pad with distinct cells.")
    source = adapter.notebook_from_cells(named).encode("utf-8")
    if len(source) > settings.NOTEBOOK_MAX_BYTES:
        raise SidecarError("notebook_path_invalid", "This notebook is too large. Try a pad with less code.")
    revision = hashlib.sha256("\n".join(name for name, _code in named).encode()).hexdigest()
    try:
        # Never through a link: the vault may hold one anywhere below its root.
        hostfiles.write_beneath(vault_root, PAD_NOTEBOOKS.parts, f"{adapter.cell_name(pad_id)[2:]}.py", source)
    except hostfiles.UnsafePath as exc:
        raise SidecarError("notebook_path_invalid", "Couldn’t prepare this notebook. Reopen the pad and try again.") from exc
    return source, revision, {cell["block_id"]: name for cell, (name, _code) in zip(cells, named, strict=True)}, named


def lesson_notebook(vault_root: Path, repository: Any, lesson_id: str,
                    path: str | None) -> tuple[bytes, dict[str, Any], bool]:
    """A lesson's notebook (spec §11.2): its bytes, its commit points and held cells, and whether the lesson is
    closed (a review: nothing is released). A lesson that exists is opened on its own notebook only; a ``path``
    names a notebook for an owner key no lesson has (the frame's fixtures)."""

    from learnloop.notebook_runtime.lessons import lesson_contract, lesson_notebook_path

    with repository.connection() as connection:
        row = connection.execute("SELECT closed_at FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
    if row is not None:
        own = lesson_notebook_path(vault_root, lesson_id)
        if own is None:
            raise SidecarError("notebook_path_invalid", "Choose a lesson with a notebook.")
        if path is not None and Path(path).as_posix() != own:
            raise SidecarError("notebook_path_invalid", "Open this notebook from its lesson.")
        path = own
    elif path is None:
        raise SidecarError("notebook_path_invalid", "Open the notebook from its lesson.")
    source = _source(vault_root, path)
    return source, lesson_contract(source), row is not None and row["closed_at"] is not None


def _errors(exc: Exception) -> SidecarError:
    if isinstance(exc, RuntimeUnavailable):
        return SidecarError("notebook_runtime_unavailable", f"Notebooks can't run here: {exc}.")
    if isinstance(exc, R.SessionNotFound):
        return SidecarError("notebook_session_not_found", "Reopen the notebook, then select Run code.")
    if isinstance(exc, R.SessionsFull):
        return SidecarError("notebook_sessions_full",
                            "Too many notebooks are open. Close one and try again.",
                            retryable=True)
    if isinstance(exc, R.NotConnected):
        return SidecarError("notebook_not_connected", "The notebook is still starting. Try again in a moment.", retryable=True)
    if isinstance(exc, R.CellUnknown):
        return SidecarError("notebook_cell_unknown", "Couldn’t find this cell. Reopen the notebook and try again.")
    if isinstance(exc, R.ReleaseRefused):
        return SidecarError("notebook_release_refused", "This part of the notebook is unavailable. Return to the lesson.")
    if isinstance(exc, R.KernelRefused):
        return SidecarError("notebook_kernel_refused", "Couldn’t run the code. Reopen the notebook and try again.", retryable=True)
    if isinstance(exc, TimeoutError):
        return SidecarError("notebook_runtime_busy", "The notebook runtime didn't answer in time. Try again.",
                            retryable=True)
    raise exc


#: Reply maps keyed by names the client compares as they are (cell names, block ids): never camelCased.
_VERBATIM_KEYS = ("cell_runs", "pad_cells")


def _call(work: Any) -> dict[str, Any]:
    try:
        result = dict(work())
        for key in _VERBATIM_KEYS:
            if key in result:
                result[key] = Verbatim(result[key])
        return versioned(result)
    except SidecarError:
        raise
    except Exception as exc:  # noqa: BLE001 - mapped, or raised as it is
        raise _errors(exc) from exc


@method("notebook.open", NotebookOpenInput)
def notebook_open_handler(ctx: SidecarContext, params: NotebookOpenInput) -> dict[str, Any]:
    """Open (or return) the owner's session on the notebook at ``path``, or on a pad's cells (``pad:<id>`` with no
    path): ``{sessionId, state, frameUrl, cellRuns, ...}``."""

    vault, repository = ctx.require_vault()
    revision = None
    names: dict[str, str] | None = None
    pad_cells: list[tuple[str, str]] | None = None
    contract: dict[str, Any] | None = None
    review = False
    if params.owner.startswith("pad:"):
        if params.path is not None:
            source = _source(vault.root, params.path)
        else:
            source, revision, names, pad_cells = pad_notebook(Path(vault.root), repository, params.owner[len("pad:"):])
    else:
        source, contract, review = lesson_notebook(Path(vault.root), repository, params.owner[len("lesson:"):],
                                                   params.path)
    config = vault.config.notebooks

    def opened() -> dict[str, Any]:
        view = _runtime(ctx).open(vault_key=_vault_key(ctx), owner=params.owner, source=source, view=params.view,
                                  limits=Limits.from_config(config), idle_minutes=config.idle_minutes,
                                  max_sessions=config.max_sessions, revision=revision, contract=contract,
                                  review=review, cells=pad_cells)
        return view if names is None else {**view, "pad_cells": names}

    return _call(opened)


def _lesson_closed(repository: Any, owner: str) -> bool:
    if not owner.startswith("lesson:"):
        return False
    with repository.connection() as connection:
        row = connection.execute("SELECT closed_at FROM lessons WHERE id = ?", (owner[len("lesson:"):],)).fetchone()
    return row is not None and row["closed_at"] is not None


def _with_lesson_state(ctx: SidecarContext, repository: Any, session_id: str) -> dict[str, Any]:
    """The session as it is, a lesson's read again from the lesson's own record: closed anywhere (another window,
    the phone, a chat), its notebook is a review from then on and releases nothing more."""

    runtime = _runtime(ctx)
    view = runtime.status(vault_key=_vault_key(ctx), session_id=session_id)
    lesson = view.get("lesson")
    if lesson is not None and not lesson.get("review") and _lesson_closed(repository, str(view.get("owner", ""))):
        view = runtime.mark_review(vault_key=_vault_key(ctx), session_id=session_id)
    return view


@method("notebook.status", NotebookSessionInput)
def notebook_status_handler(ctx: SidecarContext, params: NotebookSessionInput) -> dict[str, Any]:
    """A session's state, frame URL, restarts, attached frames and memory."""

    _vault, repository = ctx.require_vault()
    return _call(lambda: _with_lesson_state(ctx, repository, params.session_id))


@method("notebook.close", NotebookSessionInput)
def notebook_close_handler(ctx: SidecarContext, params: NotebookSessionInput) -> dict[str, Any]:
    """Stop a session's server (graceful, then forced) and forget the session."""

    ctx.require_vault()
    return _call(lambda: _runtime(ctx).close_session(vault_key=_vault_key(ctx), session_id=params.session_id))


@method("notebook.release", NotebookReleaseInput)
def notebook_release_handler(ctx: SidecarContext, params: NotebookReleaseInput) -> dict[str, Any]:
    """Release held cells (shipped ``disabled=True``): marimo runs them at once. The frame itself cannot. A lesson's
    state is read again first, so a lesson closed elsewhere releases nothing."""

    _vault, repository = ctx.require_vault()

    def release() -> dict[str, Any]:
        _with_lesson_state(ctx, repository, params.session_id)
        return _runtime(ctx).release(vault_key=_vault_key(ctx), session_id=params.session_id, names=list(params.cells))

    return _call(release)


@method("notebook.run_cells", NotebookRunCellsInput)
def notebook_run_cells_handler(ctx: SidecarContext, params: NotebookRunCellsInput) -> dict[str, Any]:
    """Run named cells with the given code (a pad cell's ⇧↵, later the teacher's edits)."""

    ctx.require_vault()
    return _call(lambda: _runtime(ctx).run_cells(vault_key=_vault_key(ctx), session_id=params.session_id,
                                                 cells=[(cell.name, cell.code) for cell in params.cells]))
