"""RW5d P2: the sketch tier through the figure service and its RPCs
(spec_reader_show_me_figures_v1 §6.6, §8.4, §8.5, §9.5; G-SM10, G-SM12, G-SM13, G-SM19).

* With ``figures.sketch_enabled`` the author's contract is
  ``FigureAuthorOutputV2`` under ``+sketch-v1``; a sketch answer is verified
  in the sealed engine and stored as a sketch (tier, spec version, engine
  digest, check lines); every build appends a ``figure_tier`` receipt.
* Off: the contract, the prompt and the reuse key are RW5b's byte for byte,
  no ``figure_tier`` row is written, and a stored sketch lists as
  "can't draw this yet" (and can't be revised or predicted on).
* Engine upgrades re-verify a stored sketch with no model call.
* Predictions on a sketch are decided by code in the engine; never evidence.

Fakes only: the author is injected; no model is reached.
"""

from __future__ import annotations

import json
import sqlite3

import pytest

from learnloop.figures import routes as R
from learnloop.figures import service as FS
from learnloop.figures import sketch as K
from learnloop_sidecar.errors import SidecarError
from tests import sketch_fixtures as F
from tests.figure_fixtures import (
    EXTRACTION,
    LEARNING_STATE_TABLES,
    AuthorFake,
    build,
    build_figure_vault,
    call,
    context,
    counts,
    flagship,
    rows,
    set_config,
)

WHY = "the grammar has no random process with state"


def _setup(tmp_path, answers, *, sketch=True):
    paths, repository = build_figure_vault(tmp_path / "vault", sketch=sketch)
    author = AuthorFake(answers)
    ctx = context(paths.root, author=author)
    return paths, repository, ctx, author


def _switch(paths, on):
    """Set figures.sketch_enabled in the vault's learnloop.toml (once set, rewritten in place)."""

    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    assert "sketch_enabled = " in text
    text = text.replace("sketch_enabled = true", "sketch_enabled = X").replace("sketch_enabled = false",
                                                                              "sketch_enabled = X")
    config.write_text(text.replace("sketch_enabled = X", f"sketch_enabled = {'true' if on else 'false'}"),
                      encoding="utf-8")


def _ledger(repository, task):
    return [row for row in rows(repository, "judgment_ledger") if row["task"] == task]


def test_a_sketch_answer_is_verified_stored_and_shown_with_its_check_lines(tmp_path):
    paths, repository, ctx, author = _setup(tmp_path, [("sketch", F.walk(), WHY)])
    figure = build(ctx)["figure"]
    assert author.calls == 1
    assert figure["tier"] == "sketch" and figure["verification"] == "illustrative"
    assert figure["label"] == FS.SKETCH_LABEL == "AI-written simulation · sandboxed · not checked against the book"
    assert "checked against the book" in figure["label"] and "matches" not in figure["label"]
    sketch = figure["sketch"]
    assert sketch["engineSha256"] and sketch["seed"] == 1 and sketch["settings"] == 27
    assert [check["kind"] for check in sketch["checks"]] == ["equals", "distribution"]
    assert sketch["checks"][0]["elements"] == ["envelope"] and sketch["notCovered"] == ["walkers"]
    program = json.loads(figure["specJson"])
    assert program["program_version"] == "sketch-v1" and "function step" in program["code"]
    (row,) = rows(repository, "interactive_figures")
    assert (row["tier"], row["spec_version"], row["kind"]) == ("sketch", "sketch-v1", "illustrative")
    assert row["engine_sha256"] and row["runtime_digest"].endswith(row["engine_sha256"])
    assert json.loads(row["checks_json"])[0]["statement"] == "sqrt(x)"
    assert row["prompt_version"].endswith(R.SKETCH_SUFFIX)
    (request,) = rows(repository, "figure_requests")
    assert json.loads(request["tiers_allowed_json"]) == ["grammar", "sketch"]


def test_the_tier_judgment_has_a_receipt_with_its_reason(tmp_path):
    """G-SM12 (on): one figure_tier row per build, the author's verdict and why."""

    paths, repository, ctx, author = _setup(tmp_path, [("sketch", F.walk(), WHY)])
    figure = build(ctx)["figure"]
    (tier,) = _ledger(repository, "figure_tier")
    assert (tier["verdict"], tier["judge"], tier["rationale"]) == ("sketch", "llm", WHY)
    assert tier["left_id"] == figure["figureId"] and tier["prompt_version"].endswith(R.SKETCH_SUFFIX)
    assert tier["judge_model"] == "fake-figure-model"
    (verified,) = _ledger(repository, "figure_verified")
    assert verified["verdict"] == "illustrative"


def test_with_the_tier_on_a_spec_answer_is_still_a_grammar_figure_with_a_receipt(tmp_path):
    paths, repository, ctx, author = _setup(tmp_path, [flagship(kind="illustrative")])
    figure = build(ctx)["figure"]
    assert figure["tier"] == "grammar" and figure["sketch"] is None and figure["verification"] == "illustrative"
    assert "SketchProgramV1" in author.prompts[0] and "why_not_spec" in author.prompts[0]
    assert R.STATUS_V2 in R.author_instructions(advanced=True, sketch=True)
    (tier,) = _ledger(repository, "figure_tier")
    assert tier["verdict"] == "spec" and tier["rationale"] == ""
    (row,) = rows(repository, "interactive_figures")
    assert row["tier"] == "grammar" and row["spec_version"] == "ifs-v1"


def test_an_unsupported_answer_records_its_verdict(tmp_path):
    paths, repository, ctx, author = _setup(tmp_path, [("unsupported", "3-D surface")])
    figure = build(ctx)["figure"]
    assert figure["verification"] == "unsupported"
    (tier,) = _ledger(repository, "figure_tier")
    assert tier["verdict"] == "unsupported" and "3-D surface" in tier["rationale"]


def test_off_the_contract_prompt_and_key_are_rw5bs_byte_for_byte(tmp_path):
    """G-SM12 (off): the V1 output model, P1's prompt, no figure_tier row, and
    the same reuse key as before P2."""

    paths, repository, ctx, author = _setup(tmp_path, [flagship(kind="illustrative")], sketch=False)
    figure = build(ctx)["figure"]
    assert "tier" not in figure and "sketch" not in figure
    prompt = author.prompts[0]
    assert "SketchProgramV1" not in prompt and "why_not_spec" not in prompt
    assert R.author_instructions() == R.AUTHOR_INSTRUCTIONS
    assert R.author_prompt_version(sketch=False) == R.AUTHOR_PROMPT_VERSION
    assert R.output_model(sketch=False) is R.FigureAuthorOutputV1
    assert _ledger(repository, "figure_tier") == []
    (row,) = rows(repository, "interactive_figures")
    assert row["prompt_version"] == R.author_prompt_version(advanced=True) == R.ADVANCED_PROMPT_VERSION
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"])
    context_ = FS.SourceContext()
    assert FS.request_hash(request, context_, None) == FS.request_hash(request, context_, None, sketch=False)
    assert FS.request_hash(request, context_, None) != FS.request_hash(request, context_, None, sketch=True)


def test_off_a_stored_sketch_lists_as_cant_draw_this_yet(tmp_path):
    paths, repository, ctx, author = _setup(tmp_path, [("sketch", F.walk(), WHY)])
    built = build(ctx)["figure"]
    _switch(paths, False)
    off = context(paths.root, author=author)
    (listed,) = call(off, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert listed["figureId"] == built["figureId"]
    assert listed["verification"] == "unsupported" and listed["specJson"] is None
    assert listed["label"].startswith("can't draw this yet") and "sketch_enabled" in listed["label"]
    with pytest.raises(SidecarError) as revise:
        call(off, "reader.figure_revise", {"figureId": built["figureId"], "note": "wrong"})
    assert revise.value.code == "sketch_disabled"
    with pytest.raises(SidecarError) as predict:
        call(off, "reader.figure_predict", {"figureId": built["figureId"], "predictionIndex": 0, "answer": "rises"})
    assert predict.value.code == "sketch_disabled"
    assert author.calls == 1


def test_a_failed_sketch_gets_the_second_attempt_with_codes_words(tmp_path):
    wrong = F.planted()[0][1]  # the claim off by a constant
    paths, repository, ctx, author = _setup(tmp_path, [("sketch", wrong, WHY), ("sketch", F.walk(), WHY)])
    figure = build(ctx)["figure"]
    assert author.calls == 2 and figure["verification"] == "illustrative"
    problems = author.contexts[1]["problems_with_the_last_attempt"]
    assert any("the stated sqrt(x) + 1" in problem for problem in problems)


def test_a_sketch_that_fails_twice_is_stored_failed_and_never_shown(tmp_path):
    wrong = F.planted()[0][1]
    paths, repository, ctx, author = _setup(tmp_path, [("sketch", wrong, WHY), ("sketch", wrong, WHY)])
    figure = build(ctx)["figure"]
    assert figure["verification"] == "failed" and figure["specJson"] is None
    assert figure["label"].startswith("couldn't build a reliable version of this")
    (row,) = rows(repository, "interactive_figures")
    assert row["tier"] == "sketch" and row["verification"] == "failed" and row["spec_json"] is None
    assert _ledger(repository, "figure_tier")[0]["verdict"] == "sketch"


def test_a_malformed_program_is_a_problem_for_the_second_attempt(tmp_path):
    paths, repository, ctx, author = _setup(tmp_path, [("sketch", "{not json", WHY), ("sketch", F.spiral(), WHY)])
    figure = build(ctx)["figure"]
    assert figure["verification"] == "illustrative" and author.calls == 2
    assert "not JSON" in author.contexts[1]["problems_with_the_last_attempt"][0]


def test_the_same_request_reuses_the_sketch_with_no_call(tmp_path):
    paths, repository, ctx, author = _setup(tmp_path, [("sketch", F.walk(), WHY)])
    first = build(ctx)["figure"]
    again = build(ctx)
    assert again["reused"] is True and again["figure"]["figureId"] == first["figureId"]
    assert author.calls == 1


def test_switching_the_tier_on_reuses_a_grammar_figure_already_built(tmp_path):
    paths, repository, ctx, author = _setup(tmp_path, [flagship(kind="illustrative")], sketch=False)
    first = build(ctx)["figure"]
    _switch(paths, True)
    on = context(paths.root, author=author)
    again = build(on)
    assert again["reused"] is True and again["figure"]["figureId"] == first["figureId"]
    assert author.calls == 1


def test_an_engine_upgrade_reverifies_with_no_model_call(tmp_path, monkeypatch):
    """G-SM13: a sketch verified under another engine is verified again by
    code before it is shown; one that now fails is never shown as checked."""

    paths, repository, ctx, author = _setup(tmp_path, [("sketch", F.walk(), WHY), ("sketch", F.spiral(), WHY)])
    good = build(ctx)["figure"]
    with repository.connection() as connection:
        connection.execute("UPDATE interactive_figures SET engine_sha256 = 'an-older-engine' WHERE id = ?",
                           (good["figureId"],))
        connection.commit()
    FS._RECHECKED.clear()
    (listed,) = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert listed["verification"] == "illustrative" and listed["sketch"]["checks"]
    assert author.calls == 1
    # Under a "new engine" the stored program fails its own claim.
    import learnloop.figures.sketch_verify as SV

    real = SV.verify_sketch

    def failing(compiled, **kwargs):
        report = real(compiled, **kwargs)
        report.outcome, report.reason = "failed", "claim 1 fails"
        return report

    monkeypatch.setattr(SV, "verify_sketch", failing)
    FS._RECHECKED.clear()
    (listed,) = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert listed["verification"] == "failed" and listed["specJson"] is None
    assert listed["label"] == FS.ENGINE_CHANGED_REASON == "couldn't run under this version · rebuild"
    with pytest.raises(SidecarError):
        call(ctx, "reader.figure_predict", {"figureId": good["figureId"], "predictionIndex": 0, "answer": "rises"})
    assert author.calls == 1


def test_a_sketch_prediction_is_decided_by_code_and_writes_no_evidence(tmp_path):
    paths, repository, ctx, author = _setup(tmp_path, [("sketch", F.walk(), WHY)])
    figure = build(ctx)["figure"]
    (prediction,) = figure["predictions"]
    assert prediction["kind"] == "direction" and prediction["answered"] is None
    before = counts(repository, LEARNING_STATE_TABLES)
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                 "answer": "rises"})
    assert found["matched"] is True and found["answer"] == "rises" and found["before"] == 0.0
    assert counts(repository, LEARNING_STATE_TABLES) == before


def test_not_right_on_a_sketch_sends_the_program_and_the_note(tmp_path):
    paths, repository, ctx, author = _setup(tmp_path, [("sketch", F.walk(), WHY), ("sketch", F.walk(), WHY)])
    first = build(ctx)["figure"]
    note = "this simulation hit an error at these settings: walkers=400 (used its whole work budget)"
    job = call(ctx, "reader.figure_revise", {"figureId": first["figureId"], "note": note})
    kept = ctx.figure_jobs.get(job["jobId"])
    if kept is not None:
        assert kept.done.wait(120)
    earlier = author.contexts[1]["earlier_version"]
    assert "sketch_json" in earlier and "spec_json" not in earlier
    assert json.loads(earlier["sketch_json"])["program_version"] == "sketch-v1"
    assert author.contexts[1]["learner_note"] == note


def test_a_sketch_built_with_nothing_from_the_books_quotes_nothing(tmp_path):
    program = F.walk(source_claims=[{"span_id": "p2", "quote": "made up"}],
                     assumptions=[{"text": "fair steps", "span_id": "p2", "quote": "made up"}])
    raw = FS._ungrounded_sketch(json.dumps(program))
    assert raw["source_claims"] == [] and raw["assumptions"][0]["quote"] is None
    compiled = K.parse_sketch(raw)
    assert compiled.program.source_claims == []


def test_the_report_counts_tiers_verdicts_and_reasons(tmp_path):
    from learnloop.reader.reader_report import build_reader_report

    paths, repository, ctx, author = _setup(tmp_path, [("sketch", F.walk(), WHY)])
    build(ctx)
    call(ctx, "reader.log_activity", {"events": [
        {"kind": "reader_action_invoked", "event": "sketch_paused", "extractionId": EXTRACTION},
        {"kind": "reader_action_invoked", "event": "sketch_error", "extractionId": EXTRACTION,
         "errorKind": "work_cap"}]})
    report = build_reader_report(repository.sqlite_path, figures_enabled=True, figure_sketch_enabled=True)
    tiers = report["figures"]["tiers"]
    assert tiers["built"] == {"sketch": {"illustrative": 1}}
    assert tiers["verdicts"] == {"sketch": 1}
    assert tiers["why_not_spec"] == [{"reason": WHY, "n": 1}]
    assert tiers["sketch_paused"] == 1 and tiers["sketch_errors"] == 1
    off = build_reader_report(repository.sqlite_path, figures_enabled=True)
    assert "tiers" not in off["figures"]


def test_sketch_events_are_salience_only_client_events():
    from learnloop.reader import reader_inquiry as RI

    assert {"sketch_paused", "sketch_error"} <= set(RI.CLIENT_ACTION_EVENTS)
    assert "error_kind" in RI.ACTIVITY_FIELDS and "message" not in RI.ACTIVITY_FIELDS


def test_the_tier_is_off_when_the_engine_cannot_run_here(tmp_path, monkeypatch):
    import learnloop.figures.sketch_engine as E

    paths, repository, ctx, author = _setup(tmp_path, [flagship(kind="illustrative")])
    monkeypatch.setattr(E, "engine_ready", lambda **_: False)
    build(ctx)
    assert "SketchProgramV1" not in author.prompts[0]
    assert _ledger(repository, "figure_tier") == []


def _verdicts(repository):
    """figure_verified rows in the order they were appended (created_at has
    one-second resolution, so two rows of one second tie on it)."""

    with repository.connection() as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = 'figure_verified' ORDER BY rowid")]


def _as_older_engine(repository, figure_id, **report_changes):
    """Make a stored sketch look verified under an earlier engine (and, with
    ``report_changes``, with that engine's report fields)."""

    with repository.connection() as connection:
        (stored,) = connection.execute("SELECT verification_report_json FROM interactive_figures WHERE id = ?",
                                       (figure_id,)).fetchone()
        report = {**json.loads(stored), **report_changes}
        connection.execute("UPDATE interactive_figures SET engine_sha256 = 'an-older-engine', "
                           "verification_report_json = ? WHERE id = ?", (json.dumps(report), figure_id))
        connection.commit()
    FS._RECHECKED.clear()


def test_an_engine_reverification_is_a_verifier_judgment_recorded_once(tmp_path):
    """Codex review F8: the re-verification's verdict reaches judgment_ledger
    before delivery (superseding the build's verdict), keyed by the program
    and the engine, once however often it is listed or the process restarts."""

    from learnloop.figures.sketch_engine import ENGINE_SHA256

    paths, repository, ctx, author = _setup(tmp_path, [("sketch", F.walk(), WHY)])
    figure = build(ctx)["figure"]
    (built,) = _verdicts(repository)
    _as_older_engine(repository, figure["figureId"])
    call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    built_again, rechecked = _verdicts(repository)
    assert built_again["id"] == built["id"]
    assert rechecked["judge"] == "verifier" and rechecked["verdict"] == "illustrative"
    assert rechecked["supersedes_id"] == built["id"] and rechecked["left_id"] == figure["figureId"]
    assert rechecked["input_hash"] == FS.reverify_hash(figure["specJson"], ENGINE_SHA256)
    assert ENGINE_SHA256[:12] in rechecked["rationale"] and "an-older-en" in rechecked["rationale"]
    assert "2 checks" in rechecked["rationale"]
    # Listed again, and after a "restart" (the in-process memory cleared): no second row.
    call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    FS._RECHECKED.clear()
    call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert len(_verdicts(repository)) == 2
    assert author.calls == 1


def test_a_failed_reverification_is_recorded_as_failed(tmp_path, monkeypatch):
    import learnloop.figures.sketch_verify as SV

    paths, repository, ctx, author = _setup(tmp_path, [("sketch", F.walk(), WHY)])
    figure = build(ctx)["figure"]
    _as_older_engine(repository, figure["figureId"])
    real = SV.verify_sketch

    def failing(compiled, **kwargs):
        report = real(compiled, **kwargs)
        report.outcome, report.reason = "failed", "claim 1 fails under this engine"
        return report

    monkeypatch.setattr(SV, "verify_sketch", failing)
    (listed,) = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert listed["verification"] == "failed"
    rechecked = _verdicts(repository)[-1]
    assert rechecked["verdict"] == "failed" and "claim 1 fails under this engine" in rechecked["rationale"]


def test_a_prediction_an_upgrade_made_decidable_can_be_answered(tmp_path):
    """Codex review F9: listing offers what the fresh report keeps, and
    record_prediction admits by the same (rechecked) report, not the stored one."""

    paths, repository, ctx, author = _setup(tmp_path, [("sketch", F.walk(), WHY)])
    figure = build(ctx)["figure"]
    # Under the "older engine" this prediction was undecidable (dropped).
    _as_older_engine(repository, figure["figureId"], dropped_predictions=[0])
    (listed,) = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert [prediction["index"] for prediction in listed["predictions"]] == [0]
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                 "answer": "rises"})
    assert found["matched"] is True


def test_a_prediction_an_upgrade_dropped_is_refused(tmp_path, monkeypatch):
    import learnloop.figures.sketch_verify as SV

    paths, repository, ctx, author = _setup(tmp_path, [("sketch", F.walk(), WHY)])
    figure = build(ctx)["figure"]
    _as_older_engine(repository, figure["figureId"])
    real = SV.verify_sketch

    def dropping(compiled, **kwargs):
        report = real(compiled, **kwargs)
        report.dropped_predictions = [0]
        return report

    monkeypatch.setattr(SV, "verify_sketch", dropping)
    (listed,) = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert listed["predictions"] == []
    with pytest.raises(SidecarError):
        call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "rises"})


def test_a_sketch_prediction_carries_the_step_it_is_graded_at(tmp_path):
    """Codex review F5: the desktop stops playback exactly where the verifier reads."""

    paths, repository, ctx, author = _setup(tmp_path, [("sketch", F.walk(), WHY)])
    (prediction,) = build(ctx)["figure"]["predictions"]
    assert prediction["targetStep"] == 100
