---
title: "learnloop.content.authoring.laddered_stems"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/authoring/laddered_stems.py"
source_paths:
  - "src/learnloop/content/authoring/laddered_stems.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.authoring"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.authoring.laddered_stems module"
  - "src/learnloop/content/authoring/laddered_stems.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-authoring"
---

# `learnloop.content.authoring.laddered_stems`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.authoring.laddered_stems` exists within [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] to own the behavior summarized by its module contract: A2 — laddered stems (spec_measurement_efficiency_v1 §3.A2).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/authoring/laddered_stems.py](../../../../../../../src/learnloop/content/authoring/laddered_stems.py) |
| Source lines | 391 |
| Owning package | [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `stem_id_for_item(item: PracticeItem) -> str | None` ([source](../../../../../../../src/learnloop/content/authoring/laddered_stems.py), line 88) — This item's stem, from either of the two places it can be declared.
- `stem_column_for_item(item: PracticeItem) -> tuple[str, str] | None` ([source](../../../../../../../src/learnloop/content/authoring/laddered_stems.py), line 109) — ``(stem_id, capability)`` for one item, or ``None`` if it is not a stem part.
- `stem_columns_for_surfaces(vault: LoadedVault, surface_item_ids: Mapping[str, str]) -> dict[str, tuple[str, str]]` ([source](../../../../../../../src/learnloop/content/authoring/laddered_stems.py), line 125) — surface id -> ``(stem_id, capability)`` for the surfaces that are stem parts.
- `stem_parts(vault: LoadedVault) -> dict[str, list[PracticeItem]]` ([source](../../../../../../../src/learnloop/content/authoring/laddered_stems.py), line 151) — stem id -> its parts, ordered by ``part_index`` then item id.
- `class StemShape` ([source](../../../../../../../src/learnloop/content/authoring/laddered_stems.py), line 178) — One stem's declared shape — how much of a capability ROW it actually fills.
  - `columns_filled(self) -> int` (line 189; public)
  - `is_ladder(self) -> bool` (line 193; public) — A stem is a LADDER only if its parts span >= 2 capability columns.
  - `as_dict(self) -> dict[str, Any]` (line 204; public)
- `stem_shapes(vault: LoadedVault) -> list[StemShape]` ([source](../../../../../../../src/learnloop/content/authoring/laddered_stems.py), line 215) — The declared shape of every stem in the vault.
- `stem_independence_signal(vault: LoadedVault, repository: Repository, *, since: str | None=None) -> Metric` ([source](../../../../../../../src/learnloop/content/authoring/laddered_stems.py), line 254) — ``laddered_stem_cross_column_agreement``: A2's revert producer.

### Module constants

- `LADDERED_STEM_VERSION` ([src/learnloop/content/authoring/laddered_stems.py](../../../../../../../src/learnloop/content/authoring/laddered_stems.py), line 80)
- `STEM_INDEPENDENCE_METRIC` ([src/learnloop/content/authoring/laddered_stems.py](../../../../../../../src/learnloop/content/authoring/laddered_stems.py), line 241)
- `MIN_PAIRS_PER_ARM` ([src/learnloop/content/authoring/laddered_stems.py](../../../../../../../src/learnloop/content/authoring/laddered_stems.py), line 246)
- `MIN_INDEPENDENCE_MARGIN` ([src/learnloop/content/authoring/laddered_stems.py](../../../../../../../src/learnloop/content/authoring/laddered_stems.py), line 251)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `stem_independence_signal`, `stem_shapes`; statically calls `stem_independence_signal`, `stem_shapes`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `stem_independence_signal`, `stem_shapes`; statically calls `stem_independence_signal`, `stem_shapes`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `Metric`; calls `Metric`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_laddered_stems.py](../../../../../../../tests/test_laddered_stems.py) — direct import
  - `test_a_part_with_no_capability_cannot_be_placed_in_a_column`
  - `test_stem_identity_falls_back_to_the_pre_existing_fingerprint`
  - `test_stem_independence_signal_abstains_before_it_has_both_arms`
  - `test_stem_independence_signal_reports_both_arms_once_pairs_exist`
  - `test_stem_shape_names_a_one_column_stem_as_not_a_ladder`

## Modification guidance

- Change laddered stems policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/authoring/laddered_stems.py](../../../../../../../src/learnloop/content/authoring/laddered_stems.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
