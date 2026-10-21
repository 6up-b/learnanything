"""Reader workbench RW2c: the worked example that takes your route (spec_reader_workbench_v1 §5.10, G40).

Over a faked ``find_sources(intent="worked_example")``: the search runs under
the workbench session's server-derived caller (``assisted_practice`` for the
item), with the learner's steps as ``learner_work_md``; what comes back is
kept only when verified, never when it reproduces the item's answer, is an
exercise or solution, or is exam material, and ``follows_learner_route``
stays first. It runs after a shown level-3+ hint in the Reader and on "Show
me a similar example", is one of the problem's calls, counts nothing, and
is absent (nothing searched, not offered) without the sources spec's S3.
Fakes only.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.source_retrieval.policy import derive_policy
from learnloop.workbench import route_example
from learnloop.workbench.check import session_calls
from tests.approach_map_fakes import EXPECTED, ITEM
from tests.hint_fakes import WriterFake
from tests.workbench_help_fakes import STEP_2, call, help_rows, open_problem, run_job, sidecar, wb_answer

ROUTE = {"span_id": "w2", "extraction_id": "ext", "source_title": "Book A", "section": "3.4", "page": 41,
         "text": "Example 3.4: take the CDF first, then read the boundary.", "role": "worked_example",
         "verdict": "follows_learner_route"}
OTHER = {"span_id": "w1", "extraction_id": "ext", "source_title": "Book A", "section": "3.2", "page": 39,
         "text": "Example 3.2: integrate the density directly.", "role": "worked_example",
         "verdict": "worked_example"}
LEAK = {"span_id": "w3", "extraction_id": "ext", "source_title": "Book A", "section": "3.5",
        "text": EXPECTED, "role": "worked_example", "verdict": "follows_learner_route"}
EXERCISE = {"span_id": "x1", "extraction_id": "ext", "source_title": "Book A", "section": "3.9",
            "text": "Exercise 3.9", "role": "exercise", "verdict": "follows_learner_route"}
UNRELATED = {"span_id": "u1", "extraction_id": "ext", "source_title": "Book B", "text": "Something else",
             "role": "worked_example", "verdict": "unrelated"}


class FindFake:
    """``find_sources(intent="worked_example")``, faked at the Reader's seam."""

    def __init__(self, hits, status="verified"):
        self.hits = hits
        self.status = status
        self.calls = []

    def __call__(self, vault, repository, query, *, caller, learner_work_md, owner_id):
        self.calls.append({"query": query, "caller": caller, "learner_work_md": learner_work_md,
                           "owner_id": owner_id})
        policy, _reason = derive_policy(caller)
        return SimpleNamespace(hits=[dict(hit) for hit in self.hits], policy=policy, status="ok",
                               manifest={"verification": {"status": self.status}, "policy": policy})


def _setup(tmp_path, config="", hits=(OTHER, ROUTE), **kwargs):
    paths, ctx, _session = sidecar(tmp_path, config, writer=WriterFake([wb_answer] * 8))
    ctx.workbench_bridge_provider = lambda *a, **k: ([], {"basis": "retrieved_verified"})
    ctx.workbench_example_find = FindFake(list(hits), **kwargs)
    ctx.passage_draw_seed = "seed-ex"
    wb, chains = open_problem(ctx, origin="reader", entry="work_through")
    return paths, ctx, wb, chains


def test_after_a_level_three_hint_the_example_takes_the_learners_route(tmp_path):
    paths, ctx, wb, _chains = _setup(tmp_path)
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    assert hint["status"] == "ready" and hint["exampleJobId"]
    example = call(ctx, "workbench.help_job", {"jobId": hint["exampleJobId"]})["result"]
    assert example["status"] == "ready" and example["shown"] is True
    assert example["line"] == "A worked example that takes your route: Book A · §3.4 · p. 41 · compare it with your step 2"
    assert example["verdict"] == "follows_learner_route" and example["spanId"] == "w2"
    # Under the session's caller: assisted practice for the item, with the steps.
    [asked] = ctx.workbench_example_find.calls
    assert derive_policy(asked["caller"])[0] == "assisted_practice" and asked["caller"].item_id == ITEM
    assert STEP_2 in asked["learner_work_md"] and "Step 1:" in asked["learner_work_md"]
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "example"]
    assert (row["counted_by"], row["shown"], row["chooser"]) == (None, 1, "none")
    # It counts nothing: the record still names the book and the check and the hint.
    record = call(ctx, "workbench.get", {"sessionId": wb})["session"]["record"]
    assert record["hints"] == 3
    # Restored under its hint.
    state = call(ctx, "workbench.help_state", {"sessionId": wb})
    assert state["hints"][0]["example"]["spanId"] == "w2"


def test_no_example_after_a_lower_rung(tmp_path):
    _paths, ctx, wb, _chains = _setup(tmp_path)
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 2}))
    assert hint["exampleJobId"] is None
    assert ctx.workbench_example_find.calls == []


def test_what_comes_back_is_filtered_and_the_route_stays_first(tmp_path, monkeypatch):
    from learnloop.source_retrieval import corpus

    exam = {"span_id": "e1", "extraction_id": "ext_exam", "source_title": "Exam", "text": "A worked exam answer",
            "role": "worked_example", "verdict": "follows_learner_route"}
    monkeypatch.setattr(corpus, "exam_withheld", lambda vault, repository, keys: frozenset(
        key for key in keys if key[0] == "ext_exam"))
    paths, ctx, wb, _chains = _setup(tmp_path, hits=(OTHER, LEAK, EXERCISE, UNRELATED, exam, ROUTE))
    vault, repository = ctx.require_vault()
    kept = route_example.keep(vault, repository, vault.practice_items[ITEM], ctx.workbench_example_find.hits)
    # Never the item's answer, an exercise, an unrelated passage or exam material.
    assert [hit["span_id"] for hit in kept] == ["w2", "w1"]
    shown = run_job(ctx, call(ctx, "workbench.show_example", {"sessionId": wb}))
    assert shown["spanId"] == "w2" and "alternatives" not in shown  # one route passage: no draw


def test_an_unverified_search_shows_nothing(tmp_path):
    paths, ctx, wb, _chains = _setup(tmp_path, status="unverified: capped")
    shown = run_job(ctx, call(ctx, "workbench.show_example", {"sessionId": wb}))
    assert shown["status"] == "none" and shown["line"] == route_example.NOTHING_LINE
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "example"]
    assert row["shown"] == 0  # its place among the calls is kept, never shown


def test_show_me_a_similar_example_is_one_of_the_problems_calls(tmp_path):
    paths, ctx, wb, chains = _setup(tmp_path, hits=(ROUTE, dict(ROUTE, span_id="w4", section="3.6")))
    before = session_calls(ctx.require_vault()[1], wb)
    shown = run_job(ctx, call(ctx, "workbench.show_example", {"sessionId": wb, "focusedStepId": chains[1]}))
    assert shown["status"] == "ready" and shown["trigger"] == "show_me" and shown["aboutStepId"] == chains[1]
    assert session_calls(ctx.require_vault()[1], wb) == before + 1
    # Two passages take the route: the draw is logged and the other is one click away.
    assert shown["alternatives"] == 1
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "example"]
    assert row["propensity"] == pytest.approx(0.5) and row["seed"] == "seed-ex"
    state = call(ctx, "workbench.help_state", {"sessionId": wb})
    assert state["examplesAvailable"] is True
    assert [entry["spanId"] for entry in state["examples"]] == [shown["spanId"]]
    other = call(ctx, "workbench.another_passage", {"sessionId": wb, "assistId": shown["assistId"]})["passage"]
    assert other["line"].startswith("A worked example that takes your route:") and other["spanId"] != shown["spanId"]
    assert session_calls(ctx.require_vault()[1], wb) == before + 1


def test_the_session_cap_holds_for_examples(tmp_path):
    _paths, ctx, wb, _chains = _setup(tmp_path, "[workbench]\nmax_calls_per_session = 1\n")
    assert run_job(ctx, call(ctx, "workbench.show_example", {"sessionId": wb}))["status"] == "ready"
    second = run_job(ctx, call(ctx, "workbench.show_example", {"sessionId": wb}))
    assert (second["status"], second["reason"]) == ("unavailable", "session_capped")
    assert len(ctx.workbench_example_find.calls) == 1


@pytest.mark.parametrize("absence", ["no_intent", "service_off"])
def test_without_the_sources_specs_s3_the_example_is_absent_not_approximated(tmp_path, monkeypatch, absence):
    config = "[source_service]\nenabled = false\n" if absence == "service_off" else ""
    if absence == "no_intent":
        from learnloop.source_retrieval import find_sources

        monkeypatch.setattr(find_sources, "INTENTS", ("explain", "remediate", "alternative", "compare"))
    paths, ctx, wb, _chains = _setup(tmp_path, config)
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    assert hint["exampleJobId"] is None
    with pytest.raises(Exception) as refused:
        call(ctx, "workbench.show_example", {"sessionId": wb})
    assert getattr(refused.value, "code", None) == "examples_unavailable"
    assert call(ctx, "workbench.help_state", {"sessionId": wb})["examplesAvailable"] is False
    vault, repository = ctx.require_vault()
    absent = route_example.example_for(vault, repository, workbench_session_id=wb, item=vault.practice_items[ITEM],
                                       steps=[], trigger="show_me", find=ctx.workbench_example_find)
    assert absent["status"] == "absent"
    assert ctx.workbench_example_find.calls == []
    assert not [row for row in help_rows(paths, wb) if row["assist_kind"] == "example"]


def test_the_default_search_is_the_sources_specs_worked_example_intent(tmp_path, monkeypatch):
    from learnloop.instructional import sources

    seen = {}

    def propose(vault, repository, query, *, caller, intent, **kwargs):
        seen.update({"intent": intent, "caller": caller, **kwargs})
        return SimpleNamespace(hits=[dict(ROUTE)], policy="assisted_practice", status="ok",
                               manifest={"verification": {"status": "verified"}})

    monkeypatch.setattr(sources, "propose_sources", propose)
    paths, ctx, wb, _chains = _setup(tmp_path)
    ctx.workbench_example_find = None
    assert run_job(ctx, call(ctx, "workbench.show_example", {"sessionId": wb}))["status"] == "ready"
    assert seen["intent"] == "worked_example" and STEP_2 in seen["learner_work_md"]
    assert derive_policy(seen["caller"])[0] == "assisted_practice"


def test_under_the_problems_cap_the_example_never_displaces_the_bridge(tmp_path, monkeypatch):
    """Regression: with threaded jobs the example after a hint could take the
    problem's last call before RW2b's bridge took its place (the bridge then
    read ``session_capped``). The example now waits for its sibling bridge."""

    import time

    import learnloop.workbench.bridge as bridge_module

    real = bridge_module.bridge_for_hint

    def slow_bridge(*args, **kwargs):
        time.sleep(0.6)  # the bridge's thread starts late
        return real(*args, **kwargs)

    monkeypatch.setattr(bridge_module, "bridge_for_hint", slow_bridge)
    _paths, ctx, wb, _chains = _setup(tmp_path, "[workbench]\nmax_calls_per_session = 1\n")
    ctx.workbench_bridge_provider = lambda *a, **k: (
        [{"span_id": "s1", "extraction_id": "ext", "label": "Book · §5.1", "text": "a step"}],
        {"basis": "retrieved_verified"})
    ctx.hints_inline = False
    started = call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3})
    jobs = ctx.workbench_help_jobs
    assert jobs.get(started["jobId"]).done.wait(30)
    hint = call(ctx, "workbench.help_job", {"jobId": started["jobId"]})["result"]
    assert hint["shown"] is True and hint["bridgeJobId"] and hint["exampleJobId"]
    assert jobs.get(hint["bridgeJobId"]).done.wait(30)
    assert jobs.get(hint["exampleJobId"]).done.wait(90)
    ctx.hints_inline = True
    bridge = call(ctx, "workbench.help_job", {"jobId": hint["bridgeJobId"]})["result"]
    example = call(ctx, "workbench.help_job", {"jobId": hint["exampleJobId"]})["result"]
    assert bridge["status"] == "ready"
    assert (example["status"], example["reason"]) == ("unavailable", "session_capped")
    assert ctx.workbench_example_find.calls == []


def test_review_f1_an_example_in_another_book_carries_that_books_identity(tmp_path):
    """Codex review F1: an example retrieved from Book B (while the problem is
    in Book A) carries Book B's source and extraction ids to the Reader, on
    the result, the restored view, its draw's options and a learner pick, so
    the Reader opens Book B there."""

    from learnloop.workbench import passage_draw

    other_book = [{**ROUTE, "source_id": "src_b", "extraction_id": "ext_b", "source_title": "Book B"},
                  {**ROUTE, "span_id": "w5", "source_id": "src_b", "extraction_id": "ext_b",
                   "source_title": "Book B", "section": "4.1"}]
    paths, ctx, wb, _chains = _setup(tmp_path, hits=other_book, config="")
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    example = call(ctx, "workbench.help_job", {"jobId": hint["exampleJobId"]})["result"]
    assert (example["sourceId"], example["extractionId"]) == ("src_b", "ext_b")
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "example"]
    view = route_example.example_view(row)
    assert (view["source_id"], view["extraction_id"]) == ("src_b", "ext_b")
    assert {option["source_id"] for option in passage_draw.options_of(row)} == {"src_b"}
    picked = call(ctx, "workbench.another_passage", {"sessionId": wb, "assistId": row["id"]})["passage"]
    assert (picked["sourceId"], picked["extractionId"]) == ("src_b", "ext_b")
    # The step it was searched against is recorded (ids and hashes, no text).
    snapshot = __import__("json").loads(row["step_snapshot_json"])
    assert snapshot and all(set(entry) == {"chain_id", "step_id", "number", "hash"} for entry in snapshot)
