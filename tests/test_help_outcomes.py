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


def _verdicts(*valid: str, questionable: str | None = None, hashes: dict[str, str] | None = None) -> str:
    hashes = hashes or {}
    rows = [{"chain_id": chain, "verdict": "valid", "hash": hashes.get(chain, f"h_{chain}")} for chain in valid]
    if questionable:
        rows.append({"chain_id": questionable, "verdict": "questionable",
                     "hash": hashes.get(questionable, f"h_{questionable}")})
    return json.dumps(rows)


def _snapshot(*chains: str, hashes: dict[str, str] | None = None) -> str:
    """A row's ``step_snapshot_json`` as the workbench writes it (ids, hashes)."""

    hashes = hashes or {}
    return json.dumps([{"chain_id": chain, "number": index, "hash": hashes.get(chain, f"h_{chain}")}
                       for index, chain in enumerate(chains, start=1)])


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
    # Step 2 is rewritten after the first hint (its hash changes), so the
    # second check's valid step 2 is new since that hint's delivery.
    edited = {two: "h_two_edited"}
    _insert(paths, [
        _row("ha_c1", wb, "check", 0, step_verdicts_json=_verdicts(one, questionable=two),
             step_snapshot_json=_snapshot(one, two), first_questionable_step_id=two,
             error_kind_guess="invalid_algebra"),
        _row("ha_h1", wb, "hint", 1, hint_kind="worked_parallel", level=3, strategy="cdf_first",
             attempt_id="att_wb", about_step_id=two, step_snapshot_json=_snapshot(one, two)),
        _row("ha_c2", wb, "check", 2, step_verdicts_json=_verdicts(one, two, hashes=edited),
             step_snapshot_json=_snapshot(one, two, hashes=edited)),
        _row("ha_h2", wb, "hint", 3, hint_kind="waypoint", level=3, strategy="P = 1/4 at the edge",
             attempt_id="att_wb", step_snapshot_json=_snapshot(one, two, hashes=edited)),
        _row("ha_h3", wb, "hint", 4, hint_kind="next_step", level=2, attempt_id="att_wb",
             step_snapshot_json=_snapshot(one, two, hashes=edited)),
        _row("ha_c3", wb, "check", 5, step_verdicts_json=_verdicts(one, two, hashes=edited),
             step_snapshot_json=_snapshot(one, two, hashes=edited)),
        _row("ha_h4", wb, "hint", 6, hint_kind="localize", level=2, attempt_id="att_wb",
             step_snapshot_json=_snapshot(one, two, hashes=edited)),
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


def _vault(paths):
    from learnloop.vault.loader import load_vault

    return load_vault(paths.root)


def _help(result, kind: str):
    [found] = [entry for entry in result.helps if entry.help == "hint" and entry.kind == kind]
    return found


def test_help_outcomes_is_deterministic_and_reads_only_existing_rows(tmp_path):
    paths, _ctx, _wb = _world(tmp_path)
    facets = _facets(paths)
    before = hashlib.sha256(Path(paths.sqlite_path).read_bytes()).hexdigest()
    vault = _vault(paths)
    first = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=facets, vault=vault)
    second = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=facets, vault=vault)
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


def _s5(paths) -> None:
    """An S5 tutor passage on the facet the day before (Oct 19, 11:30), its
    same-day next attempt (independent, correct) and, a day later, the
    world's independent attempt ``att_later`` (12:00, with a duration): S5's
    own join gives ``R_next`` continued and ``R_cold`` a success."""

    from learnloop.db.stores.source_service import insert_intervention

    add_attempt(paths.sqlite_path, "att_s5_next", correctness=1.0, created_at="2026-10-19T11:45:00+00:00")
    with closing(connect(paths.sqlite_path)) as connection:
        # Each records its facets, as attempts do (S5 joins on them).
        connection.execute("UPDATE practice_attempts SET latency_seconds = 60, evidence_facets_json = ? "
                           "WHERE id IN ('att_s5_next', 'att_later')", (json.dumps([FACET]),))
        insert_intervention(connection, id="ri_1", created_at="2026-10-19T11:30:00Z", kind="source_passage",
                            caller_kind="tutor", targets={"facets": [FACET], "learning_object_ids": [LO]})
        connection.commit()


def test_s5_outcomes_are_read_not_rederived_and_pending_until_as_of(tmp_path):
    paths, _ctx, _wb = _world(tmp_path)
    _s5(paths)
    facets = _facets(paths)
    vault = _vault(paths)
    late = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=facets, vault=vault)
    [retrieval] = [entry for entry in late.helps if entry.help == "retrieval"]
    assert retrieval.kind == "source_passage" and retrieval.source == "retrieval_intervention_outcomes"
    assert dict(retrieval.continuation) == {"continued": 1}
    assert dict(retrieval.later_independent) == {"pass": 1}
    # Before the cold attempt existed, S5's success is not yet known at as_of.
    middle = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T11:30:00Z", item_facets=facets, vault=vault)
    [retrieval] = [entry for entry in middle.helps if entry.help == "retrieval"]
    assert dict(retrieval.later_independent) == {"pending": 1}
    # Without the vault S5 cannot judge its targets: unknown, never a guess.
    blind = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=facets)
    [retrieval] = [entry for entry in blind.helps if entry.help == "retrieval"]
    assert (dict(retrieval.continuation), dict(retrieval.later_independent)) == ({"unknown": 1}, {"unmeasured": 1})
    assert blind.sources["retrieval_intervention_outcomes"] == "read_without_vault"


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



# ---------------------------------------------------------------------------
# Codex review (reader-rw2c-codex-review.md): F3-F6, F10
# ---------------------------------------------------------------------------

def _problem(tmp_path: Path, rows_for):
    """A fresh workbench problem with ``rows_for(wb, one, two)`` as its rows."""

    paths, ctx, _session = sidecar(tmp_path)
    wb, (one, two) = open_problem(ctx)
    _insert(paths, rows_for(wb, one, two))
    return paths, wb


def _only(result, help_: str, kind: str | None = None):
    [found] = [entry for entry in result.helps if entry.help == help_ and (kind is None or entry.kind == kind)]
    return found


def test_f4_a_step_already_on_the_page_that_a_later_check_validates_is_not_progress(tmp_path):
    """F4: the learner's step 1 is valid but never checked; a hint comes
    before the first check and nothing changes; the later check validates
    the existing step. That is not progress after the hint."""

    paths, _wb = _problem(tmp_path, lambda wb, one, two: [
        _row("ha_h", wb, "hint", 1, hint_kind="next_step", level=3, step_snapshot_json=_snapshot(one)),
        _row("ha_c", wb, "check", 2, step_verdicts_json=_verdicts(one), step_snapshot_json=_snapshot(one)),
    ])
    result = help_outcomes(paths.sqlite_path, [FACET], _at(30), item_facets=_facets(paths))
    assert dict(_only(result, "hint", "next_step").continuation) == {"not_continued": 1}


def test_f4_a_step_written_after_the_hint_that_the_check_validates_is_progress(tmp_path):
    paths, _wb = _problem(tmp_path, lambda wb, one, two: [
        _row("ha_h", wb, "hint", 1, hint_kind="next_step", level=3, step_snapshot_json=_snapshot(one)),
        _row("ha_c", wb, "check", 2, step_verdicts_json=_verdicts(one, two), step_snapshot_json=_snapshot(one, two)),
    ])
    result = help_outcomes(paths.sqlite_path, [FACET], _at(30), item_facets=_facets(paths))
    assert dict(_only(result, "hint", "next_step").continuation) == {"continued": 1}


def test_f4_no_work_recorded_at_delivery_stays_unknown(tmp_path):
    paths, _wb = _problem(tmp_path, lambda wb, one, two: [
        _row("ha_h", wb, "hint", 1, hint_kind="next_step", level=3),
        _row("ha_c", wb, "check", 2, step_verdicts_json=_verdicts(one, two), step_snapshot_json=_snapshot(one, two)),
    ])
    result = help_outcomes(paths.sqlite_path, [FACET], _at(30), item_facets=_facets(paths))
    assert dict(_only(result, "hint", "next_step").continuation) == {"unknown": 1}


def test_f4_an_intervening_example_is_further_help_but_the_hints_own_bridge_is_not(tmp_path):
    """F4: a worked example asked for ("show me") between a hint and the next
    check is further help; the bridge shown with the hint is part of it."""

    def rows(wb, one, two):
        return [
            _row("ha_h", wb, "hint", 1, hint_kind="next_step", level=3, step_snapshot_json=_snapshot(one)),
            _row("ha_b", wb, "bridge", 1, placement_json=json.dumps({"hint_assist_id": "ha_h", "status": "found"}),
                 shown_at="2026-10-20T10:01:30Z"),
            # A "show me" example stores the verdicts it was searched against
            # (fix round 3, M1; none on record would read unknown).
            _row("ha_x", wb, "example", 2, placement_json=json.dumps({"trigger": "show_me", "status": "found",
                                                                      "role": "worked_example"}),
                 step_snapshot_json=_snapshot(one), step_verdicts_json=_verdicts(one)),
            _row("ha_c", wb, "check", 3, step_verdicts_json=_verdicts(one, two),
                 step_snapshot_json=_snapshot(one, two)),
        ]

    paths, _wb = _problem(tmp_path, rows)
    result = help_outcomes(paths.sqlite_path, [FACET], _at(30), item_facets=_facets(paths))
    assert dict(_only(result, "hint", "next_step").continuation) == {"more_help": 1}
    # The example itself was the last help before the check: its continuation.
    assert dict(_only(result, "example").continuation) == {"continued": 1}
    # The bridge (delivered with the hint, measured from the hint's work)
    # met the example before the check: further help.
    assert dict(_only(result, "bridge").continuation) == {"more_help": 1}

    paths2, _wb2 = _problem(tmp_path / "bridge_only", lambda wb, one, two: rows(wb, one, two)[:2] + rows(wb, one, two)[3:])
    alone = help_outcomes(paths2.sqlite_path, [FACET], _at(30), item_facets=_facets(paths2))
    assert dict(_only(alone, "hint", "next_step").continuation) == {"continued": 1}


def test_f3_hints_the_learner_picked_stay_in_the_history_passage_picks_do_not_count_twice(tmp_path):
    """F3: "a smaller step" (a learner-picked hint) is a hint with its
    outcomes; "another passage" is not a second bridge."""

    paths, _wb = _problem(tmp_path, lambda wb, one, two: [
        _row("ha_w", wb, "hint", 1, hint_kind="waypoint", level=3, step_snapshot_json=_snapshot(one)),
        _row("ha_s", wb, "hint", 2, hint_kind="next_step", level=3, chooser="learner_pick", request="smaller_step",
             step_snapshot_json=_snapshot(one)),
        _row("ha_c", wb, "check", 3, step_verdicts_json=_verdicts(one, two), step_snapshot_json=_snapshot(one, two)),
        _row("ha_b", wb, "bridge", 4, placement_json=json.dumps({"hint_assist_id": "ha_s", "status": "found"})),
        _row("ha_p", wb, "bridge", 5, chooser="learner_pick",
             placement_json=json.dumps({"hint_assist_id": "ha_s", "status": "picked", "draw_assist_id": "ha_b"})),
    ])
    with closing(connect(paths.sqlite_path)) as connection:
        append_judgment(connection, task="hint_fit", left_kind="help_assist", left_id="ha_s", judge="learner_card",
                        input_hash="x", verdict="different", rationale=json.dumps({"shortcut": "notation"}),
                        created_at=_at(2))
        connection.commit()
    result = help_outcomes(paths.sqlite_path, [FACET], _at(30), item_facets=_facets(paths))
    picked = _only(result, "hint", "next_step")
    assert picked.shown == 1 and dict(picked.continuation) == {"continued": 1}
    assert dict(picked.doesnt_connect) == {"notation": 1}
    assert dict(_only(result, "hint", "waypoint").continuation) == {"more_help": 1}
    assert _only(result, "bridge").shown == 1


def test_f5_a_comparison_gets_no_credit_for_an_attempt_before_it_was_opened(tmp_path):
    """F5: attempt A Monday, an independent success B Tuesday, A's comparison
    opened Wednesday: nothing independent has happened since the comparison."""

    paths, ctx, _session = sidecar(tmp_path)
    wb, (one, two) = open_problem(ctx)
    add_attempt(paths.sqlite_path, "att_a", correctness=1.0, created_at="2026-10-19T10:00:00+00:00")
    add_attempt(paths.sqlite_path, "att_b", correctness=1.0, created_at="2026-10-20T10:00:00+00:00")
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE practice_attempts SET hints_used = 1 WHERE id = 'att_a'")
        connection.execute("UPDATE workbench_sessions SET attempt_id = 'att_a', status = 'submitted' WHERE id = ?",
                           (wb,))
        connection.commit()
    _insert(paths, [_row("ha_cmp", wb, "compare_methods", 0,
                         placement_json=json.dumps({"attempt_id": "att_a"}),
                         requested_at="2026-10-21T10:00:00Z", shown_at="2026-10-21T10:00:00Z")])
    result = help_outcomes(paths.sqlite_path, [FACET], "2026-10-21T12:00:00Z", item_facets=_facets(paths))
    comparison = _only(result, "compare_methods")
    assert dict(comparison.attempt) == {"correct": 1}
    assert dict(comparison.later_independent) == {"pending": 1}


def _grading(paths, attempt_id: str, *, points: float, at: str, revision: int, superseded_at: str | None = None,
             contract: str | None = "acv_1") -> None:
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO grading_evidence (id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "superseded_at, grading_revision, assessment_contract_version_id) VALUES (?, ?, 'c1', ?, 1, ?, ?, ?, ?)",
            (f"ge_{attempt_id}_{revision}", attempt_id, points, at, superseded_at, revision, contract))
        connection.commit()


def test_f6_a_later_regrade_never_changes_what_as_of_said(tmp_path):
    """F6: the independent attempt was graded 1/4 at noon and regraded 4/4 at
    14:00 (practice_attempts.correctness now 1.0). At 13:00 it was a fail,
    and it stays one; after the regrade it is a pass."""

    from learnloop.vault.loader import load_vault

    paths, _ctx, _wb = _world(tmp_path)
    _grading(paths, "att_later", points=1.0, at="2026-10-20T12:00:00Z", revision=0,
             superseded_at="2026-10-20T14:00:00Z")
    _grading(paths, "att_later", points=4.0, at="2026-10-20T14:00:00Z", revision=1)
    vault = load_vault(paths.root)
    facets = item_facets_of(vault)
    before = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=facets, vault=vault)
    assert dict(_help(before, "worked_parallel").later_independent) == {"fail": 1}
    after = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T15:00:00Z", item_facets=facets, vault=vault)
    assert dict(_help(after, "worked_parallel").later_independent) == {"pass": 1}
    # The same instant replays the same answer.
    assert help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=facets,
                         vault=vault).as_dict() == before.as_dict()
    # Without the vault (no rubric maximum) the past grade is unknown, never
    # the later one.
    blind = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=facets)
    assert dict(_help(blind, "worked_parallel").later_independent) == {"ungraded": 1}


def test_f6_a_hold_released_after_as_of_still_held_then(tmp_path):
    """F6: at 13:00 the attempt's grade was held for review (the blind
    record's route check held it and no criterion was assessed); an
    adjudication at 14:00 wrote assessed evidence over it, releasing it."""

    from learnloop.outcome_contract import (
        UNASSESSED_INTERPRETATION,
        UNVERIFIED_CRITERION_BLOCK,
        UNVERIFIED_INTERPRETATION_KEY,
    )
    from learnloop.vault.loader import load_vault

    paths, _ctx, _wb = _world(tmp_path)
    _grading(paths, "att_later", points=4.0, at="2026-10-20T12:00:00Z", revision=0,
             superseded_at="2026-10-20T14:00:00Z")
    unassessed = {"negative_evidence_blocked": UNVERIFIED_CRITERION_BLOCK,
                  UNVERIFIED_INTERPRETATION_KEY: UNASSESSED_INTERPRETATION}
    held_record = {"grading_support": {"proof_route_check": {"held_for_review": True, "status": "checked",
                                                             "version": "proof-route-check-v3"}}}
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE grading_evidence SET attribution_json = ? WHERE id = 'ge_att_later_0'",
                           (json.dumps(unassessed),))
        connection.execute(
            "INSERT INTO blind_grade_records (id, attempt_id, grading_prompt_version, output_schema_version, "
            "context_hash, record_json, created_at) VALUES ('bgr_1', 'att_later', 'v', 'v', 'h', ?, ?)",
            (json.dumps(held_record, separators=(",", ":")), "2026-10-20T12:00:00Z"))
        connection.commit()
    _grading(paths, "att_later", points=4.0, at="2026-10-20T14:00:00Z", revision=1)
    vault = load_vault(paths.root)
    facets = item_facets_of(vault)
    before = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=facets, vault=vault)
    assert dict(_help(before, "worked_parallel").later_independent) == {"held": 1}
    after = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T15:00:00Z", item_facets=facets, vault=vault)
    assert dict(_help(after, "worked_parallel").later_independent) == {"pass": 1}


def test_f10_an_s5_record_naming_a_passage_is_its_outcome_and_is_not_counted_again(tmp_path):
    """F10: a worked example S5 recorded (by its assist id), its cold outcome
    right-censored: the example's later outcome is S5's (pending), not the
    passage's own derivation (the independent pass an hour later), and the
    record is not a second, generic retrieval help."""

    from learnloop.db.stores.source_service import insert_intervention

    paths, _ctx, wb = _world(tmp_path)
    _insert(paths, [_row("ha_ex", wb, "example", 1,
                         placement_json=json.dumps({"hint_assist_id": "ha_h1", "status": "found",
                                                    "role": "worked_example"}),
                         shown_at="2026-10-20T10:01:30Z")])
    with closing(connect(paths.sqlite_path)) as connection:
        insert_intervention(connection, id="ri_ex", created_at="2026-10-20T10:01:30Z", kind="source_passage",
                            caller_kind="workbench", caller_ref="ha_ex",
                            targets={"facets": [FACET], "learning_object_ids": [LO]})
        connection.commit()
    # S5's own join: no independent attempt a cold delay after it yet.
    result = help_outcomes(paths.sqlite_path, [FACET], "2026-10-20T13:00:00Z", item_facets=_facets(paths),
                           vault=_vault(paths))
    example = _only(result, "example")
    assert dict(example.later_independent) == {"pending": 1}
    assert not [entry for entry in result.helps if entry.help == "retrieval"]
