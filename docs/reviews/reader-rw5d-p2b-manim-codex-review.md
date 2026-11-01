# Reader RW5d P2b, the Manim half: Codex review and fixes

- **Stage:** `reader-rw5d-p2b-manim` (branch `reader/rw5d-p2b-manim` in `learnanything-merge2`, base `2eb4bf6e61`;
  stage record `docs/reviews/reader-rw5d-p2b-manim.md`).
- **Review:** Codex on gpt-6.1-sol, job `20261101-092437-oRdyjB`, against `f271952802`. Verdict: do not land yet,
  three High findings (F1-F3) and eight Medium (F4-F11).
- **Live calls:** none. Every model call in the new tests is a fake; no Manim render ran. Python outside pytest ran
  only under `env -i` with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` (imports, the desktop
  catalog). One real `systemd-run --user --scope` + bubblewrap launch runs in the test suite around `/usr/bin/env`
  (never Manim, never vault data), skipped where no user scope can start.
- **Reproduction first:** each finding was reproduced before its fix. F1 by hand (`env -i PATH=... HOME=/tmp
  systemd-run --user --scope --quiet -- true` fails with "Failed to connect to user scope bus via local transport:
  $DBUS_SESSION_BUS_ADDRESS and $XDG_RUNTIME_DIR not defined"; with the two variables it exits 0). F2-F11 by tests run
  against the pre-fix source (`git archive f271952802 src`, `pytest -o pythonpath=<that src>`):
  `tests/test_figure_rich_review_fixes.py` 19 of 19 failed there, and the 18 new cases in
  `tests/test_manim_figure_checks.py` failed there (the F2 case ran the unmetered oracle for over two minutes before
  accepting the 823-million-step claim set; the F4 case issued the false check, `f(t = 1) = 2, but t = 1 there` on the
  constant-only variant). All pass after the fixes.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | The systemd render path drops the environment needed to launch | fixed | `037248502b` | `tests/test_manim_sandbox_hostile.py::test_the_render_launch_gives_the_scope_the_session_bus_and_unsets_it_in_the_sandbox`, `::test_the_scope_probe_launches_exactly_as_a_render_does`, `::test_the_real_capped_scope_launches_the_sandbox_without_the_session_bus` (real scope + bwrap) |
| F2 | High | Claim evaluation bypasses the verifier's work and time budgets | fixed | `037248502b` | `tests/test_manim_figure_checks.py::test_a_claim_set_past_the_work_cap_is_refused_before_the_oracle_runs`, `::test_the_meter_stops_the_oracle_even_when_the_estimate_falls_short`, `::test_the_whole_check_has_one_deadline`, `::test_a_cancel_reaches_a_long_oracle_phase` |
| F3 | High | Render output can exhaust memory outside the capped scope | fixed | `037248502b` | `tests/test_manim_sandbox_hostile.py::test_bounded_run_stops_a_flood_and_keeps_only_the_tails`, `::test_bounded_run_returns_the_output_tails_and_times_out`, `::test_render_scene_runs_bounded_by_default_and_fails_a_flood`, `::test_a_video_past_the_cap_is_never_read` |
| F4 | Medium | Extraction can verify a different function from the rendered module | fixed | `037248502b`, `5194bfa615` (`out=` writes) | `tests/test_manim_figure_checks.py::test_a_constant_the_scene_changes_makes_its_function_not_checkable[augmented,rebound,global,item,method,handed,out]`, `::test_the_finding_f4_reproduction_issues_no_check_line`, `::test_a_declared_function_bound_twice_is_not_checkable`, `::test_an_immutable_constant_the_scene_only_reads_is_kept` |
| F5 | Medium | The plotted-function check ignores Python name binding | fixed | `037248502b` | `tests/test_manim_figure_checks.py::test_plotted_from_resolves_the_binding_and_the_function_argument` (10 cases), `::test_a_rebound_plot_name_keeps_the_function_check_and_drops_the_curve` |
| F6 | Medium | Cancelling during rendering still publishes the figure | fixed | `037248502b` | `tests/test_figure_rich_review_fixes.py::test_a_cancel_during_the_render_stores_nothing`, `::test_a_cancel_during_a_failed_render_never_asks_for_the_repair`, `::test_a_cancel_raised_inside_the_render_repair_propagates` |
| F7 | Medium | "Try again" reuses the failed rich program indefinitely | fixed | `037248502b` | `tests/test_figure_rich_review_fixes.py::test_try_again_after_a_stored_rich_failure_asks_afresh`, `::test_a_crash_rerun_keeps_the_generation_and_the_rich_prompt` |
| F8 | Medium | A crash between the quick figure and enqueue permanently loses the rich half | fixed | `037248502b` | `tests/test_figure_rich_review_fixes.py::test_a_stop_between_the_quick_figure_and_the_enqueue_is_recovered_once`, `::test_a_failed_enqueue_is_not_swallowed_and_is_recovered`, `::test_a_normal_build_or_a_cancelled_one_is_never_restarted_by_recovery`; `tests/test_figure_rich_rpc.py::test_reading_a_source_starts_a_rich_job_whose_enqueue_never_happened` |
| F9 | Medium | Interrupted rich-only builds disappear without a failure state | fixed | `037248502b` | `tests/test_figure_rich_review_fixes.py::test_an_interrupted_rich_only_build_stays_as_a_failed_line_and_can_be_tried_again`, `::test_a_cancelled_rich_only_build_leaves_no_line_and_cannot_be_retried`, `::test_a_stored_rich_only_failure_lists_once`; `tests/test_figure_rich_rpc.py::test_an_interrupted_rich_only_build_reads_as_failed_and_rich_retry_requeues_it`; vitest `richFigure.test.tsx` "a rich-only build that ended with no figure says why and tries again" |
| F10 | Medium | Rich-only tier judgments can never reach `judgment_ledger` | fixed | `037248502b` | `tests/test_figure_rich_review_fixes.py::test_a_rich_only_tier_judgment_is_receipted_once_against_its_request[completed,cancelled,interrupted,waiting]`; `tests/test_figure_rich_job.py::test_rich_only_shows_the_pending_line_and_never_asks_twice` (updated) |
| F11 | Medium | The required correction path is unavailable for Manim figures | fixed | `037248502b` | `tests/test_figure_rich_review_fixes.py::test_not_right_on_an_animation_goes_to_the_rich_author_with_the_note_and_program`, `::test_not_right_on_a_fuller_version_stays_that_quick_figures_fuller_version`, `::test_try_a_different_kind_of_figure_reruns_the_tier_choice_with_the_note`, `::test_a_revision_needs_the_manim_tier_on_this_computer`; `tests/test_figure_rich_rpc.py::test_not_right_on_an_animation_through_the_sidecar[False,True]`; vitest "not right? on an animation sends the note, or asks for a different kind" |

Tests were committed in `a6d14ed2e8` (with the registry entries, the launch-site approval, the desktop-only pin and
the regenerated desktop catalog).

## What changed, per finding

- **F1.** `concept_animation.render_launch(command, workdir, bwrap, wrapper)` is now the one place a render's argv
  and env are built: the render's minimal env; under bubblewrap `HOME`/`XDG_CACHE_HOME` in scratch; under a
  `systemd-run` wrapper the session variables the launcher needs (`SCOPE_SESSION_ENV` =
  `DBUS_SESSION_BUS_ADDRESS`, `XDG_RUNTIME_DIR`), which bubblewrap unsets (`--unsetenv`, new `unset_env` argument of
  `_sandboxed_command`) before it execs the render, so model code never sees the bus. `_systemd_scope_works` probes
  with the same env (the render's minimal env plus the session variables, nothing else inherited). Under the
  `prlimit` fallback nothing of the session is passed.
- **F2.** `manim_figure.check_claims` gains one deadline for the whole check (`CHECK_SECONDS` 60 s, the sketch
  verifier's) and a metered oracle (`_ClaimBudget`, a `grammar.Meter`: `MAX_CLAIM_WORK` = the sketch verifier's
  `SKETCH_MAX_CLAIM_WORK`, a clock look every `_TICK_WORK` steps), with the sketch's `expression_steps` estimate for an
  early refusal. A claim set past either fails as too costly to check (the second attempt, then not shown). An
  `interrupt` hook runs at most every `INTERRUPT_SECONDS` during the oracle; the rich job passes its heartbeat, so a
  cancel stops even this phase.
- **F3.** `render_scene` runs through `bounded_run` by default: `Popen` in a new session, both pipes drained by threads
  with bounded tails (`_STDERR_TAIL_CHARS`), the process group killed when output passes `RENDER_MAX_OUTPUT_BYTES`
  (16 MiB) or the timeout. The mp4's size is read before its bytes (`RENDER_MAX_VIDEO_BYTES`, 512 MiB). The inspector's
  renders share it (same function).
- **F4.** Extraction keeps a module constant only when the scene can't change what the declared functions read:
  bound once in the module's own scope (`module_bindings`: no `A += 1`, no rebinding, never `global`), never mutated in
  any scope (no item or attribute store, no method call on it, no `out=A`) and, when its value may be a mutable
  object (any call other than `math`/scalar builtins, a container), never handed to other code as an argument. A
  constant built from an unstable one is dropped too; a declared function bound more than once is not checkable. The
  dropped claim is listed as not checkable with code's reason, never failed.
- **F5.** `plotted_from_ok` recognizes only the function argument of a plot call (`PLOT_FUNCTION_ARGS`: the keyword
  or the first positional argument; `always_redraw`/`add_updater` and `plot_line_graph` removed), as the bare name or a
  lambda that calls it (not one that takes it as a parameter), and only where the name resolves to the module's `def`
  (bound once in the module, not bound in any enclosing def, lambda or class). Otherwise the function check stays and
  the curve association is dropped.
- **F6.** The rich job heartbeats (`report("rendering")`, the job's cancel checkpoint) right after each render returns,
  before storing or asking for the render repair; `_run` and `_repair_render` re-raise the supplied cancellation
  exceptions ahead of their broad handlers.
- **F7.** The retry generation counts every stored row of the input, rich ones included (`ALL_SPEC_VERSIONS`), so a
  stored rich-only failure starts generation 1 on "try again"; the rich payload's author context keeps its
  `request_id` (the input and its generation), so the rich prompt and its paid checkpoint are the same across a crash
  rerun or requeue and new after an explicit retry.
- **F8.** The rich job's intent (its payload) commits inside the quick figure's own transaction
  (`verification_report.rich_intent`). `ensure_rich_job` starts a job only when none exists for that quick figure in
  any state (`rich.rich_job_for_quick`, looked up over the whole queue) and no fuller row is stored, under one
  process lock. An enqueue failure is logged (no longer swallowed silently); `reader.figures` runs
  `resume_rich_intents` first, which starts any committed intent with no job (with no grant: the recovered job belongs
  to no action). Until then the fuller line reads pending. A cancelled build is never restarted.
- **F9.** `rich_pending` keeps a rich-only build that ended with no row as a `failed` line (code's reason:
  *interrupted when LearnLoop stopped*, or the stop's message) until a later build of the input replaces it; a
  cancelled one is gone; a stored row lists itself. New RPC `figure.rich_retry {richJobId}` (desktop only, pinned)
  requeues that same job (`retry_rich_job`: failed, not cancelled, rich tiers on, not held out), so a paid answer is
  recovered. Desktop: the line reads *the animation couldn't be built · why ▸ · try again*.
- **F10.** A rich-only build's `figure_tier` judgment is appended with its request row, in the same transaction, when
  the author's choice is accepted (`left_kind` `figure_request`, `left_id` the request); `_store` no longer appends one,
  so it is written once whatever the job does, and the request names the figure when it lands. The tier report counts
  every `figure_tier` row regardless of `left_kind`.
- **F11.** `reader.figure_revise` on a shown Manim figure builds `_rich_revision`: no figure author call; a rich job
  whose payload carries the brief (from the stored program), the learner's note and the earlier program (scene,
  declared functions and claims, the checks it passed); the rich author's context gains `learner_note` and
  `earlier_version`. The new row supersedes the old (kept), stays the quick figure's fuller version when the base was
  one, and is checked, rendered and stored like any rich figure. `differentKind: true` (the note box's *try a
  different kind of figure*) goes through the tier choice with the note and what the animation showed (never its
  program). Refused while the rich tiers are off or Manim isn't available here. Desktop: *not right?* on the Manim body,
  with the checkbox.

## Notes for the landing

- The review's spec-conformance table also notes that the §9b.4 label-wording rule over a rich figure's free text
  (narration, title, demonstrates, assumptions) is absent. Not one of the eleven findings and not built here: the
  sketch tier's rule (`impersonates`) applies to names and ids, and applying it to free narration would refuse
  ordinary words ("let's check that ..."). Recorded as an open item for the owner/spec.
- Historical-p50 pending copy (*usually about N min*) remains absent (stage record open item).
- Owner checkpoint (three real requests on the plan) remains an owner item, not part of this stage.

## Gate (this step; the full suite runs once at landing)

Every pytest, vitest, npm and cargo command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G -- ...`, pytest at `-n 6`, vitest at `--maxWorkers=4`, one run at a time.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: done.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Reproduction against the pre-fix source (above): `tests/test_figure_rich_review_fixes.py` **19 failed**;
  `tests/test_manim_figure_checks.py` **18 failed, 28 passed** (the 18 are the new cases).
- Targeted pytest, round 1 (93 files: every figure, sketch, concept animation, Manim, PF sandbox and reader
  report file, every test file naming a changed module or function (`git grep` for concept_animation, manim_figure,
  figures.rich, figures.service, handlers.figures, render_scene, the figure and rich fixtures, the figure RPCs,
  parameter_registry, _systemd_scope_works, capped_scope_prefix; the `test_mvp0*_upgrade` files, which only name the
  registry, excluded), and the contract tests: desktop RPC contract, sidecar contract/registry/serializer snapshot,
  CLI help snapshot, mobile allowlist, architecture, registry audit, codex lockdown round 3, table_roles, tracked
  fixture databases, vault template): **2,326 passed, 1 failed, 17 skipped, 1 xfailed** (11 min). The one failure,
  `test_ingest_queue_store.py::test_ingest_queue_sql_has_one_persistence_owner`: the F8 lookup queried
  `ingest_jobs` from `figures/rich.py`; moved into the store as `newest_ingest_job_by_payload`.
- Round 2 (after that move): `test_ingest_queue_store.py`, `test_figure_rich_review_fixes.py`,
  `test_figure_rich_rpc.py`, `test_figure_rich_job.py`, `test_manim_figure_checks.py`, `test_architecture.py`:
  **117 passed**.
- Earlier iterations in this step: `test_manim_sandbox_hostile.py` 14 passed (the real scope + bwrap launch ran, not
  skipped; bubblewrap 0.13.0); contract set (mobile allowlist, lockdown round 3, desktop RPC contract, registry audit,
  sidecar contract/registry/serializer snapshot, architecture, CLI help snapshot) 446 passed + the 6 fixed failures
  (new constants registered, `bounded_run` approved as a launch site and `render_scene`'s stale
  `subprocess.run` approval removed, `figure.rich_retry` pinned desktop-only).
- No migration, schema, config key or DB/connection code changed: no durability run and no DB reference
  regeneration needed.
- Frontend (`apps/learnloop-tauri`): `npm install`; `npm run typecheck` clean; `npx vitest run --maxWorkers=4
  src/screens/reader/figures/`: **14 files, 381 passed** (`richFigure.test.tsx` 11, three new); `npm run
  frontend:build` built; `cargo check --manifest-path src-tauri/Cargo.toml` finished (new passthrough
  `figure_rich_retry`).
- Desktop catalog regenerated (`desktop_generate.py`) and validated (`desktop_validate.py`: 297/297 TS + 5/5 Rust,
  ACTIVE 302, reproducible).

Test files of round 1: `test_ad1_codex_review_fixes.py`, `test_ad23_owner_decisions.py`, `test_ad23_successor.py`, `test_architecture.py`, `test_attempt_content_state_successor.py`, `test_batch3_landing.py`, `test_cli_help_snapshot.py`, `test_codex_lockdown_round3.py`, `test_codex_output_schema.py`, `test_cold_retry_reschedule.py`, `test_concept_animation_service.py`, `test_concept_animation_store.py`, `test_concept_animation_validator.py`, `test_constraint_engine.py`, `test_curriculum_c1_plan_follows_path.py`, `test_deliverable_codex_review.py`, `test_desktop_rpc_contract.py`, `test_field_workbench_signals.py`, `test_figure_grammar.py`, `test_figure_offers.py`, `test_figure_panels.py`, `test_figure_predictions.py`, `test_figure_property.py`, `test_figure_region.py`, `test_figure_requests_migration.py`, `test_figure_revisions.py`, `test_figure_rich_contract.py`, `test_figure_rich_job.py`, `test_figure_rich_review_fixes.py`, `test_figure_rich_rpc.py`, `test_figures_codex_review.py`, `test_figures_final_round.py`, `test_figures_fix_round2.py`, `test_figures_fix_round3.py`, `test_figures_fix_round4.py`, `test_figures_fix_round5.py`, `test_figures_migration.py`, `test_figures_rpc.py`, `test_figures_rw5b_fix_round2.py`, `test_figures_rw5b_review.py`, `test_figures_scope_redesign.py`, `test_figures_show_me_codex_review.py`, `test_figures_show_me.py`, `test_figures_switch_off.py`, `test_figure_verification.py`, `test_grading_cli.py`, `test_ingest_queue_store.py`, `test_kinship_feature.py`, `test_library_exercises.py`, `test_lp_claim_fixes.py`, `test_manim_figure_checks.py`, `test_manim_sandbox_hostile.py`, `test_method_explicit_upgrade.py`, `test_mobile_allowlist.py`, `test_openai_chat_client.py`, `test_open_world_gate.py`, `test_p0_cutover_mvp08.py`, `test_pf_sandbox.py`, `test_plan_first_transport_offer_grants.py`, `test_plan_first_transport_offer_grants_r5.py`, `test_plan_follows_path.py`, `test_provider_resolution_parity.py`, `test_reader_ca2_one_ask.py`, `test_reader_ca4_table_by_point.py`, `test_reader_followups_successor.py`, `test_reader_report.py`, `test_reader_rw2b_review.py`, `test_reader_source_identity_guard.py`, `test_reading_paths.py`, `test_rebuild_equivalence_review.py`, `test_recurrence_commands.py`, `test_registry_audit.py`, `test_regrade_contract_upgrade.py`, `test_rw2c_switch_off.py`, `test_sensitivity_certificates.py`, `test_sidecar_animation.py`, `test_sidecar_contract.py`, `test_sidecar_registry.py`, `test_sidecar_serializer_snapshot.py`, `test_sketch_engine.py`, `test_sketch_hostile.py`, `test_sketch_parity.py`, `test_sketch_sandbox_review.py`, `test_sketch_scene_parity.py`, `test_sketch_service.py`, `test_sketch_verify.py`, `test_source_roles.py`, `test_structured_transport_parity.py`, `test_table_roles.py`, `test_teacher_te0_review_fixes.py`, `test_tracked_fixture_databases.py`, `test_ux_phase2_shell.py`, `test_vault_template.py`.
