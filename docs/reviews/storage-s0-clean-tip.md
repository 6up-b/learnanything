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
  `test_yaml_fast_read`, `test_config_refactor`) walk only what git tracks, plus
  the owner-lane copies when the lane is on;
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
5 MB except the two historical databases; no `filter=lfs` rule and no LFS
pointer file; none of the paths S0 removed; `LICENSE` is Apache-2.0; every
file on `BOOK_PAGES.md` exists; the head-fixture sweep.

**Finding:** both historical databases exceed G8's 5 MB (6.7 MB and 6.0 MB),
because a schema of 356 tables with their indexes is itself about that size;
`VACUUM` cannot fix it. The guard exempts exactly those two until S3 turns
them into SQL text dumps (an owner decision below).

## The owner-run landing (§7.1 step 6): `scripts/s0_landing.py`

With every LearnLoop process closed, from this branch:

1. `copy-out --checkout <main>`: backup-API copies of all eight vaults to
   `~/learnloop-backups/s0/<name>`, each verified file by file (sha256) and
   database by database (`integrity_check` and a digest of `iterdump`) against
   the source before and after the copy, with `S0-MANIFEST.json`; refuses on
   any difference (a process still writing) and never overwrites a backup.
2. `books-out`: each `new_textbooks/` file's real bytes from the checkout or
   the local LFS store (`.git/lfs/objects`, no network), checked against its
   pointer's oid, to `~/learnloop-books/`; the four papers to `papers/`.
3. `move-out --yes`: renames (same filesystem only) the three working vaults
   to `~/learnloop-vaults/<name>` (they stay the live vaults; their relative
   `state.sqlite` moves with them) and the five older ones to
   `~/learnloop-retired/<name>-<date>`; a dry run without `--yes`.
4. `check`: **refuses (exit 1)** unless every vault is gone from the checkout,
   every backup matches its manifest, each live vault matches its backup (no
   change since), each retired copy exists, and every textbook and paper is in
   the books folder with the right hash.
5. The owner merges S0 into the main checkout; `verify-after` confirms the
   paths are untracked and absent and the live databases pass
   `integrity_check`, then the owner re-points every pin (open each vault once
   in the desktop app for `last_vault`, `mobile.toml`, the chat unit's
   `--vault`, project hooks).

`tests/test_s0_landing.py` drives it on synthetic checkouts only: refuses
before anything is copied, refuses while the vaults are still in the checkout,
passes after the whole procedure (sources byte-identical before the move),
refuses a live vault changed after its backup, a textbook whose copy does not
match its pointer, a missing LFS object, and an existing backup directory.

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

## Owner decisions S0 still needs

1. **Approve the sanitized `migration_head_220`** (D6): it keeps the shape of
   six attempts (items, grades, times), none of your words. If not approved,
   S0 untracks it and moves its ~39 test files and the two DB-reference
   scripts to the owner lane until S3.
2. **Run the landing yourself** (`scripts/s0_landing.py`, five steps above)
   and merge S0 into the main checkout. An agent must not.
3. **Samples (D16):** the recommended default is in; confirm or drop the two
   non-commercial MIT PDFs.
4. **Screenshot `p1-02`:** redacted as a probable Blitzstein and Hwang contents
   page; restore it if it was a generated test PDF.
5. **5 MB rule vs the two historical databases** (6.7 MB, 6.0 MB): exempted
   until S3's text dumps; confirm, or have S3 come sooner.
6. Already decided, for the record: D17 Apache-2.0 (confirmed 2026-10-16), D6
   every fixture vault leaves, D2 H2 history rewrite (S4, owner-run; the old
   files and the unredacted screenshots stay in history until then).

## Open findings (not changed here)

- **`learnloop ai compare`'s working-vault refusal** (`src/learnloop/cli/ai_compare.py`
  `tracked_database_reason`) identifies a working vault by git tracking its
  database. After S0 the live vaults under `~/learnloop-vaults/` are not
  tracked, so the command would no longer refuse to compare on them in place.
  Follow-up: refuse vaults under the data root as well (S1's doctor checks are
  the natural home).
- The desktop shell's doc comment in `apps/learnloop-tauri/src-tauri/src/sidecar.rs`
  still mentions the tracked `fixtures/linear_algebra`; behaviour is already
  right (fixtures-local, then `~/LearnLoop`). Left to avoid a Rust change.
- Older docs and code comments cite `fixtures/linear_algebra` measurements as
  history; left as written.
- `tests/fixtures/glm_ocr/` and the desktop's `pdfSelection` fixture carry CC
  BY 4.0 arXiv text added after the §3.5 audit; attributed in `samples/NOTICE`.
