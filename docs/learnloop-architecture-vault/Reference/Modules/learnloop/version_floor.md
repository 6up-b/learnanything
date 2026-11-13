---
title: "learnloop.version_floor"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/version_floor.py"
source_paths:
  - "src/learnloop/version_floor.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.version_floor module"
  - "src/learnloop/version_floor.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.version_floor`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.version_floor` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: The oldest supported tag: a vault below it is refused where it is opened.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/version_floor.py](../../../../../src/learnloop/version_floor.py) |
| Source lines | 182 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `is_below_floor(tag: str | None) -> bool` ([source](../../../../../src/learnloop/version_floor.py), line 62) — Whether a vault at ``tag`` is below the floor.
- `upgrade_commands(vault_root: Path, tag: str | None) -> tuple[str, ...]` ([source](../../../../../src/learnloop/version_floor.py), line 75) — The commands that bring a vault at ``tag`` to the floor on this code, in order.
- `class BelowOldestSupported(RuntimeError)` ([source](../../../../../src/learnloop/version_floor.py), line 91) — A vault (or an unfinished upgrade's journal) below the oldest supported tag: it is not opened.
  - `__init__(self, vault_root: Path, tag: str | None, *, journal: tuple[str, str] | None=None) -> None` (line 94; internal)
  - `_message(self) -> str` (line 102; internal)
- `may_open_below_floor(vault_root: Path) -> bool` ([source](../../../../../src/learnloop/version_floor.py), line 122) — Whether this vault opens below the floor here: ``learnloop upgrade`` is upgrading it, or a test built it.
- `refuse_below_floor(vault_root: Path, config) -> None` ([source](../../../../../src/learnloop/version_floor.py), line 129) — Raise :class:`BelowOldestSupported` if the vault's config (a ``LearnLoopConfig`` loaded from its ``learnloop.toml``) is below the floor, or names no tag, unless this vault may be opened anyway.
- `refuse_journal_below_floor(vault_root: Path, predecessor: str, target: str) -> None` ([source](../../../../../src/learnloop/version_floor.py), line 140) — Raise :class:`BelowOldestSupported` for a journalled upgrade from below the floor, unless allowed.
- `upgrading(vault_root: Path) -> Iterator[None]` ([source](../../../../../src/learnloop/version_floor.py), line 148) — ``learnloop upgrade``'s allowance: in this context, ``vault_root`` opens whatever its tag.
- `allow_below_floor_in_tests(vault_root: Path) -> None` ([source](../../../../../src/learnloop/version_floor.py), line 158) — Let a test's vault below the floor, and for the rest of that test any vault, open (``tests/helpers.py``'s ``allow_below_floor`` only).
- `end_test_allowance() -> None` ([source](../../../../../src/learnloop/version_floor.py), line 166) — Close the running test's allowance (``tests/conftest.py``, after each test).

### Module constants

- `_TAG` ([src/learnloop/version_floor.py](../../../../../src/learnloop/version_floor.py), line 38)
- `_PRE_CHAIN_STEPS` ([src/learnloop/version_floor.py](../../../../../src/learnloop/version_floor.py), line 42)
- `_UPGRADING` ([src/learnloop/version_floor.py](../../../../../src/learnloop/version_floor.py), line 45)
- `_TEST_ROOTS` ([src/learnloop/version_floor.py](../../../../../src/learnloop/version_floor.py), line 50)
- `_TEST_OPEN` ([src/learnloop/version_floor.py](../../../../../src/learnloop/version_floor.py), line 54)

### Explicit exports

`__all__` declares:

- `BelowOldestSupported`
- `allow_below_floor_in_tests`
- `end_test_allowance`
- `is_below_floor`
- `may_open_below_floor`
- `refuse_below_floor`
- `refuse_journal_below_floor`
- `upgrade_commands`
- `upgrading`

## Internal implementation anchors

- `_number(tag: str) -> int | None` ([source](../../../../../src/learnloop/version_floor.py), line 57)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/activation_journal|learnloop.activation_journal]] — imports `refuse_journal_below_floor`; statically calls `refuse_journal_below_floor`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `upgrading`; statically calls `upgrading`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `refuse_below_floor`; statically calls `refuse_below_floor`
- [[Reference/Modules/learnloop/remote/runtime|learnloop.remote.runtime]] — imports `BelowOldestSupported`, `refuse_below_floor`; statically calls `refuse_below_floor`
- [[Reference/Modules/learnloop/substrate/shadow_rebuild|learnloop.substrate.shadow_rebuild]] — imports `is_below_floor`, `may_open_below_floor`; statically calls `is_below_floor`, `may_open_below_floor`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `refuse_below_floor`; statically calls `refuse_below_floor`
- [[Reference/Modules/learnloop_sidecar/handlers/app|learnloop_sidecar.handlers.app]] — imports `BelowOldestSupported`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `OLDEST_SUPPORTED`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `contextvars`, `pathlib`, `re`, `shlex`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/activation_journal|learnloop.activation_journal]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]], [[Reference/Modules/learnloop/remote/runtime|learnloop.remote.runtime]], [[Reference/Modules/learnloop/substrate/shadow_rebuild|learnloop.substrate.shadow_rebuild]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/conftest.py](../../../../../tests/conftest.py) — direct import
- [tests/followups_nov2_help_fold_helpers.py](../../../../../tests/followups_nov2_help_fold_helpers.py) — direct import
- [tests/helpers.py](../../../../../tests/helpers.py) — direct import
- [tests/serve_eligibility_helpers.py](../../../../../tests/serve_eligibility_helpers.py) — direct import
- [tests/test_version_floor.py](../../../../../tests/test_version_floor.py) — direct import
  - `test_a_journal_naming_a_link_below_the_floor_is_refused`
  - `test_a_vault_whose_config_names_no_tag_is_refused`
  - `test_the_commands_take_a_vault_older_than_the_chain_through_its_steps`
  - `test_the_floor_is_a_tag_of_the_chain_and_the_chain_counts_up`
  - `test_the_suites_allowance_opens_any_vault_until_the_test_ends`
  - `test_the_upgrade_allowance_covers_only_the_vault_it_upgrades`
  - `test_the_upgrade_command_still_upgrades_a_vault_below_the_floor`
- [tests/ux_phase1_support.py](../../../../../tests/ux_phase1_support.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains version floor within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/version_floor.py](../../../../../src/learnloop/version_floor.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
