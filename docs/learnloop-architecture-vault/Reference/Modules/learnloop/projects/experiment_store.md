---
title: "learnloop.projects.experiment_store"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/projects/experiment_store.py"
source_paths:
  - "src/learnloop/projects/experiment_store.py"
source_commit: "0d65bad5f497b745c7208230c32a3a19f6ed24b2"
source_commit_timestamp: "2026-10-12T02:33:27-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.projects"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.projects.experiment_store module"
  - "src/learnloop/projects/experiment_store.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-projects"
---

# `learnloop.projects.experiment_store`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.projects.experiment_store` exists within [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] to own the behavior summarized by its module contract: ``<vault>/projects/project_store.sqlite``: the standalone M1 store (spec §6.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/projects/experiment_store.py](../../../../../../src/learnloop/projects/experiment_store.py) |
| Source lines | 977 |
| Owning package | [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0d65bad5f497b745c7208230c32a3a19f6ed24b2` |
| Commit timestamp | `2026-10-12T02:33:27-04:00` |

## Public API

- `store_path(vault_root: Path) -> Path` ([source](../../../../../../src/learnloop/projects/experiment_store.py), line 294)
- `pending_path(vault_root: Path) -> Path` ([source](../../../../../../src/learnloop/projects/experiment_store.py), line 298)
- `class StoreSchemaError(RuntimeError)` ([source](../../../../../../src/learnloop/projects/experiment_store.py), line 302) — The store was written by a newer LearnLoop.
- `class ProjectStore` ([source](../../../../../../src/learnloop/projects/experiment_store.py), line 324) — Short transactions over the standalone store; owns every SQL write.
  - `__init__(self, path: Path, *, busy_timeout_ms: int | None=None, read_only: bool=False) -> None` (line 333; internal)
  - `for_vault(cls, vault_root: Path, *, busy_timeout_ms: int | None=None) -> 'ProjectStore'` (line 344; public)
  - `existing(cls, vault_root: Path, *, busy_timeout_ms: int | None=None, read_only: bool=False) -> 'ProjectStore | None'` (line 348; public) — Open the store only if it exists; never create it (``read_only``: never write it).
  - `_connect(self) -> sqlite3.Connection` (line 360; internal)
  - `connection(self) -> Iterator[sqlite3.Connection]` (line 367; public)
  - `_schema_of(self, connection: sqlite3.Connection) -> int` (line 376; internal)
  - `_check_schema(self) -> None` (line 384; internal) — A read-only open: refuse a newer store, read an older one as it is.
  - `_ensure_schema(self) -> None` (line 390; internal)
  - `meta(self, key: str) -> str | None` (line 407; public)
  - `set_meta(self, key: str, value: str) -> None` (line 412; public)
  - `repos(self, *, enabled_only: bool=False) -> list[dict[str, Any]]` (line 422; public)
  - `repo(self, repo_id: str) -> dict[str, Any] | None` (line 427; public)
  - `repo_by_path(self, path: str) -> dict[str, Any] | None` (line 432; public)
  - `enroll_repo(self, row: dict[str, Any]) -> tuple[dict[str, Any], bool]` (line 437; public) — Insert a repo, or re-enable the existing one.
  - `set_repo_enabled(self, repo_id: str, enabled: bool) -> None` (line 460; public)
  - `set_hook_installed(self, repo_id: str, installed: bool) -> None` (line 464; public)
  - `record_repo_sweep(self, repo_id: str, *, swept_at: str, error: str | None) -> None` (line 468; public)
  - `known_commit_shas(self, repo_id: str) -> set[str]` (line 477; public)
  - `diff_with_patch_id(self, repo_id: str, patch: str) -> dict[str, Any] | None` (line 485; public)
  - `diff_for_commit(self, repo_id: str, sha: str) -> dict[str, Any] | None` (line 493; public)
  - `diff_for_worktree_bundle(self, repo_id: str, bundle_hash: str) -> dict[str, Any] | None` (line 501; public)
  - `insert_diff(self, row: dict[str, Any]) -> tuple[dict[str, Any], bool]` (line 509; public) — Insert a capture; a concurrent duplicate returns the stored row.
  - `diff(self, diff_id: str) -> dict[str, Any] | None` (line 540; public)
  - `diffs(self, *, repo_id: str | None=None, probe_status: str | None=None) -> list[dict[str, Any]]` (line 545; public)
  - `record_generation_failure(self, diff_id: str, *, error: str, max_attempts: int) -> None` (line 560; public)
  - `finish_generation(self, diff_id: str, *, status: str, generated_at: str) -> None` (line 569; public)
  - `retry_failed_generation(self, diff_id: str) -> bool` (line 576; public) — Back to ``pending`` with fresh attempts; probes from finished stages are kept.
  - `add_provenance(self, row: dict[str, Any]) -> None` (line 589; public)
  - `latest_provenance(self) -> dict[str, dict[str, Any]]` (line 597; public) — Per diff, the newest self-reported accept style and usage tap.
  - `probes_for_diff(self, diff_id: str) -> list[dict[str, Any]]` (line 612; public)
  - `insert_probe_candidates(self, rows: list[dict[str, Any]], judgments: list[dict[str, Any]]=()) -> None` (line 621; public) — Insert a diff's candidates and their validity verdicts in one transaction.
  - `record_closed_book_answers(self, answers: dict[str, str], *, model: str) -> None` (line 638; public)
  - `record_closed_book_grades(self, grades: list[dict[str, Any]]) -> int` (line 646; public) — Each ``{probe_id, verdict, score, generic, judgment}`` with its judgment, atomically.
  - `select_probes(self, probe_ids: list[str]) -> None` (line 668; public)
  - `probe(self, probe_id: str) -> dict[str, Any] | None` (line 675; public)
  - `all_probes(self) -> list[dict[str, Any]]` (line 680; public)
  - `due_probes(self, now_iso: str, *, repo_id: str | None=None) -> list[dict[str, Any]]` (line 684; public) — Selected probes past their seal with no response, oldest first.
  - `insert_response(self, row: dict[str, Any], judgment: dict[str, Any] | None=None) -> bool` (line 703; public) — Insert a response (and the owner verdict it carries) in one transaction.
  - `response(self, response_id: str) -> dict[str, Any] | None` (line 721; public)
  - `response_for_probe(self, probe_id: str) -> dict[str, Any] | None` (line 726; public)
  - `responses(self, *, grade_status: str | None=None) -> list[dict[str, Any]]` (line 733; public)
  - `record_grade(self, response_id: str, *, score: float, verdict: str, feedback: str, provider: str, model: str, prompt_version: str, graded_at: str, judgment: dict[str, Any]) -> bool` (line 742; public) — The grade and its judgment, atomically; ``False`` if the answer was no longer pending.
  - `retry_failed_grade(self, response_id: str) -> bool` (line 764; public) — Back to ``pending`` with fresh attempts; the answer and receipts are kept.
  - `record_grade_failure(self, response_id: str, *, max_attempts: int) -> None` (line 775; public)
  - `record_adjudication(self, response_id: str, *, score: float, note: str, adjudicated_at: str, judgment: dict[str, Any]) -> bool` (line 784; public) — The owner's adjudication and its judgment, atomically.
  - `enqueue_pending(self, entries: list[dict[str, Any]], *, offset: int, received_at: str) -> int` (line 811; public) — Queue hook entries and advance the pending-file offset in one transaction.
  - `pending_commits(self, repo_id: str | None=None) -> list[dict[str, Any]]` (line 829; public)
  - `dequeue_pending(self, repo_id: str, sha: str) -> None` (line 840; public)
  - `note_unattributed(self, row: dict[str, Any]) -> bool` (line 846; public)
  - `resolve_unattributed(self, repo_id: str, sha: str, diff_id: str) -> None` (line 855; public)
  - `unattributed(self, *, unresolved_only: bool=True) -> list[dict[str, Any]]` (line 862; public)
  - `append_judgment(self, *, task: str, left_kind: str, left_id: str, judge: str, input_hash: str, verdict: str, rationale: str, created_at: str, score: float | None=None, judge_model: str | None=None, prompt_version: str | None=None, supersedes_id: str | None=None) -> str` (line 871; public)
  - `judgments(self, *, task: str | None=None, left_id: str | None=None) -> list[dict[str, Any]]` (line 898; public)
  - `record_model_event(self, action: str, event: dict[str, Any], *, owner_kind: str, owner_id: str, diff_id: str | None=None, disclosure: dict[str, Any] | None=None, cost_label: str | None=None) -> None` (line 915; public) — The ``observe_model_calls`` sink: a durable start, then a finish.
  - `set_receipt_estimate(self, call_id: str, estimated_usd: float | None) -> None` (line 953; public)
  - `receipts(self, *, diff_id: str | None=None) -> list[dict[str, Any]]` (line 959; public)

### Module constants

- `_LOG` ([src/learnloop/projects/experiment_store.py](../../../../../../src/learnloop/projects/experiment_store.py), line 31)
- `STORE_SCHEMA_VERSION` ([src/learnloop/projects/experiment_store.py](../../../../../../src/learnloop/projects/experiment_store.py), line 36)
- `STORE_RELATIVE_PATH` ([src/learnloop/projects/experiment_store.py](../../../../../../src/learnloop/projects/experiment_store.py), line 37)
- `PENDING_RELATIVE_PATH` ([src/learnloop/projects/experiment_store.py](../../../../../../src/learnloop/projects/experiment_store.py), line 38)
- `_SCHEMA` ([src/learnloop/projects/experiment_store.py](../../../../../../src/learnloop/projects/experiment_store.py), line 40)
- `_RECEIPT_START_FIELDS` ([src/learnloop/projects/experiment_store.py](../../../../../../src/learnloop/projects/experiment_store.py), line 283)
- `_RECEIPT_FINISH_FIELDS` ([src/learnloop/projects/experiment_store.py](../../../../../../src/learnloop/projects/experiment_store.py), line 287)
- `_JUDGMENT_COLUMNS` ([src/learnloop/projects/experiment_store.py](../../../../../../src/learnloop/projects/experiment_store.py), line 306)

### Explicit exports

`__all__` declares:

- `PENDING_RELATIVE_PATH`
- `ProjectStore`
- `STORE_RELATIVE_PATH`
- `STORE_SCHEMA_VERSION`
- `StoreSchemaError`
- `pending_path`
- `store_path`

## Internal implementation anchors

- `_insert_judgment(connection: sqlite3.Connection, judgment: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/projects/experiment_store.py), line 312) — Insert one ``judgments`` row on ``connection`` (inside its transaction).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]] — imports `ProjectStore`
- [[Reference/Modules/learnloop/projects/ai_runtime|learnloop.projects.ai_runtime]] — imports `ProjectStore`
- [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]] — imports `ProjectStore`, `pending_path`, `store_path`; statically calls `pending_path`, `store_path`
- [[Reference/Modules/learnloop/projects/hooks|learnloop.projects.hooks]] — imports `ProjectStore`, `pending_path`; statically calls `pending_path`
- [[Reference/Modules/learnloop/projects/probes|learnloop.projects.probes]] — imports `ProjectStore`, `store_path`; statically calls `store_path`
- [[Reference/Modules/learnloop/projects/report|learnloop.projects.report]] — imports `ProjectStore`, `STORE_SCHEMA_VERSION`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]] — imports `JournalModeSwitchError`, `switch_to_wal`; calls `switch_to_wal`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `json`, `logging`, `pathlib`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]], [[Reference/Modules/learnloop/projects/ai_runtime|learnloop.projects.ai_runtime]], [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]], [[Reference/Modules/learnloop/projects/hooks|learnloop.projects.hooks]], [[Reference/Modules/learnloop/projects/probes|learnloop.projects.probes]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ai_tool_isolation.py](../../../../../../tests/test_ai_tool_isolation.py) — direct import
  - `test_a_confinable_agent_runs_inside_the_isolation`
  - `test_an_unconfinable_agent_is_refused_before_any_request`
  - `test_the_kill_switch_runs_unconfined_and_says_so`
- [tests/test_project_atomicity.py](../../../../../../tests/test_project_atomicity.py) — direct import
- [tests/test_project_blindness.py](../../../../../../tests/test_project_blindness.py) — direct import
  - `test_rendered_prompts_carry_no_provenance_declaration_or_closed_book_origin`
- [tests/test_project_capture.py](../../../../../../tests/test_project_capture.py) — direct import
  - `test_a_pending_entry_survives_a_sweep_while_its_repo_is_unavailable`
  - `test_a_single_repo_sweep_keeps_other_repos_pending_entries`
  - `test_pending_list_captures_agent_commits_outside_the_branch_window`
  - `test_pending_list_feeds_trailerless_commits_to_the_unattributed_list`
- [tests/test_project_cli.py](../../../../../../tests/test_project_cli.py) — direct import
  - `test_accept_and_provenance_commands`
  - `test_end_to_end_answering_and_reveal`
  - `test_failed_generation_can_be_retried_without_re_authoring`
  - `test_failed_grades_can_be_retried_with_spend_controls`
  - `test_hidden_retries_are_admitted_only_against_max_retries`
  - `test_metered_calls_carry_their_admitted_output_limit`
  - `test_metered_output_limit_reaches_the_provider_request_and_its_repair`
  - `test_metered_routes_fail_closed_without_a_price`
  - `test_no_command_renders_a_sealed_question`
  - `test_probes_spends_one_budget_across_generation_and_grading`
  - `test_quitting_leaves_questions_due`
  - `test_sweep_dry_run_includes_commits_the_real_sweep_would_capture`
  - `test_sweep_dry_run_includes_queued_hook_entries`
  - `test_sweep_dry_run_makes_no_calls_and_no_writes`
- [tests/test_project_experiment_store.py](../../../../../../tests/test_project_experiment_store.py) — direct import
  - `test_a_read_only_open_neither_upgrades_nor_writes_an_older_store`
  - `test_a_read_only_open_still_refuses_a_newer_store`
  - `test_a_version_1_store_gains_the_pending_queue`
  - `test_existing_never_creates_the_store`
  - `test_m1_never_writes_state_sqlite`
  - `test_replay_and_rebuild_make_no_git_model_or_subprocess_calls`
  - `test_responses_are_practice_only`
  - `test_store_runs_in_wal_with_full_sync_in_production`
  - `test_store_schema_is_versioned`
- [tests/test_project_hooks.py](../../../../../../tests/test_project_hooks.py) — direct import
  - `test_auto_sweep_survives_a_locked_store`
  - `test_existing_shell_hook_is_preserved_and_restored`
  - `test_hook_exits_zero_under_injected_failures`
  - `test_installed_hook_appends_one_line_per_commit`
  - `test_linked_worktrees_sharing_a_hook_each_log_their_own_commits`
- [tests/test_project_probes.py](../../../../../../tests/test_project_probes.py) — direct import
  - `test_selection_is_seeded_and_reproducible`
- [tests/test_project_redaction.py](../../../../../../tests/test_project_redaction.py) — direct import
  - `test_capture_never_stores_secret_files_or_lines`
  - `test_hunk_header_secrets_never_reach_the_store`
- [tests/test_project_report.py](../../../../../../tests/test_project_report.py) — direct import
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_project_calls_reserve_the_transport_retry_at_its_doubled_allowance`

## Modification guidance

- Make changes here when the responsibility remains experiment store within learnloop.projects; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/projects/experiment_store.py](../../../../../../src/learnloop/projects/experiment_store.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
