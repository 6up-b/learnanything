---
title: "learnloop.cli.ai_compare"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/ai_compare.py"
source_paths:
  - "src/learnloop/cli/ai_compare.py"
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
  - "learnloop.cli.ai_compare module"
  - "src/learnloop/cli/ai_compare.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.ai_compare`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.ai_compare` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop ai compare`: the same real work on several subscription profiles, side by side.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py) |
| Source lines | 1204 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class CompareRefused(ValueError)` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 153) — The comparison cannot run as asked; ``code`` names why (for ``--json``).
  - `__init__(self, message: str, *, code: str) -> None` (line 156; internal)
- `class CompareRequest` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 162)
- `class Targets` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 176)
  - `as_dict(self) -> dict[str, Any]` (line 182; public)
- `database_location_reason(vault: LoadedVault) -> str | None` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 194) — Why this vault's database must not be compared on (it lies outside the vault), or None.
- `tracked_database_reason(vault: LoadedVault, *, fresh_copy: bool=False) -> str | None` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 212) — Why this vault must not be compared on, or None.
- `copy_vault(source: Path, destination: Path) -> list[Path]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 304) — A backup-API copy of ``source`` at ``destination`` (which must not exist yet).
- `check_profiles(vault: LoadedVault, request: CompareRequest) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 357) — Each named profile's identity and readiness; refuses a profile that cannot run here.
- `select_targets(vault: LoadedVault, repository: Any, request: CompareRequest, *, store: Any=None) -> Targets` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 397) — The attempts to grade, the attempt to diagnose and the item to generate from.
- `plan_allowance(profile_type: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 820) — The ChatGPT plan's local allowance state (no network); None for other types.
- `plan_compare(vault: LoadedVault, repository: Any, request: CompareRequest) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 914) — What a run would do: profiles, targets, calls and their estimates; builds no client and sends nothing.
- `run_compare(vault: LoadedVault, repository: Any, request: CompareRequest, *, client_factory: Callable[[str], Any] | None=None, progress: Callable[[str], None] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 959) — Run the plan on every ready profile; returns the report (ids, numbers and local text only).

### Module constants

- `COMPARE_VERSION` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 135)
- `DEFAULT_GRADING_ATTEMPTS` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 136)
- `DIAGNOSIS_MODES` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 137)
- `_BYTES_PER_TOKEN` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 139)
- `_SKIPPED_ATTEMPT_TYPES` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 141)
- `_ROUTES` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 143)
- `GRADING_TASK` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 146)
- `DIAGNOSIS_TASK` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 147)
- `GENERATION_TASK` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 148)
- `PROFILE_KIND` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 150)
- `_IDENTIFIER` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 540)
- `_HINTS` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 629)
- `_REMEDIES` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 645)
- `_DEFAULT_HINT` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 651)
- `_ALLOWANCE_ERRORS` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 817)
- `_ESTIMATE_BASIS` ([src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py), line 901)

### Explicit exports

`__all__` declares:

- `COMPARE_VERSION`
- `CompareRefused`
- `CompareRequest`
- `DEFAULT_GRADING_ATTEMPTS`
- `DIAGNOSIS_MODES`
- `DIAGNOSIS_TASK`
- `GENERATION_TASK`
- `GRADING_TASK`
- `PROFILE_KIND`
- `Targets`
- `check_profiles`
- `copy_vault`
- `database_location_reason`
- `plan_allowance`
- `plan_compare`
- `run_compare`
- `select_targets`
- `tracked_database_reason`

## Internal implementation anchors

- `_inside(path: Path, root: Path) -> bool` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 190)
- `_configured_database(root: Path, *, flag: str) -> str` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 263) — The vault's ``storage.sqlite_path`` as written (read without loading the environment).
- `_relocate_database(destination: Path, relative: Path) -> None` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 273) — Point the copy's ``storage.sqlite_path`` at its own database (relative to the copy).
- `_opened_database(root: Path, configured: str) -> Path` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 284) — The database file ``configured`` (relative to ``root``) opens, as the operating system resolves it.
- `_record_for(vault: LoadedVault, repository: Any, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 389)
- `_tokens(text: str) -> int` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 474)
- `_grading_contract(vault: LoadedVault, repository: Any, item: PracticeItem, attempt_id: str) -> tuple[Rubric, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 478) — The rubric and assessment contract production regrading reads for this answer (Codex review F4).
- `_grading_context(vault: LoadedVault, repository: Any, attempt: Any) -> tuple[PracticeItem, Rubric, BlindGradingContext]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 495)
- `_diagnosis_inputs(vault: LoadedVault, repository: Any, store: Any, attempt_id: str, mode: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 505) — The diagnosis's inline prompt size and, in snapshot mode, its export's (no model call).
- `_generation_inputs(vault: LoadedVault, item_id: str) -> tuple[Any, list[dict[str, Any]], str]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 528)
- `_identifier(value: Any) -> str | None` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 543)
- `class _Meter` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 547) — The model calls one comparison call made, from the receipts' own events.
- `_measured() -> Iterator[_Meter]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 616)
- `_error_class(exc: BaseException) -> str` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 622)
- `_failure_record(error: str | None, exc: BaseException | None, meter: _Meter, *, provider: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 655) — A failure as codes and ids plus a local explanation, never the provider's prose.
- `_grade(vault: LoadedVault, repository: Any, client: Any, attempt: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 680)
- `_diagnose(vault: LoadedVault, repository: Any, client: Any, attempt_id: str, *, store: Any, mode: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 708)
- `_generate(vault: LoadedVault, client: Any, item_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 748)
- `class _FailureRecorder` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 772) — The profile's client, forwarding everything, that remembers its last failure.
- `_timed(work: Callable[[], dict[str, Any]], recorder: _FailureRecorder | None=None, *, provider: str='') -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 794) — Run one comparison call; an interrupt propagates, any other failure is recorded as codes.
- `_caps(calls: int, tokens: int) -> SpendCaps` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 834) — One profile's caps: the plan's calls (enforced); tokens and dollars estimated only.
- `_planned_inputs(vault: LoadedVault, repository: Any, targets: Targets, request: CompareRequest, store: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 841) — Every planned call's prompt-side size, the same for every profile (no request).
- `_profile_estimate(vault: LoadedVault, profile: Mapping[str, Any], operations: Sequence[Mapping[str, Any]], request: CompareRequest) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 861) — One profile's planned calls with their token estimates, its caps and their check.
- `_append_judgment(repository: Any, payload: Mapping[str, Any], *, provider: str, model: str, run_id: str) -> str` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 943) — One comparison verdict in the vault copy's ledger (the comparison's own task).
- `_calls(row: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 1088)
- `_profile_summary(row: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 1094)
- `_recorded_grade(attempt: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 1115)
- `_grading_agreement(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 1121)
- `_jaccard(one: Sequence[str], other: Sequence[str]) -> float | None` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 1155)
- `_agreement(results: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/cli/ai_compare.py), line 1160)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `CompareRefused`, `CompareRequest`, `copy_vault`, `database_location_reason`, `plan_compare`, `run_compare`, `tracked_database_reason`; statically calls `CompareRefused`, `CompareRequest`, `copy_vault`, `database_location_reason`, `plan_compare`, `run_compare`, `tracked_database_reason`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/chatgpt_plan/session|learnloop.ai.chatgpt_plan.session]] — imports `MANAGE_USAGE_URL`, `PlanSession`; calls `PlanSession`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `annotate_calls`, `content_key`, `generation_limit`, `tee_model_calls`; calls `annotate_calls`, `content_key`, `generation_limit`, `tee_model_calls`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `output_budget`; calls `output_budget`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `client_for_provider`, `is_generation_profile`, `runtime_for_provider`, `serves_read_only_workspace`; calls `client_for_provider`, `is_generation_profile`, `runtime_for_provider`, `serves_read_only_workspace`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`, `subscription_usage_estimate`; calls `SpendBudget`, `SpendCaps`, `SpendEstimate`, `is_subscription_transport`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `attempt_graded_contract`, `regrade_reads_contract`; calls `attempt_graded_contract`, `regrade_reads_contract`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `BlindGradingContext`, `blind_grading_context`, `blind_grading_context_hash`, `blind_grading_prompt`, `blind_prompt_version`, `request_blind_grading_proposal`, `validate_blind_grading_proposal`; calls `blind_grading_context`, `blind_grading_context_hash`, `blind_grading_prompt`, `blind_prompt_version`, `request_blind_grading_proposal`, `validate_blind_grading_proposal`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `GradingValidationError`, `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `load_config`; calls `load_config`
- [[Reference/Modules/learnloop/db/copies|learnloop.db.copies]] — imports `backup_database`, `copy_tree_with_databases`; calls `backup_database`, `copy_tree_with_databases`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `assemble_diagnosis_context`; calls `assemble_diagnosis_context`
- [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]] — imports `diagnosis_prompt`; calls `diagnosis_prompt`
- [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]] — imports `run_diagnosis`; calls `run_diagnosis`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `current_attempt_for`, `joint_grade_record`, `live_history_store`, `needs_diagnosis`, `settings_from_config`; calls `current_attempt_for`, `joint_grade_record`, `live_history_store`, `needs_diagnosis`, `settings_from_config`
- [[Reference/Modules/learnloop/diagnosis/split/snapshot|learnloop.diagnosis.split.snapshot]] — imports `snapshot_workspace`; calls `snapshot_workspace`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `TEACH_BACK_AUTHORING_PROMPT_VERSION`, `teach_back_authoring_prompt`; calls `teach_back_authoring_prompt`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `TeachBackError`, `request_teach_back_authoring`, `teach_back_authoring_context`, `validate_teach_back_authoring`; calls `request_teach_back_authoring`, `teach_back_authoring_context`, `validate_teach_back_authoring`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/working_vault|learnloop.vault.working_vault]] — imports `working_vault_marker_reason`; calls `working_vault_marker_reason`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `itertools`, `json`, `os`, `pathlib`, `re`, `shutil`, `sqlite3`, `statistics`, `subprocess`, `time`, `typing`
- Third party: `tomlkit`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ai_compare.py](../../../../../../tests/test_ai_compare.py) — direct import
  - `test_a_json_repair_carries_the_budget_of_the_request_it_repairs`
  - `test_a_live_vault_moved_out_of_git_is_still_refused_and_its_copy_is_compared`
  - `test_an_unreadable_working_vault_mark_refuses`
  - `test_copy_from_backs_up_a_wal_database_not_named_sqlite`
  - `test_copy_from_backs_up_the_database_a_symlinked_path_opens`
  - `test_each_request_carries_the_output_budget_its_estimate_reports`
  - `test_grading_reads_the_contract_the_answer_was_graded_under`
  - `test_the_meter_counts_only_requests_that_were_sent`
  - `test_the_working_vault_check_fails_closed`
  - `test_without_git_only_a_fresh_copy_is_compared`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/ai_compare.py](../../../../../../src/learnloop/cli/ai_compare.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
