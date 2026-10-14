"""The one-time judgment on a statement that must not be rewritten (redesign 2026-10-14).

Method-explicit items read ONE structured authority: the item's
``required_method`` field, frozen with the assessment contract. Grading never
parses prompt text. Two kinds of statement cannot simply carry the canonical
sentence ("Use {method} in your answer.") without a question being asked
about their wording, and each is asked ONCE, when the item is written, never
again at grading time:

* **a source statement** (a textbook exercise's verbatim stem, at import):
  does it require the learner to use the method its author proposed? Choices
  ``requires`` / ``allows`` / ``prohibits``. Only ``requires`` keeps the
  field (``statement = source``, ``decided_by = judgment``);
* **a variant stem** (a PF variant of a parent that requires a method, at
  publication): does it prohibit or contradict that method? Choices
  ``consistent`` / ``contradicts``. ``contradicts`` refuses the publication;
  ``consistent`` lets the writer append the canonical sentence.

**The judge** is the Decider through its route (``ai.routing.
rubric_phrasing_judge`` when it names a decider profile, else the code-default
``openrouter_decider`` profile when that is ready), else the existing LLM
judge on that route (the route's chat profile, else the serving chat
provider): the same resolution as ``learnloop grading method-phrasing``
(:func:`learnloop.content.proposals.method_phrasing.resolve_judge`). There is
no heuristic fallback: with no judge ready nothing is decided (a source
statement keeps no requirement; a variant is not published yet).

**The decision** is the argmax of the Decider's probabilities (no hand-set
threshold; a tie goes to the conservative option: not ``requires``, and
``contradicts``), or the LLM judge's one label. Every verdict is appended to
``judgment_ledger`` (task ``required_method_statement``) with its
probabilities, and a statement already judged under the same question, text
and method reuses its row: the judgment is made once.

**Spend.** Every request is admitted before it is sent on its own
:class:`~learnloop.diagnosis.offline_review.spend.ReviewSpend` (the Decider at
its profile's listed input price; a metered LLM judge at the owner's price,
refused without one; a subscription judge ``estimated_only``) and leaves a
``model_call`` receipt owned by the caller (the import, or the PF run).
"""

from __future__ import annotations

import json
from contextlib import closing
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Mapping

from pydantic import Field

from learnloop.ai.execution import content_key
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendCaps
from learnloop.ai.transport import execute_structured_operation, render_structured_prompt
from learnloop.clock import Clock, utc_now_iso
from learnloop.content.proposals.method_phrasing import ROUTE as LLM_ROUTE
from learnloop.content.proposals.method_phrasing import decider_profile_name, ready_profile_client, ready_writer
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.judgments import append_judgment
from learnloop.diagnosis.offline_review.spend import ReviewSpend, RouteInfo
from learnloop.diagnosis.recurrence.judging import receipt_sink
from learnloop.vault.models import LoadedVault
from learnloop.vault.required_method import (
    SOURCE_REQUIRES,
    SourceStatementDecision,
    required_method_instruction,
)

#: ``judgment_ledger`` task of every verdict here.
TASK = "required_method_statement"
#: The Decider's question sets (its ``prompt_version`` in the ledger).
SOURCE_QUESTION_SET = "required-method-source-v1"
VARIANT_QUESTION_SET = "required-method-variant-v1"
#: The LLM judge's prompt version (the question set is in the input).
LLM_PROMPT_VERSION = "required-method-statement-llm-v1"
PURPOSE = "required_method_statement"
DECIDER_ROUTE = "required_method_decider"
Question = Literal["source", "variant"]
JudgeKind = Literal["decider", "llm"]

#: The source question's options.
SOURCE_OPTIONS = {
    "requires": (
        "The statement instructs the learner to use this method: an answer that reaches the result by another "
        "method does not do what the statement asks."
    ),
    "allows": (
        "The statement names, describes, suggests or offers this method, or shows it in an example, but an answer "
        "by another valid method still does what the statement asks."
    ),
    "prohibits": "The statement forbids this method or asks for a different one.",
}
#: The variant question's options.
VARIANT_OPTIONS = {
    "consistent": (
        "Nothing in the stem forbids the method, says it is not needed or optional, or asks for another method: "
        "adding the sentence agrees with the stem."
    ),
    "contradicts": (
        "The stem forbids the method, says it is not needed or optional, or asks for another method: adding the "
        "sentence would contradict the stem."
    ),
}
#: Argmax tie-break order: the conservative option first (never fail a
#: learner for a method nobody decided is required; never publish a stem that
#: may contradict its rubric).
CONSERVATIVE_ORDER: dict[Question, tuple[str, ...]] = {
    "source": ("allows", "prohibits", "requires"),
    "variant": ("contradicts", "consistent"),
}
OPTIONS: dict[Question, dict[str, str]] = {"source": SOURCE_OPTIONS, "variant": VARIANT_OPTIONS}
QUESTION_SETS: dict[Question, str] = {"source": SOURCE_QUESTION_SET, "variant": VARIANT_QUESTION_SET}
CONTRADICTS = "contradicts"
CONSISTENT = "consistent"
#: Output tokens an LLM judgment is admitted with (one label and a sentence).
LLM_OUTPUT_TOKENS = 400


def default_caps(calls: int = 50) -> SpendCaps:
    """One run's bound: ``calls`` judgments and $0.25 (a Decider request costs
    about $0.00002; an LLM judgment about $0.001 at Haiku's price)."""

    calls = max(1, int(calls))
    return SpendCaps(max_candidates=0, max_pairs=0, max_retries=max(4, calls), max_calls=calls,
                     max_total_tokens=calls * 8_000, max_estimated_usd=0.25)


def _estimate_tokens(text: str) -> int:
    """An upper bound on ``text``'s input tokens: its UTF-8 bytes."""

    return len(text.encode("utf-8"))


def _instructions(question: Question, method: str) -> str:
    if question == "source":
        return (
            f"The method is \"{method}\". Read the statement as a learner would. Does it require the learner to "
            "use this method?"
        )
    return (
        f"The parent exercise requires the method \"{method}\", and the sentence "
        f"\"{required_method_instruction(method)}\" will be appended to this stem. Does the stem prohibit or "
        "contradict that method?"
    )


def decider_state(question: Question, statement: str, method: str) -> str:
    """What the Decider reads (the statement verbatim)."""

    if question == "source":
        lead = "A textbook exercise statement, quoted verbatim (it will not be rewritten)."
    else:
        lead = "A generated variant of an exercise whose rubric grades use of a required method."
    return "\n".join([lead, f"Required method: {method}", "Statement:", statement])


def decider_question(question: Question, method: str) -> Any:
    from learnloop.ai.decisions import ChoiceQuestion

    return ChoiceQuestion(instructions=_instructions(question, method), options=dict(OPTIONS[question]))


class SourceStatementReading(WireModel):
    verdict: Literal["requires", "allows", "prohibits"]
    rationale: str = Field(default="", description="One sentence.")


class VariantStemReading(WireModel):
    verdict: Literal["consistent", "contradicts"]
    rationale: str = Field(default="", description="One sentence.")


READING_MODELS: dict[Question, type[WireModel]] = {"source": SourceStatementReading, "variant": VariantStemReading}


def llm_prompt(question: Question, statement: str, method: str) -> str:
    task = (
        _instructions(question, method)
        + " Return `verdict`, one of: "
        + "; ".join(f"`{key}`: {text}" for key, text in OPTIONS[question].items())
        + ". Judge the wording only; do not solve the exercise."
    )
    return render_structured_prompt(
        "learnloop required method statement judgment", LLM_PROMPT_VERSION,
        {"task": task, "context": {"question": QUESTION_SETS[question], "method": method, "statement": statement}},
    )


def statement_input_hash(question: Question, statement: str, method: str) -> str:
    """The judged input: the question set, the statement verbatim and the method's name."""

    return content_key({"task": TASK, "question": QUESTION_SETS[question], "statement": str(statement),
                        "method": " ".join(str(method).split())})


def planned_tokens(question: Question, statement: str, method: str) -> int:
    """An upper bound on one judgment's tokens, from text alone (a dry run):
    the larger of the Decider's request and the LLM judge's prompt, schema
    and output allowance."""

    asked = decider_question(question, method)
    decider = _estimate_tokens(decider_state(question, statement, method)) + _estimate_tokens(
        asked.instructions + json.dumps(asked.options, sort_keys=True))
    llm = (_estimate_tokens(llm_prompt(question, statement, method))
           + _estimate_tokens(json.dumps(READING_MODELS[question].model_json_schema())) + LLM_OUTPUT_TOKENS)
    return max(decider, llm)


def argmax(question: Question, probabilities: Mapping[str, float]) -> str:
    """The most probable option; a tie goes to the conservative one."""

    order = CONSERVATIVE_ORDER[question]
    known = {key: float(value) for key, value in probabilities.items() if key in order}
    if not known:
        raise ValueError(f"no probability for any {question} option")
    best = max(known.values())
    return next(option for option in order if known.get(option) == best)


@dataclass(frozen=True)
class StatementVerdict:
    """One judgment: the deciding option and its ledger row."""

    question: Question
    verdict: str
    judge: str
    judge_model: str
    judgment_id: str
    probabilities: dict[str, float] = field(default_factory=dict)
    #: True when an earlier row for the same input was reused (no new call).
    reused: bool = False


def recorded_verdict(
    connection: Any, *, question: Question, subject_kind: str, subject_id: str, statement: str, method: str,
) -> StatementVerdict | None:
    """The verdict already recorded for this statement and method, if any.

    Any judge's row counts (the judgment is made once); the latest wins.
    """

    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='judgment_ledger'").fetchone() is None:
        return None
    row = connection.execute(
        "SELECT id, judge, judge_model, verdict, rationale FROM judgment_ledger WHERE task = ? AND left_kind = ? "
        "AND left_id = ? AND input_hash = ? ORDER BY created_at DESC, id DESC LIMIT 1",
        (TASK, subject_kind, subject_id, statement_input_hash(question, statement, method)),
    ).fetchone()
    if row is None:
        return None
    try:
        rationale = json.loads(row[4] or "{}")
    except ValueError:
        rationale = {}
    probabilities = {str(key): float(value) for key, value in dict(rationale.get("probabilities") or {}).items()}
    return StatementVerdict(question, str(row[3]), str(row[1]), str(row[2] or ""), str(row[0]),
                            probabilities=probabilities, reused=True)


class MethodStatementJudge:
    """A resolved judge (the Decider, or the LLM judge) with its own spend."""

    def __init__(self, kind: JudgeKind, client: Any, *, spend: ReviewSpend, provider: str | None = None) -> None:
        self.kind = kind
        self.client = client
        self.spend = spend
        self.provider = provider
        self.model = str(getattr(client, "model", None) or "unknown")
        if kind == "decider":
            settings = getattr(client, "settings", None)
            price = getattr(settings, "price_per_million_input", None)
            spend.routes[DECIDER_ROUTE] = RouteInfo(
                DECIDER_ROUTE, getattr(client, "provider_name", None), getattr(client, "model", None), "metered",
                float(price) if price is not None else None, "listed_input_price" if price is not None else "unknown",
                0,
            )
        else:
            spend.register(LLM_ROUTE, client)

    def judge(
        self,
        repository: Repository,
        *,
        question: Question,
        subject_kind: str,
        subject_id: str,
        statement: str,
        method: str,
        owner: tuple[str, str],
        right: tuple[str, str] | None = None,
        clock: Clock | None = None,
    ) -> StatementVerdict:
        """The verdict for this statement: reused when recorded, else asked once and ledgered.

        Raises on a refusal (``SpendLimitExceeded``) or a failure; the caller
        treats that as no decision.
        """

        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            existing = recorded_verdict(connection, question=question, subject_kind=subject_kind,
                                        subject_id=subject_id, statement=statement, method=method)
        if existing is not None:
            return existing
        input_hash = statement_input_hash(question, statement, method)
        previous_sink = self.spend.collector.sink
        self.spend.collector.sink = receipt_sink(repository, owner_kind=owner[0], owner_id=owner[1])
        try:
            if self.kind == "decider":
                state = decider_state(question, statement, method)
                asked = decider_question(question, method)
                tokens = _estimate_tokens(state) + _estimate_tokens(
                    asked.instructions + json.dumps(asked.options, sort_keys=True))
                with self.spend.collector.observing():
                    with self.spend.request(DECIDER_ROUTE, PURPOSE, input_tokens=tokens, output_tokens=0):
                        result = self.client.decide(state, {"verdict": asked}, purpose=PURPOSE)
                answer = result.answers["verdict"]
                probabilities = {str(key): round(float(value), 4)
                                 for key, value in dict(getattr(answer, "probabilities", {}) or {}).items()}
                if not probabilities:
                    probabilities = {str(answer.choice): 1.0}
                verdict = argmax(question, probabilities)
                prompt_version, rationale_text = QUESTION_SETS[question], ""
            else:
                prompt = llm_prompt(question, statement, method)
                tokens = _estimate_tokens(prompt) + _estimate_tokens(
                    json.dumps(READING_MODELS[question].model_json_schema()))
                with self.spend.collector.observing():
                    with self.spend.request(LLM_ROUTE, PURPOSE, input_tokens=tokens, output_tokens=LLM_OUTPUT_TOKENS):
                        reading = execute_structured_operation(
                            self.client, purpose=PURPOSE, prompt=prompt, result_model=READING_MODELS[question],
                            isolated=True,
                        )
                verdict = str(reading.verdict)
                probabilities = {verdict: 1.0}
                prompt_version, rationale_text = LLM_PROMPT_VERSION, str(reading.rationale or "")[:500]
        finally:
            self.spend.collector.sink = previous_sink
        rationale = json.dumps({
            "question": QUESTION_SETS[question], "method": method, "probabilities": probabilities,
            "decision": "argmax" if self.kind == "decider" else "label", "rationale": rationale_text,
        }, sort_keys=True)
        with repository.atomic():
            judgment_id = append_judgment(
                repository.connection(), task=TASK, left_kind=subject_kind, left_id=subject_id,
                right_kind=right[0] if right else None, right_id=right[1] if right else None,
                judge=self.kind, judge_model=self.model, prompt_version=prompt_version, input_hash=input_hash,
                verdict=verdict, score=probabilities.get(verdict) if self.kind == "decider" else None,
                rationale=rationale, created_at=utc_now_iso(clock),
            )
        return StatementVerdict(question, verdict, self.kind, self.model, judgment_id, probabilities=probabilities)


def _injected(clients: Any) -> dict[str, Any] | None:
    """Tests (and callers) may inject the judge: a Decider client (it has
    ``decide``), an LLM client, or a mapping ``{"decider": ..., "llm": ...}``."""

    if clients is None:
        return None
    if isinstance(clients, Mapping):
        return dict(clients)
    if callable(getattr(clients, "decide", None)):
        return {"decider": clients}
    return {"decider": None, "llm": clients}


def resolve_statement_judge(
    vault: LoadedVault,
    *,
    clients: Any = None,
    price_per_million: float | None = None,
    caps: SpendCaps | None = None,
) -> MethodStatementJudge | None:
    """The Decider via its route, else the LLM judge on it; None when neither is ready."""

    injected = _injected(clients) or {}
    spend = ReviewSpend(caps or default_caps(), price_per_million=price_per_million, config=vault.config)
    decider_name = decider_profile_name(vault)
    client = injected.get("decider")
    if client is None and "decider" not in injected and decider_name is not None:
        client = ready_profile_client(vault, decider_name)
    if client is not None:
        return MethodStatementJudge("decider", client, spend=spend,
                                    provider=getattr(client, "provider_name", None) or decider_name)
    writer, provider = ready_writer(vault, injected)
    if writer is not None:
        return MethodStatementJudge("llm", writer, spend=spend, provider=provider)
    return None


class LazyStatementJudge:
    """Resolves the judge on first use (most writes never need one), once."""

    def __init__(self, resolve: Callable[[], MethodStatementJudge | None]) -> None:
        self._resolve = resolve
        self._resolved = False
        self._judge: MethodStatementJudge | None = None
        self.error: str | None = None

    def get(self) -> MethodStatementJudge | None:
        if not self._resolved:
            self._resolved = True
            try:
                self._judge = self._resolve()
            except Exception as exc:  # noqa: BLE001 - an unresolvable judge decides nothing
                self.error = type(exc).__name__
                self._judge = None
        return self._judge


def as_lazy(judge: Any) -> LazyStatementJudge:
    if isinstance(judge, LazyStatementJudge):
        return judge
    return LazyStatementJudge(lambda: judge)


def source_judge(
    judge: Any,
    repository: Repository,
    *,
    subject_id: str,
    owner: tuple[str, str],
    clock: Clock | None = None,
    log: Callable[[str], None] | None = None,
) -> Callable[[str, str], SourceStatementDecision | None]:
    """The ``judge_source`` callback the writer check takes for one source
    statement (``learnloop.vault.required_method.normalize_required_method``):
    the one-time judgment, or None when no judge is ready or it refused or
    failed (``log`` hears why)."""

    lazy = as_lazy(judge)

    def decide(statement: str, method: str) -> SourceStatementDecision | None:
        resolved = lazy.get()
        if resolved is None:
            if log is not None:
                log("no judge is ready" + (f" ({lazy.error})" if lazy.error else ""))
            return None
        try:
            verdict = resolved.judge(repository, question="source", subject_kind="practice_item",
                                     subject_id=subject_id, statement=statement, method=method, owner=owner,
                                     right=("required_method", method), clock=clock)
        except Exception as exc:  # noqa: BLE001 - no decision: the requirement is dropped
            if log is not None:
                log(f"the judgment failed ({type(exc).__name__})")
            return None
        return SourceStatementDecision(verdict=verdict.verdict, judgment_id=verdict.judgment_id)

    return decide


__all__ = [
    "CONSERVATIVE_ORDER",
    "CONSISTENT",
    "CONTRADICTS",
    "DECIDER_ROUTE",
    "LLM_PROMPT_VERSION",
    "LazyStatementJudge",
    "MethodStatementJudge",
    "PURPOSE",
    "SOURCE_OPTIONS",
    "SOURCE_QUESTION_SET",
    "SOURCE_REQUIRES",
    "SourceStatementReading",
    "StatementVerdict",
    "TASK",
    "VARIANT_OPTIONS",
    "VARIANT_QUESTION_SET",
    "VariantStemReading",
    "argmax",
    "as_lazy",
    "decider_question",
    "decider_state",
    "default_caps",
    "llm_prompt",
    "planned_tokens",
    "recorded_verdict",
    "resolve_statement_judge",
    "source_judge",
    "statement_input_hash",
]
