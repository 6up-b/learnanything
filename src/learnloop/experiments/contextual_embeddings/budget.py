"""The one E0 spend admission: $25 across every paid call (spec §6).

A file-backed ledger shared by every thread, process, vault copy and stage of
E0. Each physical request is admitted BEFORE it is sent: its hard maximum
charge (input token upper bound plus the output bound it is sent with, at
the pin's VERIFIED price) is reserved under an exclusive file lock only when
the reconciled charges, plus every outstanding reservation, plus this request
still fit the global cap and the request's category sub-cap (§6's
allocation). Unknown billing stays reserved until reconciled; a request that
failed without reporting usage keeps its whole reservation. A refusal raises
:class:`E0BudgetExceeded` before the request; the runner then stops the
affected work cleanly and the report says so (never a silent substitution).

**One budget per authorization (fix round 4, High 3).** The paid run's
ledger lives at ONE canonical path tied to the frozen plan's id,
``fixtures-local/contextual-embeddings/ledger/<plan_id>.ledger``
(:func:`authorized_ledger`), never under a caller-chosen run directory: a
second run of the same plan shares it, so another ``--run-dir`` cannot get a
fresh $25. A ledger for a different plan id, while another authorization's
ledger exists, needs an explicit ``--new-authorization <reason>``.

**A hard cap (fix round 4, High 2).** A settlement above its reservation
means the reservation was not a hard maximum: the ledger records the
overage, marks itself HALTED and refuses every later request in every
process (:class:`E0RunHalted`); the run stops at once with an incomplete
report.

**Codex requests stay bounded (fix round 4, Medium 10).** Subscription
routes (Codex) have no marginal bill and are admitted at $0, but every
physical subscription request (retries and repairs included) counts against
the persisted ``subscription_allowance`` (``pins.MAX_SUBSCRIPTION_REQUESTS``)
and is refused past it. Metered requests count against ``max_requests``.
``start_clock`` bounds a run's wall time from the FIRST start recorded in the
ledger, so a resumed process does not restart the clock.

The ledger also plugs into the existing spend machinery: ``LedgerEnvelope``
is a ``learnloop.ai.spend.SpendEnvelope`` (kept for reused paths and tests;
the paid run admits through request gates instead).
"""
from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import fcntl
import json
import math
import os
from pathlib import Path
import re
import threading
import time
import uuid
from typing import Any

from learnloop.ai.spend import SpendEnvelope, SpendLimitExceeded

from learnloop.experiments.contextual_embeddings import pins

LEDGER_NAME = "e0_spend_ledger.json"
LOCK_NAME = "e0_spend_ledger.lock"
#: The canonical ledger directory under a fixtures-local root.
LEDGER_DIR = ("contextual-embeddings", "ledger")
_PROCESS_LOCK = threading.Lock()


class E0Stop(Exception):
    """A step of the paid run cannot continue; nothing more is sent for it.
    The runner records the incomplete work and keeps the report (fix round 4,
    Medium 12)."""

    kind = "stopped"


class E0BudgetExceeded(SpendLimitExceeded, E0Stop):
    """The next request cannot be admitted under the E0 cap; nothing was sent."""

    kind = "budget"


class E0DeadlineExceeded(E0BudgetExceeded):
    """The run's wall-time bound (``pins.MAX_WALL_S``) has passed; nothing was sent."""

    kind = "deadline"


class E0PriceUnverified(E0BudgetExceeded):
    """A metered request priced by an unverified pin; nothing was sent."""

    kind = "price_unverified"


class E0RunHalted(E0BudgetExceeded):
    """A settlement exceeded its reservation: the whole run stops at once."""

    kind = "halted"


class E0ProviderFailure(E0Stop):
    """A provider or contract failure, normalized at the E0 boundary (fix
    round 4, High 8 and Medium 12). Carries only an allowlisted
    classification, an HTTP status code and a safe request id: never the
    provider's message, whose body can echo a credential or request text."""

    kind = "provider"

    def __init__(self, classification: str, *, status_code: int | None = None,
                 request_id: str | None = None) -> None:
        self.classification = classification
        self.status_code = status_code
        self.request_id = request_id
        parts = [f"provider failure ({classification})"]
        if status_code is not None:
            parts.append(f"status {status_code}")
        if request_id:
            parts.append(f"request {request_id}")
        super().__init__("; ".join(parts))


class E0RequestBlocked(E0Stop):
    """A request whose earlier attempt may have been charged without its
    result recorded: blocked pending reconciliation, never re-sent
    automatically (fix round 4, Medium 11)."""

    kind = "blocked"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _d(value: Any) -> Decimal:
    return Decimal(str(value))


@dataclass(frozen=True)
class Request:
    """What one physical request is admitted as."""

    category: str
    provider: str
    route: str
    purpose: str
    arm: str | None = None
    billing: str = "metered"
    estimated_usd: float = 0.0
    estimated_tokens: int = 0
    attempt: int = 0
    #: The complete request identity (a role call's checkpoint key), so a
    #: resume can tell whether a request was ever admitted (Medium 11).
    request_key: str | None = None


class E0Ledger:
    """The persistent, lock-protected E0 ledger.

    ``directory``: a ledger directory (tests, reused paths); ``file``: the
    canonical ``<plan_id>.ledger`` file (:func:`authorized_ledger`)."""

    def __init__(self, directory: Path | str | None = None, *, file: Path | str | None = None,
                 cap_usd: float = pins.E0_CAP_USD,
                 allocation: Mapping[str, float] | None = None,
                 max_requests: int = pins.MAX_PAID_REQUESTS,
                 max_subscription_requests: int = pins.MAX_SUBSCRIPTION_REQUESTS) -> None:
        if (directory is None) == (file is None):
            raise ValueError("an E0 ledger needs exactly one of a directory or a file")
        if file is not None:
            self.path = Path(file)
            self.directory = self.path.parent
            self.lock_path = self.path.with_name(self.path.name + ".lock")
        else:
            self.directory = Path(directory)  # type: ignore[arg-type]
            self.path = self.directory / LEDGER_NAME
            self.lock_path = self.directory / LOCK_NAME
        self.directory.mkdir(parents=True, exist_ok=True)
        self.cap = _d(cap_usd)
        self.allocation = {key: _d(value) for key, value in (allocation or pins.ALLOCATION_USD).items()}
        if sum(self.allocation.values(), Decimal(0)) > self.cap:
            raise ValueError("the category allocation exceeds the E0 cap")
        self.max_requests = int(max_requests)
        self._subscription_allowance = int(max_subscription_requests)
        #: The run's monotonic deadline (``start_clock``); None: no run is timed.
        self.deadline: float | None = None
        self._clock: Any = time.monotonic

    def start_clock(self, max_wall_s: float = pins.MAX_WALL_S, *, clock: Any = None,
                    wall: Callable[[], float] = time.time) -> float:
        """Bound the run to ``max_wall_s`` of wall time from the FIRST start
        recorded in this ledger (a resumed process keeps the elapsed time:
        fix round 4, Medium 10): every later admission (each retry included)
        is refused once it has passed (Codex review F14). Returns the
        monotonic deadline."""

        self._clock = clock or time.monotonic
        with self._locked() as state:
            recorded = state.setdefault("clock", {"started_at_unix": float(wall()), "max_wall_s": float(max_wall_s)})
            elapsed = max(0.0, float(wall()) - float(recorded["started_at_unix"]))
            limit = min(float(recorded["max_wall_s"]), float(max_wall_s))
        self.deadline = self._clock() + max(0.0, limit - elapsed)
        return self.deadline

    def time_left(self) -> float | None:
        if self.deadline is None:
            return None
        return self.deadline - self._clock()

    # -- storage ------------------------------------------------------------------
    @contextmanager
    def _locked(self) -> Iterator[dict[str, Any]]:
        with _PROCESS_LOCK:
            with open(self.lock_path, "a+") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    state = self._read()
                    yield state
                    self._write(state)
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 2, "cap_usd": str(self.cap),
                    "allocation": {key: str(value) for key, value in self.allocation.items()},
                    "subscription_allowance": self._subscription_allowance,
                    "entries": {}, "refusals": [], "overages": [], "halted": None}
        state = json.loads(self.path.read_text(encoding="utf-8"))
        # A ledger written under another cap is the same envelope only if the cap matches.
        if _d(state.get("cap_usd", self.cap)) != self.cap:
            raise ValueError("this E0 ledger was opened with a different cap; use its own cap")
        state.setdefault("subscription_allowance", self._subscription_allowance)
        state.setdefault("overages", [])
        state.setdefault("halted", None)
        return state

    def _write(self, state: Mapping[str, Any]) -> None:
        temporary = self.path.with_name(f".{self.path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(state, handle, sort_keys=True, indent=1)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.path)
        directory = os.open(self.directory, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    # -- authorization ------------------------------------------------------------
    def bind_authorization(self, plan_id: str, reason: str | None) -> dict[str, Any]:
        """Record (once) which plan this ledger's budget belongs to; refuse
        another plan's id."""

        with self._locked() as state:
            current = state.get("authorization")
            if current is None:
                current = {"plan_id": plan_id, "reason": reason or "first authorization", "at": _now()}
                state["authorization"] = current
            elif current.get("plan_id") != plan_id:
                raise PermissionError("this E0 ledger belongs to another plan's authorization")
        return dict(current)

    # -- accounting ---------------------------------------------------------------
    @staticmethod
    def _committed(entry: Mapping[str, Any]) -> Decimal:
        """A reconciled entry's actual charge, else its whole reservation."""

        if entry.get("actual_usd") is not None:
            return _d(entry["actual_usd"])
        return _d(entry.get("reserved_usd") or 0)

    def _totals(self, state: Mapping[str, Any]) -> tuple[Decimal, dict[str, Decimal], int]:
        """Committed money, per category, and the METERED requests."""

        total = Decimal(0)
        by_category: dict[str, Decimal] = {}
        requests = 0
        for entry in state["entries"].values():
            committed = self._committed(entry)
            total += committed
            by_category[entry["category"]] = by_category.get(entry["category"], Decimal(0)) + committed
            if entry.get("billing") != "subscription":
                requests += 1
        return total, by_category, requests

    @staticmethod
    def _subscription_count(state: Mapping[str, Any]) -> int:
        return sum(1 for entry in state["entries"].values() if entry.get("billing") == "subscription")

    def reserve(self, request: Request) -> str:
        """Admit one physical request; returns its reservation id."""

        if request.category not in self.allocation:
            raise ValueError(f"unknown E0 spend category {request.category!r}")
        if request.billing not in ("metered", "subscription"):
            raise ValueError("billing must be metered or subscription")
        usd = Decimal(0) if request.billing == "subscription" else _d(request.estimated_usd)
        if usd < 0:
            raise ValueError("estimated_usd must be nonnegative")
        deadline_passed = self.deadline is not None and self._clock() >= self.deadline
        error: type[E0BudgetExceeded] = E0BudgetExceeded
        with self._locked() as state:
            total, by_category, requests = self._totals(state)
            allowance = int(state.get("subscription_allowance", self._subscription_allowance))
            reason = None
            if state.get("halted"):
                reason, error = "the run is halted: " + str(state["halted"].get("reason")), E0RunHalted
            elif deadline_passed:
                reason, error = "the run's wall-time bound has passed", E0DeadlineExceeded
            elif request.billing == "subscription" and self._subscription_count(state) + 1 > allowance:
                reason = f"subscription request allowance {allowance} reached"
            elif request.billing != "subscription" and requests + 1 > self.max_requests:
                reason = f"request cap {self.max_requests} reached"
            elif total + usd > self.cap:
                reason = f"${float(total + usd):.4f} would pass the ${float(self.cap):.2f} E0 cap"
            elif by_category.get(request.category, Decimal(0)) + usd > self.allocation[request.category]:
                reason = (f"${float(by_category.get(request.category, Decimal(0)) + usd):.4f} would pass the "
                          f"{request.category} allocation ${float(self.allocation[request.category]):.2f}")
            if reason is not None:
                state["refusals"].append({"at": _now(), "category": request.category, "provider": request.provider,
                                          "route": request.route, "arm": request.arm, "purpose": request.purpose,
                                          "estimated_usd": float(usd), "reason": reason})
            else:
                reservation = uuid.uuid4().hex
                state["entries"][reservation] = {
                    "category": request.category, "provider": request.provider, "route": request.route,
                    "purpose": request.purpose, "arm": request.arm, "billing": request.billing,
                    "attempt": request.attempt, "reserved_usd": str(usd), "actual_usd": None,
                    "estimated_tokens": int(request.estimated_tokens), "status": "reserved",
                    "reserved_at": _now(), "request_key": request.request_key,
                }
        if reason is not None:
            raise error(reason)
        return reservation

    def settle(self, reservation: str, *, actual_usd: float | None, usage: Mapping[str, Any] | None = None,
               status: str = "settled", request_id: str | None = None, latency_s: float | None = None) -> None:
        """Reconcile a finished request. ``actual_usd`` None keeps the whole
        reservation (unknown billing); a known actual replaces it. An actual
        ABOVE the reservation (a metered request) is an overage: recorded,
        the ledger halts and :class:`E0RunHalted` is raised (after the entry
        and the halt are written, so the record survives)."""

        overage = None
        with self._locked() as state:
            entry = state["entries"].get(reservation)
            if entry is None:
                raise KeyError(reservation)
            if entry["billing"] == "subscription":
                # No marginal bill: admitted at $0 and settled at $0 whatever happened.
                entry["actual_usd"] = "0"
                entry["status"] = status
            elif actual_usd is not None:
                if actual_usd < 0:
                    raise ValueError("actual_usd must be nonnegative")
                entry["actual_usd"] = str(_d(actual_usd))
                entry["status"] = status
                if _d(actual_usd) > _d(entry["reserved_usd"]):
                    overage = {"reservation": reservation, "arm": entry.get("arm"),
                               "category": entry["category"], "route": entry["route"],
                               "reserved_usd": entry["reserved_usd"], "actual_usd": str(_d(actual_usd)),
                               "overage_usd": str(_d(actual_usd) - _d(entry["reserved_usd"])), "at": _now()}
                    entry["status"] = "overage"
                    state["overages"].append(overage)
                    if not state.get("halted"):
                        state["halted"] = {"reason": f"a settlement exceeded its reservation by "
                                                     f"${overage['overage_usd']} ({entry['route']})",
                                           "at": overage["at"]}
            else:
                # Unknown billing: the whole reservation stands until reconciled.
                entry["status"] = "unknown_billing" if status == "settled" else status
            entry["usage"] = {key: value for key, value in (usage or {}).items()
                              if key in ("input_tokens", "output_tokens", "total_tokens", "cost", "cached_tokens")}
            entry["request_id"] = request_id
            entry["latency_s"] = latency_s
            entry["settled_at"] = _now()
        if overage is not None:
            raise E0RunHalted(f"settlement exceeded its reservation by ${overage['overage_usd']}: the run stops")

    @contextmanager
    def admit(self, request: Request) -> Iterator[Charge]:
        """Reserve, run the body (the physical request), settle. A body that
        raises before settling keeps the whole reservation (``failed``)."""

        reservation = self.reserve(request)
        charge = Charge(self, reservation)
        try:
            yield charge
        except BaseException:
            if not charge.settled:
                self.settle(reservation, actual_usd=None, status="failed")
            raise
        if not charge.settled:
            self.settle(reservation, actual_usd=None, status="settled")

    def halted(self) -> dict[str, Any] | None:
        with self._locked() as state:
            return state.get("halted")

    def entries_for(self, request_key: str) -> list[dict[str, Any]]:
        """Every entry admitted under one complete request identity."""

        with self._locked() as state:
            return [dict(entry, reservation=key) for key, entry in state["entries"].items()
                    if entry.get("request_key") == request_key]

    # -- reports ------------------------------------------------------------------
    def remaining(self) -> float:
        with self._locked() as state:
            total, _by_category, _requests = self._totals(state)
        return float(max(Decimal(0), self.cap - total))

    def report(self) -> dict[str, Any]:
        with self._locked() as state:
            total, by_category, requests = self._totals(state)
            entries = list(state["entries"].values())
            refusals = list(state["refusals"])
            overages = list(state.get("overages") or [])
            halted = state.get("halted")
            allowance = int(state.get("subscription_allowance", self._subscription_allowance))
            authorization = state.get("authorization")
        outstanding = sum((_d(entry["reserved_usd"]) for entry in entries if entry.get("actual_usd") is None),
                          Decimal(0))
        by_arm: dict[str, dict[str, Any]] = {}
        for entry in entries:
            key = entry.get("arm") or entry["category"]
            row = by_arm.setdefault(key, {"requests": 0, "committed_usd": 0.0, "estimated_tokens": 0,
                                          "input_tokens": 0, "output_tokens": 0, "latency_s": 0.0,
                                          "estimated_only_tokens": 0})
            row["requests"] += 1
            row["committed_usd"] += float(self._committed(entry))
            usage = entry.get("usage") or {}
            row["input_tokens"] += int(usage.get("input_tokens") or 0)
            row["output_tokens"] += int(usage.get("output_tokens") or 0)
            row["estimated_tokens"] += int(entry.get("estimated_tokens") or 0)
            row["latency_s"] += float(entry.get("latency_s") or 0.0)
            if entry["billing"] == "subscription":
                row["estimated_only_tokens"] += int(usage.get("input_tokens") or 0) + int(
                    usage.get("output_tokens") or 0) or int(entry.get("estimated_tokens") or 0)
        return {
            "cap_usd": float(self.cap),
            "committed_usd": float(total),
            "outstanding_reservations_usd": float(outstanding),
            "remaining_usd": float(max(Decimal(0), self.cap - total)),
            "by_category": {key: {"committed_usd": float(by_category.get(key, Decimal(0))),
                                  "allocation_usd": float(value)} for key, value in self.allocation.items()},
            "requests": len(entries),
            "metered_requests": requests,
            "subscription_requests": len(entries) - requests,
            "max_metered_requests": self.max_requests,
            "subscription_allowance": allowance,
            "refusals": len(refusals),
            "refusal_reasons": sorted({str(item["reason"]).split(" would")[0] for item in refusals}),
            "halted": halted,
            "overages": [{key: item[key] for key in ("arm", "category", "reserved_usd", "actual_usd", "overage_usd")}
                         for item in overages],
            "authorization": None if not authorization else {"plan_id": authorization.get("plan_id")},
            "by_arm": by_arm,
            "basis": "reconciled charges plus outstanding reservations (unknown billing stays reserved)",
        }


# -- the canonical ledger (fix round 4, High 3) ----------------------------------------

_PLAN_ID = re.compile(r"e0_[0-9a-f]{16}")


def canonical_ledger_dir(copies: Sequence[Path]) -> Path:
    """``<fixtures-local>/contextual-embeddings/ledger`` for the copies: every
    copy must lie under the SAME fixtures-local root (independent of any run
    directory or working directory)."""

    roots = set()
    for copy in copies:
        resolved = Path(copy).resolve()
        found = next((parent for parent in (resolved, *resolved.parents) if parent.name == "fixtures-local"), None)
        if found is None:
            raise ValueError("a copy must lie under a fixtures-local directory")
        roots.add(found)
    if len(roots) != 1:
        raise ValueError("every copy of one E0 run must lie under the same fixtures-local root")
    return roots.pop().joinpath(*LEDGER_DIR)


def authorized_ledger(copies: Sequence[Path], plan_id: str, *, new_authorization: str | None = None) -> E0Ledger:
    """The ONE ledger of a frozen plan's authorization.

    The same plan always reopens ``<plan_id>.ledger``. A plan without one,
    while a ledger of another plan exists, needs ``new_authorization`` (the
    orchestrator's reason), recorded in the new ledger."""

    if not _PLAN_ID.fullmatch(str(plan_id)):
        raise ValueError("not an E0 plan id")
    directory = canonical_ledger_dir(copies)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{plan_id}.ledger"
    if not path.exists():
        others = sorted(item.name for item in directory.glob("e0_*.ledger") if item != path)
        if others and not (new_authorization and new_authorization.strip()):
            raise PermissionError("another plan's E0 authorization ledger exists; a different plan needs "
                                  "--new-authorization <reason> from the orchestrator")
    ledger = E0Ledger(file=path)
    ledger.bind_authorization(plan_id, new_authorization.strip() if new_authorization else None)
    return ledger


def known_tokens(value: Any) -> int | None:
    """A reported token count (a nonnegative int, never a bool), else None."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def explicit_cost(value: Any) -> float | None:
    """A provider's explicit, finite, nonnegative cost, else None."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    cost = float(value)
    return cost if math.isfinite(cost) and cost >= 0 else None


def reconciled_usd(usage: Mapping[str, Any], price: Callable[[int, int], float], *,
                   output_bound: int = 0) -> float | None:
    """What a finished METERED request may be reconciled to; None keeps the
    whole reservation (``unknown_billing``), counted against the cap.

    Codex re-review F21: one known zero is not a bill. A reservation moves
    (down or up) only on an explicit provider cost, or on a reported, positive
    input-token count; a request that sent text and reports no input tokens
    (or zero) is unknown billing whatever else it reports. The production
    embedding wrapper always reports ``output_tokens=0``, so an output count
    alone never settles anything. With input tokens reported but output
    tokens not, the output side is charged at the reserved ``output_bound``.
    ``price(input_tokens, output_tokens)`` prices the counts in dollars."""

    cost = explicit_cost(usage.get("cost"))
    if cost is not None:
        return cost
    tokens_in = known_tokens(usage.get("input_tokens"))
    if not tokens_in:
        return None
    tokens_out = known_tokens(usage.get("output_tokens"))
    return float(price(tokens_in, int(output_bound) if tokens_out is None else tokens_out))


class Charge:
    """One admitted request; settle it once with what the provider reported."""

    def __init__(self, ledger: E0Ledger, reservation: str) -> None:
        self.ledger = ledger
        self.reservation = reservation
        self.settled = False

    def settle(self, *, actual_usd: float | None, usage: Mapping[str, Any] | None = None,
               request_id: str | None = None, latency_s: float | None = None, status: str = "settled") -> None:
        try:
            self.ledger.settle(self.reservation, actual_usd=actual_usd, usage=usage, request_id=request_id,
                               latency_s=latency_s, status=status)
        finally:
            # An overage raises after its entry is written: never settled twice.
            self.settled = True


class LedgerEnvelope(SpendEnvelope):
    """The E0 ledger as a ``SpendEnvelope`` for reused production paths.

    ``reserve`` admits through the ledger (raising ``E0BudgetExceeded``);
    ``charge`` and ``settle`` reconcile. ``reservation_ref`` names the ledger
    entry on the request's receipt.

    Only a handle ``reserve`` returned (a ledger id, a string) is a ledger
    entry. A subscription request's place (``learnloop.ai.spend.NO_RESERVATION``,
    whose text is ``"0"``) reserved nothing, so it is never settled, charged
    or released here (Codex re-review F19: settling it raised ``KeyError('0')``).

    Use it only around a path whose every admitted request is an embedding
    (the backfill): the production ``SpendBudget`` reserves EVERY request in
    each active envelope, LLM ones included, so an LLM request under it would
    also be billed as an embedding. The system arms admit both kinds once per
    physical request with ``system_arms.SystemRequestGate`` instead."""

    def __init__(self, ledger: E0Ledger, *, category: str, provider: str, route: str,
                 arm: str | None = None) -> None:
        super().__init__(f"e0:{category}", float(ledger.cap))
        self.ledger = ledger
        self._request = Request(category=category, provider=provider, route=route, purpose="reused_path",
                                arm=arm)
        self._extra: dict[str, Decimal] = {}

    def reserve(self, usd: Decimal) -> object:
        request = Request(**{**self._request.__dict__, "estimated_usd": float(usd)})
        return self.ledger.reserve(request)

    def reservation_ref(self, handle: object) -> str | None:
        return f"e0_ledger:{handle}" if isinstance(handle, str) else None

    def unreserve(self, handle: object) -> None:
        if isinstance(handle, str):
            self.ledger.settle(handle, actual_usd=0.0, status="settled")

    def charge(self, usd: Decimal, handle: object = None) -> None:
        if isinstance(handle, str) and usd > 0:
            self._extra[handle] = self._extra.get(handle, Decimal(0)) + usd

    def settle(self, handle: object, actual: Decimal | None = None) -> None:
        """Reconcile with the production path's own reconciled figure. That
        figure cannot say whether it came from an explicit cost or from a
        reported zero (the production backfill prices ``input_tokens=0`` at
        $0), so a $0 figure for a paid request keeps the whole reservation as
        unknown billing (Codex re-review F21: one known zero is not a bill)."""

        if not isinstance(handle, str):
            return
        usd = None if actual is None else float(actual)
        if usd is not None and (not math.isfinite(usd) or usd <= 0):
            usd = None
        self.ledger.settle(handle, actual_usd=usd)

    def remaining(self) -> float:
        return self.ledger.remaining()

    def report(self) -> dict[str, object]:
        return self.ledger.report()
