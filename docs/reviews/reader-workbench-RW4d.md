# Reader workbench RW4d: syntopic reading, kept (stage `reader-rw4d`)

Branch `reader/rw4d` (worktree `learnanything-rw4b`), base `main` at
`3988cf778` (the RW4b landing; migration head 213; AD1, RW2b+H3, RW1c and
RW4b on main). Spec: `docs/specs/spec_reader_workbench_v1.md` §1's RW4d line,
§7.8 in full, the compare paragraphs of §7.3 it extends (the table, the three
voices apart W2: source `§`, LearnLoop's inference `◇` labelled, the learner's
own take `›`), §3.4 item 15 (the relation mapping), §7.5 (`library_asks.kept_json`
/ `kept_at`, in RW4a's migration), §11 (`[reader_compare] keep_enabled`), §12's
row, §14 G18 and G43, §15's test list; UX `docs/specs/ux_reader_workbench_v1.md`
§3.4 (the `⇄` mark), §4.5, §4.10 (*your take*: "kept as your own note … isn't
read for gaps"), W10; sources spec §9.4 (`compare_sources`, its five relations,
quote verification G12) and §19 (keeping a comparison is the Reader's action).
Read: `reader-workbench-RW4a.md` (§9 note 3), `RW1c.md`, `RW4b.md` (§9 note 3:
the exercise view stores no proposals); P3 §7 (source objects stay proposals).

## 0. Plan (written before the code)

**Scope.** RW4d only: requested perspectives above the compare table; "Keep
this comparison" as source-object proposals; *your take*; *remove* (supersede,
never delete); `⇄` on passages with a kept comparison (the learner's own mark,
outside the cue budget) that reopens the table; "you compared these on …" on a
later library ask; Keep on the tutor's comparison (RW1c's `TutorOffers`); a
pure read of kept comparisons for the router's card (RW6b composes it into
`reader_activity_for_card`, which does not exist yet). Not here: RW4e's role
proposals, P3's review path (unchanged; nothing here promotes), a claim index
over passages the learner did not compare (§17), RW6b's card.

**No migration.** `library_asks.kept_json` / `kept_at` exist (209); proposals go
into `source_objects`, `source_object_versions`, `source_object_citations` and
`source_object_relations` (094, RAW_LEDGER) through `reader/source_objects.py`
(`author_source_object`, `link_relation`, `review_source_object`). No new
table, so no table role, replayer or head-fixture change.

**Backend** (`src/learnloop/source_retrieval/kept_comparisons.py`, beside
RW4a's `library_ask.py` for the same frozen-cycle reason; SQL in the registered
`db/stores/library_asks.py`):
- `RELATION_MAP` (§3.4 item 15): `equivalent` → `supports`, or
  `alternate_definition` when both kept claims are definitions;
  `different_assumptions`, `different_notation`, `complementary` → `refines`;
  `disagreement` → `contradicts`; `unclear` → `unresolved`. An unknown fine
  label is not kept (fail closed). The fine label is kept in `kept_json`.
- `keep(vault, repository, ask_id, takes=…)`: reads the **stored**
  `source_comparisons` row (`comparison_id`), never the client's table. Asks
  the one held-out predicate (`exam_material.exam_withheld`, the RW4b
  statement gate's call, failing closed) about every compared span **now**: any
  hit refuses the keep (`exam_material`) and writes nothing. Each compared
  source with a verified line becomes one `source_objects` row with one
  version (`object_type = 'definition'` when the block's effective role is a
  definition, else `'claim'`; `authorship = 'ai'`, `status = 'proposed'`, the
  extraction's `revision_id`; `content_json` holds the AI-written lines with
  their labels and the comparison id; one citation with span, block content
  hash and the verified quote). A line whose quote is no longer in its block
  (the source re-extracted) is not kept and is listed. Each verified relation
  between two kept objects becomes a `source_object_relations` row
  (`authorship = 'ai'`, `review_status = 'proposed'`, mapped type). `kept_json`
  records every object and relation id with its fine label, the relation's
  statement and quotes, and the takes; `kept_at` is set. Idempotent: a second
  Keep returns the first and only adds new takes.
- *Your take*: one `learner_connects` relation per take with `learner_text`,
  `authorship = 'learner'` (connect-it semantics), on a pair (two rows) or a
  claim (one row, `related_object_id` NULL). Not routed to learner-text gaps
  (UX §4.10's row for *your take*) and never evidence.
- `remove`: every object gets a `superseded` status version
  (`review_source_object`); every relation (AI and learner) gets a superseded
  successor row (`version_ordinal + 1`, same endpoints and text) — append-only,
  nothing deleted; `kept_json` records the removal, `kept_at` cleared.
- The tutor's comparison: Keep takes a `tool_call_id`; the comparison is the
  run's `result_ref`, and only the sources that run showed (`result_keys`, after
  the tool view's withholding) are kept. It records a `library_asks` row with
  `caller = 'tutor'` (the CHECK already allows it) holding the comparison id and
  the kept ids. The comparison itself still runs only on the learner's press
  (RW1c, G59).
- `kept_marks(extraction_id)`: the spans of the open reading with a live kept
  comparison (for `⇄`), omitting any comparison with held-out material now;
  `reopen(ask_id)`: the table rebuilt from the stored comparison (RW4a's
  `compare_table`), refused while any of its spans is held out;
  `compared_on(keys)`: for a later library ask, the kept comparisons sharing
  its passages ("you compared these on 3 Oct").
- `kept_comparisons_for_card(lo_ids, as_of)`: a pure read for RW6b (typed
  entries: ask id, kept date, sources, relation types with fine labels, take
  count); nothing renders it yet. Nothing in it is evidence.
- Perspectives: `reader.library_compare` takes `requested_perspectives` (≤ 4,
  ≤ 80 chars) passed to `compare_sources`; stored on the ask row
  (`requested_perspectives_json` becomes updatable); the table gains
  `requestedPerspectives` / `missingPerspectives` only when perspectives were
  asked (so the off table is unchanged).

**RPCs** (desktop-only, pinned in `test_mobile_allowlist.py`, Tauri
passthroughs; synchronous: no model call): `reader.library_compare_keep`
(`askId` or `toolCallId`, `takes`), `reader.library_compare_remove`,
`reader.library_compare_reopen`, `reader.kept_comparisons` (marks for an
extraction). All refuse `reader_compare_keep_disabled` while the switch is off.
`reader.prompt_contract` gains `compareKeep` only while it is on.

**Config.** `[reader_compare] keep_enabled = true` (frictionless default; a
modelled default, out of the decision-only template), classified in the
parameter registry; every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry recomputed
with a "no scoring, scheduling, projection or serving change" note. Off: the
RPCs refuse, the contract has no `compareKeep`, the ask, compare and tutor
offers are 3988cf778's byte for byte (pytest and vitest pins), and no
perspectives field shows. **Successor:** none (proposals and display).

**Frontend** (new files under `screens/reader/`): `CompareKeep.tsx` (the
perspectives field; the three bands under the table: sources `§`, LearnLoop's
inferred relation `◇` labelled with its fine label, *your take (optional)* `›`
with *ⓘ where this goes*; *keep comparison ⇄*, *kept ⇄ · remove*),
`useKeptComparisons.ts` (marks for the open reading; reopen), `KeptMark.tsx`
(the `⇄` margin mark). `LibraryAnswer`/`useLibraryAsk`/`TutorOffers` gain an
optional `keep` prop (absent: RW4a's and RW1c's render unchanged);
`ReaderScreen.tsx` gets a narrow hook-up (the marks and the contract key).

**Tests** (fakes only): `test_compare_sources_keep.py` (G43: table diff with and
without Keep; proposal statuses and authorship; mapping table incl.
`alternate_definition`; fine-label round trip in `kept_json`; my take as
`learner_connects`/learner and not in learner-text gaps; remove supersedes and
deletes nothing; idempotence; held-out refusal before and after the compare;
re-extracted line dropped; tutor Keep keeps only shown sources, and the
comparison runs only on the press; marks, reopen, compared-on; card read; no
concept edge / facet / prerequisite / LO change, vault YAML unchanged; switch
off refuses and pins the contract, ask and compare outputs), the mobile
allowlist pins, the registry and defaults snapshots, the RPC contract; vitest
`compareKeep.test.tsx` and `compareKeepSwitchOff.test.tsx` (snapshots taken on
the base frontend before any RW4d frontend code).

## 1. What was built

### 1.1 Keep (`src/learnloop/source_retrieval/kept_comparisons.py`, new)

- **Where it lives.** Beside RW4a's `library_ask.py` (the frozen-cycle contract forbids `reader → source_retrieval`); it writes only through `reader/source_objects.py` (`author_source_object`, `link_relation`, `review_source_object`, and the new `supersede_relation`). Its SQL is in the registered `db/stores/library_asks.py` (`kept_row`, `kept_asks`, `asks_for_comparison`, `fork_ask`; `requested_perspectives_json` became updatable).
- **`keep(ask_id, takes)`** reads the **stored** `source_comparisons` row named by the ask's `comparison_id` (the RPC takes no table). Before anything is written:
  - the held-out predicate is asked about **every** compared span now (`exam_material.exam_withheld`, the call RW4b's statement reader makes; an exception counts as held, fail closed); any hit refuses `exam_material`;
  - every line's quote is checked again against the block **as it is now** (`compare._quote_in`, the service's own check): a source whose passage is gone, a line whose quote left the block, a relation with a quote no longer in its passage, or an unknown fine label (fail closed) is not kept and is listed in `kept_json.not_kept`;
  - every take is validated against the claims that will be kept.
  Then: one `source_objects` row per kept source with one version (`object_type = 'definition'` when the block's effective role is a definition, else `'claim'`; `authorship = 'ai'`, `status = 'proposed'`, the extraction's `revision_id`; `exact_text` = its verified quote; `content_json` = the AI-written lines with their labels, the comparison and ask ids, the question; `model_provenance_json` = model, prompt version, ledger ids, comparison id) and one citation (span, `revision_id`, block `content_hash`, verified quote). One `source_object_relations` row per verified relation between two kept claims (`authorship = 'ai'`, `review_status = 'proposed'`, the mapped type). `kept_json` (version 1) records every object id with its key, source and type, every relation id with its **fine label**, mapped type, endpoints, statement and both quotes, the takes, what was not kept, the question's and passages' LOs; `kept_at` is set. One salience-only event `comparison_kept`.
- **The mapping** (`RELATION_MAP`, `coarse_relation`): §3.4 item 15 exactly — `equivalent` → `supports`, or `alternate_definition` when both claims are definitions; `different_assumptions`, `different_notation`, `complementary` → `refines`; `disagreement` → `contradicts`; `unclear` → `unresolved`.
- **Your take**: a `learner_connects` relation with `learner_text`, `authorship = 'learner'`, `review_status = 'proposed'`, on a pair (both objects) or a claim (`related_object_id` NULL). Not routed to learner-text gaps (UX §4.10's row: "isn't read for gaps"), never a question, never evidence.
- **Idempotent.** A second Keep on a kept comparison writes nothing; with a take it adds only that take. A second comparison of a question whose first is kept (other pins, perspectives) is kept on its own `library_asks` row (`fork_ask`: the question, anchor, caller, manifests and notes copied, no comparison/keep/tutor) so each keep keeps its own ids and history; a repeated press finds that row.
- **Remove**: each claim gains a `superseded` status version (`review_source_object`), each relation (AI and learner) a superseded successor row (`version_ordinal + 1`, same endpoints, type, wording, authorship; `repository.create_source_object_relation` gained `version_ordinal`, and `repository.source_object_relation` reads one). Nothing is updated in place or deleted. `kept_json.removed` keeps the history; `kept_at` is cleared; a later Keep carries the history over.
- **The tutor's comparison** (`keep_tutor(tool_call_id)`): the request's latest successful `run` row; its `result_ref` is the comparison, its `result_keys` are what the tool view showed after its own withholding — **only those sources are kept**. The keep is recorded on a new `library_asks` row with `caller = 'tutor'` (the 209 CHECK allows it), `question_event_id` = the tutor's question, the manifest naming the tool call and run. The comparison itself still runs only on the learner's press (RW1c, G59).
- **Reads**: `kept_marks(extraction_id)` (spans with a live keep, the other sources' titles; a comparison with exam or held-out material now is left out; one predicate read for all candidates); `reopen(ask_id)` (RW4a's `compare_table` rebuilt from the stored row, showing only the kept claims, their kept lines and the kept relations; refused `exam_material` while any kept span is held out); `compared_on(keys)`; `compare_kept_state`.
- **The router card's read** `kept_comparisons_for_card(repository, learning_object_ids, as_of)`: typed entries (ask id, kept date, caller, LOs, sources with object ids and types, relations with coarse type and fine label, take count, `status = 'proposed'`), deterministic from `kept_json`, no prose and no quotes. RW6b composes it into `reader_activity_for_card`, which does not exist on main yet (see §9).
- **Report** (`reader_report.py`): `comparisons` — kept, removed, by caller, takes, kept relations by type and by fine label (counts only); `library` now counts the learner's asks only (`caller = 'learner'`), unchanged for every existing row.

### 1.2 Perspectives and the compare RPC (`library_ask.py`, `handlers/library_ask.py`)

`reader.library_compare` takes `requested_perspectives` (cleaned: trimmed, distinct ignoring case, at most 4 of at most 80 characters), passed to the service's `compare_sources` and stored on the ask row; the table then carries `requestedPerspectives` and `missingPerspectives` ("not found in your library"). With `keep_enabled` off, perspectives are refused (`reader_compare_keep_disabled`) and the call, the table and the row are RW4a's. With keep on, the table carries `kept` (this comparison's keep state, or null), and `reader.library_ask` carries `comparedOn` (kept comparisons sharing its passages).

### 1.3 RPCs (`src/learnloop_sidecar/handlers/kept_comparisons.py`, new)

Desktop only (pinned in `test_mobile_allowlist.py`; Tauri passthroughs in `commands.rs` / `main.rs`); synchronous (no model call): `reader.library_compare_keep` (`askId` or `toolCallId`, `extractionId`, `takes`), `reader.library_compare_remove`, `reader.library_compare_reopen`, `reader.kept_comparisons`. Each refuses `reader_compare_keep_disabled` while the switch is off. A library ask's follow-up is bound by its stored caller (RW4a's `follow_up_caller`); while a cold administration of its item is open — or of the tutor request's item — nothing is kept or reopened (`cold_attempt`). `reader.prompt_contract` gains `compareKeep {library, tutor, perspectives, maxPerspectives}` only while keep is on (`library` needs the library answer; `tutor` needs only the Reader's compare, the service's comparison, RW1a's inquiry and the reader tutor).

### 1.4 Config

`[reader_compare] keep_enabled = true` (frictionless default; a modelled default, out of the decision-only template), classified in the parameter registry (structural / operational: proposals and display). All 19 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries recomputed with a "no scoring, scheduling, projection or serving change" note (template `.pyc` cleared; 0 mismatches). No route: the comparison is the sources spec's `source_compare`.

### 1.5 The Reader (frontend; new files under `screens/reader/`)

- `CompareKeep.tsx`: under a compare table, the three voices apart (W2): the table (§, RW4a's) and then the **◇ band** "how LearnLoop reads the relations" — each pair once, `A ⇄ B · different assumptions`, in LearnLoop's voice labelled "LearnLoop's inference (AI-written)", with the model's line; the **› band** *your take (optional)* with an *about* select (each pair, then each claim alone; default the first pair) and *ⓘ where this goes* ("Kept as your own note on these passages, in your voice. It isn't read for gaps — and never grades you."); *keep comparison ⇄*, then *kept ⇄ · kept as proposals · nothing changes your map until you review them · remove* (and *add your take* while a take is typed); a refusal says why. `KeptComparisonView`: a kept table reopened from the stored row (no model call), with its keep state.
- `KeptMark.tsx`: `⇄` in the gutter beside a passage with a live keep (below `✎`'s place), the learner's own mark outside the cue budget; pressing it opens the kept table under the passage; Esc / *close* folds it.
- `useKeptComparisons.ts` (the marks, read on opening a reading and after a keep or remove) and `compareKeepContext.ts` (the context the Reader provides only while the contract carries `compareKeep`).
- `LibraryAnswer.tsx`: the *perspectives:* field beside *compare pinned* (keep on), the perspectives and "not found in your library" lines in `CompareTable` (only when the table carries them), `CompareKeep` under the table, *you compared these on 3 Oct · reopen ⇄*. `useLibraryAsk.ts`: `keep` settings, `compare(perspectives)` (sent only when given). `TutorOffers.tsx`: `CompareKeep` under the tutor's comparison (renders nothing without the context). `ReaderScreen.tsx` (+10 lines): the hook, the context provider around the screen, the mark beside its passage.

## 2. Gates and where they are tested

| Gate | Backend | Frontend |
|---|---|---|
| **G18** compare keeps sources apart; without Keep nothing written; no edge / facet / prerequisite / LO change | `test_compare_sources_keep.py::test_comparing_writes_no_proposal_and_keep_writes_only_proposals` (a table diff over **every** table: compare changes no proposal table; Keep changes only the four proposal tables and one event; learning-state tables and the vault's YAML unchanged), `…lines_that_failed_quote_verification_are_never_kept`, `…keep_reads_the_stored_comparison_never_the_clients_table`; RW4a's `test_reader_compare_table.py` unchanged | `compareKeep.test.tsx` (nothing kept until the press; no consensus) |
| **G43** kept comparisons are proposals; my take is the learner's; no keep, no write; the tutor's compare runs only on its press | the same table diff; statuses/authorship of versions, citations, relations; `…your_take_is_the_learners_own_relation_and_is_not_read_for_gaps`; `…the_tutors_comparison_is_kept_only_after_its_press_with_what_it_showed`; `…a_tutor_keep_keeps_only_the_sources_its_run_showed` | `compareKeep.test.tsx` (keep and remove; the tutor's keep only after the press) |
| The mapping table and fine labels | `test_the_relation_mapping_table` (9 cases), `…every_fine_label_round_trips_through_kept_json` (all six labels plus an unknown one, not kept), `…equivalent_definitions_are_alternate_definitions` | fine labels in the ◇ band |
| Held out | `…material_held_out_after_the_comparison_is_not_kept` (table diff: nothing at all changes), `…a_kept_comparison_held_out_later_is_neither_marked_nor_reopened`, `…a_comparison_holding_exam_material_is_refused`, `…the_held_out_predicate_fails_closed` | a refused keep says why and keeps nothing |
| ⇄ marks, reopen, compared on | `…marks_reopen_and_compared_on` | `compareKeep.test.tsx` (the mark beside its passage reopens the table; "you compared these on 3 Oct · reopen ⇄") |
| Switch off = 3988cf778 | `test_compare_keep_switch_off.py` (golden recorded on the base tree: contract, ask, table, the ask row, proposal counts; every RW4d RPC refuses and writes nothing; perspectives refused) | `compareKeepSwitchOff.test.tsx` (2 snapshots written on the base frontend: the comparing posture with the table; the tutor's comparison pressed) |
| W1 | `…every_rw4d_event_is_salience_only`; the card read is pure and quote-free | — |

**Fail-first evidence.** The pytest golden and the vitest snapshots were written on the base (`git archive 3988cf778 src migrations` first on `PYTHONPATH`; the base frontend before any RW4d frontend file) and pass unchanged on the tip. `test_compare_sources_keep.py` cannot import on the base (no `kept_comparisons` module); its two first-run failures (a take validated after the proposals were written; the card's LOs empty) were fixed before the backend commit.

## 3. Decisions and deviations

1. **Perspectives are under `keep_enabled`**, not their own switch: the orchestrator pins the compare display to 3988cf778 with the switch off, and §13 lists perspectives among RW4d's parts.
2. **One claim per compared source**, not one per line: a relation joins two sources' claims; the claim's citation is its first verified line's quote (else its side of a relation), and all its verified lines are in `content_json`.
3. **Re-verification at keep**: the stored comparison holds only verified lines; Keep checks each quote again against the block as it is now, so a re-extracted book never gets a citation whose quote is not in it.
4. **Remove appends successors** (RAW_LEDGER tables are append-only): a relation's superseded state is its successor row (`version_ordinal + 1`); readers that want a relation's current state read its highest version. P3's review path is unchanged.
5. **A second comparison of a kept question gets its own row** (`fork_ask`), so a kept comparison's ids never move.
6. **The tutor's keep records a `library_asks` row (`caller = 'tutor'`)**: `kept_json` lives there (§7.5), and the report counts it under comparisons, not asks.
7. **`⇄` is drawn in the extracted-text view only.** The PDF surface's overlay gutter carries RW3a's cue marks through `cueMarksFor`, which RW3b is changing in parallel; adding `⇄` there is left for after RW3b lands (§8 Q3).
8. **Keep is not atomic across rows**: `reader/source_objects.py` commits each object and relation itself. Everything that can refuse (held-out, quotes, takes) is checked before the first write; a crash mid-keep would leave proposals without `kept_json` (proposals only, never evidence) and a second press would write a second set (§8 Q4).
9. **The take is not read for gaps** (UX §4.10's row for *your take*), so no learner-text adapter is involved.
10. **The router card's read exists, unrendered**: `reader_activity_for_card` is RW6b's and not on main.

## 4. Successor

**None.** Proposals (P3 §7, `status`/`review_status = 'proposed'`) and display. Nothing here writes an attempt, evidence, mastery, certification, FSRS, a plan, a concept edge, a facet merge, a prerequisite or an LO change; replay and rebuild never read `library_asks` or the source-object tables for scoring. Off, the RPCs refuse and RW4a's compare and RW1c's tutor comparison are 3988cf778's byte for byte.

## 5. Friction audit (G52)

| Workflow | Before | After |
|---|---|---|
| Keep how two books treat a question | Notes by hand | compare → (your take) → *keep comparison ⇄* |
| Come back to it | Re-ask, pay again | `⇄` beside either passage → the table (no model call); or *you compared these on … · reopen ⇄* on a later ask |
| Ask for a view | Re-word the question | *perspectives:* "a geometric view, an application" → "not found in your library: …" |
| Keep the tutor's comparison | Not possible | *how do your books treat this?* → *keep comparison ⇄* |
| Undo | — | *remove* (superseded, not deleted) |

Keyboard: the keep, remove, take, about and perspectives controls are ordinary buttons, inputs and a select in the comparing posture's tab order; `⇄` is a focusable button in reading order; Esc folds a reopened table. No model wait: Keep, remove, reopen and marks are local reads and writes.

## 6. Tests and counts

- New backend: `tests/test_compare_sources_keep.py` **33** (25 functions, the mapping table parametrized ×9), `tests/test_compare_keep_switch_off.py` **2** (golden `tests/fixtures/compare_keep_switch_off.json`, recorded on 3988cf778).
- Changed backend: `test_mobile_allowlist.py` (+RW4d pins and its completeness check), `test_reader_intent.py` (the switched-off contract case also turns `keep_enabled` off), `test_reader_tutor_switch_off.py` (pops RW4d's own `compareKeep` at its defaults, as RW4b's landing did for its key), `test_rw4_kill_switches.py` (`_without_library` sets `compareKeep.library`/`perspectives` false: the tutor's keep stays).
- New vitest: `compareKeep.test.tsx` **9**, `compareKeepSwitchOff.test.tsx` **2** (2 base snapshots).

## 7. Files

- Backend: `src/learnloop/source_retrieval/kept_comparisons.py` (new), `src/learnloop_sidecar/handlers/kept_comparisons.py` (new), `src/learnloop/source_retrieval/library_ask.py`, `src/learnloop_sidecar/handlers/library_ask.py`, `src/learnloop_sidecar/handlers/reader.py`, `src/learnloop_sidecar/handlers/__init__.py`, `src/learnloop/db/stores/library_asks.py`, `src/learnloop/db/repositories.py`, `src/learnloop/reader/source_objects.py`, `src/learnloop/reader/reader_report.py`, `src/learnloop/config/schema.py`, `src/learnloop/config/template.py`, `src/learnloop/params/parameter_registry.py`.
- Frontend: `screens/reader/{CompareKeep.tsx, KeptMark.tsx, useKeptComparisons.ts, compareKeepContext.ts}` (new), `screens/reader/{LibraryAnswer.tsx, useLibraryAsk.ts, TutorOffers.tsx}`, `screens/ReaderScreen.tsx`, `api/{client.ts, dto.ts}`, `src-tauri/src/{commands.rs, main.rs}`.
- References: Configuration and Database references regenerated (922 leaves; schema head 213 unchanged; 333 table notes; 0 errors), the two prose counts, `Maps/LearnLoop Pipeline Map.md` (RW4d bullet).

## 8. Open questions (with the default taken)

1. *Default on?* **Yes** (`keep_enabled = true`, frictionless defaults); Keep only ever writes proposals on the learner's press.
2. *Should a take be read for gaps?* **No** (UX §4.10). If the owner wants it, the reader-question adapter could take it as a `reader_formative` text.
3. *`⇄` on the PDF surface?* **Deferred** until RW3b lands (the cue overlay is being changed there).
4. *Atomic keep?* **Default: not atomic** (each proposal commits through `reader/source_objects.py`); a single-transaction writer in the repository would make it so.
5. *Remove then keep again* writes a new set of proposals (the old ones stay superseded). **Default: yes.**
6. *A kept comparison held out later* shows no mark and refuses to reopen; its proposals stay (they hold quotes in `exact_text`). **Default: keep the rows** (removing them would be a deletion); the owner may want *remove* offered without reopening.

## 9. Friction notes for RW4e, RW6b and the router's card (R2)

1. **RW4e** (role proposals): write them through the same `reader/source_objects.py` calls; a kept comparison's claim object for a span already exists (`kept_json.objects[].id`, `content_json.kept_from = "source_comparison"`), so a role judged on the same span can be a new version of a *new* role object, never of the claim (keep the claim's `authorial_role` empty). `block_roles` gives the ingest role the keep used to choose `definition`.
2. **RW6b** (`reader_activity_for_card`): call `kept_comparisons_for_card(vault, repository, learning_object_ids=…, as_of=…)` for the "kept comparisons" part; it is typed, deterministic from `kept_json`, holds no quotes or learner prose (takes are counted), and skips removed keeps. It also omits a comparison holding material withheld now (at any `as_of`), and returns nothing when the held-out predicate cannot be read (fix round 2, F3). A comparison's current relation state is its highest `version_ordinal`.
3. **R2** (the router's card renders it): the entries carry `status = 'proposed'` and both relation labels (`relation_type`, `fine`); render them as the learner's kept relationships, never as evidence or as reviewed edges.
4. **All**: `library_asks` may now hold `caller = 'tutor'` rows (RW4d's tutor keeps); RW4a's report counts only `caller = 'learner'` asks.

## 10. Owner-run commands

No paid run is needed. To try it on a copy: `uv run python -c "from pathlib import Path; from learnloop.db.copies import copy_tree_with_databases as c; c(Path('fixtures/probability'), Path('fixtures-local/rw4d-prob'))"`, `uv run learnloop doctor --fix-state --vault fixtures-local/rw4d-prob`, then `LEARNLOOP_VAULT=$PWD/fixtures-local/rw4d-prob npm run dev` in `apps/learnloop-tauri`. In the Reader: select → Tab → *where else is this explained?* → pin two passages from two books → (perspectives) → *compare pinned* → (your take) → *keep comparison ⇄*; the passages then carry `⇄`. The comparison needs the sources spec's `source_compare` route (unset: the active provider). Switch: `[reader_compare] keep_enabled = false` in the copy's `learnloop.toml`. `uv run learnloop reader report --json --vault <copy>` shows the `comparisons` row.

**Model calls made in this stage.** Tests: fakes only. **4 unintended live calls**, all T6's `source_query_rewrite` on Codex (`gpt-5.6-sol`, the owner's ChatGPT subscription, `estimated_only`, $0 metered; 17,876–19,056 input and 139–175 output tokens each): two ad-hoc diagnostic scripts (`fixtures-local/tmp/probe_keep.py` once, `fixtures-local/tmp/diffrow.py` three times) built a test vault and asked the library **outside pytest**, so conftest's isolation of `LEARNLOOP_CONFIG_DIR` did not apply and the rewrite route resolved to Codex. Every other run was inside pytest (the rewrite reports *Codex checkout path is not configured*). The receipts are in those scripts' throwaway vaults under the worktree's `fixtures-local/tmp/tmp*/vault/state.sqlite`. No vault copy was opened and no owner vault was touched.

## 11. Gate (implement step; targeted, per the owner's 2026-10-17 rule)

Run in the worktree with `TMPDIR` = `fixtures-local/tmp`, `uv run --no-sync` after the install; `/tmp/learnloop-fullsuite.lock` was free each time.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **28 kept**, 0 broken |
| targeted `pytest -n auto -q -p no:cacheprovider` over the **98 files** below, on the stage tip | **2,008 passed**, 0 failed (6 min 3 s). The run before the tip had 1 failure: the switch-off golden compared the search's wall-clock `timings_ms` inside the ask row's `manifest_json` string; the golden now reads JSON columns as JSON (re-recorded on the base), and passed 5 of 5 alone afterwards |
| `pytest --durable-sqlite` on `test_compare_sources_keep`, `test_compare_keep_switch_off`, `test_source_objects` | **38 passed** (no migration; the source-object writes on production pragmas and WAL) |
| `npm install`, `npm run typecheck` | ok, clean |
| vitest `src/screens/reader`, `src/screens/ReaderScreen.*.test.tsx`, `attentionBudget.test.tsx`, `LibraryPlace.reread.test.tsx` | **63 files, 467 tests passed** (incl. `compareKeep.test.tsx` 9, `compareKeepSwitchOff.test.tsx` 2 with its 2 base snapshots unchanged, `libraryAsk*`, `TutorOffers`, `tutorSwitchOff`, `voices`, `attentionBudget`) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | finished, exit 0 (four passthroughs) |
| `db_generate_reference.py`, `db_validate_reference.py`, `validate_vault.py` | regenerated (922 leaves, 333 table notes, head 213); errors []; passed (1,131 notes, all reachable) |
| `desktop_validate.py` / `module_validate.py` | the pre-existing failures RW4a recorded (`pdfSelection/testing/syntheticBook.ts` unclassified; missing module notes), none for an RW4d file |
| contract tests in the targeted run: `test_config_refactor.py` (19 snapshots recomputed), `test_cli_help_snapshot.py` (unchanged), `test_sidecar_serializer_snapshot.py`, `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`, `test_architecture.py`, `test_table_roles.py`, `test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`, `test_registry_audit.py`, `test_sqlite_file_copies.py`, `test_instructional_layering.py`, `test_judge_routes.py` | pass |

**Not done:** no adversarial (Codex) review in this step; no real-UI look (exercised through the real `ReaderScreen` in jsdom); the keep has run only on fakes and on faked stored comparisons.

**The 98 pytest files run** (the new and changed test files, every test file naming `library_ask`, `source_objects`, `reader_report`, `prompt_contract`, `parameter_registry`, `DEFAULTS_SNAPSHOT`, `effective_defaults`, `source_comparisons`, `compare_sources`, `propose_comparison`, `run_source_tool`, `reader_compare`, `kept_comparisons`, `table_roles` or `library_asks`, and the contract tests above):

```text
test_ad1_codex_review_fixes test_ad1_migration test_approach_map_replay test_approach_maps_schema 
test_architecture test_cli_help_snapshot test_compare_keep_switch_off test_compare_sources_keep 
test_compare_sources test_config_refactor test_constraint_engine test_coordinated_migrations 
test_daily_plan_replay test_desktop_rpc_contract test_diagnosis_input_provenance test_diagnosis_replay 
test_exam_protection_review test_facet_identity_actions test_find_sources_intents 
test_forecast_receipts_landing test_forecast_receipts test_grading_cli test_help_assists_schema 
test_hint_feedback_widening test_hint_telemetry test_ingest_jobs test_instructional_layering 
test_judge_routes test_kinship_feature test_learner_text_source_widening test_library_ask_expand 
test_library_ask test_library_ask_review test_library_asks_migration test_library_exercises 
test_method_explicit_upgrade test_mobile_allowlist test_mvp010_upgrade test_mvp011_upgrade 
test_mvp013_upgrade test_mvp014_upgrade test_mvp015_upgrade test_mvp016_upgrade 
test_mvp017_route_check_replay test_mvp017_upgrade test_mvp018_upgrade test_mvp020_upgrade 
test_mvp021_upgrade test_mvp022_upgrade test_mvp023_upgrade test_mvp024_upgrade test_open_world_gate 
test_p0_cutover_mvp08 test_plan_determinism test_reader_compare_table test_reader_cues test_reader_dialogue 
test_reader_find_sources_callers test_reader_inquiry_kill_switch test_reader_intentions test_reader_intent 
test_reader_report test_reader_requests test_reader_rw1b_fix_round4 test_reader_rw1b_review 
test_reader_rw1c_review test_reader_rw2b_review test_reader_tutor_offers test_reader_tutor_retrieval 
test_reader_tutor_switch_off test_reader_workbench_rw2a test_reading_step_switch test_rebuild_orchestrator 
test_recurrence_commands test_recurrence_live test_registry_audit test_regrade_contract_successor 
test_regrade_contract_upgrade test_reread_safety test_retrieval_interventions_write_points 
test_rw4_kill_switches test_sensitivity_certificates test_serve_eligibility_review 
test_sidecar_reader_p3_slice2 test_sidecar_reader test_sidecar_serializer_snapshot test_source_block_fts 
test_source_objects test_source_service_spend_envelopes test_sources_merge_composition 
test_sqlite_file_copies test_stuck_prompt_replay test_table_roles test_tool_registry 
test_tool_results_withhold_answers test_tools_cli test_tracked_fixture_databases test_tutor_tool_requests 
```

## 12. Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/rw4d-onto-main`, cut from main at `f93c93b54` (the
RW3b landing record; main has DL2, successor mvp-0.29 with 20 defaults snapshots, and RW3b, migration head 215 with
`migration_head_215` and 937 configuration leaves). The stage tip is `856634d96` (base `3988cf778`), unchanged.
Main was neither fast-forwarded nor pushed here.

**The orchestrator's last verify** (Codex job `20261020-182310-SFSyDg` on `856634d96`) found one High, which the
orchestrator **ruled non-blocking**:

> With `reader_compare.keep_enabled = false`, `reader.source_objects` and `reader.proposal_inbox` still leave out
> source objects (and their proposals) whose material is exam or held out now, or that were kept from a comparison
> withheld whole. Base `3988cf778` returned them.

**The ruling.** This is exam protection, not part of keeping. The keep switch turns keeping off, not protection, and
turning protection off would return held-out text. Switch-off is therefore base-identical **except** that withheld
material is not shown. On the two owner-vault copies no source object is withheld, so parity (c) found the
switched-off reads byte-identical to main's (below).

### Commits and conflicts

- `ee20a4204`: a `--no-ff` merge of `reader/rw4d` onto `f93c93b54`. Three source conflicts, each composed so that
  both sides survive:
  - `config/template.py` (19 hunks): DL2's and RW3b's notes kept on every defaults snapshot, RW4d's
    `[reader_compare] keep_enabled` note added beside them (in full under mvp-0.9's, a one-line pointer on the others,
    **mvp-0.29 included**); the hashes were left at main's in the merge and recomputed in the next commit.
  - `params/parameter_registry.py`: RW3b's two `[cues]` rules and RW4d's `reader_compare.keep_enabled` rule both kept.
  - `tests/test_mobile_allowlist.py`: the desktop-only parametrization lists both `READER_RW3B_RPCS` and
    `READER_RW4D_RPCS`.
  - 401 generated reference notes took main's side and were regenerated afterwards.
  - Auto-merged without conflict, then checked by the gate: `ReaderScreen.tsx` (RW3b's cue and density wiring beside
    RW4d's `⇄` hook-up; RW4d's PDF-gutter merge `pdfMarks()` wraps `cueMarksFor("pdf")`, whose signature RW3b kept),
    `TutorOffers.tsx`, `LibraryAnswer.tsx`, the reader and library-ask handlers and the handler registry,
    `reader/source_objects.py`, `config/schema.py`, `dto.ts` / `client.ts`, `commands.rs` / `main.rs`, the CLI help
    snapshot and the RPC pins.
  - **RW4b's statement-reader pin** (`test_library_exercises::test_r2_no_handler_reader_module_or_s1_path_reads_an_exercise_statement_another_way`,
    repaired in RW4d's round 5) passes on the merged tree unchanged: RW3b added no reader it flags, and the pin was
    not touched.
- `45a372824`: the regeneration (below).
- `22432096e`: the RW4d x RW3b interaction test (`tests/test_rw4d_rw3b_composition.py`, 3 tests; the gate head).
- This record.

### Regeneration

- **Defaults snapshots.** With the template's `.pyc` cleared, all **20** `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries
  (mvp-0.9 … mvp-0.27, mvp-0.29) were recomputed from the composed defaults (`defaults_fingerprint_for_version`); 0
  mismatches after.
- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, `schema_head` **215**,
  **335** table notes, **938** configuration leaves in **66** sections (RW4d's `reader_compare.keep_enabled` on
  RW3b's 937). The two prose counts in `Configuration.md` and `Database.md` were moved by hand (937 → 938); the rest
  is commit labels, RW4d's tests and cited lines in the table notes and the `reader_compare` field notes (404 files).
- **CLI help snapshot and RPC pins.** A pin run of 526 tests (`test_cli_help_snapshot`,
  `test_sidecar_serializer_snapshot`, `test_desktop_rpc_contract`, `test_mobile_allowlist`, `test_sidecar_contract`,
  `test_config_refactor`, `test_registry_audit`, `test_library_exercises`, `test_architecture`, `test_table_roles`,
  `test_tracked_fixture_databases`, `test_sqlite_file_copies`, both RW4d files) passed; no snapshot needed
  rewriting. RW4d's four RPCs stay desktop-only.
- **Head fixture.** No migration: `migration_head_215` stays main's.
- **`validate_vault.py`**: passes (1,135 notes, 1,133/1,133 reachable).
- **Known failures from before this stage, not fixed:** `desktop_validate.py` still stops on
  `components/pdfSelection/testing/syntheticBook.ts`; `module_validate.py` reports **958** issues (954 at the RW3b
  landing; RW4d adds modules without module notes, such as `source_retrieval/kept_comparisons.py` and
  `learnloop_sidecar/handlers/kept_comparisons.py`).

### Gate

Python 3.12.14. `TMPDIR` was merge2's `fixtures-local/tmp`; every command after the install ran as `uv run
--no-sync`. Both suite lanes ran under `flock /tmp/learnloop-fullsuite.lock` on `22432096e` (the gate head; this
record changes docs only). The AD2+AD3 (`learnanything-ad1`), RW5a (`learnanything-dl2`) and RW4d stage
(`learnanything-rw4b`) worktrees and their processes were not touched. Every test uses fakes. **This is the first full
run over RW4d's code**: the stage and its six fix rounds ran targeted tests only.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `lint-imports --no-cache` | **28 kept**, 0 broken |
| full suite `pytest -n auto` | **14,973 passed, 2 xfailed, 0 failed** (19 min 58 s; `fixtures-local/rw4d-landing/fullsuite.log`). RW3b's landing ran 14,889 |
| `pytest -m durability` | **114 passed**, 14,861 deselected (2 min 57 s; `fixtures-local/rw4d-landing/durability.log`) |
| `npm install`, `npm run typecheck` | ok; clean |
| `npm test` (the whole vitest run, default workers) | **160 files, 1,272 tests passed** on the first run (RW3b's landing: 158 / 1,254). This settles fix round 6's `--maxWorkers=3` note: the whole run passes at default workers (load average about 3 at the time) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | ok (RW4d's four passthroughs) |
| thread, lock and timing tests | all passed on the first run, so none was rerun |
| tracked fixtures, worktree | `git status` clean after both lanes and the frontend run; no non-empty `-wal` beside a fixture |

**The interaction test** (`tests/test_rw4d_rw3b_composition.py`, added because no existing test put RW3b's cues and
RW4d's marks on one passage):
- *A cue and a `⇄` mark on one passage are independent*: after discovery marks the row-swap passage, keeping a
  comparison on it changes neither the cue marks nor the cue budget's `withheld` counts, and a second discovery
  changes no kept mark. Holding the passage out removes both: no cue on the chapter, no `⇄` on either book, reopen
  refused `comparison_withheld`, no kept object returned.
- *Discovery on a source whose kept comparison is withheld*: holding out the **other** book's pinned passage withholds
  the comparison whole (no mark, no reopen, no object), while discovery on the open book still marks its own,
  unprotected passage; the cue payload carries none of the comparison id, the ask id, the other book's passage or its
  ids, and the judge's prompts never held that passage.
- *One protection, never looser in the cues*: with a chapter of each book held out, every key RW4d's predicate
  (`exam_withheld`) withholds is one RW3b's guard (`passage_cues.protection`: `teaching_exclusions`, which contains the
  same exam material, plus `held_out_material`) does not allow.
- So they are **independent by construction**: the `⇄` mark is the learner's own (outside the cue budget, merged after
  cue placement), RW3b's cues read only the open source's own passages, and the cues' guard contains RW4d's
  predicate. Whole-comparison withholding is RW4d's alone and never hides a passage's own cue.

No failure, so no landing fix.

### Parity (backup-API copies; no model call completed)

**Setup** (scripts in `fixtures-local/landing-rw4d/scripts/`, adapted from the RW3b landing's):
- **Copies.** `fixtures/linear_algebra` and `fixtures/probability` were copied once, with `copy_tree_with_databases`,
  from the main checkout into `fixtures-local/landing-rw4d/orig/`; every other copy came from `orig/` or its upgraded
  copies through the same helper. `arxiv_v2` was not opened. Both vaults start at schema 165, label `mvp-0.8`;
  linear_algebra holds 4 source objects, probability 5.
- **Code.** Main's code is `git archive f93c93b54`; the merge's is `git archive 22432096e`.
- **Environment.** Every run went through `env -i` with only `PATH`, `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`,
  `TMPDIR` and `LANG` (empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`).
- **Routes.** `neutralize3.py`, under each code, sent all 56 route fields to `127.0.0.1:9` (the reader, tutor,
  library, sources and `source_compare`, cue, hint, workbench, AD and Decider routes included), the active provider to
  that loopback profile with no fallback; `query_rewrite`, `tutor_query_rewrite`, `tutor_rerank`, `dense`,
  `[embedding]` and `[learner_text_gaps]` off; `build_on_serve` and outcome placement off. `routes.py` resolved all 59
  `AITask`s on both codes: nothing outside the loopback profiles except `embedding`, disabled and keyless.

**(a) No schema change**

| Check | linear_algebra | probability |
|---|---|---|
| open (migrate), main's code / the merge's | 165 → 215 (49 applied) / the same | the same |
| schema, main vs merge | **identical** (1,428 objects; none on one side only; no SQL differs) | **identical** (1,427) |
| rows of every table (340), all columns | **identical** (16,540 rows); `schema_migrations` differs only in `applied_at` | **identical** (7,638 rows; the same) |
| `foreign_key_check` / `integrity_check` | 0 / ok, both sides | the same |
| `rebuild --shadow --json`, main vs merge | **0 differences** after normalisation (facet 0, mastery 2, schedule 8 on both); live database unchanged on both | **0 differences** (0 / 1 / 1) |
| `doctor --json`, main vs merge | **0 differences** after normalisation (57 issues, 1 error) | **0 differences** (101 issues, 48 errors) |

**(b) Nothing served changes** (frozen clock 2026-10-19 09:00 UTC; certification with recipe gaps and curves, the
Today queue with no session / a session / greedy, the daily plan read, served twice and read again)

| Check | linear_algebra | probability |
|---|---|---|
| at `mvp-0.8` (the copies' label) | cert **byte-identical** (132,860 bytes), Today **byte-identical** (504,488), plan byte-identical (off below mvp-0.14) | cert (17,494), Today (709,910), plan: all **byte-identical** |
| upgraded by main's code to `mvp-0.27` (`--to mvp-0.9`, `--to mvp-0.27`, `rebuild-derived-state` twice; all rc 0), opened by each code | cert **byte-identical** (129,651), Today **byte-identical** (528,665) | cert (17,495), Today (741,269): **byte-identical** |
| then by main's code to `mvp-0.29` (`--to mvp-0.29`, `rebuild-derived-state` twice; all rc 0), opened by each code | cert and Today **byte-identical** (the same sizes) | the same |
| the daily plan at mvp-0.27 and at mvp-0.29 | identical except `router_decisions.card_hash`, `snapshot_hash` and the card hash inside `detail_json`; a second run of main's code on a fresh copy differs from the first in exactly these three (`plan_repeat.sh`), as at the RW3b and DL2 landings | the same |

**(c) The real sidecar** (stdio, `SystemClock` frozen at 2026-10-19 09:00 UTC through `sidecar_clock.py`;
`kept_run.py`, compared by `ccmp.py` with run-generated ids normalised) on copies of main's mvp-0.29 vaults: (i)
`cm`, main's code; (ii) `coff`, the merge with `[reader_compare] keep_enabled = false`; (iii) `cdef`, the merge at its
defaults. Each: `reader.prompt_contract`; `reader.source_objects` for the book that has objects (probability
`src_01KYMSH13FAGNWVPPHCQ2FY3B4`, 5 objects; linear_algebra `src_01KY2YG27G1SDWA4FN939ZBB34`, 4) and
`reader.proposal_inbox`; `reader.kept_comparisons` on that book's reading; `reader.library_ask` on one of the
objects' passages (a job, polled); `reader.library_compare` on two of the objects' passages (a job, polled); the keep
RPCs (`library_compare_keep`, `_reopen`, `_remove`, `kept_comparisons`) on that ask; the reads again; on probability a
manual-graded attempt on `pi_prob_derive_complement`; `shutdown`.

| Step | (i) main vs (ii) keep off | (iii) defaults, every difference from (i) |
|---|---|---|
| `initialize` | identical apart from the vault path and the method list, which gains RW4d's four RPCs (registered, refusing) | the same |
| `reader.prompt_contract` | **byte-identical** (both vaults) | gains `compareKeep {library: true, tutor: true, perspectives: true, maxPerspectives: 4}` |
| `reader.source_objects` (both reads) | **byte-identical**: all 5 / 4 objects returned on both. **No object is withheld** on these copies (no exam or held-out material touches them and no comparison is kept), so the ruled exception lists no object id here | byte-identical to (i) |
| `reader.proposal_inbox` (both reads) | **byte-identical** (1 / 4 proposals) | byte-identical to (i) |
| `reader.library_ask` (the job's result) | **byte-identical** | gains `comparedOn: []` |
| `reader.library_compare` | **byte-identical**: `too_few_sources` (both passages are in one book; refused before any model call) | the same, plus `kept: null` |
| keep RPCs | (i) `method_not_found`; (ii) each refused `reader_compare_keep_disabled` ("Keeping comparisons is switched off …"), nothing written | `library_compare_keep` refused `stale_comparison`, `library_compare_reopen` refused `not_found`, `library_compare_remove` answers `{kept: null, removed: false}`, `kept_comparisons` answers `marks: []` (both reads) |
| the attempt (probability) | the rows it added in 26 tables are **identical** across (i), (ii) and (iii), apart from the new attempt's id in `response_ref` | identical, as left |
| `library_asks` | one learner row per run, `kept_json` / `kept_at` NULL, on all three; no source-object row added | the same |

**`model_call_receipts`**: 34 learner databases under `landing-rw4d/` carry the table; **no row** in any of them
(none completed, none attempted: the compare refused before calling).

### New findings

1. **No composition failure.** RW4d's three conflicts were bookkeeping (snapshots, registry rules, the RPC pin list);
   RW3b's cue paths and RW4d's keep paths compose without a code change, and the interaction test pins it.
2. **Keep on an ask that has no comparison is refused `stale_comparison`**, whose message ("This isn't the comparison
   this question shows any more, and it isn't kept. Compare again to keep it.") reads oddly when nothing was ever
   compared; *remove* on such an ask succeeds with `removed: false`. Nothing is written either way, and the UI only
   offers Keep under a shown table. Low; not changed.
3. **The four RW4d RPCs are registered while switched off** (they refuse), so `initialize`'s method list differs from
   base with the switch off. Same as every earlier Reader kill switch; Low.

### For the owner

- **No migration.** Nothing changes in your database until you press *keep comparison*; your algorithm version is
  unchanged and nothing served moves (parity (a), (b)).
- **What you see in the Reader.**
  - **Keep this comparison**: under a compare table (library answer, or the tutor's *how do your books treat this?*),
    *keep comparison ⇄* keeps each book's claim with its quote, and the relation LearnLoop infers between them (in
    LearnLoop's voice, labelled AI-written, with its fine label such as "different assumptions"), as **proposals**:
    nothing changes your study map until you review them. *remove* supersedes a keep; nothing is deleted.
  - **Your take (optional)**: a line in your own voice on a pair or a claim, kept as your note. It is never read for
    gaps and never grades you.
  - **`⇄` marks**: beside a passage you kept a comparison on (text view and the original PDF), outside the cue
    budget; pressing it reopens the kept table with no model call. A later library ask on the same passages says
    *you compared these on 3 Oct · reopen ⇄*.
  - **Requested perspectives**: *perspectives:* beside *compare pinned* ("a geometric view, an application"); the
    table says which were "not found in your library".
  - **Withheld comparisons say why**: when any passage behind a comparison is exam or held-out material now, the
    whole comparison is withheld (no table, mark, keep or take) and the Reader says so, instead of showing part of it.
- **The kill switch** `[reader_compare] keep_enabled = false` (default true) turns off keeping, takes, the `⇄` marks,
  reopen, perspectives and the contract's `compareKeep`; the compare and tutor tables are then RW4a's and RW1c's.
  It does **not** turn off exam protection: source objects (and their proposals) whose material is exam or held out
  now, or kept from a comparison withheld whole, stay out of `reader.source_objects` and `reader.proposal_inbox`
  (the orchestrator's ruling above). `reader_compare.enabled = false` turns comparing off altogether.

### Open questions (defaults in force)

1. *Default on?* **Yes** (`keep_enabled = true`); Keep writes proposals only on your press.
2. *Should a take be read for gaps?* **No** (UX §4.10).
3. *`⇄` on the PDF surface?* **Done** in fix round 1 (F10), beside RW3b's marks and outside their count.
4. *Atomic keep?* **Yes** since fix round 1 (F1: one `Repository.atomic()` per keep, take and remove).
5. *Remove then keep again* writes a new set of proposals (the old ones stay superseded). **Default: yes.**
6. *A kept comparison held out later* shows no mark and refuses to reopen; its rows stay (removing them would be a
   deletion), and *remove* stays offered (fix round 5's F4 ruling). **Default: keep the rows.**
7. *Relation lineage without a migration* (fix round 1's F7): the supersession record lives on the ask row; a
   `supersedes_relation_id` column (migration 216) is **deferred** unless P3's review inbox needs relation heads from
   the table.

### Open items

- **Queued follow-up: "whole-comparison provenance for `compare_sources` and tutor tool runs (RW4a/S3/RW1c
  surfaces)".** The direct `compare_sources` RPC and `instructional/tools.py` `_comparison_view` check only the
  displayed passages, the same as on main; RW4d's own reads and writes withhold the whole comparison.
- **F4 (Remove on a withheld comparison) was rejected by ruling**: Remove is cleanup with a status-only response.
- **Dropped pins count as contributing passages**, so a comparison that pinned an exam passage is never keepable
  while that passage is protected.
- **A comparison whose dropped pins name a deleted passage** is never shown or kept (fail closed).
- **Vitest under load**: fix round 6 passed only with `--maxWorkers=3`; this gate's whole run passed at default
  workers on the first run (above), so the item is settled.
- **Findings 2 and 3** above (Low).
- **From before this stage:** `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (958 issues).
