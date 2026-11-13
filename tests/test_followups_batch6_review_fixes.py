"""Follow-ups batch 6, Codex review fixes F1-F4.

F1: a prebuild's rich job left waiting for the plan is never asked again, and never sends or
stores, while its saved context touches the own passage of an item under a live administration
(spec §10b.2, G-SM29), even when that administration started after the job first met the limit.
F2: the pass's retry bound counts requeues, not candidates: a paced job never holds the slot of a
due one. F3: the suggestion report's R_cold comparison is labelled an observed-outcome
comparison, never an ITT estimate. F4: a card carrying the new released line says so in its
version.

Fakes only: the judge, the authors, the renderer and the power reader are injected; no network.
"""

from __future__ import annotations

import json

import pytest

from learnloop.algorithm_versions import LESSON_SUGGESTIONS_ALGORITHM_VERSION
from learnloop.ai.errors import AIProviderUnavailable
from learnloop.figures import power as P
from learnloop.figures import prefetch as PF
from learnloop.figures import rich as RICH
from learnloop.figures import service as FS
from learnloop.router import suggestion_report as SR
from learnloop.vault.loader import load_vault
from tests import rich_fixtures as RF
from tests.figure_fixtures import EXTRACTION, call, set_config
from tests.teacher_te1b_landing_r2_helpers import _start, _today
from tests.teacher_te1b_suggestions_helpers import _clock, _vault, no_network, shown  # noqa: F401
from tests.followups_batch6_prefetch_plan_wait_helpers import (
    _due_now,
    _env,
    _pass,
    _prebuild_jobs,
    _rig,
    _waiting,
)


@pytest.fixture(autouse=True)
def mains(monkeypatch):
    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    monkeypatch.setattr(RICH, "_LAST_REQUEUE", {})
    yield
    P.set_power_reader(None)


# --- F1: a cold check that starts after the plan wait --------------------------------------------


def _cold_on(monkeypatch, vault, span: str) -> str:
    """From now on, one of the vault's items is under an open cold check whose own passage
    (its worked answer) is ``span`` of the prebuild's source."""

    from learnloop import learner_protection as LP
    from learnloop.source_retrieval import corpus

    item_id = sorted(vault.practice_items)[0]
    real = LP.withheld_items

    def withheld(v, r):
        found = real(v, r)
        return LP.Withheld(reasons={**found.reasons, item_id: LP.WITHHELD_COLD}, known_items=found.known_items,
                           exam=found.exam)

    monkeypatch.setattr(LP, "withheld_items", withheld)
    monkeypatch.setattr(corpus, "item_exclusions", lambda repository, item: corpus.Exclusions(
        spans=frozenset({(EXTRACTION, span)}) if item.id == item_id else frozenset()))
    return item_id


def _due(job_id: str) -> None:
    """The job's retry is due now (never asked in this process, or its interval passed)."""

    RICH._LAST_REQUEUE.pop(job_id, None)


def _waiting_rig(tmp_path, monkeypatch):
    unavailable = AIProviderUnavailable("usage limit reached")
    paths, repository, ctx, rich_author = _rig(tmp_path, monkeypatch, [unavailable, RF.scene_output()])
    _pass(ctx, "tutor:q1")
    (job,) = _prebuild_jobs(repository)
    assert _waiting(job) and rich_author.calls == 1
    return paths, repository, ctx, rich_author, job


def _neighbour(job) -> str:
    """A paragraph the author was sent beside the prebuild's passage (its saved context)."""

    base = job["payload"]["base"]
    others = [span for span in base["input_span_ids"] if span not in base["span_ids"]]
    assert others, base
    return others[0]


def test_f1_the_pass_never_requeues_a_plan_wait_whose_context_a_cold_check_now_covers(tmp_path, monkeypatch):
    paths, repository, ctx, rich_author, job = _waiting_rig(tmp_path, monkeypatch)
    # The cold reservation starts after the initial plan failure, on a paragraph of the saved context.
    _cold_on(monkeypatch, load_vault(paths.root), _neighbour(job))
    _due(job["id"])
    retried: list[str] = []
    result = PF.PassResult("ok", "offer")
    PF.retry_plan_waits(_env(paths, repository, retried), result)
    assert retried == [] and result.plan_wait_retries == []
    # Through the real pass too: nothing is asked, nothing is sent.
    later = _pass(ctx, "tutor:q2")
    assert later.plan_wait_retries == [] and rich_author.calls == 1


def test_f1_the_readers_read_never_requeues_it_either(tmp_path, monkeypatch):
    paths, repository, ctx, rich_author, job = _waiting_rig(tmp_path, monkeypatch)
    _cold_on(monkeypatch, load_vault(paths.root), _neighbour(job))
    _due(job["id"])
    assert FS.prefetch_plan_waits(load_vault(paths.root), repository, EXTRACTION) == []
    call(ctx, "reader.figures", {"extractionId": EXTRACTION})
    assert rich_author.calls == 1 and _waiting(_prebuild_jobs(repository)[0])


def test_f1_the_worker_stops_a_requeued_prebuild_before_any_request(tmp_path, monkeypatch):
    paths, repository, ctx, rich_author, job = _waiting_rig(tmp_path, monkeypatch)
    _cold_on(monkeypatch, load_vault(paths.root), _neighbour(job))
    # However it was requeued (an older sidecar's read, a retry press), the worker's own gate refuses.
    assert ctx.ingest_jobs.retry_figure_rich(job["id"], error_code=RICH.WAITING_FOR_PLAN)
    (stopped,) = _prebuild_jobs(repository)
    assert rich_author.calls == 1
    assert stopped["status"] == "failed" and (stopped.get("error") or {}).get("code") == "exam_material"
    assert FS.list_figures(load_vault(paths.root), repository, EXTRACTION) == []


def test_f1_the_worker_rechecks_before_the_store(tmp_path, monkeypatch):
    """The administration starts while the author writes: nothing is stored."""

    unavailable = AIProviderUnavailable("usage limit reached")
    paths, repository, ctx, rich_author = _rig(tmp_path, monkeypatch, [unavailable, RF.scene_output()])
    _pass(ctx, "tutor:q1")
    (job,) = _prebuild_jobs(repository)
    complete = rich_author.complete
    vault = load_vault(paths.root)
    neighbour = _neighbour(job)

    def complete_then_cold(request):
        out = complete(request)
        _cold_on(monkeypatch, vault, neighbour)
        return out

    monkeypatch.setattr(rich_author, "complete", complete_then_cold)
    assert ctx.ingest_jobs.retry_figure_rich(job["id"], error_code=RICH.WAITING_FOR_PLAN)
    (stopped,) = _prebuild_jobs(repository)
    assert rich_author.calls == 2  # the request was sent before the check started
    assert stopped["status"] == "failed" and (stopped.get("error") or {}).get("code") == "exam_material"
    assert FS.list_figures(load_vault(paths.root), repository, EXTRACTION) == []


def test_f1_unreadable_protection_requeues_nothing_and_the_worker_fails_closed(tmp_path, monkeypatch):
    from learnloop import learner_protection as LP

    paths, repository, ctx, rich_author, job = _waiting_rig(tmp_path, monkeypatch)
    monkeypatch.setattr(LP, "withheld_items", lambda v, r: LP.Withheld(available=False))
    _due(job["id"])
    retried: list[str] = []
    PF.retry_plan_waits(_env(paths, repository, retried), PF.PassResult("ok", "offer"))
    assert retried == []
    assert ctx.ingest_jobs.retry_figure_rich(job["id"], error_code=RICH.WAITING_FOR_PLAN)
    assert rich_author.calls == 1


def test_f1_the_pass_also_protects_the_stored_plans_open_items(tmp_path, monkeypatch):
    from learnloop.source_retrieval import corpus
    from tests.followups_batch6_verify_fixes_helpers import _plan_holds

    paths, repository, _ctx, _rich_author, job = _waiting_rig(tmp_path, monkeypatch)
    vault = load_vault(paths.root)
    item_id = sorted(vault.practice_items)[0]
    _plan_holds(repository, item_id)
    monkeypatch.setattr(corpus, "item_exclusions", lambda repository, item: corpus.Exclusions(
        spans=frozenset({(EXTRACTION, _neighbour(job))}) if item.id == item_id else frozenset()))
    _due(job["id"])
    retried: list[str] = []
    PF.retry_plan_waits(_env(paths, repository, retried), PF.PassResult("ok", "offer"))
    assert retried == []


def test_f1_an_unrelated_cold_check_still_lets_the_retry_through(tmp_path, monkeypatch):
    paths, repository, _ctx, _rich_author, job = _waiting_rig(tmp_path, monkeypatch)
    _cold_on(monkeypatch, load_vault(paths.root), "a_span_far_away")
    _due(job["id"])
    retried: list[str] = []
    PF.retry_plan_waits(_env(paths, repository, retried), PF.PassResult("ok", "offer"))
    assert retried == [job["id"]]


# --- F2: paced jobs never take a due job's slot ----------------------------------------------------


def test_f2_a_paced_job_first_in_line_never_starves_a_due_one(tmp_path, monkeypatch):
    paths, repository, _ctx, _rich_author, job = _waiting_rig(tmp_path, monkeypatch)
    set_config(paths, "figures.prefetch", max_daily_builds=1)
    # Two jobs wait, newest first: the newer is inside its retry interval, the older is due.
    monkeypatch.setattr(FS, "prefetch_plan_waits", lambda vault, repo, extraction_id, **kwargs:
                        ["job_newer", "job_older"] if extraction_id is None else [])
    assert RICH.due_for_plan_retry("job_newer")  # just asked: paced now
    asked: list[str] = []

    def paced(job_id: str) -> bool:
        asked.append(job_id)
        return RICH.due_for_plan_retry(job_id)

    result = PF.PassResult("ok", "offer")
    PF.retry_plan_waits(PF.PrefetchEnv(vault=load_vault(paths.root), repository=repository,
                                       retry_plan_wait=paced), result)
    assert result.plan_wait_retries == ["job_older"]
    assert asked == ["job_older"]  # the never-asked job first, and the bound reached: no more asked


def test_f2_the_scan_goes_past_paced_jobs_until_the_bound_of_requeues(tmp_path, monkeypatch):
    paths, repository, _ctx, _rich_author, _job = _waiting_rig(tmp_path, monkeypatch)
    set_config(paths, "figures.prefetch", max_daily_builds=2)
    jobs = ["j1", "j2", "j3", "j4", "j5"]
    monkeypatch.setattr(FS, "prefetch_plan_waits", lambda vault, repo, extraction_id, **kwargs:
                        list(jobs) if extraction_id is None else [])
    for job_id in ("j1", "j2", "j3"):
        assert RICH.due_for_plan_retry(job_id)  # all three just asked: paced
    result = PF.PassResult("ok", "offer")
    PF.retry_plan_waits(PF.PrefetchEnv(vault=load_vault(paths.root), repository=repository,
                                       retry_plan_wait=RICH.due_for_plan_retry), result)
    assert result.plan_wait_retries == ["j4", "j5"]


def test_f2_a_job_that_keeps_meeting_the_limit_yields_the_slot_to_the_least_recently_asked(tmp_path,
                                                                                            monkeypatch):
    paths, repository, _ctx, _rich_author, _job = _waiting_rig(tmp_path, monkeypatch)
    set_config(paths, "figures.prefetch", max_daily_builds=1)
    monkeypatch.setattr(FS, "prefetch_plan_waits", lambda vault, repo, extraction_id, **kwargs:
                        ["job_newer", "job_older"] if extraction_id is None else [])
    env = PF.PrefetchEnv(vault=load_vault(paths.root), repository=repository,
                         retry_plan_wait=RICH.due_for_plan_retry)
    first = PF.PassResult("ok", "offer")
    PF.retry_plan_waits(env, first)
    assert first.plan_wait_retries == ["job_newer"]  # neither asked yet: the ledger's order
    _due_now("job_newer")  # its interval passed (it met the limit again meanwhile)
    second = PF.PassResult("ok", "offer")
    PF.retry_plan_waits(env, second)
    assert second.plan_wait_retries == ["job_older"]  # never asked: ahead of the job asked before


# --- F3: an observed-outcome comparison, labelled as one ---------------------------------------------


def _decision(decision_id: str, *, shown: bool, arm_propensity: float = 0.5) -> dict:
    return {"id": decision_id, "detail": {"shown": shown, "arm_propensity": arm_propensity}}


def test_f3_differential_outcome_availability_is_reported_never_called_itt():
    # An accepted lesson delays the card arm's cold outcomes: two of its three are still pending.
    decisions = [_decision("c1", shown=True), _decision("c2", shown=True), _decision("c3", shown=True),
                 _decision("n1", shown=False), _decision("n2", shown=False)]
    responses = [{"decision_id": "c1", "response": "accepted", "lesson_id": "les_1"},
                 {"decision_id": "c2", "response": "accepted", "lesson_id": "les_2"}]
    lessons = {"les_1": {"origin_ref": "c1"}, "les_2": {"origin_ref": "c2"}}
    outcomes = {"c3": {"s_status": "final", "s_value": 1.0}, "c1": {"s_status": "pending", "s_value": None},
                "c2": {"s_status": "pending", "s_value": None},
                "n1": {"s_status": "final", "s_value": 0.0}, "n2": {"s_status": "final", "s_value": 1.0}}
    split = SR.itt_split(decisions, responses, [], lessons, outcomes)
    assert "itt_difference_r_cold" not in split
    assert split["observed_difference_r_cold"] == 0.5
    assert split["arms"]["card"]["outcome"]["observed"] == 1 and split["arms"]["card"]["outcome"]["pending"] == 2
    assert split["arms"]["card"]["outcome"]["observed_share"] == pytest.approx(1 / 3, abs=1e-6)
    assert split["arms"]["no_card"]["outcome"]["observed_share"] == 1.0
    text = "\n".join(SR.lines(split))
    assert "ITT difference" not in text
    assert "among observed outcomes only" in text and "not an intention-to-treat estimate" in text
    assert "observed 1 of 3" in text and "observed 2 of 2" in text


def test_f3_the_cli_labels_the_r_cold_comparison_with_observed_cold_outcomes(tmp_path, shown, no_network,
                                                                            monkeypatch):
    from typer.testing import CliRunner

    from learnloop.cli import app
    from learnloop.db.stores import router_suggestions
    from learnloop.router import lesson_suggestions as LS
    from learnloop.router import outcomes as RO
    from learnloop.teacher import service as S
    from tests.teacher_fakes import TeacherFake, clients, plan_turn

    paths, repository = _vault(tmp_path, version=LESSON_SUGGESTIONS_ALGORITHM_VERSION)
    card, lesson = _start(paths, repository)
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", clients=clients(TeacherFake([plan_turn])),
                  origin="router", origin_ref=card["decision_id"], lesson_id=lesson["lesson_id"], clock=_clock(hours=2))
    with repository.connection() as connection:
        connection.execute("UPDATE lessons SET closed_at = ?, close_reason = 'goal_reached' WHERE id = ?",
                           ("2026-11-02T12:00:00Z", lesson["lesson_id"]))
        connection.commit()
    monkeypatch.setattr(LS, "_uniforms", lambda seed: (0.5, 0.0, 0.999999))
    assert _today(load_vault(paths.root), repository, _clock(days=1)) is None  # drawn, no card
    with repository.connection() as connection:
        ids = [str(row["id"]) for row in router_suggestions.decisions(connection)]
    shown_id = card["decision_id"]
    unshown = [decision_id for decision_id in ids if decision_id != shown_id]
    assert len(unshown) == 1
    observed = {shown_id: {"decision_id": shown_id, "s_status": "final", "s_value": 1.0},
                unshown[0]: {"decision_id": unshown[0], "s_status": "final", "s_value": 0.0}}
    monkeypatch.setattr(RO, "derive_router_outcomes", lambda connection, **kwargs: list(observed.values()))
    result = CliRunner().invoke(app, ["router", "report", "--vault", str(paths.root), "--json"])
    assert result.exit_code == 0, result.output
    split = json.loads(result.output)["lesson_suggestions"]
    assert split["observed_difference_r_cold"] == 1.0 and "itt_difference_r_cold" not in split
    text = CliRunner().invoke(app, ["router", "report", "--vault", str(paths.root)])
    assert text.exit_code == 0
    assert "+1.00" in text.output and "not an intention-to-treat estimate" in text.output
    assert "ITT difference" not in text.output


# --- F4: a card carrying the released line says so in its version ------------------------------------


def test_f4_a_card_with_a_released_line_moves_its_version_and_te1bs_card_keeps_its_own(tmp_path, shown,
                                                                                         no_network):
    from learnloop.daily_plan import lesson_suggestion as SG
    from learnloop.router.card import CARD_VERSION, SUGGESTION_CARD_SUFFIX, SUGGESTION_RELEASE_CARD_SUFFIX
    from tests.teacher_te1b_review_fixes_helpers import _card

    paths, repository = _vault(tmp_path, version=LESSON_SUGGESTIONS_ALGORITHM_VERSION)
    card, _lesson = _start(paths, repository)
    before = _card(paths, repository, "2026-11-03T09:00:00Z")
    assert before.card_version == CARD_VERSION + SUGGESTION_CARD_SUFFIX  # TE1b's card, unchanged
    SG.respond(load_vault(paths.root), repository, decision_id=card["decision_id"], response="released",
               clock=_clock(hours=3))
    after = _card(paths, repository, "2026-11-03T09:00:00Z")
    assert after.card_version == CARD_VERSION + SUGGESTION_CARD_SUFFIX + SUGGESTION_RELEASE_CARD_SUFFIX
    assert after.json["card_version"] == after.card_version
