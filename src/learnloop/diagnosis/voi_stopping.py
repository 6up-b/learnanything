"""mvp-0.17 Part 1: four count caps lifted onto value of information.

Owner decisions 2026-10-12/13: "lift the other 4 caps on the same value of
information basis"; follow-ups and probes are chosen by EIG/EVSI ("multiple
follow ups might be high ROI to search for the true misconception or decide
between hypotheses/decide between actions"), not by hard caps. Each former cap
stays as the kill-switch path (``voi_stopping.enabled`` and one sub-switch per
site); off, serving is ``mvp-0.16``'s exactly.

======================  ==========================================  ==========================
site                    former count cap (the kill-switch path)     what decides now
======================  ==========================================  ==========================
``probe_episode``       ``probe.episode.session_qualifying_         every next observation of an
                        observation_cap`` (4 per session)           episode, while its value pays;
                                                                    then the block closes and the
                                                                    episode completes with
                                                                    ``value_of_information_stop``
``followup_             ``scheduler.followup.max_interventions_     every further intervention on
intervention``          per_lo_per_session`` (1)                    an LO in a session
``teach_back``          ``teach_back.session_cap`` (1 per queue)    every further teach-back
``project_probe``       ``plan.project_probes_max_per_day`` (4)     every due project probe, in
                                                                    value-per-minute order
======================  ==========================================  ==========================

**The value of the next observation** is computed with the machinery that
already values probes, never a new constant:

* **Information** (EIG, nats) over the learner's rival hypotheses through the
  existing adapters: a probe instrument's composed ``P(E | H)``
  (``probe_families.instrument_conditionals``, or the episode's pinned robust
  ensemble), the follow-up slate's facet and misconception EIG, the selection
  reward's ``probe_eig_total`` for a teach-back or a project probe. The robust
  EIG is the ensemble's lower quantile (``robust_composition.ROBUST_QUANTILE``)
  where a credible set exists, the point EIG otherwise.
* **Decision value** (robust EVSI, minutes) where a next-action decision is
  at stake: the hypotheses' triage routes (``failure_triage_routes``) give
  each hypothesis its effective repair, a misconception's repair targets that
  misconception, and ``action_loss.build_loss_table`` prices a wrong repair in
  wasted learner-minutes. A decision is at stake when the plausible hypotheses
  (posterior at least ``probe.episode.action_equivalence_plausible_threshold``,
  the existing plausibility cutoff) route to two or more repairs.
  ``evsi.rank_feasible`` then values and stops: continue while the robust
  EVSI's lower bound exceeds ``lambda_time * minutes + burden``.
* **Otherwise** (no decision at stake, no complete loss table, or
  ``rank_feasible`` abstains on a flip) the robust EIG is converted to minutes
  with ``robust_composition.VALUE_PER_NAT_MINUTES``, exactly as
  ``robust_composition.evaluate_selection``'s stop rule does, and the same
  stop applies. An abstention's fallback is labelled ``value_uncertain``.
* **Minutes** are the learner's own: the item's median latency, else the
  practice mode's median shrunk toward the authored estimate, else the
  authored estimate (a probe card's ``expected_seconds``, an item's
  ``expected_minutes``), else ``action_loss.DEFAULT_INTERVENTION_MINUTES``.

lambda_time (1, the minutes numeraire), the burden (0), the nat-to-minutes
scale (60), the robust quantile (0.10), the +-0.15 stress and the loss model
are heuristic decision parameters (``robust_composition``, ``evsi``,
``action_loss``); every decision receipt lists them with that label. The
``evsi/calibration`` stage will recommend values.

**Every stop/continue decision is a forecast**, recorded beside the decision
(router R1's ``router_decisions`` detail for Today offers and plan blocks, the
probe presentation's selection components, the follow-up's gate diagnostics):
the predicted outcome distribution, the EIG, the EVSI point and robust value,
the predicted probability of an action change, the parameters with their
provenance, and the former cap's counterfactual (would it have bound?). The
shape follows the ``evsi/calibration`` branch's ``voi_forecast_v2`` body so its
report can score these too.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Iterable, Mapping, Sequence

from learnloop.algorithm_versions import VOI_STOPPING_VERSIONS
from learnloop.diagnosis.robust_composition import (
    BURDEN_COST,
    LAMBDA_TIME,
    ROBUST_QUANTILE,
    VALUE_PER_NAT_MINUTES,
    expected_information_gain,
    robust_quantile,
)
from learnloop.scheduling import action_loss as AL
from learnloop.scheduling import evsi as EV

#: Shape version of one decision's forecast body.
FORECAST_VERSION = "voi_stop_forecast_v1"

SITE_PROBE_EPISODE = "probe_episode"
SITE_FOLLOWUP = "followup_intervention"
SITE_TEACH_BACK = "teach_back"
SITE_PROJECT_PROBE = "project_probe"
SITES: tuple[str, ...] = (SITE_PROBE_EPISODE, SITE_FOLLOWUP, SITE_TEACH_BACK, SITE_PROJECT_PROBE)

#: ``[voi_stopping]`` sub-switch per site.
SITE_SWITCH: dict[str, str] = {
    SITE_PROBE_EPISODE: "probe_episodes",
    SITE_FOLLOWUP: "followups",
    SITE_TEACH_BACK: "teach_back",
    SITE_PROJECT_PROBE: "project_probes",
}

#: The count cap each site replaces; it serves again when the site is off.
FORMER_CAPS: dict[str, str] = {
    SITE_PROBE_EPISODE: "probe.episode.session_qualifying_observation_cap",
    SITE_FOLLOWUP: "scheduler.followup.max_interventions_per_lo_per_session",
    SITE_TEACH_BACK: "teach_back.session_cap",
    SITE_PROJECT_PROBE: "plan.project_probes_max_per_day",
}

CONTINUE = "continue"
STOP = "stop"
METHOD_ROBUST_EVSI = "robust_evsi"
METHOD_EIG_VALUE = "eig_value"

#: Reasons a decision names.
REASON_EVSI_CLEARS = "robust_evsi_clears_minutes_cost"
REASON_EVSI_BELOW = "robust_evsi_below_minutes_cost"
REASON_EIG_CLEARS = "eig_value_clears_minutes_cost"
REASON_EIG_BELOW = "eig_value_below_minutes_cost"

#: Candidates whose full forecast a site decision keeps (the best one always).
MAX_RECORDED_CANDIDATES = 6

#: DL1's pseudo-observations behind a duration prior (``daily_plan/estimates``).
#: Repeated here, not imported: serving code never reads the daily plan
#: (import contract ``evidence-never-reaches-the-daily-plan``).
DURATION_PSEUDO_OBSERVATIONS = 3.0
#: A latency above this many minutes is winsorized (``plan.latency_cap_minutes``'s
#: default; the plan's own estimator reads the configured value).
DEFAULT_LATENCY_CAP_MINUTES = 15.0

_ROUND_DIGITS = 8


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------


def voi_stopping_active(config: Any, site: str | None = None) -> bool:
    """True at a ``VOI_STOPPING_VERSIONS`` member with the kill switch (and the
    site's sub-switch) on. Off, the site's former count cap serves exactly."""

    algorithms = getattr(config, "algorithms", None)
    if getattr(algorithms, "algorithm_version", None) not in VOI_STOPPING_VERSIONS:
        return False
    section = getattr(config, "voi_stopping", None)
    if section is None or not bool(getattr(section, "enabled", False)):
        return False
    if site is None:
        return True
    return bool(getattr(section, SITE_SWITCH[site], False))


def probe_lane_reads_diagnosis(config: Any) -> bool:
    """mvp-0.17 Part 2: the probe hypothesis lane reads the diagnosis overlay.

    True at a ``VOI_STOPPING_VERSIONS`` member with
    ``diagnosis.probe_lane_reads_diagnosis`` on. The overlay changes only
    blind-graded events, so a joint-graded vault reads what it always read.
    """

    algorithms = getattr(config, "algorithms", None)
    if getattr(algorithms, "algorithm_version", None) not in VOI_STOPPING_VERSIONS:
        return False
    diagnosis = getattr(config, "diagnosis", None)
    return bool(getattr(diagnosis, "probe_lane_reads_diagnosis", False))


def probe_lane_holds_out_pending(config: Any) -> bool:
    diagnosis = getattr(config, "diagnosis", None)
    return str(getattr(diagnosis, "probe_lane_pending", "hold_out")) == "hold_out"


# ---------------------------------------------------------------------------
# Minutes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MinutesEstimate:
    """One candidate's expected minutes and where they came from."""

    minutes: float
    source: str
    sample_count: int = 0

    @property
    def provenance(self) -> str:
        return {
            "own_latency_median": "measured",
            "mode_latency_shrunk": "measured",
            "plan_estimate": "measured",
            "authored_prior": "heuristic",
            "heuristic_default": "heuristic",
        }.get(self.source, "heuristic")

    def as_dict(self) -> dict[str, Any]:
        return {
            "minutes": round(float(self.minutes), 6),
            "source": self.source,
            "provenance": self.provenance,
            "sample_count": int(self.sample_count),
        }


class VoiContext:
    """What one serving decision reads once: latencies, routes, loss tables.

    Built per queue build (or per follow-up decision); every read is lazy, so a
    build that values nothing reads nothing.
    """

    def __init__(self, vault: Any, repository: Any) -> None:
        self.vault = vault
        self.repository = repository
        self._latencies: tuple[dict[str, list[float]], dict[str, list[float]]] | None = None
        self._routes: list[dict[str, Any]] | None = None
        self._durations: dict[str, AL.DurationEstimate] | None = None
        self._loss_tables: dict[tuple[tuple[str, str], ...], AL.LossTable] = {}

    @property
    def plausible_threshold(self) -> float:
        episode = getattr(getattr(self.vault.config, "probe", None), "episode", None)
        return float(getattr(episode, "action_equivalence_plausible_threshold", 0.10))

    # -- minutes --------------------------------------------------------------

    def _load_latencies(self) -> tuple[dict[str, list[float]], dict[str, list[float]]]:
        if self._latencies is None:
            by_item: dict[str, list[float]] = {}
            by_mode: dict[str, list[float]] = {}
            cap = float(
                getattr(getattr(self.vault.config, "plan", None), "latency_cap_minutes", DEFAULT_LATENCY_CAP_MINUTES)
            )
            with self.repository.connection() as connection:
                rows = connection.execute(
                    "SELECT practice_item_id, practice_mode, latency_seconds FROM practice_attempts "
                    "WHERE latency_seconds IS NOT NULL AND latency_seconds > 0"
                ).fetchall()
            for row in rows:
                minutes = min(max(float(row["latency_seconds"]), 0.0) / 60.0, cap)
                by_item.setdefault(str(row["practice_item_id"]), []).append(minutes)
                by_mode.setdefault(str(row["practice_mode"]), []).append(minutes)
            self._latencies = (by_item, by_mode)
        return self._latencies

    def item_minutes(self, item: Any, *, authored_minutes: float | None = None) -> MinutesEstimate:
        """The learner's expected minutes on ``item``.

        Own latencies' median, else the practice mode's median shrunk toward the
        authored prior with DL1's three pseudo-observations, else the authored
        prior (``authored_minutes``, e.g. a probe card's expected seconds, else
        the item's ``expected_minutes``), else the conservative default.
        """

        by_item, by_mode = self._load_latencies()
        own = by_item.get(str(getattr(item, "id", "")), [])
        if own:
            return MinutesEstimate(float(statistics.median(own)), "own_latency_median", len(own))
        prior: float | None = None
        if authored_minutes is not None and authored_minutes > 0:
            prior = float(authored_minutes)
        else:
            expected = getattr(item, "expected_minutes", None)
            if expected is not None and float(expected) > 0:
                prior = float(expected)
        prior_source = "authored_prior" if prior is not None else "heuristic_default"
        if prior is None:
            prior = AL.DEFAULT_INTERVENTION_MINUTES
        mode = by_mode.get(str(getattr(item, "practice_mode", "") or ""), [])
        if mode:
            k = DURATION_PSEUDO_OBSERVATIONS
            shrunk = (len(mode) * float(statistics.median(mode)) + k * prior) / (len(mode) + k)
            return MinutesEstimate(shrunk, "mode_latency_shrunk", len(mode))
        return MinutesEstimate(prior, prior_source, 0)

    # -- loss tables ----------------------------------------------------------

    def _route_rows(self) -> list[dict[str, Any]]:
        if self._routes is None:
            try:
                self._routes = list(self.repository.failure_triage_routes())
            except Exception:  # pragma: no cover - a database without the routes table
                self._routes = []
        return self._routes

    def label_actions(self, labels: Iterable[str]) -> dict[str, str] | None:
        """Each hypothesis label's effective repair, or None when any lacks a route.

        The triage route of the label's reason (``probe_hypotheses.
        triage_reason_for_label``, the bridge episode completion already asks)
        names the first intervention. A misconception's or confusion's repair
        targets that belief, so two rival misconceptions are two repairs.
        """

        from learnloop.diagnosis.probe_hypotheses import triage_reason_for_label

        by_reason: dict[str, Mapping[str, Any]] = {}
        for route in self._route_rows():
            reason = route.get("reason")
            if reason is not None and route.get("active", 1) and reason not in by_reason:
                by_reason[str(reason)] = route
        actions: dict[str, str] = {}
        for label in labels:
            route = by_reason.get(triage_reason_for_label(label))
            if route is None or not route.get("first_intervention"):
                return None
            action = str(route["first_intervention"])
            if label.startswith(("misconception:", "confuses_with:")):
                action = f"{action}@{label}"
            actions[label] = action
        return actions

    def loss_table(self, label_actions: Mapping[str, str]) -> AL.LossTable | None:
        """``action_loss.build_loss_table`` over hypothesis labels (one route per label)."""

        key = tuple(sorted(label_actions.items()))
        if key in self._loss_tables:
            return self._loss_tables[key]
        routes = [{"reason": label, "first_intervention": action} for label, action in key]
        if self._durations is None:
            # One pooled read: every action is priced by the same logged median
            # (there is no per-intervention tag yet, action_loss §6.2).
            self._durations = {}
        actions = sorted(set(label_actions.values()))
        missing = [action for action in actions if action not in self._durations]
        if missing:
            self._durations.update(AL.attempt_minutes_by_intervention(missing, repository=self.repository))
        overrides = {action: self._durations[action].minutes for action in actions}
        try:
            table = AL.build_loss_table(
                routes=routes,
                hypotheses=[label for label, _action in key],
                duration_overrides=overrides,
            )
        except (AL.LossTableIncompleteError, AL.LossDerivationError):
            return None
        self._loss_tables[key] = table
        return table

    def duration_sources(self, actions: Iterable[str]) -> dict[str, dict[str, Any]]:
        return {
            action: self._durations[action].as_dict()
            for action in sorted(set(actions))
            if self._durations is not None and action in self._durations
        }


# ---------------------------------------------------------------------------
# Forecasts and decisions
# ---------------------------------------------------------------------------


def _outcome_key(outcome: Any) -> str:
    if isinstance(outcome, tuple):
        return "|".join("" if part is None else str(part) for part in outcome)
    return str(outcome)


def _keyed(member: Mapping[str, Mapping[Any, float]]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for label, row in member.items():
        keyed: dict[str, float] = {}
        for outcome, probability in row.items():
            key = _outcome_key(outcome)
            keyed[key] = keyed.get(key, 0.0) + float(probability)
        out[str(label)] = keyed
    return out


def _normalized(prior: Mapping[str, float], labels: Sequence[str]) -> dict[str, float]:
    weights = {label: max(float(prior.get(label, 0.0)), 0.0) for label in labels}
    total = sum(weights.values())
    if total <= 0:
        return {}
    return {label: weight / total for label, weight in weights.items()}


def _predictive(member: Mapping[str, Mapping[Any, float]], prior: Mapping[str, float]) -> dict[Any, float]:
    out: dict[Any, float] = {}
    for label, weight in prior.items():
        for outcome, probability in member.get(label, {}).items():
            out[outcome] = out.get(outcome, 0.0) + weight * float(probability)
    return out


def _posterior(member: Mapping[str, Mapping[Any, float]], prior: Mapping[str, float], outcome: Any) -> dict[str, float]:
    raw = {label: weight * float(member.get(label, {}).get(outcome, 0.0)) for label, weight in prior.items()}
    total = sum(raw.values())
    if total <= 0:
        return dict(prior)
    return {label: value / total for label, value in raw.items()}


def _map_label(distribution: Mapping[str, float]) -> str | None:
    if not distribution:
        return None
    return max(sorted(distribution), key=lambda label: distribution[label])


def heuristic_parameters(minutes: MinutesEstimate, *, method: str, evsi_used: bool) -> list[dict[str, Any]]:
    """Every number the decision ran on, with its provenance (all heuristic but the minutes)."""

    params = [
        {"name": "lambda_time", "value": LAMBDA_TIME, "provenance": "heuristic",
         "source": "robust_composition.LAMBDA_TIME", "note": "minutes numeraire, fixed at 1 (U-023); not yet calibrated"},
        {"name": "burden_cost_minutes", "value": BURDEN_COST, "provenance": "heuristic",
         "source": "robust_composition.BURDEN_COST", "note": "not yet calibrated"},
        {"name": "value_per_nat_minutes", "value": VALUE_PER_NAT_MINUTES, "provenance": "heuristic",
         "source": "robust_composition.VALUE_PER_NAT_MINUTES", "note": "nat-to-minutes scale; not yet calibrated"},
        {"name": "robust_quantile", "value": ROBUST_QUANTILE, "provenance": "heuristic",
         "source": "robust_composition.ROBUST_QUANTILE", "note": "not yet calibrated"},
        {"name": "expected_minutes", "value": round(float(minutes.minutes), 6), "provenance": minutes.provenance,
         "source": minutes.source, "sample_count": int(minutes.sample_count)},
    ]
    if evsi_used:
        params.extend(
            [
                {"name": "perturbation_delta", "value": EV.PERTURBATION_DELTA, "provenance": "heuristic",
                 "source": "evsi.PERTURBATION_DELTA", "note": "+-0.15 stress; not yet calibrated"},
                {"name": "loss_model", "value": "triage_route_wasted_minutes", "provenance": "heuristic",
                 "source": "action_loss.build_loss_table",
                 "note": "a wrong repair wastes its minutes plus the delay of the right one; not yet calibrated"},
            ]
        )
    params.append({"name": "method", "value": method, "provenance": "structural"})
    return params


@dataclass(frozen=True)
class Candidate:
    """One possible next observation at a site.

    ``members`` are composed ``P(E | H)`` tables keyed by hypothesis label
    (member 0 the mean; more members form the credible set). ``eig_scale`` is
    the independent-evidence discount on the members' EIG; ``extra_eig_nats``
    is information from an adapter outside the members (the follow-up slate's
    facet EIG, a reward's ``probe_eig_total``), already discounted.
    """

    ref: str
    minutes: MinutesEstimate
    members: tuple[Mapping[str, Mapping[Any, float]], ...] = ()
    eig_scale: float = 1.0
    extra_eig_nats: float = 0.0
    detail: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidateValue:
    ref: str
    decision: str
    reason: str
    method: str
    value_uncertain: bool
    eig_nats: float
    eig_robust_nats: float
    member_eig_nats: float
    value_point_minutes: float
    value_robust_minutes: float
    value_ucb_minutes: float | None
    cost_minutes: float
    minutes: MinutesEstimate
    forecast: dict[str, Any]
    detail: Mapping[str, Any]

    @property
    def continues(self) -> bool:
        return self.decision == CONTINUE

    @property
    def value_per_minute(self) -> float:
        return self.value_robust_minutes / max(self.minutes.minutes, 1e-6)

    def summary(self) -> dict[str, Any]:
        return {
            "ref": self.ref,
            "decision": self.decision,
            "reason": self.reason,
            "method": self.method,
            "value_uncertain": self.value_uncertain,
            "eig_nats": round(self.eig_nats, _ROUND_DIGITS),
            "eig_robust_nats": round(self.eig_robust_nats, _ROUND_DIGITS),
            "evsi_point_minutes": round(self.value_point_minutes, 6),
            "evsi_robust_minutes": round(self.value_robust_minutes, 6),
            "cost_minutes": round(self.cost_minutes, 6),
            "minutes": self.minutes.as_dict(),
        }

    def as_dict(self) -> dict[str, Any]:
        body = self.summary()
        body["evsi_ucb_minutes"] = None if self.value_ucb_minutes is None else round(self.value_ucb_minutes, 6)
        body["member_eig_nats"] = round(self.member_eig_nats, _ROUND_DIGITS)
        body["forecast"] = self.forecast
        if self.detail:
            body["detail"] = dict(self.detail)
        return body


@dataclass(frozen=True)
class SiteDecision:
    """One value-of-information stop/continue decision at a site."""

    site: str
    learning_object_id: str | None
    decision: str
    reason: str
    candidates: tuple[CandidateValue, ...]
    former_cap: dict[str, Any]
    rank: dict[str, Any] | None
    context: dict[str, Any]
    parameters: list[dict[str, Any]]

    def value_for(self, ref: str) -> CandidateValue | None:
        return next((value for value in self.candidates if value.ref == ref), None)

    @property
    def best(self) -> CandidateValue | None:
        return self.candidates[0] if self.candidates else None

    def admits(self, ref: str) -> bool:
        value = self.value_for(ref)
        return value is not None and value.continues

    def cap_comparison(self) -> str:
        """How value compared with the former cap: ``agree``, ``earlier`` (value
        stopped where the cap would not) or ``later`` (value continued where the
        cap would have bound)."""

        would_bind = bool(self.former_cap.get("would_bind"))
        if self.decision == STOP and not would_bind:
            return "earlier"
        if self.decision == CONTINUE and would_bind:
            return "later"
        return "agree"

    def as_dict(self) -> dict[str, Any]:
        best = self.best
        return {
            "forecast_version": FORECAST_VERSION,
            "site": self.site,
            "learning_object_id": self.learning_object_id,
            "decision": self.decision,
            "reason": self.reason,
            "chosen_ref": best.ref if best is not None and self.decision == CONTINUE else None,
            "best": best.as_dict() if best is not None else None,
            "candidates": [value.summary() for value in self.candidates[:MAX_RECORDED_CANDIDATES]],
            "candidate_count": len(self.candidates),
            "former_cap": dict(self.former_cap),
            "cap_comparison": self.cap_comparison(),
            "rank": self.rank,
            "context": dict(self.context),
            "parameters": list(self.parameters),
            "calibration_label": "heuristic",
        }


def _forecast(
    member0: Mapping[str, Mapping[Any, float]],
    prior: Mapping[str, float],
    *,
    eig_nats: float,
    label_actions: Mapping[str, str] | None,
    loss_table: AL.LossTable | None,
) -> dict[str, Any]:
    """Predicted outcomes, the action after each, and P(action change)."""

    predicted = _predictive(member0, prior)
    if loss_table is not None and label_actions is not None:
        action_proxy = "triage_route_repair"

        def action_of(distribution: Mapping[str, float]) -> str | None:
            return loss_table.argmin_action(distribution)
    else:
        action_proxy = "map_hypothesis"

        def action_of(distribution: Mapping[str, float]) -> str | None:
            return _map_label(distribution)

    current = action_of(prior) if prior else None
    by_outcome: dict[str, str | None] = {}
    change = 0.0
    for outcome in sorted(predicted, key=_outcome_key):
        probability = predicted[outcome]
        after = action_of(_posterior(member0, prior, outcome))
        by_outcome[_outcome_key(outcome)] = after
        if probability > 0 and after != current:
            change += probability
    return {
        "emission_alphabet": sorted(_outcome_key(outcome) for outcome in predicted),
        "predicted_outcomes": {
            _outcome_key(outcome): round(float(probability), _ROUND_DIGITS)
            for outcome, probability in sorted(predicted.items(), key=lambda pair: _outcome_key(pair[0]))
        },
        "prior": {label: round(float(value), _ROUND_DIGITS) for label, value in sorted(prior.items())},
        "likelihood": {
            label: {
                _outcome_key(outcome): round(float(probability), _ROUND_DIGITS)
                for outcome, probability in sorted(member0.get(label, {}).items(), key=lambda pair: _outcome_key(pair[0]))
            }
            for label in sorted(prior)
        },
        "current_action": current,
        "action_by_emission": by_outcome,
        "action_proxy": action_proxy,
        "eig_nats": round(float(eig_nats), _ROUND_DIGITS),
        "p_action_change": round(min(max(change, 0.0), 1.0), _ROUND_DIGITS),
    }


def value_candidates(
    ctx: VoiContext,
    site: str,
    candidates: Sequence[Candidate],
    *,
    prior: Mapping[str, float],
    learning_object_id: str | None,
    former_cap: Mapping[str, Any],
    context: Mapping[str, Any] | None = None,
    evsi_enabled: bool = True,
) -> SiteDecision:
    """Value each candidate next observation and decide stop or continue.

    ``prior`` is the belief over the learner's rival hypotheses that the
    candidates' members are keyed by. The site continues when at least one
    candidate's value pays for its minutes; the candidates come back ordered
    by robust value per minute (the best first).
    """

    labels = sorted(label for label, value in prior.items() if float(value) > 0)
    prior_n = _normalized(prior, labels)
    # Outcome keys as strings: an adapter's outcomes may be tuples holding None
    # (the follow-up's (score bucket, error type)), which do not sort.
    candidates = [replace(candidate, members=tuple(_keyed(member) for member in candidate.members))
                  for candidate in candidates]
    plausible = sorted(label for label, value in prior_n.items() if value >= ctx.plausible_threshold)
    label_actions = ctx.label_actions(prior_n) if (evsi_enabled and prior_n) else None
    loss_table = ctx.loss_table(label_actions) if label_actions else None
    at_stake = (
        loss_table is not None
        and label_actions is not None
        and len({label_actions[label] for label in plausible if label in label_actions}) >= 2
    )

    # The decision value where a next action is at stake (rank_feasible).
    rank: EV.RankResult | None = None
    evsi_by_ref: dict[str, EV.RankedCandidate] = {}
    excluded_refs: set[str] = set()
    evaluable = [candidate for candidate in candidates if candidate.members]
    if at_stake and evaluable:
        assert loss_table is not None
        diagnostic = [
            EV.DiagnosticCandidate(
                ref=candidate.ref,
                members=tuple(
                    {label: dict(member.get(label, {})) for label in prior_n if label in member}
                    for member in candidate.members
                ),
                prior=prior_n,
                expected_minutes=float(candidate.minutes.minutes),
            )
            for candidate in evaluable
        ]
        rank = EV.rank_feasible(diagnostic, loss_table)
        evsi_by_ref = {ranked.ref: ranked for ranked in rank.ranked}
        excluded_refs = {str(entry.get("ref")) for entry in rank.excluded}

    values: list[CandidateValue] = []
    for candidate in candidates:
        members = candidate.members
        member_eigs = [expected_information_gain(member, prior_n) for member in members] if prior_n else []
        member_eig = member_eigs[0] if member_eigs else 0.0
        member_eig_robust = robust_quantile(member_eigs, ROBUST_QUANTILE) if len(member_eigs) > 1 else member_eig
        scale = max(float(candidate.eig_scale), 0.0)
        extra = max(float(candidate.extra_eig_nats), 0.0)
        eig_point = scale * member_eig + extra
        eig_robust = scale * member_eig_robust + extra
        cost = LAMBDA_TIME * float(candidate.minutes.minutes) + BURDEN_COST
        ranked = evsi_by_ref.get(candidate.ref)
        value_uncertain = False
        ucb: float | None = None
        if ranked is not None and rank is not None and rank.verdict != "abstain":
            method = METHOD_ROBUST_EVSI
            point, robust, ucb = ranked.evsi.point, ranked.evsi.lcb, ranked.evsi.ucb
            threshold = ranked.stop_threshold
            continues = rank.verdict == "measure" and robust > threshold
            reason = REASON_EVSI_CLEARS if continues else (
                REASON_EVSI_BELOW if rank.verdict == "measure" else str(rank.reason)
            )
            cost = threshold
        else:
            method = METHOD_EIG_VALUE
            point = VALUE_PER_NAT_MINUTES * eig_point
            robust = VALUE_PER_NAT_MINUTES * eig_robust
            continues = robust > cost
            reason = REASON_EIG_CLEARS if continues else REASON_EIG_BELOW
            if at_stake and (rank is not None and (rank.verdict == "abstain" or candidate.ref in excluded_refs)):
                # rank_feasible could not value it robustly: EIG-per-minute with
                # the same stop, labelled as such (reader spec §9.3 item 3).
                value_uncertain = True
                reason = f"{reason}:evsi_{'excluded' if candidate.ref in excluded_refs else rank.reason}"
        forecast = (
            _forecast(
                members[0], _normalized(prior_n, [label for label in prior_n if label in members[0]]),
                eig_nats=eig_point,
                label_actions=label_actions if at_stake else None,
                loss_table=loss_table if at_stake else None,
            )
            if members and prior_n
            else {"eig_nats": round(eig_point, _ROUND_DIGITS), "predicted_outcomes": dict(candidate.detail.get("predicted_outcomes", {}) or {}),
                  "action_proxy": None, "p_action_change": None}
        )
        values.append(
            CandidateValue(
                ref=candidate.ref,
                decision=CONTINUE if continues else STOP,
                reason=reason,
                method=method,
                value_uncertain=value_uncertain,
                eig_nats=eig_point,
                eig_robust_nats=eig_robust,
                member_eig_nats=member_eig,
                value_point_minutes=float(point),
                value_robust_minutes=float(robust),
                value_ucb_minutes=None if ucb is None else float(ucb),
                cost_minutes=float(cost),
                minutes=candidate.minutes,
                forecast=forecast,
                detail=dict(candidate.detail),
            )
        )
    values.sort(key=lambda value: (-value.value_per_minute, value.ref))
    continuing = [value for value in values if value.continues]
    decision = CONTINUE if continuing else STOP
    if continuing:
        reason = continuing[0].reason
    elif values:
        reason = values[0].reason
    else:
        reason = "no_candidate"
    best_minutes = values[0].minutes if values else MinutesEstimate(AL.DEFAULT_INTERVENTION_MINUTES, "heuristic_default")
    method = values[0].method if values else METHOD_EIG_VALUE
    rank_body: dict[str, Any] | None = None
    if rank is not None:
        rank_body = {
            "verdict": rank.verdict,
            "reason": rank.reason,
            "best_ref": rank.best_ref,
            "stress_winner_flipped": rank.stress_winner_flipped,
            "excluded": [dict(entry) for entry in rank.excluded],
        }
    site_context = {
        "decision_at_stake": bool(at_stake),
        "plausible_hypotheses": plausible,
        "label_actions": dict(sorted((label_actions or {}).items())) if at_stake else None,
        "loss_table_hash": loss_table.table_hash if (at_stake and loss_table is not None) else None,
        "loss_durations": ctx.duration_sources((label_actions or {}).values()) if at_stake else None,
        **dict(context or {}),
    }
    return SiteDecision(
        site=site,
        learning_object_id=learning_object_id,
        decision=decision,
        reason=reason,
        candidates=tuple(values),
        former_cap=dict(former_cap),
        rank=rank_body,
        context=site_context,
        parameters=heuristic_parameters(best_minutes, method=method, evsi_used=bool(at_stake)),
    )


def former_cap(site: str, *, value: int, count: int) -> dict[str, Any]:
    """The replaced cap's counterfactual: would it have bound at this decision?"""

    return {
        "name": FORMER_CAPS[site],
        "value": int(value),
        "count": int(count),
        # A cap of 0 meant "never" for teach-back and project probes and
        # "unlimited" for the probe session cap (``cap > 0`` guarded it).
        "would_bind": (int(count) >= int(value)) if (int(value) > 0 or site != SITE_PROBE_EPISODE) else False,
    }


def information_candidate(
    ref: str,
    *,
    eig_nats: float,
    minutes: MinutesEstimate,
    predicted_correct: float | None = None,
    detail: Mapping[str, Any] | None = None,
) -> Candidate:
    """A candidate valued only through an adapter's EIG (no hypothesis members).

    Teach-back and project probes have no locked hypothesis set: the selection
    reward's ``probe_eig_total`` (the existing LO-mastery and facet-recall
    entropy reduction, discounted for familiarity) is their information, and
    the reward's predicted correctness is their predicted outcome distribution.
    """

    body = dict(detail or {})
    if predicted_correct is not None and math.isfinite(float(predicted_correct)):
        p = min(max(float(predicted_correct), 0.0), 1.0)
        body["predicted_outcomes"] = {"correct": round(p, _ROUND_DIGITS), "incorrect": round(1.0 - p, _ROUND_DIGITS)}
    return Candidate(ref=ref, minutes=minutes, extra_eig_nats=max(float(eig_nats), 0.0), detail=body)


def label_conditionals(
    conditionals: Mapping[str, Mapping[Any, float]],
    slot_map: Mapping[str, str],
    labels: Iterable[str],
) -> dict[str, dict[Any, float]]:
    """``{label: P(E | slot(label))}``: a card's slot rows keyed by episode label."""

    out: dict[str, dict[Any, float]] = {}
    for label in labels:
        slot = slot_map.get(label)
        if slot is None or slot not in conditionals:
            continue
        out[label] = {outcome: float(probability) for outcome, probability in conditionals[slot].items()}
    return out


# ---------------------------------------------------------------------------
# Sites
# ---------------------------------------------------------------------------


def probe_episode_decision(
    ctx: VoiContext,
    episode: Any,
    eligible: Sequence[Any],
    posterior: Mapping[str, float],
    *,
    session_id: str | None,
    familiarity: Mapping[str, float] | None = None,
) -> SiteDecision:
    """(a) Does this episode's next observation pay for its minutes?

    Each eligible instrument is valued over the episode's locked hypotheses
    with its composed ``P(E | H)``: the episode's pinned robust ensemble when
    it has one (the credible set), the point conditionals otherwise. The
    former cap's counterfactual counts the session's qualifying observations.
    """

    from learnloop.diagnosis.probe_families import instrument_conditionals

    channel = None
    if getattr(episode, "calibration_model_hash", None) is not None:
        from learnloop.diagnosis.probe_robust import load_pinned_channel

        channel = load_pinned_channel(ctx.repository, episode.calibration_model_hash)
    belief = {label: float(value) for label, value in posterior.items()}
    candidates: list[Candidate] = []
    for entry in eligible:
        if channel is not None:
            from learnloop.diagnosis.probe_robust import instrument_ensemble

            ensemble, _dch = instrument_ensemble(
                channel, entry.instrument, entry.slot_map, belief, episode_id=episode.id
            )
            members: tuple[Mapping[str, Mapping[Any, float]], ...] = tuple(ensemble.members)
        else:
            members = (label_conditionals(instrument_conditionals(entry.instrument), entry.slot_map, belief),)
        minutes = ctx.item_minutes(
            entry.item, authored_minutes=float(entry.instrument.expected_seconds) / 60.0
        )
        candidates.append(
            Candidate(
                ref=str(entry.item.id),
                minutes=minutes,
                members=members,
                eig_scale=float((familiarity or {}).get(entry.item.id, 1.0)),
                detail={
                    "hypothesis_eig_nats": round(float(entry.expected_information_gain), _ROUND_DIGITS),
                    "predictive_eig_nats": round(float(entry.predictive_eig), _ROUND_DIGITS),
                    "selection_objective": entry.selection_objective,
                    "credible_set": "pinned_channel_ensemble" if channel is not None else "point",
                },
            )
        )
    episode_config = ctx.vault.config.probe.episode
    cap = int(episode_config.session_qualifying_observation_cap)
    count = (
        int(ctx.repository.qualifying_probe_observation_count_for_session(session_id))
        if session_id is not None
        else 0
    )
    return value_candidates(
        ctx,
        SITE_PROBE_EPISODE,
        candidates,
        prior=belief,
        learning_object_id=str(episode.learning_object_id),
        former_cap=former_cap(SITE_PROBE_EPISODE, value=cap, count=count),
        context={"episode_id": str(episode.id), "session_id": session_id},
    )


def adapter_information_decision(
    ctx: VoiContext,
    site: str,
    *,
    ref: str,
    learning_object_id: str | None,
    eig_nats: float,
    minutes: MinutesEstimate,
    predicted_correct: float | None,
    cap_value: int,
    cap_count: int,
    context: Mapping[str, Any] | None = None,
    detail: Mapping[str, Any] | None = None,
) -> SiteDecision:
    """(c)/(d) A candidate whose information comes from one adapter's EIG.

    No hypothesis set is locked for a teach-back or a project probe, so no
    next-action decision is at stake: the robust EIG (the adapter's, already
    discounted for familiarity) converted to minutes must exceed the minutes.
    """

    candidate = information_candidate(
        ref, eig_nats=eig_nats, minutes=minutes, predicted_correct=predicted_correct, detail=detail
    )
    return value_candidates(
        ctx,
        site,
        [candidate],
        prior={},
        learning_object_id=learning_object_id,
        former_cap=former_cap(site, value=cap_value, count=cap_count),
        context=context,
        evsi_enabled=False,
    )


__all__ = [
    "CONTINUE",
    "VOI_STOPPING_VERSIONS",
    "adapter_information_decision",
    "probe_episode_decision",
    "Candidate",
    "CandidateValue",
    "FORECAST_VERSION",
    "FORMER_CAPS",
    "METHOD_EIG_VALUE",
    "METHOD_ROBUST_EVSI",
    "MinutesEstimate",
    "SITES",
    "SITE_FOLLOWUP",
    "SITE_PROBE_EPISODE",
    "SITE_PROJECT_PROBE",
    "SITE_TEACH_BACK",
    "STOP",
    "SiteDecision",
    "VoiContext",
    "former_cap",
    "heuristic_parameters",
    "information_candidate",
    "label_conditionals",
    "probe_lane_holds_out_pending",
    "probe_lane_reads_diagnosis",
    "value_candidates",
    "voi_stopping_active",
]
