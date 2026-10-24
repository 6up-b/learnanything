"""E1's own hard-cap ledger: <= $5 across every E1 authorization (spec §8).

E0's ``E0Ledger`` class does the admission (reserve before send, hard
maximum, unknown billing kept, overage halts), opened on a file under
``<fixtures-local>/contextual-embeddings/e1-ledger/`` with E1's cap and
allocation and a Codex allowance of zero. E1 never opens, carries or seals
an E0 ledger: its directory and plan prefix (``e1_``) are its own. Like
E0's, the cap is cumulative across E1 authorizations: a new E1 plan's
ledger carries and seals every earlier E1 ledger.
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import re
from typing import Any

from learnloop.experiments.contextual_embeddings.budget import E0Ledger, ledger_spend, seal_ledger
from learnloop.experiments.contextual_embeddings.e1 import pins as e1_pins

_PLAN_ID = re.compile(r"e1_[0-9a-f]{16}")


def local_root(path: Path) -> Path:
    resolved = Path(path).resolve()
    found = next((parent for parent in (resolved, *resolved.parents) if parent.name == "fixtures-local"), None)
    if found is None:
        raise ValueError("E1's state must lie under a fixtures-local directory")
    return found


def ledger_dir(anchor: Path) -> Path:
    """E1's ledger directory for the fixtures-local root holding ``anchor``."""

    return local_root(anchor).joinpath(*e1_pins.E1_LEDGER_DIR)


def prior_spend(anchor: Path, *, exclude: str | None = None) -> dict[str, Any]:
    directory = ledger_dir(anchor)
    plans = {}
    for path in sorted(directory.glob("e1_*.ledger")) if directory.exists() else []:
        plan_id = path.name[: -len(".ledger")]
        if plan_id != exclude:
            plans[plan_id] = ledger_spend(path)
    by_category: dict[str, Decimal] = {}
    for item in plans.values():
        for key, value in item["by_category"].items():
            by_category[key] = by_category.get(key, Decimal(0)) + Decimal(str(value))
    return {"plans": plans, "total_usd": float(sum((Decimal(item["committed_usd"]) for item in plans.values()),
                                                    Decimal(0))),
            "by_category": {key: float(value) for key, value in sorted(by_category.items())}}


def authorized_ledger(anchor: Path, plan_id: str, *, new_authorization: str | None = None) -> E0Ledger:
    """The ONE ledger of an E1 plan's authorization (``<plan_id>.ledger``)."""

    if not _PLAN_ID.fullmatch(str(plan_id)):
        raise ValueError("not an E1 plan id")
    directory = ledger_dir(anchor)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{plan_id}.ledger"
    carried: dict[str, dict[str, Any]] = {}
    if not path.exists():
        others = sorted(item for item in directory.glob("e1_*.ledger") if item != path)
        if others and not (new_authorization and new_authorization.strip()):
            raise PermissionError("another E1 plan's ledger exists; a different plan needs --new-authorization")
        for other in others:
            carried[other.name[: -len(".ledger")]] = seal_ledger(other, superseded_by=plan_id)
    ledger = E0Ledger(file=path, cap_usd=e1_pins.E1_CAP_USD, allocation=e1_pins.E1_ALLOCATION_USD,
                      max_requests=e1_pins.E1_MAX_PAID_REQUESTS, max_subscription_requests=0)
    ledger.bind_authorization(plan_id, new_authorization.strip() if new_authorization else None, carried=carried)
    return ledger


def budget_check(estimate: dict[str, float], prior: dict[str, Any]) -> dict[str, Any]:
    """Whether ``estimate`` fits E1's cumulative cap and allocations after ``prior``."""

    carried = float(prior.get("total_usd") or 0.0)
    by_category = prior.get("by_category") or {}
    categories = {}
    for name, allocation in e1_pins.E1_ALLOCATION_USD.items():
        left = round(allocation - float(by_category.get(name, 0.0)), 6)
        categories[name] = {"allocation_usd": allocation, "carried_usd": round(float(by_category.get(name, 0.0)), 6),
                            "remaining_usd": left, "estimated_usd": round(float(estimate.get(name, 0.0)), 6),
                            "fits": float(estimate.get(name, 0.0)) <= left}
    total = round(sum(float(value) for value in estimate.values()), 6)
    remaining = round(e1_pins.E1_CAP_USD - carried, 6)
    return {"cap_usd": e1_pins.E1_CAP_USD, "carried_usd": round(carried, 6), "remaining_usd": remaining,
            "carried_from": sorted(prior.get("plans") or {}), "estimated_usd": total, "categories": categories,
            "fits": total <= remaining and all(item["fits"] for item in categories.values())}
