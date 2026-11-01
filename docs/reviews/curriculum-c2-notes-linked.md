# Curriculum C2: notes in the learner's voice, linked

**Stage:** `curriculum-c2-notes-linked`, branch `curriculum/c2-notes-linked` (worktree `learnanything-ad1`), base
`2eb4bf6e61` (main: C1 mvp-0.40, RW6b, CA3-CA6b, head fixture `migration_head_228`). **Spec:**
`docs/specs/spec_deliverable_curriculum_v1.md` §10 and the §12 C2 row (§9.3, §9.4, §12.1, §12.3 as they touch notes).
**No paid or live call was made**: every model is a fake (`StructuredClientFake` doubles). **The owner's real `tend` was
never run and no note of the owner's was opened**: every test puts a FAKE `tend` executable (a Python script over
synthetic notes written into the test's tmp directory) on `LEARNLOOP_NOTES_TEND`, and `conftest` sets
`LEARNLOOP_NOTES_TEND=off` for everything else, so no test can reach the real one (it is on carson's `PATH`). `tend`'s
contract was read from its own source only (`~/.local/src/tend`: `SPEC.md` §3/§3b, `src/tend/cli.py`, `search.py`,
`remote.py`, `chunk.py`, `config.py`); that repository was not modified. Every ad-hoc script ran with an empty, existing
`HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR` and `LEARNLOOP_NOTES_TEND=off`. No owner vault was opened,
`~/.config/learnloop` was not read, and nothing ran against `fixtures/linear_algebra`, `fixtures/probability` or
`fixtures/arxiv_v2`. Display and learner-voice records only: **no successor**.

## What was built

| Piece | Where |
|---|---|
| Migration **229** (one migration): `learner_notes` (RAW_LEDGER: a snapshot of one note section, taken **only when linked**: tend reference = path, heading path, line; tend's content hash; title; heading; `captured_on` (the note's date as tend reports it, for "your note from 3 Oct"); `origin` `tend` \| `pocket_notes`; the text, bounded per note, with `truncated`; one row per (note, content hash)) and `learner_note_links` (RAW_LEDGER: `authorship` `ai` \| `learner`, `status` `proposed` \| `accepted` \| `rejected`, the passage (extraction, section, span) or the LO, `target_key`, the `how` (restates, questions, disagrees, applies, worked_it) and its one line, the state key and ledger row of the judgment, `goal_id`). CHECKs: the model only proposes, and a proposal names its LO, state, model and ledger row; the learner only accepts or rejects. Both append-only by trigger | `migrations/229_learner_notes.sql`; store `src/learnloop/db/stores/learner_notes.py` |
| Classification: `table_roles` (both RAW_LEDGER; no DERIVED table, so no replayer); AD `protected_tables` (both PROTECTED; `learner_note_links` READING, its target, how, line and state unread; `learner_notes` names no reading, its text, title, heading and tend reference unread), `column_classes` | `db/table_roles.py`, `adaptive_difficulty/protected_tables.py`, `column_classes.py` |
| Head fixture `migration_head_229` (renamed from 228; only 229 applied to a backup-API copy; rollback mode, header 1/1, integrity ok, FK check empty; exactly 229's 13 objects added, only `schema_migrations` gained a row; no note text) and every head path and migration-chain diff moved to 229 (48 test files, the sanitizer script, the two reference scripts) | `fixtures/migration_head_229/README.md`; `tests/test_learner_notes_migration.py` (`C2_ADDED_OBJECTS`) |
| **The one adapter** (§10.1): `tend search -k K --json --local --notes-only [--words] -- QUERY` and `tend serve`'s `read` op, each a subprocess with a timeout (`notes.tend.timeout_seconds`). The JSON shapes were confirmed from tend's source (`cli._print_hits`: `{"results": [Hit.as_dict()], "warning"}`; `cli.serve` / `remote.read_indexed`: `{"text": <whole file>, "title", "id"}` or `{"error"}`). LearnLoop keeps the hit's heading section: from its line to the next heading of any level, headings in code blocks ignored (tend's own chunk boundary, `chunk.split`). A read tend refuses (a folder tend marks private, a file it no longer indexes) drops the note; when `tend serve` cannot answer at all (would not start, timed out, unreadable output, no `read` op) the work waits for tend and **no file is ever opened by LearnLoop** (Codex review F1: tend's `private` setting is the only privacy gate, and LearnLoop cannot see it). A hit whose line now opens another heading is dropped (Codex review F8). **The allowlist** `notes.tend.paths` (default grove notes, Quicknote, the Obsidian vault, `~/org`; project repositories are not in it): a hit outside it, another machine's hit, or a relative path is dropped before anything is returned, stored or sent. `notes.tend.lexical_only` adds `--words`. **tend absent** (no executable; `LEARNLOOP_NOTES_TEND=off`) hides every notes feature | `src/learnloop/curriculum/notes_tend.py` |
| **Candidates without a model** (§10.3): for each `needed` line of the deliverable's current path (C0b's `path_view`, so withheld sections are already gone), `tend search` with the LO's title and with the title of each section the path names for it (the primary and the alternates): heading sections, one per section, at most `notes.max_candidates`, in tend's own order | `source_retrieval/note_links.py` `path_targets`, `candidates` |
| **One listwise `note_link_judge` per LO** (§10.3): the LO's title and statement, its primary passage's lead (C0a's `peek`, protection read now), the candidate notes' text (tend's read op). Per note `discusses` (`about` passage \| topic, `how`, one line) or `unrelated`. **The ChatGPT plan only** (§10.4, Q6): a route whose provider type is not `chatgpt_plan` is refused before anything is sent (`plan_only`); the background run is `plan_fallback.quiet()` (no offer, no grant); `plan_fallback.PLAN_ONLY_TASKS` makes `offer_blocker` refuse the task, so routing never offers OpenRouter for it and no grant routes it there; with the plan down the run ends `waiting` and the next read tries again; nothing asks. C0a's `CoverageGuard` re-reads the passage's protection before each request and inside the write; `NotesGuard` (Codex review F2) re-reads the notes' authorization (`notes.enabled`, tend present, the allowlist, Pocket Notes folders and `lexical_only` as the run started) at the same points. The answer must give exactly one verdict per candidate and `about`/`how` for each `discusses` (Codex review F12; otherwise retried, never recorded or checkpointed). The judge's receipts keep no prompt text (Codex review F3, `execution.withhold_receipt_input`) | `note_links.judge_target`, `plan_route_is_plan`; `ai/plan_fallback.py` |
| **Stored as proposals**, cached by state: a ledger verdict per candidate (`judgment_ledger`, task `note_link`, the note named by a digest, never its path), link rows and snapshots of the linked notes only, one transaction. The same state (LO, statement, passage lead, each candidate's tend hash and text) is never judged again; a new content hash is a new state, so the snapshot is refreshed and the link re-judged (§10.3). Each deliverable's topic shows its **current** state's proposals (Codex review F7): a shown-state marker (`judgment_ledger` task `note_link_shown`, judge `exact_key`, per goal and LO) is appended when the state changes, including a state judged before (reused, never repaid) and no candidates (nothing shows) | `note_links.judge_target`, `state_key`, `effective` |
| **One tap hides** (`notes.decide hide`: a `learner` `rejected` row and a `learner_card` verdict); *undo* writes the learner's `accepted`. The learner's newest row per (note, LO) (or per (note, passage) for a link made by hand) stands across re-judgments, so a hidden link stays hidden; on a proposal it is a decision only, so *undo* shows the topic's current proposal (Codex review F6). **Link by hand from the Reader** (`notes.link`: the passage menu's *link one of your notes…*; the note is read again through tend, inside the allowlist, and snapshotted; the learner's link is never re-judged and shows its note's current snapshot, the text last read (a `judgment_ledger` marker, task `note_snapshot_current`: a note changed back shows its earlier text again, Codex re-review F13); the next background run finds the heading again through a words-only tend search and re-snapshots a changed text (or makes an earlier snapshot of the same text current) without writing a link row, and only while the learner's link still stands (Codex review F8, F9)) | `note_links.decide`, `link_by_hand`, `refresh_learner_links` |
| RPCs (desktop only, pinned): `notes.path` (the notes on a deliverable's path lines, by LO; starts the background linking once a local day per path), `notes.marks`, `notes.passages` (Compare's band, with each note's take text), `notes.search` (no words: the passage's section title; the learner's words: **words only**), `notes.link`, `notes.decide`. Prompt contract `notes` (absent while off or tend absent) | `src/learnloop_sidecar/handlers/notes.py`; `handlers/reader.py` |
| **Display** (§10.2, §10.3): `›` in the margin beside the passage (text and the original PDF's gutter, after the cue marks and ⇄: the learner's own mark, outside the cue budget), opening the note(s) in the learner's voice with title, heading, date, "linked by LearnLoop's model" / "linked by you", the model's one line (◇), *hide* and *undo*; "handwritten · transcribed by Pocket Notes" for a Pocket Notes page; the deliverable path line's "› your note from 3 Oct"; Compare's *your take* band ("from your notes", both the by-book band and the table by point's whole-comparison take) with *use as my take*, which keeps RW4d's existing `learner_connects` take quoting the note (`From your note “Title › Heading”, 3 Oct: “…”`, within RW4d's 1000 characters; before a keep it waits as a typed take does); *link one of your notes…* in the passage menu | `apps/learnloop-tauri/src/screens/reader/ReaderNotes.tsx`, `notesContext.ts`, `ReaderScreen.tsx`, `DeliverableSliceCard.tsx`, `CompareKeep.tsx`, `ComparePointTable.tsx`; DTOs, client calls, Rust passthroughs |
| Config `[notes]` `enabled` (true), `max_candidates` (8, keep) and `[notes.tend]` `binary`, `paths`, `pocket_notes_paths`, `lexical_only` (false), `timeout_seconds` (10, keep), `k` (5, keep); route `ai.routing.note_link_judge` (unset: the plan under T1); disclosure (`notes`); every key classified in `parameter_registry` | `config/schema.py`, `ai/routing.py`, `ai/disclosures.py`, `params/parameter_registry.py` |
| Defaults snapshots: every one of the 31 versions records "Curriculum C2's [notes] and ai.routing.note_link_judge … display and learner-voice records: no scoring, scheduling, projection or serving change", and all 31 fingerprints were recomputed with `defaults_fingerprint_for_version` (template `.pyc` cleared) | `config/template.py` |
| `learnloop curriculum report`'s notes row (§11): proposals, links hidden, hidden share, links kept by hand, takes written from a note; counts only, never a note's text or where it lives | `cli/curriculum.py`, `note_links.report_row` |

## A note is never a source, a generation input or evidence (§10.2; tests)

- **Statically** (`tests/test_notes_never_read.py`): the only source files naming `learner_notes`, `learner_note_links`,
  `note_links` or `notes_tend` are the adapter, the store, the linking service, the notes handler, the report's CLI and
  the two registries that classify the tables (rebuild roles; AD's guard, which refuses them).
- **By the import graph** (grimp, same file): no module of `find_sources`, `corpus` (`teaching_scope`), PF generation
  (`ops.pf_generation`, `ops.pf_calls`), `attempts` (the blind grader S1 and evidence), `tutor` (the tutor and
  teach-back; the teacher's item minting is TE1, not built), `adaptive_difficulty`, `diagnosis`, `scheduling`,
  `substrate` (replay, projections), `learner`, `goals`, `hints` or `daily_plan` reaches the notes' modules; the only
  importers are the sidecar and the CLI. An import-linter contract (`notes-are-never-a-source-or-evidence`) keeps it.
- **Dynamically**: with a sentinel note linked, the coverage judge, the scope resolver and the path judge (C0a/C0b's
  later calls) never see its text, and no source artifact names it.
- AD reads neither table (`test_ad_protected_tables`), as §9.4 requires.

## C2 tests (§12.3)

`tests/test_notes_linked.py` (15): the adapter drops hits outside the allowlist and another machine's; the command
carries `--json --local --notes-only` and the query after `--`; `lexical_only` adds `--words`; reads go through tend's
read op and a refused (private) note is dropped; without a read op the file is read, inside the allowlist only; a
stalled tend times out; tend absent hides the features; the section slice follows tend's boundary; the path links the
two notes that discuss it (a Pocket Notes page labelled) and stores only those (no unrelated, outside, remote or private
note in any prompt or row; the ledger names notes by digest); the same state is not judged twice and a new content
hash is; one tap hides and the link stays hidden across a re-judgment, *undo* shows it again as the model's; a link by
hand from the Reader (search by the section, then words only), refused outside the allowlist, listed in Compare's band
with its take; a metered route is refused (nothing sent) and plan-down waits with no offer; switched off every RPC
refuses, no tend call, no model call, nothing written, and the prompt contract equals the no-tend one; the contract
key only when on and tend installed; the RPCs pinned desktop-only; the report counts without text.
`tests/test_learner_notes_migration.py` (4, one durability). `tests/test_notes_never_read.py` (3).
Frontend: `readerNotes.test.tsx` (6) and two Reader-level tests in `compareKeep.test.tsx` (the `›` mark beside its
passage opening the note; the passage menu's *link one of your notes…*; without `notes` in the contract nothing is read
or drawn and the menu is today's).

## Decisions taken here (open to the owner or the landing)

1. **`--local --notes-only` beside the spec's `tend search -k K --json [--words] QUERY`.** Both only narrow: `--local`
   keeps the search on carson (another machine's hits would be dropped by the allowlist anyway, after an ssh round
   trip; §10.4 "notes stay on carson"); `--notes-only` is tend's own exclusion of docs in project repositories, a second
   guard beside the allowlist. The query follows `--`, so a title starting with `-` is never read as a flag.
2. **The read op is the privacy gate; there is no file fallback** (Codex review F1). tend's `read` refuses folders
   tend marks private (its `private` setting: "never handed to models"); `tend search` on the CLI does not filter them.
   So a note tend refuses to read is dropped, and when `tend serve` cannot answer at all the work waits for tend.
3. **The learner's typed search is words only** (`--words` whatever `lexical_only` says): §10.4's promise is that
   LearnLoop's queries to tend's meaning search are LO and section titles, never the learner's text. A search with no
   words uses the passage's section title (meaning search unless `lexical_only`).
4. **Which LOs:** the `needed` lines of the current path, not prerequisites and not a line the learner skipped (the
   spec's "each needed LO"). A path not judged yet links nothing; linking follows the path.
5. **Where a link anchors:** the judge says whether a note discusses the passage or the topic; both are stored with the
   LO's primary passage as the anchor (the margin mark sits at its start span), and the hide is per (note, LO), so a
   re-judgment that moves a hidden note from the passage to the topic stays hidden.
6. **A judgment's record without links:** every candidate gets a ledger verdict (`discusses` / `unrelated`), so a
   judgment that links nothing is still remembered and not paid again. Each deliverable's topic shows its current
   state's proposals (Codex review F7): A, then B, then A again shows A's links again with no new call.
7. **When the background linking runs:** when the Guide's slice shows a ready (or stale) path and asks for its notes
   (`notes.path`), at most once a local day per path (its LOs and primary sections), and again after a run that waited
   (plan down, tend unreachable). While a run is going the slice reads the path again every 3 s, and every 60 s while
   it waits (Codex review F4, `NOTES_POLL_MS`, a UI cadence labelled `keep`); its end refreshes the marks too. The model call layer reuses an identical prompt's answer,
   so a hash change whose section text is the same costs nothing.
8. **The `how` line is shown as the model's (◇)** beside the note, which stays in the learner's voice: the note is the
   learner's words, the line about it is not.
9. **No `METERED_PRICE_SETTINGS` entry for `note_link_judge`** (the spec's §12.1 general rule): the route is never
   offered, so it needs no price gate; `PLAN_ONLY_TASKS` is what keeps it on the plan.
10. **The judge's receipts keep no prompt text** (Codex review F3): `execution.withhold_receipt_input` leaves
    `input_text` empty for this route; the prompt and schema hashes, the declared request identity (receipt recovery
    still works), usage and the verdicts stay.

## Constants

Structural bounds, each labelled in its module: `NOTE_CHARS = 3000` (one note's text as stored and sent; a prompt
bound), `LEAD_CHARS`, `STATEMENT_CHARS`, `HOW_LINE_CHARS`, `QUERY_CHARS`, `RESOLVE_K = 25` (tend hits scanned to find
a hand-linked heading again, Codex review F8) and the frontend's `NOTES_POLL_MS` (a UI refresh cadence, F4); the file
fallback's `FALLBACK_MAX_BYTES` is gone with the fallback (F1). Config `keep` bounds: `notes.max_candidates` (8: a prompt bound), `notes.tend.k` (5: sections per query),
`notes.tend.timeout_seconds` (10: a stalled subprocess never holds a job). The two switches and the folder lists are
structural or privacy settings. No weight, margin or threshold: which note discusses what is the model's judgment.

## Gate (this step; targeted, memory-capped)

See `docs/reviews/curriculum-c2-notes-linked-codex-review.md` (the Codex review fix step's targeted gate, with
exact pass counts). The full suite runs once, in the landing gate on the merged tree.

## Landing notes

- **Migration number.** 229 on main's 228. If another stage lands a 229 first, renumber this one, rebuild
  `migration_head_<N>` from main's head with it applied, and move `C2_ADDED_OBJECTS` into the chain diffs.
- **Expected conflicts:** `config/template.py` (one note per version and the 31 hashes: recompute),
  `tests/cli_help_snapshot.json` (`curriculum report`), the head path in ~48 tests and the reference scripts, the
  migration-chain lists, `src-tauri` command lists, `api/client.ts` / `dto.ts`, `ReaderScreen.tsx` (the margin marks,
  the passage menu), the generated reference notes and the desktop catalog's counts (`desktop_validate.py`: 297 TS /
  289 entry-build / ACTIVE 302).
- **No successor**, no algorithm version, no replayer.

## Open questions

1. ~~A private tend folder inside the allowlist, with `tend serve` down.~~ Settled by Codex review F1: the file
   fallback is dropped; notes show only while `tend serve` answers.
2. **Remote notes.** The laptop's notes are left out (`--local`). Should LearnLoop on carson ever read them (tend's
   `read` over its remote)? The spec says notes stay on carson; nothing is built.
3. **Prerequisite lines.** Only needed topics are linked (decision 4). Should a prerequisite's line get notes too?
4. **A hidden link's undo after the reading changes.** *undo* stays beside a hidden note for the rest of the reading
   (Codex review F5); there is no list of hidden notes to bring one back later (Settings could list them).

## Landing onto main

The branch `curriculum/c2-notes-linked` (worktree `learnanything-ad1`, stage tip `bb4b647e7d`) lands onto main (final
main merged: `6318d46cfe`). The orchestrator fast-forwards main and pushes. No paid or live call was made; the owner's `tend` was never run and no note
of the owner's was opened (every notes run used the FAKE `tend` of `tests/notes_fixtures.py` over synthetic notes, or
`LEARNLOOP_NOTES_TEND=off`).

### F13 (Codex round 3), fixed first

Codex round 3 (job `20261101-101544-wk64cb`) confirmed F1, F2 and F14 and reopened F13: a delayed AI judgment
reactivated an obsolete snapshot. Fix `bb852870fb`: **recording AI proposals never advances the
`note_snapshot_current` marker.** `_store_snapshot` only stores (a proposal keeps the snapshot it judged through its
link row); `_show_read`, called only by a read of the note made to show it (`link_by_hand`, `refresh_learner_links`),
advances the marker by compare-and-set on the revision (`store.current_revisions`, the newest marker's `rowid`) the
read captured before asking tend. `store.current_notes` reads markers only (the newest-snapshot fallback is gone). Two
failing-first regressions (the exact interleaving; a refresh whose marker was advanced meanwhile). Files:
`note_links.py`, its store `db/stores/learner_notes.py` (used only by `note_links`), `tests/test_notes_linked.py`.
`WAITING_RETRY_SECONDS` is not registered: the registry's module-constant audit scans only `MODULE_INVENTORY`, which
lists no C2 module. The scoped verify (job `20261101-102907-K457GP`) found the delayed-judgment case fixed and two
concurrent-refresh orderings open, ruled Low by R6 (below; details in the codex-review record).

### Merges

| Commit | What |
|---|---|
| `698ea6525e` | Merge of main `0708e12a18` (substrate facet write-on-change): no conflict. |
| `4ede2ff1af` | References regenerated on the merged tree (line citations moved by the F13 edit and round 2): `db_validate_reference` errors [], desktop catalog reproducible (297 TS / 289 entry-build / ACTIVE 302), vault valid; round-3 verify and R6 recorded. All 31 defaults fingerprints equal `defaults_fingerprint_for_version` (template `.pyc` cleared). |
| `ed113b9101` | Gate fixes (below): the notes adapter's two `tend` launch sites approved in the Codex lockdown list; the plan-only refusal says OpenRouter "isn't offered". |
| `57d2d1b8b8` | Merge of main `82ba4c8dce` (Reader RW5d P2b Manim). Conflicts: `config/template.py` (31 snapshot hunks: main's notes and C2's note both kept, every fingerprint recomputed with `defaults_fingerprint_for_version` after clearing `.pyc`; a second pass changed 0), `tests/test_judge_routes.py` (the disclosure set lists both `figure_rich_author` and `note_link_judge`, both sides' assertions kept), 450 generated reference notes (main's side, then regenerated). `src-tauri` (`commands.rs`, `main.rs`) auto-merged with both sides' passthroughs (`notes_*`, `figure_rich_cancel`, `figure_manim_opt_in`). Migration 229 stays 229 (main's head is 228); head fixture `migration_head_229`. |
| `6d1bd6cc56` | References and catalog regenerated: `db_validate_reference` errors [] after composing the hand-kept prose counts (**360 table notes, 1104 leaves in 78 sections**: base 1091, RW5d P2b +4, C2 +9); `desktop_validate.py`'s pinned inventory composed (**299 TS, 291 entry-build, ACTIVE 304**: each side added 2); vault valid. |
| `6322444431` | Merge of main `0d607bdfe9` (Reader follow-ups Nov 1). Conflict: `source_retrieval/section_coverage.py`, where main gave `CoverageGuard` a `gate` hook (C1's automatic refresh, judged on the same snapshot; a closed gate raises `GateClosed`) and C2 gave it `also`/`also_refusal` (`NotesGuard`'s notes authorization on the same snapshot). Composed: one guard takes both; on each snapshot `also` is judged first (its refusal wins), then the vault check, then the gate (closed and still published: `GateClosed`; replaced meanwhile: read again), then protection; `check` raises the refusal's own type through C2's `(reason, exception)` refusal; `admit` settles the outer gate on either (`GateClosed` is a `ProtectionChanged`). C1 passes only `gate`, C2 only `also`. 443 generated reference notes: main's side, then regenerated. No `src-tauri` or template conflict. |
| `f6676e9375` | References and catalog regenerated (`db_validate_reference` errors [], desktop catalog passed at 299/291/ACTIVE 304, vault valid); `test_landing_the_coverage_guard_composes_c1s_gate_and_c2s_also` pins the composed hooks. |
| `a39f7f467b` | Merge of main `6318d46cfe` (RW5d G-SM14 probe record: one new review doc, nothing else): no conflict; `db_validate_reference`, `desktop_validate` and `validate_vault` pass; no test rerun (documentation only). |

### Gate

Every run under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, `LEARNLOOP_NOTES_TEND=off`,
`TMPDIR` outside the worktree; pytest in `systemd-run --user --scope` (full suite 10G under
`flock /tmp/learnloop-fullsuite.lock`, the rest 5G), vitest `--maxWorkers=4`. No live model call.

| Step | Tree | Result |
|---|---|---|
| `uv run lint-imports --no-cache` | `4ede2ff1af`, `6d1bd6cc56`, `f6676e9375` | **37 kept, 0 broken** each time |
| Full pytest (`flock /tmp/learnloop-fullsuite.lock systemd-run --user --scope --quiet -p MemoryMax=10G -p MemorySwapMax=2G -- <env -i> uv run --no-sync pytest -n 8 -p no:cacheprovider --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml=…`) | `4ede2ff1af` (first merge) | 23151 passed, 89 skipped, 47 xfailed, **3 failed** (36:55): C2 defects, below; fixed in `ed113b9101`; the affected 14 files then **288 passed** |
| Full pytest, same command | `6d1bd6cc56` (after the RW5d P2b merge and the fixes) | **23293 passed, 90 skipped, 47 xfailed, 0 failed** (38:19) |
| Full pytest, same command | `f6676e9375` (after the Reader follow-ups merge; **final**) | **23357 passed, 90 skipped, 47 xfailed, 0 failed** (39:12) |
| Targeted pytest after the third merge (`-n 6`, 37 files: notes, section coverage, C0b, C1, deliverables, judge routes, lockdown, plan-first transport, architecture, mobile allowlist, desktop RPC contract, serializer snapshot, AD guard/protected tables, table roles, and every test file the Reader follow-ups landing touched) | `6322444431` | **1190 passed** |
| Durability lane (`pytest -m durability -n 6`, 5G scope, under the flock) | `ed113b9101`, `6d1bd6cc56`, final | **179 passed, 1 skipped** (`ed113b9101`, `6d1bd6cc56`); final (`f6676e9375`): **179 passed, 1 skipped** |
| Owner lane (`pytest -m owner_vaults -n 6`; `LEARNLOOP_OWNER_VAULTS` = fresh backup-API copies, `learnloop.db.copies.copy_tree_with_databases`, of `fixtures-local/owner-copies-mvp035` in the gitignored `fixtures-local/landing-c2/`, then `landing-c2b/`) | `ed113b9101`, `6d1bd6cc56` | **83 passed, 2 failed, 4 skipped** both times: exactly the two known failures, `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies::…[arxiv_v2]`; no new owner test |
| Frontend: `npm install`, `npm run typecheck`, `npm run frontend:build` | `ed113b9101`, `6d1bd6cc56`, final | ok each time |
| Whole vitest (`npx vitest run --maxWorkers=4`, 5G scope) | `ed113b9101` | first run 2 failed / 2354 passed under load (each passes alone 3/3, below); whole rerun **246 files, 2356 passed** |
| Whole vitest | `6d1bd6cc56` | **247 files, 2367 passed** |
| Whole vitest | final (`f6676e9375`) | **247 files, 2367 passed** |
| `cargo check --manifest-path src-tauri/Cargo.toml` | `4ede2ff1af`, `57d2d1b8b8` (src-tauri auto-merged with RW5d P2b's passthroughs) | ok; the Reader follow-ups merge changed nothing under `src-tauri` |
| DB reference, desktop catalog, vault | after each merge | `db_validate_reference` errors [], `desktop_validate` passed (final 299 TS / 291 entry-build / ACTIVE 304), `validate_vault` passed |

**The three full-suite failures were C2 defects the stage's targeted gates never ran** (each failed alone 3/3 before the
fix, deterministically):
- `test_codex_lockdown_round3::test_every_process_launch_site_is_approved`: `notes_tend.search` and
  `notes_tend._serve_reads` start `tend` (`subprocess.run`) and were not on the reviewed list. Reviewed and approved:
  argv lists, no shell, a timeout, only the configured `tend` binary (`notes.tend.binary`, `LEARNLOOP_NOTES_TEND`, else
  `tend` on `PATH`; absent or `off` starts nothing), no model call.
- `test_plan_first_transport::test_every_task_under_code_defaults_resolves_tool_free_and_never_codex[True-paused]` and
  `[True-signed_out]`: the contract is that a blocked offer's message says "isn't offered" or "nothing is offered";
  C2's plan-only refusal said "never offered". The message now reads "Your notes are read only by the ChatGPT plan, so
  OpenRouter isn't offered for this; it waits for the plan." (no behaviour change).

### Smoke on fresh owner copies (`fixtures-local/landing-c2-smoke/`, driver `scripts/smoke.sh`)

**Setup.** Fresh backup-API copies of the three mvp035 owner copies, neutralized under each side's own code
(`neutralize3.py`: every route at the `127.0.0.1:9` blackhole, key variable unset; rewrite, rerank, dense and
embeddings off). Main's code `git archive 0708e12a18`, the branch's `git archive 4ede2ff1af`, each with `src/`,
`migrations/` and `tests/`. Each copy under its own side's code: a bare `upgrade`, the primary desktop start,
`migrate_vault`, `rebuild-derived-state`. Every process ran under `env -i` (empty `HOME`, `CODEX_HOME`, config dir,
`LEARNLOOP_NOTES_TEND=off` unless the harness named the fake) with an audit hook logging every process start and
refusing non-loopback sockets and Codex starts.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| upgrade (main and branch) | mvp-0.35 → mvp-0.40; branch head **229** (229 applied cleanly), main 228 | same | same |
| rebuild-derived-state | 8 LOs, 70 attempts | ok | 3 LOs, 3 attempts |
| Today (3 queue variants, frozen clock), branch vs main, `notes.enabled` default, tend absent | **identical** (525,266 bytes) | identical (740,827) | identical (344,204) |
| daily plan dump (sidecar handlers, frozen clock, deterministic ids), branch vs main | **identical** (84,696 bytes) | identical (124,021) | identical (32,433) |
| tend absent: the six `notes.*` RPCs | all `notes_unavailable`; prompt contract has no `notes` key; nothing written | same | same |
| `rebuild --shadow --json` (branch copy) | **0/0/0**, live unchanged | 0/0/0 | 0/0/0 |

**With the FAKE tend over synthetic notes** (linear_algebra, a further copy; `[notes.tend]` allowlist naming the fake's
synthetic folders; harness `scripts/notes_smoke.py`):
- `notes.path` for a goal with no deliverable (the copies have none): no lines, no linking, no tend call.
- **Linking without the plan waits:** a path with one needed topic (a real LO and a real reading section of the copy,
  supplied by the harness since the copies have no judged path): `notes.path` started the run inline, which searched
  tend twice and read once, then ended **`waiting`, reason `plan_only`** (the vault's route is the blackhole
  `openai_chat`, not the ChatGPT plan): nothing sent, no link. The next read restarted nothing (0 tend calls; F14).
- `notes.search` by the passage's section title found both synthetic notes; the learner's words searched with
  `--words` only; every search carried `--json --local --notes-only`.
- `notes.link` by hand: the passage's `›` mark shows the note "linked by you"; `notes.passages` gives the take text
  `From your note “Smoke notes › …”`; `notes.decide hide` empties the marks, `keep` brings it back; a note outside the
  allowlist is refused (`not_allowed`).
- Rows: 1 snapshot, 3 link rows (link, hide, keep), 4 ledger rows (the link, its current-snapshot marker, hide, keep);
  `rebuild --shadow` 0/0/0 afterwards.
- **0 new `model_call_receipts`** across all 19 smoke databases (probability's 56 historical rows, 42 completed and 14
  failed, unchanged in each copy; the others have none).
- **Audit:** 6 entries, all the fake `tend` (4 `search`, 2 `serve`); **no socket connect of any kind**, nothing
  refused, no Codex process.

The smoke ran at `4ede2ff1af` against main `0708e12a18`, before the RW5d P2b and Reader follow-ups merges and the
gate fixes; it was not rerun on the final tree. C2's own diff against main is unchanged by those merges apart from
the composed `CoverageGuard` (covered by the targeted tests and the full suite) and the refusal wording; C2 adds
nothing to Today or the plan, and both landings recorded their own smoke on fresh copies.

### Orchestrator rulings (verbatim)

- R1: "F1's removal of the file fallback is accepted: notes show only while tend serve answers (privacy fails closed). Flagged to the owner as a departure from spec §10.1's fallback wording."
- R2: "tend search runs with --local --notes-only; the learner's typed search is words-only. Accepted (narrowing only; laptop notes are not read from carson). Flagged to the owner."
- R3: "note_link_judge has no METERED_PRICE_SETTINGS entry because it is plan-only and never offered OpenRouter. Accepted."
- R4: "The shown-state (note_link_shown) and current-snapshot (note_snapshot_current) markers live in judgment_ledger rather than a new table. Accepted for v1; no migration change."
- R5: "Notes link only to needed topics on the path; a list of hidden notes in Settings is queued as a follow-up."
- R6: "F13 remainder ruled Low under the proportionate protection bar and the stuck-loop rule (fourth round on the snapshot-currency class). It needs two concurrent background refreshes of the same hand-linked note racing an edit; the only effect is that the margin shows the note one edit stale until the next refresh. There is no data loss, no model call and no evidence. Queued follow-up: give each read a monotonic token taken at read start and publish by token order, with unchanged reads advancing the fence."

### Owner notes

- **Migration 229** (`learner_notes`, `learner_note_links`) applies on `learnloop upgrade`; no successor, no algorithm
  version, no `rebuild-derived-state` needed for C2 (run it anyway after the mvp-0.40 upgrade, as that upgrade prints).
- **Notes show only while `tend serve` answers** (R1): there is no file fallback, so with tend's server down linking
  waits and nothing is read around it. LearnLoop searches with `--local --notes-only` (R2): the laptop's notes are not
  read from carson, and project-repo docs are excluded twice (tend's flag and `notes.tend.paths`).
- **The ChatGPT plan only:** with the plan signed out or paused, linking waits quietly; OpenRouter is never offered for
  it. Sign in with `learnloop ai signin chatgpt` for linking to run.
- Linking needs a deliverable with a judged path (create one in the Guide); only needed topics get notes (R5).
- Kill switch: `[notes] enabled = false` (or tend absent) hides every notes surface; the Reader, the path and Compare
  are then today's exactly.

### Open items

1. **R6 follow-up:** monotonic read tokens published by token order, with unchanged reads advancing the fence (the
   two concurrent-refresh orderings of the round-3 verify).
2. **R5 follow-up:** a list of hidden notes in Settings (bring one back after the reading changes).
3. Open questions 2 (remote notes) and 3 (prerequisite lines) above stay with the owner.
4. Owner-flagged departures: R1 (no file fallback, spec §10.1) and R2 (`--local --notes-only`, words-only typed search).
5. Two vitest tests failed once under full-run load and passed alone 3/3 and in a whole rerun
   (`sideBySideCorrespondence.test.tsx` (iv), `sketchSandboxReview.test.tsx` "played to t_max"): timing-sensitive,
   not C2's code.
