---
title: "learnloop.substrate.compat.activity_backfill"
type: "module-reference"
status: "current"
refactor_status: "COMPAT"
version: "1.0.0"
source_path: "src/learnloop/substrate/compat/activity_backfill.py"
source_paths:
  - "src/learnloop/substrate/compat/activity_backfill.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.substrate.compat"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.compat.activity_backfill module"
  - "src/learnloop/substrate/compat/activity_backfill.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/compat"
  - "layer/domain"
  - "package/learnloop-substrate-compat"
---

# `learnloop.substrate.compat.activity_backfill`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.compat.activity_backfill` exists within [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] to own the behavior summarized by its module contract: Deterministic, idempotent backfill of the activity lineage substrate (§7.1).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/compat/activity_backfill.py](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py) |
| Source lines | 549 |
| Owning package | [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] |
| Architecture layer | `domain` |
| Refactor status | `COMPAT` |

> [!warning] Frozen compatibility boundary
> This live module is retained for old vaults. It is green but not a target for new feature growth.

## Public API

- `class BackfillReport` ([source](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py), line 59)
  - `as_dict(self) -> dict[str, Any]` (line 82; public)
- `substrate_began_at(repository: Repository) -> datetime | None` ([source](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py), line 99) — The instant the activity substrate existed from: the vault's first administration written live (the backfill's own are marked ``legacy_backfilled``), in the clock the vault's own rows are dated by.
- `answer_writer(attempt_type: str) -> str` ([source](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py), line 111) — The door that records an answer's grade record live: ordinary practice (``apply_attempt``'s grade channel, every type it applies), a probe's (``diagnostic``), or an exam's, where a sitting and an import are separate doors (their attempt types).
- `class SubstrateCutovers` ([source](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py), line 124) — When each writer of the substrate began recording, by the vault's stored facts (see the module docstring).
  - `answer_predates(self, attempt_type: str, recorded_at: str | None) -> bool` (line 134; public) — Whether an answer is history from before its writer recorded (backfilled; replay may record its grade).
  - `answer_before_its_writer(self, attempt_type: str, recorded_at: str | None) -> bool` (line 141; public) — History only by its writer's record: recorded after the vault's first live administration, before its writer's first live answer.
  - `writer_never_recorded(self, attempt_type: str) -> bool` (line 147; public) — The vault wrote the substrate live, but never an answer of this writer's.
  - `presentation_predates(self, recorded_at: str | None) -> bool` (line 152; public)
- `substrate_cutovers(repository: Repository) -> SubstrateCutovers` ([source](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py), line 158) — The writers' cutovers, read from the stored rows (before a backfill writes: its own rows never move them).
- `predates_substrate(recorded_at: str | None, began: datetime | None) -> bool` ([source](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py), line 170) — Whether a row recorded at ``recorded_at`` is history from before the substrate (see :func:`substrate_began_at`).
- `answers_without_grade_record(vault: LoadedVault, repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py), line 185) — Answers recorded after the substrate existed whose grade record (the one ``apply_attempt``'s grade channel writes) is incomplete: no observation, or an observation with no raw grade (the write failed after it minted the identity).
- `backfill_activity_substrate(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> BackfillReport` ([source](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py), line 233) — Backfill migration-065 tables from the vault + legacy SQL (§7.1 steps 1-4).

### Module constants

- `SITTING_ATTEMPT_TYPE` ([src/learnloop/substrate/compat/activity_backfill.py](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py), line 108)

## Internal implementation anchors

- `_purpose_for_attempt_type(attempt_type: str) -> str` ([source](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py), line 91)
- `_clock_at(iso: str | None) -> Clock` ([source](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py), line 226)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `SITTING_ATTEMPT_TYPE`, `answers_without_grade_record`; statically calls `answers_without_grade_record`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `answers_without_grade_record`, `backfill_activity_substrate`; statically calls `answers_without_grade_record`, `backfill_activity_substrate`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `substrate_cutovers`; statically calls `substrate_cutovers`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `evidence_reading_fixes_on`; calls `evidence_reading_fixes_on`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `parse_utc`; calls `FrozenClock`, `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/grading_epochs|learnloop.grading_epochs]] — imports `graded_more_than_once`; calls `graded_more_than_once`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `compile_assessment_contract`; calls `compile_assessment_contract`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `_CONSUMING_PURPOSES`, `_PURPOSE_TO_LEGACY_KIND`, `administration_snapshot_hash`, `canonical_hash`, `canonical_json`, `card_contract_hash`, `card_semantic_payload`, `fingerprint_of`, `resolve_legacy_item`, `surface_hash`, `surface_payload`; calls `administration_snapshot_hash`, `canonical_hash`, `canonical_json`, `card_contract_hash`, `card_semantic_payload`, `fingerprint_of`, `resolve_legacy_item`, `surface_hash`, `surface_payload`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]], [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]], [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_activity_backfill.py](../../../../../../../tests/test_activity_backfill.py) — direct import
  - `test_a_practice_answer_between_a_live_diagnostic_and_the_practice_writers_first_record_is_history`
  - `test_an_answer_whose_writer_never_recorded_live_is_reported_with_unknown_provenance`
  - `test_backfill_is_idempotent_on_fixture_copy`
  - `test_backfill_marks_unverifiable_for_missing_item`
  - `test_backfill_populates_substrate_from_fixture`
  - `test_backfill_render_once_per_shared_surface`
  - `test_diagnostic_probe_attempts_reuse_shared_surface_hash`
- [tests/test_evidence_reading_successor.py](../../../../../../../tests/test_evidence_reading_successor.py) — direct import
  - `test_r5_a_same_second_legacy_regrade_of_an_exam_answer_reaches_the_exam_channel`
- [tests/test_grade_resolution_pipeline.py](../../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_backfill_converts_probe_presentations_idempotently`
- [tests/test_rebuild_writes_no_grade_record.py](../../../../../../../tests/test_rebuild_writes_no_grade_record.py) — direct import
  - `test_a_rebuild_leaves_a_degraded_grade_unrecorded_and_doctor_repairs_it`
  - `test_a_regrade_is_an_explicit_revision_and_records_the_missing_grade`
  - `test_a_repaired_blind_grade_is_the_one_the_live_write_makes`
  - `test_a_sitting_answer_whose_own_grade_record_failed_stays_visible`
- [tests/test_replay_writes_no_ledger.py](../../../../../../../tests/test_replay_writes_no_ledger.py) — direct import
  - `test_history_from_before_the_substrate_is_backfilled_once`

## Modification guidance

- Change activity backfill policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- This is frozen old-vault compatibility code: do not extend it without an explicit compatibility decision and fixture-backed tests.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/compat/activity_backfill.py](../../../../../../../src/learnloop/substrate/compat/activity_backfill.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
