# Refactor A1: generated notes stop churning

Step A1 of `docs/specs/refactor_strategy_v3.md` (§2.3). Base: main `a810f628d8`, Nov 9. No `src` change.

## Step 0: what churns, measured on five landings

`churn_measure.py` (a scratch script, not committed) classifies each changed generated note by the first normalisation that makes the old and new text equal. The classes are: per-note stamps (`source_commit`, `source_commit_timestamp`, `source_worktree_state`, `generated_at` and the three body rows), then the table notes' `schema_head`, then test lists (the "Tests that define behavior" section and `tests/` entries in `source_paths`), then line numbers in citations. Anything left is a real change.

| Landing (range) | Generated notes changed | Stamps only | `schema_head` only | Left after both | Test lists only | Test lists differ at all | Line numbers only | Real |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Router speed 2 (`214c206ff1..a525dbcef4`) | 591 | 499 | 0 | 92 | 19 | 35 | 17 | 54 (+2 added) |
| Phone V3 (`e9ceaf8d44..ccb6573987`) | 499 | 30 | 384 | 85 | 18 | 35 | 7 | 59 (+1) |
| TE3a (`64f7d1dc86..8b0738499d`) | 558 | 68 | 385 | 105 | 17 | 45 | 16 | 69 (+3) |
| RE0 (`6b597a43ee..78669c40b9`) | 539 | 78 | 389 | 72 | 10 | 18 | 8 | 47 (+7) |
| Slip or gap (`78669c40b9..a810f628d8`) | 566 | 474 | 0 | 92 | 5 | 28 | 19 | 65 (+3) |

The map's figure holds: 499 of router speed 2's generated notes changed only their stamps. The table shows a second stamp the map didn't name. Every table note carried `schema_head`, so each landing with a migration rewrote about 385 table notes for that one line. That made it the largest single class in three of the five landings.

What's left after both stamps: 72 to 105 notes per landing. The real changes are mostly module notes' "Source facts" (the line count), "Module index" (a package map's counts), callers, dependencies and public API. These are facts that changed.

## Decision

- **Per-note stamps go.** That covers `source_commit`, `source_commit_timestamp` and `source_worktree_state` in the frontmatter, and the "Worktree state", "Source commit" and "Commit timestamp" rows in module and desktop notes. It also covers the aggregate stamps on package maps, area maps and catalogs. One `Reference/_generated.md` holds the commit.
- **`schema_head` leaves the table notes too.** It's a per-note stamp by the step's own definition, and the measurement shows it's the bulk of the churn at every migration. The Database Catalog keeps it once, and `db_validate_reference.py` checks it there.
- **Test lists stay.** They are the only cause of a change in 5 to 19 notes per landing, out of 72 to 105 left after the stamps, and they're one of several changes in 18 to 45. That's a minority, and the lists are the notes' most useful lookup ("which tests define this module"). The step's rule was to drop them only if they're the bulk.
- **Not touched:** config-field line citations (`schema.py:N`), the only cause of a change in 7 to 19 config notes per landing; and `generated_at` / `last_verified`, constant dates in the generators that never churn. Neither is named by this step.

With these changes, router speed 2's 591 changed notes would have been 92 plus `_generated.md`, and TE3a's 558 would have been 105 plus `_generated.md`.

## What changed

| File | Change |
|---|---|
| `_scripts/generated_provenance.py` (new) | Renders `Reference/_generated.md`: the newest commit touching a generator input (`src`, `tests`, `scripts`, `migrations`, `fixtures`, `apps/learnloop-tauri`, `_scripts`), its timestamp, and any input that differs from it, with a warning. It records that input commit, not HEAD, because with HEAD the commit that lands a regeneration would make the next clean-tree regeneration differ. It also holds `stamp_errors` and `note_errors` for the validators |
| `module_generate.py` | No per-module git calls (1,268 `git log` runs gone). No stamps in module notes, package maps or the catalog. The banner and Maintenance section link `_generated.md`. Writes it |
| `desktop_generate.py` | No `provenance()` or `latest_provenance()`. No stamps in module, area or catalog notes. The Dataview table loses its Commit column. `_generated.md` is one of its rendered files, so `--check` compares it too |
| `db_generate_reference.py` | No `COMMIT`/`COMMIT_TIMESTAMP` in the shared frontmatter and no `schema_head` in table notes. The Database Catalog keeps `schema_head` and links `_generated.md`. Writes it. Its JSON summary prints the input commit |
| `module_validate.py`, `desktop_validate.py` | Stamps are no longer required. A generated note that carries one fails, and `_generated.md` must exist with a full hash |
| `db_validate_reference.py` | The same for its generated notes. Its hand-written notes (Database.md, Configuration.md, Initialization.md and the rest) still need a full-hash `source_commit` and an ISO timestamp. A table note with `schema_head` fails, and the catalog's `schema_head` must equal `SCHEMA_HEAD` |
| `validate_vault.py` | `source_commit_timestamp` is still required, but only on notes without `generated: true` |
| `tests/test_desktop_activation_audit.py` | `SourceInfo` lost its three provenance fields, and the docstring's reason no longer mentioned per-source commits |
| `Reference/` | Regenerated once on the committed scripts: 2,178 generated notes, plus the new `_generated.md`. Compared with main, everything that changed is stamp removal, the module banner line, a provenance sentence in three catalogs, and the two Dataview columns (checked by script: no other line differs) |
| Vault prose | Documentation Conventions (the frontmatter contract), Documentation Dashboard (regenerate after committing), Database ("Documentation regeneration": no per-note head or commit, and the stale 377 table count is now 396) |
| `CLAUDE.md` | One paragraph: generated notes carry no commit, regenerate after committing, and a clean-tree regeneration changes nothing |

## Proofs

Each run below used the worktree's `.venv`, an empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, and all three generators in order. Each regeneration takes about 6 minutes: module 30 s, desktop 30 s, db 290 s.

1. **Validators pass** on `dc34cb262c`. `module_validate.py`: PASS (1,268/1,268 modules, 45,222 Wikilinks). `desktop_validate.py`: passed, reproducible byte-for-byte, with `_generated.md` included in `--check`. `db_validate_reference.py`: `errors: []`. `validate_vault.py`: passed (2,271 notes, 2,269/2,269 reachable).
2. **A clean-tree regeneration gives an empty diff.** After `dc34cb262c` (the regeneration commit), a full regeneration left `git status` with only this untracked record. `_generated.md` still names `1c0e9653c1`, the last commit that changed an input, so committing the regeneration didn't move it.
3. **A one-line source change touches only that module's note.** Scratch commit `e2999f163b` added one comment line to `src/learnloop/clock.py`. A full regeneration then changed two files. `Reference/Modules/learnloop/clock.md` changed in "Source lines" (41 to 42) and five symbol line numbers. `Reference/_generated.md` changed its commit and timestamp to the scratch commit. Nothing else changed. The scratch commit was then dropped (`git reset --hard dc34cb262c`).
4. **The validators catch a stamp that comes back.** I added `source_commit` to `clock.md` and `schema_head` to one table note, then reverted both. `module_validate.py` failed with "generated note carries per-note `source_commit`". `db_validate_reference.py` failed with "generated table note carries schema_head".

Before this step, the same one-line change would also have moved `clock.md`'s three stamps. Any regeneration on a branch with uncommitted inputs, or after a merge, rewrote hundreds of notes. The Database generator stamped HEAD into all 396 table notes and 81 configuration notes, so every regeneration after any commit rewrote them.

## Not done here

- Config-field line citations still move whenever `schema.py` lines shift (7 to 19 notes per landing). A3 rewrites `schema.py` and is the place to decide.
- The head fixture's path is still named in the Database Catalog's `source_paths`. A2 renames the fixture.
