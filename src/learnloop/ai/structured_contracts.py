"""One shared step for structured answers that parse but break their contract.

A structured answer can match its wire schema and still come back empty or
defaulted where the schema allows it. A caller declares a :data:`Contract`:
named, pure predicates over the parsed answer, each with one fixed requirement
line. :func:`checked_structured_call` checks the answer against them in
declared order (the first failure wins), discards a rejected answer and asks
once more with the original prompt plus that requirement
(:func:`correction_prompt`). The first request is sent exactly as the caller
built it; only the correction carries the suffix, and never the rejected answer.

One contract recovery per logical call (:data:`MAX_STRUCTURED_RECOVERIES`).
Each attempt may also use its provider's one schema repair, independently of
that credit. Every recovery is the caller's own: it is sent only
when the caller's ``admit`` says its retry slot and budget allow one, inside the
caller's remaining time and before any cancellation. With none of that, nothing
further is sent and the caller's own failure is raised through ``failure``.

A rejected answer finishes its operation receipt as failed (the answer stays on
it, for analysis) and is never saved; a checkpoint that fails the contract is
discarded by its exact stored value; only an accepted answer is saved, under the
original request's key, so a corrected answer is reused after a restart. A
correction's root receipt carries a :data:`RECOVERY_NOTE` naming that key, the
failed predicate and the recovery's ordinal (:func:`recover_from_receipts`).

Nothing here acts unless a caller declares a contract: with no checked call
active, the hooks the transport and the providers read
(:func:`claim_schema_repair`, :func:`recovery_remaining_seconds`,
:func:`correction_in_flight`) leave every request as it was.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from contextlib import nullcontext
from contextvars import ContextVar
from dataclasses import dataclass
import json
import re
from typing import Any, Generic, TypeVar

from learnloop.ai.errors import AIInvalidOutput, AIOutputTruncated
from learnloop.ai.execution import ModelCheckpoint, annotate_calls, content_key

T = TypeVar("T")

#: Contract re-asks one logical structured call may send. Provider schema
#: repairs do not spend this count; each attempt may repair once, when admitted.
MAX_STRUCTURED_RECOVERIES = 1

#: The ``budget_json`` key a correction's root receipt carries (``annotate_calls``).
RECOVERY_NOTE = "structured_recovery"

_PREDICATE_NAME = re.compile(r"[a-z][a-z0-9_]*")
#: Why a recovery was not sent; also the failure reason the caller receives.
_REFUSALS = frozenset({"recovery_spent", "cancelled", "deadline", "recovery_refused"})


@dataclass(frozen=True)
class Predicate(Generic[T]):
    """One named obligation of a parsed answer.

    ``holds`` is pure: it reads the answer and facts the caller already put in
    the request, and returns a bool. ``requirement`` is the fixed line the
    correction states. It goes to the model, so it is a constant (or built only
    from request facts the model was already given): never exception text, a
    hidden record or the rejected answer.
    """

    name: str
    holds: Callable[[T], bool]
    requirement: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not _PREDICATE_NAME.fullmatch(self.name):
            raise ValueError(f"a predicate name is snake_case: {self.name!r}")
        text = self.requirement
        if not isinstance(text, str) or not text.strip() or text != text.strip() or "\n" in text or "\r" in text:
            raise ValueError(f"predicate {self.name!r} needs one nonblank requirement line")


#: A call's contract: its predicates in the order they are checked. An empty
#: contract is a declaration that the schema already says everything required.
Contract = tuple[Predicate[T], ...]


def contract_of(*predicates: Predicate[Any]) -> tuple[Predicate[Any], ...]:
    """``predicates`` as a contract, refused when one is not a :class:`Predicate`
    or two share a name (a correction names its predicate; two would be ambiguous)."""

    names: set[str] = set()
    for predicate in predicates:
        if not isinstance(predicate, Predicate):
            raise TypeError(f"a contract holds predicates, not {type(predicate).__name__}")
        if predicate.name in names:
            raise ValueError(f"two predicates are named {predicate.name!r}")
        names.add(predicate.name)
    return tuple(predicates)


def first_failure(contract: Iterable[Predicate[T]], answer: T) -> Predicate[T] | None:
    """The first predicate ``answer`` fails, in declared order, or None."""

    for predicate in contract:
        verdict = predicate.holds(answer)
        if not isinstance(verdict, bool):
            # A truthy list or None would pass or fail by accident.
            raise TypeError(f"predicate {predicate.name!r} returned {type(verdict).__name__}, not bool")
        if not verdict:
            return predicate
    return None


def correction_prompt(first_prompt: str, predicate: Predicate[Any]) -> str:
    """The correction: the original prompt, then the failed predicate and its requirement."""

    return (f"{first_prompt}\n\nThe previous answer failed validation: {predicate.name}. "
            f"{predicate.requirement} "
            "Write the complete answer again, satisfying all the original requirements.")


class ContractRejected(Exception):
    """A parsed answer failed a contract predicate.

    Deliberately not an ``AIProviderUnavailable``: a caller's outage retry must
    not catch it and start a fresh request outside the shared recovery.
    """

    def __init__(self, predicate: Predicate[Any]) -> None:
        super().__init__(f"the structured answer failed its contract: {predicate.name}")
        self.predicate = predicate


@dataclass(frozen=True)
class RecoveryState:
    """What one logical call has spent, in the form a durable job stores and restores.

    ``recoveries`` counts the contract re-asks claimed. ``owed`` names the
    predicate whose correction the call owes once an answer was rejected; it
    is recorded before anything else, so a restart sends that correction,
    not the first request again.
    """

    recoveries: int = 0
    owed: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.recoveries, bool) or not isinstance(self.recoveries, int) or self.recoveries < 0:
            raise ValueError("recoveries is a nonnegative int")

    def as_dict(self) -> dict[str, Any]:
        return {"recoveries": self.recoveries, "owed": self.owed}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> RecoveryState:
        data = data or {}
        owed = data.get("owed")
        return cls(recoveries=data.get("recoveries", 0), owed=str(owed) if owed is not None else None)


@dataclass(frozen=True)
class RecoveryAllowance:
    """The caller's own room for the one recovery; it holds no money of its own.

    ``admit`` is the caller's retry slot and budget: called last, just before a
    recovery would be sent, it returns whether the caller admits one more
    request (and may reserve it). None means nothing authorizes another
    request, so none is sent: a timeout or an output budget is not a spend
    authorization. ``remaining_seconds`` is what is left of the call's one
    deadline (None: the caller set none); a recovery needs more than
    ``min_request_seconds`` of it. ``cancelled`` stops a recovery before it is
    sent. ``state`` is restored from a durable job and ``record`` stores each
    new state before the request it allows is sent. With ``defer`` the
    correction is recorded as owed and the call fails with
    ``correction_deferred``, for a job that sends it on its next run.
    """

    admit: Callable[[], bool] | None = None
    remaining_seconds: Callable[[], float | None] | None = None
    min_request_seconds: float = 0.0
    cancelled: Callable[[], bool] | None = None
    state: RecoveryState = RecoveryState()
    record: Callable[[RecoveryState], None] | None = None
    defer: bool = False


@dataclass(frozen=True)
class ContractFailure:
    """Why a checked call ended without an accepted answer, for the caller's ``failure``.

    ``reason``: ``contract_failed`` (the last answer failed ``predicate`` and no
    recovery is left), ``schema_failed`` (a recovery's answer did not parse),
    ``recovery_refused`` / ``deadline`` / ``cancelled`` (the recovery was not
    sent), ``correction_deferred`` (owed, recorded, for the next run) or
    ``unknown_requirement`` (a restored ``owed`` the contract no longer
    declares). ``sends`` counts the requests this run sent.
    """

    reason: str
    predicate: str | None
    state: RecoveryState
    sends: int


@dataclass(frozen=True)
class Attempt:
    """One request the caller's ``send`` makes: the first (ordinal 0) or a correction."""

    ordinal: int
    prompt: str
    #: What remains of the call's deadline when it is sent; None when the caller set none.
    timeout_seconds: float | None
    #: The predicate a correction answers; None on the first request.
    correcting: str | None = None


@dataclass(frozen=True)
class CheckedAnswer(Generic[T]):
    answer: T
    #: Served from the checkpoint: nothing was sent.
    reused: bool
    sends: int
    state: RecoveryState
    #: The predicate a stored answer failed when it was discarded on load.
    discarded: str | None = None


class _Ledger:
    """The one recovery of the checked call in flight, as the hooks below see it."""

    def __init__(self, allowance: RecoveryAllowance) -> None:
        self.allowance = allowance
        self.state = allowance.state
        self.ordinal = 0
        #: What a provider's schema repair met during the current attempt:
        #: None (not asked), "claimed", or the refusal.
        self.repair: str | None = None

    def remaining(self) -> float | None:
        remaining = self.allowance.remaining_seconds
        return None if remaining is None else remaining()

    def note(self, state: RecoveryState) -> None:
        self.state = state
        if self.allowance.record is not None:
            self.allowance.record(state)

    def claim(self, owed: str | None) -> str | None:
        """Spend the recovery (recorded before it is sent), or say why not.

        ``admit`` comes last: it may reserve the caller's budget, which a
        recovery refused for time or cancellation must not do.
        """

        if self.state.recoveries >= MAX_STRUCTURED_RECOVERIES:
            return "recovery_spent"
        refusal = self.admit()
        if refusal is not None:
            return refusal
        self.note(RecoveryState(self.state.recoveries + 1, owed if owed is not None else self.state.owed))
        return None

    def admit(self) -> str | None:
        """Caller authorization common to contract corrections and schema repairs."""

        if self.allowance.cancelled is not None and self.allowance.cancelled():
            return "cancelled"
        remaining = self.remaining()
        if remaining is not None and remaining <= self.allowance.min_request_seconds:
            return "deadline"
        if self.allowance.admit is None or not self.allowance.admit():
            return "recovery_refused"
        return None


_active: ContextVar[_Ledger | None] = ContextVar("structured_recovery", default=None)


def claim_schema_repair() -> bool:
    """Whether a provider may send its schema repair now.

    Outside a checked call, True: every provider repairs as it always has.
    Inside one, each attempt may repair once, only with caller admission, time
    left and no cancellation. This never spends the contract re-ask credit.
    """

    ledger = _active.get()
    if ledger is None:
        return True
    if ledger.repair is not None:
        return False
    refusal = ledger.admit()
    ledger.repair = refusal or "claimed"
    return refusal is None


def recovery_remaining_seconds() -> float | None:
    """What remains of the checked call's one deadline, or None (no checked call, or no deadline).

    A transport with a ceiling of its own (a background stream's) holds the
    request to the smaller of the two, so a correction never gets a fresh ceiling.
    """

    ledger = _active.get()
    return None if ledger is None else ledger.remaining()


def correction_in_flight() -> bool:
    """Whether the request being made is a checked call's correction."""

    ledger = _active.get()
    return ledger is not None and ledger.ordinal > 0


def _checker(contract: tuple[Predicate[T], ...]) -> Callable[[T], T]:
    def check(answer: T) -> T:
        failed = first_failure(contract, answer)
        if failed is not None:
            raise ContractRejected(failed)
        return answer

    return check


def _named(contract: tuple[Predicate[T], ...], name: Any) -> Predicate[T] | None:
    return next((predicate for predicate in contract if predicate.name == name), None)


def checked_structured_call(
    *,
    first_prompt: str,
    contract: Iterable[Predicate[T]],
    send: Callable[[Attempt, Callable[[T], T]], T],
    recovery: RecoveryAllowance,
    checkpoint: ModelCheckpoint[T] | None,
    failure: Callable[[ContractFailure], BaseException],
    request_key: str | None = None,
    usage: Callable[[T], dict[str, Any]] | None = None,
) -> T:
    """The accepted answer of one structured call with a contract (:func:`checked_structured_answer`)."""

    return checked_structured_answer(
        first_prompt=first_prompt, contract=contract, send=send, recovery=recovery, checkpoint=checkpoint,
        failure=failure, request_key=request_key, usage=usage,
    ).answer


def checked_structured_answer(
    *,
    first_prompt: str,
    contract: Iterable[Predicate[T]],
    send: Callable[[Attempt, Callable[[T], T]], T],
    recovery: RecoveryAllowance,
    checkpoint: ModelCheckpoint[T] | None,
    failure: Callable[[ContractFailure], BaseException],
    request_key: str | None = None,
    usage: Callable[[T], dict[str, Any]] | None = None,
) -> CheckedAnswer[T]:
    """Check, and at most once correct, one structured call's answer.

    ``send(attempt, check)`` is the caller's existing one-attempt admission and
    send: it sends ``attempt.prompt`` and passes ``check`` to the operation
    (``execute_structured_operation(check=...)``), so a rejected answer
    finishes its receipt as failed. The answer it returns is checked again
    here, so one that skipped the hook is never accepted either.

    Order: a checkpoint hit is checked (a failing one is discarded by its exact
    stored value); a restored ``owed`` correction is sent next, otherwise the
    first request, unchanged; a rejection is recorded as owed, then the one
    recovery is claimed (spent, not cancelled, time left, admitted) and the
    correction sent. An accepted answer is saved under the checkpoint's key
    (``request_key``, when given, names the original request on a
    correction's receipt instead). Any other exception of ``send`` is the
    caller's and propagates as it is; so does an unparsed first answer whose
    provider made no repair here.
    """

    contract = contract_of(*contract)
    ledger = _Ledger(recovery)
    discarded: str | None = None
    if checkpoint is not None:
        fetched = checkpoint.fetch()
        if fetched is not None:
            saved, stored = fetched
            failed = first_failure(contract, saved)
            if failed is None:
                return CheckedAnswer(saved, True, 0, ledger.state)
            # Exact value: a fresh answer another run saved since must survive.
            checkpoint.discard(stored)
            discarded = failed.name
    key = request_key if request_key is not None else (checkpoint.key if checkpoint is not None else None)
    sends = 0
    attempt = Attempt(0, first_prompt, ledger.remaining())
    if ledger.state.owed is not None:
        owed = _named(contract, ledger.state.owed)
        if owed is None:
            raise failure(ContractFailure("unknown_requirement", ledger.state.owed, ledger.state, sends))
        if ledger.state.recoveries >= MAX_STRUCTURED_RECOVERIES:
            # Restored after its correction was claimed: that recovery stays spent.
            raise failure(ContractFailure("contract_failed", owed.name, ledger.state, sends))
        refusal = ledger.claim(owed.name)
        if refusal is not None:
            raise failure(ContractFailure(refusal, owed.name, ledger.state, sends))
        attempt = Attempt(ledger.state.recoveries, correction_prompt(first_prompt, owed), ledger.remaining(), owed.name)
    while True:
        sends += 1
        answer, failed, cause = _run(ledger, send, contract, attempt, key, failure, sends)
        if failed is None:
            if checkpoint is not None:
                checkpoint.save(answer, usage(answer) if usage is not None else None)
            return CheckedAnswer(answer, False, sends, ledger.state, discarded)
        if ledger.state.recoveries >= MAX_STRUCTURED_RECOVERIES:
            raise failure(ContractFailure("contract_failed", failed.name, ledger.state, sends)) from cause
        ledger.note(RecoveryState(ledger.state.recoveries, failed.name))
        if recovery.defer:
            raise failure(ContractFailure("correction_deferred", failed.name, ledger.state, sends)) from cause
        refusal = ledger.claim(failed.name)
        if refusal is not None:
            raise failure(ContractFailure(refusal, failed.name, ledger.state, sends)) from cause
        attempt = Attempt(ledger.state.recoveries, correction_prompt(first_prompt, failed), ledger.remaining(),
                          failed.name)


def _run(
    ledger: _Ledger, send: Callable[[Attempt, Callable[[T], T]], T], contract: tuple[Predicate[T], ...],
    attempt: Attempt, key: str | None, failure: Callable[[ContractFailure], BaseException], sends: int,
) -> tuple[Any, Predicate[T] | None, BaseException | None]:
    """One send under the ledger: (answer, None, None) accepted, or (None, failed predicate, cause)."""

    ledger.ordinal = attempt.ordinal
    ledger.repair = None
    note = nullcontext() if attempt.ordinal == 0 else annotate_calls(**{RECOVERY_NOTE: {
        "request_key": key, "failed": attempt.correcting, "ordinal": attempt.ordinal,
    }})
    token = _active.set(ledger)
    try:
        with note:
            answer = send(attempt, _checker(contract))
    except ContractRejected as rejected:
        return None, rejected.predicate, rejected
    except AIOutputTruncated:
        raise
    except AIInvalidOutput as invalid:
        if attempt.ordinal == 0 and ledger.repair is None:
            # No recovery was spent on it here: the caller's own handling, as today.
            raise
        reason = ledger.repair if ledger.repair in _REFUSALS - {"recovery_spent"} else "schema_failed"
        raise failure(ContractFailure(reason, None, ledger.state, sends)) from invalid
    finally:
        _active.reset(token)
    failed = first_failure(contract, answer)
    return (answer, None, None) if failed is None else (None, failed, None)


def recovery_note(budget_json: str | None) -> dict[str, Any] | None:
    """A root receipt's :data:`RECOVERY_NOTE` (its ``budget_json``), or None."""

    try:
        note = json.loads(budget_json or "{}").get(RECOVERY_NOTE)
    except (TypeError, ValueError, AttributeError):
        return None
    return note if isinstance(note, dict) else None


def recover_from_receipts(
    receipts: Iterable[Mapping[str, Any]],
    *,
    first_prompt: str,
    request_key: str | None,
    contract: Iterable[Predicate[T]],
    read: Callable[[str], T],
) -> tuple[T, Mapping[str, Any]] | None:
    """The newest receipt answer a checked call may reuse, and its receipt, or None.

    ``receipts`` are root receipts of the call's purpose, schema and settings,
    newest first, with ``prompt_hash``, ``output_text`` and ``budget_json``
    (and ``status``, when present, must be ``completed``). A first answer's
    receipt has the first prompt's hash and no recovery note. A correction's
    has the hash of the deterministic correction for the predicate its note
    names, under ``request_key``. Either answer must read and pass the contract
    again: a rejected answer never becomes reusable because its JSON parses.
    """

    contract = contract_of(*contract)
    first_hash = content_key(first_prompt)
    for receipt in receipts:
        if receipt.get("status", "completed") != "completed" or receipt.get("output_text") is None:
            continue
        note = recovery_note(receipt.get("budget_json"))
        if note is None:
            if receipt.get("prompt_hash") != first_hash:
                continue
        else:
            predicate = _named(contract, note.get("failed"))
            ordinal = note.get("ordinal")
            if (predicate is None or request_key is None or note.get("request_key") != request_key
                    or not isinstance(ordinal, int) or not 1 <= ordinal <= MAX_STRUCTURED_RECOVERIES
                    or receipt.get("prompt_hash") != content_key(correction_prompt(first_prompt, predicate))):
                continue
        try:
            answer = read(str(receipt["output_text"]))
        except (ValueError, KeyError, TypeError):
            continue
        if first_failure(contract, answer) is None:
            return answer, receipt
    return None


__all__ = [
    "Attempt",
    "CheckedAnswer",
    "Contract",
    "ContractFailure",
    "ContractRejected",
    "MAX_STRUCTURED_RECOVERIES",
    "Predicate",
    "RECOVERY_NOTE",
    "RecoveryAllowance",
    "RecoveryState",
    "checked_structured_answer",
    "checked_structured_call",
    "claim_schema_repair",
    "contract_of",
    "correction_in_flight",
    "correction_prompt",
    "first_failure",
    "recover_from_receipts",
    "recovery_note",
    "recovery_remaining_seconds",
]
