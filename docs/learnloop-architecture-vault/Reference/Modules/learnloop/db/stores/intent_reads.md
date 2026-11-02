---
title: "learnloop.db.stores.intent_reads"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/intent_reads.py"
source_paths:
  - "src/learnloop/db/stores/intent_reads.py"
source_commit: "1d5ba0272bb7d749483eea0f91c9eda2030bc4e9"
source_commit_timestamp: "2026-10-20T00:37:51-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.intent_reads module"
  - "src/learnloop/db/stores/intent_reads.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.intent_reads`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.intent_reads` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Read-only queries for daily-loop DL2's intent resolution (spec §5.3).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/intent_reads.py](../../../../../../../src/learnloop/db/stores/intent_reads.py) |
| Source lines | 179 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1d5ba0272bb7d749483eea0f91c9eda2030bc4e9` |
| Commit timestamp | `2026-10-20T00:37:51-04:00` |

## Public API

- `commitment_tables_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/intent_reads.py), line 14)
- `commitments_covering_items(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/intent_reads.py), line 21) — Every commitment whose HEAD version targets an LO or a practice item.
- `versions_for(connection: sqlite3.Connection, commitment_ids: list[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/intent_reads.py), line 52)
- `head_targets_for(connection: sqlite3.Connection, version_ids: list[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/intent_reads.py), line 74)
- `events_for(connection: sqlite3.Connection, commitment_ids: list[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/intent_reads.py), line 95)
- `attempts_for_anchor(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/intent_reads.py), line 116) — Every attempt's FSRS-eligibility inputs, newest last per item (§5.3 anchor).
- `attempts_since(connection: sqlite3.Connection, item_ids: list[str], since: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/intent_reads.py), line 129) — Attempts on these items at or after ``since`` (a check's date), oldest first, with what decides whether one was on your own (primed, hints).
- `surprise_factors(connection: sqlite3.Connection) -> dict[str, float]` ([source](../../../../../../../src/learnloop/db/stores/intent_reads.py), line 154) — Each attempt's recorded FSRS interval factor (the fixture reproduction test).

### Explicit exports

`__all__` declares:

- `attempts_for_anchor`
- `attempts_since`
- `commitment_tables_present`
- `commitments_covering_items`
- `events_for`
- `head_targets_for`
- `surprise_factors`
- `versions_for`

## Internal implementation anchors

- `_in_clause(ids: list[str]) -> str` ([source](../../../../../../../src/learnloop/db/stores/intent_reads.py), line 48)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/intent/recall_targets|learnloop.scheduling.intent.recall_targets]] — imports `module`; statically calls `attempts_for_anchor`
- [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]] — imports `module`; statically calls `commitment_tables_present`, `commitments_covering_items`, `events_for`, `head_targets_for`, `versions_for`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `module`; statically calls `attempts_since`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/intent/recall_targets|learnloop.scheduling.intent.recall_targets]], [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]], [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_intent_codex_review.py](../../../../../../../tests/test_intent_codex_review.py) — imports consumer [[Reference/Modules/learnloop/scheduling/intent/recall_targets|learnloop.scheduling.intent.recall_targets]]
- [tests/test_intent_recall_targets.py](../../../../../../../tests/test_intent_recall_targets.py) — imports consumer [[Reference/Modules/learnloop/scheduling/intent/recall_targets|learnloop.scheduling.intent.recall_targets]]
- [tests/test_curriculum_c0b_landing.py](../../../../../../../tests/test_curriculum_c0b_landing.py) — imports consumer [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]]
- [tests/test_intent_goal_deadline.py](../../../../../../../tests/test_intent_goal_deadline.py) — imports consumer [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]]
- [tests/test_intent_resolution.py](../../../../../../../tests/test_intent_resolution.py) — imports consumer [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]]
- [tests/test_reader_followups.py](../../../../../../../tests/test_reader_followups.py) — imports consumer [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]]
- [tests/ad23_fakes.py](../../../../../../../tests/ad23_fakes.py) — imports consumer [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]]
- [tests/intent_fakes.py](../../../../../../../tests/intent_fakes.py) — imports consumer [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]]
- [tests/test_ad23_intent_compose.py](../../../../../../../tests/test_ad23_intent_compose.py) — imports consumer [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]]
- [tests/test_ad23_inversion.py](../../../../../../../tests/test_ad23_inversion.py) — imports consumer [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]]
- [tests/test_ad23_pool_membership.py](../../../../../../../tests/test_ad23_pool_membership.py) — imports consumer [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]]
- [tests/test_intent_codex_rereview.py](../../../../../../../tests/test_intent_codex_rereview.py) — imports consumer [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/intent_reads.py](../../../../../../../src/learnloop/db/stores/intent_reads.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
