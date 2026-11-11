---
title: "learnloop.evsi_calibration.eedi"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/evsi_calibration/eedi.py"
source_paths:
  - "src/learnloop/evsi_calibration/eedi.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.evsi_calibration"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.evsi_calibration.eedi module"
  - "src/learnloop/evsi_calibration/eedi.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-evsi-calibration"
---

# `learnloop.evsi_calibration.eedi`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.evsi_calibration.eedi` exists within [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] to own the behavior summarized by its module contract: Read the two Eedi releases the calibration harness uses (no network here).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/evsi_calibration/eedi.py](../../../../../../src/learnloop/evsi_calibration/eedi.py) |
| Source lines | 333 |
| Owning package | [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class EediQuestion` ([source](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 42) — One 2024 question with its distractor labels.
  - `distractors(self) -> tuple[str, ...]` (line 55; public)
  - `options_for(self, misconception_id: str) -> tuple[str, ...]` (line 58; public)
- `class EediBank` ([source](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 67) — The 2024 question bank: questions, misconception names, provenance.
  - `by_subject(self) -> dict[int, list[EediQuestion]]` (line 75; public)
- `load_eedi_2024(directory: Path) -> EediBank` ([source](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 113) — Read ``train.csv`` and ``misconception_mapping.csv`` from ``directory``.
- `class NeuripsResponses` ([source](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 167) — Answer arrays of one 2020 task, aligned by row (one row per answer).
  - `rows(self) -> int` (line 185; public)
- `load_neurips_2020(directory: Path, *, task: str='1_2', cache_dir: Path | None=None, with_dates: bool=False) -> NeuripsResponses` ([source](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 274) — Load one 2020 task's answers (cached as ``.npz`` in ``cache_dir``).
- `option_index(option: str) -> int` ([source](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 332)

### Module constants

- `OPTIONS` ([src/learnloop/evsi_calibration/eedi.py](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 33)
- `_OPTION_INDEX` ([src/learnloop/evsi_calibration/eedi.py](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 35)
- `_CACHE_VERSION` ([src/learnloop/evsi_calibration/eedi.py](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 38)

## Internal implementation anchors

- `_read_manifest(directory: Path) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 82)
- `_file_hash(paths: Sequence[Path]) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 93)
- `_misconception_id(raw: Any) -> str | None` ([source](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 103)
- `_subjects(directory: Path) -> tuple[dict[int, int], dict[int, str]]` ([source](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 189)
- `_leaf_subjects(directory: Path, task: str, levels: Mapping[int, int]) -> dict[int, int]` ([source](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 200)
- `_parse_answers(path: Path) -> dict[str, np.ndarray]` ([source](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 214)
- `_parse_dates(path: Path, answer_ids: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/eedi.py), line 240) — Minutes since the epoch for each of ``answer_ids`` (-1 when unknown).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]] — imports `load_eedi_2024`, `load_neurips_2020`; statically calls `load_eedi_2024`, `load_neurips_2020`
- [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]] — imports `EediBank`
- [[Reference/Modules/learnloop/evsi_calibration/families|learnloop.evsi_calibration.families]] — imports `EediBank`, `EediQuestion`, `OPTIONS`
- [[Reference/Modules/learnloop/evsi_calibration/family_data|learnloop.evsi_calibration.family_data]] — imports `NeuripsResponses`
- [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]] — imports `EediBank`, `EediQuestion`, `OPTIONS`
- [[Reference/Modules/learnloop/evsi_calibration/multisim|learnloop.evsi_calibration.multisim]] — imports `OPTIONS`
- [[Reference/Modules/learnloop/evsi_calibration/response_fit|learnloop.evsi_calibration.response_fit]] — imports `NeuripsResponses`
- [[Reference/Modules/learnloop/evsi_calibration/simulate|learnloop.evsi_calibration.simulate]] — imports `OPTIONS`
- [[Reference/Modules/learnloop/evsi_calibration/world|learnloop.evsi_calibration.world]] — imports `EediBank`, `EediQuestion`, `OPTIONS`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `csv`, `dataclasses`, `hashlib`, `json`, `pathlib`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]], [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]], [[Reference/Modules/learnloop/evsi_calibration/families|learnloop.evsi_calibration.families]], [[Reference/Modules/learnloop/evsi_calibration/family_data|learnloop.evsi_calibration.family_data]], [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/evsi_calibration_sim_helpers.py](../../../../../../tests/evsi_calibration_sim_helpers.py) — direct import
- [tests/test_evsi_calibration_sim.py](../../../../../../tests/test_evsi_calibration_sim.py) — direct import
  - `test_loaders_read_the_bank_and_the_answers`
- [tests/test_evsi_multisim.py](../../../../../../tests/test_evsi_multisim.py) — direct import
  - `test_the_multi_family_study_runs_every_episode_without_a_count_bound`
- [tests/test_evsi_single_family_unbounded.py](../../../../../../tests/test_evsi_single_family_unbounded.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains eedi within learnloop.evsi_calibration; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/evsi_calibration/eedi.py](../../../../../../src/learnloop/evsi_calibration/eedi.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
