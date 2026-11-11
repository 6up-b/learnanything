# Refactor T1: test files stop importing each other

A step queued after arc B's close (owner, Nov 10: "since in practice agents have been running far longer test suites
we should move some of the test fixtures into helper/assistant modules"). Branch `refactor/t1-test-helpers`, based on
main `c3a940057c` (arcs A and B closed).

**Result.** 571 files under `tests/` imported from 372 `test_*.py` modules: 1,486 importer-module pairs, 3,931
imported names (the A6 record counted 1,471). Now 4 pairs remain, all on a ratchet allowlist with reasons. What other
files took from a test file (1,431 names, plus the 414 definitions those reach, 45 of them fixtures) now lives in
`tests/<name>_helpers.py`, one per donor (372 new modules). Over all 1,287 `src` modules, the median depth-1 selection
from `scripts/affected_tests.py` drops from 190 test files and 1,684 serial test seconds to 118 files and 1,076 s
(36% less; about 3 minutes at `-n 6` instead of 4.7). Collected node ids are identical. The new guard,
`tests/test_test_layout.py`, fails on a new test-to-test import.

## Why it mattered

A6's selector walks through a test module at no cost, because a test importing another for its fixtures depends on
everything that module imports (the missed selections were real: `refactor-a6.md`, review fix 3). So a fixture
module was as wide as its whole test file: `test_source_inventory`, imported by 69 files, made each of them a
dependant of the inventory runner, the role authority, the exam profile and the rest, though they used only `_persist`
and a few builders. A6 named the remedy, narrower fixture modules rather than a cheaper rule, and T1 is that remedy.
A helper module copies only the imports its own definitions use.

## Before and after

Same script both times (`docs/reviews/artifacts/refactor-t1/t1_measure.py`): `affected_tests.select([module],
depth=1)` on a fixed sample, test ids per file from `pytest --collect-only -q`, serial seconds from one whole-suite
serial JUnit (`refactor-measures/serial.xml`, Nov 9, used for both columns, so the seconds compare like with like but
are estimates).

| Module | Test files | Test ids | Serial test s |
|---|---:|---:|---:|
| `learnloop/router/mixture.py` | 126 → 110 | 1,934 → 1,751 | 2,354 → 2,274 |
| `learnloop/daily_plan/engine.py` | 388 → 334 | 7,844 → 7,141 | 3,841 → 3,668 |
| `learnloop/figures/prefetch.py` | 116 → 70 | 1,856 → 1,347 | 1,406 → 724 |
| `learnloop/attempts/grading.py` | 1,011 → 973 | 25,393 → 25,004 | 5,408 → 4,979 |
| `learnloop/diagnosis/followups.py` | 302 → 247 | 6,141 → 4,861 | 2,356 → 2,082 |
| `learnloop/db/stores/daily_plans.py` | 380 → 302 | 6,929 → 5,923 | 3,747 → 3,436 |
| `learnloop_sidecar/handlers/daily_plan.py` | 619 → 531 | 11,546 → 10,282 | 3,321 → 2,772 |
| `learnloop_mobile/host.py` | 32 → 28 | 652 → 558 | 705 → 629 |
| `learnloop/reader/reader_dialogue.py` | 368 → 241 | 15,028 → 13,280 | 2,552 → 1,582 |
| `learnloop/teacher/service.py` | 552 → 488 | 10,049 → 9,253 | 3,613 → 2,880 |
| `learnloop/provenance.py` | 887 → 847 | 15,444 → 14,967 | 5,865 → 5,755 |
| `learnloop/ingest/resolution.py` | 206 → 151 | 3,730 → 2,672 | 1,362 → 816 |

Every `src` module (1,287 that select rather than fall back to the whole suite), depth 1:

| | Median | 75th percentile | 90th percentile |
|---|---:|---:|---:|
| Test files | 190 → 118 | 441 → 334 | 725 → 648 |
| Test ids | 4,087 → 2,582 | 9,101 → 7,410 | 18,815 → 17,709 |
| Serial test seconds | 1,684 → 1,076 | 3,286 → 2,772 | 4,572 → 4,077 |

Largest reverse fan-in before: `test_source_inventory` 69 importers, `test_source_set_synthesis` 29,
`test_km2_write_path` 22, `test_daily_plan_build` 22, `test_hint_h2b_review` 21, `test_ro4_objective_serving` 20.
After: `test_stuck_prompt` 2 (the base sequences' fallback), `test_surface_pool` 1, `test_reader_dialogue` 1.

Hubs barely move (`grading.py`, `provenance.py`): their reach is through `src` itself, which T1 does not touch. The
leaves and mid-level modules move most.

## What moved where

For each test file another file imported from (the donor), `docs/reviews/artifacts/refactor-t1/t1_move.py`:

1. **Seeds**: every name any `tests/*.py` imports from it (`from tests.test_x import ...`, function-local ones
   included, and the attributes read off `import tests.test_x as A` / `from tests import test_x as A`).
2. **Closure**: the top-level statements binding the seeds, plus every top-level definition they read at module
   level or as a global from a function or class body (`symtable`), transitively; annotations count, since
   dataclasses and `get_type_hints` resolve them against the module. Imports they need are copied, not moved.
3. **Refusals** (the plan stops): a closure reaching a `test_*` / `Test*` name, `pytestmark` or
   `pytest_generate_tests`; a name rebound at top level with readers between; a moved name declared `global`; a
   binding inside an `if`/`try`; a donor that patches its own globals (two, handled by hand below). Reviewed by hand:
   moved code naming `__file__`, `__name__`, `inspect`, `sys.modules` (five, all benign: `Path(__file__).parents[1]`
   from the same directory, `type(x).__name__`, `monkeypatch.setitem(sys.modules, ...)`).
4. **Write**: `tests/<donor without test_>_helpers.py` holds the moved statements verbatim in their order, with their
   comments and any section header whose whole section moved; the donor imports back every moved name it still
   reads and every moved fixture (`# noqa: F401`, used by parameter name), so each module's fixture set is unchanged
   and each fixture keeps its scope and autouse. Every importer's `tests.test_x` becomes `tests.x_helpers`.
5. **Re-exports**: 14 names an importer took from a donor that had itself imported them (`ITEM` from
   `test_held_grade_evidence`, really `test_route_rules_in_grader`'s) now come from the defining module
   (`t1_redirect.py`, 11 import statements); then `ruff --select F401 --fix` drops what the donors no longer use, and
   `t1_tidy.py` collapses the blank lines that left in their import blocks.

One helper per donor and not merged topic modules: the donors' private names collide (`_vault`, `_setup`, `CLOCK`
in dozens), so merging would rename fixtures and change tests, and a merged module imports the union of its parts,
which is what T1 removes. The name says the topic: `source_inventory_helpers`, `voi_stopping_helpers`. Largest:
`ad23_contract_helpers.py` (1,270 lines), then `reread_safety_helpers.py` (409).

By hand, in `t1_patches.py` (exact-pattern replacements):

- `test_plan_first_transport_offer_grants` patched `sys.modules[__name__]._DRAIN_HANG_GUARD_S` and
  `_DRAIN_STOP_GRACE_S`, which `Harness` (now in the helper) reads: the patches name the helper module.
- `test_rospeed_ad_link`'s sigmoid counter patched `sigmoid` in its own module for the landing code's copy (the
  `_old_*` functions, now in the helper): it patches the helper module.
- `tests/rw2b_fix10_base_sequence.py` and `rw2b_fix11_base_sequence.py` also run inside `git archive 7d4c5f4ce`'s tree,
  which has no helpers: they import `StuckFake` from `stuck_prompt_helpers` and fall back to `test_stuck_prompt` on
  `ModuleNotFoundError` (found by `test_reader_rw2b_fix10/11`, which failed until then).
- `tests/conftest.py` registers pytest's assert rewriting for `tests/*_helpers.py` (`register_assert_rewrite`, before
  any of them is imported). Moved asserts were rewritten in their test file; without it a failing one would report a
  bare `AssertionError` (73 helpers hold 122 asserts). No fixture, no autouse.

`scripts/affected_tests.py` is unchanged: a helper module was already free to pass through, and the test-module rule
still serves the allowlist. `tests/test_affected_tests.py`'s pass-through case used `test_stuck_prompt` →
`test_hint_h2b_review` → `test_workbench_help_kill_switch`, which no longer exists as test-to-test imports; it now
checks the leakage suite (a test module through another, at depth 0) and the same chain through `stuck_prompt_helpers`.

## The guard and its allowlist

`tests/test_test_layout.py`: any `tests/*.py` importing a `test_*` module in any form (absolute, relative,
`from tests import test_x`, function-local) fails, naming the file and line; an allowlist entry nothing needs fails
too; a third test feeds each form to the reader. Allowed, with the reason in the file:

| Importer | Imports | Why |
|---|---|---|
| `test_p2_leakage_suite` | `test_reader_dialogue` | reruns a track test function under a private alias, the one named place for every leakage guard; moving it would move the test |
| `test_p2_leakage_suite` | `test_surface_pool` | the same, two functions |
| `rw2b_fix10_base_sequence` | `test_stuck_prompt` | the fallback inside the archived base tree |
| `rw2b_fix11_base_sequence` | `test_stuck_prompt` | the same |

## Reproducing it

`docs/reviews/artifacts/refactor-t1/pipeline.sh <T1 commit>` on a clean checkout of the base resets `tests/`, moves,
redirects, prunes, applies the patches and takes `test_test_layout.py` and `test_affected_tests.py` from the T1
commit. Run in a scratch worktree of `c3a940057c`, its `tests/` differed from the branch only in blank lines inside 34
import blocks the branch had not tidied yet; the branch took the pipeline's output, so the committed `tests/` is
exactly what the pipeline writes. If a
parallel step lands first with edits to a donor, rerunning the pipeline on the new base is cheaper than resolving
conflicts by hand; the figure wait-estimate step's tree touches 14 donors (`test_route_rules_in_grader`,
`test_required_method_grading`, `test_teacher_te1_successor`, `test_batch3_landing`, ...) and 23 files where only an
import path changes.

## Proofs

- **Collect-only.** `pytest --collect-only -q tests`, then with `-m "not arc_close"` and `-m arc_close`, same flags,
  before (`c3a940057c`) and after: sorted node ids identical in all three, but for the guard's three new ids (31,256
  → 31,259; landing 31,196 → 31,199; arc_close 60 → 60). `scripts/check_gate_partition.py`: 31,259 = 31,199 + 60.
- **Tests.** Every test file whose text changed, 731 files in 4 batches at `-n 6 -m "not arc_close"`: 12,865 passed,
  49 skipped, 11 xfailed, 4 failed: the two RW2b base runs (fixed above, then passed), the guard (it read the base
  sequences while their fallback was being added; passes since), and
  `test_te3a_lesson_opportunity::test_a_lesson_raises_the_prediction_and_never_evidence_or_mastery` (only an
  import path in another function of that file changed; 6/6 alone; a load-sensitive flake, not checked on the base).
  Then 33 files (the source guards that scan `tests/` and are not among them, both RW2b files, the guard,
  `test_affected_tests`, the two hand-patched donors): 8,937 passed. The `arc_close` tests in the changed files
  (`test_evsi_multisim`, `test_ro5_calibration`, `test_ro6_tail_data`, `test_rofu_weeks`): 4 passed. No full suite.
- `uv run ruff check`, `uv run lint-imports --no-cache` (43 kept), the four vault validators: pass.

## Landing note (orchestrator)

T1 was first built on c3a940057c (tip ec1bcbc79f; its landing lane passed 31,085 / 0 failed). The figure
wait-estimate successor landed first (b15659a054) and edited many of the same test files, so the move was
rerun on b15659a054 with `pipeline.sh c86ddf5106` instead of merged: the same 372 donors and 1,845 moved names,
imports rewritten in 698 files, and `pytest --collect-only` identical to b15659a054's apart from the guard's
3 ids (31,284 to 31,287). The tables above were measured on c3a940057c.
