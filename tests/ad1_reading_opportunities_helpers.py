"""What other test files use from ``tests/test_ad1_reading_opportunities.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.reader import reader_quick_check as RQC
from learnloop.vault.loader import load_vault

from tests.ad_fakes import rows
from tests.helpers import append_config_toml, create_basic_vault
from tests.source_inventory_helpers import _persist, _register_revision


T0 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
LO_A, LO_B = "lo_svd_definition", "lo_other"
ITEM = "pi_svd_define_001"


def at(minutes: float) -> FrozenClock:
    return FrozenClock(T0 + timedelta(minutes=minutes))


def iso(minutes: float) -> str:
    return (T0 + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


class FakeMap:
    """The Reader's mapping, fixed: sec1 holds s1, s2 and the worked example we1."""

    def __init__(self) -> None:
        self.sections = {("ext1", "u1"): [LO_A]}
        self.spans = {("ext1", "s1"): [LO_A], ("ext1", "s2"): [LO_A, LO_B], ("ext1", "we1"): [LO_A]}
        self.section_span_ids = {("ext1", "u1"): ["s1", "s2", "we1"]}
        self.examples = {"ext1": {"we1"}}
        self.facets = {LO_A: ["fa1", "fa2"], LO_B: ["fb1"]}
        self.items = {ITEM: LO_A}
        self.held: set[tuple[str, str | None]] = set()

    def los_for_section(self, extraction_id, section_id):
        return list(self.sections.get((extraction_id, section_id), []))

    def los_for_span(self, extraction_id, span_id):
        return list(self.spans.get((extraction_id, span_id), []))

    def section_spans(self, extraction_id, section_id):
        return list(self.section_span_ids.get((extraction_id, section_id), []))

    def worked_example_spans(self, extraction_id):
        return set(self.examples.get(extraction_id, set()))

    def withheld(self, extraction_id, span_id):
        return (extraction_id, span_id) in self.held

    def los_for_note(self, note_id):
        return []

    def lo_for_item(self, practice_item_id):
        return self.items.get(practice_item_id)

    def facets_for_lo(self, learning_object_id):
        return list(self.facets.get(learning_object_id, []))


def _ir() -> DocumentIR:
    blocks = [
        DocumentBlock.build(span_id=span, block_type="Text", text=f"Block {span}.", ordinal=index, page=1,
                            section_path=["Ch1"])
        for index, span in enumerate(("s1", "s2", "we1"))
    ]
    unit = DocumentUnit(unit_id="u1", label="Ch1", ordinal=0, semantic_hash="sha256:u1", page_start=1,
                        page_end=1, span_ids=["s1", "s2", "we1"])
    return DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks, assets=[],
                      health=ExtractionHealth())


def _setup(tmp_path, *, config: str = ""):
    paths = create_basic_vault(tmp_path / "vault")
    if config:
        append_config_toml(paths.root, config)
    vault = load_vault(paths.root)
    repo = Repository(paths.sqlite_path)
    _register_revision(repo, source_id="src1", revision_id="rev1")
    _persist(repo, _ir(), revision_id="rev1", extraction_id="ext1")
    return paths, vault, repo


def _question(repo, style, minutes, *, answer=True, dismiss=False):
    question_id = repo.insert_reader_authored_question(fields={
        "extraction_id": "ext1", "section_id": "u1", "source_id": "src1", "question_md": f"A {style} question?",
        "expected_answer_md": "The answer.", "span_ids": ["s1"], "prompt_version": "qc-v1",
        "scope_kind": "inquiry", "question_style": style, "anchor_span_ids": ["s1"],
        "inquiry_root_event_id": f"root-{style}-{minutes}",
    }, clock=at(minutes))
    if answer:
        RQC.record_inquiry_action(repo, question_id=question_id, action="answered", response_md="my words",
                                  clock=at(minutes))
    if dismiss:
        RQC.record_inquiry_action(repo, question_id=question_id, action="dismissed", clock=at(minutes))
    return question_id


def _sweep(vault, repo, minutes, *, mapping=None, kind="serve"):
    from learnloop.adaptive_difficulty.reading import sweep

    return sweep(vault, repo, as_of=iso(minutes), sweep_kind=kind, reading_map=mapping or FakeMap(),
                 clock=at(minutes))


def _opportunities(paths):
    return rows(paths.sqlite_path, "SELECT * FROM ad_reading_opportunities ORDER BY source_written_at, id")
