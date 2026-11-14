"""The kill switches that restore a predecessor, as one table: config path, the tag it serves past, its default.

Read by scripts/vault_report.py (the owner's "does any vault set one?" before a removal step) and by the tests
that keep this table complete. Nothing that serves a vault reads it, so a row costs no behaviour.

It lives in the config package, beside the schema it is checked against, not in the schema: the schema says what a
vault can set; this answers a question about tags and the version floor (ADR-019's rule reads both). A removal step
deletes a row in the commit that deletes the field. The module imports nothing of LearnLoop; importing it runs the
package's ``__init__``, which loads the schema.

Two tables, because the standing rule needs a tag:

* TAGGED_SWITCHES: the switch of an algorithm successor, with the tag it ships with. A field is one of
  these when algorithm_versions.py, its tag predicate in router_objective_switches.py or its own
  documentation names it as that tag's kill switch.
* UNTAGGED_SWITCHES: a field whose documentation says its off value restores the previous behaviour but that
  has no successor tag (or, for four rows, is a per-task switch that is a content task at every version), so no
  floor can pass it. A removal needs an owner decision by name.

tests/test_kill_switches.py checks every path and default against LearnLoopConfig and scans the schema and
algorithm_versions.py for a switch the table lacks. A leaf only the tests can see is not in this module.
"""

from __future__ import annotations

from typing import NamedTuple


class KillSwitch(NamedTuple):
    path: str  # dotted path in learnloop.toml
    tag: str | None  # the successor tag the switch ships with; None in UNTAGGED_SWITCHES
    default: bool | float | str  # the value the schema ships (a switch set to it changes nothing)


def _untagged(path: str, default: bool | float | str) -> KillSwitch:
    return KillSwitch(path, None, default)


#: One tag's switch lives outside learnloop.toml, so no table here can name it: the phone host's phone_probes
#: (mvp-0.54) in mobile.toml (learnloop_mobile/config.py).
OUTSIDE_LEARNLOOP_TOML: tuple[str, ...] = ("phone_probes (mvp-0.54), in the phone host's mobile.toml",)

TAGGED_SWITCHES: tuple[KillSwitch, ...] = (
    # Grading, attempts, replay
    KillSwitch("diagnosis.split_enabled", "mvp-0.10", True),
    KillSwitch("diagnosis.shadow", "mvp-0.10", False),
    KillSwitch("stuck_prompt.enabled", "mvp-0.13", True),
    KillSwitch("proof_check.enabled", "mvp-0.17", True),
    KillSwitch("required_method.enabled", "mvp-0.25", True),
    KillSwitch("hints.fold_follows_attach", "mvp-0.42", True),
    KillSwitch("mastery.claim_fixes_enabled", "mvp-0.33", True),
    KillSwitch("replay.ledger_bounded", "mvp-0.34", True),
    KillSwitch("practice.attempt_keeps_content_state", "mvp-0.37", True),
    KillSwitch("ask.cold_help_converts", "mvp-0.35", True),
    KillSwitch("practice.reschedule_cold_after_assist", "mvp-0.38", True),
    KillSwitch("eligibility.enabled", "mvp-0.27", True),
    # Placement, recurrence, learner-text gaps, sources, value of information, the Decider
    KillSwitch("placement.enabled", "mvp-0.11", True),
    KillSwitch("placement.initial_probes", "mvp-0.11", False),
    KillSwitch("placement.unevidenced_return", "mvp-0.56", True),
    KillSwitch("recurrence.enabled", "mvp-0.12", True),
    KillSwitch("learner_text_gaps.sooner_check_enabled", "mvp-0.16", True),
    KillSwitch("source_service.source_first_needs", "mvp-0.19", True),
    KillSwitch("voi_stopping.enabled", "mvp-0.21", True),
    KillSwitch("voi_stopping.probe_episodes", "mvp-0.21", True),
    KillSwitch("voi_stopping.followups", "mvp-0.21", True),
    KillSwitch("voi_stopping.teach_back", "mvp-0.21", True),
    KillSwitch("voi_stopping.project_probes", "mvp-0.21", True),
    KillSwitch("voi_stopping.robust_gate_with_value", "mvp-0.21", False),
    KillSwitch("diagnosis.probe_lane_reads_diagnosis", "mvp-0.21", True),
    KillSwitch("diagnosis.probe_lane_pending", "mvp-0.21", "hold_out"),
    KillSwitch("learner_text_gaps.decider_enabled", "mvp-0.22", True),
    KillSwitch("decider_routes.learner_gap_judge", "mvp-0.22", True),
    KillSwitch("decider_routes.learner_gap_kind", "mvp-0.22", True),
    KillSwitch("decider_routes.misconception_match", "mvp-0.22", True),
    KillSwitch("decider_routes.diagnosis_link_judgment", "mvp-0.22", True),
    KillSwitch("decider_routes.field_question_classification", "mvp-0.22", True),
    KillSwitch("decider_routes.contamination_leak_judgment", "mvp-0.22", True),
    KillSwitch("decider_routes.contamination_reveal_judgment", "mvp-0.22", True),
    # The plan, the router frame, reading, intent, follow-ups
    KillSwitch("plan.enabled", "mvp-0.14", True),
    KillSwitch("plan.new_admission_enabled", "mvp-0.14", True),
    KillSwitch("plan.reading_blocks", "mvp-0.14", True),
    KillSwitch("router.probe_tie_admission", "mvp-0.15", True),
    KillSwitch("router.enabled", "mvp-0.23", True),
    KillSwitch("router.mode", "mvp-0.24", "mixture"),
    KillSwitch("router.restraint", "mvp-0.24", True),
    KillSwitch("router.lesson_suggestions.enabled", "mvp-0.43", True),
    KillSwitch("router.lesson_suggestions.in_objective", "mvp-0.53", True),
    KillSwitch("reading_paths.plan_uses_path", "mvp-0.32", True),
    KillSwitch("curriculum.plan_uses_path", "mvp-0.40", True),
    KillSwitch("curriculum.enabled", "mvp-0.40", True),
    KillSwitch("followups.enabled", "mvp-0.39", True),
    KillSwitch("intent.enabled", "mvp-0.29", True),
    KillSwitch("intent.recall_targets_enabled", "mvp-0.29", True),
    KillSwitch("data_capture.serving", "mvp-0.44", True),
    KillSwitch("followup.generate_and_serve", "mvp-0.45", True),
    KillSwitch("workbench.field_signals_enabled", "mvp-0.31", True),
    # The teacher and adaptive difficulty
    KillSwitch("teacher.enabled", "mvp-0.41", True),
    KillSwitch("teacher.weight.learned", "mvp-0.41", True),
    KillSwitch("teacher.weight.source", "mvp-0.41", "pool"),
    KillSwitch("teacher.probes", "mvp-0.51", True),
    KillSwitch("adaptive_difficulty.enabled", "mvp-0.30", True),
    KillSwitch("adaptive_difficulty.selection", "mvp-0.30", True),
    KillSwitch("adaptive_difficulty.generation_contract", "mvp-0.30", True),
    KillSwitch("adaptive_difficulty.promoted_predictor", "mvp-0.30", True),
    KillSwitch("adaptive_difficulty.learned_coupling", "mvp-0.30", False),
    KillSwitch("adaptive_difficulty.reading_opportunities", "mvp-0.30", True),
    KillSwitch("adaptive_difficulty.reading_self_check", "mvp-0.30", True),
    KillSwitch("adaptive_difficulty.lesson_opportunities", "mvp-0.52", True),
    # The router objective, RO1 to RO6
    KillSwitch("scheduler.surprise.remove_interval_factor", "mvp-0.46", True),
    KillSwitch("router_objective.available_at_reads", "mvp-0.46", True),
    KillSwitch("router_objective.self_report_not_validated", "mvp-0.46", True),
    KillSwitch("router_objective.enabled", "mvp-0.47", True),
    KillSwitch("router_objective.sensors_in_value", "mvp-0.47", True),
    KillSwitch("router_objective.stop_coin", "mvp-0.48", 0.05),
    KillSwitch("router_objective.check_rate", "mvp-0.48", "embedded"),
    KillSwitch("router_objective.pick_open_share", "mvp-0.48", 0.1),
    KillSwitch("router_objective.fitted_models", "mvp-0.48", True),
    KillSwitch("router_objective.learned_tail", "mvp-0.49", True),
    # The router objective's follow-up batch, instruct hand-off, slip or gap
    KillSwitch("router_objective.combiner_trace_outcomes", "mvp-0.50", True),
    KillSwitch("router_objective.merged_sessions", "mvp-0.50", True),
    KillSwitch("router_objective.consistent_review_draw", "mvp-0.50", True),
    KillSwitch("router_objective.monotone_combiner", "mvp-0.50", True),
    KillSwitch("router_objective.ad_predictive_link", "mvp-0.50", True),
    KillSwitch("router_objective.carried_in_prefetch", "mvp-0.50", True),
    KillSwitch("router_objective.scope_extension", "mvp-0.50", True),
    KillSwitch("router_objective.held_ad_link", "mvp-0.50", True),
    KillSwitch("router_objective.held_reading_map", "mvp-0.50", True),
    KillSwitch("router_objective.pooled_connections", "mvp-0.50", True),
    KillSwitch("router_objective.failure_share_to_other_policy", "mvp-0.55", True),
    KillSwitch("router_objective.lessons_compete_with_followups", "mvp-0.55", True),
    KillSwitch("router_objective.learner_preferences", "mvp-0.55", True),
    KillSwitch("router_objective.workbench_is_open_item", "mvp-0.55", True),
    KillSwitch("router_objective.lesson_sources_follow_diagnosis", "mvp-0.55", True),
    KillSwitch("router_objective.lesson_candidate_after_cold_miss", "mvp-0.55", True),
    KillSwitch("router_objective.preferences_inform_router", "mvp-0.55", True),
    KillSwitch("router_objective.miss_cause_sensor", "mvp-0.57", True),
    KillSwitch("router_objective.miss_cause_in_value", "mvp-0.57", True),
    # The floor's own switch, and the head's
    KillSwitch("figures.prefetch.pressed_waits", "mvp-0.58", True),
    KillSwitch("facet_diagnostic.canonical_belief_fixes", "mvp-0.59", True),
)

UNTAGGED_SWITCHES: tuple[KillSwitch, ...] = tuple(_untagged(*row) for row in (
    # Per-task switches that are a content task at every version, and the router objective's receipts
    ("decider_routes.facet_span_support", True),
    ("decider_routes.required_method_statement", True),
    ("decider_routes.ad_feature_audit", True),
    ("router_objective.receipts", True),
    # Every other field whose documentation says off restores the predecessor, with no tag
    ("figures.predictions_enabled", True),
    ("figures.region_enabled", True),
    ("figures.revisions_enabled", True),
    ("figures.advanced_panels_enabled", True),
    ("figures.offers_enabled", True),
    ("figures.show_me_enabled", True),
    ("figures.sketch_enabled", True),
    ("figures.checked_labels_enabled", True),
    ("goals.held_out_selection", True),
    ("diagnosis.history_includes_prior_analysis", "randomized"),
    ("hints.adaptive_enabled", True),
    ("workbench.enabled", True),
    ("workbench.help_enabled", True),
    ("reader_intent.enabled", True),
    ("library_ask.enabled", True),
    ("figures.rich_tiers_enabled", True),
    ("facet_identity.enabled", True),
    ("teacher.visuals", True),
    ("source_retrieval.enabled", True),
    ("mastery.irt.enabled", True),
    ("mastery.irt.difficulty_from_prior", True),
    ("scheduler.followup.gate_mode", "score"),
    ("tutor_qa.adopt_reference_questions", True),
    ("tutor_qa.expanded_delivery", True),
    ("diagnosis.grading_support", True),
    ("hints.telemetry_enabled", True),
    ("reader_inquiry.enabled", True),
    ("workbench.passage_draw_enabled", True),
    ("digest.enabled", True),
    ("digest.narrative_quotes_inquiry", True),
    ("reader_tutor.retrieval_enabled", True),
    ("reader_tutor.learner_state_enabled", True),
    ("figures.author_learner_state", True),
    ("reader_compare.scope_enabled", True),
    ("reader_compare.by_point", True),
    ("practice.as_printed.enabled", True),
    ("roles.on_demand_enabled", True),
    ("curriculum.exam_units_in_scope", True),
    ("reader.correspondence.enabled", True),
    ("reader.side_by_side.enabled", True),
    ("embedding.map_neighbors_enabled", True),
    ("graph_nomination.enabled", True),
    ("source_retrieval.tutor_deadline_cancels", False),
    ("source_retrieval.complete_passages", True),
    ("facet_identity.reword_confirm", True),
    ("plan.reading_from_furthest", True),
    ("plan.deterministic_staged_plans", True),
    ("followup.hypothesis_marks", True),
    ("adaptive_difficulty.history_answer_excerpts", True),
    ("ui.practice_feedback", "simple"),
    ("ui.shell", "simple"),
    ("teacher.confidence_events_enabled", True),
    ("teacher.episode_log", True),
    ("ask.panel_enabled", True),
    ("practice.device_eligibility_enabled", True),
))
