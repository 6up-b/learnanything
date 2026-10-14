"""`learnloop evsi calibration`: how good were the live VOI forecasts?

Reads ``voi_forecasts`` (EVSI calibration Part B) and joins, at read time:

1. **The realized outcome** of each forecast, through an outcome adapter:
   R1's ``router_decisions``/``router_outcomes`` (migration 181; the
   decision's chosen scheduler candidate -> the attempt that took it, joined
   only when R1 says ``taken``: its other statuses judge the offer, and the
   cache lags until ``learnloop rebuild``), else
   the probe and attempt ledgers (``practice_attempts.probe_presentation_id``
   -> ``probe_observations``; a queued follow-up -> the first attempt on the
   item after its queue, taken only when it answered the offer that queue
   produced, with ``superseded`` / ``answered_earlier_offer`` / ``not_taken`` /
   ``unbound_attempt`` / ``pending`` kept apart; else the first later attempt
   on the chosen item).
   The value-of-information successor's four sites (mvp-0.21) bind only by
   exact receipts (:data:`VALUE_DECISION_SITES`): a probe continue by its
   committed presentation; a follow-up by its own ``followup_value_decisions``
   receipt and the queue and offer it produced; a teach-back by the offer's
   scheduler candidate the answer was bound to; a project probe by router R1's
   ``plan_block`` row (``decision_ref``) -> its block -> the item served from
   that block -> the attempt bound to that serving's candidate. A decision
   nothing was administered for (a stop) is ``not_administered``, and one with
   no exact binding stays right-censored with its reason, never joined by a
   session rule or "the next attempt on the item".
   The realized emission is mapped into the forecast's own alphabet; one that
   cannot be mapped is counted as ``unmapped``, never guessed.
2. **Later truth**, through truth adapters that need explicit hypothesis
   linkage and independent diagnostic evidence (:func:`truth_for`): a cold
   verification's diagnosis-support update whose cited observation resolves to
   an admitted, independent match on one of its hypotheses, an admitted
   ``matched_single`` discriminating observation (not of the forecast's own
   answer), and a later teach-back whose diagnosis names the same cause. What
   a repair did (a cold check's success or failure, a factor closed as
   ``repair_confirmed`` / ``escalated_unrepaired``) is reported apart, as
   repair effect, one outcome per cold verification: it neither confirms nor
   rules out a cause. The system's own posterior moving a misconception to
   "resolved" is never truth.

Reports: (a) reliability of outcome forecasts (log loss, Brier, ECE, bins);
(b) realized vs predicted information gain; (c) action-change calibration;
(d) regret on forecasts whose truth became known. Read-only.
"""

from __future__ import annotations

import json
import math
import sqlite3
from contextlib import closing
from typing import Any, Mapping, Sequence

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import voi_forecasts as store
from learnloop.diagnosis.causal_attribution import SUPPORT_BASIS_AUTHORITY
from learnloop.diagnosis.probes import score_bucket
from learnloop.diagnosis.voi_forecasting import facet_contract_criteria_hash
from learnloop.evsi_calibration.metrics import reliability
from learnloop.learner.facet_diagnostics import facet_outcome_bucket
from learnloop.scheduling.unresolved_cost import estimate_unresolved_cost
from learnloop.scheduling.voi_forecasts import FORECAST_VERSION, entropy, posterior
from learnloop.outcome_contract import GRADE_HELD_FOR_REVIEW
from learnloop.substrate.canonical_projection import held_for_review_attempts, unassessed_evidence_row
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

#: v2 (Codex review F1/F5/F6/F3): linked independent truth with repair effect
#: apart, target-facet follow-up outcomes, bound follow-up and staged joins.
#: v3 (re-review F1/F6/F9/F10): cited diagnosis support resolved to its
#: observation; a follow-up taken only through the offer its own queue
#: produced; the facet map part of the frozen contract; one repair outcome per
#: cold verification.
#: v4 (merge onto main, R1's live tables): the router adapter joins only an
#: offer R1 says was ``taken``; a superseded, open or stale offer defers to
#: the ledgers instead of hiding the presentation's own answer.
#: v5 (merge of value-of-information stopping, mvp-0.21): the successor's four
#: value-decision sites are joined by exact receipts and scored in their own
#: alphabets.
#: v6 (router R2a, plan_router_r2_v1 §5.3): a committed live staged forecast
#: joins through the exact receipt (the plan_block decision naming its
#: controller decision -> that block's presentation of the chosen item -> the
#: attempt bound to it), right-censored as not_presented /
#: presented_unanswered, never by a session rule; a planned project probe
#: prefers its presentation's bound attempt to its serving's offer.
REPORT_VERSION = "voi_calibration_report_v6"


def _has(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone() is not None


def _loads(value: Any, default: Any) -> Any:
    if value is None:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


#: The value-of-information successor's ``voi_forecasts`` sites
#: (``diagnosis.voi_forecasting.VALUE_DECISION_SITES``).
PROBE_VALUE_SITE = "probe_episode_value_decision"
FOLLOWUP_VALUE_SITE = "followup_value_decision"
TEACH_BACK_VALUE_SITE = "teach_back_value_decision"
PROJECT_PROBE_VALUE_SITE = "project_probe_value_decision"
VALUE_DECISION_SITES = (PROBE_VALUE_SITE, FOLLOWUP_VALUE_SITE, TEACH_BACK_VALUE_SITE, PROJECT_PROBE_VALUE_SITE)

#: A teach-back's and a project probe's forecast is the selection reward's
#: predicted correctness as ``{correct, incorrect}``; an answer is ``correct``
#: when its correctness (rubric score / max points) reaches this, the
#: Bernoulli mean's decision boundary.
BINARY_CORRECTNESS_CUT = 0.5


def _administered(forecast: Mapping[str, Any]) -> bool:
    """A value decision whose described check was administered or admitted
    (``forecast_of`` committed, or a per-check receipt that kept its check)."""

    body = forecast.get("forecast") or {}
    of = body.get("forecast_of")
    return of == "committed" or (of == "subject" and body.get("decision") == "continue")


# -- outcome adapters ---------------------------------------------------------------------------


class RouterOutcomeAdapter:
    """R1: the attempt that took a logged router decision (when R1 is present)."""

    name = "router_outcomes"

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.available = _has(connection, "router_decisions") and _has(connection, "router_outcomes")

    def attempt_for(self, forecast: Mapping[str, Any]) -> tuple[str | None, str] | None:
        """The attempt R1 bound to the forecast's offer, or ``None`` to defer.

        Only R1's ``taken`` is an outcome of the forecast. Its other statuses
        judge the offer, not the check the forecast is about: a queue refresh
        supersedes an offer whose committed probe presentation stays in front
        under a new scheduler candidate, and ``router_outcomes`` is a DERIVED
        cache rebuilt only by ``learnloop rebuild``, so ``open`` can be stale.
        Those defer to the ledgers, which bind the presentation itself.
        """

        if not self.available or not forecast.get("scheduler_candidate_id"):
            return None
        if forecast.get("site") in VALUE_DECISION_SITES and not _administered(forecast):
            return None  # a stop administered nothing: the ledger adapter says so
        row = self.connection.execute(
            "SELECT o.action_attempt_id FROM router_decisions d "
            "JOIN router_outcomes o ON o.decision_id = d.id "
            "WHERE d.chosen_scheduler_candidate_id = ? AND o.action_status = 'taken' "
            "AND o.action_attempt_id IS NOT NULL ORDER BY d.created_at, d.id LIMIT 1",
            (forecast["scheduler_candidate_id"],),
        ).fetchone()
        if row is None:
            return None
        return str(row["action_attempt_id"]), "taken"


def _queues_item(action: Any, item: str) -> bool:
    """Whether an ``attempt_surprise`` action queued a follow-up of ``item``.

    The two queued shapes ``repositories._queued_followup_action`` reads.
    """

    return action in (f"intervention_followup:queued:{item}", f"negative_surprise_followup:{item}")


class LedgerOutcomeAdapter:
    """The probe and attempt ledgers (always available)."""

    name = "ledgers"

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def attempt_for(self, forecast: Mapping[str, Any]) -> tuple[str | None, str] | None:
        if forecast.get("site") in VALUE_DECISION_SITES:
            return self._value_decision_attempt(forecast)
        if forecast.get("presentation_id"):
            row = self.connection.execute(
                "SELECT id FROM practice_attempts WHERE probe_presentation_id = ?",
                (forecast["presentation_id"],),
            ).fetchone()
            return (str(row["id"]), "taken") if row is not None else (None, "pending")
        if forecast.get("site") == "followup_selection":
            return self._followup_attempt(forecast)
        if forecast.get("site") == "staged_diagnostic_selection":
            return self._staged_attempt(forecast)
        item = forecast.get("chosen_practice_item_id")
        if not item:
            return None, "no_chosen_item"
        if forecast.get("site") == "probe_robust_selection" and forecast.get("probe_episode_id"):
            row = self.connection.execute(
                "SELECT a.id FROM probe_presentations p JOIN practice_attempts a "
                "ON a.probe_presentation_id = p.id WHERE p.probe_episode_id = ? AND p.practice_item_id = ? "
                "AND a.created_at >= ? ORDER BY a.created_at, a.id LIMIT 1",
                (forecast["probe_episode_id"], item, forecast["created_at"]),
            ).fetchone()
        else:
            row = self.connection.execute(
                "SELECT id FROM practice_attempts WHERE practice_item_id = ? AND created_at >= ? "
                "ORDER BY created_at, id LIMIT 1",
                (item, forecast["created_at"]),
            ).fetchone()
        return (str(row["id"]), "taken") if row is not None else (None, "pending")

    def _requeued_after(self, item: str, gate: str, queued_at: str) -> bool:
        """A newer decision queued the same item (``pending_followup_practice_items``
        keeps the newest queue per item, so the older decision is superseded)."""

        for row in self.connection.execute(
            "SELECT triggered_actions_json FROM attempt_surprise WHERE triggered_actions_json IS NOT NULL "
            "AND attempt_id != ? AND (created_at > ? OR (created_at = ? AND attempt_id > ?))",
            (gate, queued_at, queued_at, gate),
        ):
            if any(_queues_item(action, item) for action in _loads(row["triggered_actions_json"], [])):
                return True
        return False

    def _value_decision_attempt(self, forecast: Mapping[str, Any]) -> tuple[str | None, str]:
        """The attempt a value-of-information decision's check was answered by,
        through that site's own receipts only (module docstring)."""

        if not _administered(forecast):
            return None, "not_administered"
        site = forecast.get("site")
        if site == PROBE_VALUE_SITE:
            if not forecast.get("presentation_id"):
                return None, "no_attempt_binding"
            row = self.connection.execute(
                "SELECT id FROM practice_attempts WHERE probe_presentation_id = ?",
                (forecast["presentation_id"],),
            ).fetchone()
            return (str(row["id"]), "taken") if row is not None else (None, "pending")
        if site == FOLLOWUP_VALUE_SITE:
            return self._followup_value_attempt(forecast)
        if site == TEACH_BACK_VALUE_SITE:
            return self._candidate_attempt(forecast.get("scheduler_candidate_id"), forecast.get("chosen_practice_item_id"))
        return self._plan_probe_attempt(forecast)

    def _candidate_attempt(self, candidate_id: Any, item: Any) -> tuple[str | None, str]:
        """The attempt bound to one scheduler candidate (the offer it answered)."""

        if not candidate_id or not item:
            return None, "no_attempt_binding"
        row = self.connection.execute(
            "SELECT id FROM practice_attempts WHERE scheduler_candidate_id = ? AND practice_item_id = ? "
            "ORDER BY created_at, id LIMIT 1",
            (str(candidate_id), str(item)),
        ).fetchone()
        return (str(row["id"]), "taken") if row is not None else (None, "pending")

    def _followup_value_attempt(self, forecast: Mapping[str, Any]) -> tuple[str | None, str]:
        """A queued follow-up value decision: its own receipt
        (``followup_value_decisions``, ``decision_ref``) must be the decision
        in force on its source attempt (any later decision there, a queue
        again or a suppression, rewrote the attempt's queue and supersedes
        it), then the queue and the offer it produced bind the answer
        (:meth:`_followup_attempt`)."""

        receipt_id = forecast.get("decision_ref")
        if not receipt_id or not _has(self.connection, "followup_value_decisions"):
            return None, "no_decision_receipt"
        receipt = self.connection.execute(
            "SELECT source_attempt_id, decision_ordinal, served_ref FROM followup_value_decisions WHERE id = ?",
            (str(receipt_id),),
        ).fetchone()
        if receipt is None:
            return None, "no_decision_receipt"
        if not receipt["served_ref"] or str(receipt["served_ref"]) != str(forecast.get("chosen_practice_item_id")):
            return None, "no_decision_receipt"
        later = self.connection.execute(
            "SELECT 1 FROM followup_value_decisions WHERE source_attempt_id = ? AND decision_ordinal > ? LIMIT 1",
            (receipt["source_attempt_id"], receipt["decision_ordinal"]),
        ).fetchone()
        if later is not None:
            return None, "superseded"
        return self._followup_attempt(
            {**dict(forecast), "source_attempt_id": receipt["source_attempt_id"],
             "chosen_practice_item_id": receipt["served_ref"]}
        )

    def _plan_probe_attempt(self, forecast: Mapping[str, Any]) -> tuple[str | None, str]:
        """An admitted project probe: router R1's ``plan_block`` row
        (``decision_ref``, or the block itself when R1 logged nothing) -> the
        block that decision persisted -> the probe planned in it -> its
        serving's scheduler candidate -> the attempt bound to it. A probe the
        decision admitted but planned in no block of its own is
        ``not_planned_in_this_block`` (a later decision's forecast holds it)."""

        ref = forecast.get("decision_ref")
        item = forecast.get("chosen_practice_item_id")
        if not ref or not item or not _has(self.connection, "attention_block_events"):
            return None, "no_attempt_binding"
        block_id = ((forecast.get("forecast") or {}).get("extra") or {}).get("plan_block_id")
        if block_id:
            # The block the forecast was logged with, which R1's row names.
            block = self.connection.execute(
                "SELECT id FROM attention_blocks WHERE id = ? AND (decision_ref = ? OR id = ?)",
                (str(block_id), str(ref), str(ref)),
            ).fetchone()
        else:
            block = self.connection.execute(
                "SELECT id FROM attention_blocks WHERE decision_ref = ? OR id = ? ORDER BY created_at, id LIMIT 1",
                (str(ref), str(ref)),
            ).fetchone()
        if block is None:
            return None, "no_plan_block"
        events = [
            (row["kind"], _loads(row["detail_json"], {}) or {})
            for row in self.connection.execute(
                "SELECT kind, detail_json FROM attention_block_events WHERE block_id = ? ORDER BY event_ordinal",
                (block["id"],),
            )
        ]
        if not any(kind == "item_planned" and detail.get("practice_item_id") == item for kind, detail in events):
            return None, "not_planned_in_this_block"
        served = [
            detail for kind, detail in events if kind == "item_served" and detail.get("practice_item_id") == item
        ]
        if not served:
            return None, "pending"
        bound = self._presentation_attempt([str(block["id"])], str(item))
        if bound is not None and bound[0] is not None:
            # Router R2a: the attempt that answered this serving's presentation.
            return bound
        return self._candidate_attempt(served[0].get("scheduler_candidate_id"), item)

    def _presentation_attempt(self, block_ids: Sequence[str], item: str) -> tuple[str | None, str] | None:
        """The attempt bound to the item's presentation in one of ``block_ids``
        (router R2a's receipt): ``(attempt, "taken")``, ``(None,
        "presented_unanswered")``, or None when the item was never presented
        there (or the database predates the receipt)."""

        if not block_ids or not _has(self.connection, "plan_presentations"):
            return None
        marks = ",".join("?" for _ in block_ids)
        presentations = [
            str(row["id"])
            for row in self.connection.execute(
                f"SELECT id FROM plan_presentations WHERE block_id IN ({marks}) AND practice_item_id = ? "
                "ORDER BY served_at, id",
                (*block_ids, item),
            )
        ]
        if not presentations:
            return None
        marks = ",".join("?" for _ in presentations)
        row = self.connection.execute(
            f"SELECT id FROM practice_attempts WHERE plan_presentation_id IN ({marks}) ORDER BY created_at, id LIMIT 1",
            presentations,
        ).fetchone()
        return (str(row["id"]), "taken") if row is not None else (None, "presented_unanswered")

    def _staged_attempt(self, forecast: Mapping[str, Any]) -> tuple[str | None, str]:
        """The attempt that administered a staged diagnostic decision (review F3).

        Only a ``committed`` forecast was administered at all
        (``not_administered`` otherwise: a stop, an abstention). A shadow-mode
        decision composes no work (``shadow_not_administered``), so no later
        attempt is its outcome. A live decision binds only through the exact
        receipt (router R2a, plan §5.3, owner Q10): the ``plan_block`` router
        decision that names it (``controller_decision_id``) -> that block's
        presentation of the chosen item -> the attempt bound to it
        (``practice_attempts.plan_presentation_id``). Until such a decision
        exists it stays ``no_attempt_binding``; a composed but unserved item is
        ``not_presented``, a served one nobody answered (or answered without
        the receipt) ``presented_unanswered``, both right-censored. Never
        guessed from the next attempt on the item (the error review F6 fixed
        for follow-ups) or from a session. R1's router adapter, which runs
        first, joins any forecast that carries a scheduler candidate.
        """

        body = forecast.get("forecast") or {}
        if body.get("forecast_of") != "committed" or not forecast.get("chosen_ref"):
            return None, "not_administered"
        mode = (body.get("extra") or {}).get("decision_mode")
        if mode is None and forecast.get("decision_ref") and _has(self.connection, "controller_decisions"):
            row = self.connection.execute(
                "SELECT mode FROM controller_decisions WHERE id = ?", (forecast["decision_ref"],)
            ).fetchone()
            mode = row["mode"] if row is not None else None
        if mode != "live":
            return None, "shadow_not_administered"
        ref, item = forecast.get("decision_ref"), forecast.get("chosen_practice_item_id")
        if not ref or not item or not _has(self.connection, "router_decisions"):
            return None, "no_attempt_binding"
        blocks = [
            str(row["receipt_key"]).split(":", 1)[1]
            for row in self.connection.execute(
                "SELECT receipt_key FROM router_decisions WHERE controller_decision_id = ? "
                "AND decision_kind = 'plan_block' ORDER BY created_at, id",
                (str(ref),),
            )
            if str(row["receipt_key"]).startswith("plan_block:")
        ]
        if not blocks:
            return None, "no_attempt_binding"
        bound = self._presentation_attempt(blocks, str(item))
        return bound if bound is not None else (None, "not_presented")

    def _queue_serving_at(self, item: str, at: str) -> tuple[str, str] | None:
        """The queued decision the scheduler would serve for ``item`` at ``at``.

        ``Repository.pending_followup_practice_items`` as of ``at``: the newest
        ``attempt_surprise`` queue of the item written by then (ties broken by
        attempt id, as it orders them), unless an attempt on the item since
        that queue already ended it. Returns ``(gate attempt id, queued at)``.
        """

        for row in self.connection.execute(
            "SELECT attempt_id, triggered_actions_json, created_at FROM attempt_surprise "
            "WHERE triggered_actions_json IS NOT NULL AND created_at <= ? ORDER BY created_at DESC, attempt_id DESC",
            (at,),
        ):
            if not any(_queues_item(action, item) for action in _loads(row["triggered_actions_json"], [])):
                continue
            ended = self.connection.execute(
                "SELECT 1 FROM practice_attempts WHERE practice_item_id = ? AND created_at > ? AND created_at <= ? "
                "LIMIT 1",
                (item, row["created_at"], at),
            ).fetchone()
            return None if ended is not None else (str(row["attempt_id"]), str(row["created_at"]))
        return None

    def _answered_delayed_task(self, attempt_id: str) -> bool:
        """The attempt consumed a delayed follow-up task (cold retry, certification
        probe): those lanes ride the same ``intervention_followup`` component and
        shadow a queued follow-up of the same item, so its offer was theirs."""

        if not _has(self.connection, "followup_tasks"):
            return False
        return self.connection.execute(
            "SELECT 1 FROM followup_tasks WHERE consumed_attempt_id = ? LIMIT 1", (attempt_id,)
        ).fetchone() is not None

    def _followup_attempt(self, forecast: Mapping[str, Any]) -> tuple[str | None, str]:
        """The attempt that took a queued follow-up decision (review F6, re-review F6).

        Any attempt on the item ends every queue before it, so the decision's
        fate is the first attempt on the item after its queue. That attempt took
        THIS decision only when it answered the offer this decision produced:
        its offer (``practice_attempts.scheduler_candidate_id``) is a slate
        candidate inserted as an intervention follow-up, not served by a
        delayed task, and the queue the scheduler was serving for the item when
        that slate was built (:meth:`_queue_serving_at`) is this decision's.
        The lane flag alone says the answer came through a follow-up offer, not
        whose: a decision queued again after the offer did not produce it.

        Otherwise the decision is ``superseded`` (a newer decision's queue
        produced the answered offer, or re-queued the item before any answer),
        ``answered_earlier_offer`` (the item was answered through an offer an
        older decision produced), ``not_taken`` (answered through another
        lane), ``unbound_attempt`` (the answer carries no offer binding, so
        nobody can say which lane it came through), ``no_queue_receipt`` (the
        decision's own queue is not on record) or ``pending``.
        """

        item = forecast.get("chosen_practice_item_id")
        gate = forecast.get("source_attempt_id") or forecast.get("decision_ref")
        if not item or not gate:
            return None, "no_chosen_item"
        item, gate = str(item), str(gate)
        queued = self.connection.execute(
            "SELECT created_at, triggered_actions_json FROM attempt_surprise WHERE attempt_id = ?", (gate,)
        ).fetchone()
        if queued is None or not any(
            _queues_item(action, item) for action in _loads(queued["triggered_actions_json"], [])
        ):
            return None, "no_queue_receipt"
        queued_at = str(queued["created_at"])
        first = self.connection.execute(
            "SELECT id, scheduler_candidate_id FROM practice_attempts WHERE practice_item_id = ? AND created_at > ? "
            "AND id != ? ORDER BY created_at, id LIMIT 1",
            (item, queued_at, gate),
        ).fetchone()
        if first is None:
            return None, "superseded" if self._requeued_after(item, gate, queued_at) else "pending"
        candidate_id = first["scheduler_candidate_id"]
        candidate = (
            self.connection.execute(
                "SELECT components_json, created_at FROM scheduler_slate_candidates WHERE id = ?", (candidate_id,)
            ).fetchone()
            if candidate_id
            else None
        )
        if candidate is None:
            return None, "unbound_attempt"
        components = _loads(candidate["components_json"], {}) or {}
        if float(components.get("intervention_followup") or 0.0) <= 0.0:
            return None, "not_taken"
        if self._answered_delayed_task(str(first["id"])):
            return None, "not_taken"
        producer = self._queue_serving_at(item, str(candidate["created_at"]))
        if producer is None:
            return None, "not_taken"
        if producer[0] == gate:
            return str(first["id"]), "taken"
        newer = (producer[1], producer[0]) > (queued_at, gate)
        return None, "superseded" if newer else "answered_earlier_offer"


def _observation(connection: sqlite3.Connection, attempt_id: str) -> dict[str, Any] | None:
    if not _has(connection, "probe_observations"):
        return None
    row = connection.execute(
        "SELECT grader_channel_json, features_json FROM probe_observations WHERE attempt_id = ?", (attempt_id,)
    ).fetchone()
    if row is None:
        return None
    return {"grader_channel": _loads(row["grader_channel_json"], {}), "features": _loads(row["features_json"], {})}


def _target_facet_emission(
    connection: sqlite3.Connection, body: Mapping[str, Any], attempt_id: str
) -> tuple[str | None, str]:
    """A follow-up answer read as its TARGET facet's outcome (review F5).

    Scored under the contract the forecast froze (``target_facet_contract``):
    the attempt's surviving grading evidence on the criteria whose observation
    targets include the facet, weighted as ``recall_coverage
    .derive_facet_outcomes`` weights them, bucketed as the facet updater
    buckets them. Never the whole-item grade and never today's rubric.

    The answer must have been graded under the frozen scoring contract: same
    item and rubric content, same criteria with the same criterion -> facet
    targets (``criteria_hash``, re-review F9) and, when the attempt recorded
    them, the same evidence facets. An answer graded under another contract, a
    facet no assessed criterion measured, or a forecast without a frozen
    contract (or one frozen without its facet map's identity) stays unmapped
    with its reason.
    """

    alphabet = set(body.get("emission_alphabet") or [])
    contract = body.get("target_facet_contract")
    if not isinstance(contract, Mapping):
        return None, "no_frozen_facet_contract"
    if not contract.get("criteria_hash"):
        return None, "frozen_contract_without_facet_map"
    criteria = contract.get("criteria") or {}
    if not criteria:
        return None, "facet_unmapped"
    attempt = connection.execute(
        "SELECT attempt_type, declared_dont_know, error_type, evidence_facets_json FROM practice_attempts "
        "WHERE id = ?", (attempt_id,)
    ).fetchone()
    if attempt is None:
        return None, "no_attempt"
    recorded_facets = _loads(attempt["evidence_facets_json"], None)
    if isinstance(recorded_facets, list) and recorded_facets and (
        sorted({str(value) for value in recorded_facets}) != sorted(set(contract.get("evidence_facets") or []))
    ):
        return None, "graded_under_another_contract"
    if attempt["attempt_type"] == "dont_know" or attempt["declared_dont_know"]:
        outcome = 0.0  # a don't-know answer is a failure on every facet it covers
    else:
        latest: dict[str, sqlite3.Row] = {}
        for row in connection.execute(
            "SELECT criterion_id, points_awarded, attribution_json, assessment_contract_version_id, "
            "grading_revision FROM grading_evidence WHERE attempt_id = ? AND superseded_at IS NULL",
            (attempt_id,),
        ):
            current = latest.get(str(row["criterion_id"]))
            if current is None or (row["grading_revision"] or -1) >= (current["grading_revision"] or -1):
                latest[str(row["criterion_id"])] = row
        if not latest:
            return None, "ungraded"
        versions = {row["assessment_contract_version_id"] for row in latest.values()}
        if len(versions) != 1 or None in versions:
            return None, "graded_contract_unknown"
        graded = connection.execute(
            "SELECT contract_json FROM assessment_contract_versions WHERE id = ?", (next(iter(versions)),)
        ).fetchone()
        if graded is None:
            return None, "graded_contract_unknown"
        graded_contract = _loads(graded["contract_json"], {}) or {}
        if any(graded_contract.get(key) != contract.get(key) for key in ("item_content_hash", "rubric_content_hash")):
            return None, "graded_under_another_contract"
        # The criterion -> facet targets are part of the contract an answer is
        # scored under (re-review F9): a remapped facet is another contract.
        if facet_contract_criteria_hash(graded_contract.get("criteria") or []) != contract.get("criteria_hash"):
            return None, "graded_under_another_contract"
        max_points = max(float(contract.get("max_points") or 1.0), 1.0)
        numerator = denominator = 0.0
        for criterion_id, spec in criteria.items():
            row = latest.get(str(criterion_id))
            if row is None or unassessed_evidence_row(row["attribution_json"]):
                continue  # not assessed: contributes nothing (never a zero-point failure)
            points = float(spec.get("points") or 0.0)
            weight = points / max_points * float(spec.get("facet_share") or 0.0)
            correctness = min(max(float(row["points_awarded"]) / max(points, 1.0), 0.0), 1.0)
            numerator += weight * correctness
            denominator += weight
        if denominator <= 0:
            return None, "facet_unassessed"
        outcome = numerator / denominator
    bucket = facet_outcome_bucket(outcome)
    # As the facet updater reads it: only a fatal error of the frozen rubric.
    error = str(attempt["error_type"] or "")
    if error not in set(contract.get("fatal_error_ids") or []):
        error = ""
    emission = f"{bucket}|{error}"
    if emission not in alphabet:
        emission = f"{bucket}|"
    return emission, "realized"


def _value_decision_emission(
    connection: sqlite3.Connection,
    vault: LoadedVault,
    forecast: Mapping[str, Any],
    attempt_id: str,
) -> tuple[str | None, str]:
    """A value decision's realized emission, in the alphabet its described
    check was valued in.

    * probe episode: the episode's pinned credible set (``credible_set``
      ``pinned_channel_ensemble``) values the coarse robust emission the
      observation recorded; point conditionals value the graded probe outcome;
    * follow-up: ``probes.hypothesis_conditionals``' outcome, the answer's
      score bucket and its error channel (a discriminating item's fired
      registry misconception, else the error type when the alphabet has it,
      else no error), as the probe-phase posterior reads an answer;
    * teach-back, project probe: ``correct`` when the answer's correctness
      reaches :data:`BINARY_CORRECTNESS_CUT`, else ``incorrect``.
    """

    body = forecast.get("forecast") or {}
    site = forecast.get("site")
    if site == PROBE_VALUE_SITE:
        observation = _observation(connection, attempt_id)
        if observation is None:
            return None, "no_probe_observation"
        decision = body.get("value_decision") or {}
        described = decision.get("served") or decision.get("best") or {}
        credible_set = (described.get("detail") or {}).get("credible_set")
        if credible_set == "pinned_channel_ensemble":
            return ((observation["features"] or {}).get("robust") or {}).get("observed_emission"), "realized"
        return observation["grader_channel"].get("observed_outcome"), "realized"
    attempt = connection.execute(
        "SELECT practice_item_id, rubric_score, correctness, error_type FROM practice_attempts WHERE id = ?",
        (attempt_id,),
    ).fetchone()
    if attempt is None:
        return None, "no_attempt"
    if site == FOLLOWUP_VALUE_SITE:
        item = vault.practice_items.get(str(attempt["practice_item_id"]))
        rubric = vault.rubric_for_item(item) if item is not None else None
        bucket = score_bucket(int(attempt["rubric_score"] or 0), rubric.max_points if rubric is not None else 4)
        alphabet = set(body.get("emission_alphabet") or [])
        fired = sorted(
            str(row["misconception_id"])
            for row in connection.execute(
                "SELECT misconception_id FROM error_events WHERE attempt_id = ? AND misconception_id IS NOT NULL",
                (attempt_id,),
            )
        ) if _has(connection, "error_events") else []
        for channel in fired:
            if f"{bucket}|{channel}" in alphabet:
                return f"{bucket}|{channel}", "realized"
        error = str(attempt["error_type"] or "")
        if error and f"{bucket}|{error}" in alphabet:
            return f"{bucket}|{error}", "realized"
        return f"{bucket}|", "realized"
    if attempt["correctness"] is None:
        return None, "ungraded"
    return ("correct" if float(attempt["correctness"]) >= BINARY_CORRECTNESS_CUT else "incorrect"), "realized"


def realized_emission(
    connection: sqlite3.Connection,
    vault: LoadedVault,
    forecast: Mapping[str, Any],
    attempt_id: str,
) -> tuple[str | None, str]:
    """The realized emission in the forecast's alphabet, or (None, why not).

    A grade the proofs route check holds for review (mvp-0.17, re-review F9)
    realizes nothing at any site: nothing validated it, so its score (and the
    probe outcome or facet reading drawn from it) is no outcome yet.
    """

    if held_for_review_attempts(connection, (attempt_id,)):
        return None, GRADE_HELD_FOR_REVIEW
    body = forecast.get("forecast") or {}
    alphabet = set(body.get("emission_alphabet") or [])
    site = forecast.get("site")
    if site == "probe_selection":
        observation = _observation(connection, attempt_id)
        if observation is None:
            return None, "no_probe_observation"
        emission = observation["grader_channel"].get("observed_outcome")
    elif site == "probe_robust_selection":
        observation = _observation(connection, attempt_id)
        if observation is None:
            return None, "no_probe_observation"
        emission = ((observation["features"] or {}).get("robust") or {}).get("observed_emission")
    elif site == "followup_selection":
        emission, why = _target_facet_emission(connection, body, attempt_id)
        if emission is None:
            return None, why
    elif site == "staged_diagnostic_selection":
        # A staged diagnostic check is a probe administration: its realized
        # emission is the graded probe outcome, inside the declared alphabet.
        observation = _observation(connection, attempt_id)
        if observation is None:
            return None, "no_probe_observation"
        emission = observation["grader_channel"].get("observed_outcome")
    elif site in (PROBE_VALUE_SITE, FOLLOWUP_VALUE_SITE, TEACH_BACK_VALUE_SITE, PROJECT_PROBE_VALUE_SITE):
        emission, why = _value_decision_emission(connection, vault, forecast, attempt_id)
        if emission is None:
            return None, why
        alphabet = alphabet or set((body.get("predicted_outcomes") or {}).keys())
    elif site == "causal_shadow_selection":
        if not _has(connection, "causal_discriminating_observations"):
            return None, "no_discriminating_observation"
        row = connection.execute(
            "SELECT outcome, classified_as_json FROM causal_discriminating_observations "
            "WHERE probe_attempt_id = ? ORDER BY created_at LIMIT 1",
            (attempt_id,),
        ).fetchone()
        if row is None:
            return None, "no_discriminating_observation"
        classified = _loads(row["classified_as_json"], [])
        emissions = ((body.get("extra") or {}).get("emission_by_hypothesis")) or {}
        if row["outcome"] != "matched_single" or not isinstance(classified, list) or len(classified) != 1:
            return None, f"unmatched:{row['outcome']}"
        emission = emissions.get(str(classified[0]))
    else:
        return None, "site_without_outcome_mapping"
    if emission is None or (alphabet and emission not in alphabet):
        return None, "outside_alphabet"
    return str(emission), "realized"


# -- truth adapters -------------------------------------------------------------------------------


#: Factor resolutions that record what a REPAIR did (a cold check after it), not
#: which cause was true (``causal_factor_deferral``): repair effect, never truth.
REPAIR_RESOLUTION_KINDS = ("repair_confirmed", "escalated_unrepaired")


_OBSERVATION_COLUMNS = (
    "id, probe_attempt_id, outcome, classified_as_json, admitted, admissible_as_independent, support_authority"
)


def _independent_match(row: Mapping[str, Any] | None, realized_attempt_id: str | None) -> str | None:
    """The one hypothesis an observation is independent evidence for, else None.

    Admitted (the instrument discriminated over measured features), a
    ``matched_single`` naming exactly one hypothesis, independent of what the
    learner had been shown (``admissible_as_independent`` is not 0: migration
    155's post-reveal check), and not an observation of the forecast's own
    realized answer (that answer is the forecast's outcome, not later truth).
    """

    if row is None or not row["admitted"] or row["outcome"] != "matched_single":
        return None
    if row["admissible_as_independent"] is not None and not row["admissible_as_independent"]:
        return None
    if realized_attempt_id and row["probe_attempt_id"] == realized_attempt_id:
        return None
    classified = _loads(row["classified_as_json"], [])
    if not isinstance(classified, list) or len(classified) != 1:
        return None
    return str(classified[0])


def _support_delta(support: Mapping[str, Any]) -> float:
    try:
        return float(support.get("delta") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _cited_support(
    connection: sqlite3.Connection,
    support: Mapping[str, Any],
    linked: set[str],
    hypotheses: set[str],
    realized_attempt_id: str | None,
) -> tuple[str, set[str]] | None:
    """What a cold verification's diagnosis support proves, after resolving its evidence.

    A basis and an observation id are claims (re-review F1). The cited
    observation must exist in ``causal_discriminating_observations``, carry the
    support authority its basis grants (``SUPPORT_BASIS_AUTHORITY``: the one
    table that grants it), be independent (:func:`_independent_match`) and
    match one of the forecast's hypotheses. Positive support then confirms
    the matched hypothesis, and only when the verification names it; negative
    support rules out the verification's hypotheses only when the observation
    matched ANOTHER hypothesis of the forecast. Anything else proves nothing.
    """

    delta = _support_delta(support)
    basis = support.get("basis")
    observation_id = support.get("observation_id")
    if delta == 0.0 or basis not in SUPPORT_BASIS_AUTHORITY or not observation_id:
        return None
    if not _has(connection, "causal_discriminating_observations"):
        return None
    cited = connection.execute(
        f"SELECT {_OBSERVATION_COLUMNS} FROM causal_discriminating_observations WHERE id = ?",
        (str(observation_id),),
    ).fetchone()
    matched = _independent_match(cited, realized_attempt_id)
    if matched is None or matched not in hypotheses:
        return None
    if cited["support_authority"] != SUPPORT_BASIS_AUTHORITY[basis]:
        return None
    if delta > 0:
        return ("confirmed", {matched}) if matched in linked else None
    return ("ruled_out", set(linked)) if matched not in linked else None


def truth_for(
    connection: sqlite3.Connection,
    forecast: Mapping[str, Any],
    *,
    realized_attempt_id: str | None = None,
) -> dict[str, Any] | None:
    """Independent later diagnostic truth about the forecast's hypotheses, or None.

    Truth needs two things (review F1):

    * **explicit linkage**: the evidence names one of the forecast's own
      hypothesis ids. Causal hypothesis ids belong to one episode, so this is
      episode linkage too; sharing a repair class (a route) is not linkage.
    * **independent diagnostic evidence**: a cold verification whose
      ``diagnosis_support_update`` cites a resolvable, admitted, independent
      observation matching one of its own hypotheses (:func:`_cited_support`;
      re-review F1: the basis and the id alone are claims), an admitted,
      independent ``matched_single`` discriminating observation, or a later
      teach-back naming the same cause. An observation of the forecast's own
      realized answer is not independent of the forecast.

    What a repair did (a cold check's success or failure, a factor closed as
    ``repair_confirmed`` / ``escalated_unrepaired``) is reported separately as
    ``repair_effect``, one entry per cold verification (re-review F10: a factor
    closed by a verification already listed is that verification's outcome,
    not a second one): a repair can work for the wrong reason and fail for the
    right one, so it neither confirms nor rules out a cause.
    """

    body = forecast.get("forecast") or {}
    hypotheses = set((body.get("prior") or {}).keys())
    confirmed: set[str] = set()
    ruled_out: set[str] = set()
    sources: list[str] = []
    repair_effect: list[dict[str, Any]] = []
    created = forecast.get("created_at") or ""
    if hypotheses and _has(connection, "causal_cold_verifications"):
        for row in connection.execute(
            "SELECT id, hypothesis_ids_json, repair_class_id, success, diagnosis_support_update_json "
            "FROM causal_cold_verifications WHERE created_at >= ? ORDER BY created_at, id",
            (created,),
        ):
            linked = {str(v) for v in _loads(row["hypothesis_ids_json"], [])} & hypotheses
            if not linked:
                continue
            repair_effect.append({
                "source": "cold_verification", "cold_verification_id": str(row["id"]),
                "repair_class_id": row["repair_class_id"], "success": bool(row["success"]),
                "hypothesis_ids": sorted(linked),
            })
            support = _loads(row["diagnosis_support_update_json"], {}) or {}
            proved = _cited_support(connection, support, linked, hypotheses, realized_attempt_id)
            if proved is None:
                continue
            (confirmed if proved[0] == "confirmed" else ruled_out).update(proved[1])
            sources.append("cold_verification_diagnosis_support")
    if forecast.get("factor_id") and _has(connection, "unresolved_cause_factors"):
        row = connection.execute(
            "SELECT status, resolution_kind, resolution_detail_json FROM unresolved_cause_factors WHERE id = ?",
            (forecast["factor_id"],),
        ).fetchone()
        if row is not None and row["status"] == "resolved" and row["resolution_kind"] in REPAIR_RESOLUTION_KINDS:
            detail = _loads(row["resolution_detail_json"], {}) or {}
            verification_id = detail.get("cold_verification_id")
            listed = next((effect for effect in repair_effect
                           if verification_id and effect.get("cold_verification_id") == str(verification_id)), None)
            if listed is not None:
                listed["factor_resolution"] = row["resolution_kind"]
            else:
                repair_effect.append({
                    "source": "factor_resolution", "resolution_kind": row["resolution_kind"],
                    "repair_class_id": detail.get("repair_class_id"),
                    "success": row["resolution_kind"] == "repair_confirmed",
                    "cold_verification_id": str(verification_id) if verification_id else None,
                })
        # A factor closed by a discriminating observation is read below,
        # through that observation (it names the hypothesis it matched).
    if hypotheses and _has(connection, "causal_discriminating_observations"):
        for row in connection.execute(
            f"SELECT {_OBSERVATION_COLUMNS} FROM causal_discriminating_observations "
            "WHERE admitted = 1 AND outcome = 'matched_single' AND created_at >= ? ORDER BY created_at, id",
            (created,),
        ):
            hypothesis = _independent_match(row, realized_attempt_id)
            if hypothesis is None or hypothesis not in hypotheses:
                continue
            confirmed.add(hypothesis)
            sources.append("discriminating_observation")
    if hypotheses and _has(connection, "causal_hypotheses"):
        # A teach-back after the forecast whose diagnosis names the same cause
        # (same statement class) confirms the cause existed.
        rows = connection.execute(
            "SELECT h.id, h.statement_normalized FROM causal_hypotheses h WHERE h.id IN (%s)"
            % ",".join("?" for _ in hypotheses),
            tuple(sorted(hypotheses)),
        ).fetchall()
        statements = {str(r["statement_normalized"]): str(r["id"]) for r in rows}
        if statements:
            later = connection.execute(
                "SELECT h.statement_normalized FROM causal_hypotheses h JOIN practice_attempts a "
                "ON a.id = h.attempt_id WHERE a.attempt_type = 'teach_back' AND a.created_at >= ? "
                "AND h.statement_normalized IN (%s)" % ",".join("?" for _ in statements),
                (created, *sorted(statements)),
            ).fetchall()
            for r in later:
                confirmed.add(statements[str(r["statement_normalized"])])
                sources.append("teach_back_recurrence")
    if not confirmed and not ruled_out and not repair_effect:
        return None
    return {"confirmed": sorted(confirmed - ruled_out), "ruled_out": sorted(ruled_out),
            "sources": sorted(set(sources)), "repair_effect": repair_effect}


# -- the report -----------------------------------------------------------------------------------


def _join(
    connection: sqlite3.Connection,
    vault: LoadedVault,
    forecast: Mapping[str, Any],
    adapters: Sequence[Any],
) -> dict[str, Any]:
    joined: dict[str, Any] = {"status": "pending", "adapter": None}
    for adapter in adapters:
        hit = adapter.attempt_for(forecast)
        if hit is None:
            continue
        attempt_id, status = hit
        joined["adapter"] = adapter.name
        joined["status"] = status
        if attempt_id is None:
            break
        emission, why = realized_emission(connection, vault, forecast, attempt_id)
        joined["attempt_id"] = attempt_id
        joined["status"] = why
        joined["emission"] = emission
        break
    return joined


def _round(value: float | None, digits: int = 4) -> float | None:
    return None if value is None or (isinstance(value, float) and math.isnan(value)) else round(float(value), digits)


def calibration_report(vault: LoadedVault, *, since: str | None = None) -> dict[str, Any]:
    path = VaultPaths(vault.root, vault.config).sqlite_path
    with closing(connect(path, read_only=True)) as connection:
        connection.execute("BEGIN")
        forecasts = store.list_forecasts(connection, since=since)
        adapters = [RouterOutcomeAdapter(connection), LedgerOutcomeAdapter(connection)]
        rows = []
        for forecast in forecasts:
            joined = _join(connection, vault, forecast, adapters)
            truth = truth_for(connection, forecast, realized_attempt_id=joined.get("attempt_id"))
            rows.append((forecast, joined, truth))
    report = summarize_joined(rows, since=since, router_available=adapters[0].available,
                              logging_enabled=bool(vault.config.evsi.forecast_logging),
                              measured_loss_enabled=bool(vault.config.evsi.measured_loss_enabled))
    # Part C's estimate as it would be charged now (read-only), so the owner
    # can see the measured loss before deciding to turn it on.
    try:
        estimate = estimate_unresolved_cost(
            Repository.attach(path, read_only=True),
            pseudo_count=vault.config.evsi.unresolved_cost_prior_pseudo_count,
        )
        report["unresolved_cost_estimate"] = estimate.as_dict()
    except sqlite3.Error as error:
        report["unresolved_cost_estimate"] = {"available": False, "reason": str(error)}
    return report


def summarize_joined(
    rows: Sequence[tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any] | None]],
    *,
    since: str | None = None,
    router_available: bool = False,
    logging_enabled: bool = True,
    measured_loss_enabled: bool = False,
) -> dict[str, Any]:
    by_site: dict[str, dict[str, Any]] = {}
    for forecast, joined, truth in rows:
        site = str(forecast.get("site"))
        block = by_site.setdefault(site, {
            "forecasts": 0, "status": {}, "adapters": {}, "pairs": [], "log_losses": [], "eig": [],
            "entropy_drop": [], "change_pairs": [], "evsi_point": [], "truth": 0, "regret": [],
            "predicted_loss": [], "truth_probability": [], "verdicts": {},
            "repair_effect": {"success": 0, "failure": 0},
        })
        block["forecasts"] += 1
        block["status"][joined.get("status")] = block["status"].get(joined.get("status"), 0) + 1
        if joined.get("adapter"):
            block["adapters"][joined["adapter"]] = block["adapters"].get(joined["adapter"], 0) + 1
        block["verdicts"][forecast.get("verdict")] = block["verdicts"].get(forecast.get("verdict"), 0) + 1
        body = forecast.get("forecast") or {}
        predicted = body.get("predicted_outcomes") or {}
        emission = joined.get("emission")
        prior = body.get("prior") or {}
        likelihood = body.get("likelihood") or {}
        action_after = body.get("current_action")
        if emission is not None and predicted:
            for e, p in predicted.items():
                block["pairs"].append((float(p), 1.0 if e == emission else 0.0))
            block["log_losses"].append(-math.log(max(float(predicted.get(emission, 0.0)), 1e-12)))
            if forecast.get("eig_nats") is not None and prior and likelihood:
                after = posterior(likelihood, prior, emission)
                block["eig"].append(float(forecast["eig_nats"]))
                block["entropy_drop"].append(entropy(prior) - entropy(after))
            by_emission = body.get("action_by_emission") or {}
            if forecast.get("p_action_change") is not None and emission in by_emission:
                action_after = by_emission[emission]
                changed = action_after != body.get("current_action")
                block["change_pairs"].append((float(forecast["p_action_change"]), 1.0 if changed else 0.0))
        if forecast.get("evsi_point_minutes") is not None:
            block["evsi_point"].append(float(forecast["evsi_point_minutes"]))
        counted: set[str] = set()
        for effect in (truth or {}).get("repair_effect") or []:
            # One cold verification is one repair outcome, however many ledgers
            # record it (re-review F10).
            verification_id = effect.get("cold_verification_id")
            if verification_id:
                if verification_id in counted:
                    continue
                counted.add(verification_id)
            block["repair_effect"]["success" if effect.get("success") else "failure"] += 1
        if truth is not None and truth.get("confirmed"):
            block["truth"] += 1
            belief = posterior(likelihood, prior, emission) if (emission is not None and likelihood) else prior
            p_truth = sum(float(belief.get(h, 0.0)) for h in truth["confirmed"])
            block["truth_probability"].append(p_truth)
            minutes = ((body.get("loss") or {}).get("minutes")) or {}
            regrets = [
                float(minutes[h][action_after])
                for h in truth["confirmed"]
                if h in minutes and action_after in minutes[h]
            ]
            if regrets:
                expected = sum(float(belief.get(h, 0.0)) * float(minutes[h][action_after])
                               for h in minutes if action_after in minutes[h])
                block["regret"].append(min(regrets))
                block["predicted_loss"].append(expected)
    sites: dict[str, Any] = {}
    for site, block in sorted(by_site.items()):
        outcome = reliability(block["pairs"])
        outcome["log_loss"] = _round(sum(block["log_losses"]) / len(block["log_losses"])) if block["log_losses"] else None
        outcome["realized_forecasts"] = len(block["log_losses"])
        info = {
            "n": len(block["eig"]),
            "mean_predicted_eig": _round(sum(block["eig"]) / len(block["eig"])) if block["eig"] else None,
            "mean_realized_entropy_drop": _round(sum(block["entropy_drop"]) / len(block["entropy_drop"]))
            if block["entropy_drop"] else None,
        }
        change = reliability(block["change_pairs"], bins=5)
        if block["change_pairs"]:
            change["mean_predicted"] = _round(sum(p for p, _ in block["change_pairs"]) / len(block["change_pairs"]))
            change["realized_rate"] = _round(sum(o for _, o in block["change_pairs"]) / len(block["change_pairs"]))
        truth_block = {
            "forecasts_with_truth": block["truth"],
            "mean_probability_on_truth": _round(sum(block["truth_probability"]) / len(block["truth_probability"]))
            if block["truth_probability"] else None,
            "regret_n": len(block["regret"]),
            "mean_regret_minutes": _round(sum(block["regret"]) / len(block["regret"])) if block["regret"] else None,
            "mean_predicted_loss_minutes": _round(sum(block["predicted_loss"]) / len(block["predicted_loss"]))
            if block["predicted_loss"] else None,
        }
        sites[site] = {
            "forecasts": block["forecasts"],
            "verdicts": block["verdicts"],
            "join_status": block["status"],
            "adapters": block["adapters"],
            "outcome_reliability": outcome,
            "information": info,
            "action_change": change,
            "mean_evsi_point_minutes": _round(sum(block["evsi_point"]) / len(block["evsi_point"]))
            if block["evsi_point"] else None,
            "truth": truth_block,
            # What repairs did after these forecasts: not diagnostic truth.
            "repair_effect": block["repair_effect"],
        }
    total = sum(block["forecasts"] for block in by_site.values())
    return {
        "status": "ok",
        "report_version": REPORT_VERSION,
        "forecast_version": FORECAST_VERSION,
        "since": since,
        "forecasts": total,
        "forecast_logging": logging_enabled,
        "measured_loss_enabled": measured_loss_enabled,
        "outcome_adapter": "router_outcomes then ledgers" if router_available else "ledgers (R1 tables absent)",
        "sites": sites,
        "notes": [
            "Truth counts only independent diagnostic evidence linked to the forecast's own hypotheses: "
            "a cold verification's diagnosis support whose cited observation resolves to an admitted, "
            "independent match on one of its hypotheses, an admitted discriminating observation (not of "
            "the forecast's own answer), teach-back recurrence. Repair outcomes are reported as "
            "repair_effect (one per cold verification), never as truth; the system's own posterior is "
            "never truth.",
            "Single-learner sample sizes: read every rate with its n.",
        ],
    }
