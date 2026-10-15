"""`learnloop diagnosis calibration`: how good were the saved forecasts?

Reads the forecast receipt family (saved diagnosis forecasts, owner go-ahead
2026-10-15; docs/reviews/diagnosis-forecast-receipts.md) and resolves each
receipt at read time, through its own exact binding and nothing else:

* ``diagnosis_next_observation`` (``forecast_receipts``): the frozen rule in
  the receipt (``target``) names the observation: among the attempts created
  at or after the diagnosed attempt that the receipt was NOT written after
  (``target.seen_attempt_ids``), the first, in (created_at, id) order, whose
  recorded evidence facets include the facet (canonical now: aliases and
  settled merges) and that tests it unaided (a qualifying type, not primed,
  no hint); assisted, primed or non-test attempts before it are counted as
  intervening. It must answer a plan or probe presentation or a scheduler
  offer, else the forecast is censored ``unbound_attempt``: the next
  observation is never replaced by a later one. Its emission: ``same_error``
  when the attempt's current error events show the pattern (error type or
  registry misconception), else ``pass`` when the facet's outcome under the
  assessment contract its current grade was read under (the version its rows
  cite, else the current item's, as replay reads it; EVSI calibration's
  target-facet weighting, review F5; bucketed as the facet updater buckets
  it) is ``high``, else ``other_error``.
* ``repair_cold_outcome`` (``forecast_receipts``): the task's consumed attempt
  and the cold verification's terminal disposition for it
  (``causal_cold_outcomes``). A measured disposition resolves on the cold
  attempt's CURRENT correctness against the threshold frozen in the receipt;
  any other disposition (contaminated, same surface, expired, missing chain)
  censors it with that reason.
* ``check_outcome`` (``voi_forecasts``, EVSI calibration Part B): the same
  family read through an adapter (forecaster = the decision site), joined by
  :mod:`.live_report`'s exact adapters and scored in each site's alphabet.

Every resolution reads the attempt's current grade, so a regrade re-resolves;
a grade held for review (``held_grades.held_for_review_attempts``) resolves
nothing until it is released. Censored and pending forecasts are counted with
their reasons, never scored. Read-only; replay never reads receipts.
"""

from __future__ import annotations

import bisect
import json
import math
import sqlite3
from collections import Counter
from contextlib import closing
from typing import Any, Callable, Mapping, Sequence

from learnloop.db.connection import connect
from learnloop.db.stores import forecast_receipts as receipt_store
from learnloop.db.stores import voi_forecasts as voi_store
from learnloop.db.stores.facet_identity import settled_merge_rows
from learnloop.evsi_calibration import live_report as LR
from learnloop.evsi_calibration.metrics import reliability
from learnloop.held_grades import held_for_review_attempts
from learnloop.learner.assessment_contracts import compile_assessment_contract
from learnloop.learner.capability_mapping import ROLE_WEIGHTS
from learnloop.learner.facet_diagnostics import facet_outcome_bucket
from learnloop.outcome_contract import GRADE_HELD_FOR_REVIEW, unassessed_evidence_row
from learnloop.scheduling import forecast_receipts as FR
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

#: v1: the three kinds, exact bindings, held grades unresolved, the honest n.
REPORT_VERSION = "forecast_calibration_report_v1"

#: Fewer resolved forecasts than this and a reliability table says little.
SMALL_N = 30

RESOLVED = "resolved"
PENDING = "pending"
HELD = "held"
CENSORED = "censored"

#: Join statuses of the check-outcome adapter that are still open (the rest
#: that realize nothing are right-censored with their reason).
_CHECK_PENDING = frozenset({"pending"})


def _loads(value: Any, default: Any) -> Any:
    if value is None:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _has(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone() is not None


def _resolution(state: str, reason: str, **extra: Any) -> dict[str, Any]:
    return {"state": state, "reason": reason, **extra}


# -- the shared ledger reads --------------------------------------------------------------------


class _Ledgers:
    """Lazy, read-only views every resolver shares (one snapshot)."""

    def __init__(self, connection: sqlite3.Connection, vault: LoadedVault) -> None:
        self.connection = connection
        self.vault = vault
        self._attempts: list[dict[str, Any]] | None = None
        self._keys: list[tuple[str, str]] = []
        self._canonical: Callable[[str], str] | None = None
        self._held: dict[str, bool] = {}

    def canonical(self, facet: str) -> str:
        if self._canonical is None:
            merges = dict(settled_merge_rows(self.connection)) if _has(self.connection, "facet_merges") else {}

            def resolve(value: str) -> str:
                current = self.vault.canonical_facet_id(value)
                seen: set[str] = set()
                while current in merges and current not in seen:
                    seen.add(current)
                    current = self.vault.canonical_facet_id(merges[current])
                return current

            self._canonical = resolve
        return self._canonical(facet)

    def attempts(self) -> list[dict[str, Any]]:
        if self._attempts is None:
            self._attempts = [
                dict(row)
                for row in self.connection.execute(
                    "SELECT id, practice_item_id, attempt_type, primed, hints_used, evidence_facets_json, "
                    "plan_presentation_id, probe_presentation_id, scheduler_candidate_id, correctness, created_at "
                    "FROM practice_attempts ORDER BY created_at, id"
                )
            ]
            self._keys = [(str(a["created_at"]), str(a["id"])) for a in self._attempts]
        return self._attempts

    def attempts_from(self, created_at: str) -> list[dict[str, Any]]:
        attempts = self.attempts()
        return attempts[bisect.bisect_left(self._keys, (created_at, "")):]

    def facets_of(self, attempt: Mapping[str, Any]) -> tuple[set[str], str]:
        """The attempt's facets (canonical now) and where they came from."""

        recorded = _loads(attempt.get("evidence_facets_json"), None)
        if isinstance(recorded, list) and recorded:
            return {self.canonical(str(f)) for f in recorded if f}, "recorded"
        item = self.vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
        facets = list(getattr(item, "evidence_facets", None) or [])
        return {self.canonical(str(f)) for f in facets if f}, "current_item"

    def held(self, attempt_id: str) -> bool:
        if attempt_id not in self._held:
            self._held[attempt_id] = attempt_id in held_for_review_attempts(self.connection, (attempt_id,))
        return self._held[attempt_id]

    def _contract(self, attempt_id: str, contract_id: str | None) -> tuple[Mapping[str, Any] | None, str]:
        """The assessment contract the current grade was read under, as replay
        reads it: the version its rows cite, else (a regrade of an item
        without a frozen method reads the item as it is now, and cites none)
        the current item's compiled contract."""

        if contract_id is not None:
            stored = self.connection.execute(
                "SELECT contract_json FROM assessment_contract_versions WHERE id = ?", (contract_id,)
            ).fetchone()
            contract = _loads(stored["contract_json"], None) if stored is not None else None
            return (contract, "graded") if isinstance(contract, Mapping) else (None, "graded")
        attempt = self.connection.execute(
            "SELECT practice_item_id FROM practice_attempts WHERE id = ?", (attempt_id,)
        ).fetchone()
        item = self.vault.practice_items.get(str(attempt["practice_item_id"])) if attempt is not None else None
        rubric = self.vault.rubric_for_item(item) if item is not None else None
        if item is None or rubric is None:
            return None, "current_item"
        return compile_assessment_contract(self.vault, item, rubric=rubric), "current_item"

    def facet_outcome(self, attempt_id: str, facet_id: str) -> tuple[float | None, str, str | None]:
        """One attempt's outcome on ``facet_id`` under the contract its current
        grade was read under: ``(outcome, "realized", contract source)``, or
        ``(None, why not, source)``.

        As EVSI calibration reads a follow-up's target facet (review F5) and
        ``recall_coverage.derive_facet_outcomes`` weights it: each current,
        assessed criterion whose observation targets include the facet
        (canonical now), weighted by its points and the facet's role-weighted
        share of its targets; an unassessed criterion contributes nothing. A
        don't-know answer fails every facet its contract measures.
        """

        attempt = self.connection.execute(
            "SELECT attempt_type, declared_dont_know FROM practice_attempts WHERE id = ?", (attempt_id,)
        ).fetchone()
        if attempt is None:
            return None, "no_attempt", None
        latest, contract_id = self.current_evidence(attempt_id)
        if not latest:
            return None, "ungraded", None
        contract, source = self._contract(attempt_id, contract_id)
        if contract is None:
            return None, "graded_contract_unknown", source
        target = self.canonical(facet_id)
        dont_know = attempt["attempt_type"] == "dont_know" or bool(attempt["declared_dont_know"])
        numerator = denominator = 0.0
        mapped_any = False
        for criterion in contract.get("criteria") or []:
            weights: dict[str, float] = {}
            for observed in criterion.get("targets") or []:
                role_weight = float(ROLE_WEIGHTS.get(observed.get("role"), 1.0))
                if observed.get("facet") and role_weight > 0:
                    facet = self.canonical(str(observed["facet"]))
                    weights[facet] = weights.get(facet, 0.0) + role_weight
            total = sum(weights.values())
            share = weights.get(target, 0.0) / total if total > 0 else 0.0
            if share <= 0:
                continue
            mapped_any = True
            row = latest.get(str(criterion.get("id")))
            if row is None or unassessed_evidence_row(row["attribution_json"]):
                continue  # not assessed: contributes nothing (never a zero-point failure)
            points = float(criterion.get("max_points") or 0.0)
            weight = max(points, 0.0) * share
            correctness = 0.0 if dont_know else min(max(float(row["points_awarded"]) / max(points, 1e-9), 0.0), 1.0)
            numerator += weight * correctness
            denominator += weight
        if not mapped_any:
            return None, "facet_not_in_contract", source
        if denominator <= 0:
            return None, "facet_unassessed", source
        return numerator / denominator, "realized", source

    def current_evidence(self, attempt_id: str) -> tuple[dict[str, sqlite3.Row], str | None]:
        """The attempt's current grade per criterion, read as replay reads it
        (``replay_existing_attempt``): the surviving rows in (created_at,
        criterion) order, the last row of a criterion winning (a regrade's
        rows supersede the grade they replace), and the first contract
        version they cite."""

        latest: dict[str, sqlite3.Row] = {}
        contract_id: str | None = None
        for row in self.connection.execute(
            "SELECT criterion_id, points_awarded, attribution_json, assessment_contract_version_id "
            "FROM grading_evidence WHERE attempt_id = ? AND superseded_at IS NULL "
            "ORDER BY created_at, criterion_id, id",
            (attempt_id,),
        ):
            latest[str(row["criterion_id"])] = row
            if contract_id is None and row["assessment_contract_version_id"]:
                contract_id = str(row["assessment_contract_version_id"])
        return latest, contract_id

    def graded(self, attempt_id: str) -> bool:
        return bool(self.current_evidence(attempt_id)[0])

    def assessed(self, attempt_id: str) -> bool:
        latest, _contract = self.current_evidence(attempt_id)
        return any(not unassessed_evidence_row(row["attribution_json"]) for row in latest.values())

    def shows_pattern(self, attempt_id: str, pattern: Mapping[str, Any]) -> bool:
        if not _has(self.connection, "error_events"):
            return False
        error_type = pattern.get("error_type")
        misconception = pattern.get("misconception_id")
        for row in self.connection.execute(
            "SELECT error_type, misconception_id FROM error_events WHERE attempt_id = ?", (attempt_id,)
        ):
            if error_type and row[0] == error_type:
                return True
            if misconception and row[1] == misconception:
                return True
        return False


# -- the diagnosis forecast -----------------------------------------------------------------------


def _presentation(attempt: Mapping[str, Any]) -> str | None:
    for column, label in (
        ("plan_presentation_id", "plan_presentation"),
        ("probe_presentation_id", "probe_presentation"),
        ("scheduler_candidate_id", "scheduler_candidate"),
    ):
        if attempt.get(column):
            return label
    return None


def next_observation(ledgers: _Ledgers, receipt: Mapping[str, Any]) -> dict[str, Any]:
    """The frozen rule's observation: ``{attempt, intervening, facet}`` or a reason."""

    target = (receipt.get("forecast") or {}).get("target") or {}
    facet = ledgers.canonical(str(target.get("facet_id") or receipt.get("facet_id") or ""))
    after = str(target.get("after_created_at") or "")
    if not facet or not after:
        return {"reason": "no_frozen_rule"}
    excluded = {str(value) for value in target.get("seen_attempt_ids") or []}
    excluded.add(str(target.get("after_attempt_id") or receipt.get("source_attempt_id") or ""))
    qualifying = set(target.get("qualifying_attempt_types") or [])
    intervening: list[str] = []
    for attempt in ledgers.attempts_from(after):
        if str(attempt["id"]) in excluded:
            continue
        facets, source = ledgers.facets_of(attempt)
        if facet not in facets:
            continue
        unaided = (
            str(attempt.get("attempt_type")) in qualifying
            and not attempt.get("primed")
            and not int(attempt.get("hints_used") or 0)
        )
        if not unaided:
            intervening.append(str(attempt["id"]))
            continue
        return {"attempt": attempt, "intervening": intervening, "facet": facet, "facets_from": source}
    return {"reason": "awaiting_observation", "intervening": intervening, "facet": facet}


def resolve_diagnosis(ledgers: _Ledgers, receipt: Mapping[str, Any]) -> dict[str, Any]:
    if receipt.get("binding_kind") == FR.NO_BINDING:
        return _resolution(CENSORED, str(receipt.get("censor_reason") or "no_binding"))
    found = next_observation(ledgers, receipt)
    attempt = found.get("attempt")
    if attempt is None:
        reason = str(found.get("reason"))
        state = PENDING if reason == "awaiting_observation" else CENSORED
        return _resolution(state, reason, intervening=len(found.get("intervening") or []))
    attempt_id = str(attempt["id"])
    common = {"attempt_id": attempt_id, "intervening": len(found["intervening"]), "facets_from": found["facets_from"]}
    binding = _presentation(attempt)
    if binding is None:
        return _resolution(CENSORED, "unbound_attempt", **common)
    common["binding"] = binding
    if ledgers.held(attempt_id):
        return _resolution(HELD, GRADE_HELD_FOR_REVIEW, **common)
    if not ledgers.graded(attempt_id):
        return _resolution(PENDING, "ungraded", **common)
    body = receipt.get("forecast") or {}
    if ledgers.shows_pattern(attempt_id, body.get("pattern") or {}):
        return _resolution(RESOLVED, "realized", emission="same_error", **common)
    outcome, why, contract = ledgers.facet_outcome(attempt_id, found["facet"])
    if outcome is None:
        if why == "ungraded":
            return _resolution(PENDING, why, **common)
        return _resolution(CENSORED, why, **common)
    emission = "pass" if facet_outcome_bucket(outcome) == "high" else "other_error"
    return _resolution(RESOLVED, "realized", emission=emission, facet_outcome=round(outcome, 4),
                       contract=contract, **common)


# -- the repair forecast --------------------------------------------------------------------------

_MEASURED = ("cold_success", "cold_failure")


def resolve_repair(ledgers: _Ledgers, receipt: Mapping[str, Any]) -> dict[str, Any]:
    if receipt.get("binding_kind") == FR.NO_BINDING:
        return _resolution(CENSORED, str(receipt.get("censor_reason") or "no_binding"))
    task_id = receipt.get("followup_task_id")
    connection = ledgers.connection
    if not task_id or not _has(connection, "followup_tasks"):
        return _resolution(CENSORED, "no_task_receipt")
    task = connection.execute(
        "SELECT status, consumed_attempt_id FROM followup_tasks WHERE id = ?", (str(task_id),)
    ).fetchone()
    if task is None:
        return _resolution(CENSORED, "no_task_receipt")
    dispositions = (
        [
            dict(row)
            for row in connection.execute(
                "SELECT outcome, cold_attempt_id FROM causal_cold_outcomes WHERE followup_task_id = ? "
                "ORDER BY created_at, id",
                (str(task_id),),
            )
        ]
        if _has(connection, "causal_cold_outcomes")
        else []
    )
    cold_attempt_id = task["consumed_attempt_id"]
    if not cold_attempt_id:
        closed = next((d for d in dispositions if d["outcome"] not in _MEASURED), None)
        if closed is not None:
            return _resolution(CENSORED, str(closed["outcome"]))
        return _resolution(PENDING, "awaiting_cold_attempt", task_status=task["status"])
    cold_attempt_id = str(cold_attempt_id)
    common = {"attempt_id": cold_attempt_id, "binding": "followup_task"}
    if ledgers.held(cold_attempt_id):
        return _resolution(HELD, GRADE_HELD_FOR_REVIEW, **common)
    disposition = next((d for d in dispositions if str(d.get("cold_attempt_id") or "") == cold_attempt_id), None)
    if disposition is None:
        return _resolution(PENDING, "awaiting_cold_verification", **common)
    if disposition["outcome"] not in _MEASURED:
        return _resolution(CENSORED, str(disposition["outcome"]), **common)
    if not ledgers.assessed(cold_attempt_id):
        return _resolution(CENSORED, "cold_attempt_unassessed", **common)
    attempt = connection.execute(
        "SELECT correctness FROM practice_attempts WHERE id = ?", (cold_attempt_id,)
    ).fetchone()
    if attempt is None or attempt["correctness"] is None:
        return _resolution(PENDING, "ungraded", **common)
    threshold = float(((receipt.get("forecast") or {}).get("target") or {}).get("success_threshold", 0.8))
    emission = "cold_success" if float(attempt["correctness"]) >= threshold else "cold_failure"
    return _resolution(RESOLVED, "realized", emission=emission,
                       regraded_since_verification=emission != disposition["outcome"], **common)


# -- the check-outcome adapter (voi_forecasts) ----------------------------------------------------


def check_outcome_rows(
    connection: sqlite3.Connection, vault: LoadedVault, *, since: str | None
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """``voi_forecasts`` as receipts of the family, each with its resolution."""

    rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
    if not voi_store.has_table(connection):
        return rows
    adapters = [LR.RouterOutcomeAdapter(connection), LR.LedgerOutcomeAdapter(connection)]
    for forecast in voi_store.list_forecasts(connection, since=since):
        joined = LR._join(connection, vault, forecast, adapters)
        status = str(joined.get("status"))
        extra = {"attempt_id": joined.get("attempt_id"), "binding": joined.get("adapter")}
        if joined.get("emission") is not None:
            resolution = _resolution(RESOLVED, "realized", emission=joined["emission"], **extra)
        elif status == GRADE_HELD_FOR_REVIEW:
            resolution = _resolution(HELD, status, **extra)
        elif status in _CHECK_PENDING:
            resolution = _resolution(PENDING, status, **extra)
        else:
            resolution = _resolution(CENSORED, status, **extra)
        receipt = {
            "id": forecast["id"],
            "kind": FR.CHECK_OUTCOME,
            "forecaster": str(forecast.get("site")),
            "forecaster_version": forecast.get("forecast_version"),
            "scope": "presentation" if forecast.get("presentation_id") else "decision",
            "decision_ref": forecast.get("decision_ref"),
            "forecast": forecast.get("forecast") or {},
            "p": None,
            "created_at": forecast.get("created_at"),
        }
        rows.append((receipt, resolution))
    return rows


# -- scoring --------------------------------------------------------------------------------------


def _round(value: float | None, digits: int = 4) -> float | None:
    return None if value is None or (isinstance(value, float) and math.isnan(value)) else round(float(value), digits)


#: The binary event each kind's ``p`` forecasts, as an emission.
_BINARY_EVENT = {FR.DIAGNOSIS_NEXT_OBSERVATION: "pass", FR.REPAIR_COLD_OUTCOME: "cold_success"}


def _score(kind: str, rows: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]]) -> dict[str, Any]:
    states = Counter(resolution["state"] for _, resolution in rows)
    reasons: dict[str, Counter] = {state: Counter() for state in (PENDING, HELD, CENSORED)}
    resolved = [(receipt, resolution) for receipt, resolution in rows if resolution["state"] == RESOLVED]
    for _, resolution in rows:
        if resolution["state"] in reasons:
            reasons[resolution["state"]][resolution["reason"]] += 1
    outcome_attempts = {resolution.get("attempt_id") for _, resolution in resolved if resolution.get("attempt_id")}
    decisions = {receipt.get("decision_ref") for receipt, _ in rows if receipt.get("decision_ref")}
    n = {
        "receipts": len(rows),
        "decisions": len(decisions),
        "resolved": len(resolved),
        # The honest n: forecasts resolved on one attempt are one observation.
        "distinct_outcome_attempts": len(outcome_attempts),
        "pending": dict(sorted(reasons[PENDING].items())),
        "held_for_review": dict(sorted(reasons[HELD].items())),
        "censored": dict(sorted(reasons[CENSORED].items())),
    }
    pairs: list[tuple[float, float]] = []
    log_losses: list[float] = []
    multi_brier: list[float] = []
    for receipt, resolution in resolved:
        predicted = (receipt.get("forecast") or {}).get("predicted_outcomes") or {}
        emission = resolution.get("emission")
        if not predicted or emission is None:
            continue
        for e, p in predicted.items():
            pairs.append((float(p), 1.0 if e == emission else 0.0))
        log_losses.append(-math.log(max(float(predicted.get(emission, 0.0)), 1e-12)))
        multi_brier.append(sum((float(p) - (1.0 if e == emission else 0.0)) ** 2 for e, p in predicted.items()))
    categorical = reliability(pairs)
    categorical["log_loss"] = _round(sum(log_losses) / len(log_losses)) if log_losses else None
    categorical["multiclass_brier"] = _round(sum(multi_brier) / len(multi_brier)) if multi_brier else None
    categorical["scored"] = len(log_losses)
    block: dict[str, Any] = {"n": n, "categorical": categorical}
    event = _BINARY_EVENT.get(kind)
    if event is not None:
        binary_pairs = [
            (float(receipt["p"]), 1.0 if resolution.get("emission") == event else 0.0)
            for receipt, resolution in resolved
            if receipt.get("p") is not None and resolution.get("emission") is not None
        ]
        binary = reliability(binary_pairs)
        binary["event"] = event
        if binary_pairs:
            losses = [-math.log(max(p if o else 1.0 - p, 1e-12)) for p, o in binary_pairs]
            base = sum(o for _, o in binary_pairs) / len(binary_pairs)
            binary["log_loss"] = _round(sum(losses) / len(losses))
            binary["mean_predicted"] = _round(sum(p for p, _ in binary_pairs) / len(binary_pairs))
            binary["observed_rate"] = _round(base)
            # In-sample: the Brier of always forecasting the realized rate.
            binary["base_rate_brier"] = _round(sum((base - o) ** 2 for _, o in binary_pairs) / len(binary_pairs))
        block["binary"] = binary
    block["small_n"] = len(resolved) < SMALL_N
    return block


def _splits(rows: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]], key: Callable[[Mapping[str, Any]], Any],
            event: str) -> dict[str, Any]:
    out: dict[str, dict[str, Any]] = {}
    for receipt, resolution in rows:
        label = str(key(receipt))
        block = out.setdefault(label, {"receipts": 0, "resolved": 0, "_p": [], "_o": []})
        block["receipts"] += 1
        if resolution["state"] == RESOLVED and receipt.get("p") is not None:
            block["resolved"] += 1
            block["_p"].append(float(receipt["p"]))
            block["_o"].append(1.0 if resolution.get("emission") == event else 0.0)
    for block in out.values():
        p, o = block.pop("_p"), block.pop("_o")
        block["mean_predicted"] = _round(sum(p) / len(p)) if p else None
        block["observed_rate"] = _round(sum(o) / len(o)) if o else None
    return dict(sorted(out.items()))


def summarize(rows: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]]) -> dict[str, Any]:
    """Per kind, per forecaster: the honest n and the reliability tables."""

    by_kind: dict[str, dict[str, list[tuple[Mapping[str, Any], Mapping[str, Any]]]]] = {}
    for receipt, resolution in rows:
        by_kind.setdefault(str(receipt["kind"]), {}).setdefault(str(receipt.get("forecaster")), []).append(
            (receipt, resolution)
        )
    kinds: dict[str, Any] = {}
    for kind in sorted(by_kind):
        forecasters: dict[str, Any] = {}
        for forecaster, group in sorted(by_kind[kind].items()):
            block = _score(kind, group)
            versions = Counter(str(receipt.get("forecaster_version")) for receipt, _ in group)
            block["forecaster_versions"] = dict(sorted(versions.items()))
            if kind == FR.DIAGNOSIS_NEXT_OBSERVATION:
                body = lambda receipt: receipt.get("forecast") or {}  # noqa: E731
                block["by_causal_class"] = _splits(group, lambda r: body(r).get("causal_class"), "pass")
                block["by_mode"] = _splits(group, lambda r: (r.get("versions") or {}).get("mode"), "pass")
            forecasters[forecaster] = block
        kinds[kind] = {"forecasters": forecasters, "receipts": sum(len(g) for g in by_kind[kind].values())}
    return kinds


def _resolve_all(
    connection: sqlite3.Connection, vault: LoadedVault, *, since: str | None, include_checks: bool
) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]], _Ledgers]:
    ledgers = _Ledgers(connection, vault)
    rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for receipt in receipt_store.list_receipts(connection, since=since):
        if receipt["kind"] == FR.DIAGNOSIS_NEXT_OBSERVATION:
            resolution = resolve_diagnosis(ledgers, receipt)
        elif receipt["kind"] == FR.REPAIR_COLD_OUTCOME:
            resolution = resolve_repair(ledgers, receipt)
        else:
            resolution = _resolution(CENSORED, "kind_without_resolver")
        rows.append((receipt, resolution))
    if include_checks:
        rows.extend(check_outcome_rows(connection, vault, since=since))
    return rows, ledgers


def resolved_receipts(
    vault: LoadedVault, *, since: str | None = None, include_checks: bool = False
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Every receipt with its read-time resolution (read-only, one snapshot)."""

    path = VaultPaths(vault.root, vault.config).sqlite_path
    with closing(connect(path, read_only=True)) as connection:
        connection.execute("BEGIN")
        rows, _ledgers = _resolve_all(connection, vault, since=since, include_checks=include_checks)
    return rows


def forecast_calibration_report(
    vault: LoadedVault, *, since: str | None = None, include_checks: bool = True
) -> dict[str, Any]:
    """The report (read-only, one snapshot). ``since``: receipts at or after it."""

    path = VaultPaths(vault.root, vault.config).sqlite_path
    with closing(connect(path, read_only=True)) as connection:
        connection.execute("BEGIN")
        has_receipts = receipt_store.has_table(connection)
        rows, _ledgers = _resolve_all(connection, vault, since=since, include_checks=include_checks)
    config = getattr(vault.config, "diagnosis", None)
    report = {
        "status": "ok",
        "report_version": REPORT_VERSION,
        "receipt_shape_version": FR.RECEIPT_SHAPE_VERSION,
        "since": since,
        "forecast_receipts": bool(getattr(config, "forecast_receipts", True)),
        "receipts_table": has_receipts,
        "receipts": len(rows),
        "kinds": summarize(rows),
        "notes": [
            "Each forecast resolves only through its exact binding: a diagnosis forecast on the first unseen "
            "qualifying attempt on its facet that answered a plan or probe presentation or a scheduler offer "
            "(else censored unbound_attempt), a repair forecast on its cold task's consumed attempt and "
            "verification, a check forecast through EVSI calibration's adapters. Never the next attempt on "
            "the item by guess.",
            "Resolutions read the current grade (a regrade re-resolves); a grade held for review resolves "
            "nothing until it is released. Pending and censored forecasts are counted, never scored.",
            "Single-learner sample sizes: read every rate with its n. distinct_outcome_attempts is the honest "
            "n (several forecasts resolved on one attempt are one observation); small_n marks fewer than "
            f"{SMALL_N} resolved forecasts.",
            "The diagnosis forecaster scores the diagnoser's causal class and its own confidence through the "
            "facet response model; nothing decides on it.",
        ],
    }
    return report


__all__ = [
    "REPORT_VERSION",
    "SMALL_N",
    "check_outcome_rows",
    "forecast_calibration_report",
    "next_observation",
    "resolved_receipts",
    "resolve_diagnosis",
    "resolve_repair",
    "summarize",
]
