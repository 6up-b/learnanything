"""Reader workbench RW2c: help outcomes, a replayable read (spec_reader_workbench_v1 §5.10, G39).

``help_outcomes`` is deterministic (computed twice, identical), reads only
existing rows (the database file is unchanged), replays at ``as_of`` (rows
and attempts after it are not seen), reads the hint service's replies and
the sources spec's S5 outcomes instead of re-deriving them (and reads S5 as
absent when its tables are), and its typed lines never carry the item's
answer or a free-text field. Fakes only; no model is called.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import closing
from pathlib import Path

from learnloop.db.connection import connect
from learnloop.db.stores.help_assists import insert_assist
from learnloop.db.stores.judgments import append_judgment
from learnloop.workbench.help_outcomes import help_outcomes, item_facets_of, lines_for
from tests.approach_map_fakes import EXPECTED, ITEM, LO, add_attempt
from tests.workbench_help_fakes import open_problem, sidecar

FACET = "recall"
T0 = "2026-10-20T10:00:00Z"


def _at(minutes: int) -> str:
    hour, minute = divmod(minutes, 60)
    return f"2026-10-20T{10 + hour:02d}:{minute:02d}:00Z"


def _row(assist_id: str, session: str, kind: str, minutes: int, **values):
    row = {"id": assist_id, "surface": "workbench", "assist_kind": kind, "practice_item_id": ITEM,
           "practice_item_hash": "h", "workbench_session_id": session, "chooser": "none", "shown": 1,
           "counted_by": "server" if kind in ("check", "hint") else None, "requested_at": _at(minutes),
           "shown_at": _at(minutes)}
    row.update(values)
    return row


def _verdicts(*valid: str, questionable: str | None = None) -> str:
    rows = [{"chain_id": chain, "verdict": "valid"} for chain in valid]
    if questionable:
        rows.append({"chain_id": questionable, "verdict": "questionable"})
    return json.dumps(rows)


def _insert(paths, rows) -> None:
    with closing(connect(paths.sqlite_path)) as connection:
        for row in rows:
            insert_assist(connection, row)
        connection.commit()


def _world(tmp_path: Path):
    """One problem: a check (step 2 questionable, an invalid-algebra guess), a
    level-3 worked-parallel hint, a later check where step 2 now holds; a
    second hint followed by another hint before the next check; a third hint
    with no later check. The problem is submitted correct; an independent
    attempt on the facet follows an hour later."""

    paths, ctx, _session = sidecar(tmp_path)
    wb, chains = open_problem(ctx)
    one, two = chains
    add_attempt(paths.sqlite_path, "att_wb", correctness=1.0, created_at="2026-10-20T11:00:00+00:00")
    add_attempt(paths.sqlite_path, "att_later", correctness=1.0, created_at="2026-10-20T12:00:00+00:00")
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET hints_used = 2 WHERE id = 'att_wb'")
        connection.execute("UPDATE workbench_sessions SET attempt_id = 'att_wb', status = 'submitted' WHERE id = ?",
                           (wb,))
        connection.commit()
    _insert(paths, [
        _row("ha_c1", wb, "check", 0, step_verdicts_json=_verdicts(one, questionable=two),
             first_questionable_step_id=two, error_kind_guess="invalid_algebra"),
        _row("ha_h1", wb, "hint", 1, hint_kind="worked_parallel", level=3, strategy="cdf_first",
             attempt_id="att_wb", about_step_id=two),
        _row("ha_c2", wb, "check", 2, step_verdicts_json=_verdicts(one, two)),
        _row("ha_h2", wb, "hint", 3, hint_kind="waypoint", level=3, strategy="P = 1/4 at the edge",
             attempt_id="att_wb"),
        _row("ha_h3", wb, "hint", 4, hint_kind="next_step", level=2, attempt_id="att_wb"),
        _row("ha_c3", wb, "check", 5, step_verdicts_json=_verdicts(one, two)),
        _row("ha_h4", wb, "hint", 6, hint_kind="localize", level=2, attempt_id="att_wb"),
    ])
    with closing(connect(paths.sqlite_path)) as connection:
        append_judgment(connection, task="hint_fit", left_kind="help_assist", left_id="ha_h3", judge="learner_card",
                        input_hash="x", verdict="different", rationale=json.dumps({"shortcut": "too_big"}),
                        created_at=_at(4))
        connection.execute(
            "INSERT INTO attempt_diagnoses (id, attempt_id, diagnosis_prompt_version, mode, history_mode, status, "
            "proposal_json, created_at) VALUES ('dg_1', 'att_wb', 'v', 'live', 'full', 'completed', ?, ?)",
            (json.dumps({"analysis_md": f"They wrote {EXPECTED}", "event_diagnoses": [
                {"event_index": 0, "causal_class": "learner_state", "operation": "apply_cdf_boundary",
                 "misconception_statement": "adds one to a probability",
                 "registry_match": {"kind": "durable", "id": "mc_cdf_plus_one"}}]}), "2026-10-20T11:00:30Z"))
        connection.commit()
    return paths, ctx, wb


def _facets(paths):
    from learnloop.vault.loader import load_vault

    return item_facets_of(load_vault(paths.root))


def _help(result, kind: str):
    [found] = [entry for entry in result.helps if entry.help == "hint" and entry.kind == kind]
    return found


def test_help_outcomes_is_deterministic_and_reads_only_existing_rows(tmp_path):
    paths, _ctx, _wb = _world(tmp_path)
    facets = _facets(paths)
    before = hashlib.sha256(Path(paths.sqlite_path).read_bytes()).hexdigest()
    first = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=facets)
    second = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=facets)
    assert first.as_dict() == second.as_dict()
    assert json.dumps(first.as_dict(), sort_keys=True) == json.dumps(second.as_dict(), sort_keys=True)
    # A pure read: the database file is byte-for-byte unchanged.
    assert hashlib.sha256(Path(paths.sqlite_path).read_bytes()).hexdigest() == before
    assert first.sources == {"help_assists": "read", "retrieval_intervention_outcomes": "read"}
    assert first.label.startswith("what preceded recovery for you")


def test_continuation_reads_the_next_check_with_no_other_hint_between(tmp_path):
    paths, _ctx, _wb = _world(tmp_path)
    result = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=_facets(paths))
    # Step 2 holds at the next check, with no hint between: continued.
    assert dict(_help(result, "worked_parallel").continuation) == {"continued": 1}
    # Another hint came before the next check: more help, not "unaided".
    assert dict(_help(result, "waypoint").continuation) == {"more_help": 1}
    # The next check found nothing new valid: not continued.
    assert dict(_help(result, "next_step").continuation) == {"not_continued": 1}
    assert dict(_help(result, "localize").continuation) == {"no_later_check": 1}
    # The service's own replies, not a re-derivation.
    assert dict(_help(result, "next_step").doesnt_connect) == {"too_big": 1}
    hint = _help(result, "worked_parallel")
    assert dict(hint.levels) == {3: 1} and dict(hint.attempt) == {"correct": 1}
    assert dict(hint.later_independent) == {"pass": 1}


def test_as_of_replays_the_past(tmp_path):
    paths, _ctx, _wb = _world(tmp_path)
    facets = _facets(paths)
    early = help_outcomes(paths.sqlite_path, [FACET], _at(3), item_facets=facets)
    # At 10:03 the third and fourth hints and the last check did not exist yet,
    # and neither did the submit nor the later attempt.
    assert sorted(entry.kind for entry in early.helps) == ["waypoint", "worked_parallel"]
    assert dict(_help(early, "worked_parallel").attempt) == {"not_submitted": 1}
    assert dict(_help(early, "worked_parallel").later_independent) == {"pending": 1}
    assert dict(_help(early, "waypoint").continuation) == {"no_later_check": 1}
    middle = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T11:30:00Z", item_facets=facets)
    assert dict(_help(middle, "worked_parallel").later_independent) == {"pending": 1}
    late = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T12:30:00Z", item_facets=facets)
    assert dict(_help(late, "worked_parallel").later_independent) == {"pass": 1}
    # Replaying a past instant again gives what it gave.
    assert help_outcomes(paths.sqlite_path, [FACET], _at(3), item_facets=facets).as_dict() == early.as_dict()


def test_where_the_work_goes_off_keeps_guesses_and_the_diagnosers_typed_causes(tmp_path):
    paths, _ctx, _wb = _world(tmp_path)
    result = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=_facets(paths))
    [goes] = [entry.as_dict() for entry in result.goes_off]
    assert goes["first_questionable_guesses"] == [{"kind": "invalid_algebra", "count": 1, "last": "2026-10-20"}]
    assert goes["guesses_are"] == "the check's guesses, not a diagnosis"
    causes = {entry["cause"] for entry in goes["diagnosed_causes"]}
    assert causes == {"apply_cdf_boundary", "misconception:mc_cdf_plus_one"}
    # The diagnoser's statement and analysis never reach the record.
    text = json.dumps(result.as_dict())
    assert "adds one" not in text and "They wrote" not in text


def test_a_facet_without_history_gives_no_lines(tmp_path):
    paths, _ctx, _wb = _world(tmp_path)
    result = help_outcomes(paths.sqlite_path, ["another_facet"], "2026-10-20T13:00:00Z",
                           item_facets=_facets(paths))
    assert result.helps == [] and result.goes_off == []
    assert lines_for(result) == ()


def _s5(paths, *, cold_attempt: str | None, state: str) -> None:
    from learnloop.db.stores.source_service import insert_intervention

    with closing(connect(paths.sqlite_path)) as connection:
        insert_intervention(connection, id="ri_1", created_at="2026-10-20T09:00:00Z", kind="source_passage",
                            caller_kind="tutor", targets={"facets": [FACET], "learning_object_ids": [LO]})
        connection.execute(
            "INSERT INTO retrieval_intervention_outcomes (intervention_id, next_attempt_id, next_correctness, "
            "next_assisted, cold_attempt_id, cold_outcome_state, outcome_version) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("ri_1", "att_wb", 1.0, 0, cold_attempt, state, "retrieval_outcomes.v4"))
        connection.commit()


def test_s5_outcomes_are_read_not_rederived_and_pending_until_as_of(tmp_path):
    paths, _ctx, _wb = _world(tmp_path)
    _s5(paths, cold_attempt="att_later", state="cold_success")
    facets = _facets(paths)
    late = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=facets)
    [retrieval] = [entry for entry in late.helps if entry.help == "retrieval"]
    assert retrieval.kind == "source_passage" and retrieval.source == "retrieval_intervention_outcomes"
    assert dict(retrieval.continuation) == {"continued": 1}
    assert dict(retrieval.later_independent) == {"pass": 1}
    # Before the cold attempt existed, S5's success is not yet known at as_of.
    middle = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T11:30:00Z", item_facets=facets)
    [retrieval] = [entry for entry in middle.helps if entry.help == "retrieval"]
    assert dict(retrieval.later_independent) == {"pending": 1}


def test_s5_absent_reads_as_absent(tmp_path):
    paths, _ctx, _wb = _world(tmp_path)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("DROP TABLE retrieval_intervention_outcomes")
        connection.commit()
    result = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=_facets(paths))
    assert result.sources["retrieval_intervention_outcomes"] == "absent"
    assert not [entry for entry in result.helps if entry.help == "retrieval"]
    assert [entry for entry in result.helps if entry.help == "hint"]


#: The only keys a line may carry (typed records: kinds, levels, counts, outcomes).
LINE_KEYS = {
    "label": {"line", "label"},
    "help_outcome": {"line", "facet", "help", "kind", "strategy", "levels", "shown", "continued_unaided",
                     "continuation_observed", "more_help_followed", "attempt_grades", "later_independent",
                     "doesnt_connect"},
    "goes_off": {"line", "facet", "first_questionable_guesses", "guesses_are", "diagnosed_causes", "causes_are"},
}


def test_lines_are_typed_records_that_never_carry_the_answer(tmp_path):
    paths, _ctx, _wb = _world(tmp_path)
    result = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=_facets(paths))
    lines = lines_for(result, limit=10, per_facet=10)
    assert lines and lines[0]["line"] == "label"
    for line in lines:
        assert set(line) == LINE_KEYS[line["line"]], line
    text = json.dumps(lines)
    for piece in (EXPECTED, "1/4", "x^2", "Integrate the density"):
        assert piece not in text
    # A strategy that is not a slug (it quoted the answer) is never carried.
    waypoint = next(line for line in lines if line.get("kind") == "waypoint")
    assert waypoint["strategy"] is None
    assert next(line for line in lines if line.get("kind") == "worked_parallel")["strategy"] == "cdf_first"
    # The default bound: at most three help kinds per facet, the ones with an
    # observed outcome first (most recent first among equals), then the guesses.
    bounded = lines_for(result)
    assert [line.get("kind") for line in bounded if line["line"] == "help_outcome"] == [
        "next_step", "worked_parallel", "localize"]
    assert bounded[-1]["line"] == "goes_off"


def test_the_writer_and_chooser_get_the_lines_and_never_the_answer_through_them(tmp_path):
    from tests.hint_fakes import ChooserFake, WriterFake, prefer
    from tests.workbench_help_fakes import call, run_job, wb_answer

    paths, ctx, _wb = _world(tmp_path)
    writer = WriterFake([wb_answer] * 4)
    ctx.hint_writer_client = writer
    ctx.hint_chooser_client = chooser = ChooserFake(prefer("next_step@L3", 0.6))
    wb, _chains = open_problem(ctx)
    run_job(ctx, call(ctx, "workbench.suggest_help", {"sessionId": wb}))
    run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    block = writer.contexts[-1]["workbench"]
    lines = block["help_outcomes"]
    assert lines[0] == {"line": "label", "label": "what preceded recovery for you (associations, not what works)"}
    assert {line["kind"] for line in lines if line["line"] == "help_outcome"} >= {"worked_parallel"}
    assert "never mention them" in block["help_outcomes_rule"]
    text = json.dumps(lines)
    for piece in (EXPECTED, "1/4", "x^2"):
        assert piece not in text
    for entry in chooser.calls:
        chooser_lines = entry["state"]["workbench"]["help_outcomes"]
        assert chooser_lines == lines and "1/4" not in json.dumps(chooser_lines)


def test_lines_for_ranks_every_requested_facet():
    """Regression: the ranking key was rebound to an int inside the loop, so
    the second facet's sort raised TypeError (an item with two facets)."""

    from collections import Counter

    from learnloop.workbench.help_outcomes import VERSION, HelpKindOutcome, HelpOutcomesV1

    def kind(facet: str, name: str, shown: int, continued: int) -> HelpKindOutcome:
        return HelpKindOutcome(facet, "hint", name, None, shown=shown, levels=Counter({3: shown}),
                               continuation=Counter({"continued": continued}),
                               later_independent=Counter({"pending": shown}),
                               last_at="2026-10-20T10:00:00+00:00")

    outcomes = HelpOutcomesV1(VERSION, "2026-10-20T13:00:00+00:00", ("f1", "f2"), [
        kind("f1", "waypoint", 2, 1), kind("f1", "next_step", 1, 1),
        kind("f2", "worked_parallel", 3, 2), kind("f2", "localize", 1, 0)], [], {})
    lines = lines_for(outcomes, limit=10)
    assert [(line["facet"], line["kind"]) for line in lines if line["line"] == "help_outcome"] == [
        ("f1", "waypoint"), ("f1", "next_step"), ("f2", "worked_parallel"), ("f2", "localize")]
    assert lines_for(outcomes, limit=10) == lines
