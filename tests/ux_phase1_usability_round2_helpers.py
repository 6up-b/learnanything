"""What other test files use from ``tests/test_ux_phase1_usability_round2.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


def _pdf_with_units(repo, source_id: str, labels: list[str], *, pages: int = 11) -> None:
    from tests.source_inventory_helpers import _block, _ir, _persist, _register_revision

    _register_revision(repo, source_id=source_id, revision_id=f"rev_{source_id}")
    per_unit = max(1, pages // max(1, len(labels)))
    units = []
    for index, label in enumerate(labels):
        page = min(pages - 1, index * per_unit)
        units.append((f"u{index + 1}", label, [_block(f"s{index + 1}", f"{label} text about tutoring.", page=page)],
                      f"sha256:{source_id}{index}", page))
    _persist(repo, _ir(units), revision_id=f"rev_{source_id}", extraction_id=f"ext_{source_id}")
