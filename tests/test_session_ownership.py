"""Mobile PR-4: atomic session operations and ownership (G10's PR-4 clauses).

``spec_mobile_tailnet_v1`` §6.5. Each operation is one ``BEGIN IMMEDIATE``
transaction shared by the desktop sidecar and the phone host:

* interleaved starts from two writers leave exactly one open session (before
  PR-4 the start created its session and ended the others in two commits, so
  two starts could end each other);
* a session another device owns is never ended silently
  (``session_open_elsewhere``); a stale ``replace`` is refused, and starting
  fresh keeps the replaced draft in ``session_handoffs``;
* ``adopt_session`` is a compare-and-swap on ``owner_generation`` that carries
  the session id and the checkpoint;
* every session-scoped write from a device that no longer owns the session
  fails with ``session_moved`` and writes nothing; reads stay open.

The phone host does not exist yet (M2), so the other device here is a second
``Repository`` acting as one (``owner_device_id = dev_phone``); the desktop is
the sidecar, whose requests come from the desktop (NULL) until PR-5.

Durability lane: production pragmas and WAL on fresh vaults.
"""

from __future__ import annotations

import multiprocessing
import sqlite3
import threading
import traceback
from pathlib import Path

import pytest

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.db.repositories import Repository
from learnloop.db.stores.session_ownership import SessionOwnershipError
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import create_basic_vault

pytestmark = pytest.mark.durability

ITEM = "pi_svd_define_001"
PHONE = "dev_phone"
TABLET = "dev_tablet"


def _call(ctx: SidecarContext, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _vault(tmp_path: Path):
    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    repository = Repository(paths.sqlite_path)
    with repository.connection() as connection:
        for device_id, label in ((PHONE, "Phone"), (TABLET, "Tablet")):
            connection.execute(
                "INSERT INTO mobile_devices (id, label, scope, token_hash, created_at) "
                "VALUES (?, ?, 'app', ?, '2026-10-27T00:00:00Z')",
                (device_id, label, f"hash-{device_id}"),
            )
        connection.commit()
    return paths, repository


def _desktop(paths) -> SidecarContext:
    ctx = SidecarContext()
    ctx.load_secondary(paths.root)
    ctx.grading_provider_override = "manual"
    return ctx


def _open_sessions(repository: Repository) -> list[dict]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM sessions WHERE ended_at IS NULL")]


def _draft(repository: Repository, session_id: str, answer: str = "First line of my draft\nsecond line") -> None:
    repository.update_session_checkpoint(session_id, current_practice_item_id=ITEM, current_answer=answer)


# -- starts ----------------------------------------------------------------


def test_interleaved_starts_from_two_writers_leave_exactly_one_open_session(tmp_path, monkeypatch):
    """The fail-first interleaving: the first start pauses right after creating
    its session. Before PR-4 the second start created its own session and the
    two then ended each other (no session open); now the second waits for the
    first's transaction and ends the first's session."""

    paths, _repository = _vault(tmp_path)
    original = Repository.create_session
    first_created = threading.Event()
    second_reached_create = threading.Event()
    calls = {"n": 0}
    lock = threading.Lock()

    def create_then_pause(self, **kwargs):
        session_id = original(self, **kwargs)
        with lock:
            calls["n"] += 1
            order = calls["n"]
        if order == 1:
            first_created.set()
            # Give the second start every chance to interleave.
            second_reached_create.wait(timeout=1.0)
        else:
            second_reached_create.set()
        return session_id

    monkeypatch.setattr(Repository, "create_session", create_then_pause)
    started: dict[str, dict] = {}
    errors: list[BaseException] = []

    def start(name: str) -> None:
        try:
            if name == "second":
                first_created.wait(timeout=10)
            started[name] = _call(_desktop(paths), "start_session", {"availableMinutes": 25})
        except BaseException as error:  # noqa: BLE001 - reported below
            errors.append(error)

    threads = [threading.Thread(target=start, args=(name,)) for name in ("first", "second")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert not any(thread.is_alive() for thread in threads)
    assert errors == []

    open_sessions = _open_sessions(Repository.attach(paths.sqlite_path))
    assert [row["id"] for row in open_sessions] == [started["second"]["sessionId"]]


def _start_in_process(sqlite_path: str, device_id, barrier, pipe) -> None:
    try:
        repository = Repository.attach(Path(sqlite_path))
        ids = []
        for _ in range(5):
            barrier.wait(timeout=30)
            ids.append(repository.start_session_exclusive({"available_minutes": 10}, device_id))
        pipe.send(("ok", ids))
    except BaseException:  # noqa: BLE001 - reported to the parent
        pipe.send(("error", traceback.format_exc()))
    finally:
        pipe.close()


def test_concurrent_starts_from_two_processes_of_one_device_keep_one_open_session(tmp_path):
    paths, repository = _vault(tmp_path)
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(2)
    processes, pipes = [], []
    for _ in range(2):
        parent, child = context.Pipe()
        process = context.Process(target=_start_in_process, args=(str(paths.sqlite_path), None, barrier, child))
        process.start()
        child.close()
        processes.append(process)
        pipes.append(parent)
    try:
        for parent in pipes:
            assert parent.poll(120), "a starting process did not reply"
            reply = parent.recv()
            assert reply[0] == "ok", reply
        for process in processes:
            process.join(timeout=10)
            assert process.exitcode == 0
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
    assert len(_open_sessions(repository)) == 1


def test_a_start_from_another_device_never_ends_the_open_session_silently(tmp_path):
    paths, repository = _vault(tmp_path)
    desktop = _call(_desktop(paths), "start_session", {"availableMinutes": 25})["sessionId"]
    _draft(repository, desktop)

    with pytest.raises(SessionOwnershipError) as refused:
        repository.start_session_exclusive({"available_minutes": 10}, PHONE)
    assert refused.value.code == "session_open_elsewhere"
    assert refused.value.details == {
        "session_id": desktop,
        "started_at": repository.fetch_session(desktop)["started_at"],
        "owner_device_id": None,
        "owner_label": "desktop",
        "owner_generation": 0,
        "current_practice_item_id": ITEM,
        "has_draft": True,
        "draft_first_line": "First line of my draft",
    }
    # A stale replace (any id but the open session's) is refused the same way.
    with pytest.raises(SessionOwnershipError) as stale:
        repository.start_session_exclusive({"available_minutes": 10}, PHONE, replace="not-the-open-session")
    assert stale.value.code == "session_open_elsewhere"
    assert [row["id"] for row in _open_sessions(repository)] == [desktop]
    assert repository.session_handoffs(desktop) == []


def test_starting_fresh_keeps_the_replaced_draft_and_ends_that_session(tmp_path):
    paths, repository = _vault(tmp_path)
    desktop = _call(_desktop(paths), "start_session", {"availableMinutes": 25})["sessionId"]
    _draft(repository, desktop)
    checkpoint = repository.fetch_session_checkpoint(desktop)

    phone = repository.start_session_exclusive({"available_minutes": 10}, PHONE, replace=desktop)

    assert [row["id"] for row in _open_sessions(repository)] == [phone]
    assert repository.fetch_session(phone)["owner_device_id"] == PHONE
    assert repository.fetch_session(desktop)["ended_at"] is not None
    [handoff] = repository.session_handoffs(desktop)
    assert (handoff["kind"], handoff["from_device_id"], handoff["to_device_id"], handoff["generation"]) == (
        "replace", None, PHONE, 0
    )
    assert handoff["checkpoint"]["current_answer"] == checkpoint["current_answer"]
    assert handoff["checkpoint"]["current_practice_item_id"] == ITEM
    # The receipt is append-only.
    with repository.connection() as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute("UPDATE session_handoffs SET kind = 'adopt'")


def test_a_device_replaces_its_own_session_silently(tmp_path):
    _paths, repository = _vault(tmp_path)
    first = repository.start_session_exclusive({"available_minutes": 10}, PHONE)
    second = repository.start_session_exclusive({"available_minutes": 10}, PHONE)

    assert [row["id"] for row in _open_sessions(repository)] == [second]
    assert repository.fetch_session(first)["ended_at"] is not None
    assert repository.session_handoffs(first) == []


# -- adopt ------------------------------------------------------------------


def test_adopt_is_a_compare_and_swap_that_carries_the_session_and_its_checkpoint(tmp_path):
    paths, repository = _vault(tmp_path)
    desktop = _call(_desktop(paths), "start_session", {"availableMinutes": 25})["sessionId"]
    _draft(repository, desktop)
    checkpoint = repository.fetch_session_checkpoint(desktop)

    adopted = repository.adopt_session(desktop, PHONE, 0)

    assert (adopted["session_id"], adopted["owner_device_id"], adopted["owner_label"], adopted["owner_generation"]) == (
        desktop, PHONE, "Phone", 1
    )
    assert repository.fetch_session_checkpoint(desktop) == checkpoint
    [handoff] = repository.session_handoffs(desktop)
    assert (handoff["kind"], handoff["from_device_id"], handoff["to_device_id"], handoff["generation"]) == (
        "adopt", None, PHONE, 1
    )
    # A stale generation (the tablet read generation 0) is refused with the owner.
    with pytest.raises(SessionOwnershipError) as stale:
        repository.adopt_session(desktop, TABLET, 0)
    assert stale.value.code == "session_moved"
    assert stale.value.details == {
        "session_id": desktop, "owner_device_id": PHONE, "owner_label": "Phone", "owner_generation": 1,
    }
    # The phone's retried adopt changes nothing.
    assert repository.adopt_session(desktop, PHONE, 0)["owner_generation"] == 1
    assert len(repository.session_handoffs(desktop)) == 1
    # The desktop adopts it back with the current generation.
    assert repository.adopt_session(desktop, None, 1)["owner_generation"] == 2


def test_adopting_never_loses_a_draft_on_an_item_the_device_cannot_answer(tmp_path):
    paths, repository = _vault(tmp_path)
    desktop = _call(_desktop(paths), "start_session", {"availableMinutes": 25})["sessionId"]
    _draft(repository, desktop)

    with pytest.raises(SessionOwnershipError) as refused:
        repository.adopt_session(desktop, PHONE, 0, current_item_ineligible=lambda item_id: item_id == ITEM)
    assert refused.value.code == "current_item_desktop_only"
    assert repository.fetch_session(desktop)["owner_device_id"] is None
    assert repository.session_handoffs(desktop) == []

    # With no draft the item is simply not shown on the phone: the adopt proceeds.
    _draft(repository, desktop, answer="  ")
    assert repository.adopt_session(
        desktop, PHONE, 0, current_item_ineligible=lambda item_id: True
    )["owner_device_id"] == PHONE


def test_two_devices_adopting_at_once_leave_one_owner(tmp_path):
    paths, repository = _vault(tmp_path)
    desktop = _call(_desktop(paths), "start_session", {"availableMinutes": 25})["sessionId"]
    barrier = threading.Barrier(2)
    outcomes: dict[str, str] = {}

    def adopt(device_id: str) -> None:
        barrier.wait(timeout=10)
        try:
            Repository.attach(paths.sqlite_path).adopt_session(desktop, device_id, 0)
            outcomes[device_id] = "adopted"
        except SessionOwnershipError as error:
            outcomes[device_id] = error.code

    threads = [threading.Thread(target=adopt, args=(device,)) for device in (PHONE, TABLET)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert sorted(outcomes.values()) == ["adopted", "session_moved"]
    winner = next(device for device, outcome in outcomes.items() if outcome == "adopted")
    session = repository.fetch_session(desktop)
    assert (session["owner_device_id"], session["owner_generation"]) == (winner, 1)
    assert len(repository.session_handoffs(desktop)) == 1


# -- ownership on writes ----------------------------------------------------

_SUBMISSION = "sub_desktop_draft_1"

_WRITES = (
    ("update_session_checkpoint", {"currentAnswer": "a later desktop edit"}),
    ("clear_session_checkpoint", {}),
    ("save_practice_draft", {"practiceItemId": ITEM, "answerMd": "a later desktop edit"}),
    ("skip_practice_item", {"practiceItemId": ITEM}),
    ("submit_attempt", {"practiceItemId": ITEM, "answerMd": "an answer", "attemptType": "independent_attempt",
                        "selfGrade": {"criterionPoints": {"correctness": 4}, "confidence": 4}}),
    ("submit_dont_know", {"practiceItemId": ITEM}),
    ("acknowledge_practice_submission", {"practiceItemId": ITEM, "submissionId": _SUBMISSION}),
    ("end_session", {}),
)


@pytest.mark.parametrize(("method_name", "params"), _WRITES, ids=[name for name, _ in _WRITES])
def test_every_session_scoped_write_from_the_old_owner_is_session_moved(tmp_path, method_name, params):
    paths, repository = _vault(tmp_path)
    ctx = _desktop(paths)
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    _call(ctx, "save_practice_draft", {"sessionId": session_id, "practiceItemId": ITEM,
                                       "answerMd": "my draft", "submissionId": _SUBMISSION})
    repository.adopt_session(session_id, PHONE, 0)
    checkpoint = repository.fetch_session_checkpoint(session_id)
    with repository.connection() as connection:
        attempts = connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()[0]

    with pytest.raises(SidecarError) as moved:
        _call(ctx, method_name, {"sessionId": session_id, **params})

    assert moved.value.code == "session_moved"
    assert moved.value.retryable is False
    assert moved.value.details == {
        "session_id": session_id, "owner_device_id": PHONE, "owner_label": "Phone", "owner_generation": 1,
    }
    # Nothing was written: the phone's session, checkpoint and attempts stand.
    assert repository.fetch_session(session_id)["ended_at"] is None
    assert repository.fetch_session_checkpoint(session_id) == checkpoint
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()[0] == attempts
    # Reads stay unrestricted.
    assert _call(ctx, "get_session", {"sessionId": session_id})["sessionId"] == session_id


def test_the_owner_writes_as_before_and_ended_sessions_keep_their_old_errors(tmp_path):
    paths, repository = _vault(tmp_path)
    ctx = _desktop(paths)
    session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]

    assert _call(ctx, "update_session_checkpoint", {"sessionId": session_id, "currentAnswer": "x"}) == {"ok": True}
    assert repository.fetch_session_checkpoint(session_id)["current_answer"] == "x"
    ended = _call(ctx, "end_session", {"sessionId": session_id})
    assert ended["sessionId"] == session_id
    # Ending again returns the same end, as it always did.
    assert _call(ctx, "end_session", {"sessionId": session_id})["endedAt"] == ended["endedAt"]
    with pytest.raises(SidecarError) as closed:
        _call(ctx, "update_session_checkpoint", {"sessionId": session_id, "currentAnswer": "y"})
    assert (closed.value.code, closed.value.message) == ("validation_error", f"Session {session_id} has ended.")
    with pytest.raises(SidecarError) as missing:
        _call(ctx, "end_session", {"sessionId": "no-such-session"})
    assert (missing.value.code, missing.value.message) == ("not_found", "Session no-such-session was not found.")


def test_the_desktop_start_reports_a_phone_session_instead_of_ending_it(tmp_path):
    paths, repository = _vault(tmp_path)
    phone = repository.start_session_exclusive({"available_minutes": 10}, PHONE)

    with pytest.raises(SidecarError) as elsewhere:
        _call(_desktop(paths), "start_session", {"availableMinutes": 25})

    assert elsewhere.value.code == "session_open_elsewhere"
    assert elsewhere.value.details["session_id"] == phone
    assert elsewhere.value.details["owner_label"] == "Phone"
    assert [row["id"] for row in _open_sessions(repository)] == [phone]
