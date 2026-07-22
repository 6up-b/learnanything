"""P4 §14.2 step 3 -- dual-authority ownership exclusion across EVERY administration
surface (audit H1). A staged-owned P2 commitment is the staged policy's to administer;
no legacy administration surface (legacy queue, sidecar probe path, held-out exam) may
serve its items. The legacy-queue seam is covered by test_controller_ownership; these
tests close the probe and exam surfaces the audit found unguarded.

Each test demonstrates the pre-fix failure in its docstring: before the fix the probe
selector filtered by learning_object only (a staged-owned item still surfaced) and the
exam pool iterated practice_items with no ownership check (a staged-owned item was
reservable into a held-out pool).
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services import commitments as C
from learnloop.services import controller_ownership as own
from learnloop.services.exam_pool import reserve_exam_pool
from learnloop.services.probe_episodes import (
    eligible_instruments,
    enter_episode,
    episode_hypothesis_set,
    next_probe_item,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, admit_probe_instrument_card, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
CLOCK = FrozenClock(NOW)


def _add_item(vault_root, item_id: str, *, surface_family: str | None = None) -> None:
    upsert_practice_item(
        vault_root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "diagnostic_probe", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": f"Fresh-surface prompt for {item_id}.",
            "expected_answer": "A matrix factorization into U, Sigma, and V transpose.",
            "surface_family": surface_family,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [
                    {
                        "id": "conceptual_slip",
                        "description": "Confuses SVD with a different decomposition.",
                        "max_grade": 1,
                    }
                ],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )


def _p2_commitment(repo, *, target_kind: str, target_ref: str, goal_id: str = "g1") -> str:
    commitment = C.create_commitment(
        repo,
        action="select_exemplar",
        intent_text="master this",
        targets=[{"target_kind": target_kind, "target_ref": target_ref, "role": "required"}],
        depth_preset="master_tasks_like_these",
        goal_id=goal_id,
        clock=CLOCK,
    )
    return commitment.id


# --- Probe path (audit H1) ---------------------------------------------------------


def _probe_env(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _add_item(vault_root, "pi_svd_define_002", surface_family="fresh_surface")
    vault = load_vault(vault_root)
    repo = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repo, items=(ITEM_ID, "pi_svd_define_002"))
    return vault, repo


def test_staged_owned_item_never_surfaces_in_probe_slate(tmp_path):
    """A staged-owned item (legacy_practice_item target) must be dropped from the probe
    eligible slate. Pre-fix eligible_instruments filtered by learning_object only, so the
    owned item still surfaced as an administrable probe candidate."""

    vault, repo = _probe_env(tmp_path)
    episode = enter_episode(vault, repo, LO_ID, clock=CLOCK)
    hset = episode_hypothesis_set(repo, episode)

    before = {e.item.id for e in eligible_instruments(vault, repo, episode, hypothesis_set=hset)}
    assert ITEM_ID in before, "sanity: the item is a probe candidate before ownership"

    cid = _p2_commitment(repo, target_kind="legacy_practice_item", target_ref=ITEM_ID)
    own.assign_p2_run(repo, commitment_id=cid, clock=CLOCK)

    after = {e.item.id for e in eligible_instruments(vault, repo, episode, hypothesis_set=hset)}
    assert ITEM_ID not in after, "staged-owned item must not surface via the probe path"
    # The sibling item on the same (partially-owned) LO is unaffected.
    assert "pi_svd_define_002" in after
    # next_probe_item peeks the same slate -> never the owned item.
    peek = next_probe_item(vault, repo, LO_ID)
    assert peek is not None and peek.item.id != ITEM_ID


def test_wholly_staged_owned_lo_refuses_probe_administration(tmp_path):
    """When the whole learning object is staged-owned (learning_object target), the probe
    selector refuses outright with a typed error -- no legacy probe episode may be
    administered on it. Pre-fix it silently returned a slate."""

    vault, repo = _probe_env(tmp_path)
    episode = enter_episode(vault, repo, LO_ID, clock=CLOCK)
    hset = episode_hypothesis_set(repo, episode)

    cid = _p2_commitment(repo, target_kind="learning_object", target_ref=LO_ID)
    own.assign_p2_run(repo, commitment_id=cid, clock=CLOCK)

    with pytest.raises(own.StagedOwnedAdministrationRefused):
        eligible_instruments(vault, repo, episode, hypothesis_set=hset)


def test_unowned_probe_slate_is_byte_identical(tmp_path):
    """No ownership rows -> the exclusion is a no-op; the probe slate is unchanged."""

    vault, repo = _probe_env(tmp_path)
    episode = enter_episode(vault, repo, LO_ID, clock=CLOCK)
    hset = episode_hypothesis_set(repo, episode)
    assert own.staged_owned_practice_item_ids(vault, repo) == set()
    slate = {e.item.id for e in eligible_instruments(vault, repo, episode, hypothesis_set=hset)}
    assert ITEM_ID in slate and "pi_svd_define_002" in slate


# --- Exam path (audit H1) ----------------------------------------------------------


def _exam_add_item(root, item_id, *, facets, difficulty=0.5, surface_family=None):
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
            "surface_family": surface_family,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct."}],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )


def _exam_env(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    _exam_add_item(vault_root, "pi_pool_recall_easy", facets=["recall"], difficulty=0.1, surface_family="fam_a")
    _exam_add_item(vault_root, "pi_pool_apply_mid", facets=["apply"], difficulty=0.5, surface_family="fam_b")
    _exam_add_item(vault_root, "pi_pool_derive_hard", facets=["derive"], difficulty=0.9, surface_family="fam_c")
    vault = load_vault(vault_root)
    repo = Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=CLOCK)
    return load_vault(vault_root), repo


def test_staged_owned_item_not_reservable_into_exam_pool(tmp_path):
    """A staged-owned item must be excluded from a held-out exam reservation. Pre-fix
    _candidates iterated practice_items with no ownership check, so the item was
    reservable into the pool -- two controllers over the same item."""

    vault, repo = _exam_env(tmp_path)
    goal = vault.goals[0]

    baseline = reserve_exam_pool(vault, repo, goal, clock=CLOCK)
    assert baseline.reserved_item_ids, "sanity: some items reservable before ownership"
    target = baseline.reserved_item_ids[0]
    # Release so the second reserve is a fresh selection (not the idempotent branch).
    from learnloop.services.exam_pool import release_exam_pool

    release_exam_pool(repo, goal.id, clock=CLOCK)

    cid = _p2_commitment(repo, target_kind="legacy_practice_item", target_ref=target)
    own.assign_p2_run(repo, commitment_id=cid, clock=CLOCK)

    after = reserve_exam_pool(vault, repo, goal, clock=CLOCK)
    assert target not in after.reserved_item_ids, "staged-owned item must not be exam-reservable"


def test_assign_refused_when_item_already_exam_reserved(tmp_path):
    """The mutual-exclusion is symmetric: a commitment whose item is already held-out
    exam-reserved cannot become staged-owned (typed conflict)."""

    vault, repo = _exam_env(tmp_path)
    goal = vault.goals[0]
    report = reserve_exam_pool(vault, repo, goal, clock=CLOCK)
    reserved_id = report.reserved_item_ids[0]

    cid = _p2_commitment(repo, target_kind="legacy_practice_item", target_ref=reserved_id)
    with pytest.raises(own.ExamReservationOwnershipConflict):
        own.assign_p2_run(repo, commitment_id=cid, clock=CLOCK)
    assert own.resolve_owner(repo, cid) == own.LEGACY
