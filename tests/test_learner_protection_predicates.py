"""Each way an item becomes withheld from a model context (``learner_protection.withheld_items``), one at a time.

Seeding a bug that stopped withholding an ordinary item once it had been presented as a probe survived 3,844 tests:
the other suites plant probes whose own mode already withholds them. So each reason here is planted on an ordinary
item with nothing else protecting it, with the same item unwithheld before, as the control.
"""

from __future__ import annotations

import pytest

from learnloop import learner_protection as LP
from tests.split_live_helpers import split_vault

ITEM = "pi_svd_compute_001"
AT = "2026-05-19T12:00:00Z"


@pytest.fixture
def world(tmp_path):
    _paths, vault, repository = split_vault(tmp_path / "vault", version="mvp-0.12", seed=False)
    assert vault.practice_items[ITEM].practice_mode not in LP.PROBE_MODES
    before = LP.withheld_items(vault, repository)
    assert before.available and before.reason(ITEM) is None
    return vault, repository


def _execute(repository, *statements):
    with repository.connection() as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        for sql, parameters in statements:
            connection.execute(sql, parameters)
        connection.commit()


def test_an_ordinary_item_presented_as_a_probe_is_withheld(world):
    vault, repository = world
    _execute(repository, (
        "INSERT INTO probe_presentations(id, probe_episode_id, practice_item_id, state_segment_id, status, created_at, "
        "updated_at) VALUES ('presentation', 'episode', ?, 'segment', 'submitted', ?, ?)", (ITEM, AT, AT)))
    withheld = LP.withheld_items(vault, repository)
    assert withheld.reason(ITEM) == LP.WITHHELD_PROBE
    assert LP.attempt_protection(withheld, {"item": ITEM, "type": "independent_attempt", "probe": None}) == LP.WITHHELD_PROBE


def test_an_item_held_as_a_repairs_cold_retry_is_withheld_until_the_repair_ends(world):
    vault, repository = world
    with repository.connection() as connection:
        columns = {row[1]: row for row in connection.execute("PRAGMA table_info(remediation_episodes)")}
    required = {name: "x" for name, row in columns.items() if row[3] and row[4] is None and row[5] == 0}
    values = {**required, "id": "repair", "cold_item_id": ITEM, "state": "cold_scheduled", "case_kind": "diagnosis"}
    names = ", ".join(values)
    marks = ", ".join("?" for _ in values)
    _execute(repository, (f"INSERT INTO remediation_episodes({names}) VALUES ({marks})", tuple(values.values())))
    assert LP.withheld_items(vault, repository).reason(ITEM) == LP.WITHHELD_COLD
    _execute(repository, ("UPDATE remediation_episodes SET state = 'completed' WHERE id = 'repair'", ()))
    assert LP.withheld_items(vault, repository).reason(ITEM) is None


def test_a_predicate_that_fails_withholds_everything(world, monkeypatch):
    """Fail closed: not "the items the other predicates still found"."""

    vault, repository = world
    monkeypatch.setattr(repository, "reserved_assessment_surfaces", lambda: 1 / 0)
    withheld = LP.withheld_items(vault, repository)
    assert withheld.available is False
    assert LP.attempt_protection(withheld, {"item": ITEM, "type": "independent_attempt", "probe": None}) == LP.WITHHELD_UNREADABLE
