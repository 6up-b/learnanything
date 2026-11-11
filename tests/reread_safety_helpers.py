"""What other test files use from ``tests/test_reread_safety.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pypdf import PdfWriter

from learnloop.content.pipeline import add_source as core
from learnloop.content.pipeline.runner import JobSpec
from learnloop.db.repositories import Repository
from learnloop.ingest.hashing import asset_hash, extraction_request_hash, extraction_result_hash
from learnloop.ingest.ir import IR_SCHEMA_VERSION, DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.vault.models import SourceRef
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.ux_phase1_support import fake_services, fresh_library


def call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


@dataclass
class TickingClock:
    instant: datetime

    def now(self) -> datetime:
        return self.instant

    def advance(self, minutes: int = 1) -> None:
        self.instant = self.instant + timedelta(minutes=minutes)


def _clock() -> TickingClock:
    return TickingClock(datetime(2026, 10, 14, 9, 0, 0, tzinfo=UTC))


_A_TEXT = {
    "a0": ("SectionHeader", 13, ["1 Vectors"], "1 Vectors"),
    "a1": ("Text", 13, ["1 Vectors"], "A vector space is a set with addition and scalar multiplication."),
    "a2": ("Text", 13, ["1 Vectors"], "Every vector space has a zero vector."),
    "a3": ("Text", 14, ["1 Vectors"], "A list of vectors is linearly independent when only the trivial combination is zero."),
    "a4": ("SectionHeader", 15, ["2 Spans"], "2 Spans"),
    "a5": ("Text", 15, ["2 Spans"], "The span of a list is the set of all linear combinations of it."),
    "a6": ("SectionHeader", 16, ["3 Exam review"], "3 Exam review"),
    "a7": ("Text", 16, ["3 Exam review"], "Exam problem: prove that the zero vector is unique."),
}
_B_TEXT = {
    "b0": ("SectionHeader", 13, ["1 Vectors"], "1 Vectors"),
    "b1": ("Text", 13, ["1 Vectors"], "A vector space is a set with addition and scalar multiplication."),
    "b2": ("Text", 13, ["1 Vectors"], "Every vector space has a zero vector 0."),
    "b3": ("Text", 14, ["1 Vectors"], "A list of vectors is linearly independent when only the trivial combination is zero."),
    "b4": ("SectionHeader", 15, ["2 Spans"], "2 Spans"),
    "b5": ("Text", 15, ["2 Spans"], "Spans, in new words, part one."),
    "b6": ("Text", 15, ["2 Spans"], "Spans, in new words, part two."),
    "b7": ("SectionHeader", 16, ["3 Exam review"], "3 Exam review"),
    "b8": ("Text", 16, ["3 Exam review"], "Exam problem: prove that the zero vector is unique."),
}
EXACT, MOVED, GONE = "a1", "a2", "a5"


def _ir(texts, units, *, extractor: str) -> DocumentIR:
    blocks = [
        DocumentBlock.build(span_id=span, block_type=kind, text=text, ordinal=index, page=page, section_path=path)
        for index, (span, (kind, page, path, text)) in enumerate(texts.items())
    ]
    return DocumentIR(
        extractor=extractor, extractor_version="1", blocks=blocks,
        units=[DocumentUnit(unit_id=unit_id, label=label, ordinal=index, semantic_hash=semantic,
                            page_start=13, page_end=16, span_ids=spans)
               for index, (unit_id, label, semantic, spans) in enumerate(units)],
        assets=[], health=ExtractionHealth(),
    )


def reading_a() -> DocumentIR:
    return _ir(_A_TEXT, [
        ("u1", "1 Vectors", "sha256:a-u1", ["a0", "a1", "a2", "a3"]),
        ("u2", "2 Spans", "sha256:a-u2", ["a4", "a5"]),
        ("u3", "3 Exam review", "sha256:u3", ["a6", "a7"]),
    ], extractor="marker")


def reading_b() -> DocumentIR:
    return _ir(_B_TEXT, [
        ("h1", "1 Vectors", "sha256:b-h1", ["b0", "b1", "b2", "b3"]),
        ("h2", "2 Spans", "sha256:b-h2", ["b4", "b5", "b6"]),
        ("h3", "3 Exam review", "sha256:u3", ["b7", "b8"]),
    ], extractor="glm_ocr")


def _persist(repo: Repository, ir: DocumentIR, *, revision_id: str, extraction_id: str, clock,
             page_selection=None) -> str:
    request_hash = extraction_request_hash(
        revision_id=revision_id, extractor=ir.extractor, extractor_version=ir.extractor_version,
        page_selection=page_selection, ir_schema_version=IR_SCHEMA_VERSION,
    )
    repo.insert_extraction_run(
        id=extraction_id, revision_id=revision_id, extractor=ir.extractor, extractor_version=ir.extractor_version,
        extraction_request_hash=request_hash, ir_schema_version=IR_SCHEMA_VERSION, page_selection=page_selection,
        status="running", clock=clock,
    )
    repo.persist_document_ir(extraction_id, ir)
    repo.complete_extraction_run(extraction_id, extraction_result_hash=extraction_result_hash(request_hash, ir),
                                 clock=clock)
    return extraction_id


def _made_on(extraction_id: str, revision_id: str) -> dict:
    """The selection metadata a writer records with the marks it makes on a
    reading (exam protection by extraction identity): these tests' marks are
    the owner's, exact. A mark without it is a legacy one (ambiguous)."""

    from learnloop.content.sources.exam_material import MARKS_MADE_ON_KEY, marks_made_on

    return {MARKS_MADE_ON_KEY: marks_made_on(extraction_id, revision_id)}


# --- a seeded library: one book, its reading, the learner's study state ---------------


@pytest.fixture
def studied(tmp_path):
    """A basic vault holding one book read once (``extA``), with progress, a
    selection with a held-out unit, YAML refs, a facet link, source-object
    citations and annotations on it; then a second reading (``extB``)."""

    from learnloop.reader import annotations as ANN
    from learnloop.reader import source_objects as SO
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_basic_vault
    from tests.source_inventory_helpers import _register_revision

    clock = _clock()
    paths = create_basic_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)
    _register_revision(repo, source_id="src1", revision_id="rev1")
    repo.set_source_current_revision("src1", "rev1")
    _persist(repo, reading_a(), revision_id="rev1", extraction_id="extA", clock=clock, page_selection=list(range(13, 39)))
    clock.advance()
    # Progress: section u1 read through, u2 partly.
    repo.upsert_reader_section_progress(extraction_id="extA", section_id="u1", spans_seen=4, span_count=4,
                                        revealed=True, completed=True, clock=clock)
    repo.mark_section_generation(extraction_id="extA", section_id="u1", batch_id="batch_u1")
    repo.upsert_reader_section_progress(extraction_id="extA", section_id="u2", spans_seen=1, span_count=2,
                                        clock=clock)
    repo.upsert_unit_selection(extraction_id="extA", source_id="src1", revision_id="rev1",
                               selected_unit_ids=["u1", "u2", "u3"], exam_use_modes={"u3": "held_out_evaluation"},
                               exam_paper_metadata=_made_on("extA", "rev1"))
    repo.insert_entity_source_link(entity_type="facet", entity_id="facet_x", locator=f"span:extA/{EXACT}",
                                   relation="primary", source_id="src1", revision_id="rev1", extraction_id="extA")
    repo.insert_entity_source_link(entity_type="facet", entity_id="facet_y", locator=f"span:extA/{MOVED}",
                                   relation="primary", source_id="src1", revision_id="rev1", extraction_id="extA")
    # Citations made before the book was read again (no block hash, as in the owner's books).
    SO.author_source_object(repo, source_id="src1", revision_id="rev1", object_type="definition",
                            authorial_role="definition",
                            citations=[{"span_id": EXACT}, {"span_id": MOVED}, {"span_id": GONE}], clock=clock)
    annotations = {}
    for span_id, quote in ((EXACT, "vector space"), (MOVED, "zero vector")):
        translation = ANN.translate_selection(repo, extraction_id="extA",
                                              raw_selection={"nodes": [{"span_id": span_id, "quote": quote}]})
        annotations[span_id] = ANN.append_annotation(repo, source_id="src1", revision_id="rev1", extraction_id="extA",
                                                     annotation_type="highlight", translation=translation,
                                                     clock=clock)["annotation_id"]
    clock.advance()
    vault = load_vault(paths.root)
    # An active practice item citing three passages of the old reading.
    item = vault.practice_items["pi_svd_define_001"]

    def refs(*spans):
        return [SourceRef(ref_type="canonical_source", ref_id="src1", locator=f"span:extA/{span}", source_id="src1",
                          extraction_id="extA") for span in spans]

    item.provenance.source_refs = refs(EXACT, MOVED, GONE)
    # Its learning object cites the first passage (the Reader's LO highlight).
    vault.learning_objects[item.learning_object_id].provenance.source_refs = refs(EXACT)
    return {"root": paths.root, "repo": repo, "vault": vault, "clock": clock, "annotations": annotations}


def _reread(studied, *, carry: bool = True) -> str:
    _persist(studied["repo"], reading_b(), revision_id="rev1", extraction_id="extB", clock=studied["clock"],
             page_selection=list(range(13, 39)))
    if carry:
        from learnloop.content.pipeline.reread import carry_over

        carry_over(studied["repo"], "extB", clock=studied["clock"])
    return "extB"


def _blank_pdf(path: Path, pages: int) -> Path:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    buffer = io.BytesIO()
    writer.write(buffer)
    # A NUL in the header's binary comment, as a real book's compressed
    # streams carry near its start (same length: offsets stay valid). It makes
    # an extensionless copy of the file unclassifiable, as the owner's books
    # in the originals store are (GLM-OCR live run, 2026-10-14).
    raw = buffer.getvalue().replace(b"%\xe2\xe3\xcf\xd3", b"%\x00\xe3\xcf\xd3", 1)
    path.write_bytes(raw)
    return path


LFS_POINTER = (
    b"version https://git-lfs.github.com/spec/v1\n"
    b"oid sha256:b40b1da1c4f0aa1e0bfc2bdc0f2f2a1c84e5b0d8f3a6c9e2b7d4f1a0c3e5b7d9\n"
    b"size 2795246\n"
)


class Readings:
    """A fake extractor: the first reading is Marker-shaped, a re-read with
    text recognition segments differently. Records what each read was given."""

    def __init__(self, *, fail_reread: bool = False) -> None:
        self.seen: list[dict] = []
        self.fail_reread = fail_reread
        # Called while a reading runs: what the Library resolves the book to then.
        self.during = None

    @staticmethod
    def _reread(ctx) -> bool:
        config = ctx.payload.get("pdf_config") or {}
        return bool(config.get("force_ocr")) or config.get("engine") == "glm_ocr"

    def identity(self, fetched, category, ctx):
        reread = self._reread(ctx)
        return {"extractor": "glm_ocr" if reread else "marker", "extractor_version": "1", "model_versions": {},
                "config": dict(ctx.payload.get("pdf_config") or {})}

    def extract(self, fetched, category, ctx):
        reread = self._reread(ctx)
        self.seen.append({"sha": asset_hash(fetched.raw_bytes), "pages": ctx.payload.get("page_selection"),
                          "reread": reread})
        if self.during is not None:
            self.seen[-1]["during"] = self.during()
        if reread and self.fail_reread:
            raise RuntimeError("the reading failed")
        return reading_b() if reread else reading_a()


def _card_ctx(root, readings: Readings, clock):
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=clock,
                         services=fake_services(extract=readings.extract, describe_extraction=readings.identity,
                                                background_key_checks=False))
    return ctx


@pytest.fixture
def card_book(tmp_path, monkeypatch):
    """A 40-page book read on pages 14-39 through the import queue."""

    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "global_settings"))
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.setattr(core, "text_recognition_available", lambda **_: True)
    root = fresh_library(tmp_path)
    clock = _clock()
    readings = Readings()
    ctx = _card_ctx(root, readings, clock)
    book = _blank_pdf(tmp_path / "axler.pdf", 40)
    ctx.ingest_jobs._require_runner().enqueue_batch(
        "import", [JobSpec("import", {"source": str(book), "page_selection": list(range(13, 39))})])
    ctx.ingest_jobs.drain_foreground()
    (artifact,) = ctx.repository.all_source_artifacts()
    clock.advance()
    return {"root": root, "ctx": ctx, "book": book, "source_id": artifact["id"], "readings": readings,
            "clock": clock}


_EXAM_Q = "Exam question: prove that every eigenvalue of a self-adjoint operator is real."
_THEORY = "Theory: a self-adjoint operator has only real eigenvalues, by the spectral theorem."


def _exam_reading_a() -> DocumentIR:
    return _ir({"x0": ("SectionHeader", 1, ["Exam"], "Exam"), "x1": ("Text", 1, ["Exam"], _EXAM_Q),
                "x2": ("SectionHeader", 2, ["Theory"], "Theory"), "x3": ("Text", 2, ["Theory"], _THEORY)},
               [("u1", "Exam", "sha256:exam-a", ["x0", "x1"]), ("u2", "Theory", "sha256:theory-a", ["x2", "x3"])],
               extractor="marker")


def _exam_reading_b() -> DocumentIR:
    """The re-read reuses A's unit ids for the other units: u1 is Theory here."""

    return _ir({"y0": ("SectionHeader", 2, ["Theory"], "Theory"), "y1": ("Text", 2, ["Theory"], _THEORY),
                "y2": ("SectionHeader", 1, ["Exam"], "Exam"), "y3": ("Text", 1, ["Exam"], _EXAM_Q)},
               [("u1", "Theory", "sha256:theory-b", ["y0", "y1"]), ("u2", "Exam", "sha256:exam-b", ["y2", "y3"])],
               extractor="glm_ocr")


@pytest.fixture
def exam_book(tmp_path):
    from tests.helpers import create_basic_vault
    from tests.source_inventory_helpers import _register_revision

    clock = _clock()
    paths = create_basic_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)
    _register_revision(repo, source_id="src_x", revision_id="rev_x")
    repo.set_source_current_revision("src_x", "rev_x")
    _persist(repo, _exam_reading_a(), revision_id="rev_x", extraction_id="extXA", clock=clock)
    clock.advance()
    return {"repo": repo, "clock": clock, "root": paths.root}


def _exam_sets(*, default_role: str = "textbook", scope=(("u1", "exam"),), reading: str | None = "extXA"):
    """The exam book's source set; its scope names the reading it was made on
    (``reading``; None: a legacy scope that names none)."""

    from learnloop.vault.models import SourceSet, SourceSetMember, SourceSetScope, scope_seal

    named = {"scope_extraction_id": reading, "scope_revision_id": "rev_x"} if scope and reading else {}
    member = SourceSetMember(source_id="src_x", revision_id="rev_x", default_role=default_role,
                             scope=[SourceSetScope(unit_id=unit, role_override=role) for unit, role in scope], **named)
    member.scope_seal = scope_seal(member)  # as the vault writer seals it
    return [SourceSet(id="set_x", subject_id="linear_algebra", title="Exam prep", members=[member])]


def _held_out_inventory(repo, *, extraction_id: str, unit_id: str, span_ids, held_out: bool = True) -> None:
    from learnloop.ids import new_ulid

    repo.insert_unit_inventory(
        id="inv_" + new_ulid(), source_revision_id="rev_x", extraction_id=extraction_id, unit_id=unit_id,
        unit_semantic_hash=f"sha256:{extraction_id}-{unit_id}", inventory_profile="exam",
        inventory_schema_version=1, prompt_version="test", provider="fake", model="fake",
        inventory={"assessment_signals": [{"signal_id": "sig_1", "held_out": held_out,
                                           "span_ids": list(span_ids)}]})


@pytest.fixture
def paper_book(tmp_path):
    """An exam paper registered and not yet read (each test reads it twice)."""

    from tests.helpers import create_basic_vault
    from tests.source_inventory_helpers import _register_revision

    paths = create_basic_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)
    _register_revision(repo, source_id="src_x", revision_id="rev_x")
    repo.set_source_current_revision("src_x", "rev_x")
    return {"repo": repo, "clock": _clock(), "root": paths.root}


_Q1 = "Question 1: prove that the trace of a matrix is a linear map."
_Q2 = "Question 2: prove that the determinant of a product is the product of the determinants."


def _unprotected_copies(repo: Repository, material, *needles: str) -> list[tuple[str, str]]:
    """Every block of every extraction holding any of ``needles`` that ``material`` leaves uncovered."""

    from contextlib import closing

    from learnloop.db.connection import connect

    found: list[tuple[str, str]] = []
    with closing(connect(repo.sqlite_path, read_only=True)) as connection:
        for extraction_id, span_id, text in connection.execute(
                "SELECT extraction_id, span_id, text FROM source_document_blocks ORDER BY extraction_id, ordinal"):
            if any(needle in str(text or "") for needle in needles) and not material.covers(str(extraction_id),
                                                                                             str(span_id)):
                found.append((str(extraction_id), str(span_id)))
    return found


def _second_revision(repo: Repository, *, source_id: str = "src_x", revision_id: str = "rev_x2") -> str:
    with repo.connection() as connection:
        connection.execute("INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?,?,?,?)",
                           (revision_id, source_id, f"sha256:{revision_id}", "2026-10-14T10:00:00Z"))
        connection.commit()
    return revision_id


def _paper_a(repo: Repository, clock) -> None:
    """Reading A of the exam paper: unit u1 "Exam" holds both questions in one
    block (x1); u2 is an appendix."""

    _persist(repo, _ir({"x0": ("SectionHeader", 1, ["Exam"], "Exam"), "x1": ("Text", 1, ["Exam"], f"{_Q1} {_Q2}"),
                        "x2": ("SectionHeader", 2, ["Appendix"], "Appendix"),
                        "x3": ("Text", 2, ["Appendix"], "Appendix: a table of determinants.")},
                       [("u1", "Exam", "sha256:a-exam", ["x0", "x1"]),
                        ("u2", "Appendix", "sha256:a-app", ["x2", "x3"])], extractor="marker"),
             revision_id="rev_x", extraction_id="extPA", clock=clock)
    clock.advance()


def _paper_b_with_duplicates(repo: Repository, clock) -> None:
    """The re-read B: an exact copy of A's question block (y1) and, as
    duplicated extraction output can produce, split copies of the same two
    questions (y3, y4) after a page heading (final verify, F2)."""

    _persist(repo, _ir({"y0": ("SectionHeader", 1, ["Exam"], "Exam"), "y1": ("Text", 1, ["Exam"], f"{_Q1} {_Q2}"),
                        "y2": ("SectionHeader", 1, ["Exam (continued)"], "Exam (continued)"),
                        "y3": ("Text", 1, ["Exam (continued)"], _Q1), "y4": ("Text", 1, ["Exam (continued)"], _Q2),
                        "y5": ("SectionHeader", 2, ["Appendix"], "Appendix"),
                        "y6": ("Text", 2, ["Appendix"], "Appendix: a table of determinants.")},
                       [("u1", "Exam", "sha256:b-exam", ["y0", "y1"]),
                        ("u2", "Exam (continued)", "sha256:b-cont", ["y2", "y3", "y4"]),
                        ("u3", "Appendix", "sha256:b-app", ["y5", "y6"])], extractor="glm_ocr"),
             revision_id="rev_x", extraction_id="extPB", clock=clock)
