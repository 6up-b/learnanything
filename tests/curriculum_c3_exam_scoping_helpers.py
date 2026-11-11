"""What other test files use from ``tests/test_curriculum_c3_exam_scoping.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.source_retrieval import deliverables as DL
from learnloop.vault.loader import load_vault

from tests.exam_scope_fixtures import SENTINEL_WORDS, SENTINELS


ALL_LOS = ("lo_det", "lo_eigen", "lo_inner", "lo_matrices", "lo_spectral", "lo_vectors")


def _deliverable(paths, repository, sentence="Only my midterm: eigenvalues, determinants and matrix computations",
                 **kwargs):
    created = DL.create_deliverable(load_vault(paths.root), repository, sentence, **kwargs)
    return created["goal_id"], load_vault(paths.root)


def _clean(text: str) -> None:
    for sentinel in (*SENTINELS, *SENTINEL_WORDS):
        assert sentinel not in text, sentinel
