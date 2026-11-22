---
title: "learnloop.db.stores.intent_reads"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/intent_reads.py"
source_paths:
  - "src/learnloop/db/stores/intent_reads.py"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

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

- [[Reference/Modules/learnloop/daily_plan/check_delivery|learnloop.daily_plan.check_delivery]] — imports `module`; statically calls `commitment_tables_present`, `events_for`, `head_targets_for`, `versions_for`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `module`; statically calls `attempts_since`
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

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/check_delivery|learnloop.daily_plan.check_delivery]], [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]], [[Reference/Modules/learnloop/scheduling/intent/recall_targets|learnloop.scheduling.intent.recall_targets]], [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]], [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_check_credit_activation.py](../../../../../../../tests/test_check_credit_activation.py) — imports consumer [[Reference/Modules/learnloop/daily_plan/check_delivery|learnloop.daily_plan.check_delivery]]
- [tests/test_check_delivery.py](../../../../../../../tests/test_check_delivery.py) — imports consumer [[Reference/Modules/learnloop/daily_plan/check_delivery|learnloop.daily_plan.check_delivery]]
- [tests/causal_cold_outcomes_helpers.py](../../../../../../../tests/causal_cold_outcomes_helpers.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]]
- [tests/diagnosis_journey_helpers.py](../../../../../../../tests/diagnosis_journey_helpers.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]]
- [tests/remediation_cold_retry_helpers.py](../../../../../../../tests/remediation_cold_retry_helpers.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]]
- [tests/test_causal_attribution_p0.py](../../../../../../../tests/test_causal_attribution_p0.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]]
- [tests/test_causal_attribution_p2.py](../../../../../../../tests/test_causal_attribution_p2.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]]
- [tests/test_causal_factor_deferral.py](../../../../../../../tests/test_causal_factor_deferral.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]]
- [tests/test_causal_orchestrator.py](../../../../../../../tests/test_causal_orchestrator.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]]
- [tests/test_causal_p2_acceptance.py](../../../../../../../tests/test_causal_p2_acceptance.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]]
- [tests/test_cold_retry_reschedule.py](../../../../../../../tests/test_cold_retry_reschedule.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]]
- [tests/test_coldness_receipt.py](../../../../../../../tests/test_coldness_receipt.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/intent_reads.py](../../../../../../../src/learnloop/db/stores/intent_reads.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
