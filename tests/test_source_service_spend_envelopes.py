"""F2 (Codex sources-build review): the service's money caps are enforced
before each physical request, shared across operations and threads; dry runs
report numbers; subscription requests are estimated from tokens, never capped."""
from __future__ import annotations

from decimal import Decimal
import json
import threading

import pytest

from learnloop.ai.spend import (
    SpendBudget,
    SpendCaps,
    SpendEnvelope,
    SpendEstimate,
    SpendLimitExceeded,
    spend_envelopes,
)
from learnloop.content.authoring import source_exercise_import as SEI
from learnloop.db.connection import connect
from learnloop.db.stores.source_service import spend_since
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, loaded, service_clients, set_config

PRICE = 10.0  # dollars per million tokens: large enough that one import passes a cent


class MeteredServiceLLM(FakeServiceLLM):
    """The service fake on a metered (OpenRouter-like) transport."""

    provider_name = "metered_fake"
    provider_type = "openrouter"
    model = "metered-fake-model"


def _metered_vault(tmp_path, **service):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    set_config(paths, "source_service", llm_price_per_million=PRICE, **service)
    set_config(paths, "practice_index", rerank_price_per_million=PRICE, rerank_max_cost_usd=1.0)
    return paths, repository, spans


def _reserved_usd(repository, owner_kinds=None) -> float:
    """Metered dollars the receipts show (reported cost, else tokens at the price)."""
    with connect(repository.sqlite_path, read_only=True) as connection:
        return spend_since(connection, "2000-01-01", owner_kinds=owner_kinds, price_per_million=PRICE)["usd"]


def _import(paths, repository, span, llm):
    return SEI.import_source_exercise(paths.root, repository, extraction_id="ext_text", span_ids=[span],
                                      caller="learner", clients=service_clients(llm))


def test_one_import_is_bounded_by_its_cap_across_all_its_operations(tmp_path):
    """Before: the solution match, authoring, the ladder and the family judge
    each got a fresh budget (authoring none at all), so one import could spend
    several caps. At $10 per million the solution match reserves about $0.04,
    authoring $0.24 and the span-support check $0.04: each fits a $0.30 cap
    alone, the three together do not."""

    paths, repository, spans = _metered_vault(tmp_path, import_max_cost_usd=0.30, max_daily_cost_usd=10.0)
    llm = MeteredServiceLLM()
    result = _import(paths, repository, spans["exercises"][1], llm)
    assert [name for _purpose, name in llm.calls] == ["SolutionMatch", "ExerciseAuthoring"]
    assert result["status"] == "written" and result["key_status"] == "model_answer"
    assert _reserved_usd(repository) <= 0.30
    # The same import under a wide cap makes the third request.
    paths2, repository2, spans2 = _metered_vault(tmp_path / "wide", import_max_cost_usd=5.0, max_daily_cost_usd=10.0)
    wide = MeteredServiceLLM()
    assert _import(paths2, repository2, spans2["exercises"][1], wide)["key_status"] == "book_solution"
    assert len(wide.calls) == 3


def test_the_daily_cap_refuses_a_request_before_it_is_sent(tmp_path):
    paths, repository, spans = _metered_vault(tmp_path, max_daily_cost_usd=0.25, import_max_cost_usd=5.0)
    llm = MeteredServiceLLM()
    assert _import(paths, repository, spans["exercises"][1], llm)["status"] == "written"
    first = len(llm.calls)
    # Today's receipts plus the next authoring request's reservation pass the
    # cap: it is refused before it is sent, and the import says so.
    second = _import(paths, repository, spans["exercises"][2], llm)
    assert second["status"] == "failed" and "max_daily_cost_usd" in second["reason"], second
    assert [name for _purpose, name in llm.calls[first:]] == ["SolutionMatch"]
    assert _reserved_usd(repository) <= 0.25


def test_a_harvest_never_passes_its_max_cost(tmp_path):
    from learnloop.instructional.harvest import harvest

    paths, repository, _spans = _metered_vault(tmp_path, import_max_cost_usd=5.0, max_daily_cost_usd=5.0)
    llm = MeteredServiceLLM()
    cap = 0.5
    report = harvest(loaded(paths), repository, dry_run=False, max_cost_usd=cap, facet_ids=("facet_eigen",),
                     clients=service_clients(llm), rerank_client=llm)
    assert report["status"] == "over_budget", report
    assert report["budget"]["metered_usd"] <= cap and report["budget"]["refused_requests"] >= 1
    assert report["spend"]["usd"] <= cap
    # Without the cap the same harvest goes on: the envelope stopped real work.
    wide_paths, wide_repository, _ = _metered_vault(tmp_path / "wide", import_max_cost_usd=5.0, max_daily_cost_usd=5.0)
    wide = MeteredServiceLLM()
    harvest(loaded(wide_paths), wide_repository, dry_run=False, max_cost_usd=50.0, facet_ids=("facet_eigen",),
            clients=service_clients(wide), rerank_client=wide)
    assert len(wide.calls) > len(llm.calls)


def test_a_dry_run_reports_numerical_estimates(tmp_path):
    from learnloop.instructional.harvest import harvest, verify

    paths, repository, _spans = _metered_vault(tmp_path)
    report = harvest(loaded(paths), repository, dry_run=True, max_cost_usd=None, facet_ids=("facet_eigen",))
    estimate = report["estimate"]
    assert estimate["calls"] > 0 and estimate["tokens"] > 0 and estimate["usd"] > 0
    target = report["targets"][0]["estimate"]
    assert target["imports"]["by_role"] and target["rerank"]["calls"] == 1
    checks = verify(loaded(paths), repository, dry_run=True, max_cost_usd=None)
    assert checks["estimate"]["calls"] >= 0 and "usd" in checks["estimate"]


def test_an_envelope_is_shared_by_concurrent_workers():
    envelope = SpendEnvelope("batch", 1.0)
    admitted: list[int] = []
    refused: list[int] = []

    def worker(index: int) -> None:
        budget = SpendBudget(SpendCaps(max_calls=100, max_estimated_usd=100.0))
        with spend_envelopes(envelope):
            for _ in range(10):
                try:
                    with budget.request(SpendEstimate(calls=1, total_tokens=10, estimated_usd=0.1)):
                        admitted.append(index)
                except SpendLimitExceeded:
                    refused.append(index)

    threads = [threading.Thread(target=worker, args=(index,)) for index in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(admitted) == 10 and len(refused) == 30
    assert envelope.report()["metered_usd"] == pytest.approx(1.0)


def test_subscription_requests_are_estimated_never_refused(tmp_path):
    envelope = SpendEnvelope("batch", 0.0)
    budget = SpendBudget(SpendCaps(max_calls=100), subscription=True)
    with spend_envelopes(envelope):
        for _ in range(5):
            with budget.request(SpendEstimate(calls=1, total_tokens=0, estimated_usd=0.0)) as charge:
                charge.note_estimated_only(total_tokens=1000, estimated_usd=0.001)
    report = envelope.report()
    assert report["metered_usd"] == 0 and report["refused_requests"] == 0
    assert report["estimated_only"]["tokens"] == 5000
    assert report["estimated_only"]["usd"] == pytest.approx(0.005)


def test_spend_since_estimates_subscription_tokens_and_prices_unreported_metered_cost(tmp_path):
    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    with repository.connection() as connection:
        rows = [
            ("r_sub", None, "codex", None, 1000, 500, json.dumps({"billing": "subscription"})),
            ("r_met", None, "openrouter", 0.002, 100, 100, json.dumps({"billing": "metered"})),
            ("r_unpriced", None, "openrouter", None, 3000, 1000, json.dumps({"practice_index": {"billing": "metered"}})),
        ]
        for receipt_id, parent, provider, cost, tokens_in, tokens_out, budget in rows:
            connection.execute(
                "INSERT INTO model_call_receipts(id, parent_call_id, owner_kind, owner_id, purpose, provider, status, "
                "started_at, input_tokens, output_tokens, cost, budget_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (receipt_id, parent, "source_exercise_import", "x", "p", provider, "completed",
                 "2026-10-12T10:00:00", tokens_in, tokens_out, cost, budget))
        connection.commit()
    with connect(repository.sqlite_path, read_only=True) as connection:
        spent = spend_since(connection, "2026-10-12T00:00:00", price_per_million=1.0)
    assert spent["estimated_only"] == {"requests": 1, "tokens": 1500, "usd": pytest.approx(0.0015)}
    assert spent["metered"]["requests"] == 2
    assert spent["usd"] == pytest.approx(0.002 + 0.004)
    assert Decimal(str(spent["usd"])) > 0


@pytest.mark.parametrize("since", ["2026-10-13T12:05:52Z", "2026-10-13T12:05:52+00:00",
                                   "2026-10-13T12:05:52.400000+00:00", "2026-10-13T08:05:52-04:00"])
def test_spend_since_counts_a_request_in_the_first_second_of_a_run(tmp_path, since):
    """Live sanity run: a harvest stamps its start ``…52Z`` and the rerank's
    receipt ``…52.822906+00:00``; compared as strings ``.`` sorts before
    ``Z``, so the run's first request was missing from its spend report (and
    from a daily cap starting that second). Requests from that second on count,
    whatever the stamp's suffix; earlier ones never do."""

    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    with repository.connection() as connection:
        for receipt_id, started_at in (("r_same_second", "2026-10-13T12:05:52.822906+00:00"),
                                       ("r_same_second_z", "2026-10-13T12:05:52Z"),
                                       ("r_before", "2026-10-13T12:05:51.999999+00:00")):
            connection.execute(
                "INSERT INTO model_call_receipts(id, owner_kind, owner_id, purpose, provider, status, started_at, "
                "input_tokens, output_tokens, cost, budget_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (receipt_id, "practice_rerank", "x", "p", "openrouter", "completed", started_at, 100, 100, 0.001,
                 json.dumps({"billing": "metered"})))
        connection.commit()
    with connect(repository.sqlite_path, read_only=True) as connection:
        spent = spend_since(connection, since, owner_kinds=None, price_per_million=1.0)
    assert spent["requests"] == 2
    assert spent["usd"] == pytest.approx(0.002)


# -- Codex re-review F2: every service operation under the daily cap; shared reservations ----------


def _spent_out(tmp_path):
    """A metered vault (every service route priced) whose daily cap is already spent."""

    paths, repository, spans = _metered_vault(tmp_path, max_daily_cost_usd=0.0, import_max_cost_usd=5.0,
                                              compare_max_cost_usd=5.0)
    set_config(paths, "source_retrieval", llm_price_per_million=PRICE, rerank_max_cost_usd=1.0)
    return paths, repository, spans


def test_an_ordinary_practice_request_respects_the_daily_cap(tmp_path):
    from learnloop.instructional.policy import caller_for
    from learnloop.instructional.practice import propose_practice

    paths, repository, _spans = _spent_out(tmp_path)
    llm = MeteredServiceLLM()
    result = propose_practice(loaded(paths), repository, "determinant rows swapped sign", {"kinds": "items"},
                              caller=caller_for(repository, "plan"), rerank_client=llm)
    assert [name for _purpose, name in llm.calls] == []  # nothing paid was sent
    assert result["rerank_status"].startswith("over_budget"), result["rerank_status"]
    assert "max_daily_cost_usd" in result["rerank_status"]


def test_a_verified_passage_request_respects_the_daily_cap(tmp_path):
    from learnloop.instructional.policy import caller_for
    from learnloop.instructional.sources import propose_sources

    paths, repository, _spans = _spent_out(tmp_path)
    llm = MeteredServiceLLM()
    hits = propose_sources(loaded(paths), repository, "what happens when rows are swapped",
                           caller=caller_for(repository, "reader"), intent="explain", verify=True, rerank_client=llm)
    assert [name for _purpose, name in llm.calls] == [], hits.manifest.get("verification")


def test_a_comparison_pays_for_nothing_once_the_daily_cap_is_spent(tmp_path):
    from learnloop.instructional.policy import caller_for
    from learnloop.instructional.sources import propose_comparison

    paths, repository, _spans = _spent_out(tmp_path)
    llm = MeteredServiceLLM()
    propose_comparison(loaded(paths), repository, "what happens when rows are swapped",
                       caller=caller_for(repository, "reader"), client=llm, verify_client=llm)
    assert [name for _purpose, name in llm.calls] == []


def test_the_daily_cap_is_shared_by_concurrent_processes(tmp_path):
    """Two processes (each with its own in-memory envelope) reserve against one
    vault's daily cap: a request in flight in one counts for the other."""

    from learnloop.source_retrieval import service_spend as SS

    paths, repository, _spans = _metered_vault(tmp_path, max_daily_cost_usd=1.0)
    vault = loaded(paths)
    first = SS.daily_envelope(vault, repository)
    SS._DAILY.clear()  # the second process has its own envelope objects
    second = SS.daily_envelope(vault, repository)
    assert first is not second
    outcome: dict[str, object] = {}

    def process_b() -> None:  # a fresh context: only its own envelope is active
        try:
            with spend_envelopes(second), SpendBudget(SpendCaps(max_calls=10, max_estimated_usd=10.0)).request(
                    SpendEstimate(calls=1, total_tokens=10, estimated_usd=0.6)):
                outcome["b"] = "admitted"
        except SpendLimitExceeded as exc:
            outcome["b"] = f"refused: {exc}"

    budget = SpendBudget(SpendCaps(max_calls=10, max_estimated_usd=10.0))
    with spend_envelopes(first), budget.request(SpendEstimate(calls=1, total_tokens=10, estimated_usd=0.6)):
        # Process A's request is in flight; process B asks for the same allowance.
        thread = threading.Thread(target=process_b)
        thread.start()
        thread.join()
    assert str(outcome["b"]).startswith("refused"), outcome
