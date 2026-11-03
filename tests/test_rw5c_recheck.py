"""Reader RW5c: stored figures rechecked by code, and *rebuild* (spec §6.6, §10.4; Codex review F3)."""

from __future__ import annotations

import json
from typing import Any

import pytest
from typer.testing import CliRunner

from learnloop.cli.app import app
from learnloop.content.authoring import pf_sandbox
from learnloop.db.stores import figures as store
from learnloop.figures import book_math as BM
from learnloop.figures import service as FS
from learnloop.figures import source_check as SC
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from tests.figure_fixtures import AuthorFake, build, call, context, rows, set_config
from tests.rw5c_fixtures import EXTRACTION, FLAGSHIP_EXPR, FLAGSHIP_TEX, HALF_EXPR, PARAMETERS, build_check_vault, plot, set_switch

sandboxed = pytest.mark.skipif(not pf_sandbox.sandbox_available(), reason="needs bubblewrap")
BOOK = [("s1", "Text", f"The density is $${FLAGSHIP_TEX}$$ for a mixture."), ("s5", "Text", "$f(x)=x$")]
REQUEST = {"extractionId": EXTRACTION, "spanIds": ["s5"]}
DENSITY = {"extractionId": EXTRACTION, "spanIds": ["s1"]}
HALF = plot(HALF_EXPR, parameters=PARAMETERS, low=-3, high=3, stated="f(x)", span="s1")
RIGHT = plot(FLAGSHIP_EXPR, parameters=PARAMETERS, low=-3, high=3, stated="f(x)", span="s1")


def _vault(tmp_path, answers: list[Any]) -> tuple[Any, Any, AuthorFake, Any]:
    paths, repository = build_check_vault(tmp_path / "vault", BOOK)
    author = AuthorFake(answers)
    return paths, repository, author, context(paths.root, author=author)


def _stored_before_rw5c(paths: Any, ctx: Any, params: dict[str, Any]) -> dict[str, Any]:
    """A figure built with the switch off (as every figure before RW5c), then the switch on."""

    set_switch(paths, False)
    figure = build(context(paths.root, author=ctx.figure_author_client), params)["figure"]
    set_switch(paths, True)
    return figure


@sandboxed
def test_a_stored_figure_is_rechecked_with_no_model_client_and_upgrades_in_place(tmp_path):
    paths, repository, author, ctx = _vault(tmp_path, [plot("x")])
    figure = _stored_before_rw5c(paths, ctx, REQUEST)
    assert rows(repository, "figure_source_checks") == []
    ctx = context(paths.root, author=AuthorFake())
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"][0]
    assert listed["sourceCheck"] == {"status": "none", "certificationVersion": SC.CERTIFICATION_VERSION, "reasons": [],
                                     "recheckDue": True, "rebuild": False}
    assert listed["elements"] == []
    job = call(ctx, "reader.figure_recheck", {"figureId": figure["figureId"]})
    if job["state"] == "pending":
        assert ctx.figure_jobs.get(job["jobId"]).done.wait(60)
    assert ctx.figure_author_client.calls == 0 and author.calls == 1
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"][0]
    assert listed["sourceCheck"]["status"] == "checked" and listed["sourceCheck"]["recheckDue"] is False
    assert [element["role"] for element in listed["elements"] if element["id"] == "panels.0.series.0"] == ["book"]
    # None due now.
    assert call(ctx, "reader.figure_recheck", {"figureId": figure["figureId"]})["state"] == "none"


def test_a_certification_bump_rechecks_at_no_paid_cost(tmp_path, monkeypatch):
    paths, repository, author, ctx = _vault(tmp_path, [plot("x")])
    monkeypatch.setattr(pf_sandbox, "sandbox_available", lambda: False)
    figure = build(ctx, REQUEST)["figure"]
    assert figure["sourceCheck"]["recheckDue"] is False
    built_under = SC.CERTIFICATION_VERSION
    monkeypatch.setattr(SC, "CERTIFICATION_VERSION", built_under + 1)
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"][0]
    assert listed["sourceCheck"]["recheckDue"] is True and listed["sourceCheck"]["certificationVersion"] == built_under + 1
    full = store.figure(repository.connection(), figure["figureId"])
    SC.recheck(load_vault(paths.root), repository, full)
    assert [row["certification_version"] for row in rows(repository, "figure_source_checks")] == [built_under, built_under + 1]
    assert author.calls == 1


def _certified_by_the_old_reader(tmp_path) -> tuple[Any, Any, str]:
    """Codex re-review F1: a figure whose ledger holds the "checked" the reader wrote
    before it refused the unbraced radical. KaTeX shows \\sqrt16 x as sqrt(1)*6x; the
    old reader read it whole, so 4*x was stored as matching the book."""

    book = [("a", "Text", r"$f(x)=\sqrt16 x$")]
    paths, repository = build_check_vault(tmp_path / "vault", book)
    ctx = context(paths.root, author=AuthorFake([plot("4*x", stated="f(x)", span="a")]))
    figure = _stored_before_rw5c(paths, ctx, {"extractionId": EXTRACTION, "spanIds": ["a"]})
    assert rows(repository, "figure_source_checks") == []
    element = {"id": "panels.0.series.0", "role": "book", "definition": "f", "tex": "f(x)", "plain": "f(x)",
               "equation": r"f(x)=\sqrt16 x"}
    with repository.connection() as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        store.insert_source_check(connection, {
            "id": "fsc_old_reader", "figure_id": figure["figureId"], "certification_version": 1, "trigger": "build",
            "outcome": SC.CHECKED, "definitions": [], "elements": [element], "reasons": {}, "harness_sha256": "x",
            "reader_version": "book-math-v1", "sympy_version": "x", "duration_ms": 1, "judgment_id": "j_old_reader",
            "created_at": "2026-11-02T00:00:00Z"})
        connection.commit()
    return paths, repository, figure["figureId"]


def test_a_certification_the_old_reader_stored_no_longer_delivers_checked(tmp_path):
    assert SC.CERTIFICATION_VERSION > 1 and BM.READER_VERSION != "book-math-v1"
    paths, _repository, figure_id = _certified_by_the_old_reader(tmp_path)
    ctx = context(paths.root, author=AuthorFake())
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"][0]
    assert listed["figureId"] == figure_id and listed["elements"] == []
    assert listed["sourceCheck"]["status"] == "none" and listed["sourceCheck"]["recheckDue"] is True
    audit = json.loads(CliRunner().invoke(app, ["reader", "figure-checks", "--json", "--vault", str(paths.root)]).output)
    assert audit["figures"] == 0 and audit["checked"] == []


@sandboxed
def test_the_bulk_recheck_replaces_a_certification_the_old_reader_stored(tmp_path):
    paths, repository, figure_id = _certified_by_the_old_reader(tmp_path)
    result = CliRunner().invoke(app, ["reader", "figure-checks", "--recheck", "--json", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["skipped"]["not_due"] == 0 and report["figures"] == 1
    assert report["outcomes"] == {"not_checkable": 1} and report["reasons"].get("function_arg") == 1
    assert report["checked"] == []
    newest = store.latest_source_check(repository.connection(), figure_id, SC.CERTIFICATION_VERSION)
    assert newest["reader_version"] == BM.READER_VERSION and not newest["elements"]
    ctx = context(paths.root, author=AuthorFake())
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"][0]
    assert listed["elements"] == [] and listed["sourceCheck"]["status"] == "none"
    assert listed["sourceCheck"]["recheckDue"] is False


def test_a_recheck_with_the_switch_off_or_turned_off_before_its_write_writes_nothing(tmp_path, monkeypatch):
    paths, repository, _author, ctx = _vault(tmp_path, [plot("x")])
    figure = _stored_before_rw5c(paths, ctx, REQUEST)
    full = store.figure(repository.connection(), figure["figureId"])

    def flip(_payload: dict[str, Any], _sandbox: Any) -> pf_sandbox.SandboxResult:
        set_switch(paths, False)
        return pf_sandbox.SandboxResult(True, output={"sympy_version": "fake", "results": []})

    monkeypatch.setattr(SC, "_run_sandbox", flip)
    monkeypatch.setattr(pf_sandbox, "sandbox_available", lambda: True)
    assert SC.recheck(load_vault(paths.root), repository, full) is None
    assert rows(repository, "figure_source_checks") == []
    assert SC.recheck(load_vault(paths.root), repository, full) is None  # off now: not even started
    assert rows(repository, "figure_source_checks") == []


def test_dry_run_writes_nothing_and_the_cli_reports_by_reason_key(tmp_path, monkeypatch):
    paths, repository, _author, ctx = _vault(tmp_path, [plot("x")])
    monkeypatch.setattr(pf_sandbox, "sandbox_available", lambda: False)
    _stored_before_rw5c(paths, ctx, REQUEST)
    before = {table: rows(repository, table) for table in ("figure_source_checks", "judgment_ledger", "source_block_health")}
    result = CliRunner().invoke(app, ["reader", "figure-checks", "--recheck", "--dry-run", "--json", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["status"] == "ok" and report["dry_run"] is True and report["model_calls"] == 0
    assert report["figures"] == 1 and report["outcomes"] == {"not_checkable": 1}
    assert report["reasons"] == {"sandbox_unavailable": 1}
    assert before == {table: rows(repository, table) for table in before}


@sandboxed
def test_the_cli_rechecks_only_what_is_due_and_lists_each_checked_element(tmp_path):
    paths, repository, _author, ctx = _vault(tmp_path, [plot("x")])
    _stored_before_rw5c(paths, ctx, REQUEST)
    runner = CliRunner()
    first = json.loads(runner.invoke(app, ["reader", "figure-checks", "--recheck", "--json", "--vault", str(paths.root)]).output)
    assert first["outcomes"] == {"checked": 1} and first["elements"]["book"] == 1
    again = json.loads(runner.invoke(app, ["reader", "figure-checks", "--recheck", "--json", "--vault", str(paths.root)]).output)
    assert again["figures"] == 0 and again["skipped"]["not_due"] == 1
    audit = json.loads(runner.invoke(app, ["reader", "figure-checks", "--json", "--vault", str(paths.root)]).output)
    assert audit["checked"][0]["book_equation"] == "f(x)=x" and audit["checked"][0]["page"] == 87
    assert audit["checked"][0]["definition"] == "f" and audit["checked"][0]["definition_tex"] == "x"


@sandboxed
def test_the_audit_lists_no_equation_of_a_source_held_out_after_its_check(tmp_path):
    """Codex review F2: §11.3, a check row is never delivered apart from its figure's protection."""

    from learnloop.vault.writer import upsert_source_set

    paths, repository, _author, ctx = _vault(tmp_path, [plot("x")])
    _stored_before_rw5c(paths, ctx, REQUEST)
    runner = CliRunner()
    assert json.loads(runner.invoke(app, ["reader", "figure-checks", "--recheck", "--json", "--vault", str(paths.root)]).output)["outcomes"] == {"checked": 1}
    before = json.loads(runner.invoke(app, ["reader", "figure-checks", "--json", "--vault", str(paths.root)]).output)
    assert before["checked"][0]["book_equation"] == "f(x)=x" and before["skipped"] == {"withheld": 0}
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra", "title": "x", "members": [
        {"source_id": "src_math", "revision_id": "rev_math", "default_role": "exam"}]})
    result = runner.invoke(app, ["reader", "figure-checks", "--json", "--vault", str(paths.root)])
    assert result.exit_code == 0, result.output
    audit = json.loads(result.output)
    assert audit["checked"] == [] and audit["skipped"] == {"withheld": 1}
    assert audit["figures"] == 0 and audit["outcomes"] == {}
    assert "f(x)=x" not in result.output


@sandboxed
def test_the_report_has_a_source_checks_block_only_while_the_switch_is_on(tmp_path):
    paths, repository, _author, ctx = _vault(tmp_path, [plot("x")])
    figure = build(ctx, REQUEST)["figure"]
    runner = CliRunner()
    block = json.loads(runner.invoke(app, ["reader", "report", "--json", "--vault", str(paths.root)]).output)["figures"]["source_checks"]
    assert block["figures"] == 1 and block["outcomes"] == {"checked": 1} and block["elements"]["book"] == 1
    assert block["latency_ms"]["max"] is not None and block["opened"] == {"with_book": 0, "without": 0}
    assert figure["sourceCheck"]["status"] == "checked"
    set_switch(paths, False)
    off = json.loads(runner.invoke(app, ["reader", "report", "--json", "--vault", str(paths.root)]).output)["figures"]
    assert "source_checks" not in off


def test_dry_run_needs_recheck(tmp_path):
    paths, _repository, _author, _ctx = _vault(tmp_path, [])
    result = CliRunner().invoke(app, ["reader", "figure-checks", "--dry-run", "--vault", str(paths.root)])
    assert result.exit_code == 1 and "goes with --recheck" in result.output


@sandboxed
def test_a_difference_found_at_recheck_gives_the_failed_state_with_rebuild(tmp_path):
    paths, repository, _author, ctx = _vault(tmp_path, [HALF])
    figure = _stored_before_rw5c(paths, ctx, DENSITY)
    assert figure["verification"] == "illustrative"
    full = store.figure(repository.connection(), figure["figureId"])
    SC.recheck(load_vault(paths.root), repository, full)
    listed = call(context(paths.root, author=AuthorFake()), "reader.figures", {"extractionId": EXTRACTION})["figures"][0]
    assert listed["verification"] == "failed" and listed["sourceCheck"]["status"] == "differs"
    assert listed["sourceCheck"]["rebuild"] is True and listed["specJson"] is None
    assert rows(repository, "interactive_figures")[0]["verification"] == "illustrative"
    # Predictions and an attempt's open refuse it too.
    with pytest.raises(FS.FigureRefused):
        FS.shown_figure(load_vault(paths.root), repository, figure["figureId"])


@sandboxed
def test_pressing_rebuild_calls_the_author_and_stores_a_new_version(tmp_path):
    paths, repository, _author, ctx = _vault(tmp_path, [HALF])
    figure = _stored_before_rw5c(paths, ctx, DENSITY)
    full = store.figure(repository.connection(), figure["figureId"])
    SC.recheck(load_vault(paths.root), repository, full)
    rejected_checks = rows(repository, "figure_source_checks")
    rejected_row = rows(repository, "interactive_figures")[0]
    author = AuthorFake([RIGHT])
    ctx = context(paths.root, author=author)
    rebuilt = build(ctx, {"figureId": figure["figureId"], "note": "", "rebuild": True}, rpc="reader.figure_revise")["figure"]
    assert author.calls == 1
    assert rebuilt["figureId"] != figure["figureId"] and rebuilt["supersedesId"] == figure["figureId"]
    sent = author.contexts[0]
    assert sent["learner_note"] == ""
    assert "your definition f differs" in sent["problems_with_the_last_attempt"][0]
    stored = rows(repository, "interactive_figures")
    assert stored[0] == rejected_row and stored[1]["input_hash"] != rejected_row["input_hash"]
    assert rows(repository, "figure_source_checks")[:len(rejected_checks)] == rejected_checks
    assert rebuilt["sourceCheck"]["status"] == "checked" and rebuilt["verification"] == "illustrative"
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert [item["figureId"] for item in listed] == [rebuilt["figureId"]]


@sandboxed
def test_rebuild_is_not_offered_with_revisions_off(tmp_path):
    paths, repository, _author, ctx = _vault(tmp_path, [HALF])
    figure = _stored_before_rw5c(paths, ctx, DENSITY)
    full = store.figure(repository.connection(), figure["figureId"])
    SC.recheck(load_vault(paths.root), repository, full)
    set_config(paths, "figures", revisions_enabled=False)
    ctx = context(paths.root, author=AuthorFake())
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"][0]
    assert listed["sourceCheck"]["rebuild"] is False
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_revise", {"figureId": figure["figureId"], "note": "", "rebuild": True})
    assert caught.value.code == "revisions_disabled"


def test_rebuild_of_a_figure_with_no_difference_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(pf_sandbox, "sandbox_available", lambda: False)
    paths, _repository, _author, ctx = _vault(tmp_path, [plot("x")])
    figure = build(ctx, REQUEST)["figure"]
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_revise", {"figureId": figure["figureId"], "note": "", "rebuild": True})
    assert caught.value.code == "validation_error"


def test_the_reuse_key_is_unchanged_without_a_source_check_id():
    context_ = FS.SourceContext(passage=[{"span_id": "a", "type": "Text", "text": "x"}])
    plain = FS.FigureRequest(extraction_id="e", span_ids=["a"])
    rebuilt = FS.FigureRequest(extraction_id="e", span_ids=["a"], source_check_id="fsc_1")
    other = FS.FigureRequest(extraction_id="e", span_ids=["a"], source_check_id="fsc_2")
    hashes = {FS.request_hash(request, context_, None) for request in (plain, rebuilt, other)}
    assert len(hashes) == 3
    # initial_problems are the answer to the check row: they never key a request by themselves.
    assert FS.request_hash(FS.FigureRequest(extraction_id="e", span_ids=["a"], initial_problems=["x"]), context_, None) \
        == FS.request_hash(plain, context_, None)


@sandboxed
def test_a_prebuilt_figure_nobody_pressed_for_that_differs_lists_nothing(tmp_path, monkeypatch):
    paths, repository, _author, ctx = _vault(tmp_path, [HALF])
    figure = _stored_before_rw5c(paths, ctx, DENSITY)
    with repository.connection() as connection:
        connection.execute("UPDATE interactive_figures SET origin = 'prefetch' WHERE id = ?", (figure["figureId"],))
        connection.commit()
    monkeypatch.setattr(FS, "_prebuilt_pressed", lambda _repository, _row: False)
    full = store.figure(repository.connection(), figure["figureId"])
    SC.recheck(load_vault(paths.root), repository, full)
    assert call(context(paths.root, author=AuthorFake()), "reader.figures", {"extractionId": EXTRACTION})["figures"] == []


@sandboxed
def test_section_figures_leave_a_rejected_figure_out(tmp_path):
    paths, repository, _author, ctx = _vault(tmp_path, [HALF])
    figure = _stored_before_rw5c(paths, ctx, DENSITY)
    vault = load_vault(paths.root)
    assert FS.section_figures(vault, repository, EXTRACTION, lambda span: "sec") != {}
    full = store.figure(repository.connection(), figure["figureId"])
    SC.recheck(vault, repository, full)
    assert FS.section_figures(vault, repository, EXTRACTION, lambda span: "sec") == {}


@sandboxed
def test_a_kept_build_result_read_after_the_switch_turns_off_shows_no_label(tmp_path):
    paths, repository, _author, ctx = _vault(tmp_path, [plot("x", label="the model's name")])
    job = call(ctx, "reader.figure_request", REQUEST)
    kept = ctx.figure_jobs.get(job["jobId"])
    assert kept.done.wait(60)
    set_switch(paths, False)
    ctx.vault = None
    fresh = call(context(paths.root, author=AuthorFake()), "reader.figures", {"extractionId": EXTRACTION})["figures"][0]
    assert "elements" not in fresh and "sourceCheck" not in fresh and "the model's name" in fresh["specJson"]
    view = FS.redelivered_view(load_vault(paths.root), repository, {
        "figure_id": fresh["figureId"], "elements": [{"id": "x"}], "source_check": {"status": "checked"}, "spec_json": "stale",
        "versions": 1})
    assert "elements" not in view and "source_check" not in view and "the model's name" in view["spec_json"]
