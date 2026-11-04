"""RO0 row 5 (spec_router_objective_v1 §4): an event keeps when it happened and when the server had it."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.reader import reader_inquiry as RI
from learnloop.substrate.activities import log_interaction_event
from learnloop.vault.loader import load_vault
from tests.helpers import NOW, NOW_ISO, append_config_toml, create_basic_vault

CLOCK = FrozenClock(NOW)
EVENT = {"kind": "reader_selection", "occurred_at": "2026-01-01T09:30:00.123Z", "payload": {"visit_id": "v1"}}


def _setup(tmp_path, off: bool = False):
    paths = create_basic_vault(tmp_path / "vault")
    if off:
        append_config_toml(paths.root, "[router_objective]\nreceipts = false\n")
    return load_vault(paths.root), Repository(paths.sqlite_path)


def _times(repository):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT occurred_at, received_at, created_at FROM interaction_events ORDER BY id")]


def test_the_writer_passes_them_where_the_caller_knows_them(tmp_path):
    _vault, repository = _setup(tmp_path)
    log_interaction_event(repository, kind="reader_selection", occurred_at="a", received_at="b", clock=CLOCK)
    log_interaction_event(repository, kind="reader_selection", clock=CLOCK)
    assert _times(repository) == [("a", "b", NOW_ISO), (None, None, NOW_ISO)]


def test_a_batched_reader_event_keeps_the_gap(tmp_path):
    vault, repository = _setup(tmp_path)
    RI.record_activity(repository, [EVENT], config=vault.config, clock=CLOCK)
    assert _times(repository) == [("2026-01-01T09:30:00Z", NOW_ISO, NOW_ISO)]


def test_a_stamp_that_is_no_time_is_not_kept_and_the_event_stands(tmp_path):
    vault, repository = _setup(tmp_path)
    RI.record_activity(repository, [{**EVENT, "occurred_at": "yesterday"}], config=vault.config, clock=CLOCK)
    assert _times(repository) == [(None, NOW_ISO, NOW_ISO)]


def test_off_neither_is_written(tmp_path):
    vault, repository = _setup(tmp_path, off=True)
    RI.record_activity(repository, [EVENT], config=vault.config, clock=CLOCK)
    assert _times(repository) == [(None, None, NOW_ISO)]
