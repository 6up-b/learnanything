"""What is known about a possible probe before anyone decides whether to run it.

``probe_facts`` turns plain values gathered by its caller into a frozen :class:`ProbeFacts`: the repair classes the
plausible causes need, the instrument's discriminating value, the burden in minutes, and the hard stops that hold.
It reads no clock, repository or config, so a caller that has the values can ask for the facts without a vault.

``probe_verdict`` is the repair lane's rule over those facts (``causal_probe_coherence.decide_probe`` applies it). It
keeps the facts and the thresholds apart so that a decider other than this rule can take the same facts and drop the
thresholds. ``settled_by_repair_classes`` is the rule's first two arms alone: they read only the repair classes, so a
caller with no instrument yet can still say whether the classes settle the question.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

#: A learner preference under which no probe is offered now (``probe_hard_stops.LEARNER_PREFERENCES`` minus allow).
REFUSING_PREFERENCES = frozenset({"decline", "teach_now", "no_more_diagnostics"})

HARD_STOP_MACHINE_CHECKS = "machine_checks_pending"
HARD_STOP_LEARNER_PREFERENCE = "learner_preference"
HARD_STOP_SESSION_BUDGET = "session_budget"


@dataclass(frozen=True)
class ProbeFacts:
    """The facts about one possible probe, and the hard stops that hold.

    - ``repair_class_ids``: the distinct non-empty repair classes of the plausible causes, sorted.
    - ``common_repair_covers``: one repair covers the plausible cause set (as the caller found it).
    - ``different_repairs``: more than one repair class.
    - ``action_relevant``: different repairs and no common cover; what the probe could change. The receipt's
      ``high_priority_need`` and ``blocks_branch_specific_repair`` are this fact.
    - ``expected_information_gain``: as given; the caller computes it as the share of the locked hypotheses' pairs
      the instrument's blind bundles provably separate (unitless, 0 to 1; not nats).
    - ``probability_information_changes_repair``: as given; the share of those separable pairs whose causes need
      different repairs (unitless, 0 to 1).
    - ``expected_avoided_overteaching_minutes``: minutes; the avoided over-teaching (floored at 0) times the change
      probability and the gain, each clipped to 0 to 1.
    - ``probe_burden_minutes``: minutes the probe costs the learner, floored at 0.
    - ``recent_diagnostic_burden``: how many recent attempts on the learning object were diagnostic probes (a count).
    - ``machine_checks_first``: the pending machine-check ids, in the caller's order.
    - Hard stops, each a flag: ``machine_checks_pending`` (machine-side checks must resolve first),
      ``learner_preference_refuses`` (the learner's own "not now", "teach me now" or "no more diagnostics"), and
      ``session_budget_short`` (the remaining session minutes, when known, are fewer than the probe's burden as
      given, before the floor).
    """

    repair_class_ids: tuple[str, ...]
    common_repair_covers: bool
    different_repairs: bool
    action_relevant: bool
    expected_information_gain: float
    probability_information_changes_repair: float
    expected_avoided_overteaching_minutes: float
    probe_burden_minutes: float
    recent_diagnostic_burden: int
    machine_checks_first: tuple[str, ...]
    machine_checks_pending: bool
    learner_preference_refuses: bool
    session_budget_short: bool

    @property
    def hard_stops(self) -> tuple[str, ...]:
        """The names of the hard stops that hold, in the order the rule checks them."""

        flags = (
            (HARD_STOP_MACHINE_CHECKS, self.machine_checks_pending),
            (HARD_STOP_LEARNER_PREFERENCE, self.learner_preference_refuses),
            (HARD_STOP_SESSION_BUDGET, self.session_budget_short),
        )
        return tuple(name for name, holds in flags if holds)


def probe_facts(
    *,
    repair_class_ids: Sequence[str | None],
    common_repair_covers: bool,
    expected_information_gain: float,
    probability_information_changes_repair: float,
    probe_burden_minutes: float,
    avoided_overteaching_minutes: float,
    pending_machine_checks: Sequence[str] = (),
    session_budget_minutes: float | None = None,
    learner_preference: str = "allow",
    recent_diagnostic_burden: int = 0,
) -> ProbeFacts:
    """The facts and hard stops for one possible probe, from values the caller gathered (units on
    :class:`ProbeFacts`; ``avoided_overteaching_minutes`` and ``session_budget_minutes`` are minutes)."""

    classes = tuple(sorted({str(value) for value in repair_class_ids if value}))
    different_repairs = len(classes) > 1
    expected_avoided = (
        max(0.0, avoided_overteaching_minutes)
        * max(0.0, min(1.0, probability_information_changes_repair))
        * max(0.0, min(1.0, expected_information_gain))
    )
    return ProbeFacts(
        repair_class_ids=classes,
        common_repair_covers=common_repair_covers,
        different_repairs=different_repairs,
        action_relevant=different_repairs and not common_repair_covers,
        expected_information_gain=expected_information_gain,
        probability_information_changes_repair=probability_information_changes_repair,
        expected_avoided_overteaching_minutes=expected_avoided,
        probe_burden_minutes=max(0.0, probe_burden_minutes),
        recent_diagnostic_burden=recent_diagnostic_burden,
        machine_checks_first=tuple(str(value) for value in pending_machine_checks),
        machine_checks_pending=bool(pending_machine_checks),
        learner_preference_refuses=learner_preference in REFUSING_PREFERENCES,
        # The burden as given, not floored: the floor belongs to the value comparison, and the budget check compared
        # against the raw number before the split.
        session_budget_short=(
            session_budget_minutes is not None and session_budget_minutes < probe_burden_minutes
        ),
    )


#: What is known of the chosen instrument's power to tell the causes apart. Today that is only the pairwise
#: separability of its blind bundles, never a likelihood: no instrument, a candidate whose record gives no pair to
#: read, or a computed share (which may be a computed zero).
CHANNEL_NO_INSTRUMENT = "no_instrument"
CHANNEL_NO_SEPARABILITY_RECORD = "no_separability_record"
CHANNEL_SEPARABILITY_COMPUTED = "separability_computed"


def channel_status(*, instrument: bool, separability_computed: bool) -> str:
    """Which of the three states the chosen instrument's channel is in (the ``CHANNEL_*`` names)."""

    if not instrument:
        return CHANNEL_NO_INSTRUMENT
    return CHANNEL_SEPARABILITY_COMPUTED if separability_computed else CHANNEL_NO_SEPARABILITY_RECORD


@dataclass(frozen=True)
class ProbeProposalReads:
    """What the repair lane reads about one factor's possible probe before anyone judges it, as plain values.

    ``causal_orchestrator.gather_probe_reads`` fills it, in the order the repair status always read these; the
    repair lane's verdict then reads its values unchanged. ``channel_status`` keeps a missing instrument or an
    unreadable separability record apart from the numeric zeros the verdict is given for them (the gain and change
    probability are 0.0 there, ``heuristic_default`` in their provenance). Units as on :class:`ProbeFacts`.
    """

    repair_class_ids: tuple[str, ...]
    common_repair_covers: bool
    common_repair_class_id: str | None
    pending_machine_check_ids: tuple[str, ...]
    episode_conflict: str | None
    #: Every candidate with a current blind-input contract, in the shared serving order; the chosen one is the first
    #: active candidate, else the first of any status.
    candidates: tuple[Mapping[str, Any], ...]
    chosen: Mapping[str, Any] | None
    instrument_available: bool
    channel_status: str
    expected_information_gain: float
    probability_information_changes_repair: float
    gain_provenance: str
    action_change_provenance: str
    separable_pairs: int
    inseparable_pairs: int
    prior_basis: str | None
    likelihood_completeness: Mapping[str, Any]
    probe_burden_minutes: float
    burden_provenance: str
    avoided_overteaching_minutes: float
    avoided_provenance: str
    learner_preference: str
    recent_diagnostic_burden: int

    def facts(self, *, session_budget_minutes: float | None = None) -> ProbeFacts:
        """The facts these reads give, as the repair lane's verdict computes them."""

        return probe_facts(
            repair_class_ids=self.repair_class_ids,
            common_repair_covers=self.common_repair_covers,
            expected_information_gain=self.expected_information_gain,
            probability_information_changes_repair=self.probability_information_changes_repair,
            probe_burden_minutes=self.probe_burden_minutes,
            avoided_overteaching_minutes=self.avoided_overteaching_minutes,
            pending_machine_checks=self.pending_machine_check_ids,
            session_budget_minutes=session_budget_minutes,
            learner_preference=self.learner_preference,
            recent_diagnostic_burden=self.recent_diagnostic_burden,
        )


class Thresholds(Protocol):
    """The rule's thresholds, read only when the rule reaches them (``CausalProbeParameters`` is one)."""

    @property
    def recent_diagnostic_limit(self) -> int: ...

    def __getitem__(self, key: str) -> float: ...


def settled_by_repair_classes(
    *, common_repair_covers: bool, different_repairs: bool
) -> tuple[str, str] | None:
    """The rule's first two arms, ``(verb, reason)``, or None when the repair classes leave the question open."""

    if common_repair_covers:
        return "skip_common_repair", "one low-cost repair covers the plausible cause set"
    if not different_repairs:
        return "skip_action_equivalent", "plausible causes imply the same episode repair class"
    return None


def probe_verdict(facts: ProbeFacts, thresholds: Thresholds) -> tuple[str, str]:
    """The repair lane's verdict on the facts, ``(verb, reason)``.

    A fixed ladder; the first arm that applies decides: the repair classes (a common cover, then one class), the
    hard stops (machine checks, then the learner's preference), recent diagnostic burden at or past
    ``recent_diagnostic_limit`` (a negative limit disables it), the session budget, then the value: no gain above
    ``minimum_expected_information_gain``, no change probability above ``minimum_action_change_probability``, and
    expected avoided minutes not above the burden plus ``probe_value_margin_minutes``. A probe otherwise.
    """

    settled = settled_by_repair_classes(
        common_repair_covers=facts.common_repair_covers, different_repairs=facts.different_repairs
    )
    if settled is not None:
        return settled
    if facts.machine_checks_pending:
        return "defer_machine_checks", "machine-side checks must resolve their uncertainty first"
    if facts.learner_preference_refuses:
        return "defer_learner_preference", "learner preference does not permit another probe now"
    limit = thresholds.recent_diagnostic_limit
    if limit >= 0 and facts.recent_diagnostic_burden >= limit:
        return "defer_recent_burden", "recent diagnostic burden reached the session limit"
    if facts.session_budget_short:
        return "defer_session_budget", "the remaining session budget is smaller than probe burden"
    if facts.expected_information_gain <= thresholds["minimum_expected_information_gain"]:
        return "skip_no_discrimination", "the proposed probe has no expected discriminating information"
    if facts.probability_information_changes_repair <= thresholds["minimum_action_change_probability"]:
        return "skip_no_action_change", "the proposed information cannot change the selected repair"
    if facts.expected_avoided_overteaching_minutes <= (
        facts.probe_burden_minutes + thresholds["probe_value_margin_minutes"]
    ):
        return "skip_burden_exceeds_value", "expected avoided over-teaching does not exceed probe burden"
    return "probe_now", "action-changing information is worth more than its burden"


__all__ = [
    "CHANNEL_NO_INSTRUMENT",
    "CHANNEL_NO_SEPARABILITY_RECORD",
    "CHANNEL_SEPARABILITY_COMPUTED",
    "HARD_STOP_LEARNER_PREFERENCE",
    "HARD_STOP_MACHINE_CHECKS",
    "HARD_STOP_SESSION_BUDGET",
    "REFUSING_PREFERENCES",
    "ProbeFacts",
    "ProbeProposalReads",
    "Thresholds",
    "channel_status",
    "probe_facts",
    "probe_verdict",
    "settled_by_repair_classes",
]
