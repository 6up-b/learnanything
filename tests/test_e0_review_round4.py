"""Regressions for the pre-paid-run verify of the E0 harness (fix round 4), fakes only.

High 1-8 and Medium 9-14 of Codex job 20261021-131313-hCUxeG, with the
orchestrator's rulings (verified prices and hard maximum charges, one budget
per authorization, a Codex request allowance). Every test runs offline
behind a socket guard: fake embedding transports, the fake ``openai``
module, hash vectors and fake role clients. Only the tests that need an
admitted metered request mark the prices verified (``verified_prices``);
production pins stay unverified."""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
import socket
import threading
from types import SimpleNamespace

import pytest

from learnloop.experiments.contextual_embeddings import adapters as A
from learnloop.experiments.contextual_embeddings import bank as B
from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings import budget as _budget
from learnloop.experiments.contextual_embeddings.budget import E0BudgetExceeded, E0Ledger, Request
from learnloop.experiments.contextual_embeddings.callers import Checkpoints, FakeRoleCaller, LiveRoleCaller
from learnloop.experiments.contextual_embeddings.delivery import Selection, deliver
from learnloop.experiments.contextual_embeddings.paid import run_paid, snapshot_sqlite
from tests.e0_fakes import (
    FAKE_KEYS,
    FakeEmbeddingTransport,
    FakeQwenClient,
    FakeRoleClient,
    build_e0_vault,
    fake_respond,
    unverified_prices,  # noqa: F401 - requested by name below
    verified_prices,  # noqa: F401 - requested by name below
)
from learnloop.tutor.context_delivery import BlockSource
from tests.helpers import create_basic_vault

DIMS = {pin.model: pin.dimensions for pin in pins.EMBEDDING_PINS.values()}
INT8 = frozenset({"pplx-embed-context-v1-4b", "pplx-embed-v1-4b"})
STRATA = {"reader_deictic": 2, "distant_same_source": 1, "direct_lookup": 1, "no_support": 1, "intent_explain": 1}
KEY = FAKE_KEYS["OPENROUTER_API_KEY"]


def _new(name):
    """A name this fix round adds (looked up per test, so each test fails on its
    own against an older harness instead of the module failing to import)."""

    return getattr(_budget, name)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("network attempted in an offline E0 test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _set_sqlite_path(root: Path, value: str) -> None:
    import tomlkit

    toml = Path(root) / "learnloop.toml"
    document = tomlkit.parse(toml.read_text(encoding="utf-8"))
    document.setdefault("storage", tomlkit.table())["sqlite_path"] = value
    toml.write_text(tomlkit.dumps(document), encoding="utf-8")


def _adapter(pin_name, tmp_path, *, transport, ledger=None, encoding=None):
    pin = pins.EMBEDDING_PINS[pin_name]
    cls = A.ADAPTERS[pin_name]
    encoding = encoding or ("grouped" if pin.method == "grouped" else "independent")
    return cls(pin, encoding=encoding, recipe="plain", ledger=ledger or E0Ledger(tmp_path / "ledger"), arm="test",
               transport=transport, receipts=A.Receipts(tmp_path / "receipts.jsonl"),
               store=A.VectorStore(tmp_path / "vectors"), environ=FAKE_KEYS, sleep=lambda _seconds: None)


def _documents():
    return [A.Document("w1", (A.Chunk("w1:a", "Definition of a vector space."),), key="k1")]


# -- High 1: containment ------------------------------------------------------------------


def _owner_database(tmp_path):
    owner = create_basic_vault(tmp_path / "owner")  # outside fixtures-local: the "owner's" vault
    return Path(owner.sqlite_path)


def test_h1_a_service_copy_naming_an_outside_database_is_refused_before_any_open(tmp_path):
    from learnloop.experiments.contextual_embeddings.system_arms import make_service_copy, open_service

    paths, _repository = build_e0_vault(tmp_path)
    outside = _owner_database(tmp_path)
    before = _sha(outside)
    root = make_service_copy(paths.root, tmp_path / "fixtures-local" / "service" / "r0")
    _set_sqlite_path(root, str(outside))  # an absolute path kept by copying
    with pytest.raises(C.CopyContainment):
        open_service(root)
    _set_sqlite_path(root, "../../../../owner/state.sqlite")  # an escaping relative path
    with pytest.raises(C.CopyContainment):
        open_service(root)
    assert _sha(outside) == before  # never opened, never migrated


def test_h1_a_frozen_copy_naming_an_outside_or_linked_database_is_refused(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    outside = _owner_database(tmp_path)
    _set_sqlite_path(paths.root, str(outside))
    with pytest.raises(C.CopyContainment):
        C.open_copy(paths.root)
    _set_sqlite_path(paths.root, "linked.sqlite")
    (paths.root / "linked.sqlite").symlink_to(outside)
    with pytest.raises(C.CopyContainment):
        C.open_copy(paths.root)


def test_h1_prepare_rebases_a_relocated_database_into_the_copy(tmp_path):
    owner = create_basic_vault(tmp_path / "sources" / "linear_algebra")
    relocated = tmp_path / "elsewhere" / "owner.sqlite"
    relocated.parent.mkdir(parents=True)
    Path(owner.sqlite_path).rename(relocated)
    _set_sqlite_path(owner.root, str(relocated))
    before = _sha(relocated)
    [record] = C.prepare_copies([owner.root], tmp_path / "fixtures-local" / "copies", label="t")
    copy = Path(record["copy"])
    import tomllib

    storage = tomllib.loads((copy / "learnloop.toml").read_text(encoding="utf-8"))["storage"]
    assert not Path(storage["sqlite_path"]).is_absolute()
    assert (copy / storage["sqlite_path"]).is_file()
    handle = C.open_copy(copy)
    assert handle.sqlite_path.resolve().is_relative_to(copy.resolve())
    assert _sha(relocated) == before


# -- High 2: verified prices, hard maximum, overage halts --------------------------------


def test_h2_an_unverified_price_refuses_every_metered_request_before_sending(tmp_path, unverified_prices):
    transport = FakeEmbeddingTransport(dims=DIMS)
    adapter = _adapter("voyage_4_large", tmp_path, transport=transport)
    with pytest.raises(_new("E0PriceUnverified")):
        adapter.encode_documents(_documents())
    assert transport.requests == []
    qwen = FakeQwenClient()
    adapter = A.QwenAdapter(pins.EMBEDDING_PINS["qwen3_8b"], client_factory=lambda: qwen, recipe="plain",
                            ledger=E0Ledger(tmp_path / "qwen-ledger"), arm="R1")
    with pytest.raises(_new("E0PriceUnverified")):
        adapter.encode_documents(_documents())
    assert qwen.calls == []
    from learnloop.experiments.contextual_embeddings.callers import E0RequestGate

    gate = E0RequestGate(E0Ledger(tmp_path / "role-ledger"), pins.ROLE_PINS["adjudicator"])
    with pytest.raises(_new("E0PriceUnverified")):
        gate.admit(None, purpose="adjudicate", prompt="p", budget=100)
    assert pins.unverified_prices()["roles"] == sorted(pins.ROLE_PINS)  # every role is metered (re-plan)
    assert "qwen3_8b" in pins.unverified_prices()["embeddings"]


def test_h2_a_settlement_above_its_reservation_halts_the_whole_run(tmp_path, verified_prices):
    ledger = E0Ledger(tmp_path / "ledger")
    first = ledger.reserve(Request(category="embeddings", provider="p", route="r", purpose="x", estimated_usd=0.001))
    with pytest.raises(_new("E0RunHalted")):
        ledger.settle(first, actual_usd=0.002)
    report = ledger.report()
    assert report["halted"] and report["overages"][0]["overage_usd"] == "0.001"
    # Every later request, in any category or billing class, any ledger instance, is refused.
    for billing in ("metered", "subscription"):
        with pytest.raises(_new("E0RunHalted")):
            E0Ledger(tmp_path / "ledger").reserve(Request(category="labels_audits", provider="p", route="r",
                                                          purpose="y", billing=billing, estimated_usd=0.0))


def test_h2_an_overcharged_hosted_response_stops_the_paid_run_at_once(tmp_path, verified_prices):
    class Overcharging(FakeEmbeddingTransport):
        def post(self, url, *, headers, body, timeout):
            response = super().post(url, headers=headers, body=body, timeout=timeout)
            if response.body is None:
                return response
            return A.HttpResponse(response.status, {**response.body, "usage": {"cost": 5.0}}, response.request_id)

    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    ledger = E0Ledger(tmp_path / "ledger")
    caller = FakeRoleCaller(fake_respond, ledger)
    result = run_paid(snapshot, ledger=ledger, caller=caller, run_dir=None,
                      transport=Overcharging(dims=DIMS, int8_models=INT8), qwen_client_factory=FakeQwenClient,
                      strata=STRATA, environ=FAKE_KEYS)
    assert result["status"] == "incomplete" and str(result["incomplete_reason"]).startswith("halted")
    assert result["ledger"]["halted"] and result["ledger"]["overages"]
    assert caller.calls == []  # nothing after the halt: no writer, label or answer call


def test_h2_the_dry_run_reports_unverified_prices_and_authorization_refuses_them(tmp_path, unverified_prices):
    from learnloop.experiments.contextual_embeddings.runner import dry_run, require_paid_authorization

    paths, _repository = build_e0_vault(tmp_path)
    plan = dry_run([paths.root], environ={})
    assert plan["prices"]["unverified"]["roles"] == sorted(pins.ROLE_PINS)
    assert set(plan["prices"]["unverified"]["embeddings"]) == set(pins.EMBEDDING_PINS)
    with pytest.raises(PermissionError, match="unverified prices"):
        require_paid_authorization(authorized=True, dry_run_ok=True, unverified_prices=plan["prices"]["unverified"])


# -- High 3: one budget per authorization -------------------------------------------------


def test_h3_one_canonical_ledger_per_plan_whatever_the_run_directory(tmp_path):
    copy = tmp_path / "fixtures-local" / "contextual-embeddings" / "vaults" / "v1"
    copy.mkdir(parents=True)
    first = _new("authorized_ledger")([copy], "e0_0123456789abcdef")
    assert first.path == tmp_path / "fixtures-local" / "contextual-embeddings" / "ledger" / "e0_0123456789abcdef.ledger"
    first.reserve(Request(category="embeddings", provider="p", route="r", purpose="x", estimated_usd=1.5))
    again = _new("authorized_ledger")([copy], "e0_0123456789abcdef")
    assert again.path == first.path and again.report()["committed_usd"] == 1.5  # shared, never a fresh $25
    with pytest.raises(PermissionError, match="new-authorization"):
        _new("authorized_ledger")([copy], "e0_fedcba9876543210")
    other = _new("authorized_ledger")([copy], "e0_fedcba9876543210", new_authorization="owner approved a re-plan")
    assert other.report()["authorization"] == {"plan_id": "e0_fedcba9876543210"}


def test_h3_two_paid_runs_with_different_run_directories_share_one_budget(tmp_path, monkeypatch, verified_prices):
    from learnloop.experiments.contextual_embeddings import live
    from learnloop.experiments.contextual_embeddings.runner import dry_run

    paths, _repository = build_e0_vault(tmp_path, manual_ai=True)
    for name, value in FAKE_KEYS.items():
        monkeypatch.setenv(name, value)
    plan = dry_run([paths.root], environ=FAKE_KEYS)

    def factories():
        from tests.e0_fakes import qwen_bag_of_words

        qwen = qwen_bag_of_words(4096)
        return live.LiveFactories(transport=FakeEmbeddingTransport(dims=DIMS, int8_models=INT8),
                                  qwen=lambda _config: (lambda: qwen), role_clients=lambda name: FakeRoleClient(name),
                                  system_clients={"embedder": qwen})

    one = live.run_live([paths.root], plan=plan, run_dir=tmp_path / "fixtures-local" / "runs-a", key_envs={},
                        factories=factories())
    two = live.run_live([paths.root], plan=plan, run_dir=tmp_path / "fixtures-local" / "runs-b", key_envs={},
                        factories=factories())
    canonical = tmp_path / "fixtures-local" / "contextual-embeddings" / "ledger" / f"{plan['run_id']}.ledger"
    assert canonical.is_file()
    assert not (tmp_path / "fixtures-local" / "runs-a" / "ledger").exists()
    assert two["ledger"]["requests"] > one["ledger"]["requests"]  # the second run kept counting


# -- High 4: the Qwen client is checked against its pin -----------------------------------


@pytest.mark.parametrize("change", [{"model_id": "other/embedding-model"}, {"dims": 2048},
                                    {"default_base_url": "https://example.invalid/v1"},
                                    {"provider_type": "openai_chat"}])
def test_h4_a_qwen_client_that_is_not_its_pin_is_refused_before_its_first_request(tmp_path, change, verified_prices):
    client = FakeQwenClient()
    for name, value in change.items():
        setattr(client, name, value)
    if "default_base_url" in change:
        client.profile.base_url = None
    with pytest.raises(A.AdapterError, match="does not match its pin"):
        A.QwenAdapter(pins.EMBEDDING_PINS["qwen3_8b"], client_factory=lambda: client, recipe="plain",
                      ledger=E0Ledger(tmp_path / "ledger"), arm="R1")
    assert client.calls == []


def test_h4_the_qwen_identity_is_in_cache_keys_and_receipts_and_the_service_gate(tmp_path, verified_prices):
    from learnloop.experiments.contextual_embeddings.system_arms import SystemRequestGate

    one = FakeQwenClient()
    receipts = A.Receipts(None)
    first = A.QwenAdapter(pins.EMBEDDING_PINS["qwen3_8b"], client_factory=lambda: one, recipe="plain",
                          ledger=E0Ledger(tmp_path / "ledger"), arm="R1", receipts=receipts)
    first.encode_documents(_documents())
    assert receipts.rows[-1]["identity"]["model"] == "qwen/qwen3-embedding-8b"
    assert first.identity["endpoint"] == pins.EMBEDDING_PINS["qwen3_8b"].document_endpoint
    other = FakeQwenClient()
    other.provider_name = "another_profile"
    second = A.QwenAdapter(pins.EMBEDDING_PINS["qwen3_8b"], client_factory=lambda: other, recipe="plain",
                           ledger=E0Ledger(tmp_path / "ledger2"), arm="R1")
    assert second.document_space_id == first.document_space_id  # the same validated identity
    gate = SystemRequestGate(E0Ledger(tmp_path / "gate"), SimpleNamespace(), arm="R1_service_rrf")
    with pytest.raises(_new("E0ProviderFailure")):
        gate.admit(SimpleNamespace(provider_type="openai_embedding", model="other/model"), purpose="embedding",
                   prompt=["q"], budget=None)


# -- High 5: protected headings -----------------------------------------------------------


def _blocks():
    from learnloop.db.stores.source_block_fts import BlockRow

    header = BlockRow("ext_x", "s_head", "SectionHeader", "Midterm problem 3: the secret heading", 1, "[]", 0,
                      "/page/1/SectionHeader/3")
    body = BlockRow("ext_x", "s_body", "Text", "A vector space is a set with two operations satisfying the axioms.",
                    1, json.dumps(["/page/1/SectionHeader/3"]), 1, "/page/1/Text/4")
    return header, body


def _policy(withheld):
    return C.PolicySnapshot(dict(withheld), frozenset(), {"ext_x": (2, 2)}, json.dumps(sorted(withheld)))


def test_h5_a_withheld_heading_never_reaches_a_permitted_descendant(tmp_path):
    header, body = _blocks()
    info = C.ExtractionInfo("src_x", "ext_x", None, "marker", "1", None, None, (2, 2), True, "Book")
    titles = {"/page/1/SectionHeader/3": header.text}
    policy = _policy({("ext_x", "s_head"): "exam_or_held_out"})
    [unit] = C.build_units(info, [header, body], titles, policy)
    assert "secret" not in " ".join(unit.section).lower()
    assert unit.section == (C.WITHHELD_HEADING,)
    assert unit.heading_keys == (("ext_x", "s_head"),)


def test_h5_a_heading_marked_later_invalidates_the_units_built_under_it(tmp_path):
    header, body = _blocks()
    info = C.ExtractionInfo("src_x", "ext_x", None, "marker", "1", None, None, (2, 2), True, "Book")
    titles = {"/page/1/SectionHeader/3": header.text}
    open_policy = _policy({})
    unit = next(item for item in C.build_units(info, [header, body], titles, open_policy)
                if ("ext_x", "s_body") in item.keys)
    assert unit.section == (header.text,)
    snapshot = SimpleNamespace(infos={"ext_x": info}, policy=open_policy)
    dependency = C.CorpusSnapshot.unit_dependency(snapshot, unit)
    assert ("ext_x", "s_head") in dependency.keys
    marked = _policy({("ext_x", "s_head"): "exam_or_held_out"})
    assert C.stale_reasons(dependency, marked) == ["now_withheld:exam_or_held_out"]


# -- High 6: logged questions resolve their provenance ------------------------------------


def _snapshot(tmp_path, **kwargs):
    paths, repository = build_e0_vault(tmp_path, **kwargs)
    return C.build_snapshot(C.open_copy(paths.root)), paths, repository


def test_h6_a_practice_question_is_rejected_unless_its_provenance_is_cleared(tmp_path):
    snapshot, _paths, _repository = _snapshot(tmp_path)
    events = [{"id": "e1", "question_md": "why is the zero vector unique here?", "context": "practice",
               "practice_item_id": "item_held_out", "source_context": {}},
              {"id": "e2", "question_md": "what does the span of a list mean?", "context": "library",
               "source_context": {}},
              {"id": "e3", "question_md": "what is this tool question about?", "context": "mcp_unknown",
               "source_context": {}}]
    # Without a protection authority an event naming an item is rejected (fail closed).
    questions, counts = B.logged_bank(snapshot, events)
    assert [question.question for question in questions] == ["what does the span of a list mean?"]
    assert counts["provenance_unresolved"] == 2
    # With one, the item's protection decides.
    questions, counts = B.logged_bank(snapshot, events,
                                      protection=lambda event: "held out" if event.get("practice_item_id") else None)
    assert [question.question for question in questions] == ["what does the span of a list mean?"]
    assert counts["provenance_protected"] == 1 and counts["provenance_unresolved"] == 1


def test_h6_the_production_protection_rejects_an_unknown_item_question(tmp_path):
    snapshot, paths, repository = _snapshot(tmp_path)
    repository.insert_question_event({"id": "qe_item", "context": "practice", "practice_item_id": "no_such_item",
                                      "question_md": "is the answer to this item zero?", "answer_status": "answered"})
    handle = C.open_copy(paths.root)
    questions, counts = B.logged_questions(handle, snapshot)
    assert all(question.question != "is the answer to this item zero?" for question in questions)
    assert counts["provenance_unresolved"] + counts["provenance_protected"] >= 1


# -- High 7: an unproven quote is dropped -------------------------------------------------


def test_h7_a_quote_without_complete_canonical_coverage_is_dropped(tmp_path):
    snapshot, _paths, _repository = _snapshot(tmp_path)
    blocks = snapshot.blocks["ext_book"]
    protected = next(block for block in blocks if not snapshot.policy.permitted("ext_book", block.span_id))
    index = blocks.index(protected)
    neighbour = next(block for block in reversed(blocks[:index]) if snapshot.policy.permitted("ext_book",
                                                                                                  block.span_id)
                     and block.text.strip())
    quote = neighbour.text.strip()[-30:] + " " + protected.text.strip()[:60]
    # No covered span named at all: the coverage proves nothing.
    question = B.freeze_context(B.BankQuestion("q1", "logged", None, "logged", "explain", "logged_reader",
                                               "Why does this follow?",
                                               selection=Selection("ext_book", neighbour.span_id, (), quote)),
                                snapshot)
    assert protected.text.strip()[:40] not in str(question.selected_passage)
    assert question.selection.quote is None
    delivered = deliver("D1", BlockSource(snapshot_sqlite(snapshot)), snapshot,
                        Selection("ext_book", neighbour.span_id, (), quote))
    assert all(span.get("relation") != "selected_text" for span in delivered.spans)
    assert any("coverage" in str(item.get("reason")) for item in delivered.receipt.get("policy_dropped", []))


# -- High 8: provider text never leaves an E0 path ----------------------------------------


def test_h8_an_error_body_echoing_the_key_never_reaches_logs_errors_or_the_cli(tmp_path, monkeypatch, caplog,
                                                                                 verified_prices):
    import traceback

    from typer.testing import CliRunner

    from learnloop.cli import app
    from tests.openai_fakes import install_fake_openai

    paths, _repository = build_e0_vault(tmp_path)
    handle = C.open_copy(paths.root)
    monkeypatch.setenv("OPENROUTER_API_KEY", KEY)
    install_fake_openai(monkeypatch, RuntimeError(f"401 invalid credentials: Bearer {KEY} was rejected"))
    caller = LiveRoleCaller(handle.root, handle.vault.config, E0Ledger(tmp_path / "ledger"),
                            checkpoints=Checkpoints(None))
    caplog.set_level(logging.DEBUG)
    with pytest.raises(_new("E0ProviderFailure")) as raised:
        caller.call("adjudicator", prompt="p", result_model=B.AdjudicatedLabels)
    text = "".join(traceback.format_exception(raised.value))
    assert KEY not in text and KEY not in str(raised.value) and KEY not in repr(raised.value)
    assert KEY not in caplog.text
    # The CLI prints a safe message only, whatever a run raises.
    from learnloop.experiments.contextual_embeddings import live, runner

    monkeypatch.setattr(runner, "dry_run", lambda *args, **kwargs: {"totals": {"fits_cap": True},
                                                                     "prices": {"unverified": {}}})

    def leak(*_args, **_kwargs):
        raise RuntimeError(f"provider said: invalid key {KEY}")

    monkeypatch.setattr(live, "run_live", leak)
    result = CliRunner().invoke(app, ["experiments", "e0", "run", "--copy", str(paths.root),
                                      "--i-am-authorized-to-spend", "--run-dir",
                                      str(tmp_path / "fixtures-local" / "runs")])
    assert result.exit_code == 1 and KEY not in result.output


# -- Medium 9: the canary checks the query contract, Qwen included ------------------------


def test_m9_a_broken_query_method_fails_the_canary_before_any_bulk_work(tmp_path, verified_prices):
    class BrokenQueries(FakeEmbeddingTransport):
        def post(self, url, *, headers, body, timeout):
            response = super().post(url, headers=headers, body=body, timeout=timeout)
            if body.get("input_type") == "query":
                return A.HttpResponse(200, {"data": [{"index": 0, "embedding": [1.0, 2.0]}]}, response.request_id)
            return response

    transport = BrokenQueries(dims=DIMS)
    adapter = _adapter("voyage_4_large", tmp_path, transport=transport)
    with pytest.raises(A.AdapterError):
        adapter.canary()
    documents = [request for request in transport.requests if request["body"].get("input_type") == "document"]
    assert len(documents) == 1  # the canary document only: no bulk work


def test_m9_the_qwen_route_is_canaried_before_its_service_backfill(tmp_path, verified_prices):
    from learnloop.experiments.contextual_embeddings.paid import PaidState, run_contracts

    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    qwen = FakeQwenClient()
    state = PaidState()
    run_contracts(snapshot, state, ledger=E0Ledger(tmp_path / "ledger"),
                  transport=FakeEmbeddingTransport(dims=DIMS, int8_models=INT8), receipts=A.Receipts(None),
                  store=A.VectorStore(None), qwen_client_factory=lambda: qwen, environ=FAKE_KEYS)
    assert state.contracts["R1"]["query_checked"] is True
    assert qwen.calls == [(1, "retrieval-document"), (1, "retrieval-query")]
    broken = FakeQwenClient()
    broken.model_id = "other/model"
    failed = PaidState()
    run_contracts(snapshot, failed, ledger=E0Ledger(tmp_path / "ledger2"),
                  transport=FakeEmbeddingTransport(dims=DIMS, int8_models=INT8), receipts=A.Receipts(None),
                  store=A.VectorStore(None), qwen_client_factory=lambda: broken, environ=FAKE_KEYS)
    assert {"R1", "R2", "R3", "R1_service_rrf", "R1_pool_verify"} <= failed.blocked_arms
    from learnloop.experiments.contextual_embeddings.system_arms import prepare_service_copies

    systems, report = prepare_service_copies(paths.root, tmp_path / "fixtures-local" / "svc",
                                             E0Ledger(tmp_path / "ledger3"), snapshot=snapshot,
                                             client_factory=lambda: broken, backfill=False)
    assert set(systems) == {"R0"} and report["qwen"]["how"] == "skipped" and broken.calls == []


# -- Medium 10: a Codex request allowance, a persisted clock ------------------------------


def test_m10_subscription_requests_are_bounded_by_a_persisted_allowance(tmp_path):
    ledger = E0Ledger(tmp_path / "ledger", max_subscription_requests=2)
    request = Request(category="labels_audits", provider="codex", route="gpt", purpose="x", billing="subscription")
    ledger.reserve(request)
    ledger.reserve(request)
    with pytest.raises(E0BudgetExceeded, match="subscription request allowance"):
        ledger.reserve(request)
    # Persisted: another process with the default allowance still holds the recorded one.
    with pytest.raises(E0BudgetExceeded, match="subscription request allowance 2"):
        E0Ledger(tmp_path / "ledger").reserve(request)
    assert ledger.report()["subscription_allowance"] == 2


def test_m10_a_resumed_process_keeps_the_run_clock(tmp_path):
    first = E0Ledger(tmp_path / "ledger")
    first.start_clock(100.0, wall=lambda: 1_000.0)
    resumed = E0Ledger(tmp_path / "ledger")
    resumed.start_clock(100.0, wall=lambda: 1_090.0)
    assert resumed.time_left() == pytest.approx(10.0, abs=1.0)


def test_m10_the_dry_run_reports_the_planned_codex_requests(tmp_path):
    from learnloop.experiments.contextual_embeddings.runner import dry_run

    paths, _repository = build_e0_vault(tmp_path)
    plan = dry_run([paths.root], environ={})
    codex = plan["subscription_requests"]
    # Re-plan 2026-10-22: no Codex request is planned, against a paid-run allowance of zero.
    assert codex["allowance"] == pins.PAID_RUN_SUBSCRIPTION_ALLOWANCE == 0
    assert codex["planned"] == sum(codex["roles"].values()) + sum(codex["system_arms"].values()) == 0


# -- Medium 11: execution state by complete request identity ------------------------------


def _live_caller(tmp_path, handle, client, *, ledger=None, records=None):
    return LiveRoleCaller(handle.root, handle.vault.config, ledger or E0Ledger(tmp_path / "ledger"),
                          checkpoints=Checkpoints(tmp_path / "fixtures-local" / "llm"),
                          client_factory=lambda _name: client, records=records)


def _writer_key(caller, prompt):
    from learnloop.experiments.contextual_embeddings.callers import checkpoint_key

    pin = pins.ROLE_PINS["writer"]
    client, identity = caller._client(pin)
    return checkpoint_key(pin, prompt, B.WrittenQuestions, identity=identity, output_bound=caller.output_bound(pin))


def test_m11_a_charged_but_unrecorded_request_is_blocked_never_resent(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    handle = C.open_copy(paths.root)
    client = FakeRoleClient("e0_anthropic_sonnet", respond=fake_respond)
    ledger = E0Ledger(tmp_path / "ledger")
    caller = _live_caller(tmp_path, handle, client, ledger=ledger)
    prompt = "prompt_version: e0-writer-v1\n{\"context\": {\"seeds\": []}}"
    key = _writer_key(caller, prompt)
    # A crash after the request was admitted and charged, before its checkpoint.
    ledger.reserve(Request(category="drafting_context", provider="codex_luna", route="gpt-6-luna",
                           purpose="writer:e0_writer", billing="subscription", request_key=key))
    with pytest.raises(_new("E0RequestBlocked")):
        caller.call("writer", prompt=prompt, result_model=B.WrittenQuestions)
    assert client.requests == []


def test_m11_a_settled_response_is_recovered_from_the_receipts(tmp_path):
    from learnloop.experiments.contextual_embeddings.records import ExperimentRecords

    paths, _repository = build_e0_vault(tmp_path)
    handle = C.open_copy(paths.root)
    records = ExperimentRecords(tmp_path / "fixtures-local" / "records")
    client = FakeRoleClient("e0_anthropic_sonnet", respond=fake_respond)
    ledger = E0Ledger(tmp_path / "ledger")
    caller = _live_caller(tmp_path, handle, client, ledger=ledger, records=records)
    prompt = "a writer prompt recovered after a crash"
    key = _writer_key(caller, prompt)
    ledger.reserve(Request(category="drafting_context", provider="codex_luna", route="gpt-6-luna",
                           purpose="writer:e0_writer", billing="subscription", request_key=key))
    with records.repository.connection() as connection:
        connection.execute(
            "INSERT INTO model_call_receipts(id, owner_kind, owner_id, purpose, input_text, output_text, status, "
            "started_at) VALUES ('call_1', 'experiment_e0', 'e0:test', 'e0_writer', ?, ?, 'completed', '2026-10-21')",
            (prompt, json.dumps({"questions": []})))
        connection.commit()
    result = caller.call("writer", prompt=prompt, result_model=B.WrittenQuestions)
    assert result.questions == [] and client.requests == []
    assert caller.checkpoints.get(key)["recovered"] is True


def test_m11_concurrent_workers_send_one_request_and_a_known_failure_may_retry(tmp_path, monkeypatch):
    import os

    paths, _repository = build_e0_vault(tmp_path)
    handle = C.open_copy(paths.root)
    client = FakeRoleClient("e0_anthropic_sonnet", respond=fake_respond)
    ledger = E0Ledger(tmp_path / "ledger")
    prompt = "prompt_version: e0-writer-v1\n{\"context\": {\"seeds\": []}}"
    callers = [_live_caller(tmp_path, handle, client, ledger=ledger) for _ in range(4)]
    synced = []
    real_fsync = os.fsync
    monkeypatch.setattr(os, "fsync", lambda fd: (synced.append(fd), real_fsync(fd))[1])
    threads = [threading.Thread(target=caller.call, args=("writer",),
                                kwargs={"prompt": prompt, "result_model": B.WrittenQuestions}) for caller in callers]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(client.requests) == 1  # one claim per complete request identity
    assert synced  # the checkpoint is durable
    # A request whose earlier attempt is recorded as failed may be sent again.
    failing = FakeRoleClient("e0_anthropic_sonnet", respond=lambda *_args: (_ for _ in ()).throw(RuntimeError("down")))
    other = _live_caller(tmp_path / "second", handle, failing)
    with pytest.raises(_new("E0ProviderFailure")):
        other.call("writer", prompt=prompt, result_model=B.WrittenQuestions)
    recovered = FakeRoleClient("e0_anthropic_sonnet", respond=fake_respond)
    retry = _live_caller(tmp_path / "second", handle, recovered, ledger=other.ledger)
    retry.call("writer", prompt=prompt, result_model=B.WrittenQuestions)
    assert len(recovered.requests) == 1


# -- Medium 12: failures are normalized and always reported -------------------------------


def test_m12_a_provider_failure_records_incomplete_work_instead_of_aborting(tmp_path, verified_prices):
    def respond(role, prompt, model):
        if role == "adjudicator":
            raise _new("E0ProviderFailure")("unavailable", status_code=503)
        return fake_respond(role, prompt, model)

    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    ledger = E0Ledger(tmp_path / "ledger")
    result = run_paid(snapshot, ledger=ledger, caller=FakeRoleCaller(respond, ledger), run_dir=None,
                      transport=FakeEmbeddingTransport(dims=DIMS, int8_models=INT8),
                      qwen_client_factory=FakeQwenClient, strata=STRATA, environ=FAKE_KEYS)
    assert result["status"] == "incomplete"
    assert str(result["incomplete_reason"]).startswith("provider")
    assert result["planned"]["missing"].get("mandatory_audits_missing")


def test_m12_an_unexpected_failure_still_writes_the_aggregate_report(tmp_path, monkeypatch, verified_prices):
    from learnloop.experiments.contextual_embeddings import live
    from learnloop.experiments.contextual_embeddings.runner import dry_run

    paths, _repository = build_e0_vault(tmp_path, manual_ai=True)
    plan = dry_run([paths.root], environ=FAKE_KEYS)

    def boom(*_args, **_kwargs):
        raise RuntimeError(f"stack trace with {KEY}")

    monkeypatch.setattr(live, "run_paid", boom)
    from tests.e0_fakes import qwen_bag_of_words

    qwen = qwen_bag_of_words(4096)
    factories = live.LiveFactories(transport=FakeEmbeddingTransport(dims=DIMS, int8_models=INT8),
                                   qwen=lambda _config: (lambda: qwen), role_clients=lambda name: FakeRoleClient(name))
    run_dir = tmp_path / "fixtures-local" / "runs"
    results = live.run_live([paths.root], plan=plan, run_dir=run_dir, key_envs={}, factories=factories)
    written = json.loads((run_dir / plan["run_id"] / paths.root.name / "results.json").read_text(encoding="utf-8"))
    assert results["status"] == "incomplete" and written["status"] == "incomplete"
    assert written["failures"][0]["kind"] == "failure_unknown" and KEY not in json.dumps(written)
    assert (run_dir / plan["run_id"] / paths.root.name / "report.md").is_file()


# -- Medium 13: coverage of every required slice ------------------------------------------


def test_m13_an_arm_that_fails_every_logged_question_stops_verdicts(tmp_path, monkeypatch, verified_prices):
    from learnloop.experiments.contextual_embeddings import paid

    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    logged = [B.BankQuestion("ql_1", "logged", None, "logged", "explain", "logged_library",
                             "What are the axioms of a vector space and why is the identity unique?",
                             ("real",), vault=snapshot.vault_label)]
    original = paid.rank_arm

    def drop_logged(arm, snapshot_, questions, adapter, **kwargs):
        ranked = original(arm, snapshot_, questions, adapter, **kwargs)
        if arm == "R4_grouped":
            ranked = {key: value for key, value in ranked.items() if not key.startswith("ql_")}
        return ranked

    monkeypatch.setattr(paid, "rank_arm", drop_logged)
    ledger = E0Ledger(tmp_path / "ledger")
    result = run_paid(snapshot, ledger=ledger, caller=FakeRoleCaller(fake_respond, ledger), run_dir=None,
                      transport=FakeEmbeddingTransport(dims=DIMS, int8_models=INT8),
                      qwen_client_factory=FakeQwenClient, strata=STRATA, environ=FAKE_KEYS, logged=logged)
    assert result["slice_completion"]["logged"]["R4_grouped"] == 0.0
    assert result["decisions"]["S1"]["decision"] == "stop_verdicts"
    assert any("R4_grouped@logged" in reason for reason in result["decisions"]["S1"]["reasons"])
    assert result["status"] == "incomplete"


# -- Medium 14: S4's families come from its paired evidence -------------------------------


def test_m14_s4_counts_only_the_paired_evidence_families_and_honours_exploratory():
    from learnloop.experiments.contextual_embeddings.metrics import paired_bootstrap
    from learnloop.experiments.contextual_embeddings.stop_rules import s4

    rows = [{"family": "fam_a", "a": 0.0, "b": 1.0}, {"family": None, "a": 0.0, "b": 1.0},
            {"family": "fam_b", "a": 0.0, "b": None}]  # fam_b is not complete-case evidence
    result = paired_bootstrap(rows, a="a", b="b", resamples=50)
    assert result["families"] == 1 and result["clusters"] == 2 and result["exploratory"] is True
    strong = {"difference": 0.2, "ci95": [0.1, 0.3]}
    decided = s4(finalist_vs_one_model=strong, answer_gain={"difference": 0.1}, latency_ok=True,
                 independent_families=6, exploratory=True)
    assert decided["decision"] == "defer_e1_underpowered"
    assert s4(finalist_vs_one_model=strong, answer_gain={"difference": 0.1}, latency_ok=True,
              independent_families=6, exploratory=False)["decision"] == "consider_e1"
