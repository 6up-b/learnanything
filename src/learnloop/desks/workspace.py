"""Desks and their windows (spec §5.1, §5.2, §3.4): the state read and the ``desk.apply`` ops.

A desk is a strip of slots. Slots are authoritative: a slot holds one window, or two (a pair, panes 0
and 1, one of them active). Every op names the version of the desk it changes (``expected_version``);
an applied op adds one to that version, so a client that applied ops optimistically knows the version
each later op of its batch expects. Workflow data, never evidence: nothing here imports scheduling,
evidence or the router (the import fences in ``pyproject.toml``).
"""
from __future__ import annotations

from collections.abc import Callable
import json
from typing import Annotated, Any, Literal, Union

from pydantic import Field, model_validator

from learnloop.db.stores import desks as store
from learnloop.db.stores import pad_reads
from learnloop.db.stores import pads as pad_store
from learnloop.desks.content_ref import ContentRef, StackEntry, WireModel
from learnloop.desks.protocol import OpConflict, OpRefused, apply_batch, client_seq_heads, run_op
from learnloop.db.stores.workspace_batches import DESK

#: A pair is at most two windows in one slot (spec §5.2).
PAIR_SIZE = 2
DOCKS = ("br", "bl", "right", "cb")


class _Op(WireModel):
    expected_version: int | None = None


class CreateDesk(_Op):
    op: Literal["create_desk"]
    desk_id: str = Field(min_length=1)
    title: str
    position: str = Field(min_length=1)
    goal_id: str | None = None
    companion_dock: Literal["br", "bl", "right", "cb"] = "br"


class RenameDesk(_Op):
    op: Literal["rename_desk"]
    desk_id: str
    title: str


class ArchiveDesk(_Op):
    op: Literal["archive_desk"]
    desk_id: str


class MoveDesk(_Op):
    op: Literal["move_desk"]
    desk_id: str
    position: str = Field(min_length=1)


class OpenWindow(_Op):
    op: Literal["open_window"]
    desk_id: str
    window_id: str = Field(min_length=1)
    content: ContentRef | None = None
    stack: list[StackEntry] | None = None
    view: dict[str, Any] = Field(default_factory=dict)
    after_window_id: str | None = None

    @model_validator(mode="after")
    def _content_or_stack(self) -> OpenWindow:
        if (self.content is None) == (self.stack is None):
            raise ValueError("a window shows one content reference or a pad stack, not both or neither")
        if self.stack is not None and not self.stack:
            raise ValueError("a pad stack holds at least one pad or lesson")
        return self


class CloseWindow(_Op):
    op: Literal["close_window"]
    desk_id: str
    window_id: str


class ReopenWindow(_Op):
    op: Literal["reopen_window"]
    desk_id: str
    window_id: str
    slot: int | None = Field(default=None, ge=0)


class MoveWindow(_Op):
    op: Literal["move_window"]
    desk_id: str
    window_id: str
    to_slot: int = Field(ge=0)


class MoveToDesk(_Op):
    op: Literal["move_to_desk"]
    desk_id: str
    window_id: str
    to_desk_id: str
    #: The destination's version: a transfer changes both desks, so it names both heads.
    to_expected_version: int
    after_window_id: str | None = None


class Pair(_Op):
    op: Literal["pair"]
    desk_id: str
    window_id: str


class Unpair(_Op):
    op: Literal["unpair"]
    desk_id: str
    window_id: str


class SetFocus(_Op):
    op: Literal["set_focus"]
    desk_id: str
    window_id: str | None = None


class SetActivePane(_Op):
    op: Literal["set_active_pane"]
    desk_id: str
    window_id: str


class SetView(_Op):
    op: Literal["set_view"]
    desk_id: str
    window_id: str
    view: dict[str, Any]


class SetDock(_Op):
    op: Literal["set_dock"]
    desk_id: str
    dock: Literal["br", "bl", "right", "cb"]


class SetCompanionShown(_Op):
    op: Literal["set_companion_shown"]
    desk_id: str
    shown: bool


class SetGoal(_Op):
    op: Literal["set_goal"]
    desk_id: str
    goal_id: str | None = None


class AddToStack(_Op):
    """Put a pad (or a lesson) in a stack window: a union, so it commutes with every other change to the desk and
    needs no expected version (one given is not checked). Already there: nothing changes."""

    op: Literal["add_to_stack"]
    desk_id: str
    window_id: str
    entry: StackEntry


class RemoveFromStack(_Op):
    """Take a pad (or a lesson) out of a stack window, by the same rule; not there: nothing changes."""

    op: Literal["remove_from_stack"]
    desk_id: str
    window_id: str
    entry: StackEntry


class EnsureRunningPad(_Op):
    """The desk's running pad (spec §10.5), created when it has none, and in a stack window of the desk, opened when
    it has none: idempotent, so every desk, new or old, gets one in one place. ``pad_id`` and ``window_id`` are
    client-minted and used only when something is created; no expected version (one given is not checked)."""

    op: Literal["ensure_running_pad"]
    desk_id: str
    pad_id: str = Field(min_length=1)
    window_id: str = Field(min_length=1)
    title: str = ""


DeskOp = Annotated[
    Union[CreateDesk, RenameDesk, ArchiveDesk, MoveDesk, OpenWindow, CloseWindow, ReopenWindow, MoveWindow,
          MoveToDesk, Pair, Unpair, SetFocus, SetActivePane, SetView, SetDock, SetCompanionShown, SetGoal,
          AddToStack, RemoveFromStack, EnsureRunningPad],
    Field(discriminator="op"),
]

DESK_OPS: tuple[str, ...] = (
    "create_desk", "rename_desk", "archive_desk", "move_desk", "open_window", "close_window", "reopen_window",
    "move_window", "move_to_desk", "pair", "unpair", "set_focus", "set_active_pane", "set_view", "set_dock",
    "set_companion_shown", "set_goal", "add_to_stack", "remove_from_stack", "ensure_running_pad",
)


# -- reads ----------------------------------------------------------------------------------------


def _window_out(row: dict[str, Any]) -> dict[str, Any]:
    spec = json.loads(row["spec_json"] or "{}")
    out: dict[str, Any] = {"window_id": row["window_id"], "pane": int(row["pane"]), "kind": row["kind"],
                           "active": bool(row["active"]), "view": json.loads(row["view_json"] or "{}")}
    if row["kind"] == "pad_stack":
        out["stack"] = spec.get("stack") or []
    else:
        out["content"] = spec.get("content")
    return out


def _slots(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    slots: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        slots.setdefault(int(row["slot"]), []).append(_window_out(row))
    return [{"slot": slot, "windows": windows} for slot, windows in sorted(slots.items())]


def desk_state(repository: Any) -> dict[str, Any]:
    """Every open desk with its slots, the running pads, and each client's last applied batch."""

    with repository.connection() as connection:
        desks = store.open_desks(connection)
        out = []
        running: list[str] = []
        for desk in desks:
            out.append({
                "desk_id": desk["desk_id"], "title": desk["title"], "position": desk["position"],
                "focus_window_id": desk["focus_window_id"], "goal_id": desk["goal_id"],
                "companion": {"dock": desk["companion_dock"], "shown": bool(desk["companion_shown"])},
                "version": int(desk["version"]),
                "slots": _slots(store.open_windows(connection, desk["desk_id"])),
            })
            running.extend(pad_reads.running_pad_ids(connection, desk["desk_id"]))
    return {"desks": out, "running_pad_ids": running, "server_seq": client_seq_heads(repository)}


# -- layout -------------------------------------------------------------------------------------


class _Layout:
    """One desk's open windows as a list of slots (each a list of window ids, panes in order)."""

    def __init__(self, connection: Any, desk_id: str) -> None:
        self.connection = connection
        self.desk_id = desk_id
        rows = store.open_windows(connection, desk_id)
        self.rows = {row["window_id"]: row for row in rows}
        grouped: dict[int, list[str]] = {}
        for row in rows:
            grouped.setdefault(int(row["slot"]), []).append(row["window_id"])
        self.slots: list[list[str]] = [ids for _slot, ids in sorted(grouped.items())]
        self.active = {row["window_id"] for row in rows if row["active"]}

    def index_of(self, window_id: str) -> int:
        for index, ids in enumerate(self.slots):
            if window_id in ids:
                return index
        raise OpRefused("window_not_open", "That window is not open on this desk.")

    def write(self, extra: dict[str, dict[str, Any]] | None = None) -> None:
        """Write every open window's slot, pane and active flag (and ``extra`` fields by window)."""

        extra = extra or {}
        for slot, ids in enumerate(self.slots):
            if len(ids) == 1:
                self.active.add(ids[0])
            elif not any(window_id in self.active for window_id in ids):
                self.active.add(ids[0])
            for pane, window_id in enumerate(ids):
                fields = {"desk_id": self.desk_id, "slot": slot, "pane": pane,
                          "active": 1 if window_id in self.active else 0, **extra.pop(window_id, {})}
                store.update_window(self.connection, window_id, fields)
        for window_id, fields in extra.items():
            store.update_window(self.connection, window_id, fields)


# -- ops --------------------------------------------------------------------------------------------


def _desk(connection: Any, desk_id: str, expected: int | None) -> dict[str, Any]:
    desk = store.desk(connection, desk_id)
    if desk is None:
        raise OpRefused("desk_not_found", "Couldn’t find this desk. Open a desk and try again.")
    if desk["archived_at"] is not None:
        raise OpRefused("desk_archived", "This desk is archived. Open another desk.")
    if expected is None or int(expected) != int(desk["version"]):
        raise OpConflict({"desk_id": desk_id, "version": int(desk["version"])})
    return desk


def _window_desk(connection: Any, desk_id: str, window_id: str, expected: int | None, *,
                 open_only: bool = True) -> tuple[dict, dict]:
    """The window and the desk the op names, its version checked. The version is the named desk's, never
    whichever desk holds the window now: a window that moved since the op was queued is a conflict naming
    the desk it was queued for and where the window is."""

    desk = _desk(connection, desk_id, expected)
    window = store.window(connection, window_id)
    if window is None:
        raise OpRefused("window_not_found", "Couldn’t find this window. Open it again.")
    if window["desk_id"] != desk_id:
        raise OpConflict({"desk_id": desk_id, "version": int(desk["version"]), "window_id": window_id,
                          "window_desk_id": window["desk_id"]})
    if open_only and window["closed_at"] is not None:
        raise OpRefused("window_closed", "This window is closed. Open it again.")
    return window, desk


def _apply_desk_op(connection: Any, op: Any, now: str, versions: dict[str, int]) -> dict[str, Any] | None:
    def bump(desk_id: str, **fields: Any) -> None:
        versions[desk_id] = store.update_desk(connection, desk_id, fields, now)

    if isinstance(op, CreateDesk):
        existing = store.desk(connection, op.desk_id)
        if existing is not None:
            raise OpConflict({"desk_id": op.desk_id, "version": int(existing["version"])})
        if op.expected_version not in (None, 0):
            raise OpRefused("validation_error", "Couldn’t create this desk. Reopen Reader and try again.")
        store.insert_desk(connection, desk_id=op.desk_id, title=op.title, position=op.position, goal_id=op.goal_id,
                          companion_dock=op.companion_dock, now=now)
        versions[op.desk_id] = 1
        return None
    if isinstance(op, (RenameDesk, ArchiveDesk, MoveDesk, SetDock, SetCompanionShown, SetGoal)):
        _desk(connection, op.desk_id, op.expected_version)
        if isinstance(op, RenameDesk):
            bump(op.desk_id, title=op.title)
        elif isinstance(op, ArchiveDesk):
            bump(op.desk_id, archived_at=now)
        elif isinstance(op, MoveDesk):
            bump(op.desk_id, position=op.position)
        elif isinstance(op, SetDock):
            bump(op.desk_id, companion_dock=op.dock)
        elif isinstance(op, SetCompanionShown):
            bump(op.desk_id, companion_shown=1 if op.shown else 0)
        else:
            bump(op.desk_id, goal_id=op.goal_id)
        return None
    if isinstance(op, SetFocus):
        _desk(connection, op.desk_id, op.expected_version)
        if op.window_id is not None:
            window = store.window(connection, op.window_id)
            if window is None or window["closed_at"] is not None or window["desk_id"] != op.desk_id:
                raise OpRefused("window_not_open", "Open this window on the desk before selecting it.")
        bump(op.desk_id, focus_window_id=op.window_id)
        return None
    if isinstance(op, OpenWindow):
        _desk(connection, op.desk_id, op.expected_version)
        if store.window(connection, op.window_id) is not None:
            raise OpRefused("window_exists", "This window already exists. Find it in the window list.")
        layout = _Layout(connection, op.desk_id)
        at = layout.index_of(op.after_window_id) + 1 if op.after_window_id else len(layout.slots)
        if op.stack is not None:
            kind, spec = "pad_stack", {"stack": [entry.wire() for entry in op.stack]}
        else:
            kind, spec = op.content.kind, {"content": op.content.wire()}  # type: ignore[union-attr]
        store.insert_window(connection, window_id=op.window_id, desk_id=op.desk_id, slot=len(layout.slots) + 1,
                            kind=kind, spec=spec, view=op.view, now=now)
        layout.slots.insert(at, [op.window_id])
        layout.write()
        bump(op.desk_id)
        return None
    if isinstance(op, CloseWindow):
        window, desk = _window_desk(connection, op.desk_id, op.window_id, op.expected_version)
        layout = _Layout(connection, desk["desk_id"])
        index = layout.index_of(op.window_id)
        layout.slots[index].remove(op.window_id)
        if not layout.slots[index]:
            del layout.slots[index]
        layout.active.discard(op.window_id)
        layout.write({op.window_id: {"closed_at": now, "pane": 0, "active": 1}})
        # A closed window cannot hold the focus; the client moves it on with set_focus.
        fields = {"focus_window_id": None} if desk["focus_window_id"] == op.window_id else {}
        bump(desk["desk_id"], **fields)
        return None
    if isinstance(op, ReopenWindow):
        window, desk = _window_desk(connection, op.desk_id, op.window_id, op.expected_version, open_only=False)
        if window["closed_at"] is None:
            raise OpRefused("window_open", "That window is already open.")
        layout = _Layout(connection, desk["desk_id"])
        at = min(op.slot if op.slot is not None else len(layout.slots), len(layout.slots))
        layout.slots.insert(at, [op.window_id])
        layout.write({op.window_id: {"closed_at": None}})
        bump(desk["desk_id"])
        return None
    if isinstance(op, MoveWindow):
        window, desk = _window_desk(connection, op.desk_id, op.window_id, op.expected_version)
        layout = _Layout(connection, desk["desk_id"])
        index = layout.index_of(op.window_id)
        slot = layout.slots.pop(index)
        layout.slots.insert(min(op.to_slot, len(layout.slots)), slot)
        layout.write()
        bump(desk["desk_id"])
        return None
    if isinstance(op, MoveToDesk):
        window, desk = _window_desk(connection, op.desk_id, op.window_id, op.expected_version)
        if op.to_desk_id == desk["desk_id"]:
            raise OpRefused("same_desk", "The window is already on that desk.")
        _desk(connection, op.to_desk_id, op.to_expected_version)
        source = _Layout(connection, desk["desk_id"])
        index = source.index_of(op.window_id)
        source.slots[index].remove(op.window_id)
        if not source.slots[index]:
            del source.slots[index]
        source.write()
        destination = _Layout(connection, op.to_desk_id)
        at = destination.index_of(op.after_window_id) + 1 if op.after_window_id else len(destination.slots)
        destination.slots.insert(at, [op.window_id])
        destination.active.add(op.window_id)
        destination.write()
        fields = {"focus_window_id": None} if desk["focus_window_id"] == op.window_id else {}
        bump(desk["desk_id"], **fields)
        bump(op.to_desk_id)
        return None
    if isinstance(op, Pair):
        window, desk = _window_desk(connection, op.desk_id, op.window_id, op.expected_version)
        layout = _Layout(connection, desk["desk_id"])
        index = layout.index_of(op.window_id)
        if len(layout.slots[index]) >= PAIR_SIZE:
            raise OpRefused("slot_full", "Choose a window next to an unstacked window and try again.")
        if index + 1 >= len(layout.slots):
            raise OpRefused("nothing_to_the_right", "Open a window on the right to stack these windows.")
        if len(layout.slots[index + 1]) >= PAIR_SIZE:
            raise OpRefused("slot_full", "Choose a window next to an unstacked window and try again.")
        neighbour = layout.slots.pop(index + 1)
        layout.slots[index].extend(neighbour)
        layout.active -= set(layout.slots[index])
        layout.active.add(op.window_id)
        layout.write()
        bump(desk["desk_id"])
        return None
    if isinstance(op, Unpair):
        window, desk = _window_desk(connection, op.desk_id, op.window_id, op.expected_version)
        layout = _Layout(connection, desk["desk_id"])
        index = layout.index_of(op.window_id)
        if len(layout.slots[index]) < PAIR_SIZE:
            raise OpRefused("not_paired", "This window already has its own space.")
        layout.slots[index].remove(op.window_id)
        layout.slots.insert(index + 1, [op.window_id])
        layout.write()
        bump(desk["desk_id"])
        return None
    if isinstance(op, SetActivePane):
        window, desk = _window_desk(connection, op.desk_id, op.window_id, op.expected_version)
        layout = _Layout(connection, desk["desk_id"])
        index = layout.index_of(op.window_id)
        if len(layout.slots[index]) < PAIR_SIZE:
            raise OpRefused("not_paired", "Choose a window in the stack.")
        layout.active -= set(layout.slots[index])
        layout.active.add(op.window_id)
        layout.write()
        bump(desk["desk_id"])
        return None
    if isinstance(op, (AddToStack, RemoveFromStack)):
        return _stack_membership(connection, op, now, bump)
    if isinstance(op, EnsureRunningPad):
        return _ensure_running_pad(connection, op, now, bump)
    if isinstance(op, SetView):
        window, desk = _window_desk(connection, op.desk_id, op.window_id, op.expected_version)
        store.update_window(connection, op.window_id, {"view_json": json.dumps(op.view, sort_keys=True)})
        bump(desk["desk_id"])
        return None
    raise OpRefused("unknown_op", f"Unknown desk op {getattr(op, 'op', None)!r}.")  # pragma: no cover


def _open_desk(connection: Any, desk_id: str) -> dict[str, Any]:
    desk = store.desk(connection, desk_id)
    if desk is None:
        raise OpRefused("desk_not_found", "Couldn’t find this desk. Open a desk and try again.")
    if desk["archived_at"] is not None:
        raise OpRefused("desk_archived", "This desk is archived. Open another desk.")
    return desk


def _same_entry(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return a.get("kind") == b.get("kind") and a.get("pad_id") == b.get("pad_id") and a.get("lesson_id") == b.get(
        "lesson_id")


def _stack_of(window: dict[str, Any]) -> list[dict[str, Any]]:
    return list((json.loads(window["spec_json"] or "{}") or {}).get("stack") or [])


def _write_stack(connection: Any, window_id: str, stack: list[dict[str, Any]]) -> None:
    store.update_window(connection, window_id, {"spec_json": json.dumps({"stack": stack}, sort_keys=True)})


def _stack_membership(connection: Any, op: AddToStack | RemoveFromStack, now: str, bump: Any) -> dict[str, Any]:
    """A stack's membership changed by one entry, whatever else changed on the desk meanwhile: the stack lives in
    the window's spec, apart from its view, so a whole-view write never drops a tab, and a union or a removal of one
    entry is the same at any desk version."""

    _open_desk(connection, op.desk_id)
    window = store.window(connection, op.window_id)
    if window is None or window["desk_id"] != op.desk_id:
        raise OpRefused("window_not_found", "Couldn’t find this window on the desk. Open it again.")
    if window["kind"] != "pad_stack":
        raise OpRefused("not_a_stack", "Choose a stack of pads and try again.")
    entry = op.entry.wire()
    if entry.get("kind") == "pad" and pad_reads.pad(connection, str(entry["pad_id"])) is None:
        raise OpRefused("pad_not_found", "Couldn’t find this pad. Open it again.")
    stack = _stack_of(window)
    present = any(_same_entry(existing, entry) for existing in stack)
    changed = False
    if isinstance(op, AddToStack) and not present:
        stack.append(entry)
        changed = True
    elif isinstance(op, RemoveFromStack) and present:
        remaining = [existing for existing in stack if not _same_entry(existing, entry)]
        if not remaining:
            raise OpRefused("last_in_stack", "This is the last pad in the stack. Close the window to close it.")
        stack, changed = remaining, True
    if changed:
        _write_stack(connection, op.window_id, stack)
    bump(op.desk_id)
    return {"changed": changed, "stack": stack}


def _ensure_running_pad(connection: Any, op: EnsureRunningPad, now: str, bump: Any) -> dict[str, Any]:
    """The desk's running pad, and a stack window of the desk holding it: whichever is missing is created."""

    _open_desk(connection, op.desk_id)
    running = pad_reads.running_pad_ids(connection, op.desk_id)
    created_pad = not running
    if created_pad:
        if pad_reads.pad(connection, op.pad_id) is not None:
            raise OpRefused("id_collision", "This pad already exists. Find it in the window list.")
        pad_store.insert_pad(connection, pad_id=op.pad_id, kind="running", title=op.title, home_desk_id=op.desk_id,
                             workbench_session_id=None, lesson_id=None, now=now)
        running = [op.pad_id]
    pad_id = running[0]
    entry = {"kind": "pad", "pad_id": pad_id}
    stacks = [row for row in store.open_windows(connection, op.desk_id) if row["kind"] == "pad_stack"]
    holding = next((row for row in stacks if any(_same_entry(existing, entry) for existing in _stack_of(row))), None)
    created_window = added = False
    if holding is not None:
        window_id = holding["window_id"]
    elif stacks:
        window_id = stacks[0]["window_id"]
        _write_stack(connection, window_id, [*_stack_of(stacks[0]), entry])
        added = True
    else:
        if store.window(connection, op.window_id) is not None:
            raise OpRefused("window_exists", "This window already exists. Find it in the window list.")
        layout = _Layout(connection, op.desk_id)
        store.insert_window(connection, window_id=op.window_id, desk_id=op.desk_id, slot=len(layout.slots) + 1,
                            kind="pad_stack", spec={"stack": [entry]}, view={}, now=now)
        layout.slots.append([op.window_id])
        layout.write()
        window_id, created_window = op.window_id, True
    bump(op.desk_id)
    return {"pad_id": pad_id, "window_id": window_id, "created_pad": created_pad, "created_window": created_window,
            "added_to_stack": added}


def apply_desk_ops(repository: Any, *, client_id: str, seq: int, ops: list[Any], clock: Any = None,
                   check_material: Callable[[], None] | None = None) -> dict[str, Any]:
    """``desk.apply``: one batch, applied once and in order (``learnloop.desks.protocol``)."""

    request = {"ops": [op.wire() for op in ops]}

    def apply(connection: Any, now: str) -> dict[str, Any]:
        if check_material:
            check_material()
        versions: dict[str, int] = {}
        results = [run_op(connection, lambda op=op: _apply_desk_op(connection, op, now, versions)) for op in ops]
        return {"results": results,
                "versions": [{"desk_id": desk_id, "version": version} for desk_id, version in sorted(versions.items())]}

    return apply_batch(repository, channel=DESK, client_id=client_id, seq=seq, request=request, apply_ops=apply,
                       clock=clock)


__all__ = ["DESK_OPS", "DOCKS", "DeskOp", "PAIR_SIZE", "apply_desk_ops", "desk_state"]
