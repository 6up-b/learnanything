from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock, utc_now_iso
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.db.stores import followup_serve
from learnloop.goals import goal_series
from learnloop.goals.goal_series import goal_report_series
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, seed_due_item

ITEM_ID = "pi_svd_define_001"

_GUARDED_ATTEMPT_TABLES = (
    "attempt_diagnoses",
    "blind_grade_records",
    "diagnosis_context_receipts",
    "diagnosis_feedback",
    "diagnosis_would_merge_log",
    "followup_workflow_events",
    "generated_probe_burns",
    "generated_probe_items",
    "grading_clarification_responses",
    "help_assists",
    "router_decision_bindings",
)


def _pruned_table_counts(connection):
    refs = connection.execute(
        """SELECT tables.name, fk."table", fk.on_delete
           FROM sqlite_schema AS tables JOIN pragma_foreign_key_list(tables.name) AS fk
           WHERE tables.type = 'table'"""
    ).fetchall()
    tables = {"practice_attempts"}
    while True:
        children = {child for child, parent, action in refs if parent in tables and action != "SET NULL"}
        if children <= tables:
            return {
                table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in sorted(tables)
            }
        tables.update(children)


def _live_prune_snapshot(repository):
    with repository.connection() as connection:
        return (
            [tuple(row) for row in connection.execute(
                "SELECT name, tbl_name, sql FROM sqlite_schema WHERE type = 'trigger' ORDER BY name"
            )],
            _pruned_table_counts(connection),
        )


def _seed_guarded_attempt_children(repository, attempt_id, diagnosis_id, clock):
    at = utc_now_iso(clock)
    repository.insert_blind_grade_record(
        attempt_id=attempt_id, agent_run_id=None, grading_prompt_version="test",
        output_schema_version="test", context_hash="test", record={}, clock=clock,
    )
    repository.insert_diagnosis_feedback(
        attempt_id=attempt_id, diagnosis_id=diagnosis_id, response="unsure", clock=clock,
    )
    repository.insert_would_merge(
        diagnosis_id=diagnosis_id, hypothesis_id="hyp_test", model_id="test",
        exact_key="test", exact_group_ids=[], neighbors=[], clock=clock,
    )
    repository.insert_grading_clarification(
        {"id": "clarification", "attempt_id": attempt_id, "reason": "other",
         "trigger": "hedged_criterion", "question_md": "Which factor?", "expires_at": at},
        clock=clock,
    )
    repository.insert_grading_clarification_response(
        {"id": "response", "clarification_id": "clarification", "answer_md": "The last one."},
        clock=clock,
    )
    with repository.connection() as connection:
        connection.execute(
            """INSERT INTO help_assists
               (id, surface, assist_kind, practice_item_id, attempt_id, chooser, shown, requested_at)
               VALUES ('assist', 'practice', 'hint', ?, ?, 'none', 1, ?)""",
            (ITEM_ID, attempt_id, at),
        )
        connection.execute(
            """INSERT INTO router_decisions
               (id, receipt_key, decision_kind, surface, mode, policy, algorithm_version,
                log_version, snapshot_hash, candidates_json, exclusions_json, candidate_count,
                propensity_kind, detail_json, created_at)
               VALUES ('decision', 'key', 'plan_interrupt', 'desktop', 'live', 'staged_v1',
                       'test', 'v1', 'hash', '[]', '[]', 0, 'not_served', '{}', ?)""",
            (at,),
        )
        followup_serve.insert_workflow(connection, {
            "id": "workflow", "source_attempt_id": attempt_id, "revision_key": "test",
            "learning_object_id": "lo_svd_definition", "session_id": None, "surface": "desktop",
            "origin": "practice", "feedback_held": 0, "created_at": at,
        })
        followup_serve.insert_generated_probe(
            connection, practice_item_id="pi_generated", item_revision="rev", source="workflow",
            workflow_id="workflow", at=at,
        )
        followup_serve.insert_burn(
            connection, practice_item_id="pi_generated", kind="retired", item_revision="rev",
            reason="test", workflow_id="workflow", at=at,
        )
        followup_serve.append_binding(
            connection, decision_id="decision", workflow_id="workflow", binding_kind="item",
            practice_item_id="pi_generated", at=at,
        )
        connection.commit()


def _loaded(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = seed_due_item(paths)
    return load_vault(vault_root), repository


def test_series_reflects_evidence_arriving_over_time(tmp_path):
    vault, repository = _loaded(tmp_path)
    goal = vault.goals[0]

    # Evidence lands 8 days after goal creation.
    attempt_at = NOW + timedelta(days=8)
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="SVD factorizes into U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(attempt_at),
    )

    series = goal_report_series(
        vault, repository, goal, clock=FrozenClock(NOW + timedelta(days=10))
    )

    assert len(series) >= 2
    # All points measure the same scope.
    totals = {point.total for point in series}
    assert len(totals) == 1 and totals.pop() > 0
    # The first checkpoint (goal creation) predates the attempt: replay of the
    # truncated log must show no on-track facets there.
    assert series[0].on_track_count == 0
    # Points are chronological and the last one is the live report.
    ats = [point.at for point in series]
    assert ats == sorted(ats)
    payload = series[0].as_dict()
    assert set(payload) == {
        "at",
        "on_track_count",
        "total",
        "on_track_fraction",
        "certified_count",
        "examined_count",
        "attainment_fraction",
        "predicted_recall_mean",
        "demonstrated_count",
        "ready_mean",
        "projected_ready_mean",
        "projection",
        "decay_estimated",
        "held_flat",
    }


def test_series_scratch_copy_attaches_without_migrating(tmp_path, monkeypatch):
    vault, repository = _loaded(tmp_path)

    def unexpected_migration(*_args, **_kwargs):
        raise AssertionError("historical scratch copies must retain their schema")

    monkeypatch.setattr(
        "learnloop.db.repositories.create_or_attach_current",
        unexpected_migration,
    )

    series = goal_report_series(
        vault,
        repository,
        vault.goals[0],
        clock=FrozenClock(NOW + timedelta(days=10)),
    )

    assert series


def test_series_replays_past_non_cascading_attempt_references(tmp_path):
    """Rows referencing attempts with NO ACTION must not break checkpoint truncation."""

    vault, repository = _loaded(tmp_path)
    goal = vault.goals[0]

    attempt_at = NOW + timedelta(days=8)
    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="SVD factorizes into U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(attempt_at),
    )
    repository.insert_attempt_submission_receipt(
        submission_id="sub_goal_series_001",
        attempt_id=attempt.attempt_id,
        practice_item_id=ITEM_ID,
        result={"ok": True},
        clock=FrozenClock(attempt_at),
    )

    series = goal_report_series(
        vault, repository, goal, clock=FrozenClock(NOW + timedelta(days=10))
    )

    assert series[0].on_track_count == 0
    # The live receipt survives; only the scratch copy is truncated.
    assert repository.attempt_submission_receipt("sub_goal_series_001") is not None


@pytest.mark.parametrize("with_children", [False, True], ids=["diagnosis", "all-guards"])
def test_series_prunes_append_only_rows_only_in_scratch(tmp_path, monkeypatch, with_children):
    vault, repository = _loaded(tmp_path)
    attempt_clock = FrozenClock(NOW + timedelta(days=8))
    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="SVD factorizes into U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=attempt_clock,
    )
    diagnosis_id = repository.insert_attempt_diagnosis(
        attempt_id=attempt.attempt_id,
        diagnosis_prompt_version="test",
        mode="live",
        history_mode="full",
        status="completed",
        proposal={"analysis_md": "The response names the three factors."},
        causal_view=None,
        validation_report=None,
        receipt={} if with_children else None,
        clock=attempt_clock,
    )
    if with_children:
        _seed_guarded_attempt_children(repository, attempt.attempt_id, diagnosis_id, attempt_clock)
    before = _live_prune_snapshot(repository)
    guarded_tables = _GUARDED_ATTEMPT_TABLES if with_children else ("attempt_diagnoses",)
    for table in guarded_tables:
        assert before[1][table] == 1

    rebuild = goal_series.rebuild_derived_state

    def check_pruned_rows(vault, scratch, **kwargs):
        with scratch.connection() as connection:
            for table in ("practice_attempts", *guarded_tables):
                assert connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] == 0, table
        return rebuild(vault, scratch, **kwargs)

    monkeypatch.setattr(goal_series, "rebuild_derived_state", check_pruned_rows)

    series = goal_report_series(
        vault, repository, vault.goals[0], clock=FrozenClock(NOW + timedelta(days=10))
    )

    assert [point.examined_count for point in series] == [0, 0, 1]
    assert _live_prune_snapshot(repository) == before


def test_the_scratch_guard_drop_reads_every_delete_guard_from_the_schema(tmp_path):
    """The drop lists no trigger by name: a table that gains a guard later is covered."""

    from learnloop.goals.goal_series_store import drop_scratch_delete_guards

    _vault, repository = _loaded(tmp_path)
    with repository.connection() as connection:  # this test's own vault stands for the scratch copy
        dropped = set(drop_scratch_delete_guards(connection))
        left = [
            name
            for name, sql in connection.execute("SELECT name, sql FROM sqlite_schema WHERE type = 'trigger'")
            if "DELETE" in sql.upper().split(" ON ")[0] and "RAISE" in sql.upper()
        ]
        connection.rollback()
    assert {f"{table}_no_delete" for table in _GUARDED_ATTEMPT_TABLES} <= dropped
    assert left == []


def test_series_shares_one_replay_across_unchanged_checkpoints(tmp_path, monkeypatch):
    vault, repository = _loaded(tmp_path)
    goal = vault.goals[0]

    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="SVD factorizes into U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW + timedelta(days=8)),
    )

    rebuilds = []
    real_rebuild = goal_series.rebuild_derived_state

    def counted_rebuild(*args, **kwargs):
        rebuilds.append(kwargs.get("clock"))
        return real_rebuild(*args, **kwargs)

    monkeypatch.setattr(goal_series, "rebuild_derived_state", counted_rebuild)

    series = goal_report_series(
        vault, repository, goal, clock=FrozenClock(NOW + timedelta(days=30))
    )

    # Checkpoints at days 0, 7, 14, 21, 28 (+ the live point at day 30). The
    # attempt lands on day 8, so days 0-7 share one replay and days 14-28 another.
    assert len(series) == 6
    assert len(rebuilds) == 2
    # The shared replay still reports per checkpoint: evidence appears on day 14,
    # and decay keeps moving between checkpoints inside a group.
    assert [point.examined_count for point in series[:5]] == [0, 0, 1, 1, 1]
    assert series[2].predicted_recall_mean != series[3].predicted_recall_mean


def test_series_caps_points_and_keeps_recent_window(tmp_path):
    vault, repository = _loaded(tmp_path)
    goal = vault.goals[0]

    series = goal_report_series(
        vault,
        repository,
        goal,
        clock=FrozenClock(NOW + timedelta(days=365)),
        interval_days=7,
        max_points=6,
    )

    assert len(series) == 6
    assert series[-1].at == (NOW + timedelta(days=365)).astimezone(series[-1].at.tzinfo)


def test_series_replays_past_an_adjudicated_attempt(tmp_path):
    """Append-only ledgers must stay outside the FK walk that truncates scratch copies."""

    vault, repository = _loaded(tmp_path)
    attempt_at = NOW + timedelta(days=8)
    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM_ID,
            learner_answer_md="SVD factorizes into U Sigma V^T.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(attempt_at),
    )
    repository.record_false_remediation(
        attempt_id=attempt.attempt_id,
        value=False,
        evidence_refs=[{"table": "practice_attempts", "id": attempt.attempt_id}],
        author_kind="human",
        verifier_version="test-v1",
    )

    series = goal_report_series(
        vault, repository, vault.goals[0], clock=FrozenClock(NOW + timedelta(days=10))
    )

    assert series[0].on_track_count == 0
    with repository.connection() as connection:
        adjudications = connection.execute(
            "SELECT COUNT(*) FROM false_remediation_adjudications"
        ).fetchone()[0]
    assert adjudications == 1
