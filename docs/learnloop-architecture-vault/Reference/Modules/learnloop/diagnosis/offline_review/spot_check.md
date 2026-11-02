---
title: "learnloop.diagnosis.offline_review.spot_check"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/offline_review/spot_check.py"
source_paths:
  - "src/learnloop/diagnosis/offline_review/spot_check.py"
source_commit: "2d7c4948399efdc96c3c60d7379da37bc90a9e3d"
source_commit_timestamp: "2026-10-14T20:18:37-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.offline_review"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.offline_review.spot_check module"
  - "src/learnloop/diagnosis/offline_review/spot_check.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-offline-review"
---

# `learnloop.diagnosis.offline_review.spot_check`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.offline_review.spot_check` exists within [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] to own the behavior summarized by its module contract: The optional owner spot-check (Slice 1 §12.1 "What the spot-check screens show").

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/offline_review/spot_check.py](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py) |
| Source lines | 482 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2d7c4948399efdc96c3c60d7379da37bc90a9e3d` |
| Commit timestamp | `2026-10-14T20:18:37-04:00` |

## Public API

- `build_spot_check_plan(run_dir: Path, vault: LoadedVault, *, seed: int, max_items: int=MAX_ITEMS) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 84) — The ordered screens for up to ``max_items`` stratified items (seeded).
- `render_screen(screen: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 230) — Terminal text for one screen.
- `start_or_resume_session(run_dir: Path, vault: LoadedVault, *, seed: int, new: bool=False, max_items: int=MAX_ITEMS) -> tuple[str, list[dict[str, Any]], int]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 259) — The open session (resumed at its position) or a new one.
- `advance_session(run_dir: Path, session_id: str, position: int, *, finished: bool=False) -> None` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 277)
- `receipt_identity(repository: Repository, attempt_id: str, *, view: Mapping[str, Any] | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 315) — The identity of an attempt's stored joint diagnosis as one database shows it.
- `record_diagnosis_screen(run_dir: Path, *, session_id: str, screen: Mapping[str, Any], ratings: Mapping[str, str], best: str | None, vault_repository: Repository | None=None, wrong_repairs: Mapping[str, str] | None=None) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 386) — ``ratings`` maps option label -> tap; ``best`` is a label, "none" or None (skip).
- `record_links_screen(run_dir: Path, *, session_id: str, screen: Mapping[str, Any], verdicts: Sequence[str | None]) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 425)
- `record_grade_screen(run_dir: Path, *, session_id: str, screen: Mapping[str, Any], choice: str | None) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 441) — ``choice`` is a grade label ("Grade 1"/"Grade 2"), "not_sure" or None (skip).
- `export_judgments(run_dir: Path) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 458) — All review_judgments as JSON-ready rows (ids and verdicts, no text).

### Module constants

- `SPOT_CHECK_VERSION` ([src/learnloop/diagnosis/offline_review/spot_check.py](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 54)
- `MAX_ITEMS` ([src/learnloop/diagnosis/offline_review/spot_check.py](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 55)
- `MAX_PLANTED` ([src/learnloop/diagnosis/offline_review/spot_check.py](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 56)
- `DIAGNOSIS_TAPS` ([src/learnloop/diagnosis/offline_review/spot_check.py](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 57)
- `LINK_TAPS` ([src/learnloop/diagnosis/offline_review/spot_check.py](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 58)
- `GRADE_TAPS` ([src/learnloop/diagnosis/offline_review/spot_check.py](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 59)

### Explicit exports

`__all__` declares:

- `DIAGNOSIS_TAPS`
- `GRADE_TAPS`
- `LINK_TAPS`
- `MAX_ITEMS`
- `SPOT_CHECK_VERSION`
- `advance_session`
- `build_spot_check_plan`
- `receipt_identity`
- `export_judgments`
- `record_diagnosis_screen`
- `record_grade_screen`
- `record_links_screen`
- `render_screen`
- `start_or_resume_session`

## Internal implementation anchors

- `_run_id(run_dir: Path) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 62)
- `_scratch(run_dir: Path) -> Path` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 66)
- `_rows(run_dir: Path, table: str, *, order_by: str='rowid', **where: Any) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 70)
- `_answer(run_dir: Path, target: Mapping[str, Any], planted: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 75)
- `_record(run_dir: Path, *, session_id: str, screen: str, task: str, subject_kind: str, subject_id: str, verdict: str, other_kind: str | None=None, other_id: str | None=None, detail: Mapping[str, Any] | None=None) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 282)
- `_arm_of(run_dir: Path, diagnosis_id: str) -> tuple[str | None, str | None]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 303)
- `_hash(value: Any) -> str` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 311)
- `_adjudicate_arm_a(vault_repository: Repository | None, attempt_id: str, rating: str, repair_md: str | None, displayed: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py), line 336) — Map a tap on arm (a) to a full-authority adjudication, when one exists.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]] — imports `advance_session`, `export_judgments`, `record_diagnosis_screen`, `record_grade_screen`, `record_links_screen`, `render_screen`, `start_or_resume_session`; statically calls `advance_session`, `export_judgments`, `record_diagnosis_screen`, `record_grade_screen`, `record_links_screen`, `render_screen`, `start_or_resume_session`
- [[Reference/Modules/learnloop/diagnosis/offline_review/links|learnloop.diagnosis.offline_review.links]] — imports `SPOT_CHECK_VERSION`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/diagnosis_review|learnloop.db.stores.diagnosis_review]] — imports `insert_review_row`, `review_rows`, `update_spot_check_session`; calls `insert_review_row`, `review_rows`, `update_spot_check_session`
- [[Reference/Modules/learnloop/diagnosis/diagnosis_adjudication|learnloop.diagnosis.diagnosis_adjudication]] — imports `append_diagnosis_adjudication`, `diagnosis_snapshot`; calls `append_diagnosis_adjudication`, `diagnosis_snapshot`
- [[Reference/Modules/learnloop/diagnosis/offline_review/judge|learnloop.diagnosis.offline_review.judge]] — imports `judge_view`; calls `judge_view`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `MAIN_ARMS`, `RUN_FILE`, `SCRATCH_FILE`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `VaultHistoryStore`; calls `VaultHistoryStore`
- [[Reference/Modules/learnloop/diagnosis/split/legacy_view|learnloop.diagnosis.split.legacy_view]] — imports `stored_legacy_view`; calls `stored_legacy_view`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `presented_prompt`; calls `presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `hashlib`, `json`, `pathlib`, `random`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]], [[Reference/Modules/learnloop/diagnosis/offline_review/links|learnloop.diagnosis.offline_review.links]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_diagnose_review.py](../../../../../../../tests/test_diagnose_review.py) — direct import
  - `test_an_owner_verdict_never_lands_on_a_receipt_the_owner_did_not_see`
  - `test_spot_check_hides_labels_and_is_deterministic`
  - `test_spot_check_routes_verdicts_and_resumes`

## Modification guidance

- Change spot check policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/offline_review/spot_check.py](../../../../../../../src/learnloop/diagnosis/offline_review/spot_check.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
