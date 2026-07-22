"""P4 -- the canonical action taxonomy (spec_p4_controller_and_scale §1.1).

Every live controller decision uses exactly one top-level action. Repair, completion,
transfer, integration, and ``depth_progression`` are ``practice`` subtypes. Baseline/
readiness/re-entry measurement stays ``measure_diagnostic`` even when it uses
predictive EIG; open-world authoring/validation is ``expand_model`` and is never
disguised as more measurement.

This taxonomy is spec-defined only -- there was no enum in the tree. The legacy
``intent_planner`` six-intent order is explicitly NOT promoted here (§2 code-truth).
These are structural vocabularies, not decision parameters (§17).
"""

from __future__ import annotations

# The seven top-level canonical actions (§1.1).
MEASURE_DIAGNOSTIC = "measure_diagnostic"
INSTRUCT = "instruct"
PRACTICE = "practice"
ASSESS_TERMINAL = "assess_terminal"
MAINTAIN = "maintain"
EXPAND_MODEL = "expand_model"
STOP = "stop"

ACTIONS: tuple[str, ...] = (
    MEASURE_DIAGNOSTIC, INSTRUCT, PRACTICE, ASSESS_TERMINAL, MAINTAIN,
    EXPAND_MODEL, STOP,
)

# ``practice`` subtypes (§1.1).
COMPLETION_OR_REPAIR = "completion_or_repair"
INTEGRATION = "integration"
TRANSFER = "transfer"
DEPTH_PROGRESSION = "depth_progression"
FLUENCY = "fluency"

PRACTICE_SUBTYPES: tuple[str, ...] = (
    COMPLETION_OR_REPAIR, INTEGRATION, TRANSFER, DEPTH_PROGRESSION, FLUENCY,
)

# Typed stop reasons (§4.5). ``stop`` is a successful action, never a guilt backlog.
STOP_GOAL_SATISFIED = "goal_satisfied"
STOP_GOAL_SATISFIED_NO_AUTHORIZED_DEPTH = "goal_satisfied_no_authorized_depth"
STOP_NO_POSITIVE_ROBUST_VALUE = "no_positive_robust_value"
STOP_SAME_ACTION_ACROSS_HYPOTHESES = "same_action_across_hypotheses"
STOP_BURDEN_OR_FATIGUE_CAP = "burden_or_fatigue_cap"
STOP_WAITING_FOR_DELAY_OR_FRESH_SURFACE = "waiting_for_delay_or_fresh_surface"
STOP_MODEL_EXPANSION_NEEDED = "model_expansion_needed"
STOP_LEARNER_PAUSED_OR_STOPPED = "learner_paused_or_stopped"
STOP_NO_FEASIBLE_ACTIVITY = "no_feasible_activity"

STOP_REASONS: tuple[str, ...] = (
    STOP_GOAL_SATISFIED, STOP_GOAL_SATISFIED_NO_AUTHORIZED_DEPTH,
    STOP_NO_POSITIVE_ROBUST_VALUE, STOP_SAME_ACTION_ACROSS_HYPOTHESES,
    STOP_BURDEN_OR_FATIGUE_CAP, STOP_WAITING_FOR_DELAY_OR_FRESH_SURFACE,
    STOP_MODEL_EXPANSION_NEEDED, STOP_LEARNER_PAUSED_OR_STOPPED,
    STOP_NO_FEASIBLE_ACTIVITY,
)


def is_action(action: str) -> bool:
    return action in ACTIONS


def validate(action: str, subtype: str | None) -> None:
    """Raise if the action/subtype pair is not in the canonical taxonomy."""

    if action not in ACTIONS:
        raise ValueError(f"unknown canonical action: {action!r}")
    if action == PRACTICE:
        if subtype is not None and subtype not in PRACTICE_SUBTYPES:
            raise ValueError(f"unknown practice subtype: {subtype!r}")
    if action == STOP and subtype is not None and subtype not in STOP_REASONS:
        raise ValueError(f"unknown stop reason: {subtype!r}")
