---
title: "learnloop.content.proposals.create_ids"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/proposals/create_ids.py"
source_paths:
  - "src/learnloop/content/proposals/create_ids.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.proposals"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.proposals.create_ids module"
  - "src/learnloop/content/proposals/create_ids.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-proposals"
---

# `learnloop.content.proposals.create_ids`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.proposals.create_ids` exists within [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] to own the behavior summarized by its module contract: Deterministic names for anonymous wire creates, before target validation.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/proposals/create_ids.py](../../../../../../../src/learnloop/content/proposals/create_ids.py) |
| Source lines | 84 |
| Owning package | [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `reserve_create_ids(read_ids: Callable[[], Iterable[str]]) -> Iterator[None]` ([source](../../../../../../../src/learnloop/content/proposals/create_ids.py), line 17) — Supply vault reservations without putting local state in the wire schema/prompt.
- `reserve_vault_create_ids(root: str | Path) -> Iterator[None]` ([source](../../../../../../../src/learnloop/content/proposals/create_ids.py), line 27)
- `mint_create_ids(data: Any, context: Any=None) -> Any` ([source](../../../../../../../src/learnloop/content/proposals/create_ids.py), line 44)

### Module constants

- `_PREFIXES` ([src/learnloop/content/proposals/create_ids.py](../../../../../../../src/learnloop/content/proposals/create_ids.py), line 12)

## Internal implementation anchors

- `_blank(value: Any) -> bool` ([source](../../../../../../../src/learnloop/content/proposals/create_ids.py), line 40)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `reserve_vault_create_ids`; statically calls `reserve_vault_create_ids`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `reserve_vault_create_ids`; statically calls `reserve_vault_create_ids`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `mint_create_ids`; statically calls `mint_create_ids`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `reserve_vault_create_ids`; statically calls `reserve_vault_create_ids`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `snake_case`; calls `snake_case`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `collections`, `contextlib`, `contextvars`, `hashlib`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]], [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]], [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/ad_denial_log_helpers.py](../../../../../../../tests/ad_denial_log_helpers.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/rw5c_golden_source.py](../../../../../../../tests/rw5c_golden_source.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_ad1_outside_and_cli.py](../../../../../../../tests/test_ad1_outside_and_cli.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_ad3_monitoring.py](../../../../../../../tests/test_ad3_monitoring.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_ad3_relatedness.py](../../../../../../../tests/test_ad3_relatedness.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_ai_compare.py](../../../../../../../tests/test_ai_compare.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_approach_maps.py](../../../../../../../tests/test_approach_maps.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_arcb_close_fixes.py](../../../../../../../tests/test_arcb_close_fixes.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_attempt_chain_records.py](../../../../../../../tests/test_attempt_chain_records.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_authoring_create_ids.py](../../../../../../../tests/test_authoring_create_ids.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]
- [tests/test_auto_build_spend_report.py](../../../../../../../tests/test_auto_build_spend_report.py) — imports consumer [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]]

## Modification guidance

- Change create ids policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/proposals/create_ids.py](../../../../../../../src/learnloop/content/proposals/create_ids.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
