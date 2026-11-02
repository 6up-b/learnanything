"""Reader RW5d P3: figures as a help kind (spec_reader_show_me_figures_v1 §6.4, §11.2-§11.4; G-SM15..G-SM18).

* **G-SM15.** A figure opened during an attempt adds exactly one
  hint-equivalent at Submit, however often it is reopened (its job read
  again, ``figure.open``, a "not right?" version); feedback-screen figures
  add none; a figure whose text overlaps the key writes the ``tutor_answer``
  reveal with basis ``figure:<id>``.
* **G-SM16.** On a check on your own: no figure is offered; a request
  without the take step's token is refused under ``cold_attempt`` before
  any model call; the take step converts the attempt first (its row is the
  one hint-equivalent) and the request carrying its token is built under
  ``assisted_practice``.
* **G-SM17.** ``explore_figure`` is an option only with a qualifying
  existing figure (its place in the books treats the item's topic), never
  one built from the item's own blocks; its propensity is logged; never
  offered cold.
* **G-SM18.** ``help_outcomes`` lists ``figure`` deterministically
  (computed twice); the diagnoser's context hashes as before without a
  figure trace, and reads ``+figures-v1`` with one.
* **Switch off** (``figures.help_kind_enabled = false``): no figure in
  attempts, no chooser kind, help outcomes unchanged.

Figures are help, never certification, and never reach the grader. Fakes
only: the figure author, the retrieval and the Decider are injected.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import Any

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.source_retrieval.find_sources import SourceHits
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.figure_fixtures import AuthorFake, flagship, set_config
from tests.hint_fakes import EXPECTED, ITEM, WORK, ChooserFake, WriterFake, assists, hint_vault, prefer, reveals

CONFIG = '[hints]\nchoice_policy = "argmax"\n[figures]\nsketch_enabled = false\nrich_tiers_enabled = false\n'
SELF_GRADE = {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3}
GOAL = "show how the area under 2x grows as the cut point moves"


def neutral_spec() -> dict[str, Any]:
    """A figure whose words share nothing with the CDF item's key (the
    existing overlap check reads them; a shared token writes a reveal)."""

    from learnloop.figures.help import _TEXT_KEYS
    from tests import figure_corpus as FC

    def words(value: Any, keyed: bool = False) -> Any:
        if isinstance(value, str):
            return "zebra stripes" if keyed else value
        if isinstance(value, dict):
            return {key: item if key == "choices" else words(item, keyed or key in _TEXT_KEYS)
                    for key, item in value.items()}
        if isinstance(value, list):
            return [words(item, keyed) for item in value]
        return value

    return words(FC.linear_map_spec())


class FindFake:
    """The grounding retrieval: nothing verified (an illustration, not from the books)."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(self, vault: Any, repository: Any, query: str, **kwargs: Any) -> SourceHits:
        self.calls.append({"query": query, **kwargs})
        return SourceHits(intent="explain", policy="assisted_practice", status="ok", manifest={}, hits=[])


def _call(ctx: Any, name: str, params: dict[str, Any]) -> dict[str, Any]:
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _sidecar(tmp_path, *, author: AuthorFake | None = None, help_on: bool = True):
    paths = hint_vault(tmp_path, config=CONFIG + ("" if help_on else "help_kind_enabled = false\n"))
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = True
    ctx.hint_seed = "e"
    ctx.library_ask_inline = True
    ctx.post_attempt_worker.autostart = False
    ctx.figure_author_client = author or AuthorFake([neutral_spec() for _ in range(8)])
    ctx.figure_find_sources = FindFake()
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


def _host(session: str, key: str = "k1") -> dict[str, Any]:
    return {"itemId": ITEM, "submissionId": key, "sessionId": session}


def _show_me(ctx: Any, host: dict[str, Any], goal: str = GOAL, **params: Any) -> dict[str, Any]:
    job = _call(ctx, "figure.request", {"goalText": goal, "origin": "ask", "hostRef": host, **params})
    if job["state"] == "pending":
        kept = ctx.figure_jobs.get(job["jobId"])
        assert kept is not None and kept.done.wait(60)
        job = _call(ctx, "reader.figure_job", {"jobId": job["jobId"]})
    assert job["state"] == "done", job
    return job


def _submit(ctx: Any, session: str, *, key: str = "k1", hints: int = 0) -> dict[str, Any]:
    return _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": hints, "selfGrade": SELF_GRADE, "submissionId": key})


def _attempt(paths: Any, attempt_id: str) -> dict[str, Any]:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def _figure_rows(paths: Any) -> list[dict[str, Any]]:
    return [row for row in assists(paths.sqlite_path) if row["assist_kind"] == "figure"]


def _requests(paths: Any) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute("SELECT * FROM figure_requests ORDER BY created_at, id")]


# ---------------------------------------------------------------------------
# G-SM15: one hint-equivalent per figure per attempt; feedback adds none; the reveal
# ---------------------------------------------------------------------------

def test_a_figure_on_the_answer_box_adds_one_hint_equivalent_however_often_reopened(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    job = _show_me(ctx, _host(session))
    figure = job["result"]["figure"]
    assert figure["verification"] in ("verified", "illustrative")
    assert job["result"]["help"]["countsAsHint"] is True and job["result"]["help"]["line"] == \
        "a figure on this counts as a hint"
    # Built under assisted_practice for the item, caller kind learner, origin ask; no home.
    [request] = _requests(paths)
    assert (request["origin"], request["policy"], request["caller_kind"]) == ("ask", "assisted_practice", "learner")
    assert json.loads(request["host_ref_json"])["item_id"] == ITEM
    # Read again, opened again, asked again with the same words: still one row.
    _call(ctx, "reader.figure_job", {"jobId": job["jobId"]})
    opened = _call(ctx, "figure.open", {"figureId": figure["figureId"], "hostRef": _host(session)})
    assert opened["figure"]["figureId"] == figure["figureId"] and opened["help"]["new"] is False
    again = _show_me(ctx, _host(session))
    assert again["result"]["figure"]["figureId"] == figure["figureId"]
    rows = _figure_rows(paths)
    assert len(rows) == 1
    [row] = rows
    assert (row["surface"], row["level"], row["counted_by"], row["shown"], row["figure_id"], row["submission_id"]) == (
        "practice", 2, "server", 1, figure["figureId"], "k1")
    result = _submit(ctx, session)
    attempt = _attempt(paths, result["attemptId"])
    assert attempt["hints_used"] == 1 and not attempt["primed"]
    assert _figure_rows(paths)[0]["attempt_id"] == result["attemptId"]


def test_a_not_right_version_is_the_same_figure_for_the_count(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    first = _show_me(ctx, _host(session))["result"]["figure"]
    job = _call(ctx, "reader.figure_revise", {"figureId": first["figureId"], "note": "make the cut point bigger"})
    if job["state"] == "pending":
        assert ctx.figure_jobs.get(job["jobId"]).done.wait(60)
        job = _call(ctx, "reader.figure_job", {"jobId": job["jobId"]})
    revised = job["result"]["figure"]
    assert revised["figureId"] != first["figureId"] and revised["supersedesId"] == first["figureId"]
    assert len(_figure_rows(paths)) == 1
    assert _attempt(paths, _submit(ctx, session)["attemptId"])["hints_used"] == 1


def test_two_different_figures_are_two_hint_equivalents(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    _show_me(ctx, _host(session))
    _show_me(ctx, _host(session), goal="show the density 2x and its CDF side by side")
    assert len(_figure_rows(paths)) == 2
    assert _attempt(paths, _submit(ctx, session)["attemptId"])["hints_used"] == 2


def test_feedback_figures_add_none(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    attempt_id = _submit(ctx, session)["attemptId"]
    before = _attempt(paths, attempt_id)
    job = _show_me(ctx, {"attemptId": attempt_id})
    assert job["result"]["figure"] is not None
    assert job["result"]["help"]["countsAsHint"] is False and job["result"]["help"]["line"] == "show me is free here"
    assert _figure_rows(paths) == []
    assert _attempt(paths, attempt_id) == before
    [request] = _requests(paths)
    assert request["policy"] in ("post_attempt", "assisted_practice")
    # A submission that has committed since is feedback too: free.
    job = _show_me(ctx, _host(session, "k1"), goal="show the density 2x and its CDF side by side")
    assert job["result"]["help"]["countsAsHint"] is False and _figure_rows(paths) == []


def test_a_figure_overlapping_the_key_writes_the_reveal_with_its_basis(tmp_path):
    paths, ctx, session = _sidecar(tmp_path, author=AuthorFake([flagship(demonstrates=EXPECTED)]))
    figure = _show_me(ctx, _host(session))["result"]["figure"]
    [reveal] = [row for row in reveals(paths.sqlite_path) if (row["basis"] or "").startswith("figure:")]
    assert (reveal["source_kind"], reveal["basis"]) == ("tutor_answer", f"figure:{figure['figureId']}")
    assert 0 < reveal["amount"] <= 1
    # Read again: the reveal is written once.
    _call(ctx, "figure.open", {"figureId": figure["figureId"], "hostRef": _host(session)})
    assert len([row for row in reveals(paths.sqlite_path) if (row["basis"] or "").startswith("figure:")]) == 1


def test_a_figure_with_no_overlap_writes_no_reveal(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    _show_me(ctx, _host(session))
    assert [row for row in reveals(paths.sqlite_path) if (row["basis"] or "").startswith("figure:")] == []


def test_the_reveal_text_reads_every_model_written_string_and_the_readouts():
    from learnloop.figures.help import reveal_text

    spec = flagship(demonstrates="the shaded area")
    text = reveal_text({"spec_json": json.dumps(spec), "spec_version": "interactive-figure-spec-v1"})
    assert "the shaded area" in text and "λ > 0 and 0 < p < 1" in text
    assert reveal_text({"spec_json": None}) == ""


def test_the_workbench_fold_counts_a_figure_once():
    from learnloop.db.stores import help_assists as HA

    connection = sqlite3.connect(":memory:")
    connection.executescript(
        "CREATE TABLE help_assists (id TEXT, surface TEXT, assist_kind TEXT, hint_kind TEXT, level INTEGER, "
        "workbench_session_id TEXT, practice_item_id TEXT, attempt_id TEXT, shown INTEGER, counted_by TEXT);"
        "INSERT INTO help_assists VALUES ('a', 'workbench', 'figure', NULL, 2, 'wb1', 'i', NULL, 1, 'server');"
        "INSERT INTO help_assists VALUES ('b', 'workbench', 'check', NULL, NULL, 'wb1', 'i', NULL, 1, 'server');")
    fold = HA.workbench_fold(connection, workbench_session_id="wb1")
    assert (fold.figures, fold.checks, fold.hints) == (1, 1, 2)
    assert set(HA.workbench_assist_ids(connection, workbench_session_id="wb1")) == {"a", "b"}


# ---------------------------------------------------------------------------
# G-SM16: the cold take step and its token
# ---------------------------------------------------------------------------

@pytest.fixture
def cold(monkeypatch):
    from learnloop_sidecar.handlers import figures as FHandler

    monkeypatch.setattr(FHandler, "_item_cold", lambda vault, repository, item_id: True)
    monkeypatch.setattr(FHandler, "take_step_available", lambda vault, repository, item_id: True)
    return FHandler


def test_a_cold_request_without_the_take_step_is_refused_before_any_call(tmp_path, cold):
    author = AuthorFake()
    paths, ctx, session = _sidecar(tmp_path, author=author)
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "figure.request", {"goalText": GOAL, "origin": "ask", "hostRef": _host(session)})
    assert caught.value.code == "take_step_required"
    # A crafted token is refused the same way.
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "figure.request", {"goalText": GOAL, "origin": "ask", "hostRef": _host(session),
                                      "takeStepToken": "ha_made_up"})
    assert caught.value.code == "take_step_required"
    assert author.calls == 0 and _figure_rows(paths) == [] and _requests(paths) == []
    # figure.open on a cold check needs the step too.
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "figure.open", {"figureId": "fig_x", "hostRef": _host(session)})
    assert caught.value.code == "take_step_required"


def test_the_take_step_converts_first_then_the_request_carrying_its_token_is_built(tmp_path, cold):
    paths, ctx, session = _sidecar(tmp_path)
    step = _call(ctx, "figure.take_step", {"itemId": ITEM, "submissionId": "k1", "sessionId": session})
    assert step["needed"] is True and step["banner"] == "Practice with help ◌ — you asked for a figure"
    [row] = _figure_rows(paths)
    assert (row["id"], row["request"], row["figure_id"], row["shown"], row["level"]) == (
        step["token"], "take_step", None, 1, 2)
    # The take step is idempotent per attempt.
    assert _call(ctx, "figure.take_step", {"itemId": ITEM, "submissionId": "k1", "sessionId": session})["token"] \
        == step["token"]
    # Another attempt's token is not this one's.
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "figure.request", {"goalText": GOAL, "origin": "ask", "hostRef": _host(session, "k2"),
                                      "takeStepToken": step["token"]})
    assert caught.value.code == "take_step_required"
    job = _show_me(ctx, _host(session), takeStepToken=step["token"])
    figure = job["result"]["figure"]
    # The take step's row names the figure: still one hint-equivalent.
    [row] = _figure_rows(paths)
    assert row["figure_id"] == figure["figureId"]
    [request] = _requests(paths)
    assert request["policy"] == "assisted_practice"
    assert _attempt(paths, _submit(ctx, session)["attemptId"])["hints_used"] == 1


def test_a_check_that_takes_no_help_refuses_the_take_step(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import figures as FHandler

    monkeypatch.setattr(FHandler, "_item_cold", lambda vault, repository, item_id: True)
    monkeypatch.setattr(FHandler, "take_step_available", lambda vault, repository, item_id: False)
    paths, ctx, session = _sidecar(tmp_path)
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "figure.take_step", {"itemId": ITEM, "submissionId": "k1", "sessionId": session})
    assert caught.value.code == "cold_check"
    assert _figure_rows(paths) == []


def test_no_take_step_is_needed_on_an_open_attempt(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    step = _call(ctx, "figure.take_step", {"itemId": ITEM, "submissionId": "k1", "sessionId": session})
    assert step["needed"] is False and step["token"] is None and _figure_rows(paths) == []


def test_take_step_availability_follows_the_hint_ladders_take_step(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault
    from learnloop_sidecar.handlers.figures import take_step_available

    paths = hint_vault(tmp_path, config=CONFIG)
    # Not a check at all: no take step (an open attempt needs none).
    assert take_step_available(load_vault(paths.root), Repository.attach(paths.sqlite_path), ITEM) is False


# ---------------------------------------------------------------------------
# G-SM17: explore_figure in the chooser
# ---------------------------------------------------------------------------

def _offer(figure_id: str = "fig_offered") -> dict[str, Any]:
    return {"figure_id": figure_id, "label": "a figure to explore", "goal_text": "vary the cut point",
            "kind": "illustrative", "tier": "grammar"}


def _request(**overrides: Any) -> Any:
    from learnloop.hints.service import HintRequestV1

    return HintRequestV1(practice_item_id=ITEM, session_id="s1", submission_id="k1", work_md=WORK, **overrides)


def test_explore_figure_is_offered_only_with_a_qualifying_figure_and_its_propensity_is_logged(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.hints import service as HS
    from learnloop.vault.loader import load_vault

    paths = hint_vault(tmp_path, config='[figures]\nsketch_enabled = false\n')
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    chooser = ChooserFake(prefer("explore_figure@L2", 0.9))
    result = HS.request_hint(vault, repository, _request(), writer_client=WriterFake(),
                             chooser_client_factory=lambda: chooser, seed="e", figure_provider=lambda state: _offer())
    assert result.status == "ready" and result.kind == "explore_figure" and result.level == 2
    assert result.figure["figure_id"] == "fig_offered" and result.as_dict()["figure"]["figure_id"] == "fig_offered"
    assert result.replies == []
    [row] = assists(paths.sqlite_path)
    assert (row["assist_kind"], row["hint_kind"], row["figure_id"], row["chooser"]) == (
        "figure", "explore_figure", "fig_offered", "decider")
    assert row["propensity"] is not None and 0 < row["propensity"] <= 1
    options = json.loads(row["options_json"])["options"]
    assert "explore_figure@L2" in options
    assert "explore_figure@L2" in json.loads(row["probabilities_json"])["kind_level"]


def test_without_a_qualifying_figure_the_option_is_absent_and_named(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.hints import service as HS
    from learnloop.vault.loader import load_vault

    paths = hint_vault(tmp_path, config='[figures]\nsketch_enabled = false\n')
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    HS.request_hint(vault, repository, _request(), writer_client=WriterFake(),
                    chooser_client_factory=lambda: ChooserFake(prefer("next_step@L3", 0.9)), seed="e",
                    figure_provider=lambda state: None)
    [row] = assists(paths.sqlite_path)
    record = json.loads(row["options_json"])
    assert "explore_figure@L2" not in record["options"] and record["excluded"]["explore_figure@L2"] == "no_figure"


def test_with_no_provider_every_request_is_as_before(tmp_path):
    """The switch off (no provider given): the options, the record and the
    result are the predecessor's (no explore_figure anywhere, no figure key)."""

    from learnloop.db.repositories import Repository
    from learnloop.hints import service as HS
    from learnloop.vault.loader import load_vault

    paths = hint_vault(tmp_path, config='[figures]\nsketch_enabled = false\n')
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    result = HS.request_hint(vault, repository, _request(), writer_client=WriterFake(),
                             chooser_client_factory=lambda: ChooserFake(prefer("next_step@L3", 0.9)), seed="e")
    assert "figure" not in result.as_dict()
    [row] = assists(paths.sqlite_path)
    assert "explore_figure" not in row["options_json"] and row["figure_id"] is None


def test_the_sidecar_never_offers_a_figure_cold_or_switched_off(tmp_path, monkeypatch):
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault
    from learnloop_sidecar.handlers import figures as FHandler
    from learnloop_sidecar.handlers import hints as HHandler

    paths = hint_vault(tmp_path, config=CONFIG)
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    item = vault.practice_items[ITEM]
    seen: list[str] = []
    monkeypatch.setattr("learnloop.figures.help.qualifying_figure",
                        lambda *args, **kwargs: seen.append("asked") or {"id": "fig_q", "kind": "illustrative"})
    provider = HHandler._figure_provider(vault, repository, item)
    state = type("S", (), {"earlier": []})()
    assert provider is not None and provider(state)["figure_id"] == "fig_q"
    monkeypatch.setattr(FHandler, "_item_cold", lambda vault, repository, item_id: True)
    assert provider(state) is None and seen == ["asked"]
    set_config(paths, "figures", help_kind_enabled=False)
    assert HHandler._figure_provider(load_vault(paths.root), repository, item) is None


def test_a_figure_built_from_the_items_own_blocks_never_qualifies(tmp_path, monkeypatch):
    from learnloop.db.repositories import Repository
    from learnloop.db.stores.judgments import append_judgment
    from learnloop.figures import help as FHelp
    from learnloop.source_retrieval.corpus import Exclusions
    from learnloop.vault.loader import load_vault
    from tests.figure_fixtures import EXTRACTION, build, build_figure_vault, context

    paths, repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake())
    figure = build(ctx, {"extractionId": EXTRACTION, "spanIds": ["p3"]})["figure"]
    vault = load_vault(paths.root)
    item = vault.practice_items["pi_eigen_1"]
    # The figure's section does not treat the item's topic yet.
    assert FHelp.qualifying_figure(vault, repository, item) is None
    with repository.connection() as connection:
        ledger = append_judgment(connection, task="section_coverage", left_kind="learning_object",
                                 left_id=item.learning_object_id, judge="llm", input_hash="h", verdict="develops",
                                 judge_model="m", prompt_version="v")
        section = FHelp._SectionTopics(vault, repository)._section(EXTRACTION, "p3")
        connection.execute(
            "INSERT INTO section_coverage (id, extraction_id, section_id, learning_object_id, treatment, origin, "
            "section_hash, lo_hash, state_key, ledger_id, model, prompt_version, created_at) VALUES "
            "('cov1', ?, ?, ?, 'develops', 'retrieval', 'sh', 'lh', 'sk', ?, 'm', 'v', '2026-11-01T00:00:00Z')",
            (EXTRACTION, section, item.learning_object_id, ledger))
        connection.commit()
    found = FHelp.qualifying_figure(vault, repository, item)
    assert found is not None and found["id"] == figure["figureId"]
    assert FHelp.qualifying_figure(vault, repository, item, exclude_roots=[figure["figureId"]]) is None
    # Built from the item's own passage: never.
    monkeypatch.setattr("learnloop.source_retrieval.corpus.item_exclusions",
                        lambda repository, item: Exclusions(spans=frozenset({(EXTRACTION, "p3")})))
    assert FHelp.qualifying_figure(vault, repository, item) is None


# ---------------------------------------------------------------------------
# G-SM18: help outcomes, the report and the diagnoser's trace
# ---------------------------------------------------------------------------

def _attempt_with_figure(tmp_path, author: AuthorFake | None = None):
    paths, ctx, session = _sidecar(tmp_path, author=author)
    _show_me(ctx, _host(session))
    attempt_id = _submit(ctx, session)["attemptId"]
    return paths, ctx, attempt_id


def test_help_outcomes_list_figure_deterministically_and_not_when_off(tmp_path):
    from learnloop.vault.loader import load_vault
    from learnloop.workbench.help_outcomes import help_outcomes, item_facets_of

    paths, ctx, attempt_id = _attempt_with_figure(tmp_path)
    vault = load_vault(paths.root)
    facets = item_facets_of(vault)[ITEM]
    as_of = "2999-01-01T00:00:00+00:00"
    first = help_outcomes(paths.sqlite_path, facets, as_of, item_facets=item_facets_of(vault), vault=vault)
    second = help_outcomes(paths.sqlite_path, facets, as_of, item_facets=item_facets_of(vault), vault=vault)
    assert first == second
    figures = [entry for entry in first.helps if entry.help == "figure"]
    assert figures and {entry.kind for entry in figures} == {"asked"}
    assert all(entry.shown == 1 and entry.levels[2] == 1 for entry in figures)
    set_config(paths, "figures", help_kind_enabled=False)
    off_vault = load_vault(paths.root)
    off = help_outcomes(paths.sqlite_path, facets, as_of, item_facets=item_facets_of(off_vault), vault=off_vault)
    assert not [entry for entry in off.helps if entry.help == "figure"]


def test_the_hints_report_shows_the_figure_kind_with_its_sample_size(tmp_path):
    from datetime import UTC, datetime

    from learnloop.hints.report import build_hints_report

    paths, _ctx, _attempt_id = _attempt_with_figure(tmp_path)
    now = datetime(2999, 1, 1, tzinfo=UTC)
    report = build_hints_report(paths.sqlite_path, now=now)
    assert report == build_hints_report(paths.sqlite_path, now=now)
    block = report["figures"]
    assert block["shown"] == 1 and block["by_how"] == {"asked": 1, "chooser": 0, "take_step": 0}
    assert block["attempts"] == 1 and block["attempt_correct"]["of"] == 1
    assert block["off_policy_estimate"] is None
    assert any(kind["assist_kind"] == "figure" for kind in report["kinds"])


def test_a_report_with_no_figure_has_no_figure_block(tmp_path):
    from datetime import UTC, datetime

    from learnloop.hints.report import build_hints_report

    paths, ctx, session = _sidecar(tmp_path)
    _submit(ctx, session)
    assert "figures" not in build_hints_report(paths.sqlite_path, now=datetime(2999, 1, 1, tzinfo=UTC))


def test_the_diagnoser_reads_the_figure_trace_under_its_suffix_and_never_the_program(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.diagnosis.split.figure_trace import SUFFIX, figure_trace_for_attempt
    from learnloop.vault.loader import load_vault

    paths, _ctx, attempt_id = _attempt_with_figure(tmp_path)
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    attempt = _attempt(paths, attempt_id)
    trace = figure_trace_for_attempt(vault, repository, attempt)
    assert SUFFIX == "+figures-v1"
    assert trace is not None and len(trace["figures"]) == 1
    [entry] = trace["figures"]
    assert entry["goal"] == GOAL and entry["goal_author"] == "learner" and entry["tier"] == "grammar"
    assert entry["demonstrates"] and "spec_json" not in json.dumps(trace) and "definitions" not in json.dumps(trace)
    # Off: no trace.
    set_config(paths, "figures", help_kind_enabled=False)
    assert figure_trace_for_attempt(load_vault(paths.root), repository, attempt) is None


def test_the_context_hashes_as_before_without_a_figure_trace():
    from learnloop.diagnosis.split.context import CurrentAttempt
    from learnloop.diagnosis.split.contract import diagnosis_prompt_version

    base = dict(attempt_id="a1", learning_object_id="lo", practice_item_id="pi", completed_at="2026-11-01",
                surface_group="g", item_prompt="p", reference_solution="r", rubric=(), trace_contract=None,
                learner_answer_md="x", blind_grade={"error_attributions": []})
    without = CurrentAttempt(**base)
    rendered = without.render()
    assert "figure_trace" not in rendered
    assert CurrentAttempt(**base, figure_trace=None).render() == rendered
    trace = {"note": "n", "figures": [{"order": 1, "goal": "g"}]}
    with_trace = CurrentAttempt(**base, figure_trace=trace).render()
    assert with_trace["figure_trace"] == trace
    assert {key: value for key, value in with_trace.items() if key != "figure_trace"} == rendered

    class Assembled:
        def __init__(self, current: dict[str, Any]) -> None:
            self.current = current
            self.receipt = {}

    assert diagnosis_prompt_version(Assembled(rendered)).endswith("+figures-v1") is False
    assert diagnosis_prompt_version(Assembled(with_trace)).endswith("+figures-v1")


# ---------------------------------------------------------------------------
# The switch off: today, byte for byte
# ---------------------------------------------------------------------------

def test_switched_off_no_figure_in_attempts(tmp_path):
    author = AuthorFake()
    paths, ctx, session = _sidecar(tmp_path, author=author, help_on=False)
    contract = _call(ctx, "reader.prompt_contract", {})
    assert "help" not in (contract.get("figures") or {})
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "figure.request", {"goalText": GOAL, "origin": "ask", "hostRef": _host(session)})
    assert caught.value.code == "figures_help_disabled"
    with pytest.raises(SidecarError) as caught:
        _call(ctx, "figure.take_step", {"itemId": ITEM, "submissionId": "k1", "sessionId": session})
    assert caught.value.code == "figures_help_disabled"
    assert author.calls == 0 and _figure_rows(paths) == [] and _requests(paths) == []
    assert _attempt(paths, _submit(ctx, session)["attemptId"])["hints_used"] == 0


def test_attempt_host_references_are_refused_from_any_other_origin(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    for params in ({"goalText": GOAL, "origin": "show_me", "hostRef": _host(session),
                    "readingAt": {"extractionId": "x", "spanId": "y"}},
                   {"goalText": GOAL, "origin": "ask", "hostRef": _host(session),
                    "anchor": {"extractionId": "x", "spanIds": ["y"]}},
                   {"goalText": GOAL, "origin": "ask", "hostRef": {"itemId": ITEM}},
                   {"goalText": GOAL, "origin": "ask", "hostRef": {"itemId": "pi_missing", "submissionId": "k",
                                                                   "sessionId": session}}):
        with pytest.raises(SidecarError) as caught:
            _call(ctx, "figure.request", params)
        assert caught.value.code in ("validation_error", "span_extraction_mismatch", "not_found"), params
    assert _requests(paths) == []
