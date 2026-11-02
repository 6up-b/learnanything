---
title: "learnloop.remote.runtime"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/remote/runtime.py"
source_paths:
  - "src/learnloop/remote/runtime.py"
source_commit: "e7653a9cb303eab4fb6754176605fe61a256d7e9"
source_commit_timestamp: "2026-10-25T19:59:11-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.remote"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
aliases:
  - "learnloop.remote.runtime module"
  - "src/learnloop/remote/runtime.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-remote"
---

# `learnloop.remote.runtime`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.remote.runtime` exists within [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] to own the behavior summarized by its module contract: Secondary attach: a second process on a vault the desktop owns (spec_mcp_frontend_c1 §3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/remote/runtime.py](../../../../../../src/learnloop/remote/runtime.py) |
| Source lines | 204 |
| Owning package | [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e7653a9cb303eab4fb6754176605fe61a256d7e9` |
| Commit timestamp | `2026-10-25T19:59:11-04:00` |

## Public API

- `class SchemaMismatch(RuntimeError)` ([source](../../../../../../src/learnloop/remote/runtime.py), line 63) — The vault's schema is not this code's: the desktop (primary) must migrate it.
- `vault_sqlite_path(vault_root: Path) -> Path` ([source](../../../../../../src/learnloop/remote/runtime.py), line 69) — The vault's database, from its configuration only (no dotenv, no load).
- `check_schema(sqlite_path: Path, *, vault_root: Path | None=None) -> None` ([source](../../../../../../src/learnloop/remote/runtime.py), line 77) — Refuse a database whose applied migrations differ from this code's.
- `refuse_interrupted_activation(sqlite_path: Path) -> None` ([source](../../../../../../src/learnloop/remote/runtime.py), line 88) — Refuse a vault whose activation did not commit (LP-min (a), re-review F2).
- `class RemoteRuntime` ([source](../../../../../../src/learnloop/remote/runtime.py), line 99) — One vault, attached as a secondary process.
  - `attach(cls, vault_root: Path | str, *, load_environment: bool=True) -> 'RemoteRuntime'` (line 114; public) — Attach without migrating; :class:`SchemaMismatch` unless the schema matches.
  - `vault(self) -> LoadedVault` (line 128; public) — The loaded vault, reloaded when its files changed (at most every 2 s).
  - `_settled_load(self, files: dict[str, tuple[int, int]], fingerprint: str) -> tuple[LoadedVault, str | None]` (line 147; internal) — A load whose files did not change while it ran, with its fingerprint; else the last load, marked unsettled, and no fingerprint.
  - `read_repository(self) -> Repository` (line 166; public) — A read-only attach: reads through it can never write.
  - `alias_key(self) -> bytes | None` (line 171; public) — The key chat's opaque aliases are made with: the vault's (``.learnloop/mcp/alias-key``, made by ``learnloop mcp serve``), or None, which keys them for this process (``learner_context``).
  - `schema_ok(self) -> bool` (line 182; public)
  - `describe(self) -> dict[str, Any]` (line 189; public)

### Module constants

- `FINGERPRINT_TTL_SECONDS` ([src/learnloop/remote/runtime.py](../../../../../../src/learnloop/remote/runtime.py), line 57)

### Explicit exports

`__all__` declares:

- `FINGERPRINT_TTL_SECONDS`
- `RemoteRuntime`
- `SETTLE_ATTEMPTS`
- `SchemaMismatch`
- `check_schema`
- `refuse_interrupted_activation`
- `content_files`
- `vault_content_fingerprint`
- `vault_sqlite_path`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/mcp|learnloop.cli.mcp]] — imports `SchemaMismatch`, `vault_sqlite_path`; statically calls `vault_sqlite_path`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/activation_journal|learnloop.activation_journal]] — imports `module`; calls `message`, `pending`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `load_config`; calls `load_config`
- [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]] — imports `schema_is_current`; calls `schema_is_current`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `SNAPSHOT_UNSETTLED`
- [[Reference/Modules/learnloop/remote/endpoint_token|learnloop.remote.endpoint_token]] — imports `read_alias_key`; calls `read_alias_key`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `CONTENT_FINGERPRINT_TTL_SECONDS`, `SETTLE_ATTEMPTS`, `SETTLE_PAUSE_SECONDS`, `content_digest`, `content_files`, `load_vault`, `settled_load_vault`, `vault_content_fingerprint`; calls `content_digest`, `content_files`, `load_vault`, `settled_load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `DoctorIssue`, `LoadedVault`; calls `DoctorIssue`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/mcp|learnloop.cli.mcp]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
- [tests/test_learner_data_relax_2.py](../../../../../../tests/test_learner_data_relax_2.py) — direct import
  - `test_the_mcp_ledger_row_carries_its_arguments`
- [tests/test_lp_claim_fixes_rereview.py](../../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
  - `test_f2_an_mcp_server_already_attached_stops_serving_when_a_journal_appears`
  - `test_f2_attaches_that_never_write_refuse_while_the_journal_stands`
  - `test_f2_the_phone_host_refuses_to_start_while_the_journal_stands`
- [tests/test_mcp_c1a_narrow.py](../../../../../../tests/test_mcp_c1a_narrow.py) — direct import
  - `test_a_raw_generated_id_cannot_confirm_a_guessed_title`
  - `test_every_text_field_is_authored_an_answer_or_withheld_without_a_record`
  - `test_generated_topics_are_aliased_everywhere_and_accepted_back`
  - `test_the_server_keeps_its_alias_key_beside_the_endpoint_token`
  - `test_today_and_progress_never_show_a_generated_topic_s_name`
- [tests/test_mcp_c1a_review.py](../../../../../../tests/test_mcp_c1a_review.py) — direct import
  - `test_a_check_reserved_while_passages_are_retrieved_withholds_them`
  - `test_a_diagnosis_s_cause_and_every_belief_drawn_from_it_are_held_back`
  - `test_a_diagnosis_shown_a_belief_on_a_generated_topic_is_held_back`
  - `test_a_diagnosis_shown_an_answer_whose_grading_saw_the_unpinned_one_is_held_back`
  - `test_a_prerequisite_drafted_from_an_unpinned_answer_shows_neither_its_title_nor_its_id`
  - `test_a_vault_that_changes_while_it_loads_fails_closed`
  - `test_an_unpinned_answer_shows_no_text_even_when_no_key_change_is_recorded`
  - `test_text_drawn_from_an_unpinned_answer_is_withheld_in_every_section`
  - `test_the_dry_run_bounds_the_live_verification`
- [tests/test_mcp_cli.py](../../../../../../tests/test_mcp_cli.py) — direct import
  - `test_activity_reports_chat_calls_and_passages_from_the_ledgers`
- [tests/test_mcp_http.py](../../../../../../tests/test_mcp_http.py) — direct import
- [tests/test_mcp_runtime.py](../../../../../../tests/test_mcp_runtime.py) — direct import
  - `test_attach_and_every_view_write_nothing`
  - `test_secondary_attach_refuses_a_schema_it_does_not_match`
  - `test_the_loaded_vault_follows_its_files`
- [tests/test_mcp_tools.py](../../../../../../tests/test_mcp_tools.py) — direct import
  - `test_today_shows_the_stored_plan_and_writes_nothing`
- [tests/test_reread_safety_landing.py](../../../../../../tests/test_reread_safety_landing.py) — direct import
  - `test_an_unmarked_reading_of_a_protected_book_is_withheld_from_every_model_visible_path`
- [tests/test_secondary_attach.py](../../../../../../tests/test_secondary_attach.py) — direct import
  - `test_a_directory_alias_does_not_hide_a_truncated_source_sets_file_from_the_chat_runtime`

## Modification guidance

- Make changes here when the responsibility remains runtime within learnloop.remote; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/remote/runtime.py](../../../../../../src/learnloop/remote/runtime.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
