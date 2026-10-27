"""Reader CA1, the Codex review's fixes (docs/reviews/reader-ca1-problem-as-printed-codex-review.md).

F1: a cold follow-up or an active diagnostic presentation hides the print
without any "Check once" commitment. F2: a crop never shows any of a block
that is not the problem's, even one whose centre lies outside the union.
F3: the switch off turns the multi-block crop form off too (the single-block
form unchanged). F4: a problem imported from a Reader selection, through the
real import path, has its print; a region selection's sub-box is the crop.
F5: a page known without a box still offers the original page and says the
crop can't be made. F8: a feed refresh never overwrites a report, and two
reports on two connections both count.
"""

from __future__ import annotations

import threading

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.reader.as_printed import FIGURE_LABEL, NO_CROP, crop_boxes
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop_sidecar.context import SidecarContext
from tests.helpers import append_config_toml, create_basic_vault
from tests.test_reader_ca1_as_printed import (  # noqa: F401 - fixtures
    BLUE,
    EXTRACTION,
    GREEN,
    GREY,
    ITEM,
    OWN,
    RED,
    _call,
    _image,
    _make_canonical,
    _seed_book,
    _share,
    book,
    warm,
)
from tests.test_source_inventory import _persist

NOW_ISO = "2026-01-01T00:00:00Z"


def _block(span: str, bbox, *, kind: str = "Text", ordinal: int = 0, page: int = 0) -> DocumentBlock:
    return DocumentBlock.build(span_id=span, block_type=kind, text=span, ordinal=ordinal, page=page, bbox=bbox)


# -- F2: the crop shows none of another block -----------------------------------------------------


def test_a_neighbour_reaching_into_the_gap_is_in_no_crop_though_its_centre_is_outside():
    own = [_block("a", [0, 0, 100, 20], ordinal=1), _block("b", [0, 80, 20, 100], ordinal=3)]
    # The solution's box (ordinal 2, [50, 30, 200, 70]) lies in no crop: each is its own block's box.
    crops, _ = crop_boxes(own)
    assert [(crop.span_ids, crop.bbox) for crop in crops] == [(("a",), (0.0, 0.0, 100.0, 20.0)),
                                                             (("b",), (0.0, 80.0, 20.0, 100.0))]


def test_adjacent_blocks_stay_two_crops():
    """The Astra redesign (F6): never merged (rewritten: this test pinned
    the join of two blocks sharing an edge)."""

    own = [_block("a", [0, 0, 100, 20], ordinal=1), _block("b", [0, 20, 100, 40], ordinal=2)]
    crops, _ = crop_boxes(own)
    assert [(crop.span_ids, crop.bbox) for crop in crops] == [(("a",), (0.0, 0.0, 100.0, 20.0)),
                                                             (("b",), (0.0, 20.0, 100.0, 40.0))]


def test_a_crop_is_exactly_its_blocks_box():
    """A caption the extractor drew overlapping the figure is in the figure's
    crop only as far as the figure's own box reaches (rewritten: this test
    pinned when a join was allowed)."""

    own = [_block("t", [0, 0, 100, 20], ordinal=1), _block("f", [0, 20, 100, 120], kind="Figure", ordinal=2)]
    crops, _ = crop_boxes(own)
    assert [crop.bbox for crop in crops] == [(0.0, 0.0, 100.0, 20.0), (0.0, 20.0, 100.0, 120.0)]


def test_a_figure_only_crop_never_takes_in_the_stem_beside_it(book):
    """The figure-only crop (Q10) treats the problem's own text as another
    block: two figures with the stem's text between them stay two crops."""

    from learnloop.reader.as_printed import printed_crops

    _paths, _ctx, repository = book
    blocks = [_block("f1", [0, 0, 100, 40], kind="Figure", ordinal=1), _block("t", [0, 50, 300, 60], ordinal=2),
              _block("f2", [0, 70, 100, 110], kind="Figure", ordinal=3)]
    unit = DocumentUnit(unit_id="u", label="u", ordinal=0, semantic_hash="sha256:u", page_start=0, page_end=0,
                        span_ids=[b.span_id for b in blocks])
    ir = DocumentIR(extractor="marker", extractor_version="figure-only", units=[unit], blocks=blocks, assets=[],
                    health=ExtractionHealth())
    _persist(repository, ir, revision_id="rev_ca1", extraction_id="ext_f")
    figures = printed_crops(repository, extraction_id="ext_f", span_ids=["f1", "t", "f2"], render=False,
                            figure_only=True)
    assert len(figures["crops"]) == 2 and all(set(crop) == {"index", "image"} for crop in figures["crops"])


# -- F1: every administration on your own hides the print -----------------------------------------


def _followup(repository, kind: str) -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO followup_tasks(id, kind, case_kind, case_ref, not_before, status, selected_item_id, "
            "created_at, updated_at) VALUES (?, ?, 'misconception', 'mc_x', '2020-01-01T00:00:00Z', 'pending', ?, ?, ?)",
            (f"ft_{kind}", kind, ITEM, NOW_ISO, NOW_ISO))
        connection.commit()


def _presentation(repository, status: str) -> None:
    with repository.connection() as connection:
        connection.execute("PRAGMA foreign_keys = OFF")                     # the episode's own graph is not under test
        connection.execute(
            "INSERT OR IGNORE INTO probe_episodes(id, learning_object_id, status, trigger, algorithm_version, "
            "created_at, updated_at) VALUES ('ep_ca1', 'lo_svd_definition', 'in_progress', 'initial', 'test', ?, ?)",
            (NOW_ISO, NOW_ISO))
        connection.execute(
            "INSERT INTO probe_presentations(id, probe_episode_id, practice_item_id, state_segment_id, status, "
            "created_at, updated_at) VALUES (?, 'ep_ca1', ?, 'segment', ?, ?, ?)",
            (f"pp_{status}", ITEM, status, NOW_ISO, NOW_ISO))
        connection.commit()


def _assert_figure_only(view: dict) -> None:
    assert view["kind"] == "figure" and view["cold"] is True and view["label"] == FIGURE_LABEL
    assert set(view) == {"version", "practiceItemId", "enabled", "kind", "cold", "label", "status", "crops"}
    (crop,) = view["crops"]
    image = _image(crop["image"])
    assert _share(image, GREEN) > 0.9 and _share(image, RED) == 0


def test_a_standalone_cold_follow_up_hides_the_print_with_no_check_once(book):
    _paths, ctx, repository = book
    assert _call(ctx, "practice.as_printed", {"practiceItemId": ITEM})["kind"] == "page"   # no commitment, no duty
    _followup(repository, "cold_retry")
    _assert_figure_only(_call(ctx, "practice.as_printed", {"practiceItemId": ITEM, "render": True}))


def test_a_certification_cold_probe_hides_the_print_and_nothing_locates_it(book):
    paths, ctx, repository = book
    _make_canonical(paths.root, spans=["e1", "e2"])                       # no figure: nothing at all
    ctx.reload(maintenance=False)
    _followup(repository, "certification_cold_probe")
    view = _call(ctx, "practice.as_printed", {"practiceItemId": ITEM, "render": True})
    assert view == {"version": 1, "practiceItemId": ITEM, "enabled": True, "kind": "none", "cold": True,
                    "reason": "cold_check"}


def test_an_active_diagnostic_presentation_hides_the_print_until_it_is_answered(book):
    _paths, ctx, repository = book
    _presentation(repository, "submitted")                                # an answered one locates nothing
    assert _call(ctx, "practice.as_printed", {"practiceItemId": ITEM})["kind"] == "page"
    _presentation(repository, "served")
    _assert_figure_only(_call(ctx, "practice.as_printed", {"practiceItemId": ITEM, "render": True}))


# -- F3: the switch turns the multi-block form off ------------------------------------------------


def test_the_switch_off_crops_nothing_through_the_multi_block_form_and_keeps_the_single_block(book):
    paths, ctx, _repository = book
    first = _call(ctx, "reader.block_original_region", {"extractionId": EXTRACTION, "spanIds": OWN, "render": False})
    assert first["status"] == "ok" and all(crop["image"] is None for crop in first["crops"])   # the cheap read
    append_config_toml(paths.root, "[practice.as_printed]\nenabled = false\n")
    ctx.reload(maintenance=False)
    off = _call(ctx, "reader.block_original_region", {"extractionId": EXTRACTION, "spanIds": OWN})
    assert off == {"version": 1, "extractionId": EXTRACTION, "spanIds": OWN, "status": "disabled", "crops": [],
                   "skippedSpanIds": []}
    single = _call(ctx, "reader.block_original_region", {"extractionId": EXTRACTION, "spanId": "e1"})
    assert single["reason"] == "crop" and single["regionRender"]           # pre-CA1 behaviour unchanged


def test_render_and_region_belong_to_the_multi_block_form():
    import pytest
    from pydantic import ValidationError

    from learnloop_sidecar.registry import METHOD_REGISTRY

    model = METHOD_REGISTRY["reader.block_original_region"].params_model
    for params in ({"extractionId": "x", "spanId": "e1", "render": False},
                   {"extractionId": "x", "spanId": "e1", "region": {"spanId": "e1", "page": 0, "bbox": [0, 0, 1, 1]}}):
        with pytest.raises(ValidationError):
            model.model_validate(params)


# -- F4: a Reader selection import has its print, through the real import path --------------------


def _import_selection(paths, repository, *, region=None) -> str:
    from learnloop.content.authoring import exercise_authoring as EX
    from tests.test_exercise_authoring import FakeClient, _item, _write_facet_registry
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring

    _write_facet_registry(paths.root.parent)
    raw = {"nodes": [{"spanId": "e1", "quote": "block e1"}, {"spanId": "e2", "quote": "block e2"},
                     {"spanId": "f1", "quote": "block f1"}]}
    if region is not None:
        raw["region"] = region
    from learnloop.content.authoring.ai_contracts import FigureRolePayload

    # The statement runs over every block selected (Astra batch review: a
    # single item owns the blocks its statement covers, no more), and the
    # author calls the figure its input (the Astra redesign: a figure is
    # owned by its validated role, never by the text).
    client = FakeClient(ExerciseAuthoring(items=[_item(statement_md="block e1 block e2 block f1",
                                                       title="Exercise 6.1.12",
                                                       figure_roles=[FigureRolePayload(span_id="f1",
                                                                                       role="stimulus")])]))
    result = EX.import_exercises(paths.root, repository, client, extraction_id=EXTRACTION, raw_selection=raw,
                                 source_id="src_ca1")
    (summary,) = result["items"]
    return summary["practice_item_id"]


def test_a_reader_selection_import_shows_its_print_after_binding(book, warm):
    paths, ctx, repository = book
    item_id = _import_selection(paths, repository)
    ctx.reload(maintenance=False)
    vault, _ = ctx.require_vault()
    assert vault.practice_items[item_id].canonical_exercise is None       # the selection path writes none
    view = _call(ctx, "practice.as_printed", {"practiceItemId": item_id, "render": True})
    assert view["kind"] == "page" and view["label"] == "as printed (Strang p.1)"
    assert [crop["spanIds"] for crop in view["crops"]] == [["e1"], ["e2"], ["f1"]]
    assert view["originalPage"] == {"extractionId": EXTRACTION, "spanId": "e1", "outlineSpanIds": ["e1", "e2", "f1"],
                                    "sourceId": "src_ca1"}
    assert view["transcriptionReport"] is True
    report = _call(ctx, "practice.report_transcription", {"practiceItemId": item_id, "note": "the sign"})
    assert report["reports"] == 1


def test_an_ai_proposal_over_the_same_blocks_is_not_the_book_s_problem(book, warm):
    """``canonical_extract`` provenance alone is shared with AI proposals over
    sources: without the Reader import's own event there is no print."""

    paths, ctx, _repository = book
    path = next(paths.root.rglob(f"{ITEM}.yaml"))
    payload = read_yaml(path)
    payload.pop("canonical_exercise", None)
    payload["provenance"] = {"origin": "canonical_extract", "source_refs": [
        {"ref_type": "canonical_source", "ref_id": "src_ca1", "locator": f"span:{EXTRACTION}/e1",
         "locator_scheme": "block_span_v1"}]}
    write_yaml(path, payload)
    ctx.reload(maintenance=False)
    assert _call(ctx, "practice.as_printed", {"practiceItemId": ITEM})["reason"] == "no_print"


def test_a_region_selection_s_sub_box_is_the_crop_shown(book, warm):
    paths, ctx, repository = book
    # A box inside the figure block (f1 is [72, 220, 300, 400]), reaching past it on the right.
    item_id = _import_selection(paths, repository, region={"spanId": "f1", "page": 0, "bbox": [100, 250, 400, 300]})
    ctx.reload(maintenance=False)
    vault, _ = ctx.require_vault()
    refs = {ref.locator: ref for ref in vault.practice_items[item_id].provenance.source_refs}
    assert refs[f"span:{EXTRACTION}/f1"].model_extra["region"] == {"page": 0, "bbox": [100.0, 250.0, 400.0, 300.0]}
    view = _call(ctx, "practice.as_printed", {"practiceItemId": item_id})
    by_spans = {tuple(crop["spanIds"]): crop["bbox"] for crop in view["crops"]}
    assert by_spans[("f1",)] == [100.0, 250.0, 300.0, 300.0]               # the region, clipped to f1, alone
    assert by_spans[("e2",)] == [72.0, 180.0, 540.0, 210.0]
    # The pending workbench crop takes the same region through the multi-block form.
    pending = _call(ctx, "reader.block_original_region", {
        "extractionId": EXTRACTION, "spanIds": ["f1"], "region": {"spanId": "f1", "page": 0, "bbox": [100, 250, 400, 300]}})
    assert [crop["bbox"] for crop in pending["crops"]] == [[100.0, 250.0, 300.0, 300.0]]
    image = _image(pending["crops"][0]["image"])
    assert _share(image, GREEN) > 0.9 and _share(image, GREY) == 0 and _share(image, BLUE) == 0


def test_the_workbench_session_carries_the_region_it_was_imported_with():
    from learnloop.reader.workbench import _print_region

    request = '{"rawSelection": {"nodes": [], "region": {"spanId": "f1", "page": 0, "bbox": [1, 2, 3, 4]}}}'
    assert _print_region({"import_request_json": request}) == {
        "print_region": {"span_id": "f1", "page": 0, "bbox": [1, 2, 3, 4]}}
    assert _print_region({"import_request_json": '{"rawSelection": {"nodes": []}}'}) == {}
    assert _print_region({"import_request_json": None}) == {}


# -- F5: a page without boxes still has its original page ------------------------------------------


def test_a_page_known_without_a_box_offers_the_original_page_and_no_substitute_crop(tmp_path, warm):
    paths = create_basic_vault(tmp_path / "vault")
    ctx = SidecarContext()
    ctx.load(paths.root)
    _vault, repository = ctx.require_vault()
    _seed_book(paths.root, repository)
    blocks = [DocumentBlock.build(span_id=span, block_type="Text", text=f"pypdf {span}", ordinal=i, page=0, bbox=None)
              for i, span in enumerate(("p1", "p2"), start=1)]
    unit = DocumentUnit(unit_id="up", label="p", ordinal=0, semantic_hash="sha256:up", page_start=0, page_end=0,
                        span_ids=["p1", "p2"])
    ir = DocumentIR(extractor="pypdf", extractor_version="1", units=[unit], blocks=blocks, assets=[],
                    health=ExtractionHealth())
    _persist(repository, ir, revision_id="rev_ca1", extraction_id="ext_pypdf")
    path = next(paths.root.rglob(f"{ITEM}.yaml"))
    payload = read_yaml(path)
    payload["canonical_exercise"] = {"source_id": "src_ca1", "revision_id": "rev_ca1", "extraction_id": "ext_pypdf",
                                     "span_ids": ["p1", "p2"], "label": "Exercise 2", "relation": "verbatim"}
    write_yaml(path, payload)
    ctx.reload(maintenance=False)
    view = _call(ctx, "practice.as_printed", {"practiceItemId": ITEM, "render": True})
    assert view["kind"] == "page" and view["crops"] == [] and view["status"] == "no_geometry"
    assert view["notice"] == NO_CROP and view["label"] == "as printed (Strang p.1)"
    assert view["originalPage"] == {"extractionId": "ext_pypdf", "spanId": "p1", "outlineSpanIds": ["p1", "p2"],
                                    "sourceId": "src_ca1"}
    # Without the PDF there is no page to open: nothing is offered.
    from learnloop.reader import as_printed as AP

    original = AP._pdf_path
    try:
        AP._pdf_path = lambda *_args: None
        assert _call(ctx, "practice.as_printed", {"practiceItemId": ITEM})["kind"] == "none"
    finally:
        AP._pdf_path = original


# -- F8: reports are never lost to a refresh or another report ------------------------------------


def _origin(vault, repository):
    from learnloop.reader.as_printed import printed_origin

    return printed_origin(repository, vault.practice_items[ITEM])


def _notice(repository):
    (notice,) = [n for n in repository.maintenance_notices(include_hidden=True)
                 if n["notice_type"] == "transcription_mismatch"]
    return notice


def test_a_feed_refresh_reading_before_a_report_never_overwrites_it(book, warm, monkeypatch):
    from learnloop.ops import maintenance_feed as MF

    paths, ctx, repository = book
    vault, _ = ctx.require_vault()
    MF.report_transcription_mismatch(vault, repository, ITEM, origin=_origin(vault, repository), note="first")
    # The refresh reads the live notices; a report lands between that read
    # and the refresh's writes (the interleaving the review describes).
    real = repository.maintenance_notices
    reported = {"done": False}

    def read_then_report(*args, **kwargs):
        rows = real(*args, **kwargs)
        if not reported["done"]:
            reported["done"] = True
            other = type(repository)(repository.sqlite_path)                # a second connection, its own commit
            MF.report_transcription_mismatch(load_vault(paths.root), other, ITEM, origin=_origin(vault, other), note="second")
        return rows

    monkeypatch.setattr(repository, "maintenance_notices", read_then_report)
    MF.generate_maintenance_feed(vault, repository)
    monkeypatch.setattr(repository, "maintenance_notices", real)
    notice = _notice(repository)
    assert notice["status"] == "active" and notice["detail"]["reports"] == 2
    assert [n["text"] for n in notice["detail"]["notes"]] == ["first", "second"]


def test_a_reworded_card_resolves_but_a_report_on_the_new_wording_meanwhile_is_kept(book, warm, monkeypatch):
    from learnloop.ops import maintenance_feed as MF

    paths, ctx, repository = book
    vault, _ = ctx.require_vault()
    MF.report_transcription_mismatch(vault, repository, ITEM, origin=_origin(vault, repository), note="old wording")
    path = next(paths.root.rglob(f"{ITEM}.yaml"))
    payload = read_yaml(path)
    payload["prompt"] = payload["prompt"] + " (reworded)"
    write_yaml(path, payload)
    reworded = load_vault(paths.root)
    real = repository.maintenance_notices
    state = {"done": False}

    def read_then_report(*args, **kwargs):
        rows = real(*args, **kwargs)
        if not state["done"]:
            state["done"] = True
            MF.report_transcription_mismatch(reworded, type(repository)(repository.sqlite_path), ITEM,
                                             origin=_origin(reworded, repository), note="new")
        return rows

    monkeypatch.setattr(repository, "maintenance_notices", read_then_report)
    MF.generate_maintenance_feed(reworded, repository)
    monkeypatch.setattr(repository, "maintenance_notices", real)
    notice = _notice(repository)
    assert notice["status"] == "active" and notice["detail"]["reports"] == 1
    assert [n["text"] for n in notice["detail"]["notes"]] == ["new"]
    MF.generate_maintenance_feed(reworded, repository)                     # nothing changed since: kept
    assert _notice(repository)["status"] == "active"


def test_two_reports_on_two_connections_both_count(book, warm):
    from learnloop.ops import maintenance_feed as MF

    paths, _ctx, repository = book
    errors: list[BaseException] = []
    barrier = threading.Barrier(4)

    def report(index: int) -> None:
        try:
            own = type(repository)(repository.sqlite_path)
            barrier.wait()
            fresh = load_vault(paths.root)
            MF.report_transcription_mismatch(fresh, own, ITEM, origin=_origin(fresh, own), note=f"note {index}")
        except BaseException as exc:  # noqa: BLE001 - surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=report, args=(index,)) for index in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    detail = _notice(repository)["detail"]
    assert detail["reports"] == 4 and sorted(n["text"] for n in detail["notes"]) == [f"note {i}" for i in range(4)]
    assert detail["prompt"] == load_vault(paths.root).practice_items[ITEM].prompt


def test_the_feed_upsert_of_other_notices_is_unchanged(book, warm):
    """The feed still regenerates its own notices; only the learner's report is held."""

    from learnloop.ops import maintenance_feed as MF

    _paths, ctx, repository = book
    vault, _ = ctx.require_vault()
    MF.report_transcription_mismatch(vault, repository, ITEM, origin=_origin(vault, repository))
    before = _notice(repository)
    MF.generate_maintenance_feed(vault, repository)
    after = _notice(repository)
    assert after["detail"] == before["detail"] and after["status"] == "active"


# -- Re-review F9: a split selection's items own only their own blocks ----------------------------


def _split_selection(paths, repository, *, edited_text: str | None = None) -> tuple[str, str]:
    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
    from tests.test_exercise_authoring import FakeClient, _item, _write_facet_registry

    _write_facet_registry(paths.root.parent)
    raw = {"nodes": [{"spanId": "e1", "quote": "block e1"}, {"spanId": "e2", "quote": "block e2"},
                     {"spanId": "f1", "quote": "block f1"}]}
    if edited_text is not None:
        raw["editedText"] = edited_text
    client = FakeClient(ExerciseAuthoring(items=[_item(statement_md="block e1", title="Exercise 1"),
                                                 _item(statement_md="block e2", title="Exercise 2")]))
    result = EX.import_exercises(paths.root, repository, client, extraction_id=EXTRACTION, raw_selection=raw,
                                 source_id="src_ca1")
    first, second = (summary["practice_item_id"] for summary in result["items"])
    return first, second


def test_two_exercises_split_from_one_selection_each_crop_only_their_own_block(book, warm):
    paths, ctx, repository = book
    first, second = _split_selection(paths, repository)
    ctx.reload(maintenance=False)
    one = _call(ctx, "practice.as_printed", {"practiceItemId": first, "render": True})
    two = _call(ctx, "practice.as_printed", {"practiceItemId": second, "render": True})
    assert [crop["spanIds"] for crop in one["crops"]] == [["e1"]]
    assert [crop["spanIds"] for crop in two["crops"]] == [["e2"]]
    assert one["originalPage"]["outlineSpanIds"] == ["e1"] and two["originalPage"]["outlineSpanIds"] == ["e2"]
    image = _image(two["crops"][0]["image"])
    assert _share(image, RED) > 0.9 and _share(image, GREEN) == 0             # the other blocks are not its own
    # Every block stays a source ref (provenance is the selection's); only ownership differs.
    vault, _ = ctx.require_vault()
    refs = vault.practice_items[second].provenance.source_refs
    assert [ref.locator for ref in refs] == [f"span:{EXTRACTION}/{span}" for span in ("e1", "e2", "f1")]
    assert [ref.model_extra.get("owned") for ref in refs] == [False, True, False]


def test_a_split_whose_ownership_cannot_be_read_offers_only_the_charged_page(book, warm):
    paths, ctx, repository = book
    # A selection-level edit replaces the whole text: no part maps to a block.
    first, _second = _split_selection(paths, repository, edited_text="block e1\n\nblock e2")
    ctx.reload(maintenance=False)
    view = _call(ctx, "practice.as_printed", {"practiceItemId": first, "render": True})
    assert view["kind"] == "page" and view["crops"] == [] and view["notice"] == NO_CROP
    assert view["originalPage"]["spanId"] == "e1"
    cold_view = None
    _followup(repository, "cold_retry")
    _followup_item = first
    with repository.connection() as connection:
        connection.execute("UPDATE followup_tasks SET selected_item_id=?", (_followup_item,))
        connection.commit()
    cold_view = _call(ctx, "practice.as_printed", {"practiceItemId": first, "render": True})
    assert cold_view["kind"] == "none" and cold_view["reason"] == "cold_check"


def test_a_split_written_before_ownership_was_kept_withholds_the_free_crop(book, warm):
    """Items split from one selection before the marker existed: their import
    rows (one per item, one write) say the selection was split, so neither
    item's crop is free; the original page still is offered."""

    from learnloop.content.authoring import source_exercise_import as SEI

    paths, ctx, repository = book
    append_config_toml(paths.root, "[source_service]\nenabled = true\n")
    first, second = _split_selection(paths, repository)
    for item_id in (first, second):
        path = next(paths.root.rglob(f"{item_id}.yaml"))
        payload = read_yaml(path)
        for ref in payload["provenance"]["source_refs"]:
            ref.pop("owned", None)
        write_yaml(path, payload)
    SEI.record_reader_import(paths.root, repository, {"items": [{"practice_item_id": first},
                                                                {"practice_item_id": second}]},
                             extraction_id=EXTRACTION, span_ids=["e1", "e2", "f1"], source_id="src_ca1",
                             revision_id="rev_ca1")
    ctx.reload(maintenance=False)
    for item_id in (first, second):
        view = _call(ctx, "practice.as_printed", {"practiceItemId": item_id, "render": True})
        assert view["kind"] == "page" and view["crops"] == [] and view["notice"] == NO_CROP
        assert view["originalPage"]["spanId"] == "e1"


# -- Final verify F9: a free crop only where its geometry is the item's alone ---------------------

SHARED = "ext_ca1_shared"
#: One block holding two exercises (page 0), and a third on page 1.
SHARED_LAYOUT = (
    ("s1", 0, [0.0, 0.0, 200.0, 80.0], RED, "1. Compute 2+2. 2. Compute 3+3."),
    ("s2", 1, [72.0, 50.0, 540.0, 80.0], BLUE, "3. Compute 4+4."),
)


def _seed_shared_book(root, repository) -> None:
    """A two-page PDF drawn here, its first block holding two exercises."""

    import hashlib
    import io

    from PIL import Image, ImageDraw

    from learnloop.ingest.ir import DocumentUnit
    from learnloop.ingest.originals import store_original_bytes

    pages = []
    for page in (0, 1):
        image = Image.new("RGB", (612, 792), "white")
        draw = ImageDraw.Draw(image)
        for _span, block_page, bbox, colour, _text in SHARED_LAYOUT:
            if block_page == page:
                draw.rectangle(bbox, fill=colour)
        pages.append(image)
    out = io.BytesIO()
    pages[0].save(out, format="PDF", resolution=72.0, save_all=True, append_images=pages[1:])
    raw = out.getvalue()
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    store_original_bytes(root, digest, raw)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, current_revision_id, "
            "reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            ("src_shared", "pdf", "file:///nowhere/src_shared.pdf", "Strang", "rev_shared", 1, NOW_ISO, NOW_ISO))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_shared", "src_shared", digest, None, NOW_ISO))
        connection.commit()
    blocks = [DocumentBlock.build(span_id=span, block_type="Text", text=text, ordinal=index, page=page, bbox=bbox,
                                  section_path=["6.1"])
              for index, (span, page, bbox, _colour, text) in enumerate(SHARED_LAYOUT, start=1)]
    unit = DocumentUnit(unit_id="u61s", label="6.1 Eigenvalues", ordinal=0, semantic_hash="sha256:u61s",
                        page_start=0, page_end=1, span_ids=[block.span_id for block in blocks])
    ir = DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks, assets=[],
                    health=ExtractionHealth())
    _persist(repository, ir, revision_id="rev_shared", extraction_id=SHARED)


def test_two_exercises_split_from_one_block_get_no_free_crop_and_keep_the_page(book, warm):
    """The final verify's first reproduction: both items' statements sit in
    one block, so neither owns its geometry; each offers the original page
    only (charged before Submit), never a crop showing the other exercise."""

    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
    from tests.test_exercise_authoring import FakeClient, _item, _write_facet_registry

    paths, ctx, repository = book
    _seed_shared_book(paths.root, repository)
    _write_facet_registry(paths.root.parent)
    raw = {"nodes": [{"spanId": "s1", "quote": "1. Compute 2+2. 2. Compute 3+3."}]}
    client = FakeClient(ExerciseAuthoring(items=[_item(statement_md="Compute 2+2.", title="Exercise 1"),
                                                 _item(statement_md="Compute 3+3.", title="Exercise 2")]))
    result = EX.import_exercises(paths.root, repository, client, extraction_id=SHARED, raw_selection=raw,
                                 source_id="src_shared")
    ids = [summary["practice_item_id"] for summary in result["items"]]
    assert len(ids) == 2
    ctx.reload(maintenance=False)
    vault, _ = ctx.require_vault()
    for item_id in ids:
        assert [ref.model_extra.get("owned") for ref in vault.practice_items[item_id].provenance.source_refs] == [False]
        view = _call(ctx, "practice.as_printed", {"practiceItemId": item_id, "render": True})
        assert view["kind"] == "page" and view["crops"] == [] and view["notice"] == NO_CROP
        assert view["originalPage"]["extractionId"] == SHARED and view["originalPage"]["spanId"] == "s1"


def test_a_split_over_disjoint_and_shared_blocks_withholds_only_the_sharing_items_crop(book, warm):
    """An item whose blocks are all its own keeps its crop; one that shares a
    block with another item gets none (never a partial print)."""

    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
    from tests.test_exercise_authoring import FakeClient, _item, _write_facet_registry

    paths, ctx, repository = book
    _seed_shared_book(paths.root, repository)
    _write_facet_registry(paths.root.parent)
    raw = {"nodes": [{"spanId": "s1", "quote": "1. Compute 2+2. 2. Compute 3+3."},
                     {"spanId": "s2", "quote": "3. Compute 4+4."}]}
    client = FakeClient(ExerciseAuthoring(items=[_item(statement_md="Compute 2+2.", title="Exercise 1"),
                                                 _item(statement_md="Compute 3+3.", title="Exercise 2"),
                                                 _item(statement_md="Compute 4+4.", title="Exercise 3")]))
    result = EX.import_exercises(paths.root, repository, client, extraction_id=SHARED, raw_selection=raw,
                                 source_id="src_shared")
    first, second, third = (summary["practice_item_id"] for summary in result["items"])
    ctx.reload(maintenance=False)
    for item_id in (first, second):
        view = _call(ctx, "practice.as_printed", {"practiceItemId": item_id, "render": True})
        assert view["kind"] == "page" and view["crops"] == [] and view["notice"] == NO_CROP
    view = _call(ctx, "practice.as_printed", {"practiceItemId": third, "render": True})
    assert [crop["spanIds"] for crop in view["crops"]] == [["s2"]]
    image = _image(view["crops"][0]["image"])
    assert _share(image, BLUE) > 0.9 and _share(image, RED) == 0


def test_a_split_with_an_unanchored_sibling_owns_nothing(book, warm):
    """A sibling the code could not anchor (a paraphrase, skipped) may sit in
    any block: no item of that split has a free crop."""

    paths, ctx, repository = book
    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
    from tests.test_exercise_authoring import FakeClient, _item, _write_facet_registry

    _write_facet_registry(paths.root.parent)
    raw = {"nodes": [{"spanId": "e1", "quote": "block e1"}, {"spanId": "e2", "quote": "block e2"}]}
    client = FakeClient(ExerciseAuthoring(items=[_item(statement_md="block e1", title="Exercise 1"),
                                                 _item(statement_md="a paraphrase of e2", title="Exercise 2")]))
    result = EX.import_exercises(paths.root, repository, client, extraction_id=EXTRACTION, raw_selection=raw,
                                 source_id="src_ca1")
    (summary,) = result["items"]
    ctx.reload(maintenance=False)
    view = _call(ctx, "practice.as_printed", {"practiceItemId": summary["practice_item_id"], "render": True})
    assert view["kind"] == "page" and view["crops"] == [] and view["notice"] == NO_CROP


def _strip_ownership(paths, *item_ids: str) -> None:
    for item_id in item_ids:
        path = next(paths.root.rglob(f"{item_id}.yaml"))
        payload = read_yaml(path)
        for ref in payload["provenance"]["source_refs"]:
            ref.pop("owned", None)
        write_yaml(path, payload)


def test_a_split_written_with_no_import_rows_withholds_the_free_crop(book, warm):
    """The final verify's second reproduction: a split import made with
    ``source_service.enabled = false`` has its events and the selection's
    refs but no ``source_exercise_imports`` rows. Ownership can't be read, so
    neither item's crop is free; the original page still is offered."""

    paths, ctx, repository = book
    append_config_toml(paths.root, "[source_service]\nenabled = false\n")
    first, second = _split_selection(paths, repository)
    _strip_ownership(paths, first, second)
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM source_exercise_imports").fetchone()[0] == 0
    ctx.reload(maintenance=False)
    for item_id in (first, second):
        view = _call(ctx, "practice.as_printed", {"practiceItemId": item_id, "render": True})
        assert view["kind"] == "page" and view["crops"] == [] and view["notice"] == NO_CROP
        assert view["originalPage"]["spanId"] == "e1" and view["originalPage"]["outlineSpanIds"] == ["e1", "e2", "f1"]


def test_an_import_written_before_ownership_was_kept_shows_only_the_page(book, warm):
    """A Reader import from before ownership was recorded can't show that its
    crop is its own (a sibling the import skipped leaves no row), so its crop
    is withheld whatever rows it has; the original page is still offered."""

    from learnloop.content.authoring import source_exercise_import as SEI

    paths, ctx, repository = book
    item_id = _import_selection(paths, repository)
    vault = load_vault(paths.root)
    assert all(ref.model_extra.get("owned") is True for ref in vault.practice_items[item_id].provenance.source_refs)
    _strip_ownership(paths, item_id)
    SEI.record_reader_import(paths.root, repository, {"items": [{"practice_item_id": item_id}]},
                             extraction_id=EXTRACTION, span_ids=["e1", "e2", "f1"], source_id="src_ca1",
                             revision_id="rev_ca1")
    ctx.reload(maintenance=False)
    view = _call(ctx, "practice.as_printed", {"practiceItemId": item_id, "render": True})
    assert view["kind"] == "page" and view["crops"] == [] and view["notice"] == NO_CROP
    assert view["originalPage"]["spanId"] == "e1"
