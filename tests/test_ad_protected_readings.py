"""The AD23 redesign round 8 (Option B): a reading the withheld material touches is ABSENT for AD's
reading signals. The closing test (it replaces round 7's ``test_ad_never_extracted.py``).

The oracle is an exact ROW DELETION (``tests.ad_ingest_fakes.delete_reading``): the same vault
with that reading's blocks, units, assets and reading events deleted, its items kept. No model of
extraction is needed for correctness. The builders are faithful to production (Marker with
``metadata.table_of_contents`` over several pages, GLM-OCR, Markdown from source text; production
``s{n}`` span ids, never renamed), and the withheld set comes from REAL marks: a held-out unit
mark (``save_unit_selection``, resolved by ``exam_material`` against the stored units, Marker's
page-range units included) and held-out assessment signals (``insert_unit_inventory``).

Asserted:
1. absence: every AD output on the protected vault equals the deleted copy's (25 seeds x 3 styles);
2. inertness: varying the withheld blocks (text, position, count) changes nothing;
3. clean parity: a clean reading's worked examples and sections are the Reader's and the
   incumbent's own (``role_keys``, ``learning_objects_for_*`` on the raw repository);
4. items from visible spans of a mixed reading are not over-withheld;
5. the epoch flips on marking and on release, and receipts and the dose arm follow;
6. verify 18's four probes, each passing or moot under B.

Fakes only: no network, no model call.
"""

from __future__ import annotations

import random
from contextlib import closing

import pytest

from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import LO
from tests.ad_ingest_fakes import GLM, MARKDOWN, MARKER, STYLES, T0, Element, build_vault, delete_reading, ingest_ir

EXT, CLEAN, REREAD = "ext_pr_mixed", "ext_pr_clean", "ext_pr_reread"
HEADERS = ["Worked Examples", "Worked Examples (continued)", "Exercises", "Solutions", "Chapter 2 Matrices",
           "Introduction", "Exercises for Section 5.3", "Worked\nExamples"]
TEXTS = ["Consider the matrix A and compute its determinant.", "Example 3. Compute the rank of B.",
         "Solution: the rank is two.", "We now define the trace of a square matrix.", "Repeated public text.",
         "1. 11 definition: the kernel of a linear map.", "Proof. Immediate from the definition."]
CLEAN_DOC = [Element("header", "Worked Examples", 1, 0), Element("text", "Example 1. Compute the trace of A.", 1, 0),
             Element("text", "Consider the matrix B and its determinant.", 1, 1),
             Element("header", "Exercises", 1, 1), Element("text", "Exercise 1. Invert C.", 1, 2)]


def _spans(elements, style) -> list[str]:
    return [block.span_id for block in ingest_ir(elements, style=style).blocks]


def _copy(root, style: str, mixed: list[Element], *, clean: list[Element] = CLEAN_DOC, reread: bool = True,
          view_only: str | None = None):
    """The mixed reading is its own book; the clean reading (and its re-read, the same revision)
    another: a mark on one book's reading makes that book protected, and the predicate then
    withholds its other, unmarked readings whole (rule 4)."""

    readings = {EXT: (style, mixed), CLEAN: (style, clean)}
    if reread:
        readings[REREAD] = (style, clean)
    cite = [(extraction, span) for extraction, (kind, elements) in readings.items()
            for span in _spans(elements, kind)]
    viewed = [key for key in cite if view_only is None or key[0] == view_only]
    return build_vault(root, readings, learning_object=LO, cite=cite, viewed=viewed,
                       books={EXT: "mixed", CLEAN: "clean", REREAD: "clean"})


def _units(paths, extraction):
    ir = Repository(paths.sqlite_path).load_document_ir(extraction)
    return [] if ir is None else list(ir.units)


def _mark(paths, *, unit: str | None = None, signal: list[str] | None = None, signal_unit: str | None = None) -> None:
    """Real marks on the mixed reading: a held-out unit (rule 3) and/or held-out signals."""

    repository = Repository(paths.sqlite_path)
    units = _units(paths, EXT)
    if unit is not None:
        save_unit_selection(repository, EXT, [u.unit_id for u in units], exam_use_modes={unit: "held_out_evaluation"})
    if signal:
        target = next(u for u in units if u.unit_id == (signal_unit or units[0].unit_id))
        repository.insert_unit_inventory(
            id=f"inv_{target.unit_id}", source_revision_id="rev_mixed", extraction_id=EXT, unit_id=target.unit_id,
            unit_semantic_hash=target.semantic_hash, inventory_profile="exam", inventory_schema_version=1,
            prompt_version="p", provider="fake", model="fake", made_as_role="exam",
            inventory={"assessment_signals": [{"held_out": True, "span_ids": list(signal)}]})


def _outputs(paths) -> dict:
    """Every AD reading output, inside one operation, then the sweep and the report's counts."""

    from learnloop.adaptive_difficulty import dose as D
    from learnloop.adaptive_difficulty import report as REP
    from learnloop.adaptive_difficulty.operation import ad_operation
    from learnloop.adaptive_difficulty.reading import VaultReadingMap, sweep
    from learnloop.content.sources.span_aliases import computed_aliases
    from learnloop.reader.reader_progression import learning_objects_for_section, learning_objects_for_span

    raw = Repository(paths.sqlite_path)
    spans = {extraction: [b.span_id for b in (raw.load_document_ir(extraction) or ingest_ir([], style=MARKER)).blocks]
             for extraction in (EXT, CLEAN, REREAD) if raw.get_extraction_run(extraction)}
    units = {extraction: [u.unit_id for u in _units(paths, extraction)] for extraction in spans}
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    out: dict = {}
    with ad_operation(vault, repository) as op, closing(connect(paths.sqlite_path, read_only=True)) as connection:
        mapping = VaultReadingMap(op.vault, op.repository, op.view)
        for extraction in spans:
            out[("worked", extraction)] = sorted(op.view.worked_example_spans(connection, extraction))
            out[("ir", extraction)] = op.repository.load_document_ir(extraction) is not None
            for span in spans[extraction]:
                out[("los", extraction, span)] = learning_objects_for_span(
                    op.vault, op.repository, extraction_id=extraction, span_id=span)
            for unit in units[extraction] + ["u_none"]:
                out[("section", extraction, unit)] = (
                    op.view.section_spans(extraction, unit),
                    learning_objects_for_section(op.vault, op.repository, extraction_id=extraction, section_id=unit))
                out[("dose", extraction, unit)] = D.feasible_variants(
                    vault, repository, connection, D.Boundary(visit_id="v_pr", extraction_id=extraction,
                                                              section_id=unit), [LO], reading_map=mapping, view=op.view)
        out["aliases"] = {(a, b): sorted(computed_aliases(op.repository, a, b).items())
                          for a in spans for b in spans if a != b}
    for extraction in spans:
        for unit in units[extraction]:
            out[("decide", extraction, unit)] = {k: v for k, v in D.decide(vault, repository, D.Boundary(
                visit_id=f"v_{unit}", extraction_id=extraction, section_id=unit)).as_dict().items() if k != "draw_id"}
    sweep(load_vault(paths.root), Repository(paths.sqlite_path), as_of=T0.isoformat().replace("+00:00", "Z"),
          sweep_kind="backfill")
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        out["receipts"] = sorted(tuple(row) for row in connection.execute(
            "SELECT o.kind, o.subkind, o.learning_object_id, e.extraction_id, e.span_id FROM ad_reading_opportunities o "
            "JOIN source_exposure_events e ON e.id = o.source_id"))
        report = REP.build(load_vault(paths.root), Repository(paths.sqlite_path), connection, sensitivity=False)
    out["protected_readings"] = report["protected_readings"]["readings"]
    return out


def _document(rng: random.Random) -> tuple[list[Element], dict]:
    """A mixed reading over several pages, and how it is marked: a held-out unit, signals, or both."""

    elements = []
    for index in range(rng.randint(4, 9)):
        page = index // 3
        if index == 0 or rng.random() < 0.35:
            elements.append(Element("header", rng.choice(HEADERS), rng.choice((1, 1, 2)), page))
        else:
            elements.append(Element("text", rng.choice(TEXTS), 1, page))
    if not any(element.kind == "text" for element in elements):
        elements.append(Element("text", TEXTS[0], 1, elements[-1].page))
    return elements, {"how": rng.choice(("unit", "signal", "both")), "rng": rng}


def _apply(paths, how: str, rng: random.Random) -> bool:
    """Marks the mixed reading; False when nothing could be marked (the case is then skipped)."""

    units = _units(paths, EXT)
    raw = Repository(paths.sqlite_path).load_document_ir(EXT)
    texts = [b.span_id for b in raw.blocks if b.block_type == "Text"]
    if not units or not texts:
        return False
    unit = rng.choice(units).unit_id if how in ("unit", "both") else None
    signal = rng.sample(texts, k=rng.randint(1, len(texts))) if how in ("signal", "both") else None
    _mark(paths, unit=unit, signal=signal)
    return True


@pytest.mark.parametrize("style", STYLES)
@pytest.mark.parametrize("seed", range(25))
def test_a_mixed_reading_reads_exactly_as_if_deleted(tmp_path, style, seed):
    """Property 1 (absence): the mixed reading, marked by real unit marks and signals, gives every AD
    output the copy with that reading's rows deleted gives; the clean readings stand in both."""

    rng = random.Random(f"absence:{style}:{seed}")
    elements, plan = _document(rng)
    protected = _copy(tmp_path / "protected", style, elements)
    deleted = _copy(tmp_path / "deleted", style, elements)
    marked = random.Random(f"mark:{style}:{seed}")
    if not _apply(protected, plan["how"], marked):
        pytest.skip("nothing to mark")
    _apply(deleted, plan["how"], random.Random(f"mark:{style}:{seed}"))
    from learnloop.adaptive_difficulty.material_view import detached_view

    view = detached_view(load_vault(protected.root), Repository(protected.sqlite_path))
    assert view.reading_withheld(EXT) and not view.reading_withheld(CLEAN)
    delete_reading(deleted.sqlite_path, EXT)
    left, right = _outputs(protected), _outputs(deleted)
    # The deleted copy has no blocks of EXT, so its per-span keys are absent; compare per-span keys
    # of the protected copy against "nothing" (every one is empty there).
    for key in [key for key in left if isinstance(key, tuple) and key[0] in ("los", "section", "dose", "decide")
                and key[1] == EXT]:
        value = left.pop(key)
        right.pop(key, None)
        assert value in ([], ([], []), (["none"], {"extra_worked_example": "no_unstudied_example",
                                                     "extra_question": "no_producer_result"}, {})) \
            or value.get("reason") == "protected_reading", (key, value)
    assert left == right
    assert any(row[3] == CLEAN for row in left["receipts"]) and not any(row[3] == EXT for row in left["receipts"])


@pytest.mark.parametrize("style", STYLES)
@pytest.mark.parametrize("seed", range(8))
def test_which_blocks_are_withheld_changes_nothing(tmp_path, style, seed):
    """Property 2 (inertness): two protected vaults whose mixed readings differ only in the
    withheld unit (its heading text, its position, how many blocks it holds), the visible
    elements the same, give equal outputs."""

    rng = random.Random(f"inert:{style}:{seed}")
    visible = [Element("header", "Chapter 2 Matrices", 1, 0), Element("text", TEXTS[3], 1, 0),
               Element("text", TEXTS[1], 1, 1)]

    def held(count: int, heading: str) -> list[Element]:
        return [Element("header", heading, 1, 2)] + [
            Element("text", f"Held exercise {k}: {rng.choice(TEXTS)}", 1, 2) for k in range(count)]

    results = []
    for variant in range(2):
        heading = rng.choice(HEADERS)
        unit = held(rng.randint(1, 3), heading)
        elements = visible + unit if variant == 0 or rng.random() < 0.5 else unit + visible
        paths = _copy(tmp_path / f"v{variant}", style, elements)
        units = _units(paths, EXT)
        # The held unit: the one holding its first body block (Markdown's headings are not blocks).
        held_span = next(block.span_id for block in Repository(paths.sqlite_path).load_document_ir(EXT).blocks
                         if block.text.startswith("Held exercise"))
        target = next(u.unit_id for u in units if held_span in u.span_ids)
        _mark(paths, unit=target)
        out = _outputs(paths)
        results.append({key: value for key, value in out.items()
                        if not (isinstance(key, tuple) and key[1] == EXT and key[0] != "worked")})
        assert out[("worked", EXT)] == [] and out[("ir", EXT)] is False
    assert results[0] == results[1]


@pytest.mark.parametrize("style", STYLES)
def test_a_clean_reading_is_read_as_the_reader_and_the_incumbent_read_it(tmp_path, style):
    """Property 3 (clean parity): no mark anywhere; AD's worked examples are the incumbent's
    ``role_keys``, and every span's and section's LOs and spans are the Reader's own on the raw
    repository (failed before at 8c404d2b2: the projection re-derived every reading's roles and
    paths, so Markdown roles were erased and Marker's changed)."""

    from learnloop.adaptive_difficulty.operation import ad_operation
    from learnloop.reader.reader_guidance import extraction_sections
    from learnloop.reader.reader_progression import learning_objects_for_section, learning_objects_for_span
    from learnloop.source_retrieval.corpus import role_keys

    paths = _copy(tmp_path, style, CLEAN_DOC, reread=False)
    vault, raw = load_vault(paths.root), Repository(paths.sqlite_path)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        incumbent = {span for extraction, span in role_keys(connection, [CLEAN], ("worked_example",))
                     if extraction == CLEAN}
    ir = raw.load_document_ir(CLEAN)
    rows, _blocks, _map = extraction_sections(ir)
    reader_spans = {str(row["id"]): [str(span) for span in row["span_ids"]] for row in rows}
    reader = {span: learning_objects_for_span(vault, raw, extraction_id=CLEAN, span_id=span) for span in
              [b.span_id for b in ir.blocks]}
    reader_sections = {unit: learning_objects_for_section(vault, raw, extraction_id=CLEAN, section_id=unit)
                       for unit in reader_spans}
    with ad_operation(vault, Repository(paths.sqlite_path)) as op, \
            closing(connect(paths.sqlite_path, read_only=True)) as connection:
        assert op.view.worked_example_spans(connection, CLEAN) == incumbent
        assert op.repository.load_document_ir(CLEAN) == ir
        for span, los in reader.items():
            assert learning_objects_for_span(op.vault, op.repository, extraction_id=CLEAN, span_id=span) == los
        for unit, los in reader_sections.items():
            assert op.view.section_spans(CLEAN, unit) == reader_spans[unit]
            assert learning_objects_for_section(op.vault, op.repository, extraction_id=CLEAN, section_id=unit) == los
    assert incumbent, "the clean reading has the incumbent's worked examples"


@pytest.mark.parametrize("style", STYLES)
def test_an_item_from_a_visible_span_of_a_mixed_reading_is_not_over_withheld(tmp_path, style):
    """Property 4: an item whose canonical exercise lies in a visible span of a mixed reading is
    judged by its own source, exactly as when the reading is clean; one on a withheld span is
    withheld."""

    from learnloop.adaptive_difficulty.operation import ad_operation

    from tests.ad23_fakes import set_item

    elements = [Element("header", "Chapter 2 Matrices", 1, 0), Element("text", TEXTS[3], 1, 0),
                Element("header", "Exercises", 1, 1), Element("text", "Exercise 1. Invert C.", 1, 1)]
    paths = _copy(tmp_path, style, elements, reread=False)
    blocks = Repository(paths.sqlite_path).load_document_ir(EXT).blocks
    visible_span = next(b.span_id for b in blocks if b.text == TEXTS[3])
    set_item(paths, "pi_m1a", canonical_exercise={"source_id": "src_mixed", "extraction_id": EXT,
                                                  "span_ids": [visible_span]})
    for marked in (False, True):
        if marked:
            units = _units(paths, EXT)
            _mark(paths, unit=units[-1].unit_id)
        vault = load_vault(paths.root)
        with ad_operation(vault, Repository(paths.sqlite_path)) as op:
            assert op.view.reading_withheld(EXT) is marked
            assert not op.view.withheld("pi_m1a") and "pi_m1a" in op.vault.practice_items
    held_span = next(b.span_id for b in blocks if b.text == "Exercise 1. Invert C.")
    set_item(paths, "pi_m1a", canonical_exercise={"source_id": "src_mixed", "extraction_id": EXT,
                                                  "span_ids": [held_span]})
    with ad_operation(load_vault(paths.root), Repository(paths.sqlite_path)) as op:
        assert op.view.withheld("pi_m1a")


@pytest.mark.parametrize("style", STYLES)
def test_marking_and_release_flip_the_epoch_and_the_reading_with_it(tmp_path, style):
    """Property 5: marking one unit of a clean reading makes it mixed: the epoch changes, its
    receipts go out of force, the dose arm stops at its boundaries. Releasing the mark restores
    the epoch exactly, and the receipts with it."""

    from learnloop.adaptive_difficulty import dose as D
    from learnloop.adaptive_difficulty.material_view import detached_view
    from learnloop.adaptive_difficulty.reading import sweep

    elements = [Element("header", "Chapter 2 Matrices", 1, 0), Element("text", TEXTS[3], 1, 0),
                Element("header", "Exercises", 1, 1), Element("text", "Exercise 1. Invert C.", 1, 1)]
    paths = _copy(tmp_path, style, elements, reread=False, view_only=EXT)

    def state() -> tuple[str | None, int]:
        view = detached_view(load_vault(paths.root), Repository(paths.sqlite_path))
        with closing(connect(paths.sqlite_path, read_only=True)) as connection:
            mixed = [row for row in view.reading_opportunities(connection)
                     if str(row.get("source_table")) == "source_exposure_events"
                     and connection.execute("SELECT extraction_id FROM source_exposure_events WHERE id = ?",
                                            (row["source_id"],)).fetchone()[0] == EXT]
        return view.epoch, len(mixed)

    sweep(load_vault(paths.root), Repository(paths.sqlite_path), as_of=T0.isoformat().replace("+00:00", "Z"),
          sweep_kind="backfill")
    clean_epoch, receipts = state()
    assert receipts > 0
    units = _units(paths, EXT)
    repository = Repository(paths.sqlite_path)
    save_unit_selection(repository, EXT, [u.unit_id for u in units], exam_use_modes={units[-1].unit_id: "held_out_evaluation"})
    marked_epoch, marked_receipts = state()
    assert marked_epoch != clean_epoch and marked_receipts == 0
    decision = D.decide(load_vault(paths.root), Repository(paths.sqlite_path),
                        D.Boundary(visit_id="v_epoch", extraction_id=EXT, section_id=units[0].unit_id))
    assert (decision.eligible, decision.reason) == (False, "protected_reading")
    save_unit_selection(repository, EXT, [u.unit_id for u in units], exam_use_modes={})
    released_epoch, released_receipts = state()
    assert released_epoch == clean_epoch and released_receipts == receipts


# -- verify 18's probes, under Option B ----------------------------------------------------------------


def test_probe_marker_toc_page_range_units(tmp_path):
    """F1 (Marker TOC units): a withheld "Exercises" header opened a page-range unit labelled with
    its own text over visible blocks. Under B the reading is absent: no unit, label or mapping of it
    reaches AD, as in the deleted copy (moot by absence)."""

    elements = [Element("header", "Chapter 2 Matrices", 1, 0), Element("text", TEXTS[3], 1, 0),
                Element("text", "Repeated public text.", 1, 1), Element("header", "Exercises", 1, 1),
                Element("text", "Solution: the rank is two.", 1, 1), Element("text", TEXTS[6], 1, 2)]
    protected = _copy(tmp_path / "p", MARKER, elements, reread=False)
    deleted = _copy(tmp_path / "d", MARKER, elements, reread=False)
    exercises = next(b.span_id for b in Repository(protected.sqlite_path).load_document_ir(EXT).blocks
                     if b.text == "Exercises")
    for paths in (protected, deleted):
        _mark(paths, signal=[exercises])
    delete_reading(deleted.sqlite_path, EXT)
    left, right = _outputs(protected), _outputs(deleted)
    assert left[("ir", EXT)] is False and all(not left[key][1] for key in left if key[0:2] == ("section", EXT))
    assert left["receipts"] == right["receipts"] and left["aliases"] == right["aliases"]


def test_probe_raw_section_membership_in_the_dose_arm(tmp_path):
    """F3 (raw section membership): the dose arm read a section's spans from the raw reading. Under
    B ``section_spans`` reads only through the chokepoint: nothing for a mixed reading, and the
    boundary is ineligible before any draw (passes)."""

    from learnloop.adaptive_difficulty import dose as D
    from learnloop.adaptive_difficulty.material_view import detached_view

    elements = [Element("header", "Worked Examples", 1, 0), Element("text", TEXTS[3], 1, 0),
                Element("header", "Exercises", 1, 0), Element("text", TEXTS[1], 1, 0), Element("text", TEXTS[6], 1, 0)]
    paths = _copy(tmp_path, GLM, elements, reread=False)
    exercises = next(b.span_id for b in Repository(paths.sqlite_path).load_document_ir(EXT).blocks
                     if b.text == "Exercises")
    _mark(paths, signal=[exercises])
    view = detached_view(load_vault(paths.root), Repository(paths.sqlite_path))
    assert all(view.section_spans(EXT, unit.unit_id) == [] for unit in _units(paths, EXT))
    decision = D.decide(load_vault(paths.root), Repository(paths.sqlite_path),
                        D.Boundary(visit_id="v_f3", extraction_id=EXT, section_id=_units(paths, EXT)[0].unit_id))
    assert (decision.eligible, decision.reason) == (False, "protected_reading")


def test_probe_markdown_level_two_fallback(tmp_path):
    """The Markdown ``##`` fallback: one withheld body block decided the units' granularity. Under B
    a Markdown reading with any withheld block is absent, so its units never reach AD; a clean one
    is read as stored (moot by absence; the clean case passes)."""

    from learnloop.adaptive_difficulty.operation import ad_operation

    elements = [Element("header", "A", 1), Element("header", "A1", 2), Element("text", "alpha one text."),
                Element("header", "A2", 2), Element("text", "alpha two text."), Element("header", "B", 1),
                Element("text", "withheld exam question text.")]
    paths = _copy(tmp_path, MARKDOWN, elements, reread=False)
    held = next(b.span_id for b in Repository(paths.sqlite_path).load_document_ir(EXT).blocks
                if b.text.startswith("withheld"))
    stored = Repository(paths.sqlite_path).load_document_ir(CLEAN)
    _mark(paths, signal=[held])
    with ad_operation(load_vault(paths.root), Repository(paths.sqlite_path)) as op:
        assert op.repository.load_document_ir(EXT) is None
        assert op.repository.load_document_ir(CLEAN) == stored


def test_probe_candidates_are_taken_in_reading_order_not_span_id_order(tmp_path):
    """F2 (positional span ids): with ten or more blocks "s10" sorts before "s9". The dose arm takes
    its extra worked example in reading order (the stored ordinal) on a clean reading (passes;
    failed before at 8c404d2b2: the first example by span-id string was offered)."""

    from learnloop.adaptive_difficulty import dose as D
    from learnloop.adaptive_difficulty.operation import ad_operation
    from learnloop.adaptive_difficulty.reading import VaultReadingMap

    plain = [Element("text", f"We now define object number {index} of the chapter.") for index in range(7)]
    clean = [Element("header", "Chapter 2 Matrices"), *plain, Element("text", "Example 3. Compute the rank of B."),
             Element("text", "Example 4. Compute the rank of C.")]
    paths = _copy(tmp_path, GLM, [Element("text", "Unrelated.")], clean=clean, reread=False)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    blocks = repository.load_document_ir(CLEAN).blocks
    first = next(b.span_id for b in blocks if b.text.startswith("Example 3"))
    assert first == "s9" and next(b.span_id for b in blocks if b.text.startswith("Example 4")) == "s10"
    with ad_operation(vault, repository) as op, closing(connect(paths.sqlite_path, read_only=True)) as connection:
        mapping = VaultReadingMap(op.vault, op.repository, op.view)
        _feasible, _infeasible, content = D.feasible_variants(
            vault, repository, connection, D.Boundary(visit_id="v_f2", extraction_id=CLEAN, section_id="u_none"),
            [LO], reading_map=mapping, view=op.view)
    assert content["extra_worked_example"]["span_id"] == first
