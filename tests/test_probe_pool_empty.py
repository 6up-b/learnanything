"""Empty diagnostic-probe pools are never silent (owner decision).

The lifetime never-before-seen gate can leave an open probe episode (or a
pending diagnostic replenishment need) with an EMPTY eligible pool on a small
vault. When that happens the system must (1) queue generation through the
existing needs→commissioning path when an authoring provider is available, and
(2) always raise one urgent, deduplicated maintenance notice per learning
object — self-resolving as soon as a fresh surface appears.
"""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.diagnosis.diagnostic_surface_supply import (
    PROBE_POOL_EMPTY_NOTICE_TYPE,
    probe_pool_empty_conditions,
    reconcile_diagnostic_surface_needs,
    reconcile_empty_probe_pools,
)
from learnloop.ops.maintenance_feed import generate_maintenance_feed
from learnloop.diagnosis.probe_episodes import enter_episode
from learnloop.scheduling.scheduler import build_due_queue
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import (
    ALGORITHM_VERSION,
    NOW,
    NOW_ISO,
    admit_probe_instrument_card,
    create_basic_vault,
)

CLOCK = FrozenClock(NOW)
LO_ID = "lo_svd_definition"
ORDINARY_ITEM = "pi_svd_define_001"
DIAG_ITEM = "pi_diag_fresh_probe"


def _add_item(vault_root, item_id: str, *, practice_mode: str = "diagnostic_probe") -> None:
    attempt_types = (
        ["diagnostic_probe", "dont_know"]
        if practice_mode == "diagnostic_probe"
        else ["independent_attempt", "dont_know"]
    )
    upsert_practice_item(
        vault_root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": practice_mode,
            "attempt_types_allowed": attempt_types,
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": f"Fresh diagnostic prompt for {item_id}.",
            "expected_answer": "V",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {"id": "correctness", "points": 4, "description": "Correct selection."}
                ],
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


def _vault(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    _add_item(root, DIAG_ITEM)
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id=LO_ID,
            logit_mean=0.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at="2026-05-18T12:00:00Z",
            algorithm_version=ALGORITHM_VERSION,
            updated_at=NOW_ISO,
        )
    )
    sync_vault_state(vault, repository, clock=CLOCK)
    return vault, repository


def _attempt(vault, repository, *, item_id: str, attempt_type: str, attempt_id: str):
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="answer",
                attempt_type=attempt_type,
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=2,
                criterion_points={"correctness": 2.0},
                evidence_rows=[],
                error_attributions=[],
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=None,
            ),
        ),
        clock=CLOCK,
    )


def _burn_whole_pool(vault, repository):
    """Open an episode, then administer every surface the LO has."""

    admit_probe_instrument_card(repository, items=(DIAG_ITEM,))
    episode = enter_episode(vault, repository, LO_ID, clock=CLOCK)
    assert episode.status == "in_progress"
    _attempt(
        vault,
        repository,
        item_id=DIAG_ITEM,
        attempt_type="diagnostic_probe",
        attempt_id="att_burn_diag",
    )
    _attempt(
        vault,
        repository,
        item_id=ORDINARY_ITEM,
        attempt_type="independent_attempt",
        attempt_id="att_burn_ordinary",
    )
    return episode


def _pool_notices(repository, *, include_hidden: bool = False):
    return [
        notice
        for notice in repository.maintenance_notices(include_hidden=include_hidden)
        if notice["notice_type"] == PROBE_POOL_EMPTY_NOTICE_TYPE
    ]


# --- Detection + the urgent deduplicated notice --------------------------------------


def test_empty_pool_raises_exactly_one_urgent_deduplicated_notice(tmp_path):
    vault, repository = _vault(tmp_path)
    episode = _burn_whole_pool(vault, repository)

    result = reconcile_empty_probe_pools(
        vault, repository, clock=CLOCK, provider_available=False
    )
    # Idempotent: a second sweep neither duplicates nor resets the notice.
    reconcile_empty_probe_pools(vault, repository, clock=CLOCK, provider_available=False)

    conditions = result["conditions"]
    assert [condition.learning_object_id for condition in conditions] == [LO_ID]
    assert conditions[0].reason == "excluded_as_seen"
    assert conditions[0].episode_id == episode.id

    notices = _pool_notices(repository)
    assert len(notices) == 1
    notice = notices[0]
    assert notice["severity"] == "action_needed"
    assert notice["dedup_key"] == LO_ID
    assert notice["detail"]["reason"] == "excluded_as_seen"
    assert notice["detail"]["probe_episode_id"] == episode.id
    assert notice["status"] == "active"


def test_never_authored_pool_is_distinguished_from_excluded_as_seen(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    # Remove every practice item: the LO has never had a probe-capable surface.
    for item_path in root.rglob("practice-items/*.yaml"):
        item_path.unlink()
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    episode = enter_episode(vault, repository, LO_ID, clock=CLOCK)
    assert episode.status == "pending_items"

    conditions = probe_pool_empty_conditions(vault, repository)
    assert [condition.reason for condition in conditions] == ["never_existed"]

    reconcile_empty_probe_pools(vault, repository, clock=CLOCK, provider_available=False)
    notices = _pool_notices(repository)
    assert len(notices) == 1
    assert notices[0]["detail"]["reason"] == "never_existed"


def test_pending_items_episode_with_fresh_surfaces_is_not_an_empty_pool(tmp_path):
    # A pending_items episode whose LO still has fresh surfaces is the ordinary
    # §10 missing-instrument-binding state, already parked with its own
    # generation need — not the urgent empty-pool condition.
    vault, repository = _vault(tmp_path)
    episode = enter_episode(vault, repository, LO_ID, clock=CLOCK)
    assert episode.status == "pending_items"

    assert probe_pool_empty_conditions(vault, repository) == []
    reconcile_empty_probe_pools(vault, repository, clock=CLOCK, provider_available=False)
    assert _pool_notices(repository) == []


# --- Provider-gated auto-queue --------------------------------------------------------


def test_provider_routed_queues_one_deduplicated_generation_need(tmp_path):
    vault, repository = _vault(tmp_path)
    episode = _burn_whole_pool(vault, repository)
    assert repository.probe_generation_needs(probe_episode_id=episode.id) == []

    result = reconcile_empty_probe_pools(
        vault, repository, clock=CLOCK, provider_available=True
    )
    reconcile_empty_probe_pools(vault, repository, clock=CLOCK, provider_available=True)

    pending = repository.probe_generation_needs(
        probe_episode_id=episode.id, status="pending"
    )
    assert len(pending) == 1
    assert result["queued_need_ids"] == [pending[0].id]
    notice = _pool_notices(repository)[0]
    assert notice["detail"]["provider_available"] is True
    assert notice["detail"]["auto_queued_need_id"] == pending[0].id


def test_no_provider_skips_queueing_but_still_raises_the_notice(tmp_path):
    vault, repository = _vault(tmp_path)
    episode = _burn_whole_pool(vault, repository)

    reconcile_empty_probe_pools(vault, repository, clock=CLOCK, provider_available=False)

    assert repository.probe_generation_needs(probe_episode_id=episode.id) == []
    notices = _pool_notices(repository)
    assert len(notices) == 1
    assert notices[0]["detail"]["provider_available"] is False
    assert notices[0]["detail"]["auto_queued_need_id"] is None


# --- Self-resolution ------------------------------------------------------------------


def test_notice_clears_when_a_fresh_surface_appears(tmp_path):
    vault, repository = _vault(tmp_path)
    _burn_whole_pool(vault, repository)
    reconcile_empty_probe_pools(vault, repository, clock=CLOCK, provider_available=False)
    assert len(_pool_notices(repository)) == 1

    _add_item(vault.root, "pi_diag_replacement")
    vault = load_vault(vault.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    reconcile_empty_probe_pools(vault, repository, clock=CLOCK, provider_available=False)

    assert _pool_notices(repository) == []
    hidden = _pool_notices(repository, include_hidden=True)
    assert [notice["status"] for notice in hidden] == ["resolved"]


def test_pending_diagnostic_need_with_no_fresh_surface_raises_and_clears(tmp_path):
    # No open episode: the pending replenishment need alone must surface the
    # empty pool, and the arrival of a fresh diagnostic surface must clear it
    # (the supply sweep resolves the need; the pool sweep resolves the notice).
    vault, repository = _vault(tmp_path)
    _attempt(
        vault,
        repository,
        item_id=DIAG_ITEM,
        attempt_type="diagnostic_probe",
        attempt_id="att_need_only",
    )
    reconcile_diagnostic_surface_needs(vault, repository, clock=CLOCK)
    needs = repository.diagnostic_surface_generation_needs(status="pending")
    assert len(needs) == 1

    reconcile_empty_probe_pools(vault, repository, clock=CLOCK, provider_available=False)
    notices = _pool_notices(repository)
    assert len(notices) == 1
    assert notices[0]["detail"]["pending_diagnostic_need_ids"] == [needs[0]["id"]]

    _add_item(vault.root, "pi_diag_replacement")
    vault = load_vault(vault.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    reconcile_diagnostic_surface_needs(vault, repository, clock=CLOCK)
    reconcile_empty_probe_pools(vault, repository, clock=CLOCK, provider_available=False)
    assert _pool_notices(repository) == []


# --- Wiring: the scheduler build and the maintenance feed both sweep it --------------


def test_scheduler_build_raises_the_notice_without_a_provider(tmp_path):
    vault, repository = _vault(tmp_path)
    _burn_whole_pool(vault, repository)

    build_due_queue(vault, repository, clock=CLOCK)

    notices = _pool_notices(repository)
    assert len(notices) == 1
    assert notices[0]["severity"] == "action_needed"


def test_maintenance_feed_sustains_and_auto_resolves_the_notice(tmp_path):
    vault, repository = _vault(tmp_path)
    _burn_whole_pool(vault, repository)

    live = generate_maintenance_feed(vault, repository, clock=CLOCK)
    assert any(
        notice["notice_type"] == PROBE_POOL_EMPTY_NOTICE_TYPE for notice in live
    )

    _add_item(vault.root, "pi_diag_replacement")
    vault = load_vault(vault.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    live = generate_maintenance_feed(vault, repository, clock=CLOCK)
    assert not any(
        notice["notice_type"] == PROBE_POOL_EMPTY_NOTICE_TYPE for notice in live
    )
