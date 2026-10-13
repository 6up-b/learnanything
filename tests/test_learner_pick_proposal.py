"""S0: a picked proposal is served through the plan's learner pick and leaves its usage verdict."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.db.stores.practice_index import insert_proposal
from learnloop.practice_index.usage import USAGE_TASK
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.helpers import create_daily_plan_vault
from tests.source_service_fakes import set_config

DAY1 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: DAY1)
    paths = create_daily_plan_vault(tmp_path / "vault",
                                    learning_objects={"lo_extra": [("pi_extra_1", 2.0), ("pi_extra_2", 2.0)]})
    context = SidecarContext()
    context.load(paths.root)
    context.grading_provider_override = "manual"
    _vault, repository = context.require_vault()
    with repository.connection() as connection:
        insert_proposal(connection, id="pp_test", created_at="2026-10-12T08:59:00Z", origin="rpc",
                        query_id="q", query_text="extra practice", constraints={}, path="direct",
                        path_reason="test", signals={}, reranked=False, rerank_status="disabled",
                        rerank_model=None,
                        proposed=[{"practice_item_id": "pi_extra_1", "rank": 1, "relevance": None,
                                   "kind": "item", "rationale": "fits"}],
                        exclusions={}, manifest={}, algorithm_version="mvp-0.14",
                        caller="tutor", caller_ref="qe_1", intent="practice")
    return context, paths


def _usage(repository):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT verdict, left_id, right_id, judge FROM judgment_ledger WHERE task=?", (USAGE_TASK,))]


def test_a_pick_with_a_proposal_records_practised_and_serves_through_the_plan(ctx):
    context, _paths = ctx
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]
    result = _call(context, "plan_learner_pick", {"practiceItemId": "pi_extra_1", "sessionId": session_id,
                                                   "proposalId": "pp_test"})
    assert result["enabled"] is True and result["step"]["practiceItemId"] == "pi_extra_1"
    assert result["proposalPick"]["signal"] == "practised"
    _vault, repository = context.require_vault()
    assert _usage(repository) == [{"verdict": "practised", "left_id": "pp_test", "right_id": "pi_extra_1",
                                   "judge": "learner_card"}]
    # Picking again is idempotent.
    _call(context, "plan_learner_pick", {"practiceItemId": "pi_extra_1", "sessionId": session_id,
                                         "proposalId": "pp_test"})
    assert len(_usage(repository)) == 1


def test_without_a_proposal_the_pick_is_unchanged(ctx):
    context, _paths = ctx
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]
    result = _call(context, "plan_learner_pick", {"practiceItemId": "pi_extra_2", "sessionId": session_id})
    assert result["enabled"] is True and "proposalPick" not in result
    _vault, repository = context.require_vault()
    assert _usage(repository) == []


def test_a_proposal_that_did_not_propose_the_item_is_refused(ctx):
    context, _paths = ctx
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]
    with pytest.raises(SidecarError):
        _call(context, "plan_learner_pick", {"practiceItemId": "pi_extra_2", "sessionId": session_id,
                                             "proposalId": "pp_test"})


def test_with_the_plan_off_the_pick_is_still_recorded(ctx):
    context, paths = ctx
    set_config(paths, "plan", enabled=False)
    context.load(paths.root)
    result = _call(context, "plan_learner_pick", {"practiceItemId": "pi_extra_1", "proposalId": "pp_test"})
    assert result["enabled"] is False and result["proposalPick"]["signal"] == "practised"


def test_not_what_i_asked_keeps_the_learner_text(ctx):
    context, _paths = ctx
    _call(context, "record_practice_usage", {"proposalId": "pp_test", "practiceItemId": "pi_extra_1",
                                             "signal": "not_what_i_asked",
                                             "text": "I wanted a proof, not a computation"})
    _vault, repository = context.require_vault()
    with repository.connection() as connection:
        rationale = connection.execute(
            "SELECT rationale FROM judgment_ledger WHERE task=? AND verdict='not_what_i_asked'",
            (USAGE_TASK,)).fetchone()[0]
    assert "I wanted a proof, not a computation" in rationale


# -- Codex sources-build review F16: selection before serving, delivery after it ----------------


def _interventions(repository):
    from learnloop.db.stores.source_service import interventions

    with repository.connection() as connection:
        return interventions(connection)


def test_a_failed_pick_leaves_no_delivered_intervention(ctx, monkeypatch):
    from learnloop_sidecar.handlers import daily_plan as handler

    context, _paths = ctx
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]

    def broken(*_args, **_kwargs):
        raise RuntimeError("serving failed")

    monkeypatch.setattr(handler, "learner_pick", broken)
    with pytest.raises(RuntimeError):
        _call(context, "plan_learner_pick", {"practiceItemId": "pi_extra_1", "sessionId": session_id,
                                             "proposalId": "pp_test"})
    _vault, repository = context.require_vault()
    assert _interventions(repository) == []
    # The learner's selection is kept apart from delivery.
    assert len(_usage(repository)) == 1


def _without_r1_logging(context, paths):
    """Router R1 (merged on main) logs every plan block decision by default;
    these tests hold it off to isolate the delivery's own contract."""

    set_config(paths, "router", log_decisions=False)
    context.load(paths.root)
    context.grading_provider_override = "manual"


def test_the_delivery_carries_r1s_decision_of_the_block_that_served_it(ctx):
    """With router R1 merged, the block that serves the pick has R1's
    ``plan_block`` row as its ``decision_ref``; the delivery names that row."""

    context, _paths = ctx
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]
    result = _call(context, "plan_learner_pick", {"practiceItemId": "pi_extra_1", "sessionId": session_id,
                                                   "proposalId": "pp_test"})
    _vault, repository = context.require_vault()
    [row] = _interventions(repository)
    with repository.connection() as connection:
        logged = connection.execute("SELECT decision_kind FROM router_decisions WHERE id=?",
                                    (row["router_decision_id"],)).fetchone()
    assert logged is not None and logged["decision_kind"] == "plan_block"
    assert result["proposalPick"]["routerDecisionId"] == row["router_decision_id"]


def test_the_delivery_carries_the_exact_decision_of_the_block_that_served_it(ctx):
    from learnloop.daily_plan.engine import register_plan_decision_logger, unregister_plan_decision_logger

    context, paths = ctx
    _without_r1_logging(context, paths)
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]
    written: list[str] = []

    def logger(_connection, decision):
        written.append(f"rd_{decision.block_id}")
        return written[-1]

    register_plan_decision_logger(logger)
    try:
        result = _call(context, "plan_learner_pick", {"practiceItemId": "pi_extra_1", "sessionId": session_id,
                                                       "proposalId": "pp_test"})
    finally:
        unregister_plan_decision_logger(logger)
    _vault, repository = context.require_vault()
    [row] = _interventions(repository)
    assert row["router_decision_id"] == f"rd_{result['step']['blockId']}" and row["router_decision_id"] in written
    assert result["proposalPick"]["routerDecisionId"] == row["router_decision_id"]


def test_without_a_logged_decision_none_is_recorded(ctx):
    context, paths = ctx
    _without_r1_logging(context, paths)
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]
    _call(context, "plan_learner_pick", {"practiceItemId": "pi_extra_1", "sessionId": session_id,
                                         "proposalId": "pp_test"})
    _vault, repository = context.require_vault()
    [row] = _interventions(repository)
    assert row["router_decision_id"] is None and row["kind"] == "practice_pick"


def _exercise_proposal(repository, *, status="written", item="pi_extra_2"):
    from learnloop.db.stores.source_service import insert_import

    entry = {"kind": "source_exercise", "key": "srcex:ext_text:t9", "extraction_id": "ext_text", "span_ids": ["t9"],
             "source_id": "src_text", "revision_id": "rev_text", "label": "Exercise 1", "rank": 1,
             "statement": "Solve 3x + 5 = 20.", "relevance": "relevant", "rationale": "fits"}
    with repository.connection() as connection:
        insert_proposal(connection, id="pp_ex", created_at="2026-10-12T08:59:00Z", origin="rpc",
                        query_id="q", query_text="extra practice", constraints={}, path="direct",
                        path_reason="test", signals={}, reranked=True, rerank_status="reranked",
                        rerank_model=None, proposed=[entry], exclusions={}, manifest={},
                        algorithm_version="mvp-0.14", caller="tutor", caller_ref="qe_1", intent="practice")
        insert_import(connection, id="sei_test", created_at="2026-10-12T09:00:00Z", caller="learner",
                      extraction_id="ext_text", span_ids=["t9"], status=status, proposal_id="pp_ex",
                      source_id="src_text", revision_id="rev_text", label="Exercise 1")
        if status == "written":
            connection.execute("UPDATE source_exercise_imports SET practice_item_id=? WHERE id='sei_test'", (item,))
        connection.commit()


def test_an_imported_exercise_is_delivered_when_its_item_is_served(ctx):
    context, _paths = ctx
    _vault, repository = context.require_vault()
    _exercise_proposal(repository)
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]
    result = _call(context, "plan_learner_pick", {"practiceItemId": "pi_extra_2", "sessionId": session_id,
                                                   "proposalId": "pp_ex", "sourceExerciseImportId": "sei_test"})
    assert result["step"]["practiceItemId"] == "pi_extra_2"
    [row] = _interventions(repository)
    assert row["kind"] == "source_exercise" and row["assets"]["import_id"] == "sei_test"
    assert row["assets"]["practice_item_ids"] == ["pi_extra_2"] and row["assets"]["exercise_key"] == "srcex:ext_text:t9"


@pytest.mark.parametrize("status", ["authoring", "rejected"])
def test_an_import_that_has_not_written_the_item_is_refused_before_serving(ctx, status):
    context, _paths = ctx
    _vault, repository = context.require_vault()
    _exercise_proposal(repository, status=status)
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]
    with pytest.raises(SidecarError):
        _call(context, "plan_learner_pick", {"practiceItemId": "pi_extra_2", "sessionId": session_id,
                                             "proposalId": "pp_ex", "sourceExerciseImportId": "sei_test"})
    assert _interventions(repository) == []


@pytest.mark.parametrize("kind", ["item", "imported_exercise"])
def test_with_the_plan_off_delivery_is_recorded_when_the_item_is_opened(ctx, kind):
    """Codex re-review F10: with the plan off, clicking a proposal recorded
    S5's delivery at once, although the item is served only when the learner
    opens it from the open list. The pick records the selection; the open
    (``get_practice_item`` with the proposal identity) records the delivery,
    once however often the item is loaded."""

    context, paths = ctx
    set_config(paths, "plan", enabled=False)
    context.load(paths.root)
    _vault, repository = context.require_vault()
    pick = {"practiceItemId": "pi_extra_1", "proposalId": "pp_test"}
    if kind == "imported_exercise":
        _exercise_proposal(repository)
        pick = {"practiceItemId": "pi_extra_2", "proposalId": "pp_ex", "sourceExerciseImportId": "sei_test"}
    result = _call(context, "plan_learner_pick", pick)
    assert result["enabled"] is False and result["proposalPick"]["delivery"] == "on_open"
    assert _interventions(repository) == []  # selected, not delivered: the learner may never open it
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]
    opened = _call(context, "get_practice_item", {**pick, "sessionId": session_id})
    assert opened["proposalDelivery"]["interventionId"]
    _call(context, "get_practice_item", {**pick, "sessionId": session_id})  # reloaded: still one delivery
    [row] = _interventions(repository)
    assert row["kind"] == ("practice_pick" if kind == "item" else "source_exercise")
    assert row["session_id"] == session_id


def _reserve_for_an_exam(repository, item_id):
    repository.insert_exam_pool_items([{"id": "epi_test", "goal_id": "goal_exam", "practice_item_id": item_id,
                                        "facet_id": None, "difficulty_stratum": "mid",
                                        "reserved_at": "2026-10-12T09:00:00Z", "released_at": None}])


def test_a_pick_of_an_item_reserved_for_an_exam_since_its_proposal_is_refused_before_serving(ctx):
    """Exam protection (2026-10-13, gap c): the plan's pick re-checks the exam
    reservation, so nothing is recorded or served."""

    context, _paths = ctx
    _vault, repository = context.require_vault()
    _reserve_for_an_exam(repository, "pi_extra_1")
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]
    with pytest.raises(SidecarError, match="reserved for a held-out exam"):
        _call(context, "plan_learner_pick", {"practiceItemId": "pi_extra_1", "sessionId": session_id,
                                             "proposalId": "pp_test"})
    assert _usage(repository) == []


def test_the_open_list_refuses_an_item_reserved_for_an_exam_after_its_pick(ctx):
    """With the plan off the pick is recorded first; the open-list serve re-checks
    the reservation BEFORE the item is served and records no delivery."""

    context, paths = ctx
    set_config(paths, "plan", enabled=False)
    context.load(paths.root)
    _vault, repository = context.require_vault()
    pick = {"practiceItemId": "pi_extra_1", "proposalId": "pp_test"}
    assert _call(context, "plan_learner_pick", pick)["proposalPick"]["delivery"] == "on_open"
    _reserve_for_an_exam(repository, "pi_extra_1")
    session_id = _call(context, "start_session", {"availableMinutes": 25})["sessionId"]
    with pytest.raises(SidecarError, match="reserved for a held-out exam"):
        _call(context, "get_practice_item", {**pick, "sessionId": session_id})
    assert _interventions(repository) == []
