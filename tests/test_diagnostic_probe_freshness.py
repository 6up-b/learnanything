"""Diagnostic-probe freshness (owner design intent).

Probes must be entirely fresh, never-before-seen problems, so that a probe
measures understanding rather than memorization of the question. Three rules
are pinned here:

* freshness reserve — a ``practice_mode: diagnostic_probe`` item never enters
  the ordinary scheduler pool, not even before its one administration; it is
  servable only through diagnostic flows (probe-episode selection) and the
  by-id injection doors (delayed follow-up tasks);
* freshness supply — consuming a diagnostic surface (its single
  administration) enqueues exactly one deduplicated replacement-generation
  need, derived idempotently from attempts + item state;
* never-before-seen gate — probe-intent selection hard-excludes any surface
  group the learner has already seen in ANY administration, and annotates the
  exclusion instead of dropping it silently.
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
    reconcile_diagnostic_surface_needs,
)
from learnloop.diagnosis.probe_episodes import (
    eligible_instruments,
    enter_episode,
    episode_hypothesis_set,
)
from learnloop.scheduling.scheduler import SchedulerSession, build_due_queue
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


def _add_item(
    vault_root,
    item_id: str,
    *,
    practice_mode: str = "diagnostic_probe",
    surface_family: str | None = None,
    facets: tuple[str, ...] = ("recall",),
) -> None:
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
            "evidence_facets": list(facets),
            "evidence_weights": {facet: 1.0 / len(facets) for facet in facets},
            "prompt": f"Fresh diagnostic prompt for {item_id}.",
            "expected_answer": "V",
            "surface_family": surface_family,
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


def _seed_mastery(repository: Repository) -> None:
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


def _vault(tmp_path, *, add_items=((DIAG_ITEM, "diagnostic_probe", None),)):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    for item_id, mode, surface_family in add_items:
        _add_item(root, item_id, practice_mode=mode, surface_family=surface_family)
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    _seed_mastery(repository)
    sync_vault_state(vault, repository, clock=CLOCK)
    return vault, repository


def _attempt(
    vault,
    repository,
    *,
    item_id: str,
    attempt_type: str,
    attempt_id: str,
    score: int = 2,
):
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
                rubric_score=score,
                criterion_points={"correctness": float(score)},
                evidence_rows=[],
                error_attributions=[],
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=None,
            ),
        ),
        clock=CLOCK,
    )


def _queue(vault, repository, **kwargs):
    return build_due_queue(
        vault, repository, clock=CLOCK, persist_explanations=False, **kwargs
    )


# --- 1. Freshness reserve + diagnostic serving doors --------------------------------


def test_fresh_diagnostic_probe_is_reserved_out_of_the_ordinary_queue(tmp_path):
    vault, repository = _vault(tmp_path)

    ids = {entry.practice_item_id for entry in _queue(vault, repository)}

    # Never attempted, fully active — and still not ordinary practice supply.
    assert DIAG_ITEM not in ids
    assert ORDINARY_ITEM in ids


def test_fresh_diagnostic_probe_is_selectable_in_the_probe_episode_branch(tmp_path):
    vault, repository = _vault(tmp_path)
    admit_probe_instrument_card(repository, items=(DIAG_ITEM,))
    episode = enter_episode(vault, repository, LO_ID, clock=CLOCK)
    assert episode.status == "in_progress"

    queue = _queue(vault, repository)
    scheduled = next(
        (entry for entry in queue if entry.practice_item_id == DIAG_ITEM), None
    )

    assert scheduled is not None
    assert scheduled.components["probe_eig"] > 0.0


def test_diagnostic_probe_is_servable_when_injected_by_id_via_followup_task(tmp_path):
    vault, repository = _vault(tmp_path)
    repository.create_followup_task(
        kind="cold_retry",
        case_kind="misconception",
        case_ref="mc_synthetic",
        source_attempt_id=None,
        remediation_episode_id=None,
        not_before="2026-05-01T00:00:00Z",
        expires_at="2026-12-01T00:00:00Z",
        selected_item_id=DIAG_ITEM,
        clock=CLOCK,
    )

    queue = build_due_queue(
        vault,
        repository,
        clock=CLOCK,
        session=SchedulerSession(session_id="sess_followup"),
    )

    assert DIAG_ITEM in {entry.practice_item_id for entry in queue}

    # Once administered, the surface is burned: even a stale by-id follow-up
    # task cannot resurrect it.
    _attempt(
        vault,
        repository,
        item_id=DIAG_ITEM,
        attempt_type="diagnostic_probe",
        attempt_id="att_diag_followup_consume",
    )
    queue_after = build_due_queue(
        vault,
        repository,
        clock=CLOCK,
        session=SchedulerSession(session_id="sess_followup_2"),
    )
    assert DIAG_ITEM not in {entry.practice_item_id for entry in queue_after}


# --- 2. Freshness supply: consumption enqueues one deduplicated need ----------------


def test_consuming_a_diagnostic_administration_enqueues_one_deduplicated_need(tmp_path):
    vault, repository = _vault(tmp_path)

    # No administration -> no need, however often the sweep runs.
    reconcile_diagnostic_surface_needs(vault, repository, clock=CLOCK)
    assert repository.diagnostic_surface_generation_needs() == []

    _attempt(
        vault,
        repository,
        item_id=DIAG_ITEM,
        attempt_type="diagnostic_probe",
        attempt_id="att_diag_consume",
    )

    reconcile_diagnostic_surface_needs(vault, repository, clock=CLOCK)
    reconcile_diagnostic_surface_needs(vault, repository, clock=CLOCK)

    needs = repository.diagnostic_surface_generation_needs(learning_object_id=LO_ID)
    assert len(needs) == 1
    need = needs[0]
    assert need["status"] == "pending"
    assert need["consumed_practice_item_id"] == DIAG_ITEM
    assert need["facet_ids"] == ["recall"]
    assert need["missing_capability"] == "diagnostic_probe_surface"


def test_a_fresh_replacement_surface_resolves_the_pending_need(tmp_path):
    vault, repository = _vault(tmp_path)
    _attempt(
        vault,
        repository,
        item_id=DIAG_ITEM,
        attempt_type="diagnostic_probe",
        attempt_id="att_diag_consume",
    )
    reconcile_diagnostic_surface_needs(vault, repository, clock=CLOCK)
    assert (
        repository.diagnostic_surface_generation_needs(status="pending")[0]["status"]
        == "pending"
    )

    # A never-administered diagnostic surface covering the same facet signature
    # arrives (e.g. an accepted generation proposal): the gap is closed.
    _add_item(vault.root, "pi_diag_replacement")
    vault = load_vault(vault.root)
    sync_vault_state(vault, repository, clock=CLOCK)
    reconcile_diagnostic_surface_needs(vault, repository, clock=CLOCK)

    needs = repository.diagnostic_surface_generation_needs(learning_object_id=LO_ID)
    assert len(needs) == 1
    assert needs[0]["status"] == "resolved"

    # Idempotent after resolution too: no resurrected pending row.
    reconcile_diagnostic_surface_needs(vault, repository, clock=CLOCK)
    assert [
        need["status"]
        for need in repository.diagnostic_surface_generation_needs(learning_object_id=LO_ID)
    ] == ["resolved"]


# --- 3. Never-before-seen gate for probe selection ----------------------------------


def test_probe_selection_hard_excludes_an_already_seen_surface_group(tmp_path):
    vault, repository = _vault(
        tmp_path,
        add_items=(
            (DIAG_ITEM, "diagnostic_probe", "shared_surface"),
            ("pi_shared_ordinary", "short_answer", "shared_surface"),
        ),
    )
    admit_probe_instrument_card(repository, items=(DIAG_ITEM,))
    episode = enter_episode(vault, repository, LO_ID, clock=CLOCK)
    hypothesis_set = episode_hypothesis_set(repository, episode)

    # Control: with no administration anywhere, the surface is probe-eligible.
    assert DIAG_ITEM in {
        entry.item.id
        for entry in eligible_instruments(
            vault, repository, episode, hypothesis_set=hypothesis_set
        )
    }

    # An ORDINARY administration of a same-surface-group sibling burns the
    # whole group for probe use: the learner has seen this surface.
    _attempt(
        vault,
        repository,
        item_id="pi_shared_ordinary",
        attempt_type="independent_attempt",
        attempt_id="att_shared_ordinary",
        score=4,
    )

    assert DIAG_ITEM not in {
        entry.item.id
        for entry in eligible_instruments(
            vault, repository, episode, hypothesis_set=hypothesis_set
        )
    }

    # The scheduler neither serves it as a probe nor lets it leak into the
    # ordinary pool — and the exclusion is annotated on the persisted slate
    # rather than failing silently.
    queue = build_due_queue(
        vault,
        repository,
        clock=CLOCK,
        session=SchedulerSession(session_id="sess_probe_repeat"),
    )
    assert DIAG_ITEM not in {entry.practice_item_id for entry in queue}

    slate = repository.latest_scheduler_slate_by_session("sess_probe_repeat")
    excluded_rows = [
        row
        for row in repository.scheduler_slate_candidates(slate["id"])
        if row["practice_item_id"] == DIAG_ITEM
    ]
    assert excluded_rows, "the withheld probe surface must appear on the slate log"
    components = excluded_rows[0]["components"]
    assert components["probe_surface_repeat_excluded"] == 1.0
    assert components["diagnostic_reserved_excluded"] == 1.0
