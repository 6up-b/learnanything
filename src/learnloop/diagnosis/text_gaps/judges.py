"""Paid calls of the learner-text gap pipeline, each admitted before it is sent.

One :class:`TextBudget` (a :class:`ReviewSpend`) per learner text, or the
enclosing command's: the LLM judge and stuck-text reader (subscription or
metered at the owner's price), the Decider (metered at its listed input
price), the query embedding (metered at the known price) and the
authoring-route draft. A refusal is ``SpendLimitExceeded`` and nothing is
sent. Every model verdict is appended to ``judgment_ledger``.

Two executors plug into T1's ``learnloop.matching.judge.judge_pairs``: the
LLM judge (``judge='llm'``) and the Decider (``judge='decider'``, a typed
``choice`` over same / different / unsure read from the same rendered pair; it
gives no rationale, so the ledger's rationale records its probabilities).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import closing, contextmanager
from dataclasses import dataclass, field
import json
from typing import Any

import numpy as np

from learnloop.ai.execution import content_key
from learnloop.ai.spend import SpendCaps
from learnloop.ai.transport import execute_structured_operation, render_structured_prompt
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.embedding_vectors import get_vector, put_vector
from learnloop.db.stores.judgments import append_judgment
from learnloop.diagnosis.offline_review.spend import ReviewSpend, RouteInfo
from learnloop.diagnosis.recurrence.judging import estimate_tokens, producer_label, receipt_sink
from learnloop.diagnosis.split.retrieval import QUERY_PREFIX
from learnloop.diagnosis.text_gaps.contract import (
    DECIDER_KIND_QUESTION_SET,
    DECIDER_NEEDED_QUESTION_SET,
    DECIDER_PAIR_QUESTION_SET,
    DECIDER_ROUTE,
    DRAFT_PROMPT_VERSION,
    DRAFT_PURPOSE,
    DRAFT_ROUTE,
    DRAFT_TASK,
    EMBEDDING_ROUTE,
    JUDGE_ROUTE,
    KIND_QUESTION,
    KIND_TASK,
    NEEDED_PROMPT_VERSION,
    NEEDED_PURPOSE,
    NEEDED_QUESTION,
    NEEDED_TASK,
    NEEDED_TASK_TEXT,
    PAIR_OPTIONS,
    PAIR_QUESTION_INSTRUCTIONS,
    READER_PROMPT_VERSION,
    READER_PURPOSE,
    READER_ROUTE,
    READER_TASK,
    GapReading,
    LearnerText,
    NeededVerdict,
    PrerequisiteDraft,
)
from learnloop.matching.judge import SameOrDifferent
from learnloop.matching.kinds import Subject
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.vault.models import LoadedVault

#: model_call receipts of the pipeline's calls are owned by the learner text.
MODEL_CALL_OWNER_KIND = "learner_text_gap"
ClientFactory = Callable[[], Any]


def caps_for(vault: LoadedVault) -> SpendCaps:
    config = vault.config.learner_text_gaps
    calls = int(config.max_calls_per_text)
    return SpendCaps(
        max_candidates=calls, max_pairs=calls, max_retries=max(8, calls), max_calls=calls,
        max_total_tokens=calls * 40_000, max_estimated_usd=float(config.max_usd_per_text),
    )


class TextBudget:
    """Route registration and admission over one :class:`ReviewSpend`."""

    def __init__(self, spend: ReviewSpend) -> None:
        self.spend = spend

    @classmethod
    def for_text(
        cls, vault: LoadedVault, *, price_per_million: float | None = None, cancelled: Callable[[], bool] | None = None,
    ) -> "TextBudget":
        price = price_per_million if price_per_million is not None else vault.config.learner_text_gaps.metered_price_per_million
        return cls(ReviewSpend(caps_for(vault), cancelled=cancelled, price_per_million=price))

    def register_llm(self, route: str, client: Any) -> None:
        if route not in self.spend.routes:
            self.spend.register(route, client)

    def register_decider(self, client: Any) -> None:
        if DECIDER_ROUTE in self.spend.routes:
            return
        settings = getattr(client, "settings", None)
        price = getattr(settings, "price_per_million_input", None)
        self.spend.routes[DECIDER_ROUTE] = RouteInfo(
            DECIDER_ROUTE, getattr(client, "provider_name", None), getattr(client, "model", None), "metered",
            float(price) if price is not None else None, "listed_input_price" if price is not None else "unknown",
            0,
        )

    def register_embedding(self, client: Any) -> None:
        if EMBEDDING_ROUTE in self.spend.routes:
            return
        from learnloop.diagnosis.split.jobs import register_retrieval_route

        register_retrieval_route(self.spend, client)

    @contextmanager
    def request(self, route: str, purpose: str, *, input_tokens: int, output_tokens: int | None = None) -> Iterator[Any]:
        with self.spend.collector.observing():
            with self.spend.request(route, purpose, input_tokens=input_tokens, output_tokens=output_tokens) as call:
                yield call

    @contextmanager
    def receipts(self, repository: Repository, owner_id: str) -> Iterator[None]:
        previous = self.spend.collector.sink
        self.spend.collector.sink = receipt_sink(repository, owner_kind=MODEL_CALL_OWNER_KIND, owner_id=owner_id)
        try:
            yield
        finally:
            self.spend.collector.sink = previous


# -- the two pair judges --------------------------------------------------------------


class LLMPairExecutor:
    """One isolated structured call per pair on ``learner_gap_judge`` (judge ``llm``)."""

    judge = "llm"

    def __init__(self, budget: TextBudget, client: Any) -> None:
        self.budget = budget
        self.client = client
        self.producer = producer_label(client)
        budget.register_llm(JUDGE_ROUTE, client)

    def __call__(self, prompt: str, result_model: type[SameOrDifferent], purpose: str) -> tuple[SameOrDifferent, str]:
        with self.budget.request(JUDGE_ROUTE, purpose, input_tokens=estimate_tokens(prompt)):
            result = execute_structured_operation(
                self.client, purpose=purpose, prompt=prompt, result_model=result_model, isolated=True,
            )
        return result, self.producer


def _probabilities(answer: Any) -> dict[str, float]:
    return {str(key): round(float(value), 4) for key, value in dict(getattr(answer, "probabilities", {}) or {}).items()}


def decider_rationale(question_set: str, probabilities: Mapping[str, float]) -> str:
    rendered = ", ".join(f"{key} {value:.3f}" for key, value in probabilities.items())
    return f"Decider ({question_set}) gives no rationale; probabilities: {rendered}"


class DeciderPairExecutor:
    """The Decider on the same rendered pair (judge ``decider``)."""

    judge = "decider"

    def __init__(self, budget: TextBudget, client: Any) -> None:
        from learnloop.ai.decisions import ChoiceQuestion

        self.budget = budget
        self.client = client
        self.producer = str(getattr(client, "model", None) or "unknown")
        self.question = ChoiceQuestion(instructions=PAIR_QUESTION_INSTRUCTIONS, options=PAIR_OPTIONS)
        budget.register_decider(client)

    def __call__(self, prompt: str, result_model: type[SameOrDifferent], purpose: str) -> tuple[SameOrDifferent, str]:
        tokens = estimate_tokens(prompt) + 200
        with self.budget.request(DECIDER_ROUTE, purpose, input_tokens=tokens, output_tokens=0):
            result = self.client.decide(prompt, {"verdict": self.question}, purpose=purpose)
        answer = result.answers["verdict"]
        verdict = SameOrDifferent(
            verdict=answer.choice, rationale=decider_rationale(DECIDER_PAIR_QUESTION_SET, _probabilities(answer)),
        )
        return verdict, self.producer


# -- the kind ---------------------------------------------------------------------------


def kind_state(text: LearnerText) -> dict[str, Any]:
    """What the Decider reads for the kind: the learner's text and what it was about."""

    surface = {
        "tutor_question": "a question the learner asked the tutor",
        "stuck_answer": "an answer the learner wrote after pressing \"I'm stuck\"",
        "diagnosis": "a wrong answer the learner gave",
    }[text.source_kind]
    return {"learner_text": text.text, "what_it_is": surface, "about": dict(text.context)}


def kind_input_hash(text: LearnerText) -> str:
    return content_key({"source": [text.source_kind, text.source_id], "text": text.text, "context": dict(text.context)})


def _already_logged(connection: Any, *, task: str, left: tuple[str, str], judge: str, judge_model: str,
                    prompt_version: str, input_hash: str, right: tuple[str, str] | None = None) -> str | None:
    query = (
        "SELECT id FROM judgment_ledger WHERE task = ? AND left_kind = ? AND left_id = ? AND judge = ? "
        "AND COALESCE(judge_model, '') = ? AND COALESCE(prompt_version, '') = ? AND input_hash = ?"
    )
    params: list[Any] = [task, *left, judge, judge_model, prompt_version, input_hash]
    if right is not None:
        query += " AND right_kind = ? AND right_id = ?"
        params.extend(right)
    row = connection.execute(query + " ORDER BY created_at DESC LIMIT 1", params).fetchone()
    return str(row[0]) if row is not None else None


def log_reading(repository: Repository, text: LearnerText, reading: GapReading) -> str | None:
    """The context model's reading as a ``learner_gap_kind`` verdict (idempotent)."""

    judge = "diagnoser" if reading.judge == "diagnoser" else "llm"
    prompt_version = reading.prompt_version or "unknown"
    input_hash = kind_input_hash(text)
    with repository.atomic():
        connection = repository.connection()
        existing = _already_logged(
            connection, task=KIND_TASK, left=(text.source_kind, text.source_id), judge=judge,
            judge_model=reading.judge_model, prompt_version=prompt_version, input_hash=input_hash,
        )
        if existing is not None:
            return existing
        return append_judgment(
            connection, task=KIND_TASK, left_kind=text.source_kind, left_id=text.source_id, judge=judge,
            judge_model=reading.judge_model, prompt_version=prompt_version, input_hash=input_hash,
            verdict=reading.kind, rationale=json.dumps(reading.named(), sort_keys=True)[:1000],
        )


@dataclass
class DeciderKind:
    status: str  # ok | disabled | unavailable | refused | failed
    choice: str | None = None
    probabilities: dict[str, float] = field(default_factory=dict)
    model: str | None = None
    judgment_id: str | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"status": self.status, "choice": self.choice, "probabilities": self.probabilities,
                "model": self.model, "judgment_id": self.judgment_id, "error": self.error}


def decider_kind(repository: Repository, budget: TextBudget, client: Any, text: LearnerText) -> DeciderKind:
    """The Decider's typed kind, appended to ``judgment_ledger`` (judge ``decider``)."""

    from learnloop.ai.spend import SpendLimitExceeded

    budget.register_decider(client)
    state = kind_state(text)
    model = str(getattr(client, "model", None) or "unknown")
    input_hash = kind_input_hash(text)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        existing = connection.execute(
            "SELECT id, verdict, score, rationale FROM judgment_ledger WHERE task = ? AND left_kind = ? AND left_id = ? "
            "AND judge = 'decider' AND judge_model = ? AND prompt_version = ? AND input_hash = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (KIND_TASK, text.source_kind, text.source_id, model, DECIDER_KIND_QUESTION_SET, input_hash),
        ).fetchone()
    if existing is not None:
        return DeciderKind("ok", choice=str(existing[1]), model=model, judgment_id=str(existing[0]))
    tokens = estimate_tokens(json.dumps(state, ensure_ascii=False)) + 400
    try:
        with budget.request(DECIDER_ROUTE, "learner_gap_kind", input_tokens=tokens, output_tokens=0):
            result = client.decide(state, {"kind": KIND_QUESTION}, purpose="learner_gap_kind")
    except SpendLimitExceeded as exc:
        return DeciderKind("refused", model=model, error=str(exc))
    except Exception as exc:  # noqa: BLE001 - a second opinion never fails the reading
        return DeciderKind("failed", model=model, error=type(exc).__name__)
    answer = result.answers["kind"]
    probabilities = _probabilities(answer)
    with repository.atomic():
        judgment_id = append_judgment(
            repository.connection(), task=KIND_TASK, left_kind=text.source_kind, left_id=text.source_id,
            judge="decider", judge_model=model, prompt_version=DECIDER_KIND_QUESTION_SET, input_hash=input_hash,
            verdict=answer.choice, score=probabilities.get(answer.choice),
            rationale=decider_rationale(DECIDER_KIND_QUESTION_SET, probabilities),
        )
    return DeciderKind("ok", choice=answer.choice, probabilities=probabilities, model=model, judgment_id=judgment_id)


# -- the stuck-text reader ---------------------------------------------------------------


def reader_prompt(text: LearnerText) -> str:
    return render_structured_prompt(
        "learnloop learner gap reader", READER_PROMPT_VERSION,
        {"task": READER_TASK, "context": {"learner_text": text.text, **dict(text.context)}},
    )


def read_text(budget: TextBudget, client: Any, text: LearnerText) -> GapReading:
    """One isolated call naming the gap in a stuck answer; ``failed`` on refusal or error."""

    from learnloop.ai.spend import SpendLimitExceeded

    model = producer_label(client)
    budget.register_llm(READER_ROUTE, client)
    prompt = reader_prompt(text)
    try:
        with budget.request(READER_ROUTE, READER_PURPOSE, input_tokens=estimate_tokens(prompt)):
            gap = execute_structured_operation(
                client, purpose=READER_PURPOSE, prompt=prompt, result_model=LearnerGap, isolated=True,
            )
    except SpendLimitExceeded:
        return GapReading("none", judge="llm", judge_model=model, prompt_version=READER_PROMPT_VERSION, status="refused")
    except Exception:  # noqa: BLE001 - a failed reading falls back to the grounded rule
        return GapReading("none", judge="llm", judge_model=model, prompt_version=READER_PROMPT_VERSION, status="failed")
    return GapReading.from_gap(gap, judge="llm", judge_model=model, prompt_version=READER_PROMPT_VERSION)


# -- "is it needed for this item?" ---------------------------------------------------------


def needed_context(vault: LoadedVault, item: Any, prerequisite_lo: Any) -> dict[str, Any]:
    owner = vault.learning_objects.get(item.learning_object_id)
    return {
        "item": {"prompt": item.prompt, "learning_objective": getattr(owner, "title", None)},
        "prerequisite": {"title": prerequisite_lo.title, "statement": prerequisite_lo.summary},
    }


def needed_prompt(context: Mapping[str, Any]) -> str:
    return render_structured_prompt(
        "learnloop prerequisite needed", NEEDED_PROMPT_VERSION, {"task": NEEDED_TASK_TEXT, "context": dict(context)},
    )


def ask_needed(
    repository: Repository,
    budget: TextBudget,
    *,
    context: Mapping[str, Any],
    learning_object_id: str,
    practice_item_id: str,
    judge_client: Any | None,
    decider_client: Any | None,
) -> dict[str, dict[str, Any]]:
    """Both judges' "needed?" verdicts, each appended to the ledger.

    Returns ``{judge: {"verdict", "judgment_id", "status", ...}}`` for each
    judge that was asked; a refused or failed call names its status.
    """

    from learnloop.ai.spend import SpendLimitExceeded

    out: dict[str, dict[str, Any]] = {}
    prompt = needed_prompt(context)
    input_hash = content_key({"task": NEEDED_TASK, "context": dict(context)})
    left, right = ("learning_object", learning_object_id), ("practice_item", practice_item_id)
    if judge_client is not None:
        producer = producer_label(judge_client)
        budget.register_llm(JUDGE_ROUTE, judge_client)
        try:
            with budget.request(JUDGE_ROUTE, NEEDED_PURPOSE, input_tokens=estimate_tokens(prompt)):
                verdict = execute_structured_operation(
                    judge_client, purpose=NEEDED_PURPOSE, prompt=prompt, result_model=NeededVerdict, isolated=True,
                )
            with repository.atomic():
                judgment_id = append_judgment(
                    repository.connection(), task=NEEDED_TASK, left_kind=left[0], left_id=left[1],
                    right_kind=right[0], right_id=right[1], judge="llm", judge_model=producer,
                    prompt_version=NEEDED_PROMPT_VERSION, input_hash=input_hash, verdict=verdict.verdict,
                    rationale=str(verdict.rationale or "")[:1000],
                )
            out["llm"] = {"status": "judged", "verdict": verdict.verdict, "judgment_id": judgment_id,
                          "judge_model": producer, "rationale": str(verdict.rationale or "")[:300]}
        except SpendLimitExceeded as exc:
            out["llm"] = {"status": "refused", "error": str(exc)}
        except Exception as exc:  # noqa: BLE001
            out["llm"] = {"status": "failed", "error": type(exc).__name__}
    if decider_client is not None:
        budget.register_decider(decider_client)
        model = str(getattr(decider_client, "model", None) or "unknown")
        try:
            with budget.request(DECIDER_ROUTE, NEEDED_PURPOSE, input_tokens=estimate_tokens(prompt) + 200, output_tokens=0):
                result = decider_client.decide(prompt, {"needed": NEEDED_QUESTION}, purpose=NEEDED_PURPOSE)
            answer = result.answers["needed"]
            probabilities = _probabilities(answer)
            with repository.atomic():
                judgment_id = append_judgment(
                    repository.connection(), task=NEEDED_TASK, left_kind=left[0], left_id=left[1],
                    right_kind=right[0], right_id=right[1], judge="decider", judge_model=model,
                    prompt_version=DECIDER_NEEDED_QUESTION_SET, input_hash=input_hash, verdict=answer.choice,
                    score=probabilities.get(answer.choice),
                    rationale=decider_rationale(DECIDER_NEEDED_QUESTION_SET, probabilities),
                )
            out["decider"] = {"status": "judged", "verdict": answer.choice, "judgment_id": judgment_id,
                              "judge_model": model, "probabilities": probabilities}
        except SpendLimitExceeded as exc:
            out["decider"] = {"status": "refused", "error": str(exc)}
        except Exception as exc:  # noqa: BLE001
            out["decider"] = {"status": "failed", "error": type(exc).__name__}
    return out


# -- the missing prerequisite's draft ------------------------------------------------------


def draft_prompt(context: Mapping[str, Any]) -> str:
    return render_structured_prompt(
        "learnloop missing prerequisite draft", DRAFT_PROMPT_VERSION, {"task": DRAFT_TASK, "context": dict(context)},
    )


def draft_prerequisite(budget: TextBudget, client: Any, context: Mapping[str, Any]) -> PrerequisiteDraft:
    """One authoring-route call; raises on refusal or failure (the caller logs it)."""

    budget.register_llm(DRAFT_ROUTE, client)
    prompt = draft_prompt(context)
    with budget.request(DRAFT_ROUTE, DRAFT_PURPOSE, input_tokens=estimate_tokens(prompt)):
        return execute_structured_operation(
            client, purpose=DRAFT_PURPOSE, prompt=prompt, result_model=PrerequisiteDraft, isolated=True,
        )


# -- the query embedding -------------------------------------------------------------------


def query_vector(
    repository: Repository, budget: TextBudget, embedder: Any, subject: Subject, *, field_name: str,
) -> np.ndarray | None:
    """The named gap's ``retrieval-query`` vector, stored once (a retry reuses it)."""

    model_id = str(getattr(embedder, "model_id", "") or "")
    if not model_id:
        return None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        stored = get_vector(
            connection, record_kind=subject.kind, record_id=subject.id, field=field_name,
            content_hash=subject.content_hash, model_id=model_id, task_prefix=QUERY_PREFIX,
        )
    if stored is not None:
        return stored
    budget.register_embedding(embedder)
    with budget.request(EMBEDDING_ROUTE, "embedding:learner_gap_query", input_tokens=estimate_tokens(subject.text) + 32,
                        output_tokens=0):
        vectors = embedder.embed([subject.text], QUERY_PREFIX)
    if len(vectors) != 1:
        raise ValueError("the embedding endpoint returned a different number of vectors")
    with closing(connect(repository.sqlite_path)) as connection, connection:
        put_vector(
            connection, record_kind=subject.kind, record_id=subject.id, field=field_name,
            content_hash=subject.content_hash, model_id=model_id, task_prefix=QUERY_PREFIX, vector=vectors[0],
        )
    return np.asarray(vectors[0], dtype=np.float64)


__all__ = [
    "DeciderKind",
    "DeciderPairExecutor",
    "LLMPairExecutor",
    "MODEL_CALL_OWNER_KIND",
    "TextBudget",
    "ask_needed",
    "caps_for",
    "decider_kind",
    "decider_rationale",
    "draft_prerequisite",
    "kind_state",
    "log_reading",
    "needed_context",
    "query_vector",
    "read_text",
    "reader_prompt",
]
