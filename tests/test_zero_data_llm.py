"""T8 zero-data LLM arm: past-only requests, spend caps, ledger, cache-only replay."""
from dataclasses import replace
import hashlib
import json
import sqlite3

import pytest

from learnloop.ai.spend import SpendCaps, SpendEstimate
from learnloop.db.repositories import Repository
from learnloop.field import zero_data_llm as zero
from learnloop.field.evaluation import evaluate
from learnloop.field.success_head import AttemptContent, ContentIndex
from learnloop.field.types import AttemptRow, ItemFeatures
from tests.helpers import create_basic_vault


def _rows(n=6):
    rows, entries = [], {}
    for k in range(n):
        at = f"2026-02-01T{k // 60:02}:{k % 60:02}:00Z"
        item = f"item-private-{k % 3}"
        rows.append(AttemptRow(f"attempt-{k}", ItemFeatures(item, "lo-a", at), float(k % 2), 1.0))
        entries[(item, at)] = AttemptContent(stem=f"Stem {k % 3}: compute the rank.",
                                             stem_source="exact_snapshot", kcs=("Rank", "Bases"))
    return rows, ContentIndex(entries)


@pytest.fixture
def case(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    rows, content = _rows()
    kwargs = dict(
        repository=Repository(paths.sqlite_path), cache_dir=tmp_path / "cache",
        vault_path=paths.root, model="fake-llm", caps=SpendCaps(),
        estimate_per_prediction=SpendEstimate(calls=1, total_tokens=500, estimated_usd=.001),
    )
    return paths, rows, content, kwargs


def _ledger(paths):
    with sqlite3.connect(paths.sqlite_path) as connection:
        return connection.execute(
            "SELECT task, judge, judge_model, prompt_version, score FROM judgment_ledger WHERE task=?",
            (zero.TASK,),
        ).fetchall()


def test_requests_are_past_only_and_carry_no_answers_or_current_outcome():
    rows, content = _rows(30)
    requests = list(zero.prediction_requests(rows, content).values())
    assert len(requests) == 30
    assert requests[0]["history"] == []
    last = requests[-1]
    assert len(last["history"]) == zero.HISTORY_WINDOW
    assert {entry["result"] for entry in last["history"]} == {"correct", "incorrect"}
    assert last["item"]["kcs"] == ["Rank", "Bases"]
    text = json.dumps(requests)
    assert "item-private" not in text and "attempt-" not in text  # opaque references only
    assert "outcome" not in text and "answer" not in text
    # The request for attempt k depends only on attempts before k.
    flipped = [replace(r, outcome=1 - r.outcome) if i >= 10 else r for i, r in enumerate(rows)]
    assert list(zero.prediction_requests(flipped, content))[:11] == list(
        zero.prediction_requests(rows, content))[:11]


def test_stem_is_capped_and_missing_text_abstains():
    rows, content = _rows(2)
    long = ContentIndex({**content._entries, (rows[0].features.item_id, rows[0].features.observed_at):
                         AttemptContent(stem="x" * 9000, stem_source="current_content")})
    request = zero.build_request(rows[0].features, long, [])
    assert len(request["item"]["stem"]) == zero.STEM_CHAR_CAP
    unknown = ContentIndex({})
    assert zero.build_request(rows[0].features, unknown, []) is None
    arm = zero.ZeroDataProbabilityArm({}, content=unknown, model="m")
    assert not arm.covers(rows[0].features)


def test_prepare_ledgers_caches_outside_vault_and_replay_makes_zero_calls(case, monkeypatch):
    paths, rows, content, kwargs = case
    calls = []

    def predict(request):
        calls.append(request)
        return {"p_success": .7}

    arms, report = zero.prepare_zero_data_probabilities(rows, content, predict=predict, **kwargs)
    assert report["status"] == "complete" and report["charged"]["calls"] == len(rows)
    assert len(calls) == len(rows) and arms is not None
    assert [row[:4] for row in _ledger(paths)] == [(zero.TASK, "llm", "fake-llm", zero.PROMPT_VERSION)] * len(rows)
    with sqlite3.connect(paths.sqlite_path) as connection:
        receipts = connection.execute(
            "SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind=?", (zero.TASK,)).fetchone()[0]
    assert receipts >= len(rows)
    assert "item-private" not in json.dumps(report)
    # Replay from cache: no client, no repository, no calls.
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    loaded, count = zero.load_zero_data_arms(rows, content, cache_dir=kwargs["cache_dir"],
                                             vault_path=paths.root, model="fake-llm")
    assert count == len(rows)
    result = evaluate(rows, arms=[*loaded, "mastery_ekf"], bootstrap_samples=10)
    raw = result["report1"]["arms"]["llm_zero_data"]["overall"]
    assert raw["n"] == len(rows)
    assert result["manifest"]["arm_models"]["llm_zero_data"] == "fake-llm"
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before
    # A second preparation finds everything cached and calls nothing.
    calls.clear()
    _, again = zero.prepare_zero_data_probabilities(rows, content, predict=predict, **kwargs)
    assert again["cached"] == len(rows) and not calls


def test_cache_inside_vault_is_refused(case):
    paths, rows, content, kwargs = case
    kwargs["cache_dir"] = paths.root / "cache"
    with pytest.raises(ValueError, match="outside the vault"):
        zero.prepare_zero_data_probabilities(rows, content, predict=lambda r: {}, **kwargs)
    with pytest.raises(ValueError, match="outside the vault"):
        zero.load_zero_data_arms(rows, content, cache_dir=paths.root / "c", vault_path=paths.root, model="m")


def test_dry_run_is_read_only_and_never_calls(case):
    paths, rows, content, kwargs = case
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    arms, report = zero.prepare_zero_data_probabilities(
        rows, content, predict=lambda r: pytest.fail("called"), dry_run=True, **kwargs)
    assert arms is None and report["status"] == "dry_run"
    assert report["estimate"]["calls"] == len(rows) and report["charged"]["calls"] == 0
    assert not kwargs["cache_dir"].exists()
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before


@pytest.mark.parametrize("cap", ["max_candidates", "max_calls", "max_total_tokens", "max_estimated_usd"])
def test_every_cap_blocks_before_the_first_call(case, cap):
    paths, rows, content, kwargs = case
    kwargs["caps"] = replace(kwargs["caps"], **{cap: 0})
    arms, report = zero.prepare_zero_data_probabilities(
        rows, content, predict=lambda r: pytest.fail("called"), **kwargs)
    assert arms is None and report["status"] == "over_budget"
    assert report["charged"]["calls"] == 0 and not _ledger(paths)


def test_invalid_probability_is_ledgered_but_never_cached(case):
    paths, rows, content, kwargs = case
    arms, report = zero.prepare_zero_data_probabilities(
        rows, content, predict=lambda r: {"p_success": 1.0}, **kwargs)
    assert arms is None and report["status"] == "incomplete" and report["invalid"] == len(rows)
    assert all(score is None for *_, score in _ledger(paths))
    with pytest.raises(ValueError, match="incomplete"):
        zero.load_zero_data_arms(rows, content, cache_dir=kwargs["cache_dir"], vault_path=paths.root,
                                 model="fake-llm")


def test_metered_route_refuses_hidden_retries(case):
    from learnloop.ai.execution import model_call

    paths, rows, content, kwargs = case
    sent = []

    def predict(request):
        client = type("C", (), {"provider_name": "o", "provider_type": "openai_chat", "model": "m"})()
        for index in range(2):
            with model_call(client, purpose="chat_request"):
                sent.append(index)
        return {"p_success": .6}

    arms, report = zero.prepare_zero_data_probabilities(rows, content, predict=predict, **kwargs)
    assert arms is None and report["status"] == "over_budget" and sent == [0]
    assert report["physical_request_bound"] is True and report["billing"] == "metered"


@pytest.mark.parametrize("price", [None, .001])
@pytest.mark.parametrize("enclosing_total", [False, True])
def test_codex_subscription_runs_unbounded_with_estimated_cost(case, price, enclosing_total):
    from learnloop.ai.execution import model_call, report_call_usage

    paths, rows, content, kwargs = case
    turns = []

    def predict(request):
        client = type("C", (), {"provider_name": "codex", "provider_type": "codex_sdk", "model": "m"})()
        with model_call(client, purpose=zero.TASK):  # the structured operation's receipt
            for _ in range(2):  # an initial turn and a JSON repair
                with model_call(client, purpose=f"{zero.TASK}:sdk_turn"):
                    turns.append(1)
                    report_call_usage({"input_tokens": 10_000, "output_tokens": 100})
            if enclosing_total:  # a transport that also totals its turns
                report_call_usage({"input_tokens": 20_000, "output_tokens": 200})
        return {"p_success": .4}

    kwargs.update(caps=SpendCaps(max_total_tokens=1, max_estimated_usd=0),
                  estimate_per_prediction=SpendEstimate(calls=1, total_tokens=500, estimated_usd=price))
    arms, report = zero.prepare_zero_data_probabilities(rows, content, predict=predict,
                                                        subscription=True, **kwargs)
    assert report["status"] == "complete" and arms is not None
    assert len(turns) == 2 * len(rows)
    assert report["cost_basis"] == "estimated_only" and report["physical_request_bound"] is False
    # Both physical turns count once each; an enclosing total is not added (review F5).
    assert report["charged"]["total_tokens"] == 20_200 * len(rows)
    if price is None:
        assert report["charged"]["estimated_usd"] is None
    else:
        assert report["charged"]["estimated_usd"] == pytest.approx(20_200 * price / 500 * len(rows))
    with sqlite3.connect(paths.sqlite_path) as connection:
        usage = [json.loads(u) for (u,) in connection.execute(
            "SELECT usage_json FROM model_call_receipts WHERE owner_kind=? AND purpose LIKE '%sdk_turn'",
            (zero.TASK,))]
    assert usage and {u["cost_basis"] for u in usage} == {"estimated_only"}


def _replay(arm, rows):
    arm.rebuild(())
    predictions = []
    for row in rows:
        predictions.append(arm.predict(row.features))
        arm.observe(row)
    return predictions


def _count_calls(predict):
    calls = []

    def counted(request):
        calls.append(request)
        return predict(request)

    return counted, calls


def test_resume_recovers_committed_verdicts_when_the_cache_was_never_published(case, monkeypatch):
    import os

    paths, rows, content, kwargs = case
    predict, calls = _count_calls(lambda request: {"p_success": .7})
    real_replace, failures = os.replace, []

    def replace_once(source, target, *args, **kw):
        if str(source).endswith(".tmp") and not failures:
            failures.append(target)
            raise OSError("disk full")
        return real_replace(source, target, *args, **kw)

    # The first verdict commits to the ledger, then publishing its checkpoint fails.
    monkeypatch.setattr(os, "replace", replace_once)
    with pytest.raises(OSError, match="disk full"):
        zero.prepare_zero_data_probabilities(rows, content, predict=predict, **kwargs)
    monkeypatch.setattr(os, "replace", real_replace)
    assert len(calls) == 1 and len(_ledger(paths)) == 1
    assert not [path for path in kwargs["cache_dir"].iterdir() if path.suffix in {".json", ".tmp"}]
    # Resume buys only what was never committed.
    arms, report = zero.prepare_zero_data_probabilities(rows, content, predict=predict, **kwargs)
    assert report["status"] == "complete" and arms is not None and report["recovered"] == 1
    assert len(calls) == len(rows) and len(_ledger(paths)) == len(rows)
    assert report["charged"]["calls"] == len(rows) - 1


def test_a_lost_cache_is_rebuilt_from_the_ledger_without_paying_again(case):
    paths, rows, content, kwargs = case
    predict, calls = _count_calls(lambda request: {"p_success": .7})
    arms, _ = zero.prepare_zero_data_probabilities(rows, content, predict=predict, **kwargs)
    first = _replay(arms[0], rows)
    calls.clear()
    kwargs["cache_dir"] = kwargs["cache_dir"].parent / "fresh-cache"
    dry = zero.prepare_zero_data_probabilities(rows, content, predict=predict, dry_run=True, **kwargs)[1]
    assert dry["recovered"] == len(rows) and dry["estimate"]["calls"] == 0
    assert not kwargs["cache_dir"].exists()
    arms, report = zero.prepare_zero_data_probabilities(rows, content, predict=predict, **kwargs)
    assert not calls and report["recovered"] == len(rows) and report["charged"]["calls"] == 0
    assert len(_ledger(paths)) == len(rows)
    loaded, _ = zero.load_zero_data_arms(rows, content, cache_dir=kwargs["cache_dir"],
                                         vault_path=paths.root, model="fake-llm")
    assert _replay(loaded[0], rows) == first


def test_ledger_verdicts_under_other_settings_are_not_recovered(case):
    paths, rows, content, kwargs = case
    predict, calls = _count_calls(lambda request: {"p_success": .7})
    zero.prepare_zero_data_probabilities(rows, content, predict=predict, **kwargs)
    calls.clear()
    kwargs["cache_dir"] = kwargs["cache_dir"].parent / "other-settings"
    _, report = zero.prepare_zero_data_probabilities(
        rows, content, predict=predict, settings={"reasoning_effort": "high"}, **kwargs)
    assert report["recovered"] == 0 and len(calls) == len(rows)


def test_concurrent_preparations_on_one_cache_never_both_pay(case):
    paths, rows, content, kwargs = case
    rows = rows[:1]
    calls, nested = [], {}

    def second(request):
        calls.append("second")
        return {"p_success": .7}

    def first(request):
        calls.append("first")
        # Another process starts on the same cache while this call is in flight.
        try:
            nested["result"] = zero.prepare_zero_data_probabilities(
                rows, content, predict=second, **{**kwargs, "repository": Repository(paths.sqlite_path)})
        except ValueError as exc:
            nested["error"] = str(exc)
        return {"p_success": .3}

    arms, report = zero.prepare_zero_data_probabilities(rows, content, predict=first, **kwargs)
    assert calls == ["first"] and "another" in nested["error"].lower()
    assert len(_ledger(paths)) == 1
    loaded, _ = zero.load_zero_data_arms(rows, content, cache_dir=kwargs["cache_dir"],
                                         vault_path=paths.root, model="fake-llm")
    assert loaded[0].predict(rows[0].features) == arms[0].predict(rows[0].features) == .3
    assert not [path for path in kwargs["cache_dir"].iterdir() if path.suffix == ".tmp"]
    # Once the first preparation finishes, the second finds everything done.
    _, again = zero.prepare_zero_data_probabilities(rows, content, predict=second, **kwargs)
    assert again["cached"] == 1 and calls == ["first"]


def test_recalibration_is_fit_on_past_predictions_only():
    rows, content = _rows(12)
    rows = [replace(r, outcome=1.0) for r in rows]
    probabilities = {digest: .5 for digest in zero.prediction_requests(rows, content)}
    raw = zero.ZeroDataProbabilityArm(probabilities, content=content, model="m")
    recalibrated = zero.ZeroDataProbabilityArm(probabilities, content=content, model="m", recalibrated=True)
    seen = []
    for row in rows:
        seen.append((raw.predict(row.features), recalibrated.predict(row.features)))
        raw.observe(row)
        recalibrated.observe(row)
    assert seen[0] == (.5, .5)  # nothing past: the raw sensor
    assert all(r == .5 for r, _ in seen)
    calibrated = [c for _, c in seen]
    assert calibrated == sorted(calibrated) and calibrated[-1] > .5
    assert recalibrated.intercept == pytest.approx(zero._intercept_map([(0.0, 1.0)] * 12))
    assert recalibrated.calibrated_uncertainty is False and recalibrated.name == "llm_zero_data:recalibrated"


def test_replay_fails_closed_on_a_missing_checkpoint():
    rows, content = _rows(3)
    probabilities = dict(list({d: .5 for d in zero.prediction_requests(rows, content)}.items())[:2])
    arm = zero.ZeroDataProbabilityArm(probabilities, content=content, model="m")
    with pytest.raises(ValueError, match="incomplete"):
        evaluate(rows, arms=[arm], bootstrap_samples=5)
