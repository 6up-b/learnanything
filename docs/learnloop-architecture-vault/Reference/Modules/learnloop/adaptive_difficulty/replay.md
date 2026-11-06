---
title: "learnloop.adaptive_difficulty.replay"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/replay.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/replay.py"
source_commit: "workspace/uncommitted @ HEAD b1c67e1f52ee99dcfab1eeca5de019d636162201"
source_commit_timestamp: "2026-11-06T11:48:24-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.adaptive_difficulty.replay module"
  - "src/learnloop/adaptive_difficulty/replay.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.replay`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.replay` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The AD replayer: both views from ledgers and receipts, zero model calls (spec_adaptive_difficulty_v1 §5.6, §11.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/replay.py](../../../../../../src/learnloop/adaptive_difficulty/replay.py) |
| Source lines | 990 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD b1c67e1f52ee99dcfab1eeca5de019d636162201` |
| Commit timestamp | `2026-11-06T11:48:24-05:00` |

## Public API

- `lo_view_name(learning_object_id: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 79)
- `days(value: Any) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 83)
- `class ReplaySettings` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 98) — Which parts of the subject view run (the switches, and the harness arms of §10.4).
  - `key(self) -> str` (line 116; public)
  - `from_config(cls, config: Any) -> 'ReplaySettings'` (line 125; public)
- `class AttemptEvent` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 140)
- `class ClaimEvent` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 166)
- `class OpportunityEvent` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 176)
- `class Events` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 188)
  - `ordered(self) -> list[tuple[str, Any]]` (line 197; public)
- `surface_group(item: Any) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 264) — The item's surface group (mirrors ``substrate.canonical_projection.surface_group_id``, pinned equal by a test): a shared stimulus, source-example or solution-template family, else the legacy surface family, else the item.
- `forced_failure(attempt: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 277) — §5.3's "an empty 'I'm stuck'" row (Codex review F2): only an empty stuck submission, or a historical "I don't know" answer, is a fail whatever its grade.
- `load_events(connection: Any, vault: Any, repository: Any, *, as_of: str | None=None, settings: ReplaySettings=ReplaySettings(), view: Any=None) -> Events` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 332) — Read every replay input (no model call; current content only for ``reconstructed_current``).
- `class Snapshot` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 588) — The replay's result: the subject view, each LO's view, the traces.
  - `state_hash(self) -> str` (line 601; public)
  - `lo_view(self, learning_object_id: str) -> View` (line 608; public) — The LO's view (a fresh prior view when it has no eligible row yet).
- `class Context` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 694) — What a prequential observer knows about an attempt before its update (the harness, §10.4).
- `run(events: Events, settings: ReplaySettings=ReplaySettings(), *, trace: bool=True, observer: Any=None) -> Snapshot` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 709) — Replay the events into both views (§5.6), in fixed order, float64.
- `events_fingerprint(events: Events) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 846) — The digest of everything the replay reads (attempts with their frozen inputs, claims, reading opportunities, the relatedness structure and the vault maps).
- `snapshot(vault: Any, repository: Any, *, settings: ReplaySettings | None=None, connection: Any=None, as_of: str | None=None, view: Any=None) -> Snapshot` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 874) — The current state (cached per database, vault and settings while the replay's events are unchanged).
- `clear_cache() -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 909)
- `state_rows(snap: Snapshot, *, as_of: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 933)
- `rebuild(vault: Any, repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 945) — The AD replayer (``ad_state``, ``ad_attempt_trace``): clear and rebuild, zero model calls.

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/replay.py](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 71)
- `REPLAY_VERSION` ([src/learnloop/adaptive_difficulty/replay.py](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 73)
- `VIEW_SUBJECT` ([src/learnloop/adaptive_difficulty/replay.py](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 74)
- `CLAIM_SOURCES` ([src/learnloop/adaptive_difficulty/replay.py](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 75)
- `WARMTH_SOURCES` ([src/learnloop/adaptive_difficulty/replay.py](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 76)
- `_CACHE` ([src/learnloop/adaptive_difficulty/replay.py](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 830)
- `_CACHE_LOCK` ([src/learnloop/adaptive_difficulty/replay.py](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 831)

### Explicit exports

`__all__` declares:

- `AttemptEvent`
- `ClaimEvent`
- `Events`
- `OpportunityEvent`
- `REPLAY_VERSION`
- `ReplaySettings`
- `Snapshot`
- `VIEW_SUBJECT`
- `clear_cache`
- `days`
- `events_fingerprint`
- `forced_failure`
- `load_events`
- `lo_view_name`
- `rebuild`
- `run`
- `snapshot`
- `state_rows`

## Internal implementation anchors

- `_logit(p: float) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 90)
- `_capability(item: Any) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 206)
- `_guess(vault: Any, item: Any) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 219)
- `_facet_weights(vault: Any, item: Any) -> dict[str, float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 228)
- `_historical_signals(item: Any) -> dict[str, float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 237)
- `_frozen_signals(row: Mapping[str, Any]) -> dict[str, float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 245)
- `_audited(connection: Any, item: Any, content_hash: str | None, as_of: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 253)
- `_type_mass(vault: Any, attempt_type: str) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 287)
- `_exposures(connection: Any, view: Any) -> dict[str, list[float]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 292) — Each LO's exposure times (attempts and reveals) for warmth, read through the material view: an attempt or reveal on a withheld item warms nothing (Codex verify F20).
- `_warmth(exposures: Mapping[str, Sequence[float]], lo: str, served: float, own: float | None) -> float` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 307) — ``w_t = exp(-Δh / h_w)`` with ``Δh`` the hours since the last exposure to the LO before the serve.
- `_current_grade_unassessed(evidence: Sequence[Mapping[str, Any]], wholly_unassessed: Any) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 319) — PF-c over the attempt's current grading epoch (``grading_epochs.current_epoch``), never a per-criterion merge of every live epoch (Codex re-review F1): a historical regrade that dropped a verified criterion and left its own criteria unverified measures nothing, though the droppe…
- `_grid(settings: ReplaySettings) -> tuple[P.HyperPoint, ...]` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 618)
- `_override(bank: M.Bank, settings: ReplaySettings) -> M.Bank` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 625)
- `_new_subject_view(settings: ReplaySettings, structure: M.Structure) -> View` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 632)
- `_new_lo_view(settings: ReplaySettings) -> View` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 640)
- `_apply_claim(view: View, claim: ClaimEvent, events: Events, *, observed_subjects: set[str], observed_facets: set[str], los: Iterable[str] | None=None) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 646)
- `_apply_claims_for_lo(view: View, events: Events, lo: str, *, upto: float) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 672)
- `_mixture(view: View, record: M.UpdateRecord) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 678)
- `_plain(value: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 834)
- `_summary_payload(view: View, *, uniform_mask: np.ndarray | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/replay.py), line 916)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]] — imports `rebuild`; statically calls `rebuild`
- [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]] — imports `module`; statically calls `load_events`, `run`
- [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]] — imports `module`; statically calls `snapshot`
- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `module`; statically calls `days`, `snapshot`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]] — imports `module`; statically calls `load_events`
- [[Reference/Modules/learnloop/adaptive_difficulty/readiness|learnloop.adaptive_difficulty.readiness]] — imports `module`; statically calls `snapshot`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `module`; statically calls `load_events`, `run`
- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `module`; statically calls `run`
- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `module`; statically calls `load_events`
- [[Reference/Modules/learnloop/adaptive_difficulty/serving|learnloop.adaptive_difficulty.serving]] — imports `module`; statically calls `days`, `lo_view_name`, `snapshot`
- [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]] — imports `module`; statically calls `load_events`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `rebuild`; statically calls `rebuild`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `canonical_audits`; calls `canonical_audits`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `material_view`; calls `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]] — imports `module`; calls `Bank`, `Structure`, `facet_name`, `subject_name`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `entry`, `epoch_of`; calls `entry`, `epoch_of`
- [[Reference/Modules/learnloop/adaptive_difficulty/outcomes|learnloop.adaptive_difficulty.outcomes]] — imports `module`; calls `AttemptFacts`, `category`, `help_questions_from_rows`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`; calls `hyper_grid`, `uniform_points`, `versions`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `module`; calls `live_judgments`, `lo_subject`, `load_structure`
- [[Reference/Modules/learnloop/adaptive_difficulty/state|learnloop.adaptive_difficulty.state]] — imports `ItemSpec`, `View`, `normalized_weights`; calls `ItemSpec`, `View`, `normalized_weights`
- [[Reference/Modules/learnloop/adaptive_difficulty/successor|learnloop.adaptive_difficulty.successor]] — imports `history_fallback`, `lesson_opportunities_on`, `successor_active`; calls `history_fallback`, `lesson_opportunities_on`, `successor_active`
- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `learning_opportunity_events`; calls `learning_opportunity_events`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/ad_receipts|learnloop.db.stores.ad_receipts]] — imports `module`; calls `_loads`, `has_table`
- [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] — imports `module`; calls `clear_derived`, `has_table`, `write_state`, `write_trace`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `wholly_unassessed`; calls `wholly_unassessed`
- [[Reference/Modules/learnloop/grading_epochs|learnloop.grading_epochs]] — imports `current_epoch`; calls `current_epoch`
- [[Reference/Modules/learnloop/learner/blueprint_projection|learnloop.learner.blueprint_projection]] — imports `guess_floor_for_item`; calls `guess_floor_for_item`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `default_capability_for`; calls `default_capability_for`

### Platform and third-party dependencies

- Standard library: `__future__`, `bisect`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `logging`, `math`, `threading`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]], [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]], [[Reference/Modules/learnloop/adaptive_difficulty/dose|learnloop.adaptive_difficulty.dose]], [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]], [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_goal_focus_follows_the_live_decision_view_with_promoted_predictor_off`
  - `test_the_replay_cache_never_serves_a_snapshot_across_a_protection_change`
  - `test_with_no_protection_a_frozen_dose_on_an_absent_facet_stands`
- [tests/test_ad23_fix_r5.py](../../../../../../tests/test_ad23_fix_r5.py) — direct import
  - `test_the_report_forecasts_with_the_configured_coupling`
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_a_claim_moves_no_forecast_through_a_withheld_items_facet`
  - `test_practice_minutes_come_from_the_visible_practice_cohort`
  - `test_report_sensitivity_never_re_forecasts_a_withheld_item`
  - `test_with_the_predicate_unavailable_the_report_discloses_zero_observations`
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_draw_reads_reading_recorded_since_the_last_serve`
  - `test_a_stuck_answer_is_forced_to_fail_only_when_empty`
  - `test_a_wholly_unassessed_frozen_attempt_trains_nothing_and_tests_no_cell`
  - `test_an_i_dont_know_answer_still_fails_whatever_its_grade`
  - `test_the_grid_arm_never_reads_a_later_answer`
  - `test_the_live_cache_follows_replacements_updates_and_other_connections`
- [tests/test_ad23_owner_decisions.py](../../../../../../tests/test_ad23_owner_decisions.py) — direct import
  - `test_ad_reads_history_through_its_own_fallback_and_field_keeps_its_own`
- [tests/test_ad23_successor.py](../../../../../../tests/test_ad23_successor.py) — direct import
  - `test_the_switches_compose`
- [tests/test_ad2_model.py](../../../../../../tests/test_ad2_model.py) — direct import
  - `test_ad_never_writes_evidence`
  - `test_claims_applied_at_created_at_and_request_claims_excluded`
  - `test_rebuild_byte_identical`
  - `test_replay_uses_frozen_inputs_and_explicit_history`
  - `test_surface_group_mirrors_the_projection`
  - `test_warmth_uses_only_pre_serve_exposures`
- [tests/test_ad3_reading.py](../../../../../../tests/test_ad3_reading.py) — direct import
  - `test_a_question_counts_once_and_no_verdict_reaches_evidence`
  - `test_reading_raises_prediction_never_evidence`
  - `test_reading_self_check_switch_restores_d20_and_is_moot_without_reading`
- [tests/test_ad3_subject_view.py](../../../../../../tests/test_ad3_subject_view.py) — direct import
  - `test_coupling_is_prediction_only`
  - `test_readiness_numbers_from_subject_view_with_untested_cells`
  - `test_shared_terms_alone_never_show_likely_ready`
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — direct import
  - `test_a_reading_receipt_recorded_under_other_protection_is_mapped_again`
  - `test_frozen_serve_signals_trained_on_a_newly_protected_answer_are_not_replayed`
  - `test_the_replay_cache_and_the_alias_memo_are_keyed_by_the_epoch`
- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — direct import
- [tests/test_ad_guard_offer_receipts.py](../../../../../../tests/test_ad_guard_offer_receipts.py) — direct import
  - `test_the_serving_snapshot_and_the_report_run_with_zero_denials`
- [tests/test_ad_guard_reachable_reads.py](../../../../../../tests/test_ad_guard_reachable_reads.py) — direct import
  - `test_a_legacy_grade_interpretation_reads_its_pooled_alphas_with_zero_denials`
- [tests/test_ad_protected_readings.py](../../../../../../tests/test_ad_protected_readings.py) — direct import
  - `test_attempt_evidence_from_a_visible_span_of_a_mixed_reading_is_unchanged`
- [tests/test_rebuild_orchestrator.py](../../../../../../tests/test_rebuild_orchestrator.py) — direct import
  - `test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear`
- [tests/test_rospeed_join.py](../../../../../../tests/test_rospeed_join.py) — direct import
  - `test_the_indexed_resolver_gives_the_landing_codes_rows`
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
  - `test_after_a_lesson_the_curve_the_objective_reads_has_the_topics_position`
  - `test_replay_equivalence_live_fresh_and_rebuilt`
  - `test_switch_off_is_the_predecessor_exactly`
  - `test_the_reports_lesson_row_at_the_prior_and_after_lessons`

## Modification guidance

- Make changes here when the responsibility remains replay within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/replay.py](../../../../../../src/learnloop/adaptive_difficulty/replay.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
