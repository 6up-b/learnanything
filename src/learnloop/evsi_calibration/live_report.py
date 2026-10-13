"""`learnloop evsi calibration`: how good were the live VOI forecasts?

Reads ``voi_forecasts`` (EVSI calibration Part B) and joins, at read time:

1. **The realized outcome** of each forecast, through an outcome adapter:
   R1's ``router_decisions``/``router_outcomes`` when the vault has them (the
   decision's chosen scheduler candidate -> the attempt that took it), else
   the probe and attempt ledgers (``practice_attempts.probe_presentation_id``
   -> ``probe_observations``; the first later attempt on the chosen item).
   The realized emission is mapped into the forecast's own alphabet; one that
   cannot be mapped is counted as ``unmapped``, never guessed.
2. **Later truth**, through truth adapters that need explicit hypothesis
   linkage and independent diagnostic evidence (:func:`truth_for`): a cold
   verification's diagnosis-support update on an admitted basis, an admitted
   ``matched_single`` discriminating observation (not of the forecast's own
   answer), and a later teach-back whose diagnosis names the same cause. What
   a repair did (a cold check's success or failure, a factor closed as
   ``repair_confirmed`` / ``escalated_unrepaired``) is reported apart, as
   repair effect: it neither confirms nor rules out a cause. The system's own
   posterior moving a misconception to "resolved" is never truth.

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
from learnloop.evsi_calibration.metrics import reliability
from learnloop.scheduling.unresolved_cost import estimate_unresolved_cost
from learnloop.scheduling.voi_forecasts import FORECAST_VERSION, entropy, posterior
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

REPORT_VERSION = "voi_calibration_report_v1"


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


# -- outcome adapters ---------------------------------------------------------------------------


class RouterOutcomeAdapter:
    """R1: the attempt that took a logged router decision (when R1 is present)."""

    name = "router_outcomes"

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.available = _has(connection, "router_decisions") and _has(connection, "router_outcomes")

    def attempt_for(self, forecast: Mapping[str, Any]) -> tuple[str | None, str] | None:
        if not self.available or not forecast.get("scheduler_candidate_id"):
            return None
        row = self.connection.execute(
            "SELECT o.action_status, o.action_attempt_id FROM router_decisions d "
            "JOIN router_outcomes o ON o.decision_id = d.id "
            "WHERE d.chosen_scheduler_candidate_id = ? ORDER BY d.created_at LIMIT 1",
            (forecast["scheduler_candidate_id"],),
        ).fetchone()
        if row is None:
            return None
        if row["action_status"] == "taken" and row["action_attempt_id"]:
            return str(row["action_attempt_id"]), "taken"
        return None, str(row["action_status"])


class LedgerOutcomeAdapter:
    """The probe and attempt ledgers (always available)."""

    name = "ledgers"

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def attempt_for(self, forecast: Mapping[str, Any]) -> tuple[str | None, str] | None:
        if forecast.get("presentation_id"):
            row = self.connection.execute(
                "SELECT id FROM practice_attempts WHERE probe_presentation_id = ?",
                (forecast["presentation_id"],),
            ).fetchone()
            return (str(row["id"]), "taken") if row is not None else (None, "pending")
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


def _observation(connection: sqlite3.Connection, attempt_id: str) -> dict[str, Any] | None:
    if not _has(connection, "probe_observations"):
        return None
    row = connection.execute(
        "SELECT grader_channel_json, features_json FROM probe_observations WHERE attempt_id = ?", (attempt_id,)
    ).fetchone()
    if row is None:
        return None
    return {"grader_channel": _loads(row["grader_channel_json"], {}), "features": _loads(row["features_json"], {})}


def realized_emission(
    connection: sqlite3.Connection,
    vault: LoadedVault,
    forecast: Mapping[str, Any],
    attempt_id: str,
) -> tuple[str | None, str]:
    """The realized emission in the forecast's alphabet, or (None, why not)."""

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
        row = connection.execute(
            "SELECT rubric_score, error_type, practice_item_id FROM practice_attempts WHERE id = ?", (attempt_id,)
        ).fetchone()
        if row is None or row["rubric_score"] is None:
            return None, "ungraded"
        item = vault.practice_items.get(str(row["practice_item_id"]))
        rubric = vault.rubric_for_item(item) if item is not None else None
        bucket = score_bucket(int(row["rubric_score"]), rubric.max_points if rubric is not None else 4)
        error = str(row["error_type"] or "")
        emission = f"{bucket}|{error}"
        if emission not in alphabet:
            emission = f"{bucket}|"
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


def _own_observation_ids(connection: sqlite3.Connection, realized_attempt_id: str | None) -> set[str]:
    """Discriminating observations made of the forecast's own realized answer."""

    if not realized_attempt_id or not _has(connection, "causal_discriminating_observations"):
        return set()
    return {
        str(row["id"])
        for row in connection.execute(
            "SELECT id FROM causal_discriminating_observations WHERE probe_attempt_id = ?", (realized_attempt_id,)
        )
    }


def _support_delta(support: Mapping[str, Any]) -> float:
    try:
        return float(support.get("delta") or 0.0)
    except (TypeError, ValueError):
        return 0.0


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
      ``diagnosis_support_update`` carries a non-zero delta on an admitted
      basis (``causal_attribution.SUPPORT_BASIS_AUTHORITY``) and cites its
      observation, an admitted ``matched_single`` discriminating observation,
      or a later teach-back naming the same cause. An observation of the
      forecast's own realized answer is not independent of the forecast.

    What a repair did (a cold check's success or failure, a factor closed as
    ``repair_confirmed`` / ``escalated_unrepaired``) is reported separately as
    ``repair_effect``: a repair can work for the wrong reason and fail for the
    right one, so it neither confirms nor rules out a cause.
    """

    body = forecast.get("forecast") or {}
    hypotheses = set((body.get("prior") or {}).keys())
    confirmed: set[str] = set()
    ruled_out: set[str] = set()
    sources: list[str] = []
    repair_effect: list[dict[str, Any]] = []
    created = forecast.get("created_at") or ""
    own_observations = _own_observation_ids(connection, realized_attempt_id)
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
                "source": "cold_verification", "id": str(row["id"]), "repair_class_id": row["repair_class_id"],
                "success": bool(row["success"]), "hypothesis_ids": sorted(linked),
            })
            support = _loads(row["diagnosis_support_update_json"], {}) or {}
            delta = _support_delta(support)
            if (
                delta == 0.0
                or support.get("basis") not in SUPPORT_BASIS_AUTHORITY
                or not support.get("observation_id")
                or str(support["observation_id"]) in own_observations
            ):
                continue
            (confirmed if delta > 0 else ruled_out).update(linked)
            sources.append("cold_verification_diagnosis_support")
    if forecast.get("factor_id") and _has(connection, "unresolved_cause_factors"):
        row = connection.execute(
            "SELECT status, resolution_kind, resolution_detail_json FROM unresolved_cause_factors WHERE id = ?",
            (forecast["factor_id"],),
        ).fetchone()
        if row is not None and row["status"] == "resolved" and row["resolution_kind"] in REPAIR_RESOLUTION_KINDS:
            detail = _loads(row["resolution_detail_json"], {}) or {}
            repair_effect.append({
                "source": "factor_resolution", "resolution_kind": row["resolution_kind"],
                "repair_class_id": detail.get("repair_class_id"),
                "success": row["resolution_kind"] == "repair_confirmed",
            })
        # A factor closed by a discriminating observation is read below,
        # through that observation (it names the hypothesis it matched).
    if hypotheses and _has(connection, "causal_discriminating_observations"):
        for row in connection.execute(
            "SELECT id, classified_as_json FROM causal_discriminating_observations "
            "WHERE admitted = 1 AND outcome = 'matched_single' AND created_at >= ? ORDER BY created_at, id",
            (created,),
        ):
            classified = _loads(row["classified_as_json"], [])
            if not isinstance(classified, list) or len(classified) != 1:
                continue
            hypothesis = str(classified[0])
            if hypothesis not in hypotheses or str(row["id"]) in own_observations:
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
        for effect in (truth or {}).get("repair_effect") or []:
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
            "a cold verification's diagnosis support on an admitted basis, an admitted discriminating "
            "observation (not of the forecast's own answer), teach-back recurrence. Repair outcomes are "
            "reported as repair_effect, never as truth; the system's own posterior is never truth.",
            "Single-learner sample sizes: read every rate with its n.",
        ],
    }
