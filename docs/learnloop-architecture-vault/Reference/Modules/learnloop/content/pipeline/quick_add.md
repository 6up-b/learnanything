---
title: "learnloop.content.pipeline.quick_add"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/quick_add.py"
source_paths:
  - "src/learnloop/content/pipeline/quick_add.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.pipeline"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.pipeline.quick_add module"
  - "src/learnloop/content/pipeline/quick_add.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.quick_add`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.quick_add` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: Quick add (spec_source_ingestion_v2 §1).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/quick_add.py](../../../../../../../src/learnloop/content/pipeline/quick_add.py) |
| Source lines | 395 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class QuickAddError(ValueError)` ([source](../../../../../../../src/learnloop/content/pipeline/quick_add.py), line 52) — Typed failure for the Quick-add plan/enqueue flow.
  - `__init__(self, code: str, message: str, *, details: dict[str, Any] | None=None) -> None` (line 55; internal)
- `class QuickAddPlan` ([source](../../../../../../../src/learnloop/content/pipeline/quick_add.py), line 62)
  - `source_set_id(self) -> str` (line 83; public)
  - `confirmation(self) -> dict[str, Any]` (line 86; public) — THE single confirmation checkpoint (§1): what will be imported, the selected-unit summary, the suggested role, the token estimate, and any external-AI consent.
  - `as_dict(self) -> dict[str, Any]` (line 110; public)
- `select_relevant_units(outline, *, keywords: set[str], cap_tokens: int) -> tuple[list[str], list[str], int, bool]` ([source](../../../../../../../src/learnloop/content/pipeline/quick_add.py), line 155) — Deterministic ToC-guided relevant-scope selection (§1).
- `plan_quick_add(repo, config, vault, source: str, *, subject_id: str | None=None, brief_overrides: dict[str, Any] | None=None) -> QuickAddPlan` ([source](../../../../../../../src/learnloop/content/pipeline/quick_add.py), line 242) — Build the single-confirmation Quick-add plan for an already-extracted source.
- `enqueue_quick_add(vault, ingest_jobs, plan: QuickAddPlan, *, role_override: str | None=None, output_budget_tokens: int | None=None, unlimited_token_budget: bool=False) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/quick_add.py), line 341) — Post-confirmation step: create the source set from the plan and enqueue the priority [inventory(selected) -> bootstrap_synthesis] build batch (§1).

### Module constants

- `_ROLE_BY_CATEGORY` ([src/learnloop/content/pipeline/quick_add.py](../../../../../../../src/learnloop/content/pipeline/quick_add.py), line 37)
- `_CONFIDENT_ROLE_CATEGORIES` ([src/learnloop/content/pipeline/quick_add.py](../../../../../../../src/learnloop/content/pipeline/quick_add.py), line 46)
- `_STOPWORDS` ([src/learnloop/content/pipeline/quick_add.py](../../../../../../../src/learnloop/content/pipeline/quick_add.py), line 47)

## Internal implementation anchors

- `_keywords(brief: dict[str, Any], vault, subject_id: str | None) -> set[str]` ([source](../../../../../../../src/learnloop/content/pipeline/quick_add.py), line 136)
- `_resolve_extraction(repo, source_id: str) -> tuple[str, str] | None` ([source](../../../../../../../src/learnloop/content/pipeline/quick_add.py), line 194) — Return ``(revision_id, extraction_id)`` for the latest completed extraction of ``source_id`` (its current revision preferred), or None.
- `_default_brief(brief_overrides: dict[str, Any] | None, title: str, subject_id: str | None, vault=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/quick_add.py), line 212)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `QuickAddError`, `enqueue_quick_add`, `plan_quick_add`; statically calls `enqueue_quick_add`, `plan_quick_add`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `QuickAddError`, `enqueue_quick_add`, `plan_quick_add`; statically calls `enqueue_quick_add`, `plan_quick_add`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]] — imports `build_acquisition_preview`; calls `build_acquisition_preview`
- [[Reference/Modules/learnloop/content/pipeline/build_plan|learnloop.content.pipeline.build_plan]] — imports `build_build_plan`; calls `build_build_plan`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `OutlineNotFound`, `build_source_outline`; calls `build_source_outline`
- [[Reference/Modules/learnloop/content/synthesis/brief|learnloop.content.synthesis.brief]] — imports `validate_brief`; calls `validate_brief`
- [[Reference/Modules/learnloop/learner/learner_profile|learnloop.learner.learner_profile]] — imports `read_learner_profile`; calls `read_learner_profile`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_source_set`; calls `upsert_source_set`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_quick_add.py](../../../../../../../tests/test_quick_add.py) — direct import
  - `test_narrow_adjunct_preset_uses_reference_role_and_small_upfront_brief`
  - `test_quick_add_one_url_one_confirmation_to_study_map`
  - `test_select_relevant_units_keyword_subset_under_cap`
  - `test_select_relevant_units_whole_source_when_small`

## Modification guidance

- Change quick add policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/quick_add.py](../../../../../../../src/learnloop/content/pipeline/quick_add.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
