# Storage S0: clean the public tip (stage record)

Branch `storage/s0-clean-tip` in the worktree `learnanything-lr1`, base `main` at
`e9d4de1aa` (migration head 220, latest algorithm `mvp-0.31`). Spec:
`docs/specs/spec_storage_sync_v1.md` §6.11 (S0 row), §3.5, §7.1 step 6, §7.2,
§7.3, G6/G8/G9/G13. Trigger: owner, 2026-10-23 ("start S0 as soon as AD2+AD3
and T1 land"; both have landed).

**This branch must not be fast-forwarded or merged into the main checkout by
an agent.** Updating any checkout to these commits makes git delete the clean
copies of every untracked path there, the owner's live working vaults
included. The owner lands it with `scripts/s0_landing.py` (below), which
refuses until every vault, textbook and paper is copied out and verified.

No history was rewritten, nothing was pushed, no remote, LFS command,
`tailscale` command, main-checkout file or owner vault was touched. No model
call was made (no paid call, no live call; every script outside pytest ran
under `env -i` with an empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`).

## Commits

| Commit | What |
|---|---|
| `db2b71b03` | Redact the book pages in seven screenshots (D19) |
| `bc9ec4739` | Untrack the vaults, `new_textbooks/`, the four reference PDFs; ignore the vault names; delete `.gitattributes` (LFS only); the `owner_vaults` lane |
| `8129b6d0c` | Sanitize `fixtures/migration_head_220` (§7.2) |
| `edd94d152` | Guard tests, `samples/` + `NOTICE`, `LICENSE`, README, `BOOK_PAGES.md`, `References.md`, the landing gate and its tests, CLAUDE.md |
| `cf12620af` | Head resolver in `test_embedding_store.py` reads tracked files; the landing check's `git ls-files` approved in the launch-site audit |
| `fcfe9df91`..`06f164bd5` | Codex review fixes F1-F6 (`docs/reviews/storage-s0-clean-tip-codex-review.md`) |

## D17: the code licence

Confirmed by the owner on 2026-10-16 ("apache 2.0 is fine for a license"),
recorded in the spec's D17. `LICENSE` is the canonical Apache-2.0 text
(sha256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`,
identical in three independently packaged copies in the environment, no
network used). It lands in the same commit series that removes the
third-party files, as D17 asks. The README's new "Licence" section says that
dependencies keep their terms, names Marker's model-weight restriction, and
that the two MIT samples are non-commercial.

## What leaves the tip

648 tracked paths (646 deletions + 2 that git shows as renames into
`samples/`), all by `git rm -r --cached`; their bytes stayed on disk in this
worktree and were then moved to the gitignored `fixtures-local/s0-held/`
here so the worktree behaves like a fresh clone.

| Path | Files | Why (§3.5) |
|---|---:|---|
| `fixtures/linear_algebra/` | 142 | Owner's working vault: learning history, Axler PDF in plain git, book text in `source_document_blocks` |
| `fixtures/probability/` | 114 | Owner's working vault: Blitzstein and Hwang, MIT 6.041 PDFs, a Wikipedia page |
| `fixtures/arxiv_v2/` | 90 | Owner's working vault: Welch Labs guide (LFS), *Attention Is All You Need* HTML, 10 YouTube transcripts |
| `fixtures/arxiv/` | 117 | Early owner vault; arXiv HTML, transcripts |
| `fixtures/conic-sections/` | 22 | Early owner vault; a transcript, owner answers |
| `fixtures/law/` | 71 | Early owner vault; NCBE MBE questions (all rights reserved) |
| `fixtures/physical_therapy/` | 33 | Early owner vault; a Quizlet PEAT exam |
| `fixtures/linear_algebra_legacy/` | 31 | Frozen copy with 21 owner attempts |
| `new_textbooks/` | 23 | 22 LFS PDFs and the owner's `interesting_courses.txt` |
| `docs/brainstorming/{DTransKT,a_diagnostic_driven_multi_agent_socratic_teaching_system,ace-kt}.pdf`, the IRAISE slides | 4 | Cited by DOI/link in `docs/brainstorming/References.md` |
| `.gitattributes` | 1 | Its only three lines were git-LFS rules (G9) |

Ignored from now on: the eight `fixtures/<name>/` directories (`.gitignore`;
`new_textbooks/` was already ignored). Per D6 (owner, 2026-10-16) every
fixture directory that is a vault leaves; the five that stay are the text
fixtures `grading_hardcases`, `proto_sources`, `synthesis_eval_gold` and the
historical `migration_head_220` and `mvp017_route_check_replay`.

The owner's untracked files in the main checkout (the two brainstorming PDFs
and two Markdown notes, the root-level `linear_algebra/` and `probability/`
directories) were not touched; G8 now keeps a PDF from being committed
outside `samples/`.

## Samples (D16, recommended default)

`samples/` holds four unmodified files, each in `samples/NOTICE` with title,
author, source, licence and sha256: Austin's *Understanding Linear Algebra*
section "Symmetric matrices and variance" (CC BY 4.0, from the legacy vault's
store), Wikipedia "Elevator paradox" oldid 1313119339 (CC BY-SA 4.0, from the
probability vault's store), and MIT 18.06 Spring 2010 Quiz 1 with solutions
(CC BY-NC-SA 4.0, labelled non-commercial; bytes verified against their LFS
pointers' oids). No test reads them. `NOTICE` also attributes the CC BY 4.0
GLM-OCR recording of arXiv:2302.11517 already in `tests/fixtures/glm_ocr/`
(added after the §3.5 audit, already attributed in its README).

## Screenshots (D19)

All 88 tracked PNGs under `docs/` were looked at (contact sheets; tall pages
in slices). The full list is `docs/screenshots/BOOK_PAGES.md`:

- **Attributed (7):** five show Axler 4th ed. (CC BY-NC 4.0), one MIT 6.041
  Recitation 1 (CC BY-NC-SA 4.0), one the APIET 2026 paper (CC BY 4.0). The
  README's first section now attributes Axler too.
- **Redacted (7):** six show Blitzstein and Hwang's *Introduction to
  Probability* (not redistributable); their page area is now a grey panel
  labelled "Book page removed: not redistributable (S0, D19)". The seventh,
  `p1-02-reader-preparing-original-pdf.png`, shows a contents page titled
  "Probability — The Long Version" whose chapter list matches that book; it
  may be a test PDF, so it was redacted to be safe (owner may restore).
- The rest show only the app, the owner's own items, answers and graphs (D19
  keeps them).

The original images remain in git history until the owner's D2 rewrite (H2).

## Tests moved to the `owner_vaults` lane

Marker declared in `pyproject.toml`; `tests/owner_vaults.py` resolves
`LEARNLOOP_OWNER_VAULTS=<dir>` (backup-API copies under the old fixture
names); `tests/conftest.py` skips the lane when it is unset and guards the
copies' journal headers like tracked fixtures. 103 tests in the default lane's
files are in the lane (counted by running it):

- whole working-vault parametrizations (`linear_algebra`, `probability`,
  `arxiv_v2`): `test_placement_fixture_copies`, `test_daily_loop_start_minutes`,
  `test_daily_plan_kill_switch`, `test_field_workbench_signals`,
  `test_intent_recall_targets`, `test_router_r2a_serving`, `test_ad23_successor`,
  `test_router_r2b_serving` (their synthetic cases stay in the default lane);
- single-vault tests: `test_activity_backfill` (6/6), `test_goal_decay_projection`
  (1/4, the legacy golden), `test_goal_scope_material` (1/18),
  `test_graph_editor_reads` (5/14), `test_learner_read_model_pinning` (3/3),
  `test_sidecar_contract` (5/82, four on `linear_algebra`, one on `arxiv`),
  `test_collection_dataset` (2/42), `test_doctor` (1/22, pre-044 `conic-sections`),
  `test_measurement_rank` (1/14), `test_migrate_fresh` (1/8, `arxiv` before 153),
  `test_today_surfaces` (3/11), `test_sqlite_wal_lifecycle` (1, already durability),
  `test_receipt_exactness` / `test_receipt_derivation` (the `linear_algebra` ones);
- the fixture walkers (`test_migrations`, `test_receipt_exactness`,
  `test_receipt_derivation`, `test_tracked_fixture_databases`,
  `test_yaml_fast_read`, `test_config_refactor`) and the session database guard
  in `tests/conftest.py` (since review F6) walk only what git tracks, plus the
  owner-lane copies when the lane is on;
- `test_ad2_model`'s surface-group pin now reads the tracked fixtures' items
  instead of `conic-sections` (stays in the default lane).

Every test that moved is unchanged apart from where it finds its vault; no
golden was re-pinned. S3's builders bring their default-lane coverage back.

## Sanitizing `migration_head_220` (§7.2, G13)

`scripts/sanitize_migration_head_fixture.py` ran on a backup-API copy under
`fixtures-local/`, and the result was copied into place with
`copy_tree_with_databases`:

- transcript `canonical-sources/raw/note_source_youtube_video_hvjkcmzfix8_…bin`
  (a Professor Dave Explains video, 94 cues): replaced by project-authored
  captions (`scripts/sanitized_head_transcript.py`), same cue timings and
  `video_id`; the note regenerated in the identical format (the generator was
  first checked to reproduce the original note's body exactly); the quotes in
  `proposed_patches.source_refs_json` rewritten from the new captions at the
  same locators;
- the focus-directrix concept description, copied from the video, reworded in
  `concepts/concepts.yaml` and the accepted proposal item;
- the six answers in `practice_attempts.learner_answer_md` replaced with
  synthetic answers of the same kind (same item, grade and mistake: incomplete,
  the -1 slip, the unrelated condition, +4 instead of +1, correct, correct);
  the quote in `error_events.repair_plan_json` and two `grading_evidence`
  rows that quoted answers rewritten to quote the new ones;
- one transaction with `secure_delete`, then `VACUUM`: the first sweep found
  old rows in the unused space of pages that earlier migrations' table
  rebuilds had freed and reused, which only a rewrite removes. Checked after:
  every row of every table with its rowid identical (digest), `sqlite_master`
  identical, `schema_migrations` identical (head 220), `integrity_check` ok,
  `foreign_key_check` empty, journal mode DELETE, header bytes 1/1, no
  companions; 6,721,536 → 6,696,960 bytes;
- the sweep: no eight-word window of the original transcript and no original
  answer (or the "must cross x=0" quote) in any file, any text column or the
  raw database bytes. The first pass found three windows in my own caption 67
  (an arithmetic phrase) and they were reworded. `tests/fixtures/sanitized_head_sweep.json`
  stores only sha256 prefixes; `tests/test_public_tip_guards.py` repeats the
  sweep on the tracked fixture and proves it is not vacuous on planted text.

What stays: the shape of the six attempts (items, grades, order, times on
2026-05-30/31), the note's ids, title, URL and `content_hash` label (no longer
the captions' hash). No test pinned replaced text; every test file that reads
the head fixture passes (below). The fixture's README has a new "Sanitized in
storage S0" section. **The owner approves this at S0's checkpoint (D6).**

## Guards (G8, G9, G13): `tests/test_public_tip_guards.py`

Over `git ls-files`: no SQLite database by name or header except
`fixtures/migration_head_<N>/state.sqlite` (one) and
`fixtures/mvp017_route_check_replay/state.sqlite`; no PDF/EPUB/DjVu/audio/video
outside `samples/` (by suffix or `%PDF-` magic); no other binary (git's NUL
rule) except images under `docs/` and icons/fonts under `apps/`; no
`canonical-sources/` file outside the two historical fixtures; every sample
has a `NOTICE` entry with a `Licence:` line and no entry is stale; no file over
5 MB, with a bounded exception for the two historical databases (review F5:
the head at most 8 MiB, the frozen replay fixture at most 6 MiB); no `filter=lfs` rule and no LFS
pointer file; none of the paths S0 removed; `LICENSE` is Apache-2.0; every
file on `BOOK_PAGES.md` exists; the head-fixture sweep.

**Finding:** both historical databases exceed G8's 5 MB (6.7 MB and 6.0 MB),
because a schema of 356 tables with their indexes is itself about that size;
`VACUUM` cannot fix it. The guard allows exactly those two up to a bound
(8 MiB for the head, which grows a little with each migration; 6 MiB for the
frozen replay fixture) until S3 turns them into SQL text dumps (an owner
decision below); never an unlimited exemption by name.

## The owner-run landing (§7.1 step 6): `scripts/s0_landing.py`

With every LearnLoop process closed, from this branch:

0. Every step first reads each vault's database path from its own
   `learnloop.toml` (without loading environment settings) and refuses,
   before copying or moving anything, a layout S0 cannot move as a plain
   rename: an absolute or `..` `storage.sqlite_path`, a database not named
   `*.sqlite`, a missing database, a vault that is itself a symlink, or any
   symlink in the vault (review F1, re-review F1;
   those are relocated by S1's `vault move`, §7.1 step 4). All eight vaults'
   tracked versions have the plain layout (checked on the owner-lane copies).
1. `copy-out --checkout <main>`: backup-API copies of all eight vaults to
   `~/learnloop-backups/s0/<name>`, each verified file by file (sha256) and
   database by database (`integrity_check` and a digest of `iterdump`) against
   the source before and after the copy, with `S0-MANIFEST.json`; refuses on
   any difference (a process still writing) and never overwrites a backup
   (a verified backup from an earlier, interrupted run is kept).
2. `books-out`: the inventory comes from git's index, not the working tree
   (review F2): every tracked `new_textbooks/` file and paper with the sha256
   its LFS pointer's oid names, or else its blob's, plus any untracked file
   under `new_textbooks/`; a file already staged for removal is taken from
   HEAD, and every reference paper must be in the inventory (re-review F8).
   It refuses while a plain tracked file has uncommitted edits, whose only
   copy is the working file (re-review F7: commit or discard them first). The
   inventory is written to `S0-BOOKS-MANIFEST.json` before anything is
   copied. Each file's bytes come from the checkout or the local
   LFS store (`.git/lfs/objects`, no network) only when they hash to that
   value (a plain tracked file the working tree lost comes from its blob), to
   `~/learnloop-books/`, the papers to `papers/`.
3. `move-out --yes`: refuses a vault with no verified backup in the backup
   root; renames (same filesystem only) the three working vaults to
   `~/learnloop-vaults/<name>` (they stay the live vaults; their relative
   `state.sqlite` moves with them) and marks each as a working vault
   (`.learnloop/working-vault.json`, review F3), the five older ones to
   `~/learnloop-retired/<name>-<date>`; records each move in the manifest as
   it happens, so a stopped run resumes; a dry run without `--yes`.
4. `check`: **refuses (exit 1)** unless every vault is gone from the checkout,
   every backup matches its manifest, each live vault has the plain layout,
   matches its backup (no change since) and is marked, each retired copy
   matches its backup, and every entry of the books manifest (which must
   cover git's index and every reference paper, with no uncommitted edit to
   a plain tracked file) is in the books folder with its hash. If a moved vault
   changed after its backup, `copy-out --from-moved --backup-root <new>` backs
   up the moved vaults where they now are, and `check --backup-root <new>`
   passes against that (review F4).
5. The owner merges S0 into the main checkout; `verify-after` confirms the
   paths are untracked and absent and that the database each live vault's
   own config names has the plain layout and passes `integrity_check`, then
   the owner re-points every pin (open each vault once
   in the desktop app for `last_vault`, `mobile.toml`, the chat unit's
   `--vault`, project hooks).

`tests/test_s0_landing.py` drives it on synthetic git checkouts only: refuses
before anything is copied, refuses while the vaults are still in the checkout,
passes after the whole procedure and after the simulated merge (sources
byte-identical before the move), refuses a live vault changed after its
backup and recovers with `--from-moved`, resumes an interrupted landing,
refuses a changed retired copy, a move without a backup, the four unsupported
database layouts (absolute, `..`, symlink, not `*.sqlite`), a live config that
opens another database, a corrupt paper, a lost book copy, a wrongly
materialized LFS file, a changed inventory, a textbook whose copy does not
match its pointer, a missing LFS object, an existing backup directory, a
symlinked vault root (in the checkout and as the live vault), uncommitted
edits to a tracked text file (before and after `books-out`; committed edits
are backed up), and a reference paper in neither the index nor HEAD (one
staged for removal is recovered from HEAD), and a books manifest missing a
paper.

Note for the main checkout (from its `git status` at the start of this
session): its `.gitignore` and the vaults' `learnloop.toml`/`state.sqlite`
have uncommitted changes. The vault changes move out with the vaults in step
3; the `.gitignore` change will conflict with S0's `.gitignore` edit at the
merge and is the owner's to resolve.

## Gate (this step; the full suite runs once at landing)

All pytest runs inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6`.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 35 kept, 0 broken |
| `pytest -n 6` on the 32 changed/added test files + `test_ai_tool_isolation`, `test_e0_isolation`, `test_coordinated_migrations` | 704 passed, 71 skipped (the skips are the `owner_vaults` lane and pre-existing skips) |
| `pytest -n 6` on the 39 test files that read `migration_head_*` + `test_mvp017_route_check_replay` | 602 passed, 1 failed → fixed (`test_embedding_store` globbed an untracked leftover `fixtures/migration_head_219/.learnloop/` in this worktree; it now reads tracked files) → `test_embedding_store` 22 passed |
| `pytest -n 6 -m durability` on those files + `test_tracked_fixture_databases`, `test_migrations`, `test_sqlite_wal_lifecycle` | 21 passed, 1 skipped |
| `pytest -n 6 -m owner_vaults` on the changed files with `LEARNLOOP_OWNER_VAULTS=fixtures-local/owner-lane` (backup-API copies of this worktree's git-HEAD copies, never the owner's) | 103 passed |
| `test_yaml_fast_read`, `test_config_refactor` with the lane on | 1,199 passed |
| `test_codex_lockdown_round3`, `test_coordinated_migrations`, `test_ai_tool_isolation`, `test_e0_isolation`, `test_contamination_report` | 145 passed, 1 failed (the landing script's `git ls-files` was a new launch site) → approved → `test_codex_lockdown_round3` 16 passed |
| `db_generate_reference.py`, `db_validate_reference.py` | 351 table notes, 0 errors; the only diff was `source_commit` stamps (schema unchanged), not committed |

No frontend, Rust, migration, config, CLI or algorithm change: no vitest,
cargo, successor or snapshot regeneration needed.

Test files run (for the landing gate): `test_activity_backfill`, `test_ad23_successor`,
`test_ad2_model`, `test_codex_lockdown_round3`, `test_collection_dataset`,
`test_config_refactor`, `test_daily_loop_start_minutes`, `test_daily_plan_kill_switch`,
`test_doctor`, `test_embedding_store`, `test_field_workbench_signals`,
`test_goal_decay_projection`, `test_goal_scope_material`, `test_graph_editor_reads`,
`test_intent_recall_targets`, `test_learner_read_model_pinning`, `test_measurement_rank`,
`test_migrate_fresh`, `test_migrations`, `test_placement_fixture_copies`,
`test_public_tip_guards`, `test_receipt_derivation`, `test_receipt_exactness`,
`test_router_r2a_serving`, `test_router_r2b_serving`, `test_s0_landing`,
`test_sidecar_contract`, `test_sqlite_file_copies`, `test_sqlite_wal_lifecycle`,
`test_today_surfaces`, `test_tracked_fixture_databases`, `test_yaml_fast_read`,
`test_ai_tool_isolation`, `test_e0_isolation`, `test_coordinated_migrations`,
`test_contamination_report`, `test_mvp017_route_check_replay`, and every
`git grep -l migration_head -- 'tests/test_*.py'` file.

**For the landing gate:** run it in a worktree created from the merged tree
(git creates no untracked directories, so the owner vaults are absent there,
which is G6's fresh-clone condition). Never in the main checkout.

## Owner decisions (decided 2026-10-25)

Recorded in the spec's decision log too (`docs/specs/spec_storage_sync_v1.md`
§10, rows D6, D16, D19).

1. **The sanitized `migration_head_220` stays on the tip** (D6 approved). It
   keeps the shape of six attempts (items, grades, times) and none of the
   owner's words; its ~39 test files stay in the default lane.
2. **The landing is run by the orchestrator** (not the owner by hand, and
   never by the merge agent) in the main checkout with `scripts/s0_landing.py`,
   by the command sequence in "Merge onto main and landing rehearsal" below.
3. **Samples (D16): the recommended default stands**, the two MIT 18.06
   CC BY-NC-SA 4.0 PDFs included (attributed and labelled non-commercial in
   `samples/NOTICE`).
4. **Screenshot `p1-02` stays redacted.**
5. **The two historical databases are exempt from G8's 5 MB rule until S3**
   (6.7 MB and 6.0 MB), within the bounds the guard sets (the head at most
   8 MiB, the frozen replay fixture at most 6 MiB;
   `tests/test_public_tip_guards.py` `HISTORICAL_DATABASE_MAX_BYTES`).
6. Already decided, for the record: D17 Apache-2.0 (confirmed 2026-10-16), D6
   every fixture vault leaves, D2 H2 history rewrite (S4, owner-run; the old
   files and the unredacted screenshots stay in history until then).

## Open findings (not changed here)

- ~~`learnloop ai compare`'s working-vault refusal after the move~~: fixed in
  review F3. `move-out` marks each live vault (`learnloop.vault.working_vault`:
  its resolved path and its directory's device and inode), and
  `tracked_database_reason` refuses a marked vault, also after a rename, while
  a copy carrying the mark file is compared. S1's doctor checks may take over
  the identification.
- The desktop shell's doc comment in `apps/learnloop-tauri/src-tauri/src/sidecar.rs`
  still mentions the tracked `fixtures/linear_algebra`; behaviour is already
  right (fixtures-local, then `~/LearnLoop`). Left to avoid a Rust change.
- Older docs and code comments cite `fixtures/linear_algebra` measurements as
  history; left as written.
- `tests/fixtures/glm_ocr/` and the desktop's `pdfSelection` fixture carry CC
  BY 4.0 arXiv text added after the §3.5 audit; attributed in `samples/NOTICE`.
- **Codex's remaining F7 and F8 (Low, open; ruled by the orchestrator
  2026-10-25):** the landing script's provenance edge cases for the reference
  papers stay open as Low. They do not block the landing: in the main
  checkout all four papers are tracked and unmodified (its `git status` at
  the start of this session), and the
  rehearsal below backed them up from the working tree with their blob hashes.

## Merge onto main and landing rehearsal (2026-10-25)

Merge agent, worktree `learnanything-merge2`, branch `merge/s0-onto-main`
from `main` at `bc6240a6e` (UX Phase 3 landed). No git command, file or vault
of the main checkout was touched; the owner's mvp-0.30 backups were only read.
No model call, paid or live.

### Merge

`git merge --no-ff storage/s0-clean-tip` (tip `24c10e55d`): **no conflict**.
UX Phase 3 added no test that loads an owner vault and no fixture walker
(`tests/test_ux_phase3_today.py` builds its own vaults; `test_mobile_allowlist`
only pins `workbench.open_problems` desktop-only), so **no test moved to the
`owner_vaults` lane**. In merge2 the merge deleted the eight vault directories
and `new_textbooks/` from disk: they were clean git-HEAD copies with no
untracked files, so nothing was lost, and the worktree is now in G6's
fresh-clone condition.

| Commit | What |
|---|---|
| `edefc35d3` | The merge |
| `88b78c826` | Regeneration: `Config - ai.md` (four `ai_compare.py` line citations moved by review F3: `:860` to `:867`); the manual-attempt example (`Examples/Manual Attempt and State Inspection.md`) named `fixtures/linear_algebra` in `source_paths`, so `validate_vault.py` failed; it now copies an owner-lane copy |
| `e74c18ebd` | Rehearsal finding R1 (below): `books-out` and an untracked nested repository under `new_textbooks/`, with its fail-first test |
| `4b6f204c4` | The owner's decisions of 2026-10-25 here and in the spec's §10 |

### Regeneration

- **References:** `db_generate_reference.py` rewrote 422 notes; only
  `Config - ai.md` changed beyond `source_commit` provenance (kept, above),
  the rest discarded. `db_validate_reference.py`: 0 errors (351 table notes).
- **`validate_vault.py`:** failed on the example above, then passed (1,154
  notes, 1,152/1,152 reachable).
- **Defaults snapshots:** all 22 recomputed with
  `defaults_fingerprint_for_version` (`-B`, `env -i`): 0 mismatches.
- **CLI help snapshot, RPC pins** (serializer snapshot, desktop RPC contract,
  mobile allowlist): their tests pass with no file changed.

### Gate (FULL), at `edefc35d3`; the files changed after it re-run at `4b6f204c4`

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` (5G scopes) | ok |
| `uv run lint-imports --no-cache` | 35 kept, 0 broken |
| full suite, `-n 8`, 10G scope (owner lane skipped) | **21,323 passed**, 74 skipped, 38 xfailed, 2 failed: `test_reading_hardening_2_fixes::test_f1_…` (known load flake) and `test_mvp021_upgrade::test_the_successor_rebuild_equals_mvp020s_projection` (a float difference in `facet_recall_state` under load); both **3/3 alone** |
| `-m durability` | 121 passed, 1 skipped (the owner-lane WAL test) |
| `-m owner_vaults`, `LEARNLOOP_OWNER_VAULTS` = backup-API copies of `vault-backups-20261025-mvp030/*` (three working vaults) plus the five older vaults from `main`'s tree | 101 passed, **2 failed, both data-dependent and pre-existing** (below) |
| `-m owner_vaults` on backup-API copies of all eight vaults from `main`'s tree (what the stage used) | **103 passed** |
| fixture walkers with the lane on (`test_yaml_fast_read`, `test_config_refactor`, `test_tracked_fixture_databases`, `test_migrations`, `test_receipt_exactness`, `test_receipt_derivation`) on the mvp-0.30 copies | 1,280 passed |
| at `4b6f204c4`: `test_public_tip_guards`, `test_s0_landing` (29), `test_sqlite_file_copies`, `test_codex_lockdown_round3`, `test_architecture`, `test_cli_help_snapshot`, `test_sidecar_serializer_snapshot`, `test_desktop_rpc_contract`, `test_mobile_allowlist`, `test_ai_compare`, `test_ux_phase3_today` | 386 passed |
| `npm install`, `npm run typecheck` | ok |
| `npx vitest run --maxWorkers=4` (whole) | 210 files, **1,822 passed** |
| `npm run frontend:build`; `cargo check` | ok; ok |

The two owner-lane failures on the mvp-0.30 copies read the owner's current
data, not S0: `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events`
finds no attempt without an activity observation in today's
`linear_algebra` (every attempt is backfilled), and
`test_placement_fixture_copies::…[arxiv_v2]` finds a never-practised LO
(`lo_prepare_and_inspect_aligned_coordinate_tensors`) the mvp-0.10 baseline
does not serve. Both fail the same way on `main` (`bc6240a6e`, before S0) with
the same copies placed in `fixtures/`, and pass on the git-HEAD copies. S3's
builders replace these tests; until then the owner lane is pinned to the data
its goldens were written on.

### Rehearsal of `scripts/s0_landing.py` on a scratch clone

A local clone of the repository under `fixtures-local/s0-sim/checkout` (never
the main checkout), `main` checked out at `bc6240a6e` with
`GIT_LFS_SKIP_SMUDGE=1` (pointers, as in the main checkout), its
`.git/lfs/objects` a reflink copy of the main checkout's store (443 MB, only
read). Made to look like the owner's checkout: the root `.gitignore` carries
the owner's uncommitted five-line edit (the conversation-traces block, copied
from the main checkout's file); the three working vaults' databases are in
WAL mode with an empty `-wal` beside them, and `linear_algebra`'s has an
extra table and row; the four `learnloop.toml` the owner has edited carry an
uncommitted line; `fixtures/linear_algebra/.learnloop/` holds a machine-local
file; an untracked PDF in `docs/brainstorming/`, an untracked root
`linear_algebra/`, and an untracked nested git repository
`new_textbooks/Axler-Solutions/` (the main checkout has one). Its `git status`
then matched the owner's line for line. Destinations: `--backup-root`,
`--retired-root`, `--books-root` under `fixtures-local/s0-sim/home/`,
`--vaults-root fixtures-local/s0-sim/vaults`. Every step ran with merge2's
`.venv`, `env -i` and an empty `HOME`.

| Step | Result |
|---|---|
| `check` (before anything) | **REFUSED**, exit 1: each vault still in the checkout and without a backup, no books manifest |
| `move-out` (before copy-out) | **REFUSED**, exit 1: no verified backup; nothing moved |
| `copy-out` | exit 0: eight vaults copied and verified (141, 113, 89, 116, 21, 70, 32, 30 files; one database each). Opening a WAL database read-only creates an empty `-shm` beside it (the owner's already exist) |
| `books-out`, first run (before R1's fix) | **stopped with `IsADirectoryError`** before writing the manifest or copying anything: finding R1 |
| `books-out` (after the fix, on a rebuilt clone) | exit 0: 22 textbooks from the LFS store, `interesting_courses.txt` from its blob, the four papers from the working tree, and the nested repository's working files (`Axler-Solutions/...`, not its `.git/`) |
| `move-out` (dry run) | exit 0: eight `would move` lines (three to the vaults root, five to `learnloop-retired/<name>-2026-10-25`) |
| `move-out --yes` | exit 0: eight renames; `git status` then shows ` M .gitignore` and 620 ` D fixtures/...` lines (every tracked vault file) |
| `check` | **OK**, exit 0 |
| `git merge --ff-only s0-tip` | **refused by git**: "Your local changes to the following files would be overwritten by merge: .gitignore". The deleted vault files do not block the merge. Nothing changed |
| save the `.gitignore` edit as a patch, `git checkout -- .gitignore`, `git merge --ff-only s0-tip`, `git apply` the patch | fast-forward; `git status`: ` M .gitignore` (the owner's edit back, uncommitted) and the owner's untracked files only. The four papers left `docs/brainstorming/` (their copies are in `books/papers/`); `new_textbooks/Axler-Solutions/` stayed (untracked) |
| alternative, on a second worktree: commit the `.gitignore` edit first, then `git merge --no-ff s0-tip` | clean auto-merge of `.gitignore` (the hunks do not overlap) |
| `verify-after` | OK, exit 0, with the re-pointing reminder |
| `check` (after the merge) | OK, exit 0 |

Afterwards the live `linear_algebra` held the extra table and row, the
`learnloop.toml` edit, `.learnloop/machine-local.txt` and the
`working-vault.json` mark. No prompt asks anything interactively; the only
manual actions are the `.gitignore` handling and the merge itself.

**R1 (fixed in `e74c18ebd`).** `git ls-files --others -- new_textbooks` names
a nested repository as one entry ending in `/`; `media_inventory` read it as
a file. The main checkout has `new_textbooks/Axler-Solutions/` with its own
`.git/`, so the real `books-out` would have stopped there (before copying
anything, so harmless, but the landing could not go on). Now each working
file under it is listed and backed up; its `.git/` is not (git never deletes
untracked files, so it stays in the checkout, and its index changes whenever
git runs there, which would make `check` see drift).
`tests/test_s0_landing.py::test_an_untracked_nested_repository_under_new_textbooks_is_backed_up_file_by_file`
failed with `IsADirectoryError` before the fix.

### The real landing: command sequence

For the orchestrator, after the owner's go. Main must still be `bc6240a6e`;
if it has moved, merge it into `merge/s0-onto-main` and gate again first.
Same filesystem: the checkout and `~` are both on `/home` (btrfs), as
`move-out` needs. None of `~/learnloop-backups`, `~/learnloop-vaults`,
`~/learnloop-retired`, `~/learnloop-books` exists yet.

```bash
# 0. Close every LearnLoop process: the desktop app (npm run dev / Tauri),
#    the mobile host (systemctl --user stop learnloop-mobile.service, if
#    installed), the chat server (learnloop mcp serve / its unit), any CLI.
pgrep -fa 'learnloop|learnloop_sidecar|learnloop-mobile'    # must print nothing
S0=/home/saturn/Documents/thinking/learnanything-merge2     # the merged tree, synced .venv
CHECKOUT=/home/saturn/Documents/thinking/learnanything
PY="$S0/.venv/bin/python -B"
cd "$S0"

# 1-4. The script, with its default destinations under ~.
$PY scripts/s0_landing.py check     --checkout "$CHECKOUT"   # expect REFUSED, exit 1
$PY scripts/s0_landing.py copy-out  --checkout "$CHECKOUT"   # eight "copied ... and verified"
$PY scripts/s0_landing.py books-out --checkout "$CHECKOUT"   # textbooks, papers, Axler-Solutions files
$PY scripts/s0_landing.py move-out  --checkout "$CHECKOUT"   # dry run: read the eight lines
$PY scripts/s0_landing.py move-out  --checkout "$CHECKOUT" --yes
$PY scripts/s0_landing.py check     --checkout "$CHECKOUT"   # must print OK, exit 0; stop otherwise

# 5. The merge, in the main checkout. git refuses while .gitignore has the
#    owner's uncommitted edit, so set it aside as a patch and put it back.
cd "$CHECKOUT"
git status --short | grep -v '^ D fixtures/'                 # expect: " M .gitignore" + the owner's ?? files
git diff -- .gitignore > ~/learnloop-s0-gitignore.patch
git checkout -- .gitignore
git merge --ff-only merge/s0-onto-main
git apply ~/learnloop-s0-gitignore.patch
git status --short                                           # expect: " M .gitignore" + the owner's ?? files only
#    (Alternative if the owner prefers: commit the .gitignore edit first, then
#    git merge --no-ff merge/s0-onto-main; it auto-merges cleanly.)

cd "$S0"
$PY scripts/s0_landing.py verify-after --checkout "$CHECKOUT"   # OK, exit 0
$PY scripts/s0_landing.py check        --checkout "$CHECKOUT"   # still OK
```

If a step stops part-way, run it again (done and verified work is kept). If
`check` reports that a moved vault changed after its backup:
`copy-out --from-moved --backup-root ~/learnloop-backups/s0-2`, then
`check --backup-root ~/learnloop-backups/s0-2`.

**Re-pointing (the owner, right after `verify-after`):**

1. **Desktop `last_vault`.** Start the desktop app and open
   `~/learnloop-vaults/<name>` with its vault picker (an explicit selection
   records it in `~/.config/learnloop/last_vault`; `LEARNLOOP_VAULT=` alone
   does not). Without this, a remembered vault that is gone makes the app
   open the first vault under the checkout's `fixtures-local/` instead.
2. **`mobile.toml`** (`~/.config/learnloop/mobile.toml`, see
   `deploy/mobile.toml.example`): change each `fixtures/<name>` vault path to
   `~/learnloop-vaults/<name>`, then restart `learnloop-mobile.service`.
3. **The chat unit** (`~/.config/systemd/user/learnloop-mcp.service`, if
   installed; `docs/reviews/mcp-c1a.md`): change `--vault` to
   `~/learnloop-vaults/<name>`, `systemctl --user daemon-reload`, restart.
4. **Project hooks:** for each vault, `learnloop project status --vault
   ~/learnloop-vaults/<name>` lists the enrolled repositories; for each with a
   hook, `learnloop project install-hook <repo> --vault ~/learnloop-vaults/<name>`
   rewrites its block with the new path ("updated").
5. Keep `~/learnloop-backups/s0/`, `~/learnloop-retired/` and
   `~/learnloop-s0-gitignore.patch` until a week has passed and a restore drill
   has run (§7.1 step 5).

### Open items

- R1 fixed; Codex's remaining F7/F8 open as Low (above).
- The owner lane's two data-dependent tests fail on the owner's current
  vaults (also before S0); they pass on the git-HEAD copies. S3's builders end
  this.
- `test_mvp021_upgrade::test_the_successor_rebuild_equals_mvp020s_projection`
  joins the known load flakes (3/3 alone).
- The S0 tip itself is unchanged; the landing tip is `merge/s0-onto-main`.
