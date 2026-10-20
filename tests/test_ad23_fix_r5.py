"""Adaptive difficulty AD2+AD3, fix round 5: the final verify's F12-F15
(docs/reviews/adaptive-difficulty-ad23-codex-review.md, verify 20261019-201825-NEf5k1).

* F12: ``ad report`` scores the predictor that serves: its prequential forecasts and its snapshot
  replay with the configured settings, so ``learned_coupling = false`` means no learned coupling;
* F13: with ``selection`` off, Today's projection never re-applies an AD deferral;
* F14: a commission the generation path drew inside a durable job expires 7 days after that job
  finished, and never while it runs;
* F15: a commissioned item that landed gets its receipt whatever its commission's expiry.

Fakes only: no network, no model call, no paid call.
"""

from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from learnloop.adaptive_difficulty import arms as A
from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty import report as REP
from learnloop.adaptive_difficulty import relatedness as R
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.stores import ad_serving
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import COUPLED, LO, ProposalLLM, ad23_vault, answer, block_events, env_for, reveal, selections
from tests.ad23_fakes import set_item
from tests.daily_plan_fakes import MovableClock, iso, make_env, scheduled
from tests.helpers import set_algorithm_version

ROUTER_OFF = "[router]\nenabled = false\n"


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _at(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


# -- F12: the report describes the serving predictor ------------------------------------------------

OTHER = ("pi_o1", "pi_o2", "pi_o3", "pi_o4")
MINE = ("pi_m1", "pi_m2")


def _adversarial(subject_inputs: dict[str, Any]) -> dict[str, Any]:
    los = [row["learning_object_id"] for row in subject_inputs["payload"]["learning_objects"]]
    facets = [row["facet_id"] for row in subject_inputs["payload"]["facets"]]
    return {
        "items": [{"item_id": item["item_id"], "loadings": [
            {"facet_id": f, "strength": "strong", "why": "everything"} for f in facets if f not in item["facets"]]}
            for item in subject_inputs["payload"]["items"]],
        "learning_objects": [{"learning_object_id": lo, "related": [
            {"learning_object_id": other, "strength": "strong", "why": "everything"} for other in los if other != lo]}
            for lo in los],
    }


def _coupled_history(tmp_path):
    """An adopted coupling version, four right answers on the other LO, then the first answer on
    the related LO (the verify's case)."""

    paths = ad23_vault(tmp_path, items=MINE, learning_objects={"lo_other": OTHER}, ad=COUPLED, config=ROUTER_OFF)
    for item in MINE:
        set_item(paths, item, evidence_facets=["f_mine"], evidence_weights={"f_mine": 1.0})
    for item in OTHER:
        set_item(paths, item, evidence_facets=["f_other"], evidence_weights={"f_other": 1.0})
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    inputs = R.subject_inputs(vault, repository, "linear-algebra")
    assert R.propose_subject(vault, repository, "linear-algebra", client=ProposalLLM(_adversarial(inputs))).status == "ok"
    assert R.adopt(repository, "linear-algebra", adopted_by="test")
    env, clock = env_for(paths, items=OTHER)
    build_plan(env, kind="normal", budget=12.0, remembered=12, minutes_source="chip")
    for _ in range(4):
        _record, step = advance(env, serve=True)
        assert step["kind"] == "item"
        clock.advance(2)
        answer(paths, step["practice_item_id"], correct=True, presentation_id=step["presentation_id"], clock=clock)
        clock.advance(1)
    clock.advance(60 * 24)
    env, clock = env_for(paths, items=MINE, clock=clock, session="s2")
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item" and step["learning_object_id"] == LO
    clock.advance(2)
    first = answer(paths, step["practice_item_id"], correct=False, presentation_id=step["presentation_id"],
                   clock=clock)
    return paths, first


def _replayed(vault, repository, connection, settings: RP.ReplaySettings, attempt_id: str) -> float:
    """``ad_threshold@subject``'s forecast for one attempt, prequentially, under ``settings``."""

    found: dict[str, float] = {}

    def observer(attempt, subject, _lo_view, _context) -> None:
        if attempt.attempt_id == attempt_id:
            found["p"] = A._p(subject, attempt.spec, attempt.warmth)[0]  # noqa: SLF001 - the arm's own read

    events = RP.load_events(connection, vault, repository, settings=settings)
    RP.run(events, settings, trace=False, observer=observer)
    return found["p"]


def test_the_report_forecasts_with_the_configured_coupling(tmp_path, monkeypatch):
    """F12: with an adopted coupling version and ``learned_coupling = false``, the report's
    ``ad_threshold@subject`` forecast for the related LO's first answer is the uncoupled replay's,
    which serving reads, and every replay the report runs is uncoupled; with the switch on it is
    the coupled forecast. Failed before: the report hardcoded coupling on for both its prequential
    forecasts and its snapshot."""

    paths, first = _coupled_history(tmp_path)
    repository = Repository(paths.sqlite_path)
    real_run = RP.run
    runs: list[RP.ReplaySettings] = []

    def spy(events, settings=RP.ReplaySettings(), **kwargs):
        runs.append(settings)
        return real_run(events, settings, **kwargs)

    for coupled in (False, True):
        vault = load_vault(paths.root)
        vault.config.adaptive_difficulty.learned_coupling = coupled
        RP.clear_cache()
        with closing(connect(paths.sqlite_path, read_only=True)) as connection:
            uncoupled = _replayed(vault, repository, connection, RP.ReplaySettings(coupling=False), first)
            with_coupling = _replayed(vault, repository, connection, RP.ReplaySettings(coupling=True), first)
            assert abs(uncoupled - with_coupling) > 1e-6, "the case must tell the two predictors apart"
            log = A.prequential(vault, repository, connection, arms=(A.SUBJECT,))
            (record,) = [r for r in log["records"] if r.attempt_id == first]
            assert record.first_attempt_lo and record.learning_object_id == LO
            expected = with_coupling if coupled else uncoupled
            assert abs(record.p[A.SUBJECT] - expected) < 1e-12
            assert log["settings"] == RP.ReplaySettings.from_config(vault.config)
            runs.clear()
            monkeypatch.setattr(RP, "run", spy)
            try:
                REP.build(vault, repository, connection, sensitivity=True)
            finally:
                monkeypatch.setattr(RP, "run", real_run)
            assert runs and {settings.coupling for settings in runs} == {coupled}


# -- F13: kill switch off means no AD deferrals in Today --------------------------------------------

READMISSION = ("pi_a", "pi_w1", "pi_w2", "pi_w3")
PLAN_ITEMS = READMISSION + ("pi_o1", "pi_o2")


def _deferred(tmp_path):
    """``pi_a`` displaced as ineligible (a recent partial reveal) with other work in the plan."""

    paths = ad23_vault(tmp_path, items=READMISSION, config=ROUTER_OFF, learning_objects={"lo_other": ("pi_o1", "pi_o2")})
    env, clock = env_for(paths, items=PLAN_ITEMS)
    build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    reveal(paths, "pi_a", amount=0.2, at=iso(clock.now() - timedelta(hours=23, minutes=30)))
    served = []
    for _ in range(2):
        _record, step = advance(env, serve=True)
        assert step["kind"] == "item"
        served.append(step["practice_item_id"])
        clock.advance(2)
        answer(paths, step["practice_item_id"], correct=True, presentation_id=step["presentation_id"], clock=clock)
        clock.advance(1)
    assert "pi_a" not in served
    assert [e["detail"]["failed"] for e in block_events(paths, "item_displaced")] == [["recent_reveal"]]
    return paths, env, clock


def test_with_selection_off_the_projection_offers_a_once_deferred_item(tmp_path, monkeypatch):
    """F13 (the verify's scenario): AD displaced ``pi_a`` as ineligible; its reveal then ages past
    the delay and ``selection`` is turned off. The switch-aware context carries no deferral, and
    the projection's first candidate pool includes ``pi_a``: exactly the base's rule (the context's
    pool less the plan's planned and skipped items). Failed before: ``simulate_blocks`` re-applied
    the deferral through ``PlanRecord.exclusion_ids()`` (pool ``[]`` versus ``['pi_a']``)."""

    from learnloop.daily_plan import engine as E

    _paths, env, clock = _deferred(tmp_path)
    clock.advance(45)  # the reveal is older than the delay; still today
    env.vault.config.adaptive_difficulty.selection = False
    record, _step, context = E.advance_with_context(env, serve=False)
    assert context is not None and not context.ad_deferred and "pi_a" in record.ad_deferrals()
    pools: list[set[str]] = []
    real_decide = E.decide

    def decide(sim, view, policy, **kwargs):
        pools.append({item.practice_item_id for item in view.pool})
        return real_decide(sim, view, policy, **kwargs)

    monkeypatch.setattr(E, "decide", decide)
    E.simulate_blocks(record, context, env.policy)
    base_rule = {item.practice_item_id for item in context.pool} - record.planned_ids() - {
        item.practice_item_id for item in record.items() if item.skipped}
    assert pools and "pi_a" in pools[0] and pools[0] == base_rule


def _today(root, instant: datetime, *, selection_off: bool) -> tuple[list[dict[str, Any]], list[list[str]]]:
    from learnloop.daily_plan import engine as E
    from learnloop.daily_plan.view import project_blocks

    vault = load_vault(root)
    item_los = {item: vault.practice_items[item].learning_object_id for item in PLAN_ITEMS}
    env = make_env(root, [scheduled(item, item_los[item], forgetting_risk=0.6) for item in PLAN_ITEMS],
                   clock=MovableClock(instant), session_id="s1")
    if selection_off:
        env.vault.config.adaptive_difficulty.selection = False
    record, _step, context = E.advance_with_context(env, serve=False)
    blocks = E.simulate_blocks(record, context, env.policy)
    return project_blocks(record, context, env.policy), [[i.practice_item_id for i in b.items] for _d, b in blocks]


def test_with_the_kill_switch_off_today_projects_the_predecessors_blocks(tmp_path):
    """F13 parity: on copies of a vault holding AD rows (draws and an ``ad_ineligible``
    displacement), Today's projected blocks with ``selection = false`` equal the predecessor's
    (``mvp-0.27``, which reads no AD row), and the once-deferred item is projected again."""

    paths, _env, clock = _deferred(tmp_path)
    assert selections(paths)
    off_root, pred_root = tmp_path / "copies" / "off", tmp_path / "copies" / "pred"
    copy_tree_with_databases(paths.root, off_root)
    copy_tree_with_databases(paths.root, pred_root)
    set_algorithm_version(SimpleNamespace(root=pred_root), "mvp-0.27")
    off = _today(off_root, clock.now(), selection_off=True)
    pred = _today(pred_root, clock.now(), selection_off=False)
    assert off == pred
    assert any("pi_a" in items for items in off[1])


# -- F14: a generation job's commission expires 7 days after the job finished -----------------------


def _generator():
    from learnloop.content.proposals.ai_contracts import AuthoringProposal

    from tests.structured_ai import StructuredClientFake

    class _Generator(StructuredClientFake):
        provider_name = "codex"
        provider_type = "test"
        model = "fake-generator"

        def __init__(self) -> None:
            self.contexts: list[Any] = []

        def run_authoring_proposal(self, context):
            self.contexts.append(context)
            return AuthoringProposal.model_validate({"summary": "nothing", "source_refs": [], "items": []})

    return _Generator()


def _open_ids(paths, now: datetime) -> list[str]:
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return [str(row["id"]) for row in ad_serving.open_commissions(connection, now=_iso(now))]


def _set_job(paths, job_id: str, *, status: str, finished_at: str | None) -> None:
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE ingest_jobs SET status = ?, finished_at = ? WHERE id = ?",
                           (status, finished_at, job_id))
        connection.commit()


def test_a_generation_jobs_commission_expires_seven_days_after_the_job_finished(tmp_path):
    """F14: ordinary practice generation (a reader-first ``practice_expansion`` job) draws a
    ``generation:`` commission before its model work; the commission names the job. Drawn at
    12:00, job failed at 12:10: still open at day 7 12:05, expired at day 7 12:11. A running job's
    commission never expires. With the job row gone the clock falls back to the draw. Failed
    before: the clock started at the draw whatever the job did (expired at day 7 12:00, and a
    running job's commission expired too)."""

    from learnloop.content.pipeline import jobs as J
    from learnloop.content.pipeline.runner import RunnerServices

    paths = ad23_vault(tmp_path, items=("pi_g1",), config=ROUTER_OFF)
    generator = _generator()
    repository = Repository(paths.sqlite_path)
    jobs = J.DurableIngestJobs()
    jobs.bind(repository, paths.root, background=False,
              services=RunnerServices(synthesis_client_factory=lambda _ctx: generator))
    batch_id = jobs.enqueue_practice_expansion(learning_object_ids=[LO])
    jobs.drain_foreground()
    (job,) = repository.ingest_jobs_for_batch(batch_id)
    assert job["status"] in ("completed", "failed") and generator.contexts
    (commission,) = selections(paths, kind="commission")
    assert commission["decision_key"].startswith("commission:") and ":generation:" in commission["decision_key"]
    assert commission["generating_job_id"] == job["id"]
    drawn = _at(commission["created_at"])
    day7 = drawn + timedelta(days=7)
    _set_job(paths, job["id"], status="failed", finished_at=_iso(drawn + timedelta(minutes=10)))
    assert _open_ids(paths, day7 + timedelta(minutes=5)) == [commission["id"]]
    assert _open_ids(paths, day7 + timedelta(minutes=11)) == []
    _set_job(paths, job["id"], status="running", finished_at=None)
    assert _open_ids(paths, drawn + timedelta(days=60)) == [commission["id"]]
    _set_job(paths, job["id"], status="queued", finished_at=None)
    assert _open_ids(paths, drawn + timedelta(days=60)) == [commission["id"]]
    # The job row pruned: its finish is lost, so the clock starts at the draw.
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("DELETE FROM ingest_jobs WHERE id = ?", (job["id"],))
        connection.commit()
    assert _open_ids(paths, day7 - timedelta(minutes=1)) == [commission["id"]]
    assert _open_ids(paths, day7) == []


def test_a_commission_drawn_outside_a_job_names_none(tmp_path):
    """A synchronous generation run (no durable job) draws a commission with no job: its clock
    starts at the draw, as it generated there."""

    from tests.test_ad2_serving import _generation_prompt

    paths = ad23_vault(tmp_path, items=("pi_g1",), config=ROUTER_OFF)
    _generation_prompt(paths)
    (commission,) = selections(paths, kind="commission")
    assert commission["generating_job_id"] is None
    drawn = _at(commission["created_at"])
    assert _open_ids(paths, drawn + timedelta(days=7) - timedelta(seconds=1)) == [commission["id"]]
    assert _open_ids(paths, drawn + timedelta(days=7)) == []


# -- F15: a landed commission gets its receipt whatever its expiry ----------------------------------


def _land(paths, item_id: str, commission: dict[str, Any], at: datetime) -> None:
    from learnloop.adaptive_difficulty.generation import rung_features

    from tests.test_ad2_serving import _land as land

    point = {**rung_features(commission["chosen_point"]), "tools": ["closed_book"]}
    land(paths, item_id, point, _iso(at), capability=commission["cell_capability"])


def _reconcile(paths, now: datetime) -> list[str]:
    from learnloop.adaptive_difficulty.generation import record_landed_commissions

    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    with repository.atomic():
        return record_landed_commissions(vault, repository, repository.connection(), now=_iso(now))


def _results(paths) -> list[dict[str, Any]]:
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return ad_serving.commission_results(connection)


def test_an_item_that_landed_before_expiry_gets_its_receipt_at_a_later_serve(tmp_path):
    """F15 (the verify's case): the commissioned item lands on day 1 (October 2) and the next
    fresh-item serve, which reconciles landings, comes on day 9 (October 10), after the
    commission's expiry. The item gets exactly one receipt, not marked late; reconciling again,
    and a whole rebuild, change no row. Failed before: reconciliation read only open commissions,
    so the expired one's landed item got no receipt."""

    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    from tests.test_ad2_serving import _generation_prompt

    paths = ad23_vault(tmp_path, items=("pi_g1",), config=ROUTER_OFF)
    _generation_prompt(paths)
    (commission,) = selections(paths, kind="commission")
    drawn = _at(commission["created_at"])
    _land(paths, "pi_landed", commission, drawn + timedelta(days=1))
    later = drawn + timedelta(days=9)
    assert _open_ids(paths, later) == []  # expired (it was never reconciled)
    assert len(_reconcile(paths, later)) == 1
    (result,) = _results(paths)
    assert result["selection_id"] == commission["id"] and result["practice_item_id"] == "pi_landed"
    assert result["landed_after_expiry"] == 0
    assert result["status"] in ("in_band", "realized_out_of_band")
    before = _results(paths)
    assert _reconcile(paths, later + timedelta(days=1)) == []
    rebuild_all_derived_state(load_vault(paths.root), Repository(paths.sqlite_path))
    assert _results(paths) == before


def test_an_item_that_lands_after_expiry_gets_a_marked_receipt_and_a_later_draw_owns_later_items(tmp_path):
    """F15: an item landing after its commission expired still gets its receipt, marked
    ``landed_after_expiry``; once a fresh commission is drawn for the cell, a later item belongs
    to that one only (never to the expired one), so no item is attributed twice. The report
    counts the late landing."""

    from learnloop.adaptive_difficulty.generation import commission_point

    from tests.test_ad2_serving import _generation_prompt

    paths = ad23_vault(tmp_path, items=("pi_g1",), config=ROUTER_OFF)
    _generation_prompt(paths)
    (old,) = selections(paths, kind="commission")
    drawn = _at(old["created_at"])
    _land(paths, "pi_late", old, drawn + timedelta(days=8))
    assert len(_reconcile(paths, drawn + timedelta(days=8, hours=1))) == 1
    (late,) = _results(paths)
    assert late["selection_id"] == old["id"] and late["landed_after_expiry"] == 1
    # A fresh commission for the cell; an item at the old point landing after it is not the old one's.
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    fresh = commission_point(vault, repository, learning_object_id=LO,
                             incumbent=SimpleNamespace(capability=old["cell_capability"]),
                             now=_iso(drawn + timedelta(days=10)))
    assert fresh is not None and fresh[2] != old["id"]
    _land(paths, "pi_after_fresh", old, drawn + timedelta(days=11))
    _reconcile(paths, drawn + timedelta(days=11, hours=1))
    assert [(r["selection_id"], r["practice_item_id"]) for r in _results(paths) if r["selection_id"] == old["id"]] \
        == [(old["id"], "pi_late")]
    # Round 6 (F15): ownership is by cell and order, so the fresh commission owns it.
    assert [(r["selection_id"], r["practice_item_id"]) for r in _results(paths) if r["selection_id"] != old["id"]] \
        == [(fresh[2], "pi_after_fresh")]
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        report = REP.build(load_vault(paths.root), repository, connection, sensitivity=False)
    assert report["selection"]["commissions"]["landed_after_expiry"] == 1
