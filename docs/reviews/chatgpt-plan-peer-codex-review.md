# ChatGPT plan as a Codex peer: Codex review fixes

Stage: `chatgpt-plan-peer` (worktree `learnanything-merge3`, branch
`ai/chatgpt-plan-provider`; the stage record is `chatgpt-plan-peer.md`).
Reviewed range: `37a2a7e5f..1c036a78e`. Review: Codex job
`20261015-175241-t4lz6q`, 6 findings (1 High, 5 Medium) plus six claims
that did not hold. All six findings reproduced and are fixed; none was
rejected. The fix step was interrupted three times by Claude Code restarts
(a full `/tmp`); this record is written by the run that finished it, which
kept the earlier runs' uncommitted work and committed it.

## Review

### Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Vault copying ignores the configured database location | fixed | `0c445c246` | `test_ai_compare.py`: `test_copy_from_relocates_a_database_configured_outside_the_vault[absolute]`, `[parent]`, `test_copy_from_backs_up_a_wal_database_not_named_sqlite`, `test_a_vault_whose_database_lies_outside_it_is_refused` |
| F2 | Medium | Comparison accepts generation output that production rejects | fixed | `0c445c246` | `test_ai_compare.py::test_a_draft_the_tutor_would_reject_is_invalid[no_transfer, incomplete_coverage, duplicate_coverage, invented_facet, item_local_with_facets]`; the happy-path fake now returns a draft the tutor accepts |
| F3 | Medium | Comparison reports can contain learner text and model prose | fixed | `0c445c246` | `test_ai_compare.py`: `test_refusals_and_rejections_quoting_the_learner_never_reach_the_report` (a refusal and a 400 both quoting the answer; JSON report, text output and both written reports checked), `test_a_failed_diagnosis_keeps_its_reason_in_the_report` (codes kept, the provider's message not), `test_a_usage_limit_stops_that_profile_and_shows_in_its_allowance` |
| F4 | Medium | Historical grading ignores the frozen required-method contract | fixed | `0c445c246` | `test_ai_compare.py::test_grading_reads_the_contract_the_answer_was_graded_under` (prompt and dry-run estimate) |
| F5 | Medium | Comparison verdicts never reach `judgment_ledger` | fixed | `0c445c246` | `test_ai_compare.py`: `test_a_run_on_a_copy_reports_agreement_validity_latency_tokens_and_allowance` (10 judgments in the copy, linked from the report, none in the original, every other table of the copy unchanged), `test_a_draft_the_tutor_would_reject_is_invalid` (an invalid verdict is recorded too), `test_a_failed_diagnosis_keeps_its_reason_in_the_report` (no verdict, no judgment) |
| F6 | Medium | Comparison bypasses the required spend accounting | fixed | `0c445c246` | `test_ai_compare.py`: `test_the_dry_run_names_the_plan_and_sends_nothing`, `test_the_text_dry_run_prints_the_estimate`, `test_a_generation_only_dry_run_estimates_its_one_call`, `test_a_run_on_a_copy_reports_agreement_validity_latency_tokens_and_allowance` (admission, reconciliation, every root receipt's declared caps) |

The six findings share `src/learnloop/cli/ai_compare.py`, so they landed in
one commit (hunk-level staging is interactive and unavailable here); its
message names each.

Found by this fix step's own gate (not a review finding, inside the stage):

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| G1 | Low | Two compare runs in one second shared `<stamp>.json`; the second overwrote the first | fixed: a report is `<stamp>-<run_id>.json` (the `compare_run_id` its judgments carry), written with exclusive create | `a6de0969f` | `test_ai_compare.py::test_each_run_writes_its_own_report` (failed before the fix: the name held no run id); the first full-suite run failed `test_refusals_and_rejections_quoting_the_learner_never_reach_the_report` on it (1 report, not 2) |

### Claims that did not hold

| Claim | Verdict | Where |
|---|---|---|
| "Backup-API copy; original untouched" | fixed (F1) | `0c445c246` |
| Generation validity reflects real work | fixed (F2) | `0c445c246` |
| "Ids and numbers only; no learner text or model prose" | fixed (F3) | `0c445c246` |
| "Cost estimated from reported usage" | fixed (F6) | `0c445c246` |
| The working-vault check "fails closed" (missing `git` let a vault through) | fixed: without git only the copy `--copy-from` just made passes | `0c445c246`; `test_without_git_only_a_fresh_copy_is_compared` |
| "A pinned route never falls back" | corrected: only an explicit or environment selection never falls back; an `[ai.routing]` entry does (`fallback_provider_for`) | test `test_active_chatgpt_falls_back_to_codex_while_the_plan_is_paused` (`0c445c246`) now asserts both; record §4/§8 corrected in `107778f16` |

### Reproduction first

A probe of six tests, each asserting the defect, was run against the
reviewed code (`src/` and `migrations/` exported from `1c036a78e` and put
first on the path with `-o pythonpath=…`, since `pyproject.toml` prepends
`src`): **6 passed**, so every defect was present:

- F1: the copy's `storage.sqlite_path` still resolved to the external
  `learner.db`, and a run on the copy wrote its receipts there.
- F2: a draft with `transfer_criterion = None` and an empty scenario was
  reported `valid: true`.
- F3: the written report contained the 400's or the refusal's sentinel, which
  quoted the learner's answer.
- F4: the grading prompt carried the item's edited statement ("Use row
  reduction", "Edited after the answer.").
- F5: five verdicts, `judgment_ledger` empty in the copy.
- F6: a generation-only dry run's whole estimate was
  `{"grading_input_tokens": []}`.

On the fixed tree the same probe fails 6 of 6 (each defect gone). The probe
was a temporary file and is not committed; the tests in the table are the
permanent regressions.

### What changed

- **F1** (`copy_vault`, `database_location_reason`). The source's configured
  `storage.sqlite_path` is read first (`load_config(..., load_environment=False)`).
  Its file name goes to `copy_tree_with_databases(database_names=…)`, so a
  `state.db` and its `-wal` are copied through the backup API, never as
  bytes. A database configured outside the source (absolute, or `..`) is
  backed up into the copy with `backup_database`; a name collision inside the
  source refuses. Whenever the configured path would still name the source's
  database from the copy, the copy's `learnloop.toml` is rewritten (tomlkit,
  comments kept) to its own database, and the copy is refused unless that
  database resolves inside it. A `--vault` whose database lies outside the
  vault is refused (`database_outside_vault`) before anything opens it.
- **F2.** `tutor/teach_back.py` exposes `validate_teach_back_authoring`, the
  tutor's own `_validate_teach_back_authoring` with the same facet allowance
  (the source item's evidence facets), quest and learning-object title. The
  comparison reports its fixed rejection sentence (`rejection`); the old
  reduced checks are gone.
- **F3.** A failure is recorded as its class, code, HTTP status, parameter
  name, request and receipt ids and a hint written here (`_HINTS`, or the
  route's remedy); no `detail` field. The ChatGPT plan's classified errors
  carry their structured fields as `provider_error` (status, code, param,
  request id, remedy) so no message has to be parsed; each id must match a
  plain identifier pattern or it is dropped. A diagnosis failure's fields
  come from a forwarding client that remembers the last exception
  (`run_diagnosis` records only the class).
- **F4.** `_grading_contract` calls `attempt_graded_contract` and
  `regrade_reads_contract` exactly as `regrade_attempt` does: a
  method-explicit answer is graded and validated under its frozen statement,
  rubric and method; everything else reads the item as it is now. The
  dry-run estimate builds the same context. Diagnosis already matched
  production (the async diagnoser also reads `resolved_rubric`).
- **F5.** Each verdict (a grade, valid or not; a completed or
  validation-rejected diagnosis; a draft's validity) appends to the copy's
  `judgment_ledger` through `db.stores.judgments.append_judgment`: tasks
  `ai_compare_grading` / `ai_compare_diagnosis` / `ai_compare_generation`,
  left the attempt or item, right kind `ai_profile` and id the profile, judge `llm` or
  `diagnoser`, the answering model, the production prompt version and input
  hash (`blind_grading_context_hash`, the diagnosis context hash, the
  authoring prompt's content key), rationale `{"authority": "none",
  compare_run_id, compare_version}`. No serving reader names these tasks
  (the readers filter by `stuck_reading`, `own_route_rule`, `same_cause`,
  `family_decision`, …; `decider agreement` pairs only with Decider rows),
  so they are never evidence or certification. The report links each call
  to its `judgment_id` and `receipt_ids`.
- **F6.** Each profile runs under a `SpendBudget(subscription=True)` whose
  call cap is the plan and whose token and dollar caps are estimated only
  (the owner's exemption: no physical-request bound). Every call is admitted
  with `budget.request` before it is sent (so its root receipt's
  `budget_json` records `billing: subscription`, `cost_basis: estimated_only`,
  `physical_request_bound: false` and the `ai_compare` run, kind, target and
  planned tokens), then reconciled with the usage the transport reported;
  each call and profile reports `subscription_usage_estimate` and the
  budget's use. The dry run estimates every planned call (input from the
  exact prompt, a snapshot diagnosis's export capped at
  `max_workspace_chars`, the route's output budget) and prints it in text as
  well as JSON. `COMPARE_VERSION` is 2.

### Spend and calls

No paid or live model call in this fix step (its earlier runs left no
report either: `fixtures-local/reports/ai-compare/` holds only the stage's
two reports). One free dry run of the fixed command on the stage's backup
copy `fixtures-local/compare-probability` (`--profiles codex,chatgpt
--dry-run`): nothing sent; per profile 4 calls, ~79,955 tokens planned
(input ~11,664, snapshot export ~2,755, output budget up to 65,536); the
grading prompts match the stage's earlier ~3.7k-token measurement. The
tracked fixtures were not touched.

### Gate

Run on the final code tree `a6de0969f` (the only later commit adds this
record). `TMPDIR` was the worktree's `fixtures-local/tmp`; both suite runs
held `flock /tmp/learnloop-fullsuite.lock` and used `uv run --no-sync`.
`/tmp` had room throughout (14 GB free), so no earlier out-of-space failure
was carried over.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (178 packages; pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | 22 contracts kept, 0 broken |
| `pytest -n auto` (full suite) | **11,880 passed, 1 skipped**, 0 failed (14 min 34 s); the skip is `test_served_paths_map_to_export_entries_under_input_provenance` (`importorskip` until provenance reaches this branch) |
| `pytest -m durability` | **106 passed**, 11,775 deselected (1 min 51 s) |
| stage tests (`test_ai_compare` 26, `test_chatgpt_plan_workspace` 26 with the one skip, `test_chatgpt_plan_provider`) | green (in the full suite) |
| `tests/test_coordinated_migrations.py` | green (in the full suite) |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated in `1d40f8de7` (`judgment_ledger` now names `cli/ai_compare.py` as a writer; schema head unchanged at 204); validate `errors: []` on the final tree |
| CLI help snapshot | `ai compare` help updated in `0c445c246`; green |
| RPC pins | unchanged (no sidecar method changed) |
| frontend / `src-tauri` | untouched: npm and cargo checks not required |
| tracked fixtures | `git status` clean after both runs |

An earlier full-suite run on `1d40f8de7` failed one test (11,878 passed, 1
skipped, 1 failed): G1 above, fixed in `a6de0969f` before this gate.

### Open questions (defaults in force)

1. **Live tool interoperability on the plan** (the review's spec row:
   unverified live). Default: unchanged from the stage record §9.2; the
   owner's own comparison is the verification, and `workspace_mode =
   "inline"` is one setting away.
2. **Comparison judgments in an analysis tool.** They sit in the copy's
   ledger under `ai_compare_*` tasks; no command reads them yet. Default:
   the report is the reading surface; a future agreement view may read the
   ledger by `compare_run_id`.
3. **A `--vault` with an external database is refused** even when the owner
   means it. Default: refuse (the comparison always runs on a copy, and a
   copy holds its database inside).
