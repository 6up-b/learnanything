"""S0 (G20): rendered proposals write impressions; retrieved-only ones don't; nothing burns."""
from __future__ import annotations

import sqlite3

import pytest

from learnloop.instructional.practice import record_proposal_impressions
from learnloop.practice_index.retrieval import find_practice
from tests.practice_index_fakes import FakePracticeLLM
from tests.source_service_fakes import build_service_vault, call, loaded, table_counts


def _proposal(paths, repository):
    vault = loaded(paths)
    return vault, find_practice(vault, repository, "eigenvalues of a matrix", {"limit": 3},
                                rerank_client=FakePracticeLLM(), caller={"kind": "tutor", "ref": "qe_1"})


def _rows(repository):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM instructional_impressions ORDER BY created_at, id")]


def test_rendered_keys_are_recorded_from_the_receipt_and_unknown_keys_dropped(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    vault, result = _proposal(paths, repository)
    shown = result["items"][0]["practice_item_id"]
    before = table_counts(repository, ["activity_exposure_events"])
    report = record_proposal_impressions(
        vault, repository, proposal_id=result["proposal_id"], surface="tutor_strip", session_id="s1",
        keys=[{"kind": "item", "practice_item_id": shown},
              {"kind": "item", "practice_item_id": shown},  # a duplicate counts once
              {"kind": "item", "practice_item_id": "pi_not_proposed"},
              {"kind": "source_exercise", "extraction_id": "ext_book"}])
    assert report["recorded"] == 1 and report["dropped"] == 3
    rows = _rows(repository)
    assert len(rows) == 1
    row = rows[0]
    assert (row["practice_item_id"], row["surface"], row["caller_kind"], row["caller_ref"]) == (
        shown, "tutor_strip", "tutor", "qe_1")
    assert vault.practice_items[shown].prompt[:40] in row["shown_fields_json"]
    # Never the once-ever burn boundary.
    assert table_counts(repository, ["activity_exposure_events"]) == before


def test_retrieved_only_proposals_write_no_impression(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    _proposal(paths, repository)
    assert _rows(repository) == []


def test_impressions_are_append_only(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    vault, result = _proposal(paths, repository)
    record_proposal_impressions(vault, repository, proposal_id=result["proposal_id"], surface="plan",
                                keys=[{"practice_item_id": result["items"][0]["practice_item_id"]}])
    with pytest.raises(sqlite3.DatabaseError):
        with repository.connection() as connection:
            connection.execute("UPDATE instructional_impressions SET surface='other'")
    with pytest.raises(sqlite3.DatabaseError):
        with repository.connection() as connection:
            connection.execute("DELETE FROM instructional_impressions")


def test_unknown_surface_and_proposal_are_refused(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    vault, result = _proposal(paths, repository)
    with pytest.raises(ValueError):
        record_proposal_impressions(vault, repository, proposal_id=result["proposal_id"], surface="toast", keys=[])
    with pytest.raises(ValueError):
        record_proposal_impressions(vault, repository, proposal_id="pp_missing", surface="plan", keys=[])


def test_the_rpc_records_what_the_strip_rendered(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    _vault, result = _proposal(paths, repository)
    response = call(paths.root, "record_proposal_impressions", {
        "proposalId": result["proposal_id"], "surface": "tutor_strip",
        "keys": [{"kind": "item", "practiceItemId": item["practice_item_id"]} for item in result["items"]]})
    assert response["result"]["recorded"] == len(result["items"])
