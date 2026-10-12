"""M1 desktop destinations record routes only after their durable success."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from learnloop.capture import create_capture, get_capture
from learnloop.cli import app
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import EmptyParams
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.capture import (
    CaptureInput, ListCaptureInput, dismiss_capture, get_inbox_summary,
    list_capture_inbox, purge_capture, record_route,
)
from learnloop_sidecar.handlers.ingest import ConfirmQuickAddInput, confirm_quick_add_rpc
from learnloop_sidecar.handlers.item_authoring import AuthorPracticeItemInput, author_practice_item
from learnloop_sidecar.handlers.tutor_qa import AskTutorQuestionInput, ask_tutor_question
from tests.helpers import create_basic_vault, seed_due_item
from tests.test_sidecar_quick_add import _seed_extraction
from tests.test_sidecar_tutor_qa import _TutorServer, _tutor_vault


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


@pytest.mark.parametrize("success", [False, True])
def test_card_route_after_success_only(tmp_path, success):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    seed_due_item(paths)
    repo, capture_id = _capture(root)
    ctx = _context(root)
    params = AuthorPracticeItemInput(
        capture_id=capture_id, learning_object_id="lo_svd_definition" if success else "missing",
        prompt="Why eigenvectors?", expected_answer="Invariant directions.",
    )
    if not success:
        with pytest.raises(SidecarError):
            author_practice_item(ctx, params)
        assert get_capture(repo, capture_id)["status"] == "new"
        return
    result = author_practice_item(ctx, params)
    refs = {"practice_item_id": result["practiceItemId"]}
    assert result["practiceItemId"] in load_vault(root).practice_items
    row = get_capture(repo, capture_id)
    assert (row["status"], row["route"], row["result_refs"]) == ("routed", "make_card", refs)
    record_route(repo, capture_id, "make_card", refs)  # same route/result is idempotent
    assert get_capture(repo, capture_id)["result_refs"] == refs


@pytest.mark.parametrize("success", [False, True])
def test_quick_add_route_after_durable_enqueue_only(tmp_path, monkeypatch, success):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    url = "https://example.org/book"
    _seed_extraction(paths.sqlite_path, url)
    repo, capture_id = _capture(root, url=url)
    ctx = _context(root)
    # Keep the real source-set and queue commits; suppress only background AI.
    monkeypatch.setattr(ctx.ingest_jobs, "_ensure_worker", lambda: None)
    params = ConfirmQuickAddInput(
        capture_id=capture_id, source=url, subject_id="linear-algebra" if success else "missing",
    )
    if not success:
        with pytest.raises(SidecarError):
            confirm_quick_add_rpc(ctx, params)
        assert get_capture(repo, capture_id)["status"] == "new"
        return
    result = confirm_quick_add_rpc(ctx, params)
    batch_id = result["quickAdd"]["batchId"]
    assert repo.get_ingest_batch(batch_id) is not None
    assert get_capture(repo, capture_id)["result_refs"] == {"batch_id": batch_id}
    assert get_capture(repo, capture_id)["route"] == "quick_add"


@pytest.mark.parametrize("success", [False, True])
def test_tutor_route_after_answer_only_and_reference_anchor(tmp_path, monkeypatch, success):
    server = _TutorServer()
    server.start()
    try:
        root, _ = _tutor_vault(tmp_path, server)
        repo, capture_id = _capture(root)
        ctx = _context(root)
        if not success:
            def failed(*args, **kwargs):
                raise TimeoutError("provider failed")
            monkeypatch.setattr("learnloop_sidecar.handlers.tutor_qa.ask_question", failed)
        params = AskTutorQuestionInput(
            capture_id=capture_id, subject_id="linear-algebra",
            context="library", question="Why eigenvectors?",
        )
        if not success:
            with pytest.raises(SidecarError, match="unavailable"):
                ask_tutor_question(ctx, params)
            assert get_capture(repo, capture_id)["status"] == "new"
            # A failed send can leave a reference, but never a practice item.
            assert len(load_vault(root).practice_items) == 1
            return
        result = ask_tutor_question(ctx, params)
        row = get_capture(repo, capture_id)
        assert row["route"] == "ask_tutor"
        assert row["result_refs"] == {"question_event_id": result["eventId"], "note_id": result["noteId"]}
        assert result["noteId"] in load_vault(root).notes
        assert repo.question_events(context="library", note_id=result["noteId"])[0]["id"] == result["eventId"]
        assert len(load_vault(root).practice_items) == 1
    finally:
        server.stop()


def test_summary_listing_banner_dismiss_purge_and_cli(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    create_basic_vault(root)
    repo, capture_id = _capture(root)
    config = tmp_path / "config"
    config.mkdir()
    (config / "mobile.toml").write_text(f'vault = "{tmp_path / "other"}"\nenabled = true\n')
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(config))
    ctx = _context(root)
    summary = get_inbox_summary(ctx, EmptyParams())
    assert summary["newCount"] == 1
    assert summary["vaultMismatch"] is True
    assert list_capture_inbox(ctx, ListCaptureInput())["captures"][0]["captureId"] == capture_id
    listed = CliRunner().invoke(app, ["inbox", "list", "--vault", str(root), "--json"])
    assert listed.exit_code == 0, listed.output
    assert json.loads(listed.output)["captures"][0]["capture_id"] == capture_id
    dismiss_capture(ctx, CaptureInput(capture_id=capture_id))
    assert get_capture(repo, capture_id)["status"] == "dismissed"
    purge_capture(ctx, CaptureInput(capture_id=capture_id))
    assert get_capture(repo, capture_id)["status"] == "purged"


def test_image_capture_kind_matches_desktop_dto(tmp_path):
    import io
    from PIL import Image

    root = tmp_path / "vault"
    create_basic_vault(root)
    repo = Repository(root / "state.sqlite")
    media = io.BytesIO()
    Image.new("RGB", (2, 2), "white").save(media, format="PNG")
    create_capture(repo, client_capture_id=new_ulid(), kind="image", media=media.getvalue())
    result = list_capture_inbox(_context(root), ListCaptureInput())
    assert result["captures"][0]["kind"] == "image"
