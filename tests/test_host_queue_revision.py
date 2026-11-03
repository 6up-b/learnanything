"""Mobile PR-7: the host bumps ``queue_revision`` (spec_mobile_tailnet_v1 §3.3, G12).

Attempts and session rows carry no revision of their own, so a committed mutation
from the phone tells the desktop through this counter. The M2 host does not exist
yet, so the host here is a sidecar context acting as a paired device: the bump lives
on the shared handlers (``request_origin.host_mutation``), which the host will call.
Desktop-originated writes keep today's behaviour: no origin, no bump.

Durability lane: production pragmas and WAL, a real second process, and the desktop's
own read of the revision and of its session after a phone adopted it.
"""

from __future__ import annotations

import multiprocessing
import sqlite3
import traceback
from pathlib import Path

import pytest

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.db.repositories import Repository
from learnloop_sidecar.context import SidecarContext, session_snapshot
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY
from learnloop_sidecar.request_origin import RequestOrigin, bump_for_host, host_mutation

from tests.helpers import add_followup_item, create_basic_vault, seed_due_item

pytestmark = pytest.mark.durability

ITEM = "pi_svd_define_001"
SECOND_ITEM = "pi_svd_define_002"
PHONE = RequestOrigin(device_id="dev_phone")
SELF_GRADE = {"criterionPoints": {"correctness": 4}, "confidence": 4}


def _call(ctx: SidecarContext, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _world(tmp_path):
    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    repository = seed_due_item(paths)
    add_followup_item(paths.root, SECOND_ITEM)
    repository.upsert_practice_item_state(
        SECOND_ITEM, difficulty=5.0, stability=2.0, due_at="2026-05-18T12:00:00Z",
        last_attempt_at="2026-05-16T12:00:00Z", active=True,
    )
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO mobile_devices (id, label, scope, token_hash, created_at) "
            "VALUES (?, 'Phone', 'app', 'hash', '2026-11-03T00:00:00Z')",
            (PHONE.device_id,),
        )
        connection.commit()
    ctx = _context(paths.root)
    return paths, repository, ctx


def _context(root: Path) -> SidecarContext:
    ctx = SidecarContext()
    ctx.load_secondary(root)
    ctx.grading_provider_override = "manual"
    return ctx


def _revision(repository: Repository) -> int:
    return repository.queue_revision()["revision"]


def _submit(ctx, session_id, item=ITEM, **extra):
    return _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": item, "answerMd": "an answer",
        "attemptType": "independent_attempt", "selfGrade": SELF_GRADE, **extra,
    })


# -- what bumps ------------------------------------------------------------


def test_each_committed_phone_mutation_bumps_once_and_is_visible_with_it(tmp_path):
    """Job completion, skip, session start, adopt and end (§3.3)."""

    _paths, repository, ctx = _world(tmp_path)
    reader = Repository(repository.sqlite_path)

    def bumped(name, params):
        before = _revision(reader)
        with ctx.acting_as(PHONE):
            result = _call(ctx, name, params)
        assert _revision(reader) == before + 1, name
        return result

    session_id = bumped("start_session", {"availableMinutes": 20})["sessionId"]
    assert reader.fetch_session(session_id)["owner_device_id"] == PHONE.device_id

    attempt = bumped("submit_attempt", {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": "an answer",
        "attemptType": "independent_attempt", "selfGrade": SELF_GRADE, "submissionId": "sub-1",
    })
    assert reader.fetch_practice_attempt(attempt["attemptId"]) is not None

    bumped("submit_dont_know", {"sessionId": session_id, "practiceItemId": SECOND_ITEM, "submissionId": "sub-2"})
    bumped("skip_practice_item", {"sessionId": session_id, "practiceItemId": ITEM})
    bumped("end_session", {"sessionId": session_id})


def test_adopting_and_ending_a_desktop_session_bump(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]

    before = _revision(repository)
    with ctx.acting_as(PHONE):
        _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": 0})
    assert _revision(repository) == before + 1


def test_a_clarification_job_completing_on_the_phone_bumps(tmp_path, monkeypatch):
    """The other long job on the M2 allowlist. A window that has closed is a typed
    refusal and changes nothing; an answer that lands bumps."""

    import learnloop.attempts.clarification as clarification

    _paths, repository, ctx = _world(tmp_path)
    with ctx.acting_as(PHONE):
        session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
        attempt = _submit(ctx, session_id, submissionId="sub-1")
        before = _revision(repository)
        with pytest.raises(SidecarError) as closed:
            _call(ctx, "answer_grading_clarification", {"attemptId": attempt["attemptId"], "answerMd": "because"})
        assert closed.value.code == "clarification_unanswerable"
        assert _revision(repository) == before

        monkeypatch.setattr(
            clarification, "answer_clarification",
            lambda *_args, **_kwargs: {"clarification_id": "c1", "outcome": "resolved", "regraded": True},
        )
        _call(ctx, "answer_grading_clarification", {"attemptId": attempt["attemptId"], "answerMd": "because"})
    assert _revision(repository) == before + 1


# -- what does not ------------------------------------------------------------


def test_the_desktops_own_writes_keep_todays_behaviour(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    before = _revision(repository)
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _submit(ctx, session_id, submissionId="sub-1")
    _call(ctx, "skip_practice_item", {"sessionId": session_id, "practiceItemId": SECOND_ITEM})
    _call(ctx, "end_session", {"sessionId": session_id})
    assert _revision(repository) == before


def test_a_read_a_draft_or_a_checkpoint_on_the_phone_does_not_bump(tmp_path):
    """Only what changes what the desktop shows (§3.3): a phone's reads and its draft
    autosaves would otherwise refetch Today on the desktop for nothing."""

    _paths, repository, ctx = _world(tmp_path)
    with ctx.acting_as(PHONE):
        session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
        before = _revision(repository)
        _call(ctx, "get_today_queue", {"sessionId": session_id})
        _call(ctx, "get_session", {"sessionId": session_id})
        _call(ctx, "open_queue_item", {"practiceItemId": ITEM})
        _call(ctx, "get_practice_item", {"practiceItemId": ITEM, "sessionId": session_id})
        _call(ctx, "save_practice_draft", {"sessionId": session_id, "practiceItemId": ITEM, "answerMd": "half"})
        _call(ctx, "update_session_checkpoint", {"sessionId": session_id, "currentAnswer": "half more"})
        _call(ctx, "clear_session_checkpoint", {"sessionId": session_id})
    assert _revision(repository) == before


def test_a_refused_mutation_does_not_bump(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    before = _revision(repository)
    with ctx.acting_as(PHONE):
        # The desktop still owns it, so each of these is refused and writes nothing.
        with pytest.raises(SidecarError) as elsewhere:
            _call(ctx, "skip_practice_item", {"sessionId": session_id, "practiceItemId": ITEM})
        assert elsewhere.value.code == "session_moved"
        with pytest.raises(SidecarError):
            _submit(ctx, session_id)
        with pytest.raises(SidecarError):
            _call(ctx, "end_session", {"sessionId": session_id})
        with pytest.raises(SidecarError) as stale:
            _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": 9})
        assert stale.value.code == "session_moved"
    assert _revision(repository) == before


# -- the helper's edges -----------------------------------------------------


def test_a_committed_refusal_bumps_and_any_other_refusal_does_not(tmp_path):
    _paths, repository, ctx = _world(tmp_path)

    @host_mutation
    def committed(_ctx, _params):
        raise SidecarError("submission_committed", "The attempt is in; its feedback is not.")

    @host_mutation
    def refused(_ctx, _params):
        raise SidecarError("validation_error", "No.")

    before = _revision(repository)
    with ctx.acting_as(PHONE):
        with pytest.raises(SidecarError):
            committed(ctx, None)
        assert _revision(repository) == before + 1
        with pytest.raises(SidecarError):
            refused(ctx, None)
    assert _revision(repository) == before + 1
    with pytest.raises(SidecarError):
        committed(ctx, None)
    assert _revision(repository) == before + 1


def test_a_failed_bump_never_fails_the_committed_mutation(tmp_path, monkeypatch):
    _paths, repository, ctx = _world(tmp_path)
    _vault, context_repository = ctx.require_vault()

    def locked(*_args, **_kwargs):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(context_repository, "bump_queue_revision", locked)
    with ctx.acting_as(PHONE):
        session = _call(ctx, "start_session", {"availableMinutes": 20})
    assert repository.fetch_session(session["sessionId"])["owner_device_id"] == PHONE.device_id


def test_bump_for_host_is_the_desktops_no_op(tmp_path):
    _paths, repository, ctx = _world(tmp_path)
    before = _revision(repository)
    bump_for_host(ctx)
    assert _revision(repository) == before
    with ctx.acting_as(PHONE):
        bump_for_host(ctx)
    assert _revision(repository) == before + 1


# -- the desktop's side --------------------------------------------------------


def test_a_desktop_session_reply_is_unchanged_until_the_session_leaves_it(tmp_path):
    """Byte-identical for a session that never left, and the owner once one has."""

    _paths, repository, ctx = _world(tmp_path)
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    plain = _call(ctx, "get_session", {"sessionId": session_id})
    assert set(plain) == {
        "version", "sessionId", "startedAt", "endedAt", "energy", "sleepQuality", "availableMinutes", "notesMdPath",
        "checkpoint",
    }

    with ctx.acting_as(PHONE):
        _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": 0})
    moved = session_snapshot(repository, session_id)
    assert (moved["ownerDeviceId"], moved["ownerLabel"], moved["ownerGeneration"]) == (PHONE.device_id, "Phone", 1)

    _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": 1})
    back = _call(ctx, "get_session", {"sessionId": session_id})
    assert (back["ownerDeviceId"], back["ownerLabel"], back["ownerGeneration"]) == (None, "desktop", 2)


def test_the_revision_poll_says_when_it_reloaded_and_only_then(tmp_path, monkeypatch):
    _paths, _repository, ctx = _world(tmp_path)
    awaiting = ["job_1"]
    marked: list[str] = []
    reloads: list[bool] = []

    monkeypatch.setattr(
        ctx.ingest_jobs, "completed_jobs_awaiting_reload",
        lambda job_types, *, limit: [job for job in awaiting if job not in marked],
    )
    monkeypatch.setattr(ctx.ingest_jobs, "mark_reloaded", marked.append)
    monkeypatch.setattr(ctx, "reload", lambda **kwargs: reloads.append(True))

    first = _call(ctx, "get_queue_revision", {})
    second = _call(ctx, "get_queue_revision", {})

    assert first["reloaded"] is True and "reloaded" not in second
    assert set(second) == {"version", "revision", "updatedAt"}
    assert reloads == [True] and marked == ["job_1"]


def _phone_process(root: str, session_id: str, rounds: int, queue) -> None:
    try:
        ctx = _context(Path(root))
        with ctx.acting_as(PHONE):
            for _ in range(rounds):
                bump_for_host(ctx)
            _call(ctx, "adopt_session", {"sessionId": session_id, "expectedGeneration": 0})
        queue.put(None)
    except Exception:  # noqa: BLE001 - reported to the parent
        queue.put(traceback.format_exc())


def test_a_second_process_loses_no_bump_and_the_desktop_sees_the_session_move(tmp_path):
    """G12 on the desktop's side: its own context reads the revision change a real
    second process committed, and then the session has moved, with no restart. Its
    writes are refused while it polls: the revision is the only thing that moved."""

    paths, repository, ctx = _world(tmp_path)
    session_id = _call(ctx, "start_session", {"availableMinutes": 20})["sessionId"]
    _call(ctx, "update_session_checkpoint", {"sessionId": session_id, "currentAnswer": "my draft"})
    seen = _revision(repository)
    assert "ownerDeviceId" not in _call(ctx, "get_session", {"sessionId": session_id})

    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    rounds = 20
    process = context.Process(target=_phone_process, args=(str(paths.root), session_id, rounds, queue))
    process.start()
    # The desktop keeps writing what it may (the counter too) while the phone bumps.
    local_bumps = 0
    while process.is_alive() and local_bumps < rounds:
        repository.bump_queue_revision()
        local_bumps += 1
    process.join(timeout=120)
    assert queue.get(timeout=5) is None and process.exitcode == 0

    # Every bump landed: the phone's 20 and its adopt's one, and the desktop's.
    assert _revision(repository) == seen + rounds + 1 + local_bumps
    snapshot = _call(ctx, "get_session", {"sessionId": session_id})
    assert (snapshot["ownerDeviceId"], snapshot["ownerLabel"]) == (PHONE.device_id, "Phone")
    assert repository.fetch_session_checkpoint(session_id)["current_answer"] == "my draft"
    with pytest.raises(SidecarError) as moved:
        _call(ctx, "update_session_checkpoint", {"sessionId": session_id, "currentAnswer": "a later edit"})
    assert moved.value.code == "session_moved"
