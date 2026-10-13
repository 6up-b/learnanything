"""Spend admission uses no provider, owner settings, or tracked working vault."""
from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from learnloop.ai.execution import model_call, observe_model_calls, record_model_calls
from learnloop.ai.spend import (
    SpendBudget, SpendCancelled, SpendCaps, SpendEstimate, SpendLimitExceeded,
)
from learnloop.db.repositories import Repository
from tests.helpers import create_basic_vault


@pytest.mark.parametrize("dimension", [
    "candidates", "pairs", "retries", "calls", "total_tokens", "estimated_usd",
])
def test_each_cap_exact_boundary_then_rejects_before_call(dimension):
    budget = SpendBudget(replace(SpendCaps(), **{f"max_{dimension}": 1}))
    estimate = replace(SpendEstimate(calls=1, estimated_usd=0), **{dimension: 1})
    calls = []
    with budget.request(estimate):
        calls.append("paid")
    assert getattr(budget.used, dimension) == 1
    with pytest.raises(SpendLimitExceeded, match=dimension):
        with budget.request(estimate):
            calls.append("must not run")
    assert calls == ["paid"]


def test_failed_attempt_and_retry_charge_calls_tokens_cost_without_duplicate_candidates():
    budget = SpendBudget(SpendCaps(max_retries=1))
    estimate = SpendEstimate(candidates=2, pairs=1, calls=1, total_tokens=10, estimated_usd=.1)
    with pytest.raises(RuntimeError):
        with budget.request(estimate):
            raise RuntimeError("provider failed after accepting request")
    retry = replace(estimate, candidates=0, pairs=0, retries=1)
    with budget.request(retry):
        pass
    assert budget.used == SpendEstimate(candidates=2, pairs=1, calls=2, retries=1, total_tokens=20, estimated_usd=.2)
    with pytest.raises(SpendLimitExceeded, match="retries"):
        with budget.request(retry):
            pytest.fail("retry was admitted")


def test_unknown_price_rejects_even_large_finite_cap_explicit_price_estimate_admits():
    budget = SpendBudget(SpendCaps(max_estimated_usd=1_000_000))
    unknown = SpendEstimate(calls=1, estimated_usd=None)
    with pytest.raises(SpendLimitExceeded, match="Unknown price"):
        budget.check(unknown)
    with pytest.raises(SpendLimitExceeded):
        with budget.request(unknown):
            pytest.fail("unknown price admitted")
    assert budget.used.calls == 0
    with budget.request(replace(unknown, estimated_usd=.25)):
        pass
    assert budget.used.estimated_usd == .25


def test_dry_run_is_nonmutating_and_does_not_emit_model_receipts():
    budget = SpendBudget(SpendCaps())
    plan = SpendEstimate(candidates=10, calls=2, total_tokens=100, estimated_usd=.1)
    events = []
    with observe_model_calls(lambda action, event: events.append((action, event))):
        assert budget.check(plan) == plan
        assert budget.check(plan) == plan
    assert budget.used == SpendEstimate(estimated_usd=0)
    assert events == []


def test_omitted_price_is_unknown_not_free():
    with pytest.raises(SpendLimitExceeded, match="Unknown price"):
        with SpendBudget(SpendCaps()).request(SpendEstimate(calls=1)):
            pytest.fail("missing estimate must fail closed")


def test_failed_attempt_actual_cost_overrun_stops_next_request():
    budget = SpendBudget(SpendCaps(max_estimated_usd=.2))
    with pytest.raises(RuntimeError):
        with budget.request(SpendEstimate(calls=1, estimated_usd=.1)) as charge:
            charge.reconcile(estimated_usd=.3)
            raise RuntimeError("provider billed failed attempt")
    assert budget.used.estimated_usd == .3
    with pytest.raises(SpendLimitExceeded, match="estimated_usd"):
        with budget.request(SpendEstimate(calls=1, retries=1, estimated_usd=0)):
            pytest.fail("failed attempt must remain charged")


@pytest.mark.parametrize("bad", [-1, float("nan"), float("inf"), float("-inf"), True, "1", None])
@pytest.mark.parametrize("dimension", [
    "candidates", "pairs", "retries", "calls", "total_tokens", "estimated_usd",
])
def test_caps_and_estimates_reject_invalid_numbers(dimension, bad):
    if dimension == "estimated_usd" and bad is None:
        # None is a budget with no money cap (an unset per-operation cap of the
        # source service, owner 2026-10-13; shared envelopes still bound it)
        # and an unknown estimate: both accepted.
        assert SpendCaps(max_estimated_usd=None).max_estimated_usd is None
        assert SpendEstimate(estimated_usd=None).estimated_usd is None
        return
    with pytest.raises(ValueError):
        SpendCaps(**{f"max_{dimension}": bad})
    with pytest.raises(ValueError):
        SpendEstimate(**{dimension: bad})


def test_a_budget_without_a_money_cap_never_refuses_dollars_but_keeps_its_counts():
    budget = SpendBudget(SpendCaps(max_calls=2, max_estimated_usd=None))
    for _ in range(2):
        with budget.request(SpendEstimate(calls=1, estimated_usd=1_000.0)):
            pass
    assert budget.used.estimated_usd == 2_000.0
    with pytest.raises(SpendLimitExceeded, match="calls"):
        budget.check(SpendEstimate(calls=1, estimated_usd=0.0))
    with pytest.raises(SpendLimitExceeded, match="Unknown price"):
        SpendBudget(SpendCaps(max_estimated_usd=None)).check(SpendEstimate(calls=1, estimated_usd=None))


def test_counts_reject_fractional_values():
    with pytest.raises(ValueError):
        SpendCaps(max_calls=1.5)
    with pytest.raises(ValueError):
        SpendEstimate(total_tokens=1.5)


def test_zero_caps_and_zero_price_allow_no_paid_calls():
    caps = SpendCaps(0, 0, 0, 0, 0, 0)
    budget = SpendBudget(caps)
    budget.check(SpendEstimate(estimated_usd=0))
    with pytest.raises(SpendLimitExceeded, match="calls"):
        with budget.request(SpendEstimate(calls=1, estimated_usd=0)):
            pytest.fail("call admitted")


def test_decimal_dollar_boundary_does_not_fail_from_binary_float_addition():
    budget = SpendBudget(SpendCaps(max_estimated_usd=.3))
    for cost in (.1, .2):
        with budget.request(SpendEstimate(calls=1, estimated_usd=cost)):
            pass
    assert budget.used.estimated_usd == .3
    with pytest.raises(SpendLimitExceeded):
        budget.check(SpendEstimate(estimated_usd=.00001))


def test_actual_usage_reconciles_upward_only_idempotently_and_preserves_paid_result():
    budget = SpendBudget(SpendCaps(max_total_tokens=20, max_estimated_usd=.2))
    with budget.request(SpendEstimate(calls=1, total_tokens=10, estimated_usd=.1)) as charge:
        charge.reconcile(total_tokens=5, estimated_usd=.05)
        assert budget.used.total_tokens == 10
        assert budget.used.estimated_usd == .1
        charge.reconcile(total_tokens=30, estimated_usd=.3)
        charge.reconcile(total_tokens=30, estimated_usd=.3)
        charge.reconcile()
        paid_result = "kept"
    assert paid_result == "kept"
    assert budget.used.total_tokens == 30
    assert budget.used.estimated_usd == .3
    with pytest.raises(SpendLimitExceeded):
        with budget.request(SpendEstimate(calls=1, estimated_usd=0)):
            pytest.fail("overrun must stop next request")


@pytest.mark.parametrize("usage", [
    {"total_tokens": -1}, {"total_tokens": float("nan")},
    {"estimated_usd": -1}, {"estimated_usd": float("inf")},
    {"estimated_usd": float("nan")}, {"total_tokens": True},
])
def test_invalid_actual_usage_cannot_reduce_reservation(usage):
    budget = SpendBudget(SpendCaps())
    with budget.request(SpendEstimate(calls=1, total_tokens=10, estimated_usd=.1)) as charge:
        before = budget.used
        with pytest.raises(ValueError):
            charge.reconcile(**usage)
        assert budget.used == before


def test_cancellation_stops_next_attempt_without_charge():
    cancelled = False
    budget = SpendBudget(SpendCaps(), cancelled=lambda: cancelled)
    with budget.request(SpendEstimate(calls=1, estimated_usd=0)):
        cancelled = True
    with pytest.raises(SpendCancelled):
        with budget.request(SpendEstimate(calls=1, retries=1, estimated_usd=0)):
            pytest.fail("cancelled request admitted")
    assert budget.used.calls == 1
    assert budget.used.retries == 0


@pytest.mark.parametrize("estimate", [
    SpendEstimate(), SpendEstimate(calls=2), SpendEstimate(calls=1, retries=2),
])
def test_request_requires_one_physical_attempt(estimate):
    with pytest.raises(ValueError, match="calls=1"):
        with SpendBudget(SpendCaps()).request(estimate):
            pytest.fail("invalid attempt")


def test_declared_caps_persist_on_real_receipt_for_success_and_failure(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    caps = SpendCaps(max_calls=2, max_retries=1)
    budget = SpendBudget(caps)
    client = SimpleNamespace(provider_name="fake", model="no-network")
    with record_model_calls(repository, owner_kind="cli_command", owner_id="spend-test"):
        with budget.request(SpendEstimate(calls=1, estimated_usd=0)):
            with model_call(client, purpose="embedding", prompt=["fake"]):
                pass
        with pytest.raises(RuntimeError):
            with budget.request(SpendEstimate(calls=1, retries=1, estimated_usd=0)):
                with model_call(client, purpose="embedding", prompt=["fake"]):
                    raise RuntimeError("paid failure")
        with model_call(client, purpose="after-spend-context"):
            pass
    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT purpose,status,budget_json FROM model_call_receipts ORDER BY started_at"
        ).fetchall()
    assert [(row[0], row[1]) for row in rows] == [
        ("embedding", "completed"), ("embedding", "failed"), ("after-spend-context", "completed"),
    ]
    assert [json.loads(row[2]) for row in rows[:2]] == [caps.as_dict(), caps.as_dict()]
    assert rows[2][2] is None


def test_subscription_budget_estimates_only_and_keeps_count_caps():
    """Slice A §5 rule 6: Codex runs on the subscription without token/USD caps."""
    from learnloop.ai.spend import is_subscription_transport

    caps = SpendCaps(max_candidates=1, max_pairs=1, max_calls=2, max_retries=0,
                     max_total_tokens=1, max_estimated_usd=0)
    budget = SpendBudget(caps, subscription=True)
    unknown = SpendEstimate(candidates=1, pairs=1, calls=1, total_tokens=10_000)
    assert budget.check(unknown) is unknown  # unknown price is not refused
    with budget.request(unknown) as charge:
        charge.reconcile(total_tokens=12_000)
    assert budget.used.total_tokens == 12_000 and budget.used.estimated_usd is None
    declared = budget.declared()
    assert declared["cost_basis"] == "estimated_only" and declared["billing"] == "subscription"
    assert declared["physical_request_bound"] is False
    with pytest.raises(SpendLimitExceeded, match="candidates"):
        budget.check(SpendEstimate(candidates=1, calls=1))
    with pytest.raises(SpendLimitExceeded, match="retries"):
        budget.check(SpendEstimate(calls=1, retries=1))
    with budget.request(SpendEstimate(calls=1)):
        pass
    with pytest.raises(SpendLimitExceeded, match="calls"):
        budget.check(SpendEstimate(calls=1))
    assert is_subscription_transport(client=SimpleNamespace(provider_type="codex_sdk"))
    assert not is_subscription_transport(client=SimpleNamespace(provider_type="openrouter"))
    assert is_subscription_transport(profile=SimpleNamespace(type="codex_sdk"))
    for metered in ("openai_chat", "openrouter", "openai_embedding"):
        assert not is_subscription_transport(profile=SimpleNamespace(type=metered))
    # A metered budget is unchanged: same declared caps, unknown price refused.
    assert SpendBudget(caps).declared() == caps.as_dict()
    with pytest.raises(SpendLimitExceeded, match="Unknown price"):
        SpendBudget(caps).check(SpendEstimate(calls=1))
