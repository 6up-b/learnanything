"""The AD23 redesign round 7: AD's outputs over a reading with withheld blocks equal its outputs over
the same document as if those blocks had NEVER BEEN EXTRACTED, the comparison copy being built by
the real ingest derivation (``tests/ad_ingest_fakes``: Marker's and GLM-OCR's production
converters run over the document with the withheld blocks deleted; no stored derived column is
copied).

Compared, inside an operation: the worked-example map, the Reader's span-to-LO mapping, the dose
arm's feasible extras, the reading sweep's receipts, and the span aliases between two readings.
A property over generated documents (withheld header texts and positions, Marker-style block-id
paths and GLM-OCR-style heading-text paths, re-read pairs that differ only in withheld text), and
the verify's three probes. Fakes only: no model call.
"""

from __future__ import annotations

import random
from contextlib import closing

import pytest

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import LO
from tests.ad_ingest_fakes import GLM, MARKER, T0, Element, build_copy, never_extracted

OLD, NEW = "ext_ne_old", "ext_ne_new"
HEADERS = ["Worked Examples", "Worked Examples (continued)", "Exercises", "Solutions", "Examples",
           "Worked  Examples", "Worked\nExamples", "Chapter 2 Matrices", "Introduction", "Exercises for Section 5.3"]
TEXTS = ["Consider the matrix A and compute its determinant.", "Example 3. Compute the rank of B.",
         "Solution: the rank is two.", "We now define the trace of a square matrix.", "Repeated public text.",
         "1. 11 definition: the kernel of a linear map.", "Proof. Immediate from the definition.",
         "Repeated public text."]


def _hold(monkeypatch, keys) -> None:
    from learnloop.content.sources import exam_material

    material = exam_material.Material(spans=frozenset(keys))
    monkeypatch.setattr(exam_material, "held_out_material", lambda *_args, **_kwargs: material)


def _outputs(paths, readings: dict[str, list[Element]], visible: dict[str, list[str]]) -> dict:
    from learnloop.adaptive_difficulty import dose as D
    from learnloop.adaptive_difficulty.operation import ad_operation
    from learnloop.adaptive_difficulty.reading import sweep
    from learnloop.content.sources.span_aliases import computed_aliases
    from learnloop.reader.reader_progression import learning_objects_for_span

    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    out: dict = {}
    with ad_operation(vault, repository) as op, closing(connect(paths.sqlite_path, read_only=True)) as connection:
        for extraction in readings:
            out[("worked", extraction)] = sorted(op.view.worked_example_spans(connection, extraction))
            for span in visible[extraction]:
                out[("los", extraction, span)] = learning_objects_for_span(
                    op.vault, op.repository, extraction_id=extraction, span_id=span)
            feasible, infeasible, content = D.feasible_variants(
                vault, repository, connection, D.Boundary(visit_id="v_ne", extraction_id=extraction,
                                                          section_id="u_none"), [LO], view=op.view)
            out[("dose", extraction)] = (feasible, infeasible, content)
        if len(readings) == 2:
            out["aliases"] = sorted(computed_aliases(op.repository, OLD, NEW).items())
    sweep(load_vault(paths.root), Repository(paths.sqlite_path), as_of=T0.isoformat().replace("+00:00", "Z"),
          sweep_kind="backfill")
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        out["receipts"] = sorted(tuple(row) for row in connection.execute(
            "SELECT o.kind, o.subkind, o.learning_object_id, e.extraction_id, e.span_id FROM ad_reading_opportunities o "
            "JOIN source_exposure_events e ON e.id = o.source_id"))
    return out


def _compare(tmp_path, monkeypatch, readings: dict[str, list[Element]], withheld: set[tuple[str, str]], *,
             style: str, name: str = "case") -> tuple[dict, dict]:
    """``(protected outputs, never-extracted outputs)``: the protected copy holds every element with
    ``withheld`` held out; the other was ingested without them."""

    _hold(monkeypatch, withheld)
    spans = {extraction: {span for ext, span in withheld if ext == extraction} for extraction in readings}
    absent = {extraction: never_extracted(elements, spans[extraction]) for extraction, elements in readings.items()}
    visible = {extraction: [element.span_id for element in elements] for extraction, elements in absent.items()}
    cite = [(extraction, element.span_id) for extraction, elements in readings.items() for element in elements
            if element.kind == "text"]
    viewed = [(extraction, span) for extraction, spans_ in visible.items() for span in spans_]
    protected_paths = build_copy(tmp_path / name / "protected", readings, style=style, cite=cite, viewed=viewed,
                                 learning_object=LO)
    absent_paths = build_copy(tmp_path / name / "absent", absent, style=style, cite=cite, viewed=viewed,
                              learning_object=LO)
    return _outputs(protected_paths, readings, visible), _outputs(absent_paths, absent, visible)


def _document(rng: random.Random, prefix: str, *, style: str) -> list[Element]:
    elements = []
    for index in range(rng.randint(4, 8)):
        if index == 0 or rng.random() < 0.35:
            elements.append(Element(f"{prefix}{index}", "header", rng.choice(HEADERS), rng.choice((1, 2))))
        else:
            elements.append(Element(f"{prefix}{index}", "text", rng.choice(TEXTS)))
    if not any(element.kind == "text" for element in elements[1:]):
        elements.append(Element(f"{prefix}{len(elements)}", "text", TEXTS[0]))
    return elements


@pytest.mark.parametrize("style", [MARKER, GLM])
@pytest.mark.parametrize("seed", range(25))
def test_ad_reads_a_protected_reading_as_if_its_withheld_blocks_were_never_extracted(tmp_path, monkeypatch, style,
                                                                                    seed):
    """The property: over generated documents (header texts, levels and positions, which of them and
    which body blocks are withheld), every AD output compared equals the never-extracted copy's."""

    rng = random.Random(f"{style}:{seed}")
    elements = _document(rng, "s", style=style)
    headers = [element.span_id for element in elements if element.kind == "header"]
    texts = [element.span_id for element in elements if element.kind == "text"]
    held = set(rng.sample(headers, k=rng.randint(1, len(headers))))
    if len(texts) > 1 and rng.random() < 0.5:
        held.add(rng.choice(texts[:-1]))
    protected, absent = _compare(tmp_path, monkeypatch, {OLD: elements}, {(OLD, span) for span in held}, style=style)
    assert protected == absent


@pytest.mark.parametrize("style", [MARKER, GLM])
@pytest.mark.parametrize("seed", range(10))
def test_a_re_read_that_differs_only_in_withheld_text_aliases_as_never_extracted(tmp_path, monkeypatch, style, seed):
    """Two readings of one book that differ only in their withheld headers' text (and duplicated
    public blocks whose matching neighbours could decide an alias): the aliases, the mapping and the
    receipts equal the never-extracted pair's, and do not depend on the withheld text."""

    rng = random.Random(f"reread:{style}:{seed}")
    base = _document(rng, "o", style=style)
    if not any(element.text == "Repeated public text." for element in base):
        base.insert(1, Element("o_dup", "text", "Repeated public text."))
    held = {element.span_id for element in base if element.kind == "header"}
    old = base
    new = [Element(element.span_id.replace("o", "n", 1), element.kind,
                   rng.choice(HEADERS) if element.span_id in held else element.text, element.level) for element in base]
    new.append(Element("n_tail", "text", "Repeated public text."))
    withheld = {(OLD, span) for span in held} | {(NEW, span.replace("o", "n", 1)) for span in held}
    protected, absent = _compare(tmp_path, monkeypatch, {OLD: old, NEW: new}, withheld, style=style, name="a")
    assert protected == absent
    other = [element if element.span_id not in {span for _ext, span in withheld} else
             Element(element.span_id, element.kind, "Introduction", element.level) for element in new]
    protected_other, _absent = _compare(tmp_path, monkeypatch, {OLD: old, NEW: other}, withheld, style=style, name="b")
    assert protected_other == protected


# -- the verify's probes (closed-checklist verify 17) ---------------------------------------------------


@pytest.mark.parametrize("style", [MARKER, GLM])
def test_a_withheld_headings_text_never_decides_a_public_blocks_role_receipt_or_offer(tmp_path, monkeypatch, style):
    """Probes 1 and 2: withheld H reads "Worked Examples (continued)" or "Exercises"; public P under
    it has no lead cue; an earlier public worked example W is cited too. P's role, the sweep's
    receipt kind for its view, and the dose arm's extra worked example are the same for both texts
    and equal the never-extracted copy's (failed before: H's text, through P's stored inherited hint
    and path, decided them)."""

    def document(heading: str) -> list[Element]:
        # P (s3) sits under a visible "Worked Examples" heading by position; at ingest its stored hint
        # came from the nearer withheld H, so H's text decided whether it could be one at all.
        return [Element("s0", "header", "Worked Examples"), Element("s1", "text", "Example 3. Compute the rank of B."),
                Element("s2", "header", heading, 2), Element("s3", "text", "Consider the matrix A and compute its determinant."),
                Element("s4", "text", "We now define the trace of a square matrix.")]

    results = []
    for heading in ("Worked Examples (continued)", "Exercises"):
        protected, absent = _compare(tmp_path, monkeypatch, {OLD: document(heading)}, {(OLD, "s2")}, style=style,
                                     name=heading[:5])
        assert protected == absent
        results.append(protected)
    assert results[0] == results[1]


@pytest.mark.parametrize("style", [MARKER, GLM])
def test_a_withheld_headings_exact_text_never_decides_a_span_alias(tmp_path, monkeypatch, style):
    """Probe 3: a book read twice; the readings differ only in withheld H's exact text; duplicated
    public blocks sit under it. The aliases (and so which LO a visible exposure doses) do not depend
    on H's text and equal the never-extracted pair's (failed before: the stored section path, H's
    text in GLM-OCR's, scored the duplicate's match)."""

    def old(heading: str) -> list[Element]:
        # The duplicated block sits only under H in the old reading.
        return [Element("o0", "header", "Chapter 2 Matrices"), Element("o1", "header", heading, 2),
                Element("o2", "text", "Repeated public text."), Element("o3", "text", "We now define the trace.")]

    def new(heading: str) -> list[Element]:
        # The new reading has it before H and under it: H's text in the stored section path decided
        # which of the two it re-anchors to.
        return [Element("n0", "header", "Chapter 2 Matrices"), Element("n1", "text", "Repeated public text."),
                Element("n2", "header", heading, 2), Element("n3", "text", "Repeated public text."),
                Element("n4", "text", "A closing remark.")]

    withheld = {(OLD, "o1"), (NEW, "n2")}
    first, absent = _compare(tmp_path, monkeypatch, {OLD: old("Worked Examples"), NEW: new("Worked Examples")},
                             withheld, style=style, name="same")
    assert first == absent
    second, _ = _compare(tmp_path, monkeypatch, {OLD: old("Worked Examples"), NEW: new("Exercises")},
                         withheld, style=style, name="differs")
    assert second == first
