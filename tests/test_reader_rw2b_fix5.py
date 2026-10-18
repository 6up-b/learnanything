"""Reader workbench RW2b + hints H3, fix round 5: the verify's five Highs, under the orchestrator's rulings.

``docs/reviews/reader-rw2b-h3-codex-review.md``, "Fix round 5 (orchestrator)":

* items 1-2: a defined name whose WRITTEN body restricts its variable is never
  used in a check (any kind); a solve or substitution step whose own text
  restricts a domain is the model's reading; two definitions that differ in
  body or in restriction status never resolve (hint claims too);
* item 3: a check's verdict carries a fingerprint of the FULL checked text;
* items 4-5: the submit's count is the sum of distinct parts (the authored
  reveals, sent on their own as ``authoredHints``; the book once; every
  distinct server assist), with round 4's rule for a client that does not
  send them.

Fakes only; the symbolic tests run the real PF-b sandbox (skipped without
bubblewrap). No model is reached.
"""

from __future__ import annotations

from contextlib import closing
import sqlite3

import pytest

from learnloop.content.authoring.pf_sandbox import sandbox_available
from learnloop.workbench.symbolic import CHECKED, MODEL, SymbolicClaim, run_checks
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, prefer
from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture
from tests.workbench_help_fakes import call, open_problem, run_job, sidecar, wb_answer

needs_bwrap = pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")


def _outcomes(*claims):
    outcomes, problem = run_checks(list(claims))
    assert problem is None
    return [(o.method, o.holds) for o in outcomes]


# -- Items 1-2: restrictions written through names ------------------------------------------------


@needs_bwrap
def test_items_1_2_a_solve_through_a_restricted_name_is_never_checked():
    # The verify's reproduction: f(0) is undefined, though f(x) - f(x) evaluates to 0.
    assert _outcomes(SymbolicClaim(1, "solving", "-x", "0", "x", text="x=0",
                                   earlier=(r"f(x)=\frac{x^2}{x}", "f(x)-f(x)=x"))) == [(MODEL, None)]


@needs_bwrap
def test_items_1_2_a_substitution_into_a_restricted_name_is_never_checked():
    # The verify's reproduction: the written f is undefined at 1.
    assert _outcomes(SymbolicClaim(1, "substitution", "x-1", "0", "x", value="1", text="f(1)=0",
                                   earlier=(r"f(x)=\frac{(x-1)^2}{x-1}",))) == [(MODEL, None)]


@needs_bwrap
def test_items_1_2_a_restricted_name_is_not_used_by_any_kind_and_taints_names_that_write_it():
    assert _outcomes(
        SymbolicClaim(1, "equivalence", "x+1", "x+1", text="f(x) + 1 = x + 1", earlier=(r"f(x) = \frac{x^2}{x}",)),
        SymbolicClaim(2, "differentiation", "x", "1", "x", text="f'(x) = 1", earlier=(r"f(x) = \frac{x^2}{x}",)),
        # h is written with g, which divides by its variable (h evaluates to 0).
        SymbolicClaim(3, "substitution", "0", "0", "x", value="1", text="h(1) = 0",
                      earlier=(r"g(x) = \frac{1}{x}", "h(x) = g(x) - g(x)")),
    ) == [(MODEL, None)] * 3


@needs_bwrap
def test_items_1_2_two_definitions_differing_only_in_their_restriction_never_resolve():
    assert _outcomes(SymbolicClaim(1, "substitution", "x", "2", "x", value="2", text="f(2) = 2",
                                   earlier=("f(x) = x", r"f(x) = \frac{x^2}{x}"))) == [(MODEL, None)]


@needs_bwrap
def test_items_1_2_names_are_never_resolved_and_a_name_free_step_still_checks():
    # Fix round 6 supersedes round 5's unrestricted-name control: no name resolves.
    assert _outcomes(
        SymbolicClaim(1, "substitution", "x^2+1", "5", "x", value="2", text="f(2) = 5", earlier=("f(x) = x^2 + 1",)),
        SymbolicClaim(2, "solving", "x/2 = 3", "6", "x", text="x = 6", earlier=(r"\frac{x}{2} = 3",)),
    ) == [(MODEL, None)] * 2
    assert _outcomes(SymbolicClaim(1, "solving", "2*x = 12", "6", "x", text="x = 6", earlier=("2x = 12",)),
                     SymbolicClaim(2, "equivalence", "x^2 + 1", "x^2 + 1", text="x^2 + 1 = 1 + x^2")) == [
        (CHECKED, True)] * 2


@needs_bwrap
def test_items_1_2_a_solve_or_substitution_whose_own_text_restricts_a_domain_is_never_checked():
    assert _outcomes(
        SymbolicClaim(1, "substitution", "x^2", "1", "x", value="1/y", text=r"f\left(\frac{1}{y}\right) = 1",
                      earlier=("f(x) = x^2",)),
        SymbolicClaim(2, "solving", "x - 1/y", "1/y", "x", text=r"x = \frac{1}{y}", earlier=(r"x - \frac{1}{y} = 0",)),
    ) == [(MODEL, None)] * 2


@needs_bwrap
def test_items_1_2_a_hint_claim_through_a_restricted_name_is_never_checked(tmp_path):
    claim = {"step": 1, "statement": "f(1) = 0", "kind": "substitution", "expression": "x-1", "result": "0",
             "variable": "x", "value": "1", "lower": "", "upper": "", "relation": ""}
    writer = WriterFake([lambda context: {**wb_answer(context), "claims": [claim]}, wb_answer])
    _paths, ctx, _session = sidecar(tmp_path, writer=writer, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx, steps=(r"f(x)=\frac{(x-1)^2}{x-1}",))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    assert [entry["status"] for entry in hint["claims"]] == ["model"]


# -- Item 3: the full-text fingerprint ------------------------------------------------------------


def test_item3_the_snapshot_and_the_check_view_carry_a_full_text_fingerprint(tmp_path):
    from learnloop.hints.workbench import WorkbenchHintContext, WorkbenchStep, text_fingerprint
    from learnloop.workbench.check import check_view

    # FNV-1a 64 reference values (the workbench's textFingerprint pins the same).
    assert text_fingerprint("") == "fnv1a64:cbf29ce484222325"
    assert text_fingerprint("a") == "fnv1a64:af63dc4c8601ec8c"
    long_a, long_b = "1=1" + " " * 1997 + "+0", "1=1" + " " * 1997 + "+1"
    assert long_a[:2000] == long_b[:2000] and text_fingerprint(long_a) != text_fingerprint(long_b)
    step = WorkbenchStep(chain_id="c1", step_id="s1", number=1, kind="step", body_md=long_a)
    [entry] = WorkbenchHintContext(workbench_session_id="wb", steps=(step,)).snapshot()
    assert entry["fingerprint"] == text_fingerprint(long_a) and len(entry["body_md"]) == 2000
    import json

    row = {"id": "ha_1", "step_snapshot_json": json.dumps([entry]), "placement_json": "{}",
           "step_verdicts_json": json.dumps([{"chain_id": "c1", "verdict": "valid", "method": "checked",
                                              "depends_on": [], "assumption": "", "map_node_id": None,
                                              "route_id": None, "reason": "", "content_hash": step.content_hash}])}
    [verdict] = check_view(row, [step])["verdicts"]
    assert verdict["checked_fingerprint"] == text_fingerprint(long_a)


# -- Items 4-5: the count is the sum of distinct parts --------------------------------------------


def _attempt(paths, attempt_id):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def _box_submit(ctx, session, key, *, hints_used, authored=None):
    payload = {"sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
               "hintsUsed": hints_used, "submissionId": key}
    if authored is not None:
        payload["authoredHints"] = authored
    return call(ctx, "submit_attempt", payload)


def _two_open_problems(ctx, *, origin="practice"):
    """Two open problems of one item: A, abandoned, B opened, A reopened."""

    entry = "work_through" if origin == "reader" else "practice_screen"
    first, _chains = open_problem(ctx, origin=origin, entry=entry)
    call(ctx, "workbench.abandon", {"sessionId": first})
    second, _chains = open_problem(ctx, origin=origin, entry=entry)
    assert second != first
    call(ctx, "workbench.reopen", {"sessionId": first})
    return first, second


def test_items_4_5_one_check_on_each_of_two_open_problems_records_two(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    first, second = _two_open_problems(ctx)
    for wb in (first, second):
        assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["shown"] is True
    attempt = _box_submit(ctx, session, "two-problems", hints_used=0, authored=0)
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 2


def test_items_4_5_a_book_on_another_surface_and_an_authored_hint_record_two(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx, origin="reader", entry="work_through")
    assert call(ctx, "workbench.get", {"sessionId": wb})["session"]["record"]["bookCounted"] is True
    # The answer box had not seen the book yet: it sends its one authored reveal.
    attempt = _box_submit(ctx, session, "book-and-authored", hints_used=1, authored=1)
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 2


def test_items_4_5_a_book_alone_records_one(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    open_problem(ctx, origin="reader", entry="work_through")
    attempt = _box_submit(ctx, session, "book-alone", hints_used=1, authored=0)
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 1


def test_items_4_5_a_book_counted_on_two_problems_records_one(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    _two_open_problems(ctx, origin="reader")
    attempt = _box_submit(ctx, session, "book-twice", hints_used=1, authored=0)
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 1


def test_items_4_5_a_hint_free_submit_is_unchanged(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    row = _attempt(paths, _box_submit(ctx, session, "free", hints_used=0, authored=0)["attemptId"])
    assert (row["hints_used"], row["primed"], row["attempt_type"]) == (0, 0, "independent_attempt")


def test_items_4_5_an_older_client_without_authored_hints_keeps_round_4s_rule(tmp_path, grader):
    paths, ctx, session = sidecar(tmp_path)
    wb, _chains = open_problem(ctx)
    assert run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))["shown"] is True
    attempt = _box_submit(ctx, session, "old-client", hints_used=1)
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 2
