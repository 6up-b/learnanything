"""A1: what was decided before the router saw candidates, linked into each committed decision.

A decision's own row holds the candidates it chose among and the propensity of its
draw. Offline evaluation also needs what stood upstream of that: which items were
considered at all, which the scheduler's gates and the plan's classification
refused and why, the probe and teach-back decisions in full, the likelihoods and
configuration they read, and the code that ran. Its parts:

* ``gates``: the scheduler's exclusions by reason (every id), the probe block, the
  cold deferrals. Recorded whether or not a session exists yet (a plan's Start builds
  before one opens, when the scheduler writes no slate).
* ``classification``: each item the plan classified, its lane and reason, and the
  **admission**: deterministic, so probability 1 (it reached a candidate pool) or
  probability 0 (with why). The decision's own propensity stays conditional on
  admission (:func:`admission_probability`).
* ``upstream``: every value-of-information decision of the build (probe episodes,
  further teach-backs, due project probes) with all its candidates (mvp-0.44 lifts
  the six-summary cap; ``voi_stopping.SiteDecision.record_all_candidates``), and the
  likelihood rows of in-episode probes, plus any upstream draw.
* ``inputs``: what the build read: each considered item's priority, the session,
  minutes, requests.
* ``config``: the configuration that shaped the build.

**Size.** A part is stored once by its own hash (``prefilter_payloads``); a receipt
holds counts and hashes only, so unchanged gates and configuration are referenced and
never copied. ``inputs`` changes with each build, as the priorities do, so it is kept
compact. ``learnloop data-capture report`` states the rows and bytes actually written.

A receipt never blocks the learner's plan or changes what is served: every writer
fails soft, and a vault below the migration simply writes none.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import lru_cache
import hashlib
import json
import logging
import os
from pathlib import Path
import subprocess
from typing import Any

from learnloop.data_capture.gates import receipts_on
from learnloop.db.stores import data_capture as store
from learnloop.ids import new_ulid

logger = logging.getLogger(__name__)

RECEIPT_VERSION = "prefilter_v1"
SURFACE_PLAN_POOL = "plan_pool"
SURFACE_TODAY_OFFER = "today_offer"
SURFACE_DECISION_ROW = "decision_row"
#: ``LEARNLOOP_CODE_REVISION`` names the running code where no checkout does (a packaged app).
CODE_REVISION_ENV = "LEARNLOOP_CODE_REVISION"
#: Decimal places of a priority or minutes in ``inputs``: float noise must not defeat the dedupe.
_ROUND_DIGITS = 4


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def code_revision() -> str:
    """The running code's revision: the environment's name for it, the checkout's commit, or the
    installed package's version, labelled. Asked once per process; never raises."""

    named = os.environ.get(CODE_REVISION_ENV, "").strip()
    if named:
        return named
    try:
        found = subprocess.run(
            ["git", "-C", str(Path(__file__).resolve().parent), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=2, check=False,
        )
        if found.returncode == 0 and found.stdout.strip():
            return f"git:{found.stdout.strip()}"
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        from importlib.metadata import version

        return f"package:{version('learnloop')}"
    except Exception:  # noqa: BLE001 - a revision we cannot name is said to be unknown
        return "unknown"


@dataclass(frozen=True)
class Material:
    """One build's prefilter, its parts already canonical, ready to link into its decisions."""

    surface: str
    parts: Mapping[str, str]
    considered: int
    admitted: int
    refused: int
    versions: Mapping[str, Any] = field(default_factory=dict)
    session_present: bool = False
    scheduler_trace: bool = False

    def hashes(self) -> dict[str, str]:
        return {name: content_hash(content) for name, content in self.parts.items()}


def _round(value: Any) -> Any:
    return round(float(value), _ROUND_DIGITS) if isinstance(value, (int, float)) and not isinstance(value, bool) else value


def _trace_parts(trace: Any) -> dict[str, Any]:
    """The scheduler's own parts of a build's trace (``OfferTrace``), ``{}`` with none."""

    if trace is None:
        return {
            "gates": {"exclusions": {}, "trace": "not_available"},
            "upstream": {"voi_decisions": [], "likelihoods": {}, "trace": "not_available"},
            "considered": [],
            "session": {},
            "config": {},
        }
    return {
        "gates": {
            "exclusions": {str(reason): sorted(set(ids)) for reason, ids in sorted(dict(trace.exclusions).items())},
            "probe_block_reason": trace.probe_block_reason,
            "cold_deferrals": [dict(row) for row in trace.cold_deferrals],
            "pinned_item_id": trace.pinned_item_id,
            "placement_active": trace.placement_active,
        },
        "upstream": {
            "voi_decisions": [dict(row) for row in trace.voi_decisions],
            "teach_back_exclusion_reason": trace.teach_back_exclusion_reason,
            "likelihoods": {
                item.practice_item_id: dict(item.hypothesis_channel)
                for item in trace.considered if getattr(item, "hypothesis_channel", None)
            },
            # A draw upstream of the router (off where staged plans are deterministic, the default).
            "exploration": {key: value for key, value in dict(trace.exploration).items() if key != "seed"},
            "base_propensity": {key: _round(value) for key, value in sorted(dict(trace.base_propensity).items()) if value},
        },
        "considered": [
            {"id": item.practice_item_id, "lo": item.learning_object_id, "priority": _round(item.priority)}
            for item in trace.considered
        ],
        "session": {key: value for key, value in dict(trace.session_context).items() if key != "session_id"},
        "config": dict(trace.config_snapshot),
    }


def _admission(admitted: Iterable[str], refused: Mapping[str, Iterable[str]]) -> dict[str, Any]:
    """Deterministic admission as probability 1 and probability 0 (with why)."""

    return {
        "deterministic": True,
        "router_probability": "conditional_on_admission",
        "probability_1": sorted(set(admitted)),
        "probability_0": {str(reason): sorted(set(ids)) for reason, ids in sorted(refused.items()) if ids},
    }


def _material(surface: str, built: Mapping[str, Any], *, classification: Mapping[str, Any], inputs: Mapping[str, Any],
              config_extra: Mapping[str, Any], versions: Mapping[str, Any], considered: int, admitted: int, refused: int,
              session_present: bool, scheduler_trace: bool) -> Material:
    parts = {
        "gates": canonical(built["gates"]),
        "classification": canonical(classification),
        "upstream": canonical(built["upstream"]),
        "inputs": canonical(inputs),
        "config": canonical({**dict(built["config"]), **dict(config_extra)}),
    }
    likelihoods = built["upstream"].get("likelihoods") or {}
    return Material(
        surface=surface,
        parts=parts,
        considered=considered,
        admitted=admitted,
        refused=refused,
        versions={**dict(versions), **({"likelihood_rows_hash": content_hash(canonical(likelihoods))} if likelihoods else {})},
        session_present=session_present,
        scheduler_trace=scheduler_trace,
    )


def plan_pool_material(
    trace: Any,
    pool: Sequence[Any],
    *,
    session_present: bool,
    minutes: float,
    minutes_left: float | None,
    lanes_allowed: Sequence[str],
    reentry: bool,
    requested: Iterable[str],
    push: Iterable[str],
    deadlines: Mapping[str, str],
    open_problems: Iterable[str] | None,
    repair_rule: str,
    probes_planned_today: int,
    plan_config: Mapping[str, Any],
    versions: Mapping[str, Any],
) -> Material:
    """The plan's pool: the scheduler's gates, then the lanes (A1's "no OfferTrace today")."""

    built = _trace_parts(trace)
    gate_refused = built["gates"]["exclusions"]
    later: dict[str, list[str]] = {}
    voi_receipts = []
    rows = []
    for item in pool:
        rows.append({
            "id": item.practice_item_id, "lo": item.learning_object_id, "lane": item.lane, "reason": item.reason,
            "minutes": _round(item.est_minutes), "rank": item.rank,
            **({"check": item.check_kind} if item.check_kind else {}),
            **({"followup": True} if item.followup else {}),
            **({"requested": True} if item.requested else {}),
        })
        if item.lane is None:
            later.setdefault(f"plan:{item.reason}", []).append(item.practice_item_id)
        if getattr(item, "voi", None) is not None:
            voi_receipts.append(dict(item.voi))
    # The due project probes' value decisions are upstream too (kept or held back).
    if voi_receipts:
        built["upstream"] = {**built["upstream"], "project_probes": voi_receipts}
    admitted = [item.practice_item_id for item in pool if item.lane is not None]
    refused = {**gate_refused, **later}
    classification = {"pool": rows, "lanes_allowed": list(lanes_allowed), "admission": _admission(admitted, refused)}
    considered_ids = {item.practice_item_id for item in pool} | {i for ids in gate_refused.values() for i in ids}
    inputs = {
        "considered": built["considered"], "session": built["session"],
        "minutes": _round(minutes), "minutes_left": _round(minutes_left), "reentry": bool(reentry),
        "requested": sorted(set(requested)), "push": sorted(set(push)), "deadlines": dict(sorted(deadlines.items())),
        "open_problems": None if open_problems is None else sorted(set(open_problems)), "repair_rule": repair_rule,
        "probes_planned_today": int(probes_planned_today),
    }
    return _material(SURFACE_PLAN_POOL, built, classification=classification, inputs=inputs,
                     config_extra={"plan": dict(plan_config)}, versions=versions, considered=len(considered_ids),
                     admitted=len(set(admitted)), refused=len(considered_ids - set(admitted)),
                     session_present=session_present, scheduler_trace=trace is not None)


def today_offer_material(trace: Any, *, offered: Iterable[str], versions: Mapping[str, Any]) -> Material:
    """Today's composed offer: the same scheduler parts as the plan's pool."""

    built = _trace_parts(trace)
    offered_ids = sorted(set(offered))
    gate_refused = built["gates"]["exclusions"]
    considered_ids = {row["id"] for row in built["considered"]} | {i for ids in gate_refused.values() for i in ids}
    composed_out = sorted({row["id"] for row in built["considered"]} - set(offered_ids))
    refused = {**gate_refused, **({"not_in_the_composed_offer": composed_out} if composed_out else {})}
    classification = {"admission": _admission(offered_ids, refused)}
    inputs = {"considered": built["considered"], "session": built["session"], "limit": trace.limit}
    return _material(SURFACE_TODAY_OFFER, built, classification=classification, inputs=inputs, config_extra={},
                     versions=versions, considered=len(considered_ids | set(offered_ids)),
                     admitted=len(offered_ids), refused=len(considered_ids - set(offered_ids)),
                     session_present=bool(trace.session_id), scheduler_trace=True)


def decision_row_material(row: Mapping[str, Any], *, versions: Mapping[str, Any]) -> Material:
    """A decision whose path keeps no scheduler build: what its own row says it considered and refused,
    named as such (``scheduler_trace = 0``), so the report never reads it as a complete trace."""

    candidates = json.loads(row.get("candidates_json") or "[]")
    exclusions = json.loads(row.get("exclusions_json") or "{}")
    named = (exclusions.get("named") or {}) if isinstance(exclusions, Mapping) else {}
    counted = (exclusions.get("counted") or {}) if isinstance(exclusions, Mapping) else {}
    refs = [str(entry.get("ref")) for entry in candidates if isinstance(entry, Mapping)]
    feasible = [str(entry.get("ref")) for entry in candidates if isinstance(entry, Mapping) and entry.get("feasible", True)]
    built = {"gates": {"exclusions": named, "counted": counted, "trace": "decision_row"},
             "upstream": {"voi_decisions": [], "likelihoods": {}, "trace": "decision_row"}, "config": {}}
    refused_ids = {str(i) for ids in named.values() for i in ids}
    return _material(SURFACE_DECISION_ROW, built, classification={"admission": _admission(feasible, named)},
                     inputs={"snapshot_hash": row.get("snapshot_hash")}, config_extra={}, versions=versions,
                     considered=len(set(refs) | refused_ids), admitted=len(set(feasible)),
                     refused=len(refused_ids), session_present=bool(row.get("session_id")), scheduler_trace=False)


def record(connection: Any, *, decision_id: str, decision_kind: str, material: Material | None, config: Any, at: str) -> bool:
    """Link ``material`` into a committed decision, on the caller's connection and transaction. Fails
    soft: off, below the migration, or refused, nothing is written and the decision stands."""

    if material is None or not receipts_on(config):
        return False
    try:
        if not store.receipts_present(connection):
            return False
        hashes = material.hashes()
        versions = {"receipt": RECEIPT_VERSION, **dict(material.versions)}
        row = {
            "id": new_ulid(),
            "decision_id": decision_id,
            "decision_kind": decision_kind,
            "surface": material.surface,
            "receipt_version": RECEIPT_VERSION,
            "algorithm_version": str(config.algorithms.algorithm_version),
            "code_revision": code_revision(),
            "config_hash": hashes["config"],
            "versions_json": canonical(versions),
            "session_present": 1 if material.session_present else 0,
            "scheduler_trace": 1 if material.scheduler_trace else 0,
            "considered_count": material.considered,
            "admitted_count": material.admitted,
            "refused_count": material.refused,
            "gates_hash": hashes["gates"],
            "classification_hash": hashes["classification"],
            "upstream_hash": hashes["upstream"],
            "inputs_hash": hashes["inputs"],
            "config_payload_hash": hashes["config"],
            "created_at": at,
        }
        parts = {hashes[name]: (name, content) for name, content in material.parts.items()}
        return store.insert_prefilter_receipt(connection, row, parts)
    except Exception:  # noqa: BLE001 - a receipt never blocks the learner's plan
        logger.warning("data capture: the prefilter receipt of %s was not written", decision_id, exc_info=True)
        return False


def read(connection: Any, decision_id: str) -> dict[str, Any] | None:
    """One decision's receipt with its parts resolved (read-only), or None."""

    if not store.receipts_present(connection):
        return None
    row = store.prefilter_receipt(connection, decision_id)
    if row is None:
        return None
    return {
        **row,
        "versions": json.loads(row["versions_json"]),
        "gates": store.prefilter_part(connection, row["gates_hash"]),
        "classification": store.prefilter_part(connection, row["classification_hash"]),
        "upstream": store.prefilter_part(connection, row["upstream_hash"]),
        "inputs": store.prefilter_part(connection, row["inputs_hash"]),
        "config": store.prefilter_part(connection, row["config_payload_hash"]),
    }


def admission_probability(receipt: Mapping[str, Any], practice_item_id: str) -> float | None:
    """The deterministic admission of an item: 1, 0, or None when the build never considered it.
    The joint probability of serving it is this times the decision's own (conditional) propensity."""

    admission = (receipt.get("classification") or {}).get("admission") or {}
    if practice_item_id in (admission.get("probability_1") or ()):
        return 1.0
    if any(practice_item_id in ids for ids in (admission.get("probability_0") or {}).values()):
        return 0.0
    return None


__all__ = [
    "CODE_REVISION_ENV",
    "Material",
    "RECEIPT_VERSION",
    "SURFACE_DECISION_ROW",
    "SURFACE_PLAN_POOL",
    "SURFACE_TODAY_OFFER",
    "admission_probability",
    "canonical",
    "code_revision",
    "content_hash",
    "decision_row_material",
    "plan_pool_material",
    "read",
    "record",
    "today_offer_material",
]
