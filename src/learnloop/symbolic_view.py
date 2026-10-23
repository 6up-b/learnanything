"""Reader workbench RW2b: the ONE accessor for stored symbolic results (fix round 11, the orchestrator's ruling).

A check's verdicts (``help_assists.step_verdicts_json``: each verdict's
``method``), its symbolic outcomes (``placement_json["symbolic"]``) and a
hint's claims (``contract_failures_json["claims"]``: each claim's
``status``) are stored as they were decided. Whether they may READ as
"checked" depends on ``workbench.symbolic_checks_enabled`` at read time (off
by default since fix round 9): with it off, a stored ``checked`` or
``checked_numerically`` reads as the model's reading. Every reader of these
fields goes through this module, with the CURRENT switch, never a value
cached with a job: the check view and help_state, a recheck's reused view, the
ladder's hint context, the hint views and the hint job's payload (cached and
first delivery), the workbench report and the diagnoser's workbench trace.
``tests/test_architecture.py`` keeps every other module off the raw fields.

The stored rows are history and stay as they were. Dependency-free (stdlib
only), so the diagnosis package may import it under
``evidence-never-reads-the-workbench``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from typing import Any

#: How the symbolic check decided a verdict or a claim.
SYMBOLIC_METHODS = frozenset(("checked", "checked_numerically"))
MODEL = "model"
MODEL_LABEL = "model's reading, not checked"


def switch(config: Any) -> bool:
    """``workbench.symbolic_checks_enabled`` from a config, a vault, or None (off)."""

    section = getattr(getattr(config, "config", config), "workbench", None)
    return bool(getattr(section, "symbolic_checks_enabled", False))


def switch_now(vault: Any) -> bool:
    """``workbench.symbolic_checks_enabled`` as the vault's config file says
    NOW (fix round 14, item 3): a job that holds a vault captured earlier (a
    post-attempt drain) reads the live file, never the captured snapshot.
    Unreadable: off."""

    root = getattr(vault, "root", None)
    if root is None:
        return switch(vault)
    try:
        from pathlib import Path

        from learnloop.config.loader import load_config

        return switch(load_config(Path(root) / "learnloop.toml", load_environment=False))
    except Exception:  # noqa: BLE001 - fail closed
        return False


def trace_view(trace: Mapping[str, Any] | None, *, enabled: bool) -> dict[str, Any] | None:
    """A diagnoser's workbench trace with each check's verdicts as read now."""

    if not trace:
        return trace  # type: ignore[return-value]
    assists = []
    for entry in trace.get("assists") or ():
        if isinstance(entry, Mapping) and entry.get("assist") == "check":
            verdicts = [{**verdict, "method": symbolic_view(verdict.get("method"), enabled=enabled)}
                        for verdict in entry.get("verdicts") or () if isinstance(verdict, Mapping)]
            assists.append({**entry, "verdicts": verdicts})
        else:
            assists.append(entry)
    return {**trace, "assists": assists}


def symbolic_view(raw: Any, *, enabled: bool) -> str:
    """A stored method or claim status as it may be read now."""

    value = str(raw or MODEL)
    return value if enabled or value not in SYMBOLIC_METHODS else MODEL


def _loads(value: Any, default: Any) -> Any:
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def verdict_records(row: Mapping[str, Any] | None, *, enabled: bool) -> list[dict[str, Any]]:
    """A check row's stored verdict records, each ``method`` as read now."""

    records = _loads((row or {}).get("step_verdicts_json"), [])
    out = []
    for record in records if isinstance(records, list) else []:
        if isinstance(record, Mapping):
            out.append({**record, "method": symbolic_view(record.get("method"), enabled=enabled)})
    return out


def has_verdict_record(row: Mapping[str, Any] | None) -> bool:
    """Whether a row recorded step verdicts at all (an empty record
    included): a help's unaided progress needs the verdicts standing at its
    delivery, and none on record is not "none valid" (Reader RW2c fix round
    3, M1)."""

    return (row or {}).get("step_verdicts_json") is not None


def symbolic_outcomes(placement: Any, *, enabled: bool) -> list[dict[str, Any]]:
    """A check row's stored symbolic outcomes (``placement_json``), each
    ``method`` as read now (with the switch off a decided ``holds`` is not shown)."""

    entries = _loads(placement, {}).get("symbolic") if isinstance(_loads(placement, {}), Mapping) else None
    out = []
    for entry in entries or ():
        if isinstance(entry, Mapping):
            method = symbolic_view(entry.get("method"), enabled=enabled)
            out.append({**entry, "method": method, **({} if method != MODEL else {"holds": None})})
    return out


def claim_view(claim: Mapping[str, Any], *, enabled: bool) -> dict[str, Any]:
    """One stored claim as read now (its status and its label)."""

    out = dict(claim)
    status = symbolic_view(out.get("status"), enabled=enabled) if out.get("status") in SYMBOLIC_METHODS \
        else out.get("status")
    if status != out.get("status"):
        out.update(status=status, label=MODEL_LABEL)
    return out


def claims_view(claims: Iterable[Any] | None, *, enabled: bool) -> list[dict[str, Any]]:
    return [claim_view(claim, enabled=enabled) for claim in claims or () if isinstance(claim, Mapping)]


def stored_claims(row: Mapping[str, Any] | None, *, enabled: bool) -> list[dict[str, Any]]:
    """A hint row's stored claims (``contract_failures_json``) as read now."""

    record = _loads((row or {}).get("contract_failures_json"), {})
    return claims_view(record.get("claims") if isinstance(record, Mapping) else None, enabled=enabled)


def rounds_view(rounds: Iterable[Any] | None, *, enabled: bool) -> list[Any]:
    """A hint's writer rounds with each round's claims as they may be stored
    NOW (fix round 13: the switch read right before the row is serialized)."""

    out = []
    for entry in rounds or ():
        if isinstance(entry, Mapping) and entry.get("claims"):
            out.append({**entry, "claims": claims_view(entry.get("claims"), enabled=enabled)})
        else:
            out.append(entry)
    return out


def live_switch(reader: Any) -> bool | None:
    """A live switch reader's value now (None: no reader; an error: off)."""

    if reader is None:
        return None
    try:
        return bool(reader())
    except Exception:  # noqa: BLE001 - fail closed
        return False


def hint_result_view(result: Mapping[str, Any], *, enabled: bool) -> dict[str, Any]:
    """A hint job's payload as read now: its claims remapped and the CURRENT
    switch (the payload is cached with the job; the switch is read each time)."""

    out = dict(result)
    if "claims" in out:
        out["claims"] = claims_view(out.get("claims"), enabled=enabled)
    out["symbolic_enabled"] = bool(enabled)
    return out


__all__ = [
    "has_verdict_record",
    "MODEL",
    "MODEL_LABEL",
    "SYMBOLIC_METHODS",
    "claim_view",
    "claims_view",
    "hint_result_view",
    "live_switch",
    "rounds_view",
    "stored_claims",
    "switch",
    "switch_now",
    "trace_view",
    "symbolic_outcomes",
    "symbolic_view",
    "verdict_records",
]
