# Refactor step M0: structure measures that cannot slip back

Branch `refactor/m0-structure-ratchets`, based on main `16a9e3fd48`. Proposed in
`refactor-strategy-v3-audit-2026-11-12.md` §2.3, §2.8 and §3. Not landed: the owner has not approved it. Nothing under
`src/` changes.

## What it adds

- `scripts/refactor_measures.py`: a `structure` group (JSON key `computed.structure`, a "Structure" table in the
  Markdown). One parse per file feeds both the old counts and the new ones. The command-line run sweeps files in up to 8 processes with the full `python_facts`; the test's `structure_sweep()` is serial and lean (see Runtime).
  The existing `computed` values are byte-identical to before (checked by diffing the JSON of the old and new script).
- `tests/goldens/structure.toml` and `tests/test_structure_ratchets.py`: a ratchet on measures a, b, d (three numbers),
  e, f and g. `python tests/test_structure_ratchets.py --write` regenerates the golden.
- The test loads the script by path (`importlib.util.spec_from_file_location`, as `test_refactor_measures.py`,
  `test_affected_tests.py`, `test_table_review.py` and `test_vault_report.py` already do). The script imports nothing
  from `tests/`, and the test imports nothing from `learnloop`: it reads tracked source.
- `CLAUDE.md` is not edited: its "## Commands" block has no line for the identity pins or the effective-defaults
  golden (both are only described under "## Tests"), so there is no pattern to mirror.

## Definitions, values at the tip, and the audit's numbers

All values are at this branch's tip (main `16a9e3fd48` plus M0). The audit measured at `e9a7733612`, before K3.5 and
D2b part 1 merged, so a difference of a few is code that moved, not a different method.

| | Measure and definition | Tip | Audit | Difference |
|---|---|---:|---:|---|
| a | Modules in the largest strongly connected component of the module import graph over the four packages in `src/`. Edges: every `import` / `from ... import` at any depth, function-local included; those under `if TYPE_CHECKING:` left out (its `else` kept). `from pkg import name` is an edge to `pkg.name` when that is a module, else to `pkg`. | 189 (166,736 lines; next components 36, 9, 8, 6) | 189 | none |
| b | Modules in any component of more than one module. | 286 | 286 | none |
| c | Edges `(module, target)` that exist only inside functions; modules with at least one. Reported only. | 2,839; 565 | 2,836; 564 | +3, +1: code moved since `e9a7733612` |
| d | In `src/learnloop`: packages (any first-level directory holding a tracked `.py` below it, `content/` included though it has no `__init__.py`); root modules (`*.py` beside the package `__init__.py`, without `__init__.py` and `__main__.py`); root modules not named `*_upgrade.py`. | 46; 78; 34 | 46; 80; 36 | the audit counted `__init__.py` and `__main__.py` as root modules; both are left out here (80 - 2, 36 - 2) |
| e | Functions (sync or async, any nesting) over 200 lines, the script's existing `functions_over_200_lines`. | 83 | n/a | reused, not new |
| f | Comment tokens (full-line and inline) whose text matches `STAGE_COMMENT` after cutting `noqa:` code lists. | 2,424 of 35,040 | 2,297 of 32,615 | see below |
| g | Tracked `tests/test_*.py` whose name matches `STAGE_TEST_NAME`. | 185 | 196 | see below |
| h | Attribute reads `datetime.now`, `datetime.utcnow`, `date.today`, `time.time` (a call or a bare reference) in `src` outside `learnloop/clock.py`; `time.monotonic` apart. Reported only. | 105 (70 / 0 / 1 / 34) in 62 modules; 224 monotonic | n/a | |
| i | Modules reachable from `learnloop.cli*` and `learnloop.tui*` but not from `learnloop_sidecar`, `learnloop_mobile`, `learnloop_mcp` (importing `a.b.c` also reaches `a` and `a.b`); lines are raw file lines. Reported only. | 241 modules, 92,399 lines; reached from none: 6 modules, 3,603 lines | 241, 92,381; 3,603 | +18 lines of code moved |
| j | `enabled` booleans: annotated `bool` fields in `config/schema.py` whose name contains `enabled`; effective config leaves: the `key = value` lines plus the `# key = null` lines of `tests/goldens/effective_defaults.toml`. Reported only. | 123; 1,189 (120 of them unset) | 123 | none (a plain `enabled` name alone gives 48) |

### f: why 2,424 and not 2,297

`STAGE_COMMENT` is, case-insensitively, `ruling(s)`, `ruled`, `codex`, `round N`, `fix round`, `landing(s)`, `landed`,
plus (case-sensitive) `F` or `R` with one or two digits, with an optional hyphen (`review F3`, `R12`). It is matched
against comment tokens only, so a docstring or string holding "round 2" does not count. Two differences from the
audit's rough regex explain the gap: the denominator counts inline comments too (the audit's 32,615 is the count of
lines starting with `#`, 32,630 now), and the F/R-number alternative is mine. I checked the F/R alternative on a
sample: `noqa: F403` is the false positive it had, which the `noqa:` cut removes; `F1` as a score would match, but the
sample of 25 had none. Treat the number as a ratchet baseline, not a precise count of history comments.

### g: why 185 and not 196

`STAGE_TEST_NAME` matches a name carrying a fix round (`fix_round4`, `fix10`, `fix_r5`), a review pass (`codex_review`,
`rereview`, `review_fixes`, `review_r3`), a final verification, a ruling, or a landing (`landing`, `close_fixes`). It
does not match a stage id alone (`test_ro4_value.py`, `test_te3b_offers.py`): a first draft that did gave 266, and those
files name the feature's owner while still checking one behaviour. The audit's regex is not on file; this one is
narrower in that way. Sample of the 185, every 14th: `test_ad1_codex_rereview_fixes.py`, `test_batch3_landing.py`,
`test_data_capture_landing_review.py`, `test_exam_protection_landing.py`, `test_figures_show_me_codex_review.py`,
`test_intent_codex_rereview.py`, `test_mobile_v2_rereview_fixes.py`, `test_reader_ca2_codex_review.py`,
`test_reader_recap_review_r2.py`, `test_reader_rw2b_fix6.py`, `test_reading_hardening_review_fixes.py`,
`test_ro6_codex_rereview.py`, `test_te3b_codex_review.py`, `test_ux_phase1_usability_round1.py`. Known doubtful
matches, kept: `test_e0_relabel_round.py` (a relabelling round is its subject). The golden lists all 185.

### Golden contents

`[ratchet]` holds the eight gated numbers. `[members]` holds the 189 component modules, the 78 root module names, the 83
long functions as `path name` (no line number, so editing above one does not move it) and the 185 test names; those let
a failure name what is new. `[stage_comments_by_file]` holds 495 files with their stage-comment counts so a failure can
name the files that gained some. The file is about 1,050 lines; it only changes when someone raises or lowers it.

## Proof

The test passes at the tip. Each scratch edit below was made, run, and reverted (nothing committed; a new file was
added with `git add -N` so `git ls-files` sees it, then removed).

Function-local import joining a new module to the largest component (a new `adaptive_difficulty/zz_probe_cycle.py`
that imports `claims`, plus a function in `claims.py` that imports it):

```
structure ratchet 'largest_import_component' rose: the largest import cycle (modules in the biggest strongly connected component of the import graph, function-local imports included, TYPE_CHECKING left out) is 190, the golden holds 189 (+1).
  joined the component:
    learnloop.adaptive_difficulty.zz_probe_cycle
structure ratchet 'modules_in_an_import_cycle' rose: modules in any import cycle is 287, the golden holds 286 (+1).
Two ways out: fix the code so the number does not rise, or raise tests/goldens/structure.toml in the same commit with the reason in the commit message (uv run python tests/test_structure_ratchets.py --write).
```

A function of 201 lines appended to `ids.py`:

```
structure ratchet 'functions_over_200_lines' rose: functions over 200 lines is 84, the golden holds 83 (+1).
  new long functions:
    src/learnloop/ids.py _probe_long
Two ways out: ... (same sentence)
```

A new root module `src/learnloop/zz_probe_root.py`:

```
structure ratchet 'first_level_root_modules' rose: root modules in src/learnloop is 79, the golden holds 78 (+1).
  new root modules:
    zz_probe_root
structure ratchet 'first_level_root_modules_not_upgrade' rose: root modules in src/learnloop not named *_upgrade.py is 35, the golden holds 34 (+1).
  new root modules:
    zz_probe_root
Two ways out: ... (same sentence)
```

`test_the_failure_message_names_what_is_new` checks the message format without the sweep. The import-cycle proof was rerun on the serial path after the change and names `learnloop.adaptive_difficulty.zz_probe_cycle` again.

## Runtime

- The test runs inside pytest-xdist workers in the landing gate, so its path starts no processes. `structure_sweep()`
  is serial: one `ast.parse` per file, the import and clock visitor, the long-function scan, and tokenizing only the
  files whose raw text matches `STAGE_COMMENT` anywhere (a file that never matches has no stage comment). It skips
  `python_facts`' other token-level counts. Its numbers equal the full run's (the JSON `computed.structure` of the
  command-line run is unchanged, and the golden did not move on `--write`).
- Serial wall time of `test_no_structure_number_rose_above_the_golden`: 6.6 s alone; 7.7 s inside `-n 4` with three
  other test files (`test_architecture`, `test_test_layout`, `test_effective_defaults_golden`), on this 32-core desktop.
  That is over the brief's 5 s and inside the relaxed 8 s; I added no further machinery.
- `scripts/refactor_measures.py` end to end keeps the process pool and the full `python_facts` (8.4 s, against 14.2 s
  before M0).
- A ratchet key missing from the golden's `[ratchet]` fails with a message saying so (it used to pass silently);
  `test_a_ratchet_key_missing_from_the_golden_fails` covers it.

## Open questions

1. The 5-second budget holds on this machine only because of the process pool. If a slower machine or a loaded `-n 8`
   run goes over, the cheapest cut is to skip tokenizing files with no `STAGE_COMMENT` match anywhere in their text; I
   did not do it because the comment-line total in the script's report would then need a second path.
2. Measure f counts inline comments and a wider vocabulary than the audit; if the owner wants the audit's figure to
   stay the baseline, say which regex it was and I will use it.
3. Measure g leaves out stage-id names. Whether a file named for its owner (`test_ro4_value.py`) should count is a
   judgment for the owner; including them would be 266 and the ratchet would hold the stage-id naming back too.
4. The golden carries the members, so raising it in a commit that adds one module rewrites a line in the list as well
   as the number. That is intended (the diff shows what was admitted), but it is a conflict surface for two branches
   that both raise.
5. Measure c, h, i and j are reported only, as asked; none is ratcheted.
