from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.curriculum.graph_edit_proposals import (
    GraphEditError,
    propose_graph_edits,
    queue_restructure_request,
    resolve_edge_direction,
)
from learnloop.ops.maintenance_feed import generate_maintenance_feed
from learnloop.content.proposals.patches import apply_accepted_items, reject_applied_items
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import (
    upsert_concept,
    upsert_concept_edge,
    upsert_learning_object,
    upsert_practice_item,
)
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault, write_facets

CLOCK = FrozenClock(NOW)


def _add_second_concept(root) -> None:
    """A second concept + LO + practice item so prerequisite edges have endpoints."""

    upsert_concept(
        root,
        "matrix_norms",
        {"title": "Matrix norms", "type": "concept", "description": "Norms of matrices."},
        clock=CLOCK,
    )
    upsert_learning_object(
        root,
        {
            "id": "lo_matrix_norms",
            "title": "Matrix norms",
            "subjects": ["linear-algebra"],
            "concept": "matrix_norms",
            "knowledge_type": "definition",
            "status": "active",
            "summary": "Define the spectral and Frobenius norms.",
            "prerequisites": [],
            "confusables": [],
            "provenance": {"origin": "human", "source_refs": []},
        },
        clock=CLOCK,
    )
    upsert_practice_item(
        root,
        {
            "id": "pi_matrix_norms_001",
            "learning_object_id": "lo_matrix_norms",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Define the Frobenius norm.",
            "expected_answer": "Square root of the sum of squared entries.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
        },
        clock=CLOCK,
    )


def _record_attempt(repository, *, attempt_id, item_id, lo_id, rubric_score, created_at) -> None:
    repository.insert_practice_attempt(
        {
            "id": attempt_id,
            "practice_item_id": item_id,
            "learning_object_id": lo_id,
            "practice_mode": "short_answer",
            "attempt_type": "independent_attempt",
            "rubric_score": rubric_score,
            "created_at": created_at,
            "updated_at": created_at,
        }
    )


# --- propose_graph_edits ----------------------------------------------------


def test_propose_graph_edits_creates_one_user_batch(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _add_second_concept(paths.root)

    result = propose_graph_edits(
        paths.root,
        "SVD is a prerequisite for matrix norms.",
        [
            {
                "item_type": "concept_edge",
                "operation": "create",
                "payload": {
                    "source": "singular_value_decomposition",
                    "target": "matrix_norms",
                    "relation_type": "prerequisite",
                },
            }
        ],
    )

    assert result["batch_id"]
    assert len(result["items"]) == 1
    assert result["items"][0]["item_type"] == "concept_edge"
    assert result["items"][0]["validation_status"] == "valid"
    assert result["items"][0]["decision"] == "pending"

    repository = Repository(paths.sqlite_path)
    batch = repository.proposal_batch(result["batch_id"])
    assert batch["purpose"] == "graph_editor"
    assert batch["summary"] == "SVD is a prerequisite for matrix norms."
    run = repository.agent_run(batch["agent_run_id"])
    assert run["provider"] == "user"


def test_propose_graph_edits_requires_rationale_and_edits(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    with pytest.raises(GraphEditError):
        propose_graph_edits(paths.root, "   ", [{"item_type": "concept", "operation": "create", "payload": {}}])
    with pytest.raises(GraphEditError):
        propose_graph_edits(paths.root, "rationale", [])


def test_propose_graph_edits_update_stamps_target_hash(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")

    result = propose_graph_edits(
        paths.root,
        "Rename the SVD concept.",
        [
            {
                "item_type": "concept",
                "operation": "update",
                "target_entity_id": "singular_value_decomposition",
                "payload": {"title": "SVD (edited)"},
            }
        ],
    )

    repository = Repository(paths.sqlite_path)
    item = repository.proposal_items(result["batch_id"])[0]
    assert item["operation"] == "update"
    # §8.2 accept-time staleness hash is stamped like the synthesis/append flow.
    assert item["payload"]["expected_target_hash"].startswith("sha256:")


def test_propose_graph_edits_task_blueprint_raw_row(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")

    result = propose_graph_edits(
        paths.root,
        "Add a blueprint to the SVD LO.",
        [
            {
                "item_type": "task_blueprint",
                "operation": "create",
                "target_entity_id": "lo_svd_definition",
                "payload": {
                    "id": "bp_svd_recall",
                    "learning_object_id": "lo_svd_definition",
                    "weight": 1.0,
                    "recipes": [],
                },
            }
        ],
    )

    repository = Repository(paths.sqlite_path)
    item = repository.proposal_items(result["batch_id"])[0]
    assert item["item_type"] == "task_blueprint"
    assert item["decision"] == "pending"
    assert item["validation_status"] == "valid"


def test_propose_graph_edits_rejects_unknown_item_type(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    with pytest.raises(GraphEditError):
        propose_graph_edits(
            paths.root, "bad", [{"item_type": "practice_item", "operation": "create", "payload": {}}]
        )


# --- concept_edge deactivate apply / revert ---------------------------------


def _seed_single_prereq_edge(paths) -> None:
    _add_second_concept(paths.root)
    upsert_concept_edge(
        paths.root,
        {
            "id": "edge_svd_norms",
            "relation_type": "prerequisite",
            "source": "singular_value_decomposition",
            "target": "matrix_norms",
            "strength": 0.8,
            "rationale": "SVD comes first.",
        },
        clock=CLOCK,
    )


def test_concept_edge_deactivate_snapshots_edge_into_payload(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _seed_single_prereq_edge(paths)

    # A bare retire gesture (only a target id) must still validate and carry the
    # full pre-apply snapshot for revert.
    result = propose_graph_edits(
        paths.root,
        "Retire the SVD -> norms edge.",
        [{"item_type": "concept_edge", "operation": "delete", "target_entity_id": "edge_svd_norms"}],
    )

    repository = Repository(paths.sqlite_path)
    item = repository.proposal_items(result["batch_id"])[0]
    assert item["operation"] == "deactivate"
    assert item["payload"]["source_concept_id"] == "singular_value_decomposition"
    assert item["payload"]["target_concept_id"] == "matrix_norms"
    assert item["payload"]["relation_type"] == "prerequisite"
    assert item["payload"]["strength"] == 0.8
    assert item["payload"]["rationale"] == "SVD comes first."


def test_accept_concept_edge_deactivate_removes_edge(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _seed_single_prereq_edge(paths)
    assert any(edge.id == "edge_svd_norms" for edge in load_vault(paths.root).edges)

    result = propose_graph_edits(
        paths.root,
        "Retire the SVD -> norms edge.",
        [{"item_type": "concept_edge", "operation": "delete", "target_entity_id": "edge_svd_norms"}],
    )
    item_id = result["items"][0]["id"]
    applied = apply_accepted_items(paths.root, result["batch_id"], [item_id], clock=CLOCK)
    assert applied.applied_count == 1

    reloaded = load_vault(paths.root)
    assert all(edge.id != "edge_svd_norms" for edge in reloaded.edges)


def test_reject_after_apply_restores_concept_edge(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _seed_single_prereq_edge(paths)

    result = propose_graph_edits(
        paths.root,
        "Retire the SVD -> norms edge.",
        [{"item_type": "concept_edge", "operation": "delete", "target_entity_id": "edge_svd_norms"}],
    )
    item_id = result["items"][0]["id"]
    apply_accepted_items(paths.root, result["batch_id"], [item_id], clock=CLOCK)
    assert all(edge.id != "edge_svd_norms" for edge in load_vault(paths.root).edges)

    rejected = reject_applied_items(paths.root, result["batch_id"], [item_id], clock=CLOCK)
    assert rejected == 1

    reloaded = load_vault(paths.root)
    edge = next(edge for edge in reloaded.edges if edge.id == "edge_svd_norms")
    assert edge.source == "singular_value_decomposition"
    assert edge.target == "matrix_norms"
    assert edge.relation_type == "prerequisite"
    assert edge.strength == 0.8
    assert edge.rationale == "SVD comes first."


def test_resolve_edge_direction_retire_removes_and_can_restore(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _seed_single_prereq_edge(paths)
    repository = Repository(paths.sqlite_path)
    generate_maintenance_feed(load_vault(paths.root), repository, clock=CLOCK)

    result = resolve_edge_direction(paths.root, "edge_svd_norms", "retire", "Not actually a prerequisite.")
    assert result["filed_edit"] is True
    item_id = result["items"][0]["id"]

    apply_accepted_items(paths.root, result["batch_id"], [item_id], clock=CLOCK)
    assert all(edge.id != "edge_svd_norms" for edge in load_vault(paths.root).edges)

    reject_applied_items(paths.root, result["batch_id"], [item_id], clock=CLOCK)
    assert any(edge.id == "edge_svd_norms" for edge in load_vault(paths.root).edges)


def test_propose_graph_edits_rejects_concept_delete_at_filing(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    with pytest.raises(GraphEditError) as exc:
        propose_graph_edits(
            paths.root,
            "Drop the SVD concept.",
            [{"item_type": "concept", "operation": "delete", "target_entity_id": "singular_value_decomposition"}],
        )
    assert exc.value.code == "unsupported_operation"


# --- queue_restructure_request ----------------------------------------------


def test_queue_restructure_request_requires_a_locked_facet(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    # No goal -> facet "recall" is unlocked; queueing must point at the normal flow.
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    write_facets(paths, [{"id": "recall", "kind": "definition", "claim": "SVD recall."}])

    with pytest.raises(GraphEditError) as exc:
        queue_restructure_request(paths.root, ["recall"], "merge", "combine facets")
    assert exc.value.code == "facets_not_locked"


def test_queue_restructure_request_records_and_surfaces_in_feed(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")  # goal scopes the SVD concept -> facet locked
    write_facets(paths, [{"id": "recall", "kind": "definition", "claim": "SVD recall."}])

    record = queue_restructure_request(paths.root, ["recall"], "split", "recall conflates two skills")
    assert record["need_id"]
    assert record["locked_facet_ids"] == ["recall"]
    assert record["status"] == "pending"

    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    notices = generate_maintenance_feed(vault, repository, clock=CLOCK)
    restructure = [n for n in notices if n["notice_type"] == "restructure_request"]
    assert len(restructure) == 1
    assert restructure[0]["detail"]["operation"] == "split"
    assert restructure[0]["detail"]["facet_ids"] == ["recall"]


def test_queue_restructure_request_rejects_bad_operation(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    with pytest.raises(GraphEditError):
        queue_restructure_request(paths.root, ["recall"], "rename", "nope")


# --- ambiguous_edge_direction notices + resolve_edge_direction --------------


def _seed_bidirectional_prereq(paths) -> None:
    _add_second_concept(paths.root)
    upsert_concept_edge(
        paths.root,
        {
            "id": "edge_svd_norms",
            "relation_type": "prerequisite",
            "source": "singular_value_decomposition",
            "target": "matrix_norms",
            "rationale": "SVD first.",
        },
        clock=CLOCK,
    )
    upsert_concept_edge(
        paths.root,
        {
            "id": "edge_norms_svd",
            "relation_type": "prerequisite",
            "source": "matrix_norms",
            "target": "singular_value_decomposition",
        },
        clock=CLOCK,
    )


def test_ambiguous_edge_direction_notice_carries_evidence(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _seed_bidirectional_prereq(paths)
    repository = Repository(paths.sqlite_path)

    # First correct on the SVD (source) item at t1; the norms (target) item is
    # wrong before t1 and correct after -> before/after success 0.0 -> 1.0.
    _record_attempt(
        repository, attempt_id="a_norms_before", item_id="pi_matrix_norms_001",
        lo_id="lo_matrix_norms", rubric_score=1, created_at="2026-05-19T10:00:00Z",
    )
    _record_attempt(
        repository, attempt_id="a_svd_correct", item_id="pi_svd_define_001",
        lo_id="lo_svd_definition", rubric_score=4, created_at="2026-05-19T11:00:00Z",
    )
    _record_attempt(
        repository, attempt_id="a_norms_after", item_id="pi_matrix_norms_001",
        lo_id="lo_matrix_norms", rubric_score=4, created_at="2026-05-19T12:00:00Z",
    )

    vault = load_vault(paths.root)
    notices = generate_maintenance_feed(vault, repository, clock=CLOCK)
    ambiguous = {n["dedup_key"]: n for n in notices if n["notice_type"] == "ambiguous_edge_direction"}
    assert {"edge_svd_norms", "edge_norms_svd"} <= set(ambiguous)

    svd_edge = ambiguous["edge_svd_norms"]
    assert svd_edge["detail"]["reason"] == "bidirectional"
    assert svd_edge["detail"]["source_concept"]["title"] == "Singular Value Decomposition"
    evidence = svd_edge["detail"]["evidence"]
    assert evidence["target_success_before"] == 0.0
    assert evidence["target_success_after"] == 1.0


def test_ambiguous_edge_direction_omits_sparse_evidence(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _seed_bidirectional_prereq(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    notices = generate_maintenance_feed(vault, repository, clock=CLOCK)
    ambiguous = next(n for n in notices if n["notice_type"] == "ambiguous_edge_direction")
    # No attempts -> evidence omitted rather than fabricated.
    assert ambiguous["detail"]["evidence"] is None


def test_resolve_edge_direction_flip_files_proposal_and_resolves_notice(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _seed_bidirectional_prereq(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    generate_maintenance_feed(vault, repository, clock=CLOCK)

    result = resolve_edge_direction(paths.root, "edge_svd_norms", "flip", "Norms come first.")
    assert result["filed_edit"] is True
    assert result["batch_id"]
    assert result["resolved_notice_ids"]

    item = repository.proposal_items(result["batch_id"])[0]
    assert item["item_type"] == "concept_edge"
    assert item["operation"] == "update"
    # Flip swaps the endpoints on the same edge id.
    assert item["payload"]["source_concept_id"] == "matrix_norms"
    assert item["payload"]["target_concept_id"] == "singular_value_decomposition"
    assert item["target_entity_id"] == "edge_svd_norms"

    for notice_id in result["resolved_notice_ids"]:
        assert repository.maintenance_notice(notice_id)["status"] == "resolved"


def test_resolve_edge_direction_keep_resolves_without_filing(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _seed_bidirectional_prereq(paths)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    generate_maintenance_feed(vault, repository, clock=CLOCK)

    result = resolve_edge_direction(paths.root, "edge_svd_norms", "keep", "Direction is right.")
    assert result["filed_edit"] is False
    assert result["batch_id"] is None
    assert result["resolved_notice_ids"]


def test_resolve_edge_direction_unknown_edge_errors(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    with pytest.raises(GraphEditError) as exc:
        resolve_edge_direction(paths.root, "edge_missing", "flip", "x")
    assert exc.value.code == "edge_not_found"
