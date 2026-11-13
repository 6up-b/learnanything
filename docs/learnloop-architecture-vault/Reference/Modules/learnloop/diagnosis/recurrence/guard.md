---
title: "learnloop.diagnosis.recurrence.guard"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/recurrence/guard.py"
source_paths:
  - "src/learnloop/diagnosis/recurrence/guard.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.recurrence"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.recurrence.guard module"
  - "src/learnloop/diagnosis/recurrence/guard.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-recurrence"
---

# `learnloop.diagnosis.recurrence.guard`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.recurrence.guard` exists within [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] to own the behavior summarized by its module contract: The same-answer/different-cause guard (Slice 2 §3.6).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/recurrence/guard.py](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py) |
| Source lines | 721 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class PlantedPair` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 86)
- `class DiagnoserLink` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 166) — Whether one M1 diagnosis of a planted B answer linked its A answer.
  - `false_merge(self) -> bool` (line 182; public)
- `class M1Run` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 187)
- `read_m1_run(run_dir: Path, *, history_mode: str | None=None) -> M1Run` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 209) — An M1 review run's planted same-answer/different-cause cases (Slice 1 S1.0).
- `suite_from_run(run_dir: Path, *, history_mode: str | None=None) -> list[PlantedPair]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 317) — Planted cases of an M1 review run (Slice 1 S1.0), as guard pairs.
- `is_link_case(pair: PlantedPair) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 323) — An M1 case whose diagnoser citations are checked (not a statement pair).
- `record_diagnoser_links(repository: Repository, links: Sequence[DiagnoserLink]) -> int` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 329) — Append each M1 diagnosis's link outcome as a ``diagnoser`` verdict on the planted pair (idempotent).
- `guard_pairs(suite: Sequence[PlantedPair]) -> list[CandidatePair]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 377)
- `registered_cases(repository: Repository) -> list[PlantedPair]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 384) — The planted cases registered as required (beyond the built-in suite).
- `register_suite(repository: Repository, cases: Sequence[PlantedPair]) -> int` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 398) — Make cases required for the switch (idempotent by case id).
- `guard_suite(*, from_run: Path | None=None, repository: Repository | None=None, history_mode: str | None=None) -> list[PlantedPair]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 413) — The built-in suite, the registered cases, and an M1 run's cases (deduplicated).
- `suite_hash(suite: Sequence[PlantedPair]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 431)
- `guard_status(repository: Repository, *, suite: Sequence[PlantedPair] | None=None, judge_model: str | None=None, history_mode: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 466) — Each planted pair's standing verdicts under the current prompt and input.
- `run_guard(vault: LoadedVault, repository: Repository, *, caps: Any, price_per_million: float | None=None, from_run: Path | None=None, dry_run: bool=False, rerun: bool=False, cancelled: Any=None, judge_client: Any=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 566) — Judge every required planted pair the configured judge has not judged.
- `configured_judge_model(vault: LoadedVault) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 681) — The PRODUCER the same-cause judge route resolves to, from config alone.

### Module constants

- `GUARD_SUBJECT_KIND` ([src/learnloop/diagnosis/recurrence/guard.py](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 59)
- `GUARD_SUITE_VERSION` ([src/learnloop/diagnosis/recurrence/guard.py](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 60)
- `DIAGNOSER_STATEMENT_SUFFIX` ([src/learnloop/diagnosis/recurrence/guard.py](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 62)
- `DIAGNOSER_LINK_SOURCE` ([src/learnloop/diagnosis/recurrence/guard.py](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 64)
- `GUARD_KIND` ([src/learnloop/diagnosis/recurrence/guard.py](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 68)
- `BUILTIN_SUITE` ([src/learnloop/diagnosis/recurrence/guard.py](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 106)

### Explicit exports

`__all__` declares:

- `BUILTIN_SUITE`
- `DiagnoserLink`
- `M1Run`
- `GUARD_KIND`
- `GUARD_SUBJECT_KIND`
- `GUARD_SUITE_VERSION`
- `PlantedPair`
- `configured_judge_model`
- `guard_pairs`
- `guard_status`
- `guard_suite`
- `is_link_case`
- `read_m1_run`
- `record_diagnoser_links`
- `register_suite`
- `registered_cases`
- `run_guard`
- `suite_from_run`
- `suite_hash`

## Internal implementation anchors

- `_case(expected: str, topic: str, problem: str, answer: str | None, a: str, b: str, quote_a: str | None=None, quote_b: str | None=None) -> PlantedPair` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 99)
- `_primary_learner_statement(proposal: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 193)
- `_subject(pair: PlantedPair, side: str) -> Subject` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 360)
- `_diagnoser_link_rows(repository: Repository, *, history_mode: str | None) -> dict[frozenset[str], list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py), line 437) — Recorded M1 diagnoser link outcomes under the CURRENT diagnosis prompt (and, given one, the configured history mode), by planted pair.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/recurrence|learnloop.cli.recurrence]] — imports `run_guard`; statically calls `run_guard`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `configured_judge_model`; statically calls `configured_judge_model`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `record_model_calls`; calls `content_key`, `record_model_calls`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`; calls `provider_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/diagnosis_review|learnloop.db.stores.diagnosis_review]] — imports `review_rows`; calls `review_rows`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/recurrence|learnloop.db.stores.recurrence]] — imports `register_guard_cases`; calls `register_guard_cases`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `RUN_FILE`, `SCRATCH_FILE`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `command_spend`; calls `command_spend`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `default_judge_client`, `estimate_tokens`, `judge_executor`, `producer_label`, `producer_label_for`, `receipt_sink`; calls `default_judge_client`, `estimate_tokens`, `judge_executor`, `producer_label`, `producer_label_for`, `receipt_sink`
- [[Reference/Modules/learnloop/diagnosis/recurrence/kind|learnloop.diagnosis.recurrence.kind]] — imports `SAME_CAUSE`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `settings_from_config`; calls `settings_from_config`
- [[Reference/Modules/learnloop/diagnosis/split/settings|learnloop.diagnosis.split.settings]] — imports `DIAGNOSIS_PROMPT_VERSION`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `already_judged`, `judge_pairs`, `pair_input_hash`, `pair_prompt`; calls `already_judged`, `judge_pairs`, `pair_input_hash`, `pair_prompt`
- [[Reference/Modules/learnloop/matching/kinds|learnloop.matching.kinds]] — imports `MatchKind`, `Subject`; calls `MatchKind`, `Subject`
- [[Reference/Modules/learnloop/matching/shortlist|learnloop.matching.shortlist]] — imports `CandidatePair`; calls `CandidatePair`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/recurrence|learnloop.cli.recurrence]], [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/recurrence_commands_helpers.py](../../../../../../../tests/recurrence_commands_helpers.py) — direct import
- [tests/test_recurrence_commands.py](../../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_a_citation_that_did_not_validate_merges_nothing_and_is_reported`
  - `test_a_false_merge_blocks_the_switch_and_a_fixed_judge_reruns_through_the_guard`
  - `test_a_registered_case_the_judge_never_saw_blocks_the_switch`
  - `test_an_explicit_rerun_supersedes_the_same_models_false_merge`
  - `test_an_m1_case_from_a_run_is_required_and_its_false_merge_blocks_the_switch`
  - `test_guard_verdicts_from_another_judge_model_do_not_open_the_switch`
  - `test_the_cli_backlog_and_guard_dry_runs`
  - `test_the_guard_dry_run_sends_nothing`
  - `test_the_guard_judges_the_diagnosers_own_statement_for_the_b_answer`
  - `test_the_guard_reruns_only_unjudged_pairs`
  - `test_the_guard_stops_at_its_call_cap`
  - `test_the_judge_producer_is_model_and_effort_so_codex_tiers_never_share_a_guard_pass`
  - `test_verdicts_split_across_two_models_do_not_pass_for_the_configured_one`

## Modification guidance

- Change guard policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/recurrence/guard.py](../../../../../../../src/learnloop/diagnosis/recurrence/guard.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
