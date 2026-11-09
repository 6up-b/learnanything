---
title: "learnloop.cli.probability_arms"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/probability_arms.py"
source_paths:
  - "src/learnloop/cli/probability_arms.py"
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
  - "learnloop.cli.probability_arms module"
  - "src/learnloop/cli/probability_arms.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.probability_arms`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.probability_arms` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: CLI adapter for the ``llm_probability`` V1-V3 arms and the judge routes.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/probability_arms.py](../../../../../../src/learnloop/cli/probability_arms.py) |
| Source lines | 439 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `load_machine_environment(vault_root: Path) -> None` ([source](../../../../../../src/learnloop/cli/probability_arms.py), line 40) — Load keys the way the app does: the vault .env, then settings.env.
- `resolve_route(loaded, judge: str, *, price_per_million: float | None, output_tokens: int | None=None, task: str | None=None) -> JudgeRoute` ([source](../../../../../../src/learnloop/cli/probability_arms.py), line 58) — The configured route for a judge, without credentials or a client.
- `prepare_or_load_probability_arms(loaded, inputs: dict[str, Any], *, cache_dir: Path, selection: Sequence[tuple[str, str]], prepare: bool=False, dry_run: bool=False, caps: SpendCaps, price_per_million: float | None, output_tokens: int | None=None, cancelled=lambda: False, routes: dict[str, JudgeRoute] | None=None) -> tuple[list[Any], dict[str, Any]]` ([source](../../../../../../src/learnloop/cli/probability_arms.py), line 137) — Return ``(arms, aggregate report)``; arms is empty unless complete.
- `pairwise_comparisons(selection: Sequence[tuple[str, str]]) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/cli/probability_arms.py), line 233) — V2 vs V1, V3 vs V2, V3 vs V1 within each judge; LLM vs Decider per variant.
- `judge_readiness(loaded, *, probe: bool=False, http=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/probability_arms.py), line 261) — Route resolution, key presence, disclosures; ``probe`` adds a free GET.
- `live_decider_estimate(loaded, *, task: str='llm_probability_decider') -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/probability_arms.py), line 359) — ``--live-decider --dry-run``: the call's estimate, with nothing sent.
- `live_decider_check(loaded, *, task: str='llm_probability_decider', http=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/probability_arms.py), line 384) — One minimal, spend-capped Decider call that carries no learner data.

### Module constants

- `ROUTE_TASKS` ([src/learnloop/cli/probability_arms.py](../../../../../../src/learnloop/cli/probability_arms.py), line 35)
- `ROUTER_TASKS` ([src/learnloop/cli/probability_arms.py](../../../../../../src/learnloop/cli/probability_arms.py), line 36)
- `METERED_LLM_TYPES` ([src/learnloop/cli/probability_arms.py](../../../../../../src/learnloop/cli/probability_arms.py), line 37)
- `READINESS_QUESTION_SET` ([src/learnloop/cli/probability_arms.py](../../../../../../src/learnloop/cli/probability_arms.py), line 258)
- `READINESS_STATE` ([src/learnloop/cli/probability_arms.py](../../../../../../src/learnloop/cli/probability_arms.py), line 324)
- `READINESS_CAPS` ([src/learnloop/cli/probability_arms.py](../../../../../../src/learnloop/cli/probability_arms.py), line 326)

### Explicit exports

`__all__` declares:

- `ROUTE_TASKS`
- `ROUTER_TASKS`
- `load_machine_environment`
- `pairwise_comparisons`
- `prepare_or_load_probability_arms`
- `judge_readiness`
- `live_decider_check`
- `live_decider_estimate`
- `resolve_route`

## Internal implementation anchors

- `_endpoint_hash(value: str | None) -> str` ([source](../../../../../../src/learnloop/cli/probability_arms.py), line 53)
- `_decider_client(loaded, task: str, name: str)` ([source](../../../../../../src/learnloop/cli/probability_arms.py), line 115)
- `_llm_client(loaded, task: str, name: str, subscription: bool)` ([source](../../../../../../src/learnloop/cli/probability_arms.py), line 123)
- `_total_estimate(judge_reports) -> dict[str, Any]` ([source](../../../../../../src/learnloop/cli/probability_arms.py), line 218)
- `_consumer_status(config, consumer: str, *, field_on: bool) -> str` ([source](../../../../../../src/learnloop/cli/probability_arms.py), line 299) — Whether the route's consumer sends anything now (review F5: the Tier-1 routes are live).
- `_readiness_request(loaded, task: str)` ([source](../../../../../../src/learnloop/cli/probability_arms.py), line 330) — The readiness call fully resolved without credentials, a client or a write.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]] — imports `judge_readiness`, `live_decider_check`, `live_decider_estimate`; statically calls `judge_readiness`, `live_decider_check`, `live_decider_estimate`
- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `pairwise_comparisons`, `prepare_or_load_probability_arms`; statically calls `pairwise_comparisons`, `prepare_or_load_probability_arms`
- [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]] — imports `prepare_or_load_probability_arms`; statically calls `prepare_or_load_probability_arms`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `feature_audit_enabled`, `outside_forecasters`; calls `feature_audit_enabled`, `outside_forecasters`
- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `ChoiceQuestion`, `NoulQuestion`, `ScoreQuestion`, `request_body`; calls `ChoiceQuestion`, `NoulQuestion`, `ScoreQuestion`, `request_body`
- [[Reference/Modules/learnloop/ai/disclosures|learnloop.ai.disclosures]] — imports `JUDGE_ROUTES`, `judge_route_disclosures`; calls `judge_route_disclosures`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `call_labels`, `observe_model_calls`; calls `call_labels`, `observe_model_calls`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `output_budget`; calls `output_budget`
- [[Reference/Modules/learnloop/ai/providers/decider|learnloop.ai.providers.decider]] — imports `DeciderProviderClient`, `estimate_input_tokens`, `probe_decider_endpoint`, `resolved_decider_settings`; calls `DeciderProviderClient`, `estimate_input_tokens`, `probe_decider_endpoint`, `resolved_decider_settings`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`, `ready_client_for_task`, `route_profile_mismatch`, `runtime_for_provider`; calls `provider_for_task`, `ready_client_for_task`, `route_profile_mismatch`, `runtime_for_provider`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`; calls `SpendBudget`, `SpendCaps`, `SpendEstimate`, `is_subscription_transport`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `BOUNDED_STRUCTURED_COMPLETION`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `global_settings_path`, `load_dotenv`; calls `global_settings_path`, `load_dotenv`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `CONTENT_TASKS`, `SERVING_TASKS`, `enabled`; calls `enabled`
- [[Reference/Modules/learnloop/field/probability_arms|learnloop.field.probability_arms]] — imports `JUDGES`, `arm_name`; calls `arm_name`
- [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]] — imports `DECIDER_OUTPUT_TOKENS`, `JudgeRoute`, `check_cache_location`, `committed_judgments`, `load_arms`, `prediction_points`, `prepare_judge`, `render_plan`; calls `JudgeRoute`, `check_cache_location`, `committed_judgments`, `load_arms`, `prediction_points`, `prepare_judge`, `render_plan`
- [[Reference/Modules/learnloop/field/probability_states|learnloop.field.probability_states]] — imports `StateRenderer`; calls `StateRenderer`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `hashlib`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]], [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]], [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probability_prep.py](../../../../../../tests/test_probability_prep.py) — direct import
  - `test_decider_end_to_end_through_the_fake_endpoint`
  - `test_dry_run_and_caps_refuse_before_any_client_call_or_write`
  - `test_harness_routes_follow_the_vault_config_not_the_env_override`
  - `test_llm_judge_metered_route_is_isolated_bounded_and_ledgered`
  - `test_switches_and_cache_location_are_enforced`
- [tests/test_success_head_cli.py](../../../../../../tests/test_success_head_cli.py) — direct import

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/probability_arms.py](../../../../../../src/learnloop/cli/probability_arms.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
