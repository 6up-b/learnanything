---
title: "learnloop.diagnosis.split.provenance"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/provenance.py"
source_paths:
  - "src/learnloop/diagnosis/split/provenance.py"
source_commit: "79e939595fb556058069200a8e4fab83c6f8b390"
source_commit_timestamp: "2026-10-15T12:46:53-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.split"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.split.provenance module"
  - "src/learnloop/diagnosis/split/provenance.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.provenance`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.provenance` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: What a diagnosis read, recorded with it (spec_mcp_frontend_c1 §4.8).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/provenance.py](../../../../../../../src/learnloop/diagnosis/split/provenance.py) |
| Source lines | 614 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `79e939595fb556058069200a8e4fab83c6f8b390` |
| Commit timestamp | `2026-10-15T12:46:53-04:00` |

## Public API

- `class AttemptRead` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 109) — One attempt shown to the diagnoser.
- `class DiagnosisReads` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 119) — What a diagnosis context showed (see the module doc).
  - `join(self, *others: DiagnosisReads) -> DiagnosisReads` (line 133; public)
  - `title_map(self) -> dict[str, tuple[str, ...]]` (line 158; public) — ``{topic: every name it was shown as}``.
- `shown_titles(vault: Any, topics: Iterable[Any]) -> tuple[tuple[str, str], ...]` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 167) — ``(topic, its title)`` for each topic a context rendered by name, as the vault it rendered from holds it (codex review F2).
- `hypothesis_read(record: Any) -> DiagnosisReads` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 186) — A prior hypothesis record (``history.HypothesisRecord``) read.
- `registry_read(record: Any) -> DiagnosisReads` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 201) — A registry record (``history.RegistryRecord``) read.
- `repair_read(record: Any) -> DiagnosisReads` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 211) — A repair record (``history.RepairRecord``): its operator was written with its owning hypotheses, whose records are folded in.
- `attempt_read(attempt: Any, *, title: str | None=None) -> DiagnosisReads` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 219) — A history attempt (``history.HistoryAttempt``) shown, with its topic's name when the rendering showed one (``title``).
- `reads_of_context(*, current_attempt_id: str, current_item_id: str, current_learning_object_id: str, learning_object_ids: Iterable[str], attempts: Iterable[Any], hypotheses: Iterable[Any], registry: Iterable[Any], repairs: Iterable[Any], titles: Iterable[tuple[str, str]]=()) -> DiagnosisReads` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 229) — What an assembled context showed: the diagnosed attempt with its blind (or joint) grade, its item's question, rubric and reference solution, the neighbourhood's topics (``titles``: the names it showed them by), every history attempt rendered, and every prior hypothesis, registry…
- `class SnapshotEntries` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 265) — What each exported file serves (``relative path -> DiagnosisReads``), and each file's closed record frozen when the export was written (``records``, codex review F3: :func:`freeze_entries`).
  - `whole(self) -> DiagnosisReads` (line 274; public)
- `simple_command(command: str) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 326) — Whether ``command`` is one simple command (codex review F1): every character printable, no line break, quotes closed, and no shell syntax outside single quotes (no control operator such as ``&``, ``;`` or ``|``, no redirection, subshell, substitution, expansion or escape).
- `served_entries(entries: SnapshotEntries, opened: Sequence[str] | None) -> tuple[str, tuple[str, ...]]` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 416) — What the reported activity served: ``("unreported", ())``, ``("outside", every path)``, ``("whole", every path)`` or ``("entries", the paths)`` (see the module doc).
- `snapshot_reads(entries: SnapshotEntries, opened: Sequence[str] | None) -> DiagnosisReads` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 445) — The export entries the diagnoser's reported activity served (:func:`served_entries`).
- `snapshot_record(entries: SnapshotEntries, opened: Sequence[str] | None) -> Any` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 461) — The closed record of what the reported activity served: the records of the entries served, as frozen when the export was written (codex review F3), plus why it is incomplete (:func:`snapshot_reads`).
- `diagnosis_record(connection: Any, reads: DiagnosisReads) -> Any` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 484) — The diagnosis's closed write-time record, on the writer's connection: every attempt read under its pinned contract (with its grading folded in when a grader's output about it was shown), the items whose rubric and reference solution were read, the topics, and the recorded inputs…
- `frozen_record(store: Any, reads: DiagnosisReads) -> Any` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 548) — THE record of what a diagnosis context showed, frozen when the context is built (codex review F3): every contract, grading and derived text's record as it stands now, before the diagnoser runs, so a regrade while it runs never replaces the provenance of what it was shown.
- `freeze_entries(store: Any, entries: Mapping[str, DiagnosisReads]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 573) — Each export file's closed record, frozen when the export is written (codex review F3); :func:`snapshot_record` joins the ones served.

### Module constants

- `SNAPSHOT_UNREPORTED` ([src/learnloop/diagnosis/split/provenance.py](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 70)
- `GRADING_REPLACED` ([src/learnloop/diagnosis/split/provenance.py](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 73)
- `GRADING_UNIDENTIFIED` ([src/learnloop/diagnosis/split/provenance.py](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 76)
- `NOT_FROZEN` ([src/learnloop/diagnosis/split/provenance.py](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 78)
- `_READ_COMMANDS` ([src/learnloop/diagnosis/split/provenance.py](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 80)
- `_NAME_COMMANDS` ([src/learnloop/diagnosis/split/provenance.py](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 81)
- `_SHELLS` ([src/learnloop/diagnosis/split/provenance.py](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 82)
- `_UNQUOTED_SYNTAX` ([src/learnloop/diagnosis/split/provenance.py](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 86)
- `_DOUBLE_QUOTED_SYNTAX` ([src/learnloop/diagnosis/split/provenance.py](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 88)
- `_GLOB` ([src/learnloop/diagnosis/split/provenance.py](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 89)
- `_SED_PRINT` ([src/learnloop/diagnosis/split/provenance.py](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 91)
- `_READ_OPTIONS` ([src/learnloop/diagnosis/split/provenance.py](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 95)
- `SNAPSHOT_OUTSIDE` ([src/learnloop/diagnosis/split/provenance.py](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 313)

### Explicit exports

`__all__` declares:

- `GRADING_REPLACED`
- `GRADING_UNIDENTIFIED`
- `NOT_FROZEN`
- `SNAPSHOT_OUTSIDE`
- `SNAPSHOT_UNREPORTED`
- `AttemptRead`
- `DiagnosisReads`
- `RecordRead`
- `SnapshotEntries`
- `attempt_read`
- `diagnosis_record`
- `freeze_entries`
- `frozen_record`
- `hypothesis_read`
- `reads_of_context`
- `registry_read`
- `repair_read`
- `served_entries`
- `shown_titles`
- `simple_command`
- `snapshot_reads`
- `snapshot_record`

## Internal implementation anchors

- `_grader_text(attempt: Any) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 181)
- `_relative(root: Path, token: str) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 278) — ``token`` as an export path relative to ``root``, or None when it lies outside.
- `_names(entries: SnapshotEntries, token: str) -> tuple[str, set[str]] | None` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 293) — ``("file", {path})`` or ``("dir", {paths under it})`` for an export path, or None when the token names nothing in the export.
- `_outside(entries: SnapshotEntries, tokens: Iterable[str]) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 316)
- `_command_files(entries: SnapshotEntries, command: str, depth: int=0) -> set[str] | str` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 351) — The export files a reported command read; :data:`_WHOLE` when it cannot be accounted for (the whole export counts as read), or :data:`_OUTSIDE` when it names a path outside the export.
- `_read_attempts(reads: DiagnosisReads) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 521)
- `_replaced(shown: Mapping[str, str], now: Mapping[str, str], attempts: Iterable[str]) -> Any` ([source](../../../../../../../src/learnloop/diagnosis/split/provenance.py), line 525) — Incomplete for every attempt whose grading changed since the history read what it showed (``shown``: :meth:`VaultHistoryStore.grading_marks`, read in one snapshot with the payloads shown; ``now``: ``write_provenance.grading_marks``, read in one snapshot with the record), and for…

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `DiagnosisReads`, `reads_of_context`, `shown_titles`; statically calls `DiagnosisReads`, `reads_of_context`, `shown_titles`
- [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]] — imports `frozen_record`, `served_entries`, `snapshot_reads`, `snapshot_record`; statically calls `frozen_record`, `served_entries`, `snapshot_reads`, `snapshot_record`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `NOT_FROZEN`, `diagnosis_record`; statically calls `diagnosis_record`
- [[Reference/Modules/learnloop/diagnosis/split/snapshot|learnloop.diagnosis.split.snapshot]] — imports `DiagnosisReads`, `SnapshotEntries`, `attempt_read`, `freeze_entries`, `hypothesis_read`, `registry_read`, `repair_read`, `shown_titles`; statically calls `DiagnosisReads`, `SnapshotEntries`, `attempt_read`, `freeze_entries`, `hypothesis_read`, `registry_read`, `repair_read`, `shown_titles`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `GRADING`, `Inputs`, `UNIDENTIFIED_GRADING`, `WriteRecord`, `answer_inputs`, `attempt_statement_refs`, `closure`, `fold_topic_records`, `grading_mark`, `grading_marks`, `read_snapshot`; calls `WriteRecord`, `answer_inputs`, `attempt_statement_refs`, `closure`, `fold_topic_records`, `grading_mark`, `grading_marks`, `read_snapshot`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `pathlib`, `re`, `shlex`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]], [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]], [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]], [[Reference/Modules/learnloop/diagnosis/split/snapshot|learnloop.diagnosis.split.snapshot]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_chatgpt_plan_landing.py](../../../../../../../tests/test_chatgpt_plan_landing.py) — direct import
  - `test_a_snapshot_diagnosis_on_the_plan_records_what_it_served_with_its_row_and_forecasts`
- [tests/test_diagnosis_input_provenance.py](../../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
- [tests/test_learner_blindness_relax_codex_review.py](../../../../../../../tests/test_learner_blindness_relax_codex_review.py) — direct import
  - `test_an_earlier_workbench_trace_counts_its_item_and_leaves_the_record_incomplete`

## Modification guidance

- Change provenance policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/provenance.py](../../../../../../../src/learnloop/diagnosis/split/provenance.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
