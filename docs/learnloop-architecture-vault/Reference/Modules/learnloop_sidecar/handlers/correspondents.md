---
title: "learnloop_sidecar.handlers.correspondents"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/correspondents.py"
source_paths:
  - "src/learnloop_sidecar/handlers/correspondents.py"
source_commit: "2344f59e1d61bcf8d365a1d714e32afa70c3788e"
source_commit_timestamp: "2026-11-01T22:54:29-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.correspondents module"
  - "src/learnloop_sidecar/handlers/correspondents.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.correspondents`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.correspondents` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Deliverable curriculum C0a RPCs: section coverage and its read API (spec_deliverable_curriculum_v1 §6.4–6.5; ux_reader_compare_ask_v1 §6, §12.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/correspondents.py](../../../../../../src/learnloop_sidecar/handlers/correspondents.py) |
| Source lines | 644 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2344f59e1d61bcf8d365a1d714e32afa70c3788e` |
| Commit timestamp | `2026-11-01T22:54:29-05:00` |

## Public API

- `find_section_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 88) — Reader CA5a's switch (``reader.correspondence.enabled``), respecting ``curriculum.enabled`` (which gates the data) and the Reader itself.
- `figures_follow_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 97) — RW5d P4a (figures follow the section): CA5's ``reader.correspondence.enabled`` (respecting ``curriculum.enabled`` and the Reader) with ``figures.enabled``.
- `hidden_everywhere(vault: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 104)
- `hidden_sources(vault: Any) -> list[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 108)
- `prompt_contract_fields(vault: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 112) — What the Reader's prompt contract adds for CA5a and CA5 (absent while off, so the Guide is exactly as before): the pressed *find this section in my other books* (CA5a, for a section with no judged coverage) and the one-line *also in your books* (CA5, for a section with judged co…
- `class CorrespondentsInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 164)
- `reader_correspondents(ctx: SidecarContext, params: CorrespondentsInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 174) — The other books' sections that treat this section's LOs (no model call, no write).
- `class CoverInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 361)
- `curriculum_cover(ctx: SidecarContext, params: CoverInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 367) — The learner's pressed check: judge where the other books treat this section's LOs (in the background).
- `class CoverJobInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 408)
- `curriculum_cover_job(ctx: SidecarContext, params: CoverJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 413) — A coverage job's state; the first read of a failed one relays its OpenRouter offer.
- `class CoverageCorrectInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 440)
- `curriculum_coverage_correct(ctx: SidecarContext, params: CoverageCorrectInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 451) — *Not about this* / *also about…*: kept across re-judgments; marks nothing as known.
- `class CorrespondentPeekInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 474)
- `reader_correspondent_peek(ctx: SidecarContext, params: CorrespondentPeekInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 481) — A hit's first blocks for the Guide's peek (Codex review F1, F2): no model call.
- `class CorrespondentDismissInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 500)
- `reader_correspondent_dismiss(ctx: SidecarContext, params: CorrespondentDismissInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 517) — *Not about this* on an unchecked hit, or its undo: one transaction (Codex review F3, F6).
- `reader_correspondence_preferences(ctx: SidecarContext, _params: ParamsModel) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 557) — The line's hide preferences (Settings); reports the switch, like the prompt contract.
- `class SetCorrespondencePreferencesInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 564)
- `reader_set_correspondence_preferences(ctx: SidecarContext, params: SetCorrespondencePreferencesInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 572) — *Hide for this book* / *hide everywhere* (or Settings bringing it back).

### Module constants

- `LOG` ([src/learnloop_sidecar/handlers/correspondents.py](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 64)
- `CORRESPONDENT_RPCS` ([src/learnloop_sidecar/handlers/correspondents.py](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 67)
- `FIND_SECTION_RPCS` ([src/learnloop_sidecar/handlers/correspondents.py](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 76)
- `ALSO_IN_BOOKS_RPCS` ([src/learnloop_sidecar/handlers/correspondents.py](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 81)
- `COVER_ORIGIN` ([src/learnloop_sidecar/handlers/correspondents.py](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 85)
- `_REGISTRY_LOCK` ([src/learnloop_sidecar/handlers/correspondents.py](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 252)

### Explicit exports

`__all__` declares:

- `ALSO_IN_BOOKS_RPCS`
- `CORRESPONDENT_RPCS`
- `FIND_SECTION_RPCS`
- `figures_follow_enabled`
- `find_section_enabled`
- `prompt_contract_fields`

## Internal implementation anchors

- `_library_cache(ctx: SidecarContext) -> SC.LibraryCache` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 126) — The open vault's library cache (one per database, as the jobs are).
- `_require(ctx: SidecarContext, extraction_id: str) -> tuple[Any, Any, str]` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 139)
- `_sidecar_error(exc: SC.CoverageError) -> SidecarError` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 157)
- `_with_figures(ctx: SidecarContext, vault: Any, repository: Any, view: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 190) — RW5d P4a (spec §10.2): each judged correspondent section lists the kept figures anchored in it (``figures``, present only when there is one): a figure the learner built reading Strang §6.4 is offered from the section of another book that corresponds to it.
- `class _Jobs` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 239) — One vault's coverage jobs by id, and the LOs being judged now (one judgment per LO and vault in this sidecar).
- `_jobs(ctx: SidecarContext) -> _Jobs` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 255) — The open vault's jobs (Codex review F8): one registry per database, so after a vault switch neither a job's id, its section key nor its running LOs are seen from the other vault (a job of the vault left behind is fenced by its guard: it sends and records nothing more).
- `_public(job: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 271)
- `_job_for(ctx: SidecarContext, extraction_id: str, section_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 276)
- `_run(ctx: SidecarContext, vault: Any, repository: Any, job_id: str, learning_object_ids: list[str]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 284)
- `_require_find_section(ctx: SidecarContext, extraction_id: str) -> tuple[Any, Any, str]` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 466)
- `_preferences(vault: Any, repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 538) — What the Reader and Settings show: the switch, and what the learner hid (books by name).
- `_on_disk_preferences(config_path: Any) -> tuple[list[str], bool]` ([source](../../../../../../src/learnloop_sidecar/handlers/correspondents.py), line 622) — ``[reader.correspondence]``'s hide keys as the file holds them now (absent: the defaults).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `prompt_contract_fields`; statically calls `prompt_contract_fields`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `record_model_calls`; calls `record_model_calls`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `note_unit`, `relay_hint`, `unit`, `unit_origin`, `unit_stamp`, `unit_token`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; calls `enabled`, `section_figures`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ops/settings_store|learnloop.ops.settings_store]] — imports `SettingsStoreError`, `apply_config_updates`; calls `SettingsStoreError`, `apply_config_updates`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `reader_enabled`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `SpanViewError`, `record_span_exposures`; calls `record_span_exposures`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `library_scope`; calls `library_scope`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; calls `Library`, `LibraryCache`, `admission_problem`, `correct`, `correspondents`, `dismiss`, `enabled`, `judge`, `peek`, `section_learning_objects`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `VaultLockError`, `vault_mutation_lock`; calls `vault_mutation_lock`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `background_jobs`; calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `_require_source_reader`, `_source_id_for_extraction`; calls `_require_source_reader`, `_source_id_for_extraction`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `pathlib`, `threading`, `tomllib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_c0a_rpcs_are_all_of_them`
  - `test_the_pinned_ca5_rpcs_are_all_of_them`
  - `test_the_pinned_ca5a_rpcs_are_all_of_them`
- [tests/test_reader_ca5_also_in_books.py](../../../../../../tests/test_reader_ca5_also_in_books.py) — direct import
  - `test_the_ca5_rpcs_are_registered_and_desktop_only`
- [tests/test_section_coverage_rpcs.py](../../../../../../tests/test_section_coverage_rpcs.py) — direct import
  - `test_coverage_jobs_belong_to_the_vault_that_started_them`
  - `test_the_rpcs_are_registered_and_desktop_only`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/correspondents.py](../../../../../../src/learnloop_sidecar/handlers/correspondents.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
