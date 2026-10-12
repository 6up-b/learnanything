# Project understanding M1: Codex review fixes

Stage `projects-m1`, branch `projects/m1`, worktree `learnanything-projects-m1`.
The review covered `16db5ac5..projects/m1` at `adc8fba0` (codex-job `20261012-013023-L8egLz`).
The fixes run from `0fa326ee` to `fbaf4b7e`.

Each finding was reproduced first, as a failing test, before it was fixed. Every repo here is a temporary repo, and every model is a fake. Where a test needed the operating system, it ran real processes: bubblewrap, git worktrees and git hooks.

## Findings

| Id | Severity | Title | Verdict | Commit | Test, or reason |
|---|---|---|---|---|---|
| F1 | High | Secrets in Git hunk headers bypass redaction | fixed | `0fa326ee` | `test_project_redaction.py::test_hunk_header_context_is_scanned_and_coordinates_kept`, `::test_hunk_header_secrets_never_reach_the_store` (bundle, store and WAL bytes); `test_project_cli.py::test_hunk_header_secrets_never_reach_a_model` (every recorded prompt) |
| F2 | High | An empty working directory does not enforce disclosure or closed-book isolation | fixed | `8a48cb03` | `test_ai_tool_isolation.py`: real bubblewrap processes try to read the project store, `state.sqlite`, a repo file and agent transcripts and fail, including through the exact Codex launch path (the same launch reads them when not isolated); an agent that can't be confined is refused before any request; kill switch; fail-closed without bubblewrap |
| F3 | High | Metered output estimates are not enforced on requests | fixed | `128759f9` | `test_project_cli.py::test_metered_calls_carry_their_admitted_output_limit` (the subscription stays unbounded); `::test_metered_output_limit_reaches_the_provider_request_and_its_repair` (provider `max_tokens` 32, then 20 for the repair) |
| F4 | Medium | `project probes` grants the command's spend budget twice | fixed | `620cb6e2` | `test_project_cli.py::test_probes_spends_one_budget_across_generation_and_grading` (3 calls under `--max-calls 3`, was 5); `::test_probes_dry_run_estimates_generation_and_the_grading_it_enables` |
| F5 | Medium | A crash can leave a final grade without its judgment | fixed | `d1574869` | `test_project_atomicity.py`: a trigger aborts the judgment insert at each boundary (candidates, closed-book verdicts, grades, adjudications, unfair taps); nothing partial persists and a rerun completes with exactly one judgment each |
| F6 | Medium | Concurrent graders produce conflicting unsuperseded judgments | fixed | `48ef5a1d` (store guard in `d1574869`) | `test_project_atomicity.py::test_a_second_grader_waits_its_turn_instead_of_paying`; `::test_interleaved_graders_leave_one_outcome_and_report_it` (on pre-fix code it stored 0.0 and reported 0.9) |
| F7 | Medium | A model's rationale flag substitutes for verifying stated rationale | fixed | `f1221bc5` | `test_project_probes.py::test_a_rationale_flag_on_plain_code_is_not_a_stated_reason`, `::test_a_cited_comment_must_state_the_proposed_reason`, `::test_a_descriptive_commit_subject_is_not_a_reason`, `::test_the_reason_check_is_persisted_in_the_verifier_judgment` |
| F8 | Medium | Missing closed-book answers pass the specificity filter | fixed | `e3f2791c` | `test_project_probes.py::test_incomplete_closed_book_answers_never_pass_the_filter[empty, missing_one, duplicate, unknown]` |
| F9 | Medium | Partial sweeps permanently discard pending captures | fixed | `b276adec` | `test_project_capture.py::test_a_pending_entry_survives_a_sweep_while_its_repo_is_unavailable`, `::test_a_single_repo_sweep_keeps_other_repos_pending_entries`; `test_project_experiment_store.py::test_a_version_1_store_gains_the_pending_queue` |
| F10 | Medium | Failed answers have no supported recovery path | fixed | `aaadd4d9` | `test_project_cli.py::test_failed_grades_can_be_retried_with_spend_controls`, `::test_failed_generation_can_be_retried_without_re_authoring` |
| F11 | Medium | Sweep dry-run excludes the work the real command will capture | fixed | `71bec397` | `test_project_cli.py::test_sweep_dry_run_includes_commits_the_real_sweep_would_capture` (the estimate equals the calls the real sweep makes, and nothing is written); `::test_sweep_dry_run_includes_queued_hook_entries` |
| F12 | Medium | Hook installation misattributes commits across Git worktrees | fixed | `23ce6c39` | `test_project_hooks.py::test_linked_worktrees_sharing_a_hook_each_log_their_own_commits` (real linked worktrees); `::test_a_first_build_unguarded_block_is_replaced` |
| F13 | Medium | The sweep silently loses eligible history beyond 5,000 commits | fixed | `8e6eb492` | `test_project_capture.py::test_the_sweep_pages_through_history_beyond_one_git_log_page`, `::test_history_beyond_the_scan_limit_is_reported_not_silently_skipped` |
| F14 | Medium | M1 excludes small behavioral changes using an M1b-only threshold | fixed | `7f851d01` | `test_project_capture.py::test_small_behavioural_changes_are_probed` (a flipped comparison), `::test_a_diff_with_nothing_probeable_is_still_excluded` |
| F15 | Medium | The default grader does not perform the specified high-effort pass | fixed | `d52f5695` | `test_project_cli.py::test_project_grading_runs_at_high_effort_by_default`, `::test_the_effective_grading_request_carries_high_effort` (the effort the Codex turn starts with), `::test_grading_effort_leaves_chat_profiles_without_an_effort_alone` |

Fixed: 15. Rejected: 0. All three High findings are fixed.

## How each finding was fixed

- **F1.** `redact_diff` keeps a hunk header's coordinates and scans the source text git repeats after them. A match becomes `@@ -a,b +c,d @@ [REDACTED:<kind>]` and is counted. `SECRET_PATTERN_VERSION` is now `project-secrets-v2`, so captures record which scanner they had.
- **F2.** `learnloop.ai.isolation` adds a `tool_isolation` request and a deny-by-default bubblewrap sandbox:
  - system trees are read-only;
  - the empty working directory is writable;
  - there is no home, vault or repo;
  - the agent home is in memory, with only `auth.json` (writable, so token refreshes persist), `config.toml` and `installation_id` bound back. Session transcripts, history and memory databases stay out: they can hold the very code a closed-book check must not see;
  - it has its own PID namespace, so `/proc` shows no host process or working directory.

  Chat transports declare `tool_free`. The Codex SDK client declares `tool_isolation`, and under a request it launches its app-server through a sandboxed launcher (or wraps `sdk_launch_command`). It fails closed when bubblewrap is missing.

  Project calls require isolation (`project.require_tool_isolation = true`). A route that can't comply is not ready, and `PaidCalls` refuses it before admission. Receipts record `tool_isolation` (`tool_free`, `bubblewrap` or `none`), and the vault and enrolled repos are passed as hidden paths. The Codex subscription stays allowed, now sandboxed.
- **F3.** Metered calls run under `generation_limit(output_tokens)`. The chat client turns that into `max_tokens` and spends the JSON repair from the same budget. The subscription keeps no output restraint (rule 6). Each call's output budget gains a 4,000-token reasoning headroom so the enforced limit doesn't truncate reasoning models, and plans and calls share one set of budget helpers.
- **F4.** `project probes` builds one `PaidCalls` for the whole command. The dry run plans generation for due diffs plus a grade for every question the session could serve, counting the questions that generation would add.
- **F5.** The store writes each outcome together with its judgment in one transaction:
  - candidates with their validity verdicts;
  - closed-book verdicts;
  - grades;
  - adjudications, with the superseded grade read inside the same transaction;
  - unfair taps.
- **F6.** `grade_responses` takes a non-blocking `grade.lock` before any model call. A second grader reports `busy`, pays nothing and leaves the answers pending, and the CLI says so. `record_grade` accepts only a still-pending answer (F5), so if graders on different hosts still race, the loser writes nothing and reports `already_graded` with the outcome of record.
- **F7.** `stated_reason` checks every citation of a `why` candidate itself:
  - the span must be prose: a commit message, or a code comment judged from the cited source lines, so a quote without its `#` still counts;
  - it must contain a reason cue;
  - it must share at least two content terms with the reference answer, and at least a quarter of them.

  The flag proves nothing, and the check is stored in the verifier judgment. The fake's cited `why` now quotes the commit body that states the reason, not the descriptive subject.
- **F8.** A closed-book reply that is missing an id, repeats one or invents one fails the stage. The candidates stay `pending_closed_book`, and an attempt and the error are recorded. Grader replies with duplicate item ids fail the same way.
- **F9.** Hook entries move into `pending_commits` in the same transaction that advances the file offset. Each entry is removed only after its repo's sweep has processed it. Store schema 2 adds the table, and a version-1 store is upgraded in place, because every statement is idempotent.
- **F10.** `project grade --retry-failed` and `project sweep --retry-failed` work under the same caps and dry-run:
  - a dry run writes nothing;
  - a real run resets a failed item only once the run is admitted and its routes are ready;
  - answers, receipts and finished generation stages are kept, so a retried diff doesn't pay for authoring again.
- **F11.** Commit capture is split into a read-only `prepare_commit` and the store step. `discover_captures` runs both of the sweep's sources (the trailer window and the post-commit queue, including unread lines) without writing anything. `sweep --dry-run` plans generation for every capture that would be probed.
- **F12.** Each enrolled work tree gets its own hook block, marked with its repo id and guarded by its top-level path. A commit is logged only by the block of the worktree it was made in, and uninstalling removes only that block. A block from the first build is replaced on reinstall.
- **F13.** `git log` is read in pages of 2,000. Past 200,000 commits the sweep stops and marks the repo's history incomplete (status `partial`, `last_sweep_error`, dry-run discovery errors) instead of reporting success.
- **F14.** Only a capture with no probe-able file is excluded. `project.min_diff_lines` is documented as the M1b randomization threshold.
- **F15.** The grading role builds its client from a configuration copy whose routed profile takes `project.grading_reasoning_effort` (default `high`), when that profile takes an effort. An empty value keeps the route's own effort, and other roles and features are untouched. Routes, dry-runs and receipts report the effort.

## Notes

- **New config leaves (2):**
  - `project.grading_reasoning_effort = "high"`;
  - `project.require_tool_isolation = true`, a kill switch with honest receipts.

  Both are classified by the existing `project.` registry rule. The `mvp-0.9` defaults snapshot is updated, as in the stage's decision 12, and the configuration reference is regenerated (532 leaves).
- **No vault migration.** `state.sqlite` is untouched (G6 still passes). The project store moves to `user_version` 2, so M1b's tables will take 3.
- **Shared code touched:**
  - `ai/isolation.py` (new);
  - `ai/providers/codex.py`: sandboxing only under an explicit isolation request, so other features are unchanged;
  - `ai/providers/openai_chat.py`: declares `tool_free`;
  - `tests/structured_ai.py`: the payload fake declares `tool_free`.
- **Residuals, stated honestly:**
  - The sandbox needs Linux bubblewrap with unprivileged user namespaces; it works on this host. Elsewhere, project calls on Codex are refused until the kill switch is set.
  - The network isn't unshared, since the app-server needs its API. Environment variables pass through.
  - The reason check in F7 is lexical: it's conservative and may reject a real reason worded very differently.
  - A crash after a completed paid call but before its outcome commits re-pays that one call on resume. The paid output stays in the call receipt.
- **Stage review file updated.** `project-understanding-m1.md` now matches the fixes: isolation, small diffs, store schema 2, grading effort, retries, and open questions 4 and 7.

## Gate results

Run at `fbaf4b7e`, with only the review files uncommitted.

| Check | Result |
|---|---|
| `uv sync --extra dev` + `uv pip install pypdfium2` | OK (the stage doesn't touch `learnloop_mobile`, so `--extra mobile` wasn't needed) |
| `uv run lint-imports --no-cache` | **8 contracts kept, 0 broken** |
| `uv run pytest -n auto` | **6,309 passed**, 14 existing deprecation warnings, 185 s (6,256 before the fixes; 53 new tests) |
| `uv run pytest -m durability` | **63 passed**, 6,246 deselected |
| Project and isolation tests with `--durable-sqlite` | **157 passed** |
| `db_generate_reference.py` + `db_validate_reference.py` | **0 errors**: schema head 166 (no vault migration), 261 table notes, 532 config leaves. `validate_vault.py` passed (1,022 notes) |
| Frontend (`apps/learnloop-tauri`) | Not changed; npm checks not applicable |
| Live or paid model calls | None. Every model is a fake; bubblewrap, git worktrees and hooks ran for real in temporary directories |
