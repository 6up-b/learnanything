"""FG1c landing, R1: a recorded exposure of a workflow's causes before its probe's answer makes that answer
not independent, whatever surface showed them and whether or not feedback was held. Codex's verify job
20261104-110826-NW4UVh is the first test."""

from __future__ import annotations

from datetime import timedelta
import json
import logging

import pytest

from learnloop.db.stores import hypothesis_marks as store
from learnloop.followup_run import marks as panel
from learnloop.followup_run.serving import is_holding
from learnloop.followup_serve import workflow as wf
from learnloop.substrate.replay import rebuild_derived_state
from learnloop_sidecar.context import SidecarContext

from tests.followup_serve_helpers import CLOCK, miss_with_rivals, rival_causes_vault
from tests.helpers import append_config_toml
from tests.followup_journey_helpers import _Runtime, _answer, _call, _generate, journey  # noqa: F401 - the fixture
from tests.hypothesis_marks_helpers import MARKS_OFF, _rows

NOON = "2026-07-01T12:00:00Z"
TWO = "2026-07-01T14:00:00Z"
THREE = "2026-07-01T15:00:00Z"


def _before_the_answer(hours: float = 2.0) -> str:
    """A display event's stamp, as the client writes it, before ``_answer``'s frozen clock."""

    return (CLOCK.now() - timedelta(hours=hours)).isoformat().replace("+00:00", "Z")


def _exam_origin(repository, outcome):
    """As ``run_exam_sitting_pipeline`` opens one: nothing held."""

    with repository.connection() as connection:
        connection.execute("UPDATE followup_workflows SET origin = 'exam', feedback_held = 0 WHERE id = ?",
                           (outcome.workflow_id,))
    row = wf.get(repository, outcome.workflow_id)
    assert row["origin"] == "exam" and not is_holding(row)
    return row


def _insert(repository, row, *, shown_at, attempt_id=None, factor_id="same", surface="why"):
    with repository.atomic(), repository.connection() as connection:
        written = store.insert_exposure(connection, {
            "attempt_id": attempt_id or row["source_attempt_id"],
            "factor_id": row["factor_id"] if factor_id == "same" else factor_id,
            "workflow_id": row["id"],
            "surface": surface,
            "hypothesis_version_ids_json": json.dumps(["h1"]),
            "probe_answered": 0,
            "shown_at": shown_at,
            "created_at": shown_at,
        })
    assert written


def _ready(ctx, repository, outcome):
    _generate(ctx, repository)
    row = wf.get(repository, outcome.workflow_id)
    assert row["presentation_id"], row
    return row


def _open_and_answer(ctx, repository, row):
    _call(ctx, "followup_status", {"attemptId": row["source_attempt_id"]})  # this process's vault reads the new item
    _call(ctx, "open_queue_item", {"practiceItemId": row["practice_item_id"]})
    _call(ctx, "get_probe_contract", {"practiceItemId": row["practice_item_id"]})
    _answer(ctx, repository, row, points={"fact_0": 0, "fact_1": 2})
    return repository.causal_discriminating_observations(factor_id=row["factor_id"])[0]


def _versions(repository, attempt_id):
    return [str(value["id"]) for value in repository.causal_hypotheses_for_attempt(attempt_id)]


# -- Codex's reproduction ---------------------------------------------------------------------------


def test_codexs_reproduction_an_exam_origin_exposure_at_noon_and_an_answer_at_two(journey):
    ctx, _vault, repository, _result, outcome = journey
    _exam_origin(repository, outcome)
    row = _ready(ctx, repository, outcome)
    assert not row["shown_anyway_at"] and not row["exposed_at"]
    _insert(repository, row, shown_at=NOON)
    assert wf.probe_answer_exposed(repository, row["presentation_id"], answered_at=TWO) == wf.CAUSES_SHOWN_BEFORE_PROBE


def test_through_the_doors_the_answers_observation_is_not_independent_and_closes_nothing(journey):
    ctx, _vault, repository, result, outcome = journey
    _exam_origin(repository, outcome)
    row = _ready(ctx, repository, outcome)
    reply = _call(ctx, "record_hypothesis_exposure", {
        "attemptId": result.attempt_id, "surface": "marks_feedback",
        "hypothesisVersionIds": _versions(repository, result.attempt_id)[:2], "shownAt": _before_the_answer(),
    })
    assert reply["recorded"] is True
    observation = _open_and_answer(ctx, repository, row)
    assert observation["admissible_as_independent"] == 0 and not observation["admitted"]
    assert observation["admission_reason"] == wf.CAUSES_SHOWN_BEFORE_PROBE
    assert repository.unresolved_cause_factor(row["factor_id"])["status"] == "open"


def test_with_no_exposure_the_same_answer_stays_independent(journey):
    ctx, _vault, repository, _result, outcome = journey
    _exam_origin(repository, outcome)
    observation = _open_and_answer(ctx, repository, _ready(ctx, repository, outcome))
    assert observation["admissible_as_independent"] == 1 and observation["admitted"]


# -- what counts ------------------------------------------------------------------------------------


def test_an_exposure_after_the_answer_leaves_it_independent(journey):
    ctx, _vault, repository, _result, outcome = journey
    row = _ready(ctx, repository, outcome)
    _insert(repository, row, shown_at=THREE)
    assert wf.probe_answer_exposed(repository, row["presentation_id"], answered_at=TWO) is None
    # Two offsets, one instant: a time is compared as a time, never as text.
    _insert(repository, row, shown_at="2026-07-01T15:30:00+02:00")
    assert wf.probe_answer_exposed(repository, row["presentation_id"], answered_at=TWO) == wf.CAUSES_SHOWN_BEFORE_PROBE


def test_the_panel_on_the_answers_own_feedback_doesnt_relabel_the_answer(journey):
    ctx, _vault, repository, result, outcome = journey
    row = _ready(ctx, repository, outcome)
    observation = _open_and_answer(ctx, repository, row)
    assert observation["admissible_as_independent"] == 1
    later = (CLOCK.now() + timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
    assert _call(ctx, "record_hypothesis_exposure", {
        "attemptId": result.attempt_id, "surface": "marks_probe_feedback",
        "hypothesisVersionIds": _versions(repository, result.attempt_id)[:2], "shownAt": later,
    })["recorded"] is True
    answered = str(repository.fetch_practice_attempt(observation["probe_attempt_id"])["created_at"])
    assert wf.probe_answer_exposed(repository, row["presentation_id"], answered_at=answered) is None
    vault, _ = ctx.require_vault()
    rebuild_derived_state(vault, repository)
    assert repository.causal_discriminating_observations(factor_id=row["factor_id"])[0]["admissible_as_independent"] == 1


def test_an_exposure_on_another_attempts_factor_leaves_it_independent(journey):
    ctx, _vault, repository, _result, outcome = journey
    row = _ready(ctx, repository, outcome)
    _insert(repository, row, shown_at=NOON, attempt_id="att_someone_else", factor_id="factor_someone_else")
    _insert(repository, row, shown_at=NOON, attempt_id="att_no_factor", factor_id=None)
    assert wf.probe_answer_exposed(repository, row["presentation_id"], answered_at=TWO) is None


@pytest.mark.parametrize("attempt, factor", [("own", None), ("own", "factor_of_a_later_revision"), ("other", "same")])
def test_the_workflows_attempt_or_its_factor_is_enough(journey, attempt, factor):
    """A list shown before the factor opened carries no factor; its causes are still this attempt's."""

    ctx, _vault, repository, _result, outcome = journey
    row = _ready(ctx, repository, outcome)
    _insert(repository, row, shown_at=NOON, factor_id=factor,
            attempt_id=None if attempt == "own" else "att_sharing_the_factor")
    assert wf.probe_answer_exposed(repository, row["presentation_id"], answered_at=TWO) == wf.CAUSES_SHOWN_BEFORE_PROBE


def test_an_exposure_while_held_is_recorded_and_counts(journey):
    ctx, _vault, repository, result, outcome = journey
    row = _ready(ctx, repository, outcome)
    assert is_holding(row)
    reply = _call(ctx, "record_hypothesis_exposure", {
        "attemptId": result.attempt_id, "surface": "why",
        "hypothesisVersionIds": _versions(repository, result.attempt_id)[:1], "shownAt": _before_the_answer(),
    })
    assert reply["recorded"] is True
    written = _rows(repository, "hypothesis_list_exposures")
    assert len(written) == 1 and written[0]["probe_answered"] == 0
    # Marks stay refused while held, and the bundle still carries no panel.
    assert "hypothesisMarks" not in _call(ctx, "get_feedback", {"attemptId": result.attempt_id})
    observation = _open_and_answer(ctx, repository, row)
    assert observation["admissible_as_independent"] == 0 and observation["admission_reason"] == wf.CAUSES_SHOWN_BEFORE_PROBE


@pytest.mark.parametrize("surface", sorted(panel.EXPOSURE_SURFACES))
def test_every_surface_that_sends_a_display_event_reaches_it(journey, surface):
    ctx, _vault, repository, result, outcome = journey
    _exam_origin(repository, outcome)
    row = _ready(ctx, repository, outcome)
    assert _call(ctx, "record_hypothesis_exposure", {
        "attemptId": result.attempt_id, "surface": surface,
        "hypothesisVersionIds": _versions(repository, result.attempt_id)[:1], "shownAt": _before_the_answer(),
    })["recorded"] is True
    observation = _open_and_answer(ctx, repository, row)
    assert observation["admissible_as_independent"] == 0, surface


def test_a_display_event_with_a_bad_time_is_recorded_at_the_servers(journey):
    ctx, _vault, repository, result, outcome = journey
    _exam_origin(repository, outcome)
    _ready(ctx, repository, outcome)
    assert _call(ctx, "record_hypothesis_exposure", {
        "attemptId": result.attempt_id, "surface": "why",
        "hypothesisVersionIds": _versions(repository, result.attempt_id)[:1], "shownAt": "not a time",
    })["recorded"] is True
    assert _rows(repository, "hypothesis_list_exposures")[0]["shown_at"] != "not a time"


@pytest.mark.parametrize("shown, answered", [("not a time", TWO), (NOON, "not a time"), (NOON, None)])
def test_a_time_that_cant_be_placed_counts_as_before(journey, shown, answered):
    ctx, _vault, repository, _result, outcome = journey
    row = _ready(ctx, repository, outcome)
    _insert(repository, row, shown_at=shown)
    assert wf.probe_answer_exposed(repository, row["presentation_id"], answered_at=answered) == wf.CAUSES_SHOWN_BEFORE_PROBE


# -- an exposure read never fails an answer ---------------------------------------------------------


def test_an_unreadable_table_is_not_independent_and_raises_nothing(journey, caplog):
    ctx, _vault, repository, _result, outcome = journey
    row = _ready(ctx, repository, outcome)
    with repository.connection() as connection:
        connection.execute("ALTER TABLE hypothesis_list_exposures RENAME COLUMN factor_id TO renamed_away")
    with caplog.at_level(logging.WARNING):
        reason = wf.probe_answer_exposed(repository, row["presentation_id"], answered_at=TWO)
    assert reason == wf.CAUSE_EXPOSURES_UNREADABLE and "could not be read" in caplog.text


def test_an_unreadable_table_doesnt_cost_the_answer(journey):
    ctx, _vault, repository, _result, outcome = journey
    row = _ready(ctx, repository, outcome)
    with repository.connection() as connection:
        connection.execute("ALTER TABLE hypothesis_list_exposures RENAME COLUMN factor_id TO renamed_away")
    observation = _open_and_answer(ctx, repository, row)
    assert observation["admissible_as_independent"] == 0
    assert observation["admission_reason"] == wf.CAUSE_EXPOSURES_UNREADABLE


# -- labels stand, and the rebuild keeps it -----------------------------------------------------------


def test_fg1s_two_labels_still_come_first(journey):
    ctx, _vault, repository, result, outcome = journey
    row = _ready(ctx, repository, outcome)
    _insert(repository, row, shown_at=NOON)
    _call(ctx, "followup_show_anyway", {"attemptId": result.attempt_id})
    assert wf.probe_answer_exposed(repository, row["presentation_id"], answered_at=TWO) == "followup_feedback_shown_anyway"


def test_a_rebuild_keeps_the_answer_not_independent(journey):
    ctx, _vault, repository, result, outcome = journey
    _exam_origin(repository, outcome)
    row = _ready(ctx, repository, outcome)
    _call(ctx, "record_hypothesis_exposure", {
        "attemptId": result.attempt_id, "surface": "why",
        "hypothesisVersionIds": _versions(repository, result.attempt_id)[:1], "shownAt": _before_the_answer(),
    })
    assert _open_and_answer(ctx, repository, row)["admissible_as_independent"] == 0
    vault, _ = ctx.require_vault()
    rebuild_derived_state(vault, repository)
    observation = repository.causal_discriminating_observations(factor_id=row["factor_id"])[0]
    assert observation["admissible_as_independent"] == 0 and len(_rows(repository, "hypothesis_list_exposures")) == 1


# -- marks off ---------------------------------------------------------------------------------------


@pytest.fixture
def marks_off(tmp_path, monkeypatch):
    monkeypatch.setattr("learnloop_sidecar.handlers.practice.ready_grading_provider",
                        lambda *_args, **_kw: ("fake", _Runtime(), object()))
    vault, repository, paths = rival_causes_vault(tmp_path, config=MARKS_OFF)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    vault, repository = ctx.require_vault()
    result, outcome = miss_with_rivals(vault, repository)
    return ctx, vault, repository, result, outcome


def test_with_marks_off_show_anyways_flag_still_protects_the_answer(marks_off):
    ctx, _vault, repository, result, outcome = marks_off
    row = _ready(ctx, repository, outcome)
    _call(ctx, "followup_show_anyway", {"attemptId": result.attempt_id})
    assert _call(ctx, "record_hypothesis_exposure", {
        "attemptId": result.attempt_id, "surface": "why",
        "hypothesisVersionIds": _versions(repository, result.attempt_id)[:1], "shownAt": _before_the_answer(),
    })["recorded"] is False
    assert _rows(repository, "hypothesis_list_exposures") == []
    observation = _open_and_answer(ctx, repository, row)
    assert observation["admissible_as_independent"] == 0
    assert observation["admission_reason"] == "followup_feedback_shown_anyway"


def test_an_exposure_recorded_before_marks_went_off_still_counts(journey):
    ctx, _vault, repository, _result, outcome = journey
    row = _ready(ctx, repository, outcome)
    _insert(repository, row, shown_at=NOON)
    append_config_toml(ctx.vault_root, MARKS_OFF)
    ctx.reload(maintenance=False)
    assert wf.probe_answer_exposed(repository, row["presentation_id"], answered_at=TWO) == wf.CAUSES_SHOWN_BEFORE_PROBE


# -- the doors that showed causes with no display event ------------------------------------------------


def _not_showing(bundle):
    assert bundle["causalFeedback"] is None and bundle["unresolvedCauses"] == [] and bundle["feedbackMd"] is None
    assert bundle["followup"]["held"] is True


@pytest.mark.parametrize("name, params", [
    ("add_error_event", {"errorType": "x", "severity": 0.5}),
    ("rate_followup", {"useful": True}),
    ("trigger_followup", {}),
    ("trigger_regrade", {"learnerReason": "My answer was right.", "contestId": "contest-1"}),
])
def test_a_door_on_a_held_screen_keeps_the_causes_held(journey, name, params):
    ctx, _vault, repository, result, outcome = journey
    _not_showing(_call(ctx, name, {"attemptId": result.attempt_id, **params}))
    assert is_holding(wf.get(repository, outcome.workflow_id))


def test_a_plain_regrade_on_a_held_screen_keeps_the_causes_held(journey, monkeypatch):
    ctx, _vault, _repository, result, _outcome = journey
    monkeypatch.setattr("learnloop_sidecar.handlers.feedback._run_regrade", lambda *_args, **_kw: None)
    _not_showing(_call(ctx, "trigger_regrade", {"attemptId": result.attempt_id}))


def test_the_same_door_with_nothing_held_returns_the_whole_bundle(journey):
    ctx, _vault, repository, result, outcome = journey
    _call(ctx, "followup_show_anyway", {"attemptId": result.attempt_id})
    assert not is_holding(wf.get(repository, outcome.workflow_id))
    bundle = _call(ctx, "add_error_event", {"attemptId": result.attempt_id, "errorType": "x", "severity": 0.5})
    assert bundle["feedbackMd"] and "followup" not in bundle


def test_every_door_of_the_handler_goes_through_the_hold():
    """Only ``get_feedback`` composes the hold itself, and ``_door_bundle`` is the one other reader."""

    import inspect

    from learnloop_sidecar.handlers import feedback

    assert inspect.getsource(feedback).count("feedback_bundle(vault, repository,") == 2


@pytest.mark.parametrize("kind", ["attempt", "error_event"])
def test_the_inspector_on_a_held_attempt_is_a_recorded_exposure(journey, kind):
    ctx, _vault, repository, result, outcome = journey
    row = _ready(ctx, repository, outcome)
    target = result.attempt_id
    if kind == "error_event":
        _call(ctx, "add_error_event", {"attemptId": result.attempt_id, "errorType": "x", "severity": 0.5})
        with repository.connection() as connection:
            target = connection.execute("SELECT id FROM error_events WHERE attempt_id = ? LIMIT 1", (result.attempt_id,)).fetchone()[0]
    assert _call(ctx, "inspect_entity", {"id": target})["kind"] == kind
    written = _rows(repository, "hypothesis_list_exposures")
    assert [value["surface"] for value in written] == ["inspector"]
    assert sorted(json.loads(written[0]["hypothesis_version_ids_json"])) == sorted(set(_versions(repository, result.attempt_id)))
    later = (CLOCK.now() + timedelta(days=3650)).isoformat()
    assert wf.probe_answer_exposed(repository, row["presentation_id"], answered_at=later) == wf.CAUSES_SHOWN_BEFORE_PROBE


def test_the_inspector_with_marks_off_writes_nothing(marks_off):
    ctx, _vault, repository, result, _outcome = marks_off
    assert _call(ctx, "inspect_entity", {"id": result.attempt_id})["kind"] == "attempt"
    assert _rows(repository, "hypothesis_list_exposures") == []
