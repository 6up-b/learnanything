"""What other test files use from ``tests/test_tutor_delivery_fixes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.repositories import Repository

from tests.helpers import append_config_toml, create_basic_vault
from tests.source_retrieval_fakes import seed_source


#: One chapter: a header (s1) then nine paragraphs s2..s10. The Ask is about s6.
CHAPTER = [
    ("Paragraph two sets up the notation for the chapter.", 1),
    ("Paragraph three defines the transpose of a matrix.", 1),
    ("Paragraph four says a matrix is symmetric when it equals its transpose.", 1),
    ("Paragraph five, right before the step: assume A^T = A and Av = tv.", 1),
    ("Paragraph six, the step: hence t is real, by Theorem 3.2 and Lemma 9.9.", 2),
    ("Paragraph seven, right after the step: so the eigenvalues are real numbers.", 2),
    ("Paragraph eight extends the result to Hermitian matrices.", 2),
    ("Paragraph nine gives an example with a 2 by 2 matrix.", 2),
    ("Paragraph ten summarises the section.", 2),
]
THEOREM = ("Theorem 3.2 (Spectral theorem). Every real symmetric matrix A has real eigenvalues "
           "and an orthonormal basis of eigenvectors.")


def _vault(tmp_path, *, chapter=CHAPTER, extra_units=None, config: str | None = None):
    paths = create_basic_vault(tmp_path / "vault")
    if config:
        append_config_toml(paths.root, config)
    repository = Repository(paths.sqlite_path)
    units = dict(extra_units or {})
    units["ch_sym"] = ("Chapter 4 Symmetric matrices", list(chapter))
    seed_source(repository, source_id="src_text", revision_id="rev_text", extraction_id="ext_text",
                title="Linear Algebra Text", units=units)
    return paths, repository


def _span_of(repository, text_start: str, extraction_id: str = "ext_text") -> str:
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id = ? AND text LIKE ?",
            (extraction_id, text_start + "%"),
        ).fetchone()
    assert row is not None, text_start
    return str(row["span_id"])
