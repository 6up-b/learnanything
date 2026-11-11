"""Reader CA1: the problem as printed (ux_reader_compare_ask_v1 §8; K15, C10, Q10, Q12).

The crop holds only the problem's own blocks (a neighbouring block between
two of them splits the crop, never shows in it), one per page in reading
order, from a real PDF made here (no book text is committed); a check on
your own gets nothing but the figure the problem needs, with no locator; a
variant shows nothing; the switch off restores today. *Your photo* finds the
capture a card was written from. The transcription report is a maintenance
notice that resolves when the wording changes. The original page opened
before Submit is kept with the draft (it counts as the book). Nothing here
records an exposure or calls a model.
"""

from __future__ import annotations

import io
from datetime import timedelta
from pathlib import Path

import pytest
from PIL import Image
from pydantic import ValidationError

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.ingest.ir import DocumentBlock
from learnloop.reader.as_printed import FIGURE_LABEL, crop_boxes, item_as_printed, printed_crops
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.helpers import append_config_toml, create_basic_vault
from tests.reader_ca1_as_printed_helpers import (
    BLUE,
    EXTRACTION,
    GREEN,
    GREY,
    ITEM,
    LAYOUT,
    OWN,
    RED,
    _call,
    _image,
    _make_canonical,
    _seed_book,
    _share,
)
from tests.reader_ca1_as_printed_helpers import (  # noqa: F401 - fixtures, used by parameter name
    book,
    cold,
    warm,
)

def _exposures(repository) -> int:
    with repository.connection() as connection:
        return connection.execute("SELECT COUNT(*) FROM source_exposure_events").fetchone()[0]


# -- the crop: only the problem's own blocks (C10) -------------------------------------------------


def _blocks(spans):
    return [DocumentBlock.build(span_id=span, block_type=kind, text=span, ordinal=index, page=page, bbox=bbox)
            for index, (span, kind, page, bbox, _c, _o) in enumerate(LAYOUT, start=1) if span in spans]


def test_each_of_the_problems_blocks_is_its_own_crop_in_reading_order():
    """The Astra redesign (F6): never merged, so a crop is exactly one
    block's box (rewritten: this test pinned the old join of consecutive
    blocks into their union)."""

    crops, skipped = crop_boxes(_blocks(OWN))
    assert [(crop.page, crop.span_ids) for crop in crops] == [(0, ("e1",)), (0, ("e2",)), (0, ("f1",)), (1, ("e3",))]
    assert crops[1].bbox == (72.0, 180.0, 540.0, 210.0) and skipped == []
    # Nothing between them still leaves two crops, each its own box, unpadded.
    apart, _ = crop_boxes(_blocks(["e1", "e2"]))
    assert [(crop.span_ids, crop.bbox) for crop in apart] == [(("e1",), (72.0, 100.0, 540.0, 130.0)),
                                                             (("e2",), (72.0, 180.0, 540.0, 210.0))]


def test_a_block_without_a_page_or_a_box_crops_nothing():
    own = _blocks(["e1"]) + [DocumentBlock.build(span_id="nobox", block_type="Text", text="t", ordinal=99, page=0),
                             DocumentBlock.build(span_id="nopage", block_type="Text", text="t", ordinal=100,
                                                 bbox=[1.0, 1.0, 2.0, 2.0])]
    crops, skipped = crop_boxes(own)
    assert [crop.span_ids for crop in crops] == [("e1",)] and skipped == ["nobox", "nopage"]


def test_the_crops_from_the_page_hold_only_the_problems_own_ink(book):
    _paths, _ctx, repository = book
    printed = printed_crops(repository, extraction_id=EXTRACTION, span_ids=OWN, render=True)
    assert printed["status"] == "ok"
    assert [crop["span_ids"] for crop in printed["crops"]] == [["e1"], ["e2"], ["f1"], ["e3"]]
    assert [crop["page_label"] for crop in printed["crops"]] == ["1", "1", "1", "2"]
    first, second, figure, third = (_image(crop["image"]) for crop in printed["crops"])
    for image in (first, second, figure, third):
        assert _share(image, BLUE) == 0 and _share(image, GREY) == 0       # no neighbour, no caption
    assert _share(first, RED) > 0.9 and _share(second, RED) > 0.9 and _share(third, RED) > 0.9
    assert _share(figure, GREEN) > 0.9
    # Rendered at the reader's scale (1.4): a 468 x 30 pt block.
    assert (first.width, first.height) == (656, 42)


def test_without_the_original_the_geometry_is_kept_and_nothing_is_drawn(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    ctx = SidecarContext()
    ctx.load(paths.root)
    _vault, repository = ctx.require_vault()
    _seed_book(paths.root, repository, with_pdf=False)
    printed = printed_crops(repository, extraction_id=EXTRACTION, span_ids=OWN, render=True)
    assert printed["status"] == "no_original"
    assert [crop["image"] for crop in printed["crops"]] == [None, None, None, None]


# -- the practice view (K15) -----------------------------------------------------------------------


def test_the_practice_view_locates_the_problem_outside_a_check_and_records_nothing(book, warm):
    _paths, ctx, repository = book
    before = _exposures(repository)
    view = _call(ctx, "practice.as_printed", {"practiceItemId": ITEM})
    assert view["kind"] == "page" and view["cold"] is False
    assert view["label"] == "as printed (Strang p.1)"
    assert view["locator"] == {"sourceTitle": "Strang", "exerciseLabel": "Exercise 6.1.12", "pageLabel": "1"}
    assert view["originalPage"] == {"extractionId": EXTRACTION, "spanId": "e1", "outlineSpanIds": ["e1", "e2", "f1"],
                                    "sourceId": "src_ca1"}
    assert view["transcriptionReport"] is True
    assert view["crops"] and all(crop["image"] is None for crop in view["crops"])   # no render asked: labels only
    rendered = _call(ctx, "practice.as_printed", {"practiceItemId": ITEM, "render": True})
    assert all(crop["image"] for crop in rendered["crops"])
    assert _exposures(repository) == before                               # the crop is the stem: no exposure


def test_during_a_check_on_your_own_only_the_figure_shows_and_nothing_locates_it(book, cold):
    _paths, ctx, _repository = book
    view = _call(ctx, "practice.as_printed", {"practiceItemId": ITEM, "render": True})
    assert view["kind"] == "figure" and view["cold"] is True and view["label"] == FIGURE_LABEL
    assert set(view) == {"version", "practiceItemId", "enabled", "kind", "cold", "label", "status", "crops"}
    (crop,) = view["crops"]
    assert set(crop) == {"index", "image"}                                # no page, label, box or span
    image = _image(crop["image"])
    assert _share(image, GREEN) > 0.9 and _share(image, GREY) == 0 and _share(image, RED) == 0


def test_a_check_on_your_own_without_a_figure_shows_nothing(book, cold):
    paths, ctx, _repository = book
    _make_canonical(paths.root, spans=["e1", "e2"])
    ctx.reload(maintenance=False)
    view = _call(ctx, "practice.as_printed", {"practiceItemId": ITEM, "render": True})
    assert view == {"version": 1, "practiceItemId": ITEM, "enabled": True, "kind": "none", "cold": True,
                    "reason": "cold_check"}


def test_a_due_check_on_your_own_is_read_on_the_server(tmp_path):
    """D46 itself, not a stub: a due "Check once" on the item hides the print."""

    from learnloop.clock import FrozenClock
    from learnloop.curriculum import commitments as C
    from learnloop_sidecar.handlers.as_printed import cold_now
    from tests.intent_fakes import NOW, make_intent_vault

    iv = make_intent_vault(tmp_path / "vault")
    assert cold_now(iv.vault, iv.repository, "pi_b1") is False
    C.create_commitment(
        iv.repository, action="test_me_later", intent_text="rebuild without the book",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": "pi_b1", "role": "required"}],
        depth_preset="keep_in_touch", client_idempotency_key="reader_reconstruct:pi_b1",
        due_hint=(NOW - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"), clock=FrozenClock(NOW))
    assert cold_now(iv.vault, iv.repository, "pi_b1") is True
    assert cold_now(iv.vault, iv.repository, "pi_a1") is False


def test_an_unreadable_check_fails_closed(book, monkeypatch):
    import learnloop.intent.checks as checks

    def broken(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(checks, "served_check", broken)
    _paths, ctx, _repository = book
    assert _call(ctx, "practice.as_printed", {"practiceItemId": ITEM})["kind"] == "figure"


def test_a_variant_has_no_print_of_its_own(book, warm):
    paths, ctx, _repository = book
    _make_canonical(paths.root, relation="variant_of")
    ctx.reload(maintenance=False)
    view = _call(ctx, "practice.as_printed", {"practiceItemId": ITEM})
    assert view["kind"] == "none" and view["reason"] == "variant"


def test_an_item_with_no_page_and_no_photo_shows_nothing(tmp_path, warm):
    paths = create_basic_vault(tmp_path / "vault")
    ctx = SidecarContext()
    ctx.load(paths.root)
    view = _call(ctx, "practice.as_printed", {"practiceItemId": ITEM})
    assert view["kind"] == "none" and view["reason"] == "no_print"


def test_the_switch_off_shows_nothing_and_refuses_the_report(book, warm):
    paths, ctx, _repository = book
    append_config_toml(paths.root, "[practice.as_printed]\nenabled = false\n")
    ctx.reload(maintenance=False)
    assert _call(ctx, "practice.as_printed", {"practiceItemId": ITEM}) == {
        "version": 1, "enabled": False, "kind": "none", "cold": False, "reason": "disabled"}
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "practice.report_transcription", {"practiceItemId": ITEM})
    assert caught.value.code == "disabled"


def test_the_view_function_without_a_canonical_exercise_or_photo():
    class Item:
        canonical_exercise = None

    assert item_as_printed(None, Item(), enabled=True, cold=False, render=False)["reason"] == "no_print"


# -- your photo ------------------------------------------------------------------------------------


def _route_photo(root: Path, repository, item_id: str, *, purge: bool = False) -> str:
    from learnloop.capture import create_capture, route_capture
    from learnloop.ids import new_ulid

    image = Image.new("RGB", (40, 30), (10, 200, 10))
    raw = io.BytesIO()
    image.save(raw, format="PNG")
    created = create_capture(repository, client_capture_id=new_ulid(), kind="image", media=raw.getvalue(),
                             captured_at="2026-10-04T08:00:00+00:00", root=root)
    route_capture(repository, created["capture_id"], route="make_card", result_refs={"practice_item_id": item_id})
    if purge:
        with repository.connection() as connection:
            connection.execute("UPDATE capture_inbox SET purged_at = '2026-10-05T00:00:00Z' WHERE id = ?",
                               (created["capture_id"],))
            connection.commit()
    return created["capture_id"]


def test_a_card_written_from_a_photo_shows_the_photo_outside_a_check(tmp_path, monkeypatch):
    import learnloop.intent.checks as checks
    from learnloop.capture import photo_for_practice_item

    paths = create_basic_vault(tmp_path / "vault")
    ctx = SidecarContext()
    ctx.load(paths.root)
    _vault, repository = ctx.require_vault()
    assert photo_for_practice_item(repository, ITEM) is None
    capture_id = _route_photo(paths.root, repository, ITEM)
    _route_photo(paths.root, repository, "pi_someone_else")
    monkeypatch.setattr(checks, "served_check", lambda *args, **kwargs: None)
    view = _call(ctx, "practice.as_printed", {"practiceItemId": ITEM})
    assert view["kind"] == "photo" and view["label"] == "your photo"
    assert view["photo"] == {"captureId": capture_id, "capturedAt": "2026-10-04T08:00:00+00:00"}
    assert "transcriptionReport" not in view
    media = _call(ctx, "get_capture_media", {"captureId": capture_id})
    assert media["dataUrl"].startswith("data:image/")
    monkeypatch.setattr(checks, "served_check", lambda *args, **kwargs: {"locators_hidden": True})
    assert _call(ctx, "practice.as_printed", {"practiceItemId": ITEM})["reason"] == "cold_check"


def test_a_purged_photo_is_not_offered(tmp_path):
    from learnloop.capture import photo_for_practice_item

    paths = create_basic_vault(tmp_path / "vault")
    ctx = SidecarContext()
    ctx.load(paths.root)
    _vault, repository = ctx.require_vault()
    _route_photo(paths.root, repository, ITEM, purge=True)
    assert photo_for_practice_item(repository, ITEM) is None


# -- the transcription doesn't match the page ------------------------------------------------------


def _notices(repository):
    return [n for n in repository.maintenance_notices(include_hidden=True) if n["notice_type"] == "transcription_mismatch"]


def test_the_report_is_one_notice_that_counts_keeps_the_text_and_reopens(book, warm):
    from learnloop.ops.maintenance_feed import dismiss_notice

    _paths, ctx, repository = book
    first = _call(ctx, "practice.report_transcription", {"practiceItemId": ITEM, "note": "  the subscript is i, not 1 "})
    assert first["status"] == "active" and first["reports"] == 1
    _call(ctx, "practice.report_transcription", {"practiceItemId": ITEM})
    (notice,) = _notices(repository)
    assert notice["entity_type"] == "practice_item" and notice["entity_id"] == ITEM
    assert notice["severity"] == "action_needed" and "Exercise 6.1.12" in notice["title"]
    assert notice["action"] == {"action": "open_practice_item", "label": "Fix the wording", "practice_item_id": ITEM}
    detail = notice["detail"]
    assert detail["reports"] == 2 and [n["text"] for n in detail["notes"]] == ["the subscript is i, not 1"]
    assert detail["span_ids"] == OWN and detail["extraction_id"] == EXTRACTION
    dismiss_notice(repository, notice["id"])
    again = _call(ctx, "practice.report_transcription", {"practiceItemId": ITEM, "note": "still wrong"})
    assert again["status"] == "active" and again["reports"] == 3


def test_the_report_resolves_when_the_wording_changes_and_holds_until_then(book, warm):
    from learnloop.ops.maintenance_feed import generate_maintenance_feed

    paths, ctx, repository = book
    _call(ctx, "practice.report_transcription", {"practiceItemId": ITEM})
    vault, _ = ctx.require_vault()
    generate_maintenance_feed(vault, repository)
    assert _notices(repository)[0]["status"] == "active"
    path = next(paths.root.rglob(f"{ITEM}.yaml"))
    payload = read_yaml(path)
    payload["prompt"] = payload["prompt"] + " (reworded to match the page)"
    write_yaml(path, payload)
    generate_maintenance_feed(load_vault(paths.root), repository)
    assert _notices(repository)[0]["status"] == "resolved"


def test_only_a_verbatim_import_can_be_reported(book, warm):
    paths, ctx, _repository = book
    _make_canonical(paths.root, relation="variant_of")
    ctx.reload(maintenance=False)
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "practice.report_transcription", {"practiceItemId": ITEM})
    assert caught.value.code == "validation_error"
    with pytest.raises(SidecarError) as unknown:
        _call(ctx, "practice.report_transcription", {"practiceItemId": "pi_nope"})
    assert unknown.value.code == "not_found"


# -- the multi-block form of reader.block_original_region ------------------------------------------


def test_the_crop_rpc_takes_a_problems_blocks(book):
    _paths, ctx, _repository = book
    result = _call(ctx, "reader.block_original_region", {"extractionId": EXTRACTION, "spanIds": OWN})
    assert result["status"] == "ok" and [crop["spanIds"] for crop in result["crops"]] == [["e1"], ["e2"], ["f1"], ["e3"]]
    assert all(crop["image"] for crop in result["crops"])
    single = _call(ctx, "reader.block_original_region", {"extractionId": EXTRACTION, "spanId": "e1"})
    assert single["reason"] == "crop" and single["regionRender"]
    for params in ({"extractionId": EXTRACTION}, {"extractionId": EXTRACTION, "spanId": "e1", "spanIds": ["e1"]}):
        with pytest.raises(ValidationError):
            METHOD_REGISTRY["reader.block_original_region"].params_model.model_validate(params)


# -- the original page opened before Submit stays with the draft (Q12) -----------------------------


def test_the_draft_keeps_page_seen_under_its_retry_key(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    ctx = SidecarContext()
    ctx.load(paths.root)
    session_id = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]

    def save(key, **extra):
        _call(ctx, "save_practice_draft", {"sessionId": session_id, "practiceItemId": ITEM, "answerMd": "A",
                                           "hintsUsed": 0, "submissionId": key, **extra})

    def checkpoint():
        return _call(ctx, "get_session", {"sessionId": session_id})["checkpoint"]

    save("k1", pageSeen=True)
    assert checkpoint()["pageSeen"] is True and checkpoint()["hintsUsed"] == 0
    save("k1")                                                              # a save without it keeps it
    assert checkpoint()["pageSeen"] is True
    save("k2")                                                              # another draft never inherits it
    assert "pageSeen" not in checkpoint()
