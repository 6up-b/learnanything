"""AD's one paid-call path, and the held-out check before each request it sends (spec A8; Codex re-review F11).

Every model request adaptive difficulty sends goes through :func:`ask_llm` or
:func:`ask_decider`: the outside forecasters' LLM and Decider requests, and
the feature audit's Decider request and its LLM fallback (the backfill and
the background preparation run those). Each takes the job's
:class:`SendGuard` and consults it

* before every attempt it starts (``PaidCalls``' per-attempt admission, so a
  retry after ``AIOutputTruncated`` or a provider failure is checked again),
  and
* before every physical request the transport makes (the guard is the
  context's request gate, in front of any gate already installed).

The guard reads the held-out predicate afresh each time
(:func:`~learnloop.adaptive_difficulty.protection.protection`, never a
predicate a caller computed earlier), from the vault that is loaded *now*
(the job's ``live_vault`` provider: a same-vault reload's source sets and
exam scopes, not the ones the job started with; fix round 4, V1), and asks
it of everything the job's requests quote: the item ids, the current revisions, and the frozen
identities of the revisions a frozen state quotes
(:meth:`~learnloop.adaptive_difficulty.protection.Protection.covers_identity`).
Its first refusal refuses every later request of the job, which reports
``protected``. Requests already sent keep their accounting (their model-call
receipts and spend), and the job records nothing built on its model output
once the guard has refused (:meth:`SendGuard.check` before each record).

**The guarantee** (fix round 6, the orchestrator's statement): nothing is
sent or recorded whose content was held out in the vault snapshot current
at that request's or record's admission. Reading the snapshot and admitting
are one atomic step relative to reload (the sidecar publishes the vault and
its generation together under one lock, and the admission compares the
generation under it). A reload that lands after admission is
indistinguishable from an owner edit made a moment after the send, and is
out of scope: no lock is held across protection building, a model call,
transport work or an SQLite commit. The last confirmation runs as close to
dispatch as the code allows (:func:`before_dispatch`, once the request's
receipt is written) and, for a record, as the last check before the insert
inside its write transaction.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.execution import active_request_gate, gate_model_requests
from learnloop.ai.spend import SpendBudget, SpendCaps, spend_envelopes


#: How many times a check rebuilds protection when the vault was reloaded
#: while it was being built (fix round 5, V1), before refusing.
RELOAD_RETRIES = 3


class ProtectedContent(AIInterrupted):
    """A request refused before it was sent: something it quotes is protected now.

    An ``AIInterrupted``, so that no retry loop, transport or spend layer
    between the guard and AD retries it or relabels it as a provider
    failure; AD catches it and reports ``protected``."""


class StaleSnapshot(ProtectedContent):
    """Refused because the loaded vault changed under the check (a reload, a
    switch, retries exhausted), not because the content is held out.

    Retryable (fix round 6, V3): AD reports ``stale``, and the preparation
    queue keeps the revision for a later run instead of settling it."""


class SendGuard:
    """One job's held-out check, consulted before each request it sends.

    ``items``: the revisions the requests quote as they are now (the vault's
    current item, an audited snapshot). ``item_ids``: ids that must not be
    protected. ``identities``: frozen
    :func:`~learnloop.adaptive_difficulty.outside.source_identity` records
    (a frozen state's target and history). ``protected``: the caller's
    earlier predicate or id set, whose ids stay protected (an earlier
    predicate can only add to today's; it never replaces it). ``live_vault``:
    the provider of the vault loaded now (the sidecar's context's vault at
    check time); None for a caller with no reload (the CLI backfill, which
    holds the vault it loaded), whose own ``vault`` is then the current one.
    A provider with a ``generation()`` method (the sidecar's) also reports
    its reload generation, which every check and admission binds to (fix
    round 5, V1)."""

    def __init__(self, vault: Any, repository: Any, *, items: Iterable[Any] = (), item_ids: Iterable[str] = (),
                 identities: Iterable[Mapping[str, Any]] = (), protected: Any = None,
                 live_vault: Callable[[], Any] | None = None) -> None:
        self._vault = vault
        self._live_vault = live_vault
        self._repository = repository
        self._items = [item for item in items if item is not None]
        self._item_ids = frozenset(str(value) for value in item_ids) | frozenset(
            str(getattr(item, "id", "")) for item in self._items)
        self._identities = [identity for identity in identities]
        caller = getattr(protected, "ids", protected)
        self._earlier = frozenset(str(value) for value in (caller or ()))
        self._lock = threading.Lock()
        #: Why the job's requests were refused (None: none was), and as what.
        self.refused: str | None = None
        self._refused_kind: type[ProtectedContent] = ProtectedContent

    @property
    def stale(self) -> bool:
        """The job was refused for a changed snapshot (retryable), not held-out content."""

        return self.refused is not None and issubclass(self._refused_kind, StaleSnapshot)

    def check(self, purpose: str = "request") -> Any:
        """Raise :class:`ProtectedContent` when the job may send (or record) nothing more.

        Returns the reload generation of the snapshot the check judged (None
        without a provider of one), for :meth:`confirm` at the admission it
        guards. :class:`StaleSnapshot` (retryable) when the loaded vault
        changed under it; :class:`ProtectedContent` (terminal) when the
        content is held out in the snapshot it judged.

        Why here, before each request and not once per job (Codex re-review
        F11): the check used to run once before the forecaster pair, so a
        source marked held out while the first request ran still reached the
        Decider request after it, and an LLM retry after ``AIOutputTruncated``
        still sent it. The predicate is read afresh at every call, and the
        first refusal is kept: every later request of the job is refused.

        The guarantee (fix round 6): nothing is sent or recorded whose
        content was held out in the vault snapshot current at that request's
        or record's admission. Reading the snapshot and admitting are one
        atomic step relative to reload. A reload that lands after admission is
        indistinguishable from an owner edit made a moment after the send,
        and is out of scope: no lock is held across a model call, transport
        work, protection building or an SQLite commit."""

        self._raise_refused()
        reason, generation, kind = self._protected_now()
        self._refuse_if(reason, purpose, kind)
        return generation

    def confirm(self, generation: Any, purpose: str = "record") -> None:
        """Admit, or refuse when the vault was reloaded since ``generation`` was checked.

        Fix rounds 5 and 6, V1: a check judges one snapshot; a reload between
        it and the admission it guards (the physical request, the record's
        insert) could replace that vault with one that holds the content out.
        The comparison runs under the context's publication lock (its
        ``admit``), so no reload interleaves between reading the generation
        and admitting; it refuses as stale (retryable) when the generation
        moved, and the job's later requests are refused too."""

        self._raise_refused()
        if self._live_vault is None:
            return
        try:
            admit = getattr(self._live_vault, "admit", None)
            current = (admit(generation) if admit is not None
                       else self._snapshot()[1] == generation)
        except Exception:  # noqa: BLE001 - an unreadable provider never admits
            current = False
        if not current:
            self._refuse_if("the vault was reloaded after its protection was checked", purpose, StaleSnapshot)

    def _raise_refused(self) -> None:
        with self._lock:
            if self.refused is not None:
                raise self._refused_kind(self.refused)

    def _refuse_if(self, reason: str | None, purpose: str, kind: type[ProtectedContent] = None) -> None:
        with self._lock:
            if reason is not None and self.refused is None:
                self.refused = f"{reason} (refused before {purpose})"
                self._refused_kind = kind or ProtectedContent
            if self.refused is not None:
                raise self._refused_kind(self.refused)

    def _snapshot(self) -> tuple[Any, Any]:
        """``(the vault loaded now, its reload generation)``, read as one snapshot.

        The sidecar's provider reads both under its publication lock
        (``snapshot()``); a plain callable has no generation (None)."""

        if self._live_vault is None:
            return self._vault, None
        snapshot = getattr(self._live_vault, "snapshot", None)
        if snapshot is not None:
            vault, generation = snapshot()
            return vault, generation
        reader = getattr(self._live_vault, "generation", None)
        return self._live_vault(), (reader() if reader is not None else None)

    def _protected_now(self) -> tuple[str | None, Any, type[ProtectedContent]]:
        """``(why it is refused or None, the reload generation judged, the refusal's kind)``.

        Fix round 5, V1: building protection from a snapshot takes a while,
        and a same-root reload in between (an exam scope added) replaced the
        vault, so the old one's verdict was used. The generation is read with
        the vault and again afterwards: when it moved, protection is rebuilt
        from the new snapshot, up to :data:`RELOAD_RETRIES` times, then the
        request is refused as stale. Another vault, none, or an unreadable
        provider is stale too (the job's fence also stops a switch); only
        content held out in the judged snapshot is ``protected`` (fix round
        6, V3: a transient refusal is never settled work)."""

        for _attempt in range(1 + RELOAD_RETRIES):
            try:
                vault, before = self._snapshot()
            except Exception:  # noqa: BLE001 - an unreadable provider protects everything
                return "the loaded vault could not be read", None, StaleSnapshot
            if vault is None:
                return "no vault is loaded", before, StaleSnapshot
            if self._live_vault is not None and _root(vault) != _root(self._vault):
                return "another vault is loaded", before, StaleSnapshot
            reason = self._judged(vault)
            try:
                after = self._snapshot()[1]
            except Exception:  # noqa: BLE001
                return "the loaded vault could not be read", None, StaleSnapshot
            if before == after:
                return reason, after, ProtectedContent
        return "the vault kept being reloaded while its protection was checked", None, StaleSnapshot

    def _judged(self, vault: Any) -> str | None:
        from learnloop.adaptive_difficulty.protection import Protection, protection

        current = protection(vault, self._repository)
        if self._earlier:
            current = Protection(current.ids | self._earlier, current.material)
        for item_id in sorted(self._item_ids):
            if item_id in current:
                return f"item {item_id} is protected"
        for item in self._items:
            if current.covers(item):
                return f"a revision of item {getattr(item, 'id', '?')} is protected"
        for identity in self._identities:
            if current.covers_identity(identity):
                practice_item_id = identity.get("practice_item_id") if isinstance(identity, Mapping) else None
                return f"a frozen revision of item {practice_item_id} is protected"
        return None


def _root(vault: Any) -> str | None:
    root = getattr(vault, "root", None)
    try:
        return str(Path(root).resolve()) if root is not None else None
    except (OSError, TypeError, ValueError):
        return str(root)


#: The job's guard and the generation its latest check judged, for the last
#: confirmation before dispatch (fix round 6, V1-b).
_DISPATCH: ContextVar[dict[str, Any] | None] = ContextVar("ad_send_dispatch", default=None)


def _checked(guard: SendGuard, purpose: str) -> Any:
    generation = guard.check(purpose)
    holder = _DISPATCH.get()
    if holder is not None and holder.get("guard") is guard:
        holder["generation"] = generation
        holder["purpose"] = purpose
    return generation


def before_dispatch() -> None:
    """The last confirmation before a request is dispatched (fix round 6, V1-b).

    Called once the request's start receipt is written (``claims.FencedRepository``),
    which is the last work before the transport sends: after the outer
    request gate's admission and the receipt, so nothing between the final
    confirmation and the transport call can be a reload this check missed
    (a later one is out of scope, as the guarantee says). Outside an AD send
    it does nothing."""

    holder = _DISPATCH.get()
    if holder is not None and "generation" in holder:
        holder["guard"].confirm(holder["generation"], f"dispatching {holder.get('purpose', 'the request')}")


class _GuardGate:
    """The guard as the context's request gate, behind the gate already installed."""

    def __init__(self, guard: SendGuard, outer: Any | None) -> None:
        self._guard = guard
        self._outer = outer

    def admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> Any:
        # The outer gate first, then the check and its confirmation: the
        # guard's admission is the last before the request's receipt and the
        # transport (fix round 6, V1-b). A refusal settles the outer
        # admission, so nothing it reserved is kept for a request never sent.
        admission = (None if self._outer is None
                     else self._outer.admit(client, purpose=purpose, prompt=prompt, budget=budget))
        try:
            self._guard.confirm(_checked(self._guard, purpose), purpose)
        except ProtectedContent:
            if self._outer is not None:
                self._outer.settle(admission, {})
            raise
        return admission

    def settle(self, admission: Any, usage: dict[str, Any]) -> None:
        if self._outer is not None:
            self._outer.settle(admission, usage)


@contextmanager
def _sending(guard: SendGuard, envelope: Any) -> Iterator[None]:
    token = _DISPATCH.set({"guard": guard})
    try:
        with spend_envelopes(envelope), gate_model_requests(_GuardGate(guard, active_request_gate())):
            yield
    finally:
        _DISPATCH.reset(token)


def ask_llm(guard: SendGuard, route: Any, client: Any, *, price: float | None, repository: Any,
            caps: Mapping[str, Any], owner_kind: str, owner_id: str, purpose: str, prompt: str,
            result_model: Any, metadata: Mapping[str, Any], envelope: Any) -> tuple[Any, Any]:
    """One logical LLM call on ``route`` (its retries included), each attempt checked first.

    Returns ``(answer, calls)``; raises what the call raised, and
    :class:`ProtectedContent` when the guard refused an attempt."""

    from learnloop.practice_index.paid import PaidCalls

    subscription = route.billing == "subscription"

    def admit(_estimate: Any) -> None:
        # PaidCalls asks before every attempt, and before it allows a retry.
        guard.confirm(_checked(guard, purpose), purpose)

    calls = PaidCalls(route=route, budget=SpendBudget(SpendCaps(max_estimated_usd=None, **dict(caps)),
                                                      subscription=subscription),
                      price_per_million=price, repository=repository, owner_kind=owner_kind, owner_id=owner_id,
                      admit=admit)
    with _sending(guard, envelope):
        answer = calls.call(client, purpose=purpose, prompt=prompt, result_model=result_model,
                            output_tokens=route.output_tokens, metadata=dict(metadata))
    return answer, calls


def ask_decider(guard: SendGuard, client: Any, *, config: Any, repository: Any, task: str, state: Any,
                questions: Mapping[str, Any], owner_id: str, route: str, question_set_version: str,
                envelope: Any) -> Any:
    """One Decider request (no retry path), checked before it is admitted and before it is sent."""

    from learnloop.decider_judgments import ask_decider as decider_request

    with _sending(guard, envelope):
        _checked(guard, task)
        return decider_request(client, config=config, repository=repository, task=task, state=state,
                               questions=dict(questions), owner_id=owner_id, route=route,
                               question_set_version=question_set_version)


__all__ = ["ProtectedContent", "SendGuard", "StaleSnapshot", "ask_decider", "ask_llm", "before_dispatch",
           "refusal_status"]


def refusal_status(exc: BaseException) -> str:
    """The outcome status of a refusal: ``stale`` (retryable) or ``protected`` (terminal)."""

    return "stale" if isinstance(exc, StaleSnapshot) else "protected"
