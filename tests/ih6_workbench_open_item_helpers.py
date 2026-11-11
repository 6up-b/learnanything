"""What other test files use from ``tests/test_ih6_workbench_open_item.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from learnloop.reader import workbench as WB
from learnloop.vault.loader import load_vault

from tests.daily_plan_fakes import iso


def _phone_workbench(world) -> dict[str, Any]:
    item = sorted(load_vault(world.paths.root).practice_items)[0]
    with world.repository.connection() as connection:
        connection.execute("UPDATE sessions SET started_at = ? WHERE id = ?",
                           (iso(world.now["at"] - timedelta(minutes=1)), world.session))
        connection.commit()
    row, _resumed = WB.open_session(world.repository, origin="plan", entry="plan", stem_md="A question.",
                                    practice_item_id=item)
    return row
