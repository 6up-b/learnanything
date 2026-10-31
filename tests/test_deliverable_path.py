"""Curriculum C0b: the deliverable path across books, its honest labels, the learner's
overrides, the Guide's slice, "Am I ready?" and the report's rows
(spec_deliverable_curriculum_v1 §7.1-§7.5, §8.5, §9, §11; G-C1, G-C3).

Every model is a fake; coverage is C0a's own judge with C0a's fake.
"""
from __future__ import annotations

from datetime import datetime, timedelta, UTC

import pytest

from learnloop.clock import FrozenClock
from learnloop.curriculum import commitments as C
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.source_retrieval import deliverables as DL
from learnloop.source_retrieval import reading_paths as RP
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import DeliverableFake, build_deliverable_vault, cover_all
from tests.section_coverage_fixtures import HELD_OUT_SENTINEL
from tests.source_retrieval_fakes import EXAM_QUESTION


def _scoped(paths, repository, sentence="eigenvalues for my midterm", *, depth="learn_to_use_it", due_at=None,
            fake=None):
    goal_id = DL.create_deliverable(load_vault(paths.root), repository, sentence, due_at=due_at)["goal_id"]
    vault = load_vault(paths.root)
    DL.resolve(vault, repository, goal_id, client=fake or DeliverableFake())
    vault = load_vault(paths.root)
    if depth:
        DL.add_input(vault, repository, goal_id, "depth", text=depth)
    return goal_id, load_vault(paths.root)


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


@pytest.fixture
def scoped(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    cover_all(paths, repository, "lo_eigen")
    goal_id, vault = _scoped(paths, repository)
    return paths, repository, goal_id, vault


def test_one_primary_per_lo_from_its_coverage_alternates_from_other_books(scoped):
    paths, repository, goal_id, vault = scoped
    fake = DeliverableFake(primaries={"Eigenvalues": "5.2 The characteristic equation"})
    result = DP.judge(vault, repository, goal_id, client=fake)
    assert result.status == "ready" and fake.calls == 1
    view = DP.path_view(vault, repository, goal_id)
    assert view["status"] == "ready" and len(view["lines"]) == 1
    line = view["lines"][0]
    assert line["learning_object_id"] == "lo_eigen" and line["label"] == "core" and line["reason_by"] == "model"
    assert (line["section"]["extraction_id"], line["section"]["section_id"]) == ("ext_lay", "lay_char")
    assert {(a["extraction_id"], a["section_id"]) for a in line["alternates"]} == {("ext_book", "ch_eigen"),
                                                                                  ("ext_lay", "lay_eigen")}
    labels = _rows(repository, "SELECT label FROM deliverable_path_sections WHERE goal_id = ? ORDER BY label",
                   (goal_id,))
    assert labels == [("alternate",), ("alternate",), ("core",)]
    ledger = _rows(repository, "SELECT task, judge, verdict FROM judgment_ledger WHERE task = 'deliverable_path_role'")
    assert ledger == [("deliverable_path_role", "llm", "core")]
    # A fresh state pays nothing.
    assert DP.judge(vault, repository, goal_id, client=fake).status == "fresh" and fake.calls == 1


def test_an_unknown_section_falls_back_to_codes_choice_and_an_omitted_lo_is_still_placed(scoped):
    paths, repository, goal_id, vault = scoped
    DP.judge(vault, repository, goal_id, client=DeliverableFake(bogus_primary=("Eigenvalues",)))
    line = DP.path_view(vault, repository, goal_id)["lines"][0]
    assert line["reason_by"] == "code" and line["reason"] == DP.DEFAULT_REASON
    assert line["section"]["treatment"] in DP.PRIMARY_TREATMENTS
    # Omitted by the model: code places it with its first eligible section.
    paths2 = paths
    goal2, vault2 = _scoped(paths2, repository, "eigenvalues again")
    DP.judge(vault2, repository, goal2, client=DeliverableFake(omit=("Eigenvalues",)))
    assert [line["learning_object_id"] for line in DP.path_view(vault2, repository, goal2)["lines"]] == ["lo_eigen"]


def test_a_mentions_only_section_is_never_a_primary(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    cover_all(paths, repository, "lo_eigen", treatments={
        "Chapter 5 Eigenvalues": "mentions", "5.1 Eigenvectors and eigenvalues": "applies",
        "5.2 The characteristic equation": "mentions"})
    goal_id, vault = _scoped(paths, repository)
    fake = DeliverableFake(primaries={"Eigenvalues": "Chapter 5 Eigenvalues"})
    # Nothing the judge could pick: no call (else every read would pay for a path with no line).
    assert DP.judge(vault, repository, goal_id, client=fake).status == "no_sections" and fake.calls == 0
    view = DP.path_view(vault, repository, goal_id)
    assert view["status"] == "no_sections" and view["lines"] == []
    assert [entry["learning_object_id"] for entry in view["uncovered"]] == ["lo_eigen"]


def test_already_shown_only_while_demonstrated(scoped, monkeypatch):
    paths, repository, goal_id, vault = scoped
    real = RP.lo_statuses

    def demonstrated(vault_, repository_, ids):
        out = real(vault_, repository_, ids)
        return {lo: (RP.LoStatus("demonstrated", True, False) if lo == "lo_eigen" else status)
                for lo, status in out.items()}

    monkeypatch.setattr(RP, "lo_statuses", demonstrated)
    DP.judge(vault, repository, goal_id, client=DeliverableFake())
    line = DP.path_view(vault, repository, goal_id)["lines"][0]
    assert line["label"] == "already_shown" and line["reason_by"] == "code" and "shown this on your own" in line["reason"]
    monkeypatch.setattr(RP, "lo_statuses", real)
    # No longer demonstrated (a new state): the stored label is not trusted; it is core again.
    again = DP.path_view(vault, repository, goal_id)
    assert again["status"] == "stale" and again["lines"][0]["label"] == "core"
    assert again["lines"][0]["reason"] == DP.NOT_SHOWN_REASON


def test_prerequisites_come_first_and_only_when_not_demonstrated(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault", prerequisite=True)
    cover_all(paths, repository, "lo_eigen", "lo_det")
    goal_id, vault = _scoped(paths, repository, "eigenvalues")
    inputs = DP.path_inputs(vault, repository, goal_id)
    kinds = {entry.learning_object_id: entry.kind for entry in inputs.los}
    assert kinds == {"lo_eigen": "needed", "lo_det": "prerequisite"}
    assert inputs.lo("lo_det").required_by == ("lo_eigen",)
    DP.judge(vault, repository, goal_id, client=DeliverableFake())
    lines = DP.path_view(vault, repository, goal_id)["lines"]
    assert [(line["learning_object_id"], line["label"]) for line in lines] == [("lo_det", "prerequisite"),
                                                                              ("lo_eigen", "core")]


def test_the_closure_reach_follows_the_depth():
    class _Lo:
        def __init__(self, concept, prerequisites=()):
            self.concept, self.prerequisites, self.status = concept, list(prerequisites), "active"

    class _Vault:
        learning_objects = {"a": _Lo("ca", ["cb"]), "b": _Lo("cb", ["cc"]), "c": _Lo("cc")}

    assert DP.prerequisite_closure(_Vault(), ["a"], "get_the_idea") == {"b": {"a"}}
    assert DP.prerequisite_closure(_Vault(), ["a"], "fluency") == {"b": {"a"}, "c": {"a"}}


def test_overrides_use_instead_skip_and_check_later(scoped):
    paths, repository, goal_id, vault = scoped
    DP.judge(vault, repository, goal_id, client=DeliverableFake(primaries={"Eigenvalues": "Chapter 5 Eigenvalues"}))
    out = DP.override(vault, repository, goal_id, "lo_eigen", "use_instead", section_ref="ext_lay/lay_eigen")
    line = DP.path_view(vault, repository, goal_id)["lines"][0]
    assert line["override"] == "use_instead" and line["section"]["section_id"] == "lay_eigen"
    assert ("ext_book", "ch_eigen") in {(a["extraction_id"], a["section_id"]) for a in line["alternates"]}
    assert _rows(repository, "SELECT judge, verdict FROM judgment_ledger WHERE id = (SELECT ledger_id FROM "
                             "deliverable_path_sections WHERE id = ?)", (out["override"]["id"],)) == [
        ("learner_card", "use_instead")]
    DP.override(vault, repository, goal_id, "lo_eigen", "skip")
    assert DP.path_view(vault, repository, goal_id)["lines"][0]["effective_label"] == "skipped"
    checked = DP.override(vault, repository, goal_id, "lo_eigen", "check_later")
    commitment_id = checked["check"]["commitment_id"]
    line = DP.path_view(vault, repository, goal_id)["lines"][0]
    assert line["effective_label"] == "check_pending" and line["check"]["state"] == "one_check_pending"
    with repository.connection() as connection:
        row = connection.execute("SELECT created_action FROM commitments WHERE id = ?", (commitment_id,)).fetchone()
    assert row[0] == "test_me_later"
    snapshot = next(s for s in __import__("learnloop.scheduling.intent.resolution", fromlist=["x"]).load_snapshots(
        repository.connection()) if s.id == commitment_id)
    assert snapshot.provenance["via"] == "deliverable_path" and snapshot.provenance["goal_id"] == goal_id
    # Answered (here: stopped), the line is back with its honest label; nothing was marked known.
    C.retire(repository, commitment_id=commitment_id)
    assert DP.path_view(vault, repository, goal_id)["lines"][0]["effective_label"] == "core"
    with pytest.raises(DL.DeliverableError):
        DP.override(vault, repository, goal_id, "lo_eigen", "use_instead", section_ref="ext_exam/exam_q")


def test_gc1_no_exam_or_held_out_text_reaches_the_path_judge_and_no_row_names_them(scoped):
    paths, repository, goal_id, vault = scoped
    fake = DeliverableFake()
    DP.judge(vault, repository, goal_id, client=fake)
    for prompt in fake.prompts:
        assert EXAM_QUESTION not in prompt and HELD_OUT_SENTINEL not in prompt and "exam_q" not in prompt
        assert "lay_held" not in prompt
    named = {row[0] for row in _rows(repository, "SELECT extraction_id || '/' || section_id FROM "
                                                 "deliverable_path_sections")}
    assert not any(ref.startswith("ext_exam/") or ref == "ext_lay/lay_held" for ref in named)


def test_the_guide_slice_shows_this_books_lines_other_books_and_not_needed(scoped):
    paths, repository, goal_id, vault = scoped
    DP.judge(vault, repository, goal_id, client=DeliverableFake(primaries={"Eigenvalues": "Chapter 5 Eigenvalues"}))
    book = DP.guide_slice(vault, repository, "ext_book")
    assert book["status"] == "ready" and book["goal"]["id"] == goal_id
    assert [(line["section"]["section_id"], line["label"]) for line in book["lines"]] == [("ch_eigen", "core")]
    assert {entry["section_id"] for entry in book["not_needed"]} == {"ch_det", "ch_orth"}
    assert book["not_needed_label"] == f"not needed for {book['goal']['title']}"
    lay = DP.guide_slice(vault, repository, "ext_lay")
    assert [(line["section"]["section_id"], line["label"]) for line in lay["lines"]] == [("lay_char", "alternate")] or \
        [(line["section"]["section_id"], line["label"]) for line in lay["lines"]] == [("lay_eigen", "alternate")]
    assert lay["elsewhere"][0]["section"]["section_id"] == "ch_eigen"
    assert "lay_held" not in {entry["section_id"] for entry in lay["not_needed"]}  # withheld: never listed
    # No deliverable names the exam: the Guide is RW7a's there.
    assert DP.guide_slice(vault, repository, "ext_exam")["status"] == "none"


def test_no_deliverable_leaves_the_guide_to_rw7a(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    assert DP.guide_slice(load_vault(paths.root), repository, "ext_book") == {"extraction_id": "ext_book",
                                                                               "status": "none"}


def test_ask_depth_and_no_scope_states(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id = DL.create_deliverable(load_vault(paths.root), repository, "eigenvalues")["goal_id"]
    vault = load_vault(paths.root)
    assert DP.path_view(vault, repository, goal_id)["status"] == "no_scope"
    DL.resolve(vault, repository, goal_id, client=DeliverableFake())
    vault = load_vault(paths.root)
    assert DP.path_view(vault, repository, goal_id)["status"] == "ask_depth"
    DL.add_input(vault, repository, goal_id, "depth", text="fluency")
    view = DP.path_view(vault, repository, goal_id)
    assert view["status"] == "no_sections" and view["uncovered"][0]["learning_object_id"] == "lo_eigen"
    assert DP.coverage_owed(vault, repository, goal_id) == ["lo_eigen"]


def test_check_due_is_bounded_by_tomorrow_fourteen_days_and_the_deadline(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    clock = FrozenClock(datetime(2026, 10, 31, 9, tzinfo=UTC))
    # No FSRS state: DL2's Check once delay (capture.test_me_later_days, 7 by default).
    assert DP.check_due(vault, repository, "lo_eigen", due_at=None, clock=clock) == "2026-11-07"
    assert DP.check_due(vault, repository, "lo_eigen", due_at="2026-11-01T23:59:59Z", clock=clock) == "2026-11-01"
    assert DP.READY_MAX_WAIT_DAYS == 14 and DP.ready_parameters(vault) == (0.80, 7)


def test_am_i_ready_creates_one_check_per_untested_lo_never_an_exam_reserved_item(tmp_path):
    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id, vault = _scoped(paths, repository, "matrix computations and vector lists", due_at="2026-12-01")
    needs = [entry["learning_object_id"] for entry in DL.needed_learning_objects(vault, repository, goal_id)]
    assert needs == ["lo_matrices", "lo_vectors"]
    items = sorted(item.id for item in vault.practice_items.values() if item.learning_object_id == "lo_matrices")
    repository.insert_exam_pool_items([{"id": "epi_1", "goal_id": goal_id, "practice_item_id": items[0],
                                        "reserved_at": "2026-10-30T00:00:00Z"}])
    before = DP.readiness(vault, repository, goal_id)
    assert [line["state"] for line in before["lines"]] == ["untested", "untested"]
    assert before["checks_owed"] == ["lo_matrices", "lo_vectors"]
    out = DP.ready_checks(vault, repository, goal_id)
    picked = {entry["learning_object_id"]: entry["item_id"] for entry in out["created"]}
    assert picked["lo_matrices"] and picked["lo_matrices"] != items[0]  # G-C3: never the reserved item
    assert all(entry["due_hint"] <= "2026-12-01" for entry in out["created"])
    assert out["readiness"]["checks_owed"] == []
    # Pressed again: no second check while one is pending.
    assert DP.ready_checks(vault, repository, goal_id)["created"] == []
    # A demonstrated LO gets no check, and "likely" is AD's labelled prediction, injected.
    view = DP.readiness(vault, repository, goal_id, likely=lambda lo: {"likely": True, "line": "likely ready (a prediction)"})
    assert {line["state"] for line in view["lines"]} == {"likely"}


def test_g_c3_held_out_items_are_never_picked(tmp_path, monkeypatch):
    from learnloop import learner_protection as LP

    paths, repository = build_deliverable_vault(tmp_path / "vault")
    goal_id, vault = _scoped(paths, repository, "matrix computations")
    real = LP.withheld_items

    def everything_but_one(vault_, repository_):
        found = real(vault_, repository_)
        items = sorted(i.id for i in vault_.practice_items.values() if i.learning_object_id == "lo_matrices")
        return LP.Withheld(reasons={**found.reasons, **{item: "exam" for item in items[:-1]}},
                           known_items=found.known_items)

    monkeypatch.setattr(LP, "withheld_items", everything_but_one)
    items = sorted(i.id for i in vault.practice_items.values() if i.learning_object_id == "lo_matrices")
    assert DP.check_item(vault, repository, "lo_matrices") == items[-1]
    monkeypatch.setattr(LP, "withheld_items", lambda v, r: LP.Withheld(available=False))
    assert DP.check_item(vault, repository, "lo_matrices") is None  # unreadable protection: no item (fail closed)


def test_the_report_rows_are_aggregates_only(scoped):
    paths, repository, goal_id, vault = scoped
    DP.judge(vault, repository, goal_id, client=DeliverableFake())
    DP.override(vault, repository, goal_id, "lo_eigen", "skip")
    out = DP.report(vault, repository)
    assert out["coverage"]["judged_rows"] >= 3 and out["choice"]["path_lines"] == 1
    assert out["choice"]["choices"] == {"skip": 1} and out["choice"]["swap_share"] == 0.0
    time_row = out["time"][0]
    assert time_row["goal_id"] == goal_id and time_row["book_order_minutes_left"] >= time_row["path_minutes_left"]
    assert "sections read" in out["never_success"]


def test_a_section_withheld_since_judging_is_never_shown_and_reasons_are_codes(scoped):
    from tests.section_coverage_fixtures import hold_out

    paths, repository, goal_id, vault = scoped
    DP.judge(vault, repository, goal_id, client=DeliverableFake(primaries={"Eigenvalues": "5.2 The characteristic equation"}))
    hold_out(repository, "lay_char")
    view = DP.path_view(vault, repository, goal_id)
    refs = {(line["section"]["extraction_id"], line["section"]["section_id"]) for line in view["lines"]}
    refs |= {(a["extraction_id"], a["section_id"]) for line in view["lines"] for a in line["alternates"]}
    assert ("ext_lay", "lay_char") not in refs
    assert all(line["reason_by"] == "code" for line in view["lines"])
    assert datetime.now(UTC) - timedelta(days=1) < datetime.now(UTC)


def test_reading_more_of_a_book_already_started_does_not_make_a_new_judgment(scoped):
    paths, repository, goal_id, vault = scoped
    first = DP.path_inputs(vault, repository, goal_id).state_key()
    repository.upsert_reader_section_progress(extraction_id="ext_book", section_id="ch_det", spans_seen=1,
                                              span_count=3)
    started = DP.path_inputs(vault, repository, goal_id)
    assert started.context["reading"] == [{"book": "Linear Algebra Notes"}] and started.state_key() != first
    repository.upsert_reader_section_progress(extraction_id="ext_book", section_id="ch_orth", completed=True)
    assert DP.path_inputs(vault, repository, goal_id).state_key() == started.state_key()
