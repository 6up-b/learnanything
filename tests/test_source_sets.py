"""ING M4 — source-set vault entity, one-source-two-sets, exam use modes,
coverage preview, and doctor checks (spec_source_ingestion_v2 §4.3, §9.3, §14)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ops.doctor import run_doctor
from learnloop.content.sources.role_authority import role_authority
from learnloop.content.synthesis.source_coverage import build_source_coverage
from learnloop.content.synthesis.source_unit_inventory import run_unit_inventory
from learnloop.content.synthesis.source_unit_selection import default_exam_use_modes, save_unit_selection
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.writer import upsert_source_set

from tests.test_source_inventory import (
    FakeInventoryClient,
    _block,
    _ir,
    _persist,
    _register_revision,
)

_CLOCK = FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC))


def _vault(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    init_vault(root, clock=_CLOCK)
    add_subject(root, "linear-algebra", "Linear Algebra", clock=_CLOCK)
    return root


def _repo(root: Path) -> Repository:
    return Repository(root / "state.sqlite")


def test_one_source_two_sets_different_roles(tmp_path):
    root = _vault(tmp_path)
    repo = _repo(root)
    _register_revision(repo, source_id="src_axler", revision_id="rev_axler")
    ir = _ir(
        [
            ("chapter_02", "Vector Spaces", [_block("s1", "A vector space is a set with two operations.")], "sha256:c2", 2),
            ("chapter_04_exercises", "Exercises", [_block("s2", "Problem 1. Prove the rank-nullity theorem.")], "sha256:c4", 4),
        ]
    )
    _persist(repo, ir, revision_id="rev_axler", extraction_id="ext_axler")

    # The SAME source pinned in two sets with different roles/scopes (§4.3).
    upsert_source_set(
        root,
        {
            "id": "set_foundations",
            "subject_id": "linear-algebra",
            "title": "Foundations",
            "members": [
                {
                    "source_id": "src_axler",
                    "revision_id": "rev_axler",
                    "default_role": "primary_textbook",
                    "scope": [{"unit_id": "chapter_02"}],
                    "priority": 1,
                }
            ],
        },
        clock=_CLOCK,
    )
    upsert_source_set(
        root,
        {
            "id": "set_drills",
            "subject_id": "linear-algebra",
            "title": "Drills",
            "members": [
                {
                    "source_id": "src_axler",
                    "revision_id": "rev_axler",
                    "default_role": "reference",
                    "scope": [{"unit_id": "chapter_04_exercises", "role_override": "problem_set"}],
                    "priority": 1,
                }
            ],
        },
        clock=_CLOCK,
    )

    vault = load_vault(root)
    sets = {source_set.id: source_set for source_set in vault.source_sets}
    assert set(sets) == {"set_foundations", "set_drills"}
    assert sets["set_foundations"].members[0].default_role == "primary_textbook"
    # The unit-level role override is honored — the exercise section acts as a problem set.
    assert sets["set_drills"].members[0].scope[0].role_override == "problem_set"

    # The two roles yield different authority and different inventory content.
    client = FakeInventoryClient()
    textbook = run_unit_inventory(repo, "ext_axler", "chapter_02", role="primary_textbook", profile="semantic", client=client, clock=_CLOCK)
    drills = run_unit_inventory(repo, "ext_axler", "chapter_04_exercises", role="problem_set", profile="practice", client=client, clock=_CLOCK)
    assert textbook.inventory.claims and not textbook.inventory.practice_signals
    assert drills.inventory.practice_signals and not drills.inventory.claims
    assert role_authority("primary_textbook").semantic_contract
    assert not role_authority("problem_set").semantic_contract


def test_exam_use_modes_persist_at_selection(tmp_path):
    root = _vault(tmp_path)
    repo = _repo(root)
    _register_revision(repo, source_id="src_exam", revision_id="rev_exam")
    ir = _ir(
        [
            ("q1", "Question 1", [_block("s1", "Compute the eigenvalues of the given matrix.")], "sha256:q1", 1),
            ("q2", "Question 2", [_block("s2", "State and prove the spectral theorem.")], "sha256:q2", 2),
        ]
    )
    _persist(repo, ir, revision_id="rev_exam", extraction_id="ext_exam")

    modes = default_exam_use_modes(["q1", "q2"], held_out_fraction=0.5)
    assert modes["q1"] == "held_out_evaluation" and modes["q2"] == "blueprint_only"

    saved = save_unit_selection(
        repo,
        "ext_exam",
        ["q1", "q2"],
        exam_use_modes=modes,
        exam_paper_metadata={"year": "2024", "syllabus": "AQA", "weighting": {"q1": 10, "q2": 15}},
        clock=_CLOCK,
    )
    assert saved["exam_use_modes"] == modes
    assert saved["exam_paper_metadata"]["syllabus"] == "AQA"


def test_source_coverage_readiness_report(tmp_path):
    root = _vault(tmp_path)
    repo = _repo(root)
    _register_revision(repo, source_id="src_txt", revision_id="rev_txt")
    ir = _ir([("ch1", "Vectors", [_block("s1", "A vector space is a set with two operations about eigenvector.")], "sha256:c1", 1)])
    _persist(repo, ir, revision_id="rev_txt", extraction_id="ext_txt")
    client = FakeInventoryClient()
    run_unit_inventory(repo, "ext_txt", "ch1", role="primary_textbook", profile="combined", client=client, clock=_CLOCK)

    upsert_source_set(
        root,
        {
            "id": "set_cov",
            "subject_id": "linear-algebra",
            "title": "Coverage",
            "members": [
                {"source_id": "src_txt", "revision_id": "rev_txt", "default_role": "primary_textbook", "scope": [{"unit_id": "ch1"}], "priority": 1}
            ],
        },
        clock=_CLOCK,
    )
    vault = load_vault(root)
    source_set = next(s for s in vault.source_sets if s.id == "set_cov")
    report = build_source_coverage(repo, vault, source_set)

    assert report["source_set_id"] == "set_cov"
    assert report["concept_matrix"]  # eigenvector concept present
    # Curriculum-linkage axis is honestly unlinked pending entity_source_links.
    assert report["curriculum_linkage_seam"] == "entity_source_links_m5_m6"
    codes = {flag["code"] for flag in report["readiness"]["flags"]}
    # A textbook-only collection has teaching but no representative assessment.
    assert "teaching_without_assessment" in codes


def test_doctor_flags_source_set_issues(tmp_path):
    root = _vault(tmp_path)
    repo = _repo(root)
    _register_revision(repo, source_id="src_ok", revision_id="rev_ok")

    upsert_source_set(
        root,
        {
            "id": "set_bad",
            "subject_id": "nonexistent-subject",
            "title": "Bad",
            "members": [
                {"source_id": "src_ok", "revision_id": "rev_ok", "default_role": "made_up_role", "scope": [], "priority": 1},
                {"source_id": "src_missing", "revision_id": "rev_missing", "default_role": "exam", "scope": [], "priority": 1},
            ],
        },
        clock=_CLOCK,
    )
    report = run_doctor(root)
    codes = {issue.code for issue in report.issues}
    assert "source_set:missing_subject" in codes  # error
    assert "source_set:unknown_role" in codes  # warning (open string, fails closed)
    assert "source_set:missing_source" in codes  # error
