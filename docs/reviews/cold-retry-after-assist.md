# The cold-retry reschedule: a fresh cold retry after help on a cold follow-up (mvp-0.38)

Stage `cold-retry-after-assist`, branch `sched/cold-retry-after-assist` in `learnanything-dl2`, base `1bcde2096`
(main: latest algorithm `mvp-0.37`, migrations through 226, head fixture `migration_head_226`). Owner decision
2026-10-25 (Reader CA2 follow-up Q4, recorded as an open question in `docs/reviews/reader-ca2-one-ask.md` §3): when
the learner takes help on a cold follow-up, the attempt still converts to practice with help (CA2,
`ask.cold_help_converts`), and a fresh cold retry is now scheduled, so the repair can still be measured cold instead
of being left unmeasurable. Process: `docs/algorithm-change-playbook.md`.

No migration, no schema change, no frontend or `src-tauri` change. Fakes only: no model call, no paid call, no owner
vault or copy of one (synthetic vaults only).

## 1. Where things happen today (mvp-0.37)

| What | Where |
|---|---|
| A repair cold retry is **created** | `remediation.record_remediation_attempt`, primed branch: the episode's primed attempt schedules a `cold_retry` on the episode's `cold_item_id`, `not_before = primed attempt + COLD_RETRIEVAL_DELAY` (1 day), `expires_at = not_before + 30 days` |
| Its **cold surface** is chosen | `remediation.start_remediation_treatment`: the best-ranked item (`_rank_items`) on a surface group other than the primed item's whose material the learner was not shown (`exposed_items`, held-out material included) |
| Help on a due cold follow-up is **admitted** | `serve_eligibility._decide_submit` (`COLD_CHECK_HELP_TAKEN`, claims no task), under `serve_eligibility.help_converts_active` (mvp-0.35+, `ask.cold_help_converts`) |
| The assisted attempt **does not consume** it | `record_remediation_attempt` (`assisted_attempt` -> return) and `certification_cold_probe._record_probe_outcome` (returns None) |
| The measurement is **withdrawn** | at the next serve of the item: `serve_eligibility._decide_cold_check` sees the item practised since the task was created (`COLD_CHECK_PRACTISED_SINCE_SCHEDULED`) and `scheduler.apply_eligibility_writes` -> `remediation.withdraw_cold_measurement` records `unmeasurable_no_held_out_surface` and expires the task. If the item is never served again, the expiry sweep labels it at its window's end |

So under mvp-0.37 the repair ends unmeasurable. The coldness receipt explains why the same surface cannot simply be
re-timed: its `surface_novelty` dimension fails on any surface ever attempted, and an attempt on the cold item inside
the window is a hard exposure (`cold_item_answer_reveal`), the one finding that blocks a verification.

## 2. The rule (mvp-0.38, `practice.reschedule_cold_after_assist`)

`remediation.reschedule_assisted_cold_retry`, called first in `record_remediation_attempt`, live only (the attempt
step passes the vault; replay and a regrade pass none). It acts when the rule is live
(`reschedule_cold_after_assist_active`: the tag or later, the switch on, and CA2's rule on, without which submit
refuses the assisted attempt) and the attempt is assisted (`assisted_attempt`: hints, a hinted type, or primed) on the
item of a due, open `cold_retry` (the consumer's own lookup, `active_followup_task_for_item(kind="cold_retry")`: the
task an unassisted attempt would have consumed), and is not an exam attempt. In the attempt's transaction:

1. **The assisted retry ends now**, with the existing typed disposition: `withdraw_cold_measurement` (reason
   `cold_check_help_taken`, `detail.stage = "submit"`; the function gained a `stage` argument, default `"serve"`), its
   final coldness receipt, the task expired. Below the tag the same disposition lands at the next serve.
2. **The bound.** If the withdrawn retry was itself a fresh one (its context carries
   `remediation.ASSISTED_RESCHEDULE_CONTEXT_KEY`), nothing more is scheduled: **one fresh retry per assisted chain**, a
   structural bound in the functional form (no count constant; label `keep`). No existing cap applied: the lane had no
   retry count, because before CA2 an assisted cold attempt was refused.
3. **The surface.** The lane's one rule, factored out unchanged as `remediation._independent_cold_item` (treatment
   now calls it with the primed surface excluded, exactly its old inline code), over the repair's ranked items with
   the primed surface and the assisted retry's surface excluded, then (Codex review F1) skipping, in rank order, any
   surface already hard-contaminated since the primed attempt: the final receipt's own scan
   (`coldness_receipt.repair_surface_hard_contamination`: its answer revealed, or its surface group administered,
   between the primed attempt and the assisted one), because the fresh retry keeps the primed source attempt and its
   final receipt would hard-fail such a surface. Skipped surfaces are listed in the candidate summary
   (`contaminated`). None left: the fresh opportunity is decided `structurally_refused / no_independent_surface` (or
   `no_uncontaminated_surface` when the exposure history ruled every independent surface out) with its
   schedule-refusal receipt, and the repair stays unmeasurable, as below the tag.
4. **The timing is the existing rule, no new delay.** `not_before = the assisted attempt + COLD_RETRIEVAL_DELAY`,
   `expires_at = not_before + COLD_RETRY_WINDOW`. `COLD_RETRY_WINDOW` names the 30 days the primed branch always used
   inline (one value, both sites). The delay runs from the attempt that took the help because that is the latest
   exposure on the repair: it is the lane's "later session, not this one" rule, the same rule the scheduler re-applies
   after a reveal (`scheduler._cold_task_reveals`).
5. **The context is the repair's.** The fresh task copies the withdrawn task's scheduling-time context (§6.2: the
   primed source attempt, repair class, hypotheses, reveal spend) and adds where it came from
   (`assisted_reschedule`: the withdrawn task, the assisted attempt, the withdrawn cold item, the reason). Its
   `source_attempt_id` stays the primed attempt. So the coldness receipt scans from the primed attempt and records the
   assisted attempt as what it is, a retrieval-type co-intervention on the repair's learning object: the fresh retry
   qualifies as cold retrieval, and `qualifies_as_repair_effect_verification` is honest that help came in between.
   Co-interventions are recorded, never blocking (`record_cold_verification_from_task`), so the verification still
   lands.
6. **Bookkeeping.** A new cold-measurement opportunity per withdrawn retry (`trigger_kind = "assisted_cold_retry"`,
   `trigger_ref` = the withdrawn task; its unique key makes it idempotent), decided `scheduled` with the fresh task in
   the same insert. The episode stays `cold_scheduled` and its `cold_item_id` moves to the fresh surface (reveal
   attribution follows it). An unassisted answer on the fresh surface consumes it and completes the episode through
   the unchanged consumer.

7. **The forecast (Codex review F2).** The fresh task gets its own repair forecast
   (`forecast_receipts.record_repair_expectation` via `_repair_forecast`), bound to it, written in its scheduling
   transaction, for the primed attempt with the carried repair class and hypotheses. The receipt key carries the task,
   so the original forecast stays as written and censors on the withdrawn retry's disposition
   (`unmeasurable_no_held_out_surface`), while a measured replacement resolves in `learnloop diagnosis calibration`.

## 3. Certification probes: not rescheduled

`docs/specs/spec_measurement_efficiency_v1.md` §5.7 (as implemented in `goals/certification_cold_probe.py`): "one
held-out-surface item per certified LO", and "one probe per certificate, ever" is a schema fact, migration 139's
`uq_followup_tasks_certification_probe` unique index on `case_ref` (the certificate id) for the whole life of the vault,
consumed or expired. The scheduler's idempotency read is status-blind on purpose, and `false_certification_rate` reads
an expired probe as `probe_expired`, unmeasured, never a pass. A fresh probe for the same certificate would need a
migration that drops that invariant and a spec change to the metric's denominator, which the owner's decision does not
ask for (it names the repair). A re-earned certificate (different cells or recipe) hashes to a new id and earns a new
probe through the existing scheduler. So an assisted probe stays as CA2 left it (practice with help; the next serve
withdraws it), and the rule only ever looks up `kind = "cold_retry"`. Test:
`test_an_assisted_certification_probe_is_left_as_the_predecessor_leaves_it`.

## 4. The successor (playbook items 1-8)

| Item | Done |
|---|---|
| 1. New tag | `COLD_RETRY_RESCHEDULE_ALGORITHM_VERSION = "mvp-0.38"`, one constant, appended to `SUCCESSOR_CHAIN` after `mvp-0.37`; `COLD_RETRY_RESCHEDULE_VERSIONS`; `LATEST_ALGORITHM_VERSION` follows. A change to which cold checks are scheduled and served is a successor by the 2026-10-17 eligibility rule even though replay is unchanged |
| 2. Ledgers immutable | nothing rewritten; a task withdrawn below the tag stays withdrawn |
| 3. Upgrade | `learnloop/cold_retry_reschedule_upgrade.py` (`upgrade_to_cold_retry_reschedule`), the chain's journalled link built on `attempt_content_state_upgrade.py`: the predecessor, or `mvp-0.9` onwards through the chain; anything older refused; one `BEGIN IMMEDIATE` activation under the vault mutation lock with the journal and the durable publication last; `complete_interrupted_activation` completes its own journal and hands any earlier link's down. The CLI (`upgrade --to mvp-0.38`, the bare upgrade's target, the help and refusal text) and the CLI and sidecar openers install it as the chain's latest completion; `activation_journal`'s docstring names it |
| 4. Defaults fingerprint | `practice.reschedule_cold_after_assist = true` (a modelled default, left out of the decision-only template); every snapshot recomputed (29), the `mvp-0.38` snapshot added; dropping the key reproduces every earlier value (checked for all 28) |
| 5. Table roles | no new table |
| 6. Replay / rebuild equivalence | replay passes no vault, so it schedules nothing; `followup_tasks` and `remediation_episodes` are `WORKFLOW` tables no rebuild clears. A same-version rebuild leaves the lane exactly as live left it, and `rebuild --shadow` is 0/0/0 with the fresh retry scheduled and consumed (switch on and off) |
| 7. Shadow rebuild on a copy | in-test only (`shadow_rebuild` on synthetic vaults; `live_database_unchanged`); no owner-vault copy in this stage |
| 8. Upgrade path | CLI upgrade from `mvp-0.9`, `mvp-0.30`, `mvp-0.35`, `mvp-0.36`, `mvp-0.37`; bare upgrade; pre-chain refusal; an interrupted `mvp-0.38` activation completed by the next CLI command and by the upgrade itself; a failure after the rename; an interrupted `mvp-0.37` activation completed then upgraded, with and without an installed completion |

**Kill switch.** `practice.reschedule_cold_after_assist` (default true), classified in
`params/parameter_registry.py` as a structural operational kill switch. Off, or below the tag, the rule returns before
reading anything and `record_remediation_attempt` runs the predecessor's branches unchanged; the off-state test
compares the whole lane (tasks, episode, outcomes, opportunity decisions) with an `mvp-0.37` vault's, and then the next
serve withdraws the retry as the predecessor does.

**No made-up constants.** No new weight, margin or threshold. The delay and window are the lane's existing ones
(`COLD_RETRIEVAL_DELAY`, the 30-day window now named `COLD_RETRY_WINDOW`); the bound is structural (a context marker,
one fresh retry per chain, `keep`: an anti-nag ceiling on a learner who keeps taking help).

## 5. Files

- `src/learnloop/algorithm_versions.py`: the tag, the chain, the version set.
- `src/learnloop/diagnosis/remediation.py`: `COLD_RETRY_WINDOW`, `_independent_cold_item`,
  `reschedule_cold_after_assist_active`, `reschedule_assisted_cold_retry`, `withdraw_cold_measurement(stage=)`, the
  call in `record_remediation_attempt`.
- `src/learnloop/cold_retry_reschedule_upgrade.py` (new); `cli/app.py`, `cli/runtime.py`, `learnloop_sidecar/context.py`,
  `activation_journal.py`, `pyproject.toml` (the experiments-isolation contract's module list).
- `src/learnloop/config/schema.py` (`PracticeConfig.reschedule_cold_after_assist`), `config/template.py` (notes, 29
  fingerprints, the `mvp-0.38` snapshot), `params/parameter_registry.py`.
- `tests/test_cold_retry_reschedule.py` (new); `tests/cli_help_snapshot.json`; chain-tail pins moved in the existing
  successor tests (the latest is `mvp-0.38`; version sets gain it; `test_attempt_content_state_successor.py` no longer
  calls mvp-0.37 the latest).
- `docs/learnloop-architecture-vault/_scripts/db_generate_reference.py` (the field's description) and the regenerated
  reference notes.

## 6. Tests (`tests/test_cold_retry_reschedule.py`)

**Fail-first.** Run against the base's `remediation.py` (only the new names stubbed, the rule a no-op), the five
schedule tests fail: `test_help_on_a_due_cold_retry_schedules_one_fresh_retry_on_another_surface`,
`test_the_fresh_retry_is_invisible_until_due_then_measures_the_repair_cold`,
`test_help_on_the_fresh_retry_too_ends_it_and_spawns_nothing`,
`test_without_another_independent_surface_the_refusal_is_recorded_and_nothing_is_scheduled`,
`test_a_shadow_rebuild_is_zero_with_the_fresh_retries_present`. With the change all pass.

| Area | Tests |
|---|---|
| The schedule | the withdrawn retry's typed disposition (`stage = submit`, `cold_check_help_taken`); one fresh retry on the unused surface; `not_before` / `expires_at` from the existing rule; the carried context and marker; the opportunity decided `scheduled`; the episode's cold item |
| Measured cold | invisible until due; an unassisted answer consumes it and completes the episode; the final coldness evaluation has no hard contamination, qualifies as cold retrieval and lists the assisted attempt as a co-intervention |
| Unchanged | an unassisted cold retry is consumed as before |
| The bound | help on the fresh retry withdraws it and schedules nothing; a later assisted answer finds nothing; two tasks in all |
| No surface | the refusal recorded; nothing scheduled; the episode's cold item unchanged |
| Certification | an assisted probe stays open; no second probe |
| The switch | the gate (tag / switch off / CA2 off / predecessor / predecessor with the switch on; no vault); off and below the tag: the lane equals an `mvp-0.37` vault's, and the next serve withdraws as practised |
| Replay | a same-version rebuild leaves `followup_tasks`, `remediation_episodes` and the opportunities exactly as live |
| Rebuild equivalence | `shadow_rebuild` 0/0/0 (mastery, facet, schedule) with the fresh retry scheduled and consumed, switch on and off, on the rebuild-equivalent placement vault. (The basic vault with its seeded due item is not rebuild-equivalent at any version, the predecessor and no-hint runs included: a pre-existing fixture property, not this change) |
| The chain | one constant after mvp-0.37 and the latest; the snapshots; the registry rule; the upgrades and journals listed in §4 |

## 7. Gate

Every pytest command ran in `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at `-n 6`,
one test run at a time; every Python command outside pytest under `env -i` with empty, existing HOME, CODEX_HOME and
LEARNLOOP_CONFIG_DIR directories (no route configured, no live call).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken (and again after the last code change) |
| fail-first: `tests/test_cold_retry_reschedule.py` against the base's `remediation.py` (new names stubbed, rule a no-op) | 5 failed (the five schedule tests in §6), as intended |
| pytest `tests/test_cold_retry_reschedule.py` | 29 passed |
| pytest batch 1 (60 files: the new file, every test naming the chain or the latest version, and the contract tests, below) | 1,475 passed, 17 skipped, 6 xfailed, 6 failed: chain-tail set literals this stage moves (`"mvp-0.36", LATEST` sets, two negative indices, the recurrence vocabulary); fixed, then those 6 files: 135 passed, 6 skipped, 1 xfailed, 1 failed (one more index), fixed, that file 12 passed, 1 xfailed |
| pytest batch 2 (62 files exercising `remediation`, the cold lanes, `PracticeConfig` or the attempt write, below) | 2,127 passed, 5 skipped |
| after the last code change (the reschedule's savepoint guard): the new file, `test_remediation_cold_retry`, `test_reader_ca2_one_ask`, `test_certification_cold_probe`, `test_causal_cold_outcomes`, `test_coldness_receipt`, `test_post_attempt_pipeline`, `test_serve_eligibility`, `test_primed_attempts`, `test_guided_redo` | 597 passed |
| DB/config reference: `db_generate_reference.py`, `db_validate_reference.py` | regenerated (the new field and the 1,066-leaf counts); validated, errors `[]` |
| CLI help snapshot | regenerated (`python -m tests.test_cli_help_snapshot --write`): only `upgrade` moves |
| durability lane | not run: no migration, no DB or connection code |
| npm / vitest / frontend build, cargo check | not run: nothing under `apps/` changed |
| full suite | not run (owner rule 2026-10-17: once, in the landing gate) |

**Batch 1:** test_cold_retry_reschedule.py test_ad23_successor.py test_ai_config.py test_assumed_known.py test_attempt_content_state_successor.py test_batch3_landing.py test_config_refactor.py test_diagnosis_input_provenance.py test_exam_protection_review.py test_field_workbench_signals.py test_intent_codex_rereview.py test_learner_report_superseded.py test_lp_claim_fixes.py test_lp_claim_fixes_rereview.py test_lp_claim_fixes_review.py test_method_explicit_upgrade.py test_mvp011_upgrade.py test_mvp013_upgrade.py test_mvp014_upgrade.py test_mvp015_upgrade.py test_mvp016_upgrade.py test_mvp017_upgrade.py test_mvp018_upgrade.py test_mvp020_upgrade.py test_mvp021_upgrade.py test_mvp022_upgrade.py test_mvp023_upgrade.py test_mvp024_upgrade.py test_plan_determinism.py test_plan_determinism_landing.py test_plan_follows_path.py test_pr4_superseded_claims_landing.py test_reader_ca2_one_ask.py test_reader_guidance.py test_reader_recap_review_r2.py test_reader_recap_review_r3.py test_reading_step_switch.py test_rebuild_equivalence.py test_rebuild_equivalence_review.py test_recurrence_commands.py test_reference_gate_imports.py test_regrade_contract_replay.py test_regrade_contract_successor.py test_regrade_contract_upgrade.py test_required_method_grading.py test_route_rules_in_grader.py test_serve_eligibility_review.py test_ux_phase1_round2_rereview.py test_cli_help_snapshot.py test_sidecar_serializer_snapshot.py test_sidecar_contract.py test_desktop_rpc_contract.py test_mobile_allowlist.py test_architecture.py test_table_roles.py test_coordinated_migrations.py test_tracked_fixture_databases.py test_registry_audit.py test_e0_isolation.py test_ad_denial_log.py

**Batch 2:** test_ad23_inversion.py test_attempt_content_state_race.py test_authoring_contract.py test_causal_attribution_p0.py test_causal_attribution_p2.py test_causal_cold_outcomes.py test_causal_factor_deferral.py test_causal_orchestrator.py test_causal_p2_acceptance.py test_causal_repair_sidecar_rpcs.py test_coldness_receipt.py test_collection_dataset.py test_common_repair_delivery.py test_compare_methods.py test_daily_loop_lo_lifecycle_serving.py test_daily_plan_build.py test_daily_plan_owner_decisions.py test_diagnostic_probe_freshness.py test_dialogue_causal_join.py test_exam_protection.py test_family_memory_projection.py test_followup_diagnostic_selection.py test_forecast_receipts.py test_goal_series.py test_guided_redo.py test_held_grade_evidence.py test_hypothesis_surface_wiring.py test_instrument_servability_journeys.py test_instrument_serving.py test_intent_codex_review.py test_intent_fix_round4.py test_item_authoring.py test_mcp_c1a_landing.py test_mcp_c1a_review.py test_migrations.py test_misconception_transitions_intake.py test_pfc_unassessed_readers.py test_post_attempt_pipeline.py test_practice_index_admission.py test_prescription_passages.py test_primed_attempts.py test_probe_remint.py test_quick_check.py test_reader_ca1_codex_review.py test_reader_rw1c_review.py test_reader_workbench_rw2a.py test_remediation_cold_retry.py test_retrieval_interventions_write_points.py test_reveal_ledger.py test_router_r2a_serving.py test_scheduler.py test_scoreboard.py test_serve_eligibility.py test_sidecar_remediation_surfaces.py test_stuck_prompt.py test_ux_phase4_feedback.py test_ux_phase4_landing.py test_voi_forecasts.py test_certification_cold_probe.py test_mvp09_upgrade.py test_mvp010_upgrade.py test_sidecar_measurement.py

No paid or live call was made: every grade is self-graded, no model route is configured, no vault but synthetic ones
was opened.

## 8. Open questions

- ~~The repair forecast for the fresh retry~~: resolved by Codex review F2 (§2 item 7).
- **Surface novelty on the fresh surface.** The lane's rule excludes the primed and assisted surfaces and items whose
  material was shown, not every surface the learner has ever attempted (neither did treatment's first pick). The
  ranking puts never- and least-recently-attempted items first; a fresh surface attempted long ago would record
  `surface_novelty = fail` as evidence (not blocking), exactly as a first pick could.
- **An assisted cold follow-up that is not yet due** (practised before the check fell due) is outside the owner's
  decision: it is practice before the check, withdrawn at the next serve as before.

## Landing onto main (2026-10-27)

Landed in `learnanything-dl2` on `sched/cold-retry-after-assist` (stage tip `ed3677743`, base `1bcde2096`) by merging
`main` twice: `dbc1559e7` (the Oct 27 follow-ups: tests and docs only) and then `d2f10ef55` (the Reader RW5c design
spec: docs only). Main was neither fast-forwarded nor pushed. The successor stays **mvp-0.38** after mvp-0.37, with no
migration.

### Commits and conflicts

| Commit | What |
|---|---|
| `4fab205a2` | `--no-ff` merge of `main` `dbc1559e7`. **No conflicts.** The follow-ups' test files merged as they are: `test_field_workbench_signals.py` keeps the branch's chain pin (latest `mvp-0.38`, the version set with it) beside main's own-workbench-history change. `tests/test_rebuild_closed_row_answer.py` still **fails strictly at mvp-0.38** (3 xfailed): this stage does not touch the LO-lifecycle replay gap it pins. |
| `569d2212a` | The DB reference regenerated. Only one note changed in content: `Tables/forecast_receipts.md` now lists `tests/test_cold_retry_reschedule.py`, which comes from the stage's own F2 fix. The ~430 notes whose only change was the `source_commit` stamp were left as they were. |
| `3d4560898` | `--no-ff` merge of `main` `d2f10ef55` (docs only). **No conflicts.** No `src/` or `tests/` file changed, so the gate was not rerun. `db_validate_reference.py` still gives errors `[]`. |

`git diff main` lists no binary, no tracked database and nothing under `fixtures-local/`, and `.gitignore` is unchanged.

### Regeneration

- DB reference: `db_generate_reference.py`, then `db_validate_reference.py`: **errors []**, both after the first merge and after the second.
- The defaults fingerprints were not recomputed: the merges changed nothing under `src/`.
- The CLI help snapshot, the sidecar serializer snapshot and the sidecar contract pass as merged. Nothing needed regenerating, and no RPC or serializer changed.
- The targeted run after the first merge covered the follow-ups' 9 test files, the two snapshot tests and the closed-row file: **175 passed, 17 skipped, 3 xfailed** (80 s).

### Gate (at `569d2212a`; `env -i` with empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `TMPDIR`; logs in `fixtures-local/landing/logs/`)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` (5G scope); `lint-imports --no-cache` | **36 kept**, 0 broken |
| full suite (`flock`, 10G/2G scope, `pytest -n 8 --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml`) | **22,330 passed, 0 failed**, 89 skipped, 47 xfailed. pytest time 2,229.7 s (37:10); wall time 37 min 12 s, with no lock wait. No reruns were needed, there was no faulthandler dump, and no parity ran alongside. |
| durability (`-m durability`, the same flock and 10G scope) | **176 passed**, 1 skipped (61.4 s; wall 63 s) |
| owner lane (`-m owner_vaults`, 5G scope, `-n 6`; fresh backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp035/{linear_algebra,probability,arxiv_v2}` in `fixtures-local/landing-cr38/owner-lane/`) | 83 passed, **2 failed**, 4 skipped (56 s). These are exactly the two expected after the follow-ups: `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies[arxiv_v2]`. The skips are the early vaults that have no copy (`conic-sections`, `arxiv` x2, `linear_algebra_legacy`). |
| frontend / Tauri | not run: nothing under `apps/` changed |

### Parity (fresh backup-API copies of the same mvp035 owner copies; `fixtures-local/landing-cr38/`, scripts in `scripts/cr38_*.sh`)

Setup: `base/` holds the copies, all at mvp-0.35. Every route goes to the `127.0.0.1:9` blackhole (65 tasks). The only
other route is the opt-in `embedding` route, which is off and has no key. `code_main` is `git archive dbc1559e7` and
`code_branch` is `git archive 569d2212a`. Every run went through `env -i` with empty dirs. `run.py`'s audit hooks
refuse Codex process starts and non-loopback sockets; they logged nothing.

**No owner copy holds a due `cold_retry`.** linear_algebra has two open treatment episodes, probability has one and
arxiv_v2 has none. So the live runs (`live_cold.py`) create the case on real data:

1. A primed attempt on the episode's primed item schedules the lane's `cold_retry`.
2. A day and an hour later, the retry is due, and the learner takes help on it (`hints_used = 1`).
3. Ten more self-graded attempts follow (30% hinted).

- **(a) `upgrade --to mvp-0.37`, main's code vs the branch's** (then a primary load; a second main copy is the noise control).
  - Every row is identical: 18,814 / 10,301 / 23,714 rows in 358 tables.
  - The only raw differences are the activation timestamps in 3 tables (`derived_state_rebuilds`, `parameter_registry`, `parameter_registry_manifests`). Main's second copy shows the same 3.
  - Integrity is ok, foreign keys 0, schema SQL identical.
  - `rebuild --shadow` right after the upgrade: mastery 21 / 18 / 34, facet 0, schedule 0, identical on both sides. This is the `algorithm_version` stamp only, as at every earlier landing.
  - After `rebuild-derived-state` on each side: **0/0/0** on both.
  - A normalized row comparison (ULIDs and times masked) of main vs branch then shows **no differing table**: 19,121 / 10,373 / 23,556 rows.
  - `doctor` is identical: 57 / 1, 102 / 48 and 76 / 47 (issues / errors), all known content errors.
- **(b) `upgrade --to mvp-0.38`** (branch code, on copies of (a)'s branch vaults). It prints "mvp-0.37 -> mvp-0.38" and leaves no journal.
  - **0 LOs and 0 item schedules moved.**
  - The cold lane (`followup_tasks`, episodes, opportunities and decisions, cold outcomes, coldness and forecast receipts) is **identical before and after**: the activation moves nothing.
  - Rows are preserved. The only changes are the projection activation's rewrite of the facet rows (36 / 1 / 2 `facet_capability_evidence`, 76 / 2 / 4 `facet_recall_state`), the `parameter_registry` refresh (352), and +1 `derived_state_rebuilds` and +1 `parameter_registry_manifests`.
  - **Serving: no change.** Today and the certification/curve dumps are identical after the version stamp. The daily plan picks the same blocks and items. Only the router card's `card_hash` / `snapshot_hash` (and its `detail_json`) move, because the card carries the version.
  - Shadow right after the upgrade: the stamp only (21 / 18 / 34). After `rebuild-derived-state`: **0/0/0**.
  - **Live, after the rebuild: 12 attempts on each copy, then shadow 0/0/0 on all three.** Without the rebuild, the live shadow is the activation's stamp only.
  - On linear_algebra and probability, the help on the due retry did what §2 says:
    - The retry was expired with `unmeasurable_no_held_out_surface` (`stage = submit`, `cold_check_help_taken`).
    - One fresh `cold_retry` was scheduled on another surface: `pi_compute_with_complex_numbers_teach_back_ya8r73` on linear_algebra, `pi_three_independent_birthd` on probability.
    - Its `not_before` is the assisted attempt + 1 day and its `expires_at` is 30 days after that.
    - The `assisted_cold_retry` opportunity was decided `scheduled / independent_surface_selected`.
    - The episode stays `cold_scheduled`, with `cold_item_id` moved to the fresh surface. The fresh task has its own forecast receipt (+1).
  - A last run on copies of the rebuilt vaults ran the live post-attempt pipeline after each attempt. It kept the fresh item out of the random attempts and answered it unassisted once due (`cr38_b_consume.sh`). The retry was consumed and the episode `completed`; shadow **0/0/0**.
    - On probability, the final coldness receipt is **`cold_success`**, `qualifies_as_cold_retrieval = true`, no hard exposure, and `qualifies_as_repair_effect_verification = false`. That is honest: help came in between.
    - On linear_algebra, the outcome is `missing_chain` (cold retrieval true). That episode is a legacy one with no causal chain. The control shows the same `missing_chain` at mvp-0.37: main's code, the original retry answered unassisted, no help (`cr38_ctl.sh`). It is a property of the episode, not of this change.
  - The bare `upgrade` goes from mvp-0.37 to mvp-0.38. From mvp-0.35 it chains through to mvp-0.38. In both cases the shadow after `rebuild-derived-state` is 0/0/0.
- **(c) The kill switch off reproduces mvp-0.37.**
  - The copies:
    - `c37main`: mvp-0.37, main's code;
    - `c37`: mvp-0.37, branch code;
    - `c38off`: mvp-0.38 with `practice.reschedule_cold_after_assist = false`;
    - `c38on`: mvp-0.38 with the switch on.
  - Each ran the same 12 live attempts (the primed attempt, then help on the due retry).
  - The whole cold lane is **identical for c37main, c37 and c38off**, both after the live run and after a Today read. The assisted retry is left open; nothing is withdrawn at submit and nothing is rescheduled.
  - c38on alone withdraws the retry and schedules the fresh one.
  - Mastery, schedules and Today are identical across all four after the version stamp: the rule changes no learner state.
- **(d) An interrupted mvp-0.38 activation** (`os._exit(17)` after the config publication) on all three copies:
  - `upgrade --to mvp-0.38` completes it ("completed the interrupted activation of mvp-0.38"; run again: "vault is already mvp-0.38").
  - The desktop start completes it.
  - Both equal the clean upgrade: 0 LOs moved.
  - `Repository` and `open_vault_repository` without a completer refuse with "The upgrade to mvp-0.38 did not finish ... run `learnloop upgrade --to mvp-0.38`". The secondary attach and the remote schema check refuse too. Each leaves the vault as it was, and the upgrade then completes it.
  - Plain `doctor --json` is a read-only attach and refuses too, with `InterruptedActivation`; the journal stays. This is as at the earlier landings.
- **(e) `ad report --json`: no new denials.**
  - linear_algebra and arxiv_v2: 0 throughout.
  - probability: 6 live denials at mvp-0.35, its historical lines.
    - (a)'s `--to mvp-0.37` archived them once per command (one archive in each of a_main, a_main2 and a_branch).
    - `--to mvp-0.38` from mvp-0.37 found an empty log and archived nothing new.
    - The bare chained upgrade from mvp-0.35 archived them **once**, as `…archived-mvp-0.35-to-mvp-0.38-…`.
    - After the live run: 0 live and 6 archived.
- **Receipts and calls.** No run wrote a `model_call_receipts` row:
  - the 55 linear_algebra and arxiv_v2 copies hold 0;
  - the probability copies hold the source's 56 historical receipts;
  - the empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` stayed empty.

  **Spend: $0.** Nothing under `~/learnloop-vaults`, `~/learnloop-retired` or `~/learnloop-books` was opened or listed.

**Harness note (not this stage).** In the first live runs, the post-attempt pipeline did not run, and attempts went
straight to `complete_self_graded_attempt` with no serve. In that harness, an unassisted attempt on a follow-up's item
after earlier practice can consume the follow-up, because the serve-time withdrawal (practised since scheduled) never
runs. This is the same at mvp-0.37: c37main's original retry was consumed this way. The app always serves first.

### Owner notes

1. Back up the vaults.
2. Close the desktop app, the MCP server and the phone page.
3. Run `learnloop upgrade --to mvp-0.38` on each vault. From mvp-0.35 it chains through mvp-0.36 and mvp-0.37, and the bare `learnloop upgrade` does the same.
4. The activation moves no LO, schedule or follow-up task. An interrupted one is completed by the next CLI command or the desktop start.

Kill switch: `[practice] reschedule_cold_after_assist = false` restores mvp-0.37's behaviour for new attempts, with no
downgrade. The owner's vaults are still at mvp-0.35.

### Open items

- Owner questions from §8 (still open):
  - **Replacement surface selection:** the lane's rule excludes the primed and assisted surfaces and anything shown, not every surface ever attempted.
  - **Help on a not-yet-due follow-up:** outside the decision; it is withdrawn at the next serve as before.
  - **Certification probes not rescheduled:** one probe per certificate, ever (§3).
- The LO-lifecycle replay gap (`tests/test_rebuild_closed_row_answer.py`, main's follow-ups (3)) is unchanged at mvp-0.38 and still needs its own successor.
