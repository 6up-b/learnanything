"""Adaptive hints H2b: outcome placement (spec_adaptive_hints_v1 §6.1, §7.2-7.3, D11).

After a hinted answer graded not fully correct on an item with a map, one
background call (route ``hint_outcome``) places the final answer on the map;
each shown hint gets a ``judgment_ledger`` verdict (``reached`` /
``not_reached`` / ``unknown``). Measurement only (no grade, diagnosis or
evidence change); gated so tests and vault copies make no call; joins the
maps' envelope; runs in H1's background registry with its claim, lease and
fence. Fakes only.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import closing
from typing import Any

import pytest

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.ai.execution import report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.db.repositories import Repository
from learnloop.hints import map_builder, outcome
from learnloop.hints.outcome import OutcomePlacementV1, hint_verdict, place_outcome, validate_placement
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.approach_map_fakes import good_map
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, hint_vault, judgments, prefer, receipts, store_map
from tests.structured_ai import StructuredClientFake, _request_context

PARTIAL = {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3}
FULL = {"criterionPoints": {"cdf": 2, "value": 2}, "confidence": 3}
REACHES_CDF = {"route_id": "r_ref", "reached_node_id": "cdf", "quote": "F(x) = x^2 on [0, 1]",
               "work_matches_a_route": True}


class OutcomeFake(StructuredClientFake):
    provider_name = "fake_outcome"
    provider_type = "codex_sdk"
    model = "fake-outcome-model"

    def __init__(self, answers: list[dict[str, Any]] | None = None, *, provider_type: str = "codex_sdk",
                 gate: threading.Event | None = None) -> None:
        self.answers = list(answers or [])
        self.provider_type = provider_type
        self.gate = gate
        self.contexts: list[dict[str, Any]] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def complete(self, request: Any) -> Any:
        self.contexts.append(json.loads(json.dumps(_request_context(request.prompt, request.purpose))))
        if self.gate is not None:
            assert self.gate.wait(30)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 40,
                           "resolved_model": self.model})
        answer = self.answers.pop(0) if self.answers else REACHES_CDF
        return request.result_model.model_validate(answer)

    @property
    def calls(self) -> int:
        return len(self.contexts)


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _sidecar(tmp_path, config: str = "", *, map_: bool = True):
    paths = hint_vault(tmp_path, config='[hints]\nchoice_policy = "argmax"\n' + config)
    if map_:
        store_map(paths)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = True
    ctx.hint_seed = "e"
    ctx.hint_writer_client = WriterFake()
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


def _hinted_attempt(ctx, session, *, grade=PARTIAL, key: str = "k1", option: str = "next_step@L3",
                    hint: bool = True) -> str:
    if hint:
        ctx.hint_chooser_client = ChooserFake(prefer(option, 0.9))
        job = _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": key,
                                                   "answerMd": WORK})
        assert job["result"]["status"] == "ready"
    return _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": 0, "selfGrade": grade, "submissionId": key})["attemptId"]


def _rows(paths, sql, params=()):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, params)]


def _evidence(paths) -> dict[str, list]:
    """Every table's rows (to show which tables a placement wrote)."""

    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        tables = [name for (name,) in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
        return {table: sorted(map(repr, connection.execute(f'SELECT * FROM "{table}"').fetchall()))
                for table in tables}


#: What a placement may write: its verdicts, its receipt and checkpoint, its
#: claim (and a metered call's spend reservation). Never evidence.
PLACEMENT_TABLES = {"judgment_ledger", "model_call_receipts", "model_work_checkpoints", "judgment_work_claims",
                    "source_service_spend"}


def test_a_hinted_wrong_answer_is_placed_and_each_hint_judged_measurement_only(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    attempt_id = _hinted_attempt(ctx, session)
    before = _evidence(paths)
    fake = OutcomeFake()
    result = place_outcome(load_vault(paths.root), Repository.attach(paths.sqlite_path), attempt_id, client=fake)
    assert result.status == "placed" and fake.calls == 1
    # The call sees the map and the submitted answer; never a grade or a hint.
    context = fake.contexts[0]
    assert context["learner_answer"] == WORK and "approach_map" in context
    assert "grade" not in json.dumps(context).lower() or "never grade" in json.dumps(context).lower()
    [verdict] = judgments(paths.sqlite_path, "hint_outcome")
    assert (verdict["judge"], verdict["left_kind"], verdict["right_kind"], verdict["right_id"]) == (
        "llm", "help_assist", "practice_attempt", attempt_id)
    # The next step aimed at the goal; the answer reaches the CDF only.
    assert verdict["verdict"] == "not_reached"
    rationale = json.loads(verdict["rationale"])
    assert rationale["placement"]["reached_node_id"] == "cdf" and rationale["measurement_only"] is True
    # Measurement only: the attempt, its reveals, mastery, diagnosis, every
    # evidence table and the assist rows are unchanged.
    after = _evidence(paths)
    changed = {table for table in after if after[table] != before.get(table)}
    assert changed <= PLACEMENT_TABLES, changed
    assert "judgment_ledger" in changed
    [receipt] = receipts(paths.sqlite_path, "hint_outcome")
    assert receipt["owner_id"] == attempt_id


def test_it_runs_in_the_background_after_submit_with_an_injected_client(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    fake = OutcomeFake()
    ctx.hint_outcome_client = fake
    attempt_id = _hinted_attempt(ctx, session)
    assert map_builder.wait_for_background_builds(30)
    assert fake.calls == 1
    assert [row["right_id"] for row in judgments(paths.sqlite_path, "hint_outcome")] == [attempt_id]


def test_no_call_in_tests_without_an_injected_client(tmp_path, monkeypatch):
    # tests/conftest.py sets both guards; with no client nothing starts.
    import os

    assert os.environ.get("LEARNLOOP_APPROACH_MAP_BUILDS") == "off"
    assert os.environ.get("LEARNLOOP_HINT_MODELS") == "off"
    started: list[Any] = []
    monkeypatch.setattr(map_builder.BackgroundBuilds, "launch",
                        lambda self, *args, **kwargs: started.append(args) or None)
    paths, ctx, session = _sidecar(tmp_path)
    _hinted_attempt(ctx, session)
    assert started == [] and judgments(paths.sqlite_path, "hint_outcome") == []
    assert receipts(paths.sqlite_path, "hint_outcome") == []


@pytest.mark.parametrize("case", ["fully_correct", "no_hint", "no_map", "switched_off", "adaptive_off", "maps_off"])
def test_nothing_is_placed_when_none_is_due(tmp_path, case):
    config = {"switched_off": "outcome_placement_enabled = false\n"}.get(case, "")
    paths, ctx, session = _sidecar(tmp_path, config, map_=case != "no_map")
    attempt_id = _hinted_attempt(ctx, session, grade=FULL if case == "fully_correct" else PARTIAL,
                                 hint=case != "no_hint")
    vault = load_vault(paths.root)
    if case == "adaptive_off":
        vault.config.hints.adaptive_enabled = False
    if case == "maps_off":
        vault.config.hints.maps.enabled = False
    fake = OutcomeFake()
    result = place_outcome(vault, Repository.attach(paths.sqlite_path), attempt_id, client=fake)
    expected = {"fully_correct": "not_due", "no_hint": "not_due", "no_map": "no_map", "switched_off": "disabled",
                "adaptive_off": "disabled", "maps_off": "disabled"}[case]
    assert result.status == expected and fake.calls == 0
    assert judgments(paths.sqlite_path, "hint_outcome") == []
    # Scheduling refuses before any thread for the switches and an unhinted attempt.
    if case in ("switched_off", "adaptive_off", "maps_off", "no_hint"):
        assert outcome.schedule_outcome_placement(vault, paths.sqlite_path, attempt_id, client=fake) is None


def test_an_attempt_is_placed_once(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    attempt_id = _hinted_attempt(ctx, session)
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    fake = OutcomeFake()
    assert place_outcome(vault, repository, attempt_id, client=fake).status == "placed"
    assert place_outcome(vault, repository, attempt_id, client=fake).status == "already_placed"
    assert fake.calls == 1


def test_an_unusable_placement_is_reasked_once_then_recorded_unknown(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    attempt_id = _hinted_attempt(ctx, session)
    bad = {"route_id": "r_ref", "reached_node_id": "cdf", "quote": "words the learner never wrote",
           "work_matches_a_route": True}
    fake = OutcomeFake([bad, bad])
    result = place_outcome(load_vault(paths.root), Repository.attach(paths.sqlite_path), attempt_id, client=fake)
    assert (result.status, result.rounds, fake.calls) == ("invalid", 2, 2)
    assert "quote_not_in_answer" in json.dumps(fake.contexts[1])
    [verdict] = judgments(paths.sqlite_path, "hint_outcome")
    assert verdict["verdict"] == "unknown"
    assert json.loads(verdict["rationale"])["reason"] == "placement_invalid"


def test_a_metered_route_needs_a_price_and_joins_the_maps_envelope(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    attempt_id = _hinted_attempt(ctx, session)
    vault, repository = load_vault(paths.root), Repository.attach(paths.sqlite_path)
    metered = OutcomeFake(provider_type="openrouter")
    assert place_outcome(vault, repository, attempt_id, client=metered).status == "unpriced"
    vault.config.hints.price_per_million = 1.0
    vault.config.hints.maps.max_daily_cost_usd = 0.0
    assert place_outcome(vault, repository, attempt_id, client=metered).status == "capped"
    assert metered.calls == 0
    # The envelope counts outcome placement's receipts beside the maps' own.
    assert map_builder.ENVELOPE_OWNER_KINDS == ("approach_map", "hint_outcome")
    vault.config.hints.maps.max_daily_cost_usd = 0.5
    assert place_outcome(vault, repository, attempt_id, client=metered).status == "placed"
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        spend = map_builder.maps_spend_today(vault, connection)
    assert spend["metered_usd"] > 0 and spend["envelope"] == "hints.maps.max_daily_cost_usd"


def test_a_closed_registry_starts_nothing_and_a_dead_fence_writes_nothing(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    attempt_id = _hinted_attempt(ctx, session)
    vault = load_vault(paths.root)
    registry = map_builder.BackgroundBuilds(drain_seconds=1.0)
    registry.bind(paths.sqlite_path)
    registry.close()
    fake = OutcomeFake()
    assert outcome.schedule_outcome_placement(vault, paths.sqlite_path, attempt_id, client=fake,
                                              builds=registry) is None
    # A placement whose vault was switched away while the model answered:
    # the late writes are fenced (no verdict, no receipt finish).
    live = map_builder.BackgroundBuilds(drain_seconds=1.0)
    live.bind(paths.sqlite_path)
    gate = threading.Event()
    slow = OutcomeFake(gate=gate)
    done: list[Any] = []
    thread = outcome.schedule_outcome_placement(vault, paths.sqlite_path, attempt_id, client=slow, builds=live,
                                                on_done=done.append)
    assert thread is not None
    for _ in range(300):
        if slow.contexts:
            break
        threading.Event().wait(0.01)
    live.close(timeout=0.1)
    gate.set()
    thread.join(30)
    assert done and done[0].status == "stale"
    assert judgments(paths.sqlite_path, "hint_outcome") == []


def test_the_verdict_in_code():
    payload = good_map()
    routes_reached = OutcomePlacementV1(**REACHES_CDF)
    assert hint_verdict({"target_node_id": "cdf"}, routes_reached, payload)[0] == "reached"
    assert hint_verdict({"target_node_id": "goal"}, routes_reached, payload)[0] == "not_reached"
    # A kind without a target: the next node from where it was placed.
    assert hint_verdict({"from_node_id": "g", "route_id": "r_ref"}, routes_reached, payload)[:2] == ("reached", None)
    assert hint_verdict({}, routes_reached, payload)[:2] == ("unknown", "no_target")
    off_route = OutcomePlacementV1(route_id="", reached_node_id="", quote="", work_matches_a_route=False)
    assert hint_verdict({"target_node_id": "cdf"}, off_route, payload)[:2] == ("unknown", "answer_on_no_route")
    assert hint_verdict({"target_node_id": "elsewhere"}, routes_reached, payload)[:2] == (
        "unknown", "target_on_another_route")
    assert validate_placement(OutcomePlacementV1(route_id="r_x", reached_node_id="zz", quote="",
                                                 work_matches_a_route=True), payload, WORK) == [
        "unknown_route", "unknown_node", "no_quote"]
