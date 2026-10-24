"""Reader RW5a: the figure switch, and the one gate every figure-derived model request passes.

Shared by the figure service (``learnloop.figures``) and the learner-text gap
worker (``learnloop.diagnosis.text_gaps``), so it lives outside the figure
package: evidence-side code may use it without importing ``learnloop.figures``
(the ``evidence-never-reads-figures`` contract).

* :func:`figures_enabled` is the ONE switch predicate (``figures.enabled``),
  with ONE default: off when a config has no ``figures`` section. RW5b's
  :func:`advanced_panels_enabled` and :func:`offers_enabled` sit under it, and
  :func:`offerable` is the one rule for which cited blocks an offer may name
  (the library organizer and the tutor use it without importing the figure
  package).
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


def advanced_panels_enabled(vault: Any) -> bool:
    """RW5b: ``figures.advanced_panels_enabled`` under ``figures.enabled``
    (heat maps, vector fields, trajectories and iterated maps)."""

    config = getattr(vault, "config", vault)
    return figures_enabled(config) and bool(getattr(config.figures, "advanced_panels_enabled", False))


def offers_enabled(vault: Any) -> bool:
    """RW5b: ``figures.offers_enabled`` under ``figures.enabled``: the library
    organizer and the Reader tutor judge ``explorable`` on a cited equation or
    figure block in the call they already make. Off, neither asks nor shows."""

    config = getattr(vault, "config", vault)
    return figures_enabled(config) and bool(getattr(config.figures, "offers_enabled", False))


#: The block types an offer may name: an equation, or a figure the figure
#: author may crop (the figure service's own figure block types).
OFFER_BLOCK_TYPES = frozenset({"Equation", "Figure", "FigureGroup", "Picture", "PictureGroup"})
#: The judgment's two answers; anything else (an old output without the
#: field included) reads as no.
EXPLORABLE = ("yes", "no")


def offerable(block_type: Any) -> bool:
    """Whether a cited block is one "make this explorable" may be offered on:
    code decides the block (by its extracted type), the judge only whether it
    could support a figure."""

    return str(block_type or "") in OFFER_BLOCK_TYPES


def offer_kind(block_type: Any) -> str | None:
    """``equation`` | ``figure`` for an offerable block, else None."""

    if not offerable(block_type):
        return None
    return "equation" if str(block_type) == "Equation" else "figure"


def offerable_blocks(repository: Any, keys: Any) -> dict[tuple[str, str], str]:
    """Which of these ``(extraction_id, span_id)`` blocks an offer may name,
    each with its kind (:func:`offer_kind`), read from the stored blocks."""

    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores.source_block_fts import blocks_by_key

    wanted = list(dict.fromkeys((str(key[0]), str(key[1])) for key in keys))
    if not wanted:
        return {}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        blocks = blocks_by_key(connection, wanted)
    found: dict[tuple[str, str], str] = {}
    for key in wanted:
        kind = offer_kind(blocks[key].block_type) if key in blocks else None
        if kind is not None:
            found[key] = kind
    return found


def explorable_yes(value: Any) -> bool:
    """The judge said yes (an old output with no field, or anything else, is no)."""

    return str(value or "").strip().lower() == "yes"


#: RW5b (Codex review F3): the ``judgment_ledger`` task of the Reader tutor's
#: ``explorable`` verdicts, one row per judged block of an answer (left: the
#: answer's question event; right: the block). The library organizer's verdict
#: is in its ``library_contribution`` row's rationale.
TUTOR_EXPLORABLE_TASK = "figure_explorable"


def tutor_explorable_judgment_id(question_event_id: str, extraction_id: str, span_id: str) -> str:
    """The ledger id of the tutor's verdict on one block of one answer: derived,
    so the press reads it back without a search, and an answer judges a block once."""

    from learnloop.ai.execution import content_key

    return "fxj_" + content_key([str(question_event_id), str(extraction_id), str(span_id)])[:40]


def tutor_explorable_yes(repository: Any, question_event_id: str, keys: Any) -> set[tuple[str, str]]:
    """Which of these ``(extraction_id, span_id)`` blocks the tutor's ledger
    rows for this answer record as ``explorable: yes``."""

    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores.practice_index import judgments_by_ids

    ids = {tutor_explorable_judgment_id(question_event_id, *key): (str(key[0]), str(key[1])) for key in keys}
    if not ids:
        return set()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = judgments_by_ids(connection, list(ids))
    return {ids[found] for found, row in rows.items()
            if row.get("task") == TUTOR_EXPLORABLE_TASK and row.get("left_id") == str(question_event_id)
            and explorable_yes(row.get("verdict"))}


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


__all__ = [
    "EXPLORABLE",
    "FiguresChanged",
    "FiguresGate",
    "OFFER_BLOCK_TYPES",
    "TUTOR_EXPLORABLE_TASK",
    "advanced_panels_enabled",
    "explorable_yes",
    "figures_enabled",
    "offer_kind",
    "offerable",
    "offerable_blocks",
    "offers_enabled",
    "text_key",
    "tutor_explorable_judgment_id",
    "tutor_explorable_yes",
]
