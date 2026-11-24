"""What earlier migrations' upgrade diffs use from the probe router's stop migration
(``tests/test_probe_router_stop_migration.py``), kept here because a test file never imports another
(``tests/test_test_layout.py``)."""

from __future__ import annotations

#: 273 rebuilds probe_episodes (its completion_reason CHECK gains 'router_stop'): an upgrade from before it to the head
#: sees that table's definition changed, and nothing else of 273's.
ROUTER_STOP_ALTERED_TABLES = frozenset({"probe_episodes"})
