# Refactor G6.2 and G6.3: one table of surface sets; the passage-admission extraction not done

Steps G6.2 and G6.3 of `docs/specs/refactor_strategy_v3.md` (arc G, **G6**), built from the design
`docs/reviews/refactor-g6-design.md` (§1 the surfaces, §3a the deliberate differences, §5 G6.2 and G6.3). Branch
`refactor/g6.2-surface-sets` from main `713a0efd08`. Structure track: nothing served, stored or sent to a model
changes. `tests/test_protection_surface_matrix.py` passes unedited and no identity pin moved.

**Result.** G6.2 is done: every protection surface has a row in one table, `SURFACE_SETS` in
`src/learnloop/content/sources/exam_material.py`, and every surface that reads a set object reads it through that
table. G6.3 stopped under the strategy's cost rule: the one extraction the exits' code allows covers three of
the design's exits and adds about 23 lines while removing 21, and no test gets simpler (§3). No new defect was
ledgered; one asymmetry between exits is reported for a decision (§3.3).

## 1. The table (G6.2)

`exam_material.SURFACE_SETS` maps each surface to one of three values:

| Value | Meaning | Reader |
|---|---|---|
| `ALL_EXAM` | all exam material (rules 1-4, the held-out partition included) | `exam_material` |
| `HELD_OUT` | the held-out partition (rules 3-4 and the signals) | `held_out_material` |
| `NO_EXAM_SET` | the surface answers another question (device, workflow, exposure, the learner's own raw reading) | none |

Two small readers select by row: `surface_material(vault, repository, surface) -> Material` (the row's set) and
`surface_exam_material(vault, repository, surface) -> ExamMaterial` (all exam material with its verdicts and
held-out part; any other row raises `ValueError`, so a call and its row cannot disagree). An unknown surface
raises `KeyError`. Both call the existing readers through the module's globals, so every test or fault patch on
`exam_material` / `held_out_material` still reaches them.

Compositions stay with their owners and are not table values: teaching adds roles and exercise links
(`corpus.teaching_exclusions`), the item union its reservations, cold checks and probes
(`learner_protection.withheld_items`), AD the exam reservations, serving its kill switch and reservations. The
table records the exam set each is built on, as the design's own example does (`"teaching": "all_exam"`).

**Where it differs from the design.** The design proposed one `material_for_surface` returning a `Material`.
Several all-exam surfaces need the whole `ExamMaterial` (the canonical import's refusal carries `verdict`s;
section coverage keeps the object in `Protection.material`; the book guide's and learner protection's tests fake
`exam_material` with objects that have no `.material`), so a second reader returns it, checked against the row.
A third value, `NO_EXAM_SET`, gives the device, workflow, exposure and raw-reading columns a row (the brief:
every matrix surface has one). Keys are plain strings, as in the design's call-site example. Two rows are a
surface's second decision, which its matrix column does not ask: `library_ask_anchor` (an ask anchored on a
held-out passage refuses; the matrix's ask has no anchor) and `library_tutor_refusal` (a held-out pin refuses
the pinned tutor; the column's exam-only cells are the drop).

### Per surface: where the set was chosen, before and after

| Row | Matrix codes | Set | Before | After |
|---|---|---|---|---|
| teaching | TE, MR | ALL_EXAM | `corpus.teaching_exclusions`: `EM.exam_material(...).material` | `EM.surface_material(..., "teaching")`; MR reads it through TE |
| reader_ask | RA | HELD_OUT | `held_out_material` in `reader_dialogue.ask`, `tutor_qa.ask_question`, `reader_tutor._admitted` | `surface_material(..., "reader_ask")` at all three |
| reader_presets | PS | HELD_OUT | `reader_requests.model_synthesis`: `held_out_material` | `surface_material(..., "reader_presets")` |
| reader_checks | CK | HELD_OUT | `jobs._refuse_held_out_reader_material`: `held_out_material` | `surface_material(..., "reader_checks")` |
| reader_guidance | GU (RD's actions) | HELD_OUT | `reader_guidance.held_out_sections`, `reading_protection`: `held_out_material` | `surface_material(..., "reader_guidance")` |
| reader_import | RI, RN | HELD_OUT | `jobs.handle_reader_exercise_import`: `exam_material(...)`, then `.is_held_out` and `.held_out`; `exercise_authoring.author_exercises`' default `held_out_material` | `surface_material(..., "reader_import")` at both; the job reads the held-out partition directly (the same material: `ExamMaterial.held_out` and `held_out_partition` are built by the same `_add_protection`) |
| canonical_import | CI, CN | ALL_EXAM | `source_exercise_import.import_source_exercise`: `exam_material` | `surface_exam_material(..., "canonical_import")`; the author still gets `.material` |
| book_solution | BS | ALL_EXAM | `find_book_solution`: `exam_material` | `surface_exam_material(..., "book_solution")` |
| figures | FI | ALL_EXAM | `figures.protection.withheld_message` → `spans_withheld` | unchanged (named reader, in the row's comment) |
| section_coverage | SC, TB | ALL_EXAM | `section_coverage.read_protection`: `EM.exam_material` | `EM.surface_exam_material(..., "section_coverage")` |
| quote | SQ | ALL_EXAM | `source_ref_protected` over learner protection's exam object | that object is read under the `learner_protection` row (below) |
| mcp_passages | MC | ALL_EXAM | `remote.sources._classifier`: `exam_material` | `surface_exam_material(..., "mcp_passages")` |
| book_guide | BG | ALL_EXAM | `reading_paths.path_inputs`: `EM.exam_material` | `EM.surface_exam_material(..., "book_guide")` |
| leakage_floor | LF | HELD_OUT | `practice_leakage`: `held_out_spans` (the text) | unchanged (named reader) |
| reserved_questions | RF | ALL_EXAM | `practice_leakage.reserved_questions`: the item union's exam reason, plus LF's text | unchanged (named readers) |
| library_ask_anchor | (LA's anchor) | HELD_OUT | `library_ask.ask_library` and `open_comparison`: `EM.held_out_material` | `EM.surface_material(..., "library_ask_anchor")` at both |
| library_ask | LA | ALL_EXAM | `find_sources` pool: `exam_withheld` | unchanged (named reader) |
| library_result | OR, LJ, TJ | ALL_EXAM | `library_ask.withheld_now`: `EM.exam_material(...).withheld` | `EM.surface_exam_material(..., "library_result").withheld` |
| library_tutor_refusal | (PT's refusal) | HELD_OUT | `library_ask.ask_tutor`: `EM.held_out_material` | `EM.surface_material(..., "library_tutor_refusal")` |
| library_tutor_pins | PT | ALL_EXAM | `source_retrieval.tutor.PinnedSpanProvider`: `exam_withheld` | unchanged (named reader) |
| compare | CM | ALL_EXAM | `compare.compare_sources`: `exam_withheld` (three sites); `open_comparison`'s anchor: `EM.exam_material` | `exam_withheld` unchanged; `open_comparison`'s anchor `EM.surface_exam_material(..., "compare")` |
| routine_serving | RT, OT | HELD_OUT | `serving_exclusions`: `held_out_items` behind the switch | unchanged (named reader) |
| practice_pick | PK | HELD_OUT | `practice.refuse_protected_pick`: `held_out_material` | `surface_material(..., "practice_pick")` |
| session_serve | SS | HELD_OUT | `serving.refuse_held_out_item`: `held_out_material` | `surface_material(..., "session_serve")` |
| exposure_with_held_out / exposure | EH / EX | HELD_OUT / NO_EXAM_SET | `exposed_items(..., with_held_out=)` | unchanged (named flag) |
| cold_administration, serve_eligibility, device_eligibility, followup_door, followup_feedback, item_detail | CO, SE, DV PF, FD, FB, KY | NO_EXAM_SET | no exam read | unchanged |
| learner_protection | LP, AP, LC | ALL_EXAM | `learner_protection.withheld_items`: `EM.exam_material` (and `held_out_items`) | `EM.surface_exam_material(..., "learner_protection")`; `held_out_items` unchanged |
| figure_prebuild_items | IP | NO_EXAM_SET | reservations, cold checks, probes; FI reads the spans | unchanged |
| ad_forecast | AD | HELD_OUT | `adaptive_difficulty.protection.protection`: `held_out_material` | `surface_material(..., "ad_forecast")` |
| phone | PW PG PI RV GP PA PH AS | ALL_EXAM | `phone_media.phone_withheld`: `exam_material`; `phone_reader.destination_material`: `exam_material(...).material` | `surface_exam_material(..., "phone")`, `surface_material(..., "phone")` |
| phone_dose_offer | DO | HELD_OUT | AD's view (G6-P4, not driven by the matrix) | unchanged |
| mcp_library | ML | ALL_EXAM | `remote.views.library`: `exam_material`, labels only | `surface_exam_material(..., "mcp_library")` |
| library_search, reader_history, reader_render | LS, DH, RD | NO_EXAM_SET | no exam read (RD's action metadata is `reader_guidance`'s) | unchanged |

Readers left named (`spans_withheld`, `exam_withheld`, `held_out_items`, `held_out_spans`, `exposed_items`)
are each fixed to one set already, and the row's comment names them. Moving those call sites onto the table
would change signatures that many tests fake with fixed-arity lambdas, and `exam_withheld`'s early return on no
keys (no read) would need a third table reader; the test below holds their rows to the matrix all the same.
Readers of E or H outside the matrix's surfaces (passage cues, kept comparisons, the reader digest, deliverables,
source roles, cues, macros, figure grounding and source checks, workbench draws, the router reader, generation)
were not migrated: they have no row.

### The test

`tests/test_protection_surface_sets.py` (new; 103 tests, about 2 s) reads the matrix's `EXPECTED_TABLE` and
`NOT_DRIVEN` from its file with `ast` (a test file never imports another) and asserts:

- every matrix column maps to a row, and every row is reached by a column or is a named second decision;
- where the sets part (fixtures 1 and 2: `1.paper`, `2.exam`, `2.split-exam`, `6.1*`, `6.2*`: all exam
  material, not held out), an `ALL_EXAM` surface's cells are W or R and a `HELD_OUT` or `NO_EXAM_SET` surface's
  are S, for every driven column (RF on its item rows only: its span rows ask LF's question; ML excluded: it
  lists every title and only labels);
- where they agree (fixture 3: `3.held`, `6.3*`), every surface that reads an exam set withholds and every
  `NO_EXAM_SET` surface shows;
- on the textbook retrieval vault's unmarked exam member, `surface_material` reads H for `reader_ask` and E for
  `phone`, `surface_exam_material` serves `canonical_import`, and a row naming another set, or no row, raises.

Mutation check (not committed): with `reader_ask` set to `ALL_EXAM` and `routine_serving` to `NO_EXAM_SET`,
4 tests failed (RA's parting cells; RT's and OT's fixture-3 cells; the vault reader test), 99 passed.

## 2. Net lines (G6.2)

- `ba8c3cd55b` (table, readers, 20 call sites, the test): src +143 −43 (**+100**), test +149.
- `cfd267f27b` (the Reader tutor's second guard, `open_comparison`): +7 −7 (**0**).
- The docs commit: this record, three lines in the Privacy and Trust note.

The design expected G6.2 to add a little; most of the +100 is the table (one line and comment per surface).

## 3. G6.3: why the extraction stopped

### 3.1 The exits, read at this tip

| Exit | What it resolves | Set | Failure | Reasons it records |
|---|---|---|---|---|
| `tutor_qa._admitted_linked` (the linked fallback) | each block through `BlockSource` (the extraction's IR) | E, read lazily inside `source_retrieval.tutor.reference_filter`, after the scope check | raises | `its passage could not be read`, `outside the tutor's sources for this question`, `exam material`, the lead-role and overlap reasons; stored as the delivery receipt's `linked_withheld` |
| `PinnedSpanProvider` (pinned tutor) | `blocks_by_key` | E (`exam_withheld`) | raises | `no such passage`, `it is exam material`, scope, overlap; the manifest's `dropped_pins` |
| `TutorPool`, `reader_tutor._admitted` (retrieved hits) | none (hits exist) | teaching scope; H as a second guard, counts only | raises | counts |
| `library_ask.withheld_now` (kept results, organizer, both delivery guards) | `blocks_by_key` | E | any error withholds every key | none (refuses whole) |
| `deliver_passages`, `deliver_tutor` | through `refuse_withheld` → `withheld_now` | E | as above | none |
| `compare_sources`: pins and anchor (`admitted`) | `blocks_by_key` (and again for pins at line 458) | E, then the caller's `withhold` | raises | `no such passage`, `it is exam material`, `the caller may not read it`, scope, overlap; the result's `dropped_pins` |
| `compare_sources`: candidates, `_also_in` | none (hits exist) | E, then the caller's `withhold` | raises | the manifest's counts |
| `find_sources` final pool | none | E | raises | the manifest's count |
| phone: `phone_withheld`, `refuse_if_withheld`, `sendable_exchanges` | none | E, whole reading or spans, with a refusal message | an unreadable predicate withholds the whole reading (never raises) | the refusal message |

The delivery guards already share one function (`refuse_withheld`). The only mechanics duplicated across exits
are "resolve each key to a stored block, then the set": the pinned provider, compare's pins and
`withheld_now`, whose reason words already agree.

### 3.2 The measurement

A draft `source_retrieval/admission.py` (`admit_passages(vault, repository, keys, surface) -> (blocks,
withheld-with-reason)`, 32 lines) applied to those three exits measured +41 −21 before their three import lines,
so about **+23 net**, and reached three of the design's exits. No test got simpler: the tests drive the exits,
none patches the duplicated lines. The draft was reverted; nothing of it is committed.

Reaching the other exits as a pure extraction is not possible:

- the linked fallback reads E only after a block passes the scope, and records the scope reason first; a
  shared key-level check reads E for every linked span and names `exam material` for a key that is both out of
  scope and exam material, which changes the stored `linked_withheld` receipt;
- the search-hit exits (retrieved pool, compare candidates, `find_sources`) hold blocks already; resolving them
  again is an extra read per call;
- the exits fail differently on purpose (refuse the request; withhold a kept result whole; withhold a phone
  reading whole and answer), and each records its own reason words in a persisted receipt or result;
- compare's caller withholding is its documented caller policy.

Each of those would be a named argument, so one function for all exits would carry the set, the failure shape,
the reason vocabulary, the reason order, the caller's withholding and the item rules as arguments: more code
than the duplication it replaces. Under the cost rule, G6.3 stops here.

### 3.3 Differences between exits

Deliberate, as the design and the fixes record say: H for the Reader and E for the library, pins, compare, MCP and
the phone (§3a); the pinned tutor refuses a held-out pin and drops an exam pin, while its finished job is judged
by E (`refactor-g6-fixes-1.md`, judgment 1); a kept result fails closed by withholding, a fresh request by
refusing, the phone by withholding the whole reading.

One asymmetry, **not ledgered**, for the owner or orchestrator to rule on: while an item is being practised, a
block whose own lead names an exercise or a solution ("Solution:", "Exercise 3.2") is withheld by
`reference_filter` (references and the linked fallback) and by `reader_tutor.ItemBoundGuard` (the Reader
tutor) even when its role hint misses it, but not by the pinned tutor's pins, compare's pins and candidates
under assisted practice, or the tutor's retrieved pool (`tutor_pool`: answer overlap only). The item-bound
scope drops blocks by effective role hint, and `corpus.effective_hint` only demotes a hint, so a solution lead
under an `ordinary_prose` hint stays in scope. Why not ledgered: no test here drives it, it is the item's-own-
solution question (Q8), not exam protection, the item's linked passages and its answer overlap are guarded on
every path, and a pin is the learner's own choice; the realistic case is another exercise's solution with a
wrong hint. If it is ruled a defect, its fail-first test is an item-bound pinned (or retrieved) passage whose
lead is `Solution:` with an `ordinary_prose` hint, not linked to the item and not reproducing its key.

## 4. What I ran

Every pytest through the brief's wrapper (`env -i`, empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`), from a
script file, `-n 1`, in a 3 G scope, one at a time. Results are in the implementer's report; the gate list is
the brief's.

## 5. Not verified

- The landing gate, the arc-close gate, durability, `--fresh-connections`, P-shadow and P-draw (structure step:
  the claim of no change rests on the matrix, the identity pins and the affected tests).
- Affected tests outside the name filter (838 files selected; 295 run) and every `arc_close` test.
- The asymmetry in §3.3 (read, not driven).
- The matrix's five undriven columns (BS, DO, TJ per row, CM, FB) hold their rows only through the
  design's inferred cells; the new test does not assert them.
