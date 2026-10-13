"""RW1a x main: the passage check's model call under the shared output-budget policy.

RW1a's passage check (the reconnect line's quick check) was built on the T6
follow-up's policy (``learnloop.ai.output_budget``) but only took its budget:
a metered call was held to the route's allowance, and a truncation failed the
check at once. The policy asks more of a caller that owns its spend
admission (one physical request per admitted attempt):

* the route's budget reaches every transport (a prompt hint on the
  subscription, where no output cap is sent), with the route's reasoning
  effort (``ai.route_reasoning_effort.canonical_ingest``);
* a truncation is never accepted: it is logged and retried once at double the
  budget through ``TruncationRetry``, held to the transport's ceiling; the
  retry is admitted (and its receipt tagged) like any retry, and a second
  truncation, or one already at the ceiling, fails the check.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from learnloop.ai.errors import AIOutputTruncated
from learnloop.ai.execution import single_request_active
from learnloop.reader import reader_quick_check as RQC
from tests.helpers import append_config_toml
from tests.test_reader_guidance import _setup as _guide_setup
from tests.test_reader_passage_check import RecordingClient, _author, _inquiry_rows, _receipts, _root, _spend


class TruncatingClient(RecordingClient):
    """Cuts the first ``cuts`` answers off at their output budget."""

    def __init__(self, *, cuts: int = 1, max_tokens: int | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.cuts = cuts
        self.single: list[bool] = []
        if max_tokens is not None:
            self.profile = SimpleNamespace(max_tokens=max_tokens)

    def complete(self, request):
        self.single.append(single_request_active())
        if len(self.requests) < self.cuts:
            self.requests.append(request)
            raise AIOutputTruncated("the answer stopped at its output budget")
        return super().complete(request)


def _roots(repo):
    return [receipt for receipt in _receipts(repo) if receipt["parent_call_id"] is None]


def test_a_truncated_metered_check_is_retried_once_at_double_its_budget(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    client = TruncatingClient(provider_type="openai_compatible")
    row = _author(repo, client, _root(vault, repo), spend=_spend(price_per_million=1.0))
    assert row["scope_kind"] == "inquiry" and len(_inquiry_rows(repo)) == 1
    assert [request.output_budget_tokens for request in client.requests] == [4_000, 8_000]
    # Each attempt is one admitted physical request.
    assert client.single == [True, True]
    first, retry = _roots(repo)
    assert first["status"] == "truncated"
    assert "truncation_retry" not in json.loads(first["budget_json"])
    assert json.loads(retry["budget_json"])["truncation_retry"] == {
        "role": "reading_quick_check", "model": "fake-model", "previous_budget": 4_000, "budget": 8_000,
    }


def test_a_second_truncation_fails_the_check_and_is_never_accepted(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    client = TruncatingClient(cuts=2, provider_type="openai_compatible")
    with pytest.raises(AIOutputTruncated):
        _author(repo, client, _root(vault, repo), spend=_spend(price_per_million=1.0))
    assert [request.output_budget_tokens for request in client.requests] == [4_000, 8_000]
    assert _inquiry_rows(repo) == []


def test_a_truncation_at_the_transports_ceiling_is_not_retried(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    client = TruncatingClient(provider_type="openai_compatible", max_tokens=4_000)
    with pytest.raises(AIOutputTruncated):
        _author(repo, client, _root(vault, repo), spend=_spend(price_per_million=1.0))
    assert [request.output_budget_tokens for request in client.requests] == [4_000]
    assert _inquiry_rows(repo) == []


def test_a_truncation_retry_over_the_per_check_cap_is_refused_before_it_is_sent(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    client = TruncatingClient(provider_type="openai_compatible")
    # The first attempt fits $0.05 at $4 per million (about 6,000 tokens); the
    # retry, at twice the output budget on top of it, does not.
    with pytest.raises(RQC.PassageCheckRefused) as refused:
        _author(repo, client, _root(vault, repo), spend=_spend(price_per_million=4.0, max_usd_per_check=0.05))
    assert refused.value.reason == "spend_refused" and refused.value.refusal == "over_cap"
    assert [request.output_budget_tokens for request in client.requests] == [4_000]


def test_the_subscription_check_carries_the_budget_as_a_hint_and_the_routes_effort(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    client = RecordingClient(provider_type="codex_sdk")
    _author(repo, client, _root(vault, repo), spend=_spend(reasoning_effort="low"))
    (request,) = client.requests
    assert request.output_budget_tokens == 4_000
    assert request.reasoning_effort == "low"


def test_a_truncated_subscription_check_is_retried_at_double_without_a_request_bound(tmp_path):
    vault, repo = _guide_setup(tmp_path)
    client = TruncatingClient(provider_type="codex_sdk")
    row = _author(repo, client, _root(vault, repo), spend=_spend())
    assert row["scope_kind"] == "inquiry"
    assert [request.output_budget_tokens for request in client.requests] == [4_000, 8_000]
    assert client.single == [False, False]


def test_the_vaults_route_effort_reaches_the_check(tmp_path):
    from learnloop.content.pipeline import jobs

    vault, repo = _guide_setup(tmp_path)
    append_config_toml(vault.root, """
    [ai.route_reasoning_effort]
    canonical_ingest = "low"
    """)
    spend = jobs._passage_check_spend(SimpleNamespace(vault_root=vault.root, cancelled=lambda: False))
    assert spend.reasoning_effort == "low"
    client = RecordingClient(provider_type="codex_sdk")
    _author(repo, client, _root(vault, repo), spend=spend)
    assert client.requests[0].reasoning_effort == "low"
    assert client.requests[0].output_budget_tokens == spend.output_tokens


def test_a_truncation_retry_counts_toward_the_day_like_any_call(tmp_path):
    # The day's count is of logical calls (root receipts, failed ones
    # included): with the last slot taken by the truncated attempt, the retry
    # is refused before it is sent, and the day is never overrun.
    vault, repo = _guide_setup(tmp_path)
    client = TruncatingClient(provider_type="openai_compatible")
    with pytest.raises(RQC.PassageCheckRefused) as refused:
        _author(repo, client, _root(vault, repo), spend=_spend(price_per_million=1.0, max_checks_per_day=1),
                clock=None)
    assert refused.value.reason == "capped"
    assert [request.output_budget_tokens for request in client.requests] == [4_000]
    assert len(_roots(repo)) == 1
