"""What other test files use from ``tests/test_facet_authority_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.content.facet_identity import actions as facet_actions
from learnloop.content.facet_identity import authority
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.vault.writer import upsert_source_set

from tests.facet_authority_helpers import _CLOCK, SUBJECT, _source_set
from tests.source_inventory_helpers import _block, _ir, _persist, _register_revision


def _block_ref(extraction_id: str, span_id: str, *, source_id: str, revision_id: str, relation: str = "primary") -> dict:
    """A persisted block-span provenance ref, as a facet payload records one."""

    return {
        "ref_type": "canonical_source", "ref_id": source_id, "source_id": source_id, "revision_id": revision_id,
        "extraction_id": extraction_id, "locator": f"span:{extraction_id}/{span_id}",
        "locator_scheme": "block_span_v1", "relation": relation,
    }


def _add_split_chapter(repo, root, scope):
    """A textbook chapter the owner split at its level-2 headings: ``Theory`` (s1) and ``Exam`` (s2)."""

    _register_revision(repo, source_id="src_split", revision_id="rev_split")
    ir = _ir([("chapter", "Chapter", [
        _block("s1", "Theory: a symmetric matrix equals its transpose.", section=("chapter", "Theory")),
        _block("s2", "Exam: on the test, symmetric means a positive diagonal.", section=("chapter", "Exam")),
    ], "sha256:chapter", 3)])
    _persist(repo, ir, revision_id="rev_split", extraction_id="ext_split")
    save_unit_selection(repo, "ext_split", ["chapter"],
                        boundary_overrides=[{"op": "split_at_heading", "unit_id": "chapter"}], clock=_CLOCK)
    current = _source_set(root)
    members = [member.model_dump(mode="json", exclude_none=True) for member in current.members]
    members.append({"source_id": "src_split", "revision_id": "rev_split", "default_role": "primary_textbook",
                    "scope": scope, "priority": 1, "scope_extraction_id": "ext_split",
                    "scope_revision_id": "rev_split"})
    upsert_source_set(root, {"id": "set_la", "subject_id": SUBJECT, "title": "Linear Algebra",
                             "members": members}, clock=_CLOCK)
    return authority.CitationResolver.for_source_set(repo, _source_set(root))


def _authority_verdicts(repository) -> list[dict]:
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = ? ORDER BY left_id, created_at, id",
            (facet_actions.MANUAL_AUTHORITY_TASK,),
        ).fetchall()
    return [dict(row) for row in rows]
