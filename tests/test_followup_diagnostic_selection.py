"""Follow-up task selection must not pick administered diagnostic surfaces.

Owner refinement of the single-use rule: prevention happens at task
SELECTION/CREATION time — a generic follow-up must never point at a
``diagnostic_probe`` item that already carried its one administration (the
scheduler's serving door would refuse the task, leaving it
consumed-but-unserved) — with a kind-based exception for explicit
repair/diagnostic journeys (``scheduler.REPAIR_JOURNEY_TASK_KINDS``), whose
by-id injections keep serving.
"""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.followups import _choose_intervention_item
from learnloop.services.scheduler import (
    REPAIR_JOURNEY_TASK_KINDS,
    SchedulerSession,
    build_due_queue,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import ALGORITHM_VERSION, NOW, NOW_ISO, create_basic_vault

CLOCK = FrozenClock(NOW)
LO_ID = "lo_svd_definition"
SOURCE_ITEM = "pi_svd_define_001"
DIAG_ITEM = "pi_diag_single_use"
FALLBACK_ITEM = "pi_followup_fallback"


def _add_item(vault_root, item_id: str, *, practice_mode: str) -> None:
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
            "prompt": f"Prompt for {item_id}.",
            "expected_answer": "V",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {"id": "correctness", "points": 4, "description": "Correct selection."}
                ],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )


def _vault(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    _add_item(root, DIAG_ITEM, practice_mode="diagnostic_probe")
    _add_item(root, FALLBACK_ITEM, practice_mode="short_answer")
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


def _administer(vault, repository, item_id: str, *, attempt_id: str, attempt_type: str):
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


def _select(vault, repository):
    return _choose_intervention_item(
        vault,
        repository,
        attempt_id=None,
        learning_object_id=LO_ID,
        exclude_practice_item_id=SOURCE_ITEM,
        target_facets=["recall"],
        failed_facets=["recall"],
        intent="probe",
        max_error_severity=0.5,
        clock=CLOCK,
    )


def _task(repository, *, kind: str, case_kind: str, case_ref: str, item_id: str):
    return repository.create_followup_task(
        kind=kind,
        case_kind=case_kind,
        case_ref=case_ref,
        source_attempt_id=None,
        remediation_episode_id=None,
        not_before="2026-05-01T00:00:00Z",
        expires_at="2026-12-01T00:00:00Z",
        selected_item_id=item_id,
        learning_object_id=LO_ID,
        clock=CLOCK,
    )


# --- Selection time -------------------------------------------------------------------


def test_fresh_diagnostic_surface_remains_selectable(tmp_path):
    vault, repository = _vault(tmp_path)

    selection = _select(vault, repository)

    slate_ids = {row["practice_item_id"] for row in selection.slate}
    assert DIAG_ITEM in slate_ids
    assert selection.administered_diagnostic_skips == []


def test_generic_selection_skips_an_administered_diagnostic_and_falls_back(tmp_path):
    vault, repository = _vault(tmp_path)
    _administer(
        vault,
        repository,
        DIAG_ITEM,
        attempt_id="att_diag_burned",
        attempt_type="diagnostic_probe",
    )

    selection = _select(vault, repository)

    # The burned surface never enters the slate; the next eligible ordinary
    # item is chosen instead, and the skip is recorded rather than silent.
    slate_ids = {row["practice_item_id"] for row in selection.slate}
    assert DIAG_ITEM not in slate_ids
    assert selection.candidate is not None
    assert selection.candidate.id == FALLBACK_ITEM
    assert selection.administered_diagnostic_skips == [DIAG_ITEM]


# --- Serving time: scheduler refusal consistent with the allowlist --------------------


def test_repair_journey_task_with_administered_diagnostic_still_serves(tmp_path):
    assert "cold_retry" in REPAIR_JOURNEY_TASK_KINDS
    vault, repository = _vault(tmp_path)
    _administer(
        vault,
        repository,
        DIAG_ITEM,
        attempt_id="att_diag_burned",
        attempt_type="diagnostic_probe",
    )
    _task(
        repository,
        kind="cold_retry",
        case_kind="misconception",
        case_ref="mc_repair_journey",
        item_id=DIAG_ITEM,
    )

    queue = build_due_queue(
        vault,
        repository,
        clock=CLOCK,
        session=SchedulerSession(session_id="sess_repair_journey"),
    )

    served = next(
        (entry for entry in queue if entry.practice_item_id == DIAG_ITEM), None
    )
    assert served is not None, "an explicit repair-journey selection must serve"
    assert served.followup_kind == "cold_retry"


def test_stale_generic_task_with_administered_diagnostic_is_refused(tmp_path):
    vault, repository = _vault(tmp_path)
    _administer(
        vault,
        repository,
        DIAG_ITEM,
        attempt_id="att_diag_burned",
        attempt_type="diagnostic_probe",
    )
    _task(
        repository,
        kind="certification_cold_probe",
        case_kind="certification",
        case_ref="cert_stale_generic",
        item_id=DIAG_ITEM,
    )

    queue = build_due_queue(
        vault,
        repository,
        clock=CLOCK,
        session=SchedulerSession(session_id="sess_generic_refusal"),
    )

    assert DIAG_ITEM not in {entry.practice_item_id for entry in queue}
