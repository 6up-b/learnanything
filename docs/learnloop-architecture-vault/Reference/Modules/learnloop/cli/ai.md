---
title: "learnloop.cli.ai"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/ai.py"
source_paths:
  - "src/learnloop/cli/ai.py"
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
  - "learnloop.cli.ai module"
  - "src/learnloop/cli/ai.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.ai`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.ai` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop ai`: provider sign-in, status, a latency check and a side-by-side comparison.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/ai.py](../../../../../../src/learnloop/cli/ai.py) |
| Source lines | 602 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `ai_signin(provider: Annotated[str, typer.Argument(help='The provider to sign in to: chatgpt.')], new_account: Annotated[bool, typer.Option('--new-account', help='Register a new client (switch ChatGPT accounts).')]=False, consent: Annotated[bool, typer.Option('--consent', help='Ask for consent again, e.g. to enable ChatGPT plan usage after a decline.')]=False, no_browser: Annotated[bool, typer.Option('--no-browser', help='Print the sign-in URL instead of opening a browser.')]=False, port: Annotated[int | None, typer.Option('--port', min=0, max=65535, help='Loopback callback port (default 1455, else any free port).')]=None, timeout: Annotated[float, typer.Option('--timeout', min=10, max=3600, help='Seconds to wait for the browser.')]=300.0, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/ai.py), line 57) — Continue with ChatGPT: sign in once per machine so `chatgpt_plan` profiles can use your plan.
- `ai_signout(provider: Annotated[str, typer.Argument(help='chatgpt')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/ai.py), line 125) — Sign out: revoke the renewable session, then clear the saved tokens on this machine.
- `ai_resume(provider: Annotated[str, typer.Argument(help='chatgpt')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/ai.py), line 144) — End a usage-limit pause now, so the next request tries the ChatGPT plan again.
- `ai_status(provider: Annotated[str, typer.Argument(help='chatgpt')], vault: Annotated[Path | None, typer.Option('--vault', help="Also list this vault's chatgpt_plan profiles and the routes that use them.")]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/ai.py), line 163) — This machine's ChatGPT sign-in and plan state, from local files only (no network).
- `ai_models(provider: Annotated[str, typer.Argument(help='chatgpt')], vault: Annotated[Path | None, typer.Option('--vault', help="Use a profile's base URL from this vault (with --profile).")]=None, profile: Annotated[str | None, typer.Option('--profile', help='A chatgpt_plan profile in --vault.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/ai.py), line 202) — List the models your ChatGPT account offers (one unbilled request with your sign-in).
- `ai_latency(vault: Annotated[Path, typer.Option('--vault', help='Vault whose provider profiles to compare (receipts land here; use a fixtures-local copy).')], provider: Annotated[list[str], typer.Option('--provider', help='A provider profile to time; repeatable (e.g. chatgpt and openrouter; a Codex profile needs ai.agent_harness_opt_in).')], runs: Annotated[int, typer.Option('--runs', min=1, max=20, help='Calls per provider.')]=3, timeout: Annotated[float, typer.Option('--timeout', min=5, max=600, help='Seconds per call.')]=120.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='USD per million tokens; required for a metered profile.')]=None, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0, help='A reservation cap for every metered profile together: each call reserves its prompt plus its full output budget (never what is billed).')]=0.5, dry_run: Annotated[bool, typer.Option('--dry-run', help='Show the plan; build no client and send nothing.')]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/ai.py), line 239) — Time a tiny structured call through each provider (wall clock per call).
- `ai_compare(vault: Annotated[Path, typer.Option('--vault', help="A backup-API copy of a vault (receipts land here); with --copy-from, the new copy's directory.")], profiles: Annotated[list[str], typer.Option('--profiles', help='Subscription profiles to compare, comma-separated or repeated (e.g. chatgpt,chatgpt_luna; a Codex profile needs ai.agent_harness_opt_in).')], copy_from: Annotated[Path | None, typer.Option('--copy-from', help='Copy this vault to --vault first (backup API; also with --dry-run); the original is only read.')]=None, attempts: Annotated[int, typer.Option('--attempts', min=0, max=20, help='Attempts to blind-grade per profile (latest non-pass and pass first).')]=3, attempt_id: Annotated[list[str] | None, typer.Option('--attempt', help='An attempt to grade (repeatable; replaces the automatic choice).')]=None, diagnosis_attempt: Annotated[str | None, typer.Option('--diagnosis-attempt', help='The attempt to diagnose (default: the latest non-pass that needs one).')]=None, diagnosis_mode: Annotated[str, typer.Option('--diagnosis-mode', help='History mode of the diagnosis: snapshot (default), full or exact.')]='snapshot', no_diagnosis: Annotated[bool, typer.Option('--no-diagnosis', help='Skip the diagnosis.')]=False, no_generation: Annotated[bool, typer.Option('--no-generation', help='Skip the structured generation.')]=False, timeout: Annotated[int, typer.Option('--timeout', min=30, max=3600, help="Seconds per call (a workspace turn's rounds included).")]=900, output: Annotated[Path, typer.Option('--output', help='Directory for the JSON report (outside the vault).')]=Path('fixtures-local/reports/ai-compare'), dry_run: Annotated[bool, typer.Option('--dry-run', help='Show the plan; build no client and send nothing.')]=False, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/ai.py), line 440) — Run the same grading, diagnosis and generation on each profile and compare them.

### Module constants

- `PROVIDERS` ([src/learnloop/cli/ai.py](../../../../../../src/learnloop/cli/ai.py), line 28)
- `LATENCY_INPUT_TOKENS` ([src/learnloop/cli/ai.py](../../../../../../src/learnloop/cli/ai.py), line 33)
- `WELCOME` ([src/learnloop/cli/ai.py](../../../../../../src/learnloop/cli/ai.py), line 49)

### Explicit exports

`__all__` declares:

- `ai_app`

## Internal implementation anchors

- `_require_chatgpt(provider: str) -> None` ([source](../../../../../../src/learnloop/cli/ai.py), line 36)
- `_fail(message: str, *, json_output: bool, code: str='error', **extra: Any) -> None` ([source](../../../../../../src/learnloop/cli/ai.py), line 41)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `ai_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/chatgpt_plan/oauth|learnloop.ai.chatgpt_plan.oauth]] — imports `SignInError`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/routes|learnloop.ai.chatgpt_plan.routes]] — imports `plan_profiles`; calls `plan_profiles`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/session|learnloop.ai.chatgpt_plan.session]] — imports `PlanSession`; calls `PlanSession`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/store|learnloop.ai.chatgpt_plan.store]] — imports `StoreError`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIOutputTruncated`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `generation_limit`, `single_request`; calls `generation_limit`, `single_request`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `output_budget`, `record_truncation`; calls `output_budget`, `record_truncation`
- [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] — imports `list_plan_models`; calls `list_plan_models`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `client_for_provider`, `route_profile_mismatch`, `runtime_for_provider`; calls `client_for_provider`, `route_profile_mismatch`, `runtime_for_provider`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`; calls `SpendBudget`, `SpendCaps`, `SpendEstimate`, `is_subscription_transport`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `consume_client_usage`; calls `consume_client_usage`
- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `CompareRefused`, `CompareRequest`, `copy_vault`, `database_location_reason`, `plan_compare`, `run_compare`, `tracked_database_reason`; calls `CompareRefused`, `CompareRequest`, `copy_vault`, `database_location_reason`, `plan_compare`, `run_compare`, `tracked_database_reason`
- [[Reference/Modules/learnloop/cli/receipts|learnloop.cli.receipts]] — imports `bind_command_vault`; calls `bind_command_vault`
- [[Reference/Modules/learnloop/cli/render|learnloop.cli.render]] — imports `_dump`; calls `_dump`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `CHATGPT_PLAN_API_BASE_URL`, `CHATGPT_PLAN_PROFILE_TYPE`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `datetime`, `decimal`, `json`, `pathlib`, `statistics`, `time`, `typing`, `webbrowser`
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

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_cli_ingest.py](../../../../../../tests/test_cli_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_facet_identity_ingest.py](../../../../../../tests/test_facet_identity_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_graph_nomination_ingest.py](../../../../../../tests/test_graph_nomination_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_teach_back_generation.py](../../../../../../tests/test_teach_back_generation.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/ai.py](../../../../../../src/learnloop/cli/ai.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
