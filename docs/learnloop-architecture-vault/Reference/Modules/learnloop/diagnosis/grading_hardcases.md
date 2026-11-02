---
title: "learnloop.diagnosis.grading_hardcases"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/grading_hardcases.py"
source_paths:
  - "src/learnloop/diagnosis/grading_hardcases.py"
source_commit: "1ef2f14ebf6f15de8b60736f60650017d40712d3"
source_commit_timestamp: "2026-10-15T12:39:41-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.diagnosis.grading_hardcases module"
  - "src/learnloop/diagnosis/grading_hardcases.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.grading_hardcases`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.grading_hardcases` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: `learnloop grading hardcases`: wrong rejection and wrong acceptance per judge route.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py) |
| Source lines | 930 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1ef2f14ebf6f15de8b60736f60650017d40712d3` |
| Commit timestamp | `2026-10-15T12:39:41-04:00` |

## Public API

- `class HardCase` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 169)
  - `content_key(self) -> str` (line 184; public) — The case keyed by its content (item, rubric, answer, label).
- `method_criteria(case: 'HardCase') -> tuple[str, ...]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 208) — The criteria a case's required method grades on use of the method.
- `load_cases(path: Path | None=None) -> tuple[str, list[HardCase]]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 215) — The gold set, validated: labels name real criteria, valid cases none.
- `gold_set_coverage(cases: Sequence[HardCase]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 295) — Cases and real traces per cell, and what the set can and cannot show.
- `case_context(vault: LoadedVault, case: HardCase, arm: str=PRODUCTION_ARM) -> BlindGradingContext` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 320) — The blind grading context as the live door builds it at the latest successor (``attempts._blind_grading_plan``): C2 verifier observations and PF-c's reference policy with the own-route rules (``own-route-v2``, with the item's required method; live grading drops the policy only w…
- `role_output_tokens(vault: LoadedVault, route: str) -> dict[str, int]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 385) — The grader's output budget on ``route`` (a profile name): the policy budget of the production grading route (:data:`HARDCASE_ROUTES`), held to that profile's ``max_tokens``.
- `judge_outcome(case: HardCase, states: Mapping[str, str]) -> str` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 476) — What one judge did with one case.
- `gate_states(case: HardCase, grader_raw: Any, declared_unverified: Sequence[str], *, divergent_route: bool=False) -> tuple[dict[str, str], str]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 559) — The production decision path on one case, and what the rule did.
- `run_hardcases(vault: LoadedVault, *, routes: Sequence[str], caps: SpendCaps, cases_path: Path | None=None, dry_run: bool=False, price_per_million: float | None=None, input_price_per_million: float | None=None, output_price_per_million: float | None=None, clients: Mapping[str, Any] | None=None, cancelled: Callable[[], bool] | None=None, arms: Sequence[str]=(PRODUCTION_ARM,), repeats: int=1) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 629) — Plan (dry run) or run the gold set on each route; aggregate report.
- `write_report(report: Mapping[str, Any], output_dir: Path) -> dict[str, str]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 855)

### Module constants

- `HARNESS_VERSION` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 119)
- `PRODUCTION_ROUTE_RULES` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 121)
- `CATEGORIES` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 122)
- `CELLS` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 124)
- `VALID_CELLS` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 128)
- `FAILING_CELLS` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 130)
- `METHOD_CELL` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 131)
- `PROVENANCES` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 132)
- `REAL_TRACE_CELLS` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 134)
- `ROLES` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 135)
- `REFERENCE_ARMS` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 138)
- `CHECK_ARMS` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 139)
- `PRODUCTION_ARM` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 140)
- `ALL_ARMS` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 141)
- `WITHHELD_CHECK` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 143)
- `HARDCASE_ROUTES` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 150)
- `LEDGER_TASKS` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 152)
- `CASE_KIND` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 153)
- `DEFAULT_CASES` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 155)
- `EEDI_MAP_NOTE` ([src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 156)

### Explicit exports

`__all__` declares:

- `ALL_ARMS`
- `CATEGORIES`
- `CELLS`
- `DEFAULT_CASES`
- `EEDI_MAP_NOTE`
- `HARNESS_VERSION`
- `HardCase`
- `LEDGER_TASKS`
- `METHOD_CELL`
- `PRODUCTION_ARM`
- `PRODUCTION_ROUTE_RULES`
- `PROVENANCES`
- `case_context`
- `gate_states`
- `gold_set_coverage`
- `judge_outcome`
- `load_cases`
- `method_criteria`
- `run_hardcases`
- `write_report`

## Internal implementation anchors

- `_cell(category: str, final_status: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 202)
- `_production_policy(case: HardCase) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 355) — PF-c's policy with the production own-route rules and the item's required method.
- `_split_arm(arm: str) -> tuple[str, str]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 364)
- `_grader_request(vault: LoadedVault, case: HardCase, arm: str) -> tuple[str, str, Any]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 371)
- `_requests(vault: LoadedVault, case: HardCase, arms: Sequence[str]) -> dict[tuple[str, str], tuple[str, str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 379) — (role, arm) -> (prompt, prompt version, result model).
- `_planned_entry(vault: LoadedVault, route: str, role: str) -> RoleClient` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 396)
- `_resolved_entry(vault: LoadedVault, route: str, role: str, injected: Any | None) -> RoleClient` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 407)
- `_repetition_entry(entry: RoleClient, repetition: int) -> RoleClient` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 437) — Repetition 0 is the plain call (earlier checkpoints stay valid); a later repetition is a separately identified fresh call with its own checkpoint.
- `_wilson(count: int, n: int) -> list[float] | None` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 449)
- `_rate(count: int, n: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 458)
- `_criterion_states(case: HardCase, points: Mapping[str, float], *, unverified: Sequence[str]=()) -> dict[str, str]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 462) — ``full`` | ``short`` | ``unassessed`` per rubric criterion.
- `_summary(cases: Sequence[HardCase], outcomes: Mapping[str, str | None]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 514) — The headline rates (cells 1-2 and 3-4, as before) and the method cell's own.
- `_noise_floor(cases: Sequence[HardCase], by_repetition: Sequence[Mapping[str, str | None]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 542) — How often a judge's outcome on a case changes between fresh repetitions.
- `_verdict(role: str, case: HardCase, call: CallResult, outcome: str | None) -> tuple[str, float | None]` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 598)
- `_record_judgment(caller: PFCaller, role: str, case: HardCase, call: CallResult, outcome: str | None, *, arm: str, repetition: int) -> str` ([source](../../../../../../src/learnloop/diagnosis/grading_hardcases.py), line 612) — Append one judge's verdict on one case, once (review F7).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]] — imports `ALL_ARMS`, `PRODUCTION_ARM`, `run_hardcases`, `write_report`; statically calls `run_hardcases`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `output_budget`; calls `output_budget`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`, `is_subscription_transport`; calls `is_subscription_transport`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `BOUNDED_STRUCTURED_COMPLETION`, `ISOLATED_TURN`
- [[Reference/Modules/learnloop/attempts/answer_check|learnloop.attempts.answer_check]] — imports `final_answer_check`; calls `final_answer_check`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `BlindGradingContext`, `blind_context_from_grading_context`, `blind_grading_prompt`, `blind_prompt_version`; calls `blind_context_from_grading_context`, `blind_grading_prompt`, `blind_prompt_version`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `build_grading_context`; calls `build_grading_context`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `METHOD_ROUTE_RULES_VERSION`, `apply_route_rule`, `apply_valid_alternative_gate`, `blind_result_model`, `policy_method_criteria`, `reference_policy`; calls `apply_route_rule`, `apply_valid_alternative_gate`, `blind_result_model`, `policy_method_criteria`, `reference_policy`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `diagnostic_verifier_observations`; calls `diagnostic_verifier_observations`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `CallResult`, `METERED_TYPES`, `PFCaller`, `PFUnavailable`, `RoleClient`, `estimate_tokens`, `pricing_basis`, `validate_pricing`; calls `PFCaller`, `PFUnavailable`, `RoleClient`, `estimate_tokens`, `pricing_basis`, `validate_pricing`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `Rubric`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `required_method_problems`; calls `required_method_problems`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `math`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_grading_hardcases.py](../../../../../../tests/test_grading_hardcases.py) — direct import
  - `test_a_dry_run_plans_the_grader_and_builds_no_client`
  - `test_a_failed_case_is_counted_never_a_crashed_run`
  - `test_a_run_scores_both_error_rates_per_route_and_the_production_path`
  - `test_a_set_without_real_traces_is_labelled_smoke_coverage`
  - `test_a_verbatim_quote_keeps_the_mark_down_on_a_divergent_route`
  - `test_cell_5_pairs_each_required_method_with_the_same_mathematics_without_one`
  - `test_every_fact_and_method_state_on_a_required_method_bypassed`
  - `test_outcomes_name_both_errors_and_the_unassessed_middle`
  - `test_outcomes_on_a_required_method_bypassed`
  - `test_repetitions_are_fresh_and_give_a_noise_floor`
  - `test_the_cli_dry_run`
  - `test_the_grader_arms_cross_the_reference_and_the_check`
  - `test_the_loader_refuses_a_malformed_required_method_case`
  - `test_the_production_path_applies_p1_to_a_divergent_route`
  - `test_the_production_path_enforces_a_required_method_without_a_quote`
  - `test_the_production_path_reads_the_graders_declared_uncertainty`
  - `test_the_tracked_gold_set_is_valid_and_covers_every_cell`
- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_the_hardcase_harness_plans_the_grader_at_its_routes_policy_budget`
  - `test_the_hardcase_harness_retries_a_truncated_grade_once_at_double`

## Modification guidance

- Change grading hardcases policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/grading_hardcases.py](../../../../../../src/learnloop/diagnosis/grading_hardcases.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
