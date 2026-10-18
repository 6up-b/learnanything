"""Adaptive difficulty AD1: the Codex review's findings (docs/reviews/adaptive-difficulty-ad1-codex-review.md).

Each test reproduces one finding and failed on b85acc8a0 (the stage tip the
review read) for the reason its docstring names. Fakes only: no network, no
paid call.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import (
    AuditDecider,
    ForecastLLM,
    ad_plan_vault,
    ad_receipts,
    everything_text,
    plan_env,
    rows,
)


def _build(env):
    build_plan(env, kind="normal", budget=10.0, remembered=10, minutes_source="chip")


def _serve(env):
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item" and step["presentation_id"]
    return step


def _stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _forecast_judgments(paths):
    return rows(paths.sqlite_path, "SELECT * FROM judgment_ledger WHERE task = 'ad_item_forecast' ORDER BY rowid")


# -- F1 [High]: historical revisions are judged on their own source --------------------------


SENTINEL = "SENTINEL-HISTORICAL-HELD-OUT-41c9"


def _held_out_vault(tmp_path):
    from learnloop.content.synthesis.source_unit_selection import save_unit_selection
    from tests.source_service_fakes import build_textbook_vault

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    return paths, repository, spans


def _snapshot(paths, item) -> str:
    from learnloop.adaptive_difficulty.feature_audit import item_revision

    content_hash, item_json = item_revision(item)
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute("INSERT INTO practice_item_snapshots(content_hash, practice_item_id, item_json, created_at) "
                           "VALUES (?, ?, ?, '2026-10-01T09:00:00Z')", (content_hash, str(item.id), item_json))
    return content_hash


def test_historical_snapshots_of_held_out_material_are_never_audited(tmp_path):
    """F1: a held-out revision kept in ``practice_item_snapshots`` (its item
    since deleted, or the item's current revision made from other material)
    was audited, its held-out stem sent to the Decider and the LLM judge,
    because protection checked only the vault's current item ids. Each
    revision is now checked on its own source references."""

    from learnloop.adaptive_difficulty.backfill import backfill
    from learnloop.adaptive_difficulty.outside import Clients
    from learnloop.vault.models import CanonicalExercise

    paths, repository, spans = _held_out_vault(tmp_path)
    vault = load_vault(paths.root)
    base = vault.practice_items["pi_eigen_1"]
    held_exercise = CanonicalExercise(source_id="src_text", extraction_id="ext_text",
                                      span_ids=[spans["exercises"][1]])
    # A deleted item's held-out revision, and a held-out earlier revision of
    # an item whose current revision is ordinary practice.
    deleted = base.model_copy(update={"id": "pi_deleted", "prompt": f"{SENTINEL}: a deleted exam item.",
                                      "expected_answer": f"{SENTINEL} answer", "canonical_exercise": held_exercise})
    earlier = base.model_copy(update={"prompt": f"{SENTINEL}: an earlier exam revision.",
                                      "expected_answer": f"{SENTINEL} earlier", "canonical_exercise": held_exercise})
    assert "pi_deleted" not in vault.practice_items
    _snapshot(paths, deleted)
    _snapshot(paths, earlier)

    decider = AuditDecider()
    llm = ForecastLLM(audit={"complexity": "1"})
    backfill(vault, repository, audit=True, llm_v1=False, reading=False, dry_run=False,
             clients=Clients(llm=llm, decider=decider), decider_factory=lambda: decider)
    assert decider.calls, "the ordinary revisions are still audited"
    sent = "\n".join(llm.prompts + [call["body"] for call in decider.calls])
    assert SENTINEL not in sent
    assert SENTINEL not in everything_text(paths.sqlite_path)
    audited = {row["left_id"] for row in rows(paths.sqlite_path,
                                                "SELECT left_id FROM judgment_ledger WHERE task = 'ad_feature_audit'")}
    from learnloop.adaptive_difficulty.feature_audit import item_revision

    assert item_revision(deleted)[0] not in audited and item_revision(earlier)[0] not in audited
    assert item_revision(base)[0] in audited
    plan = backfill(vault, repository, audit=True, llm_v1=False, reading=False, dry_run=True)
    assert plan["audit"]["protected_skipped"] >= 2


def test_a_revision_is_protected_by_its_own_source_even_under_an_ordinary_id(tmp_path):
    from learnloop.adaptive_difficulty.feature_audit import audit_revision
    from learnloop.adaptive_difficulty.outside import Clients, forecast_item
    from learnloop.adaptive_difficulty.protection import protection
    from learnloop.vault.models import CanonicalExercise

    paths, repository, spans = _held_out_vault(tmp_path)
    vault = load_vault(paths.root)
    base = vault.practice_items["pi_eigen_1"]
    earlier = base.model_copy(update={"prompt": f"{SENTINEL}: earlier.", "canonical_exercise": CanonicalExercise(
        source_id="src_text", extraction_id="ext_text", span_ids=[spans["exercises"][1]])})
    guard = protection(vault, repository)
    assert "pi_eigen_1" not in guard and not guard.covers(base) and guard.covers(earlier)
    decider, llm = AuditDecider(), ForecastLLM()
    assert audit_revision(vault, repository, earlier, decider_factory=lambda: decider, llm_client=llm,
                          protected=guard).status == "protected"
    assert forecast_item(vault, repository, earlier, clients=Clients(llm=llm), protected=guard).status == "protected"
    assert decider.calls == [] and llm.prompts == []


# -- F2 [High]: outside forecasts send the inputs frozen at the serve -------------------------


def _edit_prompt(paths, item_id: str, prompt: str) -> None:
    import yaml

    path = paths.practice_item_path("linear-algebra", item_id)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["prompt"] = prompt
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_outside_forecasts_send_the_inputs_frozen_at_the_serve(tmp_path):
    """F2: the background ``llm_v3`` job read the history and the item when it
    ran, so an attempt regraded after the serve (or an edited stem) reached
    a receipt stamped ``inputs_as_of`` = the serve. The serve now freezes
    the request inputs; the job sends exactly those."""

    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation

    paths = ad_plan_vault(tmp_path)
    env, clock = plan_env(paths)
    _build(env)
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "correctness, hints_used, created_at) VALUES ('att_before', 'pi_m1c', 'lo_m1', 'short_answer', "
            "'independent_attempt', 0.0, 0, ?)", (_stamp(clock.now() - timedelta(days=1)),))
    step = _serve(env)
    served_item = step["practice_item_id"]
    original_stem = load_vault(paths.root).practice_items[served_item].prompt
    # After the serve, before the background job: a regrade and an edit.
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute("UPDATE practice_attempts SET correctness = 1.0 WHERE id = 'att_before'")
    _edit_prompt(paths, served_item, "An edited stem written after the serve.")
    vault = load_vault(paths.root)
    llm, decider = ForecastLLM(p_correct=0.4), AuditDecider(p_yes=0.65)
    outcomes = forecast_presentation(vault, Repository(paths.sqlite_path), step["presentation_id"],
                                     clients=Clients(llm=llm, decider=decider),
                                     clock=FrozenClock(clock.now() + timedelta(minutes=10)))
    assert sorted(outcome.status for outcome in outcomes) == ["ok", "ok"]
    state = json.loads(llm.prompts[0].split("\n\n")[-1])["state"]
    assert [entry["result"] for entry in state["learner"]["recent_attempts"]] == ["incorrect"]
    assert state["item"]["stem"] == " ".join(original_stem.split())
    assert "edited stem" not in llm.prompts[0] and "edited stem" not in decider.calls[0]["body"]
    from learnloop.adaptive_difficulty.outside import frozen_state_key

    frozen = rows(paths.sqlite_path, "SELECT content_json, created_at FROM item_forecast_payloads WHERE owner_key = ?",
                  (frozen_state_key(step["presentation_id"]),))
    assert len(frozen) == 1
    frozen_state = json.loads(frozen[0]["content_json"])
    served_at = rows(paths.sqlite_path, "SELECT served_at FROM plan_presentations WHERE id = ?",
                     (step["presentation_id"],))[0]["served_at"]
    assert frozen[0]["created_at"] == served_at and frozen_state["inputs_as_of"] == served_at
    for receipt in ad_receipts(paths.sqlite_path):
        if receipt["forecaster"].startswith("llm_v3"):
            inputs = json.loads(receipt["inputs_json"])
            assert inputs["state_hash"] == frozen_state["state_hash"]
            assert receipt["inputs_as_of"] == served_at


def test_a_presentation_without_frozen_inputs_is_never_forecast(tmp_path):
    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation

    paths = ad_plan_vault(tmp_path)
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
                           "VALUES ('blk', 'practice', 10, 'hash', '2026-10-12T09:00:00Z')")
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
                           "VALUES ('pp_old', 'blk', 'pi_m1a', 'chooser', '2026-10-12T09:00:00Z')")
    llm, decider = ForecastLLM(), AuditDecider()
    outcomes = forecast_presentation(load_vault(paths.root), Repository(paths.sqlite_path), "pp_old",
                                     clients=Clients(llm=llm, decider=decider))
    assert {outcome.status for outcome in outcomes} == {"no_frozen_inputs"}
    assert llm.prompts == [] and decider.calls == [] and ad_receipts(paths.sqlite_path) == []


# -- F3: a reopened presentation never fabricates historical records ---------------------------


def test_reopening_a_presentation_served_while_ad_was_off_records_nothing(tmp_path):
    """F3: a step served with receipts off and reopened after they were turned
    on kept its original ``served_at``, so the hook froze today's item and
    incumbent under the original time. Only the serve that inserts the
    presentation records anything now."""

    paths = ad_plan_vault(tmp_path, config="[adaptive_difficulty]\nforecast_receipts = false\n")
    env, clock = plan_env(paths)
    _build(env)
    step = _serve(env)
    assert ad_receipts(paths.sqlite_path) == []
    env.vault.config.adaptive_difficulty.forecast_receipts = True
    clock.advance(180)
    again = _serve(env)
    assert again["presentation_id"] == step["presentation_id"]
    assert ad_receipts(paths.sqlite_path) == []
    assert rows(paths.sqlite_path, "SELECT * FROM item_serve_inputs") == []
    assert rows(paths.sqlite_path, "SELECT * FROM item_forecast_payloads") == []


# -- F4: a delayed tutor answer is stamped when it completed -----------------------------------


def test_a_pending_tutor_answer_is_stamped_when_it_completes(tmp_path):
    """F4: a tutor question pending at a serve and answered afterwards was
    recorded at its creation time, before the serve, and an answer delayed
    past the sweep's overlap was missed. The pending-to-answered update
    stamps ``answered_at`` once and the sweep reads it."""

    from tests.test_ad1_reading_opportunities import FakeMap, _setup, _sweep, at, iso

    paths, vault, repo = _setup(tmp_path)
    mapping = FakeMap()
    pending = repo.insert_question_event(
        {"context": "reader", "note_id": "span:ext1/s1", "question_md": "why?", "answer_status": "pending"},
        clock=at(-1))
    # A second question asked long before, answered after the overlap window.
    slow = repo.insert_question_event(
        {"context": "reader", "note_id": "span:ext1/s1", "question_md": "and this?", "answer_status": "pending"},
        clock=at(-180))
    _sweep(vault, repo, 0, mapping=mapping)  # the serve at 09:00 sees both pending
    assert rows(paths.sqlite_path, "SELECT * FROM ad_reading_opportunities") == []
    repo.update_question_event_answer(pending, answer_md="because", question_type="mechanism", facets=[],
                                      hint_equivalent=False, leak_suspected=False, answer_status="answered",
                                      answered_at=iso(1))
    # A later answer of the same row never moves its completion time.
    repo.update_question_event_answer(pending, answer_md="because, again", question_type="mechanism", facets=[],
                                      hint_equivalent=False, leak_suspected=False, answer_status="answered",
                                      answered_at=iso(5))
    repo.update_question_event_answer(slow, answer_md="later", question_type="mechanism", facets=[],
                                      hint_equivalent=False, leak_suspected=False, answer_status="answered",
                                      answered_at=iso(150))
    # Something newer pushes the overlap window's lower bound past the slow
    # question's creation time.
    repo.insert_source_exposure_event(
        {"context": "reader", "extraction_id": "ext1", "span_id": "s2", "revision_id": "rev1", "source_id": "src1",
         "entity_type": "reader", "entity_id": "visit1"}, clock=at(120))
    _sweep(vault, repo, 125, mapping=mapping)
    _sweep(vault, repo, 200, mapping=mapping)
    tutor = {row["source_id"]: row for row in rows(
        paths.sqlite_path, "SELECT * FROM ad_reading_opportunities WHERE kind = 'reader_tutor_exchange'")}
    assert set(tutor) == {pending, slow}
    assert tutor[pending]["source_written_at"].startswith(iso(1)[:16])
    assert tutor[slow]["source_written_at"].startswith(iso(150)[:16])
    assert all(row["source_written_at"] > iso(0) for row in tutor.values()), "never before the 09:00 serve"
    stored = rows(paths.sqlite_path, "SELECT answered_at FROM question_events WHERE id = ?", (pending,))[0]
    assert stored["answered_at"] == iso(1)


def test_the_tutor_turn_stamps_its_answer_on_its_own_clock(tmp_path):
    from learnloop.clock import utc_now_iso

    from tests.test_ad1_reading_opportunities import _setup, at

    _paths, _vault, repo = _setup(tmp_path)
    event = repo.insert_question_event(
        {"context": "reader", "note_id": "span:ext1/s1", "question_md": "why?", "answer_status": "pending"},
        clock=at(0))
    before = utc_now_iso()
    repo.update_question_event_answer(event, answer_md=None, question_type=None, facets=None, hint_equivalent=False,
                                      leak_suspected=False, answer_status="failed")
    with sqlite3.connect(_paths.sqlite_path) as connection:
        assert connection.execute("SELECT answered_at FROM question_events WHERE id = ?",
                                  (event,)).fetchone()[0] is None, "a failed turn is not an answer"
    repo.update_question_event_answer(event, answer_md="x", question_type=None, facets=None, hint_equivalent=False,
                                      leak_suspected=False, answer_status="answered")
    with sqlite3.connect(_paths.sqlite_path) as connection:
        assert connection.execute("SELECT answered_at FROM question_events WHERE id = ?",
                                  (event,)).fetchone()[0] >= before


# -- F5: the vault lifecycle fence stops background work ---------------------------------------


class _ClosingDecider(AuditDecider):
    """Answers, but the vault is switched away while the request is out."""

    def __init__(self, builds, **kwargs):
        super().__init__(**kwargs)
        self.builds = builds

    def decide(self, state, questions, *, purpose, timeout_seconds=None):
        result = super().decide(state, questions, purpose=purpose, timeout_seconds=timeout_seconds)
        self.builds.close(timeout=1.0)
        return result


def test_a_vault_switch_fences_the_feature_audit(tmp_path):
    """F5: ``audit_revision`` got no fence: after a vault switch or a close it
    still appended judgments, wrote payloads and asked its LLM fallback. Now
    nothing more is asked or written, and the request already sent keeps
    its accounting."""

    from learnloop.adaptive_difficulty.feature_audit import audit_revision
    from learnloop.hints.map_builder import BackgroundBuilds

    paths = ad_plan_vault(tmp_path)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    builds = BackgroundBuilds()
    builds.bind(paths.sqlite_path)
    fence = builds.admit(paths.sqlite_path)
    # A tie on every dimension would hand everything to the LLM fallback.
    decider = _ClosingDecider(builds, distributions={name: {"a": 0.5, "b": 0.5} for name in
                                                     ("complexity", "transfer", "scaffolding", "span", "response")})
    llm = ForecastLLM(audit={"complexity": "1"})
    outcome = audit_revision(vault, repository, vault.practice_items["pi_m1a"], decider_factory=lambda: decider,
                             llm_client=llm, fence=fence)
    assert outcome.status == "stale"
    assert len(decider.calls) == 1 and llm.prompts == [], "no request after the close"
    assert rows(paths.sqlite_path, "SELECT * FROM judgment_ledger WHERE task = 'ad_feature_audit'") == []
    assert rows(paths.sqlite_path, "SELECT * FROM item_forecast_payloads") == []
    accounted = rows(paths.sqlite_path, "SELECT status FROM model_call_receipts WHERE owner_kind = 'ad_feature_audit'")
    assert [row["status"] for row in accounted] == ["completed"], "the sent request keeps its accounting"
    # A fence closed before the unit starts asks nothing at all.
    second = audit_revision(vault, repository, vault.practice_items["pi_m1b"], decider_factory=lambda: decider,
                            llm_client=llm, fence=fence)
    assert second.status == "stale" and len(decider.calls) == 1


class _ClosingLLM(ForecastLLM):
    def __init__(self, builds, **kwargs):
        super().__init__(**kwargs)
        self.builds = builds

    def complete(self, request):
        answer = super().complete(request)
        self.builds.close(timeout=1.0)
        return answer


def test_a_vault_switch_fences_the_outside_forecasters(tmp_path):
    from learnloop.adaptive_difficulty.outside import Clients, forecast_item, forecast_presentation
    from learnloop.hints.map_builder import BackgroundBuilds

    paths = ad_plan_vault(tmp_path)
    env, clock = plan_env(paths)
    _build(env)
    step = _serve(env)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    builds = BackgroundBuilds()
    builds.bind(paths.sqlite_path)
    decider = AuditDecider()
    llm = _ClosingLLM(builds)
    outcomes = forecast_presentation(vault, repository, step["presentation_id"],
                                     clients=Clients(llm=llm, decider=decider), fence=builds.admit(paths.sqlite_path))
    assert {outcome.status for outcome in outcomes} == {"stale"}
    assert len(llm.prompts) == 1 and decider.calls == []
    assert not [row for row in ad_receipts(paths.sqlite_path) if row["forecaster"].startswith("llm_v3")]
    assert _forecast_judgments(paths) == []
    builds.bind(paths.sqlite_path)
    llm_v1 = _ClosingLLM(builds)
    outcome = forecast_item(vault, repository, vault.practice_items["pi_m1a"], clients=Clients(llm=llm_v1),
                            fence=builds.admit(paths.sqlite_path))
    assert outcome.status == "stale" and len(llm_v1.prompts) == 1
    assert not [row for row in ad_receipts(paths.sqlite_path) if row["scope"] == "item"]


# -- F6: one purchase per revision, across jobs and processes ----------------------------------


class _SlowDecider(AuditDecider):
    def decide(self, state, questions, *, purpose, timeout_seconds=None):
        time.sleep(0.4)
        return super().decide(state, questions, purpose=purpose, timeout_seconds=timeout_seconds)


def test_overlapping_preparations_audit_a_revision_once(tmp_path):
    """F6: preparations of ``[A, B]`` and ``[B]`` (different in-flight keys),
    or a sidecar job and a CLI backfill, could both pay for B's audit before
    either wrote it. Each unit now takes a durable claim and re-checks what
    is persisted once it holds it."""

    from learnloop.adaptive_difficulty.background import prepare_items
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path, config="[adaptive_difficulty]\noutside_forecasters = []\n")
    vault = load_vault(paths.root)
    decider = _SlowDecider()
    clients = Clients(llm=ForecastLLM(), decider=decider)
    results: dict[str, list] = {}

    def run(name, ids):
        results[name] = prepare_items(vault, Repository(paths.sqlite_path), ids, clients=clients,
                                      decider_factory=lambda: decider)

    first = threading.Thread(target=run, args=("ab", ["pi_m1a", "pi_m1b"]))
    second = threading.Thread(target=run, args=("b", ["pi_m1b"]))
    first.start()
    time.sleep(0.1)
    second.start()
    first.join(30)
    second.join(30)
    asked = [call["state"]["question"] for call in decider.calls]
    prompts = load_vault(paths.root).practice_items
    assert asked.count(prompts["pi_m1b"].prompt) == 1, "B is paid for once"
    assert asked.count(prompts["pi_m1a"].prompt) == 1
    statuses = sorted(entry["audit"]["status"] for name in results for entry in results[name]
                      if entry["practice_item_id"] == "pi_m1b")
    assert statuses in (["audited", "busy"], ["audited", "current"])


def test_a_claim_held_by_another_process_is_skipped(tmp_path):
    from learnloop.adaptive_difficulty.claims import CLAIM_TASK, PRODUCER, audit_key, item_forecast_key
    from learnloop.adaptive_difficulty.feature_audit import audit_revision, item_revision
    from learnloop.adaptive_difficulty.outside import Clients, forecast_item
    from learnloop.clock import utc_now_iso
    from learnloop.db.stores.judgment_claims import claim_work

    paths = ad_plan_vault(tmp_path)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    item = vault.practice_items["pi_m1a"]
    content_hash, _json = item_revision(item)
    with repository.atomic():
        for key in (audit_key(content_hash), item_forecast_key(content_hash)):
            claim_work(repository.connection(), claim_key=key, task=CLAIM_TASK, producer=PRODUCER,
                       prompt_version=None, input_hash="", owner="proc_cli:other", now=utc_now_iso(),
                       lease_seconds=120)
    decider, llm = AuditDecider(), ForecastLLM()
    assert audit_revision(vault, repository, item, decider_factory=lambda: decider, llm_client=llm).status == "busy"
    assert forecast_item(vault, repository, item, clients=Clients(llm=llm)).status == "busy"
    assert decider.calls == [] and llm.prompts == []


# -- F7: the configured metered price is classified --------------------------------------------


def test_a_configured_ad_price_is_a_classified_config_leaf():
    """F7: ``adaptive_difficulty.price_per_million`` is null by default, so the
    default-config audit never saw it; set (as a metered route needs), it was
    a numeric leaf ``classify_config_path`` returned None for."""

    from learnloop.config.schema import LearnLoopConfig
    from learnloop.params import parameter_registry as pr

    config = LearnLoopConfig.model_validate({"adaptive_difficulty": {"price_per_million": 1.0}})
    leaves = pr.config_numeric_leaves(config)
    assert "adaptive_difficulty.price_per_million" in leaves
    unclassified = [path for path in leaves if path.startswith("adaptive_difficulty.")
                    and pr.classify_config_path(path) is None]
    assert unclassified == []
    rule = pr.classify_config_path("adaptive_difficulty.price_per_million")
    assert rule is not None and (rule.kind, rule.param_class) == ("structural", "operational")


# -- F8: accepted outside verdicts reach judgment_ledger ---------------------------------------


def test_accepted_outside_forecasts_append_one_judgment_each(tmp_path):
    """F8: an outside forecaster's probability reached its receipt and its
    payloads but no ``judgment_ledger`` row (handoffs §0: every paid verdict
    is ledgered). Each accepted forecast now appends one, in its receipt's
    transaction; a refused one appends none, and a rerun writes nothing."""

    from learnloop.adaptive_difficulty.outside import Clients, forecast_item, forecast_presentation

    paths = ad_plan_vault(tmp_path)
    env, clock = plan_env(paths)
    _build(env)
    step = _serve(env)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    clients = Clients(llm=ForecastLLM(p_correct=0.4), decider=AuditDecider(p_yes=0.65))
    forecast_presentation(vault, repository, step["presentation_id"], clients=clients)
    forecast_item(vault, repository, vault.practice_items["pi_m1a"], clients=clients)
    judgments = _forecast_judgments(paths)
    by_forecaster = {row["right_id"]: row for row in judgments}
    assert set(by_forecaster) == {"llm_v3:llm", "llm_v3:decider", "llm_v1:item"}
    receipts = {row["receipt_key"]: row for row in ad_receipts(paths.sqlite_path)}
    for forecaster, row in by_forecaster.items():
        rationale = json.loads(row["rationale"])
        receipt = receipts[rationale["receipt_key"]]
        assert receipt["forecaster"] == forecaster and receipt["id"] == rationale["receipt_id"]
        assert row["score"] == pytest.approx(receipt["p"]) and row["judge_model"] and row["prompt_version"]
        assert row["input_hash"] == json.loads(receipt["forecast_json"])["request_hash"]
        assert row["right_kind"] == "forecaster"
    assert by_forecaster["llm_v3:decider"]["judge"] == "decider" and by_forecaster["llm_v3:llm"]["judge"] == "llm"
    assert by_forecaster["llm_v1:item"]["left_kind"] == "practice_item_revision"
    assert by_forecaster["llm_v3:llm"]["left_kind"] == "plan_presentation"
    forecast_presentation(vault, repository, step["presentation_id"], clients=clients)
    forecast_item(vault, repository, vault.practice_items["pi_m1a"], clients=clients)
    assert len(_forecast_judgments(paths)) == 3


def test_a_refused_forecast_appends_no_judgment(tmp_path):
    from learnloop.adaptive_difficulty.outside import Clients, forecast_item

    from tests.test_ad1_outside_and_cli import MeteredLLM

    paths = ad_plan_vault(tmp_path)
    vault = load_vault(paths.root)
    outcome = forecast_item(vault, Repository(paths.sqlite_path), vault.practice_items["pi_m1a"],
                            clients=Clients(llm=MeteredLLM()))
    assert outcome.status == "refused_spend" and _forecast_judgments(paths) == []


# -- F9: the dry run plans the spend it will charge --------------------------------------------


METERED = """
[ai.providers.metered_test]
type = "openrouter"
model = "vendor/metered-model"
"""


def _route_to_metered(paths) -> None:
    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    assert "\n[ai.routing]\n" in text
    config.write_text(text.replace("\n[ai.routing]\n", '\n[ai.routing]\nad_feature_audit = "metered_test"\n'
                                   'ad_forecast_llm = "metered_test"\n', 1), encoding="utf-8")


def test_the_backfill_dry_run_plans_routes_through_the_spend_framework(tmp_path):
    """F9: the dry run printed input tokens only: no dollars, output allowance,
    billing label or cap check, and it listed Decider requests with the
    audit's Decider switch off. It now plans each resolved route."""

    from learnloop.adaptive_difficulty.backfill import backfill

    def plan(name, extra=""):
        paths = ad_plan_vault(tmp_path / name, config=METERED + extra)
        _route_to_metered(paths)
        before = paths.sqlite_path.read_bytes()
        result = backfill(load_vault(paths.root), Repository(paths.sqlite_path), audit=True, llm_v1=True,
                          reading=False, dry_run=True)
        assert paths.sqlite_path.read_bytes() == before
        return result

    unpriced = plan("unpriced")
    audit, v1 = unpriced["audit"], unpriced["llm_v1"]
    assert audit["decider"]["requests"] == audit["revisions"] > 0
    assert audit["decider"]["cost_basis"] == "listed_input_price" and audit["decider"]["estimated_usd"] > 0
    assert audit["llm"]["role"] == "fallback_worst_case" and audit["llm"]["billing"] == "metered"
    assert "price_per_million" in audit["llm"]["refused"] and "price_per_million" in v1["llm"]["refused"]
    assert v1["llm"]["output_tokens_per_call"] > 0
    assert unpriced["spend"]["metered_worst_case_usd"] is None and unpriced["spend"]["fits_today"] is None

    priced = plan("priced", "\n[adaptive_difficulty]\nprice_per_million = 2.0\ndaily_spend_cap_usd = 0.5\n")
    llm = priced["llm_v1"]["llm"]
    assert "refused" not in llm and llm["estimated_usd"] > 0
    assert llm["estimated_tokens"] >= llm["calls"] * llm["output_tokens_per_call"]
    worst = priced["spend"]["metered_worst_case_usd"]
    assert worst == pytest.approx(priced["audit"]["decider"]["estimated_usd"] + priced["audit"]["llm"]["estimated_usd"]
                                  + llm["estimated_usd"], abs=1e-5)
    assert priced["spend"]["fits_today"] is (worst <= 0.5)

    off = plan("decider_off", "\n[decider_routes]\nad_feature_audit = false\n")
    assert off["audit"]["decider"]["requests"] == 0 and off["audit"]["llm"]["role"] == "primary"


# -- F10: new revisions are prepared after publication, not only from a plan --------------------


def test_a_reload_prepares_the_revisions_published_since_the_last_load(tmp_path):
    """F10: preparation was scheduled only from the daily plan's unresolved
    pool, so an imported or generated item outside it was never audited or
    forecast. A reload of the same vault (every publication and import ends
    in one) now prepares the new and edited revisions; a first open
    schedules nothing (the existing pool is the owner-run backfill's)."""

    from learnloop.adaptive_difficulty.outside import Clients
    from learnloop_sidecar.context import SidecarContext

    paths = ad_plan_vault(tmp_path, config="[adaptive_difficulty]\noutside_forecasters = [\"llm_v1:item\"]\n")
    ctx = SidecarContext()
    decider, llm = AuditDecider(), ForecastLLM(p_correct=0.5)
    ctx.ad_clients = Clients(llm=llm, decider=decider)
    ctx.load(paths.root)
    _wait_idle(ctx)
    assert decider.calls == [] and llm.prompts == [], "a first open is the backfill's"
    _edit_prompt(paths, "pi_m1b", "A revised stem published after the open.")
    ctx.reload(maintenance=False)
    _wait_idle(ctx)
    assert [call["state"]["question"] for call in decider.calls] == ["A revised stem published after the open."]
    assert len(llm.prompts) == 1
    item_receipts = [row for row in ad_receipts(paths.sqlite_path) if row["scope"] == "item"]
    assert [row["practice_item_id"] for row in item_receipts] == ["pi_m1b"]
    ctx.reload(maintenance=False)
    _wait_idle(ctx)
    assert len(decider.calls) == 1, "an unchanged reload prepares nothing"
    ctx.map_builds.close()


def _wait_idle(ctx, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while ctx.map_builds.running and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not ctx.map_builds.running


def test_the_watchers_changed_items_are_prepared():
    from learnloop.adaptive_difficulty.background import changed_revisions

    class _Vault:
        def __init__(self, items):
            self.practice_items = items

    a, b, c = object(), object(), object()
    assert changed_revisions(None, _Vault({"a": a})) == []
    assert changed_revisions(_Vault({"a": a, "b": b}), _Vault({"a": a, "b": c, "n": c})) == ["b", "n"]
