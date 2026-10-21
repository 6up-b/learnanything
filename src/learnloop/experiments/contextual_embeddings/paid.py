"""The E0 paid run's steps (orchestrator-authorized, after review; never in this stage).

Order (spec §5, §6, §11): freeze -> contracts (one canary per hosted
adapter) -> bank (writer) -> R3 contexts -> encode and rank every arm ->
system arms on a separate service copy -> labels and adjudication -> score
and pick finalists on development -> delivery D0-D3 and the finalists' D1
answers -> judges -> S1-S4 -> report.

Every request is admitted by the one E0 ledger before it is sent. A refusal
(``E0BudgetExceeded``) or an endpoint/contract failure stops the affected
step: its arm is recorded as blocked with its original denominator and the
report is marked incomplete; no other model or recipe stands in for it.
Every step is resumable: vectors, checkpointed LLM results and the ledger are
keyed by complete input identity, so a rerun pays only for what is missing.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
import time
from typing import Any

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.adapters import (
    ADAPTERS,
    AdapterError,
    EmbeddingAdapter,
    PreparedQuery,
    QwenAdapter,
    Receipts,
    Transport,
    VectorStore,
    build_index,
)
from learnloop.experiments.contextual_embeddings.answers import ScoredAnswer, answer_and_judge, summarize_answers
from learnloop.experiments.contextual_embeddings.bank import (
    BankQuestion,
    QuestionLabels,
    accept_agreed,
    adjudicate,
    audit_plan,
    evidence_sets_from_labels,
    label_question,
    plan_seeds,
    pool_for,
    smoke_bank,
    write_questions,
)
from learnloop.experiments.contextual_embeddings.budget import E0BudgetExceeded, E0Ledger
from learnloop.experiments.contextual_embeddings.corpus import CorpusSnapshot
from learnloop.experiments.contextual_embeddings.delivery import (
    Delivered,
    deliver,
    retrieved_d1,
)
from learnloop.experiments.contextual_embeddings.evaluate import agreement, arm_summary, completion, paired, question_rows
from learnloop.experiments.contextual_embeddings.metrics import latency_summary
from learnloop.experiments.contextual_embeddings.retrieval import (
    BM25,
    documents_for,
    exact_search,
    generate_contexts,
    recipe_text,
)
from learnloop.experiments.contextual_embeddings.stop_rules import decide
from learnloop.tutor.context_delivery import BlockSource

QWEN_ARMS = ("R1", "R2", "R3")
HOSTED_FAMILIES = {"R4": ("R4_grouped", "R4_singleton", "R4_independent"),
                   "R5": ("R5_grouped", "R5_singleton", "R5_independent")}
SELECTION_CONTEXT_CHARS = 1200


@dataclass
class PaidState:
    """What a paid run has done (aggregates for the report, failures for the ledger)."""

    failures: list[dict[str, Any]] = field(default_factory=list)
    contracts: dict[str, Any] = field(default_factory=dict)
    blocked_arms: set[str] = field(default_factory=set)
    stopped: str | None = None

    def fail(self, item: str, kind: str, reason: str, denominator: Any = None) -> None:
        self.failures.append({"item": item, "kind": kind, "reason": reason, "denominator": denominator})


def effective_query(question: BankQuestion, snapshot: CorpusSnapshot) -> str:
    """The complete query every arm encodes: the question, and for a known
    selection its in-view passage (the Reader's actual context), never an
    oracle location for a library question."""

    if question.selection is None:
        return question.effective_query
    block = next((block for block in snapshot.blocks.get(question.selection.extraction_id, [])
                  if block.span_id == question.selection.span_id), None)
    passage = question.selection.quote or (block.text if block is not None else "")
    passage = " ".join(passage.split())[:SELECTION_CONTEXT_CHARS]
    return f"{question.effective_query}\n\nSelected passage: {passage}" if passage else question.effective_query


def allowed_units(question: BankQuestion, snapshot: CorpusSnapshot) -> set[str]:
    if question.scope.startswith("extraction:"):
        extraction_id = question.scope.split(":", 1)[1]
        return {unit.unit_id for unit in snapshot.units if unit.extraction_id == extraction_id}
    return {unit.unit_id for unit in snapshot.units}


def make_adapter(arm: str, snapshot: CorpusSnapshot, *, ledger: E0Ledger, transport: Transport | None,
                 receipts: Receipts, store: VectorStore, qwen_client_factory: Callable[[], Any] | None,
                 key_envs: Mapping[str, str] | None = None, environ: Mapping[str, str] | None = None) -> EmbeddingAdapter:
    spec = pins.RETRIEVAL_ARMS[arm]
    pin = pins.EMBEDDING_PINS[spec.embedding]
    revisions = sorted(f"{info.extractor}/{info.extractor_version}/{info.extraction_id}"
                       for info in snapshot.infos.values())
    key_env = (key_envs or {}).get(pin.provider, pin.key_env)
    if pin.provider == "openrouter":
        if qwen_client_factory is None:
            raise AdapterError("no Qwen client factory", kind="auth")
        return QwenAdapter(pin, client_factory=qwen_client_factory, recipe=spec.recipe, ledger=ledger, arm=arm,
                           extraction_revisions=revisions, receipts=receipts, store=store, key_env=key_env,
                           environ=environ)
    return ADAPTERS[pin.name](pin, encoding=spec.encoding, recipe=spec.recipe, ledger=ledger, arm=arm,
                              extraction_revisions=revisions, transport=transport, receipts=receipts, store=store,
                              key_env=key_env, environ=environ)


def run_contracts(snapshot: CorpusSnapshot, state: PaidState, **adapter_kwargs: Any) -> dict[str, Any]:
    """One canary per hosted adapter; a failing one blocks its arms."""

    for arm in ("R4_grouped", "R4_singleton", "R4_independent", "R5_grouped", "R5_singleton", "R5_independent"):
        try:
            adapter = make_adapter(arm, snapshot, **adapter_kwargs)
            state.contracts[arm] = adapter.canary()
        except E0BudgetExceeded as exc:
            state.blocked_arms.add(arm)
            state.fail(arm, "budget", str(exc))
        except AdapterError as exc:
            state.blocked_arms.add(arm)
            state.contracts[arm] = {"status": "failed", "kind": exc.kind}
            state.fail(arm, f"contract_{exc.kind}", str(exc))
    return state.contracts


def rank_arm(arm: str, snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], adapter: EmbeddingAdapter, *,
             headers: Mapping[str, str] | None = None, top: int = pins.POOL_DEPTH) -> dict[str, list[str]]:
    spec = pins.RETRIEVAL_ARMS[arm]
    documents, chunk_unit = documents_for(snapshot, spec.encoding, spec.recipe, adapter.document_space_id, headers)
    vectors = adapter.encode_documents(documents)
    entries = []
    for document, document_vectors in zip(documents, vectors, strict=True):
        for chunk, vector in zip(document.chunks, document_vectors, strict=True):
            entries.append((chunk_unit[chunk.chunk_id], adapter.document_space_id, adapter.query_encoder_id, vector))
    index = build_index(entries)
    queries = [PreparedQuery(question.query_id, effective_query(question, snapshot)) for question in questions]
    query_vectors = adapter.encode_queries(queries)
    ranked = {}
    for question, vector in zip(questions, query_vectors, strict=True):
        hits = exact_search(index, vector, query_encoder=adapter.query_encoder_id, top_k=top,
                            allowed=allowed_units(question, snapshot))
        ranked[question.query_id] = [unit_id for unit_id, _score in hits]
    return ranked


def rank_bm25(snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], headers: Mapping[str, str]) -> dict[str, list[str]]:
    texts = {unit.unit_id: recipe_text(snapshot, unit, "llm_context", headers) for unit in snapshot.units
             if unit.unit_id in headers}
    index = BM25.build(texts)
    ranked = {}
    for question in questions:
        allowed = allowed_units(question, snapshot)
        hits = [unit_id for unit_id, _score in index.search(effective_query(question, snapshot), top_k=len(texts))
                if unit_id in allowed]
        ranked[question.query_id] = hits[: pins.POOL_DEPTH]
    return ranked


def label_all(snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], rankings: Mapping[str, Mapping[str, Sequence[str]]],
              caller: Any) -> dict[str, QuestionLabels]:
    labelled: dict[str, QuestionLabels] = {}
    for question in questions:
        pool = pool_for(question, {arm: ranked.get(question.query_id, []) for arm, ranked in rankings.items()},
                        snapshot)
        labelled[question.query_id] = label_question(question, pool, snapshot, caller)
    plan = audit_plan(list(labelled.values()))
    for query_id, labels in labelled.items():
        question = next(question for question in questions if question.query_id == query_id)
        if query_id in plan:
            labels.audit_reason = plan[query_id]
            adjudicate(question, labels, snapshot, caller)
        else:
            accept_agreed(labels)
        question.evidence_sets = evidence_sets_from_labels(labels, snapshot)
        question.label_provenance = "adjudicated" if labels.adjudicated else "model_only"
    return labelled


def pick_finalists(summary: Mapping[str, Mapping[str, Any]]) -> dict[str, str | None]:
    """On development only: the best one-model (Qwen) arm and each hosted
    family's best arm, by Complete Evidence@10 (ties by arm name)."""

    def best(arms: Sequence[str]) -> str | None:
        scored = [(summary[arm]["ce10"], arm) for arm in arms if arm in summary and summary[arm].get("ce10") is not None]
        return min(scored, key=lambda item: (-item[0], item[1]))[1] if scored else None

    return {"one_model": best(QWEN_ARMS), "R4": best(HOSTED_FAMILIES["R4"]), "R5": best(HOSTED_FAMILIES["R5"])}


def run_paid(snapshot: CorpusSnapshot, *, ledger: E0Ledger, caller: Any, run_dir: Path | None,
             transport: Transport | None = None, qwen_client_factory: Callable[[], Any] | None = None,
             logged: Sequence[BankQuestion] = (), strata: Mapping[str, int] | None = None,
             key_envs: Mapping[str, str] | None = None, environ: Mapping[str, str] | None = None,
             latency_budget_s: float | None = None,
             system_handles: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One vault copy's paid E0 run (see the module docstring)."""

    state = PaidState()
    receipts = Receipts(None if run_dir is None else run_dir / "receipts.jsonl")
    store = VectorStore(None if run_dir is None else run_dir / "vectors")
    adapter_kwargs = dict(ledger=ledger, transport=transport, receipts=receipts, store=store,
                          qwen_client_factory=qwen_client_factory, key_envs=key_envs, environ=environ)
    run_contracts(snapshot, state, **adapter_kwargs)
    smoke, _smoke_stats = smoke_bank(snapshot)
    seeds, shortfall = plan_seeds(snapshot, strata=strata)
    for stratum, missing in shortfall.items():
        state.fail(f"bank:{stratum}", "shortfall", "not enough seeds", missing)
    development: list[BankQuestion] = []
    try:
        development, _stats = write_questions(snapshot, seeds, caller)
    except E0BudgetExceeded as exc:
        state.stopped = f"budget: writer ({exc})"
    questions = [*development, *logged]
    headers: dict[str, str] = {}
    if state.stopped is None:
        try:
            headers, context_stats = generate_contexts(snapshot, caller)
            if context_stats["missing"]:
                state.fail("R3", "context_missing", "units without a generated context", context_stats["missing"])
        except E0BudgetExceeded as exc:
            state.blocked_arms.update({"R3", "R3_bm25"})
            state.fail("R3", "budget", str(exc))
    rankings: dict[str, dict[str, list[str]]] = {}
    latencies: dict[str, float] = {}
    for arm in ("R1", "R2", "R3", *HOSTED_FAMILIES["R4"], *HOSTED_FAMILIES["R5"]):
        if state.stopped is not None or arm in state.blocked_arms:
            continue
        if arm == "R3" and not headers:
            state.blocked_arms.add(arm)
            continue
        started = time.monotonic()
        try:
            adapter = make_adapter(arm, snapshot, **adapter_kwargs)
            rankings[arm] = rank_arm(arm, snapshot, [*smoke, *questions], adapter,
                                     headers=headers if arm == "R3" else None)
        except E0BudgetExceeded as exc:
            state.blocked_arms.add(arm)
            state.fail(arm, "budget", str(exc), len(questions))
        except (AdapterError, KeyError) as exc:
            state.blocked_arms.add(arm)
            state.fail(arm, "adapter", str(exc), len(questions))
        latencies[arm] = time.monotonic() - started
    if headers and "R3_bm25" not in state.blocked_arms:
        rankings["R3_bm25"] = rank_bm25(snapshot, [*smoke, *questions], headers)
    if system_handles is not None and state.stopped is None:
        from learnloop.experiments.contextual_embeddings.system_arms import rank_system

        texts = {question.query_id: effective_query(question, snapshot) for question in [*smoke, *questions]}
        for arm, key in (("R0", "R0"), ("R1_service_rrf", "R1_service"), ("R1_service_pool", "R1_service")):
            handle = system_handles.get(key)
            if handle is None:
                state.blocked_arms.add(arm)
                state.fail(arm, "not_prepared", "no service copy for this system arm", len(questions))
                continue
            try:
                rankings[arm], dropped = rank_system(handle, snapshot, [*smoke, *questions], arm=arm,
                                                     ledger=ledger, query_text=texts)
                if any(dropped.values()):
                    state.fail(arm, "hits_dropped", "withheld or unmapped production hits", dropped)
            except E0BudgetExceeded as exc:
                state.blocked_arms.add(arm)
                state.fail(arm, "budget", str(exc), len(questions))
    labelled: dict[str, QuestionLabels] = {}
    if state.stopped is None and questions:
        try:
            labelled = label_all(snapshot, questions, rankings, caller)
        except E0BudgetExceeded as exc:
            state.stopped = f"budget: labels ({exc})"
    arms = sorted(rankings)
    rows = question_rows(snapshot, questions, rankings, labelled)
    summary = arm_summary(rows, arms)
    finalists = pick_finalists(summary)
    answers: list[ScoredAnswer] = []
    source = BlockSource(snapshot_sqlite(snapshot))
    if state.stopped is None:
        try:
            for question in questions:
                if question.selection is not None:
                    for arm in ("D0", "D1", "D2", "D3"):
                        answers.append(answer_and_judge(question, arm, deliver(arm, source, snapshot,
                                                                                question.selection), caller))
                for finalist in [value for value in finalists.values() if value]:
                    delivered: Delivered = retrieved_d1(source, snapshot,
                                                        rankings[finalist].get(question.query_id, [])[: pins.TOP_K])
                    answers.append(answer_and_judge(question, f"{finalist}:D1", delivered, caller))
        except E0BudgetExceeded as exc:
            state.stopped = f"budget: answers ({exc})"
    answer_summary = summarize_answers(answers)
    answer_rows = _answer_rows(answers, questions)
    direct = {arm: _paired_answers(answer_rows, "D1", arm) for arm in ("D2", "D3")}
    context_gain = {family: paired(rows, arms_[1], arms_[0]) for family, arms_ in HOSTED_FAMILIES.items()
                    if arms_[0] in rankings and arms_[1] in rankings}
    hosted = [value for key, value in finalists.items() if key != "one_model" and value]
    best_hosted = max(hosted, key=lambda arm: (summary[arm]["ce10"] or -1, arm)) if hosted else None
    one_model = finalists["one_model"]
    vs = paired(rows, one_model, best_hosted) if one_model and best_hosted else None
    qwen_contextual = max([arm for arm in ("R2", "R3") if arm in summary and summary[arm]["ce10"] is not None],
                          key=lambda arm: (summary[arm]["ce10"], arm), default=None)
    qwen_vs_hosted = paired(rows, qwen_contextual, best_hosted) if qwen_contextual and best_hosted else None
    answer_gain = (_paired_answers(answer_rows, f"{one_model}:D1", f"{best_hosted}:D1")
                   if one_model and best_hosted else None)
    agree = agreement(list(labelled.values()))
    answer_latency = {arm: latency_summary([item.latency_s for item in answers
                                            if item.arm == arm and item.latency_s is not None])
                      for arm in sorted({item.arm for item in answers})}
    decisions = decide(
        s1_inputs={"kappa": agree["agreement"]["kappa"], "unresolved_sets": agree["unresolved"],
                   "extraction_failures": 0, "policy_failures": 0, "arm_completion": completion(rows, arms) |
                   {arm: 0.0 for arm in state.blocked_arms}},
        s2_inputs={"direct": direct,
                   "latency_fits": {arm: _fits(answers, arm, latency_budget_s) for arm in ("D2", "D3")}},
        s3_inputs={"context_gain": context_gain, "qwen_vs_hosted": qwen_vs_hosted},
        s4_inputs={"finalist_vs_one_model": vs, "answer_gain": answer_gain,
                   "latency_ok": _fits(answers, f"{best_hosted}:D1", latency_budget_s) if best_hosted else None,
                   "independent_families": len({question.family for question in questions if question.family})},
    )
    status = "complete" if state.stopped is None and not state.blocked_arms else "incomplete"
    return {
        "status": status, "incomplete_reason": state.stopped or (
            "blocked arms: " + ", ".join(sorted(state.blocked_arms)) if state.blocked_arms else None),
        "contracts": state.contracts, "failures": state.failures,
        "retrieval": summary, "paired": {"context_gain:" + key: value for key, value in context_gain.items()}
        | ({"best_hosted_vs_one_model": vs} if vs else {}),
        "answers": answer_summary, "delivery": direct, "finalists": finalists,
        "label_quality": agree, "decisions": decisions, "ledger": ledger.report(),
        "latency_s": {arm: round(value, 3) for arm, value in latencies.items()}, "answer_latency_s": answer_latency,
        "reader_latency_budget_s": latency_budget_s,
        "bank": {"by_slice": {"smoke": len(smoke), "development": len(development), "logged": len(logged)}},
    }


def snapshot_sqlite(snapshot: CorpusSnapshot) -> Path:
    path = getattr(snapshot, "sqlite_path", None)
    if path is None:
        raise ValueError("the snapshot does not know its database (set snapshot.sqlite_path)")
    return Path(path)


def _answer_rows(answers: Sequence[ScoredAnswer], questions: Sequence[BankQuestion]) -> list[dict[str, Any]]:
    family = {question.query_id: question.family or "none" for question in questions}
    rows: dict[str, dict[str, Any]] = {}
    for item in answers:
        row = rows.setdefault(item.query_id, {"family": family.get(item.query_id, "none")})
        row[item.arm] = None if item.passes is None else float(item.passes)
    return list(rows.values())


def _paired_answers(rows: Sequence[Mapping[str, Any]], a: str, b: str) -> dict[str, Any]:
    from learnloop.experiments.contextual_embeddings.metrics import paired_bootstrap

    return paired_bootstrap(rows, a=a, b=b)


def _fits(answers: Sequence[ScoredAnswer], arm: str, budget_s: float | None) -> bool | None:
    """Whether an arm's p95 answer latency fits the pinned Reader budget;
    None when no budget is pinned (S2/S4 then fail closed)."""

    if budget_s is None:
        return None
    values = [item.latency_s for item in answers if item.arm == arm and item.latency_s is not None]
    summary = latency_summary(values)
    return summary["p95"] is not None and summary["p95"] <= budget_s
