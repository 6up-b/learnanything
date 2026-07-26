"""Aug A5 / causal §5.8 rule 4: the missing-vocabulary note store.

The signal under test is capture, not clustering: an abstention that reaches the
store is a permanent record that the vocabulary could not name something, and one
that does not is lost forever (standing constraint 6).
"""

from __future__ import annotations

import sqlite3

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.causal_attribution import materialize_causal_episode
from learnloop.services.missing_vocabulary import (
    MISSING_VOCABULARY_NOTE_VERSION,
    authoring_facet_abstention_notes,
    missing_vocabulary_report,
    record_authoring_facet_abstention_notes,
    record_missing_vocabulary_notes,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def _abstaining_attempt(
    vault,
    repository,
    attempt_id: str,
    *,
    abstention_reason: str = "no facet names branch retention",
    target_criterion_ids: list[str] | None = None,
):
    """An attempt whose diagnosis declines to name the cause."""

    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id="pi_svd_define_001",
                learner_answer_md="U Sigma Q",
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"correctness": 0},
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}",
                        "criterion_id": "correctness",
                        "points_awarded": 0.0,
                        "evidence": "The final factor is not transposed.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[
                    GradeAttribution(
                        error_type="conceptual_slip",
                        severity=0.7,
                        evidence="Something went wrong that the taxonomy cannot name.",
                        is_misconception=False,
                        resolution_status="abstained",
                        abstention_reason=abstention_reason,
                        cause_scope="unknown",
                        target_criterion_ids=target_criterion_ids
                        if target_criterion_ids is not None
                        else ["correctness"],
                        first_divergence={
                            "anchor_kind": "span",
                            "criterion_id": "correctness",
                            "quote": "Q",
                        },
                    )
                ],
                grader_confidence=0.4,
                confidence=2,
                manual_review_reason=None,
                feedback_md="Unclear which step broke.",
                repair_suggestions=[],
            ),
        ),
        clock=FrozenClock(NOW),
    )


def test_diagnostic_abstention_writes_a_note(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    result = _abstaining_attempt(vault, repository, "att_abstain_1")

    notes = repository.missing_vocabulary_notes()
    assert len(notes) == 1
    note = notes[0]
    assert note["source"] == "diagnostic_abstention"
    assert note["abstention_reason"] == "no facet names branch retention"
    assert note["attempt_id"] == result.attempt_id
    assert note["criterion_id"] == "correctness"
    assert note["practice_item_id"] == "pi_svd_define_001"
    assert note["note_version"] == MISSING_VOCABULARY_NOTE_VERSION
    # The trace is what could not be named.
    assert note["trace"]["learner_answer_md"] == "U Sigma Q"
    assert note["trace"]["first_divergence"]["quote"] == "Q"
    # Version stamps mirror A4's set, so a later cluster can tell a real gap from
    # an artifact of one prompt version.
    assert note["grading_prompt_version"]
    assert note["decision_policy_version"] == "causal_p2_v1"
    assert note["repair_policy_version"] == "structural_lexicographic_v2"


def test_note_capture_is_idempotent_across_rematerialization(tmp_path):
    """Regrade and replay both re-materialize; neither may double-count an
    abstention, or the rate this store exists to report is fiction."""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    result = _abstaining_attempt(vault, repository, "att_abstain_idem")
    first = repository.missing_vocabulary_notes()

    for _ in range(3):
        materialize_causal_episode(
            vault,
            repository,
            attempt_id=result.attempt_id,
            repair_suggestions=[],
            clock=FrozenClock(NOW),
        )
    assert repository.missing_vocabulary_notes() == first


def test_an_unlocalized_abstention_still_lands_with_a_null_criterion(tmp_path):
    """"Which criterion" is part of what the vocabulary failed to say, so a null
    there is data — not a reason to drop the note."""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    _abstaining_attempt(
        vault,
        repository,
        "att_abstain_unlocalized",
        target_criterion_ids=[],
    )

    notes = repository.missing_vocabulary_notes()
    assert len(notes) == 1
    assert notes[0]["criterion_id"] is None


def test_a_resolved_diagnosis_writes_no_note(tmp_path):
    """Only refusals are captured. A diagnosis that named its cause is not a
    vocabulary gap."""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id="pi_svd_define_001",
                learner_answer_md="U Sigma Q",
            ),
            attempt_id="att_resolved",
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"correctness": 0},
                evidence_rows=[
                    {
                        "id": "ge_att_resolved",
                        "criterion_id": "correctness",
                        "points_awarded": 0.0,
                        "evidence": "Q used where Q transpose was required.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[
                    GradeAttribution(
                        error_type="conceptual_slip",
                        severity=0.7,
                        evidence="The final factor is not transposed.",
                        is_misconception=True,
                        misconception_statement="Q and Q transpose treated as identical.",
                        resolution_status="unresolved",
                        cause_scope="learner_state",
                        operation="transpose_confusion",
                    )
                ],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
                feedback_md="Check the transpose.",
                repair_suggestions=[],
            ),
        ),
        clock=FrozenClock(NOW),
    )

    assert repository.missing_vocabulary_notes() == []


def test_authoring_facet_abstention_notes_read_the_criteria(tmp_path):
    """Causal §5.8 rule 4: an item that names no canonical facet is the
    authoring-side half of the same signal."""

    notes = authoring_facet_abstention_notes(
        {
            "id": "pi_variant_001",
            "learning_object_id": "lo_svd",
            "capability": "transfer",
            "evidence_facets": [],
            "grading_rubric": {
                "criteria": [
                    {
                        "id": "criterion_sign_cases",
                        "title": "Enumerates both sign cases",
                        "measurement_status": "no_canonical_facet",
                    },
                    {
                        "id": "criterion_local_format",
                        "title": "Uses the requested notation",
                        "measurement_status": "item_local",
                    },
                    {
                        "id": "criterion_mapped",
                        "title": "Applies the definition",
                        "measurement_status": "direct",
                    },
                ]
            },
        }
    )

    assert [note["criterion_id"] for note in notes] == [
        "criterion_sign_cases",
        "criterion_local_format",
    ]
    assert [note["abstention_reason"] for note in notes] == [
        "no_canonical_facet",
        "item_local",
    ]
    assert all(note["source"] == "authoring_facet_abstention" for note in notes)
    assert all(note["attempt_id"] is None for note in notes)
    assert all(
        note["grading_prompt_version"] == "mvp-0.8-causal-attribution-honesty"
        for note in notes
    )
    assert all(note["decision_policy_version"] == "causal_p2_v1" for note in notes)
    assert all(
        note["repair_policy_version"] == "structural_lexicographic_v2"
        for note in notes
    )


def test_authoring_note_carries_the_proposal_run_version_set(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    run_id = repository.insert_agent_run(
        {
            "id": "run_authoring_abstention",
            "purpose": "authoring",
            "provider": "openrouter",
            "provider_type": "openai_compatible",
            "provider_revision": "provider-r7",
            "model": "author-model",
            "prompt_version": "author-prompt-r9",
            "started_at": NOW_ISO,
            "completed_at": NOW_ISO,
            "status": "completed",
        }
    )
    repository.persist_proposal_batch(
        {
            "id": "patch_authoring_abstention",
            "agent_run_id": run_id,
            "purpose": "authoring",
            "source_refs": [],
            "created_at": NOW_ISO,
        },
        [],
    )

    written = record_authoring_facet_abstention_notes(
        repository,
        [
            {
                "id": "proposal_abstention",
                "item_type": "practice_item",
                "payload": {
                    "id": "pi_abstention",
                    "learning_object_id": "lo_svd_definition",
                    "grading_rubric": {
                        "criteria": [
                            {
                                "id": "criterion_local",
                                "measurement_status": "item_local",
                            }
                        ]
                    },
                },
            }
        ],
        patch_id="patch_authoring_abstention",
    )

    assert written == 1
    note = repository.missing_vocabulary_notes()[0]
    assert note["grading_prompt_version"] == "author-prompt-r9"
    assert note["grader_model"] == "author-model"
    assert note["grader_provider"] == "openrouter"
    assert note["grader_provider_revision"] == "provider-r7"
    assert note["agent_run_id"] == run_id
    assert note["decision_policy_version"] == "causal_p2_v1"
    assert note["repair_policy_version"] == "structural_lexicographic_v2"


def test_notes_are_append_only_and_reject_untyped_refusals(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)

    with pytest.raises(ValueError, match="abstention reason"):
        record_missing_vocabulary_notes(
            repository,
            [{"source": "diagnostic_abstention", "abstention_reason": "  "}],
        )
    with pytest.raises(ValueError, match="unknown missing-vocabulary note source"):
        record_missing_vocabulary_notes(
            repository,
            [{"source": "guesswork", "abstention_reason": "because"}],
        )

    written = record_missing_vocabulary_notes(
        repository,
        [
            {
                "source": "authoring_facet_abstention",
                "abstention_reason": "no_canonical_facet",
                "criterion_id": "criterion_sign_cases",
            }
        ],
        clock=FrozenClock(NOW),
    )
    assert written == 1
    note_id = repository.missing_vocabulary_notes()[0]["id"]
    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "UPDATE missing_vocabulary_notes SET abstention_reason = 'x' WHERE id = ?",
                (note_id,),
            )
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "DELETE FROM missing_vocabulary_notes WHERE id = ?", (note_id,)
            )


def test_report_surfaces_the_abstention_rate(tmp_path):
    """The tail that says "the vocabulary cannot name what the learner did".
    Standing constraint 2 requires it to be readable."""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    _abstaining_attempt(vault, repository, "att_rate_1")
    _abstaining_attempt(
        vault,
        repository,
        "att_rate_2",
        abstention_reason="no facet names solution enumeration",
    )

    report = missing_vocabulary_report(repository)
    assert report["notes"] == 2
    assert report["by_source"]["diagnostic_abstention"] == 2
    assert report["abstentions"] == 2
    assert report["attributions"] == 2
    assert report["abstention_rate"] == 1.0
    assert report["uncaptured_diagnostic_abstentions"] == 0
    assert set(report["by_reason"]["diagnostic_abstention"]) == {
        "no facet names branch retention",
        "no facet names solution enumeration",
    }
