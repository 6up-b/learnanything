"""Curriculum C5: notes as learner text (spec_deliverable_curriculum_v1 §10.2, §12 C5), with
C2b's rules: the notes are the vault's own and note text is learner text.

With the learner's opt-in (``notes.gaps_enabled``, default off; owner Q9) a LINKED note is a
tier-2 learner-text-gaps input (``source_kind = 'learner_note'``), keyed to the topics and
passages it is linked to, read with its snapshot's text like any other learner text (C2b: the
pipeline's ordinary routes, the Decider and the embedding shortlist; the row keeps the words).
A hidden link or an unlinked note never feeds gaps; switched off the gaps code reads no note
row; a note linked to (or written beside) protected material is never read; an unmatched
prerequisite named from a note is never drafted.

Every note is synthetic vault data (tests/notes_fixtures.py). Every model is a fake; background
work runs inline and the post-attempt worker never starts a thread (jobs are run by hand).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.diagnosis.text_gaps import jobs as J
from learnloop.diagnosis.text_gaps.contract import (
    NON_SERVING_SOURCE_KINDS,
    NOTE_SOURCE_KINDS,
    READABLE_SOURCE_KINDS,
    READER_NOTE_PROMPT_VERSION,
    SOURCE_KINDS,
)
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients
from learnloop.diagnosis.text_gaps.sources import learner_text
from learnloop.source_retrieval import note_links as NL
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.vault.loader import load_vault
from tests.helpers import NOW
from tests.notes_fixtures import SENTINEL, edit_annotation
from tests.reading_path_fixtures import call
from tests.section_coverage_fixtures import table_counts
from tests.test_notes_linked import _deliverable, _lines
from tests.text_gap_fakes import ChoiceDecider, GapLLMFake, always, word_match

CLOCK = FrozenClock(NOW)
GAPS_ON = "[notes]\ngaps_enabled = true\n"
#: What reading a note may write: gap rows, their jobs, ledger verdicts, receipts and
#: work claims (the holding pen only for a belief, not exercised here).
GAP_TABLES = {"learner_text_gaps", "learner_text_gap_jobs", "judgment_ledger", "model_call_receipts",
              "judgment_work_claims", "model_call_spend", "text_write_provenance"}
#: Evidence, mastery, grading, scheduling and claims: never written by a note's reading.
NEVER_TABLES = ("practice_attempts", "grading_evidence", "facet_recall_state", "facet_capability_evidence",
                "probe_observations", "fsrs_states", "learner_claims", "learner_gap_check_advances",
                "learner_gap_commitments", "self_reports")


class PlanGapFake(GapLLMFake):
    """The gap reader and judge on the ChatGPT plan."""

    provider_name = "fake_plan_gap"
    provider_type = "chatgpt_plan"
    model = "fake/plan-gap"


class MeteredGapFake(GapLLMFake):
    provider_name = "fake_metered_gap"
    provider_type = "openrouter"
    model = "fake/metered-gap"


def _linked(tmp_path: Path, monkeypatch=None, *, gaps: bool = True, config: str = ""):
    """C2's deliverable vault with the path's two vault notes linked (the typed Reader note
    carries ``SENTINEL``; the other is a capture), and the opt-in on (or off)."""

    paths, repository, ctx, goal_id, corpus, notes = _deliverable(tmp_path, config=(GAPS_ON if gaps else "") + config)
    ctx.post_attempt_worker.autostart = False  # jobs are run by hand here
    lines = _lines(call(ctx, "notes.path", {"goal_id": goal_id}))
    assert {line["noteKey"] for line in lines} == {corpus["typed"], corpus["captured"]}
    _CORPUS[str(repository.sqlite_path)] = corpus
    return paths, repository, ctx, goal_id, corpus, lines


#: The corpus of each linked vault (by database), so :func:`_snapshots` can name its notes.
_CORPUS: dict[str, dict[str, str]] = {}
TYPED, CAPTURED = "typed", "captured"


def _snapshots(repository) -> dict[str, str]:
    """``{"typed" | "captured": the newest snapshot id}``."""

    corpus = _CORPUS[str(repository.sqlite_path)]
    names = {corpus[TYPED]: TYPED, corpus[CAPTURED]: CAPTURED}
    with repository.connection() as connection:
        return {names[str(row[1])]: str(row[0]) for row in connection.execute(
            "SELECT id, note_key FROM learner_notes ORDER BY created_at, rowid") if str(row[1]) in names}


def _typed_line(lines):
    return next(line for line in lines if "Av = lv" in line["note"]["text"])


def _jobs(repository, kind: str = "learner_note") -> list[tuple]:
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT source_id, state, attempt_count FROM learner_text_gap_jobs WHERE source_kind = ? "
            "ORDER BY created_at, id", (kind,))]


def _gaps(repository) -> list[dict]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM learner_text_gaps WHERE source_kind = 'learner_note' ORDER BY created_at, id")]


def _clients(llm, *, decider=None) -> PipelineClients:
    return PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=(lambda: decider) if decider else None,
                           drafter=lambda: llm, tutor=None, embedder=None)


def _run(paths, repository, clients, *, source: tuple[str, str] | None = None):
    return J.process_next_gap_job(paths.root, repository, owner="t", clients=clients, clock=CLOCK, source=source)


def _readings(llm) -> list[dict]:
    return [payload for purpose, payload in llm.calls if purpose == "learner_gap_reading"]


# -- the contract and the kinds --------------------------------------------------------------------

def test_learner_note_is_a_readable_tier_2_kind_read_like_other_learner_text():
    assert "learner_note" in SOURCE_KINDS and "learner_note" in READABLE_SOURCE_KINDS
    assert "learner_note" in NON_SERVING_SOURCE_KINDS  # never a sooner check or a placement observation
    assert NOTE_SOURCE_KINDS == ("learner_note",)
    assert load_vault  # (imported for the tests below)


# -- switched off: today's, byte for byte, and no note row read --------------------------------------

def test_switched_off_the_gaps_code_reads_no_note_row_and_queues_nothing(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch, gaps=False)
    vault = load_vault(paths.root)
    assert vault.config.notes.gaps_enabled is False  # the default: off
    assert _jobs(repository) == []  # the link run queued nothing
    contract = call(ctx, "reader.prompt_contract", {})
    assert contract["notes"] == {"enabled": True, "meaning": False, "pocketNotesLabel": NL.POCKET_NOTES_LABEL,
                                 "takePrefix": NL.TAKE_PREFIX}  # C2's contract exactly: no `gaps`
    # From here on any read of a note row by the gaps code fails the test.
    from learnloop.db.stores import learner_notes as notes_store
    from learnloop.source_retrieval import note_gaps

    def refuse(*_args, **_kwargs):
        raise AssertionError("the gaps code read a note row while switched off")

    snapshot_id = "ln_anything"
    llm = PlanGapFake()
    with monkeypatch.context() as patched:
        for name in ("links", "notes_by_id", "current_notes", "learner_rows_for", "tables_present"):
            patched.setattr(notes_store, name, refuse)
        for name in ("linked_notes", "linked_note_ids", "note_text"):
            patched.setattr(note_gaps, name, refuse)
        before = table_counts(repository)
        swept = J.sweep_backlog(vault, repository, include_history=True)
        assert set(swept) == set(J.BACKLOG_KINDS) and "learner_note" not in swept  # today's keys exactly
        assert J.enqueue_learner_notes(vault, repository) == 0
        assert learner_text(vault, repository, "learner_note", snapshot_id) is None
        assert table_counts(repository) == before
        # A note job queued while it was on: switched off it is skipped, never read.
        J.enqueue(repository, source_kind="learner_note", source_id=snapshot_id, clock=CLOCK)
        outcome = _run(paths, repository, _clients(llm))
        assert (outcome.source_kind, outcome.state) == ("learner_note", "skipped")
        assert llm.calls == [] and _gaps(repository) == []
    # The learner's acts on notes queue nothing either.
    typed = _typed_line(lines)
    hidden = call(ctx, "notes.decide", {"link_id": typed["linkId"], "choice": "hide"})
    call(ctx, "notes.decide", {"link_id": hidden["linkId"], "choice": "keep"})
    assert [row for row in _jobs(repository) if row[0] != snapshot_id] == []


def test_switched_off_the_pipeline_and_the_reader_are_todays(tmp_path, monkeypatch):
    """The learner_text_gaps switch also holds: with the pipeline off nothing is queued
    even with the opt-in on, and the notes surfaces' contract carries `gaps` only with it."""

    paths, repository, ctx, goal_id, corpus, lines = _linked(
        tmp_path, monkeypatch, config="[learner_text_gaps]\nenabled = false\n")
    assert _jobs(repository) == []
    assert J.sweep_backlog(load_vault(paths.root), repository) == {kind: 0 for kind in J.BACKLOG_KINDS}
    assert call(ctx, "reader.prompt_contract", {})["notes"]["gaps"] is True


# -- only linked notes, keyed to what they are linked to ---------------------------------------------

def test_only_linked_notes_are_queued_with_their_snapshot_and_their_topics(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    assert set(snapshots) == {TYPED, CAPTURED}  # only linked notes are stored (C2)
    queued = {row[0] for row in _jobs(repository)}
    assert queued == set(snapshots.values())  # the link run queued exactly the linked notes' snapshots
    assert J.enqueue_learner_notes(load_vault(paths.root), repository) == 0  # idempotent
    text = learner_text(load_vault(paths.root), repository, "learner_note", snapshots[TYPED])
    assert text is not None and text.source_kind == "learner_note" and text.context_judge == "gap_reader"
    assert SENTINEL in text.text and "Av = lv" in text.text  # the snapshot's text
    assert text.anchor_learning_object_ids == ("lo_eigen",) and text.subject_id == "linear-algebra"
    assert text.attempt_id is None and text.practice_item_id is None
    assert [lo["title"] for lo in text.context["learning_objects"]] == ["Eigenvalues"]
    assert text.context["passages"] and text.context["passages"][0]["lead"]  # the linked section, protection read
    captured = learner_text(load_vault(paths.root), repository, "learner_note", snapshots[CAPTURED])
    assert captured is not None and "2x2 eigen example" in captured.text and "handwritten" not in captured.context["note"]


def test_a_changed_note_is_read_with_its_current_snapshot_and_the_old_one_is_not(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    old = _snapshots(repository)[TYPED]
    edit_annotation(repository, corpus[TYPED].split(":", 1)[1], "Eigenvalues again: Av = lv, now with a picture.")
    call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})
    new = _snapshots(repository)[TYPED]
    assert new != old and new in {row[0] for row in _jobs(repository)}  # the new snapshot is queued
    vault = load_vault(paths.root)
    assert learner_text(vault, repository, "learner_note", old) is None  # no longer the linked text
    assert "now with a picture" in learner_text(vault, repository, "learner_note", new).text


# -- a hidden link never feeds gaps ------------------------------------------------------------------

def test_a_hidden_link_is_never_read_and_undo_queues_it_again(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    typed = _typed_line(lines)
    hidden = call(ctx, "notes.decide", {"link_id": typed["linkId"], "choice": "hide"})
    vault = load_vault(paths.root)
    assert learner_text(vault, repository, "learner_note", snapshots[TYPED]) is None
    llm = PlanGapFake(reading=LearnerGap(kind="none"))
    outcome = _run(paths, repository, _clients(llm), source=("learner_note", snapshots[TYPED]))
    assert outcome.state == "skipped"
    with repository.connection() as connection:
        assert connection.execute("SELECT last_error FROM learner_text_gap_jobs WHERE source_id = ?",
                                  (snapshots[TYPED],)).fetchone()[0] == "nothing to read"
    assert all(SENTINEL not in json.dumps(payload) for payload in _readings(llm))  # never sent
    assert _gaps(repository) == []
    # The other note still feeds gaps.
    assert _run(paths, repository, _clients(llm), source=("learner_note", snapshots[CAPTURED])).state == "done"
    # undo (keep): linked again, so its skipped job is queued again and read.
    call(ctx, "notes.decide", {"link_id": hidden["linkId"], "choice": "keep"})
    assert (snapshots[TYPED], "queued") in {row[:2] for row in _jobs(repository)}
    assert _run(paths, repository, _clients(llm), source=("learner_note", snapshots[TYPED])).state == "done"
    assert {gap["source_id"] for gap in _gaps(repository)} == set(snapshots.values())


def test_an_unlinked_note_never_feeds_gaps(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    # The unrelated capture and the exam's annotation were never linked, so never stored or queued.
    with repository.connection() as connection:
        stored = {str(row[0]) for row in connection.execute("SELECT note_key FROM learner_notes")}
    assert corpus["unrelated"] not in stored and corpus["exam"] not in stored
    assert len(_jobs(repository)) == 2
    # An id that is no linked snapshot reads nothing.
    assert learner_text(load_vault(paths.root), repository, "learner_note", "ln_not_a_snapshot") is None


# -- tier 2 only ------------------------------------------------------------------------------------

def test_reading_a_note_is_tier_2_only_and_keeps_its_words_like_any_learner_text(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    vault = load_vault(paths.root)
    los_before = set(vault.learning_objects)
    # A prerequisite the note relies on, matching lo_det: matched, but no edge and no sooner check.
    llm = PlanGapFake(reading=LearnerGap(kind="prerequisite", prerequisite_name="the determinant of a matrix",
                                         prerequisite_line="Uses det(A - lI) without knowing determinants."),
                      decide=word_match("determinant"))
    before = table_counts(repository)
    outcome = _run(paths, repository, _clients(llm), source=("learner_note", snapshots[TYPED]))
    assert outcome.state == "done" and outcome.action == "matched_prerequisite"
    after = table_counts(repository)
    changed = {name for name in after if after[name] != before.get(name)}
    assert changed <= GAP_TABLES, changed
    for table in NEVER_TABLES:
        assert after.get(table, 0) == before.get(table, 0), table
    (gap,) = _gaps(repository)
    assert (gap["source_kind"], gap["source_id"], gap["kind"], gap["target_id"]) == (
        "learner_note", snapshots[TYPED], "prerequisite", "lo_det")
    assert gap["anchor_learning_object_id"] == "lo_eigen" and gap["edge_id"] is None
    assert SENTINEL in gap["learner_text"]  # C2b: the row keeps the note's words (learner text)
    assert gap["chooser"] == load_vault(paths.root).config.learner_text_gaps.chooser
    detail = json.loads(gap["detail_json"])
    assert detail["embedding"] != "never_for_notes" and detail.get("edge") == "not_applicable"
    # Read with its own task and prompt version.
    (reading,) = _readings(llm)
    assert "note the learner wrote in their own notes" in reading["task"] and reading["context"]["surface"] == "learner_note"
    with repository.connection() as connection:
        versions = {row[0] for row in connection.execute(
            "SELECT prompt_version FROM judgment_ledger WHERE left_kind = 'learner_note'")}
        ledger = json.dumps([list(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE left_kind = 'learner_note'")])
        gaps_dump = json.dumps([list(row) for row in connection.execute("SELECT * FROM learner_text_gaps")])
    assert READER_NOTE_PROMPT_VERSION in versions and ledger
    assert SENTINEL in gaps_dump
    # Its words carry a write-time provenance record (its topics), as a formative answer's do.
    with repository.connection() as connection:
        records = [json.dumps([list(row) for row in connection.execute(
            "SELECT * FROM text_write_provenance WHERE kind = 'learner_text_gap'")])]
    assert "lo_eigen" in records[0]
    # An unmatched prerequisite named from a note is never drafted into a new topic.
    unmatched = PlanGapFake(reading=LearnerGap(kind="prerequisite", prerequisite_name="complex roots of polynomials"))
    outcome = _run(paths, repository, _clients(unmatched), source=("learner_note", snapshots[CAPTURED]))
    assert outcome.action == "unmatched_prerequisite"
    assert not [purpose for purpose, _ in unmatched.calls if purpose == "learner_gap_prerequisite_draft"]
    assert set(load_vault(paths.root).learning_objects) == los_before
    second = _gaps(repository)[-1]
    assert json.loads(second["detail_json"])["reason"] == "never_drafted_from_a_note"
    assert table_counts(repository).get("learner_gap_commitments", 0) == before.get("learner_gap_commitments", 0)


def test_a_notes_receipts_keep_the_prompt_like_any_learner_text(tmp_path, monkeypatch):
    """C2b: the withheld receipt input is gone for notes (note text is learner text)."""

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    llm = PlanGapFake(reading=LearnerGap(kind="none"))
    assert _run(paths, repository, _clients(llm), source=("learner_note", snapshots[TYPED])).state == "done"
    with repository.connection() as connection:
        connection.row_factory = None
        names = [column[0] for column in connection.execute("SELECT * FROM model_call_receipts LIMIT 0").description]
        rows = [dict(zip(names, row)) for row in connection.execute(
            "SELECT * FROM model_call_receipts WHERE purpose = 'learner_gap_reading'").fetchall()]
    assert rows and any(row["input_text"] and SENTINEL in row["input_text"] for row in rows)


# -- the ordinary transport: the Decider and the gap routes, like any learner text ------------------

def test_a_note_is_read_on_the_ordinary_routes_with_the_decider(tmp_path, monkeypatch):
    """C2b: no plan-only rule for a note's reading: the gap reader and judge's own routes read
    it (a client that is not the ChatGPT plan), and the Decider is asked."""

    from learnloop.ai import plan_fallback
    from learnloop.diagnosis.text_gaps import contract as C
    from learnloop.diagnosis.text_gaps import pipeline as P

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    reader = GapLLMFake(reading=LearnerGap(kind="prerequisite", prerequisite_name="the determinant of a matrix"),
                        decide=word_match("determinant"))
    decider = ChoiceDecider(kind="prerequisite", pair=word_match("determinant"))
    outcome = _run(paths, repository, _clients(reader, decider=decider), source=("learner_note", snapshots[TYPED]))
    assert outcome.state == "done" and _readings(reader)
    assert decider.states  # the Decider read the note like any learner text
    assert not hasattr(P, "note_reader_client") and not hasattr(C, "NOTE_ROUTE")
    assert "note_link_judge" not in plan_fallback.PLAN_ONLY_TASKS
    planned = J.plan(load_vault(paths.root), repository)
    assert "note_link_judge" not in planned["routes"]


# -- exam material never reaches the gap model through a note's context ------------------------------

def test_gc1_exam_sentinels_never_reach_the_gap_model_via_a_notes_context(tmp_path, monkeypatch):
    """G-C1 for C5, on C3's exam-scope fixture with C2's FAKE tend over synthetic notes. A note's
    own words are the learner's and are sent as such (one synthetic note copies a past-paper
    question); everything else in every gap reading (the topics, the passages' books, sections
    and openings) names no exam material, no held-out section and not the syllabus. A note the
    learner linked by hand to an exam unit is not read at all."""

    from learnloop.diagnosis.text_gaps.sources import SourceWithheld
    from learnloop.source_retrieval import deliverable_path as DP
    from learnloop.source_retrieval import deliverables as DL
    from learnloop.source_retrieval import section_coverage as SC
    from tests.deliverable_fixtures import DeliverableFake
    from tests.exam_scope_fixtures import NEVER_ON_A_PATH, PAPER, SPANS, SYLLABUS_MARKER, build_exam_scope_vault
    from tests.notes_fixtures import NoteLinkFake, add_capture
    from tests.section_coverage_fixtures import CoverageJudgeFake
    from tests.test_curriculum_c3_exam_scoping import ALL_LOS, _clean
    from tests.test_curriculum_c3_exam_scoping import _deliverable as exam_deliverable

    quoted = PAPER["paper_q1"][1][0][0]
    paths, repository = build_exam_scope_vault(tmp_path / "vault", config=GAPS_ON)
    add_capture(repository, "Eigenvalues: det(A - lI) = 0, worked by hand.")
    add_capture(repository, "Determinants flip sign when rows swap.")
    add_capture(repository, f"Copied from the midterm (determinants, eigenvalues, matrix): I copied this: {quoted}")
    hand = add_capture(repository, "Rank practice: my try at the exam practice rank question.")
    vault = load_vault(paths.root)
    judge = CoverageJudgeFake()
    for lo_id in ALL_LOS:
        SC.judge(vault, repository, lo_id, client=judge)
    goal_id, vault = exam_deliverable(paths, repository, "eigenvalues, determinants, matrix computations, spectral")
    DL.add_input(vault, repository, goal_id, "passage", extraction_id="ext_syl", span_ids=[SPANS["syl_main"]])
    assert DL.resolve(load_vault(paths.root), repository, goal_id, client=DeliverableFake()).status == "ready"
    DL.add_input(load_vault(paths.root), repository, goal_id, "depth", text="learn_to_use_it")
    DP.judge(load_vault(paths.root), repository, goal_id, client=DeliverableFake())
    run = NL.link_goal(load_vault(paths.root), repository, goal_id,
                       client=NoteLinkFake(discusses=("det(A - lI)", "flip sign", "I copied this")))
    assert run.status == "done", run
    # The learner links a note by hand to the exam unit inside the mixed textbook.
    NL.link_by_hand(load_vault(paths.root), repository, hit={"note_key": f"capture:{hand}"},
                    extraction_id="ext_mixed", span_id=SPANS["mixed_exam"])
    vault = load_vault(paths.root)
    assert J.enqueue_learner_notes(vault, repository) >= 3
    with repository.connection() as connection:
        (held_id,) = [str(row[0]) for row in connection.execute(
            "SELECT id FROM learner_notes WHERE note_key = ?", (f"capture:{hand}",))]
    with pytest.raises(SourceWithheld):
        learner_text(vault, repository, "learner_note", held_id)
    # The note reading's request gate refuses it too (Codex review F3: protection read now).
    from learnloop.diagnosis.text_gaps.sources import learner_note_refusal

    assert learner_note_refusal(vault, repository, held_id) == "the note is linked to protected material"
    llm = PlanGapFake(reading=LearnerGap(kind="none"))
    outcomes = J.run_pending(paths.root, repository, owner="t", clients=_clients(llm), clock=CLOCK)
    assert {o.state for o in outcomes} <= {"done", "skipped"}
    held = next(o for o in outcomes if o.source_id == held_id)
    assert held.state == "skipped"
    with repository.connection() as connection:
        assert connection.execute("SELECT last_error FROM learner_text_gap_jobs WHERE source_id = ?",
                                  (held_id,)).fetchone()[0].startswith("held out")
    readings = _readings(llm)
    assert len(readings) >= 3  # every other linked note was read: the sweep is not vacuous
    copied_sent = 0
    for payload in readings:
        own = payload["context"]["learner_text"]
        assert "my try at the exam practice rank question" not in own  # the held-out note is never sent
        copied_sent += quoted in own
        rest = json.dumps({key: value for key, value in payload["context"].items() if key != "learner_text"})
        _clean(rest)
        _clean(payload["task"])
        assert SYLLABUS_MARKER not in rest
        for extraction_id in NEVER_ON_A_PATH:
            assert extraction_id not in rest
        if quoted not in own:
            _clean(own)
    assert copied_sent == 1  # only the note that copied it carries the quote, in its own words


# -- the opt-in from Settings, and the queue at a vault's open ----------------------------------------

def test_settings_opt_in_writes_the_switch_queues_the_linked_notes_and_off_reads_none(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers.notes import GAPS_LINE

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch, gaps=False)
    assert _jobs(repository) == [] and "gaps" not in call(ctx, "reader.prompt_contract", {})["notes"]
    out = call(ctx, "notes.set_gaps", {"enabled": True})
    assert out["gapsEnabled"] is True and out["line"] == GAPS_LINE
    assert "only ever steers what to suggest, never grades you" in GAPS_LINE
    assert load_vault(paths.root).config.notes.gaps_enabled is True
    assert call(ctx, "reader.prompt_contract", {})["notes"]["gaps"] is True
    assert {row[0] for row in _jobs(repository)} == set(_snapshots(repository).values())
    # Off again: the contract is C2's, and a queued note job is skipped unread.
    ctx.post_attempt_worker.autostart = False
    assert call(ctx, "notes.set_gaps", {"enabled": False})["gapsEnabled"] is False
    assert "gaps" not in call(ctx, "reader.prompt_contract", {})["notes"]
    llm = PlanGapFake()
    assert _run(paths, repository, _clients(llm)).state == "skipped" and llm.calls == []


def test_a_vault_opened_with_the_opt_in_on_queues_its_linked_notes(tmp_path, monkeypatch):
    from learnloop.ops.settings_store import apply_config_updates
    from tests.reading_path_fixtures import context

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch, gaps=False)
    assert _jobs(repository) == []
    apply_config_updates(paths.root / "learnloop.toml", {("notes", "gaps_enabled"): True})
    reopened = context(paths.root)
    reopened.post_attempt_worker.autostart = False
    try:
        assert {row[0] for row in _jobs(repository)} == set(_snapshots(repository).values())
    finally:
        reopened.close()


# -- Codex review (C5) fixes -------------------------------------------------------------------------

class PhysicalPlanFake(PlanGapFake):
    """The plan's gap model whose every answer is one PHYSICAL request (a real plan client's
    shape): admitted through the context's request gate before anything is sent."""

    def complete(self, request):
        from learnloop.ai.execution import model_call

        with model_call(self, purpose=request.purpose, prompt=request.prompt):
            return super().complete(request)


class PlanOutageFake(PhysicalPlanFake):
    """The plan resolves as ready, then its inference reports the usage limit reached."""

    def __init__(self, *, down: set[str], **kwargs):
        super().__init__(**kwargs)
        self.down = set(down)

    def complete(self, request):
        from learnloop.ai.chatgpt_plan.session import ChatGPTPlanUsageExhausted

        if request.purpose in self.down:
            self.calls.append((request.purpose, {}))
            raise ChatGPTPlanUsageExhausted("usage limit reached; plan requests are paused")
        return super().complete(request)


def _ordinary_text(source_id: str = "stuck-ordinary"):
    from learnloop.diagnosis.text_gaps.contract import LearnerText

    return LearnerText(source_kind="stuck_answer", source_id=source_id, text="I think eigenvalues are always positive",
                       context_judge="gap_reader", created_at=NOW, subject_id="linear-algebra",
                       anchor_learning_object_ids=("lo_eigen",))


def _clear_backoff(repository, source_id: str) -> None:
    with repository.atomic():
        repository.connection().execute("UPDATE learner_text_gap_jobs SET not_before = NULL WHERE source_id = ?",
                                        (source_id,))


def test_c2b_a_notes_belief_is_handled_like_any_learner_texts(tmp_path, monkeypatch):
    """C2b drops C5's Codex F1 rule (a note's belief never a holding-pen candidate, its words
    never kept): the gap row keeps the named belief, and no ``never_a_candidate_from_a_note``
    refusal is recorded."""

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    belief = "Every matrix has real eigenvalues"
    plan = PlanGapFake(reading=LearnerGap(kind="misconception", belief_statement=belief))
    outcome = _run(paths, repository, _clients(plan), source=("learner_note", snapshots[TYPED]))
    assert outcome.state == "done"
    (gap,) = _gaps(repository)
    assert belief in gap["named_json"]
    assert json.loads(gap["detail_json"]).get("reason") != "never_a_candidate_from_a_note"


def test_c2b_a_reader_note_written_beside_material_protected_since_is_never_read(tmp_path, monkeypatch):
    """C2b: a linked Reader note whose own anchor became protected material after it was
    linked (its book marked exam, say) is not read for gaps: the reading is refused and the
    request gate refuses it too."""

    from learnloop.diagnosis.text_gaps.sources import SourceWithheld, learner_note_refusal
    from learnloop.source_retrieval import note_gaps
    from learnloop.source_retrieval import vault_notes as VN

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    vault = load_vault(paths.root)
    assert learner_text(vault, repository, "learner_note", snapshots[TYPED]) is not None
    real = VN.beside_protected
    monkeypatch.setattr(note_gaps.VN, "beside_protected",
                        lambda vault, repository, key: key == corpus[TYPED] or real(vault, repository, key))
    with pytest.raises(SourceWithheld):
        learner_text(vault, repository, "learner_note", snapshots[TYPED])
    assert learner_note_refusal(vault, repository, snapshots[TYPED]) == note_gaps.PROTECTED
    llm = PlanGapFake(reading=LearnerGap(kind="none"))
    outcome = _run(paths, repository, _clients(llm), source=("learner_note", snapshots[TYPED]))
    assert outcome.state == "skipped" and _readings(llm) == []
    # A capture holds no book text: it is read.
    assert learner_text(vault, repository, "learner_note", snapshots[CAPTURED]) is not None


def test_f3_revoking_consent_before_dispatch_sends_nothing(tmp_path, monkeypatch):
    """Codex review F3: the text is built, then the learner turns the opt-in off before the
    first request: the request gate refuses it, nothing is sent or logged, the job is skipped."""

    from learnloop.ops.settings_store import apply_config_updates

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    original = J.learner_text

    def built_then_switched_off(*args, **kwargs):
        text = original(*args, **kwargs)
        apply_config_updates(paths.root / "learnloop.toml", {("notes", "gaps_enabled"): False})
        return text

    monkeypatch.setattr(J, "learner_text", built_then_switched_off)
    plan = PhysicalPlanFake(reading=LearnerGap(kind="none"))
    outcome = _run(paths, repository, _clients(plan), source=("learner_note", snapshots[TYPED]))
    assert outcome.state == "skipped" and plan.calls == [] and _gaps(repository) == []
    # The same with the notes switched off altogether.
    monkeypatch.setattr(J, "learner_text", original)
    apply_config_updates(paths.root / "learnloop.toml", {("notes", "gaps_enabled"): True})

    def built_then_notes_off(*args, **kwargs):
        text = original(*args, **kwargs)
        apply_config_updates(paths.root / "learnloop.toml", {("notes", "enabled"): False})
        return text

    monkeypatch.setattr(J, "learner_text", built_then_notes_off)
    outcome = _run(paths, repository, _clients(plan), source=("learner_note", snapshots[CAPTURED]))
    assert outcome.state == "skipped" and plan.calls == [] and _gaps(repository) == []


def test_f3_hiding_the_link_between_requests_stops_the_reading_and_writes_nothing(tmp_path, monkeypatch):
    """Codex review F3: the learner hides the link after the reading request: the pair
    verdicts are never sent and no gap row is written; *undo* queues it again."""

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    typed = _typed_line(lines)
    hidden: dict = {}

    class HidesAfterReading(PhysicalPlanFake):
        def complete(self, request):
            result = super().complete(request)
            if request.purpose == "learner_gap_reading":
                hidden.update(call(ctx, "notes.decide", {"link_id": typed["linkId"], "choice": "hide"}))
            return result

    plan = HidesAfterReading(reading=LearnerGap(kind="prerequisite", prerequisite_name="the determinant of a matrix"),
                             decide=word_match("determinant"))
    outcome = _run(paths, repository, _clients(plan), source=("learner_note", snapshots[TYPED]))
    assert outcome.state == "skipped"
    assert [purpose for purpose, _ in plan.calls] == ["learner_gap_reading"]  # no pair verdict was sent
    assert _gaps(repository) == []
    call(ctx, "notes.decide", {"link_id": hidden["linkId"], "choice": "keep"})
    assert (snapshots[TYPED], "queued") in {row[:2] for row in _jobs(repository)}


def test_f3_switched_off_before_the_final_write_writes_nothing(tmp_path, monkeypatch):
    """Codex review F3: the opt-in turned off after the last request: the gap row is not written."""

    from learnloop.ops.settings_store import apply_config_updates

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)

    class OffAfterReading(PhysicalPlanFake):
        def complete(self, request):
            result = super().complete(request)
            apply_config_updates(paths.root / "learnloop.toml", {("notes", "gaps_enabled"): False})
            return result

    plan = OffAfterReading(reading=LearnerGap(kind="none"))
    outcome = _run(paths, repository, _clients(plan), source=("learner_note", snapshots[TYPED]))
    assert outcome.state == "skipped" and _gaps(repository) == []


def test_c2b_a_note_and_an_ordinary_gap_share_the_gap_readers_route(tmp_path, monkeypatch):
    """C2b: one command budget across a note and an ordinary gap: both are read on the gap
    reader's own route (metered, charged), never a separate notes route."""

    from learnloop.ai.spend import SpendCaps
    from learnloop.diagnosis.offline_review.spend import ReviewSpend
    from learnloop.diagnosis.text_gaps import pipeline as P
    from learnloop.diagnosis.text_gaps.judges import TextBudget

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    vault = load_vault(paths.root)
    caps = SpendCaps(max_candidates=100, max_pairs=100, max_retries=10, max_calls=100, max_total_tokens=2_000_000,
                     max_estimated_usd=1.0)
    shared = TextBudget.for_command(ReviewSpend(caps, price_per_million=1.0, config=vault.config))
    metered = MeteredGapFake(reading=LearnerGap(kind="none"))
    note_text = learner_text(vault, repository, "learner_note", snapshots[TYPED])
    P.process_learner_text(paths.root, repository, note_text, clients=PipelineClients(judge=lambda: metered,
                           reader=lambda: metered), budget=shared, clock=CLOCK)
    P.process_learner_text(paths.root, repository, _ordinary_text(),
                           clients=PipelineClients(judge=lambda: metered, reader=lambda: metered),
                           budget=shared, clock=CLOCK)
    routes = shared.spend.routes
    assert set(routes) <= {"learner_gap_reader", "learner_gap_judge"} and routes["learner_gap_reader"].billing == "metered"
    assert len(_readings(metered)) == 2
    assert (shared.spend.estimated_usd.get("learner_gap_reader") or 0.0) > 0.0


# -- Codex re-review (C5) fixes ----------------------------------------------------------------------

PROTECTED_PASSAGE = ("ext_book", "ch_eigen", "s1")
SAME_LEAD_PASSAGE = ("ext_book", "ch_eigen", "s2")


@pytest.mark.parametrize("change", ["link_removed", "same_lead_elsewhere"])
def test_f3_rereview_the_gate_is_bound_to_the_prepared_passages(tmp_path, monkeypatch, change):
    """Codex re-review F3: the text is prepared with its linked passage's opening, then that
    passage becomes protected and its link goes, while the note stays linked (by its topic;
    or, second case, to another passage whose opening reads the same). The gate revalidates
    the passages the prepared request was BUILT from, and the payload itself, before every
    request and the write: nothing is sent, nothing written, the job is skipped (queued
    again, rebuilt from its links as they are then, by the next sweep)."""

    from learnloop.source_retrieval import note_gaps

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    typed_id = snapshots[TYPED]
    original_text, original_linked, original_lead = J.learner_text, note_gaps.linked_notes, note_gaps._section_lead
    prepared: dict = {}
    changed = {"now": False}

    def linked_now(vault, repository):
        out = original_linked(vault, repository)
        if not changed["now"]:
            return out
        moved = () if change == "link_removed" else (SAME_LEAD_PASSAGE,)
        return [note_gaps.LinkedNote(note_id=entry.note_id, note_key=entry.note_key,
                                     learning_object_ids=entry.learning_object_ids, passages=moved, note=entry.note)
                if entry.note_id == typed_id else entry for entry in out]

    opening: dict = {}

    def lead_now(vault, repository, library, passage):
        passage = tuple(passage)
        if passage == SAME_LEAD_PASSAGE:
            return opening["s1"]  # another passage whose opening reads the same
        if passage == PROTECTED_PASSAGE and changed["now"]:
            raise note_gaps.NoteWithheld("linked to protected material")
        found = original_lead(vault, repository, library, passage)
        if passage == PROTECTED_PASSAGE:
            opening["s1"] = found
        return found

    def prepared_then_changed(*args, **kwargs):
        text = original_text(*args, **kwargs)
        prepared["passages"] = list(text.context.get("passages") or [])
        assert prepared["passages"], "the prepared request carries the passage's opening"
        changed["now"] = True
        return text

    monkeypatch.setattr(note_gaps, "linked_notes", linked_now)
    monkeypatch.setattr(note_gaps, "_section_lead", lead_now)
    monkeypatch.setattr(J, "learner_text", prepared_then_changed)
    vault = load_vault(paths.root)
    assert note_gaps.refusal(vault, repository, typed_id) is None  # unchanged yet: readable
    plan = PhysicalPlanFake(reading=LearnerGap(kind="none"))
    outcome = _run(paths, repository, _clients(plan), source=("learner_note", typed_id))
    # Whatever links stand now, the prepared request held the protected passage: not sent.
    current = note_gaps.note_text(load_vault(paths.root), repository, typed_id)
    assert current is not None  # the note is still linked: a check of the CURRENT links alone admits it
    assert (current["context"].get("passages") or []) == ([] if change == "link_removed" else prepared["passages"])
    assert outcome.state == "skipped" and plan.calls == [] and _gaps(repository) == []
    with repository.connection() as connection:
        error = connection.execute("SELECT last_error FROM learner_text_gap_jobs WHERE source_id = ?",
                                   (typed_id,)).fetchone()[0]
    assert error.startswith("stopped:")


def test_f3_rereview_a_payload_changed_after_preparation_is_not_sent(tmp_path, monkeypatch):
    """Codex re-review F3: a topic linked after the text was prepared changes what the request
    would carry: the prepared request is stale, so the reading stops before sending it."""

    from learnloop.source_retrieval import note_gaps

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    typed_id = _snapshots(repository)[TYPED]
    original_text, original_linked = J.learner_text, note_gaps.linked_notes
    changed = {"now": False}

    def linked_now(vault, repository):
        out = original_linked(vault, repository)
        if not changed["now"]:
            return out
        return [note_gaps.LinkedNote(note_id=entry.note_id, note_key=entry.note_key,
                                     learning_object_ids=entry.learning_object_ids + ("lo_det",),
                                     passages=entry.passages, note=entry.note)
                if entry.note_id == typed_id else entry for entry in out]

    def prepared_then_changed(*args, **kwargs):
        text = original_text(*args, **kwargs)
        changed["now"] = True
        return text

    monkeypatch.setattr(note_gaps, "linked_notes", linked_now)
    monkeypatch.setattr(J, "learner_text", prepared_then_changed)
    plan = PhysicalPlanFake(reading=LearnerGap(kind="none"))
    outcome = _run(paths, repository, _clients(plan), source=("learner_note", typed_id))
    assert outcome.state == "skipped" and plan.calls == [] and _gaps(repository) == []
    # The next run prepares it again from its links as they are now, and reads it.
    monkeypatch.setattr(J, "learner_text", original_text)
    J.enqueue_learner_notes(load_vault(paths.root), repository)
    outcome = _run(paths, repository, _clients(plan), source=("learner_note", typed_id))
    assert outcome.state == "done" and len(_readings(plan)) == 1


def test_f6_hidden_before_pair_dispatch_then_undo_resumes_without_an_abandoned_claim(tmp_path, monkeypatch):
    """Codex re-review F6: the learner hides the link after the reading, so the gate refuses
    the pair request after its work claim was taken. The claim is released as the stop
    unwinds (no lease left behind); after *undo* the note is read to the end, its pair
    verdict sent once, never ``claimed_elsewhere`` until it fails."""

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    source = ("learner_note", snapshots[TYPED])
    typed = _typed_line(lines)
    hidden: dict = {}

    class HidesAfterReading(PhysicalPlanFake):
        def complete(self, request):
            result = super().complete(request)
            if request.purpose == "learner_gap_reading" and not hidden:
                hidden.update(call(ctx, "notes.decide", {"link_id": typed["linkId"], "choice": "hide"}))
            return result

    reading = LearnerGap(kind="prerequisite", prerequisite_name="the determinant of a matrix")
    plan = HidesAfterReading(reading=reading, decide=word_match("determinant"))
    outcome = _run(paths, repository, _clients(plan), source=source)
    assert outcome.state == "skipped"
    with repository.connection() as connection:
        leased = connection.execute("SELECT COUNT(*) FROM judgment_work_claims WHERE state = 'leased'").fetchone()[0]
    assert leased == 0  # the pair's claim was released as the stop unwound
    call(ctx, "notes.decide", {"link_id": hidden["linkId"], "choice": "keep"})
    again = PhysicalPlanFake(reading=reading, decide=word_match("determinant"))
    outcome = _run(paths, repository, _clients(again), source=source)
    assert outcome.state == "done", (outcome.state, outcome.error)
    assert any(purpose == "learner_gap_same_prerequisite" for purpose, _ in again.calls)
    assert len(_gaps(repository)) == 1


# -- landing step 0: note jobs never reuse a checkpointed reading or decision ------------------------

#: A synthetic sentinel in the protected passage's opening (never a real book's words).
PASSAGE_SENTINEL = "PASSAGE-SENTINEL-c5-L0"


class PromptRecordingPlanFake(PhysicalPlanFake):
    """The plan's gap model that keeps every physical request's whole prompt."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prompts: list[tuple[str, str]] = []

    def complete(self, request):
        self.prompts.append((request.purpose, str(request.prompt)))
        return super().complete(request)


class PairsDownPlanFake(PlanOutageFake):
    """The plan reads the note, then its pair verdicts hit the usage limit (the job is
    released, waiting for the plan, with whatever it checkpointed)."""

    def __init__(self, **kwargs):
        super().__init__(down={"learner_gap_same_prerequisite"}, **kwargs)


def _payload_of(repository, source_id: str) -> dict:
    with repository.connection() as connection:
        raw = connection.execute("SELECT payload_json FROM learner_text_gap_jobs WHERE source_id = ?",
                                 (source_id,)).fetchone()[0]
    return json.loads(raw) if raw else {}


def _set_payload(repository, source_id: str, payload: dict, *, state: str | None = None) -> None:
    with repository.atomic():
        repository.connection().execute(
            "UPDATE learner_text_gap_jobs SET payload_json = ?, state = COALESCE(?, state), not_before = NULL "
            "WHERE source_id = ?", (json.dumps(payload), state, source_id))


def _protected_passage_changes(monkeypatch, typed_id: str):
    """The typed note is linked to PROTECTED_PASSAGE (its opening carries PASSAGE_SENTINEL) and
    to its topic. ``change()`` makes that passage protected and removes its link, while the
    note stays linked by its topic."""

    from learnloop.source_retrieval import note_gaps

    original_linked, original_lead = note_gaps.linked_notes, note_gaps._section_lead
    changed = {"now": False}

    def linked_now(vault, repository):
        out = original_linked(vault, repository)
        if not changed["now"]:
            return out
        return [note_gaps.LinkedNote(note_id=entry.note_id, note_key=entry.note_key,
                                     learning_object_ids=entry.learning_object_ids, passages=(), note=entry.note)
                if entry.note_id == typed_id else entry for entry in out]

    def lead_now(vault, repository, library, passage):
        if tuple(passage) == PROTECTED_PASSAGE:
            if changed["now"]:
                raise note_gaps.NoteWithheld("linked to protected material")
            return f"{original_lead(vault, repository, library, passage)} {PASSAGE_SENTINEL}"
        return original_lead(vault, repository, library, passage)

    monkeypatch.setattr(note_gaps, "linked_notes", linked_now)
    monkeypatch.setattr(note_gaps, "_section_lead", lead_now)
    return lambda: changed.update(now=True)


def test_step0_a_checkpointed_note_reading_is_never_reused_after_its_inputs_change(tmp_path, monkeypatch):
    """Codex re-review F3, third reopening (job 20261101-190354-nKrEQg): the note is read with
    its linked passage's opening (the plan's model echoes that passage's sentinel into the
    prerequisite it names), and the pair verdicts wait for the plan. The passage then becomes
    protected and its link goes, while the note stays linked by its topic. The retry must not
    reuse the earlier reading or decision: it is prepared again from the current links and read
    again by a fresh plan call, so no pair request carries the protected passage's sentinel.
    The plan's reading of a note is never written to the job's checkpoint at all."""

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    typed_id = _snapshots(repository)[TYPED]
    source = ("learner_note", typed_id)
    change = _protected_passage_changes(monkeypatch, typed_id)
    first_text = learner_text(load_vault(paths.root), repository, *source)
    assert PASSAGE_SENTINEL in json.dumps(first_text.context)  # read with the passage's opening

    echoed = LearnerGap(kind="prerequisite", prerequisite_name=f"the determinant of a matrix {PASSAGE_SENTINEL}")
    first = PairsDownPlanFake(reading=echoed, decide=word_match("determinant"))
    outcome = _run(paths, repository, _clients(first), source=source)
    assert outcome.state == "retry_later"  # the pair verdicts failed: retried later (C2b: no plan wait)
    assert len(_readings(first)) == 1
    payload = _payload_of(repository, typed_id)
    assert "reading" not in payload and "decided" not in payload, payload
    assert PASSAGE_SENTINEL not in json.dumps(payload)

    change()
    _clear_backoff(repository, typed_id)
    again = PromptRecordingPlanFake(reading=LearnerGap(kind="prerequisite",
                                                       prerequisite_name="the determinant of a matrix"),
                                    decide=word_match("determinant"))
    outcome = _run(paths, repository, _clients(again), source=source)
    for purpose, prompt in again.prompts:
        assert PASSAGE_SENTINEL not in prompt, purpose  # the reproduction: a pair request carried it
    assert outcome.state == "done", (outcome.state, outcome.error)
    assert len(_readings(again)) == 1  # read again, by a fresh (unmetered) plan call
    assert any(purpose == "learner_gap_same_prerequisite" for purpose, _ in again.prompts)
    assert PASSAGE_SENTINEL not in json.dumps(_gaps(repository), default=str)
    assert PASSAGE_SENTINEL not in json.dumps(_payload_of(repository, typed_id))


@pytest.mark.parametrize("state", ["queued", "skipped"])
def test_step0_a_legacy_checkpointed_note_reading_is_cleared_on_requeue_and_ignored_on_retry(
        tmp_path, monkeypatch, state):
    """A note job checkpointed before step 0 (its payload holds the plan's reading and decision,
    echoing the protected passage): a requeue of a skipped job clears both fields, and a retry
    of a queued job ignores them, re-preparing from the current links and reading afresh."""

    paths, repository, ctx, goal_id, corpus, lines = _linked(tmp_path, monkeypatch)
    typed_id = _snapshots(repository)[TYPED]
    source = ("learner_note", typed_id)
    change = _protected_passage_changes(monkeypatch, typed_id)
    stale = {"name": f"the determinant of a matrix {PASSAGE_SENTINEL}"}
    J.enqueue_learner_notes(load_vault(paths.root), repository)
    legacy = {"reading": {"kind": "prerequisite", "status": "ok", "judge": "llm",
                          "prerequisite_name": stale["name"], "prompt_version": READER_NOTE_PROMPT_VERSION},
              "decided": {"reading": {"kind": "prerequisite", "status": "ok", "judge": "llm",
                                      "prerequisite_name": stale["name"],
                                      "prompt_version": READER_NOTE_PROMPT_VERSION},
                          "decider": {"status": "disabled"}, "chooser": "context_model", "kind": "prerequisite"}}
    _set_payload(repository, typed_id, legacy, state=state)
    change()
    if state == "skipped":
        assert J.enqueue_learner_notes(load_vault(paths.root), repository) == 1
        payload = _payload_of(repository, typed_id)
        assert "reading" not in payload and "decided" not in payload, payload
        _set_payload(repository, typed_id, {**payload, **legacy})  # and a retry ignores them all the same
    again = PromptRecordingPlanFake(reading=LearnerGap(kind="prerequisite",
                                                       prerequisite_name="the determinant of a matrix"),
                                    decide=word_match("determinant"))
    outcome = _run(paths, repository, _clients(again), source=source)
    for purpose, prompt in again.prompts:
        assert PASSAGE_SENTINEL not in prompt, purpose
    assert outcome.state == "done", (outcome.state, outcome.error)
    assert len(_readings(again)) == 1
    payload = _payload_of(repository, typed_id)
    assert "reading" not in payload and "decided" not in payload, payload
