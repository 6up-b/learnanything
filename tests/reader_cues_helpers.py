"""What other test files use from ``tests/test_reader_cues.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.reader import reader_cues as RCU
from learnloop.reader.reader_guidance import build_guide_plan
from learnloop.vault.loader import load_vault
from learnloop.vault.models import SourceRef
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, append_config_toml, create_basic_vault
from tests.source_inventory_helpers import _persist, _register_revision


_CLOCK = FrozenClock(NOW)
STATEMENT = "SVD is the same as eigendecomposition"


def _ir() -> DocumentIR:
    """Two sections: u1 (s0-s3) is read, u2 (s4-s5) holds the exercises."""

    text = {
        "s1": "The singular value decomposition writes A as U Sigma V transpose.",
        "s2": "The columns of U and V are orthonormal.",
        "s3": "Sigma holds the singular values on its diagonal.",
        "s5": "Exercise 2.1: compute the SVD of a 2 by 2 matrix.",
    }
    blocks = [
        DocumentBlock.build(span_id="s0", block_type="Section", text="Singular value decomposition",
                            ordinal=0, page=1, section_path=["SVD"]),
        *[DocumentBlock.build(span_id=span, block_type="Text", text=text[span], ordinal=index + 1, page=1,
                              section_path=["SVD"]) for index, span in enumerate(("s1", "s2", "s3"))],
        DocumentBlock.build(span_id="s4", block_type="Section", text="Exercises", ordinal=4, page=2,
                            section_path=["Exercises"]),
        DocumentBlock.build(span_id="s5", block_type="Text", text=text["s5"], ordinal=5, page=2,
                            section_path=["Exercises"]),
    ]
    units = [
        DocumentUnit(unit_id="u1", label="SVD", ordinal=0, semantic_hash="sha256:svd", page_start=1, page_end=1,
                     span_ids=["s0", "s1", "s2", "s3"]),
        DocumentUnit(unit_id="u2", label="Exercises", ordinal=1, semantic_hash="sha256:ex", page_start=2,
                     page_end=2, span_ids=["s4", "s5"]),
    ]
    return DocumentIR(extractor="marker", extractor_version="1", units=units, blocks=blocks, assets=[],
                      health=ExtractionHealth())


def _refs(spans) -> list[SourceRef]:
    return [SourceRef(ref_type="canonical_source", ref_id="src1", locator=f"span:ext1/{span}",
                      source_id="src1", extraction_id="ext1") for span in spans]


def _active_error(repository: Repository, *, error_id: str = "err-svd", attempt_id: str | None = None) -> None:
    event = {
        "id": error_id, "learning_object_id": "lo_svd_definition", "error_type": "conceptual_slip",
        "severity": 0.9, "is_misconception": True, "status": "active", "created_at": NOW_ISO,
        "misconception_statement": STATEMENT,
    }
    if attempt_id:
        event["attempt_id"] = attempt_id
    repository.insert_error_event(event)


def _cue_vault(tmp_path, *, cite=("s1", "s2", "s3", "s5"), error: bool = True, on_disk: bool = False, config: str = ""):
    """The basic vault with ``ext1`` (two sections) and pi_svd_define_001
    citing ``cite``; an active error on its LO makes every cited passage a
    ``recent_misunderstanding`` passage of the Guide."""

    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    if config:
        append_config_toml(root, config)
    repository = Repository(paths.sqlite_path)
    _register_revision(repository, source_id="src1", revision_id="rev1")
    _persist(repository, _ir(), revision_id="rev1", extraction_id="ext1")
    vault = load_vault(root)
    item = vault.practice_items["pi_svd_define_001"]
    item.provenance.source_refs = _refs(cite)
    if on_disk:
        upsert_practice_item(root, item, clock=_CLOCK)
        vault = load_vault(root)
    if error:
        _active_error(repository)
    return root, vault, repository


def _plan_and_cues(vault, repository):
    plan = build_guide_plan(vault, repository, extraction_id="ext1")
    return plan, RCU.guide_cues(vault, repository, extraction_id="ext1", plan=plan)


def _attempt(repository: Repository, *, attempt_id: str, answer: str | None) -> None:
    repository.insert_practice_attempt({
        "id": attempt_id, "practice_item_id": "pi_svd_define_001", "learning_object_id": "lo_svd_definition",
        "subject": "linear-algebra", "concept": "singular_value_decomposition", "practice_mode": "short_answer",
        "attempt_type": "independent_attempt", "learner_answer_md": answer, "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0}, "rubric_score": 1, "correctness": 0.25, "confidence": 3,
        "latency_seconds": 30, "hints_used": 0, "error_type": "conceptual_slip", "grader_confidence": 1.0,
        "created_at": NOW_ISO, "updated_at": NOW_ISO,
    })


def _answered_cue() -> dict:
    """A cue whose earlier work is an answer to pi_svd_define_001."""

    return {
        "cue_id": "cue_answered", "span_id": "s1", "learning_object_id": "lo_svd_definition",
        "learning_object_title": "SVD definition", "target_id": "err-svd",
        "earlier": {"practice_item_id": "pi_svd_define_001"},
    }
