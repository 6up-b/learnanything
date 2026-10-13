"""Learner-text gaps with the Decider as the authoritative judge (Tier 1, mvp-0.22).

Before mvp-0.22 the LLM judge and the Decider both judged every candidate pair
and the "needed?" question, both logged, and ``learner_text_gaps.chooser``
said whose kind and prerequisite verdicts counted (beliefs: the LLM's). At
mvp-0.22 the Decider decides, and the LLM is asked only for what the Decider
gave no answer (unavailable, refused for spend, failing):

* **pairs** (same prerequisite / same belief): T1's ``judge_pairs`` asks the
  Decider first, with its claims, fencing and per-producer reuse; the argmax
  of its same / different / unsure distribution is the verdict. A pair it
  failed gets a ``judgment_ledger`` failure row and goes to the LLM judge
  through ``judge_pairs`` again. A pair another worker holds, or a fenced one,
  is unsettled and defers the reading as before; a cancellation, or a spend
  refusal of the LLM fallback, defers it with ``spend=True``.
* **needed?**: the Decider's yes / no / unsure, else the LLM's.
* **kind**: the Decider's typed kind is authoritative; the context model still
  names the gap (the Decider names nothing), and its reading's kind decides
  only when the Decider gave no answer. A kind the Decider already answered
  for the same text (a Tier-1 row on the same input) is reused, never paid for
  twice, as the predecessor's second opinion was.

Each Decider request is admitted on the text's budget under the route it is
served on, ``learner_gap_decider`` (``decider_judgments.decide``'s
``route``).

Switches: ``decider_routes.learner_gap_judge`` (pairs and needed?) and
``decider_routes.learner_gap_kind``; off, the predecessor path runs as it was.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
import json
from typing import Any

from learnloop.ai.decisions import choice_probabilities
from learnloop.ai.errors import AIInterrupted
from learnloop.ai.execution import content_key
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.decider_judgments import (
    FAILURE_VERDICTS, VERSION, Decision, NoClearAnswer, argmax, decide, record_failure,
)
from learnloop.diagnosis.recurrence.judging import estimate_tokens
from learnloop.diagnosis.text_gaps.contract import (
    DECIDER_PAIR_QUESTION_SET,
    DECIDER_ROUTE,
    KIND_QUESTION,
    NEEDED_QUESTION,
    NEEDED_TASK,
    GapReading,
    LearnerText,
)
from learnloop.diagnosis.text_gaps.judges import (
    DeciderKind,
    DeciderPairExecutor,
    LLMPairExecutor,
    TextBudget,
    decider_rationale,
    kind_input_hash,
    kind_state,
    log_reading,
    needed_prompt,
    read_text,
)
from learnloop.diagnosis.text_gaps.judges import ask_needed as ask_both_needed
from learnloop.diagnosis.text_gaps.pipeline import (
    PipelineClients,
    ReadingDeferred,
    _stopped,
    _unsettled,
    _verdicts,
    _with_standing,
    authoritative,
)
from learnloop.matching.judge import JudgedPair, SameOrDifferent, judge_pairs, pair_input_hash
from learnloop.vault.models import LoadedVault

#: The switch of the pair and "needed?" judgments, and of the kind.
JUDGE_SWITCH = "learner_gap_judge"
KIND_SWITCH = "learner_gap_kind"


#: Marks a pair verdict the Tier-1 executor took as the argmax (review F9).
ARGMAX_PRODUCER_SUFFIX = "#argmax"


class ArgmaxPairExecutor(DeciderPairExecutor):
    """The Decider as the authoritative pair judge: the argmax of its distribution decides.

    Its producer (the ledger's ``judge_model``, which ``judge_pairs`` keys its
    claims and reuse on) is the model marked :data:`ARGMAX_PRODUCER_SUFFIX`:
    a predecessor second opinion on the same pair took the response's choice
    field, so it is never reused as a deciding verdict (review F9); the pair
    is asked once more under Tier 1, and that verdict is reused from then on.
    """

    def __init__(self, budget: TextBudget, client: Any) -> None:
        super().__init__(budget, client)
        self.producer = f"{self.producer}{ARGMAX_PRODUCER_SUFFIX}"

    def __call__(self, prompt: str, result_model: type[SameOrDifferent], purpose: str) -> tuple[SameOrDifferent, str]:
        with self.budget.request(DECIDER_ROUTE, purpose, input_tokens=estimate_tokens(prompt) + 200,
                                 output_tokens=0):
            result = self.client.decide(prompt, {"verdict": self.question}, purpose=purpose)
        probabilities = choice_probabilities(result.answers["verdict"], self.question)
        choice = argmax(probabilities)
        if choice is None:
            # A same / different tie is no answer (review F8): the pair goes to the LLM.
            raise NoClearAnswer("the Decider's top options are tied")
        rounded = {option: round(float(value), 4) for option, value in probabilities.items()}
        return result_model(verdict=choice, rationale=decider_rationale(DECIDER_PAIR_QUESTION_SET, rounded)), \
            self.producer


def _failure_status(pair: JudgedPair) -> str:
    if pair.error == "SpendLimitExceeded":
        return "refused"
    if pair.error == "AIProviderUnavailable":
        return "unavailable"
    if pair.error == NoClearAnswer.__name__:
        return "tied"
    return "failed"


def _record_failures(repository: Repository, kind: Any, pairs: Sequence[Any], *, model: str,
                     statuses: Mapping[int, tuple[str, str | None]]) -> None:
    for index, (status, error) in statuses.items():
        pair = pairs[index]
        record_failure(repository, Decision(
            kind.task, pair_input_hash(kind, pair.left, pair.right), pair.left.kind, pair.left.id,
            pair.right.kind, pair.right.id, status=status, model=model,
        ), error=error)


def judge_all(repository: Repository, kind: Any, pairs: list, *, budget: TextBudget,
              clients: PipelineClients) -> dict[str, Any]:
    """The Decider's verdict on every pair, the LLM's where it gave none (see the module doc).

    ``selected`` holds the deciding verdicts (None when neither judge is
    available), ``selected_judges`` which judge gave each, and
    ``selected_unsettled`` the pairs without one.
    """

    out: dict[str, Any] = {
        "authority": "selected", "selected": {}, "selected_judges": {}, "selected_unsettled": [],
        "llm": None, "decider": None, "llm_results": [], "decider_results": [],
        "llm_unsettled": [], "decider_unsettled": [],
    }
    if not pairs:
        return out
    decider, judge = clients.get("decider"), clients.get("judge")
    if decider is None and judge is None:
        out["selected"] = None
        return out
    fallback: list[int] = list(range(len(pairs)))
    failures: dict[int, tuple[str, str | None]] = {}
    if decider is not None:
        executor = ArgmaxPairExecutor(budget, decider)
        # A spend refusal of the Decider is a failure it hands to the LLM;
        # only a cancellation stops the batch.
        results = _with_standing(
            repository, kind, judge_pairs(repository, kind, pairs, execute=executor, stop_on=(AIInterrupted,)),
            judge="decider", producer=executor.producer,
        )
        stop = _stopped(results)
        if stop is not None:
            raise ReadingDeferred(f"decider pair judging stopped: {stop}", spend=True)
        out["decider"] = _verdicts(results)
        out["decider_unsettled"] = _unsettled(results)
        out["decider_results"] = [pair.as_dict() for pair in results]
        for subject_id, verdict in out["decider"].items():
            out["selected"][subject_id] = verdict
            out["selected_judges"][subject_id] = "decider"
        # Only a pair the Decider FAILED falls back; one another worker holds,
        # or a fenced one, waits for its verdict (the reading is deferred).
        fallback = [index for index, pair in enumerate(results) if pair.status == "failed"]
        failures = {index: (_failure_status(results[index]), results[index].error) for index in fallback}
        model = executor.producer
    else:
        failures = {index: ("unavailable", None) for index in fallback}
        model = "unavailable"
    _record_failures(repository, kind, pairs, model=model, statuses=failures)
    if fallback and judge is not None:
        executor = LLMPairExecutor(budget, judge)
        asked = [pairs[index] for index in fallback]
        results = _with_standing(repository, kind, judge_pairs(repository, kind, asked, execute=executor),
                                 judge="llm", producer=executor.producer)
        stop = _stopped(results)
        if stop is not None:
            raise ReadingDeferred(f"llm pair judging stopped: {stop}", spend=True)
        out["llm"] = _verdicts(results)
        out["llm_unsettled"] = _unsettled(results)
        out["llm_results"] = [pair.as_dict() for pair in results]
        for subject_id, verdict in out["llm"].items():
            out["selected"][subject_id] = verdict
            out["selected_judges"][subject_id] = "llm"
    out["selected_unsettled"] = [
        {"id": pair.right.id, "status": failures.get(index, ("unsettled", None))[0],
         "error": failures.get(index, (None, None))[1]}
        for index, pair in enumerate(pairs) if pair.right.id not in out["selected"]
    ]
    return out


def ask_needed(vault: LoadedVault, repository: Repository, budget: TextBudget, *, context: Mapping[str, Any],
               learning_object_id: str, practice_item_id: str, clients: PipelineClients) -> dict[str, dict[str, Any]]:
    """The Decider's "needed?" verdict, else the LLM judge's; ``selected`` is the deciding one."""

    decision = decide(
        root=vault.root, config=vault.config, repository=repository, task=JUDGE_SWITCH, ledger_task=NEEDED_TASK,
        state=needed_prompt(context), question=NEEDED_QUESTION, question_name="needed",
        left_kind="learning_object", left_id=learning_object_id,
        right_kind="practice_item", right_id=practice_item_id, spend=budget.spend,
        input_hash=content_key({"task": NEEDED_TASK, "context": dict(context)}),
        client_factory=lambda: clients.get("decider"), route=DECIDER_ROUTE,
    )
    decided = {"status": "judged" if decision.choice is not None else decision.status,
               "verdict": decision.choice, "judgment_id": decision.judgment_id, "judge_model": decision.model,
               "probabilities": decision.probabilities}
    if decision.choice is not None:
        return {"decider": decided, "selected": {**decided, "judge": "decider"}}
    # The predecessor LLM call, its output policy and its ledger row, unchanged.
    fallback = ask_both_needed(repository, budget, context=context, learning_object_id=learning_object_id,
                               practice_item_id=practice_item_id, judge_client=clients.get("judge"),
                               decider_client=None)
    llm = fallback.get("llm") or {"status": "unavailable"}
    return {"decider": decided, "llm": llm, "selected": {**llm, "judge": "llm"}}


def _recorded_kind(repository: Repository, text: LearnerText) -> Decision | None:
    """The Decider's Tier-1 answer already on the ledger for this text's kind, or None.

    The same text and context (the input hash) under the same question set:
    a reading taken up again (a job whose progress predates its decision, a
    re-review) reuses the paid answer, as ``judges.decider_kind`` reused its
    second opinion. A row holding no answer is never reused.
    """

    input_hash = kind_input_hash(text)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            "SELECT id, verdict, judge_model, rationale FROM judgment_ledger WHERE task = ? AND left_kind = ? "
            "AND left_id = ? AND judge = 'decider' AND prompt_version = ? AND input_hash = ? "
            "ORDER BY created_at DESC, rowid DESC",
            (KIND_SWITCH, text.source_kind, text.source_id, VERSION, input_hash),
        ).fetchall()
    for row in rows:
        verdict = str(row[1])
        if verdict in FAILURE_VERDICTS or verdict not in KIND_QUESTION.options:
            continue
        try:
            detail = json.loads(row[3] or "{}")
        except (TypeError, ValueError):
            detail = {}
        probabilities = detail.get("probabilities") if isinstance(detail, dict) else None
        decision = Decision(KIND_SWITCH, input_hash, text.source_kind, text.source_id, status="ok", choice=verdict,
                            probabilities=dict(probabilities) if isinstance(probabilities, dict) else {},
                            model=str(row[2] or "unknown"), judgment_id=str(row[0]))
        return decision
    return None


def decide_kind(
    vault: LoadedVault, repository: Repository, text: LearnerText, budget: TextBudget, clients: PipelineClients,
    progress: Mapping[str, Any], checkpoint: Callable[..., None],
) -> tuple[GapReading | None, DeciderKind, str, str]:
    """The Decider's kind, authoritative; the context model names the gap (``pipeline._decide``)."""

    result = _recorded_kind(repository, text) or decide(
        root=vault.root, config=vault.config, repository=repository, task=KIND_SWITCH, state=kind_state(text),
        question=KIND_QUESTION, question_name="kind", left_kind=text.source_kind, left_id=text.source_id,
        input_hash=kind_input_hash(text), spend=budget.spend, client_factory=lambda: clients.get("decider"),
        route=DECIDER_ROUTE,
    )
    decider = DeciderKind("ok" if result.choice is not None else result.status, choice=result.choice,
                          probabilities=result.probabilities, model=result.model, judgment_id=result.judgment_id)
    reading = text.reading
    # A stuck answer has no context model's reading: one reader call names
    # its gap, unless the Decider says there is none to name.
    if reading is None and text.context_judge == "gap_reader" and result.choice in (None, "prerequisite", "misconception"):
        if isinstance(progress.get("reading"), Mapping):
            # Read by an earlier attempt that stopped: never paid for twice.
            reading = GapReading.from_progress(progress["reading"])
        else:
            reader = clients.get("reader")
            reading = read_text(budget, reader, text) if reader is not None else GapReading(
                "none", judge="llm", status="unavailable", prompt_version="")
            if reading.status == "refused":
                raise ReadingDeferred("the stuck-text reading was refused", spend=True)
            if reading.status == "ok":
                checkpoint(reading=reading.as_progress())
    if reading is not None and reading.status == "ok":
        log_reading(repository, text, reading)
    # The Decider's kind decides; without its answer the context model's does.
    chooser = "decider" if result.choice is not None else "context_model"
    kind = authoritative(chooser, reading, decider)
    checkpoint(decided={"reading": reading.as_progress() if reading is not None else None,
                        "decider": decider.as_dict(), "chooser": chooser, "kind": kind})
    return reading, decider, chooser, kind


__all__ = ["ARGMAX_PRODUCER_SUFFIX", "ArgmaxPairExecutor", "JUDGE_SWITCH", "KIND_SWITCH", "ask_needed", "decide_kind", "judge_all"]
