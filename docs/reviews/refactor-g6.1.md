# Refactor G6.1: the protection surface matrix

Step G6.1 of `docs/specs/refactor_strategy_v3.md` (arc G, **G6**), built from the design `docs/reviews/refactor-g6-design.md` (the build sheet: §1 surfaces, §2 fixtures, §3 matrix, §4 fail closed, §5 G6.1, §6 open questions). Branch `refactor/g6-protection-authority` from main `e6314fc0df`. Tests, one ledger section and this record; nothing under `src/` or `apps/` changes.

**Result.** `tests/test_protection_surface_matrix.py` pins what 51 of the sheet's 56 surfaces answer today for each of 37 fixture rows: 1,502 cells, each asked of the production function, plus 100 fault cells and 30 reach cells. The sheet's inferred answers held in all but 11 cells, none of them a leak; 14 of its open cells (`?`) are settled. Six of its seven proposed defects are confirmed (G6-P1, P2, P3, P5, P6, P7), each with today's answer pinned and a strict xfail for the fix (ledger, "From G6"). G6-P4 was not driven. No new defect. The file runs in about 46 s, so it is marked `slow`.

## 1. The world and its fixtures

One vault (`tests/protection_matrix_helpers.py`, `build_world`), built once per module from `tests/source_service_fakes.build_textbook_vault`. Every fixture is a namespaced source (`src_g6*` / `rev_g6*` / `ext_g6*`) whose every block, heading included, carries one letters-only marker word (`GSIXPAPER`, `GSIXHELDEXAM`, ...); the markers share no numerals or words, so a prompt, payload or lexical fingerprint that carries a block is found by its word. Each source's original is a distinct stored PDF (pages vary), so the phone's page endpoint reads the right file. The world sets `source_service.llm_price_per_million = 1.0`: without a price the canonical import's admission skips its author before the context is built (CN could not be read).

| Row | Built with | Target |
|---|---|---|
| 0.control | a clean textbook `ext_g6clean`, one unit per clean item plus the control unit | control text span |
| 1.paper | `seed_source`, member `default_role: exam`, no marks or signals | its text span (E whole, H empty, asserted) |
| 2.exam / 2.neighbor | two units on two pages; member textbook with scope `r2_exam → exam`, `scope_extraction_id`/`scope_revision_id` set | exam text / theory text |
| 2.split-exam / -theory | the `_add_split_chapter` recipe, namespaced (`split_at_heading` override through `save_unit_selection`; scope names `chapter#Exam`) | each half's block |
| 3.held / 3.neighbor / 3.camel | `save_unit_selection(..., exam_use_modes={h3_exam: held_out_evaluation})` | held text / theory text / held text selected as `spanId` |
| 3.unresolved | the same writer, the mark naming `no_such_unit` | theory span (whole reading held) |
| 4.unmarked | reading A marked; `exam_scope_fixtures._second_reading` adds B, unmarked, same revision | B's text span |
| 4.legacy | `repository.upsert_unit_selection` without `marks_made_on` | theory span (whole reading held) |
| 5.signal | `insert_unit_inventory` with a held-out signal, `made_as_role="exam"` (writes the ledger row too) | signal span |
| 5.unknown | one `source_held_out_signal_marks` row with `extraction_id` NULL, plain SQL, triggers on | theory span (whole reading held) |
| 6.Ncanonical / 6.Nblock | items with a `canonical_exercise` only, or a block-locator source ref only, on 1, 2.exam, 3.held, 4.unmarked, 5.signal | item + its span |
| 6.whole-ref | a source ref naming `ext_g6h3` with no block | item |
| 6.exam-reserved, cold-task, remediation, assess-reserved, probe, held-grade | clean items carrying both a canonical exercise and a block ref (as an import writes them), held by: an unreleased `exam_pool_items` row; a pending `cold_retry` task (`not_before` 2099); a repair episode in `treatment` with `cold_item_id` and no task; a live assessment reservation of its legacy surface (`ensure_activity_family/card/card_version/surface`, `insert_surface_reservation`); `practice_mode: diagnostic_probe`; a held grade (`_held_apply`) | item + its own clean span |
| 6.presented (reach only) | an ordinary clean item with a completed `probe_presentations` row (valid episode and segment rows) | item |
| 7.reader-import | `handle_reader_exercise_import` on the paper with `FakeClient`, background key checks off | the item it wrote (its stem is the paper's text) |
| 8.invalid / 8.empty | a backup-API copy of the world whose `source_sets.yaml` is unparseable / zero bytes | 6.1canonical's item and span |
| 9.switch-off | a copy with `goals.held_out_selection = false` (`set_config_switch`) | 6.3canonical's item and span |
| +.shown | a clean item with one recent unlinked `tutor_answer` reveal | item |
| +.held-feedback | a clean item only: **no held follow-up workflow was built** | item (KY only) |

Every item but the probe has one recorded attempt (`_graded_apply`), so the learner context has a trace to show or withhold; attempts are made before the holds, so none claims a task. A surface that writes what another reads (an exposure, an Ask exchange, a queued request, an import) runs on its own copy of the world (`Probe.world(..., own=...)`), so no cell depends on the order surfaces ran in.

## 2. Surfaces covered

Driven through the production function (51): TE MR RA PS CK GU FI IP SC SQ MC | CI RI LF RF | RT OT PK SS DV PF EX EH CO SE | LP AP AD LC | PW PG PI RV GP PA PH AS | ML LA OR LJ PT TB LS DH FD KY BG | RD RN CN. The sidecar's surfaces (RA PA RV RD GP PH DH AS LA OR LJ PT) are called through `METHOD_REGISTRY` on a `SidecarContext` loaded with `maintenance=False`, the phone ones inside `ctx.acting_as(RequestOrigin(..., phone_reader=True))`; each context is closed when its test ends, so its drain and quick-check threads are joined. Model-facing surfaces get a recording double that stops the request at its first model call: a cell is S when the target's marker is in what the model was sent, W when the model was reached without it, R when the request was refused first.

How some cells are read:
- **OR** is its current-key check (`refuse_withheld`): R when it refuses, else S. The organizer pool after the check is empty for a planted kept hit, which is not a protection answer.
- **OR, LJ, PT** read a kept ask whose search returned the target, planted by answering the handler's `propose_sources` with the target's passage (a search made before the mark).
- **LA, PT** are span questions: an item row asks them of its span, once per span.
- **CK** in the matrix is the section check; the inquiry and selection callers are a reach test.
- **IP / MC** read the item's own passage; **RF** the item's stem, else the span's text; **LC** the item stem's first word in the whole context; **KY** whether the detail carries the key.

Not driven (5), each a hole in the proof; their columns stay in the table as the sheet's inferred answers and nothing asserts them (`NOT_DRIVEN`):
- **BS** (`find_book_solution`): needs the target inside a solution region (a solution-role block after it); adding one to every fixture changes every other surface's neighbours. Fixture work, no seam.
- **DO** (phone dose offer): the dose arm needs AD's material view and a deterministic draw, which live in the AD helpers' own world (`tests/ad1_reading_opportunities_helpers._setup`, `FakeMap`), not composed here. Fixture work, no seam.
- **TJ** per row: a completed tutor job naming a row's target needs that job made before the row's mark; the single world has its marks from the start. Driven once as G6-P2's scenario (a mark made after the answer).
- **CM** (`compare_sources`): needs the comparison's and verification's model doubles and pinned passages; not done for time.
- **FB** (held follow-up feedback): no held workflow was built.

## 3. Cells where the code differed from the sheet

| Cell | Sheet | Code | Why (evidence) |
|---|---|---|---|
| BG × 2.split-theory | S | W | `extraction_sections` groups the split chapter as one section (`chapter`: s1, s2): the raw unit, not the split children. `path_inputs` withholds a section with any exam span, so the theory half goes with the exam half. Over-withholding. |
| GP × 2.split-theory | S | W | The same single section: the phone's guide masks its label (`Section 1`). |
| TB × 2.split-theory | S | R | Section coverage's `Library` reads the same section as withheld: "That passage is kept for your exam". |
| LF × 4.unmarked, 6.4canonical, 6.4block | W | S | `held_out_spans` fingerprints the held-out spans of marked readings; reading B, held back whole, is not fingerprinted. In this fixture B's text differs from A's; in a real re-read it is the same book text, whose held unit A's fingerprint already covers. Not ledgered (no realistic leak found); flagged for the owner. |
| RF × 4.unmarked | W | S | The same inventory (`reserved_questions` adds `held_out_spans`). |
| RF × 1.paper | S | W | Fixture 7's stem is the paper's own text and `withheld_items` withholds fixture 7 as `WITHHELD_EXAM` (K1-2), so the paper's words are a reserved stem. A world-composition effect of K1-2, not of the paper. |
| LS × 4.unmarked, 6.4canonical, 6.4block | S | W | `search_library` reads the library scope, which holds each source's current reading; B is an alternate reading, so it is never searched. Not a protection decision. |

Open cells settled: KY × 8.invalid and 8.empty are R (`SourceSetsUnreadable` from `practice_item_detail`, K1-10); CN × 2.exam, 2.split-exam, 3.held, 3.camel, 5.signal, 6.2/6.3/6.5 canonical and block, 9.switch-off are S (G6-P7). DO's three `S?` and TJ's two `R?` are not settled (not driven).

## 4. Deliberate differences (sheet §3a), as pinned cells

All hold as the sheet reads them: E-only rows (1.paper, 2.exam, 2.split-exam) are S for RA PS CK GU RI and W/R for TE MR FI SC MC CI and the phone (D2, D3); PT drops an E-only pin (W) where RA answers on it (S); E-only items and fixture 7 are S for RT PK SS and W for LP AP LC, with RF reserving fixture 7's stem (K1-2, unresolved owner call); LP withholds the cold, remediation, assessment and probe items where AD admits them (D5); the pre-task remediation item is S for RT and W for OT CO LP (two lifetimes); RF is S for cold and probe items (the floor's subset); 6.whole-ref is W for SQ and S for every item gate (D9); 9.switch-off is S for the serving gates and still W/R for Q2, Q6 and the phone (D7); LS, RD and DH show protected local text (local reading); ML lists every title (title-only contract); PI refuses the image original of a reading whose page PG serves (2.neighbor, 2.split-theory, 3.neighbor); DV PF SE FD answer device, eligibility and workflow questions and admit protected items.

## 5. Defects

| Id | Confirmed | Today's pin | Fail-first test (strict xfail) |
|---|---|---|---|
| G6-P1 | yes: IP is S for 6.exam-reserved while FI is S (clean source) | matrix IP × 6.exam-reserved | `test_an_exam_reserved_items_own_passage_is_withheld_from_figure_prebuilds` |
| G6-P2 | yes: a finished pinned answer is returned twice after its passage is held out | `test_a_completed_pinned_answer_is_returned_after_its_passage_is_held_out` | `test_a_completed_pinned_answer_is_refused_once_its_passage_is_held_out` |
| G6-P3 | yes, through the RPC with `reader_inquiry` off: the earlier answer quoting a since-held neighbour is in the next model context | `test_a_legacy_reader_thread_sends_an_answer_grounded_in_a_passage_held_out_since` | `test_a_legacy_reader_thread_leaves_out_an_answer_grounded_in_held_out_material` |
| G6-P4 | not driven (DO); neither confirmed nor refuted | none | none |
| G6-P5 | yes: a kept job naming `g6missing_extraction:s1` is returned and its notes judged | `test_a_kept_answer_naming_a_passage_that_does_not_exist_is_returned` | `test_a_kept_answer_naming_a_passage_that_does_not_exist_is_refused` |
| G6-P6 | yes: RI is S for 3.camel (held text reaches the author) and R for 3.held | matrix RI × 3.camel | `test_a_camel_case_selection_of_held_out_material_is_refused_before_the_author` |
| G6-P7 | yes, both callers: RN is S for 3.held, 3.camel, 5.signal (and their items, 9); CN is S for every partial row | matrix RN and CN columns | `test_the_reader_imports_author_never_sees_a_held_out_neighbour`, `test_the_canonical_imports_author_never_sees_an_exam_neighbour` |

Each xfail was run with `--runxfail` and fails at its own assertion (or `DID NOT RAISE`), not in setup. In the two-unit fixtures the protected block next to the selected theory exercise is the protected unit's heading (it carries the unit's marker); in the split chapter it is the exam half's text. No new defect (G6-P8 onward). One observation, not ledgered: `corpus.item_exclusions` reads an item's source refs and entity links, not its `canonical_exercise`, so an item with a canonical exercise and no source ref names no own passage to IP or MC. Every production writer found writes both (`exercise_authoring` drafts); only the test recipe `_with_exercise` writes one alone, so the clean items here carry both.

## 6. The sheet's §6 questions

1. Can the phone dose draw select an E-only extra question? **Not settled**: DO not driven.
2. Does the canonical import's full wrapper keep the protected adjacent block? **Yes**: CN is S for every partial row (the statement reader passes the safe selection; `_context_blocks` adds the neighbour).
3. Does bad source-set metadata block `practice_item_detail`? **Yes, always for this read**: `SourceSetsUnreadable` from the plain detail (no `administer`), and also when the exam predicate raises (fault cells KY R/R, the clean item too). Side effects were not inspected.
4. Does a translated stale Reader selection reach a different protected block? **Not settled**: no render view or re-anchor mapping was built.
5. Does the legacy-history leak survive the direct tutor and the inquiry-off RPC? **The RPC: yes** (G6-P3's pair). The direct `tutor_qa.ask_question` caller was not run.
6. Is the phone's final provenance check enough after a legacy thread reached the model? **Not settled**: not run on the phone.
7. Are missing figure ancestors handled at final delivery? **Not settled**: the figure lineage and `shown_figure` were not driven.
8. Are no-key or damaged cached answers safe? **A well-formed key naming no passage is not** (G6-P5, kept job and organizer). Empty provenance was not run.
9. Does the fixture-7 import create shown-material evidence? **No**: EX and EH are S for 7.reader-import.
10. K6-12/13 retry settlement: outside this step's cells; not run.

## 7. Fail closed

The exam predicate's readers (`exam_material`, `held_out_material`, `held_out_partition`, `held_out_items`, `spans_withheld`, `exam_withheld`, `role_material`, `held_out_spans`, `source_marks`) patched to raise in every module that bound them; each driven surface asked about a protected and a clean target (`FAULT_EXPECTED`, 100 cells). Fixture 8 is the matrix's own rows.

- Refuse (R): TE MR RA PS CK GU FI SC SQ MC CI RI LF RF RT OT PK SS EH PG PI RV GP PA LA OR LJ PT TB KY BG RD RN CN.
- Withhold (W): IP (nothing readable: every prebuild withheld), LP AP AD LC (unavailable), PW PH AS.
- **Open to the fault (S on the protected target), as pinned:** DV, PF, SE, FD (device, eligibility and workflow doors: no exam read), EX and CO (shown material and cold reservations: no source-set read), ML (titles stay; text is never sent), LS and DH (raw local search and history: no predicate). The same surfaces are S on rows 8.invalid and 8.empty. Each answers another question; the sheet's §4 reads them the same way.

## 8. What I ran

All under the brief's wrapper (`env -i`, empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`), each pytest at `-n 1` in a 3 G scope, one command at a time.

- `tests/test_protection_surface_matrix.py`: 134 passed, 7 xfailed in 46.09 s.
- The proof dependencies, the layout, architecture and identity tests, ruff, lint-imports and the gate partition: results in the landing report.

## 9. Not verified

The five undriven columns (BS, DO, TJ per row, CM, FB) and G6-P4; §6 questions 1, 4, 6, 7 and 10, and the direct-caller half of 5; the figure lineage boundaries (`row_withheld`, `learner_state_withheld`, `shown_figure`, the prefetch's `protected`); MCP's reservation-during-retrieval and raw-id cases; the phone's guide placed-question sources beyond the heading mask; the R4/R5 payload exceptions beyond KY; a held follow-up's two feedback fields (R10). Cells are pinned on this synthetic world only; no owner data was read.
