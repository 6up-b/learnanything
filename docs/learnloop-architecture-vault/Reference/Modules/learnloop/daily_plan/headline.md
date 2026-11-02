---
title: "learnloop.daily_plan.headline"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/headline.py"
source_paths:
  - "src/learnloop/daily_plan/headline.py"
source_commit: "0fc6e3e96f73e725ecc0505e16fc9c79902a881c"
source_commit_timestamp: "2026-10-20T01:23:55-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.headline module"
  - "src/learnloop/daily_plan/headline.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.headline`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.headline` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: The optional Today headline (``spec_daily_loop_v1.md`` §6.7, D7).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/headline.py](../../../../../../src/learnloop/daily_plan/headline.py) |
| Source lines | 224 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0fc6e3e96f73e725ecc0505e16fc9c79902a881c` |
| Commit timestamp | `2026-10-20T01:23:55-04:00` |

## Public API

- `classify_learning_objects(vault: Any, repository: Any, *, now: datetime | None=None, learning_object_ids: Iterable[str] | None=None) -> dict[str, str]` ([source](../../../../../../src/learnloop/daily_plan/headline.py), line 51) — Each active LO in exactly one headline class.
- `expected_recall_today(vault: Any, repository: Any, *, now: datetime, excluded_item_ids: Iterable[str]=()) -> tuple[float | None, int]` ([source](../../../../../../src/learnloop/daily_plan/headline.py), line 136) — Mean FSRS retrievability now over items with memory state, and their count; ``excluded_item_ids`` (DL2: intent) are left out.
- `intent_exclusions(vault: Any, repository: Any, *, now: datetime) -> tuple[frozenset[str], frozenset[str]]` ([source](../../../../../../src/learnloop/daily_plan/headline.py), line 160) — ``(excluded LO ids, excluded item ids)`` by resolved intent (F10); both empty when intent changes nothing.
- `today_headline(vault: Any, repository: Any, *, now: datetime) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/headline.py), line 188)

### Module constants

- `HEADLINE_CLASSES` ([src/learnloop/daily_plan/headline.py](../../../../../../src/learnloop/daily_plan/headline.py), line 47)
- `EXPECTED_RECALL_TOOLTIP` ([src/learnloop/daily_plan/headline.py](../../../../../../src/learnloop/daily_plan/headline.py), line 48)

### Explicit exports

`__all__` declares:

- `EXPECTED_RECALL_TOOLTIP`
- `HEADLINE_CLASSES`
- `classify_learning_objects`
- `expected_recall_today`
- `intent_exclusions`
- `today_headline`

## Internal implementation anchors

- `_demonstrated(vault: Any, repository: Any, learning_object: Any, facets: list[str], cells_by_facet: dict[str, list[Any]], canonical: bool) -> bool` ([source](../../../../../../src/learnloop/daily_plan/headline.py), line 96)
- `_has_direct_evidence(facets: list[str], cells_by_facet: dict[str, list[Any]], mastery: Any, canonical: bool) -> bool` ([source](../../../../../../src/learnloop/daily_plan/headline.py), line 124)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `module`; statically calls `classify_learning_objects`
- [[Reference/Modules/learnloop/reader_learner_state|learnloop.reader_learner_state]] — imports `module`; statically calls `classify_learning_objects`
- [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]] — imports `HEADLINE_CLASSES`, `classify_learning_objects`, `today_headline`; statically calls `classify_learning_objects`, `today_headline`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `today_headline`; statically calls `today_headline`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/daily_plan/reentry|learnloop.daily_plan.reentry]] — imports `retrievability`; calls `retrievability`
- [[Reference/Modules/learnloop/goals/certification|learnloop.goals.certification]] — imports `is_demonstrated_credit`; calls `is_demonstrated_credit`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `lo_certification`, `required_capabilities_for_facet`; calls `lo_certification`, `required_capabilities_for_facet`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `scope_facets`; calls `scope_facets`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `is_canonical_state_vault`; calls `is_canonical_state_vault`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `load_placement_state`, `placement_active`; calls `load_placement_state`, `placement_active`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `intent_serving`; calls `intent_serving`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop/reader_learner_state|learnloop.reader_learner_state]], [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_daily_plan_composition.py](../../../../../../tests/test_daily_plan_composition.py) — direct import
  - `test_a_check_miss_awaiting_its_diagnosis_stays_assumed_and_is_not_rechecked`
- [tests/test_intent_codex_review.py](../../../../../../tests/test_intent_codex_review.py) — direct import
  - `test_f10_the_headline_leaves_out_excluded_los_and_items`
- [tests/test_mcp_c1a_narrow.py](../../../../../../tests/test_mcp_c1a_narrow.py) — direct import
  - `test_today_and_progress_never_show_a_generated_topic_s_name`
- [tests/test_router_card.py](../../../../../../tests/test_router_card.py) — direct import
  - `test_only_the_authoritative_classification_says_demonstrated`
- [tests/test_today_headline.py](../../../../../../tests/test_today_headline.py) — direct import
  - `test_a_blueprint_lo_with_an_integration_gap_is_learning`
  - `test_assumed_comes_first_and_is_omitted_before_placement`
  - `test_each_lo_is_in_exactly_one_class`
  - `test_expected_recall_is_a_labelled_model_estimate`
  - `test_partial_demonstration_is_learning_and_whole_is_demonstrated`

## Modification guidance

- Make changes here when the responsibility remains headline within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/headline.py](../../../../../../src/learnloop/daily_plan/headline.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
