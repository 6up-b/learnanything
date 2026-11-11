"""What other test files use from ``tests/test_source_inventory.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.content.synthesis.ai_contracts import (
    InventoryAssessmentSignal,
    InventoryClaim,
    InventoryConceptMention,
    InventoryPracticeSignal,
    InventoryProcedureSignal,
    SourceUnitInventory,
)
from learnloop.db.repositories import Repository
from learnloop.ingest.hashing import extraction_request_hash, extraction_result_hash
from learnloop.ingest.ir import IR_SCHEMA_VERSION, DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth

from tests.structured_ai import StructuredClientFake


_CLOCK = FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC))


def _repo(tmp_path: Path) -> Repository:
    return Repository(tmp_path / "state.sqlite")


def _block(span_id: str, text: str, *, block_type="Text", role_hint="ordinary_prose", page=1, section=("root",)) -> DocumentBlock:
    return DocumentBlock.build(
        span_id=span_id,
        block_type=block_type,
        text=text,
        ordinal=int(span_id[1:]),
        role_hint=role_hint,
        page=page,
        section_path=list(section),
    )


def _ir(units_blocks, *, extractor="text") -> DocumentIR:
    blocks: list[DocumentBlock] = []
    units: list[DocumentUnit] = []
    for ordinal, (unit_id, label, block_list, semantic_hash, page) in enumerate(units_blocks):
        span_ids = []
        for block in block_list:
            blocks.append(block)
            span_ids.append(block.span_id)
        units.append(
            DocumentUnit(
                unit_id=unit_id,
                label=label,
                ordinal=ordinal,
                semantic_hash=semantic_hash,
                page_start=page,
                page_end=page,
                span_ids=span_ids,
            )
        )
    return DocumentIR(
        extractor=extractor,
        extractor_version="1",
        units=units,
        blocks=blocks,
        assets=[],
        health=ExtractionHealth(),
    )


def _persist(repo: Repository, ir: DocumentIR, *, revision_id: str, extraction_id: str, config=None) -> str:
    request_hash = extraction_request_hash(
        revision_id=revision_id,
        extractor=ir.extractor,
        extractor_version=ir.extractor_version,
        config=config,
        ir_schema_version=IR_SCHEMA_VERSION,
    )
    repo.insert_extraction_run(
        id=extraction_id,
        revision_id=revision_id,
        extractor=ir.extractor,
        extractor_version=ir.extractor_version,
        extraction_request_hash=request_hash,
        ir_schema_version=IR_SCHEMA_VERSION,
        config=config,
        status="running",
        clock=_CLOCK,
    )
    repo.persist_document_ir(extraction_id, ir)
    repo.complete_extraction_run(
        extraction_id, extraction_result_hash=extraction_result_hash(request_hash, ir), clock=_CLOCK
    )
    return extraction_id


def _register_revision(repo: Repository, source_id="src1", revision_id="rev1") -> None:
    now = _CLOCK.now().isoformat()
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, created_at, updated_at) VALUES (?,?,?,?,?)",
            (source_id, "pdf", "file:///book.pdf", now, now),
        )
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?,?,?,?)",
            (revision_id, source_id, "sha256:abc", now),
        )
        connection.commit()


class FakeInventoryClient(StructuredClientFake):
    """AI double exposing run_source_unit_inventory (house fake-client pattern).

    Emits role/profile-appropriate canned signals, always citing span ids drawn
    from the window it is given so the validator passes. Counts calls so cache
    reuse is provable (zero new calls on a cache hit)."""

    model = "fake-model-1"
    provider_type = "codex"

    def __init__(self):
        self.calls: list[object] = []

    def run_source_unit_inventory(self, context):
        self.calls.append(context)
        span_ids = [block["span_id"] for block in context.unit_view["blocks"]] or ["s_missing"]
        profile = context.inventory_profile
        role = context.role
        inv = SourceUnitInventory(
            unit_id=context.unit_id,
            semantic_hash=context.semantic_hash,
            outline_summary=f"summary of {context.unit_id}",
            concept_mentions=[
                InventoryConceptMention(name="eigenvector", span_ids=span_ids[:1]),
            ],
        )
        # Sections are keyed on PROFILE (§7 shared envelope), never on role — the
        # cache is profile-keyed. Role governs authority: an exam unit never mints
        # a canonical claim even under a combined profile (§4.2).
        wants_semantic = profile in {"semantic", "combined"}
        wants_practice = profile in {"practice", "combined"}
        wants_assessment = profile in {"assessment", "combined"}
        if wants_semantic and role != "exam":
            inv.claims = [
                InventoryClaim(
                    kind="definition",
                    statement="An eigenvector is a nonzero vector scaled by A.",
                    preconditions=["A is square"],
                    postconditions=["Av is parallel to v"],
                    span_ids=span_ids,
                )
            ]
            inv.procedure_signals = [
                InventoryProcedureSignal(contract="find eigenvalues", ordered_steps=["form A - lambda I"], observable_step_span_ids=span_ids)
            ]
        if wants_practice:
            inv.practice_signals = [
                InventoryPracticeSignal(kind="exercise", task_family="compute_eigenvalues", valid_method_hints=["characteristic polynomial"], span_ids=span_ids)
            ]
        if wants_assessment:
            inv.assessment_signals = [
                InventoryAssessmentSignal(
                    held_out=True,
                    task_family="compute_eigenvalues",
                    capability_demands=["apply"],
                    representation="symbolic",
                    response_format="short_answer",
                    point_or_time_emphasis="high",
                    span_ids=span_ids,
                )
            ]
        return inv
