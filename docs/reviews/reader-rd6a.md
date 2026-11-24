# Reader workbench v2, RD6a: the goal lens (backend)

The backend half of stage RD6 of `docs/specs/spec_reader_workbench_v2.md` (§3.2-§3.5, §12 except §12.6, §14,
§15.3, §16's RD6 row). Branch `reader/rd6a-goal-lens-backend`, based on main `ba7884c102` (migration head 266,
latest tag mvp-0.68). The frontend half (the band, criticality marks, dimming, callouts, the path view) builds on
the contract below.

**What it delivers.** `goal.band`, `goal.lens` and `goal.section_choice`, with their Rust passthroughs and typed
`client.ts`/`dto.ts` entries, plus a passthrough and a typed entry for the existing `curriculum.path` (the frontend
needs it to start the coverage and path judgment a goal owes). No UI, **no migration**, no config key, no kill
switch, no algorithm tag, no prompt change, no model call, nothing on the phone.

## 1. What landed

| Item | Where |
|---|---|
| The level rules (pure; no I/O, no weight or threshold) | `learnloop/curriculum/goal_lens.py` |
| The reads they are computed from (the real model, read once per request) | `learnloop/source_retrieval/goal_lens_reads.py` |
| *Read it anyway* on a section, as a judgment-ledger verdict | `learnloop/source_retrieval/goal_lens_choices.py` |
| Checks answered today (the band's filled ◇) | `learnloop/intent/inline_checks.py:answered_checks` |
| The RPCs | `H:goal_lens.py` (registered in `handlers/__init__.py`) |
| The range rule shared with `passage.union_range` | `learnloop/section_map.py:range_span_ids` (the union wraps it; its replies and codes are unchanged) |
| `path_view(inputs=...)`, `owed_among` | `source_retrieval/deliverable_path.py` (callers unchanged) |
| LOs named per reading | `db/stores/section_coverage.py:learning_objects_in_reading` |
| Fences | `pyproject.toml`: the lens's three modules are sources of `passage-projections-are-read-only` and forbidden to both grader fences |
| Rust and client | `src-tauri/src/commands.rs`, `main.rs` (four commands), `src/api/client.ts` (`goalBand`, `goalLens`, `goalSectionChoice`, `curriculumPath`), `src/api/dto.ts` |
| Desktop only | `tests/test_mobile_allowlist.py` (`READER_RD6A_RPCS`) |

**Placement.** The spec puts the lens at `curriculum/goal_lens.py`. The deliverable path and coverage live in
`source_retrieval`, which already imports `curriculum` (`curriculum.commitments`), so a module in `curriculum` that
read them would close a package cycle. `curriculum/goal_lens.py` is therefore the pure core only (it imports
nothing from `learnloop`), and the reads sit beside the path in `source_retrieval`. The due checks come from the
sidecar (`intent.inline_checks`), as RD0's review already found for the due-checks read.

## 2. The RPCs

Params are `extra="forbid"`, replies `versioned`, none is on the phone allowlist. Each refuses with
`curriculum_disabled` while `curriculum.enabled` is off (the path it displays is off then). None calls a model or
starts background work: the coverage and the path judgment start where they do today (`curriculum.path` with
`judge: true`, the Guide's slice, `set_depth`, `set_scope`).

| Method | Input | Reply |
|---|---|---|
| `goal.band` | `{goal_id}` | `{goal_id, goal: {id, title, sentence, kind, due_at, set_at}, status, message, reason, depth, depth_label, depths: [{id, label, means, learning_objects, sections, minutes}], learning_objects: [dot], counts: {learning_objects, demonstrated, likely, untested}, unmatched, checks: {due_today, answered_today, first: {commitment_id, host}}, next, pace, coverage: {unjudged, covering, failure}, path}` |
| `goal.lens` | `{goal_id, extraction_id}` (the whole reading), or plus `{from_span_id, to_span_id}`, or plus `{t0, t1}` | `{goal_id, extraction_id, status, message, depth, depth_label, mapping, levels: [section level]}` |
| `goal.section_choice` | `{goal_id, extraction_id, section_id, choice: read_anyway\|none, operation_id}` | `{choice: {operation_id, goal_id, extraction_id, section_id, choice, replayed, created_at}}` |

- **A dot** (path order: path lines first, then the goal's other LOs): `{learning_object_id, title, kind:
  needed|prerequisite|later, ordinal, readiness: demonstrated|likely|untested, readiness_line, beyond_depth,
  primary: {extraction_id, section_id, start_span_id, title, book}, check: due|answered|null, held}`. The band
  shows needed LOs, the prerequisites not yet shown (the path's own set) and the LOs needed only deeper; `counts`
  are over the LOs within the chosen depth. Readiness is `lo_certification` (demonstrated), AD's labelled
  prediction through the same reader `curriculum.ready` uses (likely), else untested.
- **`next`**: `{kind: "checks", count, check}` while checks are due, else `{kind: "section", learning_object_id,
  section}` (the next unread core or prerequisite primary), else `{kind: "path_read"}`, else `{kind: "none"}`.
- **`depths`**: per depth, the LOs the path's closure reaches there, the distinct primary sections they read (the
  path's choice, else coverage's first eligible one) and their minutes at DL1's reading pace.
- **`path`**: `curriculum.path`'s own view (equal to it, tested), with a held LO's row reduced (below).
- **`pace`**: `goals.goal_pace`'s `as_dict()` (the real rate), null when unreadable.
- **`coverage.unjudged`**: the goal's topics whose coverage is not judged for their current statement (their
  sections read partial); `covering`/`failure`: the background coverage's state in this sidecar.
- **A section level**: `{section_id, title, start_span_id, span_ids, level, mapping, reason_key, reason_md,
  known_level, lo_ids, learning_objects: [{learning_object_id, title, kind, level, reason_key, treatment,
  path_label, override, held, answered_today}], determining_lo_id, learner_line, coverage_line, held, dim, choice,
  judged_per: "section"}`. `span_ids` are the requested range's passages in the section; passages inherit the level
  (decision D1).
- **Status** is the path's (`no_scope`, `ask_depth`, `no_sections`, `pending`, `judging`, `failed`, `stale`, `ready`,
  `withheld`), or `not_a_deliverable` for a goal the learner did not set (only learner goals can be mapped:
  `deliverables.goal_of`); an unknown goal is `not_found`. `goal.lens` checks the Reader is on and the source is
  readable, as `curriculum.guide_slice` does.

## 3. The level rules (`curriculum.goal_lens`; table test `tests/test_reader_rd6a_goal_lens_core.py`)

**Per goal LO covered at the section** (in this order; `lo_level`):

| Rule | Level | `reason_key` |
|---|---|---|
| demonstrated (`lo_certification`) | already shown | `demonstrated` |
| assumed known (an open assumption row, or the path's `assumed` label) | already shown | `assumed` |
| needed only at a deeper depth than the chosen one | later | `deeper_depth` |
| *I know this, check me later* while that check waits (effective `check_pending`) | already shown | `check_pending` |
| *skip it* on the LO's path line | out (no need) | `you_skipped` |
| the section is a needed LO's primary, treatment `introduces`/`develops` | core | `primary` |
| the section is a prerequisite LO's primary | supporting | `prerequisite` |
| the section is an alternate on the LO's path line | supporting | `alternate` |
| another section that introduces or develops it, off the path | supporting | `another_treatment` |
| applies it / mentions it | supporting | `applies` / `mentions` |
| the learner's *also about…* with no judged treatment | supporting | `learner_about` |

**Per section** (`section_level`):

| Case | Level / mapping | `reason_key` |
|---|---|---|
| protected (exam or held-out) section, or a reading outside the library | unmapped / unmapped | `withheld` / `left_out` |
| no coverage row names the section and the path places nothing there | unmapped / unmapped | `unmapped` |
| the path places a goal LO here that coverage no longer names | partial / partial (known level kept) | `partial_unplaced` |
| a goal topic not yet judged could still raise the level (any level but core) | partial / partial (known level kept) | `partial_unsettled` |
| some goal LO needs it | the highest need: core > supporting > later > already shown | the determining LO's |
| mapped, settled, its only goal LO skipped by the learner | skippable | `you_skipped` |
| mapped, settled, rows only for LOs outside the goal | skippable | `out_of_scope` |
| mapped, settled, the judge marked it not about the goal's LOs | skippable | `not_about` |

Equal need goes to path order. `dim` is true for skippable and later sections unless the learner chose *read it
anyway* there (the level itself never changes: the choice keeps the section lit). Dimming on or off is the
client's per-machine toggle (D5).

**The words.** `reason_md` is `deliverable_path_sections.reason` as the path shows it for the determining LO's
primary or prerequisite section (the model's line, or code's), an alternate's own one-line difference, and
otherwise a sentence assembled from the labels (`reason_text`; no model). `learner_line` names the learner's
choice (here or on the path) or "You answered its cold check on your own today."; `coverage_line` reads
"coverage: develops “Eigenvalues” · a goal LO · its primary section · core".

**A due check (spec §12.6.1, D15).** While a check is due on an LO (`checks.due_for`'s rows for the goal), its
band dot has no title or readiness line, `checks.first` names no LO, its path row has `reason: null`, `held: true`
and empty alternate differences, and every section level that covers it has `held: true`, the neutral
`reason_md` (`HELD_REASON`), no coverage line, no determining LO and no LO title. Answered (settled on the learner's
own), the ◇ fills (`check: "answered"`) and the text returns.

## 4. Storage: the path view's stored overrides

- **A path line's choices** (*use this one instead*, *read it anyway*, *skip it*, *check me later*, `none`) are
  `curriculum.path_override`'s, per LO, in `deliverable_path_sections` (migration 228), unchanged. The lens reads
  them through `effective_lines`.
- **"┊ not needed for your goal · read it anyway"** (§12.5) is on a section with no LO on the path, so no path line
  can carry it. It is a `learner_card` verdict in `judgment_ledger` (task `goal_lens_section`, left
  `deliverable_goal:<goal id>`, right `reader_section:<extraction>/<section>`, verdict `read_anyway` or `none`),
  the newest per (goal, section) standing, idempotent by the client's `operation_id` (ledger id `glc_<op>`; a
  reused id with another choice is refused). This is Reader CA5a's precedent for *not about this* and fence 4's
  rule (the goal lens writes only receipts). **No new table, so no migration: 267 is free.**
- **The RD0 write protocol** (`{client_id, seq, ops}`) is the desks' and pads' local-first outbox. These are
  single, immediate choices like `curriculum.path_override`, so they don't join that sequence; a retry is safe
  through the operation id.

## 5. Judgment calls (read these first)

1. **Partial, beyond the spec's literal case.** The spec's "partial" (the path places LOs here that coverage covers
   only some of) can't arise from the path's *effective* lines, which re-validate against coverage. It is kept
   from the current judgment's stored rows (`partial_unplaced`). The case that matters is a goal topic whose
   coverage has never been judged: a section with only other LOs' rows would otherwise read "skippable". It reads
   `partial_unsettled` instead ("missing mapping never becomes not needed", review F6). Core is exempt, since nothing
   can raise it. A topic the background coverage already tried in this sidecar and found no candidate section for
   counts as settled (the Guide's in-memory `attempted` set). After a restart it is unsettled until
   `curriculum.path {judge: true}` runs coverage again, which the frontend should call when it opens a goal.
2. **"Later"** is the path's own depth rule: the needed LOs' prerequisite closure reaches one step at *get the
   idea* and two otherwise (`deliverable_path.CLOSURE_DEPTH`). An LO the deeper closure reaches but the chosen one
   doesn't is later. With today's constants only *get the idea* has later LOs.
3. **Learner skip** takes the LO out of the section's need, so a section about nothing else is skippable with
   `you_skipped`. The spec's skippable rule speaks only of out-of-scope LOs; the learner's own skip is the closest
   honest reading.
4. **Check me later while pending** shows as already shown (`check_pending`), parallel to the spec's "an `assumed`
   label counts as already shown for display".
5. **Before the first judgment** (status `pending`) there are no path lines, so no section is core: sections that
   develop a needed LO are supporting (`another_treatment`). Code's fallback primaries are not used for levels.
   They only open a dot's section, and only for LOs off the path.
6. **Held text (D15)** is enforced in the backend for the surfaces RD6 composes. RD7 adds the inline administration
   and the veils.
7. **No server-side level cache.** The spec suggests one per (goal, extraction, contract head). Each call reads
   the path's inputs once (`path_view(inputs=...)`). The frontend should ask for a whole reading once per window
   (no range) and filter visible ranges client-side, invalidating on path, coverage, depth, override or check
   changes. A cache keyed on the path state key, the overrides and the certification digest is the follow-up if
   that proves slow.
8. **Depth sizes** are minutes at DL1's reading pace and section counts. Pages are not given (no page map on every
   source), and transcript sections are counted in words like any section, not in video seconds.

## 6. What the frontend half needs

- One `goalBand` per desk goal. Its `path` is the path view's data, `depths` the depth buttons with their sizes
  (`curriculumSetDepth` sets the depth), `unmatched` the dashed dots (`curriculumScopeDecide` adds a phrase),
  `next` "next for the goal", `pace` the "am I ready?" pace line (null deadline: "no deadline, so no pace target").
- `goalLens` per source window (whole reading; ranges for transcripts with `t0/t1`). The marks come from `level`
  plus `mapping` (unmapped: no bar; partial: a short grey tick), dimming from `dim`, the why card from `reason_md`,
  `learner_line`, `coverage_line` and `judged_per`, and the shelf row from the reply's `mapping`.
- `curriculumPathOverride` for a line's choices (exists), `goalSectionChoice` for *read it anyway* on a dimmed
  section, and `curriculumPath {judge: true}` to start what a goal owes (the "map it" empty state uses
  `curriculumSetScope` for a goal with no resolution).
- "You are reading" maps the focused window's position through the lens levels (client side). The Teacher lesson
  per LO comes from the existing lesson RPCs. Exercise picks are the path lines' `exercise`.

## 7. What waits

- **RD7:** inline checks (`check.begin_inline` and the rest), veils and `check_veil_sets`; the closed marker; the
  ◇ click to administer. RD6 shows due/answered and hides held text only.
- **Deferred (§17):** passage-grain levels (an `aside` role). Video chapters (RD10) refining transcript sections.
- **RD-retire:** the lens replaces the Guide rail's path card and the reading-path panel then. Both stay as they
  are now.

## 8. Persisted meaning and acceptance

- **No persisted meaning moves** (spec §15.3: RD6 "none, display of the real model"). Nothing scores, schedules,
  certifies or serves from the lens. The section choice is a RAW_LEDGER verdict nothing else reads. The two
  refactors in `deliverable_path` keep every caller's behaviour (`path_view` reads its inputs when none are given;
  `coverage_owed` calls `owed_among` with the same ids). No tag. `tests/test_identity_pins.py` is unchanged and
  passes; no row-recording golden moved.
- **Replies equal on a rebuild:** `test_the_replies_are_equal_after_a_rebuild_of_derived_state` compares the band
  and both readings' lens before and after `rebuild_all_derived_state` (certification and mastery are derived).
- **No model call, no write:** `test_band_and_lens_make_no_model_call_and_write_nothing` (every fake's call
  count zero, every table's row count unchanged).

## 9. Tests

New: `tests/test_reader_rd6a_goal_lens_core.py` (the table test of every rule: 34 rows, plus the held, reason,
learner-line, vocabulary, band and next-step tests), `tests/test_reader_rd6a_goal_lens.py` (the RPCs over the real
path and coverage: levels, a deeper LO and a depth change, overrides, read it anyway, unjudged coverage settling,
a due then answered check, the rebuild, no call or write, empty states, ranges), helper `tests/goal_lens_helpers.py`.
Edited: `tests/test_reader_rd0_fences.py` (the goal lens is built: it is no longer declared-only, its modules are
the read-only fence's sources, and a new test breaks the fence and the grader fence with one import from each),
`tests/test_mobile_allowlist.py` (`READER_RD6A_RPCS`).

No defect was found, so the ledger gains no row.

## Fix round (backend): the RD6 adversarial review (Codex Astra, 2026-11-23)

Branch `reader/rd6fix`, from the second integration batch (`326aac6928`), both halves in one branch. The review had
2 blockers, 8 majors and 4 minors; each was checked against the code here and every one held. Each has a fail-first
test (shown failing against the code before the fix) and a ledger row, RD6-1 upward. No migration, algorithm tag,
prompt or config key; no persisted row changes meaning (the coverage freshness fixes change what a read concludes,
not what a row says). The frontend sides are in RD6b's fix round.

| Finding | Ledger | What changed | Fail-first test |
|---|---|---|---|
| Blocker 1: a held LO's path row still named it (title, phrase, section titles, treatment words, exercise label, a dot's primary, `next`) | RD6-1 | One server function masks every text-bearing field of the band, its path and the lens: `GL.protect_band` / `GL.protect_lens` in `curriculum.goal_lens`, and `band_view` / `lens_view` require a `Protection` (no reply leaves unmasked). Neutral words replace text; ids, numbers and flags stay | `test_reader_rd6_fix_protection.py`: the field table (`test_every_text_bearing_band_field_is_masked`, 27 rows), `test_a_held_los_own_path_row_names_nothing` (end to end, every string of both replies walked) |
| Blocker 2: masking held only the goal's own LOs; a section shared with another goal's due LO, a reason naming it, a goal containing only the other LO | RD6-2 | `goal_lens_reads.protection` reads every due LO whatever the goal: their titles (matched as whole words in any text), the sections treating them (standing coverage about them, their placements in any goal, the checks' hosts), the LOs depending on them (prerequisites, or assumed by a section read for them). A protected section is held in every goal's lens; a reason that names a held LO or belongs to a dependent LO is withheld | `test_another_goals_due_check_masks_a_shared_section_and_names_nothing_of_it`, `test_every_text_bearing_lens_field_is_masked` (15 rows) |
| Major: a changed section's needed rows dropped, the section skippable | RD6-3 | A goal LO whose rows on a section were all written against an earlier version of it (section hash), with none standing now, leaves the section partial (`partial_unsettled`), never skippable or unmapped (`SectionReads.stale`) | `test_reader_rd6_fix_freshness.py::test_a_section_changed_since_a_needed_los_rows_is_unknown_for_it_never_skippable` |
| Major: "tried once, found nowhere" settled after the library changed | RD6-4 | A coverage attempt is keyed by the LO's statement and the library's scope signature (`DP.attempt_keys`): a reading added, re-extracted or switched unsettles the LO for the lens and owes it to coverage again | `test_an_lo_tried_and_found_nowhere_is_settled_only_against_that_library` |
| Major: band and lens reads could write files (`curriculum._require` finishing a stopped publication) | RD6-5 | `goal.band` and `goal.lens` take `curriculum._require_read` (the same refusal, no recovery); the next curriculum action finishes the publication | `test_reader_rd6_fix_reads.py::test_band_and_lens_reads_leave_an_unfinished_goal_change_for_the_next_action` (every vault file's size and time) |
| Major (backend side): a ready band never learned a check fell due | RD6-7 | `goal.band` carries `next_check_due` (the earliest check not due yet, from the serving view the due checks already build, so one build serves both); the frontend reads the band again then | `test_the_band_says_when_the_next_check_falls_due_so_it_is_read_again_then` |

Corrections to this record: §5 judgment call 6 ("held text is enforced in the backend for the surfaces RD6 composes")
was true only of the reason and alternates' differences of the goal's own LOs; it now holds of every text-bearing
field and across goals. §5 judgment call 1's settled set is now bound to the library as well as the statement. §9's
"no model call, no write" test counted table rows only; the new reads test checks the files.

Judgment calls: a dependent LO's reason is withheld, not rewritten (no prompt); a section title that names a held LO
is neutral even when the section is not known to treat it (the words alone would tell); the neutral words are
"a topic with a cold check due", "a section held until its cold check", "an exercise held until its cold check".
