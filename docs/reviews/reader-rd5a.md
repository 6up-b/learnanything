# Reader workbench v2, RD5a: the menus, backend half

The backend half of stage RD5 of `docs/specs/spec_reader_workbench_v2.md` (§0 item 7, §9, §10.6, §16's RD5 row).
Branch `reader/rd5a-menus-backend`, cut from the RD4 fix round's backend tip `6453e5f9b7` (not yet on main; it lands
with that round's frontend half). The frontend half (the split source menu and the pad menu wired to every verb, What
this knows, Compare and Teach me opening windows) builds on what is listed here.

**What it delivers.** `passage.promoted` with its polled, cancellable job (`passage.promoted_job`,
`passage.promoted_cancel`), `passage.knows` (What this knows as one read), one machinery for the menus' promoted rows
and the pads' proposals (`learnloop.passage_union.elsewhere`), the proposals RD4a deferred (correspondents and search),
the verb table below, Rust passthroughs and typed `client.ts`/`dto.ts` entries. No UI, no migration, no config key, no
kill switch, no algorithm tag (§15.3: "RD5: none; promoted rows are display"), no prompt change, nothing on the phone,
no model call in any test.

## 1. Promoted rows

`passage.promoted {objectKind, extractionId?, spanId?, t?, annotationId?, blockId?, windowId?, deskId?}`; the object
is a passage, a transcript cue (its span, or a time), a highlight or margin note (its annotation and the passage it
sits on), a window header (the passage in view) or a pad line (its block: its passages are its own links and its lift
lineage's, `pads.emission.passages_of`). Reply `{objectKey, rows, cap: 4, pendingJob: {jobId}, paid}`.

**Candidates.** From the union read of the object's passages, at once, no model:

| Kind | Glyph | When | Reason | Action | Learner act |
|---|---|---|---|---|---|
| `question` | ? | an exchange of the learner's tied to the passage | "you asked the tutor about this on <date>" | open the thread (`ContentRef` thread) | the exchange's time |
| `adjustment` | ◇ | an exchange whose question was read as a misconception | "the tutor corrected how you read this passage" | open the thread | the exchange's time |
| `gap` | ◇ | a misconception or prerequisite named from the learner's words placed on the passage (not unanchored) | "LearnLoop read your words about this on <date>" | `knows` (What this knows, the gap) | the gap's time |
| `your_words` | › | a pad line linked to the passage | "you linked this passage to a pad line" | open the pad at the block | the link's time |
| `carried` | ◌ | a question still carried from the passage | "since <date>" | the carried question | its `since` |
| `note` | › | a margin note with words | its first 80 characters | the annotation | its time |
| `figure` | ◇ | a figure made for the passage | "help, not a check" | `figure.open` | none |
| `next_step` | § | another passage the cue judge tied to the same learner problem | the link's relation in words | open the passage beside | none (checked, the link's `pick_rank`) |

From the job (`passage.promoted_job`), polled through the client's one poller, cancelled when the menu closes (a newer
menu on the same desk supersedes it):

| Kind | Finder | Checked |
|---|---|---|
| `correspondent` | `section_coverage.correspondents` for each passage's section (no model): another book's section the coverage judge says treats the same learning objects; with none, its keyword search hits | judged: yes; keyword hits: no ("found by search, not checked") |
| `elsewhere` | `search_spans` over the other sources with the passage's (or the pad line's) words, deep only with the learner's OK to use AI and retrieval on; then `verify_spans` picks at most four | a pick: yes ("says this in other words"); without a judgment, every hit: no |

A due check is never a row: nothing about a due check may show before it opens (§12.6.1).

**Order** (`passage_union.promoted.rank`, one function). *An orchestrator default the owner may override* (option A of
the three put to the orchestrator; the spec says only "ranked from the union read and the learner's history for this
object"):

1. rows that carry an act of the learner's on this object first, the most recent act first;
2. then the rest by their own judge's rank, checked before unchecked;
3. one row of each kind before a second of any kind;
4. ties by row id;
5. a row the learner dismissed or marked "not this" on this object is left out;
6. at most four (the spec's attention limit, never a score cut). No weights.

**The follow-up (option C, spec §17).** A ranking learned from the labels (opened versus dismissed or "not this"), with
A as its prior, once labels give training data. What C needs and what is stored now: each row's `rowId` is stable for
its object, kind and target, and `proposal.label` with `proposalKind: "promoted_row"` already keeps "opened",
"dismiss", "not this" and "ignored" per row (existing storage, no change). **Not stored: which rows were shown, and in
which position.** `proposal_labels.label` has no "shown" value and no position column, so recording impressions needs new
storage (a label value and a position, or an impressions table): not added here, as asked.

## 2. What this knows

`passage.knows {object}` → `{objectKey, sourceIds, places: [{extractionId, spanId, role, knows}]}`: each of the
object's passages with its whole union entry (annotations, pad blocks, exchanges and adjustments, gaps with their anchor
quality, passage links, figures, due-check hosts with nothing of the item, notes, authored questions, carried questions,
exposure; every row with its `alias`), and the passage's effective role (`exercise`, `solution`, … from
`corpus.block_roles`), which Make it practice reads.

## 3. The verbs and their server entries

| Verb | Objects | Server entry | New |
|---|---|---|---|
| Ask (a) | passage, cue, highlight, note, pad line | `companion.ask` (`padBlockIds` for a pad line) | existing |
| Note in margin (n) | passage, cue; pad line | `reader.create_annotation`; `pad.apply` `insert_block` (`payload.parent_block_id`) | existing |
| Append to “<target>” (w) | passage, cue, highlight | `pad.apply` (`insert_block` a `source_quote`, `link_anchor` with `annotationId`) and `reader.create_annotation` when the passage has no highlight; `pad.list` for the submenu; `desk.apply` `ensure_running_pad` / `add_to_stack` for "+ a new pad" | existing |
| Carry (c) | passage, cue, highlight, note, pad line | `carried.carry` (`originKind` selection/note/block, `anchor`) | existing |
| Open beside (b) | passage, cue, highlight | the first promoted row of kind `correspondent`/`next_step`/`elsewhere`, or `reader.correspondents`; then `desk.apply` `open_window` with its `ContentRef` | existing |
| Find in my sources (/) | every object with text | `search.everything` (and `search.job`) | existing |
| Compare (=) | passage, cue, highlight | `reader.library_compare` (a `question` and `anchor_span_ids`) or `compare_sources`; the window is `open_window` with `content: {kind: "compare", comparisonId \| query}` | existing |
| Show me (v) | passage, cue, highlight; a pad line with a linked passage | `figure.request` (`origin: "selection"`, the passage's `extraction_id`/`span_ids`; for a pad line, its passages from `passage.knows`) | existing (a pad line with no passage has no Show me) |
| Make it practice (p) | passage, cue | `reader.import_exercise` when `passage.knows` says the role is `exercise`, else `reader.author_section_question` | existing |
| Make it practice (p) | pad line | `author_practice_item` (the line as the prompt, the expected answer and the learning object chosen in the review sheet; the LO offered from `reader.span_learning_objects` of the line's passages) | existing; no server drafting from a pad line (§5 below) |
| Teach me this (t) | passage, cue, highlight; pad line | `lesson.turn` `{action: "open", entry: "reader_selection", selection: {extraction_id, span_ids}}` (a pad line: its passages; with none, `entry: "learning_object"`); the window is `open_window` with `content: {kind: "lesson", lessonId}` | existing |
| Submit this block as… (s) | pad line | `pad.submit_block` | existing |
| New desk from these (d) | window | `desk.apply` `create_desk`, `move_to_desk` | existing |
| Gather linked sources (g) | window | `desk.apply` (the client's §6.6 moves) | existing |
| Share a slot with the next (,) / Own slot (.) | window | `desk.apply` `pair` / `unpair` | existing |
| What this knows (i) | every object | `passage.knows` | **new** |
| Promoted rows | every object | `passage.promoted`, `passage.promoted_job`, `passage.promoted_cancel` | **new** |
| Insert: sketch cell (k) | pad | `pad.apply` `insert_block` (`kind: "sketch"`) | existing |
| Insert: a source piece (i, "a piece of another source…") | pad | `passage.content` (RD4's fix round), then `pad.apply` `insert_block` (`kind: "source_piece"`) | existing |
| Insert: marimo cell (m) | pad | none until RD9b (the one honest disabled row) | — |

## 4. Proposals (RD4a deferred)

`pads.proposals.propose_for_blocks(..., vault=)`, called after every pad batch, now finds, best first: a passage the cue
judge tied to the same learner problem (as before, ranked for this learner); else another book's section the coverage
judge says treats the same topic (`found_by: "correspondent"`, checked); else a passage found for the block's words by
keyword (`found_by: "search"`, "found by search, not checked"). None of them calls a model at the commit (meaning search
and its verification are the menu job's); without the vault only passage links are looked at. The order among the
finders is the same rule's: the learner-ranked judgment first, then judged coverage, then unchecked search. Still at
most one proposal per words version.

## 5. Deviations and open questions

1. **Make it practice from a pad line drafts nothing on the server.** The spec says it "drafts an item from this line".
   No drafter takes a learner's line today; one would be a new prompt (its own landing, with its identity pin). The
   entry named above prefills the review sheet with the line and asks the learner for the expected answer. Options for
   the owner: keep that; or add a drafter (a structured prompt, the line and its passages in, a draft item out) in a
   landing of its own.
2. **Impressions are not stored** (§1, option C): which rows were shown and in which position need new storage.
3. **The order is an orchestrator default** (§1); the owner may choose option B (a fixed kind order) or ask for C now.
4. **A window header's rows** are those of the passage in view (the client names it), not of the whole reading.

## 6. Tests

New: `tests/test_menu_promoted_rows.py` (promoted rows differ by passage, a table over six passages: an exchange, a gap,
a due check, a pad link, a carried question, nothing; reasons and actions; a due check never a row; judged rows through
the job, checked before unchecked; a dismissed row left out on its object; cancellation; the order rule; a cue by time
and a pad line by its passages; What this knows; params and the phone allowlist) and
`tests/test_menu_elsewhere_and_proposals.py` (search findings checked by the judge's picks or all unchecked;
correspondents judged first, the keyword fallback only without them; a pad block's correspondent and search proposals).
Edited: `tests/test_mobile_allowlist.py` (`READER_RD5A_RPCS`). Fail-first: on the base (`6453e5f9b7`'s `src`) both new
files fail at collection (the modules do not exist); the order's rules are each pinned by a case of their own.

## 7. Commands and results

Each pytest run: `-n 1 -p no:cacheprovider` through the scratch wrapper in a 3G scope.

| Command | Result |
|---|---|
| The two new files during the build | 19 passed; 3 passed |
| `tests/test_mobile_allowlist.py` with the new file | 381 passed |
| `scripts/affected_tests.py --files <the changed src files>` | asked for the full suite (the handler change reaches the sidecar) |
| The 75 files that import pads, desks, the union read, correspondents or section coverage, or use their builders, plus identity pins, structure ratchets, the four row-recording goldens, CLI snapshot, effective defaults, public tip guards, RD0 fences, sqlite copies, kill switches and architecture, two chunks, `-m "not arc_close"` | 1 failed, 1513 passed (architecture: the cue resolution imported the union's private `_range`; made public as `span_range`); 467 passed |
| Architecture, the menu files, the RD4 fix-round file and the RD0 reads, after that | 63 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `uv run ruff check` / `uv run lint-imports --no-cache` | All checks passed! / Contracts: 52 kept, 0 broken. |
| `uv run python scripts/check_gate_partition.py` | collected 33486: landing 33420 + arc_close 66 |
| `npm run typecheck` / `cargo check --offline` | exit 0, no errors / Finished |
| `generate_all.py`, then the four vault validators | VALIDATORS |

No identity pin, golden or structure number moved; no ledger row (no defect found in existing code).

## 8. What I did not verify

- A real `search_spans` deep search, `verify_spans` judgment or correspondents over a real library (fakes only; the
  owner-copy lane can time `passage.promoted` and its job over a vault's most-read reading).
- The landing gate, the full suite, `npm test`, `npm run frontend:build`.
