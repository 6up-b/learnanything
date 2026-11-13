---
title: "learnloop.cli.project"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/project.py"
source_paths:
  - "src/learnloop/cli/project.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Inspect Persistent State"
aliases:
  - "learnloop.cli.project module"
  - "src/learnloop/cli/project.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.project`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.project` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop project`: delayed questions on agent-written code (project understanding M1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/project.py](../../../../../../src/learnloop/cli/project.py) |
| Source lines | 889 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `project_enroll(repo: Annotated[Path, typer.Argument(help='A git work tree whose agent-written commits you want questions about.')], vault: VaultOption=None, since_days: Annotated[int | None, typer.Option('--since-days', min=0, help='Also capture agent commits from this many days back (default: project.enroll_backfill_days).')]=None, context_scope: Annotated[str, typer.Option('--context-scope', help="'diff' (default) or 'repo'; repo scope needs READ_ONLY_WORKSPACE, which is not built yet, so diff scope is used.")]='diff', hook: Annotated[bool, typer.Option('--install-hook', help='Also install the append-only post-commit hook.')]=False, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 258) — Enroll a repo: from now on its agent-trailer commits are captured automatically.
- `project_unenroll(repo: Annotated[str, typer.Argument(help='Repo path or id.')], vault: VaultOption=None, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 305) — Stop capturing a repo.
- `project_install_hook(repo: Annotated[str, typer.Argument(help='Enrolled repo path or id.')], vault: VaultOption=None, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 326) — Install the append-only post-commit hook (it never blocks a commit).
- `project_uninstall_hook(repo: Annotated[str, typer.Argument(help='Enrolled repo path or id.')], vault: VaultOption=None, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 347) — Remove LearnLoop's block from the repo's post-commit hook.
- `project_sweep(vault: VaultOption=None, repo: Annotated[str | None, typer.Option('--repo', help='Only this enrolled repo (path or id).')]=None, capture_only: Annotated[bool, typer.Option('--capture-only', help='Capture without generating questions (no model calls).')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Estimate generation for captured diffs and for the commits a real sweep would capture; no model calls or writes.')]=False, max_diffs: Annotated[int, typer.Option('--max-diffs', min=0, help='Generate for at most this many diffs, oldest first.')]=30, retry_failed: Annotated[bool, typer.Option('--retry-failed', help='Also retry diffs whose question generation failed (finished stages are kept, not re-paid).')]=False, max_candidates: MaxCandidates=300, max_calls: MaxCalls=200, max_retries: MaxRetries=4, max_tokens: MaxTokens=2000000, max_cost_usd: MaxCost=2.0, price_per_million: PriceOption=None, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 371) — Capture new agent-trailer commits, then generate their questions.
- `project_accept(repo: Annotated[Path, typer.Option('--repo', help="Enrolled repo (default: the cwd's repo).")]=Path('.'), commit: Annotated[list[str] | None, typer.Option('--commit', help='Capture this commit (repeatable) instead of the working tree.')]=None, agent: Annotated[str | None, typer.Option('--agent', help='claude_code, codex, other or unknown.')]=None, include_untracked: Annotated[bool, typer.Option('--include-untracked', help='Include untracked files (.gitignore respected).')]=False, vault: VaultOption=None, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 440) — Mark agent work that has no trailer: the working tree, or `--commit <sha>`.
- `project_provenance(diff_id: Annotated[str, typer.Argument(help='A captured diff id (see `status --diffs`).')], accept_style: Annotated[str | None, typer.Option('--accept-style', help='per_hunk, all_at_once or unknown.')]=None, usage: Annotated[str | None, typer.Option('--usage', help='i_designed_it_typed, we_iterated or it_designed.')]=None, vault: VaultOption=None, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 486) — Optional self-report of how the code was produced.
- `project_status(vault: VaultOption=None, disclosure: Annotated[bool, typer.Option('--disclosure', help='What was sent to models, per repo.')]=False, diffs: Annotated[bool, typer.Option('--diffs', help='List captured diffs (no question text).')]=False, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 520) — Captured and pending counts.
- `project_report(vault: VaultOption=None, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 573) — The M1 probe report: validity, value, capture coverage, accuracy by provenance.
- `project_probes(vault: VaultOption=None, repo: Annotated[str | None, typer.Option('--repo', help='Only questions about this repo.')]=None, limit: Annotated[int, typer.Option('--limit', min=1, help='Questions this session.')]=10, list_only: Annotated[bool, typer.Option('--list', help='Print due questions and their ids; answer with `project answer`.')]=False, no_generate: Annotated[bool, typer.Option('--no-generate', help='Do not generate questions for due diffs that have none.')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Estimate generation and grading; serve nothing.')]=False, max_candidates: MaxCandidates=300, max_calls: MaxCalls=200, max_retries: MaxRetries=4, max_tokens: MaxTokens=2000000, max_cost_usd: MaxCost=2.0, price_per_million: PriceOption=None, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 650) — Answer due questions (unassisted unless you say otherwise).
- `project_answer(probe_id: Annotated[str, typer.Argument(help='A due probe id (see `probes --list`).')], text: Annotated[str | None, typer.Option('--text', help='Your answer, from memory.')]=None, dont_know: Annotated[bool, typer.Option('--dont-know')]=False, unfair: Annotated[bool, typer.Option('--unfair', help='The question is unfair or ambiguous.')]=False, skip: Annotated[bool, typer.Option('--skip')]=False, looked: Annotated[bool, typer.Option('--looked', help='You looked at the code.')]=False, used_ai: Annotated[bool, typer.Option('--used-ai', help='You used AI.')]=False, no_grade: Annotated[bool, typer.Option('--no-grade', help='Save now; grade later with `project grade`.')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Estimate grading; record nothing.')]=False, max_calls: MaxCalls=5, max_retries: MaxRetries=2, max_tokens: MaxTokens=50000, max_cost_usd: MaxCost=0.25, price_per_million: PriceOption=None, vault: VaultOption=None, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 784) — Answer one due question non-interactively.
- `project_grade(vault: VaultOption=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Estimate; make no calls.')]=False, retry_failed: Annotated[bool, typer.Option('--retry-failed', help='Also retry answers whose grading failed (attempts start again; answers and receipts are kept).')]=False, max_calls: MaxCalls=50, max_retries: MaxRetries=4, max_tokens: MaxTokens=500000, max_cost_usd: MaxCost=1.0, price_per_million: PriceOption=None, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 838) — Grade saved answers whose grading is still pending (blind grader); `--retry-failed` retries failed ones.
- `project_contest(response_id: Annotated[str, typer.Argument(help='The graded response id.')], score: Annotated[float, typer.Option('--score', min=0.0, max=1.0, help='Your adjudicated score (0-1).')], note: Annotated[str, typer.Option('--note', help='Why the grade was wrong.')]='', vault: VaultOption=None, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 866) — Contest a grade: your adjudication becomes the outcome of record; the grade is kept.

### Module constants

- `GRADING_BUSY` ([src/learnloop/cli/project.py](../../../../../../src/learnloop/cli/project.py), line 85)
- `_LOOKED` ([src/learnloop/cli/project.py](../../../../../../src/learnloop/cli/project.py), line 593)
- `_USED_AI` ([src/learnloop/cli/project.py](../../../../../../src/learnloop/cli/project.py), line 594)
- `_HELP_LINE` ([src/learnloop/cli/project.py](../../../../../../src/learnloop/cli/project.py), line 595)

### Explicit exports

`__all__` declares:

- `project_app`

## Internal implementation anchors

- `_clock() -> Clock` ([source](../../../../../../src/learnloop/cli/project.py), line 88)
- `_vault_root(vault: Path | None) -> Path` ([source](../../../../../../src/learnloop/cli/project.py), line 92)
- `_config(root: Path) -> LearnLoopConfig` ([source](../../../../../../src/learnloop/cli/project.py), line 101)
- `_store(root: Path, *, read_only: bool=False) -> ProjectStore` ([source](../../../../../../src/learnloop/cli/project.py), line 105) — The vault's project store; a dry run opens it ``read_only`` (no write, no upgrade).
- `_paid(store: ProjectStore, config: LearnLoopConfig, caps, price_per_million: float | None, *, run_id: str | None=None, cancelled=None) -> PaidCalls` ([source](../../../../../../src/learnloop/cli/project.py), line 114)
- `_routes(root: Path, config: LearnLoopConfig, store: ProjectStore, roles: tuple[str, ...])` ([source](../../../../../../src/learnloop/cli/project.py), line 129) — Project routes with the vault and every enrolled repo masked from agents.
- `_emit(payload: dict[str, Any], json_output: bool, text: str | None=None) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 135)
- `_fail(message: str, json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 142)
- `_generate(root: Path, config: LearnLoopConfig, store: ProjectStore, diffs: list[dict[str, Any]], *, paid: PaidCalls, dry_run: bool, clock: Clock, prospective: list[PreparedCapture]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/project.py), line 147) — Generate for ``diffs`` under the command's one budget (``paid``).
- `_serving_grade_plan(questions: int) -> list[PlannedCall]` ([source](../../../../../../src/learnloop/cli/project.py), line 190) — One grading call per question an answering session may serve.
- `_grading_plan(store: ProjectStore, responses: list[dict[str, Any]]) -> list[PlannedCall]` ([source](../../../../../../src/learnloop/cli/project.py), line 196)
- `_grade(root: Path, config: LearnLoopConfig, store: ProjectStore, response_ids: list[str] | None, *, caps, price_per_million: float | None, clock: Clock, dry_run: bool=False, retry_failed: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/project.py), line 207)
- `_read_answer() -> tuple[str | None, str, str]` ([source](../../../../../../src/learnloop/cli/project.py), line 602) — (answer text, kind or 'quit', declaration) from stdin.
- `_render_reveal(info: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/cli/project.py), line 633)
- `_serve_probes(root: Path, config: LearnLoopConfig, store: ProjectStore, paid: PaidCalls, *, clock: Clock, repo_id: str | None, limit: int, list_only: bool, generate: bool, dry_run: bool, json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/project.py), line 696)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `project_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `_cancellation`; calls `_cancellation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `utc_now_iso`; calls `SystemClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`, `load_config`; calls `load_config`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/projects/ai_runtime|learnloop.projects.ai_runtime]] — imports `PaidCalls`, `PlannedCall`, `caps_from_options`, `describe_routes`, `project_routes`; calls `PaidCalls`, `PlannedCall`, `caps_from_options`, `describe_routes`, `project_routes`
- [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]] — imports `AGENTS`, `PreparedCapture`, `capture_commit`, `capture_working_tree`, `discover_captures`, `enroll_repo`, `estimate_tokens`, `find_repo`, `sweep`; calls `capture_commit`, `capture_working_tree`, `discover_captures`, `enroll_repo`, `estimate_tokens`, `find_repo`, `sweep`
- [[Reference/Modules/learnloop/projects/experiment_store|learnloop.projects.experiment_store]] — imports `ProjectStore`
- [[Reference/Modules/learnloop/projects/git|learnloop.projects.git]] — imports `GitError`, `repo_toplevel`; calls `repo_toplevel`
- [[Reference/Modules/learnloop/projects/hooks|learnloop.projects.hooks]] — imports `HookError`, `install_hook`, `uninstall_hook`; calls `install_hook`, `uninstall_hook`
- [[Reference/Modules/learnloop/projects/probes|learnloop.projects.probes]] — imports `GRADING_ITEM_TOKENS_ESTIMATE`, `PROMPT_OVERHEAD_TOKENS`, `ProbeStateError`, `SealedProbeError`, `contest_grade`, `diffs_awaiting_generation`, `due_probes`, `generate_probes`, `grade_responses`, `grading_output_tokens`, `open_probe`, `plan_for_bundle`, `plan_generation`, `record_response`, `reveal`; calls `contest_grade`, `diffs_awaiting_generation`, `due_probes`, `generate_probes`, `grade_responses`, `grading_output_tokens`, `open_probe`, `plan_for_bundle`, `plan_generation`, `record_response`, `reveal`
- [[Reference/Modules/learnloop/projects/report|learnloop.projects.report]] — imports `build_report`, `build_status`, `render_report`; calls `build_report`, `build_status`, `render_report`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `refuse_vault_below_floor`; calls `refuse_vault_below_floor`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `find_vault_root`; calls `find_vault_root`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `pathlib`, `re`, `sys`, `typing`
- Third party: `typer`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_project_cli.py](../../../../../../tests/test_project_cli.py) — direct import
  - `test_declaration_tokens_are_whole_words`
- [tests/test_project_experiment_store.py](../../../../../../tests/test_project_experiment_store.py) — direct import
  - `test_m1_never_writes_state_sqlite`
  - `test_replay_and_rebuild_make_no_git_model_or_subprocess_calls`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/project.py](../../../../../../src/learnloop/cli/project.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
