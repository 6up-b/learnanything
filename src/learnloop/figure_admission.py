"""Reader RW5a: the figure switch, and the one gate every figure-derived model request passes.

Shared by the figure service (``learnloop.figures``) and the learner-text gap
worker (``learnloop.diagnosis.text_gaps``), so it lives outside the figure
package: evidence-side code may use it without importing ``learnloop.figures``
(the ``evidence-never-reads-figures`` contract).

* :func:`figures_enabled` is the ONE switch predicate (``figures.enabled``),
  with ONE default: off when a config has no ``figures`` section.
* :class:`FiguresGate` is a :class:`~learnloop.ai.execution.RequestGate`. It
  records a key of the configuration when a unit of work starts (a build:
  the vault, the switch, the author route, the day's cap and the price; a
  figure prediction's learner-text reading: the vault and the switch) and,
  before EACH physical model request (transport retries, JSON repair and
  every pipeline call included, since ``model_call`` asks the installed gate),
  reads the configuration as it is NOW and compares. Any change refuses the
  request with :class:`FiguresChanged`, and every later request of that unit
  too: nothing more is asked. It composes with the gate already installed.

Why a gate and not checks at named call sites (owner scope decision,
2026-10-21): "no figure-derived call after switch-off" is a property of every
physical request, and five review rounds kept finding the next unnamed one (a
retry, the Decider, a cap held in an envelope, a price held in a client).
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Hashable
from typing import Any

from learnloop.ai.execution import active_request_gate


def figures_enabled(vault: Any) -> bool:
    """``figures.enabled`` of ``vault`` (a loaded vault or its config): the one
    predicate, defaulting to off when there is no ``figures`` section."""

    config = getattr(vault, "config", vault)
    return bool(getattr(getattr(config, "figures", None), "enabled", False))


def text_key(vault: Any) -> Hashable:
    """What a figure prediction's learner-text reading depends on: the vault
    and the switch (its money cap is ``learner_text_gaps``'s, as on main)."""

    return (str(getattr(vault, "root", "")), figures_enabled(vault))


class FiguresChanged(BaseException):
    """A figure-derived request refused before it was sent: the configuration
    its unit of work started under has changed (the switch turned off, the
    route, cap or price changed, or another vault is open).

    A ``BaseException``, deliberately: the learner-text pipeline turns any
    ``Exception`` from a judge into a "failed" reading and carries on, which
    would write a result after the switch went off. This one passes every
    such handler up to the unit's owner (the build, the gap job), which ends
    the work there; no retry loop, transport or spend layer retries it.
    ``admission_refused`` makes a receipt sink that swallows its own failures
    re-raise it."""

    admission_refused = True


class FiguresGate:
    """Admit a figure-derived unit of work's requests only while its key holds.

    ``key(vault)`` is computed when the gate is made and again, from the
    vault configured now (``live_vault()``, the sidecar's loaded vault; else
    the vault reloaded from disk), before every request and at :meth:`check`.
    """

    def __init__(self, vault: Any, key: Callable[[Any], Hashable], *,
                 live_vault: Callable[[], Any] | None = None) -> None:
        self._root = getattr(vault, "root", None)
        self._key = key
        self._start = key(vault)
        self._live = live_vault
        self._outer = active_request_gate()
        self._lock = threading.Lock()
        #: Why the unit's requests are refused (None: they are not).
        self.changed: str | None = None

    def _current(self) -> Any | None:
        try:
            if self._live is not None:
                return self._live()
            from learnloop.vault.loader import load_vault

            return load_vault(self._root) if self._root is not None else None
        except Exception:  # noqa: BLE001 - an unreadable configuration admits nothing
            return None

    def check(self, purpose: str = "request") -> None:
        """Raise :class:`FiguresChanged` when the unit may do nothing more."""

        with self._lock:
            if self.changed is None:
                vault = self._current()
                if vault is None or getattr(vault, "root", None) != self._root:
                    self.changed = "the vault is no longer open"
                elif not figures_enabled(vault):
                    self.changed = "figures were switched off"
                elif self._key(vault) != self._start:
                    self.changed = "the figure route, cap or price changed"
            if self.changed is not None:
                raise FiguresChanged(f"{purpose} not sent: {self.changed}; nothing more is asked")

    def admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> Any:
        # The outer gate first, then this check: a refusal settles the outer
        # admission, so nothing it reserved is kept for a request never sent.
        admission = None if self._outer is None else self._outer.admit(client, purpose=purpose, prompt=prompt,
                                                                       budget=budget)
        try:
            self.check(purpose)
        except FiguresChanged:
            if self._outer is not None:
                self._outer.settle(admission, {})
            raise
        return admission

    def settle(self, admission: Any, usage: dict[str, Any]) -> None:
        if self._outer is not None:
            self._outer.settle(admission, usage)


__all__ = ["FiguresChanged", "FiguresGate", "figures_enabled", "text_key"]
