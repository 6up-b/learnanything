---
title: "learnloop.content.synthesis.vault_epigraphs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/vault_epigraphs.py"
source_paths:
  - "src/learnloop/content/synthesis/vault_epigraphs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.content.synthesis.vault_epigraphs module"
  - "src/learnloop/content/synthesis/vault_epigraphs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.vault_epigraphs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.vault_epigraphs` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Start-screen epigraphs: quotes and haiku about freshly synthesized material.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py) |
| Source lines | 379 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `request_vault_epigraphs(client: StructuredTransport, context: VaultEpigraphContext) -> VaultEpigraphBatch` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 62) — Author one epigraph batch through the shared transport (raw call).
- `epigraph_checkpoint(store: Any, client: Any, context: VaultEpigraphContext) -> ModelCheckpoint[VaultEpigraphBatch]` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 75) — One epigraph batch's checkpoint, keyed on what it sends: the rendered prompt (which lists the subject's recent epigraphs, so a batch that was kept changes the next request), the schema and the client's settings.
- `class ContentDigest` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 91) — What the model gets to write about: bounded, deduplicated titles/claims.
- `digest_from_proposal_rows(rows: Iterable[Mapping[str, Any]], *, summary: str='') -> ContentDigest` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 100) — Digest the proposal rows a synthesis persisted (bootstrap or the new_coverage part of an append).
- `digest_for_append(rows: Iterable[Mapping[str, Any]], new_inventories: Iterable[Mapping[str, Any]] | None, neighborhood: Mapping[str, Any] | None, *, summary: str='') -> ContentDigest` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 123) — An append may emit only provenance links, so top the row digest up from the new unit inventories and the bounded affected neighborhood.
- `normalize_epigraph(item: VaultEpigraph | Mapping[str, Any]) -> tuple[str, list[str]] | None` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 188) — ``(kind, lines)`` for a well-formed epigraph, else None.
- `generate_vault_epigraphs(repository: Repository, vault: LoadedVault, client: Any, *, subject_id: str, source_set_id: str | None, synthesis_run_id: str | None, mode: str, digest: ContentDigest, brief: Mapping[str, Any] | None=None, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 239) — Author and persist one batch.

### Module constants

- `EPIGRAPH_PURPOSE` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 39)
- `EPIGRAPHS_PER_SYNTHESIS` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 40)
- `EPIGRAPH_KINDS` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 41)
- `QUOTE_MAX_WORDS` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 42)
- `QUOTE_MAX_CHARS` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 43)
- `HAIKU_LINES` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 44)
- `HAIKU_LINE_MAX_WORDS` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 45)
- `HAIKU_LINE_MAX_CHARS` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 46)
- `MAX_DIGEST_CONCEPTS` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 47)
- `MAX_DIGEST_CLAIMS` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 48)
- `MAX_DIGEST_LEARNING_OBJECTS` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 49)
- `MAX_DIGEST_ITEM_CHARS` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 50)
- `MAX_SUMMARY_CHARS` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 51)
- `RECENT_FOR_DEDUPE` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 52)
- `RECENT_IN_PROMPT` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 53)
- `_BRIEF_KEYS` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 54)
- `_WRAPPING_QUOTES` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 55)
- `_MARKDOWN_LEAD` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 56)
- `_ATTRIBUTION_TAIL` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 58)
- `_WHITESPACE` ([src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 59)

### Explicit exports

`__all__` declares:

- `ContentDigest`
- `EPIGRAPHS_PER_SYNTHESIS`
- `EPIGRAPH_PURPOSE`
- `digest_for_append`
- `digest_from_proposal_rows`
- `epigraph_checkpoint`
- `generate_vault_epigraphs`
- `normalize_epigraph`
- `request_vault_epigraphs`

## Internal implementation anchors

- `_field_of(entries: Any, key: str) -> list[Any]` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 153)
- `_digest(summary: Any, concepts: list[Any], claims: list[Any], learning_objects: list[Any]) -> ContentDigest` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 157)
- `_bounded(values: Iterable[Any], cap: int) -> list[str]` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 166)
- `_collapse(text: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 181)
- `_rejected_line(line: str) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 221)
- `_dedupe_key(text: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 232)
- `_generate(repository: Repository, vault: LoadedVault, client: Any, *, subject_id: str, source_set_id: str | None, synthesis_run_id: str | None, mode: str, digest: ContentDigest, brief: Mapping[str, Any] | None, clock: Clock | None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 271)
- `_subject_title(vault: LoadedVault, subject_id: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 356)
- `_source_set_title(vault: LoadedVault, source_set_id: str | None) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py), line 362)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `digest_for_append`, `digest_from_proposal_rows`, `generate_vault_epigraphs`; statically calls `digest_for_append`, `digest_from_proposal_rows`, `generate_vault_epigraphs`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `ModelCheckpoint`, `checkpointed`, `model_settings`; calls `checkpointed`, `model_settings`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `consume_client_usage`; calls `consume_client_usage`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/synthesis/ai_contracts|learnloop.content.synthesis.ai_contracts]] — imports `VAULT_EPIGRAPHS_PROMPT_VERSION`, `VaultEpigraph`, `VaultEpigraphBatch`, `VaultEpigraphContext`, `vault_epigraphs_prompt`; calls `VaultEpigraphContext`, `vault_epigraphs_prompt`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `logging`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_vault_epigraphs.py](../../../../../../../tests/test_vault_epigraphs.py) — direct import
  - `test_digest_caps_dedupes_and_truncates`
  - `test_digest_for_append_uses_inventories_and_neighborhood`
  - `test_prompt_round_trips_through_the_structured_fake`
  - `test_unknown_kind_is_rejected_by_the_normalizer`

## Modification guidance

- Change vault epigraphs policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/vault_epigraphs.py](../../../../../../../src/learnloop/content/synthesis/vault_epigraphs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
