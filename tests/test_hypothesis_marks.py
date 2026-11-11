"""FG1c, spec §7: the learner's marks on possible causes, and the hypothesis-list exposure receipt
(spec_router_objective_v1 §4 row 6), through the sidecar's doors, models faked."""

from __future__ import annotations

from contextlib import closing
from datetime import timedelta
import json
import sqlite3

import pytest

from learnloop.db.stores import hypothesis_marks as store
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from learnloop.followup_run import marks as panel
from learnloop.followup_serve import marks as M
from learnloop.followup_serve import workflow as wf
from learnloop.substrate.replay import rebuild_derived_state
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError

from tests.followup_serve_helpers import (
    CLOCK,
    AuthorFake,
    BlindRivalClient,
    author_clients,
    live_miss,
    live_shape_vault,
    miss_with_rivals,
    rival_causes_vault,
    run_jobs,
)
from tests.followup_journey_helpers import _Runtime, _answer, _bundle_without_ids, _call, _forced, _generate, journey  # noqa: F401 - the fixture
from tests.hypothesis_marks_helpers import MARKS_OFF, _mark, _released, _rows, _serve_and_answer

LEDGERS = frozenset({"hypothesis_list_exposures", "hypothesis_exposure_probe_links", "hypothesis_marks"})


def _served_and_answered(ctx, repository, attempt_id, outcome, *, points=None):
    _generate(ctx, repository)
    return _serve_and_answer(ctx, repository, attempt_id, outcome, points=points)


def _dump(paths, *, without=LEDGERS):
    """Every row of every table, for the whole-database comparison."""

    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        return {table: connection.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall()
                for table in tables if table not in without}


# -- timing: §6.0, as FG1 built it ------------------------------------------------------------------


def test_while_held_there_is_no_list_and_nothing_can_be_marked_but_a_display_event_is_recorded(journey):
    ctx, _vault, repository, result, _outcome = journey
    assert "hypothesisMarks" not in _call(ctx, "get_feedback", {"attemptId": result.attempt_id})
    with pytest.raises(SidecarError) as caught:
        _mark(ctx, result.attempt_id, "none_of_these")
    assert caught.value.code == "validation_error" and "held" in str(caught.value)
    version = repository.causal_hypotheses_for_attempt(result.attempt_id)[0]["id"]
    reply = _call(ctx, "record_hypothesis_exposure", {"attemptId": result.attempt_id, "surface": "why",
                                                      "hypothesisVersionIds": [version]})
    # R1: what the screen says it showed is recorded, and it's what labels the probe's answer.
    assert reply["recorded"] is True
    assert len(_rows(repository, "hypothesis_list_exposures")) == 1 and _rows(repository, "hypothesis_marks") == []


def test_after_the_probe_is_answered_its_feedback_shows_the_misss_list(journey):
    ctx, _vault, repository, result, outcome = journey
    probe, _row = _served_and_answered(ctx, repository, result.attempt_id, outcome)
    bundle = _call(ctx, "get_feedback", {"attemptId": probe.attempt_id})
    marks = bundle["hypothesisMarks"]
    assert marks["attemptId"] == result.attempt_id and marks["surface"] == "marks_probe_feedback"
    assert marks["probeAnswered"] is True and len(marks["hypotheses"]) == 2
    assert all(row["mark"] is None and row["statement"] for row in marks["hypotheses"])
    # The miss's own screen shows the same list, in the same order.
    again = _call(ctx, "get_feedback", {"attemptId": result.attempt_id})["hypothesisMarks"]
    assert again["surface"] == "marks_feedback" and again["replacesCardTap"] is True
    assert [row["hypothesisVersionId"] for row in again["hypotheses"]] == [row["hypothesisVersionId"] for row in marks["hypotheses"]]


def test_with_no_probe_the_list_is_on_the_feedback_screen(journey, monkeypatch):
    ctx, _vault, repository, result, outcome = journey
    _forced(monkeypatch, "no_intervention")
    _generate(ctx, repository)
    assert wf.get(repository, outcome.workflow_id)["feedback_released_at"]
    marks = _call(ctx, "get_feedback", {"attemptId": result.attempt_id})["hypothesisMarks"]
    assert marks["probeAnswered"] is False and len(marks["hypotheses"]) == 2


def test_a_practice_lane_miss_keeps_the_cards_tap(tmp_path):
    paths, vault, repository = live_shape_vault(tmp_path, task_features=False)
    client = BlindRivalClient()
    client.causes = 1
    result, outcome = live_miss(vault, repository, client)
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    assert wf.get(repository, outcome.workflow_id)["lane"] == wf.LANE_PRACTICE
    marks = panel.view(vault, repository, result.attempt_id)
    assert marks["replaces_card_tap"] is False and len(marks["hypotheses"]) == 1


def test_show_anyway_shows_the_list_and_still_marks_the_answer_not_independent(journey):
    ctx, _vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    assert marks["probeAnswered"] is False
    _mark(ctx, result.attempt_id, "my_gap", marks["hypotheses"][0]["hypothesisVersionId"])
    _probe, row = _serve_and_answer(ctx, repository, result.attempt_id, outcome)
    observation = repository.causal_discriminating_observations(factor_id=row["factor_id"])[0]
    assert not observation["admitted"] and observation["admissible_as_independent"] == 0
    assert repository.unresolved_cause_factor(row["factor_id"])["status"] == "open"


def test_a_marks_read_that_fails_costs_the_panel_and_not_the_feedback(journey, monkeypatch):
    ctx, _vault, repository, result, outcome = journey
    _released(ctx, repository, outcome, result)
    monkeypatch.setattr(panel, "bundle_view", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("no")))
    bundle = _call(ctx, "get_feedback", {"attemptId": result.attempt_id})
    assert "hypothesisMarks" not in bundle and bundle["feedbackMd"]


def test_marking_never_strands_next(journey):
    ctx, _vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    before = _call(ctx, "followup_next", {"attemptId": result.attempt_id})
    _mark(ctx, result.attempt_id, "not_it", marks["hypotheses"][0]["hypothesisVersionId"])
    assert _call(ctx, "followup_next", {"attemptId": result.attempt_id}) == before
    assert before["action"] == "open"


# -- (1) the exposure receipt ------------------------------------------------------------------------


def test_an_exposure_records_the_order_as_displayed_not_the_servers(journey):
    ctx, _vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    shown = [row["hypothesisVersionId"] for row in marks["hypotheses"]]
    assert _call(ctx, "record_hypothesis_exposure", {
        "attemptId": result.attempt_id, "surface": "unresolved_cause_card", "hypothesisVersionIds": shown[::-1],
        "shownAt": "2026-10-16T12:00:00Z"})["recorded"] is True
    assert _call(ctx, "record_hypothesis_exposure", {
        "attemptId": result.attempt_id, "surface": "marks_feedback", "hypothesisVersionIds": shown})["recorded"] is True
    other, panel_row = _rows(repository, "hypothesis_list_exposures")
    assert json.loads(other["hypothesis_version_ids_json"]) == shown[::-1]
    assert other["surface"] == "unresolved_cause_card" and other["order_seed"] is None
    assert other["factor_id"] == wf.get(repository, outcome.workflow_id)["factor_id"]
    assert other["workflow_id"] == outcome.workflow_id and other["probe_answered"] == 0
    assert other["shown_at"] == "2026-10-16T12:00:00Z"
    assert panel_row["order_seed"] == marks["orderSeed"] and panel_row["order_version"] == M.ORDER_VERSION


def test_a_probe_answered_later_is_a_later_linked_receipt_and_the_row_never_changes(journey):
    ctx, _vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    shown = [row["hypothesisVersionId"] for row in marks["hypotheses"]]
    _call(ctx, "record_hypothesis_exposure", {"attemptId": result.attempt_id, "surface": "marks_feedback",
                                              "hypothesisVersionIds": shown})
    before = _rows(repository, "hypothesis_list_exposures")
    probe, _row = _serve_and_answer(ctx, repository, result.attempt_id, outcome)
    assert _rows(repository, "hypothesis_list_exposures") == before
    links = _rows(repository, "hypothesis_exposure_probe_links")
    assert [(link["exposure_id"], link["probe_attempt_id"]) for link in links] == [(before[0]["id"], probe.attempt_id)]
    # A display after the answer says so itself, and needs no link.
    _call(ctx, "record_hypothesis_exposure", {"attemptId": result.attempt_id, "surface": "marks_feedback",
                                              "hypothesisVersionIds": shown})
    later = _rows(repository, "hypothesis_list_exposures")[-1]
    assert later["probe_answered"] == 1 and later["probe_attempt_id"] == probe.attempt_id
    assert len(_rows(repository, "hypothesis_exposure_probe_links")) == 1


@pytest.mark.parametrize("surface, ids", [
    ("the_moon", None),
    ("why", []),
    ("why", ["not_a_cause"]),
])
def test_a_refused_exposure_writes_nothing_warns_and_answers_quietly(journey, caplog, surface, ids):
    ctx, _vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    shown = [row["hypothesisVersionId"] for row in marks["hypotheses"]] if ids is None else ids
    reply = _call(ctx, "record_hypothesis_exposure", {"attemptId": result.attempt_id, "surface": surface,
                                                      "hypothesisVersionIds": shown})
    assert reply["recorded"] is False and "refused" in caplog.text
    assert _rows(repository, "hypothesis_list_exposures") == []


def test_a_cause_of_another_attempt_is_not_this_attempts_exposure(journey, tmp_path):
    ctx, _vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    reply = _call(ctx, "record_hypothesis_exposure", {"attemptId": "att_other", "surface": "why",
                                                      "hypothesisVersionIds": [marks["hypotheses"][0]["hypothesisVersionId"]]})
    assert reply["recorded"] is False


def test_a_refused_row_rolls_back_alone_and_the_rest_of_the_transaction_stands(journey, caplog):
    _ctx, _vault, repository, result, _outcome = journey
    with repository.atomic(), repository.connection() as connection:
        connection.execute("UPDATE followup_workflows SET updated_at = updated_at || '' WHERE source_attempt_id = ?",
                           (result.attempt_id,))
        written = store.insert_exposure(connection, {"attempt_id": result.attempt_id, "surface": "",
                                                     "hypothesis_version_ids_json": "[]", "probe_answered": 0,
                                                     "shown_at": "t", "created_at": "t"})
        assert written is None
        assert store.insert_exposure(connection, {"attempt_id": result.attempt_id, "surface": "why",
                                                  "hypothesis_version_ids_json": "[]", "probe_answered": 0,
                                                  "shown_at": "t", "created_at": "t"})
    assert len(_rows(repository, "hypothesis_list_exposures")) == 1
    assert "refused" in caplog.text


def test_a_refused_link_never_blocks_the_probes_answer(journey, monkeypatch, caplog):
    ctx, _vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    _call(ctx, "record_hypothesis_exposure", {"attemptId": result.attempt_id, "surface": "marks_feedback",
                                              "hypothesisVersionIds": [row["hypothesisVersionId"] for row in marks["hypotheses"]]})
    with repository.connection() as connection:
        connection.execute("CREATE TRIGGER refuses BEFORE INSERT ON hypothesis_exposure_probe_links "
                           "BEGIN SELECT RAISE(ABORT, 'refused'); END")
        connection.commit()
    _probe, row = _serve_and_answer(ctx, repository, result.attempt_id, outcome)
    assert wf.get(repository, outcome.workflow_id)["state"] == wf.SETTLED
    assert "refused" in caplog.text and _rows(repository, "hypothesis_exposure_probe_links") == []


# -- (2) the raw ledger ------------------------------------------------------------------------------


def test_a_mark_stores_what_the_spec_lists_and_a_change_of_mind_appends(journey):
    ctx, _vault, repository, result, outcome = journey
    probe, row = _served_and_answered(ctx, repository, result.attempt_id, outcome)
    marks = _call(ctx, "get_feedback", {"attemptId": probe.attempt_id})["hypothesisMarks"]
    first, second = (entry["hypothesisVersionId"] for entry in marks["hypotheses"])
    reply = _mark(ctx, result.attempt_id, "my_gap", second, surface="marks_probe_feedback")
    assert [entry["mark"] for entry in reply["marks"]["hypotheses"]] == [None, "my_gap"]
    reply = _mark(ctx, result.attempt_id, "partly", second, surface="marks_probe_feedback")
    assert [entry["mark"] for entry in reply["marks"]["hypotheses"]] == [None, "partly"]
    rows = _rows(repository, "hypothesis_marks")
    assert [entry["mark"] for entry in rows] == ["my_gap", "partly"]
    stored = rows[0]
    assert stored["attempt_id"] == result.attempt_id and stored["factor_id"] == row["factor_id"]
    assert stored["hypothesis_version_id"] == second and stored["display_position"] == 2
    assert json.loads(stored["display_order_json"]) == [first, second]
    assert stored["order_seed"] == marks["orderSeed"] and stored["surface"] == "marks_probe_feedback"
    assert stored["probe_answered"] == 1 and stored["probe_attempt_id"] == probe.attempt_id
    outcome_known = json.loads(stored["probe_outcome_json"])
    assert outcome_known["classification"] == "matched_single" and outcome_known["admitted"] is True
    assert stored["workflow_id"] == outcome.workflow_id and stored["learning_object_id"] == result.learning_object_id


def test_a_mark_before_the_probe_says_no_outcome_is_known(journey):
    ctx, _vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    _mark(ctx, result.attempt_id, "not_it", marks["hypotheses"][0]["hypothesisVersionId"])
    stored = _rows(repository, "hypothesis_marks")[0]
    assert stored["probe_answered"] == 0 and stored["probe_attempt_id"] is None and stored["probe_outcome_json"] is None


def test_a_live_diagnosis_is_stored_by_its_id(tmp_path):
    paths, vault, repository = live_shape_vault(tmp_path, task_features=False)
    result, _outcome = live_miss(vault, repository, BlindRivalClient())
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    wf.set_fields(repository, wf.attempt_workflow(repository, result.attempt_id)["id"], feedback_released_at="2026-10-16T00:00:00Z")
    listed = panel.markable_list(vault, repository, result.attempt_id)
    assert listed.diagnosis_id
    panel.record_mark(vault, repository, attempt_id=result.attempt_id, mark="my_gap",
                      hypothesis_version_id=listed.order[0], clock=CLOCK)
    assert _rows(repository, "hypothesis_marks")[0]["diagnosis_id"] == listed.diagnosis_id


def test_none_of_these_takes_optional_words_and_the_latest_counts(journey):
    ctx, _vault, repository, result, outcome = journey
    _released(ctx, repository, outcome, result)
    reply = _mark(ctx, result.attempt_id, "none_of_these")["marks"]
    assert reply["noneOfThese"] is True and reply["noneOfTheseText"] is None
    reply = _mark(ctx, result.attempt_id, "none_of_these", freeText="  I misread the sign  ")["marks"]
    assert reply["noneOfTheseText"] == "I misread the sign"
    stored = _rows(repository, "hypothesis_marks")
    assert stored[-1]["hypothesis_version_id"] is None and stored[-1]["display_position"] is None
    reply = _mark(ctx, result.attempt_id, "cleared")["marks"]
    assert reply["noneOfThese"] is False and reply["noneOfTheseText"] is None
    assert [entry["mark"] for entry in _rows(repository, "hypothesis_marks")] == ["none_of_these", "none_of_these", "cleared"]


def test_cleared_takes_a_mark_back_by_appending(journey):
    ctx, _vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    version = marks["hypotheses"][1]["hypothesisVersionId"]
    _mark(ctx, result.attempt_id, "my_gap", version)
    reply = _mark(ctx, result.attempt_id, "cleared", version)["marks"]
    assert reply["hypotheses"][1]["mark"] is None and len(_rows(repository, "hypothesis_marks")) == 2


@pytest.mark.parametrize("params", [
    {"mark": "certainly"},
    {"mark": "my_gap"},
    {"mark": "my_gap", "hypothesisVersionId": "not_on_the_list"},
    {"mark": "partly", "freeText": "words only go with None of these", "hypothesisVersionId": "FIRST"},
    {"mark": "none_of_these", "hypothesisVersionId": "FIRST"},
    {"mark": "none_of_these", "surface": "why"},
])
def test_a_mark_that_fits_nothing_is_refused(journey, params):
    ctx, _vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    params = {key: (marks["hypotheses"][0]["hypothesisVersionId"] if value == "FIRST" else value) for key, value in params.items()}
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "record_hypothesis_mark", {"attemptId": result.attempt_id, **params})
    assert caught.value.code == "validation_error"
    assert _rows(repository, "hypothesis_marks") == []


# -- (3) the order -----------------------------------------------------------------------------------


def test_the_order_is_a_logged_seed_over_stable_identities():
    seed, order = M.display_order("att", ["a", "b", "c"])
    assert (seed, order) == M.display_order("att", ["c", "a", "b"])
    # A new cause moves nothing else; a later version of a cause is the same identity, so its place holds.
    assert [key for key in M.display_order("att", ["a", "b", "c", "d"])[1] if key != "d"] == list(order)
    # Over attempts, both orders appear for a pair: position isn't confounded with the diagnoser's order.
    first = {M.display_order(f"att{index}", ["a", "b"])[1][0] for index in range(40)}
    assert first == {"a", "b"}


def test_the_list_keeps_its_order_on_every_read_and_a_new_version_keeps_its_place(journey):
    ctx, vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    assert _call(ctx, "get_feedback", {"attemptId": result.attempt_id})["hypothesisMarks"]["hypotheses"] == marks["hypotheses"]
    listed = panel.markable_list(vault, repository, result.attempt_id)
    keys = [row["key"] for row in listed.hypotheses]
    assert list(M.display_order(result.attempt_id, keys)[1]) == keys
    assert listed.order_seed == marks["orderSeed"]
    assert keys == [str(repository.causal_hypothesis(row["hypothesis_version_id"])["episode_key"]) for row in listed.hypotheses]


# -- (5) what it affects -----------------------------------------------------------------------------


def test_marks_change_no_row_outside_their_own_ledger(journey):
    """Grades, certification, factor state, mastery, the schedule, every self-report and every belief:
    the whole database but the three ledgers, row by row, through every mark there is."""

    ctx, vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    versions = [row["hypothesisVersionId"] for row in marks["hypotheses"]]
    paths = _paths(vault)
    before = _dump(paths)
    _mark(ctx, result.attempt_id, "my_gap", versions[0])
    _mark(ctx, result.attempt_id, "not_it", versions[1])
    _mark(ctx, result.attempt_id, "partly", versions[0])
    _mark(ctx, result.attempt_id, "none_of_these", freeText="None of these; I misread the sign.")
    _mark(ctx, result.attempt_id, "cleared", versions[1])
    _call(ctx, "record_hypothesis_exposure", {"attemptId": result.attempt_id, "surface": "marks_feedback",
                                              "hypothesisVersionIds": versions})
    after = _dump(paths)
    assert {table for table in before if before[table] != after[table]} == set()
    assert len(_rows(repository, "hypothesis_marks")) == 5


def _paths(vault):
    from learnloop.vault.paths import VaultPaths

    return VaultPaths(vault.root, vault.config)


def test_a_rebuild_ignores_marks_and_keeps_them(journey):
    ctx, vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)
    version = marks["hypotheses"][0]["hypothesisVersionId"]
    paths = _paths(vault)
    rebuild_derived_state(vault, repository)
    rebuild_derived_state(vault, repository)
    without = _dump(paths)
    _mark(ctx, result.attempt_id, "my_gap", version)
    rebuild_derived_state(vault, repository)
    with_marks = _dump(paths)
    derived = {table for table, role in TABLE_ROLES.items() if role is TableRole.DERIVED and table in without}
    assert derived
    assert ({table: _without_surrogates(with_marks)[table] for table in derived}
            == {table: _without_surrogates(without)[table] for table in derived})
    assert len(_rows(repository, "hypothesis_marks")) == 1


def _without_surrogates(dump):
    """A rebuild mints new ids and stamps new times: what replay derives is the rest."""

    import re

    def plain(row):
        text = re.sub(r"[0-9A-HJKMNP-TV-Z]{26}", "ULID", repr(row))
        return re.sub(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?(Z|\+00:00)", "TIME", text)

    return {table: sorted(plain(row) for row in rows) for table, rows in dump.items()}


def test_marks_are_never_forwarded_to_the_self_report_channel(journey, monkeypatch):
    ctx, _vault, repository, result, outcome = journey
    marks = _released(ctx, repository, outcome, result)

    def forbidden(*_args, **_kwargs):  # pragma: no cover - the test fails if this runs
        raise AssertionError("a mark reached the self-report channel")

    monkeypatch.setattr("learnloop.diagnosis.causal_attribution.record_unresolved_cause_self_report", forbidden)
    for hypothesis in marks["hypotheses"]:
        _mark(ctx, result.attempt_id, "my_gap", hypothesis["hypothesisVersionId"])
    factor_id = wf.get(repository, outcome.workflow_id)["factor_id"]
    assert repository.unresolved_cause_factor(factor_id)["status"] == "open"
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM causal_attribution_reports").fetchone()[0] == 0


def _without_ids(prompts):
    import re

    return [re.sub(r"[0-9A-HJKMNP-TV-Z]{26}", "ULID", prompt) for prompt in prompts]


def test_the_blind_grader_never_sees_marks_and_the_diagnoser_does(tmp_path):
    """Two identical vaults; one has marks and free text on an earlier miss. The next answer's grader
    prompts are the same in both and hold none of it; its diagnoser's context holds both, attributed."""

    secret = "SENTINEL_WORDS_OF_THE_LEARNER"
    prompts = {}
    for name in ("plain", "marked"):
        paths, vault, repository = live_shape_vault(tmp_path / name, task_features=False)
        client = BlindRivalClient()
        result, _outcome = live_miss(vault, repository, client)
        row = wf.attempt_workflow(repository, result.attempt_id)
        wf.finish(repository, str(row["id"]), to_state=wf.SKIPPED, reason="continue_without_it",
                  release=wf.RELEASE_CONTINUE_WITHOUT, clock=CLOCK)
        if name == "marked":
            listed = panel.markable_list(vault, repository, result.attempt_id)
            panel.record_mark(vault, repository, attempt_id=result.attempt_id, mark="my_gap",
                              hypothesis_version_id=listed.order[0], clock=CLOCK)
            panel.record_mark(vault, repository, attempt_id=result.attempt_id, mark="none_of_these",
                              free_text=secret, clock=CLOCK)
        client.prompts.clear()
        client.calls.clear()
        later = type(CLOCK)(CLOCK.now() + timedelta(days=2))
        live_miss(vault, repository, client, clock=later, answer="A = V Sigma U again wrong")
        prompts[name] = list(zip(client.calls, client.prompts, strict=True))
    grader = {name: [prompt for purpose, prompt in rows if "grad" in purpose] for name, rows in prompts.items()}
    assert grader["plain"] and _without_ids(grader["plain"]) == _without_ids(grader["marked"])
    assert all(secret not in prompt and "learner_marks" not in prompt for prompt in grader["marked"])
    diagnoser = [prompt for purpose, prompt in prompts["marked"] if "diagnos" in purpose]
    assert diagnoser and any(secret in prompt and M.ATTRIBUTION in prompt for prompt in diagnoser)
    assert not any(secret in prompt or "learner_marks" in prompt for purpose, prompt in prompts["plain"])


def test_the_diagnoser_reads_only_marks_made_before_the_attempt_it_is_on(tmp_path):
    from learnloop.diagnosis.split.history import AttemptRef, VaultHistoryStore

    paths, vault, repository = live_shape_vault(tmp_path, task_features=False)
    result, _outcome = live_miss(vault, repository, BlindRivalClient())
    row = wf.attempt_workflow(repository, result.attempt_id)
    wf.finish(repository, str(row["id"]), to_state=wf.SKIPPED, reason="continue_without_it",
              release=wf.RELEASE_CONTINUE_WITHOUT, clock=CLOCK)
    listed = panel.markable_list(vault, repository, result.attempt_id)
    panel.record_mark(vault, repository, attempt_id=result.attempt_id, mark="my_gap",
                      hypothesis_version_id=listed.order[0], clock=CLOCK)
    stored = _rows(repository, "hypothesis_marks")[0]["created_at"]
    history = VaultHistoryStore(vault, repository)
    def shown(at):
        rows = history.attempts_before(AttemptRef("att_later", at), None)
        return next(row for row in rows if row.attempt_id == result.attempt_id).learner_marks
    assert shown("2099-01-01T00:00:00Z")[0]["created_at"] == stored
    assert shown(stored) == ()


def test_the_switch_off_keeps_the_diagnosers_context_as_it_was_whatever_rows_exist(tmp_path):
    from learnloop.diagnosis.split.history import AttemptRef, VaultHistoryStore
    from learnloop.vault.loader import load_vault
    from tests.helpers import append_config_toml

    paths, vault, repository = live_shape_vault(tmp_path, task_features=False)
    result, _outcome = live_miss(vault, repository, BlindRivalClient())
    row = wf.attempt_workflow(repository, result.attempt_id)
    wf.finish(repository, str(row["id"]), to_state=wf.SKIPPED, reason="continue_without_it",
              release=wf.RELEASE_CONTINUE_WITHOUT, clock=CLOCK)
    listed = panel.markable_list(vault, repository, result.attempt_id)
    panel.record_mark(vault, repository, attempt_id=result.attempt_id, mark="my_gap",
                      hypothesis_version_id=listed.order[0], clock=CLOCK)
    append_config_toml(paths.root, MARKS_OFF)
    off = load_vault(paths.root)
    rows = VaultHistoryStore(off, repository).attempts_before(AttemptRef("later", "2099-01-01T00:00:00Z"), None)
    assert all(attempt.learner_marks == () for attempt in rows)


# -- (7) the kill switch -----------------------------------------------------------------------------


def test_off_means_no_key_no_rows_and_the_same_replies(tmp_path, monkeypatch):
    monkeypatch.setattr("learnloop_sidecar.handlers.practice.ready_grading_provider",
                        lambda *_a, **_k: ("fake", _Runtime(), object()))
    replies = {}
    for name, config in {"on": "", "off": MARKS_OFF}.items():
        _vault, _repository, paths = rival_causes_vault(tmp_path / name, config=config)
        ctx = SidecarContext()
        ctx.load(paths.root)
        ctx.post_attempt_worker.autostart = False
        vault, repository = ctx.require_vault()
        result, outcome = miss_with_rivals(vault, repository)
        _generate(ctx, repository)
        _call(ctx, "followup_show_anyway", {"attemptId": result.attempt_id})
        bundle = _call(ctx, "get_feedback", {"attemptId": result.attempt_id})
        versions = [str(row["id"]) for row in repository.causal_hypotheses_for_attempt(result.attempt_id)]
        receipt = _call(ctx, "record_hypothesis_exposure", {"attemptId": result.attempt_id, "surface": "why",
                                                            "hypothesisVersionIds": versions})
        mark = _mark(ctx, result.attempt_id, "my_gap", versions[0])
        probe, _row = _serve_and_answer(ctx, repository, result.attempt_id, outcome)
        probe_bundle = _call(ctx, "get_feedback", {"attemptId": probe.attempt_id})
        replies[name] = {"bundle": bundle, "probe": probe_bundle, "receipt": receipt, "mark": mark}
        replies[name]["rows"] = {table: len(_rows(repository, table)) for table in LEDGERS}
    assert replies["off"]["rows"] == dict.fromkeys(LEDGERS, 0)
    assert replies["on"]["rows"]["hypothesis_marks"] == 1
    assert replies["off"]["receipt"]["recorded"] is False and replies["off"]["mark"]["recorded"] is False
    assert "hypothesisMarks" not in replies["off"]["bundle"] and "hypothesisMarks" not in replies["off"]["probe"]
    # On adds exactly that one key to each bundle: everything else is the same read, byte for byte.
    for key in ("bundle", "probe"):
        assert set(replies["on"][key]) - set(replies["off"][key]) == {"hypothesisMarks"}
        shown = {name: dict(replies[name][key]) for name in ("on", "off")}
        shown["on"].pop("hypothesisMarks")
        assert _normalized(shown["on"]) == _normalized(shown["off"])


def _normalized(reply):
    import re

    text = json.dumps(_bundle_without_ids(reply), sort_keys=True, default=str)
    text = re.sub(r"[0-9A-HJKMNP-TV-Z]{26}", "ULID", text)
    return re.sub(r"\b(dr|cdo|chs|hs|pp|ge|rc|fw|cpc)_[0-9a-f]{16,}", r"\1_ID", text)


def test_with_no_causes_on_the_attempt_the_bundle_has_no_key(tmp_path):
    from tests.split_live_helpers import split_vault

    paths, _vault, _repository = split_vault(tmp_path, version="mvp-0.44")
    ctx = SidecarContext()
    ctx.load(paths.root)
    vault, repository = ctx.require_vault()
    assert panel.view(vault, repository, "att_nothing") is None


def test_the_switch_is_on_by_default_and_classified():
    from learnloop.config.schema import FollowupServeConfig
    from learnloop.params.parameter_registry import classify_config_path

    assert FollowupServeConfig().hypothesis_marks is True
    assert "kill switch" in classify_config_path("followup.hypothesis_marks").rationale
