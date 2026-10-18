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
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.execution import active_request_gate, gate_model_requests
from learnloop.ai.spend import SpendBudget, SpendCaps, spend_envelopes


#: How many times a check rebuilds protection when the vault was reloaded
#: while it was being built (fix round 5, V1), before refusing.
RELOAD_RETRIES = 3
_UNREADABLE = object()


class ProtectedContent(AIInterrupted):
    """A request refused before it was sent: something it quotes is protected now.

    An ``AIInterrupted``, so that no retry loop, transport or spend layer
    between the guard and AD retries it or relabels it as a provider
    failure; AD catches it and reports ``protected``."""


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
        #: Why the job's requests were refused (None: none was).
        self.refused: str | None = None

    def check(self, purpose: str = "request") -> Any:
        """Raise :class:`ProtectedContent` when the job may send (or record) nothing more.

        Returns the reload generation the check judged (None without a
        provider of one), for :meth:`confirm` at the admission it guards.

        Why here, before each request and not once per job (Codex re-review
        F11): the check used to run once before the forecaster pair, so a
        source marked held out while the first request ran still reached the
        Decider request after it, and an LLM retry after ``AIOutputTruncated``
        still sent it. The predicate is read afresh at every call, and the
        first refusal is kept: every later request of the job is refused."""

        with self._lock:
            if self.refused is not None:
                raise ProtectedContent(self.refused)
        reason, generation = self._protected_now()
        self._refuse_if(reason, purpose)
        return generation

    def confirm(self, generation: Any, purpose: str = "record") -> None:
        """Refuse when the vault was reloaded since ``generation`` was checked.

        Fix round 5, V1: a check judges one vault; a reload between it and
        the admission it guards (the physical request, the record's write
        transaction) could replace that vault with one that holds the
        content out. The admission compares the generation and refuses when
        it moved; the job's later requests are refused too."""

        moved = None
        if self._generation_reader() is not None and self._generation() != generation:
            moved = "the vault was reloaded after its protection was checked"
        self._refuse_if(moved, purpose)

    def _refuse_if(self, reason: str | None, purpose: str) -> None:
        with self._lock:
            if reason is not None and self.refused is None:
                self.refused = f"{reason} (refused before {purpose})"
            if self.refused is not None:
                raise ProtectedContent(self.refused)

    def _generation_reader(self) -> Callable[[], Any] | None:
        return getattr(self._live_vault, "generation", None) if self._live_vault is not None else None

    def _generation(self) -> Any:
        reader = self._generation_reader()
        if reader is None:
            return None
        try:
            return reader()
        except Exception:  # noqa: BLE001 - an unreadable generation never matches
            return _UNREADABLE

    def _loaded_vault(self) -> tuple[Any | None, str | None]:
        """The vault loaded now, or None with why (fix round 4, V1).

        Why not the job's own vault: a same-vault reload replaces the
        context's vault without stopping its jobs, and a source-set or exam
        scope edit it brings holds out material the job's vault does not.
        The frozen inputs stay frozen; only protection is re-resolved. Another
        vault, or none, refuses (the job's fence also stops a switch)."""

        if self._live_vault is None:
            return self._vault, None
        try:
            current = self._live_vault()
        except Exception:  # noqa: BLE001 - an unreadable provider protects everything
            return None, "the loaded vault could not be read"
        if current is None:
            return None, "no vault is loaded"
        if _root(current) != _root(self._vault):
            return None, "another vault is loaded"
        return current, None

    def _protected_now(self) -> tuple[str | None, Any]:
        """``(why it is protected or None, the reload generation judged)``.

        Fix round 5, V1: the loaded vault is read once and its protection
        built from it, which takes a while; a same-root reload in between
        (an exam scope added) replaced the vault, and the old one's verdict
        was used. The reload generation is read before and after: when it
        moved, protection is rebuilt from the new vault, up to
        :data:`RELOAD_RETRIES` times, then the request is refused."""

        for _attempt in range(1 + RELOAD_RETRIES):
            before = self._generation()
            vault, gone = self._loaded_vault()
            if vault is None:
                return gone, before
            reason = self._judged(vault)
            after = self._generation()
            if before == after and after is not _UNREADABLE:
                return reason, after
        return "the vault kept being reloaded while its protection was checked", None

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


class _GuardGate:
    """The guard as the context's request gate, in front of the gate already installed."""

    def __init__(self, guard: SendGuard, outer: Any | None) -> None:
        self._guard = guard
        self._outer = outer

    def admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> Any:
        # Immediately before the physical request: the check, then its
        # generation compared once more (fix round 5, V1).
        self._guard.confirm(self._guard.check(purpose), purpose)
        if self._outer is None:
            return None
        return self._outer.admit(client, purpose=purpose, prompt=prompt, budget=budget)

    def settle(self, admission: Any, usage: dict[str, Any]) -> None:
        if self._outer is not None:
            self._outer.settle(admission, usage)


@contextmanager
def _sending(guard: SendGuard, envelope: Any) -> Iterator[None]:
    with spend_envelopes(envelope), gate_model_requests(_GuardGate(guard, active_request_gate())):
        yield


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
        guard.confirm(guard.check(purpose), purpose)

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

    guard.check(task)
    with _sending(guard, envelope):
        return decider_request(client, config=config, repository=repository, task=task, state=state,
                               questions=dict(questions), owner_id=owner_id, route=route,
                               question_set_version=question_set_version)


__all__ = ["ProtectedContent", "SendGuard", "ask_decider", "ask_llm"]
