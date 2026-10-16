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
  offer whose record verifies (it exists, is of the answered item and was
  administered to that attempt: Codex review F4), else the forecast is
  censored ``unbound_attempt`` (a reference that establishes nothing is
  listed as rejected): the next observation is never replaced by a later
  one. The facet must first be assessed under the assessment contract the
  current grade cites (the latest row of every criterion citing one and the
  same version, as EVSI calibration review F5 reads a grade; anything else is
  ``graded_contract_unknown``, never today's content: F2); unassessed or
  unmapped, the forecast is censored. Then its emission: ``same_error`` when
  an error event attributed to the facet (the facets it names, else those of
  the criteria it names, else the contract's only facet; never one the grader
  scoped off the learner) shows the pattern (error type or registry
  misconception: F1), else ``pass`` when the facet's outcome (EVSI
  calibration's target-facet weighting, bucketed as the facet updater buckets
  it) is ``high``, else ``other_error``.
* ``repair_cold_outcome`` (``forecast_receipts``): the task's consumed attempt
  and the cold verification's terminal disposition for it
  (``causal_cold_outcomes``). A measured disposition resolves on the cold
  attempt's grade as it stands now (``diagnosis.forecast_receipts.
  effective_cold_outcome``: held and unassessed grades are no outcome; the
  correctness against the threshold frozen in the receipt), the rule the
  repair forecaster's own measured sample reads; any other disposition
  (contaminated, same surface, expired, missing chain) censors it with that
  reason.
* ``check_outcome`` (``voi_forecasts``, EVSI calibration Part B): the same
  family read through an adapter (forecaster = the decision site), joined by
  :mod:`.live_report`'s exact adapters and scored in each site's alphabet.

Every resolution reads the attempt's current grade, so a regrade re-resolves
(a diagnosis forecast only when the regrade cites the contract it was read
under: a method-explicit item's does, any other is ``graded_contract_unknown``);
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
from learnloop.db.stores.plan_presentations import bindable_presentation
from learnloop.diagnosis.forecast_receipts import (
    MEASURED_COLD_DISPOSITIONS,
    NON_LEARNER_VALIDITY,
    effective_cold_outcome,
)
from learnloop.evsi_calibration import live_report as LR
from learnloop.evsi_calibration.metrics import reliability
from learnloop.held_grades import held_for_review_attempts
from learnloop.learner.capability_mapping import ROLE_WEIGHTS
from learnloop.learner.facet_diagnostics import facet_outcome_bucket
from learnloop.outcome_contract import GRADE_HELD_FOR_REVIEW, unassessed_evidence_row
from learnloop.scheduling import forecast_receipts as FR
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

#: v1: the three kinds, exact bindings, held grades unresolved, the honest n.
#: v2 (Codex review 2026-10-15): bindings verified, the graded contract or
#: censored (never today's content), the pattern only on the facet once it is
#: assessed, the repair outcome through the shared effective-outcome rule.
REPORT_VERSION = "forecast_calibration_report_v2"

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
        self._contracts: dict[str, Mapping[str, Any] | None] = {}

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
                    "plan_presentation_id, probe_presentation_id, scheduler_candidate_id, scheduler_slate_id, "
                    "session_id, correctness, created_at FROM practice_attempts ORDER BY created_at, id"
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

    def _contract(self, contract_id: str | None) -> Mapping[str, Any] | None:
        """The assessment contract the current grade cites (Codex review F2).

        Only a version the grade's rows cite is read. A grade that cites none
        (or several) was read under content that is not on record: a regrade
        of an item without a frozen method reads the item as it was then and
        cites nothing. Compiling today's item instead would let an edit of
        its rubric rewrite a resolved forecast, so it is ``None``
        (``graded_contract_unknown``)."""

        if contract_id is None:
            return None
        if contract_id not in self._contracts:
            stored = self.connection.execute(
                "SELECT contract_json FROM assessment_contract_versions WHERE id = ?", (contract_id,)
            ).fetchone()
            contract = _loads(stored["contract_json"], None) if stored is not None else None
            self._contracts[contract_id] = contract if isinstance(contract, Mapping) else None
        return self._contracts[contract_id]

    def facet_outcome(self, attempt_id: str, facet_id: str) -> tuple[float | None, str, Mapping[str, Any] | None]:
        """One attempt's outcome on ``facet_id`` under the contract its current
        grade cites: ``(outcome, "realized", contract)``, or ``(None, why
        not, contract or None)``.

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
        contract = self._contract(contract_id)
        if contract is None:
            return None, "graded_contract_unknown", None
        target = self.canonical(facet_id)
        dont_know = attempt["attempt_type"] == "dont_know" or bool(attempt["declared_dont_know"])
        numerator = denominator = 0.0
        mapped_any = False
        for criterion in contract.get("criteria") or []:
            weights = self._criterion_weights(criterion)
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
            return None, "facet_not_in_contract", contract
        if denominator <= 0:
            return None, "facet_unassessed", contract
        return numerator / denominator, "realized", contract

    def _criterion_weights(self, criterion: Mapping[str, Any]) -> dict[str, float]:
        """A contract criterion's facets (canonical now), role-weighted."""

        weights: dict[str, float] = {}
        for observed in criterion.get("targets") or []:
            role_weight = float(ROLE_WEIGHTS.get(observed.get("role"), 1.0))
            if observed.get("facet") and role_weight > 0:
                facet = self.canonical(str(observed["facet"]))
                weights[facet] = weights.get(facet, 0.0) + role_weight
        return weights

    def current_evidence(self, attempt_id: str) -> tuple[dict[str, sqlite3.Row], str | None]:
        """The attempt's current grade per criterion and the contract it cites.

        The rows are read as replay reads them (``replay_existing_attempt``):
        the surviving rows in (created_at, criterion) order, the last row of
        a criterion winning (a regrade's rows supersede the grade they
        replace). The contract is the one version the winning rows ALL cite
        (EVSI calibration review F5's rule), else None: a regrade whose rows
        cite none, or rows citing different versions, establish no contract
        (Codex review F2)."""

        latest: dict[str, sqlite3.Row] = {}
        for row in self.connection.execute(
            "SELECT criterion_id, points_awarded, attribution_json, assessment_contract_version_id "
            "FROM grading_evidence WHERE attempt_id = ? AND superseded_at IS NULL "
            "ORDER BY created_at, criterion_id, id",
            (attempt_id,),
        ):
            latest[str(row["criterion_id"])] = row
        versions = {row["assessment_contract_version_id"] or None for row in latest.values()}
        contract_id = str(next(iter(versions))) if len(versions) == 1 and None not in versions else None
        return latest, contract_id

    def graded(self, attempt_id: str) -> bool:
        return bool(self.current_evidence(attempt_id)[0])

    def _attributed_facets(self, plan: Mapping[str, Any], contract: Mapping[str, Any]) -> set[str] | None:
        """The facets an error event's recorded attribution names (canonical
        now), as the grading's own facet attribution reads it: the facets it
        names (``target_evidence_families``, a ``facet_capability`` target),
        else the facets of the contract criteria it names
        (``target_criterion_ids``, a ``criterion`` target); ``None`` when it
        names nothing. An attribution the grader scoped off the learner (the
        item contract, its interpretation, the interaction) or whose facet
        write it blocked names none (an empty set)."""

        if plan.get("facet_write_blocked") or str(plan.get("cause_scope") or "") in NON_LEARNER_VALIDITY:
            return set()
        ref = plan.get("target_ref") if isinstance(plan.get("target_ref"), Mapping) else {}
        facets = {self.canonical(str(f)) for f in plan.get("target_evidence_families") or [] if f}
        if ref.get("kind") == "facet_capability" and ref.get("facet_id"):
            facets.add(self.canonical(str(ref["facet_id"])))
        if facets:
            return facets
        criteria = {str(c) for c in plan.get("target_criterion_ids") or [] if c}
        if ref.get("kind") == "criterion" and ref.get("criterion_id"):
            criteria.add(str(ref["criterion_id"]))
        if not criteria:
            return None
        named: set[str] = set()
        for criterion in contract.get("criteria") or []:
            if str(criterion.get("id")) in criteria:
                named.update(self._criterion_weights(criterion))
        return named

    def facet_shows_pattern(
        self, attempt_id: str, pattern: Mapping[str, Any], facet_id: str, contract: Mapping[str, Any]
    ) -> bool:
        """Does an error event on the attempt attributed to ``facet_id`` show
        the pattern (Codex review F1)? An error confined to another facet is
        that facet's, never this one's recurrence. An error that names no
        target is attributed to the facet only when the contract measures no
        other facet."""

        if not _has(self.connection, "error_events"):
            return False
        error_type = pattern.get("error_type")
        misconception = pattern.get("misconception_id")
        target = self.canonical(facet_id)
        measured: set[str] | None = None
        for row in self.connection.execute(
            "SELECT error_type, misconception_id, repair_plan_json FROM error_events WHERE attempt_id = ? "
            "ORDER BY created_at, id",
            (attempt_id,),
        ):
            if not ((error_type and row[0] == error_type) or (misconception and row[1] == misconception)):
                continue
            plan = _loads(row[2], {}) or {}
            facets = self._attributed_facets(plan if isinstance(plan, Mapping) else {}, contract)
            if facets is None:
                if measured is None:
                    measured = set()
                    for criterion in contract.get("criteria") or []:
                        measured.update(self._criterion_weights(criterion))
                facets = measured if measured == {target} else set()
            if target in facets:
                return True
        return False


# -- exact bindings -------------------------------------------------------------------------------


def _plan_binding(ledgers: _Ledgers, attempt: Mapping[str, Any]) -> str | None:
    """Why the attempt's plan presentation does not bind it (None: it does):
    router R2a's own write-time rule, read again (it exists, is of the item,
    no other attempt answered it)."""

    bound, why = bindable_presentation(
        ledgers.connection, str(attempt["plan_presentation_id"]),
        practice_item_id=str(attempt.get("practice_item_id") or ""), attempt_id=str(attempt["id"]),
    )
    return None if bound is not None else (why or "unknown_presentation")


def _probe_binding(ledgers: _Ledgers, attempt: Mapping[str, Any]) -> str | None:
    """Why the attempt's probe presentation does not bind it: it must exist,
    be of the item, and this attempt be the one that answered it."""

    connection = ledgers.connection
    if not _has(connection, "probe_presentations"):
        return "no_presentation_ledger"
    presentation_id = str(attempt["probe_presentation_id"])
    row = connection.execute(
        "SELECT practice_item_id FROM probe_presentations WHERE id = ?", (presentation_id,)
    ).fetchone()
    if row is None:
        return "unknown_presentation"
    if str(row[0]) != str(attempt.get("practice_item_id")):
        return "presentation_of_another_item"
    first = connection.execute(
        "SELECT id FROM practice_attempts WHERE probe_presentation_id = ? ORDER BY created_at, id LIMIT 1",
        (presentation_id,),
    ).fetchone()
    if first is None or str(first[0]) != str(attempt["id"]):
        return "presentation_answered_by_another_attempt"
    return None


def _scheduler_binding(ledgers: _Ledgers, attempt: Mapping[str, Any]) -> str | None:
    """Why the attempt's scheduler offer does not bind it: the exact offer
    link the attempt store writes (``_link_attempt_to_scheduler_candidate``)
    and the data-quality report checks: a returned candidate of the item, in
    the attempt's slate and session, generated no later than the answer, and
    chosen by this attempt."""

    connection = ledgers.connection
    if not _has(connection, "scheduler_slate_candidates") or not _has(connection, "scheduler_slates"):
        return "no_offer_ledger"
    row = connection.execute(
        "SELECT c.practice_item_id, c.slate_id, c.was_returned, c.chosen_attempt_id, s.session_id, s.generated_at "
        "FROM scheduler_slate_candidates c LEFT JOIN scheduler_slates s ON s.id = c.slate_id WHERE c.id = ?",
        (str(attempt["scheduler_candidate_id"]),),
    ).fetchone()
    if row is None:
        return "unknown_candidate"
    if str(row["practice_item_id"]) != str(attempt.get("practice_item_id")):
        return "candidate_of_another_item"
    if not row["was_returned"]:
        return "candidate_not_offered"
    if str(row["chosen_attempt_id"] or "") != str(attempt["id"]):
        return "candidate_chosen_by_another_attempt"
    session = str(attempt.get("session_id") or "")
    if str(row["slate_id"]) != str(attempt.get("scheduler_slate_id") or "") or not session or (
        str(row["session_id"] or "") != session
    ):
        return "candidate_of_another_slate_or_session"
    if not row["generated_at"] or str(row["generated_at"]) > str(attempt.get("created_at") or ""):
        return "offered_after_answer"
    return None


_BINDINGS = (
    ("plan_presentation_id", "plan_presentation", _plan_binding),
    ("probe_presentation_id", "probe_presentation", _probe_binding),
    ("scheduler_candidate_id", "scheduler_candidate", _scheduler_binding),
)


def _binding(ledgers: _Ledgers, attempt: Mapping[str, Any]) -> tuple[str | None, dict[str, str]]:
    """The exact receipt the attempt answered (Codex review F4): the first of
    its references whose record verifies, ``(label, {})``; else ``(None,
    {label: why})`` for every reference it carries that establishes nothing.
    A nonempty column is a claim, not a binding (none of them is checked by a
    foreign key but the plan presentation's)."""

    rejected: dict[str, str] = {}
    for column, label, check in _BINDINGS:
        if not attempt.get(column):
            continue
        why = check(ledgers, attempt)
        if why is None:
            return label, {}
        rejected[label] = why
    return None, rejected


# -- the diagnosis forecast -----------------------------------------------------------------------


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
    binding, rejected = _binding(ledgers, attempt)
    if binding is None:
        if rejected:
            common["rejected_bindings"] = rejected
        return _resolution(CENSORED, "unbound_attempt", **common)
    common["binding"] = binding
    if ledgers.held(attempt_id):
        return _resolution(HELD, GRADE_HELD_FOR_REVIEW, **common)
    if not ledgers.graded(attempt_id):
        return _resolution(PENDING, "ungraded", **common)
    # The facet must be assessed under the graded contract before anything
    # resolves, a recurrence included (Codex review F1).
    outcome, why, contract = ledgers.facet_outcome(attempt_id, found["facet"])
    if outcome is None or contract is None:
        if why == "ungraded":
            return _resolution(PENDING, why, **common)
        return _resolution(CENSORED, why, **common)
    body = receipt.get("forecast") or {}
    if ledgers.facet_shows_pattern(attempt_id, body.get("pattern") or {}, found["facet"], contract):
        return _resolution(RESOLVED, "realized", emission="same_error", facet_outcome=round(outcome, 4), **common)
    emission = "pass" if facet_outcome_bucket(outcome) == "high" else "other_error"
    return _resolution(RESOLVED, "realized", emission=emission, facet_outcome=round(outcome, 4), **common)


# -- the repair forecast --------------------------------------------------------------------------

_MEASURED = MEASURED_COLD_DISPOSITIONS


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
    # The rule the repair forecaster's measured sample reads (Codex review F3).
    threshold = float(((receipt.get("forecast") or {}).get("target") or {}).get("success_threshold", 0.8))
    emission, why = effective_cold_outcome(connection, cold_attempt_id, threshold=threshold)
    if emission is None:
        if why == GRADE_HELD_FOR_REVIEW:
            return _resolution(HELD, why, **common)
        return _resolution(PENDING if why == "ungraded" else CENSORED, why, **common)
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
            "whose record verifies (else censored unbound_attempt, with any reference that established nothing "
            "listed as rejected), a repair forecast on its cold task's consumed attempt and verification, a "
            "check forecast through EVSI calibration's adapters. Never the next attempt on the item by guess.",
            "Resolutions read the current grade (a regrade re-resolves); a grade held for review resolves "
            "nothing until it is released. A diagnosis forecast reads its facet under the contract the grade "
            "cites, never today's content (graded_contract_unknown otherwise), and counts a recurrence only "
            "through an error attributed to that facet once it is assessed. Pending and censored forecasts are "
            "counted, never scored.",
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
