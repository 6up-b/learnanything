---
title: "learnloop.projects.capture"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/projects/capture.py"
source_paths:
  - "src/learnloop/projects/capture.py"
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
  - "learnloop.projects.capture module"
  - "src/learnloop/projects/capture.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-projects"
---

# `learnloop.projects.capture`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.projects.capture` exists within [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] to own the behavior summarized by its module contract: Automatic capture of agent-written diffs (spec §3, §4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py) |
| Source lines | 1269 |
| Owning package | [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0d65bad5f497b745c7208230c32a3a19f6ed24b2` |
| Commit timestamp | `2026-10-12T02:33:27-04:00` |

## Public API

- `estimate_tokens(text: str) -> int` ([source](../../../../../../src/learnloop/projects/capture.py), line 101) — A conservative token estimate for budgets and spend (≈3 bytes/token).
- `parse_trailers(raw: str) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/projects/capture.py), line 110)
- `strip_agent_trailers(message: str) -> str` ([source](../../../../../../src/learnloop/projects/capture.py), line 123) — Remove agent attribution (trailers, "Generated with" lines) from a message.
- `detect_agent(trailers: Iterable[tuple[str, str]], message: str='') -> str | None` ([source](../../../../../../src/learnloop/projects/capture.py), line 141) — The coding agent named by a commit's trailers, or ``None`` if none is.
- `class FileChange` ([source](../../../../../../src/learnloop/projects/capture.py), line 160)
  - `binary(self) -> bool` (line 168; public)
- `list_changes(repo: Path, base: str, head: str | None) -> list[FileChange]` ([source](../../../../../../src/learnloop/projects/capture.py), line 176) — Changed tracked files between ``base`` and ``head`` (``None``: working tree).
- `parse_hunks(diff_text: str) -> list[tuple[int, int]]` ([source](../../../../../../src/learnloop/projects/capture.py), line 264) — New-side ``(start, end)`` line ranges (1-based, inclusive) of each hunk.
- `scope_range(lines: list[str], start: int, end: int) -> tuple[int, int] | None` ([source](../../../../../../src/learnloop/projects/capture.py), line 286) — The enclosing function/class around a hunk, by header and indentation.
- `class Bundle` ([source](../../../../../../src/learnloop/projects/capture.py), line 368)
- `build_bundle(repo: Path, *, base: str, head: str | None, snapshot_kind: str, base_sha: str | None, head_sha_value: str | None, changes: list[FileChange], untracked: list[str], commit_message: str, rules: PathRules, config: LearnLoopConfig) -> Bundle` ([source](../../../../../../src/learnloop/projects/capture.py), line 441)
- `class BundleIntegrityError(RuntimeError)` ([source](../../../../../../src/learnloop/projects/capture.py), line 545) — A stored bundle is missing or no longer matches its content hash.
- `load_bundle(vault_root: Path, digest: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/capture.py), line 549)
- `enroll_repo(vault_root: Path, config: LearnLoopConfig, repo_path: Path, *, clock: Clock | None=None, backfill_days: int | None=None, context_scope: str='diff') -> tuple[dict[str, Any], bool]` ([source](../../../../../../src/learnloop/projects/capture.py), line 588)
- `find_repo(store: ProjectStore, repo: str | Path) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/projects/capture.py), line 621) — An enrolled repo by id, path, or any path inside its work tree.
- `class CaptureResult` ([source](../../../../../../src/learnloop/projects/capture.py), line 639)
  - `as_dict(self) -> dict[str, Any]` (line 645; public)
- `class PreparedCapture` ([source](../../../../../../src/learnloop/projects/capture.py), line 750) — A commit capture worked out from git alone: nothing is stored yet.
  - `excluded_reason(self, config: LearnLoopConfig) -> str | None` (line 763; public)
- `prepare_commit(store: ProjectStore, config: LearnLoopConfig, repo_row: dict[str, Any], sha: str, *, agent: str | None=None, agent_source: str | None=None, info: dict[str, Any] | None=None) -> PreparedCapture | CaptureResult` ([source](../../../../../../src/learnloop/projects/capture.py), line 767) — Everything a commit capture needs, read-only (git and store reads).
- `capture_commit(store: ProjectStore, vault_root: Path, config: LearnLoopConfig, repo_row: dict[str, Any], sha: str, *, capture_source: str, trigger: str, clock: Clock | None=None, agent: str | None=None, agent_source: str | None=None, info: dict[str, Any] | None=None) -> CaptureResult` ([source](../../../../../../src/learnloop/projects/capture.py), line 833)
- `capture_working_tree(store: ProjectStore, vault_root: Path, config: LearnLoopConfig, repo_row: dict[str, Any], *, clock: Clock | None=None, agent: str | None=None, include_untracked: bool=False, message: str='') -> CaptureResult` ([source](../../../../../../src/learnloop/projects/capture.py), line 870) — Capture uncommitted changes (staged and unstaged) against HEAD.
- `class SweepReport` ([source](../../../../../../src/learnloop/projects/capture.py), line 965)
  - `as_dict(self) -> dict[str, Any]` (line 980; public)
- `sweep(vault_root: Path, config: LearnLoopConfig, *, clock: Clock | None=None, trigger: str='manual', repo_ids: set[str] | None=None, busy_timeout_ms: int | None=None) -> SweepReport` ([source](../../../../../../src/learnloop/projects/capture.py), line 1084) — Capture every new agent-trailer commit in enrolled repos (git only).
- `discover_captures(vault_root: Path, config: LearnLoopConfig, *, repo_ids: set[str] | None=None) -> tuple[list[PreparedCapture], list[str]]` ([source](../../../../../../src/learnloop/projects/capture.py), line 1150) — What ``sweep`` would capture now, without writing anything (for dry runs).
- `auto_sweep(vault_root: Path, config: LearnLoopConfig | None, *, clock: Clock | None=None, trigger: str='app_start', min_interval_minutes: int | None=None, busy_timeout_ms: int=1000) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/capture.py), line 1205) — The automatic sweep at app start and plan build.

### Module constants

- `_LOG` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 60)
- `BUNDLE_FORMAT` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 62)
- `MAX_FILES_PER_CAPTURE` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 63)
- `MAX_UNTRACKED_FILE_BYTES` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 64)
- `MAX_EXCERPT_FILE_BYTES` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 65)
- `MAX_SCOPE_LINES` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 66)
- `SWEEP_PAGE_COMMITS` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 70)
- `SWEEP_MAX_SCANNED_COMMITS` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 71)
- `AGENT_TRAILER_KEYS` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 72)
- `_DIFF_FLAGS` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 73)
- `AGENTS` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 74)
- `_AGENT_RULES` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 76)
- `_BODY_MARKERS` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 87)
- `_HUNK_RE` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 90)
- `_SCOPE_HEADER_RE` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 91)
- `_TRAILER_LINE_RE` ([src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py), line 120)

### Explicit exports

`__all__` declares:

- `AGENTS`
- `BUNDLE_FORMAT`
- `Bundle`
- `BundleIntegrityError`
- `CaptureResult`
- `FileChange`
- `SweepReport`
- `auto_sweep`
- `build_bundle`
- `capture_commit`
- `capture_working_tree`
- `detect_agent`
- `discover_captures`
- `enroll_repo`
- `estimate_tokens`
- `find_repo`
- `list_changes`
- `load_bundle`
- `parse_hunks`
- `parse_trailers`
- `prepare_commit`
- `PreparedCapture`
- `scope_range`
- `strip_agent_trailers`
- `sweep`

## Internal implementation anchors

- `_range_args(base: str, head: str | None) -> list[str]` ([source](../../../../../../src/learnloop/projects/capture.py), line 172)
- `_literal(path: str) -> str` ([source](../../../../../../src/learnloop/projects/capture.py), line 217)
- `_file_diff(repo: Path, base: str, head: str | None, change: FileChange) -> str` ([source](../../../../../../src/learnloop/projects/capture.py), line 221)
- `_untracked_diff(repo: Path, path: str) -> str` ([source](../../../../../../src/learnloop/projects/capture.py), line 230)
- `_head_lines(repo: Path, head: str | None, path: str) -> list[str] | None` ([source](../../../../../../src/learnloop/projects/capture.py), line 239) — Head-side text lines of ``path``; ``None`` when unavailable or not text.
- `_indent(line: str) -> int` ([source](../../../../../../src/learnloop/projects/capture.py), line 281)
- `_merge(ranges: Iterable[tuple[int, int]]) -> list[tuple[int, int]]` ([source](../../../../../../src/learnloop/projects/capture.py), line 329)
- `class _BundleFile` ([source](../../../../../../src/learnloop/projects/capture.py), line 343)
- `_context_ranges(item: _BundleFile, context: int) -> list[tuple[int, int]]` ([source](../../../../../../src/learnloop/projects/capture.py), line 382)
- `_fit_budget(items: list[_BundleFile], message_tokens: int, budget: int, context: int) -> bool` ([source](../../../../../../src/learnloop/projects/capture.py), line 393) — Apply ±context, extend to scopes within budget, else shrink.
- `_strip_credentials(url: str | None) -> str | None` ([source](../../../../../../src/learnloop/projects/capture.py), line 566)
- `_remote_url(repo: Path) -> str | None` ([source](../../../../../../src/learnloop/projects/capture.py), line 581)
- `_commit_info(repo: Path, sha: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/capture.py), line 654)
- `_parse_commit_record(record: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/capture.py), line 660)
- `_excluded_reason(bundle: Bundle, config: LearnLoopConfig) -> str | None` ([source](../../../../../../src/learnloop/projects/capture.py), line 671) — Why a capture is not probed: only when no probe-able file is left.
- `_store_capture(store: ProjectStore, vault_root: Path, config: LearnLoopConfig, repo_row: dict[str, Any], bundle: Bundle, *, snapshot_kind: str, base_sha: str | None, head: str | None, patch: str | None, agent: str, agent_source: str, capture_timing: str, capture_source: str, trigger: str, committed_at: str | None, clock: Clock | None, rules: PathRules) -> CaptureResult` ([source](../../../../../../src/learnloop/projects/capture.py), line 687)
- `_agent_commits(repo: Path, since_iso: str) -> tuple[list[dict[str, Any]], bool]` ([source](../../../../../../src/learnloop/projects/capture.py), line 932) — Agent commits in the capture window (oldest first), and whether all were scanned.
- `_tally(report: SweepReport, result: CaptureResult) -> None` ([source](../../../../../../src/learnloop/projects/capture.py), line 998)
- `_read_pending(vault_root: Path, store: ProjectStore) -> tuple[list[dict[str, Any]], int, int]` ([source](../../../../../../src/learnloop/projects/capture.py), line 1007) — New pending-list entries since the stored byte offset, and the new offset.
- `_process_pending(store: ProjectStore, vault_root: Path, config: LearnLoopConfig, repo_row: dict[str, Any], repo: Path, sha: str, known: set[str], report: SweepReport, summary: dict[str, Any], *, trigger: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/projects/capture.py), line 1036) — One queued hook entry: capture it, list it as unattributed, or drop it.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]] — imports `AGENTS`, `PreparedCapture`, `capture_commit`, `capture_working_tree`, `discover_captures`, `enroll_repo`, `estimate_tokens`, `find_repo`, `sweep`; statically calls `capture_commit`, `capture_working_tree`, `discover_captures`, `enroll_repo`, `estimate_tokens`, `find_repo`, `sweep`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `auto_sweep`; statically calls `auto_sweep`
- [[Reference/Modules/learnloop/projects/ai_runtime|learnloop.projects.ai_runtime]] — imports `estimate_tokens`; statically calls `estimate_tokens`
- [[Reference/Modules/learnloop/projects/probes|learnloop.projects.probes]] — imports `BundleIntegrityError`, `estimate_tokens`, `load_bundle`, `parse_hunks`; statically calls `estimate_tokens`, `load_bundle`, `parse_hunks`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `auto_sweep`; statically calls `auto_sweep`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `FrozenClock`, `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`, `load_config`; calls `load_config`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] — imports `asset_hash`; calls `asset_hash`
- [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] — imports `canonical_source_raw_path`, `store_original_bytes`; calls `canonical_source_raw_path`, `store_original_bytes`
- [[Reference/Modules/learnloop/projects/experiment_store|learnloop.projects.experiment_store]] — imports `ProjectStore`, `pending_path`, `store_path`; calls `pending_path`, `store_path`
- [[Reference/Modules/learnloop/projects/git|learnloop.projects.git]] — imports `GitError`, `empty_tree_sha`, `git_text`, `head_sha`, `patch_id`, `repo_toplevel`, `run_git`; calls `GitError`, `empty_tree_sha`, `git_text`, `head_sha`, `patch_id`, `repo_toplevel`, `run_git`
- [[Reference/Modules/learnloop/projects/redaction|learnloop.projects.redaction]] — imports `PathRules`, `RedactionCounter`, `SECRET_PATTERN_VERSION`, `load_path_rules`, `redact_diff`, `redact_lines`, `redact_text`; calls `RedactionCounter`, `load_path_rules`, `redact_diff`, `redact_lines`, `redact_text`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `json`, `logging`, `math`, `pathlib`, `re`, `secrets`, `typing`, `urllib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]], [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]], [[Reference/Modules/learnloop/projects/ai_runtime|learnloop.projects.ai_runtime]], [[Reference/Modules/learnloop/projects/probes|learnloop.projects.probes]], [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_project_atomicity.py](../../../../../../tests/test_project_atomicity.py) — direct import
- [tests/test_project_blindness.py](../../../../../../tests/test_project_blindness.py) — direct import
  - `test_rendered_prompts_carry_no_provenance_declaration_or_closed_book_origin`
- [tests/test_project_capture.py](../../../../../../tests/test_project_capture.py) — direct import
  - `test_a_diff_with_nothing_probeable_is_still_excluded`
  - `test_a_pending_entry_survives_a_sweep_while_its_repo_is_unavailable`
  - `test_a_single_repo_sweep_keeps_other_repos_pending_entries`
  - `test_backfill_window_captures_recent_agent_commits`
  - `test_budget_truncation_is_honest`
  - `test_context_extends_to_the_enclosing_scope_within_budget`
  - `test_enroll_rejects_a_non_repo`
  - `test_generated_with_claude_code_body_marker_counts_as_agent`
  - `test_history_beyond_the_scan_limit_is_reported_not_silently_skipped`
  - `test_merge_commits_are_not_captured`
  - `test_pending_list_captures_agent_commits_outside_the_branch_window`
  - `test_pending_list_feeds_trailerless_commits_to_the_unattributed_list`
  - `test_renames_are_captured_with_their_old_path`
  - `test_scope_range_finds_the_enclosing_function`
  - `test_small_behavioural_changes_are_probed`
  - `test_strip_agent_trailers_removes_attribution_only`
  - `test_sweep_captures_agent_trailer_commits_once`
  - `test_sweep_ignores_human_commits_and_commits_before_the_window`
  - `test_the_sweep_pages_through_history_beyond_one_git_log_page`
  - `test_trailer_detection`
  - `test_untracked_files_need_the_flag_and_respect_gitignore`
  - `test_working_tree_capture_is_pre_commit_and_deduplicated`
- [tests/test_project_experiment_store.py](../../../../../../tests/test_project_experiment_store.py) — direct import
  - `test_replay_and_rebuild_make_no_git_model_or_subprocess_calls`
- [tests/test_project_hooks.py](../../../../../../tests/test_project_hooks.py) — direct import
  - `test_auto_sweep_is_throttled_at_plan_build`
  - `test_auto_sweep_never_raises`
  - `test_auto_sweep_survives_a_locked_store`
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

- Make changes here when the responsibility remains capture within learnloop.projects; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/projects/capture.py](../../../../../../src/learnloop/projects/capture.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
