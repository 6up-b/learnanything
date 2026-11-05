"""RO0 row 4 (spec_router_objective_v1 §4): who initiated an exposure. A new field, not a new row."""

from __future__ import annotations

import json

import pytest

from learnloop.config.schema import LearnLoopConfig, RouterObjectiveConfig
from learnloop.db.repositories import Repository
from learnloop.reader import reader_inquiry as RI
from learnloop.router_objective import exposure as EX
from learnloop.vault.loader import load_vault
from tests.helpers import append_config_toml, create_basic_vault

OFF = LearnLoopConfig.model_validate({}).model_copy(update={"router_objective": RouterObjectiveConfig(receipts=False)})
BASE = {"context": "reader", "extraction_id": "e1", "span_id": "s1"}


def _setup(tmp_path, off: bool = False):
    paths = create_basic_vault(tmp_path / "vault")
    if off:
        append_config_toml(paths.root, "[router_objective]\nreceipts = false\n")
    return load_vault(paths.root), Repository(paths.sqlite_path)


@pytest.mark.parametrize(("context", "stated", "expected"), [
    ("reader", None, "learner"),
    ("provenance", None, "learner"),
    ("tutor_citation", None, "tutor_citation"),
    ("remediation_delivery", None, "plan"),
    ("reader", "plan", "plan"),
    ("reader", "dose_offer", "dose_offer"),
    ("reader", "lesson", "lesson"),
    ("reader", "made_up", "learner"),
])
def test_the_initiator_is_the_clients_word_else_the_contexts_else_the_learner(context, stated, expected):
    assert EX.initiator_for(context, stated) == expected


def test_one_exposure_is_one_row_with_its_fields(tmp_path):
    vault, repository = _setup(tmp_path)
    session = repository.create_session()
    event_id = repository.insert_source_exposure_event({
        **BASE, **EX.fields(vault.config, repository, context="reader", initiator="plan", block_id="b1", visit_id="v1")})
    rows = repository.source_exposure_events(extraction_id="e1")
    assert [row["id"] for row in rows] == [event_id], "coldness readers count rows"
    row = rows[0]
    assert (row["initiator"], row["initiator_block_id"], row["initiator_session_id"], row["initiator_visit_id"]) == (
        "plan", "b1", session, "v1")
    assert row["context"] == "reader", "context keeps its meaning"


def test_off_the_writer_writes_what_it_always_did(tmp_path):
    vault, repository = _setup(tmp_path, off=True)
    assert EX.fields(vault.config, repository, context="reader", initiator="plan") == {}
    repository.insert_source_exposure_event({**BASE})
    row = repository.source_exposure_events(extraction_id="e1")[0]
    assert all(row[column] is None for column in EX.COLUMNS)


def test_the_span_view_handler_records_the_mapped_initiator(tmp_path):
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.handlers.provenance import SpanViewInput, get_span_view_handler
    from tests.helpers import seed_explanatory_source

    vault, repository = _setup(tmp_path)
    seeded = seed_explanatory_source(vault.root, repository)
    ctx = SidecarContext()
    ctx.load(vault.root, maintenance=False)
    extraction_id, span_id = "ext_cited", seeded["span_id"]
    get_span_view_handler(ctx, SpanViewInput(extraction_id=extraction_id, span_id=span_id, context="tutor_citation"))
    get_span_view_handler(ctx, SpanViewInput(extraction_id=extraction_id, span_id=span_id, context="reader", initiator="plan",
                                             block_id="b9", visit_id="v9"))
    rows = sorted(repository.source_exposure_events(extraction_id=extraction_id), key=lambda row: row["id"])
    assert [(row["context"], row["initiator"], row["initiator_block_id"], row["initiator_visit_id"]) for row in rows] == [
        ("tutor_citation", "tutor_citation", None, None), ("reader", "plan", "b9", "v9")]


def test_a_reader_visit_names_who_sent_it_with_the_servers_session_and_the_plans_block(tmp_path):
    vault, repository = _setup(tmp_path)
    session = repository.create_session()
    RI.record_activity(repository, [
        {"kind": "reader_view_opened", "payload": {"visit_id": "v1", "extraction_id": "e1", "initiator": "plan"}},
        {"kind": "reader_view_opened", "payload": {"visit_id": "v2", "extraction_id": "e1"}},
    ], config=vault.config)
    with repository.connection() as connection:
        rows = [(json.loads(row[0]), row[1]) for row in connection.execute(
            "SELECT payload_json, origin FROM interaction_events WHERE kind = 'reader_view_opened' ORDER BY id")]
    assert {payload["visit_id"]: payload["initiator"] for payload, _origin in rows} == {"v1": "plan", "v2": "learner"}
    assert all(payload["session_id"] == session for payload, _origin in rows)
    assert all(origin == "learner" for _payload, origin in rows), "origin keeps its meaning"


def test_off_a_reader_visit_keeps_none_of_it(tmp_path):
    vault, repository = _setup(tmp_path, off=True)
    repository.create_session()
    RI.record_activity(repository, [{"kind": "reader_view_opened", "payload": {
        "visit_id": "v1", "extraction_id": "e1", "initiator": "plan", "block_id": "b", "session_id": "s", "ask_available": True}}],
        config=vault.config)
    with repository.connection() as connection:
        payload = json.loads(connection.execute(
            "SELECT payload_json FROM interaction_events WHERE kind = 'reader_view_opened'").fetchone()[0])
    assert not {"initiator", "block_id", "session_id", "ask_available"} & set(payload)
