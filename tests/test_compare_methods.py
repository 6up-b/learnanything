"""Reader workbench RW2c: "Compare with the book's method" (spec_reader_workbench_v1 §5.10, §5.4, G40).

Offered only after a correct Submit of a workbench problem; the reference is
read by id (the item's key; the book's solution only when the key status is
``book_solution``), nothing is retrieved; a reveal of an existing kind is
recorded ON THE ITEM (never on the submitted attempt) before anything is
shown, so the reveal-aware cold lane treats the family as revealed and the
next attempt on the item is primed; the attempt's own row is untouched. The
lines run on ``workbench_check``'s route (its receipts and caps) and a valid
different route is named valid. Fakes only.
"""

from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime, timedelta
import json

import pytest

from learnloop.clock import FrozenClock, utc_now_iso
from learnloop.db.connection import connect
from learnloop.workbench import compare_methods
from tests.approach_map_fakes import EXPECTED, ITEM, LO, add_attempt, write_item
from tests.hint_fakes import receipts, reveals
from tests.workbench_help_fakes import STEP_1, STEP_2, CheckFake, call, help_rows, open_problem, run_job, sidecar

SIBLING = "pi_cdf_2"


def _lines(context):
    steps = [entry["step"] for entry in context["steps"]]
    return {"learner_route_valid": True, "same_method": False, "differences": [
        {"kind": "method", "learner_step": steps[0], "line": "You took the CDF first; the book integrates directly."},
        {"kind": "step", "learner_step": 99, "line": "A step that does not exist."},
        {"kind": "assumption", "learner_step": 0, "line": "The book assumes the support is [0, 1]."},
    ]}


def _submitted(tmp_path, *, correctness=1.0, config=""):
    """A workbench problem submitted with ``correctness`` (the attempt and
    the session's submitted state written as the submit leaves them)."""

    paths, ctx, _session = sidecar(tmp_path, config, check=CheckFake([_lines] * 4))
    write_item(paths, SIBLING, family_id="fam_cdf")
    ctx.load(paths.root)
    wb, _chains = open_problem(ctx)
    created = utc_now_iso(FrozenClock(datetime.now(UTC) - timedelta(minutes=5)))
    add_attempt(paths.sqlite_path, "att_wb", correctness=correctness, answer=f"{STEP_1}\n{STEP_2}",
                created_at=created)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE workbench_sessions SET status = 'submitted', attempt_id = 'att_wb' WHERE id = ?",
                           (wb,))
        connection.commit()
    return paths, ctx, wb


def _attempt_row(paths, attempt_id="att_wb"):
    with closing(connect(paths.sqlite_path)) as connection:
        connection.row_factory = None
        return connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone()


def test_offered_only_after_a_correct_workbench_submit(tmp_path):
    paths, ctx, _wb = _submitted(tmp_path)
    assert call(ctx, "workbench.compare_offer", {"attemptId": "att_wb"}) | {"version": None} == {
        "available": True, "reason": None, "referenceKind": "item_key", "label": compare_methods.OFFER_LABEL,
        "version": None}
    # Not correct: not offered.
    _paths2, ctx2, _wb2 = _submitted(tmp_path / "partial", correctness=0.5)
    assert call(ctx2, "workbench.compare_offer", {"attemptId": "att_wb"})["reason"] == "not_correct"
    # An attempt from the answer box (no workbench problem): not offered.
    add_attempt(paths.sqlite_path, "att_box", correctness=1.0)
    assert call(ctx, "workbench.compare_offer", {"attemptId": "att_box"})["reason"] == "not_a_workbench_submit"


def test_never_offered_for_exam_material(tmp_path, monkeypatch):
    from learnloop.content.sources import exam_material

    _paths, ctx, _wb = _submitted(tmp_path)
    monkeypatch.setattr(exam_material, "item_exam_status", lambda item, **_kw: object())
    assert call(ctx, "workbench.compare_offer", {"attemptId": "att_wb"})["reason"] == "exam_material"
    with pytest.raises(Exception) as refused:
        call(ctx, "workbench.compare_methods", {"attemptId": "att_wb"})
    assert getattr(refused.value, "code", None) == "compare_unavailable"
    assert reveals(_paths.sqlite_path) == []


def test_the_reference_is_read_by_id_and_a_reveal_on_the_item_comes_first(tmp_path, monkeypatch):
    from learnloop.source_retrieval import find_sources

    def no_retrieval(*_args, **_kwargs):
        raise AssertionError("compare methods retrieves nothing")

    monkeypatch.setattr(find_sources, "find_sources", no_retrieval)
    paths, ctx, wb = _submitted(tmp_path)
    before = _attempt_row(paths)
    opened = call(ctx, "workbench.compare_methods", {"attemptId": "att_wb"})
    comparison = opened["comparison"]
    assert comparison["reference"] == {"kind": "item_key", "label": "The item's answer key", "text": EXPECTED}
    assert [step["bodyMd"] for step in comparison["learner"]["steps"]] == [STEP_1, STEP_2]
    # One reveal, an existing kind, on the item and never on the attempt.
    [reveal] = reveals(paths.sqlite_path)
    assert (reveal["source_kind"], reveal["practice_item_id"], reveal["attempt_id"], reveal["amount"]) == (
        "answer_display", ITEM, None, 1.0)
    assert reveal["basis"] == f"compare_methods:{comparison['assistId']}" and reveal["id"] == comparison["revealId"]
    # Stamped after the attempt's own second, so the next attempt's window sees it.
    from learnloop.clock import parse_utc

    assert parse_utc(reveal["created_at"]) > parse_utc(_attempt_created(paths))
    # Evidence untouched: the submitted attempt's row is byte-identical.
    assert _attempt_row(paths) == before
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "compare_methods"]
    assert (row["shown"], row["counted_by"], row["attempt_id"]) == (1, None, None)
    # A second open is the same comparison (no second reveal).
    again = call(ctx, "workbench.compare_methods", {"attemptId": "att_wb"})["comparison"]
    assert again["assistId"] == comparison["assistId"] and len(reveals(paths.sqlite_path)) == 1


def _attempt_created(paths):
    with closing(connect(paths.sqlite_path)) as connection:
        return connection.execute("SELECT created_at FROM practice_attempts WHERE id = 'att_wb'").fetchone()[0]


def test_the_lines_run_on_the_check_route_and_name_a_valid_route_valid(tmp_path):
    paths, ctx, wb = _submitted(tmp_path)
    opened = call(ctx, "workbench.compare_methods", {"attemptId": "att_wb"})
    lines = call(ctx, "workbench.help_job", {"jobId": opened["linesJobId"]})["result"]
    assert lines["status"] == "ready"
    payload = lines["lines"]
    assert payload["routeLine"] == compare_methods.VALID_ROUTE_LINE
    assert payload["label"] == "AI-written: one line per difference"
    # A line naming a step that does not exist is dropped.
    assert [entry["kind"] for entry in payload["differences"]] == ["method", "assumption"]
    assert payload["dropped"] == 1
    # The check route's receipts: one of the problem's calls, never the hint service's.
    [receipt] = [row for row in receipts(paths.sqlite_path, "workbench_check")
                 if row["owner_id"].startswith(f"{wb}:")]
    assert receipt["owner_id"] == f"{wb}:{opened['comparison']['assistId']}"
    assert receipts(paths.sqlite_path, "hint_writer") == []
    # The prompt carried the steps and the reference read by id.
    [context] = ctx.workbench_check_client.contexts
    assert context["reference"]["kind"] == "item_key" and len(context["steps"]) == 2
    # Restored with its lines on a later open.
    again = call(ctx, "workbench.compare_methods", {"attemptId": "att_wb"})
    assert again["linesJobId"] is None and again["comparison"]["lines"]["routeLine"] == compare_methods.VALID_ROUTE_LINE


def test_the_reveal_makes_the_cold_lane_treat_the_family_as_revealed_and_primes_the_next_attempt(tmp_path):
    from learnloop.scheduling.scheduler import cold_check_decision
    from learnloop import serve_eligibility

    paths, ctx, _wb = _submitted(tmp_path)
    vault, repository = ctx.require_vault()
    now = datetime.now(UTC)
    repository.create_followup_task(
        kind="cold_retry", case_kind="misconception", case_ref="ep_cmp",
        not_before=utc_now_iso(FrozenClock(now - timedelta(days=1))),
        expires_at=utc_now_iso(FrozenClock(now + timedelta(days=29))),
        selected_item_id=SIBLING, clock=FrozenClock(now - timedelta(days=2)))
    later = utc_now_iso(FrozenClock(now + timedelta(minutes=5)))
    before = cold_check_decision(vault, repository, SIBLING, now_iso=later, learning_object_id=LO)
    assert before.verdict == serve_eligibility.SERVE
    call(ctx, "workbench.compare_methods", {"attemptId": "att_wb"})
    vault, repository = ctx.require_vault()
    after = cold_check_decision(vault, repository, SIBLING, now_iso=later, learning_object_id=LO)
    # A reveal in the family's learning object since the check was scheduled: held.
    assert after.verdict == serve_eligibility.DEFER_UNTIL
    # And the item's next submit is primed by the full answer shown.
    submit = serve_eligibility.decide(serve_eligibility.gather(
        repository, practice_item_id=ITEM, learning_object_id=LO, at=later), serve_eligibility.SUBMIT)
    assert submit.primed is True


def test_an_imported_exercise_with_a_book_solution_shows_the_books_passage_as_a_source_review(tmp_path, monkeypatch):
    paths, ctx, wb = _submitted(tmp_path)
    solution = {"kind": "book_solution", "text": "Solution 3.4. F(x) = x^2, so the answer is 1/4.",
                "label": "The book's solution · Exercise 3.4 · p. 42", "extraction_id": "ext",
                "span_ids": ["s41", "s42"], "page": 42}
    monkeypatch.setattr(compare_methods, "book_solution", lambda vault, repository, item: dict(solution))
    assert call(ctx, "workbench.compare_offer", {"attemptId": "att_wb"})["referenceKind"] == "book_solution"
    comparison = call(ctx, "workbench.compare_methods", {"attemptId": "att_wb"})["comparison"]
    assert comparison["reference"]["kind"] == "book_solution" and comparison["reference"]["spanIds"] == ["s41", "s42"]
    [reveal] = reveals(paths.sqlite_path)
    assert (reveal["source_kind"], reveal["attempt_id"]) == ("source_review", None)
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "compare_methods"]
    assert json.loads(row["cited_span_ids_json"]) == ["s41", "s42"]


def test_book_solution_reads_the_checked_span_ids_and_never_exam_material(tmp_path, monkeypatch):
    """The book's passage is read by the span ids the key check recorded, only
    for a ``book_solution`` key, and withheld when it is exam material."""

    from types import SimpleNamespace

    from learnloop.db.stores import source_service
    from learnloop.source_retrieval import corpus

    paths, ctx, _wb = _submitted(tmp_path)
    vault, repository = ctx.require_vault()
    item = SimpleNamespace(id=ITEM, canonical_exercise=SimpleNamespace(extraction_id="ext", label="Exercise 3.4"),
                           expected_answer=EXPECTED, prompt="p", required_method=None)
    monkeypatch.setattr(source_service, "effective_key_status", lambda connection, value: "book_solution")
    monkeypatch.setattr(source_service, "reference_content_hash", lambda value: "h")
    monkeypatch.setattr(source_service, "applicable_checks", lambda *a, **k: [
        {"key_status": "book_solution", "verification": {"book_solution": {"span_ids": ["s1"], "page": 3}}}])
    from learnloop.db.stores import source_block_fts

    block = SimpleNamespace(text="Solution 3.4 text")
    monkeypatch.setattr(source_block_fts, "blocks_by_key", lambda connection, keys: {("ext", "s1"): block})
    found = compare_methods.book_solution(vault, repository, item)
    assert found["text"] == "Solution 3.4 text" and found["span_ids"] == ["s1"] and found["page"] == 3
    monkeypatch.setattr(corpus, "exam_withheld", lambda vault, repository, keys: frozenset(keys))
    assert compare_methods.book_solution(vault, repository, item) is None
    monkeypatch.setattr(source_service, "effective_key_status", lambda connection, value: "panel_agrees")
    monkeypatch.setattr(corpus, "exam_withheld", lambda vault, repository, keys: frozenset())
    assert compare_methods.book_solution(vault, repository, item) is None


def test_switched_off_nothing_is_offered_or_written(tmp_path):
    paths, ctx, _wb = _submitted(tmp_path, config="[workbench]\ncompare_methods_enabled = false\n")
    assert call(ctx, "workbench.compare_offer", {"attemptId": "att_wb"})["reason"] == "disabled"
    with pytest.raises(Exception):
        call(ctx, "workbench.compare_methods", {"attemptId": "att_wb"})
    assert reveals(paths.sqlite_path) == []
