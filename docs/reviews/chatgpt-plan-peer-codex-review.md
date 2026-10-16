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

## Re-review

Review: Codex job `20261015-224415-8RpOsK` (gpt-6-astra, high effort,
read-only) of `1c036a78e..bf61e6eee`. F2, F3, F4 and F5 were confirmed
fixed; F1 and F6 were reopened through two new Medium findings, F7 and F8.
Both reproduced and are fixed; none was rejected.

### Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F7 (reopens F1) | Medium | Database path normalization changes which database is copied | fixed | `e187f179e` | `test_ai_compare.py::test_copy_from_backs_up_the_database_a_symlinked_path_opens[absolute]`, `[relative]`; `[inside]` is a guard for the behaviour kept |
| F8 (reopens F6) | Medium | Reported output budgets never reach the model requests | fixed | `e187f179e` | `test_ai_compare.py::test_each_request_carries_the_output_budget_its_estimate_reports` |

Earlier findings, as the re-review left them: F2, F3, F4, F5 confirmed
fixed (no change in this step); F1 and F6 closed by F7 and F8.

### Reproduction first

The three new tests were run against the reviewed tree (`bf61e6eee`)
before any source change: **3 failed, 1 passed**.

- F7 `[absolute]`: `storage.sqlite_path = <tmp>/data/current/../state.db`,
  where `current` links to `data/releases/v1`. The vault opens
  `data/releases/state.db` (`VaultPaths(...).sqlite_path.resolve()` says
  so), but the copy held the decoy at `data/state.db`: probe rows
  `[('decoy',)]`, not `[('opened',)]`.
- F7 `[relative]`: `current/../state.db`, with `current` (inside the vault)
  linking to a directory outside it. `normpath` read this as the vault's own
  `state.db`, which does not exist. The copy got no database (`copied ==
  []`), and its configuration named an empty path inside it.
- F7 `[inside]`: `data/state.db` through a symlinked `data` directory. This
  passed before and passes after: the tree copy backs it up through the
  link at `data/state.db`, and the fix must keep that.
- F8: three requests (a grading, a snapshot diagnosis and a teach-back
  draft) were captured through `run_compare()` with
  `ai.route_output_tokens` = 1234 / 2345 / 3456. Their `output_budget_tokens`
  were `[None, None, None]`, while the dry run reported 1234 / 2345 / 3456.

### What changed

- **F7** (`_opened_database`, `copy_vault`). The source's configured path is
  resolved to the file the vault opens. Each directory on the way is
  `realpath`'d, so a symlinked directory followed by `..` resolves where the
  kernel resolves it. The file name is kept as written. The lexical path is
  kept only when it reaches the same physical directory, so a database the
  tree holds through a symlink (the file itself, or a directory) stays the
  tree's and is copied in place. The copy's placement is checked separately,
  from its own configuration as written. The copy keeps a configured path
  only when it is exactly the plain relative path to the backup; otherwise
  the configuration is rewritten. The copy is refused unless its database
  is the backup the copy made, inside it. The `--vault` check
  (`database_location_reason`) already used `Path.resolve()` and needed no
  change.
- **F8** (`run_compare`). Each call runs under
  `generation_limit(<planned output_tokens>)`, the budget the estimate
  reserves (`output_budget`: `ai.route_output_tokens.<route>`, held to a
  profile's `max_tokens`, else the shared default). Neither subscription
  transport takes a hard cap. The ChatGPT plan states the budget once in
  the prompt (no `max_output_tokens`), and Codex does the same and also
  charges its JSON repair against what remains. The test checks every wire
  request, all three workspace rounds of the diagnosis included: each ends
  with its own budget, stated once. The subscription exemption still holds:
  no `single_request()` bound, and the diagnosis still makes its 3 physical
  requests. Each call's `spend` now records `output_budget_tokens`, and
  `COMPARE_VERSION` is 3 (judgments carry it in their rationale).

### Spend and calls

No paid, live or dry-run model call was made in this step. Every test uses
the fake Responses server on 127.0.0.1. The tracked fixtures were not
touched.

### Gate (re-review)

Run on the final code tree `444f96ec1` (the only later commit adds this
section). `TMPDIR` was the worktree's `fixtures-local/tmp`; both suite runs
held `flock /tmp/learnloop-fullsuite.lock` and used `uv run --no-sync`.
`/tmp` had 13 GB free.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (178 packages; pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | 22 contracts kept, 0 broken |
| `git diff --check` | clean |
| `pytest -n auto` (full suite) | **11,884 passed, 1 skipped**, 0 failed (19 min 25 s): the earlier 11,880 plus the 4 new tests. The skip is still `test_served_paths_map_to_export_entries_under_input_provenance` (`importorskip` until provenance reaches this branch) |
| `pytest -m durability` | **106 passed**, 11,779 deselected (1 min 53 s) |
| stage tests (`test_ai_compare` 30, `test_chatgpt_plan_*`, `test_output_budget`, `test_cli_help_snapshot`) | green: 117 passed, 1 skipped as a targeted run, and green in the full suite |
| `tests/test_coordinated_migrations.py` | green (in the full suite) |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated in `444f96ec1` (source commits only, plus `Config - voi_stopping`'s test citations now naming `test_ai_compare.py`; schema head unchanged at 204). Validate reports `errors: []` |
| CLI help snapshot | unchanged (no option or help text changed); green |
| RPC pins | unchanged (no sidecar method changed) |
| frontend / `src-tauri` | untouched: npm and cargo checks not required |
| tracked fixtures | `git status` clean after both runs |

### Open questions (defaults in force)

4. **Serving does not send these budgets on subscription routes.** With F8,
   every comparison request carries its route's output budget, and the
   same sentence goes to every profile. Serving grading
   (`attempts/grading.py`), teach-back authoring and diagnosis jobs on
   Codex or the plan send none: `ReviewSpend.request` applies
   `generation_limit` only on metered routes. So on a subscription route, a
   comparison prompt ends with one budget sentence that the serving prompt
   lacks. Default: keep it. It is the owner's output-budget policy ("the
   budget is what a request sends"), and it is identical across the
   profiles being compared. Making serving send it on subscription routes
   would change every serving role, which is outside this stage.
