# Router objective follow-up batch: Codex review (`router/ro-followups`)

Review job `/home/saturn/.cache/codex-agent/jobs/20261105-215240-rNmMSZ` (gpt-6.1-sol) on the batch at
`122e47603b` (base `e7a7d7734f`, successor mvp-0.50). Three Medium findings, all reproduced first with a failing test
and fixed; none rejected. No model request added, no paid call, no schema change (head 246), synthetic vaults only.

## Review

### Findings

| Id | Severity | Title | Verdict | Commit | Test (fails on the pre-fix source) |
|---|---|---|---|---|---|
| F1 | Medium | The carried-valuation kill switch leaves the new fitting behaviour active | fixed | `fb2442fb96` | `tests/test_rofu_carried.py::test_the_switch_turned_off_after_carriers_exist_reads_the_predecessors_transitions` |
| F2 | Medium | The unconditional merged sessions can change serving below the successor tag | fixed | `235b7218fc` | `tests/test_rofu_speed.py::test_a_deadline_admits_more_draws_merged_so_the_default_is_the_per_block_loop`, `::test_the_numeric_policy_merges_only_at_the_tag_with_its_switch` |
| F3 | Medium | Early published answers lose their carried valuation permanently | fixed | `1b7c1f3285` | `tests/test_rofu_carried.py::test_an_early_publication_served_keeps_its_carried_valuation` |

**F1.** Reproduced on a synthetic mixture vault at mvp-0.50 (the no-model branch, 8 boundaries, carriers in the
log): with `carried_in_prefetch = false` set afterwards, `tail_data.logged` still returned rows with
`carried_source = "later_prefetch"`. Fix: `logged` applies `_with_late_carried` only when
`tail_data.carried_in_prefetch_on(config)` (the tag, the objective serving and the switch); the chooser's `_carry_on`
asks the same predicate, so the serving and the reading side cannot disagree. The test turns the switch off after
carriers exist and compares with the predecessor's reading of the same traces (`_with_late_carried` as the
identity): the transitions (decision, generator, reward, `next_v_tail`, `next_phi`, cutoff kind), the censoring
counts and the fits are equal, and the censoring differs from the switch-on reading (the late records were lifting
`cutoff_unmatched`).

**F2.** Reproduced: the same 22-topic synthetic decision (5 candidates incl. a probe, seed `s`), a clock charging one
unit per FSRS update, a budget of 2.5 first batches (16,205 units), refining up to 64 draws:

| Path | Completed draws | Numeric choice |
|---|---:|---|
| Per-block loop (mvp-0.49) | 16 | `stop_for_today` |
| Merged sessions | 64 | `a` |

Codex's 8 vs 32 draws on its own instrument agree in kind: the fixed-draw equality does not cover a deadline. Fix:
`value.MERGED_SESSIONS` is gone; `_Model`, `evaluate`, `baselines` and `gain` take `merged_sessions` (default False,
the per-block loop), and the numeric policy passes `objective_chooser._merged(config)` (the tag, the objective
serving and the new `[router_objective] merged_sessions`, default true) to every rollout of a decision: the
evaluation and its refinement, the LLM correction, the carried valuation, the baselines and the day's gain curve
(the day's price runs inside the same deadline, so it is gated too). The key is a structural kill switch in
`params/parameter_registry.py`; every defaults snapshot is recomputed (41 versions; the frozen mvp-0.49 digest in
`test_rofu_successor.py` still holds with the batch's keys dropped). Serving time at the tag is item 3's (arxiv_v2
shape, 8 draws: 423 ms per-block, 232 ms merged); below the tag, or off, a decision runs the per-block loop again,
so it takes mvp-0.49's time and completes mvp-0.49's draws within its deadline (the test's default run: 16 draws,
the per-block values exactly).

**F3.** Reproduced with a gated LLM (`timeout_seconds = 3`): the second decision served `published_uncorrected`
with `residual.previous.status = carried` and **no** `q_status`, so `_defer_carry` registered nothing and the
transition into it stayed `cutoff_unmatched`. Fix: at the tag with `carried_in_prefetch`, every answer that can serve
carries its own carried valuation (`NumericPolicy.carried`, a field never serialized): an early publication's
residual is pending and its callable is frozen to its own uncorrected inputs and actions (the same factory as the
final answer's, the first batch's draws, the carried cutoff); the final answer carries its own. The serve registers
the one it took, so the handoff no longer depends on whether the serve or the job's completion comes first; the
`DEFERRED` material key (installed only at completion) is gone. Off, or below the tag, the publication is RO6's
exactly (`early_carry` is None, no field set). The test serves the early publication, releases the LLM, lets the jobs
and the next prefetch run, and checks: the published decision's `previous.q_status = not_valued_before_the_serve`,
`deferred_to = next_prefetch`; a later trace's `carried_for` holds it `valued`, with the `q` of an evaluation at the
carried cutoff on uncorrected inputs (no effect slope); the transition into it is valued at `previous_cutoff`
(before: censored).

Other commits of this step: `4944977efb` (four version-pin test files, test-only) and the record (this file, the
corrected claims in `router-followups-nov5.md` and the spec's as-built, the regenerated architecture reference).

### Claims that did not hold (corrected in `docs/reviews/router-followups-nov5.md` and the spec's as-built)

- "Each part that changes serving has its own switch" / "off ... mvp-0.49's exactly": now true for item 3
  (`merged_sessions`, F2) and item 4's reading side (F1); the switches table lists `merged_sessions`.
- "Before the completion event, so a serve always finds it": replaced by "every answer that can serve carries its
  own" (F3).
- "Numerical only": the merged path is a serving change through the deadline (F2); the note in `value.py` says so.

### Spec conformance rows left as recorded

The unbuilt items Codex lists (floor draws as contrasts, the two caches, the κ0 availability covariate and the
goal-date sensor inside `V`, the memory forecast curve and the whole-day return gap, FG1d's pins, RO1's admission
anchor and the upgrade's mastery stamps) are recorded in `docs/reviews/router-followups-nov5.md` with the smallest
way to finish each; this step does not widen scope. Pending carried valuations are process memory (lost on a
restart: the transition stays censored, as mvp-0.49's), as recorded there.

### Gate

Every Python command outside pytest ran under `env -i PATH HOME=<empty> CODEX_HOME=<empty>
LEARNLOOP_CONFIG_DIR=<empty>` (scratch dirs outside the worktree); every pytest under `systemd-run --user --scope
--quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`; the batch under `flock /tmp/learnloop-fullsuite.lock`.
No full suite (the landing gate runs it once).

| Step | Command / selection | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`; `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `uv run lint-imports --no-cache` | 43 kept, 0 broken |
| Reproduce-first | each new test on the pre-fix source | F1: 1 failed (`carried_source` still `later_prefetch` with the switch off); F2: 2 failed (the default evaluation merged; the numeric policy never passed `merged_sessions`); F3: 1 failed (`previous.q_status` None on the served publication) |
| Fixed tests | `tests/test_rofu_carried.py tests/test_rofu_speed.py tests/test_rofu_successor.py tests/test_rofu_scope.py tests/test_rofu_learning.py tests/test_rofu_weeks.py`, `-n 6` | 47 passed |
| Targeted batch | 155 files (`docs/reviews/router-followups-codex-review.targeted-tests.txt`): every test file naming the objective chooser, `value`, `tail_data`, `tail_serve` or the mixture helpers; every `test_ro[0-9]*.py` and `test_rofu_*.py`; every file naming the defaults snapshots, the parameter registry or `RouterObjectiveConfig` (the config defaults snapshot and the version-pin files); the display-label audit (`test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`); `test_architecture` (frozen cycles); `test_cli_help_snapshot`; the process-launch allowlist (`test_ai_tool_isolation`, `test_e0_isolation`, `test_codex_tool_lockdown`, `test_codex_lockdown_round3`); `test_table_roles`, `test_registry_audit`, `test_module_catalog_inventory`, `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_sidecar_registry`, `test_mobile_allowlist`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_public_tip_guards`, `test_sqlite_file_copies`, `test_data_capture_successor`, `test_config_refactor`; `-n 6` | 2831 passed, 16 skipped, 3 xfailed, 5 failed: four version-pin files the batch's successor commit missed (`test_attempt_content_state_successor`, `test_cold_retry_reschedule`, `test_ad23_successor` x2, `test_batch3_landing`, still naming mvp-0.49 as the latest; fixed test-only in `4944977efb`) |
| Pin files rerun | those four files, `-n 6` | 88 passed, 3 skipped |
| References | `db_generate_reference.py`, `db_validate_reference.py` (1174 effective leaves with `merged_sessions`: errors []), `module_generate.py`, `module_validate.py` (PASS), `validate_vault.py` (passed) | ok |
| Not applicable | no migration or DB/connection code (no durability lane), no frontend, nothing under `src-tauri` | |

Paid routes: none added; no model request, no paid call made in this step.
