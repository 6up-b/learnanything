# Codex review of lp-learner-report-superseded: fixes

Stage `lp-learner-report-superseded`, branch `lp/learner-report-superseded`
(worktree `learnanything-ad1`). Review: Codex on gpt-6.1-sol, job
`20261027-124252-mwHQw6`, against `34a35db2a`. Every finding was reproduced by
a failing test before its fix (reproductions committed first in `97c6f1b96`).

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Replacement and its mastery effect can commit in different orders | fixed | `a1cf03b45` | `test_two_writers_on_one_warm_lo_apply_their_reports_in_the_order_replay_reads`, `test_a_failure_between_the_replacement_and_its_re_anchor_leaves_the_earlier_report_in_force` |
| F2 | Medium | Replay assumes claim IDs preserve order across processes | fixed (the supersession-edge minimum; see below) | `a1cf03b45` | `test_a_replacement_from_another_process_whose_id_sorts_first_replays_after_the_claim_it_replaced[warm,attempt-free]`, `test_after_what_they_replaced_moves_only_a_replacement_that_would_sort_first` |
| F3 | Medium | Attempt-free rebuilds discard variance left by superseded claims | fixed | `a1cf03b45`, `63610f28b` | `test_two_retirements_on_an_lo_without_attempts_rebuild_to_the_variance_the_replaced_one_left` |

All three tests live in `tests/test_learner_report_superseded.py`.

### F1: one transaction for replacement, position and re-anchor

Reproduced: writer A paused between its replacement and its re-anchor, and
writer B's whole report (claim, `superseded_by` mark, re-anchor) landed in
between. The fault-injection test showed the replacement committed with no
re-anchor (the earlier report marked `superseded_by` a claim whose effect
never ran).

Fix: `mastery.replace_claim_and_reanchor(vault, repository, claim, clock=)`
runs `Repository.replace_learner_claim`, the application-position record and
`reanchor_mastery_from_claim` in one `Repository.atomic()` (`BEGIN IMMEDIATE`,
or a savepoint inside a caller's transaction) from mvp-0.36 on. Both LO seam
callers use it (`item_authoring._apply_difficulty_report`,
`rung_variants.request_rung_variant`). Below the tag both writes happen
exactly as the predecessor wrote them (`nullcontext`). Now B waits at its
`BEGIN IMMEDIATE` until A's whole report commits, and an injected re-anchor
failure rolls the replacement back (rows identical to before; the vault still
rebuilds to live). The two-writer test makes A's and B's reports differ
(pseudo-count 0.25 at level 0.70 against 2.0 at 0.90), so the order of the
merges shows in the result.

### F2: replay places a replacing claim after what it replaced

Reproduced: a forked child process wrote the replacing report in the same
second, at the same attempt count, with a claim id sorting before the first
(`"0" * 26`; ULIDs are monotonic within one process only). Replay applied the
replacement first: the warm LO's mean differed, and on an attempt-free LO the
replaced report's variance was lost.

Fix: `mastery.after_what_they_replaced(claims, keys)`. When a replacing
claim's order key ties with or sorts before the key of the claim it replaced,
the replacing claim's key becomes that claim's key extended by one component,
which places it right after that claim (chains included). Every other key is
unchanged. It is applied in `substrate/replay._ClaimStream.open` (positions,
and so the pending re-anchors and every `claims_made` point) and in
`mastery._retained_cold_variance` (the F8 variance order). Rows written below
the tag carry no `superseded_by`, so this changes nothing there. This is sound
because of F1: a replacement commits after the claim it replaces has fully
applied.

Not done: recording a vault-wide application sequence. That would be a new
column, a change to the branch's migration 225, a rebuilt head fixture and a
regenerated DB reference. Under F1 the supersession edge already gives the
order within a replace chain, and that chain is this stage's subject. The
same-second, same-attempt-count, cross-process order of two claims from
*different* sources (for example a learner report and a tutor gap) still
falls back to `(created_at, id)`. That gap predates this stage (mvp-0.33
placement) and is listed under open questions.

### F3: the attempt-free seed reads the replaced anchors' variance

Reproduced: two `too_easy` retirements on `lo_diag`, zero attempts (asserted),
the first at `claim_pseudo_count = 0.25` (variance 4) and the second at 2.
Live kept 4 and the rebuild gave 3 (shadow `logit_variance` -1.0).

Fix: `initial_mastery_state_for_learning_object` with no `claims_made`
(live, the attempt-free rebuild, an activation's re-seed) now seeds the mean
from the claims in force, as before, and reads every claim on record,
replaced ones included, for the retained variance. The field's frozen-prior
shim (`field/priors.py`) accepts the new keyword and still reads only the
claims in force. Its priors are unchanged, which
`test_the_field_priors_read_only_the_claims_in_force` pins.

### The claims that did not hold

* "The replacing claim sorts after its predecessor": corrected in
  `docs/reviews/lp-learner-report-superseded.md`. The replacement now applies
  after it (F1), and replay places it after it (F2).
* "Retained variance includes what every replaced anchor left": now true on
  the attempt-free path too (F3).
* "The zero-evidence test exercises reports before any attempt": it did not,
  because rung requests write self-report attempts. It is renamed
  `test_two_rung_requests_on_a_cold_lo_then_an_attempt_rebuild_to_live` with
  an honest docstring. The attempt-free case is the F3 test.

No new constant, weight or threshold. The F2 extension component is
structural (a tie-break in the order), so no parameter-registry key. No
config, migration, schema, frontend or `src-tauri` change in this step.

## Gate (this fix step; the full suite runs once at landing)

Every pytest ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G`. No paid or live calls, no owner-vault copies, synthetic
vaults only.

* `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2`.
* `uv run lint-imports --no-cache`: 36 kept, 0 broken (rerun after the last
  change).
* `git diff --check 5c6a0834f..HEAD`: clean.
* Targeted run 1 (`-n 6`, behind `flock /tmp/learnloop-fullsuite.lock`), 78
  files: **1317 passed, 1 failed, 4 skipped, 6 xfailed**. The one failure was
  `test_the_field_priors_read_only_the_claims_in_force` (the frozen-prior shim
  lacked the keyword), fixed in `63610f28b`.
* Rerun `tests/test_learner_report_superseded.py tests/test_field_priors.py`:
  **58 passed, 2 xfailed**.
* Targeted run 2 (`-n 6`, behind the lock), 21 more files naming rung
  variants, learner reports or the shadow rebuild: **398 passed**.
* `tests/test_field_cli.py tests/test_field_signal_production_paths.py`:
  **21 passed**.
* `--durable-sqlite tests/test_learner_report_superseded.py` (WAL, FULL;
  covers the two-writer and cross-process tests on production pragmas):
  **56 passed, 2 xfailed** (the 2 xfails are the separate class's strict
  xfail at mvp-0.35 and mvp-0.36).

Files in run 1: test_activity_families, test_ad23_fix_review, test_ad2_model,
test_ad_guard, test_anti_double_count, test_architecture, test_assumed_known,
test_attempt_completion, test_capability_residual, test_capture_desktop,
test_capture_route_recovery, test_causal_activity_policy,
test_causal_attribution_p0, test_causal_attribution_p1,
test_causal_p2_acceptance, test_characterization_mastery_reliability,
test_cli_help_snapshot, test_cold_start_revision, test_config_refactor,
test_coverage_denominator_boundary, test_daily_loop_reader_retire,
test_diagnostic_probe_single_use, test_discrimination_profiles, test_doctor,
test_durable_promotion_arms, test_evidence_config, test_exam_seeding,
test_facet_diagnostics_v03, test_facet_locks_landing, test_field_priors,
test_ingest_instrument_gates, test_ingest_runner, test_init,
test_irt_difficulty, test_item_authoring, test_item_parameters,
test_km2b_consumer_rekey, test_km2_write_path,
test_learner_claim_application_migration,
test_learner_claim_superseded_migration, test_learner_report_superseded,
test_lp_claim_fixes, test_lp_claim_fixes_rereview, test_lp_claim_fixes_review,
test_mastery, test_mastery_step_attribution, test_misconception_resolution,
test_plan_first_transport_grant_scope, test_plan_first_transport_offer_grants,
test_plan_first_transport_offer_grants_r5, test_planted_misgrade,
test_practice_information, test_primed_attempts, test_question_promotions,
test_rbeq_pr2_landing, test_reader_adoption_ownership, test_reader_ca2_one_ask,
test_rebuild_equivalence, test_rebuild_equivalence_review,
test_rebuild_orchestrator, test_reference_check_binding,
test_reference_gate_imports, test_replay, test_retrieval_spaces_migration,
test_section_coverage_migration, test_sidecar_blueprint_picker,
test_sidecar_serializer_snapshot, test_source_append,
test_source_exercise_import, test_source_set_synthesis, test_state_sync,
test_surprise, test_table_roles, test_teach_back,
test_tracked_fixture_databases, test_tutor_promotion_service,
test_tutor_promotion_w2, test_voi_stopping.

Files in run 2: test_ad23_contract, test_ad2_serving, test_approach_map_replay,
test_batch3_landing, test_chatgpt_plan_workspace, test_contract_commissioning,
test_diagnosis_adjudication, test_forecast_receipts, test_hint_telemetry,
test_ingest_jobs, test_ingest_queue_store, test_intent_exclusion,
test_model_grade_lane, test_practice_item_quality_gates, test_quick_check,
test_regrade_contract_successor, test_regrade_contract_upgrade,
test_shadow_rebuild, test_sqlite_file_copies, test_ux_phase1_connect_ai,
test_vault_writer.

## Open questions

* Cross-source claim order at one point (pre-existing since mvp-0.33): two
  re-anchoring claims from different sources on one LO, in the same second,
  at the same attempt count, written by two processes, replay in
  `(created_at, id)` order, which can invert across processes. A
  transactional application sequence (a column recorded inside the re-anchor
  transaction) would close it. That is a separate successor, for the owner's
  checkpoint.

## Re-review

Codex on gpt-6.1-sol, job `20261027-134328-0AMLhl`, against `e0fbcb59d`.
Verdict REOPENED on one new finding; F1, F2 and F3 confirmed fixed.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Replacement and its mastery effect can commit in different orders | confirmed fixed by the re-review | `a1cf03b45` | (as above) |
| F2 | Medium | Replay assumes claim IDs preserve order across processes | confirmed fixed by the re-review | `a1cf03b45` | (as above) |
| F3 | Medium | Attempt-free rebuilds discard variance left by superseded claims | confirmed fixed by the re-review | `a1cf03b45`, `63610f28b` | (as above) |
| F4 | Medium | Long replacement chains crash replay | fixed | `a056c135a` (reproductions `878c14eaa`) | `test_after_what_they_replaced_handles_a_chain_longer_than_the_recursion_limit`, `test_a_report_chain_longer_than_the_recursion_limit_replays_and_seeds` |

### F4: supersession edges resolved iteratively

Reproduced in two tests. The first: a 1,100-claim chain passed to
`mastery.after_what_they_replaced` newest first, the way
`Repository.learner_claims` returns rows (`ORDER BY created_at DESC, id`). The
second: 1,100 sequential `too_easy`-style reports, one second apart, on one
warm LO through the production seam `replace_claim_and_reanchor`, followed by
`_ClaimStream.open`, the attempt-free seed
`initial_mastery_state_for_learning_object` (now) and a rebuild to live. Both
raised `RecursionError` at `mastery.py:249`. The recursive `key_of` went one
frame deeper for each predecessor not yet resolved, and reading newest first
meant no predecessor had been resolved yet. With every report written in the
same second the ids sort oldest first, which is why a same-second chain did
not show it.

Fix: `after_what_they_replaced` now does a post-order depth-first walk with an
explicit stack. A claim's key is settled only after every claim it replaced
has been settled. The rule itself is unchanged: an unordered claim does not
descend, a replacing key that ties or sorts first is extended by one
component, and an edge back onto the path is skipped. The unit test checks
both shapes. The already-ordered chain keeps its keys. In the fully inverted
chain each key is its predecessor's key extended by one. The existing
`test_after_what_they_replaced_moves_only_a_replacement_that_would_sort_first`
passes unchanged. No new parameter, schema change or frontend change.

### Re-review gate

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: done.
* `uv run lint-imports --no-cache`: 36 kept, 0 broken.
* Reproductions before the fix:
  `uv run pytest tests/test_learner_report_superseded.py -k recursion_limit`:
  2 failed (`RecursionError`). After the fix, with
  `-k "recursion_limit or after_what_they_replaced"`: 3 passed.
* Targeted run, `systemd-run --user --scope --quiet -p MemoryMax=5G -p
  MemorySwapMax=1G -- uv run pytest -n 6 <44 files>`: **766 passed, 4
  skipped, 6 xfailed** in 185 s. The 44 files are every test file that
  imports `learner.mastery` or `substrate.replay`, or names
  `initial_mastery_state_for_learning_object`, `_ClaimStream` or
  `replace_claim_and_reanchor`, plus the architecture, rebuild-orchestrator,
  shadow-rebuild, item-authoring and field-priors files:
  test_anti_double_count, test_architecture, test_capability_residual,
  test_causal_activity_policy, test_causal_attribution_p1,
  test_causal_p2_acceptance, test_characterization_mastery_reliability,
  test_cold_start_revision, test_coverage_denominator_boundary,
  test_diagnostic_probe_single_use, test_discrimination_profiles,
  test_doctor, test_durable_promotion_arms, test_evidence_config,
  test_exam_seeding, test_facet_diagnostics_v03, test_field_priors,
  test_ingest_instrument_gates, test_irt_difficulty, test_item_authoring,
  test_item_parameters, test_km2b_consumer_rekey, test_km2_write_path,
  test_learner_report_superseded, test_lp_claim_fixes,
  test_lp_claim_fixes_rereview, test_lp_claim_fixes_review, test_mastery,
  test_misconception_resolution, test_planted_misgrade,
  test_practice_information, test_primed_attempts, test_rebuild_equivalence,
  test_rebuild_equivalence_review, test_rebuild_orchestrator, test_replay,
  test_shadow_rebuild, test_source_append, test_source_set_synthesis,
  test_state_sync, test_surprise, test_teach_back, test_tutor_promotion_w2,
  test_voi_stopping.
* Not run, because nothing changed there: durability lane (no migration or
  DB code), frontend, cargo, DB reference scripts. Full suite: deferred to
  the landing gate (owner rule, 2026-10-17).
* `git diff --check`: clean.
