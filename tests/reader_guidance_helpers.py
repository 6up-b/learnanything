"""What other test files use from ``tests/test_reader_guidance.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.curriculum import task_blueprints as TB
from learnloop.vault.loader import load_vault
from learnloop.vault.models import SourceRef

from tests.diagnosis_fakes import ReviewFakeClient
from tests.helpers import create_basic_vault
from tests.split_live_helpers import split_vault
from tests.source_inventory_helpers import _persist, _register_revision


def _setup(tmp_path, *, locator: str = "span:ext1/s1", extractor_block_id: str | None = None):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _register_revision(repository, source_id="src1", revision_id="rev1")
    blocks = [
        DocumentBlock.build(
            span_id="s0", block_type="Section", text="Singular value decomposition",
            ordinal=0, page=1, section_path=["SVD"],
        ),
        DocumentBlock.build(
            span_id="s1", block_type="Text",
            text="The singular value decomposition writes A as U Sigma V transpose.",
            ordinal=1, page=1, section_path=["SVD"], extractor_block_id=extractor_block_id,
        ),
        DocumentBlock.build(
            span_id="s2", block_type="Text",
            text="The columns of U and V are orthonormal.",
            ordinal=2, page=1, section_path=["SVD"],
        ),
    ]
    ir = DocumentIR(
        extractor="marker", extractor_version="1",
        units=[DocumentUnit(
            unit_id="u1", label="SVD", ordinal=0, semantic_hash="sha256:svd",
            page_start=1, page_end=1, span_ids=["s0", "s1", "s2"],
        )],
        blocks=blocks, assets=[], health=ExtractionHealth(),
    )
    _persist(repository, ir, revision_id="rev1", extraction_id="ext1")
    vault = load_vault(tmp_path / "vault")
    vault.practice_items["pi_svd_define_001"].provenance.source_refs = [
        SourceRef(
            ref_type="canonical_source", ref_id="src1",
            locator=locator, source_id="src1", extraction_id="ext1",
        )
    ]
    return vault, repository


def _place_question(repository, *, explicit: bool = True):
    version = TB.register_blueprint_version(
        repository,
        blueprint_slug="bp-reader-svd",
        spec={
            "source_rev": "rev1",
            "unit_id": "u1",
            "family_key": "svd-definition",
            "exemplars": [{
                "exemplar_ref": "pi_svd_define_001",
                "unit_id": "u1",
                "family_key": "svd-definition",
            }],
            "solution_recipes": [{
                "all_of": [{"facet": "definition", "capability": "retrieval"}],
            }],
        },
    )
    placement = {"section": "u1", "phase": "after_section", "pattern": "self_explanation"}
    if explicit:
        placement["practice_item_id"] = "pi_svd_define_001"
    TB.place_reading_question(
        repository, blueprint_version_id=version.id, placement=placement,
    )
    TB.review_blueprint_version(repository, blueprint_version_id=version.id)
    return version


_DIAGNOSED = "The learner thinks V needs no transpose in the SVD."


class _StatementFake(ReviewFakeClient):
    """The M1 fake, with the diagnoser naming a misconception statement."""

    def _diagnosis(self, request, context):
        result = super()._diagnosis(request, context)
        events = [
            event.model_copy(update={"misconception_statement": _DIAGNOSED})
            for event in result.event_diagnoses
        ]
        return result.model_copy(update={"event_diagnoses": events})


def _graded_vault_with_extraction(tmp_path, *, version: str, config: str = ""):
    """A graded diagnosis vault at ``version`` whose SVD-compute item cites ext1/s1."""

    paths, vault, repository = split_vault(tmp_path, version=version, config=config, seed=False)
    _register_revision(repository, source_id="src1", revision_id="rev1")
    _persist(repository, _svd_ir(), revision_id="rev1", extraction_id="ext1")
    return paths, vault, repository


def _svd_ir() -> DocumentIR:
    blocks = [
        DocumentBlock.build(
            span_id="s0", block_type="Section", text="Singular value decomposition",
            ordinal=0, page=1, section_path=["SVD"],
        ),
        DocumentBlock.build(
            span_id="s1", block_type="Text",
            text="The singular value decomposition writes A as U Sigma V transpose.",
            ordinal=1, page=1, section_path=["SVD"],
        ),
    ]
    return DocumentIR(
        extractor="marker", extractor_version="1",
        units=[DocumentUnit(
            unit_id="u1", label="SVD", ordinal=0, semantic_hash="sha256:svd",
            page_start=1, page_end=1, span_ids=["s0", "s1"],
        )],
        blocks=blocks, assets=[], health=ExtractionHealth(),
    )


def _cite_extraction(vault) -> None:
    # Set after grading so the grader's context is the vault's own.
    vault.practice_items["pi_svd_compute_001"].provenance.source_refs = [
        SourceRef(
            ref_type="canonical_source", ref_id="src1",
            locator="span:ext1/s1", source_id="src1", extraction_id="ext1",
        )
    ]
