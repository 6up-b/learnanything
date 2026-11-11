"""What other test files use from ``tests/test_curriculum_c2b_past_papers.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.vault.loader import add_subject
from learnloop.vault.writer import upsert_concept, upsert_source_set
from learnloop.vault.yaml_io import write_yaml

from tests.exam_scope_fixtures import build_exam_scope_vault, ref
from tests.practice_index_fakes import _learning_object
from tests.source_retrieval_fakes import seed_source


NOW = "2026-05-30T00:00:00Z"
PROB_PAPER = {"prob_q1": ("Question 1", [("Find P(A | B) for the two urns and justify it.", 1)])}


def _two_subject_vault(tmp_path, *, config: str = ""):
    """C3's exam-scope vault (linear algebra, past papers testing PAST_PAPER_LOS) plus a second
    active subject, Probability, whose own past paper tests lo_bayes. No syllabus input."""

    paths, repository = build_exam_scope_vault(tmp_path / "vault", config=config)
    add_subject(paths.root, "probability", "Probability")
    seed_source(repository, source_id="src_prob_paper", revision_id="rev_prob_paper", extraction_id="ext_prob_paper",
                title="Probability midterm 2025", units=PROB_PAPER, furniture=False)
    upsert_source_set(paths.root, {"id": "sset_prob", "subject_id": "probability", "title": "Probability sources",
                                   "members": [{"source_id": "src_prob_paper", "revision_id": "rev_prob_paper",
                                                "default_role": "exam"}]})
    save_unit_selection(repository, "ext_prob_paper", list(PROB_PAPER),
                        exam_use_modes={"prob_q1": "available_for_practice"})
    upsert_concept(paths.root, "bayes_c", {
        "title": "Bayes' rule", "type": "concept", "aliases": [], "description": "Conditional probability.",
        "tags": [], "created_at": NOW, "updated_at": NOW})
    lo = _learning_object("lo_bayes", "Bayes rule")
    lo.update(subjects=["probability"], concept="bayes_c", summary="P(A|B) = P(B|A)P(A)/P(B).")
    lo["provenance"] = {"origin": "human", "source_refs": [ref("src_prob_paper", "ext_prob_paper", "s2")]}
    write_yaml(paths.learning_object_path("probability", "lo_bayes"), lo)
    return paths, repository
