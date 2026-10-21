"""The one E0 spend admission: $25 across every paid call (spec §6).

A file-backed ledger under the experiment directory, shared by every thread,
process, vault copy and stage of E0. Each physical request is admitted
BEFORE it is sent: its conservative estimate (input bound plus full output
bound at the pin's upper-bound price) is reserved under an exclusive file lock
only when the reconciled charges, plus every outstanding reservation, plus
this request still fit the global cap and the request's category sub-cap
(§6's allocation). Unknown billing stays reserved until reconciled; a request
that failed without reporting usage keeps its whole reservation. A refusal
raises :class:`E0BudgetExceeded` before the request; the runner then stops the
affected work cleanly and the report says so (never a silent substitution).

Subscription routes (Codex, owner decision 2026-10-12) have no marginal bill:
they are admitted at $0, never refused for money, still count against the
request cap, and their token usage is tallied ``estimated_only``.

The ledger also plugs into the existing spend machinery: ``LedgerEnvelope``
is a ``learnloop.ai.spend.SpendEnvelope``, so any production path a stage
reuses on a copy (an embedding backfill under ``spend_envelopes``) reserves in
the same ledger.
"""
from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import fcntl
import json
import os
from pathlib import Path
import threading
import uuid
from typing import Any

from learnloop.ai.spend import SpendEnvelope, SpendLimitExceeded

from learnloop.experiments.contextual_embeddings import pins

LEDGER_NAME = "e0_spend_ledger.json"
LOCK_NAME = "e0_spend_ledger.lock"
_PROCESS_LOCK = threading.Lock()


class E0BudgetExceeded(SpendLimitExceeded):
    """The next request cannot be admitted under the E0 cap; nothing was sent."""


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


class E0Ledger:
    """The persistent, lock-protected E0 ledger."""

    def __init__(self, directory: Path | str, *, cap_usd: float = pins.E0_CAP_USD,
                 allocation: Mapping[str, float] | None = None,
                 max_requests: int = pins.MAX_PAID_REQUESTS) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / LEDGER_NAME
        self.lock_path = self.directory / LOCK_NAME
        self.cap = _d(cap_usd)
        self.allocation = {key: _d(value) for key, value in (allocation or pins.ALLOCATION_USD).items()}
        if sum(self.allocation.values(), Decimal(0)) > self.cap:
            raise ValueError("the category allocation exceeds the E0 cap")
        self.max_requests = int(max_requests)

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
            return {"version": 1, "cap_usd": str(self.cap),
                    "allocation": {key: str(value) for key, value in self.allocation.items()},
                    "entries": {}, "refusals": []}
        state = json.loads(self.path.read_text(encoding="utf-8"))
        # A ledger written under another cap is the same envelope only if the cap matches.
        if _d(state.get("cap_usd", self.cap)) != self.cap:
            raise ValueError("this E0 ledger was opened with a different cap; use its own cap")
        return state

    def _write(self, state: Mapping[str, Any]) -> None:
        temporary = self.path.with_name(f".{self.path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(state, handle, sort_keys=True, indent=1)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.path)

    # -- accounting ---------------------------------------------------------------
    @staticmethod
    def _committed(entry: Mapping[str, Any]) -> Decimal:
        """A reconciled entry's actual charge, else its whole reservation."""

        if entry.get("actual_usd") is not None:
            return _d(entry["actual_usd"])
        return _d(entry.get("reserved_usd") or 0)

    def _totals(self, state: Mapping[str, Any]) -> tuple[Decimal, dict[str, Decimal], int]:
        total = Decimal(0)
        by_category: dict[str, Decimal] = {}
        requests = 0
        for entry in state["entries"].values():
            committed = self._committed(entry)
            total += committed
            by_category[entry["category"]] = by_category.get(entry["category"], Decimal(0)) + committed
            requests += 1
        return total, by_category, requests

    def reserve(self, request: Request) -> str:
        """Admit one physical request; returns its reservation id."""

        if request.category not in self.allocation:
            raise ValueError(f"unknown E0 spend category {request.category!r}")
        if request.billing not in ("metered", "subscription"):
            raise ValueError("billing must be metered or subscription")
        usd = Decimal(0) if request.billing == "subscription" else _d(request.estimated_usd)
        if usd < 0:
            raise ValueError("estimated_usd must be nonnegative")
        with self._locked() as state:
            total, by_category, requests = self._totals(state)
            reason = None
            if requests + 1 > self.max_requests:
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
                refused = True
            else:
                refused = False
                reservation = uuid.uuid4().hex
                state["entries"][reservation] = {
                    "category": request.category, "provider": request.provider, "route": request.route,
                    "purpose": request.purpose, "arm": request.arm, "billing": request.billing,
                    "attempt": request.attempt, "reserved_usd": str(usd), "actual_usd": None,
                    "estimated_tokens": int(request.estimated_tokens), "status": "reserved",
                    "reserved_at": _now(),
                }
        if refused:
            raise E0BudgetExceeded(reason)
        return reservation

    def settle(self, reservation: str, *, actual_usd: float | None, usage: Mapping[str, Any] | None = None,
               status: str = "settled", request_id: str | None = None, latency_s: float | None = None) -> None:
        """Reconcile a finished request. ``actual_usd`` None keeps the whole
        reservation (unknown billing); a known actual replaces it."""

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
            else:
                # Unknown billing: the whole reservation stands until reconciled.
                entry["status"] = "unknown_billing" if status == "settled" else status
            entry["usage"] = {key: value for key, value in (usage or {}).items()
                              if key in ("input_tokens", "output_tokens", "total_tokens", "cost", "cached_tokens")}
            entry["request_id"] = request_id
            entry["latency_s"] = latency_s
            entry["settled_at"] = _now()

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
            "requests": requests,
            "refusals": len(refusals),
            "refusal_reasons": sorted({str(item["reason"]).split(" would")[0] for item in refusals}),
            "by_arm": by_arm,
            "basis": "reconciled charges plus outstanding reservations (unknown billing stays reserved)",
        }


class Charge:
    """One admitted request; settle it once with what the provider reported."""

    def __init__(self, ledger: E0Ledger, reservation: str) -> None:
        self.ledger = ledger
        self.reservation = reservation
        self.settled = False

    def settle(self, *, actual_usd: float | None, usage: Mapping[str, Any] | None = None,
               request_id: str | None = None, latency_s: float | None = None, status: str = "settled") -> None:
        self.ledger.settle(self.reservation, actual_usd=actual_usd, usage=usage, request_id=request_id,
                           latency_s=latency_s, status=status)
        self.settled = True


class LedgerEnvelope(SpendEnvelope):
    """The E0 ledger as a ``SpendEnvelope`` for reused production paths.

    ``reserve`` admits through the ledger (raising ``E0BudgetExceeded``);
    ``charge`` and ``settle`` reconcile. ``reservation_ref`` names the ledger
    entry on the request's receipt."""

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
        return f"e0_ledger:{handle}"

    def unreserve(self, handle: object) -> None:
        self.ledger.settle(str(handle), actual_usd=0.0, status="settled")

    def charge(self, usd: Decimal, handle: object = None) -> None:
        if handle is not None and usd > 0:
            self._extra[str(handle)] = self._extra.get(str(handle), Decimal(0)) + usd

    def settle(self, handle: object, actual: Decimal | None = None) -> None:
        self.ledger.settle(str(handle), actual_usd=None if actual is None else float(actual))

    def remaining(self) -> float:
        return self.ledger.remaining()

    def report(self) -> dict[str, object]:
        return self.ledger.report()
