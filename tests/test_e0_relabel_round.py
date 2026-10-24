"""The relabel round (owner 2026-10-23: "Sonnet both + rubric"), fakes only.

* **The probability service copy's Qwen backfill.** Paid run 3 left 177 of
  337 records unembedded: ``ProtectedTextRefused`` on two passes, although
  the copy's redaction had blanked every withheld block (111). The
  diagnosis (counts only, on the run's own copies): the guard's probe of one
  withheld 19-character assessment-lane heading is text that seven
  PERMITTED blocks of the same extraction also contain, so the guard refused
  permitted text. Redaction was right and nothing withheld was about to be
  sent. The guard now probes only what is distinctive to withheld text (every
  window of it that no permitted block contains, not just its first 48
  characters), and the backfill refuses, before sending, any record of a
  withheld block (an unredacted copy). Both fail closed.
* **The relabel.** Label A is Claude Sonnet 5.5 too, an independent pass; the
  relevance rubric is revised on the development slice and frozen by hash.
* **The cumulative cap.** A new authorization carries every earlier
  authorization's committed spend (and seals those ledgers), so the $40 is
  E0-wide, enforced by the ledger before each send.
* **Reuse.** ``--reuse-run`` points a new plan at an earlier run's
  content-keyed stores (checkpoints, vectors, service copies, records); its
  ledger chain still knows every earlier admission.

No network: a socket guard refuses any connection.
"""
from __future__ import annotations

import socket
from contextlib import closing

import pytest

from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings.budget import E0Ledger
from tests.e0_fakes import FakeQwenClient, build_e0_vault
from tests.e0_fakes import verified_prices  # noqa: F401 - the fixture below

#: The fake vault's withheld solution block (``role_hint="solution"``).
SOLUTION = "Solution: apply linearity to 0 = 0 + 0 and cancel T(0) on both sides."


class Qwen(FakeQwenClient):
    """The fake production embedding client with the backfill's capability fields."""

    modalities = frozenset({"text"})
    max_input_tokens = 32_768


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("network attempted in an offline E0 test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def _set_text(paths, prefix: str, text: str) -> None:
    """Rewrite one block of the frozen fake copy (before any snapshot)."""

    from learnloop.db.connection import connect

    with closing(connect(paths.sqlite_path)) as connection:
        changed = connection.execute("UPDATE source_document_blocks SET text = ? WHERE text LIKE ?",
                                     (text, prefix + "%")).rowcount
        connection.commit()
    assert changed == 1


def _service(tmp_path, paths, snapshot, *, redact: bool = True):
    from learnloop.experiments.contextual_embeddings.system_arms import (
        enable_embeddings_on_copy,
        make_service_copy,
        open_service,
        redact_service_copy,
    )

    root = make_service_copy(paths.root, tmp_path / "fixtures-local" / "svc" / "qwen")
    enable_embeddings_on_copy(root)
    handle = open_service(root)
    if redact:
        redact_service_copy(handle, snapshot.policy)
    return handle


# -- 1. the backfill: permitted text that contains a withheld block's text ----------------


def test_a_permitted_block_containing_a_withheld_blocks_text_is_embedded(tmp_path, verified_prices):
    """Paid run 3's probability failure, in miniature: a permitted block
    contains the whole text of a withheld one (there, a 19-character
    assessment-lane heading inside seven permitted Text blocks). Redaction
    blanks the withheld block; the permitted one is what the backfill sends,
    and it must be embedded, so the dense coverage completes."""

    from learnloop.experiments.contextual_embeddings.system_arms import (
        backfill_service_copy,
        dense_coverage_complete,
        guarded_factory,
    )

    paths, _repository = build_e0_vault(tmp_path)
    _set_text(paths, "Exercise 2.1.", "Exercise 2.1. Show that every linear map sends the zero vector to the zero "
              "vector. A worked answer would begin: " + SOLUTION)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    assert any(snapshot.policy.verdict(extraction_id, block.span_id) and block.text == SOLUTION
               for extraction_id, blocks in snapshot.blocks.items() for block in blocks)
    handle = _service(tmp_path, paths, snapshot)
    qwen = Qwen()
    reports = backfill_service_copy(handle, E0Ledger(tmp_path / "ledger"),
                                    client_factory=guarded_factory(lambda: qwen, snapshot))
    assert all(report.get("status") == "complete" for report in reports), [r.get("error_type") for r in reports]
    assert dense_coverage_complete(handle)["complete"] is True


def test_the_guard_still_refuses_withheld_text_even_past_its_first_characters(tmp_path):
    """Failing closed, and stronger than before: every window of a withheld
    block that no permitted block contains is probed, so a leaked tail is
    refused as well as a leaked head (the old guard probed the first 48
    characters only)."""

    from learnloop.experiments.contextual_embeddings.system_arms import ProtectedTextRefused, guarded_factory

    paths, _repository = build_e0_vault(tmp_path)
    tail = " and so T(0) = 0, which is what the exercise asks; nothing else is needed for this proof."
    _set_text(paths, "Solution: apply linearity", SOLUTION + tail)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    inner = FakeQwenClient()
    client = guarded_factory(lambda: inner, snapshot)()
    client.embed(["Definition 1.1 (Vector space). A vector space is a set V"], "retrieval-document")
    for leaked in (SOLUTION + tail, "Section: Chapter 2\n" + tail.strip(), "Exam question 1: prove that the "
                   "additive inverse in a vector space is unique."):
        with pytest.raises(ProtectedTextRefused):
            client.embed(["permitted text", leaked], "retrieval-document")
    assert len(inner.calls) == 1


def test_an_unredacted_service_copy_is_refused_before_any_request(tmp_path, verified_prices):
    """The record-level check: a backfill whose records include a withheld
    block (the copy was never redacted) sends nothing, whatever the text."""

    from learnloop.experiments.contextual_embeddings.system_arms import backfill_service_copy, guarded_factory

    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    handle = _service(tmp_path, paths, snapshot, redact=False)
    qwen = Qwen()
    reports = backfill_service_copy(handle, E0Ledger(tmp_path / "ledger"),
                                    client_factory=guarded_factory(lambda: qwen, snapshot), policy=snapshot.policy)
    assert qwen.calls == []
    assert any(report.get("status") == "refused_unredacted" and report.get("withheld_records", 0) > 0
               for report in reports)


# -- 2. the cumulative cap: a new authorization carries and seals the earlier ones ---------


def _copy(tmp_path):
    copy = tmp_path / "fixtures-local" / "contextual-embeddings" / "vaults" / "v"
    copy.mkdir(parents=True, exist_ok=True)
    return copy


def _spend(ledger, usd, *, category="labels_audits", key=None, output_tokens=None, settle=True):
    from learnloop.experiments.contextual_embeddings.budget import Request

    reservation = ledger.reserve(Request(category=category, provider="e0_anthropic_sonnet", route="claude-sonnet-5-5",
                                         purpose="label_a:e0_label_a", billing="metered", estimated_usd=usd,
                                         estimated_tokens=10, request_key=key))
    if settle:
        ledger.settle(reservation, actual_usd=usd, usage={"input_tokens": 10, "output_tokens": output_tokens or 5})
    return reservation


def test_a_new_authorization_carries_the_earlier_spend_into_one_cumulative_cap(tmp_path):
    from learnloop.experiments.contextual_embeddings import pins
    from learnloop.experiments.contextual_embeddings.budget import E0BudgetExceeded, authorized_ledger

    copy = _copy(tmp_path)
    first = authorized_ledger([copy], "e0_1111111111111111", new_authorization="first")
    _spend(first, 10.0)
    _spend(first, 4.0, category="answers_verification")
    _spend(first, 0.149, category="drafting_context", settle=False)  # outstanding: carried at its reservation
    with pytest.raises(PermissionError, match="new-authorization"):
        authorized_ledger([copy], "e0_2222222222222222")
    second = authorized_ledger([copy], "e0_2222222222222222", new_authorization="owner: Sonnet both + rubric")
    report = second.report()
    assert report["committed_usd"] == 0.0 and report["carried_usd"] == pytest.approx(14.149)
    assert report["remaining_usd"] == pytest.approx(pins.E0_CAP_USD - 14.149)
    assert report["carried_from"] == ["e0_1111111111111111"]
    assert report["by_category"]["labels_audits"]["carried_usd"] == pytest.approx(10.0)
    # The category allocation is cumulative: labels may spend 33.00 - 10.00 more, not 33.00.
    with pytest.raises(E0BudgetExceeded, match="labels_audits allocation"):
        _spend(second, pins.ALLOCATION_USD["labels_audits"] - 10.0 + 0.01)
    # And the cap: answers 5.90 - 4.00 left, so 2.00 is refused there before the cap.
    with pytest.raises(E0BudgetExceeded):
        _spend(second, 2.0, category="answers_verification")
    _spend(second, 1.0, category="answers_verification")
    assert second.report()["cumulative_committed_usd"] == pytest.approx(15.149)
    # Reopening the new plan keeps its carried spend (never a fresh cap).
    again = authorized_ledger([copy], "e0_2222222222222222")
    assert again.report()["carried_usd"] == pytest.approx(14.149) and again.remaining() == pytest.approx(
        pins.E0_CAP_USD - 15.149)


def test_the_earlier_ledger_is_sealed_for_any_code_that_reads_it(tmp_path):
    import json

    from learnloop.experiments.contextual_embeddings.budget import E0RunHalted, authorized_ledger

    copy = _copy(tmp_path)
    first = authorized_ledger([copy], "e0_1111111111111111", new_authorization="first")
    _spend(first, 1.0)
    authorized_ledger([copy], "e0_2222222222222222", new_authorization="relabel")
    state = json.loads(first.path.read_text(encoding="utf-8"))
    assert state["superseded"]["by"] == "e0_2222222222222222"
    # ``halted`` is what every earlier version of this code already refuses on.
    assert "superseded by e0_2222222222222222" in state["halted"]["reason"]
    with pytest.raises(E0RunHalted):
        _spend(authorized_ledger([copy], "e0_1111111111111111"), 0.01)


def test_the_earlier_ledgers_admissions_stay_visible_so_a_known_truncation_is_not_resent(tmp_path):
    """The relabel reuses run 3's checkpoints, whose failure markers point
    at run 3's ledger entries: through the chain, a request that stopped at
    max_tokens under the earlier plan is still never re-sent at that bound."""

    import json

    from learnloop.experiments.contextual_embeddings import retrieval as Rt
    from learnloop.experiments.contextual_embeddings.adapters import HttpResponse
    from learnloop.experiments.contextual_embeddings.budget import E0ProviderFailure, authorized_ledger
    from learnloop.experiments.contextual_embeddings.callers import Checkpoints, LiveRoleCaller

    posts = []

    class Truncating:
        def post(self, url, *, headers, body, timeout):
            posts.append(body)
            return HttpResponse(200, {"id": "msg_1", "type": "message", "role": "assistant", "model": body["model"],
                                      "stop_reason": "max_tokens", "stop_sequence": None,
                                      "content": [{"type": "text", "text": '{"contexts": ['}],
                                      "usage": {"input_tokens": 1200, "output_tokens": body["max_tokens"]}}, "r")

    paths, _repository = build_e0_vault(tmp_path)
    handle = C.open_copy(paths.root)
    store = tmp_path / "fixtures-local" / "runs" / "e0_1111111111111111" / "v" / "llm"
    first = authorized_ledger([paths.root], "e0_1111111111111111", new_authorization="first")
    caller = LiveRoleCaller(handle.root, handle.vault.config, first, checkpoints=Checkpoints(store),
                            environ={"ANTHROPIC_API_KEY": "sk-ant-test-not-real"}, anthropic_transport=Truncating())
    with pytest.raises(E0ProviderFailure):
        caller.call("context", prompt="window", result_model=Rt.GeneratedContexts, arm="R3")
    [marker] = list(store.glob(".*.failed.json"))
    marker.write_text(json.dumps(json.loads(marker.read_text())["reservations"]))  # the first run's format
    second = authorized_ledger([paths.root], "e0_2222222222222222", new_authorization="relabel")
    resumed = LiveRoleCaller(handle.root, handle.vault.config, second, checkpoints=Checkpoints(store),
                             environ={"ANTHROPIC_API_KEY": "sk-ant-test-not-real"}, anthropic_transport=Truncating())
    with pytest.raises(E0ProviderFailure, match="known truncated"):
        resumed.call("context", prompt="window", result_model=Rt.GeneratedContexts, arm="R3")
    assert len(posts) == 1


# -- 3. the relabel's pins: Sonnet both, the rubric frozen ---------------------------------


def test_both_label_passes_are_sonnet_and_the_rubric_is_frozen_by_hash():
    import hashlib

    from learnloop.experiments.contextual_embeddings import bank as B
    from learnloop.experiments.contextual_embeddings import pins

    roles = pins.ROLE_PINS
    assert roles["label_a"].model == roles["label_b"].model == "claude-sonnet-5-5"
    assert roles["label_a"].prompt_version == roles["label_b"].prompt_version == "e0-label-v2"
    assert roles["adjudicator"].model == "claude-opus-5-5" and roles["adjudicator"].prompt_version == "e0-adjudicate-v2"
    assert hashlib.sha256(B.RELEVANCE_RUBRIC.encode("utf-8")).hexdigest() == pins.LABEL_RUBRIC_SHA256
    for instructions in (B.LABEL_INSTRUCTIONS, B.RELEVANCE_ONLY_INSTRUCTIONS):
        assert instructions.startswith(B.RELEVANCE_RUBRIC)
    # The development-slice finding the revision targets: area is not background.
    assert "not enough for background" in B.RELEVANCE_RUBRIC
    assert "lower one" in B.RELEVANCE_RUBRIC


def test_an_edited_rubric_refuses_to_load(monkeypatch):
    from learnloop.experiments.contextual_embeddings import bank as B
    from learnloop.experiments.contextual_embeddings import pins

    assert B.check_rubric_frozen() == pins.LABEL_RUBRIC_SHA256
    with pytest.raises(RuntimeError, match="frozen hash"):
        B.check_rubric_frozen(B.RELEVANCE_RUBRIC + " Also judge style.")
    monkeypatch.setattr(pins, "LABEL_RUBRIC_SHA256", "0" * 64)
    with pytest.raises(RuntimeError, match="frozen hash"):
        B.check_rubric_frozen()


def test_the_two_passes_stay_independent_requests_in_different_orders(tmp_path):
    """Same model, still two passes: each its own request, its own candidate
    order and refs, its own pass number, blind to arm and to the other pass."""

    import json

    from learnloop.experiments.contextual_embeddings import bank as B

    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    question = B.freeze_context(B.BankQuestion("q1", "development", None, "writer", "explain", "intent_explain",
                                               "Why is the additive identity unique?"), snapshot)
    pool = [unit.unit_id for unit in snapshot.units][:12]
    seen = []

    class Caller:
        def call(self, role, *, prompt, result_model, arm=None):
            seen.append((role, prompt, arm))
            context = json.loads(prompt[prompt.index("{"):])["context"]
            return result_model.model_validate({"labels": [{"ref": item["ref"], "relevance": "unrelated"}
                                                           for item in context["candidates"]],
                                                "sufficient_sets": [], "answerable": False})

    B.label_question(question, pool, snapshot, Caller())
    (role_a, prompt_a, arm_a), (role_b, prompt_b, arm_b) = seen
    assert (role_a, role_b) == ("label_a", "label_b") and arm_a is arm_b is None
    texts = [[item["text"] for item in json.loads(prompt[prompt.index("{"):])["context"]["candidates"]]
             for prompt in (prompt_a, prompt_b)]
    assert sorted(texts[0]) == sorted(texts[1]) and texts[0] != texts[1]
    assert '"pass": 1' in prompt_a and '"pass": 2' in prompt_b
    assert "pass_1" not in prompt_b and "R1" not in prompt_a


# -- 4. the offline estimate and the authorization budget ----------------------------------


def _entry(category, purpose, route, tokens_in, tokens_out, usd, arm=None):
    return {"category": category, "purpose": purpose, "route": route, "arm": arm, "billing": "metered",
            "reserved_usd": str(usd), "actual_usd": str(usd),
            "usage": {"input_tokens": tokens_in, "output_tokens": tokens_out}}


def test_the_reuse_estimate_reprices_every_label_request_at_todays_pins():
    from learnloop.experiments.contextual_embeddings import bank as B
    from learnloop.experiments.contextual_embeddings.pins import token_estimate
    from learnloop.experiments.contextual_embeddings.plan import REUSE_ASSUMPTIONS, budget_check, reuse_estimate

    ledger = {"entries": {
        "a": _entry("labels_audits", "label_a:e0_label_a", "claude-haiku-5-5", 1_000_000, 200_000, 0.2),
        "b": _entry("labels_audits", "label_b:e0_label_b", "claude-sonnet-5-5", 1_000_000, 100_000, 3.0),
        "c": _entry("labels_audits", "adjudicator:e0_adjudicator", "claude-opus-5-5", 1_000_000, 100_000, 6.0),
        "k": _entry("labels_audits", "adjudicator:canary", "claude-opus-5-5", 22, 4, 0.0002, arm="canary"),
        "t": _entry("answers_verification", "tutor:e0_tutor", "claude-haiku-5-5", 10, 10, 0.5, arm="R1:D1"),
        "d": _entry("answers_verification", "tutor:e0_tutor", "claude-haiku-5-5", 10, 10, 0.7, arm="D2"),
        "s": _entry("answers_verification", "system:verify", "anthropic/claude-haiku-5.5", 10, 10, 0.1, arm="R0"),
        "e": _entry("embeddings", "embed:documents", "voyage-4-large", 10, 0, 0.03, arm="R5_grouped"),
    }}
    estimate = reuse_estimate(ledger)
    growth = 1 + REUSE_ASSUMPTIONS["label_pool_growth"]
    rubric = token_estimate(B.RELEVANCE_RUBRIC)
    # Label A's Haiku tokens at Sonnet's $2 / $10 (its own output counts kept).
    assert estimate["roles"]["label_a"]["repriced_usd"] == pytest.approx(
        ((1_000_000 * growth + rubric) * 2 + 200_000 * growth * 10) / 1e6, abs=1e-4)
    assert estimate["roles"]["adjudicator"]["calls"] == 1  # the canary is not a label request
    assert estimate["roles"]["adjudicator"]["repriced_usd"] == pytest.approx(
        ((1_000_000 * growth + rubric) * 4 + 100_000 * growth * 20) / 1e6, abs=1e-4)
    # D0-D3 answers are reused; the finalist answers are the worst case; system twice.
    assert estimate["categories"]["answers_verification"] == pytest.approx(0.5 + 0.2 + 0.01)
    fits = budget_check(estimate["categories"], {"total_usd": 14.149, "by_category": {"labels_audits": 11.302},
                                                 "plans": {"e0_1111111111111111": {}}})
    assert fits["remaining_usd"] == pytest.approx(40.0 - 14.149)
    assert fits["categories"]["labels_audits"]["remaining_usd"] == pytest.approx(33.0 - 11.302)
    assert fits["fits"] is True
    assert budget_check({"labels_audits": 22.0}, {"total_usd": 14.149, "by_category": {"labels_audits": 11.302}})[
        "fits"] is False


def test_the_dry_run_budget_uses_the_reused_runs_ledger_and_fails_closed_without_it(tmp_path):
    import json

    from learnloop.experiments.contextual_embeddings.budget import authorized_ledger
    from learnloop.experiments.contextual_embeddings.runner import dry_run

    paths, _repository = build_e0_vault(tmp_path)
    missing = dry_run([paths.root], environ={}, reuse_run="e0_1111111111111111")
    assert missing["budget"]["fits"] is False and "error" in missing["budget"]["reuse"]
    earlier = authorized_ledger([paths.root], "e0_1111111111111111", new_authorization="first")
    _spend(earlier, 3.0)
    plan = dry_run([paths.root], environ={}, reuse_run="e0_1111111111111111")
    budget = plan["budget"]
    assert budget["basis"] == "reuse_estimate" and budget["carried_usd"] == pytest.approx(3.0)
    assert budget["carried_from"] == ["e0_1111111111111111"] and budget["fits"] is True
    assert budget["reuse"]["roles"]["label_a"]["model"] == "claude-sonnet-5-5"
    # Nothing was sealed or created by planning.
    assert "superseded" not in json.loads(earlier.path.read_text(encoding="utf-8"))
    assert not (earlier.path.parent / f"{plan['run_id']}.ledger").exists()


# -- 5. reuse: a new plan reads the earlier run's stores and re-sends only what changed ----


def _factories(clients):
    from learnloop.experiments.contextual_embeddings import live
    from tests.e0_fakes import FakeEmbeddingTransport, FakeRoleClient, qwen_bag_of_words
    from learnloop.experiments.contextual_embeddings import pins

    qwen = qwen_bag_of_words(4096)

    def role_client(name):
        clients.append(FakeRoleClient(name))
        return clients[-1]

    dims = {pin.model: pin.dimensions for pin in pins.EMBEDDING_PINS.values()}
    return live.LiveFactories(transport=FakeEmbeddingTransport(dims=dims, int8_models=frozenset(
        {"pplx-embed-context-v1-4b", "pplx-embed-v1-4b"})), qwen=lambda _config: (lambda: qwen),
        role_clients=role_client, system_clients={"embedder": qwen})


def _roles(clients):
    return sorted({str(request["purpose"]).removeprefix("e0_") for client in clients for request in client.requests})


def test_a_reused_run_resends_only_the_changed_requests_and_keeps_its_own_results(tmp_path, monkeypatch,
                                                                                  verified_prices):
    import json
    from dataclasses import replace

    from learnloop.experiments.contextual_embeddings import live, pins
    from learnloop.experiments.contextual_embeddings.runner import dry_run
    from tests.e0_fakes import FAKE_KEYS

    paths, _repository = build_e0_vault(tmp_path, manual_ai=True)
    for name, value in FAKE_KEYS.items():
        monkeypatch.setenv(name, value)
    run_dir = tmp_path / "fixtures-local" / "runs"
    first_plan = dry_run([paths.root], environ=FAKE_KEYS)
    first_clients: list = []
    first = live.run_live([paths.root], plan=first_plan, run_dir=run_dir, key_envs={},
                          factories=_factories(first_clients))
    assert {"writer", "context", "label_a", "label_b", "tutor"} <= set(_roles(first_clients))
    earlier_results = (run_dir / first_plan["run_id"] / paths.root.name / "results.json").read_bytes()
    # A changed label A pin: a new plan id; label A's requests change, nothing else does.
    monkeypatch.setitem(pins.ROLE_PINS, "label_a", replace(pins.ROLE_PINS["label_a"], prompt_version="e0-label-x"))
    second_plan = dry_run([paths.root], environ=FAKE_KEYS, reuse_run=first_plan["run_id"])
    assert second_plan["run_id"] != first_plan["run_id"] and second_plan["budget"]["fits"]
    second_clients: list = []
    second = live.run_live([paths.root], plan=second_plan, run_dir=run_dir, key_envs={},
                           factories=_factories(second_clients), new_authorization="relabel test",
                           reuse_run=first_plan["run_id"])
    assert _roles(second_clients) == ["label_a"]
    written = run_dir / second_plan["run_id"] / paths.root.name / "results.json"
    assert json.loads(written.read_text())["reused_run"] == first_plan["run_id"]
    assert (run_dir / first_plan["run_id"] / paths.root.name / "results.json").read_bytes() == earlier_results
    assert second["ledger"]["carried_from"] == [first_plan["run_id"]]
    assert second["ledger"]["carried_usd"] == pytest.approx(first["ledger"]["committed_usd"])


def test_a_reused_run_with_other_candidate_maps_is_refused_before_anything_is_sealed(tmp_path, monkeypatch,
                                                                                     verified_prices):
    import json

    from learnloop.experiments.contextual_embeddings import live
    from learnloop.experiments.contextual_embeddings.budget import authorized_ledger
    from learnloop.experiments.contextual_embeddings.runner import dry_run
    from tests.e0_fakes import FAKE_KEYS

    paths, _repository = build_e0_vault(tmp_path, manual_ai=True)
    run_dir = tmp_path / "fixtures-local" / "runs"
    earlier = run_dir / "e0_1111111111111111" / "frozen"
    earlier.mkdir(parents=True)
    plan = dry_run([paths.root], environ=FAKE_KEYS)
    (earlier / "run_plan.json").write_text(json.dumps({"splits": plan["splits"]}))
    (earlier / "candidate_maps.json").write_text(json.dumps({paths.root.name: []}))
    ledger = authorized_ledger([paths.root], "e0_1111111111111111", new_authorization="first")
    with pytest.raises(live.PlanMismatch, match="candidate maps"):
        live.run_live([paths.root], plan=plan, run_dir=run_dir, key_envs={}, factories=_factories([]),
                      new_authorization="relabel", reuse_run="e0_1111111111111111")
    assert "superseded" not in json.loads(ledger.path.read_text(encoding="utf-8"))
    with pytest.raises(live.PlanMismatch, match="no frozen plan"):
        live.run_live([paths.root], plan=plan, run_dir=run_dir, key_envs={}, factories=_factories([]),
                      new_authorization="relabel", reuse_run="e0_2222222222222222")
