"""Regressions for the Codex review of the E0 harness (F1-F18), fakes only.

Each test names its finding. Every one runs offline: hash-vector embeddings,
fake role clients, the fake ``openai`` module; a socket guard refuses any
connection. The CLI test runs the paid command from a directory outside any
vault, with the live factories replaced by fakes."""
from __future__ import annotations

import json
import socket

import pytest

from learnloop.experiments.contextual_embeddings import bank as B
from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.adapters import (
    AdapterError,
    Chunk,
    Document,
    PreparedQuery,
    StoreCorrupt,
    VectorStore,
    VoyageIndependentAdapter,
    decode,
)
from learnloop.experiments.contextual_embeddings.answers import ScoredAnswer, judge_prompt, tutor_prompt, TutorAnswer
from learnloop.experiments.contextual_embeddings.budget import E0Ledger
from learnloop.experiments.contextual_embeddings.callers import (
    Checkpoints,
    FakeRoleCaller,
    LiveRoleCaller,
    PinMismatch,
    with_experiment_profiles,
)
from learnloop.experiments.contextual_embeddings.delivery import Delivered, Selection
from learnloop.experiments.contextual_embeddings.paid import latency_check, pick_finalists, run_paid, slice_summaries
from learnloop.experiments.contextual_embeddings.records import ExperimentRecords
from tests.embedding_fakes import BagOfWordsEmbedder
from tests.e0_fakes import (
    EXAM,
    FAKE_KEYS,
    FakeEmbeddingTransport,
    FakeQwenClient,
    FakeRoleClient,
    build_e0_vault,
    fake_respond,
    qwen_bag_of_words,
)

from tests.e0_fakes import verified_prices  # noqa: F401 - the fixture below

#: Every metered pin priced as verified (E0 admission refuses unverified prices; fix round 4).
pytestmark = pytest.mark.usefixtures("verified_prices")


DIMS = {pin.model: pin.dimensions for pin in pins.EMBEDDING_PINS.values()}
INT8 = frozenset({"pplx-embed-context-v1-4b", "pplx-embed-v1-4b"})
STRATA = {"reader_deictic": 2, "distant_same_source": 1, "direct_lookup": 1, "no_support": 1, "intent_explain": 1}
PROTECTED = ("Solution: apply linearity", "Exam question 1", "Midterm problems")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("network attempted in an offline E0 test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def _snapshot(tmp_path, name="e0vault", **kwargs):
    paths, repository = build_e0_vault(tmp_path, name, manual_ai=kwargs.pop("manual_ai", False))
    return C.build_snapshot(C.open_copy(paths.root), **kwargs), paths


class RejectingQwen(BagOfWordsEmbedder):
    """A Qwen stand-in that fails the test if any protected text reaches it."""

    def __init__(self) -> None:
        super().__init__(dims=4096)
        self.texts: list[str] = []

    def embed(self, inputs, task_prefix):
        for text in inputs:
            assert not any(marker in str(text) for marker in PROTECTED), "protected text reached the embedder"
            self.texts.append(str(text))
        return super().embed(inputs, task_prefix)


# -- F1 -------------------------------------------------------------------------------------


def test_f1_service_copy_preparation_never_sends_protected_text(tmp_path):
    from learnloop.experiments.contextual_embeddings.system_arms import prepare_service_copies

    snapshot, paths = _snapshot(tmp_path, manual_ai=True)
    assert any(snapshot.policy.verdict(*key) for key in [(e, b.span_id) for e, bs in snapshot.blocks.items()
                                                         for b in bs])
    qwen = RejectingQwen()
    ledger = E0Ledger(tmp_path / "ledger")
    handles, report = prepare_service_copies(paths.root, tmp_path / "fixtures-local" / "service", ledger,
                                             snapshot=snapshot, client_factory=lambda: qwen)
    assert report["r0"]["redaction"]["blanked_blocks"] > 0
    assert qwen.texts and not any(marker in text for text in qwen.texts for marker in PROTECTED)
    from contextlib import closing

    from learnloop.db.connection import connect

    for key in ("R0", "R1_service"):
        with closing(connect(handles[key].sqlite_path, read_only=True)) as connection:
            texts = [row[0] for row in connection.execute("SELECT text FROM source_document_blocks")]
        assert not any(marker in (text or "") for text in texts for marker in PROTECTED), key


def test_f1_the_guard_refuses_a_batch_carrying_protected_text(tmp_path):
    from learnloop.experiments.contextual_embeddings.system_arms import ProtectedTextRefused, guarded_factory

    snapshot, _paths = _snapshot(tmp_path)
    inner = FakeQwenClient()
    client = guarded_factory(lambda: inner, snapshot)()
    client.embed(["Definition 1.1 (Vector space). A vector space is a set V"], "retrieval-document")
    with pytest.raises(ProtectedTextRefused):
        client.embed(["Section: Chapter 2\n" + EXAM], "retrieval-document")
    assert len(inner.calls) == 1


# -- F2 -------------------------------------------------------------------------------------


def test_f2_a_metered_request_is_sent_and_reserved_at_the_output_budget_policy(tmp_path, monkeypatch):
    from learnloop.ai.output_budget import output_budget
    from learnloop.ai.providers.openrouter import OpenRouterProviderClient
    from tests.openai_fakes import install_fake_openai

    fake = install_fake_openai(monkeypatch, json.dumps({"labels": [], "sufficient_sets": [], "answerable": False,
                                                        "unresolved": True}))
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-not-real")
    paths, _repository = build_e0_vault(tmp_path)
    handle = C.open_copy(paths.root)
    config = with_experiment_profiles(handle.vault.config)
    ledger = E0Ledger(tmp_path / "ledger")
    caller = LiveRoleCaller(handle.root, handle.vault.config, ledger, checkpoints=Checkpoints(None),
                            client_factory=lambda name: OpenRouterProviderClient(name, config.ai.providers[name]))
    caller.call("adjudicator", prompt="adjudicate this", result_model=B.AdjudicatedLabels)
    bound = output_budget(config, None, provider="e0_openrouter_sonnet")
    assert bound == 16_384  # the normal policy, never the pin's lower expectation
    sent = fake.instances[0].requests[0]
    assert sent["max_tokens"] == bound
    entry = next(iter(json.loads((tmp_path / "ledger" / "e0_spend_ledger.json").read_text())["entries"].values()))
    assert entry["estimated_tokens"] >= bound  # reserved at the bound actually sent


# -- F3 -------------------------------------------------------------------------------------


def test_f3_a_resolved_client_that_differs_from_its_pin_is_refused_before_any_request(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    handle = C.open_copy(paths.root)
    ledger = E0Ledger(tmp_path / "ledger")
    cases = [FakeRoleClient("codex_luna", provider_type="openrouter",  # codex_luna overridden with a metered route
                            base_url="https://openrouter.ai/api/v1"),
             FakeRoleClient("codex_luna", model="gpt-4.1-mini"),  # another model
             FakeRoleClient("e0_openrouter_sonnet", base_url="https://example.invalid/v1")]  # another endpoint
    for client in cases:
        role = "writer" if client.provider_name == "codex_luna" else "adjudicator"
        caller = LiveRoleCaller(handle.root, handle.vault.config, ledger, checkpoints=Checkpoints(None),
                                client_factory=lambda _name, client=client: client)
        with pytest.raises(PinMismatch):
            caller.call(role, prompt="x", result_model=B.WrittenQuestions)
        assert client.requests == []
    assert ledger.report()["requests"] == 0
    changed = handle.vault.config.ai.model_copy(update={"providers": {
        **handle.vault.config.ai.providers,
        "e0_openrouter_sonnet": with_experiment_profiles(handle.vault.config).ai.providers[
            "e0_openrouter_sonnet"].model_copy(update={"model": "other/model"})}})
    with pytest.raises(PinMismatch, match="differently"):
        with_experiment_profiles(handle.vault.config.model_copy(update={"ai": changed}))


def test_f3_a_changed_identity_never_reuses_a_checkpoint():
    from learnloop.experiments.contextual_embeddings.callers import checkpoint_key

    pin = pins.ROLE_PINS["writer"]
    one = checkpoint_key(pin, "p", B.WrittenQuestions, identity={"model": "gpt-6-luna"}, output_bound=16_384)
    two = checkpoint_key(pin, "p", B.WrittenQuestions, identity={"model": "gpt-6-luna-2"}, output_bound=16_384)
    three = checkpoint_key(pin, "p", B.WrittenQuestions, identity={"model": "gpt-6-luna"}, output_bound=8_192)
    assert len({one, two, three}) == 3


# -- F4 and F11: the paid CLI, from outside any vault, twice ---------------------------------


def test_f4_f11_the_paid_cli_keeps_receipts_in_its_own_repository_and_resumes(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from learnloop.cli import app
    from learnloop.experiments.contextual_embeddings import live

    paths, _repository = build_e0_vault(tmp_path, manual_ai=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)
    for name, value in FAKE_KEYS.items():
        monkeypatch.setenv(name, value)
    transports = []

    def factories():
        transport = FakeEmbeddingTransport(dims=DIMS, int8_models=INT8)
        transports.append(transport)
        qwen = qwen_bag_of_words(4096)
        return live.LiveFactories(transport=transport, qwen=lambda _config: (lambda: qwen),
                                  role_clients=lambda name: FakeRoleClient(name),
                                  system_clients={"embedder": qwen})

    monkeypatch.setattr(live, "default_factories", factories)
    run_dir = tmp_path / "fixtures-local" / "contextual-embeddings" / "runs"
    command = ["experiments", "e0", "run", "--copy", str(paths.root), "--run-dir", str(run_dir),
               "--i-am-authorized-to-spend", "--json"]
    first = CliRunner().invoke(app, command)
    assert first.exit_code == 0, first.output
    assert not (outside / "learnloop.toml").exists()
    result = json.loads(first.output.strip().splitlines()[-1])
    outcome = result["vaults"][paths.root.name]
    assert outcome["records"]["receipts"] > 0 and outcome["records"]["judgments"] > 0
    assert outcome["service_preparation"]["r0"]["how"] == "prepared"
    second = CliRunner().invoke(app, command)
    assert second.exit_code == 0, second.output
    again = json.loads(second.output.strip().splitlines()[-1])["vaults"][paths.root.name]
    assert again["service_preparation"]["r0"]["how"] == "reopened"
    assert again["service_preparation"]["qwen"]["how"] == "reopened"
    documents = [request for request in transports[-1].requests
                 if request["body"].get("input_type") == "document" and "vector space is a set with" not in
                 json.dumps(request["body"])]
    assert documents == []  # resumed: no document re-sent
    assert again["records"]["judgments"] == outcome["records"]["judgments"]  # appended once


# -- F5 -------------------------------------------------------------------------------------


def test_f5_the_paid_run_executes_the_frozen_split_or_refuses(tmp_path):
    from learnloop.experiments.contextual_embeddings.live import PlanMismatch, rebuild_frozen
    from learnloop.experiments.contextual_embeddings.runner import dry_run

    paths, _repository = build_e0_vault(tmp_path)
    plan = dry_run([paths.root], reserve_share=0.5, environ={})
    assert plan["reserve_share"] == 0.5 and "reserved" in plan["splits"][paths.root.name].values()
    _handles, snapshots, strata = rebuild_frozen([paths.root], plan)
    assert snapshots[0].family_status == plan["splits"][paths.root.name]
    assert strata[paths.root.name] == plan["bank"]["vaults"][paths.root.name]["development_strata"]
    with pytest.raises(PlanMismatch):
        rebuild_frozen([paths.root], {**plan, "reserve_share": 0.0})
    with pytest.raises(PlanMismatch, match="predates"):
        rebuild_frozen([paths.root], {key: value for key, value in plan.items() if key != "reserve_share"})


# -- F6 -------------------------------------------------------------------------------------


def test_f6_deictic_questions_carry_their_own_selection_to_every_role(tmp_path):
    snapshot, _paths = _snapshot(tmp_path)
    units = [unit for unit in snapshot.units if unit.extraction_id == "ext_book" and unit.tokens >= 12][:2]
    questions = [B.BankQuestion(f"q{index}", "development", None, "writer", "explain", "reader_deictic",
                                "Why does this step follow?", selection=Selection(unit.extraction_id,
                                                                                  unit.members[0].span_id))
                 for index, unit in enumerate(units)]
    for question in questions:
        B.freeze_context(question, snapshot)
    first, second = questions
    assert first.selected_passage and first.selected_passage != second.selected_passage
    delivered = Delivered("D1", [{"extraction_id": "x", "span_id": "s", "text": "a passage", "relation": "x"}])
    answer = TutorAnswer(answer="because", cited_refs=["r1"], abstained=False)
    for question in questions:
        passage = question.selected_passage
        candidates = {"c1": {"section": "", "within": None, "text": "t"}}
        assert passage in question.retrieval_query
        assert passage in B.label_prompt(question, candidates, 0)
        assert passage in B.sufficiency_prompt(question, candidates, 0)
        assert passage in tutor_prompt(question, delivered)[0]
        assert passage in judge_prompt(question, delivered, answer, order_salt=0)
    with pytest.raises(RuntimeError):
        B.BankQuestion("q9", "development", None, "writer", "explain", "x", "unfrozen").context()


def test_f6_a_quote_over_withheld_spans_falls_back_to_the_selected_block(tmp_path):
    snapshot, _paths = _snapshot(tmp_path)
    withheld = next(block.span_id for block in snapshot.blocks["ext_book"]
                    if snapshot.policy.verdict("ext_book", block.span_id))
    permitted = next(unit for unit in snapshot.units if unit.extraction_id == "ext_book")
    question = B.BankQuestion("q1", "logged", None, "logged", "explain", "logged_reader", "Why?",
                              selection=Selection("ext_book", permitted.members[0].span_id, (withheld,),
                                                  "Solution: apply linearity to 0 = 0 + 0"))
    B.freeze_context(question, snapshot)
    assert "Solution" not in question.selected_passage


# -- F7 -------------------------------------------------------------------------------------


def _labels(pool):
    return B.QuestionLabels("q1", list(pool), [{unit: "required" for unit in pool}, {unit: "helpful" for unit in pool}],
                            [[frozenset(pool[:2])], []], [True, False])


@pytest.mark.parametrize("sets, labels, answerable, problem", [
    ([["c1", "c999"]], None, True, "unknown_ref_in_set"),
    ([["c1", "c1"]], None, True, "duplicate_ref_in_set"),
    ([["c1"]], "drop", True, "disputed_candidate_unlabelled"),
    ([], None, True, "answerable_without_a_set"),
    ([["c1"]], None, False, "unanswerable_with_a_set"),
])
def test_f7_a_malformed_adjudication_leaves_sufficiency_unresolved(tmp_path, sets, labels, answerable, problem):
    snapshot, _paths = _snapshot(tmp_path)
    pool = [unit.unit_id for unit in snapshot.units][:3]
    question = B.freeze_context(B.BankQuestion("q1", "development", None, "writer", "explain", "intent_explain",
                                               "Why does a linear map preserve zero?"), snapshot)

    def respond(role, prompt, _model):
        context = json.loads(prompt[prompt.index("{"):])["context"]
        refs = [candidate["ref"] for candidate in context["candidates"]]
        given = [{"ref": ref, "relevance": "required"} for ref in refs]
        if labels == "drop":
            given = given[1:]
        return {"labels": given, "sufficient_sets": sets, "answerable": answerable, "unresolved": False}

    result = B.adjudicate(question, _labels(pool), snapshot, FakeRoleCaller(respond))
    assert result.unresolved and result.final_sets == [] and problem in result.problems
    assert B.evidence_sets_from_labels(result, snapshot) == []


# -- F8 -------------------------------------------------------------------------------------


def test_f8_a_bounded_fallback_keeps_its_name_and_never_enters_the_whole_context_pairs(tmp_path, monkeypatch):
    monkeypatch.setattr(pins, "GENERATOR_CONTEXT_TOKENS", sum(pins.GENERATOR_RESERVES.values()) + 1)
    snapshot, _paths = _snapshot(tmp_path)
    ledger = E0Ledger(tmp_path / "ledger")
    result = run_paid(snapshot, ledger=ledger, caller=FakeRoleCaller(fake_respond, ledger), run_dir=None,
                      transport=FakeEmbeddingTransport(dims=DIMS, int8_models=INT8),
                      qwen_client_factory=lambda: FakeQwenClient(), strata=STRATA, environ=FAKE_KEYS)
    assert result["delivery"]["does_not_fit"]["D3"] > 0 and result["delivery"]["does_not_fit"]["D2"] > 0
    assert result["answers"]["D3"]["n"] == 0 and result["answers"]["D3"]["missing"] > 0
    assert any(arm.startswith("D3_fallback_") for arm in result["answers"])
    assert result["delivery"]["D3"]["n"] == 0  # no fallback answer paired as a whole-source result
    from learnloop.experiments.contextual_embeddings.report import render

    assert "does_not_fit" in render(result)


# -- F9 -------------------------------------------------------------------------------------


def _answer(query_id, arm, latency):
    return ScoredAnswer(query_id, arm, [], final={"correct": "pass"}, latency_s=latency)


def test_f9_latency_needs_the_deadline_and_no_paired_regression_against_the_incumbent():
    incumbent = [_answer(f"q{index}", "R1:D1", 1.0) for index in range(10)]
    slow = [_answer(f"q{index}", "R4_grouped:D1", 1.0 + 20.0) for index in range(10)]
    fast = [_answer(f"q{index}", "R4_grouped:D1", 1.05) for index in range(10)]
    regressed = latency_check(incumbent + slow, "R4_grouped:D1", "R1:D1", 60.0)
    assert regressed["fits_deadline"] and regressed["regression"] and regressed["ok"] is False
    assert latency_check(incumbent + fast, "R4_grouped:D1", "R1:D1", 60.0)["ok"] is True
    assert latency_check(incumbent + fast, "R4_grouped:D1", "R1:D1", 0.5)["ok"] is False
    assert latency_check(incumbent + fast, "R4_grouped:D1", "R1:D1", None)["ok"] is None


def test_f9_finalist_latency_includes_a_fresh_online_query_and_the_search(tmp_path):
    snapshot, _paths = _snapshot(tmp_path)
    ledger = E0Ledger(tmp_path / "ledger")
    qwen = FakeQwenClient()
    result = run_paid(snapshot, ledger=ledger, caller=FakeRoleCaller(fake_respond, ledger),
                      run_dir=tmp_path / "fixtures-local" / "run",
                      transport=FakeEmbeddingTransport(dims=DIMS, int8_models=INT8),
                      qwen_client_factory=lambda: qwen, strata=STRATA, environ=FAKE_KEYS, latency_budget_s=60.0)
    one_model = result["finalists"]["one_model"]
    assert one_model in ("R1", "R2", "R3")
    queries = [count for count, task in qwen.calls if task == "retrieval-query"]
    assert queries.count(1) >= result["planned"]["questions"]  # one fresh online query per question
    check = result["latency_checks"]["finalist_vs_incumbent"]
    assert check["incumbent"] == f"{one_model}:D1" and check["paired"] > 0


# -- F10 ------------------------------------------------------------------------------------


def test_f10_verdicts_enter_judgment_ledger_once(tmp_path):
    from learnloop.experiments.contextual_embeddings.answers import answer_and_judge

    snapshot, _paths = _snapshot(tmp_path)
    records = ExperimentRecords(tmp_path / "fixtures-local" / "records")
    caller = FakeRoleCaller(fake_respond, records=records)
    question = B.freeze_context(B.BankQuestion("q1", "development", None, "writer", "explain", "intent_explain",
                                               "Why does a linear map send the additive identity to the identity?"),
                                snapshot)
    pool = [unit.unit_id for unit in snapshot.units][:6]
    for _ in range(2):  # a resume appends nothing twice
        labels = B.label_question(question, pool, snapshot, caller)
        B.adjudicate(question, labels, snapshot, caller)
        delivered = Delivered("D1", [{"extraction_id": "ext_book", "span_id": "s2", "text": "t", "relation": "x"}])
        answer_and_judge(question, "D1", delivered, caller)
    tasks = {row["task"] for row in records.judgments()}
    assert tasks == {"e0_label", "e0_label_sets", "e0_label_adjudication", "e0_answer_judgement"}
    rows = records.judgments("e0_label")
    assert len(rows) == 2 * len(pool)  # two passes, once each
    assert all(row["judge_model"] and row["prompt_version"] and row["input_hash"] for row in rows)
    assert all("spans" in json.loads(row["rationale"]) for row in rows)


# -- F11 ------------------------------------------------------------------------------------


def test_f11_an_interrupted_service_copy_is_set_aside_and_prepared_again(tmp_path):
    from learnloop.experiments.contextual_embeddings.system_arms import SERVICE_STATE, prepare_service_copies

    snapshot, paths = _snapshot(tmp_path, manual_ai=True)
    service = tmp_path / "fixtures-local" / "service"
    ledger = E0Ledger(tmp_path / "ledger")
    _handles, report = prepare_service_copies(paths.root, service, ledger, snapshot=snapshot,
                                              client_factory=lambda: BagOfWordsEmbedder(dims=4096))
    assert report["r0"]["how"] == "prepared"
    state = json.loads((service / SERVICE_STATE).read_text())
    state["qwen"]["status"] = "copying"  # as if interrupted mid-preparation
    (service / SERVICE_STATE).write_text(json.dumps(state))
    _handles, again = prepare_service_copies(paths.root, service, ledger, snapshot=snapshot,
                                             client_factory=lambda: BagOfWordsEmbedder(dims=4096))
    assert again["r0"]["how"] == "reopened" and again["qwen"]["how"] == "prepared"
    assert any(path.name.startswith(".qwen.stale-") for path in service.iterdir())


# -- F12 ------------------------------------------------------------------------------------


def test_f12_system_arms_use_find_sources_and_an_unverified_intent_is_no_ranking(tmp_path):
    from learnloop.experiments.contextual_embeddings.system_arms import make_service_copy, open_service, rank_system

    snapshot, paths = _snapshot(tmp_path, manual_ai=True)
    handle = open_service(make_service_copy(paths.root, tmp_path / "fixtures-local" / "service" / "r0"))
    explain = B.freeze_context(B.BankQuestion("q1", "development", None, "writer", "explain", "intent_explain",
                                              "Why is the additive identity unique?"), snapshot)
    remediate = B.freeze_context(B.BankQuestion("q2", "development", None, "writer", "remediate",
                                                "intent_remediate", "I think the identity is not unique, why?"),
                                 snapshot)
    ledger = E0Ledger(tmp_path / "ledger")
    ranked, report = rank_system(handle, snapshot, [explain, remediate], arm="R0", ledger=ledger,
                                 query_text={"q1": explain.retrieval_query, "q2": remediate.retrieval_query})
    assert "q1" in ranked and "q2" not in ranked  # the mandatory verification could not run
    assert report["ranked"] == 1 and sum(report["missing"].values()) == 1
    assert any(key.startswith("verification_") for key in report["missing"])
    _ranked, verify = rank_system(handle, snapshot, [explain], arm="R1_pool_verify", ledger=ledger,
                                  query_text={"q1": explain.retrieval_query})
    assert verify["interface"] == "pool_verify" and verify["ranked"] == 0 and verify["missing"]


def test_f12_an_incompletely_covered_service_copy_blocks_the_qwen_system_arms(tmp_path):
    snapshot, _paths = _snapshot(tmp_path)
    ledger = E0Ledger(tmp_path / "ledger")
    result = run_paid(snapshot, ledger=ledger, caller=FakeRoleCaller(fake_respond, ledger), run_dir=None,
                      transport=FakeEmbeddingTransport(dims=DIMS, int8_models=INT8),
                      qwen_client_factory=lambda: FakeQwenClient(), strata=STRATA, environ=FAKE_KEYS,
                      system_handles={"R0": None, "R1_service": object()},
                      system_preparation={"qwen": {"coverage": {"complete": False}}})
    kinds = {(row["item"], row["kind"]) for row in result["failures"]}
    assert ("R1_service_rrf", "coverage_incomplete") in kinds and ("R1_pool_verify", "coverage_incomplete") in kinds
    assert result["status"] == "incomplete"


# -- F13 ------------------------------------------------------------------------------------


def test_f13_a_conjunction_split_across_batches_is_found_by_the_joint_review(tmp_path):
    snapshot, _paths = _snapshot(tmp_path)
    pool = [unit.unit_id for unit in snapshot.units][:6]
    needed = {pool[0], pool[5]}
    texts = {snapshot.unit(unit_id).text: unit_id for unit_id in pool}
    question = B.freeze_context(B.BankQuestion("q1", "development", None, "writer", "explain", "intent_explain",
                                               "A question needing two passages"), snapshot)

    def respond(_role, prompt, model):
        context = json.loads(prompt[prompt.index("{"):])["context"]
        refs = {candidate["ref"]: texts[candidate["text"]] for candidate in context["candidates"]}
        if model.__name__ == "SufficiencyPass":
            both = [ref for ref, unit in refs.items() if unit in needed]
            return {"sufficient_sets": [both] if len(both) == 2 else [], "answerable": len(both) == 2}
        labels = [{"ref": ref, "relevance": "required" if unit in needed else "unrelated"} for ref, unit in refs.items()]
        return {"labels": labels, "sufficient_sets": [], "answerable": False}

    labels = B.label_question(question, pool, snapshot, FakeRoleCaller(respond), batch=2)
    assert frozenset(needed) in labels.pass_sets[0] and frozenset(needed) in labels.pass_sets[1]
    assert labels.pass_answerable == [True, True]


# -- F14 ------------------------------------------------------------------------------------


def test_f14_a_run_past_its_wall_time_stops_cleanly_and_reports_incomplete(tmp_path):
    snapshot, _paths = _snapshot(tmp_path)
    ledger = E0Ledger(tmp_path / "ledger")
    now = [0.0]
    ledger.start_clock(10.0, clock=lambda: now[0])
    now[0] = 11.0
    result = run_paid(snapshot, ledger=ledger, caller=FakeRoleCaller(fake_respond, ledger), run_dir=None,
                      transport=FakeEmbeddingTransport(dims=DIMS, int8_models=INT8),
                      qwen_client_factory=lambda: FakeQwenClient(), strata=STRATA, environ=FAKE_KEYS)
    assert result["status"] == "incomplete" and "wall-time" in result["incomplete_reason"]
    assert result["decisions"]["S1"]["decision"] == "stop_verdicts"


# -- F15 ------------------------------------------------------------------------------------


def test_f15_provider_limits_use_a_guaranteed_upper_bound(tmp_path):
    dense = "∑∫∂√∞≈≠≤≥" * 40 + "{}[]()^_\\$" * 40
    assert pins.token_upper_bound(dense) >= len(dense.encode("utf-8"))
    assert pins.token_estimate(dense) < len(dense.encode("utf-8"))  # the estimate is not a bound
    pin = pins.EMBEDDING_PINS["voyage_4_large"]
    limited = type(pin)(**{**pin.as_dict(), "max_tokens_per_document": pins.token_estimate(dense) + 100})
    adapter = VoyageIndependentAdapter(limited, encoding="independent", recipe="plain",
                                       ledger=E0Ledger(tmp_path / "ledger"), arm="R5_independent",
                                       transport=FakeEmbeddingTransport(dims=DIMS), environ=FAKE_KEYS)
    with pytest.raises(AdapterError, match="limit"):
        adapter.encode_documents([Document("d", (Chunk("c", dense),), key="k")])
    with pytest.raises(AdapterError, match="limit"):
        adapter.encode_queries([PreparedQuery("q", dense)])
    snapshot, _paths = _snapshot(tmp_path)
    first = snapshot.units[0]
    units = [item for item in snapshot.units
             if (item.extraction_id, item.segment) == (first.extraction_id, first.segment)]
    bound = sum(pins.token_upper_bound(item.text) + pins.CHUNK_MARKER_TOKENS for item in units)
    estimate = sum(item.tokens + pins.CHUNK_MARKER_TOKENS for item in units)
    assert estimate < bound
    # Between the estimate and the bound: the estimate alone would have called it a fit.
    assert C.whole_segment_windows(units, limit_tokens=(bound + estimate) // 2) == []
    assert len(C.whole_segment_windows(units, limit_tokens=bound)) == 1


# -- F16 ------------------------------------------------------------------------------------


def test_f16_finalists_come_from_the_primary_development_slice_only():
    def row(index, split, stratum, r1, r2):
        return {"query_id": f"q{index}", "family": "f", "stratum": stratum, "split": split, "intent": "explain",
                "R1:ce10": r1, "R2:ce10": r2}

    rows = ([row(index, "development", "reader_deictic", 1.0, 0.0) for index in range(4)]
            + [row(10 + index, "logged", "logged_reader", 0.0, 1.0) for index in range(10)]
            + [row(30 + index, "development", "direct_lookup", 0.0, 1.0) for index in range(10)])
    slices = slice_summaries(rows, ["R1", "R2"])
    assert pick_finalists(slices["primary_development"])["one_model"] == "R1"
    from learnloop.experiments.contextual_embeddings.evaluate import arm_summary

    assert pick_finalists(arm_summary(rows, ["R1", "R2"]))["one_model"] == "R2"  # what mixing would have picked
    assert slices["logged"]["R2"]["ce10"] == 1.0 and slices["direct_lookup"]["R1"]["total"] == 10
    assert set(slices["by_stratum"]) == {"reader_deictic", "logged_reader", "direct_lookup"}


# -- F17 ------------------------------------------------------------------------------------


def test_f17_a_writer_that_omits_seeds_makes_the_run_incomplete_with_its_denominator(tmp_path):
    snapshot, _paths = _snapshot(tmp_path)
    ledger = E0Ledger(tmp_path / "ledger")

    def respond(role, prompt, model):
        value = fake_respond(role, prompt, model)
        if role == "writer":
            value["questions"] = value["questions"][:1]  # one question for a whole batch
        return value

    result = run_paid(snapshot, ledger=ledger, caller=FakeRoleCaller(respond, ledger), run_dir=None,
                      transport=FakeEmbeddingTransport(dims=DIMS, int8_models=INT8),
                      qwen_client_factory=lambda: FakeQwenClient(), strata=STRATA, environ=FAKE_KEYS)
    planned = result["planned"]
    assert planned["development_written"] < planned["development_seeds"]
    assert planned["missing"]["bank_missing"] == planned["development_seeds"] - planned["development_written"]
    assert result["status"] == "incomplete"
    assert any("planned work missing" in reason for reason in result["decisions"]["S1"]["reasons"])
    from learnloop.experiments.contextual_embeddings.report import render

    assert "bank_missing" in render(result)


def test_f17_an_answer_stop_keeps_the_planned_denominator(tmp_path):
    snapshot, _paths = _snapshot(tmp_path)
    allocation = {"embeddings": 2.0, "drafting_context": 5.0, "labels_audits": 10.0, "answers_verification": 0.0}
    ledger = E0Ledger(tmp_path / "ledger", cap_usd=17.0, allocation=allocation)
    roles = {**pins.ROLE_PINS, "tutor": pins.ROLE_PINS["judge_adjudicator"]}  # a metered tutor: no room
    result = run_paid(snapshot, ledger=ledger, caller=FakeRoleCaller(fake_respond, ledger, role_pins=roles),
                      run_dir=None, transport=FakeEmbeddingTransport(dims=DIMS, int8_models=INT8),
                      qwen_client_factory=lambda: FakeQwenClient(), strata=STRATA, environ=FAKE_KEYS)
    assert result["planned"]["answers_made"] == 0
    assert result["planned"]["missing"]["answers_missing"] == sum(result["planned"]["answers"].values()) > 0
    assert all(entry["missing"] == entry["planned"] for entry in result["answers"].values() if "planned" in entry)


# -- F18 ------------------------------------------------------------------------------------


def test_f18_a_torn_vector_append_is_recovered_and_raw_output_is_kept(tmp_path):
    store = VectorStore(tmp_path / "vectors")
    pin = pins.EMBEDDING_PINS["pplx_4b"]
    raw = [[1] * pin.dimensions]
    vectors = [decode(raw[0], pin).tolist()]
    store.put("space", "k1", vectors, raw=raw)
    path = tmp_path / "vectors" / "space.jsonl"
    with open(path, "a", encoding="utf-8") as handle:
        handle.write('{"key": "k2", "vectors": [[0.1, 0.2')  # a crash mid-append
    reopened = VectorStore(tmp_path / "vectors")
    assert reopened.get("space", "k1") == vectors and reopened.get("space", "k2") is None
    assert reopened.recovered["space"] > 0
    assert decode(reopened.get_raw("space", "k1")[0], pin).tolist() == vectors[0]  # decoding reproducible
    reopened.put("space", "k3", vectors, raw=raw)
    assert set(json.loads(line)["key"] for line in path.read_text().splitlines()) == {"k1", "k3"}
    lines = path.read_text().splitlines()
    damaged = json.loads(lines[0])
    damaged["vectors"][0][0] = 0.0
    path.write_text(json.dumps(damaged) + "\n" + lines[1] + "\n")
    with pytest.raises(StoreCorrupt):
        VectorStore(tmp_path / "vectors").get("space", "k1")


def test_f18_query_vectors_are_cached_and_not_repaid(tmp_path):
    transport = FakeEmbeddingTransport(dims=DIMS)
    store = VectorStore(tmp_path / "vectors")

    def adapter():
        return VoyageIndependentAdapter(pins.EMBEDDING_PINS["voyage_4_large"], encoding="independent",
                                        recipe="plain", ledger=E0Ledger(tmp_path / "ledger"), arm="R5_independent",
                                        transport=transport, store=VectorStore(tmp_path / "vectors"),
                                        environ=FAKE_KEYS)

    first = adapter().encode_queries([PreparedQuery("q1", "what is a basis"), PreparedQuery("q2", "span")])
    sent = len(transport.requests)
    second = adapter().encode_queries([PreparedQuery("q1", "what is a basis"), PreparedQuery("q2", "span")])
    assert second == first and len(transport.requests) == sent
    adapter().encode_queries([PreparedQuery("q1", "what is a basis")], fresh=True)
    assert len(transport.requests) == sent + 1
    del store


def test_f18_concurrent_writers_never_duplicate_a_key(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    stores = [VectorStore(tmp_path / "vectors") for _ in range(4)]

    def write(index):
        stores[index % 4].put("space", f"k{index % 10}", [[float(index)]])

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(write, range(80)))
    keys = [json.loads(line)["key"] for line in (tmp_path / "vectors" / "space.jsonl").read_text().splitlines()]
    assert sorted(keys) == sorted(f"k{index}" for index in range(10))


