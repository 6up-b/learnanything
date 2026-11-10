"""RW5d P2b: the rich tiers through the sidecar (spec §6.8, §8.6, §9b.3, §12.3; G-SM21, G-SM22).

* The prompt contract carries ``figures.rich`` (the Manim opt-in's state)
  only while the rich tiers are on.
* ``figure.manim_opt_in``: "allow" writes the standing opt-in with its date;
  "not now" writes "declined"; allowing where Manim can't run is refused.
* A press with Manim on the menu builds the quick figure and starts the rich
  job on the durable queue; ``reader.figures`` shows the fuller line; a
  rich-only press answers with its pending line.
* Origin (SM9): a granted press's job carries its token and action; without a
  grant it carries neither (no offer, no grant honoured). A plan-waiting job
  is asked again by a later read, at most once per interval, and no response
  carries an offer for it.
* ``figure.rich_cancel`` cancels only the rich job; ``figure.rich_retry``
  requeues a rich-only build that ended with no row (Codex review F9).
* A read recovers a rich job whose enqueue never happened (F8), and "not
  right?" on an animation goes to the rich author or, asked for a different
  kind, back to the tier choice (F11).

Fakes only: the authors, the renderer and the function runner are injected;
the queue drains in the foreground.
"""

from __future__ import annotations

import pytest

from learnloop.ai import plan_fallback
from learnloop.ai.errors import AIProviderUnavailable
from learnloop.content.pipeline.runner import RunnerServices
from learnloop.figures import rich as RICH
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from tests import rich_fixtures as RF
from tests.figure_fixtures import EXTRACTION, AuthorFake, build, build_figure_vault, call, context, flagship
from tests.figure_fixtures import set_config

WHY = "a narrated video shows the spiral tighten"


def _ctx(tmp_path, monkeypatch, author_answers=(), rich_answers=None, *, opt_in="standing", rich=True,
         foreground=True):
    paths, repository = build_figure_vault(tmp_path / "vault", rich=rich)
    if opt_in is not None:
        set_config(paths, "figures", manim_opt_in=opt_in)
    RF.ready_manim(monkeypatch)
    author = AuthorFake(list(author_answers))
    ctx = context(paths.root, author=author)
    rich_author = RF.RichAuthorFake(rich_answers)
    services = RunnerServices(figure_rich_client_factory=lambda job: rich_author, figure_rich_renderer=RF.Renders(),
                              figure_function_runner=RF.InProcessRunner())
    ctx.ingest_jobs.bind(ctx.repository, ctx.vault_root, services=services, background=False)
    if not foreground:
        monkeypatch.setattr(ctx.ingest_jobs, "_ensure_worker", lambda: None)
    return paths, repository, ctx, author, rich_author


def _contract(ctx):
    return call(ctx, "reader.prompt_contract", {}).get("figures") or {}


def test_the_contract_carries_the_rich_state_only_while_on(tmp_path, monkeypatch):
    _paths, _repository, ctx, _author, _rich = _ctx(tmp_path, monkeypatch, opt_in=None)
    assert _contract(ctx)["rich"] == {"manimOptIn": "ask"}
    _paths, _repository, off, _author, _rich = _ctx(tmp_path / "off", monkeypatch, rich=False)
    assert "rich" not in _contract(off)


def test_the_standing_opt_in_is_written_once_with_its_date(tmp_path, monkeypatch):
    paths, _repository, ctx, _author, _rich = _ctx(tmp_path, monkeypatch, opt_in=None)
    assert call(ctx, "figure.manim_opt_in", {"choice": "allow"})["manimOptIn"] == "standing"
    config = load_vault(paths.root).config.figures
    assert config.manim_opt_in == "standing" and len(config.manim_opt_in_at or "") == 10
    assert _contract(ctx)["rich"] == {"manimOptIn": "standing"}
    assert call(ctx, "figure.manim_opt_in", {"choice": "decline"})["manimOptIn"] == "declined"
    assert load_vault(paths.root).config.figures.manim_opt_in == "declined"


def test_allowing_where_manim_cannot_run_is_refused(tmp_path, monkeypatch):
    paths, _repository, ctx, _author, _rich = _ctx(tmp_path, monkeypatch, opt_in=None)
    monkeypatch.setattr(RICH, "manim_runtime_state", lambda vault, probe=True: {"ready": False, "reason": "no_bwrap",
                                                                                "version": None})
    with pytest.raises(SidecarError) as refused:
        call(ctx, "figure.manim_opt_in", {"choice": "allow"})
    assert refused.value.code == "manim_unavailable"
    assert load_vault(paths.root).config.figures.manim_opt_in is None
    assert "rich" not in _contract(ctx)  # where Manim can't run, the contract is P2's


def test_a_press_builds_the_quick_figure_and_the_fuller_one_lands_under_it(tmp_path, monkeypatch):
    _paths, repository, ctx, author, rich_author = _ctx(
        tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    result = build(ctx)
    quick = result["figure"]
    assert quick["tier"] == "grammar" and quick["verification"] == "illustrative"
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    (line,) = listed["figures"]
    assert listed["richPending"] == []
    assert line["figureId"] == quick["figureId"] and line["fuller"]["state"] == "ready"
    assert line["fuller"]["figure"]["manim"]["mediaFileName"].startswith("sha256-")
    assert author.calls == 1 and rich_author.calls == 1
    # The response names no batch: nothing in it can carry another unit's offer.
    assert "batchId" not in str(listed) and "fallbackAvailable" not in str(listed)


def test_a_rich_only_press_answers_with_its_pending_line(tmp_path, monkeypatch):
    _paths, _repository, ctx, _author, rich_author = _ctx(
        tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], foreground=False)
    result = build(ctx)
    assert result["figure"] is None and result["rich"]["state"] == "pending"
    assert result["rich"]["anchorSpanId"] == "p3" and result["rich"]["phase"] == "writing"
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert listed["figures"] == [] and listed["richPending"][0]["richJobId"] == result["rich"]["richJobId"]
    # Cancel: only the rich job; nothing stored, no rich call.
    cancelled = call(ctx, "figure.rich_cancel", {"richJobId": result["rich"]["richJobId"]})
    assert cancelled["state"] == "cancelled"
    assert call(ctx, "reader.figures", {"extractionId": EXTRACTION})["richPending"] == []
    assert rich_author.calls == 0


def test_a_granted_press_carries_its_token_and_action_to_the_rich_job(tmp_path, monkeypatch):
    _paths, _repository, ctx, _author, _rich = _ctx(
        tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))], foreground=False)
    token = plan_fallback.GrantToken(str(ctx.vault_root.resolve()), "figure.request")
    monkeypatch.setattr(plan_fallback, "unit_token", lambda root: token)
    monkeypatch.setattr(plan_fallback, "unit_origin", lambda: "figure.request")
    seen = []
    original = ctx.ingest_jobs.enqueue_figure_rich
    monkeypatch.setattr(ctx.ingest_jobs, "enqueue_figure_rich",
                        lambda **kwargs: seen.append(kwargs) or original(**kwargs))
    build(ctx, {"goalText": "the spiral", "origin": "show_me", "anchor": {"extractionId": EXTRACTION,
                                                                        "spanIds": ["p3"]}}, rpc="figure.request")
    (spawned,) = seen
    assert spawned["grant"] == token and spawned["origin"] == "figure.request"


def test_without_a_grant_the_job_belongs_to_no_action_waits_and_a_read_asks_again(tmp_path, monkeypatch):
    _paths, repository, ctx, _author, rich_author = _ctx(
        tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))],
        [AIProviderUnavailable("usage limit reached"), RF.scene_output()])
    seen = []
    original = ctx.ingest_jobs.enqueue_figure_rich
    monkeypatch.setattr(ctx.ingest_jobs, "enqueue_figure_rich",
                        lambda **kwargs: seen.append(kwargs) or original(**kwargs))
    monkeypatch.setattr(RICH, "_LAST_REQUEUE", {})
    retried = []
    original_retry = ctx.ingest_jobs.retry_figure_rich
    monkeypatch.setattr(ctx.ingest_jobs, "retry_figure_rich",
                        lambda job_id, **kwargs: retried.append(job_id) or original_retry(job_id, **kwargs))
    calls = iter([0.0, 10.0])
    monkeypatch.setattr(RICH.time, "monotonic", lambda: next(calls, 10_000.0))
    build(ctx)
    (spawned,) = seen
    assert spawned["grant"] is None and spawned["origin"] is None
    (job,) = repository.ingest_jobs_by_types(["figure_rich"])
    assert job["status"] == "failed" and job["error"]["code"] == RICH.WAITING_FOR_PLAN
    # The read asks the plan again (the plan is back: the fuller one lands); no offer in any response.
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert retried == [job["id"]] and "fallbackAvailable" not in str(listed)
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert listed["figures"][0]["fuller"]["state"] == "ready" and rich_author.calls == 2


def test_cancelling_an_unknown_or_other_job_is_refused(tmp_path, monkeypatch):
    _paths, _repository, ctx, _author, _rich = _ctx(tmp_path, monkeypatch)
    with pytest.raises(SidecarError) as missing:
        call(ctx, "figure.rich_cancel", {"richJobId": "ijob_nope"})
    assert missing.value.code == "not_found"


def test_switched_off_the_rpcs_refuse_and_the_listing_has_no_rich_key(tmp_path, monkeypatch):
    _paths, _repository, ctx, _author, _rich = _ctx(tmp_path, monkeypatch, rich=False)
    for name, params in (("figure.rich_cancel", {"richJobId": "x"}), ("figure.rich_retry", {"richJobId": "x"}),
                         ("figure.manim_opt_in", {"choice": "allow"})):
        with pytest.raises(SidecarError) as refused:
            call(ctx, name, params)
        assert refused.value.code == "rich_disabled"
    assert "richPending" not in call(ctx, "reader.figures", {"extractionId": EXTRACTION})


def test_rich_build_cancelled_is_a_salience_only_event_without_words(tmp_path, monkeypatch):
    from learnloop.attempts import salience_firewall as SF
    from learnloop.reader import reader_inquiry as RI

    _paths, repository, ctx, _author, _rich = _ctx(
        tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], foreground=False)
    result = build(ctx)
    call(ctx, "figure.rich_cancel", {"richJobId": result["rich"]["richJobId"]})
    (row,) = [row for row in repository.reader_interaction_events(kind="reader_action_invoked")
              if row["payload"].get("event") == "rich_build_cancelled"]
    assert row["payload"]["authority_class"] == SF.SALIENCE_ONLY and row["payload"]["tier"] == "manim"
    assert "rich_build_cancelled" in RI.RW5D_SERVER_EVENTS
    assert {"fuller_version_opened", "quick_version_opened"} <= set(RI.CLIENT_ACTION_EVENTS)
    assert not set(RI.RW5D_SERVER_EVENTS) & set(RI.CLIENT_ACTION_EVENTS)


def test_an_interrupted_rich_only_build_reads_as_failed_and_rich_retry_requeues_it(tmp_path, monkeypatch):
    """Codex review F9 through the sidecar: the failed line, then ``figure.rich_retry``."""

    from learnloop.content.pipeline.runner import IngestRunner

    _paths, repository, ctx, author, rich_author = _ctx(
        tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], foreground=False)
    result = build(ctx)
    job_id = result["rich"]["richJobId"]
    with repository.connection() as connection:
        connection.execute("UPDATE ingest_jobs SET status = 'running', worker_id = 'dead', attempt_count = 1, "
                           "heartbeat_at = '2000-01-01T00:00:00Z' WHERE id = ?", (job_id,))
        connection.commit()
    IngestRunner(repository, vault_root=ctx.vault_root, worker_id="w2").recover_stale_leases()
    (line,) = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["richPending"]
    assert line["state"] == "failed" and line["reason"] == "interrupted when LearnLoop stopped"
    # The queue drains in the foreground again: the retry runs the job.
    monkeypatch.setattr(ctx.ingest_jobs, "_ensure_worker", type(ctx.ingest_jobs)._ensure_worker.__get__(ctx.ingest_jobs))
    assert call(ctx, "figure.rich_retry", {"richJobId": job_id})["state"] == "pending"
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert listed["richPending"] == [] and listed["figures"][0]["tier"] == "manim"
    assert author.calls == 1 and rich_author.calls == 1
    with pytest.raises(SidecarError) as again:
        call(ctx, "figure.rich_retry", {"richJobId": job_id})
    assert again.value.code == "not_failed"


def test_reading_a_source_starts_a_rich_job_whose_enqueue_never_happened(tmp_path, monkeypatch):
    """Codex review F8 through the sidecar: the read recovers the durable intent, with no grant."""

    from learnloop.figures import service as FS

    _paths, repository, ctx, _author, rich_author = _ctx(
        tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    monkeypatch.setattr(FS._RichSpawn, "after_quick", lambda self, *args, **kwargs: None)
    seen = []
    original = ctx.ingest_jobs.enqueue_figure_rich
    monkeypatch.setattr(ctx.ingest_jobs, "enqueue_figure_rich",
                        lambda **kwargs: seen.append(kwargs) or original(**kwargs))
    build(ctx)
    assert seen == []
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    (spawned,) = seen
    assert spawned["grant"] is None and spawned["origin"] is None
    assert spawned["payload"]["build_mode"] == "recovered"
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert listed["figures"][0]["fuller"]["state"] == "ready" and rich_author.calls == 1
    call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert len(seen) == 1


@pytest.mark.parametrize("different_kind", [False, True])
def test_not_right_on_an_animation_through_the_sidecar(tmp_path, monkeypatch, different_kind):
    """Codex review F11: ``reader.figure_revise`` on a Manim figure (and its "different kind" escape)."""

    _paths, repository, ctx, author, rich_author = _ctx(
        tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY), flagship(kind="illustrative")])
    build(ctx)
    (first,) = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    params = {"figureId": first["figureId"], "note": "red please"}
    if different_kind:
        params["differentKind"] = True
    job = call(ctx, "reader.figure_revise", params)
    kept = ctx.figure_jobs.get(job["jobId"])
    assert kept is not None and kept.done.wait(120)
    result = call(ctx, "reader.figure_job", {"jobId": job["jobId"]})["result"]
    (line,) = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert line["supersedesId"] == first["figureId"] and line["versions"] == 2
    if different_kind:
        assert author.calls == 2 and rich_author.calls == 1 and line["tier"] == "grammar"
        assert result["figure"]["tier"] == "grammar"
    else:
        assert author.calls == 1 and rich_author.calls == 2 and line["tier"] == "manim"
        assert result["figure"] is None and result["rich"]["state"] == "pending"
        assert rich_author.contexts[1]["learner_note"] == "red please"


def test_a_failed_animation_correction_reads_as_failed_and_rich_retry_asks_again(tmp_path, monkeypatch):
    """Codex re-review F14 through the sidecar: the correction's failed line
    (the earlier animation stays), then ``figure.rich_retry`` asks afresh."""

    wrong = RF.scene_output(declared={**RF.DECLARED, "claims": [
        {"kind": "equals", "function": "x", "expr": "exp(a*t)*sin(b*t)"}]})
    _paths, _repository, ctx, author, rich_author = _ctx(
        tmp_path, monkeypatch, [("rich", "manim", RF.brief(), WHY)], [RF.scene_output(), wrong, wrong])
    build(ctx)
    (first,) = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    job = call(ctx, "reader.figure_revise", {"figureId": first["figureId"], "note": "red please"})
    kept = ctx.figure_jobs.get(job["jobId"])
    assert kept is not None and kept.done.wait(120)
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert [figure["figureId"] for figure in listed["figures"]] == [first["figureId"]]
    (line,) = listed["richPending"]
    assert line["state"] == "failed" and line["reason"]
    retried = call(ctx, "figure.rich_retry", {"richJobId": line["richJobId"]})
    assert retried["state"] == "pending" and retried["richJobId"] != line["richJobId"]
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert listed["richPending"] == []
    (shown,) = listed["figures"]
    assert shown["supersedesId"] == first["figureId"] and shown["verification"] == "illustrative"
    assert author.calls == 1 and rich_author.calls == 4
