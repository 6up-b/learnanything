"""Configuration gates and parameters for the objective router and daily plan.

Selects objective serving, scoring, and which signals and models enter value.
Reads the stop coin, randomized checks, and deliberately open pick rates.
Gates lesson offers, plan handoffs, learner preferences, and miss-cause inputs.
Defines the switch snapshots used by the follow-up generator and prefetch
boundary, and the keys excluded when deriving common draw seeds.
"""

from __future__ import annotations

from typing import Any


def objective_on(config: Any) -> bool:
    """RO4 (§8.3): the objective serves: ``[router_objective] enabled``. Off, the predecessor's mixture and
    frame exactly."""

    section = getattr(config, "router_objective", None)
    return bool(getattr(section, "enabled", False))


def objective_scores_on(config: Any) -> bool:
    """RO4 (§8.3, §8.7): a comparison score can be formed: the objective serves AND RO0's receipts are on
    (with receipts off the objective serves and no score forms)."""

    section = getattr(config, "router_objective", None)
    return objective_on(config) and bool(getattr(section, "receipts", False))


def sensors_in_value_on(config: Any) -> bool:
    """RO4 (§8.4): the LLM's effect-slope correction enters the value (by hand off)."""

    section = getattr(config, "router_objective", None)
    return objective_on(config) and bool(getattr(section, "sensors_in_value", False))


def stop_coin_rate(config: Any) -> float:
    """RO5 §9 item 1: the stop coin's probability each way at a reversible boundary (0: no coin drawn)."""

    if not objective_on(config):
        return 0.0
    return float(getattr(getattr(config, "router_objective", None), "stop_coin", 0.0) or 0.0)


CHECKS_EMBEDDED = "embedded"
CHECKS_RATE = "rate"
CHECKS_OFF = "off"


def check_mode(config: Any) -> tuple[str, float]:
    """RO5 §9 item 2: ``(mode, value)``: ``("embedded", checks per day)``, ``("rate", per topic per day)`` or
    ``("off", 0)``. With the objective off, off."""

    section = getattr(config, "router_objective", None)
    if not objective_on(config):
        return CHECKS_OFF, 0.0
    rate = getattr(section, "check_rate", CHECKS_OFF)
    if rate == CHECKS_EMBEDDED:
        per_day = int(getattr(section, "embedded_checks_per_day", 0) or 0)
        return (CHECKS_EMBEDDED, float(per_day)) if per_day > 0 else (CHECKS_OFF, 0.0)
    if isinstance(rate, str) or float(rate) <= 0.0:
        return CHECKS_OFF, 0.0
    return CHECKS_RATE, float(rate)


def calibrated_weight_on(config: Any) -> bool:
    """RO5 §9 item 2 into §8.7: the randomized checks' comparison scores move ``w``. The check arm's own switch
    (Codex review F5): with ``check_rate = "off"`` the weight is RO4's calculation exactly, even after checks and
    scores accumulated."""

    return check_mode(config)[0] != CHECKS_OFF


def pick_open_share(config: Any) -> float:
    """RO5 §9 item 6: the seeded share of misconception picks left open."""

    return float(getattr(getattr(config, "router_objective", None), "pick_open_share", 0.0) or 0.0)


def fitted_models_on(config: Any) -> bool:
    """RO5 §9 item 7: the rollouts read AD's fitted learning posterior and the combiner fed resolved checks."""

    section = getattr(config, "router_objective", None)
    return objective_on(config) and bool(getattr(section, "fitted_models", False))


def learned_tail_on(config: Any) -> bool:
    """RO6 (§10): the numeric policy values its candidates with the learned tail's residual (the objective
    serving and ``[router_objective] learned_tail``). Off, mvp-0.48 exactly: nothing is fitted, read or traced."""

    section = getattr(config, "router_objective", None)
    return objective_on(config) and bool(getattr(section, "learned_tail", False))


def followup_on(config: Any, key: str) -> bool:
    """One part of the follow-up batch serves: the tag, the objective serving and its own ``[router_objective]``
    switch ``key`` (default true). Off, or below the tag, that part is mvp-0.49's exactly."""

    section = getattr(config, "router_objective", None)
    return objective_on(config) and bool(getattr(section, key, False))


def monotone_combiner_on(config: Any) -> bool:
    """The follow-up batch's landing ruling R6: the memory model's combiner is monotone in ability by construction
    (``memory.FORM_MONOTONE``), in its prior and its fit: the tag, the objective serving and ``[router_objective]
    monotone_combiner`` (a structural kill switch, default true); off, or below the tag, mvp-0.49's linear combiner."""

    return followup_on(config, "monotone_combiner")


#: The follow-up batch's landing ruling R8: its switches that change a logged decision's value or mixture, so each
#: is part of RO6's generator payload and flipping one is a change point, never a change of ``Q`` under the same
#: generator version. ``carried_in_prefetch`` is not here: it changes which transitions are valued, not the logger.
#: ``held_ad_link`` (router speed, item 1; Codex review F1 on it): like ``merged_sessions``, the same values per draw
#: but more draws within a deadline, so it changes the logger's values and is here too. So are router speed stage 2's
#: ``held_reading_map`` (item 1) and ``pooled_connections`` (item 4; its Codex review F2): the same values, but the
#: input builds finish sooner, leaving the numeric refinement more of the same deadline.
FOLLOWUP_GENERATOR_SWITCHES: tuple[str, ...] = (
    "combiner_trace_outcomes", "merged_sessions", "consistent_review_draw", "monotone_combiner", "ad_predictive_link",
    "scope_extension", "held_ad_link", "held_reading_map", "pooled_connections")


def followup_generator_switches(config: Any) -> dict[str, bool]:
    """R8: each of :data:`FOLLOWUP_GENERATOR_SWITCHES` as it serves (:func:`followup_on`), and slip or gap SG2's."""

    out = {key: followup_on(config, key) for key in FOLLOWUP_GENERATOR_SWITCHES}
    # Slip or gap SG2 changes a logged decision's values (R8's rule), so it is part of the generator payload and a
    # flip is a change point. SG1 changes none, so it is not.
    out["miss_cause_in_value"] = miss_cause_in_value_on(config)
    return out


#: The follow-up batch's landing ruling R12: every switch of the batch, as part of the prefetch boundary key, so a
#: flip between a prefetch and its serve starts a new job (``carried_in_prefetch`` too: it changes what the job does
#: with its carried valuation, though not the logger's values).
FOLLOWUP_SWITCHES: tuple[str, ...] = (*FOLLOWUP_GENERATOR_SWITCHES, "carried_in_prefetch")

#: Router speed stage 2's landing ruling R2: switches that change no value at a fixed draw count (only how soon the
#: input builds finish), so the numeric policy's random seed is derived from the boundary identity WITHOUT them
#: (``objective_chooser.numeric_seed``): whatever they are, its draws are main's. They stay in the prefetch key, the
#: generator payload and ``serving_switches``.
SEED_NEUTRAL_SWITCHES: tuple[str, ...] = ("held_reading_map", "pooled_connections")
#: IH4 (spec_instruct_handoff_v1 §7): what the boundary identity names only so a new preference, or a flip, starts a new
#: job, and that moves no value at a fixed draw count (``w_pref`` at 0 and no acceptance row changes nothing, bit for
#: bit): the switch in ``objective_settings`` and the ledger's mark beside it. ``objective_chooser.numeric_seed`` takes
#: both out, as it takes :data:`SEED_NEUTRAL_SWITCHES` out of the follow-up batch's snapshot.
SEED_NEUTRAL_OBJECTIVE_KEYS: tuple[str, ...] = ("preferences_inform_router",)
SEED_NEUTRAL_IDENTITY_KEYS: tuple[str, ...] = ("preferences",)
#: Slip or gap (spec_slip_vs_gap_v1 §7): what the boundary identity names so a flip, or a change in a topic's miss
#: sensor (a diagnosis landing, a probe answered), starts a new job: both switches in ``objective_settings``, the
#: sensor's mark beside them, and the sensor on a lesson offer's card record (:data:`MISS_CAUSE_OFFER_KEY`).
#: ``objective_chooser.numeric_seed`` takes them out, so a decision is valued on the same draws whatever they are
#: (common random numbers). SG1 moves no value at all. SG2 does move values, but only through its inputs (a diagnosed
#: topic's lesson and repair slopes), never through the draws: with it on, a decision whose topics have no diagnosed
#: miss is the predecessor's bit for bit, and one that has differs from it by the split alone.
COMMON_DRAW_OBJECTIVE_KEYS: tuple[str, ...] = ("miss_cause_sensor", "miss_cause_in_value")
COMMON_DRAW_IDENTITY_KEYS: tuple[str, ...] = ("miss_cause",)
MISS_CAUSE_OFFER_KEY = "miss_cause"


def followup_switch_snapshot(config: Any) -> dict[str, bool]:
    """R12: each of :data:`FOLLOWUP_SWITCHES` as it serves."""

    return {key: followup_on(config, key) for key in FOLLOWUP_SWITCHES}


def lesson_offers_on(config: Any) -> bool:
    """Teacher TE3b: lesson offers are candidates of the router objective, lesson minutes count on its clock and
    LOs with a pending lesson check join its population: the objective serving and TE1b's suggestions on (the router
    and its decision log, lessons able to open). Off, mvp-0.52 exactly."""

    if not objective_on(config):
        return False
    router = getattr(config, "router", None)
    teacher = getattr(config, "teacher", None)
    return bool(getattr(router, "enabled", False) and getattr(router, "log_decisions", False)
                and getattr(teacher, "enabled", False))


def failure_share_to_other_policy_on(config: Any) -> bool:
    """IH5: a failed policy's share of the objective's mix goes to the other policy, not staged: the tag, the
    objective serving and ``[router_objective] failure_share_to_other_policy`` (default true). Off, or below the tag,
    mvp-0.54's mix exactly."""

    section = getattr(config, "router_objective", None)
    return objective_on(config) and bool(
        getattr(section, "failure_share_to_other_policy", False))


def lessons_compete_with_followups_on(config: Any) -> bool:
    """IH2 (spec_instruct_handoff_v1 §5, the same unreleased tag as IH5): a lesson offer and a follow-up compete in one
    logged decision wherever a lesson is available: the tag, lesson offers on (:func:`lesson_offers_on`: the objective
    serving and TE1b's suggestions) and ``[router_objective] lessons_compete_with_followups`` (default true). Off, or
    below the tag, mvp-0.54's boundary exactly: forced items keep offers out and take a drawn one back."""

    section = getattr(config, "router_objective", None)
    return lesson_offers_on(config) and bool(
        getattr(section, "lessons_compete_with_followups", False))


def learner_preferences_on(config: Any) -> bool:
    """IH3 (spec_instruct_handoff_v1 §6, the same unreleased tag as IH5): the learner may name what would help and have
    it served: the tag and ``[router_objective] learner_preferences`` (default true). It needs no lesson offers and no
    objective: the options are whatever the plan can serve. Off, or below the tag, there is no link, nothing is served
    through it and no preference is written, as mvp-0.54."""

    section = getattr(config, "router_objective", None)
    return bool(getattr(section, "learner_preferences", False))


def workbench_is_open_item_on(config: Any) -> bool:
    """IH6 (spec_instruct_handoff_v1 §7b, the same unreleased tag as IH5): an open workbench is an open item for the plan:
    the tag, the workbench itself on (off, nothing can resume the problem, so it holds nothing) and
    ``[router_objective] workbench_is_open_item`` (default true). It needs no objective: any chooser's boundary crosses on
    a read. Off, or below the tag, mvp-0.54's reads exactly."""

    section = getattr(config, "router_objective", None)
    workbench = getattr(config, "workbench", None)
    return bool(getattr(workbench, "enabled", False)) and bool(
        getattr(section, "workbench_is_open_item", False))


def lesson_sources_follow_diagnosis_on(config: Any) -> bool:
    """IH7 (spec_instruct_handoff_v1 §7c, the same unreleased tag as IH5): a lesson opened from an offer or a suggestion
    reads the sections matching the diagnosed confusion beside the topic's linked ones: the tag and ``[router_objective]
    lesson_sources_follow_diagnosis`` (default true). It needs no objective: it changes what a lesson reads, never what
    the router decides. Off, or below the tag, the brief is mvp-0.54's, byte for byte."""

    section = getattr(config, "router_objective", None)
    return bool(getattr(section, "lesson_sources_follow_diagnosis", False))


def lesson_candidate_after_cold_miss_on(config: Any) -> bool:
    """The owner's decision 4 of Nov 9 (spec_instruct_handoff_v1 §8, the same unreleased tag as IH5): a topic with a missed
    cold check since its last lesson is a lesson candidate, with no threshold on the miss's size, count or error type (the
    router, the diagnosis and the teacher then decide through the algorithm), and its reason says when ("On Nov 3, a check
    on it wasn't fully right."): the tag and ``[router_objective] lesson_candidate_after_cold_miss`` (default true). It needs no
    objective: it says what is offerable wherever lesson candidates are built (an offer, TE1b's card, IH3's options). Off,
    or below the tag, mvp-0.54's ``cold_failing`` rule (the two latest cold checks below full) and its wording exactly."""

    section = getattr(config, "router_objective", None)
    return bool(getattr(section, "lesson_candidate_after_cold_miss", False))


def preferences_inform_router_on(config: Any) -> bool:
    """IH4 (spec_instruct_handoff_v1 §7, the same unreleased tag as IH5): what the learner said would help informs the
    objective's non-LLM parts and its LLM card: the tag, the objective serving and ``[router_objective]
    preferences_inform_router`` (default true). Staged reads nothing, whatever this says. Off, or below the tag, the
    acceptance model, the numeric policy, the trace and the card are the predecessor's exactly, and a preference
    freezes no inputs for them."""

    section = getattr(config, "router_objective", None)
    return objective_on(config) and bool(getattr(section, "preferences_inform_router", False))


def miss_cause_sensor_on(config: Any) -> bool:
    """SG1 (spec_slip_vs_gap_v1 §3): each candidate topic's ``miss_cause`` sensor is frozen in the objective's trace, on a
    lesson offer's card record and on the LLM policy's card: the tag, the objective serving and ``[router_objective]
    miss_cause_sensor`` (default true). No numeric value moves. Off, or below the tag, the trace, the offer's record and
    the card are the predecessor's byte for byte."""

    section = getattr(config, "router_objective", None)
    return objective_on(config) and bool(getattr(section, "miss_cause_sensor", False))


def miss_cause_in_value_on(config: Any) -> bool:
    """SG2 (spec_slip_vs_gap_v1 §3): the numeric policy's lesson and repair effect slopes split by the miss's cause, with
    the surprise calibrating ``p_gap``: SG1 on (it reads SG1's sensor) and ``[router_objective] miss_cause_in_value``
    (default true). Off, or below the tag, every value is the predecessor's."""

    section = getattr(config, "router_objective", None)
    return miss_cause_sensor_on(config) and bool(getattr(section, "miss_cause_in_value", False))


__all__ = [
    "CHECKS_EMBEDDED",
    "CHECKS_OFF",
    "CHECKS_RATE",
    "calibrated_weight_on",
    "check_mode",
    "fitted_models_on",
    "FOLLOWUP_GENERATOR_SWITCHES",
    "FOLLOWUP_SWITCHES",
    "SEED_NEUTRAL_IDENTITY_KEYS",
    "SEED_NEUTRAL_OBJECTIVE_KEYS",
    "SEED_NEUTRAL_SWITCHES",
    "followup_generator_switches",
    "followup_switch_snapshot",
    "failure_share_to_other_policy_on",
    "followup_on",
    "learner_preferences_on",
    "lessons_compete_with_followups_on",
    "lesson_offers_on",
    "monotone_combiner_on",
    "learned_tail_on",
    "pick_open_share",
    "stop_coin_rate",
    "workbench_is_open_item_on",
    "lesson_sources_follow_diagnosis_on",
    "lesson_candidate_after_cold_miss_on",
    "preferences_inform_router_on",
    "COMMON_DRAW_IDENTITY_KEYS",
    "COMMON_DRAW_OBJECTIVE_KEYS",
    "MISS_CAUSE_OFFER_KEY",
    "miss_cause_in_value_on",
    "miss_cause_sensor_on",
    "objective_on",
    "objective_scores_on",
    "sensors_in_value_on",
]
