"""Characterization tests (P0.0, spec_p0_measurement_correctness.md §2): pin current behavior; these tests document reality, not desired behavior. When P0.x intentionally changes behavior, update these tests in the same commit and note the change.

Pins the current assessment-contract and exam behavior:

  * the assessment contract hash is ONE monolithic content hash covering prompt,
    expected answer, rubric semantics, criterion targets, and evidence
    fingerprint — there are no separate card / surface / administration hashes,
  * exam predictions are frozen at exam start (the snapshot fields),
  * exam-pool reservation is keyed by the mutable ``goal_id`` with no
    target-contract version pin (the reservation row shape),
  * "burn" of a completed exam item is incidental: finishing releases the pool
    back to practice, and the only thing preventing re-reservation is the
    attempt-history check — there is no exposure / burn / pristine ledger.
"""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.services.assessment_contracts import (
    compile_assessment_contract,
    contract_hash,
)
from learnloop.services.attempts import ResolvedGrade
from learnloop.services.exam_pool import (
    release_exam_pool,
    reserve_exam_pool,
    reserved_item_ids,
)
from learnloop.services.exam_session import (
    finish_exam,
    record_exam_answer,
    start_exam,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import (
    NOW,
    NOW_ISO,
    create_basic_vault,
    seed_due_item,
    set_algorithm_version,
)

LO_ID = "lo_svd_definition"
GOAL_ID = "goal_linear_algebra_ml"
ITEM_ID = "pi_svd_define_001"


# ---------------------------------------------------------------------------
# Assessment contract: one monolithic hash.
# ---------------------------------------------------------------------------


def _mvp07_vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    return paths, load_vault(paths.root)


def _reload(paths):
    return load_vault(paths.root)


def test_contract_hash_is_single_monolithic_content_hash(tmp_path):
    """One hash covers the whole contract; there is no per-facet hash split.

    ``contract_hash`` is a plain content hash over the full compiled contract
    dict, and the module exposes no card/surface/administration hash function.
    """

    import learnloop.services.assessment_contracts as ac

    hash_fns = [
        name
        for name in dir(ac)
        if not name.startswith("_")
        and name.endswith("_hash")
        and callable(getattr(ac, name))
    ]
    # The only public hashing entry point is the single monolithic contract hash.
    assert hash_fns == ["contract_hash"]

    _paths, vault = _mvp07_vault(tmp_path)
    item = vault.practice_items[ITEM_ID]
    contract = compile_assessment_contract(vault, item)
    # The compiled contract carries no separately-addressed card/surface/
    # administration hash fields — only the whole-contract digest is authoritative.
    assert "card_hash" not in contract
    assert "surface_hash" not in contract
    assert "administration_hash" not in contract
    # The whole compiled contract hashes to a single stable digest.
    assert contract_hash(contract) == contract_hash(contract)


def test_single_hash_moves_when_any_covered_component_changes(tmp_path):
    """Changing prompt, expected answer, rubric, or a target all move the ONE hash.

    Because the hash is monolithic, there is no way to change one semantic
    component without perturbing the single digest.
    """

    paths, vault = _mvp07_vault(tmp_path)
    baseline = contract_hash(compile_assessment_contract(vault, vault.practice_items[ITEM_ID]))

    item_path = paths.practice_item_path("linear-algebra", ITEM_ID)

    # (a) prompt
    data = read_yaml(item_path)
    data["prompt"] = "Define the singular value decomposition precisely."
    write_yaml(item_path, data)
    after_prompt = contract_hash(
        compile_assessment_contract(_reload(paths), _reload(paths).practice_items[ITEM_ID])
    )
    assert after_prompt != baseline

    # (b) expected answer
    data = read_yaml(item_path)
    data["expected_answer"] = "U Sigma V^T with orthonormal U, V and diagonal Sigma."
    write_yaml(item_path, data)
    after_answer = contract_hash(
        compile_assessment_contract(_reload(paths), _reload(paths).practice_items[ITEM_ID])
    )
    assert after_answer not in (baseline, after_prompt)

    # (c) rubric semantics (criterion max points)
    data = read_yaml(item_path)
    data["grading_rubric"]["criteria"][0]["points"] = 3
    write_yaml(item_path, data)
    after_rubric = contract_hash(
        compile_assessment_contract(_reload(paths), _reload(paths).practice_items[ITEM_ID])
    )
    assert after_rubric not in (baseline, after_prompt, after_answer)

    # (d) criterion facet x capability target
    data = read_yaml(item_path)
    data["grading_rubric"]["criteria"][0]["targets"] = [
        {"facet": "recall", "capability": "coordination", "role": "primary"}
    ]
    write_yaml(item_path, data)
    after_target = contract_hash(
        compile_assessment_contract(_reload(paths), _reload(paths).practice_items[ITEM_ID])
    )
    assert after_target not in (baseline, after_prompt, after_answer, after_rubric)


# ---------------------------------------------------------------------------
# Exam session: predictions frozen at start.
# ---------------------------------------------------------------------------


def _add_item(root, item_id, *, facets, difficulty=0.5):
    upsert_practice_item(
        root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "dont_know"],
            "evidence_facets": facets,
            "evidence_weights": {facet: 1.0 for facet in facets},
            "prompt": f"Prompt {item_id}.",
            "expected_answer": "Answer.",
            "difficulty": difficulty,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=FrozenClock(NOW),
    )


def _exam_vault(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_item(vault_root, "pi_exam_a", facets=["recall"], difficulty=0.2)
    _add_item(vault_root, "pi_exam_b", facets=["apply"], difficulty=0.6)
    repository = seed_due_item(paths)
    return load_vault(vault_root), paths, repository


def _grade(rubric_score: int) -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=rubric_score,
        criterion_points={"correctness": float(rubric_score)},
        evidence_rows=[],
        error_attributions=[],
        grader_confidence=1.0,
        confidence=4,
        manual_review_reason=None,
    )


def test_predictions_frozen_at_start_with_snapshot_fields(tmp_path):
    vault, _paths, repository = _exam_vault(tmp_path)
    reserve_exam_pool(vault, repository, vault.goals[0], item_count=2, clock=FrozenClock(NOW))
    session = start_exam(vault, repository, GOAL_ID, clock=FrozenClock(NOW))

    # Freeze happens BEFORE any evidence lands: no attempts recorded at start.
    assert repository.attempted_practice_item_ids() == set()

    frozen = repository.exam_predictions(session["session_id"])
    assert len(frozen) == 2
    for row in frozen:
        # The frozen snapshot fields: a scalar predicted correctness plus a
        # per-facet projection snapshot.
        assert set(row) >= {"practice_item_id", "predicted_correctness", "facet_projection"}
        assert 0.0 <= row["predicted_correctness"] <= 1.0
        projection = row["facet_projection"]
        assert isinstance(projection, dict)
        for facet_snapshot in projection.values():
            assert set(facet_snapshot) == {
                "current_recall",
                "projected_recall",
                "target_recall",
                "label",
            }


def test_predictions_are_not_refrozen_on_restart(tmp_path):
    vault, _paths, repository = _exam_vault(tmp_path)
    reserve_exam_pool(vault, repository, vault.goals[0], item_count=2, clock=FrozenClock(NOW))
    session = start_exam(vault, repository, GOAL_ID, clock=FrozenClock(NOW))
    before = repository.exam_predictions(session["session_id"])

    again = start_exam(vault, repository, GOAL_ID, clock=FrozenClock(NOW))
    assert again["already_started"] is True
    after = repository.exam_predictions(session["session_id"])
    assert [r["predicted_correctness"] for r in after] == [
        r["predicted_correctness"] for r in before
    ]


# ---------------------------------------------------------------------------
# Exam pool: reservation keyed by mutable goal_id, no contract version pin.
# ---------------------------------------------------------------------------


def test_reservation_row_shape_keyed_by_goal_no_contract_version(tmp_path):
    vault, _paths, repository = _exam_vault(tmp_path)
    reserve_exam_pool(vault, repository, vault.goals[0], item_count=2, clock=FrozenClock(NOW))

    rows = repository.reserved_exam_pool_items(GOAL_ID)
    assert rows
    row = rows[0]
    # The reservation is a plain (goal_id, practice_item_id) row with a difficulty
    # stratum and reservation timestamps — no target-contract / assessment-contract
    # version pin, so re-authoring the goal's targets cannot invalidate it.
    assert set(row) == {
        "id",
        "goal_id",
        "practice_item_id",
        "facet_id",
        "difficulty_stratum",
        "reserved_at",
        "released_at",
    }
    assert row["goal_id"] == GOAL_ID
    assert "assessment_contract_version_id" not in row
    assert "target_contract_version" not in row
    assert "contract_version_id" not in row


# ---------------------------------------------------------------------------
# Burn: incidental via attempt history; no exposure/burn/pristine ledger.
# ---------------------------------------------------------------------------


def test_finish_releases_pool_and_reservation_is_blocked_only_by_attempt_history(tmp_path):
    """A completed exam item is attempted, then released back to practice.

    Re-reservation is prevented incidentally by the attempt-history check, not by
    any explicit surface/feedback/pristine/burn ledger.
    """

    vault, _paths, repository = _exam_vault(tmp_path)
    reserve_exam_pool(vault, repository, vault.goals[0], item_count=2, clock=FrozenClock(NOW))
    session = start_exam(vault, repository, GOAL_ID, clock=FrozenClock(NOW))
    session_id = session["session_id"]

    record_exam_answer(vault, repository, session_id, "pi_exam_a", answer_md="A", resolved_grade=_grade(4))
    record_exam_answer(vault, repository, session_id, "pi_exam_b", answer_md="B", resolved_grade=_grade(2))
    finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))

    # Pool released: the items are no longer quarantined (rejoin practice).
    assert reserved_item_ids(repository) == set()

    # Both examined items are now in attempt history.
    attempted = repository.attempted_practice_item_ids()
    assert {"pi_exam_a", "pi_exam_b"} <= attempted

    # A fresh reservation cannot re-pick the burned items — but ONLY because the
    # candidate filter excludes attempted items. There is no exposure/burn table.
    report = reserve_exam_pool(vault, repository, vault.goals[0], item_count=2, clock=FrozenClock(NOW))
    assert set(report.reserved_item_ids).isdisjoint({"pi_exam_a", "pi_exam_b"})

    # The mechanism is exactly the attempt-history check. There is no exam-item
    # burn / pristine ledger: no repository API tracks exam-item exposure/burn
    # state (the only exposure API is the unrelated ingest source-library one).
    assert not any("burn" in name or "pristine" in name for name in dir(repository))
    assert not any("exam" in name and "burn" in name for name in dir(repository))


def test_release_alone_makes_an_unattempted_item_reservable_again(tmp_path):
    """Release (not burn) is what frees a pool; an item never attempted is fully
    reservable again after release. Only an attempt turns it into a burned item.
    """

    vault, _paths, repository = _exam_vault(tmp_path)
    reserve_exam_pool(vault, repository, vault.goals[0], item_count=2, clock=FrozenClock(NOW))
    reserved = set(reserved_item_ids(repository))
    assert reserved

    freed = release_exam_pool(repository, GOAL_ID)
    assert set(freed) == reserved
    assert reserved_item_ids(repository) == set()

    # No attempts happened, so nothing is burned: the same items are reservable.
    again = reserve_exam_pool(vault, repository, vault.goals[0], item_count=2, clock=FrozenClock(NOW))
    assert not again.already_reserved
    assert set(again.reserved_item_ids) == reserved
