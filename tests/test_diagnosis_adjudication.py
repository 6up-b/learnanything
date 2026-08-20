"""Diagnosis adjudication store (spec_diagnostic_augmentation_v1.md §2 A4).

Every test drives the real `apply_attempt` -> receipt -> adjudicate path. Hand-
built receipt dicts are how dead code passes review in this area, so nothing
here fabricates one.
"""

from __future__ import annotations

import json
import sqlite3

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.diagnosis.causal_attribution import record_causal_diagnosis_contest
from learnloop.diagnosis.diagnosis_adjudication import (
    adjudicated_ground_truth,
    adjudication_queue,
    anchor_key,
    append_diagnosis_adjudication,
    diagnosis_adjudication_scoreboard,
    diagnosis_snapshot,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault


def _attempt(vault, repository, attempt_id: str, *, abstain: bool = False):
    """One real graded attempt: a named learner-state cause, or an abstention.

    The abstention arm is the case §3 B1 insists the eval set must contain --
    "planted errors that no facet in the vocabulary can express" -- and it is
    exactly what an `abstained` resolution_status with no candidate cause is.
    """

    attribution = GradeAttribution(
        error_type="conceptual_slip",
        severity=0.7,
        evidence="The final factor is not transposed.",
        is_misconception=not abstain,
        misconception_statement=(
            None if abstain else "The learner treats Q and Q transpose as identical."
        ),
        resolution_status="abstained" if abstain else "unresolved",
        abstention_reason=(
            "no facet in the vocabulary names branch retention" if abstain else None
        ),
        cause_scope="unknown" if abstain else "learner_state",
        operation=None if abstain else "transpose_confusion",
        first_divergence=(
            None
            if abstain
            else {"anchor_kind": "span", "criterion_id": "correctness", "quote": "Q"}
        ),
        model_reported_causal_confidence=0.65,
        candidate_causes=(
            []
            if abstain
            else [
                {
                    "statement": "The learner treats Q and Q transpose as identical.",
                    "cause_scope": "learner_state",
                    "target_ref": {
                        "kind": "facet_capability",
                        "facet_id": "recall",
                        "capability": "retrieval",
                    },
                }
            ]
        ),
        postdictive_claims=(
            []
            if abstain
            else [{"criterion_id": "correctness", "must": "not_full_credit"}]
        ),
    )
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
                        "evidence": "Q was used where Q transpose was required.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[attribution],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
                feedback_md="Check the transpose on the final factor.",
                repair_suggestions=[
                    {
                        "practice_mode": "targeted_review",
                        "operator": "insert_transpose",
                        "rationale": "Preserve the factorization; repair the transpose.",
                        "target_refs": [
                            {
                                "kind": "facet_capability",
                                "facet_id": "recall",
                                "capability": "retrieval",
                            }
                        ],
                        "expected_minutes": 2.0,
                        "answer_reveal_budget": 0.5,
                        "repaired_trace": {
                            "learner_work_prefix": "U Sigma ",
                            "repair_insertion_point": {
                                "anchor_kind": "span",
                                "criterion_id": "correctness",
                                "quote": "Q",
                            },
                            "minimal_edit": "replace Q with Q^T",
                            "regenerated_work": "",
                            "repaired_answer_md": "U Sigma Q^T",
                            "changed_latent_claims": [
                                "the right singular-vector factor is transposed"
                            ],
                            "changed_checkpoint_ids": [],
                        },
                    }
                ],
            ),
        ),
        clock=FrozenClock(NOW),
    )


def _vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return load_vault(paths.root), Repository(paths.sqlite_path), paths


def test_correct_verdict_inherits_the_system_choice_and_pins_every_version(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_correct")

    snapshot = diagnosis_snapshot(repository, "att_correct")
    assert snapshot is not None
    assert snapshot.system_abstained is False
    assert snapshot.system_anchor == {
        "anchor_kind": "span",
        "criterion_id": "correctness",
        "quote": "Q",
    }

    # The whole ergonomic claim: "the diagnosis was right" needs no arguments.
    record = append_diagnosis_adjudication(
        repository, attempt_id="att_correct", verdict="correct"
    )

    assert record["verdict"] == "correct"
    assert record["system_abstained"] is False
    # `correct` asserts the system's anchor and repair WERE the right ones, so
    # they become the adjudicated ground truth rather than being left null.
    assert record["adjudicated_anchor"] == snapshot.system_anchor
    assert record["adjudicated_anchor_kind"] == "span"
    assert record["adjudicated_repair_class_id"] == snapshot.system_repair_class_id

    # A verdict that cannot name the version it judged is not an eval record.
    assert record["diagnosis_receipt_id"] == snapshot.receipt_id
    assert record["decision_policy_version"] == snapshot.decision_policy_version
    assert record["repair_policy_version"] == snapshot.repair_policy_version
    assert record["grading_prompt_version"] == snapshot.grading_prompt_version
    assert record["receipt_schema_version"] == snapshot.receipt_schema_version
    assert record["system_snapshot"]["selection_basis"] == snapshot.selection_basis
    assert record["system_snapshot"]["system_repair_class_id"] == (
        snapshot.system_repair_class_id
    )
    assert record["adjudicator_source"] == "human_owner"


def test_store_is_append_only_and_a_second_opinion_supersedes(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_supersede")

    first = append_diagnosis_adjudication(
        repository, attempt_id="att_supersede", verdict="correct"
    )
    second = append_diagnosis_adjudication(
        repository,
        attempt_id="att_supersede",
        verdict="wrong_anchor",
        adjudicated_anchor={
            "anchor_kind": "whole_answer",
            "criterion_id": "correctness",
        },
        adjudicated_repair_md="Re-derive the factorization from the definition.",
        rationale="On reflection the divergence is upstream of the transpose.",
    )

    assert second["supersedes_id"] == first["id"]
    assert repository.active_diagnosis_adjudication("att_supersede")["id"] == (
        second["id"]
    )
    assert [row["id"] for row in repository.diagnosis_adjudications_for_attempt(
        "att_supersede"
    )] == [first["id"], second["id"]]

    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "UPDATE diagnosis_adjudications SET verdict = 'correct' WHERE id = ?",
                (first["id"],),
            )
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "DELETE FROM diagnosis_adjudications WHERE id = ?", (first["id"],)
            )

    # A stale predecessor would fork the chain and give the attempt two heads,
    # which would let one attempt count twice in every rate.
    with pytest.raises(ValueError, match="must supersede the current head"):
        append_diagnosis_adjudication(
            repository,
            attempt_id="att_supersede",
            verdict="correct",
            supersedes_id=first["id"],
        )

    # A superseded verdict must not be counted twice in a rate.
    board = diagnosis_adjudication_scoreboard(repository, group_by=None)
    assert board["overall"]["records"] == 1
    assert board["overall"]["by_verdict"]["wrong_anchor"] == 1


def test_verdict_must_agree_with_what_the_system_actually_did(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_named")
    _attempt(vault, repository, "att_abstained", abstain=True)

    assert diagnosis_snapshot(repository, "att_abstained").system_abstained is True

    with pytest.raises(ValueError, match="named a cause"):
        append_diagnosis_adjudication(
            repository, attempt_id="att_named", verdict="correctly_abstained"
        )
    with pytest.raises(ValueError, match="abstained"):
        append_diagnosis_adjudication(
            repository,
            attempt_id="att_abstained",
            verdict="wrong_anchor",
            adjudicated_anchor={
                "anchor_kind": "span",
                "criterion_id": "correctness",
                "quote": "Q",
            },
        )

    # The SQL CHECK is the backstop if a future caller skips the service.
    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO diagnosis_adjudications(
                  id, attempt_id, diagnosis_receipt_id, verdict, system_abstained,
                  queue_reason, adjudicator_source, system_snapshot_json, created_at
                ) VALUES ('adj_bad', 'att_named', 'dr_x', 'correctly_abstained', 0,
                          'manual', 'human_owner', '{}', '2026-05-19T12:00:00Z')
                """
            )


def test_anchor_asserting_verdicts_require_an_anchor(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_anchor")

    with pytest.raises(ValueError, match="requires an adjudicated anchor"):
        append_diagnosis_adjudication(
            repository, attempt_id="att_anchor", verdict="wrong_anchor"
        )
    with pytest.raises(ValueError, match="repair that should have been chosen"):
        append_diagnosis_adjudication(
            repository, attempt_id="att_anchor", verdict="wrong_repair"
        )
    # `should_have_abstained` is exempt: the claim is that the vocabulary has
    # no name for the cause, so demanding one would be incoherent.
    record = append_diagnosis_adjudication(
        repository,
        attempt_id="att_anchor",
        verdict="should_have_abstained",
        rationale="No facet expresses branch retention.",
    )
    assert record["adjudicated_anchor"] is None


def test_repair_class_outside_the_offered_set_is_rejected(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_repair")

    with pytest.raises(ValueError, match="not one this episode offered"):
        append_diagnosis_adjudication(
            repository,
            attempt_id="att_repair",
            verdict="wrong_repair",
            adjudicated_repair_class_id="rc_invented",
        )
    record = append_diagnosis_adjudication(
        repository,
        attempt_id="att_repair",
        verdict="wrong_repair",
        adjudicated_repair_md="Re-derive the SVD factor order before fixing notation.",
    )
    assert record["adjudicated_repair_class_id"] is None
    assert record["adjudicated_anchor"] is not None  # inherited: anchor was right


def test_abstention_precision_and_recall_watch_both_tails(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_tp", abstain=True)
    _attempt(vault, repository, "att_fp", abstain=True)
    _attempt(vault, repository, "att_fn")
    _attempt(vault, repository, "att_tn")

    append_diagnosis_adjudication(
        repository, attempt_id="att_tp", verdict="correctly_abstained"
    )
    # The sixth verdict. Without it a false abstention has no representation
    # and abstention precision is 1.0 by construction.
    append_diagnosis_adjudication(
        repository,
        attempt_id="att_fp",
        verdict="should_not_have_abstained",
        adjudicated_anchor={
            "anchor_kind": "span",
            "criterion_id": "correctness",
            "quote": "Q",
        },
    )
    append_diagnosis_adjudication(
        repository, attempt_id="att_fn", verdict="should_have_abstained"
    )
    append_diagnosis_adjudication(repository, attempt_id="att_tn", verdict="correct")

    board = diagnosis_adjudication_scoreboard(repository, group_by=None)["overall"]
    assert board["abstention_confusion"] == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}
    assert board["abstention_precision"] == pytest.approx(0.5)
    assert board["abstention_recall"] == pytest.approx(0.5)
    assert board["abstention_cases_present"] is True

    # Only `correct`/`wrong_anchor`/`wrong_repair` score the anchor: an
    # abstention has no anchor, and `should_have_abstained` says the whole
    # diagnosis should not have happened.
    assert board["anchor_scored"] == 1
    assert board["first_divergence_anchor_accuracy"] == pytest.approx(1.0)


def test_empty_denominators_report_null_not_a_flattering_one(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_only_filled")
    append_diagnosis_adjudication(
        repository, attempt_id="att_only_filled", verdict="correct"
    )

    board = diagnosis_adjudication_scoreboard(repository, group_by=None)["overall"]
    assert board["abstention_precision"] is None
    assert board["abstention_recall"] is None
    assert board["abstention_cases_present"] is False
    assert board["first_divergence_anchor_accuracy"] == pytest.approx(1.0)


def test_contest_leads_the_queue_and_is_provenance_never_the_verdict(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_quiet")
    _attempt(vault, repository, "att_contested")

    report = record_causal_diagnosis_contest(
        vault,
        repository,
        attempt_id="att_contested",
        response="diagnosis_wrong",
        clock=FrozenClock(NOW),
    )
    assert report["response"] == "diagnosis_wrong"

    entries = adjudication_queue(repository)
    assert [entry.attempt_id for entry in entries][0] == "att_contested"
    contested = entries[0]
    assert contested.queue_reason == "learner_contest"
    assert contested.learner_report["response"] == "diagnosis_wrong"
    assert {entry.queue_reason for entry in entries} == {
        "learner_contest",
        "sampled",
    }

    # The learner said the diagnosis was wrong; the adjudicator disagrees. The
    # store must record the ADJUDICATOR's verdict and keep the contest as
    # linked provenance -- a bounded learner report is not `adjudicated`
    # authority (§2 / SUPPORT_AUTHORITIES).
    record = append_diagnosis_adjudication(
        repository, attempt_id="att_contested", verdict="correct"
    )
    assert record["verdict"] == "correct"
    assert record["queue_reason"] == "learner_contest"
    assert record["learner_report_id"]

    # ...and the contest itself is untouched: still its own record, still the
    # learner's own words.
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT response FROM causal_attribution_reports WHERE attempt_id = ?",
            ("att_contested",),
        ).fetchall()
    assert [row["response"] for row in rows] == ["diagnosis_wrong"]

    # An adjudicated attempt leaves the queue.
    assert "att_contested" not in {
        entry.attempt_id for entry in adjudication_queue(repository)
    }


def test_abstentions_outrank_the_unflagged_stratum(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_a_plain")
    _attempt(vault, repository, "att_b_abstained", abstain=True)

    entries = adjudication_queue(repository)
    assert [entry.queue_reason for entry in entries] == [
        "system_abstention",
        "sampled",
    ]
    assert entries[0].attempt_id == "att_b_abstained"

    filtered = adjudication_queue(repository, reasons=["system_abstention"])
    assert [entry.attempt_id for entry in filtered] == ["att_b_abstained"]
    with pytest.raises(ValueError, match="unknown queue reasons"):
        adjudication_queue(repository, reasons=["nonsense"])


def test_queue_reason_is_persisted_so_selection_bias_is_auditable(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_c1")
    _attempt(vault, repository, "att_c2", abstain=True)
    record_causal_diagnosis_contest(
        vault,
        repository,
        attempt_id="att_c1",
        response="diagnosis_wrong",
        clock=FrozenClock(NOW),
    )
    append_diagnosis_adjudication(repository, attempt_id="att_c1", verdict="correct")
    append_diagnosis_adjudication(
        repository, attempt_id="att_c2", verdict="correctly_abstained"
    )

    board = diagnosis_adjudication_scoreboard(repository, group_by="queue_reason")
    assert board["overall"]["by_queue_reason"]["learner_contest"] == 1
    assert board["overall"]["by_queue_reason"]["system_abstention"] == 1
    assert {group["queue_reason"] for group in board["groups"]} == {
        "learner_contest",
        "system_abstention",
    }


def test_scoreboard_groups_by_prompt_version_and_model(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_v1")
    append_diagnosis_adjudication(repository, attempt_id="att_v1", verdict="correct")

    board = diagnosis_adjudication_scoreboard(repository, group_by="version")
    assert len(board["groups"]) == 1
    group = board["groups"][0]
    snapshot = diagnosis_snapshot(repository, "att_v1")
    assert group["grading_prompt_version"] == snapshot.grading_prompt_version
    assert group["records"] == 1
    with pytest.raises(ValueError, match="unknown scoreboard grouping"):
        diagnosis_adjudication_scoreboard(repository, group_by="phase_of_the_moon")


def test_ground_truth_export_is_shaped_for_the_planted_overlap(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _attempt(vault, repository, "att_gt_named")
    _attempt(vault, repository, "att_gt_abstained", abstain=True)
    append_diagnosis_adjudication(
        repository, attempt_id="att_gt_named", verdict="correct"
    )
    append_diagnosis_adjudication(
        repository, attempt_id="att_gt_abstained", verdict="correctly_abstained"
    )

    labels = adjudicated_ground_truth(repository)
    assert set(labels) == {"att_gt_named", "att_gt_abstained"}
    assert labels["att_gt_abstained"]["should_abstain"] is True
    assert labels["att_gt_named"]["should_abstain"] is False
    # The join key B4 compares against a planted anchor.
    assert labels["att_gt_named"]["anchor_key"] == anchor_key(
        diagnosis_snapshot(repository, "att_gt_named").system_anchor
    )
    assert labels["att_gt_named"]["grading_prompt_version"]

    scoped = adjudicated_ground_truth(repository, attempt_ids=["att_gt_named"])
    assert set(scoped) == {"att_gt_named"}


def test_attempt_without_a_diagnosis_receipt_cannot_be_adjudicated(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    with pytest.raises(ValueError, match="no diagnosis receipt"):
        append_diagnosis_adjudication(
            repository, attempt_id="att_missing", verdict="correct"
        )


def test_cli_queue_adjudicate_scoreboard_round_trip(tmp_path):
    vault, repository, paths = _vault(tmp_path)
    _attempt(vault, repository, "att_cli_named")
    _attempt(vault, repository, "att_cli_abstained", abstain=True)
    runner = CliRunner()

    queued = runner.invoke(
        app, ["diagnosis", "queue", "--vault", str(paths.root), "--json"]
    )
    assert queued.exit_code == 0, queued.output
    payload = json.loads(queued.output)
    assert [row["attempt_id"] for row in payload["queue"]][0] == "att_cli_abstained"
    assert payload["queue"][0]["queue_reason"] == "system_abstention"
    assert payload["queue"][0]["system"]["system_abstained"] is True

    named = runner.invoke(
        app,
        [
            "diagnosis",
            "adjudicate",
            "att_cli_named",
            "--verdict",
            "wrong_anchor",
            "--anchor-kind",
            "span",
            "--anchor-criterion",
            "correctness",
            "--anchor-quote",
            "U Sigma",
            "--repair",
            "Fix the factor order before the transpose.",
            "--vault",
            str(paths.root),
            "--json",
        ],
    )
    assert named.exit_code == 0, named.output
    record = json.loads(named.output)["adjudication"]
    assert record["verdict"] == "wrong_anchor"
    assert record["adjudicated_anchor"]["quote"] == "U Sigma"

    abstained = runner.invoke(
        app,
        [
            "diagnosis",
            "adjudicate",
            "att_cli_abstained",
            "--verdict",
            "correctly_abstained",
            "--vault",
            str(paths.root),
            "--json",
        ],
    )
    assert abstained.exit_code == 0, abstained.output

    board = runner.invoke(
        app,
        ["diagnosis", "scoreboard", "--vault", str(paths.root), "--json"],
    )
    assert board.exit_code == 0, board.output
    overall = json.loads(board.output)["overall"]
    assert overall["records"] == 2
    assert overall["first_divergence_anchor_accuracy"] == pytest.approx(0.0)
    assert overall["abstention_precision"] == pytest.approx(1.0)
    assert overall["abstention_recall"] == pytest.approx(1.0)

    # A verdict the system's own behaviour contradicts must fail loudly.
    bad = runner.invoke(
        app,
        [
            "diagnosis",
            "adjudicate",
            "att_cli_abstained",
            "--verdict",
            "correct",
            "--vault",
            str(paths.root),
        ],
    )
    assert bad.exit_code == 1


def test_cli_scoreboard_warns_when_no_abstention_case_exists(tmp_path):
    vault, repository, paths = _vault(tmp_path)
    _attempt(vault, repository, "att_warn")
    append_diagnosis_adjudication(repository, attempt_id="att_warn", verdict="correct")

    board = CliRunner().invoke(
        app, ["diagnosis", "scoreboard", "--vault", str(paths.root)]
    )
    assert board.exit_code == 0, board.output
    assert "no abstention cases" in board.output
