"""Reader RW5d P3, Codex review (docs/reviews/reader-rw5d-p3-figures-help-codex-review.md).

* **F1.** The answer box's practice session is resolved on the server (it
  exists, is open, this device owns it, and the submission key is not
  another session's), and a cold take step's token is bound to that identity.
* **F2.** The reveal reads what the grammar and sketch tiers show: a
  grammar figure's shaded areas and readouts, formatted as the desktop's
  panels format them.
* **Step 0 (orchestrator ruling R1).** Attempt hosts are grammar and sketch
  only: no rich tier on the menu, no rich job, no fuller version, a Manim
  figure refused at ``figure.open`` and ``reader.figure_revise``, and a
  queued attempt-hosted rich job (legacy payloads included) stopped before
  any model request. The Manim scene is not scanned (F13).
* **F3.** One row per figure across the hosts of one attempt (the answer
  box's key handed into Work in Steps: CA2's aliases).
* **F4.** "Not right?" on a figure open on an attempt host is asked, recorded
  and reveal-checked on that host, whatever host it was first built on.
* **F5.** Switching figure help off between the build and the delivery stops
  the delivery (a build's, ``figure.open``'s and the chooser's line), and the
  build's admission key carries the switch.
* **F6.** A figure between a hint and the next check is further help, and a
  workbench figure row keeps the work it was opened against.

Fakes only: the figure author, the retrieval and the Decider are injected.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import Any

import pydantic
import pytest

from learnloop_sidecar.errors import SidecarError
from tests.figure_fixtures import AuthorFake, flagship, set_config
from tests.hint_fakes import ITEM, ChooserFake, WriterFake, assists, prefer, reveals
from tests.test_figures_help import (
    GOAL,
    _attempt,
    _call,
    _figure_rows,
    _host,
    _requests,
    _show_me,
    _sidecar,
    _submit,
    neutral_spec,
)


# ---------------------------------------------------------------------------
# F1: the session is the server's, and the token names it
# ---------------------------------------------------------------------------

def test_f1_an_unknown_or_ended_session_is_refused_before_any_job(tmp_path):
    author = AuthorFake([neutral_spec()])
    paths, ctx, session = _sidecar(tmp_path, author=author)
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "figure.request", {"goalText": GOAL, "origin": "ask",
                                      "hostRef": {"itemId": ITEM, "submissionId": "k1", "sessionId": "made_up"}})
    assert caught.value.code == "not_found"
    _vault, repository = ctx.require_vault()
    ended = repository.create_session()
    with repository.connection() as connection:
        connection.execute("UPDATE sessions SET ended_at = '2026-11-01T00:00:00Z' WHERE id = ?", (ended,))
        connection.commit()
    with pytest.raises(SidecarError):
        _call(ctx, "figure.request", {"goalText": GOAL, "origin": "ask", "hostRef": _host(ended)})
    assert author.calls == 0 and _requests(paths) == [] and _figure_rows(paths) == []


def test_f1_a_key_already_in_another_session_is_refused_so_no_row_escapes_the_fold(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    _show_me(ctx, _host(session))
    _vault, repository = ctx.require_vault()
    other = repository.create_session()
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "figure.request", {"goalText": "show the density 2x and its CDF side by side", "origin": "ask",
                                      "hostRef": _host(other)})
    assert caught.value.code == "validation_error"
    with pytest.raises(SidecarError):
        _call(ctx, "figure.open", {"figureId": _figure_rows(paths)[0]["figure_id"], "hostRef": _host(other)})
    # Every row of the key is in the session the attempt is submitted in: the fold counts what attaches.
    [row] = _figure_rows(paths)
    assert row["practice_session_id"] == session
    attempt = _attempt(paths, _submit(ctx, session)["attemptId"])
    assert attempt["hints_used"] == 1 and _figure_rows(paths)[0]["attempt_id"] == attempt["id"]


def test_f1_a_take_step_token_from_another_session_is_not_this_attempts(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import figures as FHandler

    monkeypatch.setattr(FHandler, "_item_cold", lambda vault, repository, item_id: True)
    monkeypatch.setattr(FHandler, "take_step_available", lambda vault, repository, item_id: True)
    paths, ctx, session = _sidecar(tmp_path)
    step = _call(ctx, "figure.take_step", {"itemId": ITEM, "submissionId": "k1", "sessionId": session})
    row = _figure_rows(paths)[0]
    assert row["practice_session_id"] == session
    # The token's row is bound to its session: the same key under another open session is refused.
    _vault, repository = ctx.require_vault()
    other = repository.create_session()
    with pytest.raises(SidecarError):
        _call(ctx, "figure.request", {"goalText": GOAL, "origin": "ask", "hostRef": _host(other),
                                      "takeStepToken": step["token"]})
    assert FHandler._token_row_matches(row, item_id=ITEM, session_id=other, kind="practice",
                                       submissions=frozenset({"k1"}), workbenches=frozenset()) is False
    assert FHandler._token_row_matches(row, item_id=ITEM, session_id=session, kind="practice",
                                       submissions=frozenset({"k1"}), workbenches=frozenset()) is True


# ---------------------------------------------------------------------------
# F2: the reveal reads what the grammar and sketch tiers show, as formatted
# (orchestrator ruling: rich figures never appear on attempt hosts, so the
# Manim scan is the base one: F2/F10/F11/F12/F13 closed structurally)
# ---------------------------------------------------------------------------

SCENE = '''from manim import *

class Area(Scene):
    def construct(self):
        unused = "0.5"
        self.play(Create(Circle(radius=2)))
'''


def _manim_row(**changes: Any) -> dict[str, Any]:
    """A stored Manim figure as the rich job writes it (``rich.canonical_spec``)."""

    from learnloop.figures import manim_figure as M
    from learnloop.figures import rich as RICH

    figure = M.ManimFigure(scene_code=changes.pop("scene_code", SCENE), scene_class="Area",
                           title=changes.pop("title", "zebra stripes"),
                           narration_md=changes.pop("narration_md", "zebra stripes"))
    spec = RICH.canonical_spec(figure, {"demonstrates": "zebra stripes", "brief": "b"}, [], [])
    return {"spec_json": spec, "spec_version": M.MANIM_FIG_VERSION, "tier": "manim"}


def test_s0_f13_an_undisplayed_string_in_a_scene_is_not_reveal_text():
    """Codex re-re-review F13: a program's strings are not its shown words.
    The scene is never scanned (a rich figure is never on an attempt host)."""

    from learnloop.figures.help import reveal_text

    text = reveal_text(_manim_row()).split("\n")
    assert "0.5" not in text and "Circle" not in text


def test_f2_numbers_are_formatted_as_the_desktop_panels_format_them():
    from learnloop.figures.help import format_value

    # FigurePanels.tsx formatValue: String(Number(v.toPrecision(5))), toExponential(3), toFixed(1)%.
    assert format_value(0.12345) == "0.12345"
    assert format_value(1 / 3) == "0.33333"
    assert format_value(2.0) == "2" and format_value(0) == "0" and format_value(-0.25) == "-0.25"
    assert format_value(99999.5) == "100000"
    assert format_value(123456) == "1.235e+5" and format_value(0.000123456) == "1.235e-4"
    assert format_value(0.25, "percent") == "25.0%" and format_value(0.0005, "percent") == "0.1%"
    assert format_value(-0.0004, "percent") == "-0.0%"
    assert format_value(float("nan")) == "—"


def test_f2_a_grammar_figures_shaded_area_is_read_as_shown():
    from learnloop.figures import spec as S
    from learnloop.figures.help import format_value, reveal_text
    from tests import figure_corpus as FC

    spec = FC.flagship_spec()
    evaluated = S.evaluate_figure(S.parse_spec(json.dumps(spec)))
    shades = [shade for panel in evaluated["panels"] for shade in panel.get("shades") or ()]
    assert shades, "the flagship shades an area"
    text = reveal_text({"spec_json": json.dumps(spec), "spec_version": S.SPEC_VERSION}).split("\n")
    assert all(format_value(shade["value"]) in text for shade in shades)


# ---------------------------------------------------------------------------
# F3: one row per figure across the hosts of one attempt
# ---------------------------------------------------------------------------

def test_f3_the_same_figure_opened_on_the_answer_box_and_in_work_in_steps_counts_once(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    vault, _repository = ctx.require_vault()
    figure = _show_me(ctx, _host(session))["result"]["figure"]
    # The answer box's draft (key k1) is handed into Work in Steps.
    view = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                         "stemMd": vault.practice_items[ITEM].prompt, "practiceSessionId": session,
                                         "submissionId": "k1"})["session"]
    workbench = {"itemId": ITEM, "workbenchSessionId": view["sessionId"]}
    opened = _call(ctx, "figure.open", {"figureId": figure["figureId"], "hostRef": workbench})
    assert opened["help"]["status"] == "counted" and opened["help"]["new"] is False
    assert len(_figure_rows(paths)) == 1
    # A take step on either host is the attempt's one take step too.
    from learnloop_sidecar.handlers.figures import attempt_aliases

    _vault, repository = ctx.require_vault()
    submissions, workbenches = attempt_aliases(repository, ITEM, None, view["sessionId"])
    assert "k1" in submissions and view["sessionId"] in workbenches


# ---------------------------------------------------------------------------
# F4: "not right?" on the host the figure is open on now
# ---------------------------------------------------------------------------

def test_f4_revising_a_reader_figure_opened_in_practice_is_recorded_and_reveal_checked_there(tmp_path):
    from learnloop.vault.loader import load_vault
    from tests.figure_fixtures import EXTRACTION, build, build_figure_vault, context

    paths, repository = build_figure_vault(tmp_path / "vault")
    item = load_vault(paths.root).practice_items["pi_eigen_1"]
    author = AuthorFake([flagship(), flagship(demonstrates=f"the answer is {item.expected_answer}")])
    ctx = context(paths.root, author=author)
    ctx.library_ask_inline = True
    reader_figure = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p3"]})["figure"]
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    host = {"itemId": item.id, "submissionId": "k1", "sessionId": session}
    opened = _call(ctx, "figure.open", {"figureId": reader_figure["figureId"], "hostRef": host})
    assert opened["help"]["status"] == "counted" and opened["help"]["new"] is True
    job = _call(ctx, "reader.figure_revise", {"figureId": reader_figure["figureId"], "note": "bigger",
                                              "hostRef": host})
    if job["state"] == "pending":
        assert ctx.figure_jobs.get(job["jobId"]).done.wait(60)
        job = _call(ctx, "reader.figure_job", {"jobId": job["jobId"]})
    revised = job["result"]["figure"]
    assert revised["supersedesId"] == reader_figure["figureId"]
    # Recorded on the attempt: the same figure for the count (one row), and its own reveal check.
    assert job["result"]["help"]["status"] == "counted" and job["result"]["help"]["new"] is False
    rows = [row for row in assists(paths.sqlite_path) if row["assist_kind"] == "figure"]
    assert len(rows) == 1 and rows[0]["submission_id"] == "k1"
    assert [row["basis"] for row in reveals(paths.sqlite_path) if (row["basis"] or "").startswith("figure:")] == [
        f"figure:{revised['figureId']}"]


def test_f4_a_revision_names_an_attempt_host_or_none(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    figure = _show_me(ctx, _host(session))["result"]["figure"]
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "reader.figure_revise", {"figureId": figure["figureId"], "note": "x",
                                            "hostRef": {"questionEventId": "q1"}})
    assert caught.value.code == "validation_error"


# ---------------------------------------------------------------------------
# F5: the switch is rechecked at admission and at every delivery
# ---------------------------------------------------------------------------

def _off(paths: Any, ctx: Any) -> None:
    set_config(paths, "figures", help_kind_enabled=False)
    ctx.reload(maintenance=False)


def test_f5_switched_off_between_the_build_and_the_delivery_nothing_is_shown_or_counted(tmp_path):
    from learnloop_sidecar.handlers.figures import deliver_figure, record_attempt_figure

    paths, ctx, session = _sidecar(tmp_path)
    # A figure built for free (feedback), so nothing about it is recorded yet.
    attempt_id = _submit(ctx, session, key="k0")["attemptId"]
    figure = _show_me(ctx, {"attemptId": attempt_id})["result"]["figure"]
    host = {"kind": "practice", "item_id": ITEM, "submission_id": "k1", "session_id": session,
            "workbench_session_id": None, "attempt_id": None, "cold": False, "take_step_id": None}
    _off(paths, ctx)
    delivered = deliver_figure(ctx, {"figure": {"figure_id": figure["figureId"]}, "reused": False,
                                     "_attempt": dict(host)})
    assert delivered["figure"] is None and delivered["help"]["status"] == "disabled"
    assert record_attempt_figure(ctx, dict(host), figure["figureId"])["status"] == "disabled"
    assert _figure_rows(paths) == []
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "figure.open", {"figureId": figure["figureId"], "hostRef": _host(session)})
    assert caught.value.code == "figures_help_disabled"


def test_f5_an_attempt_builds_admission_key_carries_the_switch(tmp_path):
    from learnloop.figures import service as FS
    from learnloop.vault.loader import load_vault
    from tests.hint_fakes import hint_vault

    paths = hint_vault(tmp_path, config="[figures]\nsketch_enabled = false\nrich_tiers_enabled = false\n")
    on = load_vault(paths.root)
    request = FS.FigureRequest(extraction_id=None, span_ids=[], origin="ask", goal_text=GOAL, goal_author="learner",
                               host_ref={"item_id": ITEM, "submission_id": "k1"})
    reader = FS.FigureRequest(extraction_id="e", span_ids=[], origin="show_me", goal_text=GOAL,
                              goal_author="learner", reading_at={"extraction_id": "e", "span_id": "s"})
    key, reader_key = FS.key_for(request), FS.key_for(reader)
    set_config(paths, "figures", help_kind_enabled=False)
    off = load_vault(paths.root)
    assert key(on) != key(off)
    assert reader_key(on) == reader_key(off)


def test_f5_a_chooser_figure_line_switched_off_before_delivery_is_not_shown(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.hints import service as HS
    from learnloop_sidecar.handlers.hints import _deliver
    from learnloop.hints.service import HintRequestV1
    from tests.hint_fakes import WORK
    from tests.test_figures_help import _offer

    paths, ctx, session = _sidecar(tmp_path)
    attempt_id = _submit(ctx, session, key="k0")["attemptId"]
    figure = _show_me(ctx, {"attemptId": attempt_id})["result"]["figure"]
    vault, _repository = ctx.require_vault()
    request = HintRequestV1(practice_item_id=ITEM, session_id=session, submission_id="k1", work_md=WORK)
    result = HS.request_hint(vault, Repository.attach(paths.sqlite_path), request,
                             writer_client=WriterFake(), seed="e",
                             chooser_client_factory=lambda: ChooserFake(prefer("explore_figure@L2", 0.9)),
                             figure_provider=lambda state: _offer(figure["figureId"]))
    assert result.kind == "explore_figure"
    _off(paths, ctx)
    assert _deliver(ctx, ITEM, str(result.assist_id)) == HS.NOT_DELIVERABLE
    [row] = [row for row in assists(paths.sqlite_path) if row["id"] == result.assist_id]
    assert row["shown"] == 0


# ---------------------------------------------------------------------------
# F6: a figure between a hint and the next check is further help
# ---------------------------------------------------------------------------

def _verdicts(entries: list[tuple[str, str, str]]) -> str:
    return json.dumps([{"chain_id": chain, "verdict": verdict, "hash": hash_} for chain, verdict, hash_ in entries])


def _snapshot(entries: list[tuple[str, str, str]]) -> str:
    return json.dumps([{"chain_id": chain, "number": index, "hash": hash_}
                       for index, (chain, _verdict, hash_) in enumerate(entries, start=1)])


def test_f6_hint_then_figure_then_check_is_more_help_not_unaided_progress():
    from learnloop.hints.report_workbench import workbench_unaided_progress

    delivered = [("a", "valid", "h_a"), ("b", "questionable", "h_b")]
    later = [("a", "valid", "h_a"), ("b", "valid", "h_b2")]

    def rows(between_kind: str) -> list[dict[str, Any]]:
        return [
            {"id": "ha_c0", "assist_kind": "check", "shown": 1, "shown_at": "2026-11-01T09:59:00Z",
             "step_verdicts_json": _verdicts(delivered), "step_snapshot_json": _snapshot(delivered)},
            {"id": "ha_h", "assist_kind": "hint", "hint_kind": "next_step", "level": 3, "shown": 1,
             "shown_at": "2026-11-01T10:00:00Z", "about_step_id": "b",
             "step_snapshot_json": _snapshot(delivered), "step_verdicts_json": _verdicts(delivered)},
            {"id": "ha_f", "assist_kind": between_kind, "shown": 1, "shown_at": "2026-11-01T10:01:00Z",
             "step_snapshot_json": _snapshot(delivered)},
            {"id": "ha_c", "assist_kind": "check", "shown": 1, "shown_at": "2026-11-01T10:02:00Z",
             "step_verdicts_json": _verdicts(later), "step_snapshot_json": _snapshot(later)},
        ]

    assert workbench_unaided_progress(rows("example")[1], rows("example")) == "more_help"
    assert workbench_unaided_progress(rows("figure")[1], rows("figure")) == "more_help"
    # The figure's own continuation reads its snapshot and the check before it (b newly valid after it).
    assert workbench_unaided_progress(rows("figure")[2], rows("figure")) == "continued"


def test_f6_a_workbench_figure_row_keeps_the_work_it_was_opened_against(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    vault, _repository = ctx.require_vault()
    attempt_id = _submit(ctx, session, key="k0")["attemptId"]
    figure = _show_me(ctx, {"attemptId": attempt_id})["result"]["figure"]
    view = _call(ctx, "workbench.open", {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM,
                                         "stemMd": vault.practice_items[ITEM].prompt,
                                         "practiceSessionId": session})["session"]
    _call(ctx, "workbench.save_step", {"sessionId": view["sessionId"], "clientIdempotencyKey": "s0", "op": "add",
                                       "bodyMd": "F(x) = x^2 on [0, 1]", "afterStepId": None})
    opened = _call(ctx, "figure.open", {"figureId": figure["figureId"],
                                        "hostRef": {"itemId": ITEM, "workbenchSessionId": view["sessionId"]}})
    assert opened["help"]["new"] is True
    [row] = _figure_rows(paths)
    snapshot = json.loads(row["step_snapshot_json"])
    assert len(snapshot) == 1 and set(snapshot[0]) == {"chain_id", "step_id", "number", "hash"}
    assert "x^2" not in row["step_snapshot_json"]


# ---------------------------------------------------------------------------
# F7, F9: predictions inside an attempt are linked to its figure row and frozen at Submit
# ---------------------------------------------------------------------------

def _predictions(paths: Any) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute("SELECT * FROM figure_predictions ORDER BY created_at, id")]


def _homeless_figure(tmp_path):
    paths, ctx, session = _sidecar(tmp_path, author=AuthorFake([flagship(demonstrates="zebra stripes")
                                                                for _ in range(4)]))
    job = _show_me(ctx, _host(session))
    figure = job["result"]["figure"]
    return paths, ctx, session, figure


def test_f9_a_homeless_attempt_illustration_keeps_its_predictions_with_no_invented_home(tmp_path):
    paths, ctx, session, figure = _homeless_figure(tmp_path)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        stored = connection.execute("SELECT extraction_id, grounding, input_span_keys_json FROM interactive_figures "
                                    "WHERE id = ?", (figure["figureId"],)).fetchone()
    assert stored[0] is None and stored[1] == "none"
    # The view offers the predictions, and the prediction RPC records one.
    assert figure["predictions"], "the illustration's predictions are shown"
    choice = figure["predictions"][0]["choices"][0]["value"]
    found = _call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                 "answer": choice})
    assert found["learnerAnswer"] == choice
    [prediction] = _predictions(paths)
    [row] = _figure_rows(paths)
    assert prediction["extraction_id"] is None and prediction["assist_id"] == row["id"]


def test_f7_the_trace_reads_only_what_this_attempt_wrote_as_it_stood_at_submit(tmp_path):
    from datetime import UTC, datetime

    from learnloop.clock import FrozenClock
    from learnloop.db.repositories import Repository
    from learnloop.diagnosis.split.figure_trace import figure_trace_for_attempt
    from learnloop.figures import service as FS
    from learnloop.vault.loader import load_vault

    paths, ctx, session, figure = _homeless_figure(tmp_path)
    first = figure["predictions"][0]["choices"][0]["value"]
    made = _call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                "answer": first})
    attempt_id = _submit(ctx, session)["attemptId"]
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    before = figure_trace_for_attempt(vault, repository, _attempt(paths, attempt_id))
    assert [entry["prompt_index"] for entry in before["figures"][0]["predictions"]] == [0]
    # Later, after Submit: another prediction on the same figure and a "what changed?" on the first.
    second = figure["predictions"][1]["choices"][0]["value"]
    _call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 1, "answer": second})
    later = FrozenClock(datetime(2999, 1, 1, tzinfo=UTC))
    FS.record_explanation(vault, repository, made["predictionId"], "it moved left", clock=later)
    after = figure_trace_for_attempt(vault, repository, _attempt(paths, attempt_id))
    assert after == before
    assert [row["assist_id"] for row in _predictions(paths)][1] is None


def test_f7_predictions_made_before_the_attempt_are_not_its_trace(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.diagnosis.split.figure_trace import figure_trace_for_attempt
    from learnloop.vault.loader import load_vault

    paths, ctx, session = _sidecar(tmp_path, author=AuthorFake([flagship(demonstrates="zebra stripes")
                                                                for _ in range(4)]))
    # Built for free on an earlier attempt's feedback, predicted on there (no attempt row open).
    earlier = _submit(ctx, session, key="k0")["attemptId"]
    figure = _show_me(ctx, {"attemptId": earlier})["result"]["figure"]
    _call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                         "answer": figure["predictions"][0]["choices"][0]["value"]})
    assert _predictions(paths)[0]["assist_id"] is None
    # Opened on the next attempt: the trace lists the figure, with no prediction of this attempt's.
    _call(ctx, "figure.open", {"figureId": figure["figureId"], "hostRef": _host(session)})
    attempt_id = _submit(ctx, session)["attemptId"]
    trace = figure_trace_for_attempt(load_vault(paths.root), Repository.attach(paths.sqlite_path),
                                     _attempt(paths, attempt_id))
    assert trace is not None and trace["figures"][0]["predictions"] == []


# ---------------------------------------------------------------------------
# Step 0 (structural, the orchestrator's ruling R1): attempt hosts are grammar
# and sketch only; rich (Manim) figures stay Reader-side
# ---------------------------------------------------------------------------

def _rich_attempt(tmp_path, monkeypatch, answers, *, foreground: bool = True):
    from learnloop.content.pipeline.runner import RunnerServices
    from tests import rich_fixtures as RF
    from tests.figure_fixtures import build_figure_vault, context
    from tests.test_figures_help import FindFake

    paths, repository = build_figure_vault(tmp_path / "vault", rich=True)
    set_config(paths, "figures", manim_opt_in="standing")
    RF.ready_manim(monkeypatch)
    author = AuthorFake(list(answers))
    ctx = context(paths.root, author=author)
    ctx.library_ask_inline = True
    ctx.figure_find_sources = FindFake()
    rich_author = RF.RichAuthorFake(None)
    services = RunnerServices(figure_rich_client_factory=lambda job: rich_author, figure_rich_renderer=RF.Renders(),
                              figure_function_runner=RF.InProcessRunner())
    ctx.ingest_jobs.bind(ctx.repository, ctx.vault_root, services=services, background=False)
    if not foreground:
        monkeypatch.setattr(ctx.ingest_jobs, "_ensure_worker", lambda: None)
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, {"itemId": "pi_eigen_1", "submissionId": "k1", "sessionId": session}, rich_author


def _rich_jobs(paths: Any) -> list[tuple[str, str]]:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return [(row[0], row[1]) for row in connection.execute(
            "SELECT id, status FROM ingest_jobs WHERE job_type = 'figure_rich' ORDER BY created_at, id")]


def _drain(ctx: Any, monkeypatch: Any) -> None:
    monkeypatch.setattr(ctx.ingest_jobs, "_ensure_worker",
                        type(ctx.ingest_jobs)._ensure_worker.__get__(ctx.ingest_jobs))
    ctx.ingest_jobs._ensure_worker()


def test_s0_an_attempt_host_build_offers_no_rich_tier_and_its_quick_figure_counts_once(tmp_path, monkeypatch):
    """A show me on the answer box, with the rich tiers on and the standing
    Manim opt-in: the author's menu has no rich tier (an answer naming one is
    refused and asked again), no rich job starts, the quick figure has no
    fuller version, and it is one hint-equivalent however often it opens."""

    from tests import rich_fixtures as RF

    paths, ctx, host, rich_author = _rich_attempt(
        tmp_path, monkeypatch,
        [("rich", "manim", RF.brief(), "a narrated video", flagship(kind="illustrative")),
         flagship(kind="illustrative")])
    job = _show_me(ctx, host, goal="show the spiral tighten as the damping grows")
    figure = job["result"]["figure"]
    assert figure is not None and figure["tier"] == "grammar" and "rich" not in job["result"]
    assert figure.get("fuller") is None
    assert job["result"]["help"]["status"] == "counted" and job["result"]["help"]["new"] is True
    assert _rich_jobs(paths) == [] and rich_author.calls == 0
    again = _call(ctx, "figure.open", {"figureId": figure["figureId"], "hostRef": host})
    assert again["help"]["new"] is False and again["figure"].get("fuller") is None
    assert len(_figure_rows(paths)) == 1


def test_s0_an_attempt_host_rich_request_is_refused_at_the_rpc(tmp_path, monkeypatch):
    """A Reader figure with a fuller Manim version: on an attempt host the
    Manim version is never opened, revised or read by its job, and the quick
    figure opens without its fuller version."""

    from tests import rich_fixtures as RF
    from tests.figure_fixtures import EXTRACTION, build

    paths, ctx, host, rich_author = _rich_attempt(
        tmp_path, monkeypatch, [("rich", "manim", RF.brief(), "a narrated video", flagship(kind="illustrative"))])
    quick = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p3"]})["figure"]
    listed = _call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    (line,) = listed["figures"]
    assert line["fuller"]["state"] == "ready"
    manim = line["fuller"]["figure"]["figureId"]
    [(rich_job, _status)] = _rich_jobs(paths)
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "figure.open", {"figureId": manim, "hostRef": host})
    assert caught.value.code == "validation_error"
    # No rich build is read by its job on an attempt host (the parameter is
    # gone: the dispatcher answers ``validation_error`` for it).
    with pytest.raises(pydantic.ValidationError):
        _call(ctx, "figure.open", {"richJobId": rich_job, "hostRef": host})
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "reader.figure_revise", {"figureId": manim, "note": "slower", "hostRef": host})
    assert caught.value.code == "validation_error"
    assert _figure_rows(paths) == []
    opened = _call(ctx, "figure.open", {"figureId": quick["figureId"], "hostRef": host})
    assert opened["figure"]["fuller"] is None and opened["help"]["status"] == "counted"
    assert rich_author.calls == 1 and len(_figure_rows(paths)) == 1


def test_s0_a_legacy_queued_attempt_rich_job_stops_before_any_model_request(tmp_path, monkeypatch):
    """A rich job queued for an attempt host before this change (its payload
    has no ``attempt_hosted`` flag): the worker resolves the stored request's
    host and stops it before any model request, figure help on or off; it is
    not retried either."""

    from learnloop.db.repositories import Repository
    from learnloop.figures import rich as RICH
    from tests import rich_fixtures as RF
    from tests.figure_fixtures import EXTRACTION, build

    paths, ctx, host, rich_author = _rich_attempt(
        tmp_path, monkeypatch, [("rich", "manim", RF.brief(), "a narrated video")], foreground=False)
    result = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p3"]})
    rich_job = result["rich"]["richJobId"]
    payload = Repository.attach(paths.sqlite_path).get_ingest_job(rich_job)["payload"]
    assert "attempt_hosted" not in (payload.get("base") or {})
    # The request as a pre-change attempt build stored it (figure_requests is
    # append-only: a copy under a new id naming the answer box, and the queued
    # job's payload pointed at it, still without the flag).
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        row = dict(connection.execute("SELECT * FROM figure_requests WHERE id = ?",
                                      (payload["request_id"],)).fetchone())
        row.update(id="fr_legacy_attempt", host_ref_json=json.dumps(
            {"item_id": host["itemId"], "submission_id": host["submissionId"], "session_id": host["sessionId"]},
            sort_keys=True))
        connection.execute(f"INSERT INTO figure_requests ({', '.join(row)}) VALUES ({', '.join('?' for _ in row)})",
                           tuple(row.values()))
        payload = {**payload, "request_id": "fr_legacy_attempt"}
        connection.execute("UPDATE ingest_jobs SET payload_json = ? WHERE id = ?", (json.dumps(payload), rich_job))
        connection.commit()
    assert RICH.attempt_hosted_job(Repository.attach(paths.sqlite_path), payload) is True
    _drain(ctx, monkeypatch)
    assert rich_author.calls == 0
    [(_job, status)] = _rich_jobs(paths)
    assert status == "failed"
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        tiers = [row[0] for row in connection.execute("SELECT tier FROM interactive_figures")]
    assert "manim" not in tiers
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "figure.rich_retry", {"richJobId": rich_job})
    assert caught.value.code == "validation_error"
    assert rich_author.calls == 0 and _figure_rows(paths) == []


def test_s0_an_attempt_hosted_payload_is_refused_by_its_flag_too(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.figures import rich as RICH
    from tests.hint_fakes import hint_vault

    repository = Repository.attach(hint_vault(tmp_path).sqlite_path)
    assert RICH.attempt_hosted_job(repository, {"base": {"attempt_hosted": True}}) is True
    assert RICH.attempt_hosted_job(repository, {"base": {}, "request_id": "fr_missing"}) is False


# ===========================================================================
# Codex re-review (job 20261101-220851-WBO5kk): F1 (F2 and F12 closed by step 0)
# ===========================================================================

def test_rr_f1_a_fresh_key_under_another_open_session_is_refused(tmp_path):
    """Re-review F1: the answer box's session must be the one open session
    (mobile PR-4 keeps exactly one: ``start_session_exclusive``), so a fresh
    key cannot put a figure row under a session its Submit does not fold."""

    author = AuthorFake([neutral_spec() for _ in range(4)])
    paths, ctx, session = _sidecar(tmp_path, author=author)
    _vault, repository = ctx.require_vault()
    other = repository.create_session()
    for host in (_host(other, key="fresh"), _host(session, key="fresh")):
        with pytest.raises(SidecarError) as caught:
            _call(ctx, "figure.request", {"goalText": GOAL, "origin": "ask", "hostRef": host})
        assert caught.value.code == "validation_error"
        with pytest.raises(SidecarError):
            _call(ctx, "figure.take_step", {"itemId": ITEM, "submissionId": host["submissionId"],
                                            "sessionId": host["sessionId"]})
    assert author.calls == 0 and _requests(paths) == [] and _figure_rows(paths) == []
    # The session the learner submits in folds exactly what attached: nothing escaped.
    with repository.connection() as connection:
        connection.execute("UPDATE sessions SET ended_at = '2026-11-01T00:00:00Z' WHERE id = ?", (other,))
        connection.commit()
    attempt = _attempt(paths, _submit(ctx, session, key="fresh")["attemptId"])
    assert attempt["hints_used"] == 0 and _figure_rows(paths) == []


def _copy_attempt(paths: Any, source_key: str, **changes: Any) -> None:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        row = dict(connection.execute("SELECT * FROM practice_attempts WHERE submission_id = ?",
                                      (source_key,)).fetchone())
        row.update(changes)
        columns = ", ".join(row)
        connection.execute(f"INSERT INTO practice_attempts ({columns}) VALUES ({', '.join('?' for _ in row)})",
                           tuple(row.values()))
        connection.commit()


def test_rr_f1_a_committed_key_of_another_item_or_session_is_not_free_feedback(tmp_path):
    """Re-review F1: a committed submission key is feedback only for the
    attempt it committed (this item, and the session named), resolved to that
    attempt; another item's key, or the key under another session, is refused."""

    author = AuthorFake([neutral_spec() for _ in range(4)])
    paths, ctx, session = _sidecar(tmp_path, author=author)
    _submit(ctx, session, key="k0")
    _copy_attempt(paths, "k0", id="att_elsewhere", practice_item_id="pi_elsewhere", submission_id="k_other")
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "figure.request", {"goalText": GOAL, "origin": "ask", "hostRef": _host(session, key="k_other")})
    assert caught.value.code == "validation_error"
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "figure.request", {"goalText": GOAL, "origin": "ask",
                                      "hostRef": {"itemId": ITEM, "submissionId": "k0", "sessionId": "made_up"}})
    assert caught.value.code == "validation_error"
    assert author.calls == 0 and _requests(paths) == []
    # This item's committed key in its own session: free, bound to that attempt.
    job = _show_me(ctx, _host(session, key="k0"))
    assert job["result"]["help"]["host"] == "feedback" and job["result"]["help"]["countsAsHint"] is False
    [request] = _requests(paths)
    assert json.loads(request["host_ref_json"])["attempt_id"] is not None
