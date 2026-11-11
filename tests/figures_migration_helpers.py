"""What other test files use from ``tests/test_figures_migration.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


#: What 216 adds (nothing is altered): the earlier migrations' "nothing else
#: changed" diffs on the way to head read this (tests/test_ad1_migration.py,
#: test_approach_maps_schema.py, test_help_assists_schema.py, test_library_asks_migration.py).
RW5A_ADDED_OBJECTS = frozenset({
    "interactive_figures", "figure_predictions", "idx_interactive_figures_extraction", "idx_interactive_figures_input",
    "idx_interactive_figures_supersedes", "idx_interactive_figures_reuse", "idx_figure_predictions_extraction", "figure_predictions_no_delete",
    "figure_predictions_explanation_once", "sqlite_autoindex_interactive_figures_1",
    "sqlite_autoindex_figure_predictions_1", "sqlite_autoindex_figure_predictions_2",
})
