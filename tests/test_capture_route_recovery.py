"""Destination receipts survive a lost response, failed route write and restart."""
from __future__ import annotations

import pytest

from learnloop.capture import get_capture
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers import capture as capture_rpc
from learnloop_sidecar.handlers import item_authoring, ingest, tutor_qa
from tests.test_capture_desktop import _capture, _context
from tests.test_sidecar_quick_add import _seed_extraction
from tests.test_sidecar_tutor_qa import _TutorServer, _tutor_vault


@pytest.fixture(params=["card", "quick_add", "tutor"])
def destination(request, tmp_path, monkeypatch):
    server = _TutorServer()
    server.start()
    root, paths = _tutor_vault(tmp_path, server)
    route = request.param
    url = "https://example.org/book"
    if route == "quick_add":
        _seed_extraction(paths.sqlite_path, url)
    repo, capture_id = _capture(root, url=url if route == "quick_add" else None)
    ctx = _context(root)
    monkeypatch.setattr(ctx.ingest_jobs, "_ensure_worker", lambda: None)
    if route == "card":
        handler, module = item_authoring.author_practice_item, item_authoring
        params = item_authoring.AuthorPracticeItemInput(
            capture_id=capture_id, learning_object_id="lo_svd_definition",
            prompt="Why eigenvectors?", expected_answer="Invariant directions.",
        )
    elif route == "quick_add":
        handler, module = ingest.confirm_quick_add_rpc, capture_rpc
        params = ingest.ConfirmQuickAddInput(
            capture_id=capture_id, source=url, subject_id="linear-algebra",
        )
    else:
        handler, module = tutor_qa.ask_tutor_question, tutor_qa
        params = tutor_qa.AskTutorQuestionInput(
            capture_id=capture_id, subject_id="linear-algebra",
            context="library", question="Why eigenvectors?",
        )
    try:
        yield route, root, repo, capture_id, ctx, handler, module, params, server
    finally:
        server.stop()


def _assert_single(route, root, repo, result, server):
    if route == "card":
        cards = load_vault(root).practice_items
        assert result["practiceItemId"] in cards
        assert len(cards) == 2
    elif route == "quick_add":
        with repo.connection() as conn:
            assert conn.execute("SELECT count(*) FROM ingest_batches").fetchone()[0] == 1
            assert conn.execute("SELECT count(*) FROM ingest_jobs").fetchone()[0] == 2
        assert repo.get_ingest_batch(result["quickAdd"]["batchId"])
    else:
        events = repo.question_events(context="library", note_id=result["noteId"])
        assert [event["id"] for event in events] == [result["eventId"]]
        assert len([r for r in server.requests if r["path"] == "/tutor-qa"]) == 1


@pytest.mark.parametrize("failure", ["lost_response", "route_write", "receipt_write", "crash_gap"])
def test_destination_retry_recovers_one_result(destination, monkeypatch, failure):
    route, root, repo, capture_id, ctx, handler, module, params, server = destination
    class Crash(BaseException):
        pass

    with monkeypatch.context() as patch:
        if failure == "route_write":
            def fail(*args, **kwargs):
                raise OSError("route commit failed")
            patch.setattr(capture_rpc, "record_route", fail)
        elif failure == "receipt_write":
            original = capture_rpc.update_route_intent
            def fail(*args, **kwargs):
                if "response" in kwargs:
                    raise OSError("response commit failed")
                return original(*args, **kwargs)
            patch.setattr(capture_rpc, "update_route_intent", fail)
        elif failure == "crash_gap":
            def fail(*args, **kwargs):
                raise Crash()
            patch.setattr(module, "finish_route", fail)
        if failure == "crash_gap":
            with pytest.raises(Crash):
                handler(ctx, params)
            first = None
        else:
            first = handler(ctx, params)
            if failure in ("route_write", "receipt_write"):
                assert first["captureRoutePending"] is True
                assert get_capture(repo, capture_id)["status"] == "new"
    # A new sidecar snapshot and repository, not an in-memory retry cache.
    ctx.reload(maintenance=False)
    result = handler(ctx, params)
    assert get_capture(repo, capture_id)["status"] == "routed"
    if first is not None:
        assert result == {k: v for k, v in first.items() if k != "captureRoutePending"}
    assert handler(ctx, params) == result
    _assert_single(route, root, repo, result, server)


def test_reload_failure_is_truthful_and_retry_safe(destination, monkeypatch):
    route, root, repo, capture_id, ctx, handler, module, params, server = destination
    def fail(*args, **kwargs):
        raise RuntimeError("snapshot refresh failed")
    with monkeypatch.context() as patch:
        patch.setattr(ctx, "reload", fail)
        if route == "tutor":
            # The only tutor reload is before asking, after creating the note.
            with pytest.raises(RuntimeError, match="snapshot refresh"):
                handler(ctx, params)
            assert get_capture(repo, capture_id)["status"] == "new"
            assert repo.question_events(context="library") == []
        else:
            result = handler(ctx, params)
            assert result["reloadPending"] is True
            assert get_capture(repo, capture_id)["status"] == "routed"
    ctx.reload(maintenance=False)
    result = handler(ctx, params)
    _assert_single(route, root, repo, result, server)


def test_changed_route_inputs_cannot_create_a_second_destination(destination):
    route, root, repo, capture_id, ctx, handler, module, params, server = destination
    result = handler(ctx, params)
    field = {"card": "prompt", "quick_add": "source", "tutor": "question"}[route]
    changed = params.model_copy(update={field: "different"})
    with pytest.raises(SidecarError, match="original capture route"):
        handler(ctx, changed)
    _assert_single(route, root, repo, result, server)


@pytest.mark.parametrize("invalid", ["content", "destination"])
def test_preflight_failure_allows_corrected_input(destination, invalid):
    route, root, repo, capture_id, ctx, handler, module, params, server = destination
    fields = {
        "card": {"content": {"prompt": " "}, "destination": {"learning_object_id": "missing"}},
        "quick_add": {"content": {"source": "https://example.org/not-imported"},
                      "destination": {"subject_id": "missing"}},
        "tutor": {"content": {"question": " "}, "destination": {"subject_id": "missing"}},
    }
    with pytest.raises(SidecarError):
        handler(ctx, params.model_copy(update=fields[route][invalid]))
    assert get_capture(repo, capture_id)["status"] == "new"
    with repo.connection() as conn:
        assert conn.execute("SELECT intent_json FROM capture_routes WHERE capture_id=?",
                            (capture_id,)).fetchone()[0] is None
    result = handler(ctx, params)
    _assert_single(route, root, repo, result, server)


@pytest.mark.parametrize("answer_status", ["pending", "failed"])
def test_incomplete_tutor_event_is_not_duplicated(tmp_path, monkeypatch, answer_status):
    server = _TutorServer()
    server.start()
    try:
        root, _ = _tutor_vault(tmp_path, server)
        repo, capture_id = _capture(root)
        ctx = _context(root)
        params = tutor_qa.AskTutorQuestionInput(
            capture_id=capture_id, subject_id="linear-algebra",
            context="library", question="Why eigenvectors?",
        )
        intent = capture_rpc.route_intent(repo, params, "ask_tutor")
        repo.insert_question_event({
            "id": intent["destination_id"], "context": "library",
            "question_md": params.question, "answer_status": answer_status,
        })
        with pytest.raises(SidecarError, match="No second question was created"):
            tutor_qa.ask_tutor_question(ctx, params)
        assert len(repo.question_events(context="library")) == 1
        assert not server.requests
        assert get_capture(repo, capture_id)["status"] == "new"
    finally:
        server.stop()


def test_reload_does_not_hold_a_sqlite_writer(destination, monkeypatch):
    route, root, repo, capture_id, ctx, handler, module, params, server = destination
    reload = ctx.reload
    def checked_reload(*args, **kwargs):
        # This distinct Repository must be able to write while reload runs.
        repo.bump_queue_revision()
        return reload(*args, **kwargs)
    monkeypatch.setattr(ctx, "reload", checked_reload)
    result = handler(ctx, params)
    assert not result.get("reloadPending")
    _assert_single(route, root, repo, result, server)


def test_tutor_ai_does_not_hold_a_sqlite_writer(tmp_path, monkeypatch):
    from learnloop.tutor import tutor_qa as domain

    server = _TutorServer()
    server.start()
    try:
        root, _ = _tutor_vault(tmp_path, server)
        repo, capture_id = _capture(root)
        ctx = _context(root)
        request = domain.request_tutor_answer
        def checked_request(*args, **kwargs):
            repo.bump_queue_revision()
            return request(*args, **kwargs)
        monkeypatch.setattr(domain, "request_tutor_answer", checked_request)
        result = tutor_qa.ask_tutor_question(ctx, tutor_qa.AskTutorQuestionInput(
            capture_id=capture_id, subject_id="linear-algebra",
            context="library", question="Why eigenvectors?",
        ))
        _assert_single("tutor", root, repo, result, server)
    finally:
        server.stop()


def test_purge_during_tutor_answer_does_not_restore_capture(tmp_path, monkeypatch):
    from learnloop.capture import purge_capture
    from learnloop.tutor import tutor_qa as domain

    server = _TutorServer()
    server.start()
    try:
        root, _ = _tutor_vault(tmp_path, server)
        repo, capture_id = _capture(root)
        ctx = _context(root)
        request = domain.request_tutor_answer
        def purge_during_request(*args, **kwargs):
            purge_capture(repo, capture_id)
            return request(*args, **kwargs)
        monkeypatch.setattr(domain, "request_tutor_answer", purge_during_request)
        params = tutor_qa.AskTutorQuestionInput(
            capture_id=capture_id, subject_id="linear-algebra",
            context="library", question="Why eigenvectors?",
        )
        result = tutor_qa.ask_tutor_question(ctx, params)
        # The started answer is real; purge removes the inbox payload, not
        # already-created notes/questions. It must never resurrect routing.
        assert result["captureRoutePending"] is True
        assert get_capture(repo, capture_id)["status"] == "purged"
        assert get_capture(repo, capture_id)["text"] is None
        with pytest.raises(SidecarError, match="purged"):
            tutor_qa.ask_tutor_question(ctx, params)
        _assert_single("tutor", root, repo, result, server)
    finally:
        server.stop()
