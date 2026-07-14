from __future__ import annotations

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository

from tests.helpers import create_basic_vault


def _seed_agent_run(sqlite_path, run_id: str = "run_1") -> None:
    with connect(sqlite_path) as connection:
        connection.execute(
            """
            INSERT INTO agent_runs(id, purpose, provider, provider_type, model,
              provider_revision, started_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, "authoring", "codex", "codex", "gpt", None, "2026-01-01T00:00:00Z", "completed"),
        )
        connection.commit()


def _batch(run_id: str = "run_1") -> dict:
    return {
        "id": "pp1",
        "agent_run_id": run_id,
        "purpose": "authoring",
        "source_refs": [],
        "created_at": "2026-01-01T00:00:00Z",
    }


def _item(client_id: str, item_type: str, **overrides) -> dict:
    data = {
        "client_item_id": client_id,
        "item_type": item_type,
        "operation": "create",
        "payload": {"id": client_id},
        "created_at": "2026-01-01T00:00:00Z",
    }
    data.update(overrides)
    return data


def test_new_item_types_persist(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _seed_agent_run(paths.sqlite_path)
    repository = Repository(paths.sqlite_path)
    items = [
        _item("f1", "facet"),
        _item("tb1", "task_blueprint"),
        _item("pl1", "provenance_link"),
        _item("nm1", "notation_mapping"),
        _item("sc1", "source_conflict"),
    ]
    repository.persist_proposal_batch(_batch(), items)
    stored = repository.proposal_items("pp1")
    assert {item["item_type"] for item in stored} == {
        "facet",
        "task_blueprint",
        "provenance_link",
        "notation_mapping",
        "source_conflict",
    }


def test_depends_on_normalized_into_dependency_table(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _seed_agent_run(paths.sqlite_path)
    repository = Repository(paths.sqlite_path)
    # facet -> blueprint -> criterion dependency chain (§10.2 / §12).
    items = [
        _item("facet_client", "facet", id="f_a"),
        _item("bp_client", "task_blueprint", depends_on_client_item_ids=["facet_client"]),
        _item("crit_client", "rubric", depends_on_client_item_ids=["bp_client"]),
    ]
    repository.persist_proposal_batch(_batch(), items)
    stored = {item["client_item_id"]: item for item in repository.proposal_items("pp1")}

    bp_deps = repository.proposal_item_dependencies(stored["bp_client"]["id"])
    assert bp_deps == [stored["facet_client"]["id"]]
    crit_deps = repository.proposal_item_dependencies(stored["crit_client"]["id"])
    assert crit_deps == [stored["bp_client"]["id"]]
    # Every item defaults to a pending dependency status.
    assert all(item["dependency_status"] == "pending" for item in stored.values())


def test_unknown_dependency_is_dropped_not_dangling(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _seed_agent_run(paths.sqlite_path)
    repository = Repository(paths.sqlite_path)
    items = [_item("only", "facet", depends_on_client_item_ids=["ghost"])]
    repository.persist_proposal_batch(_batch(), items)
    stored = repository.proposal_items("pp1")[0]
    assert repository.proposal_item_dependencies(stored["id"]) == []


def test_dependency_status_can_be_blocked(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _seed_agent_run(paths.sqlite_path)
    repository = Repository(paths.sqlite_path)
    repository.persist_proposal_batch(_batch(), [_item("f1", "facet")])
    item_id = repository.proposal_items("pp1")[0]["id"]
    repository.set_proposal_item_dependency_status(
        item_id, dependency_status="blocked", block_reason={"missing": ["dep"]}
    )
    reread = repository.proposal_item(item_id)
    assert reread["dependency_status"] == "blocked"
    assert reread["dependency_block_reason"] == {"missing": ["dep"]}
