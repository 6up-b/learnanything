"""Reader RW5d P3, Codex review (docs/reviews/reader-rw5d-p3-figures-help-codex-review.md).

* **F1.** The answer box's practice session is resolved on the server (it
  exists, is open, this device owns it, and the submission key is not
  another session's), and a cold take step's token is bound to that identity.
* **F2.** The reveal reads what each tier shows: a Manim figure's narration
  and its ``Text``/``MathTex`` arguments by AST, a JS animation's literals,
  a grammar figure's shaded areas, all formatted as the desktop's panels
  format them.
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
# F2: the reveal reads what each tier shows, as it is formatted
# ---------------------------------------------------------------------------

SCENE = '''from manim import *

class Area(Scene):
    def construct(self):
        title = Text("the area under the curve")
        value = MathTex("0.25")
        self.play(Write(title), Write(value))
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


def test_f2_a_manim_figure_reveals_its_shown_words_and_narration():
    from learnloop.figures.help import reveal_text

    text = reveal_text(_manim_row())
    assert "0.25" in text and "the area under the curve" in text
    # Narration states the key: read too.
    assert "P(X <= 1/2) = 1/4" in reveal_text(_manim_row(narration_md="So P(X <= 1/2) = 1/4.",
                                                         scene_code="class A(Scene):\n    pass\n"))
    # Program structure (class names, radii) is never text; the brief is not shown.
    neutral = reveal_text(_manim_row(scene_code="class A(Scene):\n    def construct(self):\n"
                                               "        self.add(Circle(radius=0.25))\n"))
    assert "0.25" not in neutral and "Circle" not in neutral and neutral.split("\n").count("b") == 0


def test_f2_a_manim_figure_stating_the_key_overlaps_it_and_a_neutral_one_does_not(tmp_path):
    from learnloop.hints import service as hint_service
    from learnloop.figures.help import reveal_text
    from learnloop.vault.loader import load_vault
    from tests.hint_fakes import hint_vault

    item = load_vault(hint_vault(tmp_path).root).practice_items[ITEM]
    stated = _manim_row(scene_code=f'class A(Scene):\n    def construct(self):\n'
                                   f'        self.add(MathTex("{item.expected_answer}"))\n')
    assert hint_service.reveal_amount(item, reveal_text(stated)) > 0
    assert hint_service.reveal_amount(item, reveal_text(_manim_row(
        scene_code="class A(Scene):\n    def construct(self):\n        self.add(Circle())\n"))) == 0


def test_f2_a_js_animation_reads_its_html_and_js_literals():
    from learnloop.figures.help import reveal_text

    spec = {"demonstrates": "zebra", "html": "<div id='a'>area = 0.25</div>", "js": "label.textContent = `F(1/2)`;"}
    text = reveal_text({"spec_json": json.dumps(spec), "spec_version": "js-anim-v1"})
    assert "a" in text.split("\n") and "F(1/2)" in text


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
