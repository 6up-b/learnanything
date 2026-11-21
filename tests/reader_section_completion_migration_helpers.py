"""What earlier migrations' upgrade diffs use from the section-completion migration 259
(``tests/test_section_end.py``), kept here because a test file never imports another (``tests/test_test_layout.py``;
refactor step T1)."""

from __future__ import annotations


#: What 259 alters (``reader_section_progress`` gains two nullable columns, ``completion_cause`` and
#: ``completion_algorithm_version``): earlier migrations' "nothing else changed" diffs on the way to head read this.
SECTION_END_ALTERED_TABLES = frozenset({"reader_section_progress"})
