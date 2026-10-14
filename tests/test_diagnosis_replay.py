"""Slice 1 M2 §6.3/§13 C1, C3: replay reads both shapes and never calls a model."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.ai import transport as transport_module
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, tables_for_role
from learnloop.diagnosis.split.live import diagnosis_for_attempt
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import FakeEmbeddingClient, ReviewFakeClient
from tests.split_live_helpers import at, drain_jobs, enable_embeddings, split_vault, submit

pytestmark = pytest.mark.durability

CLOCK = FrozenClock(datetime(2026, 9, 1, 12, 0, tzinfo=UTC))
HEAD_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_202"
#: Raw ledgers that replay REWRITES (error events, debug payloads) or appends
#: to (hypotheses), plus the factors the projection reconciles.
REWRITTEN = ("error_events", "causal_hypotheses", "attempt_debug_payloads", "unresolved_cause_factors")


def _snapshot(repository: Repository, tables) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    with connect(repository.sqlite_path, read_only=True) as connection:
        for table in sorted(tables):
            rows = [dict(row) for row in connection.execute(f'SELECT * FROM "{table}"')]
            out[table] = sorted(rows, key=lambda value: json.dumps(value, sort_keys=True, default=str))
    return out


def _diagnosed_split_vault(tmp_path):
    paths, vault, repository = split_vault(tmp_path)
    client = ReviewFakeClient()
    first = submit(vault, repository, client, when=at(20))
    second = submit(vault, repository, client, item_id="pi_svd_compute_002", answer="B = U Sigma V nope", when=at(21))
    drain_jobs(vault, repository, client, clock=FrozenClock(at(22)))
    return paths, vault, repository, client, (first.attempt_id, second.attempt_id)


def test_split_vault_rebuild_is_a_fixed_point_and_keeps_diagnosis_sourced_causes(tmp_path):
    _paths, vault, repository, _client, attempts = _diagnosed_split_vault(tmp_path)
    tables = {*tables_for_role(TableRole.DERIVED), *REWRITTEN}

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    first = _snapshot(repository, tables)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    second = _snapshot(repository, tables)

    assert second == first
    for attempt_id in attempts:
        diagnosis = repository.latest_attempt_diagnosis(attempt_id)
        raw = repository.raw_error_events_for_attempt(attempt_id)
        assert raw and not any((event["repair_plan"] or {}).get("candidate_causes") for event in raw)
        overlaid = repository.error_events_for_attempt(attempt_id)
        assert all((event["repair_plan"] or {}).get("candidate_causes") for event in overlaid)
        heads = repository.causal_hypotheses_for_attempt(attempt_id)
        assert heads and {row["generation_agent_run_id"] for row in heads} == {diagnosis["agent_run_id"]}


def test_replay_makes_zero_model_and_embedding_calls(tmp_path, monkeypatch):
    paths, vault, repository, client, _attempts = _diagnosed_split_vault(tmp_path)
    enable_embeddings(paths.root)
    vault = load_vault(paths.root)
    embedder = FakeEmbeddingClient()
    calls_before = list(client.calls)

    def refuse(*_args, **_kwargs):
        raise AssertionError("replay must not call a model (S7)")

    monkeypatch.setattr(transport_module, "execute_structured_operation", refuse)
    monkeypatch.setattr("learnloop.attempts.blind_grading.execute_structured_operation", refuse)
    monkeypatch.setattr("learnloop.diagnosis.split.contract.execute_structured_operation", refuse)
    monkeypatch.setattr("learnloop.diagnosis.misconceptions.execute_structured_operation", refuse)
    # No provider client of any kind (chat or embedding) is even resolved.
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task", refuse)
    monkeypatch.setattr("learnloop.diagnosis.split.jobs.default_embedding_client", refuse)
    monkeypatch.setattr("learnloop.diagnosis.split.jobs.default_diagnosis_client", refuse)
    monkeypatch.setattr(FakeEmbeddingClient, "embed", refuse)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)

    assert client.calls == calls_before
    assert embedder.calls == 0


def test_joint_reads_are_untouched_by_the_overlay(tmp_path):
    root = tmp_path / "head"
    copy_tree_with_databases(HEAD_FIXTURE, root)
    repository = Repository(root / "state.sqlite")
    with connect(repository.sqlite_path, read_only=True) as connection:
        attempt_ids = [row[0] for row in connection.execute("SELECT id FROM practice_attempts")]
    assert attempt_ids
    for attempt_id in attempt_ids:
        assert repository.error_events_for_attempt(attempt_id) == repository.raw_error_events_for_attempt(attempt_id)
        assert repository.fetch_attempt_feedback_metadata(attempt_id) == repository.raw_attempt_feedback_metadata(attempt_id)
        view = diagnosis_for_attempt(repository, attempt_id)
        if repository.raw_error_events_for_attempt(attempt_id):
            assert view is not None and view["mode"] == "legacy_view"
    grouped = repository.all_error_events_by_attempt()
    for attempt_id, events in grouped.items():
        assert events == repository.raw_error_events_for_attempt(attempt_id)


def test_joint_fixture_rebuild_is_identical_at_the_previous_version(tmp_path):
    """C1 for joint vaults: no blind record and no diagnosis exist, so a
    same-version (mvp-0.9) rebuild reproduces itself byte for byte."""

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD_FIXTURE, root)
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    tables = {*tables_for_role(TableRole.DERIVED), *REWRITTEN}
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    first = _snapshot(repository, tables)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _snapshot(repository, tables) == first
    assert repository.blind_graded_attempt_ids() == set()
