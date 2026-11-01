"""Curriculum C5: notes as learner text (spec_deliverable_curriculum_v1 §10.2, §10.4, §12 C5).

With the learner's opt-in (``notes.gaps_enabled``, default off; owner Q9) a LINKED note is a
tier-2 learner-text-gaps input (``source_kind = 'learner_note'``), keyed to the topics and
passages it is linked to, read with its snapshot's text on the ChatGPT plan only. A hidden
link or an unlinked note never feeds gaps; switched off the gaps code reads no note row.

Every tend here is C2's FAKE executable (tests/notes_fixtures.py) over synthetic notes in tmp:
the owner's real tend and notes are never reached. Every model is a fake; background work
runs inline and the post-attempt worker never starts a thread (jobs are run by hand).
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
from tests.notes_fixtures import SENTINEL
from tests.reading_path_fixtures import call
from tests.section_coverage_fixtures import table_counts
from tests.test_notes_linked import _deliverable, _lines
from tests.text_gap_fakes import ChoiceDecider, GapLLMFake, always, word_match

CLOCK = FrozenClock(NOW)
GAPS_ON = "[notes]\ngaps_enabled = true\n"
#: What reading a note may write: gap rows, their jobs, ledger verdicts, receipts and
#: work claims (the holding pen only for a belief, not exercised here).
GAP_TABLES = {"learner_text_gaps", "learner_text_gap_jobs", "judgment_ledger", "model_call_receipts",
              "judgment_work_claims", "model_call_spend"}
#: Evidence, mastery, grading, scheduling and claims: never written by a note's reading.
NEVER_TABLES = ("practice_attempts", "grading_evidence", "facet_recall_state", "facet_capability_evidence",
                "probe_observations", "fsrs_states", "learner_claims", "learner_gap_check_advances",
                "learner_gap_commitments", "text_write_provenance", "self_reports")


class PlanGapFake(GapLLMFake):
    """The gap reader and judge on the ChatGPT plan (the only client a note may reach)."""

    provider_name = "fake_plan_gap"
    provider_type = "chatgpt_plan"
    model = "fake/plan-gap"


class MeteredGapFake(GapLLMFake):
    provider_name = "fake_metered_gap"
    provider_type = "openrouter"
    model = "fake/metered-gap"


def _linked(tmp_path: Path, monkeypatch, *, gaps: bool = True, config: str = ""):
    """C2's deliverable vault with the path's two notes linked (the typed one carries
    ``SENTINEL``; the other is a Pocket Notes page), and the opt-in on (or off)."""

    paths, repository, ctx, goal_id, fake_tend, corpus, notes = _deliverable(
        tmp_path, monkeypatch, config=(GAPS_ON if gaps else "") + config)
    ctx.post_attempt_worker.autostart = False  # jobs are run by hand here
    lines = _lines(call(ctx, "notes.path", {"goal_id": goal_id}))
    assert {line["note"]["heading"] for line in lines} == {"Eigen stuff", "Eigen page"}
    return paths, repository, ctx, goal_id, fake_tend, lines


def _snapshots(repository) -> dict[str, str]:
    with repository.connection() as connection:
        return {str(row[1]): str(row[0]) for row in connection.execute("SELECT id, heading FROM learner_notes")}


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
                           drafter=lambda: llm, tutor=None, embedder=None, note_reader=lambda: llm)


def _run(paths, repository, clients, *, source: tuple[str, str] | None = None):
    return J.process_next_gap_job(paths.root, repository, owner="t", clients=clients, clock=CLOCK, source=source)


def _readings(llm) -> list[dict]:
    return [payload for purpose, payload in llm.calls if purpose == "learner_gap_reading"]


# -- the contract and the kinds --------------------------------------------------------------------

def test_learner_note_is_a_readable_tier_2_kind_read_on_the_plan_only():
    assert "learner_note" in SOURCE_KINDS and "learner_note" in READABLE_SOURCE_KINDS
    assert "learner_note" in NON_SERVING_SOURCE_KINDS  # never a sooner check or a placement observation
    assert NOTE_SOURCE_KINDS == ("learner_note",)
    assert load_vault  # (imported for the tests below)


# -- switched off: today's, byte for byte, and no note row read --------------------------------------

def test_switched_off_the_gaps_code_reads_no_note_row_and_queues_nothing(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch, gaps=False)
    vault = load_vault(paths.root)
    assert vault.config.notes.gaps_enabled is False  # the default: off
    assert _jobs(repository) == []  # the link run queued nothing
    contract = call(ctx, "reader.prompt_contract", {})
    assert contract["notes"] == {"enabled": True, "lexicalOnly": False, "pocketNotesLabel": NL.POCKET_NOTES_LABEL,
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
    typed = next(line for line in lines if line["note"]["heading"] == "Eigen stuff")
    hidden = call(ctx, "notes.decide", {"link_id": typed["linkId"], "choice": "hide"})
    call(ctx, "notes.decide", {"link_id": hidden["linkId"], "choice": "keep"})
    assert [row for row in _jobs(repository) if row[0] != snapshot_id] == []


def test_switched_off_the_pipeline_and_the_reader_are_todays(tmp_path, monkeypatch):
    """The learner_text_gaps switch also holds: with the pipeline off nothing is queued
    even with the opt-in on, and the notes surfaces' contract carries `gaps` only with it."""

    paths, repository, ctx, goal_id, fake_tend, lines = _linked(
        tmp_path, monkeypatch, config="[learner_text_gaps]\nenabled = false\n")
    assert _jobs(repository) == []
    assert J.sweep_backlog(load_vault(paths.root), repository) == {kind: 0 for kind in J.BACKLOG_KINDS}
    assert call(ctx, "reader.prompt_contract", {})["notes"]["gaps"] is True


# -- only linked notes, keyed to what they are linked to ---------------------------------------------

def test_only_linked_notes_are_queued_with_their_snapshot_and_their_topics(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    assert set(snapshots) == {"Eigen stuff", "Eigen page"}  # only linked notes are stored (C2)
    queued = {row[0] for row in _jobs(repository)}
    assert queued == set(snapshots.values())  # the link run queued exactly the linked notes' snapshots
    assert J.enqueue_learner_notes(load_vault(paths.root), repository) == 0  # idempotent
    text = learner_text(load_vault(paths.root), repository, "learner_note", snapshots["Eigen stuff"])
    assert text is not None and text.source_kind == "learner_note" and text.context_judge == "gap_reader"
    assert SENTINEL in text.text and "Av = lv" in text.text  # the snapshot's text
    assert text.anchor_learning_object_ids == ("lo_eigen",) and text.subject_id == "linear-algebra"
    assert text.attempt_id is None and text.practice_item_id is None
    assert [lo["title"] for lo in text.context["learning_objects"]] == ["Eigenvalues"]
    assert text.context["passages"] and text.context["passages"][0]["lead"]  # the linked section, protection read
    pocket = learner_text(load_vault(paths.root), repository, "learner_note", snapshots["Eigen page"])
    assert pocket is not None and "handwritten" in pocket.context["note"]


def test_a_changed_note_is_read_with_its_current_snapshot_and_the_old_one_is_not(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    old = _snapshots(repository)["Eigen stuff"]
    entry = next(e for e in fake_tend.entries if e["hit"]["heading"] == "Eigen stuff")
    Path(entry["hit"]["path"]).write_text("* Eigen stuff\nEigenvalues again: Av = lv, now with a picture.\n", encoding="utf-8")
    entry["hit"].update(hash="h-new", line=1)
    fake_tend.save()
    call(ctx, "notes.path", {"goal_id": goal_id, "retry": True})
    with repository.connection() as connection:
        new = connection.execute("SELECT id FROM learner_notes WHERE heading = 'Eigen stuff' AND id != ?",
                                 (old,)).fetchone()[0]
    assert new in {row[0] for row in _jobs(repository)}  # the new snapshot is queued
    vault = load_vault(paths.root)
    assert learner_text(vault, repository, "learner_note", old) is None  # no longer the linked text
    assert "now with a picture" in learner_text(vault, repository, "learner_note", new).text


# -- a hidden link never feeds gaps ------------------------------------------------------------------

def test_a_hidden_link_is_never_read_and_undo_queues_it_again(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    typed = next(line for line in lines if line["note"]["heading"] == "Eigen stuff")
    hidden = call(ctx, "notes.decide", {"link_id": typed["linkId"], "choice": "hide"})
    vault = load_vault(paths.root)
    assert learner_text(vault, repository, "learner_note", snapshots["Eigen stuff"]) is None
    llm = PlanGapFake(reading=LearnerGap(kind="none"))
    outcome = _run(paths, repository, _clients(llm), source=("learner_note", snapshots["Eigen stuff"]))
    assert outcome.state == "skipped"
    with repository.connection() as connection:
        assert connection.execute("SELECT last_error FROM learner_text_gap_jobs WHERE source_id = ?",
                                  (snapshots["Eigen stuff"],)).fetchone()[0] == "nothing to read"
    assert all(SENTINEL not in json.dumps(payload) for payload in _readings(llm))  # never sent
    assert _gaps(repository) == []
    # The other note still feeds gaps.
    assert _run(paths, repository, _clients(llm), source=("learner_note", snapshots["Eigen page"])).state == "done"
    # undo (keep): linked again, so its skipped job is queued again and read.
    call(ctx, "notes.decide", {"link_id": hidden["linkId"], "choice": "keep"})
    assert (snapshots["Eigen stuff"], "queued") in {row[:2] for row in _jobs(repository)}
    assert _run(paths, repository, _clients(llm), source=("learner_note", snapshots["Eigen stuff"])).state == "done"
    assert {gap["source_id"] for gap in _gaps(repository)} == set(snapshots.values())


def test_an_unlinked_note_never_feeds_gaps(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    # The corpus's unrelated, outside, remote and private notes were never linked, so never stored or queued.
    with repository.connection() as connection:
        stored = " ".join(str(row[0]) for row in connection.execute("SELECT path FROM learner_notes"))
    assert "groceries" not in stored and "README" not in stored and "private" not in stored
    assert len(_jobs(repository)) == 2
    # An id that is no linked snapshot reads nothing.
    assert learner_text(load_vault(paths.root), repository, "learner_note", "ln_not_a_snapshot") is None


# -- tier 2 only ------------------------------------------------------------------------------------

def test_reading_a_note_is_tier_2_only_and_keeps_no_note_text(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    vault = load_vault(paths.root)
    los_before = set(vault.learning_objects)
    # A prerequisite the note relies on, matching lo_det: matched, but no edge and no sooner check.
    llm = PlanGapFake(reading=LearnerGap(kind="prerequisite", prerequisite_name="the determinant of a matrix",
                                         prerequisite_line="Uses det(A - lI) without knowing determinants."),
                      decide=word_match("determinant"))
    before = table_counts(repository)
    outcome = _run(paths, repository, _clients(llm), source=("learner_note", snapshots["Eigen stuff"]))
    assert outcome.state == "done" and outcome.action == "matched_prerequisite"
    after = table_counts(repository)
    changed = {name for name in after if after[name] != before.get(name)}
    assert changed <= GAP_TABLES, changed
    for table in NEVER_TABLES:
        assert after.get(table, 0) == before.get(table, 0), table
    (gap,) = _gaps(repository)
    assert (gap["source_kind"], gap["source_id"], gap["kind"], gap["target_id"]) == (
        "learner_note", snapshots["Eigen stuff"], "prerequisite", "lo_det")
    assert gap["anchor_learning_object_id"] == "lo_eigen" and gap["edge_id"] is None
    assert gap["learner_text"] == "" and gap["chooser"] == "context_model"  # the row keeps no note text
    detail = json.loads(gap["detail_json"])
    assert detail["embedding"] == "never_for_notes" and detail.get("edge") == "not_applicable"
    # Read with its own task and prompt version, on the plan.
    (reading,) = _readings(llm)
    assert "note the learner wrote in their own notes" in reading["task"] and reading["context"]["surface"] == "learner_note"
    with repository.connection() as connection:
        versions = {row[0] for row in connection.execute(
            "SELECT prompt_version FROM judgment_ledger WHERE left_kind = 'learner_note'")}
        ledger = json.dumps([list(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE left_kind = 'learner_note'")])
        gaps_dump = json.dumps([list(row) for row in connection.execute("SELECT * FROM learner_text_gaps")])
    assert READER_NOTE_PROMPT_VERSION in versions
    assert SENTINEL not in ledger and SENTINEL not in gaps_dump
    # An unmatched prerequisite named from a note is never drafted into a new topic.
    unmatched = PlanGapFake(reading=LearnerGap(kind="prerequisite", prerequisite_name="complex roots of polynomials"))
    outcome = _run(paths, repository, _clients(unmatched), source=("learner_note", snapshots["Eigen page"]))
    assert outcome.action == "unmatched_prerequisite"
    assert not [purpose for purpose, _ in unmatched.calls if purpose == "learner_gap_prerequisite_draft"]
    assert set(load_vault(paths.root).learning_objects) == los_before
    second = _gaps(repository)[-1]
    assert json.loads(second["detail_json"])["reason"] == "never_drafted_from_a_note"
    assert table_counts(repository).get("learner_gap_commitments", 0) == before.get("learner_gap_commitments", 0)


def test_a_notes_receipts_keep_no_prompt_text(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    llm = PlanGapFake(reading=LearnerGap(kind="none"))
    assert _run(paths, repository, _clients(llm), source=("learner_note", snapshots["Eigen stuff"])).state == "done"
    assert SENTINEL in json.dumps(_readings(llm))  # the plan's reader read the note itself
    with repository.connection() as connection:
        connection.row_factory = None
        names = [column[0] for column in connection.execute("SELECT * FROM model_call_receipts LIMIT 0").description]
        rows = [dict(zip(names, row)) for row in connection.execute(
            "SELECT * FROM model_call_receipts WHERE purpose = 'learner_gap_reading'").fetchall()]
    assert all(row["input_text"] is None for row in rows)
    assert SENTINEL not in json.dumps(rows, default=str)


# -- the plan only: no Decider, no other route; waits when the plan is down -------------------------

def test_the_plan_only_no_decider_and_waiting_when_the_plan_is_down(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    source = ("learner_note", snapshots["Eigen stuff"])
    # The plan down: no client. It waits (refunded, released for later); nothing is sent or logged.
    llm = PlanGapFake()
    down = PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=None, drafter=lambda: llm, note_reader=None)
    outcome = _run(paths, repository, down, source=source)
    assert (outcome.state, outcome.error) == ("retry_later", "waiting_for_plan")
    assert llm.calls == [] and _gaps(repository) == []
    with repository.connection() as connection:
        job = dict(connection.execute("SELECT * FROM learner_text_gap_jobs WHERE source_id = ?", (source[1],)).fetchone())
    assert job["state"] == "queued" and job["attempt_count"] == 0 and job["not_before"]  # never fails for waiting
    # A metered route as the notes' reader: refused before anything is sent.
    metered = MeteredGapFake()
    clients = PipelineClients(judge=lambda: metered, reader=lambda: metered, drafter=lambda: metered,
                              note_reader=lambda: metered)
    with repository.atomic():
        repository.connection().execute("UPDATE learner_text_gap_jobs SET not_before = NULL WHERE source_id = ?",
                                        (source[1],))
    outcome = _run(paths, repository, clients, source=source)
    assert outcome.error == "waiting_for_plan" and metered.calls == []
    # The plan up: read by the plan only. The Decider (OpenRouter) is never asked, even with
    # Tier 1's Decider switches on, and the gap judge's own route is not used for a note.
    with repository.atomic():
        repository.connection().execute("UPDATE learner_text_gap_jobs SET not_before = NULL WHERE source_id = ?",
                                        (source[1],))
    plan = PlanGapFake(reading=LearnerGap(kind="prerequisite", prerequisite_name="the determinant of a matrix"),
                       decide=always("different"))
    other = GapLLMFake()  # the gap judge's own (non-plan) route
    decider = ChoiceDecider(kind="misconception", pair=always("same"))
    clients = PipelineClients(judge=lambda: other, reader=lambda: other, decider=lambda: decider, drafter=lambda: other,
                              embedder=None, note_reader=lambda: plan)
    outcome = _run(paths, repository, clients, source=source)
    assert outcome.state == "done"
    assert decider.states == [] and other.calls == []
    assert {purpose for purpose, _ in plan.calls} <= {"learner_gap_reading", "learner_gap_same_prerequisite"}
    (gap,) = _gaps(repository)
    assert gap["decider_kind"] is None and json.loads(gap["decider_json"])["status"] == "disabled"


def test_the_default_note_reader_is_resolved_quietly_and_only_on_the_plan(tmp_path, monkeypatch):
    """No real client is resolved here: routing's resolution is replaced by a double."""

    from types import SimpleNamespace

    from learnloop.ai import plan_fallback
    from learnloop.ai import routing
    from learnloop.diagnosis.text_gaps import pipeline as P

    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    vault = load_vault(paths.root)
    assert P.note_reader_client(vault) is None  # the test suite sets LEARNLOOP_NOTE_LINK_MODELS=off
    monkeypatch.delenv(P.NOTE_MODELS_ENV, raising=False)
    asked: list[tuple[str, bool]] = []
    answer: dict = {}

    def resolve(_root, _config, task, **_kwargs):
        asked.append((task, plan_fallback.offers_suppressed()))
        return SimpleNamespace(**answer)

    monkeypatch.setattr(routing, "ready_client_for_task", resolve)
    monkeypatch.setattr(routing, "is_plan_profile", lambda _config, name: name == "plan")
    plan, metered = PlanGapFake(), MeteredGapFake()
    answer.update(ready=True, fallback_from=None, provider_name="plan", client=plan)
    assert P.note_reader_client(vault) is plan
    answer.update(provider_name="openrouter", client=metered)  # the notes' route set to another provider
    assert P.note_reader_client(vault) is None
    answer.update(provider_name="plan", client=metered)  # a plan profile whose client is not the plan's
    assert P.note_reader_client(vault) is None
    answer.update(provider_name="plan", client=plan, fallback_from="plan")  # a fallback is never a note's reader
    assert P.note_reader_client(vault) is None
    answer.update(ready=False, fallback_from=None)  # the plan down
    assert P.note_reader_client(vault) is None
    assert asked and all(task == P.NOTE_READER_TASK and quiet for task, quiet in asked)  # resolved quietly
    assert P.NOTE_READER_TASK in plan_fallback.PLAN_ONLY_TASKS  # never offered OpenRouter, never granted
    assert plan_fallback.offer_blocker(vault.config, P.NOTE_READER_TASK) is not None


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
    from tests.notes_fixtures import NoteLinkFake, install_fake_tend
    from tests.section_coverage_fixtures import CoverageJudgeFake
    from tests.test_curriculum_c3_exam_scoping import ALL_LOS, _clean
    from tests.test_curriculum_c3_exam_scoping import _deliverable as exam_deliverable

    fake_tend = install_fake_tend(tmp_path / "tend", monkeypatch)
    quoted = PAPER["paper_q1"][1][0][0]
    fake_tend.add(fake_tend.notes / "eigen.org", "* Eigen notes\nEigenvalues: det(A - lI) = 0, worked by hand.\n",
                  words=["eigenvalues"], heading="Eigen notes", line=1, title="eigen")
    fake_tend.add(fake_tend.notes / "det.org", "* Determinant notes\nDeterminants flip sign when rows swap.\n",
                  words=["determinants"], heading="Determinant notes", line=1, title="det")
    fake_tend.add(fake_tend.pocket / "2026-10-05.md", f"# Copied from the midterm\nI copied this: {quoted}\n",
                  words=["determinants", "eigenvalues", "matrix"], heading="Copied from the midterm", line=1,
                  title="2026-10-05")
    hand = fake_tend.add(fake_tend.notes / "rank.org", "* Rank practice\nMy try at the exam practice rank question.\n",
                         words=["rankpractice"], heading="Rank practice", line=1, title="rank")
    paths, repository = build_exam_scope_vault(tmp_path / "vault", config=fake_tend.config() + GAPS_ON)
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
    NL.link_by_hand(load_vault(paths.root), repository, hit={**hand, "heading_path": hand["heading"],
                                                             "content_hash": hand["hash"]},
                    extraction_id="ext_mixed", span_id=SPANS["mixed_exam"])
    vault = load_vault(paths.root)
    assert J.enqueue_learner_notes(vault, repository) >= 3
    with repository.connection() as connection:
        (held_id,) = [str(row[0]) for row in connection.execute(
            "SELECT id FROM learner_notes WHERE path LIKE '%rank.org'")]
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
        assert "My try at the exam practice rank question" not in own  # the held-out note is never sent
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

    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch, gaps=False)
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

    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch, gaps=False)
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


def test_f1_a_notes_belief_never_becomes_a_candidate_nor_leaves_the_plan_through_an_ordinary_gap(tmp_path, monkeypatch):
    """Codex review F1: the plan's reader echoes the note (a synthetic sentinel) into the belief
    it names. Nothing derived from the note is stored where ordinary consumers read it (no
    holding-pen candidate, no named words on the gap row), so an ordinary gap on the same topic,
    read by routes that are not the plan, never sends it."""

    from learnloop.diagnosis.text_gaps import pipeline as P

    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    echoed = f"Every matrix has real eigenvalues ({SENTINEL})"
    plan = PlanGapFake(reading=LearnerGap(kind="misconception", belief_statement=echoed))
    outcome = _run(paths, repository, _clients(plan), source=("learner_note", snapshots["Eigen stuff"]))
    assert outcome.state == "done"
    with repository.connection() as connection:
        pen = json.dumps([list(row) for row in connection.execute("SELECT * FROM misconception_candidates")])
        gaps_dump = json.dumps([list(row) for row in connection.execute("SELECT * FROM learner_text_gaps")])
    assert SENTINEL not in pen and SENTINEL not in gaps_dump
    (gap,) = _gaps(repository)
    assert gap["action"] != "belief_candidate"
    assert json.loads(gap["detail_json"]).get("reason") == "never_a_candidate_from_a_note"
    # An ordinary gap on lo_eigen, read and judged off the plan (the gap judge's route and the Decider).
    other = GapLLMFake(reading=LearnerGap(kind="misconception", belief_statement="eigenvalues are always positive"))
    decider = ChoiceDecider(kind="misconception", pair=always("different"))
    P.process_learner_text(paths.root, repository, _ordinary_text(),
                           clients=PipelineClients(judge=lambda: other, reader=lambda: other,
                                                   decider=lambda: decider, drafter=lambda: other),
                           clock=CLOCK)
    assert other.calls  # the ordinary gap was read and judged: the check is not vacuous
    assert SENTINEL not in json.dumps(other.calls, default=str)
    assert SENTINEL not in json.dumps(decider.states, default=str)
    # Every reader of the gap table that sends elsewhere reads no note-derived words.
    with repository.connection() as connection:
        card = P.named_gaps_for_card(connection)
    assert SENTINEL not in json.dumps(card, default=str)


def test_f2_a_note_outside_the_current_allowlist_is_never_queued_or_read(tmp_path, monkeypatch):
    """Codex review F2: a note linked while its folder was allowed, then the folder removed from
    ``notes.tend.paths``: its snapshot is no longer a gaps input (queue, text, read)."""

    from learnloop.ops.settings_store import apply_config_updates
    from learnloop.source_retrieval import note_gaps

    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch, gaps=False)
    snapshots = _snapshots(repository)
    apply_config_updates(paths.root / "learnloop.toml", {("notes", "tend", "paths"): [str(fake_tend.quicknote)],
                                                         ("notes", "gaps_enabled"): True})
    vault = load_vault(paths.root)
    assert note_gaps.linked_note_ids(vault, repository) == [snapshots["Eigen page"]]  # the excluded note drops out
    assert J.enqueue_learner_notes(vault, repository) == 1
    assert {row[0] for row in _jobs(repository)} == {snapshots["Eigen page"]}
    assert learner_text(vault, repository, "learner_note", snapshots["Eigen stuff"]) is None
    J.enqueue(repository, source_kind="learner_note", source_id=snapshots["Eigen stuff"], clock=CLOCK)
    llm = PlanGapFake()
    outcome = _run(paths, repository, _clients(llm), source=("learner_note", snapshots["Eigen stuff"]))
    assert outcome.state == "skipped" and llm.calls == []


def test_f3_revoking_consent_before_dispatch_sends_nothing(tmp_path, monkeypatch):
    """Codex review F3: the text is built, then the learner turns the opt-in off before the
    first request: the request gate refuses it, nothing is sent or logged, the job is skipped."""

    from learnloop.ops.settings_store import apply_config_updates

    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    original = J.learner_text

    def built_then_switched_off(*args, **kwargs):
        text = original(*args, **kwargs)
        apply_config_updates(paths.root / "learnloop.toml", {("notes", "gaps_enabled"): False})
        return text

    monkeypatch.setattr(J, "learner_text", built_then_switched_off)
    plan = PhysicalPlanFake(reading=LearnerGap(kind="none"))
    outcome = _run(paths, repository, _clients(plan), source=("learner_note", snapshots["Eigen stuff"]))
    assert outcome.state == "skipped" and plan.calls == [] and _gaps(repository) == []
    # The same with the notes switched off altogether.
    monkeypatch.setattr(J, "learner_text", original)
    apply_config_updates(paths.root / "learnloop.toml", {("notes", "gaps_enabled"): True})

    def built_then_notes_off(*args, **kwargs):
        text = original(*args, **kwargs)
        apply_config_updates(paths.root / "learnloop.toml", {("notes", "enabled"): False})
        return text

    monkeypatch.setattr(J, "learner_text", built_then_notes_off)
    outcome = _run(paths, repository, _clients(plan), source=("learner_note", snapshots["Eigen page"]))
    assert outcome.state == "skipped" and plan.calls == [] and _gaps(repository) == []


def test_f3_hiding_the_link_between_requests_stops_the_reading_and_writes_nothing(tmp_path, monkeypatch):
    """Codex review F3: the learner hides the link after the reading request: the pair
    verdicts are never sent and no gap row is written; *undo* queues it again."""

    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    typed = next(line for line in lines if line["note"]["heading"] == "Eigen stuff")
    hidden: dict = {}

    class HidesAfterReading(PhysicalPlanFake):
        def complete(self, request):
            result = super().complete(request)
            if request.purpose == "learner_gap_reading":
                hidden.update(call(ctx, "notes.decide", {"link_id": typed["linkId"], "choice": "hide"}))
            return result

    plan = HidesAfterReading(reading=LearnerGap(kind="prerequisite", prerequisite_name="the determinant of a matrix"),
                             decide=word_match("determinant"))
    outcome = _run(paths, repository, _clients(plan), source=("learner_note", snapshots["Eigen stuff"]))
    assert outcome.state == "skipped"
    assert [purpose for purpose, _ in plan.calls] == ["learner_gap_reading"]  # no pair verdict was sent
    assert _gaps(repository) == []
    call(ctx, "notes.decide", {"link_id": hidden["linkId"], "choice": "keep"})
    assert (snapshots["Eigen stuff"], "queued") in {row[:2] for row in _jobs(repository)}


def test_f3_switched_off_before_the_final_write_writes_nothing(tmp_path, monkeypatch):
    """Codex review F3: the opt-in turned off after the last request: the gap row is not written."""

    from learnloop.ops.settings_store import apply_config_updates

    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)

    class OffAfterReading(PhysicalPlanFake):
        def complete(self, request):
            result = super().complete(request)
            apply_config_updates(paths.root / "learnloop.toml", {("notes", "gaps_enabled"): False})
            return result

    plan = OffAfterReading(reading=LearnerGap(kind="none"))
    outcome = _run(paths, repository, _clients(plan), source=("learner_note", snapshots["Eigen stuff"]))
    assert outcome.state == "skipped" and _gaps(repository) == []


@pytest.mark.parametrize("note_first", [True, False])
def test_f4_mixed_queues_keep_metered_routes_metered(tmp_path, monkeypatch, note_first):
    """Codex review F4: one command budget across a note (the plan) and an ordinary gap (a
    metered route), in both orders: the note is accounted on its own route, the ordinary gap's
    requests stay metered and capped."""

    from learnloop.ai.spend import SpendCaps
    from learnloop.diagnosis.offline_review.spend import ReviewSpend
    from learnloop.diagnosis.text_gaps import pipeline as P
    from learnloop.diagnosis.text_gaps.judges import TextBudget

    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    vault = load_vault(paths.root)
    caps = SpendCaps(max_candidates=100, max_pairs=100, max_retries=10, max_calls=100, max_total_tokens=2_000_000,
                     max_estimated_usd=1.0)
    shared = TextBudget.for_command(ReviewSpend(caps, price_per_million=1.0, config=vault.config))
    plan = PlanGapFake(reading=LearnerGap(kind="none"))
    metered = MeteredGapFake(reading=LearnerGap(kind="none"))
    note_text = learner_text(vault, repository, "learner_note", snapshots["Eigen stuff"])

    def note():
        P.process_learner_text(paths.root, repository, note_text, clients=_clients(plan), budget=shared, clock=CLOCK)

    def ordinary():
        P.process_learner_text(paths.root, repository, _ordinary_text(),
                               clients=PipelineClients(judge=lambda: metered, reader=lambda: metered),
                               budget=shared, clock=CLOCK)

    for step in ((note, ordinary) if note_first else (ordinary, note)):
        step()
    routes = shared.spend.routes
    assert routes["learner_gap_reader"].billing == "metered"
    assert routes[P.NOTE_READER_TASK].billing == "subscription"
    assert _readings(plan) and _readings(metered)
    assert (shared.spend.estimated_usd.get("learner_gap_reader") or 0.0) > 0.0  # the metered reading was charged
    assert shared.spend.budget.used.total_tokens > 0


def test_f4_the_dry_run_plan_names_the_notes_route(tmp_path, monkeypatch):
    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    planned = J.plan(load_vault(paths.root), repository)
    assert "note_link_judge" in planned["routes"] and planned["by_source"].get("learner_note") == 2


def test_f5_a_plan_outage_at_inference_waits_and_never_fails_the_note(tmp_path, monkeypatch):
    """Codex review F5: the plan resolves, then its inference reports the usage limit: the
    reading waits (attempt refunded, backed off), however many times; never a failed gap."""

    paths, repository, ctx, goal_id, fake_tend, lines = _linked(tmp_path, monkeypatch)
    snapshots = _snapshots(repository)
    source = ("learner_note", snapshots["Eigen stuff"])
    plan = PlanOutageFake(down={"learner_gap_reading"}, reading=LearnerGap(kind="none"))
    for _round in range(J.MAX_ATTEMPTS + 2):
        outcome = _run(paths, repository, _clients(plan), source=source)
        assert (outcome.state, outcome.error) == ("retry_later", "waiting_for_plan")
        _clear_backoff(repository, source[1])
    assert _gaps(repository) == []
    with repository.connection() as connection:
        job = dict(connection.execute("SELECT * FROM learner_text_gap_jobs WHERE source_id = ?", (source[1],)).fetchone())
    assert job["state"] == "queued" and job["attempt_count"] == 0
    # The pair verdicts' outage waits too.
    pairs_down = PlanOutageFake(down={"learner_gap_same_prerequisite"},
                                reading=LearnerGap(kind="prerequisite", prerequisite_name="the determinant of a matrix"))
    outcome = _run(paths, repository, _clients(pairs_down), source=source)
    assert (outcome.state, outcome.error) == ("retry_later", "waiting_for_plan")
    assert _gaps(repository) == []
    # The plan back: read.
    _clear_backoff(repository, source[1])
    assert _run(paths, repository, _clients(PlanGapFake(reading=LearnerGap(kind="none"))), source=source).state == "done"
