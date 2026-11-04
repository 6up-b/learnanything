# Router objective RO1: Codex review fixes

Branch `router/ro1-interval`, worktree `learnanything-ro1`. Codex reviewed the stage at `54836fc5b0` (job
`20261104-182738-9yiEfX`, gpt-6.1-sol). It returned three Medium findings and no High ones. All three were
reproduced and fixed, and none was rejected. No model, Decider or embedding call was made, and no money was
spent. No schema change: migration 242 and the head fixture are untouched.

Owner decisions in force (2026-10-12): the spec defaults are accepted; Codex runs paid roles on the subscription;
the Decider is `perplexity/pplx-decider-v1.1-27b` on OpenRouter; frictionless defaults (honest labels, generous
defaults, live changes behind kill switches). The owner's decisions in spec §1 were not re-argued.

## Findings

| ID | Severity | Title | Verdict | Commit | Test (tests/…) or reason |
|---|---|---|---|---|---|
| F1 | Medium | The router card's week of activity ignores availability | Fixed | `d822647550` | `test_ro1_availability.py::test_the_whole_card_reads_no_exam_before_its_import_at_the_tag[tag,off,below]` (the whole `CardGatherer.inputs`: week of activity, per-topic evidence, `as_of_attempt_id`, recent work; before and after the import), `::test_the_weeks_activity_counts_an_import_inside_its_week_once_it_is_known` (the window stays occurrence time). Both failed on the old `_interaction`: `[tag]` read `attempts=3`, `active_days=1` on May 5 for an exam imported May 19 |
| F2 | Medium | The report's interval ratio runs from an ineligible attempt | Fixed | `73f023834f` | `test_ro1_upgrade_report.py::test_a_primed_retry_after_the_review_is_not_the_intervals_anchor` (F2's case: 1.5; the old code reports 6.0, reproduced on the old module), `::test_serving_reads_the_anchor_past_a_primed_retry_and_a_held_grade` (a real primed retry, and a held grade through a faked `held_for_review_attempts`) |
| F3 | Medium | The report's queue due and review load ignore serving's rules | Fixed | `73f023834f` | `test_ro1_upgrade_report.py::test_the_report_counts_the_queue_and_load_admission_counts` (a paused LO, a waiting "Check once", a Light touch target of 0.80 whose effective due is later than the stored one, an inactive item; the report's population equals the plan's `_review_items` item for item; the old code counts `after = 5` with four of the five items unservable, reproduced), `::test_the_observer_reads_the_live_database_read_only_with_commitments`, `::test_an_observer_failure_is_a_shadow_failure`; `test_shadow_rebuild.py::test_shadow_rebuild_cli_json_is_stable_and_leaves_live_hash_unchanged` (the CLI JSON, the live hash and receipts unchanged) |

### F1: the week of activity

`CardGatherer._interaction` now keeps its 7-day `created_at` window, which is when the work happened, and adds
`AND coalesce(received_at, created_at) < now` when `_attempt_time` says availability: at the tag, with
`[router_objective] available_at_reads` on, on a database with the column. Otherwise it runs the predecessor's SQL
byte for byte. `question_events` and `reveal_events` have no `received_at` and are written when they happen, so
they are unchanged.

### F2 and F3: the report reads serving

- `engine.review_population(vault, repository, intent, minutes=)` is the body of `_review_items`, which now calls
  it. The plan's admission and the report therefore share one population: active, servable items in an intent
  that isn't excluded or held, at the effective due date, with the review the interval runs from.
- `schedule_effects.serving_schedule(vault, repository, as_of=)` takes that read with the build's own intent view
  (`intent_serving`), at one minute per item. It also returns the recall-target anchors (`load_anchors`: the
  latest FSRS-eligible attempt not held for review).
- `shadow_rebuild(..., observe=)` calls the observer on the live database (attached read-only, under the baseline
  config) and on the replayed copy (under the candidate). It returns the results as `observed_before` and
  `observed_after`. If the observer fails, the run raises `ShadowRebuildError` naming the side. The substrate
  still doesn't import the plan (L4/L5): the CLI passes the observer in.
- `schedule_effects(..., serving_before=, serving_after=)`: the queue due and the review load come from serving's
  read. The interval ratio is still over the stored due dates, but it is measured from the anchor, falling back
  to the stored column only when an item has no qualifying review (imported state, as
  `IntentServing.last_review_at` does). Activity cards keep their shifts and ratios. Nothing serves their due
  dates, so they get no queue entry, which is the honest label.
- The record's synthetic numbers, rerun with the new code at 0, 3, 7 and 14 days: identical. That vault has no
  commitment, primed retry, held grade or inactive item. Spec §5.7 and `router-ro1.md` are updated.

**One limit, recorded rather than changed.** With no commitment, and recall targets at their 0.90 default
for uncommitted items, `intent_serving` returns None. The plan's own `_review_items` then measures each interval
from `last_attempt_at`, not from the anchor. The report's review load is admission's number, so it does the
same. Its interval ratio always uses the anchor. Changing admission's anchor in that case would change what the
live plan admits. That is outside RO1 and goes through the algorithm-change playbook, so it is listed as an open
question.

### The review's other claims

- "Nothing in §5 was dropped": corrected in `router-ro1.md` item 8 (F1).
- "The combination test checks gate booleans": the F1 tests now observe availability's behavior for the tag,
  the switch off and the predecessor on the whole card. The self-report gate's behavior is observed in
  `test_ro1_self_report.py`. No further combination test was added.
- "RO1-specific crash and concurrency exercises" (§5.6 row): no finding names a defect, and this step adds no
  write path (the observer is read-only on the live side). Not widened.

## Gate

Run in the worktree on `4c9e2af868` (the code and catalog commits; this file is the next commit). Every pytest
inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6`, TMPDIR in the stage's
scratch directory. Non-pytest Python ran under `env -i PATH=$PATH HOME=<empty> CODEX_HOME=<empty>
LEARNLOOP_CONFIG_DIR=<empty>`. **One slip:** a single string-replacement patch on `substrate/shadow_rebuild.py` ran
with `python3` outside `env -i`. It imported nothing from learnloop and made no network or model call. Every later
patch used the Edit tool.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install --offline pypdfium2==5.14.0` | ok |
| `uv run lint-imports --no-cache` | 42 kept, 0 broken (frozen cycles kept) |
| `tests/test_ro1_availability.py` after F1; the same with the fix reverted | 15 passed; reverted: 2 failed (the new F1 tests), 13 passed |
| `tests/test_ro1_upgrade_report.py` after F2/F3 | 7 passed |
| Targeted: 50 files (below) | **886 passed, 3 xfailed, 0 failed** (387 s) |
| `tests/test_intent_plan.py`, `tests/test_daily_plan_build.py` (the plan engine, run after the batch) | 31 passed |
| `module_generate.py` then `module_validate.py` | PASS (1191 notes; links 41226/41226, 39235/39235) |
| Durability lane | not needed: no migration, no DB or connection code changed |
| DB reference scripts | not needed: no schema change |
| Frontend, cargo | not touched |

Targeted files: every `test_ro1_*.py`; every test file that names `router_card`/`CardGatherer`,
`shadow_rebuild`/`schedule_effects`/`_review_items`/`review_population`, `review_load`/`projected_review_load`;
and the contract and audit files: the CLI help snapshot, the
sidecar serializer snapshot, the desktop RPC contract, architecture, the display-label audit
(`test_measurement_state_labels.py`) and the process-launch allowlist (`test_codex_lockdown_round3.py`).

- tests/test_approach_map_replay.py
- tests/test_architecture.py
- tests/test_batch3_landing.py
- tests/test_cli_help_snapshot.py
- tests/test_codex_lockdown_round3.py
- tests/test_cold_retry_reschedule.py
- tests/test_compare_sources_keep.py
- tests/test_curriculum_c0b_landing.py
- tests/test_curriculum_c1_plan_follows_path.py
- tests/test_daily_plan_admission.py
- tests/test_daily_plan_review_regressions.py
- tests/test_desktop_rpc_contract.py
- tests/test_followup_rival_factor.py
- tests/test_forecast_receipts.py
- tests/test_help_fold_attach_successor.py
- tests/test_hint_telemetry.py
- tests/test_intent_codex_review.py
- tests/test_intent_exclusion.py
- tests/test_mcp_c1a_landing.py
- tests/test_mcp_tools.py
- tests/test_measurement_state_labels.py
- tests/test_method_explicit_landing.py
- tests/test_model_grade_lane.py
- tests/test_project_experiment_store.py
- tests/test_reader_digest_narrative.py
- tests/test_reader_followups.py
- tests/test_reader_followups_successor.py
- tests/test_reader_question_note_id_placement.py
- tests/test_rebuild_equivalence.py
- tests/test_reference_gate_imports.py
- tests/test_regrade_contract_successor.py
- tests/test_regrade_contract_upgrade.py
- tests/test_reread_safety_landing.py
- tests/test_ro1_availability.py
- tests/test_ro1_interval_factor.py
- tests/test_ro1_projection.py
- tests/test_ro1_self_report.py
- tests/test_ro1_successor.py
- tests/test_ro1_upgrade_report.py
- tests/test_router_card.py
- tests/test_router_r2a_landing.py
- tests/test_router_r2c_teach_back.py
- tests/test_router_reader_activity.py
- tests/test_shadow_rebuild.py
- tests/test_sidecar_serializer_snapshot.py
- tests/test_sqlite_file_copies.py
- tests/test_teacher_te0_confidence_events.py
- tests/test_teacher_te0_review_fixes.py
- tests/test_teacher_te1b_review_fixes.py
- tests/test_teacher_te1_successor.py

## Open question for the owner

- With intent's view off (no commitment, and recall targets at their 0.90 default for uncommitted items), admission's
  review load measures an item's interval from `last_attempt_at`. A primed retry or a held grade therefore
  shortens it. The view-on path has used the anchor since DL2's review F5. This predates RO1. Changing it would
  change admitted new material, so it would need its own playbook entry.
