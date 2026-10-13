"""mvp-0.21 Part 1: four count caps lifted onto value of information.

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
                        observation_cap`` (4 per session) and       episode, while its value pays;
                        ``probe.episode.maximum_observations``      then the block closes and the
                        (4 per episode)                             episode completes with
                                                                    ``value_of_information_stop``
``followup_             ``scheduler.followup.max_interventions_     every intervention on an LO,
intervention``          per_lo_per_session`` (1)                    the first included: the whole
                                                                    eligible slate is valued and
                                                                    the best that pays is queued
``teach_back``          ``teach_back.session_cap`` (1 per queue)    every teach-back, greedily,
                                                                    each conditional on those
                                                                    already kept
``project_probe``       ``plan.project_probes_max_per_day`` (4)     every due project probe,
                                                                    greedily and conditionally,
                                                                    in that order
======================  ==========================================  ==========================

**The value of the next observation** is computed with the machinery that
already values probes, never a new constant:

* **Information** (EIG, nats) over the learner's rival hypotheses through the
  existing adapters: a probe instrument's composed ``P(E | H)``
  (``probe_families.instrument_conditionals``, or the episode's pinned robust
  ensemble), the follow-up slate's facet and misconception EIG, the selection
  reward's ``probe_eig_total`` for a teach-back or a project probe. The robust
  EIG is the ensemble's lower quantile (``voi_stopping.robust_quantile``)
  where a credible set exists, the point EIG otherwise.
* **Decision value** (robust EVSI, minutes) where a next-action decision is
  at stake: the hypotheses' triage routes (``failure_triage_routes``) give
  each hypothesis its effective repair, a misconception's repair targets that
  misconception, and ``action_loss.build_loss_table`` prices a wrong repair in
  wasted learner-minutes. A decision is at stake when the hypotheses with
  posterior mass route to two or more repairs through a complete loss table
  (the plausibility cutoff, ``probe.episode.action_equivalence_plausible_
  threshold``, only describes the belief in the receipt: EVSI weighs the whole
  posterior, so growing certainty shrinks the decision value continuously).
  ``evsi.rank_feasible`` then values and stops: continue while the robust
  EVSI's lower bound exceeds ``lambda_time * minutes + burden``.
* **Otherwise** (no complete loss table, a single repair across the whole
  posterior, or ``rank_feasible`` abstaining on a flip or excluding an input)
  the robust EIG is converted to minutes
  with ``robust_composition.VALUE_PER_NAT_MINUTES``, exactly as
  ``robust_composition.evaluate_selection``'s stop rule does, and the same
  stop applies. An abstention's fallback is labelled ``value_uncertain``.
* **Minutes** are the learner's own: the item's median latency, else the
  practice mode's median shrunk toward the authored estimate, else the
  authored estimate (a probe card's ``expected_seconds``, an item's
  ``expected_minutes``), else ``action_loss.DEFAULT_INTERVENTION_MINUTES``.

lambda_time (1, the minutes numeraire), the burden (0), the nat-to-minutes
scale (60), the +-0.15 stress and the loss model are heuristic decision
parameters (``robust_composition``, ``evsi``, ``action_loss``); every decision
receipt lists them with that label.

**The multi-family EVSI study's changes** (``docs/reviews/evsi-multisim.md``
§6.1, ranks 1 to 3; :class:`VoiSettings`), each behind its own switch at the
study's recommendation, each restoring this successor as it was before the
study at the value in brackets:

* rank 1, ``robust_gate_with_value`` (false; true): the mvp-0.8 robust
  completion gate does not end an episode while value decides it
  (``probe_episodes.robust_gate_applies``); a value stop records the gate's
  verdict as a counterfactual (:func:`with_robust_gate_counterfactual`);
* rank 2, ``lookahead_max_checks`` (3; 1): in a probe episode
  (:data:`LOOKAHEAD_SITES`), where a decision is at stake, ``rank_feasible``
  did not abstain and no single check pays, the best 2-3 ranked checks that
  can all be administered (one per canonical surface group) are valued
  jointly (``evsi.robust_batch_evsi``) and a paying batch continues with the
  site's own choice among it (:func:`_lookahead`);
* rank 3, ``robust_quantile`` (0.25; 0.10): the credible set's lower quantile
  this value gate reads (``rank_feasible``, the robust EIG, the batch); the
  mvp-0.8 paths keep ``robust_composition.ROBUST_QUANTILE`` (0.10).

Receipts label these ``evsi_multisim`` at the study's values. The study's
rank 4 (the measured unresolved cost in the loss table) is wired at the merge
onto main, where it lives, behind ``evsi.measured_loss_enabled`` (off).

**Every stop/continue decision is a forecast**, recorded beside the decision
in a table no rebuild clears (router R1's ``router_decisions`` detail for
Today offers and plan blocks, the probe presentation's selection components,
the episode's completion detail, the follow-up's own
``followup_value_decisions`` receipt, one row per decision): the predicted
outcome distribution, the EIG, the EVSI point and robust value, the predicted
probability of an action change, the parameters with their provenance, the
lookahead's batches when it ran (``lookahead``), and the former caps'
counterfactuals (would they have bound? the robust completion gate's
verdict on a value stop). Where the serving path
commits a different candidate from value's recommendation (router R1's seeded
exploration, a manual follow-up), the receipt names both and carries the
SERVED candidate's complete forecast with how it was chosen. The shape follows
the ``evsi/calibration`` branch's ``voi_forecast_v2`` body so its report can
score these too.

**Several checks chosen together** (teach-backs in one queue, project probes
in one plan) are admitted greedily, each valued conditionally on those
already admitted (:func:`greedy_information_admission`; the hypothesis term
over the expected posterior branches, :class:`HypothesisChannel`), so two
checks that would tell LearnLoop the same thing are not both admitted, while
two that tell independent things are. A check the plan cannot fit is never
admitted, so nothing is conditioned on it.
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
from learnloop.scheduling import unresolved_cost as UC

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

#: The probe episode's own count, lifted with the session cap at the
#: ``probe_episode`` site (reader spec §18 and §20.7 name it with the session
#: cap): stamped on each episode at entry, it ends an episode by count only
#: where the site is off or a calibration session lifts the value rule.
EPISODE_MAXIMUM_CAP = "probe.episode.maximum_observations"

#: A follow-up suppressed because the best eligible candidate's value does not
#: pay for its minutes.
VOI_VALUE_SUPPRESSION = "voi_value_below_minutes_cost"

#: Follow-up suppressions decided by value, not by the trigger's signals. The
#: follow-up gate fitter (``gate_fit``) keeps them out of its trigger-quality
#: labels (silent negatives and manual-override positives alike): a trigger
#: that fired and was then outvalued says nothing about the trigger.
VALUATION_SUPPRESSION_REASONS = frozenset({VOI_VALUE_SUPPRESSION})

CONTINUE = "continue"
STOP = "stop"
METHOD_ROBUST_EVSI = "robust_evsi"
METHOD_EIG_VALUE = "eig_value"
#: A decision the lookahead took: ``robust_evsi_lookahead_<k>``.
METHOD_LOOKAHEAD_PREFIX = "robust_evsi_lookahead_"
#: Where the lookahead acts: the probe episode, the only site the multi-family
#: study simulated (its §7.1). Its §6.2 waits for live ``voi_forecasts``
#: calibration before the lookahead acts at the follow-up and teach-back sites
#: (Codex review of voi-v2, F15); a later rollout there gets its own site
#: control. ``lookahead_max_checks = 1`` still turns it off here.
LOOKAHEAD_SITES: frozenset[str] = frozenset({SITE_PROBE_EPISODE})

#: The loss regime a decision's loss table is built under (rank 4 of the
#: multi-family EVSI study, wired at the merge onto main): the minutes-only
#: table (a wrong repair wastes its minutes plus the delay of the right one),
#: or, with ``evsi.measured_loss_enabled`` (EVSI calibration Part C, off by
#: default), the same table plus the measured minutes an unresolved cause
#: costs later (``scheduling.unresolved_cost``), named as the causal shadow
#: selector names its own measured regime.
LOSS_REGIME_MINUTES = "triage_route_wasted_minutes"
LOSS_REGIME_MEASURED = "route_plus_measured_unresolved_minutes_v1"

#: Reasons a decision names.
REASON_EVSI_CLEARS = "robust_evsi_clears_minutes_cost"
REASON_EVSI_BELOW = "robust_evsi_below_minutes_cost"
REASON_EIG_CLEARS = "eig_value_clears_minutes_cost"
REASON_EIG_BELOW = "eig_value_below_minutes_cost"
#: The lookahead (the multi-family study's rank 2): no single check pays, but
#: the best 2-3 valued jointly do.
REASON_EVSI_BATCH_CLEARS = "robust_evsi_batch_clears_minutes_cost"

#: The mvp-0.8 robust completion gate. While value decides an episode it no
#: longer ends it (the study's rank 1, ``voi_stopping.robust_gate_with_value``
#: off); a value stop's receipt carries its verdict as a counterfactual.
ROBUST_GATE = "probe_episodes._robust_completion_override"
ROBUST_GATE_SWITCH = "voi_stopping.robust_gate_with_value"

#: Where the study's recommended values come from (receipt provenance).
STUDY_PROVENANCE = "evsi_multisim"
STUDY_REFERENCE = "docs/reviews/evsi-multisim.md §6.1"

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
    """mvp-0.21 Part 2: the probe hypothesis lane reads the diagnosis overlay.

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


@dataclass(frozen=True)
class VoiSettings:
    """The multi-family EVSI study's three switches (``[voi_stopping]``,
    ``docs/reviews/evsi-multisim.md`` §6.1 ranks 1-3), read once per decision.

    At their restore values (``robust_gate_with_value = true``,
    ``lookahead_max_checks = 1``, ``robust_quantile = 0.10``) the successor
    decides exactly as it did before the study."""

    robust_gate_with_value: bool
    lookahead_max_checks: int
    robust_quantile: float

    @classmethod
    def from_config(cls, config: Any) -> "VoiSettings":
        from learnloop.config.schema import VoiStoppingConfig

        defaults = VoiStoppingConfig()
        section = getattr(config, "voi_stopping", None)
        return cls(
            robust_gate_with_value=bool(getattr(section, "robust_gate_with_value", defaults.robust_gate_with_value)),
            lookahead_max_checks=max(int(getattr(section, "lookahead_max_checks", defaults.lookahead_max_checks)), 1),
            robust_quantile=float(getattr(section, "robust_quantile", defaults.robust_quantile)),
        )

    def is_study_default(self, name: str) -> bool:
        from learnloop.config.schema import VoiStoppingConfig

        return getattr(self, name) == getattr(VoiStoppingConfig(), name)


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


#: Rank 4's scopes: which of the value rule's hypothesis labels leave a cause
#: whose later cost EVSI calibration Part C prices (``scheduling.unresolved_cost``:
#: a persistent cause, ``learner_state`` or ``unknown``, keeps producing the
#: same error until something else catches it). The labels are the probe
#: hypotheses (``probes.build_hypothesis_set``, ``probe_hypotheses``), not
#: ``causal_hypotheses`` rows, so each is read explicitly:
#:
#: * **no problem** (``mastered``; ``robust_initial_grasp``, whose triage reason
#:   is a memory lapse that spaced review already repairs): nothing is left
#:   unresolved, so never charged;
#: * **a gap the next teaching resolves** (``unfamiliar`` and the partial-schema
#:   templates): Part C's prior is Eedi's excess repeat rate of a
#:   misconception-consistent error over learners taught in between, and its
#:   personal measurement is the recurrence of one misconception's class. A
#:   gap is an absence, not a belief that keeps producing the same wrong
#:   answer: the LO stays in teaching and practice until it is known, so a
#:   wrong first action only delays the right one, a cost the minutes-only
#:   cell already charges (the delay of the effective repair). Not charged;
#: * **a misconception or a confusion** (``misconception:<id>``,
#:   ``confuses_with:<concept>``, triage ``false_belief_or_confusion``): Part
#:   C's own case, a ``learner_state`` cause charged the learner's
#:   recurrence-measured estimate;
#: * **the open set** (``other_or_unknown``) and any label this map does not
#:   know: an ``unknown`` cause, which Part C charges as persistent.
UNRESOLVED_NO_PROBLEM_LABELS = frozenset({"mastered", "robust_initial_grasp"})
UNRESOLVED_GAP_LABELS = frozenset(
    {
        "unfamiliar",
        "surface_only",
        "recall_without_mechanism",
        "procedure_without_selection",
        "schema_without_transfer",
    }
)
SCOPE_NO_PROBLEM = "no_problem"
SCOPE_KNOWLEDGE_GAP = "knowledge_gap"


def unresolved_scope_for_label(label: str) -> tuple[str, str]:
    """``(scope, reason)`` of one hypothesis label for rank 4's loss: a
    persistent scope (``learner_state``, ``unknown``) is charged Part C's
    estimate; ``no_problem`` and ``knowledge_gap`` are not (the reason names
    why on the cell)."""

    if label in UNRESOLVED_NO_PROBLEM_LABELS:
        return SCOPE_NO_PROBLEM, "no_problem_left_unresolved"
    if label in UNRESOLVED_GAP_LABELS:
        return SCOPE_KNOWLEDGE_GAP, "gap_resolved_by_next_teaching"
    if label.startswith(("misconception:", "confuses_with:")):
        return "learner_state", "persistent_misconception"
    return "unknown", "unknown_cause"


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
        self._loss_tables: dict[tuple[Any, ...], AL.LossTable] = {}
        self._settings: VoiSettings | None = None
        self._unresolved: dict[tuple[str, ...], tuple[dict[str, dict[str, Any]], dict[str, Any]]] = {}
        self._unresolved_estimate: UC.UnresolvedCost | None = None

    @property
    def settings(self) -> VoiSettings:
        """The study's switches from the vault's config."""

        if self._settings is None:
            self._settings = VoiSettings.from_config(getattr(self.vault, "config", None))
        return self._settings

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

    # -- the loss regime (rank 4) ---------------------------------------------

    @property
    def measured_loss(self) -> bool:
        """EVSI calibration Part C's switch, ``evsi.measured_loss_enabled`` (off
        by default): the loss table also charges what leaving a cause
        unresolved costs later (the multi-family study's rank 4)."""

        evsi = getattr(getattr(self.vault, "config", None), "evsi", None)
        return bool(getattr(evsi, "measured_loss_enabled", False))

    @property
    def loss_regime(self) -> str:
        return LOSS_REGIME_MEASURED if self.measured_loss else LOSS_REGIME_MINUTES

    def unresolved_minutes(self, labels: Iterable[str]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
        """The decision's per-label unresolved-cost cell entries and the full
        estimate (for the receipt), read once per label set.

        Part C's estimate (``unresolved_cost.estimate_unresolved_cost``: the
        learner's recurrence-measured cost of a persistent cause, shrunk toward
        Eedi's prior) is charged by each label's explicit scope
        (:func:`unresolved_scope_for_label`), never by a ``causal_hypotheses``
        lookup a probe label would miss: a misconception or a confusion is
        charged, a label that means no problem or a gap the next teaching
        resolves is not, and only the open-set label is an unknown cause."""

        key = tuple(sorted(set(labels)))
        if key not in self._unresolved:
            if self._unresolved_estimate is None:
                evsi = getattr(self.vault.config, "evsi", None)
                pseudo_count = float(getattr(evsi, "unresolved_cost_prior_pseudo_count", 5.0))
                self._unresolved_estimate = UC.estimate_unresolved_cost(self.repository, pseudo_count=pseudo_count)
            scopes = {label: unresolved_scope_for_label(label) for label in key}
            per_label = UC.unresolved_minutes_for_scopes(
                self._unresolved_estimate,
                {label: scope for label, (scope, _reason) in scopes.items()},
                reasons={label: reason for label, (_scope, reason) in scopes.items()},
            )
            self._unresolved[key] = (per_label, self._unresolved_estimate.as_dict())
        return self._unresolved[key]

    def unresolved_estimate(self, labels: Iterable[str]) -> dict[str, Any] | None:
        """The measured unresolved cost a decision's table charged, or None in
        the minutes-only regime."""

        if not self.measured_loss:
            return None
        return self.unresolved_minutes(labels)[1]

    def loss_table(self, label_actions: Mapping[str, str]) -> AL.LossTable | None:
        """``action_loss.build_loss_table`` over hypothesis labels (one route per label).

        With ``evsi.measured_loss_enabled`` (rank 4, off by default) the table
        also charges each off-diagonal cell the measured minutes an unresolved
        cause costs (``unresolved_minutes``); off, it is the minutes-only
        table exactly. The cache is keyed on the regime and the charged
        minutes."""

        routes_key = tuple(sorted(label_actions.items()))
        unresolved: dict[str, dict[str, Any]] | None = None
        if self.measured_loss:
            unresolved = self.unresolved_minutes(label for label, _action in routes_key)[0]
        key = (
            routes_key,
            self.loss_regime,
            tuple(sorted((label, float(entry.get("minutes") or 0.0)) for label, entry in (unresolved or {}).items())),
        )
        if key in self._loss_tables:
            return self._loss_tables[key]
        routes = [{"reason": label, "first_intervention": action} for label, action in routes_key]
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
                hypotheses=[label for label, _action in routes_key],
                duration_overrides=overrides,
                unresolved_minutes=unresolved,
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


def _quantile_parameter(settings: VoiSettings) -> dict[str, Any]:
    if settings.is_study_default("robust_quantile"):
        provenance = STUDY_PROVENANCE
        note = f"{STUDY_REFERENCE} rank 3 (0.10 restores robust_composition.ROBUST_QUANTILE)"
    else:
        provenance = "heuristic"
        note = (
            "robust_composition.ROBUST_QUANTILE's value, as before the study; not yet calibrated"
            if settings.robust_quantile == ROBUST_QUANTILE
            else "set in config; not yet calibrated"
        )
    return {"name": "robust_quantile", "value": settings.robust_quantile, "provenance": provenance,
            "source": "voi_stopping.robust_quantile", "note": note}


def _lookahead_parameter(settings: VoiSettings) -> dict[str, Any]:
    default = settings.is_study_default("lookahead_max_checks")
    return {"name": "lookahead_max_checks", "value": settings.lookahead_max_checks,
            "provenance": STUDY_PROVENANCE if default else "heuristic",
            "source": "voi_stopping.lookahead_max_checks",
            "note": f"{STUDY_REFERENCE} rank 2 (1 turns the lookahead off)" if default else "set in config"}


def heuristic_parameters(
    minutes: MinutesEstimate,
    *,
    method: str,
    evsi_used: bool,
    settings: VoiSettings | None = None,
    lookahead_site: bool = True,
    loss_regime: str = LOSS_REGIME_MINUTES,
    unresolved_cost: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Every number the decision ran on, with its provenance: heuristic but the
    minutes, and the multi-family study's recommendations (``evsi_multisim``)
    where its switches are at their defaults. ``lookahead_max_checks`` is
    listed only where the lookahead can act (``lookahead_site``,
    :data:`LOOKAHEAD_SITES`). Where a decision is at stake the loss model
    names its regime (rank 4): the minutes-only table, or the measured
    unresolved cost on top (``unresolved_cost``, the estimate it charged)."""

    settings = settings or VoiSettings.from_config(None)
    params = [
        {"name": "lambda_time", "value": LAMBDA_TIME, "provenance": "heuristic",
         "source": "robust_composition.LAMBDA_TIME", "note": "minutes numeraire, fixed at 1 (U-023); not yet calibrated"},
        {"name": "burden_cost_minutes", "value": BURDEN_COST, "provenance": "heuristic",
         "source": "robust_composition.BURDEN_COST", "note": "not yet calibrated"},
        {"name": "value_per_nat_minutes", "value": VALUE_PER_NAT_MINUTES, "provenance": "heuristic",
         "source": "robust_composition.VALUE_PER_NAT_MINUTES", "note": "nat-to-minutes scale; not yet calibrated"},
        _quantile_parameter(settings),
        {"name": "expected_minutes", "value": round(float(minutes.minutes), 6), "provenance": minutes.provenance,
         "source": minutes.source, "sample_count": int(minutes.sample_count)},
    ]
    if evsi_used:
        params.extend(
            [
                {"name": "perturbation_delta", "value": EV.PERTURBATION_DELTA, "provenance": "heuristic",
                 "source": "evsi.PERTURBATION_DELTA", "note": "+-0.15 stress; not yet calibrated"},
                {"name": "loss_model", "value": loss_regime, "provenance": "heuristic",
                 "source": "action_loss.build_loss_table",
                 "note": "a wrong repair wastes its minutes plus the delay of the right one; not yet calibrated"
                 if loss_regime == LOSS_REGIME_MINUTES else
                 "a wrong repair wastes its minutes plus the delay of the right one plus the measured minutes "
                 "an unresolved cause costs later (evsi.measured_loss_enabled, EVSI calibration Part C)"},
            ]
        )
        if unresolved_cost is not None:
            params.append(
                {"name": "unresolved_minutes", "value": unresolved_cost.get("minutes"),
                 "provenance": str(unresolved_cost.get("provenance") or "heuristic"),
                 "source": str(unresolved_cost.get("source") or "unresolved_cost"),
                 "note": "scheduling.unresolved_cost (multi-family study rank 4); charged on every off-diagonal "
                         "cell of a misconception, a confusion or an unknown cause, never of a label that means "
                         "no problem or a gap the next teaching resolves (voi_stopping.unresolved_scope_for_label)",
                 "estimate": dict(unresolved_cost)}
            )
        if lookahead_site:
            params.append(_lookahead_parameter(settings))
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
    ``infeasible_reason`` marks a candidate the site cannot serve within its
    constraints (a project probe that does not fit the plan's minutes): it is
    valued for its receipt but never continues. ``surface_group`` is the
    observation's canonical surface group (``surface_group_id``): once one
    check of a group is answered the exposure rule excludes the others, so a
    lookahead batch holds at most one check per group (Codex review of voi-v2,
    F13). None: a surface of its own.
    """

    ref: str
    minutes: MinutesEstimate
    members: tuple[Mapping[str, Mapping[Any, float]], ...] = ()
    eig_scale: float = 1.0
    extra_eig_nats: float = 0.0
    detail: Mapping[str, Any] = field(default_factory=dict)
    infeasible_reason: str | None = None
    surface_group: str | None = None


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
    #: The lookahead's forecast when it ran (no single check paid with a
    #: decision at stake): the batches it valued and whether one paid.
    lookahead: dict[str, Any] | None = None

    def value_for(self, ref: str) -> CandidateValue | None:
        return next((value for value in self.candidates if value.ref == ref), None)

    @property
    def best(self) -> CandidateValue | None:
        return self.candidates[0] if self.candidates else None

    @property
    def chosen(self) -> CandidateValue | None:
        """The recommended next observation: the first candidate (in robust
        value-per-minute order) whose value pays for its minutes, or None."""

        return next((value for value in self.candidates if value.continues), None)

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

    def as_dict(
        self,
        *,
        served_ref: str | None = None,
        served_by: Mapping[str, Any] | None = None,
        subject_ref: str | None = None,
    ) -> dict[str, Any]:
        """The logged decision.

        ``recommended_ref`` is value's own pick. ``served_ref`` (given once the
        serving path has chosen, e.g. after router R1's seeded exploration) is
        the observation actually committed; ``chosen_ref`` names it, and
        ``served`` carries ITS complete forecast (emission alphabet, predicted
        outcomes, likelihood rows), so calibration scores the answer against
        the forecast of the item that was asked, with ``served_by`` saying how
        it was chosen (the exploration propensity). ``subject_ref`` adds one
        candidate's own full valuation (``subject``), for a receipt kept per
        candidate (a plan's due project probe).
        """

        best = self.best
        recommended = self.chosen if self.decision == CONTINUE else None
        body: dict[str, Any] = {
            "forecast_version": FORECAST_VERSION,
            "site": self.site,
            "learning_object_id": self.learning_object_id,
            "decision": self.decision,
            "reason": self.reason,
            "recommended_ref": recommended.ref if recommended is not None else None,
            "chosen_ref": served_ref if served_ref is not None else (
                recommended.ref if recommended is not None else None
            ),
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
        if self.lookahead is not None:
            body["lookahead"] = dict(self.lookahead)
        if served_ref is not None:
            served = self.value_for(served_ref)
            body["served_ref"] = served_ref
            body["served_is_recommended"] = recommended is not None and recommended.ref == served_ref
            body["served"] = served.as_dict() if served is not None else None
            body["served_by"] = dict(served_by) if served_by else {"mechanism": "value_recommendation"}
        if subject_ref is not None:
            subject = self.value_for(subject_ref)
            body["subject_ref"] = subject_ref
            body["subject"] = subject.as_dict() if subject is not None else None
        return body


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
    by robust value per minute (the best first). ``candidates`` come in the
    site's own order (its first is the check it would serve, e.g. the probe
    episode's highest predictive information rate), which the lookahead's
    serving rule reads.

    The multi-family study's switches (:class:`VoiSettings`): the credible
    set's lower ``robust_quantile`` is the robust value (``rank_feasible``'s
    EVSI, the robust EIG, a batch's value); and at a site in
    :data:`LOOKAHEAD_SITES` (the probe episode), when a decision is at stake,
    ``rank_feasible`` did not abstain and no single candidate pays, the best
    2 to ``lookahead_max_checks`` ranked candidates that can be administered
    together are valued jointly (:func:`_lookahead`).
    """

    settings = ctx.settings
    quantile = settings.robust_quantile
    labels = sorted(label for label, value in prior.items() if float(value) > 0)
    prior_n = _normalized(prior, labels)
    # Outcome keys as strings: an adapter's outcomes may be tuples holding None
    # (the follow-up's (score bucket, error type)), which do not sort.
    candidates = [replace(candidate, members=tuple(_keyed(member) for member in candidate.members))
                  for candidate in candidates]
    plausible = sorted(label for label, value in prior_n.items() if value >= ctx.plausible_threshold)
    label_actions = ctx.label_actions(prior_n) if (evsi_enabled and prior_n) else None
    loss_table = ctx.loss_table(label_actions) if label_actions else None
    # A decision is at stake when the complete loss table routes the belief's
    # support (every hypothesis with mass) to two or more repairs. EVSI then
    # decides across the whole posterior, so growing certainty shrinks the
    # decision value continuously to a stop. The plausibility cutoff only
    # describes the belief in the receipt: gating on it switched a near-sure
    # belief onto the EIG objective and restarted measurement (review F6).
    at_stake = (
        loss_table is not None
        and label_actions is not None
        and len({label_actions[label] for label in prior_n if label in label_actions}) >= 2
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
        rank = EV.rank_feasible(diagnostic, loss_table, quantile=quantile)
        evsi_by_ref = {ranked.ref: ranked for ranked in rank.ranked}
        excluded_refs = {str(entry.get("ref")) for entry in rank.excluded}

    values: list[CandidateValue] = []
    for candidate in candidates:
        members = candidate.members
        member_eigs = [expected_information_gain(member, prior_n) for member in members] if prior_n else []
        member_eig = member_eigs[0] if member_eigs else 0.0
        member_eig_robust = robust_quantile(member_eigs, quantile) if len(member_eigs) > 1 else member_eig
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
        if candidate.infeasible_reason:
            # Valued for the receipt, never admitted: it cannot be served
            # within the site's constraints (review F10).
            continues = False
            reason = str(candidate.infeasible_reason)
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
    lookahead: dict[str, Any] | None = None
    lookahead_site = site in LOOKAHEAD_SITES
    if (
        lookahead_site
        and settings.lookahead_max_checks >= 2
        and at_stake
        and rank is not None
        and rank.verdict != "abstain"
        and loss_table is not None
        and not any(value.continues for value in values)
    ):
        values, lookahead = _lookahead(values, candidates, diagnostic, rank, loss_table, settings)
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
    unresolved_cost = ctx.unresolved_estimate(label_actions or {}) if at_stake else None
    if at_stake:
        # Rank 4: which loss the EVSI above was priced in.
        site_context["loss_regime"] = ctx.loss_regime
        if unresolved_cost is not None:
            site_context["unresolved_cost"] = unresolved_cost
            site_context["unresolved_scopes"] = {
                label: unresolved_scope_for_label(label)[0] for label in sorted(label_actions or {})
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
        parameters=heuristic_parameters(
            best_minutes, method=method, evsi_used=bool(at_stake), settings=settings, lookahead_site=lookahead_site,
            loss_regime=ctx.loss_regime, unresolved_cost=unresolved_cost,
        ),
        lookahead=lookahead,
    )


def _lookahead(
    values: list[CandidateValue],
    candidates: Sequence[Candidate],
    diagnostic: Sequence[EV.DiagnosticCandidate],
    rank: EV.RankResult,
    loss_table: AL.LossTable,
    settings: VoiSettings,
) -> tuple[list[CandidateValue], dict[str, Any]]:
    """The multi-family study's lookahead (rank 2, ``evsi_multisim`` §6.1;
    ``evsi_calibration/policies.py:_paying_batch`` and ``decide_package``).

    No single check pays, a decision is at stake and ``rank_feasible`` did not
    abstain: the top ``k`` of its ranking (k = 2 up to
    ``lookahead_max_checks``, the smallest first) are valued jointly
    (:func:`evsi.robust_batch_evsi`). A batch must be administrable as a
    whole: the ranking keeps one check per canonical surface group (its best
    ranked), because answering one check of a group excludes the others from
    the episode (Codex review of voi-v2, F13); the dropped ones are recorded
    (``skipped_same_surface``). The first batch whose robust value
    exceeds its checks' summed minutes cost pays, and so every check in it
    does; the site serves its own choice among them (its first candidate when
    that one is in the batch, else the batch's top-ranked check), and only that
    one continues (method ``robust_evsi_lookahead_<k>``, reason
    ``robust_evsi_batch_clears_minutes_cost``, the batch's value and cost; its
    own single-check value is kept in ``detail.single_check``). The returned
    body is the batch's forecast, recorded whether or not a batch paid.
    """

    feasible = {candidate.ref for candidate in candidates if candidate.members and not candidate.infeasible_reason}
    groups = {candidate.ref: candidate.surface_group for candidate in candidates}
    ranked: list[str] = []
    skipped: list[str] = []
    seen_groups: set[str] = set()
    for entry in rank.ranked:
        if entry.ref not in feasible:
            continue
        group = groups.get(entry.ref)
        if group is not None and group in seen_groups:
            # Mutually exclusive with a better-ranked check: never in one batch.
            skipped.append(entry.ref)
            continue
        if group is not None:
            seen_groups.add(group)
        ranked.append(entry.ref)
    by_ref = {candidate.ref: candidate for candidate in diagnostic}
    body: dict[str, Any] = {
        "max_checks": settings.lookahead_max_checks,
        "quantile": settings.robust_quantile,
        "ranking": ranked[:MAX_RECORDED_CANDIDATES],
        "skipped_same_surface": skipped[:MAX_RECORDED_CANDIDATES],
        "paid": False,
        "tried": [],
    }
    found: EV.BatchEVSI | None = None
    for k in range(2, min(settings.lookahead_max_checks, len(ranked)) + 1):
        refs = ranked[:k]
        try:
            batch = EV.robust_batch_evsi(
                [by_ref[ref] for ref in refs], loss_table, k=k, quantile=settings.robust_quantile
            )
        except EV.EVSIInputError as error:
            body["tried"].append({"k": k, "refs": list(refs), "excluded": error.reason})
            break
        body["tried"].append(
            {"k": k, "refs": list(refs), "evsi_point_minutes": round(batch.point, 6),
             "evsi_robust_minutes": round(batch.lcb, 6), "cost_minutes": round(batch.stop_threshold, 6)}
        )
        if batch.pays:
            found = batch
            break
    if found is None:
        return values, body
    site_choice = next((candidate.ref for candidate in candidates if candidate.ref in feasible), None)
    if site_choice in found.refs:
        chosen_ref, rule = str(site_choice), "site_choice_in_batch"
    else:
        chosen_ref, rule = found.refs[0], "batch_top_ranked"
    method = f"{METHOD_LOOKAHEAD_PREFIX}{found.k}"
    body.update(
        {
            "paid": True,
            "k": found.k,
            "batch": list(found.refs),
            "surface_groups": {ref: groups.get(ref) for ref in found.refs},
            "method": method,
            "chosen_ref": chosen_ref,
            "chosen_rule": rule,
            "site_choice_ref": site_choice,
            "evsi_point_minutes": round(found.point, 6),
            "evsi_robust_minutes": round(found.lcb, 6),
            "evsi_ucb_minutes": round(found.ucb, 6),
            "cost_minutes": round(found.stop_threshold, 6),
            "member_count": found.member_count,
            "current_action": found.current_action,
            "p_action_change": round(found.p_action_change, _ROUND_DIGITS),
            "emission_count": found.emission_count,
        }
    )
    out: list[CandidateValue] = []
    for value in values:
        if value.ref not in found.refs:
            out.append(value)
            continue
        detail = {**dict(value.detail), "lookahead_batch": list(found.refs)}
        if value.ref != chosen_ref:
            out.append(replace(value, detail=detail))
            continue
        detail["single_check"] = {
            "method": value.method,
            "reason": value.reason,
            "evsi_point_minutes": round(value.value_point_minutes, 6),
            "evsi_robust_minutes": round(value.value_robust_minutes, 6),
            "cost_minutes": round(value.cost_minutes, 6),
        }
        out.append(
            replace(
                value,
                decision=CONTINUE,
                reason=REASON_EVSI_BATCH_CLEARS,
                method=method,
                value_point_minutes=float(found.point),
                value_robust_minutes=float(found.lcb),
                value_ucb_minutes=float(found.ucb),
                cost_minutes=float(found.stop_threshold),
                detail=detail,
            )
        )
    return out, body


def with_robust_gate_counterfactual(decision: SiteDecision, verdict: str | None) -> SiteDecision:
    """The value decision with the robust completion gate's verdict as a
    counterfactual on its former-cap receipt (the study's rank 1): the gate
    did not run because value decides; ``verdict`` is what it would have said
    (``couldnt_reliably_distinguish``) or None."""

    cap = dict(decision.former_cap)
    cap["robust_completion_gate"] = {
        "name": ROBUST_GATE,
        "switch": ROBUST_GATE_SWITCH,
        "verdict": verdict,
        "would_bind": verdict is not None,
    }
    cap["would_bind"] = bool(cap.get("would_bind")) or verdict is not None
    return replace(decision, former_cap=cap)


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
    infeasible_reason: str | None = None,
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
    return Candidate(
        ref=ref,
        minutes=minutes,
        extra_eig_nats=max(float(eig_nats), 0.0),
        detail=body,
        infeasible_reason=infeasible_reason,
    )


# ---------------------------------------------------------------------------
# Greedy conditional valuation of several checks chosen together
# ---------------------------------------------------------------------------

#: The selection reward's variance floor (``selection_rewards.
#: probe_information_gain_components``), repeated so the conditional terms below
#: reproduce its numbers exactly for the first pick.
_VARIANCE_FLOOR = 1e-6
#: The facet-variance prior that reward reads for a facet with no state.
_DEFAULT_FACET_VARIANCE = 0.25
#: Relative tolerance for "the decomposition reproduces the logged total".
_RECONSTRUCTION_TOLERANCE = 1e-6
#: Decimal places two expected posteriors must share to be one belief branch.
_BRANCH_MERGE_DIGITS = 12
#: Belief branches kept per hypothesis variable before coarser merging. A
#: bound on arithmetic, never on checks: past it, posteriors are merged at
#: fewer decimals (each merge keeps the branches' mean) and the receipt says so.
_MAX_BELIEF_BRANCHES = 4096
#: The coarser decimal places tried, in order, once the bound is passed.
_COARSE_MERGE_DIGITS = (9, 6, 4, 3, 2, 1)

#: A check the plan cannot fit (review F10): it is never admitted, and never
#: conditioned on.
REASON_DOES_NOT_FIT = "does_not_fit_plan_minutes"
#: A check the plan already holds (planned, not yet answered) when it values
#: the rest again (final verify F10): the others are conditioned on it, and its
#: minutes are not charged again.
REASON_ALREADY_PLANNED = "already_planned"
#: A check a plan holds because the learner asked for it (L3: requests first,
#: Codex review of voi-v2 F14), not by its value: it is charged once as a
#: request, and the other checks are valued given it.
REASON_LEARNER_REQUEST = "learner_request"
#: A due check a plan refresh cannot hold (skipped or answered in this plan,
#: or outside the plan's frozen universe; Codex review of voi-v2 F10): never
#: valued, never conditioned on, so it cannot suppress one the plan can hold.
REASON_NOT_IN_PLAN = "not_available_to_this_plan"

_Branches = tuple[tuple[float, tuple[tuple[str, float], ...]], ...]


def _clamp01(value: float) -> float:
    return min(max(float(value), 0.0), 1.0)


def _merge_branches(branches: Iterable[tuple[float, Mapping[str, float]]], digits: int) -> list[tuple[float, dict[str, float]]]:
    """Branches whose posteriors agree to ``digits`` places become one, with
    their total weight and their weighted mean posterior."""

    merged: dict[tuple[tuple[str, float], ...], list[Any]] = {}
    for weight, posterior in branches:
        if weight <= 0:
            continue
        key = tuple((label, round(float(posterior[label]), digits)) for label in sorted(posterior))
        slot = merged.get(key)
        if slot is None:
            merged[key] = [float(weight), {label: float(weight) * float(value) for label, value in posterior.items()}]
        else:
            slot[0] += float(weight)
            for label, value in posterior.items():
                slot[1][label] = slot[1].get(label, 0.0) + float(weight) * float(value)
    return [
        (total, {label: mass / total for label, mass in sums.items()})
        for total, sums in merged.values()
    ]


def _entropy(distribution: Mapping[Any, float]) -> float:
    return -sum(p * math.log(p) for p in distribution.values() if p > 0)


def _targets_predictive_entropy(
    targets: Sequence[Mapping[str, Mapping[str, float]]], belief: Mapping[str, float]
) -> float:
    """Summed predictive outcome entropy of the held-out targets under
    ``belief`` (each target over the labels it has a row for, renormalized)."""

    total = 0.0
    for rows in targets:
        predictive: dict[str, float] = {}
        mass = 0.0
        for label, weight in belief.items():
            row = rows.get(label)
            if row is None:
                continue
            mass += weight
            for outcome, probability in row.items():
                predictive[outcome] = predictive.get(outcome, 0.0) + weight * float(probability)
        if mass <= 0:
            continue
        total += _entropy({outcome: value / mass for outcome, value in predictive.items()})
    return total


def predictive_information(
    likelihood: Mapping[str, Mapping[str, float]],
    targets: Sequence[Mapping[str, Mapping[str, float]]],
    posterior: Mapping[str, float],
) -> float:
    """The §7.4 predictive EIG of a check (rows ``likelihood``) about held-out
    ``targets`` under ``posterior``, in nats: ``H_prior - sum_o m(o) H_post(o)``.

    ``probe_families.instrument_predictive_information_gain`` on label-keyed
    rows (``label_conditionals``), with its conventions: the belief is the
    posterior over the labels the check has rows for, renormalized; each
    target's predictive is over the labels it has rows for. So on any belief
    branch the predictive objective is recomputed, never scaled from the
    hypothesis information (Codex final verify F2)."""

    labels = [label for label in posterior if label in likelihood]
    weights = {label: max(float(posterior[label]), 0.0) for label in labels}
    total = sum(weights.values())
    if total <= 0 or len(labels) <= 1 or not targets:
        return 0.0
    belief = {label: weight / total for label, weight in weights.items()}
    prior_entropy = _targets_predictive_entropy(targets, belief)
    mixture: dict[str, float] = {}
    for label, weight in belief.items():
        for outcome, probability in likelihood[label].items():
            mixture[outcome] = mixture.get(outcome, 0.0) + weight * float(probability)
    expected = 0.0
    for outcome, outcome_probability in mixture.items():
        if outcome_probability <= 0:
            continue
        updated = {label: weight * float(likelihood[label].get(outcome, 0.0)) for label, weight in belief.items()}
        updated_total = sum(updated.values())
        if updated_total <= 0:
            expected += outcome_probability * prior_entropy
            continue
        expected += outcome_probability * _targets_predictive_entropy(
            targets, {label: value / updated_total for label, value in updated.items()}
        )
    return max(prior_entropy - expected, 0.0)


@dataclass(frozen=True)
class HypothesisChannel:
    """What one check tells about the learner's rival hypotheses: its
    likelihood rows ``P(E | H)`` over one hypothesis variable (``belief_key``,
    an open probe episode's locked set) with that variable's current belief.

    The selection reward's hypothesis term is ``scale`` times the check's
    information in nats under its own objective: the hypothesis EIG (the
    reward normalizes it by the set's maximum entropy), or, on the §7.4
    predictive objective, the predictive EIG about the episode's held-out
    ``targets`` (the reward normalizes it by their prior predictive entropy);
    both discounted for familiarity. ``scale`` is read back as term /
    standalone information, so the first check reproduces the logged term
    exactly. Valued after earlier checks on the same variable, the
    information is the same objective recomputed on each expected posterior
    branch their outcomes leave and averaged (outcomes independent given
    ``H``): for the hypothesis objective ``I(E; H | E_earlier)``; for the
    predictive objective the targets' expected predictive uncertainty the
    check still removes. Two checks revealing independent bits each keep
    their information; a check that repeats an earlier one, or whose targets
    the earlier ones already settled, adds none. A label the check has no row
    for is one it says nothing about (its outcome distribution is the check's
    predictive over the labels it covers).
    """

    belief_key: str
    prior: tuple[tuple[str, float], ...]
    likelihood: Mapping[str, Mapping[str, float]]
    scale: float
    objective: str = "hypothesis_eig"
    #: The held-out targets' rows (label-keyed), for the predictive objective.
    targets: tuple[Mapping[str, Mapping[str, float]], ...] = ()

    @classmethod
    def from_mapping(cls, body: Mapping[str, Any] | None, *, hypothesis_term: float) -> "HypothesisChannel | None":
        """``{belief_key, prior, likelihood, objective, targets}`` (the
        scheduler's ``ScheduledItem.hypothesis_channel``), or None when it
        carries no information or the reward logged no hypothesis term."""

        if not isinstance(body, Mapping) or hypothesis_term <= 0:
            return None
        try:
            likelihood = _keyed(body["likelihood"])
            raw_prior = {str(label): max(float(value), 0.0) for label, value in dict(body["prior"]).items()}
            belief_key = str(body["belief_key"])
            objective = str(body.get("objective") or "hypothesis_eig")
            targets = (
                tuple(_keyed(rows) for rows in body.get("targets") or () if rows)
                if objective == "predictive_eig"
                else ()
            )
        except (KeyError, TypeError, ValueError, AttributeError):
            return None
        total = sum(raw_prior.values())
        if total <= 0 or not likelihood:
            return None
        prior = {label: value / total for label, value in raw_prior.items() if value > 0}
        channel = cls(
            belief_key=belief_key,
            prior=tuple(sorted(prior.items())),
            likelihood=likelihood,
            scale=1.0,
            objective=objective,
            targets=targets,
        )
        standalone = channel.standalone_nats
        if standalone <= 0:
            return None
        return replace(channel, scale=float(hypothesis_term) / standalone)

    @property
    def recomputes_predictive(self) -> bool:
        """The predictive objective with its held-out targets carried."""

        return self.objective == "predictive_eig" and bool(self.targets)

    @property
    def standalone_nats(self) -> float:
        """The check's information at the current belief, under its objective."""

        return self.at(dict(self.prior))

    def at(self, posterior: Mapping[str, float]) -> float:
        """The check's information (nats, its own objective) under ``posterior``."""

        if self.recomputes_predictive:
            return predictive_information(self.likelihood, self.targets, posterior)
        return expected_information_gain(self.likelihood, dict(posterior))

    @property
    def labelled(self) -> str:
        """How the conditional hypothesis term is computed, for the receipt."""

        if self.objective == "predictive_eig":
            if self.recomputes_predictive:
                return "expected_posterior_branches:predictive_objective"
            # No targets carried (an older body): the reward's term is scaled
            # by the conditional hypothesis information (an approximation).
            return "expected_posterior_branches:predictive_term_scaled_by_hypothesis_eig"
        return "expected_posterior_branches"

    def root(self) -> _Branches:
        return ((1.0, self.prior),)

    def information(self, branches: _Branches) -> float:
        """The check's information in nats (its own objective), expected over
        ``branches``: recomputed on each branch, never scaled."""

        return sum(weight * self.at(dict(posterior)) for weight, posterior in branches)

    def split(self, branches: _Branches) -> tuple[_Branches, bool]:
        """The posterior branches after this check's outcome, merged; the flag
        says whether coarser merging was needed (the bound was passed)."""

        children: list[tuple[float, dict[str, float]]] = []
        for weight, posterior_items in branches:
            posterior = dict(posterior_items)
            covered = {label: mass for label, mass in posterior.items() if label in self.likelihood}
            covered_mass = sum(covered.values())
            if covered_mass <= 0:
                children.append((weight, posterior))
                continue
            predictive: dict[str, float] = {}
            for label, mass in covered.items():
                for outcome, probability in self.likelihood[label].items():
                    predictive[outcome] = predictive.get(outcome, 0.0) + (mass / covered_mass) * float(probability)
            for outcome, probability in predictive.items():
                if probability <= 0:
                    continue
                child = {
                    label: (
                        mass * float(self.likelihood[label].get(outcome, 0.0)) / probability
                        if label in covered
                        else mass
                    )
                    for label, mass in posterior.items()
                }
                children.append((weight * probability, child))
        merged = _merge_branches(children, _BRANCH_MERGE_DIGITS)
        coarse = False
        for digits in _COARSE_MERGE_DIGITS:
            if len(merged) <= _MAX_BELIEF_BRANCHES:
                break
            merged = _merge_branches(merged, digits)
            coarse = True
        return (
            tuple((weight, tuple(sorted(posterior.items()))) for weight, posterior in merged),
            coarse,
        )


@dataclass(frozen=True)
class InformationTerms:
    """One candidate's information as the selection reward decomposes it.

    ``selection_rewards.probe_information_gain_components`` sums three
    entropy reductions into ``probe_eig_total``: the hypothesis EIG (already
    discounted for familiarity), the LO-mastery Gaussian
    ``0.5 * log(prior_var / posterior_var)``, and the facet-recall reduction
    ``sum_f w_f * 0.5 * log(var_f / var_f * (1 - w_f d / (mass_f + 2)))``.
    These terms are read back from the reward's debug body (never recomputed
    from new constants), so the information of a check can be valued
    conditionally on the checks already chosen:

    * the LO-mastery term adds the check's observation precision
      ``1/posterior_var - 1/prior_var`` to the belief left by the earlier
      checks (a Gaussian's posterior variance does not depend on the outcome,
      so each "expected belief branch" is this one deterministic update);
    * a facet's term shrinks the variance the earlier checks left, against
      the evidence mass they added (``w d`` each);
    * the hypothesis term is valued over the expected posterior branches the
      earlier checks on the same hypothesis variable leave, from the check's
      own likelihood rows (:class:`HypothesisChannel`; review F2 reopened).
      Only when a check with a hypothesis term carries no rows is it counted
      once per learning object (labelled ``once_per_learning_object``).

    For the first check chosen the terms reproduce ``probe_eig_total``
    exactly (:meth:`from_reward_debug` refuses a body they do not reproduce).
    """

    learning_object_id: str
    hypothesis_nats: float
    lo_prior_variance: float
    lo_posterior_variance: float
    discount: float
    #: ``(facet id, evidence weight, prior variance, prior evidence mass)``.
    facets: tuple[tuple[str, float, float, float], ...]
    hypothesis: HypothesisChannel | None = None

    @classmethod
    def from_reward_debug(
        cls,
        learning_object_id: str,
        debug: Mapping[str, Any] | None,
        *,
        total_nats: float | None = None,
        hypothesis_channel: Mapping[str, Any] | None = None,
    ) -> "InformationTerms | None":
        """The terms behind a scheduled item's ``reward_debug``, or None when the
        body is missing or does not reproduce ``total_nats``.
        ``hypothesis_channel`` is the item's likelihood rows over its open
        probe episode's hypotheses, when it has a hypothesis term."""

        if not isinstance(debug, Mapping):
            return None
        try:
            probe = debug["probe_eig"]
            ability = debug["ability_vector"]
            demand = debug["item_demand_vector"]
            lo_mastery = probe["lo_mastery"]
            discount = _clamp01(float(probe.get("independent_evidence_discount", 1.0)))
            prior_variance = max(math.exp(2.0 * float(lo_mastery["prior_entropy"])), _VARIANCE_FLOOR)
            posterior_variance = max(
                math.exp(2.0 * float(lo_mastery["expected_posterior_entropy"])), _VARIANCE_FLOOR
            )
            hypothesis = max(float((probe.get("hypothesis") or {}).get("reduction", 0.0) or 0.0), 0.0)
            variances = ability.get("facet_recall_variance_by_facet") or {}
            masses = ability.get("facet_independent_evidence_mass_by_facet") or {}
            facets = tuple(
                (
                    str(facet),
                    max(float(weight), 0.0),
                    max(float(variances.get(facet, _DEFAULT_FACET_VARIANCE)), _VARIANCE_FLOOR),
                    max(float(masses.get(facet, 0.0)), 0.0),
                )
                for facet, weight in sorted((demand.get("evidence_weights") or {}).items())
                if float(weight) > 0
            )
        except (KeyError, TypeError, ValueError, AttributeError):
            return None
        terms = cls(
            learning_object_id=str(learning_object_id),
            hypothesis_nats=hypothesis,
            lo_prior_variance=prior_variance,
            lo_posterior_variance=min(posterior_variance, prior_variance),
            discount=discount,
            facets=facets,
            hypothesis=HypothesisChannel.from_mapping(hypothesis_channel, hypothesis_term=hypothesis),
        )
        if total_nats is not None:
            alone = terms.conditional_nats(InformationState())["total"]
            if abs(alone - float(total_nats)) > _RECONSTRUCTION_TOLERANCE * max(1.0, abs(float(total_nats))):
                return None
        return terms

    @property
    def lo_precision(self) -> float:
        return max(1.0 / self.lo_posterior_variance - 1.0 / self.lo_prior_variance, 0.0)

    @property
    def hypothesis_conditioning(self) -> str:
        if self.hypothesis_nats <= 0:
            return "none"
        if self.hypothesis is not None:
            return self.hypothesis.labelled
        return "once_per_learning_object"

    def _hypothesis_nats(self, state: "InformationState") -> float:
        if self.hypothesis_nats <= 0:
            return 0.0
        channel = self.hypothesis
        if channel is None:
            # No likelihood rows: counted once per learning object (labelled).
            return 0.0 if self.learning_object_id in state.hypothesis_learning_objects else self.hypothesis_nats
        branches = state.beliefs.get(channel.belief_key)
        if branches is None:
            return self.hypothesis_nats
        return max(0.0, channel.scale * channel.information(branches))

    def conditional_nats(self, state: "InformationState") -> dict[str, float]:
        """This check's information given the checks already in ``state``."""

        hypothesis = self._hypothesis_nats(state)
        variance = state.lo_variance.get(self.learning_object_id, self.lo_prior_variance)
        precision = self.lo_precision
        after = max(1.0 / (1.0 / variance + precision), _VARIANCE_FLOOR) if precision > 0 else variance
        lo_reduction = max(0.0, 0.5 * math.log(variance / after)) if after > 0 else 0.0
        facet_reduction = 0.0
        for facet, weight, prior_variance, prior_mass in self.facets:
            facet_variance, mass = state.facets.get(facet, (prior_variance, prior_mass))
            fraction = _clamp01((weight * self.discount) / (mass + 2.0))
            facet_after = max(facet_variance * (1.0 - fraction), _VARIANCE_FLOOR)
            facet_reduction += weight * 0.5 * math.log(facet_variance / facet_after)
        facet_reduction = max(0.0, facet_reduction)
        return {
            "hypothesis": hypothesis,
            "lo_mastery": lo_reduction,
            "facet_recall": facet_reduction,
            "total": max(0.0, hypothesis + lo_reduction + facet_reduction),
        }


@dataclass(frozen=True)
class InformationState:
    """The belief the checks chosen so far are expected to leave behind.

    ``beliefs`` holds, per hypothesis variable, the expected posterior
    branches ``(probability, posterior)`` the chosen checks' outcomes leave;
    ``coarse_beliefs`` names the variables whose branches needed coarser
    merging (receipt label)."""

    lo_variance: Mapping[str, float] = field(default_factory=dict)
    facets: Mapping[str, tuple[float, float]] = field(default_factory=dict)
    hypothesis_learning_objects: frozenset[str] = frozenset()
    beliefs: Mapping[str, _Branches] = field(default_factory=dict)
    coarse_beliefs: frozenset[str] = frozenset()

    def after(self, terms: InformationTerms) -> "InformationState":
        lo_variance = dict(self.lo_variance)
        variance = lo_variance.get(terms.learning_object_id, terms.lo_prior_variance)
        precision = terms.lo_precision
        if precision > 0:
            lo_variance[terms.learning_object_id] = max(1.0 / (1.0 / variance + precision), _VARIANCE_FLOOR)
        facets = dict(self.facets)
        for facet, weight, prior_variance, prior_mass in terms.facets:
            facet_variance, mass = facets.get(facet, (prior_variance, prior_mass))
            fraction = _clamp01((weight * terms.discount) / (mass + 2.0))
            facets[facet] = (max(facet_variance * (1.0 - fraction), _VARIANCE_FLOOR), mass + weight * terms.discount)
        hypothesis = set(self.hypothesis_learning_objects)
        beliefs = dict(self.beliefs)
        coarse = set(self.coarse_beliefs)
        if terms.hypothesis_nats > 0:
            channel = terms.hypothesis
            if channel is None:
                hypothesis.add(terms.learning_object_id)
            else:
                branches, coarsened = channel.split(beliefs.get(channel.belief_key, channel.root()))
                beliefs[channel.belief_key] = branches
                if coarsened:
                    coarse.add(channel.belief_key)
        return InformationState(
            lo_variance=lo_variance,
            facets=facets,
            hypothesis_learning_objects=frozenset(hypothesis),
            beliefs=beliefs,
            coarse_beliefs=frozenset(coarse),
        )


@dataclass(frozen=True)
class InformationEntry:
    """One check valued through the selection reward's information (no
    hypothesis members): a teach-back or a due project probe."""

    ref: str
    learning_object_id: str | None
    eig_nats: float
    minutes: MinutesEstimate
    predicted_correct: float | None = None
    terms: InformationTerms | None = None
    detail: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GreedyAdmission:
    """Checks admitted one at a time, each valued conditionally on those
    already admitted; ``steps`` holds every step's decision (the last one is
    the stop, unless every candidate was admitted)."""

    site: str
    admitted: tuple[str, ...]
    steps: tuple[SiteDecision, ...]
    #: Checks already selected before this admission (planned, not yet
    #: answered, or a learner request): conditioned on first, never valued or
    #: charged again.
    preselected: tuple[str, ...] = ()
    #: Why each preselected check is held (default ``already_planned``;
    #: ``learner_request`` for a requested check, Codex review of voi-v2 F14).
    preselected_reasons: Mapping[str, str] = field(default_factory=dict)

    def step_for(self, ref: str) -> tuple[int, SiteDecision] | None:
        """The step that admitted ``ref``, else the final step (its stop)."""

        if ref in self.admitted:
            index = self.admitted.index(ref)
            return index, self.steps[index]
        if not self.steps:
            return None
        return len(self.steps) - 1, self.steps[-1]

    def receipt_for(self, ref: str) -> dict[str, Any] | None:
        if ref in self.preselected:
            # Not a value decision: the plan already holds this check (or the
            # learner asked for it), and the others were valued given it.
            return {
                "forecast_version": FORECAST_VERSION,
                "site": self.site,
                "decision": CONTINUE,
                "reason": str(self.preselected_reasons.get(ref, REASON_ALREADY_PLANNED)),
                "subject_ref": ref,
                "admitted": True,
                "context": dict(self.steps[0].context) if self.steps else {},
                "calibration_label": "heuristic",
            }
        located = self.step_for(ref)
        if located is None:
            return None
        index, step = located
        body = step.as_dict(subject_ref=ref)
        admitted = ref in self.admitted
        # The step's own verdict is about its best candidate; this receipt is
        # about ``ref``: admitted at this step, or never admitted (the stop).
        body["decision"] = CONTINUE if admitted else STOP
        if not admitted:
            subject = step.value_for(ref)
            if subject is not None and not subject.continues:
                # Its own reason: its value does not pay, or it does not fit.
                body["reason"] = subject.reason
            elif step.decision == CONTINUE:
                body["reason"] = "not_reached"
        body["greedy_step"] = index
        body["admitted"] = admitted
        return body

    def bodies(self) -> list[dict[str, Any]]:
        out = []
        for index, step in enumerate(self.steps):
            body = step.as_dict()
            body["greedy_step"] = index
            out.append(body)
        return out


def greedy_information_admission(
    ctx: VoiContext,
    site: str,
    entries: Sequence[InformationEntry],
    *,
    cap_value: int,
    cap_count: int = 0,
    context: Mapping[str, Any] | None = None,
    minutes_budget: float | None = None,
    max_item_minutes: float | None = None,
    preselected: Iterable[str] = (),
    preselected_reasons: Mapping[str, str] | None = None,
) -> GreedyAdmission:
    """Admit checks greedily, each valued conditionally on those already chosen.

    The reader spec's rule (§9.3 item 3, the four-cap decision in §18): at
    each step every remaining check is valued given the belief the admitted
    ones are expected to leave (:class:`InformationTerms`); the best one by
    robust value per minute is admitted while its value pays for its minutes
    (``lambda_time * minutes + burden``), and adding stops at the first step
    whose best remaining check does not pay. So two checks that would tell
    LearnLoop the same thing are not both admitted, and the number follows
    from value, never from a count. No next-action decision is at stake for
    these checks (no locked hypothesis set), so the robust EIG in minutes is
    the value. The former cap is only a counterfactual in each step's receipt
    (``cap_count`` checks of this kind were already counted before step 0).
    A check whose reward body is missing is valued on its logged total alone,
    and its receipt says ``conditioning: unavailable``.

    Feasibility (review F10): with ``minutes_budget`` (the plan's minutes) a
    check is admissible only while it fits the minutes the admitted ones leave,
    and with ``max_item_minutes`` (the longest block a check can sit in) only
    when it fits one block. A check that does not fit is valued for its receipt
    (``does_not_fit_plan_minutes``) but never admitted, so later checks are
    conditioned only on checks the plan can actually hold.

    ``preselected`` (final verify F10) names checks among ``entries`` the plan
    already holds (planned on an earlier boundary, not yet answered): every
    other check is valued given them, and they are neither valued nor charged
    against ``minutes_budget`` again (the budget is what is left after them).
    ``preselected_reasons`` says why each is held (``already_planned`` by
    default; ``learner_request`` for a request, which the plan charged once
    before the split, Codex review of voi-v2 F14).
    """

    preselected_refs = tuple(dict.fromkeys(str(ref) for ref in preselected))
    by_ref_all = {entry.ref: entry for entry in entries}
    held = tuple(ref for ref in preselected_refs if ref in by_ref_all)
    held_reasons = {ref: str((preselected_reasons or {}).get(ref, REASON_ALREADY_PLANNED)) for ref in held}
    state = InformationState()
    for ref in held:
        terms = by_ref_all[ref].terms
        if terms is not None:
            state = state.after(terms)
    remaining = [entry for entry in entries if entry.ref not in set(held)]
    admitted: list[str] = []
    steps: list[SiteDecision] = []
    spent = 0.0
    while remaining:
        limit = math.inf
        if minutes_budget is not None:
            limit = min(limit, float(minutes_budget) - spent)
        if max_item_minutes is not None:
            limit = min(limit, float(max_item_minutes))
        candidates = []
        for entry in remaining:
            if entry.terms is not None:
                parts = entry.terms.conditional_nats(state)
                eig = parts["total"]
                conditioning = {
                    "conditioning": "chosen_before" if (admitted or held) else "none_chosen",
                    "conditional_parts_nats": {key: round(value, _ROUND_DIGITS) for key, value in parts.items()},
                    "hypothesis_conditioning": entry.terms.hypothesis_conditioning,
                }
                channel = entry.terms.hypothesis
                if channel is not None and channel.belief_key in state.coarse_beliefs:
                    conditioning["hypothesis_branches"] = "coarsely_merged"
            else:
                eig = max(float(entry.eig_nats), 0.0)
                conditioning = {"conditioning": "unavailable"}
            fits = float(entry.minutes.minutes) <= limit + 1e-9
            candidates.append(
                information_candidate(
                    entry.ref,
                    eig_nats=eig,
                    minutes=entry.minutes,
                    predicted_correct=entry.predicted_correct,
                    detail={
                        **dict(entry.detail),
                        "learning_object_id": entry.learning_object_id,
                        "unconditioned_eig_nats": round(max(float(entry.eig_nats), 0.0), _ROUND_DIGITS),
                        **conditioning,
                        **(
                            {"minutes_left": round(limit, 6)}
                            if math.isfinite(limit)
                            else {}
                        ),
                    },
                    infeasible_reason=None if fits else REASON_DOES_NOT_FIT,
                )
            )
        by_ref = {entry.ref: entry for entry in remaining}
        decision = value_candidates(
            ctx,
            site,
            candidates,
            prior={},
            learning_object_id=None,
            former_cap=former_cap(site, value=cap_value, count=int(cap_count) + len(admitted)),
            context={
                **dict(context or {}),
                "greedy_step": len(steps),
                "chosen_before": [*held, *admitted],
                **(
                    {"already_planned": planned}
                    if (planned := [ref for ref in held if held_reasons[ref] == REASON_ALREADY_PLANNED])
                    else {}
                ),
                **(
                    {"learner_requests": requested}
                    if (requested := [ref for ref in held if held_reasons[ref] == REASON_LEARNER_REQUEST])
                    else {}
                ),
                **(
                    {"minutes_budget": round(float(minutes_budget), 6), "minutes_admitted": round(spent, 6)}
                    if minutes_budget is not None
                    else {}
                ),
                **({"max_item_minutes": round(float(max_item_minutes), 6)} if max_item_minutes is not None else {}),
            },
            evsi_enabled=False,
        )
        steps.append(decision)
        chosen = decision.chosen
        if decision.decision != CONTINUE or chosen is None:
            break
        picked = by_ref[chosen.ref]
        admitted.append(picked.ref)
        spent += float(picked.minutes.minutes)
        if picked.terms is not None:
            state = state.after(picked.terms)
        remaining = [entry for entry in remaining if entry.ref != picked.ref]
    return GreedyAdmission(
        site=site, admitted=tuple(admitted), steps=tuple(steps), preselected=held, preselected_reasons=held_reasons
    )


def not_in_plan_receipt(site: str, ref: str, why: str) -> dict[str, Any]:
    """The receipt of a due check a plan refresh cannot take (Codex review of
    voi-v2, F10): ``why`` is ``skipped_in_this_plan``,
    ``answered_in_this_plan`` or ``outside_plan_universe``. Not a value
    decision: the check was neither valued nor conditioned on."""

    return {
        "forecast_version": FORECAST_VERSION,
        "site": site,
        "decision": STOP,
        "reason": REASON_NOT_IN_PLAN,
        "availability": str(why),
        "subject_ref": ref,
        "admitted": False,
        "calibration_label": "heuristic",
    }


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


def hypothesis_channel_body(
    belief_key: str,
    eligible: Any,
    posterior: Mapping[str, float],
    *,
    objective: str,
) -> dict[str, Any]:
    """An in-episode probe's likelihood rows over its episode's hypotheses
    (``{belief_key, prior, likelihood, objective}``, plus ``targets`` on the
    predictive objective), the input of :meth:`HypothesisChannel.from_mapping`:
    the instrument's composed ``P(E | H)`` keyed by episode label, as the
    probe-episode site reads it, and the held-out targets' rows likewise."""

    from learnloop.diagnosis.probe_families import instrument_conditionals

    body: dict[str, Any] = {
        "belief_key": str(belief_key),
        "prior": {str(label): float(value) for label, value in posterior.items()},
        "likelihood": label_conditionals(instrument_conditionals(eligible.instrument), eligible.slot_map, posterior),
        "objective": str(objective),
    }
    if str(objective) == "predictive_eig":
        # The held-out targets the predictive objective is about (the same
        # ones the episode's own predictive EIG used), so a later conditional
        # valuation recomputes it on each posterior branch (final verify F2).
        body["targets"] = [
            label_conditionals(instrument_conditionals(instrument), slot_map, posterior)
            for instrument, slot_map in getattr(eligible, "predictive_targets", ()) or ()
        ]
    return body


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
                # The exposure rule's group (eligible_instruments): one answer
                # excludes the rest of the group from this episode (F13).
                surface_group=getattr(entry, "surface_group", None),
            )
        )
    episode_config = ctx.vault.config.probe.episode
    cap = int(episode_config.session_qualifying_observation_cap)
    count = (
        int(ctx.repository.qualifying_probe_observation_count_for_session(session_id))
        if session_id is not None
        else 0
    )
    cap_body = former_cap(SITE_PROBE_EPISODE, value=cap, count=count)
    # The episode's own count (``probe.episode.maximum_observations``, stamped
    # on the episode at entry) is lifted with the session cap (reader spec §18,
    # §20.7); its counterfactual rides on the same receipt.
    maximum = getattr(episode, "maximum_observations", None)
    if maximum is not None:
        qualifying = sum(
            1
            for row in ctx.repository.probe_observations_for_episode(episode.id)
            if row["observation"].eligible_for_completion
        )
        episode_bind = qualifying >= int(maximum)
        cap_body["episode_maximum"] = {
            "name": EPISODE_MAXIMUM_CAP,
            "value": int(maximum),
            "count": int(qualifying),
            "would_bind": episode_bind,
        }
        cap_body["would_bind"] = bool(cap_body["would_bind"]) or episode_bind
    return value_candidates(
        ctx,
        SITE_PROBE_EPISODE,
        candidates,
        prior=belief,
        learning_object_id=str(episode.learning_object_id),
        former_cap=cap_body,
        context={"episode_id": str(episode.id), "session_id": session_id},
    )


# ---------------------------------------------------------------------------
# The follow-up decision's durable receipt
# ---------------------------------------------------------------------------


def record_followup_decision(
    repository: Any,
    *,
    attempt_id: str,
    learning_object_id: str,
    session_id: str | None,
    outcome: str,
    decision: Mapping[str, Any] | None,
    manual_override: bool,
    need_id: str | None,
    algorithm_version: str,
    clock: Any = None,
) -> str:
    """Append one follow-up value decision to its immutable receipt table.

    Each decision on a source attempt gets its own id and ordinal (an automatic
    decision, then the learner's manual follow-up; a generation need, then a
    queue once a candidate exists), so none overwrites another and none is
    dropped (review F1 reopened). ``decision`` is ``SiteDecision.as_dict``
    (None when there was no candidate to value).
    """

    from learnloop.clock import utc_now_iso
    from learnloop.db.stores.followup_value import insert_decision

    body = dict(decision) if decision is not None else None
    with repository.atomic(), repository.connection() as connection:
        return insert_decision(
            connection,
            {
                "source_attempt_id": str(attempt_id),
                "learning_object_id": str(learning_object_id),
                "session_id": session_id,
                "decision_outcome": outcome,
                "verdict": body.get("decision") if body is not None else None,
                "manual_override": bool(manual_override),
                "recommended_ref": body.get("recommended_ref") if body is not None else None,
                "served_ref": body.get("served_ref") if body is not None else None,
                "need_id": need_id,
                "candidate_count": int(body.get("candidate_count") or 0) if body is not None else 0,
                "forecast_version": body.get("forecast_version") if body is not None else None,
                "decision_json": body,
                "algorithm_version": algorithm_version,
                "created_at": utc_now_iso(clock),
            },
        )


def record_offer_value_forecasts(
    vault: Any,
    repository: Any,
    *,
    slate_id: str,
    candidate_ids: Mapping[str, str],
    probe_decisions: Mapping[str, SiteDecision],
    teach_back_receipts: Sequence[Mapping[str, Any]],
    exploration_by_item: Mapping[str, Mapping[str, Any]] | None = None,
    clock: Any = None,
) -> None:
    """The value decisions a Today offer acted on, as EVSI calibration
    forecasts (``voi_forecasts``, behind ``evsi.forecast_logging``; logging
    only, never raises).

    One row per decision per offer, router R1's grain (each offer is one
    ``today_offer`` decision, keyed by its slate), with the offer's slate as
    ``decision_ref``: each teach-back the offer kept or dropped (its
    candidate in this slate, and R1's ``scheduler_exploration`` marker when
    the seeded exploration drew it), and each probe episode whose next
    observation the offer withheld because it does not pay. An episode's
    continue acts where its observation is committed, so it is logged with the
    presentation (``probe_episodes.record_presentation_forecast``), never here,
    and an episode's completion on its value stop is logged at the completion.
    """

    from learnloop.diagnosis.voi_forecasting import record_value_decision_forecast

    exploration = dict(exploration_by_item or {})
    for episode_id, decision in sorted(probe_decisions.items()):
        if decision.decision != STOP:
            continue
        record_value_decision_forecast(
            vault,
            repository,
            decision.as_dict(),
            receipt_key=f"probe_episode_value_decision:{slate_id}:{episode_id}",
            clock=clock,
            decision_ref=slate_id,
            probe_episode_id=str(episode_id),
        )
    for body in teach_back_receipts:
        ref = body.get("subject_ref")
        if not ref:
            continue
        kept = body.get("decision") == CONTINUE
        record_value_decision_forecast(
            vault,
            repository,
            body,
            receipt_key=f"teach_back_value_decision:{slate_id}:{ref}",
            scheduler_exploration=exploration.get(str(ref)) if kept else None,
            clock=clock,
            decision_ref=slate_id,
            scheduler_candidate_id=candidate_ids.get(str(ref)),
        )


def record_plan_value_forecasts(
    vault: Any,
    repository: Any,
    receipts: Sequence[Mapping[str, Any]],
    *,
    block_id: str,
    decision_ref: str | None,
    clock: Any = None,
) -> None:
    """A daily-plan block decision's due project probe receipts as EVSI
    calibration forecasts (``project_probe_value_decision``; logging only).

    One row per probe per block decision (the plan values its due probes at
    every boundary, conditioned on those it already holds), keyed by the block
    (or the stop receipt) and carrying router R1's ``plan_block`` row id as
    ``decision_ref`` when R1 logged the decision. A probe the plan already
    holds, a learner request and a probe the plan cannot take are not value
    decisions and record nothing."""

    from learnloop.diagnosis.voi_forecasting import record_value_decision_forecast

    for body in receipts:
        ref = body.get("subject_ref")
        if not ref:
            continue
        record_value_decision_forecast(
            vault,
            repository,
            body,
            receipt_key=f"project_probe_value_decision:{block_id}:{ref}",
            extra={"plan_block_id": block_id},
            clock=clock,
            decision_ref=decision_ref or block_id,
        )


def followup_receipts(repository: Any, attempt_id: str) -> list[dict[str, Any]]:
    """Every follow-up value decision on ``attempt_id``, in decision order.

    Each row is a RECEIPT (``followup_value_decisions``): written once by the
    live follow-up path, never updated (immutable by trigger) and never
    cleared by a rebuild or a regrade's replay, unlike
    ``attempt_surprise.gate_diagnostics_json`` (DERIVED). ``decision`` is the
    value decision with its forecasts (None when nothing was valued).
    """

    from learnloop.db.stores.followup_value import decisions_for_attempt

    with repository.connection() as connection:
        return decisions_for_attempt(connection, str(attempt_id))


def followup_receipt(repository: Any, attempt_id: str) -> dict[str, Any] | None:
    """The latest valued follow-up decision on ``attempt_id`` (its
    ``SiteDecision`` body), or None."""

    for row in reversed(followup_receipts(repository, attempt_id)):
        if isinstance(row.get("decision"), Mapping):
            return dict(row["decision"])
    return None


__all__ = [
    "CONTINUE",
    "LOOKAHEAD_SITES",
    "LOSS_REGIME_MEASURED",
    "LOSS_REGIME_MINUTES",
    "UNRESOLVED_GAP_LABELS",
    "UNRESOLVED_NO_PROBLEM_LABELS",
    "unresolved_scope_for_label",
    "METHOD_LOOKAHEAD_PREFIX",
    "REASON_EVSI_BATCH_CLEARS",
    "REASON_LEARNER_REQUEST",
    "REASON_NOT_IN_PLAN",
    "ROBUST_GATE",
    "ROBUST_GATE_SWITCH",
    "VoiSettings",
    "with_robust_gate_counterfactual",
    "EPISODE_MAXIMUM_CAP",
    "VALUATION_SUPPRESSION_REASONS",
    "VOI_VALUE_SUPPRESSION",
    "VOI_STOPPING_VERSIONS",
    "probe_episode_decision",
    "Candidate",
    "CandidateValue",
    "FORECAST_VERSION",
    "FORMER_CAPS",
    "GreedyAdmission",
    "HypothesisChannel",
    "InformationEntry",
    "InformationState",
    "InformationTerms",
    "METHOD_EIG_VALUE",
    "METHOD_ROBUST_EVSI",
    "MinutesEstimate",
    "REASON_ALREADY_PLANNED",
    "REASON_DOES_NOT_FIT",
    "SITES",
    "SITE_FOLLOWUP",
    "SITE_PROBE_EPISODE",
    "SITE_PROJECT_PROBE",
    "SITE_TEACH_BACK",
    "STOP",
    "SiteDecision",
    "VoiContext",
    "followup_receipt",
    "followup_receipts",
    "record_offer_value_forecasts",
    "record_plan_value_forecasts",
    "former_cap",
    "greedy_information_admission",
    "heuristic_parameters",
    "hypothesis_channel_body",
    "information_candidate",
    "label_conditionals",
    "not_in_plan_receipt",
    "predictive_information",
    "probe_lane_holds_out_pending",
    "probe_lane_reads_diagnosis",
    "record_followup_decision",
    "value_candidates",
    "voi_stopping_active",
]
