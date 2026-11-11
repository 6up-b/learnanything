"""What other test files use from ``tests/test_learner_notes_vault_origin_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: The objects 233 redefines (rebuilt in place, same name; it adds nothing).
C2B_ALTERED_TABLES = frozenset({"learner_notes"})
