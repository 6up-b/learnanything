"""Adaptive difficulty AD1: measure and log (spec_adaptive_difficulty_v1 §14 AD1).

The gate's server-side tests (G-AD1-3 and G-AD1-10 are in
``test_ad1_attempt_columns.py``, G-AD1-11 in ``test_ad1_reading_opportunities.py``).
Each failed before AD1 for the reason its docstring names: no
``item_unassisted_success`` forecast kind, no serve-time receipts, no serve
inputs, no feature audit, no outside forecasters, no switches. Fakes only: no
network, no paid call.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.clock import FrozenClock, parse_utc
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import (
    ALL_OFF,
    ITEMS,
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


def _presentation(paths, presentation_id):
    return rows(paths.sqlite_path, "SELECT * FROM plan_presentations WHERE id = ?", (presentation_id,))[0]


def _clock_at(env_clock, minutes: float) -> FrozenClock:
    return FrozenClock(env_clock.now() + timedelta(minutes=minutes))


# -- G-AD1-1 ----------------------------------------------------------------------------------


class _Abort(BaseException):
    """Raised after AD's writes, inside the serve transaction (not an Exception)."""


def test_forecast_receipt_written_in_serve_transaction(tmp_path, monkeypatch):
    """Serving a plan item writes one item forecast per in-process forecaster in
    the same transaction as ``plan_presentations``, with ``inputs_as_of <=
    served_at`` (fails before AD1: there is no such receipt)."""

    from learnloop.scheduling.forecast_receipts import valid_for_serve

    paths = ad_plan_vault(tmp_path / "a")
    env, _clock = plan_env(paths)
    _build(env)
    step = _serve(env)
    presentation = _presentation(paths, step["presentation_id"])
    receipts = ad_receipts(paths.sqlite_path)
    assert sorted(receipt["forecaster"] for receipt in receipts) == ["lo_general+composite", "mastery_ekf"]
    for receipt in receipts:
        assert receipt["plan_presentation_id"] == step["presentation_id"]
        assert (receipt["scope"], receipt["binding_kind"], receipt["decision_kind"]) == (
            "presentation", "plan_presentation", "serve")
        assert receipt["event"] == "unassisted_success" and receipt["status"] == "ok"
        assert 0.0 <= receipt["p"] <= 1.0
        assert receipt["created_at"] == presentation["served_at"]
        assert parse_utc(receipt["inputs_as_of"]) <= parse_utc(presentation["served_at"])
        assert valid_for_serve(receipt, presentation["served_at"])
    serve_inputs = rows(paths.sqlite_path, "SELECT * FROM item_serve_inputs")
    assert [row["plan_presentation_id"] for row in serve_inputs] == [step["presentation_id"]]
    # A reopened step writes nothing new.
    again = _serve(env)
    assert again["presentation_id"] == step["presentation_id"]
    assert len(ad_receipts(paths.sqlite_path)) == 2

    # Same transaction: a serve that fails after AD's writes keeps neither.
    from learnloop.adaptive_difficulty import serve as ad_serve

    original = ad_serve.record_plan_serve

    def record_then_abort(*args, **kwargs):
        written = original(*args, **kwargs)
        assert written is not None and len(written.receipt_ids) == 2
        raise _Abort()

    second = ad_plan_vault(tmp_path / "b")
    env_b, _clock_b = plan_env(second)
    _build(env_b)
    monkeypatch.setattr(ad_serve, "record_plan_serve", record_then_abort)
    with pytest.raises(_Abort):
        advance(env_b, serve=True)
    assert rows(second.sqlite_path, "SELECT * FROM plan_presentations") == []
    assert ad_receipts(second.sqlite_path) == []
    assert rows(second.sqlite_path, "SELECT * FROM item_serve_inputs") == []


def test_a_failed_ad_write_never_breaks_the_serve(tmp_path, monkeypatch):
    from learnloop.adaptive_difficulty import serve as ad_serve

    paths = ad_plan_vault(tmp_path)
    env, _clock = plan_env(paths)
    _build(env)

    def broken(*_args, **_kwargs):
        raise RuntimeError("AD broke")

    monkeypatch.setattr(ad_serve, "build_row", broken)
    step = _serve(env)
    assert _presentation(paths, step["presentation_id"])
    assert ad_receipts(paths.sqlite_path) == [] and rows(paths.sqlite_path, "SELECT * FROM item_serve_inputs") == []


# -- G-AD1-2 ----------------------------------------------------------------------------------


def _forecast_presentation(paths, presentation_id, clock, *, llm=None, decider=None):
    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation

    vault = load_vault(paths.root)
    return forecast_presentation(vault, Repository(paths.sqlite_path), presentation_id,
                                 clients=Clients(llm=llm or ForecastLLM(p_correct=0.4),
                                                 decider=decider or AuditDecider(p_yes=0.65)),
                                 clock=clock)


def test_late_outside_forecast_is_valid_if_inputs_predate_serve(tmp_path):
    """``llm_v3:*`` run after the serve, in the background: their receipts arrive
    late and are valid, because the inputs they read predate the serve (fails
    before AD1: no validity rule, no outside forecaster)."""

    from learnloop.scheduling.forecast_receipts import valid_for_serve

    paths = ad_plan_vault(tmp_path)
    env, clock = plan_env(paths)
    _build(env)
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "correctness, hints_used, created_at) VALUES ('att_before', 'pi_m1c', 'lo_m1', 'short_answer', "
            "'independent_attempt', 1.0, 0, ?)",
            ((clock.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),))
    step = _serve(env)
    served_at = _presentation(paths, step["presentation_id"])["served_at"]
    # An attempt completed after the serve is not an input of its forecasts.
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "correctness, hints_used, created_at) VALUES ('att_after', 'pi_m1b', 'lo_m1', 'short_answer', "
            "'independent_attempt', 0.0, 2, ?)", ((clock.now() + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),))
    llm, decider = ForecastLLM(p_correct=0.4), AuditDecider(p_yes=0.65)
    outcomes = _forecast_presentation(paths, step["presentation_id"], _clock_at(clock, 10), llm=llm, decider=decider)
    assert sorted((outcome.forecaster, outcome.status) for outcome in outcomes) == [
        ("llm_v3:decider", "ok"), ("llm_v3:llm", "ok")]
    late = {receipt["forecaster"]: receipt for receipt in ad_receipts(paths.sqlite_path)
            if receipt["forecaster"].startswith("llm_v3")}
    assert late["llm_v3:llm"]["p"] == pytest.approx(0.4) and late["llm_v3:decider"]["p"] == pytest.approx(0.65)
    for receipt in late.values():
        assert parse_utc(receipt["created_at"]) > parse_utc(served_at)
        assert parse_utc(receipt["received_at"]) >= parse_utc(receipt["created_at"])
        assert receipt["inputs_as_of"] == served_at
        assert valid_for_serve(receipt, served_at)
    from tests.structured_ai import _request_context

    card = json.loads(llm.prompts[0].split("\n\n")[-1])["state"]["learner"]
    assert [(entry["result"], entry["hints_used"]) for entry in card["recent_attempts"]] == [("correct", 0)]
    assert _request_context is not None
    payloads = rows(paths.sqlite_path, "SELECT * FROM item_forecast_payloads")
    assert {payload["kind"] for payload in payloads} == {"request", "response"}
    # Run again: each presentation is forecast once.
    assert all(outcome.status == "ok" for outcome in outcomes)
    assert _forecast_presentation(paths, step["presentation_id"], _clock_at(clock, 20)) == []


def test_forecast_with_post_serve_inputs_is_invalid(tmp_path):
    from learnloop.scheduling.forecast_receipts import ForecastReceipt, record_receipts, valid_for_serve

    paths = ad_plan_vault(tmp_path)
    env, clock = plan_env(paths)
    _build(env)
    step = _serve(env)
    served_at = _presentation(paths, step["presentation_id"])["served_at"]
    after = (clock.now() + timedelta(minutes=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    record_receipts(Repository(paths.sqlite_path), [ForecastReceipt(
        receipt_key="item_unassisted_success:plan_presentation:x:late_reader", kind="item_unassisted_success",
        forecaster="late_reader", forecaster_version="v", scope="presentation", decision_kind="serve",
        binding_kind="plan_presentation", event="unassisted_success", forecast={"p": 0.5}, inputs={},
        parameters=[], inputs_as_of=after, p=0.5, columns={"plan_presentation_id": step["presentation_id"]},
    )], created_at=(clock.now() + timedelta(minutes=4)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    receipt = [row for row in ad_receipts(paths.sqlite_path) if row["forecaster"] == "late_reader"][0]
    assert not valid_for_serve(receipt, served_at)
    assert not valid_for_serve({"inputs_as_of": None}, served_at)


# -- G-AD1-4 ----------------------------------------------------------------------------------


def _audit_rows(paths):
    return rows(paths.sqlite_path, "SELECT * FROM judgment_ledger WHERE task = 'ad_feature_audit' ORDER BY rowid")


def test_feature_audit_ledgered_with_fallback(tmp_path):
    """The Decider's argmax per dimension, a tie is no answer, the LLM fallback
    recorded (fails before AD1: no audit task)."""

    from learnloop.adaptive_difficulty.feature_audit import audit_revision, canonical_audits, item_revision

    paths = ad_plan_vault(tmp_path)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    item = vault.practice_items["pi_m1a"]
    tie = {"0": 0.3, "1": 0.3, "2": 0.2, "3": 0.1, "4": 0.1}
    decider = AuditDecider({"complexity": tie, "transfer": {"near": 0.8}, "scaffolding": {"none": 0.9},
                            "span": {"multi_step": 0.7}, "response": {"short_constructed": 0.6}})
    llm = ForecastLLM(audit={"complexity": "2"})
    outcome = audit_revision(vault, repository, item, decider_factory=lambda: decider, llm_client=llm,
                             clock=FrozenClock(datetime(2026, 10, 12, 10, 0, tzinfo=UTC)))
    content_hash, _json = item_revision(item)
    assert outcome.status == "audited" and outcome.content_hash == content_hash
    assert outcome.answered == {"complexity": "2", "transfer": "near", "scaffolding": "none", "span": "multi_step",
                                "response": "short_constructed"}
    assert outcome.judges["complexity"] == "llm" and outcome.judges["transfer"] == "decider"
    ledger = _audit_rows(paths)
    decider_rows = [row for row in ledger if row["judge"] == "decider"]
    assert len(decider_rows) == 5 and {row["right_id"] for row in decider_rows} == set(outcome.answered)
    assert all(row["prompt_version"] == "ad-feature-audit-v1" and row["left_kind"] == "practice_item_revision"
               and row["left_id"] == content_hash for row in ledger)
    tied = [row for row in decider_rows if row["right_id"] == "complexity"][0]
    assert tied["verdict"] == "tied" and tied["score"] is None
    assert json.loads(tied["rationale"])["probabilities"]["1"] == pytest.approx(0.3)
    fallback = [row for row in ledger if row["judge"] == "llm"]
    assert [(row["right_id"], row["verdict"]) for row in fallback] == [("complexity", "2")]
    assert json.loads(fallback[0]["rationale"])["fallback"] == "tied"
    assert json.loads(fallback[0]["rationale"])["decider_judgment_id"] == tied["id"]
    # The Decider read the stem and reference answer only.
    assert set(decider.calls[0]["state"]) == {"question", "reference_answer", "schema"}
    # The canonical audit is the earliest answer; a later run asks nothing.
    from learnloop.adaptive_difficulty.operation import ad_operation

    with ad_operation(vault, repository), sqlite3.connect(paths.sqlite_path) as connection:
        canonical = canonical_audits(connection, content_hash)  # an AD reader: inside an operation
    assert canonical["complexity"]["judgment_id"] == fallback[0]["id"]
    rerun = audit_revision(vault, repository, item, decider_factory=lambda: decider, llm_client=llm)
    assert rerun.status == "current" and len(decider.calls) == 1 and len(_audit_rows(paths)) == len(ledger)


def test_a_failed_decider_hands_every_dimension_to_the_llm(tmp_path):
    from learnloop.adaptive_difficulty.feature_audit import audit_revision

    paths = ad_plan_vault(tmp_path)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    llm = ForecastLLM(audit={"complexity": "1", "transfer": "same_context", "scaffolding": "cue",
                             "span": "single_step", "response": "short_constructed"})
    outcome = audit_revision(vault, repository, vault.practice_items["pi_m1a"],
                             decider_factory=lambda: AuditDecider(error=RuntimeError("down")), llm_client=llm)
    assert outcome.decider_status == "failed" and len(outcome.answered) == 5
    ledger = _audit_rows(paths)
    assert sorted(row["verdict"] for row in ledger if row["judge"] == "decider") == ["failed"] * 5
    assert all(json.loads(row["rationale"])["fallback"] == "failed" for row in ledger if row["judge"] == "llm")


def test_the_decider_switch_off_audits_with_the_llm_only(tmp_path):
    from learnloop.adaptive_difficulty.feature_audit import audit_revision

    paths = ad_plan_vault(tmp_path, config="[decider_routes]\nad_feature_audit = false\n")
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    decider = AuditDecider()
    llm = ForecastLLM(audit={"complexity": "1"})
    audit_revision(vault, repository, vault.practice_items["pi_m1a"], decider_factory=lambda: decider, llm_client=llm)
    ledger = _audit_rows(paths)
    assert decider.calls == [] and [row["judge"] for row in ledger] == ["llm"]
    assert json.loads(ledger[0]["rationale"])["fallback"] == "decider_off"


# -- G-AD1-5 ----------------------------------------------------------------------------------


AD_TABLES = ("item_serve_inputs", "ad_reading_opportunities", "item_forecast_payloads")


def _ad_row_counts(sqlite_path):
    counts = {table: rows(sqlite_path, f"SELECT COUNT(*) AS n FROM {table}")[0]["n"] for table in AD_TABLES}
    counts["item_forecasts"] = len(ad_receipts(sqlite_path))
    counts["audits"] = rows(sqlite_path, "SELECT COUNT(*) AS n FROM judgment_ledger WHERE task = 'ad_feature_audit'"
                            )[0]["n"]
    return counts


class _RecordingGrader:
    """A structured grader recording every prompt it is sent (full credit)."""

    provider_name = "fake_grader"
    provider_type = "fake"
    model = "fake-grader"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def supports(self, capability: str) -> bool:
        from learnloop.ai.isolation import TOOL_FREE
        from learnloop.ai.transport import ISOLATED_TURN, STRUCTURED_COMPLETION

        return capability in {STRUCTURED_COMPLETION, TOOL_FREE, ISOLATED_TURN}

    def complete(self, request):
        from learnloop.attempts.ai_contracts import CriterionEvidence, GradingProposal
        from tests.structured_ai import _request_context

        self.prompts.append(request.prompt)
        context = _request_context(request.prompt, request.purpose)
        return GradingProposal(
            attempt_id=context.attempt_id, practice_item_id=context.practice_item_id, rubric_score=4,
            criterion_evidence=[CriterionEvidence(criterion_id="correctness", points_awarded=4, evidence="Right.")],
            fatal_errors=[], error_attributions=[], grader_confidence=0.9, repair_suggestions=[],
        )


def _graded_attempt_prompts(tmp_path, name: str, config: str) -> tuple[list[str], dict]:
    from learnloop.attempts.attempts import AttemptDraft, complete_attempt_with_ai_required
    from tests.helpers import append_config_toml, create_basic_vault
    from tests.split_live_helpers import ReadyRuntime

    paths = create_basic_vault(tmp_path / name)
    if config:
        append_config_toml(paths.root, config)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    grader = _RecordingGrader()
    result = complete_attempt_with_ai_required(
        vault, repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="U Sigma V^T", hints_used=1,
                     attempt_type="hinted_attempt", submission_id="k1", difficulty_rating="hard",
                     first_hint_progress="no_draft"),
        runtime=ReadyRuntime(), ai_client=grader, clock=FrozenClock(datetime(2026, 10, 12, 9, 0, tzinfo=UTC)),
    )
    # The attempt's own id is the one thing that differs between two vaults.
    return ([prompt.replace(result.attempt_id, "<attempt>") for prompt in grader.prompts],
            repository.fetch_practice_attempt(result.attempt_id))


def test_ad1_switches_restore_predecessor(tmp_path):
    """All four switches false: no new rows, prompts byte-identical, no extra
    calls (fails before AD1: there are no switches to set)."""

    from learnloop.adaptive_difficulty.backfill import backfill
    from learnloop.adaptive_difficulty.background import prepare_items
    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation
    from learnloop_sidecar.context import config_dto

    paths = ad_plan_vault(tmp_path / "off", config=ALL_OFF)
    env, clock = plan_env(paths)
    _build(env)
    step = _serve(env)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    decider, llm = AuditDecider(), ForecastLLM()
    clients = Clients(llm=llm, decider=decider)
    prepare_items(vault, repository, ITEMS, clients=clients, decider_factory=lambda: decider)
    assert forecast_presentation(vault, repository, step["presentation_id"], clients=clients) == []
    result = backfill(vault, repository, audit=True, llm_v1=True, reading=True, dry_run=False, clients=clients,
                      decider_factory=lambda: decider)
    assert {part["status"] for part in (result["audit"], result["llm_v1"], result["reading"])} == {"disabled"}
    assert _ad_row_counts(paths.sqlite_path) == {table: 0 for table in (*AD_TABLES, "item_forecasts", "audits")}
    assert decider.calls == [] and llm.prompts == [], "no extra calls"
    assert "adaptiveDifficulty" not in config_dto(vault)
    # Prompts byte-identical: the grader sees exactly what it saw before AD1,
    # with the tap and the marker sent, and they are not stored.
    on_prompts, on_attempt = _graded_attempt_prompts(tmp_path, "graded_on", "")
    off_prompts, off_attempt = _graded_attempt_prompts(tmp_path, "graded_off", ALL_OFF)
    assert on_prompts and on_prompts == off_prompts
    assert all("hard" not in prompt.split("prompt_version")[0] for prompt in on_prompts)
    assert (on_attempt["difficulty_rating"], on_attempt["first_hint_progress"]) == ("hard", "no_draft")
    assert (off_attempt["difficulty_rating"], off_attempt["first_hint_progress"]) == (None, None)


def test_the_master_switch_turns_every_ad_behaviour_off(tmp_path):
    paths = ad_plan_vault(tmp_path, config="[adaptive_difficulty]\nenabled = false\n")
    env, _clock = plan_env(paths)
    _build(env)
    _serve(env)
    assert _ad_row_counts(paths.sqlite_path)["item_forecasts"] == 0
    assert _ad_row_counts(paths.sqlite_path)["item_serve_inputs"] == 0


# -- G-AD1-6 ----------------------------------------------------------------------------------


SENTINEL = "SENTINEL-HELD-OUT-7d1f"


def test_held_out_sentinel_never_reaches_ad_inputs(tmp_path):
    """A sentinel in a held-out unit appears in no AD prompt, receipt, payload
    or audit input (fails before AD1: there is no AD input to guard)."""

    from learnloop.adaptive_difficulty.backfill import backfill
    from learnloop.adaptive_difficulty.background import prepare_items
    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation
    from learnloop.adaptive_difficulty.serve import record_plan_serve
    from learnloop.content.synthesis.source_unit_selection import save_unit_selection
    from learnloop.vault.models import CanonicalExercise
    from learnloop.vault.writer import upsert_practice_item
    from tests.source_service_fakes import build_textbook_vault

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    vault = load_vault(paths.root)
    base = vault.practice_items["pi_eigen_1"]
    held = base.model_copy(update={
        "id": "pi_held", "prompt": f"{SENTINEL}: find the eigenvalues.", "expected_answer": f"{SENTINEL} answer",
        "canonical_exercise": CanonicalExercise(source_id="src_text", extraction_id="ext_text",
                                                span_ids=[spans["exercises"][1]]),
    })
    upsert_practice_item(paths.root, held.model_dump(mode="json"))
    vault = load_vault(paths.root)
    from learnloop.adaptive_difficulty.protection import protected_items

    assert "pi_held" in protected_items(vault, repository)
    served = "2026-10-12T09:00:00Z"
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "correctness, created_at) VALUES ('att_held', 'pi_held', ?, ?, 'independent_attempt', 1.0, "
            "'2026-10-11T09:00:00Z')", (held.learning_object_id, held.practice_mode))
        for block, item_id in (("blk_other", "pi_eigen_2"), ("blk_held", "pi_held")):
            connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
                               "VALUES (?, 'practice', 10, 'hash', ?)", (block, served))
            connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
                               "VALUES (?, ?, ?, 'chooser', ?)", (f"pp_{block}", block, item_id, served))
    for block, item_id in (("blk_other", "pi_eigen_2"), ("blk_held", "pi_held")):
        with repository.atomic():
            record_plan_serve(vault, repository, presentation_id=f"pp_{block}", practice_item_id=item_id,
                              served_at=served)
    decider = AuditDecider()
    llm = ForecastLLM(audit={"complexity": "1"})
    clients = Clients(llm=llm, decider=decider)
    prepared = prepare_items(vault, repository, list(vault.practice_items), clients=clients,
                             decider_factory=lambda: decider)
    assert any(entry.get("audit", {}).get("status") == "audited" for entry in prepared)
    assert [entry for entry in prepared if entry["practice_item_id"] == "pi_held"][0]["audit"]["status"] == "protected"
    for presentation in ("pp_blk_other", "pp_blk_held"):
        forecast_presentation(vault, repository, presentation, clients=clients)
    backfill(vault, repository, audit=True, llm_v1=True, reading=True, dry_run=False, clients=clients,
             decider_factory=lambda: decider)
    assert llm.prompts and decider.calls
    sent = "\n".join(llm.prompts + [call["body"] for call in decider.calls])
    assert SENTINEL not in sent
    stored = everything_text(paths.sqlite_path)
    assert "pi_eigen_2" in stored and SENTINEL not in stored
    assert "pi_held" not in json.dumps(rows(paths.sqlite_path, "SELECT * FROM item_serve_inputs"))
    assert not [row for row in ad_receipts(paths.sqlite_path) if row["practice_item_id"] == "pi_held"]


# -- G-AD1-7 ----------------------------------------------------------------------------------


def test_replay_reads_receipts_zero_model_calls(tmp_path, monkeypatch):
    """A rebuild with every model constructor forbidden succeeds and leaves AD's
    receipts byte-identical: replay neither re-asks nor rewrites them (fails
    before AD1: there are no receipts to read)."""

    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    paths = ad_plan_vault(tmp_path)
    env, clock = plan_env(paths)
    _build(env)
    step = _serve(env)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    forecast_presentation(vault, repository, step["presentation_id"],
                          clients=Clients(llm=ForecastLLM(), decider=AuditDecider()))
    before = everything_text(paths.sqlite_path)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("replay constructed a model client")

    import learnloop.ai.routing as routing

    for name in ("ready_client_for_task", "build_client", "client_for_task"):
        if hasattr(routing, name):
            monkeypatch.setattr(routing, name, forbidden)
    import learnloop.decider_judgments as decider_judgments

    monkeypatch.setattr(decider_judgments, "client_for", forbidden)
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(clock.now() + timedelta(hours=1)))
    assert everything_text(paths.sqlite_path) == before


# -- G-AD1-8 ----------------------------------------------------------------------------------


def test_serve_inputs_frozen_against_later_audit_and_edit(tmp_path):
    """An audit landing after the serve, a re-audit and an item edit change no
    ``item_serve_inputs`` row; the served revision is in
    ``practice_item_snapshots`` (fails before AD1: no receipt)."""

    import yaml

    from learnloop.adaptive_difficulty.feature_audit import audit_revision, item_revision

    paths = ad_plan_vault(tmp_path)
    env, clock = plan_env(paths)
    _build(env)
    step = _serve(env)
    frozen = rows(paths.sqlite_path, "SELECT * FROM item_serve_inputs")
    assert len(frozen) == 1
    row = frozen[0]
    assert json.loads(row["audit_json"]) == {dim: None for dim in json.loads(row["audit_json"])}
    assert json.loads(row["resolved_features_json"])["complexity"] == 1
    snapshot = rows(paths.sqlite_path, "SELECT * FROM practice_item_snapshots WHERE content_hash = ?",
                    (row["content_hash"],))
    assert snapshot and snapshot[0]["practice_item_id"] == step["practice_item_id"]
    # An audit that lands after the serve, then a re-audit, then an edit.
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    item = vault.practice_items[step["practice_item_id"]]
    decider = AuditDecider({"complexity": {"3": 0.9}})
    audit_revision(vault, repository, item, decider_factory=lambda: decider,
                   clock=FrozenClock(clock.now() + timedelta(minutes=5)))
    audit_revision(vault, repository, item, decider_factory=lambda: AuditDecider({"complexity": {"4": 0.9}}),
                   clock=FrozenClock(clock.now() + timedelta(minutes=6)))
    path = paths.practice_item_path("linear-algebra", step["practice_item_id"])
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["prompt"] = "An edited question."
    payload["task_features"]["complexity"] = 4
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    edited = load_vault(paths.root).practice_items[step["practice_item_id"]]
    assert item_revision(edited)[0] != row["content_hash"]
    assert rows(paths.sqlite_path, "SELECT * FROM item_serve_inputs") == frozen
    with sqlite3.connect(paths.sqlite_path) as connection:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("UPDATE item_serve_inputs SET resolved_features_json = '{}'")
    # A later serve of another never-attempted item reads the audit answered before it.
    clock.advance(10)
    audit_revision(load_vault(paths.root), repository, load_vault(paths.root).practice_items["pi_m1b"],
                   decider_factory=lambda: AuditDecider({"complexity": {"2": 0.9}}),
                   clock=FrozenClock(clock.now()))
    later_vault = load_vault(paths.root)
    from learnloop.adaptive_difficulty.serve import record_plan_serve

    served = clock.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
                           "VALUES ('blk_x', 'practice', 10, 'hash', ?)", (served,))
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at) "
                           "VALUES ('pp_x', 'blk_x', 'pi_m1b', 'chooser', ?)", (served,))
    with repository.atomic():
        record_plan_serve(later_vault, repository, presentation_id="pp_x", practice_item_id="pi_m1b", served_at=served)
    second = [r for r in rows(paths.sqlite_path, "SELECT * FROM item_serve_inputs") if r["plan_presentation_id"] == "pp_x"]
    audit = json.loads(second[0]["audit_json"])
    assert audit["complexity"]["value"] == "2" and json.loads(second[0]["resolved_features_json"])["complexity"] == 2


# -- G-AD1-9 ----------------------------------------------------------------------------------


def test_item_only_forecast_enters_inputs_only_if_received_before_serve(tmp_path):
    """An ``llm_v1:item`` receipt prepared with the pool appears in the first
    serve's ``z_i``; one received after the serve is scored but absent from
    that serve's inputs (fails before AD1: no item-scoped receipt)."""

    from learnloop.adaptive_difficulty.background import prepare_items
    from learnloop.adaptive_difficulty.outside import Clients, forecast_item

    paths = ad_plan_vault(tmp_path)
    env, clock = plan_env(paths)
    _build(env)
    vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
    # Prepared with the pool: the first planned item before its serve.
    prepare_items(vault, repository, ["pi_m1a"], clients=Clients(llm=ForecastLLM(p_correct=0.7)),
                  decider_factory=lambda: AuditDecider(), clock=FrozenClock(clock.now()))
    clock.advance(1)
    step = _serve(env)
    assert step["practice_item_id"] == "pi_m1a"
    first = rows(paths.sqlite_path, "SELECT * FROM item_serve_inputs WHERE practice_item_id = 'pi_m1a'")[0]
    z_v1 = json.loads(first["signals_json"])["z_v1"]
    item_receipt = [row for row in ad_receipts(paths.sqlite_path) if row["scope"] == "item"][0]
    assert z_v1["available"] is True and z_v1["receipt_id"] == item_receipt["id"]
    assert z_v1["value"] == pytest.approx(-__import__("math").log(0.7 / 0.3), abs=1e-6)
    assert (item_receipt["binding_kind"], item_receipt["decision_kind"], item_receipt["forecaster"]) == (
        "first_presentation", "item_prepare", "llm_v1:item")
    # The next item is served first, its forecast arrives after: scored, not an input.
    clock.advance(1)
    _record, second_step = advance(env, serve=True, skip_practice_item_id="pi_m1a")
    second_item = second_step["practice_item_id"]
    second = rows(paths.sqlite_path, "SELECT * FROM item_serve_inputs WHERE practice_item_id = ?", (second_item,))[0]
    clock.advance(1)
    late = forecast_item(load_vault(paths.root), repository, load_vault(paths.root).practice_items[second_item],
                         clients=Clients(llm=ForecastLLM(p_correct=0.2)), clock=FrozenClock(clock.now()))
    assert late.status == "ok"
    assert json.loads(second["signals_json"])["z_v1"]["available"] is False
    assert rows(paths.sqlite_path, "SELECT signals_json FROM item_serve_inputs WHERE practice_item_id = ?",
                (second_item,))[0]["signals_json"] == second["signals_json"]
    late_receipt = [row for row in ad_receipts(paths.sqlite_path)
                    if row["scope"] == "item" and row["practice_item_id"] == second_item][0]
    assert parse_utc(late_receipt["received_at"]) > parse_utc(second["served_at"])
    # An item forecast is made once per revision.
    assert forecast_item(load_vault(paths.root), repository, load_vault(paths.root).practice_items[second_item],
                         clients=Clients(llm=ForecastLLM())).status == "current"
