"""The E0 paid run's steps (orchestrator-authorized, after review; never in this stage).

Order (spec §5, §6, §11): freeze -> contracts (one canary per hosted
adapter) -> bank (writer) -> each question's ONE frozen context -> R3
contexts -> encode and rank every arm -> system arms on redacted service
copies -> labels and adjudication -> score; finalists on the development
slice -> delivery D0-D3 and the finalists' D1 answers in a fixed interleaved
schedule, with online latency -> judges -> S1-S4 -> report.

Every request is admitted by the one E0 ledger before it is sent. A refusal
(``E0BudgetExceeded``, the wall-time bound and an unverified price included),
a normalized provider failure (``E0ProviderFailure``, fix round 4) or an
endpoint/contract failure stops the affected step; an overage halts the
whole run (``E0RunHalted``): its arm is recorded as blocked with its
original denominator and the report is marked incomplete; no other model or
recipe stands in for it.

**Planned denominators (Codex review F17).** The bank's seeds, the labels
every question needs, the mandatory audits and the answers the frozen
schedule owes are counted before they run; whatever a stop, an omitted
writer answer or a failure leaves undone is reported as missing beside its
planned count, makes the run ``incomplete`` and stops verdicts (S1).

**Slices (Codex review F16).** Finalists are chosen on the prespecified
primary slice only: development questions outside the ``direct_lookup`` and
``no_support`` strata (the context-dependent/support questions of spec
§5.2). Logged questions, direct lookups, no-support controls, every stratum
and every intent are reported separately with their own denominators and
paired intervals.

**Fallbacks (Codex review F8).** A D2/D3 delivery that does not fit keeps its
fallback's name (``D3_fallback_d2``) and receipt through scoring; the
whole-context comparisons pair only real D2/D3 answers, and ``does_not_fit``
cases are counted apart.

**Latency (Codex review F9).** A finalist's Reader latency is measured
online per question: a fresh query embedding, the exact search and the D1
delivery, plus the tutor call, each recorded once (a resumed run reuses the
original measurement and marks the cache condition). S4 compares the hosted
finalist with the incumbent (the best one-model arm) paired, at p50 and p95,
within ``pins.LATENCY_REGRESSION_TOLERANCE``, and against the frozen
deadline; S2 compares D2/D3 with D1 the same way.

Resume: vectors (documents and queries), checkpointed LLM results, the
latency measurements and the ledger are keyed by complete input identity,
so a rerun pays only for what is missing.
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
    SpaceVectors,
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
    freeze_context,
    label_question,
    plan_seeds,
    pool_for,
    smoke_bank,
    stable_order,
    write_questions,
)
from learnloop.experiments.contextual_embeddings.budget import E0Ledger, E0Stop
from learnloop.experiments.contextual_embeddings.callers import Checkpoints
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
#: Strata outside the primary representation endpoint (spec §5.2).
NON_PRIMARY_STRATA = frozenset({"direct_lookup", "no_support"})
DELIVERY_ARMS = ("D0", "D1", "D2", "D3")


@dataclass
class PaidState:
    """What a paid run has done (aggregates for the report, failures for the ledger)."""

    failures: list[dict[str, Any]] = field(default_factory=list)
    contracts: dict[str, Any] = field(default_factory=dict)
    blocked_arms: set[str] = field(default_factory=set)
    stopped: str | None = None
    #: Planned work not done: ``{kind: count}`` (Codex review F17).
    incomplete: dict[str, int] = field(default_factory=dict)

    def fail(self, item: str, kind: str, reason: str, denominator: Any = None) -> None:
        self.failures.append({"item": item, "kind": kind, "reason": reason, "denominator": denominator})

    def missing(self, kind: str, count: int) -> None:
        if count:
            self.incomplete[kind] = self.incomplete.get(kind, 0) + int(count)

    def stop(self, step: str, exc: Exception) -> None:
        if self.stopped is None:
            self.stopped = f"{getattr(exc, 'kind', 'stopped')}: {step} ({exc})"


def _time_up(state: PaidState, ledger: E0Ledger, step: str) -> bool:
    """Stop cleanly at the run's wall-time bound (Codex review F14), and at
    once when the ledger is halted by an overage (fix round 4, High 2)."""

    halted = ledger.halted()
    if halted and (state.stopped is None or not state.stopped.startswith("halted")):
        state.stopped = f"halted: {halted.get('reason')} (before {step})"
    left = ledger.time_left()
    if left is not None and left <= 0 and state.stopped is None:
        state.stopped = f"deadline: the wall-time bound passed before {step}"
    return state.stopped is not None


#: The arms a failed Qwen route canary blocks (representation and service).
QWEN_ROUTE_ARMS = ("R1", "R2", "R3", "R1_service_rrf", "R1_service_pool", "R1_pool_verify")
#: One canary per embedding route (Qwen first: its service backfill waits on it).
CANARY_ARMS = ("R1", "R4_grouped", "R4_singleton", "R4_independent", "R5_grouped", "R5_singleton", "R5_independent")


def effective_query(question: BankQuestion, snapshot: CorpusSnapshot) -> str:
    """The complete query every arm encodes: the question's frozen context
    (``bank.freeze_context``), never an oracle location for a library question."""

    return freeze_context(question, snapshot).retrieval_query


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
    """One public canary per embedding route, Qwen included, BEFORE any bulk
    work (the service backfill included: fix round 4, Medium 9): the
    document AND query contracts, their compatibility and the returned
    identity. A failing one blocks its arms (a failed Qwen canary blocks
    every Qwen arm, the service arms too)."""

    for arm in CANARY_ARMS:
        blocked = QWEN_ROUTE_ARMS if arm == "R1" else (arm,)
        try:
            adapter = make_adapter(arm, snapshot, **adapter_kwargs)
            state.contracts[arm] = adapter.canary()
        except E0Stop as exc:
            state.blocked_arms.update(blocked)
            state.contracts[arm] = {"status": "failed", "kind": exc.kind}
            state.fail(arm, exc.kind, str(exc))
        except AdapterError as exc:
            state.blocked_arms.update(blocked)
            state.contracts[arm] = {"status": "failed", "kind": exc.kind}
            state.fail(arm, f"contract_{exc.kind}", str(exc))
    return state.contracts


def contracts_state(contracts: Mapping[str, Any]) -> PaidState:
    """A state carrying contracts already run (``run_live`` runs them before
    the service backfill), with their blocked arms."""

    state = PaidState()
    state.contracts = dict(contracts)
    for arm, result in contracts.items():
        if (result or {}).get("status") == "failed":
            state.blocked_arms.update(QWEN_ROUTE_ARMS if arm == "R1" else (arm,))
            state.fail(arm, f"contract_{(result or {}).get('kind')}", "the route's canary failed")
    return state


def rank_arm(arm: str, snapshot: CorpusSnapshot, questions: Sequence[BankQuestion], adapter: EmbeddingAdapter, *,
             headers: Mapping[str, str] | None = None, top: int = pins.POOL_DEPTH,
             indexes: dict[str, tuple[EmbeddingAdapter, SpaceVectors]] | None = None) -> dict[str, list[str]]:
    spec = pins.RETRIEVAL_ARMS[arm]
    documents, chunk_unit = documents_for(snapshot, spec.encoding, spec.recipe, adapter.document_space_id, headers)
    vectors = adapter.encode_documents(documents)
    entries = []
    for document, document_vectors in zip(documents, vectors, strict=True):
        for chunk, vector in zip(document.chunks, document_vectors, strict=True):
            entries.append((chunk_unit[chunk.chunk_id], adapter.document_space_id, adapter.query_encoder_id, vector))
    index = build_index(entries)
    if indexes is not None:
        indexes[arm] = (adapter, index)
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


def label_all(snapshot: CorpusSnapshot, questions: Sequence[BankQuestion],
              rankings: Mapping[str, Mapping[str, Sequence[str]]], caller: Any,
              state: PaidState | None = None) -> dict[str, QuestionLabels]:
    """Labels for every question, then the audits. A stop keeps what was done:
    a question never labelled is counted missing; a MANDATORY audit that never
    ran leaves the question unresolved (model-only labels are never ground
    truth there); a sampled audit that never ran is counted missing."""

    state = state if state is not None else PaidState()
    labelled: dict[str, QuestionLabels] = {}
    for question in questions:
        pool = pool_for(question, {arm: ranked.get(question.query_id, []) for arm, ranked in rankings.items()},
                        snapshot)
        try:
            labelled[question.query_id] = label_question(question, pool, snapshot, caller)
        except E0Stop as exc:
            state.stop("labels", exc)
            break
    state.missing("labels_missing", len(questions) - len(labelled))
    plan = audit_plan(list(labelled.values()))
    by_id = {question.query_id: question for question in questions}
    for query_id, labels in labelled.items():
        question = by_id[query_id]
        if query_id in plan:
            labels.audit_reason = plan[query_id]
            if state.stopped is None:
                try:
                    adjudicate(question, labels, snapshot, caller)
                except E0Stop as exc:
                    state.stop("audits", exc)
            if not labels.adjudicated:
                if plan[query_id] == "seeded_sample":
                    accept_agreed(labels)
                    state.missing("sampled_audits_missing", 1)
                else:
                    labels.unresolved = True
                    state.missing("mandatory_audits_missing", 1)
        else:
            accept_agreed(labels)
        question.evidence_sets = evidence_sets_from_labels(labels, snapshot)
        question.label_provenance = "adjudicated" if labels.adjudicated else "model_only"
    return labelled


def primary_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """The prespecified selection slice: development, context-dependent/support strata."""

    return [row for row in rows if row["split"] == "development" and row["stratum"] not in NON_PRIMARY_STRATA]


def slice_summaries(rows: Sequence[Mapping[str, Any]], arms: Sequence[str]) -> dict[str, Any]:
    """Every slice reported apart with its own denominator (``total`` rows,
    ``scored`` per arm)."""

    def group(key: str, value: Any) -> list[Mapping[str, Any]]:
        return [row for row in rows if row.get(key) == value]

    slices: dict[str, Any] = {
        "primary_development": arm_summary(primary_rows(rows), arms),
        "development_all": arm_summary(group("split", "development"), arms),
        "logged": arm_summary(group("split", "logged"), arms),
        "direct_lookup": arm_summary([row for row in group("split", "development")
                                      if row["stratum"] == "direct_lookup"], arms),
        "no_support": arm_summary([row for row in group("split", "development") if row["stratum"] == "no_support"],
                                  arms),
        "by_stratum": {stratum: arm_summary(group("stratum", stratum), arms)
                       for stratum in sorted({row["stratum"] for row in rows})},
        "by_intent": {intent: arm_summary(group("intent", intent), arms)
                      for intent in sorted({str(row.get("intent")) for row in rows})},
    }
    return slices


def pick_finalists(summary: Mapping[str, Mapping[str, Any]]) -> dict[str, str | None]:
    """On the primary development slice only: the best one-model (Qwen) arm
    and each hosted family's best arm, by Complete Evidence@10 (ties by arm name)."""

    def best(arms: Sequence[str]) -> str | None:
        scored = [(summary[arm]["ce10"], arm) for arm in arms if arm in summary and summary[arm].get("ce10") is not None]
        return min(scored, key=lambda item: (-item[0], item[1]))[1] if scored else None

    return {"one_model": best(QWEN_ARMS), "R4": best(HOSTED_FAMILIES["R4"]), "R5": best(HOSTED_FAMILIES["R5"])}


def _online_retrieval(arm: str, question: BankQuestion, snapshot: CorpusSnapshot, source: BlockSource,
                      indexes: Mapping[str, tuple[EmbeddingAdapter, SpaceVectors]], measured: Checkpoints) -> float | None:
    """One question's online retrieval-through-delivery time for a retrieval
    arm: a FRESH query embedding (never the cache), the exact search and the D1
    delivery. Recorded once; a resume returns the original measurement."""

    entry = indexes.get(arm)
    if entry is None:
        return None
    adapter, index = entry
    text = effective_query(question, snapshot)
    key = f"online_{adapter.query_encoder_id}_{question.query_id}"
    saved = measured.get(key)
    if saved is not None:
        return saved["result"]["retrieval_s"]
    started = time.monotonic()
    vector = adapter.encode_queries([PreparedQuery(question.query_id, text)], fresh=True)[0]
    hits = exact_search(index, vector, query_encoder=adapter.query_encoder_id, top_k=pins.TOP_K,
                        allowed=allowed_units(question, snapshot))
    retrieved_d1(source, snapshot, [unit_id for unit_id, _score in hits])
    seconds = round(time.monotonic() - started, 4)
    measured.put(key, {"result": {"retrieval_s": seconds}, "latency_s": seconds, "receipts": []})
    return seconds


def latency_check(answers: Sequence[ScoredAnswer], arm: str | None, incumbent: str | None,
                  budget_s: float | None) -> dict[str, Any]:
    """Whether ``arm`` meets the frozen deadline AND shows no paired p50/p95
    regression against ``incumbent`` (within the pinned tolerance). ``ok`` is
    None when no budget is pinned or nothing was measured (S2/S4 fail closed)."""

    def values(name: str | None) -> dict[str, float]:
        return {item.query_id: float(item.latency_s) for item in answers
                if name is not None and item.arm == name and item.latency_s is not None}

    mine, theirs = values(arm), values(incumbent)
    pairs = sorted(set(mine) & set(theirs))
    own = latency_summary([mine[key] for key in pairs]) if pairs else latency_summary(list(mine.values()))
    base = latency_summary([theirs[key] for key in pairs])
    tolerance = 1.0 + pins.LATENCY_REGRESSION_TOLERANCE
    fits_deadline = None if budget_s is None or own["p95"] is None else own["p95"] <= budget_s
    regression = None
    if pairs and base["p50"] is not None and own["p50"] is not None:
        regression = own["p50"] > base["p50"] * tolerance or own["p95"] > base["p95"] * tolerance
    ok = None if fits_deadline is None or regression is None else bool(fits_deadline and not regression)
    cached = sum(1 for item in answers if item.arm == arm and item.cached)
    return {"arm": arm, "incumbent": incumbent, "paired": len(pairs), "p50": own["p50"], "p95": own["p95"],
            "incumbent_p50": base["p50"], "incumbent_p95": base["p95"], "deadline_s": budget_s,
            "fits_deadline": fits_deadline, "regression": regression, "tolerance": pins.LATENCY_REGRESSION_TOLERANCE,
            "cached_tutor_answers": cached, "ok": ok}


def run_paid(snapshot: CorpusSnapshot, *, ledger: E0Ledger, caller: Any, run_dir: Path | None,
             transport: Transport | None = None, qwen_client_factory: Callable[[], Any] | None = None,
             logged: Sequence[BankQuestion] = (), strata: Mapping[str, int] | None = None,
             key_envs: Mapping[str, str] | None = None, environ: Mapping[str, str] | None = None,
             latency_budget_s: float | None = None,
             system_handles: Mapping[str, Any] | None = None,
             system_preparation: Mapping[str, Any] | None = None,
             system_clients: Mapping[str, Any] | None = None,
             contracts: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One vault copy's paid E0 run (see the module docstring). ``contracts``:
    the route canaries already run (``run_live`` runs them before the service
    backfill); None runs them here first."""

    receipts = Receipts(None if run_dir is None else run_dir / "receipts.jsonl")
    store = VectorStore(None if run_dir is None else run_dir / "vectors")
    measured = Checkpoints(None if run_dir is None else run_dir / "latency")
    adapter_kwargs = dict(ledger=ledger, transport=transport, receipts=receipts, store=store,
                          qwen_client_factory=qwen_client_factory, key_envs=key_envs, environ=environ)
    if contracts is None:
        state = PaidState()
        run_contracts(snapshot, state, **adapter_kwargs)
    else:
        state = contracts_state(contracts)
    smoke, _smoke_stats = smoke_bank(snapshot)
    seeds, shortfall = plan_seeds(snapshot, strata=strata)
    for stratum, missing in shortfall.items():
        state.fail(f"bank:{stratum}", "shortfall", "not enough seeds", missing)
    development: list[BankQuestion] = []
    writer_stats: dict[str, Any] = {"planned": len(seeds)}
    if not _time_up(state, ledger, "the writer"):
        development, writer_stats = write_questions(snapshot, seeds, caller)
        if writer_stats.get("stopped"):
            state.stopped = f"budget: writer ({writer_stats['stopped']})"
    bank_missing = int(writer_stats.get("unanswered_seeds", 0)) + int(writer_stats.get("unattempted_seeds", 0))
    if not writer_stats.get("calls") and state.stopped:
        bank_missing = len(seeds)
    state.missing("bank_missing", bank_missing)
    if bank_missing:
        state.fail("bank:writer", "missing", "seeds without a written question", {"planned": len(seeds),
                                                                                    "written": len(development)})
    questions = [*development, *logged]
    for question in [*smoke, *questions]:
        freeze_context(question, snapshot)
    headers: dict[str, str] = {}
    if not _time_up(state, ledger, "R3 contexts"):
        try:
            headers, context_stats = generate_contexts(snapshot, caller)
            if context_stats["missing"]:
                state.fail("R3", "context_missing", "units without a generated context", context_stats["missing"])
        except E0Stop as exc:
            state.blocked_arms.update({"R3", "R3_bm25"})
            state.fail("R3", exc.kind, str(exc))
    rankings: dict[str, dict[str, list[str]]] = {}
    latencies: dict[str, float] = {}
    indexes: dict[str, tuple[EmbeddingAdapter, SpaceVectors]] = {}
    for arm in ("R1", "R2", "R3", *HOSTED_FAMILIES["R4"], *HOSTED_FAMILIES["R5"]):
        if _time_up(state, ledger, arm) or arm in state.blocked_arms:
            continue
        if arm == "R3" and not headers:
            state.blocked_arms.add(arm)
            continue
        started = time.monotonic()
        try:
            adapter = make_adapter(arm, snapshot, **adapter_kwargs)
            rankings[arm] = rank_arm(arm, snapshot, [*smoke, *questions], adapter,
                                     headers=headers if arm == "R3" else None, indexes=indexes)
        except E0Stop as exc:
            state.blocked_arms.add(arm)
            state.fail(arm, exc.kind, str(exc), len(questions))
        except (AdapterError, KeyError) as exc:
            state.blocked_arms.add(arm)
            state.fail(arm, "adapter", str(exc), len(questions))
        latencies[arm] = time.monotonic() - started
    if headers and "R3_bm25" not in state.blocked_arms:
        rankings["R3_bm25"] = rank_bm25(snapshot, [*smoke, *questions], headers)
    system: dict[str, Any] = {}
    if system_handles is not None and not _time_up(state, ledger, "the system arms"):
        from learnloop.experiments.contextual_embeddings.system_arms import DENSE_ARMS, SYSTEM_ARMS, rank_system

        coverage = ((system_preparation or {}).get("qwen") or {}).get("coverage") or {}
        texts = {question.query_id: effective_query(question, snapshot) for question in [*smoke, *questions]}
        for arm, (key, _interface) in SYSTEM_ARMS.items():
            if arm in state.blocked_arms:
                continue  # its route canary failed: no service work for it
            handle = system_handles.get(key)
            if handle is None:
                state.blocked_arms.add(arm)
                state.fail(arm, "not_prepared", "no service copy for this system arm", len(questions))
                continue
            if arm in DENSE_ARMS and system_preparation is not None and not coverage.get("complete"):
                # A partially covered index is no fully covered Qwen arm.
                state.blocked_arms.add(arm)
                state.fail(arm, "coverage_incomplete", "the service copy's dense coverage is incomplete", coverage)
                continue
            try:
                rankings[arm], system[arm] = rank_system(handle, snapshot, [*smoke, *questions], arm=arm,
                                                         ledger=ledger, query_text=texts, clients=system_clients)
                if system[arm]["withheld"] or system[arm]["unmapped"]:
                    state.fail(arm, "hits_dropped", "withheld or unmapped production hits",
                               {"withheld": system[arm]["withheld"], "unmapped": system[arm]["unmapped"]})
                if system[arm]["missing"]:
                    state.fail(arm, "questions_unranked", "verification, pool or dense fallbacks",
                               system[arm]["missing"])
            except E0Stop as exc:
                state.blocked_arms.add(arm)
                state.fail(arm, exc.kind, str(exc), len(questions))
    labelled: dict[str, QuestionLabels] = {}
    if questions and not _time_up(state, ledger, "labels"):
        labelled = label_all(snapshot, questions, rankings, caller, state)
    elif questions:
        state.missing("labels_missing", len(questions))
    arms = sorted(rankings)
    rows = question_rows(snapshot, questions, rankings, labelled)
    primary = primary_rows(rows)
    slices = slice_summaries(rows, arms)
    summary = slices["primary_development"]
    finalists = pick_finalists(summary)
    answers: list[ScoredAnswer] = []
    source = BlockSource(snapshot_sqlite(snapshot))
    finalist_arms = [value for value in finalists.values() if value]
    planned_pairs = [(question, arm) for question in questions if question.selection is not None
                     for arm in DELIVERY_ARMS]
    planned_pairs += [(question, f"{finalist}:D1") for question in questions for finalist in finalist_arms]
    # A fixed interleaved schedule (spec §6): paired arms alternate, not in blocks.
    schedule = stable_order(planned_pairs, "answer-schedule", key=lambda pair: (pair[0].query_id, pair[1]))
    planned_counts: dict[str, int] = {}
    for _question, arm in planned_pairs:
        planned_counts[arm] = planned_counts.get(arm, 0) + 1
    done = 0
    if state.stopped is None:
        for question, arm in schedule:
            if _time_up(state, ledger, "answers"):
                break
            try:
                if arm in DELIVERY_ARMS:
                    started = time.monotonic()
                    delivered = deliver(arm, source, snapshot, question.selection)
                    answers.append(answer_and_judge(question, arm, delivered, caller,
                                                    retrieval_latency_s=round(time.monotonic() - started, 4)))
                else:
                    finalist = arm.split(":", 1)[0]
                    online = _online_retrieval(finalist, question, snapshot, source, indexes, measured)
                    delivered = retrieved_d1(source, snapshot,
                                             rankings[finalist].get(question.query_id, [])[: pins.TOP_K])
                    answers.append(answer_and_judge(question, arm, delivered, caller, retrieval_latency_s=online))
                done += 1
            except E0Stop as exc:
                state.stop("answers", exc)
                break
            except AdapterError as exc:
                state.fail(arm, "online_latency", str(exc), 1)
    state.missing("answers_missing", len(schedule) - done)
    answer_summary = summarize_answers(answers, planned_counts)
    answer_rows = _answer_rows(answers, questions)
    does_not_fit = {arm: sum(1 for item in answers if item.planned_arm == arm) for arm in ("D2", "D3")}
    direct = {arm: _paired_answers(answer_rows, "D1", arm) for arm in ("D2", "D3")}
    d1_vs_d0 = _paired_answers(answer_rows, "D0", "D1")
    context_gain = {family: paired(primary, arms_[1], arms_[0]) for family, arms_ in HOSTED_FAMILIES.items()
                    if arms_[0] in rankings and arms_[1] in rankings}
    hosted = [value for key, value in finalists.items() if key != "one_model" and value]
    best_hosted = max(hosted, key=lambda arm: (summary[arm]["ce10"] or -1, arm)) if hosted else None
    one_model = finalists["one_model"]
    vs = paired(primary, one_model, best_hosted) if one_model and best_hosted else None
    vs_logged = paired([row for row in rows if row["split"] == "logged"], one_model, best_hosted) \
        if one_model and best_hosted else None
    qwen_contextual = max([arm for arm in ("R2", "R3") if arm in summary and summary[arm]["ce10"] is not None],
                          key=lambda arm: (summary[arm]["ce10"], arm), default=None)
    qwen_vs_hosted = paired(primary, qwen_contextual, best_hosted) if qwen_contextual and best_hosted else None
    answer_gain = (_paired_answers(answer_rows, f"{one_model}:D1", f"{best_hosted}:D1")
                   if one_model and best_hosted else None)
    agree = agreement(list(labelled.values()))
    answer_latency = {arm: latency_summary([item.latency_s for item in answers
                                            if item.arm == arm and item.latency_s is not None])
                      for arm in sorted({item.arm for item in answers})}
    latency = {"D2_vs_D1": latency_check(answers, "D2", "D1", latency_budget_s),
               "D3_vs_D1": latency_check(answers, "D3", "D1", latency_budget_s),
               "finalist_vs_incumbent": latency_check(answers, f"{best_hosted}:D1" if best_hosted else None,
                                                      f"{one_model}:D1" if one_model else None, latency_budget_s)}
    completion_by_arm = completion(primary, arms) | {arm: 0.0 for arm in state.blocked_arms}
    # Coverage of every REQUIRED slice, not only the one that selects finalists
    # (fix round 4, Medium 13): an arm that ranked its development questions but
    # failed every logged one is materially incomplete there, and S1 sees it.
    slice_rows = {"development_all": [row for row in rows if row["split"] == "development"],
                  "logged": [row for row in rows if row["split"] == "logged"]}
    slice_completion: dict[str, dict[str, float]] = {}
    for name, members in slice_rows.items():
        if any(row["answerable"] and not row["unresolved"] and row.get("labelled", True) for row in members):
            shares = completion(members, arms) | {arm: 0.0 for arm in state.blocked_arms}
            slice_completion[name] = shares
            completion_by_arm |= {f"{arm}@{name}": share for arm, share in shares.items()}
    s4_evidence = [result for result in (vs, answer_gain) if result]
    # S4's independent families are those of its complete-case PAIRED evidence,
    # and its own exploratory flag holds (fix round 4, Medium 14).
    s4_families = min((int(result.get("families", 0)) for result in s4_evidence), default=0)
    s4_exploratory = not s4_evidence or any(result.get("exploratory", True) for result in s4_evidence)
    decisions = decide(
        s1_inputs={"kappa": agree["agreement"]["kappa"], "unresolved_sets": agree["unresolved"],
                   "extraction_failures": 0, "policy_failures": 0, "arm_completion": completion_by_arm,
                   "incomplete_work": dict(state.incomplete)},
        s2_inputs={"direct": direct,
                   "latency_fits": {"D2": latency["D2_vs_D1"]["ok"], "D3": latency["D3_vs_D1"]["ok"]}},
        s3_inputs={"context_gain": context_gain, "qwen_vs_hosted": qwen_vs_hosted},
        s4_inputs={"finalist_vs_one_model": vs, "answer_gain": answer_gain,
                   "latency_ok": latency["finalist_vs_incumbent"]["ok"] if best_hosted else None,
                   "independent_families": s4_families, "exploratory": s4_exploratory},
    )
    # An arm that scored too few of its questions (a system arm whose required
    # verification never ran, say) is materially incomplete, not complete.
    thin = sorted(arm for arm, share in completion_by_arm.items()
                  if share < pins.ARM_COMPLETION_MIN and arm not in state.blocked_arms)
    complete = state.stopped is None and not state.blocked_arms and not state.incomplete and not thin
    reasons = [state.stopped] if state.stopped else []
    if state.blocked_arms:
        reasons.append("blocked arms: " + ", ".join(sorted(state.blocked_arms)))
    if thin:
        reasons.append("materially incomplete arms: " + ", ".join(thin))
    if state.incomplete:
        reasons.append("planned work missing: " + ", ".join(f"{key} {value}"
                                                            for key, value in sorted(state.incomplete.items())))
    return {
        "status": "complete" if complete else "incomplete",
        "incomplete_reason": "; ".join(reasons) if reasons else None,
        "contracts": state.contracts, "failures": state.failures,
        "planned": {"development_seeds": len(seeds), "development_written": len(development),
                    "writer": {key: value for key, value in writer_stats.items() if key != "stopped"},
                    "questions": len(questions), "labelled": len(labelled), "answers": planned_counts,
                    "answers_made": done, "missing": dict(sorted(state.incomplete.items()))},
        "retrieval": summary, "retrieval_slices": slices, "selection_slice": "primary_development",
        "paired": {"context_gain:" + key: value for key, value in context_gain.items()}
        | ({"best_hosted_vs_one_model": vs} if vs else {})
        | ({"best_hosted_vs_one_model:logged": vs_logged} if vs_logged else {}),
        "answers": answer_summary,
        "delivery": {**direct, "D1_vs_D0": d1_vs_d0, "does_not_fit": does_not_fit},
        "finalists": finalists, "system_arms": system, "slice_completion": slice_completion,
        "label_quality": agree, "decisions": decisions, "ledger": ledger.report(),
        "latency_s": {arm: round(value, 3) for arm, value in latencies.items()}, "answer_latency_s": answer_latency,
        "latency_checks": latency, "reader_latency_budget_s": latency_budget_s,
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
