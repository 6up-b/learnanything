"""The durability lane must reach fixtures of every scope, not only the test body."""

from __future__ import annotations

import pytest

from learnloop.db.connection import connect
from tests import helpers

_SYNCHRONOUS_OFF = 0
_SYNCHRONOUS_FULL = 2


def _observe_sqlite_mode(root) -> dict[str, object]:
    paths = helpers.create_basic_vault(root)
    connection = connect(paths.sqlite_path)
    try:
        synchronous = connection.execute("PRAGMA synchronous").fetchone()[0]
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
    finally:
        connection.close()
    return {
        "synchronous": synchronous,
        "journal_mode": journal_mode,
        "fresh_vaults": helpers._FRESH_VAULTS,
    }


@pytest.fixture(scope="module")
def durable_module_observation(tmp_path_factory):
    return _observe_sqlite_mode(tmp_path_factory.mktemp("durable-module") / "vault")


@pytest.fixture(scope="module")
def fast_module_observation(tmp_path_factory):
    return _observe_sqlite_mode(tmp_path_factory.mktemp("fast-module") / "vault")


@pytest.mark.durability
def test_module_fixture_of_a_durability_test_uses_production_sqlite(durable_module_observation):
    assert durable_module_observation == {
        "synchronous": _SYNCHRONOUS_FULL,
        "journal_mode": helpers.production_journal_mode(),
        "fresh_vaults": True,
    }


def test_module_fixture_of_a_plain_test_uses_the_session_lane(request, fast_module_observation):
    if request.config.getoption("--durable-sqlite"):
        expected = {"synchronous": _SYNCHRONOUS_FULL, "journal_mode": helpers.production_journal_mode(), "fresh_vaults": True}
    else:
        expected = {"synchronous": _SYNCHRONOUS_OFF, "journal_mode": "memory", "fresh_vaults": False}
    assert fast_module_observation == expected
