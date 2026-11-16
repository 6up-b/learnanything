# L2a: reading-request store pilot

Base: `a6c6c6fcc4`, branch `refactor/l2a-reading-requests`. Uncommitted implementation; landing gate belongs to the orchestrator.

Moved the reading-request group to `src/learnloop/db/stores/reading_requests.py`, with `ReadingRequestStoreMixin` as Repository's eighth, last base. Read and followed `session_ownership.py` and `collection.py`: future annotations, ordinary imports, implicit unannotated `self`, and `self.connection()` supplied by Repository. The module docstring names the request and its three tables. No call sites changed, including the cross-feature extraction transaction's `self._record_reading_request_for_extraction(...)`.

The tip contains **nine method definitions**, the alias and SQL constant (eleven class members), plus the module helper. The map's “11 methods / 192 definition lines” does not match this tip: 192 is the total removed text, including comments and blank lines. All explicitly requested members moved; none was left behind. The supplied `l2-map-work/` directory exists but is empty, so its TSV assignment and patch map could not be read. Sections 5–6 and the pilot paragraph of `l2-map-2026-11-16.txt` were read; source membership and patch sites were checked directly.

All scratch scripts/logs are under:

```text
/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/73b37aee-2550-41c4-88a8-8730b0f3c0c0/scratchpad/refactor-l2a/
```

## Proof 1: AST and exact removal

`prove_move.py`, against `git show HEAD:src/learnloop/db/repositories.py` (positions ignored), printed:

```text
AST identical: _READING_REQUEST_UPSERT
AST identical: record_reading_request
AST identical: set_source_wanted_reading
AST identical: _record_reading_request_for_extraction
AST identical: pending_reading_request
AST identical: settle_reading_request
AST identical: fail_reading_request
AST identical: defer_reading_request
AST identical: pending_reading_requests
AST identical: due_reading_requests
AST identical: reading_request_unsettled
AST identical: _reading_request
Text identity: 178 group lines + 14 helper lines removed verbatim; only import/base added; no other repository edits.
AST identity: all remaining Repository members unchanged.
```

The script also compares both moved text blocks verbatim with the new module and reconstructs the complete expected repository text. `_reading_request` had only two callers, both in this group, so it moved without a facade re-export or back-import.

## Proof 2: surface, descriptors, globals and metadata

`capture_surface.py` ran through the supplied `py.sh python` **before editing**, then again at the tip. `surface_base.json` and `surface_tip.json` contain the full sorted names and per-member metadata. `prove_move.py` printed:

```text
Surface base=tip: len(dir)=1055 sha256=9640e2da96c81c2fe9cbead3009b895eb8c1e557c147765a23b5b76955b0ac7d alias_identity=True; all descriptor types unchanged.
MRO: no moved-name collisions; old bases keep their order; Repository.connection override unchanged.
Globals: utc_now_iso, Clock, sqlite3, Any are identical objects from the same imports.
Patched-module hazards used: []; back-imports to repositories: [].
```

The hash is SHA-256 of newline-joined `sorted(dir(Repository))`; the lists themselves were also compared. The constant has type `str` and no `__qualname__`/`__module__`. For each remaining row below, the module changes from `learnloop.db.repositories` to `learnloop.db.stores.reading_requests`. Qualnames change from `Repository.<suffix>` to `ReadingRequestStoreMixin.<suffix>`:

| Member | Type, unchanged | Qualname suffix |
| --- | --- | --- |
| record_reading_request | function | record_reading_request |
| set_source_wanted_reading | function | record_reading_request |
| _record_reading_request_for_extraction | classmethod | _record_reading_request_for_extraction |
| pending_reading_request | function | pending_reading_request |
| settle_reading_request | function | settle_reading_request |
| fail_reading_request | function | fail_reading_request |
| defer_reading_request | function | defer_reading_request |
| pending_reading_requests | function | pending_reading_requests |
| due_reading_requests | function | due_reading_requests |
| reading_request_unsettled | function | reading_request_unsettled |

Searched `src/`, `tests/`, `scripts/` and `docs/learnloop-architecture-vault/_scripts/` for `__module__`, `__qualname__`, `getsource`, `getsourcelines` and `getsourcefile`; reviewed the matches (`introspection_refs.txt`). No consumer reads this metadata for the moved members. Generic metadata readers concern model/schema types, handlers, AD operations or thread diagnostics. The whole-module source guard in `test_p0_projection_cutover.py:316` checks `grading_evidence` writers; this move contains none of those. Other literal repository-path guards cover unrelated methods/tokens and need no changes.

## Proof 3: patches

Every test patch targeting a moved member is on Repository, not its module:

| Site | Target/expansion |
| --- | --- |
| tests/test_reading_request_sweep.py:103 | loop at :100: due_reading_requests and pending_reading_requests |
| tests/test_reading_request_sweep.py:181, :185 | settle_reading_request direct assignment and restoration |
| tests/test_reading_request_sweep.py:259 | pending_reading_request |
| tests/test_reading_request_sweep.py:397 | pending_reading_requests |
| tests/test_reading_hardening_review_fixes.py:63 | helper used at :96, parametrized at :83: settle_reading_request and pending_reading_request |
| same helper, calls at :128, :158, :200 | settle_reading_request at each call |
| tests/test_reading_hardening_review_fixes.py:267, :297 | fail_reading_request at each site |

No additional `mock.patch` sites or module patches target moved names. Searches included helper/loop expansion and direct assignments. The currently patched facade globals remain `connect`, `new_ulid`, `COLLECTION_VERSION`, `create_or_attach_current` and `recurrence_key`; none occurs as a loaded name in the moved ASTs. No facade patch replaces `utc_now_iso`, `Clock`, `Any`, `sqlite3` or `_reading_request`. Patches to shared `SystemClock.now`/sqlite3 objects still affect the same imported objects.

`prove_patches.py` printed a success line for each of the ten callable names (nine definitions plus alias), then this summary:

```text
Patch probes: 10/10 callable overrides effective and restored; 1/1 SQL constant override effective.
Direct assignment/restoration: effective; final alias identity: True.
```

The existing tests at every site above passed in the affected-file run, exercising their real call paths.

## Inventories

- Added the new file to `tests/test_architecture.py::REGISTERED_SQL_OWNERS`; no behavioral assertion weakened. It writes request fields in `source_auto_build_state` and reads `source_extraction_runs`/`source_revisions`.
- Searched table references and owner registries in `src/` and `tests/`, plus literal `repositories.py` references. `table_roles.py` still classifies those tables as WORKFLOW, WORKFLOW and RAW_LEDGER; the derived-table replayer registry has no ownership entry to move for them.
- Ran `py.sh python tests/test_structure_ratchets.py --write` (the advertised writer, using the binding wrapper instead of `uv run`). It excludes untracked files. `check_inventories.py` then used the same writer/current functions with the new store included in memory, without staging anything. All eight actual totals are unchanged: 143, 249, 46, 35, 35, 72, 2371, 184, in golden order. Only per-file comment ownership changes: repositories 10→9; new store 0→1. No gate threshold raised or spuriously lowered. Store Python files: **55→56**.
- `module_generate.py` discovers all source files and classifies `learnloop.db.*` as infrastructure / ACTIVE automatically, so it needs no new entry. Updated `db_generate_reference.py::repository_methods_by_table` to follow imported Repository bases, preserving the moved table/method inventory and including the seven existing mixins. An isolated execution of just that function's AST retained every previous mapping; the three affected tables retain exactly 12, 10 and 9 method/helper mappings. No generator was run; generated `Reference/` notes are untouched.
- Inspected all 15 import-linter contracts mentioning `learnloop.db`, including infrastructure/domain boundaries and frozen deferred-cycle exemptions. No contract/exemption changes needed: the new store imports only stdlib, typing and `learnloop.clock`.
- `scripts/refactor_measures.py::repository_methods` remains a direct-definition count (915→906), not a public-surface count. It was not changed; the full dir proof establishes the unchanged interface. Make that measure inheritance-aware before interpreting it across further splits.

## Checks

In commands below, `S` means the absolute scratch directory above; every tool used the supplied wrapper. Tests ran one command at a time, with explicit paths and at most four workers.

```text
$S/t.sh tests/test_structure_ratchets.py tests/test_architecture.py tests/test_test_layout.py tests/test_identity_pins.py tests/test_registry_audit.py -q -n 4
332 passed in 36.23s

$S/t.sh tests/test_apply_recovery.py tests/test_architecture.py tests/test_reading_hardening_2_fixes.py tests/test_reading_hardening_review_fixes.py tests/test_reading_hardening_verify_fixes.py tests/test_reading_request_sweep.py tests/test_repository_scopes.py tests/test_ux_phase1_finish.py tests/test_ux_phase1_review_fixes.py tests/test_ux_phase1_round2_rereview.py -q -n 4 -m "not arc_close"
135 passed, 16 warnings in 53.30s

$S/t.sh tests/test_structure_ratchets.py -q -n 4
3 passed in 6.64s (after final golden update)

$S/py.sh ruff check
All checks passed!

$S/py.sh lint-imports --no-cache
Analyzed 1257 files, 14096 dependencies; 42 kept, 0 broken.
```

`select_reading_tests.sh` uses `rg -l` plus `test_repository_scopes.py`, sorts/deduplicates into text manifests and forms bash arrays in chunks of at most 60. Ten files selected, one chunk. The three prohibited hanging test files matched none of the selection and were not run. Warnings were multiprocessing fork deprecations. No test failures or sandbox-blocked checks occurred. The full suite/landing gate, arc-close tests and vault generation were not run. The absent map TSVs could not be verified. `.pytest_tmp` contains no `run-*` directories from these runs; no killed runs or cleanup were needed. `git diff --check` passed.

## What the pilot says about the rest of L2

- Mechanical: slice contiguous source text, move feature-only helper/constant/alias together, reproduce imports, add one last base, compare complete ASTs and exact residual text. This group needed no compatibility seam or transaction rewrite.
- Judgment: confirm exclusive helper use, global patch lookup, descriptor and alias behavior, MRO collisions, table-owner guards, metadata/source consumers and generator inventories. The empty map directory and incorrect method count required source verification.
- Time: approximately ten minutes including discovery, implementation, proofs, inventory work and reporting; test wall times were 36.23s + 53.30s + 6.64s. The physical edit is a small part of the work; budget roughly 15–30 minutes for another similarly isolated group with its verification.
- A script can consume group assignments, preserve exact definition/decorator spans plus constants/aliases/helpers, generate imports and mixin/base edits, produce AST/residual-text proofs, capture isolated before/after surfaces and select affected tests. It should flag patched globals, shared helpers, owner registries, source guards and direct-only measures for review.
- The recipe does not yet fit methods using patched facade globals (connect, new_ulid, create_or_attach_current, recurrence_key, especially the value COLLECTION_VERSION), shared facade helpers that would create cycles, or cross-feature transactions whose ownership cannot follow one table family. Those need a separately justified compatibility seam, neutral helpers, retained owners or an explicit transaction design; they cannot be resolved by this pilot's slicing alone.
