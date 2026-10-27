"""Reader CA1, the landing finding: a block carrying Unicode math is read in
the form the import wrote it, so a verbatim statement still gets its free
crop, and containment is otherwise exactly as strict.

The import passes each selected part through ``unicode_math_to_latex``
("exist λ ∈ 𝐅" becomes "exist $\\lambda \\in F$"), so the prompt holds the
converted text while the extraction keeps the Unicode. A real PDF is drawn
here (no book text is committed); every model is a fake.
"""

from __future__ import annotations

import hashlib
import io

import pytest
from PIL import Image, ImageDraw

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.content.sources.math_text import unicode_math_to_latex
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.ingest.originals import store_original_bytes
from learnloop.reader.as_printed import NO_CROP, _contained
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.test_reader_ca1_as_printed import RED, _call, _image, _share, book, warm  # noqa: F401 - fixtures
from tests.test_source_inventory import _persist

EXT = "ext_ca1_unicode"
NOW_ISO = "2026-01-01T00:00:00Z"
STEM = "Explain why there does not exist λ ∈ 𝐅 such that λ² = −1."
#: (span, bbox, text): an Axler-style exercise, the same with an answer
#: after it, and a second exercise.
LAYOUT = (
    ("x1", [72.0, 100.0, 540.0, 140.0], f"10 {STEM}"),
    ("x2", [72.0, 200.0, 540.0, 240.0], f"11 {STEM} The answer: none exists."),
    ("x3", [72.0, 300.0, 540.0, 340.0], "12 Show that x ∈ ℝ has x² ≥ 0."),
)


def _converted(text: str) -> str:
    return unicode_math_to_latex(text)[0]


@pytest.fixture
def seeded(book):
    paths, ctx, repository = book
    image = Image.new("RGB", (612, 792), "white")
    draw = ImageDraw.Draw(image)
    for _span, bbox, _text in LAYOUT:
        draw.rectangle(bbox, fill=RED)
    out = io.BytesIO()
    image.save(out, format="PDF", resolution=72.0)
    raw = out.getvalue()
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    store_original_bytes(paths.root, digest, raw)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, current_revision_id, "
            "reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            ("src_uni", "pdf", "file:///nowhere/book.pdf", "Axler", "rev_uni", 1, NOW_ISO, NOW_ISO))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_uni", "src_uni", digest, None, NOW_ISO))
        connection.commit()
    blocks = [DocumentBlock.build(span_id=span, block_type="Text", text=text, ordinal=index, page=0, bbox=bbox,
                                  section_path=["1.B"])
              for index, (span, bbox, text) in enumerate(LAYOUT, start=1)]
    unit = DocumentUnit(unit_id="u_uni", label="1.B", ordinal=0, semantic_hash="sha256:u_uni", page_start=0,
                        page_end=0, span_ids=[block.span_id for block in blocks])
    ir = DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks, assets=[],
                    health=ExtractionHealth())
    _persist(repository, ir, revision_id="rev_uni", extraction_id=EXT)
    return paths, ctx, repository


def _import(paths, repository, span: str, statement: str) -> str:
    """A Reader import whose author echoes the converted text verbatim (the
    landing's case D)."""

    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
    from tests.test_exercise_authoring import FakeClient, _item, _write_facet_registry

    _write_facet_registry(paths.root.parent)
    text = next(text for name, _bbox, text in LAYOUT if name == span)
    raw = {"nodes": [{"spanId": span, "quote": text}]}
    client = FakeClient(ExerciseAuthoring(items=[_item(statement_md=statement, expected_answer_md="none")]))
    (summary,) = EX.import_exercises(paths.root, repository, client, extraction_id=EXT, raw_selection=raw,
                                     source_id="src_uni")["items"]
    return summary["practice_item_id"]


def _view(ctx, item_id: str) -> dict:
    ctx.reload(maintenance=False)
    return _call(ctx, "practice.as_printed", {"practiceItemId": item_id, "render": True})


def _no_free_crop(view: dict, span: str) -> None:
    assert view["kind"] == "page" and view["crops"] == [] and view["notice"] == NO_CROP
    assert view["originalPage"]["spanId"] == span


def test_a_verbatim_import_of_unicode_math_gets_its_free_crop(seeded, warm):
    paths, ctx, repository = seeded
    item_id = _import(paths, repository, "x1", _converted(STEM))
    prompt = read_yaml(next(paths.root.rglob(f"{item_id}.yaml")))["prompt"]
    assert "$" in prompt and "∈" not in prompt                         # the import converted it
    view = _view(ctx, item_id)
    assert [crop["spanIds"] for crop in view["crops"]] == [["x1"]]
    assert _share(_image(view["crops"][0]["image"]), RED) > 0.9


def test_an_answer_after_the_converted_statement_still_gives_no_free_crop(seeded, warm):
    paths, ctx, repository = seeded
    item_id = _import(paths, repository, "x2", _converted(STEM))
    _no_free_crop(_view(ctx, item_id), "x2")


def test_a_statement_that_only_partly_covers_the_converted_block_gives_no_free_crop(seeded, warm):
    paths, ctx, repository = seeded
    # The statement is the first half of the exercise: the rest of the block follows it.
    item_id = _import(paths, repository, "x3", _converted("12 Show that x ∈ ℝ"))
    _no_free_crop(_view(ctx, item_id), "x3")


def test_a_statement_reaching_past_what_prints_gives_no_free_crop(seeded, warm):
    paths, ctx, repository = seeded
    item_id = _import(paths, repository, "x1", _converted(STEM))
    path = next(paths.root.rglob(f"{item_id}.yaml"))
    payload = read_yaml(path)
    payload["prompt"] = payload["prompt"] + " Then do the same over $\\mathbb{C}$."
    write_yaml(path, payload)
    _no_free_crop(_view(ctx, item_id), "x1")


def test_containment_reads_the_converted_form_and_nothing_more():
    block = f"10 {STEM}"
    inside, part = _contained(block, _converted(STEM))
    assert inside and part is not None                                  # "10" is a label
    assert _contained(block, STEM)[0]                                   # the printed form still places
    assert not _contained(f"{STEM} The answer: none exists.", _converted(STEM))[0]
    assert not _contained(f"The answer is 4. {STEM}", _converted(STEM))[0]
    assert not _contained(block, "Explain why there does not exist")[0]
