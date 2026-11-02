"""RW5d P4a: figures follow the section (spec_reader_show_me_figures_v1 §10.2).

A kept figure is anchored to spans, so it has a section. When the learner
reads a section that judged coverage (C0a, read through
``reader.correspondents``) says another book's section corresponds to, that
correspondent lists the figures anchored in it (``figures``), so the Guide's
*also in your books* can offer *an interactive version from Lay §5.1*. A read
joined through the anchor's section: nothing is copied (no ``source_objects``
row, Q8), nothing is written, no model is called. Exam and held-out material
is protected on both sides: a protected open section has no correspondents,
a correspondent with a withheld span is not listed, and a figure is listed
only while nothing it was built from is held out now. Behind CA5's
``reader.correspondence.enabled``: off, the read is byte-identical to before.
"""

from __future__ import annotations

import json

from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.stores import figures as store
from learnloop.figures import service as FS
from learnloop.figures import spec as S
from tests import figure_corpus as FC
from tests.reading_path_fixtures import call, context
from tests.section_coverage_fixtures import (
    BOOK_EIGEN,
    CoverageJudgeFake,
    LAY,
    build_coverage_vault,
    hold_out,
    table_counts,
)
from tests.source_retrieval_fakes import BOOK

FIND = {"extraction_id": "ext_book", "section_id": BOOK_EIGEN}
QUIET = {**FIND, "search_fallback": False}
#: ext_lay's spans (seed_source numbering): lay_eigen s1-s3, lay_char s5-s6, lay_held s8-s9, lay_ortho s11-s12.
LAY_EIGEN_SPAN = "s2"
LAY_CHAR_SPAN = "s6"
LAY_HELD_SPAN = "s9"


def _judged(tmp_path, *, config: str = ""):
    paths, repository = build_coverage_vault(tmp_path / "vault", config=config)
    judge = CoverageJudgeFake(treatments={"5.1 Eigenvectors and eigenvalues": "introduces",
                                          "5.2 The characteristic equation": "develops"})
    ctx = context(paths.root, coverage_inline=True, coverage_judge_client=judge)
    call(ctx, "curriculum.cover", FIND)
    return paths, repository, ctx, judge


def _figure(repository, figure_id: str, *, extraction_id: str = "ext_lay", span_ids=(LAY_EIGEN_SPAN,),
            verification: str = "illustrative", input_span_ids=(), input_span_keys=(),
            created_at: str = "2026-10-30T00:00:00Z") -> None:
    spec = FC.flagship_spec()
    with repository.connection() as connection:
        store.insert_figure(connection, {
            "id": figure_id, "extraction_id": extraction_id, "span_ids": list(span_ids),
            "input_span_ids": list(input_span_ids) or list(span_ids), "input_span_keys": list(input_span_keys),
            "origin": "selection", "spec_json": json.dumps(spec), "spec_version": S.SPEC_VERSION,
            "kind": "illustrative", "verification": verification,
            "verification_report": {"reason": "failed a check"} if verification == "failed" else {},
            "model": "fake", "prompt_version": "v1", "input_hash": f"hash_{figure_id}", "created_at": created_at,
        })
        connection.commit()


def _sections(view):
    return {(section["extractionId"], section["sectionId"]): section for group in view["learningObjects"]
            for source in group["sources"] for section in source["sections"]}


def _figure_ids(view) -> dict[tuple[str, str], list[str]]:
    return {key: [figure["figureId"] for figure in section["figures"]]
            for key, section in _sections(view).items() if "figures" in section}


def test_a_figure_kept_in_a_corresponding_section_is_offered_from_it(tmp_path):
    _paths, repository, ctx, judge = _judged(tmp_path)
    _figure(repository, "fig_lay_eigen")
    _figure(repository, "fig_lay_failed", verification="failed", created_at="2026-10-30T00:00:01Z")
    # A figure in the open book is the learner's own book: it is never "also in your books".
    _figure(repository, "fig_book", extraction_id="ext_book", span_ids=("s2",))
    calls, before = judge.calls, table_counts(repository)
    view = call(ctx, "reader.correspondents", QUIET)
    assert table_counts(repository) == before and judge.calls == calls  # a read: no write, no model call
    assert view["status"] == "judged"
    assert _figure_ids(view) == {("ext_lay", "lay_eigen"): ["fig_lay_eigen"]}
    [entry] = _sections(view)[("ext_lay", "lay_eigen")]["figures"]
    assert entry["extractionId"] == "ext_lay" and entry["anchorSpanId"] == LAY_EIGEN_SPAN
    assert entry["verification"] == "illustrative" and entry["label"]
    # The line names the figure's home (its book and section) from the section it is listed under.
    home = _sections(view)[("ext_lay", "lay_eigen")]
    assert home["sourceTitle"] == "Lay" and home["title"] == "5.1 Eigenvectors and eigenvalues"
    # A section with no kept figure carries no key (the read is as before there).
    assert "figures" not in _sections(view)[("ext_lay", "lay_char")]
    # Nothing is mirrored into source objects (Q8).
    with repository.connection() as connection:
        mirrored = connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'source_objects'").fetchone()[0]
        if mirrored:
            assert connection.execute("SELECT COUNT(*) FROM source_objects WHERE id LIKE 'fig_%'").fetchone()[0] == 0


def test_switched_off_the_read_is_byte_identical(tmp_path):
    for name, config in (("reader_off", "[reader.correspondence]\nenabled = false"),
                         ("figures_off", "[figures]\nenabled = false")):
        _paths, repository, ctx, _judge = _judged(tmp_path / name, config=config)
        before = call(ctx, "reader.correspondents", QUIET)
        _figure(repository, "fig_lay_eigen")
        after = call(ctx, "reader.correspondents", QUIET)
        assert json.dumps(after, sort_keys=True) == json.dumps(before, sort_keys=True), name
        assert "figures" not in json.dumps(after), name


def test_a_figure_built_from_held_out_or_exam_material_is_never_offered(tmp_path):
    _paths, repository, ctx, _judge = _judged(tmp_path)
    _figure(repository, "fig_ok")
    # Anchored in lay_eigen, but its author was sent a held-out passage of lay_held.
    _figure(repository, "fig_held_input", input_span_ids=(LAY_EIGEN_SPAN, LAY_HELD_SPAN))
    # Anchored in lay_eigen, but grounded on the exam's question (a retrieved passage in another source).
    _figure(repository, "fig_exam_input", input_span_keys=(("ext_exam", "s1"),))
    # Anchored in the held-out section itself.
    _figure(repository, "fig_held_home", span_ids=(LAY_HELD_SPAN,))
    view = call(ctx, "reader.correspondents", QUIET)
    assert _figure_ids(view) == {("ext_lay", "lay_eigen"): ["fig_ok"]}
    serialized = json.dumps(view)
    for figure_id in ("fig_held_input", "fig_exam_input", "fig_held_home"):
        assert figure_id not in serialized


def test_protection_is_read_again_on_both_sides(tmp_path):
    _paths, repository, ctx, _judge = _judged(tmp_path)
    _figure(repository, "fig_lay_eigen")
    _figure(repository, "fig_lay_char", span_ids=(LAY_CHAR_SPAN,))
    assert _figure_ids(call(ctx, "reader.correspondents", QUIET)) == {
        ("ext_lay", "lay_eigen"): ["fig_lay_eigen"], ("ext_lay", "lay_char"): ["fig_lay_char"]}
    # The figure's side: its section held out after it was built leaves with its figure.
    hold_out(repository, "lay_char")
    view = call(ctx, "reader.correspondents", QUIET)
    assert _figure_ids(view) == {("ext_lay", "lay_eigen"): ["fig_lay_eigen"]}
    assert "fig_lay_char" not in json.dumps(view)
    # The open section's side: protected now, it has no correspondents and so offers no figure.
    save_unit_selection(repository, "ext_book", list(BOOK), exam_use_modes={BOOK_EIGEN: "held_out_evaluation"})
    view = call(ctx, "reader.correspondents", QUIET)
    assert view["status"] == "withheld" and "fig_" not in json.dumps(view)
    assert LAY  # the fixture's units (lay_held stays held out throughout)


def test_an_unreadable_figure_store_offers_no_figure_and_keeps_the_correspondents(tmp_path, monkeypatch):
    _paths, repository, ctx, _judge = _judged(tmp_path)
    _figure(repository, "fig_lay_eigen")

    def broken(*_args, **_kwargs):
        raise RuntimeError("the figures could not be read")

    monkeypatch.setattr(FS, "section_figures", broken)
    view = call(ctx, "reader.correspondents", QUIET)
    assert view["status"] == "judged" and ("ext_lay", "lay_eigen") in _sections(view)
    assert _figure_ids(view) == {}


def test_the_quiet_read_never_reverifies_an_outdated_sketch_or_writes(tmp_path, monkeypatch):
    """Codex review F3: a sketch built under an older engine is re-verified
    (and its verdict appended to ``judgment_ledger``) only when its own book's
    figures are listed for showing, never by the correspondents read, which
    stays a read: no verification run, no row written, in any section."""

    import learnloop.figures.sketch_verify as SV
    from learnloop.figures import sketch as K
    from tests import sketch_fixtures as SF

    _paths, repository, ctx, _judge = _judged(tmp_path)
    for figure_id, span in (("fig_sketch_old", LAY_EIGEN_SPAN), ("fig_sketch_elsewhere", "s12")):
        with repository.connection() as connection:
            store.insert_figure(connection, {
                "id": figure_id, "extraction_id": "ext_lay", "span_ids": [span], "input_span_ids": [span],
                "origin": "selection", "spec_json": json.dumps(SF.walk()), "spec_version": K.SKETCH_VERSION,
                "tier": "sketch", "kind": "illustrative", "verification": "illustrative",
                "verification_report": {}, "engine_sha256": "an-older-engine", "model": "fake",
                "prompt_version": "v1", "input_hash": f"hash_{figure_id}", "created_at": "2026-10-30T00:00:00Z",
            })
            connection.commit()
    FS._RECHECKED.clear()
    verified: list[object] = []
    real = SV.verify_sketch

    def counting(compiled, **kwargs):
        verified.append(compiled)
        return real(compiled, **kwargs)

    monkeypatch.setattr(SV, "verify_sketch", counting)
    before = table_counts(repository)
    view = call(ctx, "reader.correspondents", QUIET)
    assert verified == [] and table_counts(repository) == before
    # Offered (whether it still runs is decided when it is opened).
    assert _figure_ids(view) == {("ext_lay", "lay_eigen"): ["fig_sketch_old"]}
    # Opening it (its own book's listing) re-verifies and records the verdict, as before.
    listed = call(ctx, "reader.figures", {"extractionId": "ext_lay"})["figures"]
    assert {figure["figureId"] for figure in listed} >= {"fig_sketch_old"}
    assert verified and table_counts(repository)["judgment_ledger"] > before["judgment_ledger"]
