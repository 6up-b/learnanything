"""What other test files use from ``tests/test_revision_refresh.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.vault.loader import load_vault

from tests.source_inventory_helpers import _block, _ir, _persist


_CLOCK = FrozenClock(datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC))


def _member_revision(root, source_id):
    vault = load_vault(root)
    ss = next(s for s in vault.source_sets if s.id == "set_la")
    return next(m.revision_id for m in ss.members if m.source_id == source_id)


def _register_new_revision(repo, *, changed: bool):
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?,?,?,?)",
            ("rev_text_v2", "src_text", "sha256:v2", _CLOCK.now().isoformat()),
        )
        connection.commit()
    first = "A real square matrix is symmetric precisely when A equals its transpose." if changed \
        else "A real square matrix is symmetric when A^T = A."
    ir = _ir([
        ("chapter_symmetry", "Symmetric matrices",
         [_block("s1", first),
          _block("s2", "The spectral theorem applies to real symmetric matrices.")],
         "sha256:sym2", 5),
    ])
    _persist(repo, ir, revision_id="rev_text_v2", extraction_id="ext_text_v2")
