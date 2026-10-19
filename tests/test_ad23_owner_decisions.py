"""Adaptive difficulty AD2+AD3: the owner's decisions of 2026-10-19 and the final verify's F11
(docs/reviews/adaptive-difficulty-ad23.md §3.4, docs/reviews/adaptive-difficulty-ad23-codex-review.md).

* F11: an automatic retry of a commission that waited on models that were off never clears an
  explicit cancellation;
* F5: an unlanded commission expires 7 days after its job finished, so a fresh one can be drawn
  for its cell; one in review stays open;
* the defaults: ``calibrate_below = 0.25``, ``learned_coupling`` off, AD's own history fallback
  (``current_content``) with field's ``legacy_fallback`` unchanged.

Fakes only: no network, no model call, no paid call.
"""

from __future__ import annotations

import json
import os
from contextlib import closing
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import ad_serving
from learnloop.vault.loader import load_vault

from tests.ad23_fakes import LO, ad23_vault, env_for, selections

ROUTER_OFF = "[router]\nenabled = false\n"
HARD = {"complexity": 3, "transfer": "far", "scaffolding": "none", "span": "multi_step",
        "response": "long_constructed", "tools": ["closed_book"]}
ITEMS = ("pi_k1", "pi_k2")


def _commissioned(tmp_path) -> tuple[Any, dict[str, Any]]:
    """A serve whose cell pool reaches no band draws one serve-time commission."""

    paths = ad23_vault(tmp_path, items=ITEMS, features={i: HARD for i in ITEMS}, config=ROUTER_OFF)
    env, _clock = env_for(paths, items=ITEMS)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item"
    (commission,) = selections(paths, kind="commission")
    assert ":serve:" in commission["decision_key"] and commission["chosen_point"]
    return paths, commission


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
            return AuthoringProposal.model_validate({"summary": "commissioned", "source_refs": [], "items": []})

    return _Generator()


def _open_ids(paths, now: datetime) -> list[str]:
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        return [str(row["id"]) for row in ad_serving.open_commissions(connection, now=_iso(now))]


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _job(repository, batch_id: str) -> dict[str, Any]:
    (job,) = repository.ingest_jobs_for_batch(batch_id)
    return job


# -- F11: an automatic retry never clears an explicit cancellation ----------------------------------


def test_a_cancelled_commission_stays_cancelled_when_models_come_back_on(tmp_path, monkeypatch):
    """F11 (the final verify): the commission is queued with models on; the worker runs it with
    ``LEARNLOOP_AD_MODELS=off`` (failed, ``ad_models_off``); the learner cancels its batch; models
    come back on and the ordinary schedule enqueues the commission again. The batch stays
    cancelled, the job stays failed and no client is resolved. Only the learner's explicit resume
    runs it. Failed before: the retry called ``resume_batch()``, which cleared the cancellation,
    requeued the job and generated."""

    from learnloop.adaptive_difficulty.generation import schedule_commission_generation
    from learnloop.adaptive_difficulty.spend import MODELS_ENV
    from learnloop.content.pipeline import jobs as J

    paths, commission = _commissioned(tmp_path)
    generator = _generator()
    resolved: list[str] = []

    def default_client(_ctx):  # the production resolver's seam: never a live client here
        resolved.append(os.environ.get(MODELS_ENV, ""))
        return generator

    monkeypatch.setattr(J, "default_synthesis_client", default_client)
    repository = Repository(paths.sqlite_path)
    jobs = J.DurableIngestJobs()
    jobs.bind(repository, paths.root, background=False)
    vault = load_vault(paths.root)

    def enqueue(commission_id: str, learning_object_id: str) -> str:
        return jobs.enqueue_practice_expansion(learning_object_ids=[learning_object_id],
                                               ad_commission_id=commission_id)

    monkeypatch.delenv(MODELS_ENV, raising=False)
    monkeypatch.setattr(jobs, "_ensure_worker", lambda: None)
    assert schedule_commission_generation(vault, repository, enqueue) == [commission["id"]]
    batch_id = J.ad_commission_batch_id(commission["id"])
    assert _job(repository, batch_id)["status"] == "queued"
    # queued -> failed: the worker runs it with models off.
    monkeypatch.setenv(MODELS_ENV, "off")
    jobs.drain_foreground()
    job = _job(repository, batch_id)
    assert job["status"] == "failed" and job["error"]["code"] == J.AD_MODELS_OFF_CODE
    # failed -> cancelled: the learner cancels the batch.
    jobs.cancel_batch(batch_id)
    assert repository.get_ingest_batch(batch_id)["cancel_requested"]
    # Models back on: the ordinary schedule enqueues the commission again, twice.
    monkeypatch.delenv(MODELS_ENV, raising=False)
    for _ in range(2):
        schedule_commission_generation(vault, repository, enqueue)
        jobs.drain_foreground()
    batch = repository.get_ingest_batch(batch_id)
    job = _job(repository, batch_id)
    assert batch["cancel_requested"], "an automatic retry cleared the learner's cancellation"
    assert job["status"] == "failed" and job["error"]["code"] == J.AD_MODELS_OFF_CODE
    assert resolved == [] and generator.contexts == []
    # The runner's retry refuses a cancelled batch outright; an uncancelled one it requeues.
    assert jobs._require_runner().requeue_failed_unless_cancelled(batch_id, error_code=J.AD_MODELS_OFF_CODE) is False
    # Only the learner's explicit resume clears the cancellation and runs it.
    jobs.resume_batch(batch_id)
    jobs.drain_foreground()
    assert not repository.get_ingest_batch(batch_id)["cancel_requested"]
    assert _job(repository, batch_id)["status"] == "completed" and resolved == [""]
    assert len(generator.contexts) == 1


# -- F5: an unlanded commission expires 7 days after its job finished --------------------------------


def _run_commission(paths, commission, monkeypatch) -> tuple[Any, Any, str]:
    """Queue and run the commission's generation with a fake generator that writes no item."""

    from learnloop.adaptive_difficulty.generation import schedule_commission_generation
    from learnloop.content.pipeline import jobs as J
    from learnloop.content.pipeline.runner import RunnerServices

    generator = _generator()
    repository = Repository(paths.sqlite_path)
    jobs = J.DurableIngestJobs()
    jobs.bind(repository, paths.root, background=False,
              services=RunnerServices(synthesis_client_factory=lambda _ctx: generator))

    def enqueue(commission_id: str, learning_object_id: str) -> str:
        return jobs.enqueue_practice_expansion(learning_object_ids=[learning_object_id],
                                               ad_commission_id=commission_id)

    schedule_commission_generation(load_vault(paths.root), repository, enqueue)
    batch_id = J.ad_commission_batch_id(commission["id"])
    return repository, jobs, batch_id


def test_an_unlanded_commission_expires_seven_days_after_its_job_and_a_fresh_one_is_drawn(tmp_path, monkeypatch):
    """F5 (owner decision 2026-10-19): the commission's generation finished without landing an
    item. It stays open (and suppresses further commissions for its cell) for 7 days after its
    job finished, then expires; a fresh commission is then drawn for the cell, and the old one
    stays closed (superseded) whatever time it is asked about. At most one is ever open per cell.
    Failed before: the commission stayed open for ever (``open_commissions`` had no time)."""

    from learnloop.adaptive_difficulty.generation import commission_point

    paths, commission = _commissioned(tmp_path)
    repository, _jobs, batch_id = _run_commission(paths, commission, monkeypatch)
    job = _job(repository, batch_id)
    assert job["status"] == "completed" and (job.get("result") or {}).get("ad_commission_id") == commission["id"]
    finished = _at(job["finished_at"])
    assert _open_ids(paths, finished + timedelta(days=6, hours=23)) == [commission["id"]]
    assert _open_ids(paths, finished + timedelta(days=7)) == []
    vault = load_vault(paths.root)
    incumbent = SimpleNamespace(capability=commission["cell_capability"])
    # Within the 7 days the generation path reuses the open commission for the cell.
    early = commission_point(vault, repository, learning_object_id=LO, incumbent=incumbent,
                             now=_iso(finished + timedelta(days=1)))
    assert early is not None and early[2] == commission["id"]
    # After them, a fresh commission is drawn for the same cell.
    later = _iso(finished + timedelta(days=8))
    fresh = commission_point(vault, repository, learning_object_id=LO, incumbent=incumbent, now=later)
    assert fresh is not None and fresh[2] != commission["id"]
    drawn = {row["id"]: row for row in selections(paths, kind="commission")}
    assert (drawn[fresh[2]]["cell_facet"], drawn[fresh[2]]["cell_capability"]) == \
        (commission["cell_facet"], commission["cell_capability"])
    # The old one is superseded, so it never reopens; exactly one is open for the cell.
    assert _open_ids(paths, finished + timedelta(days=1)) == [fresh[2]]
    assert _open_ids(paths, _at(later)) == [fresh[2]]


def _proposal(paths, patch_id: str, *, created_at: str, decision: str = "pending", decided_at: str | None = None,
              validation: str = "valid") -> str:
    """A practice item for the commission's LO in the job's own proposal (the generator wrote none)."""

    item_id = f"{patch_id}_{created_at.replace(':', '')}"
    payload = {"id": "pi_commissioned", "learning_object_id": LO, "prompt": "A commissioned question."}
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO proposed_patch_items(id, proposed_patch_id, client_item_id, item_type, operation, "
            "payload_json, decision, validation_status, decided_at, created_at, updated_at) "
            "VALUES (?, ?, ?, 'practice_item', 'create', ?, ?, ?, ?, ?, ?)",
            (item_id, patch_id, item_id, json.dumps(payload), decision, validation, decided_at, created_at,
             created_at))
        connection.commit()
    return item_id


def test_a_commission_whose_item_is_in_review_stays_open_until_the_decision(tmp_path, monkeypatch):
    """F5: an item written for the commission's LO since the draw, routed to review, keeps the
    commission open however long the review takes (an invalid row, which review cannot accept,
    does not). Once the reviewer rejects it, the commission expires 7 days after the decision."""

    paths, commission = _commissioned(tmp_path)
    repository, _jobs, batch_id = _run_commission(paths, commission, monkeypatch)
    job = _job(repository, batch_id)
    finished, patch_id = _at(job["finished_at"]), job["result"]["patch_id"]
    _proposal(paths, patch_id, created_at=_iso(finished + timedelta(days=1)), validation="invalid")
    assert _open_ids(paths, finished + timedelta(days=7)) == []
    item_id = _proposal(paths, patch_id, created_at=_iso(finished))
    assert _open_ids(paths, finished + timedelta(days=30)) == [commission["id"]]
    decided = finished + timedelta(days=12)
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE proposed_patch_items SET decision = 'rejected', decided_at = ? WHERE id = ?",
                           (_iso(decided), item_id))
        connection.commit()
    assert _open_ids(paths, decided + timedelta(days=6)) == [commission["id"]]
    assert _open_ids(paths, decided + timedelta(days=7)) == []


def test_a_commission_waiting_on_models_stays_open_and_a_cancelled_one_expires(tmp_path, monkeypatch):
    """F5 with F10/F11: a job waiting until the models are back on has not finished, so its
    commission stays open; once its batch is cancelled the generation has finished, and the
    commission expires 7 days after the job did."""

    from learnloop.adaptive_difficulty.generation import schedule_commission_generation
    from learnloop.adaptive_difficulty.spend import MODELS_ENV
    from learnloop.content.pipeline import jobs as J

    paths, commission = _commissioned(tmp_path)
    monkeypatch.setattr(J, "default_synthesis_client", lambda _ctx: _generator())
    repository = Repository(paths.sqlite_path)
    jobs = J.DurableIngestJobs()
    jobs.bind(repository, paths.root, background=False)
    monkeypatch.setattr(jobs, "_ensure_worker", lambda: None)
    schedule_commission_generation(load_vault(paths.root), repository, lambda cid, lo: jobs.enqueue_practice_expansion(
        learning_object_ids=[lo], ad_commission_id=cid))
    batch_id = J.ad_commission_batch_id(commission["id"])
    # Not yet run: open, however late.
    queued_at = _at(_job(repository, batch_id)["created_at"])
    assert _open_ids(paths, queued_at + timedelta(days=30)) == [commission["id"]]
    monkeypatch.setenv(MODELS_ENV, "off")
    jobs.drain_foreground()
    job = _job(repository, batch_id)
    assert job["status"] == "failed" and job["error"]["code"] == J.AD_MODELS_OFF_CODE
    finished = _at(job["finished_at"])
    assert _open_ids(paths, finished + timedelta(days=30)) == [commission["id"]]
    jobs.cancel_batch(batch_id)
    assert _open_ids(paths, finished + timedelta(days=6)) == [commission["id"]]
    assert _open_ids(paths, finished + timedelta(days=7)) == []


# -- the defaults ------------------------------------------------------------------------------------


def test_the_owner_defaults_of_2026_10_19():
    """``calibrate_below`` 0.25 (amendment A17), ``learned_coupling`` off until the owner adopts a
    coupling version, and AD's own history fallback ``current_content`` beside field's unchanged
    ``legacy_fallback = "exclude"``; the new key is classified in the parameter registry."""

    from learnloop.adaptive_difficulty import selection as S
    from learnloop.adaptive_difficulty.successor import coupling_on, history_fallback
    from learnloop.config.schema import LearnLoopConfig
    from learnloop.params.parameter_registry import REGISTRY

    config = LearnLoopConfig.model_validate({"algorithms": {"algorithm_version": "mvp-0.28"}})
    section = config.adaptive_difficulty
    assert section.calibrate_below == 0.25 and S.SelectionConstants().calibrate_below == 0.25
    assert S.constants_from_config(config).calibrate_below == 0.25
    assert section.learned_coupling is False and not coupling_on(config)
    assert section.history_fallback == "current_content" and history_fallback(config) == "current_content"
    assert config.field.legacy_fallback == "exclude"
    spec = REGISTRY["adaptive_difficulty.history_fallback"]
    assert spec.kind == "decision" and spec.param_class == "constraint"


def test_ad_reads_history_through_its_own_fallback_and_field_keeps_its_own(tmp_path):
    """A historical attempt (no bound presentation, no saved revision) trains AD by default,
    read against today's item text, while field's own rows still exclude it; with
    ``history_fallback = "exclude"`` AD excludes it too."""

    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.field.outcomes import load_attempt_rows

    from tests.ad23_fakes import answer

    paths = ad23_vault(tmp_path)
    attempt_id = answer(paths, "pi_m1a", correct=True, presentation_id=None)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        (field_row,) = [row for row in load_attempt_rows(connection, vault) if row.attempt_id == attempt_id]
        assert field_row.revision_status == "excluded"
        event = next(e for e in RP.load_events(connection, vault, repository).attempts if e.attempt_id == attempt_id)
        assert event.input_status == "reconstructed_current" and event.eligible
        vault.config.adaptive_difficulty.history_fallback = "exclude"
        event = next(e for e in RP.load_events(connection, vault, repository).attempts if e.attempt_id == attempt_id)
        assert event.input_status == "excluded" and not event.eligible
