---
title: "learnloop.attempts.salience_firewall"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/salience_firewall.py"
source_paths:
  - "src/learnloop/attempts/salience_firewall.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.salience_firewall module"
  - "src/learnloop/attempts/salience_firewall.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.salience_firewall`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.salience_firewall` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Reading-signal / salience firewall (spec_p3_reader_integration §8.2, §15.4; design §C).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py) |
| Source lines | 228 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class SalienceEvidenceRejected(ValueError)` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 77) — Raised when a salience-only signal is fed into an evidence/belief API.
- `salience_payload(payload: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 81) — Stamp ``authority_class='salience_only'`` onto a reader/reading event payload.
- `is_salience_only(obj: Any) -> bool` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 115)
- `reject_salience(obj: Any, *, context: str='evidence_ingestion') -> None` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 119) — Hard reject: raise if ``obj`` carries salience-only authority.
- `proposal_priority_signal(events: list[Mapping[str, Any]]) -> dict[str, float]` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 131) — The ONE allowed downstream of salience (§8.2): reorder PROPOSAL priority only.
- `salience_projection_v1(events: list[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 156) — Versioned salience projector v1 (§8.2, design B step 9).

### Module constants

- `SALIENCE_ONLY` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 31)
- `DWELL_SEGMENT_MAX` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 35)
- `READING_EVENT_KINDS` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 40)
- `SALIENCE_PROJECTIONS` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 65)
- `SALIENCE_PROJECTOR_VERSION` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 146)
- `_DEPTH_SUGGEST_HIGHLIGHT_WEIGHT` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 151)
- `_DEPTH_SUGGEST_QUESTION_WEIGHT` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 152)
- `_DEPTH_SUGGEST_REVISIT_WEIGHT` ([src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py), line 153)

## Internal implementation anchors

- `_extract_authority_class(obj: Any) -> str | None` ([source](../../../../../../src/learnloop/attempts/salience_firewall.py), line 89) — Best-effort recovery of an authority class from a dict, an event row, or an object carrying a payload/metadata/draft.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `reject_salience`; statically calls `reject_salience`
- [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop/reader/reader_restoration|learnloop.reader.reader_restoration]] — imports `salience_payload`; statically calls `salience_payload`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `READING_EVENT_KINDS`, `SALIENCE_ONLY`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]], [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]], [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]], [[Reference/Modules/learnloop/reader/reader_restoration|learnloop.reader.reader_restoration]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_p3_journeys.py](../../../../../../tests/test_p3_journeys.py) — direct import
  - `test_arc_and_salience_heads_rebuild_deterministically`
- [tests/test_reader_authoring.py](../../../../../../tests/test_reader_authoring.py) — direct import
  - `test_coach_response_is_corpus_only_salience`
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
  - `test_real_reader_writes_carry_the_salience_firewall_stamp`
- [tests/test_reader_restoration.py](../../../../../../tests/test_reader_restoration.py) — direct import
  - `test_restoration_records_salience_exposure_and_cannot_be_evidence`
- [tests/test_salience_firewall.py](../../../../../../tests/test_salience_firewall.py) — direct import
  - `test_apply_attempt_chokepoint_rejects_salience`
  - `test_highlights_may_reorder_proposals_only`
  - `test_non_salience_input_is_not_rejected`
  - `test_reject_salience_hard_rejects_every_reading_signal`
  - `test_salience_payload_always_stamps_authority_class`
  - `test_salience_projection_dwell_is_bounded`
  - `test_salience_projection_v1_is_salience_only_and_rejected_as_evidence`

## Modification guidance

- Change salience firewall policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/salience_firewall.py](../../../../../../src/learnloop/attempts/salience_firewall.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
