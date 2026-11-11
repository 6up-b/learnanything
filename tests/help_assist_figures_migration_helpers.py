"""What other test files use from ``tests/test_help_assist_figures_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: What 232 alters and adds: the earlier migrations' "nothing else changed"
#: diffs on the way to head read these.
#: Codex review F7/F9: figure_predictions is rebuilt too (nullable
#: extraction_id, assist_id, explained_at; the explanation trigger fixes assist_id).
P3_ALTERED_TABLES = frozenset({"help_assists", "help_assists_identity_fixed", "figure_predictions",
                               "figure_predictions_explanation_once"})
P3_ADDED_OBJECTS = frozenset({"idx_help_assists_figure", "idx_figure_predictions_assist"})
