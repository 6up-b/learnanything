"""What other test files use from ``tests/test_reader_ca1_as_printed.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import base64
import hashlib
import io
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.ingest.originals import store_original_bytes
from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import create_basic_vault
from tests.source_inventory_helpers import _persist


ITEM = "pi_svd_define_001"
EXTRACTION = "ext_ca1"
RED, BLUE, GREEN, GREY = (220, 0, 0), (0, 0, 220), (0, 170, 0), (150, 0, 150)
#: (span, type, page, bbox, colour, own): the exercise's own blocks are red
#: (text) and green (its figure); a worked example sits between two of its
#: blocks (blue), another exercise below (blue), the figure's caption (purple, named GREY).
LAYOUT = (
    ("e1", "Text", 0, [72.0, 100.0, 540.0, 130.0], RED, True),
    ("w1", "Text", 0, [72.0, 140.0, 540.0, 170.0], BLUE, False),
    ("e2", "Text", 0, [72.0, 180.0, 540.0, 210.0], RED, True),
    ("f1", "Figure", 0, [72.0, 220.0, 300.0, 400.0], GREEN, True),
    ("c1", "Caption", 0, [72.0, 405.0, 300.0, 420.0], GREY, False),
    ("x9", "Text", 0, [72.0, 450.0, 540.0, 480.0], BLUE, False),
    ("e3", "Text", 1, [72.0, 50.0, 540.0, 80.0], RED, True),
)
OWN = [span for span, *_rest, own in LAYOUT if own]


def _call(ctx, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _pdf_bytes() -> bytes:
    """Two US-letter pages (612 x 792 pt at 72 dpi), each block a filled box."""

    pages = []
    for page in (0, 1):
        image = Image.new("RGB", (612, 792), "white")
        draw = ImageDraw.Draw(image)
        for _span, _type, block_page, bbox, colour, _own in LAYOUT:
            if block_page == page:
                draw.rectangle(bbox, fill=colour)
        pages.append(image)
    out = io.BytesIO()
    pages[0].save(out, format="PDF", resolution=72.0, save_all=True, append_images=pages[1:])
    return out.getvalue()


def _seed_book(root: Path, repository, *, with_pdf: bool = True) -> None:
    raw = _pdf_bytes()
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    if with_pdf:
        store_original_bytes(root, digest, raw)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, current_revision_id, "
            "reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            ("src_ca1", "pdf", "file:///nowhere/src_ca1.pdf", "Strang", "rev_ca1", 1,
             "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_ca1", "src_ca1", digest, None, "2026-01-01T00:00:00Z"))
        connection.commit()
    blocks = [DocumentBlock.build(span_id=span, block_type=kind, text=f"block {span}", ordinal=index, page=page,
                                  bbox=bbox, section_path=["6.1"])
              for index, (span, kind, page, bbox, _colour, _own) in enumerate(LAYOUT, start=1)]
    unit = DocumentUnit(unit_id="u61", label="6.1 Eigenvalues", ordinal=0, semantic_hash="sha256:u61",
                        page_start=0, page_end=1, span_ids=[block.span_id for block in blocks])
    ir = DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks, assets=[],
                    health=ExtractionHealth())
    _persist(repository, ir, revision_id="rev_ca1", extraction_id=EXTRACTION)


def _make_canonical(root: Path, *, relation: str = "verbatim", spans: list[str] | None = None) -> None:
    path = next(root.rglob(f"{ITEM}.yaml"))
    payload = read_yaml(path)
    payload["canonical_exercise"] = {"source_id": "src_ca1", "revision_id": "rev_ca1", "extraction_id": EXTRACTION,
                                     "span_ids": spans or OWN, "label": "Exercise 6.1.12", "relation": relation}
    # The statement is the exercise's text, as an import writes it (Codex
    # review of the Astra fixes, F1: a block the statement does not place is
    # never cropped for free).
    payload["prompt"] = " ".join(f"block {span}" for span, kind, *_rest in LAYOUT
                                 if span in (spans or OWN) and kind != "Figure")
    write_yaml(path, payload)


@pytest.fixture
def book(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    ctx = SidecarContext()
    ctx.load(paths.root)
    _vault, repository = ctx.require_vault()
    _seed_book(paths.root, repository)
    _make_canonical(paths.root)
    ctx.reload(maintenance=False)
    return paths, ctx, repository


@pytest.fixture
def warm(monkeypatch):
    """Not a check on your own (the D46 read is pinned; the real one is tested below)."""

    import learnloop.intent.checks as checks

    monkeypatch.setattr(checks, "served_check", lambda *args, **kwargs: None)


@pytest.fixture
def cold(monkeypatch):
    import learnloop.intent.checks as checks

    monkeypatch.setattr(checks, "served_check", lambda *args, **kwargs: {"cold": True, "locators_hidden": True})


def _image(data_url: str) -> Image.Image:
    assert data_url.startswith("data:image/png;base64,")
    return Image.open(io.BytesIO(base64.b64decode(data_url.split(",", 1)[1]))).convert("RGB")


def _share(image: Image.Image, colour: tuple[int, int, int]) -> float:
    """The share of pixels near ``colour`` (the PDF writer's JPEG blurs edges)."""

    near = sum(count for count, pixel in image.getcolors(image.width * image.height)
               if all(abs(a - b) < 60 for a, b in zip(pixel, colour, strict=True)))
    return near / (image.width * image.height)
