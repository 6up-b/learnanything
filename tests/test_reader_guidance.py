from __future__ import annotations

from learnloop.db.repositories import MasteryState, Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.services.reader_guidance import build_guide_plan
from learnloop.services import task_blueprints as TB
from learnloop.services import reader_dialogue as RD
from learnloop.vault.loader import load_vault
from learnloop.vault.models import SourceRef

from tests.helpers import ALGORITHM_VERSION, NOW_ISO, create_basic_vault
from tests.test_source_inventory import _persist, _register_revision


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


def test_unplaced_source_item_never_becomes_a_boundary_question(tmp_path):
    vault, repository = _setup(tmp_path)
    plan = build_guide_plan(vault, repository, extraction_id="ext1")

    assert plan["personalized"] is True
    assert plan["goal_context"]["goal_id"] == "goal_linear_algebra_ml"
    section = plan["sections"][0]
    assert section["end_span_id"] == "s2"
    assert section["question"] is None
    assert section["suggested_passages"][0]["span_id"] == "s1"


def test_reviewed_boundary_placement_connects_question_to_active_goal(tmp_path):
    vault, repository = _setup(tmp_path)
    _place_question(repository)
    plan = build_guide_plan(vault, repository, extraction_id="ext1")

    section = plan["sections"][0]
    assert section["question"]["practice_item_id"] == "pi_svd_define_001"
    assert section["question"]["goal_id"] == "goal_linear_algebra_ml"
    assert section["question"]["reading_phase"] == "after_section"
    assert section["question"]["placement"] == "owner_reviewed"


def test_legacy_placement_uses_only_its_reviewed_familiar_exemplar(tmp_path):
    vault, repository = _setup(tmp_path)
    _place_question(repository, explicit=False)
    plan = build_guide_plan(vault, repository, extraction_id="ext1")

    assert plan["sections"][0]["question"]["practice_item_id"] == "pi_svd_define_001"


def test_dont_bring_this_back_suppresses_the_exact_reviewed_placement(tmp_path):
    vault, repository = _setup(tmp_path)
    _place_question(repository)
    first = build_guide_plan(vault, repository, extraction_id="ext1")
    placement_id = first["sections"][0]["question"]["placement_event_id"]

    RD.question_control(
        repository,
        control="dont_bring_this_back",
        subject_id=placement_id,
        subject_type="reader_question_placement",
    )
    revisited = build_guide_plan(vault, repository, extraction_id="ext1")

    assert revisited["sections"][0]["question"] is None


def test_unresolved_misunderstanding_drives_plain_language_passage_reason(tmp_path):
    vault, repository = _setup(tmp_path)
    repository.upsert_mastery_state(MasteryState(
        learning_object_id="lo_svd_definition", logit_mean=-0.8,
        logit_variance=1.4, evidence_count=2, last_evidence_at=NOW_ISO,
        algorithm_version=ALGORITHM_VERSION, updated_at=NOW_ISO,
    ))
    repository.insert_error_event({
        "id": "err-svd", "learning_object_id": "lo_svd_definition",
        "error_type": "conceptual_slip", "severity": 0.9,
        "is_misconception": True, "status": "active", "created_at": NOW_ISO,
        "misconception_statement": "SVD is the same as eigendecomposition",
    })

    plan = build_guide_plan(vault, repository, extraction_id="ext1")
    passage = plan["sections"][0]["suggested_passages"][0]
    assert passage["learner_signal"] == "recent_misunderstanding"
    assert "SVD is the same as eigendecomposition" in passage["reason"]
    # Posterior parameters influence rank but never leak into the response.
    assert "logit" not in str(plan) and "variance" not in str(plan)


def test_timestamp_provenance_anchors_video_transcript_guidance(tmp_path):
    vault, repository = _setup(
        tmp_path, locator="t=11.5-14.0", extractor_block_id="t=10.0-12.0",
    )
    plan = build_guide_plan(vault, repository, extraction_id="ext1")
    assert plan["sections"][0]["question"] is None
    assert plan["sections"][0]["suggested_passages"][0]["span_id"] == "s1"
