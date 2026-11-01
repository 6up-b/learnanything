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
