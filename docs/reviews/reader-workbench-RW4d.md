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
