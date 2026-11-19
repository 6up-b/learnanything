# G6 design: the protection surface matrix and its steps

The build sheet for refactor step G6 ("Protection: one authority per question"). A read-only design pass by a Codex worker (gpt-6-astra) at main `e6314fc0df`, 2026-11-19, filed as written apart from path clean-up. It re-locates K1's inventory (`refactor-k1.md`) at this tip, lists every surface with the set it reads, the nine fixtures, the matrix of today's answers, the fail-closed behaviour, seven defect cells (proposed ledger ids G6-P1 to G6-P7) and the steps G6.1 onward. Cells marked as inferred or with `?` are settled by G6.1's tests before the matrix is a baseline. Nothing was run to produce it.

---

Read-only review at `e6314fc0df008db528d657cbf3f80fe8dedd0982`. No files changed; no tests, databases, vaults, network requests, or model calls were run.

“Verified” below means verified by reading this tip. Matrix outcomes are **inferred**, not executed. `?` identifies an outcome needing the specific test listed in section 6.

Path abbreviations:

- `L/` = `src/learnloop/`
- `R/` = `src/learnloop/source_retrieval/`
- `S/` = `src/learnloop_sidecar/handlers/`
- `EM` = `L/content/sources/exam_material.py`
- `LP` = `L/learner_protection.py`

The owner defaults referred to as “§8” are in `docs/reviews/exam-protection.md:193`, not a section 8 of K1.

## 1. The surfaces

Use these set names:

| Name | Meaning and authority |
|---|---|
| **E** | All exam material: `ExamMaterial.material`, including H. `EM:1023`, construction at `1033–1041`. |
| **H** | Held-out partition: `held_out_material(vault_or_sets, repository)`, `EM:1236`; partition at `1273`. |
| **T** | Existing teaching composition: E plus excluded roles and exercise/assessment links. This is not a third partition of exam material. `R/corpus.py:226`. |
| **U** | LP’s item union: exam-derived items, exam reservations, assessment reservations, cold tasks, remediation cold items, probes, unreadable items. `LP:160`. |
| **H+ER** | AD’s H-derived items plus exam-pool reservations. `L/adaptive_difficulty/protection.py:86`. |
| **—** | Another question: exposure, device capability, workflow ownership, grade visibility, or intentional raw reading. Do not substitute E/H/U. |

“Named” means the function or constant already explicitly identifies its policy. “Implicit” means a caller selects the set through a concrete call or field access; there is no common surface declaration.

Signatures below omit type annotations where they do not distinguish the entry point. `v` and `r` abbreviate the actual `vault` and `repository` parameters.

### Span, model, authoring, and retrieval surfaces

| Matrix code | Production entry and signature | Question; current choice |
|---|---|---|
| TE | `R/corpus.py:226` `teaching_exclusions(v, r, *, readable_roles=frozenset())` | Q2; **T**, named composition. E selected at `245`; additional roles/links at `247`, `253`. |
| MR | `R/corpus.py:446` `model_reader_withheld(v, r, keys)` | Q2; **T**, named model-reader rule; calls teaching exclusions at `462`, adds solutions/assessment restrictions at `467–469`. |
| RA | `S/reader.py:140` `reader_ask(ctx, params: ReaderAskInput)` | Q2; desktop **H**, implicit. `reader_dialogue.ask` selects H at `L/reader/reader_dialogue.py:700`; `tutor_qa.ask_question` repeats final-context admission at `L/tutor/tutor_qa.py:898`. |
| PS | `L/reader/reader_requests.py:559` `model_synthesis(client, *, source_sets)`; returned `synthesize(repository, request, clock)` at `575` | Q2; **H**, implicit at `584`. Protected focus refuses at `586`; protected neighbors are removed at `588`. Production must pass a vault, not a bare list. |
| CK | `L/content/pipeline/jobs.py:2929` `handle_reader_quick_check(ctx)`; inquiry handler `3073`; selection handler `3147` | Q2; **H**, shared `_refuse_held_out_reader_material(ctx, extraction_id, span_ids)` at `2974`, selection at `2982`. Exercise all three callers separately under this column. |
| GU | `L/reader/reader_guidance.py:495` `held_out_sections(vault_or_sets, repository, extraction_id, section_rows)` | Q2; **H**, named; selects H at `509`. `reading_protection(...)` at `524` uses the same partition. |
| FI | `L/figures/protection.py:107` `withheld_message(v, r, extraction_id, span_ids)` | Q2; **E**, documented/named locally, selected through `spans_withheld` at `118`, then `EM:1229`. K10 moved this out of `figures/service.py`. |
| IP | `L/figures/protection.py:434` `item_passages(v, r, *, clock=None)` | Q6/Q8; **subset of U plus stored-plan items**, not E/H alone. Named `LIVE_ADMINISTRATION_REASONS` at `411`; U at `450`, selected reasons at `453–454`, plan items at `456`. **Exam reservations are omitted**; see P1 below. |
| SC | `R/section_coverage.py:273` `read_protection(v, r, *, readable_roles=frozenset())` | Q2; **T**, plus held-back-reading information. Gate `291`, E `296`, teaching composition `297`, source marks `298`. Implicit surface choice. Coverage, deliverable judgments, and Teacher use this production object. |
| SQ | `EM:1466` `source_ref_protected(material, ref, repository)` | Q2 quote safety; **E supplied by caller**. Conservative whole-reference/touched-reading decision at `1477–1486`. Implicit at callers. |
| MC | `L/remote/sources.py:152` `find_passages(v, r, query, *, call_id, intent="explain", learning_object_ids=(), misconception_id=None, verify=False, limit=6, char_budget=DEFAULT_CHAR_BUDGET, clock=None, alias_key=None)` | Q2/Q6/Q8/Q9; **E + T + own passages of protected U items**. `_PROTECTING` at `65`; `_classifier` selects E/T at `226`, `231`; own-item restriction at `240`. Rechecks current U inside final transaction at `198`. Named pieces, implicit overall surface composition. |
| CI | `L/content/authoring/source_exercise_import.py:1100` `import_source_exercise(root, repository, *, extraction_id, span_ids, caller, proposal_id=None, clients=None, time_box_seconds=None, validate=None, need_id=None, learning_object_hint=None, label=None, import_id=None, clock=None, screen=None)` | Q3; **E**, implicit at `1209`, rejection at `1214–1216`. Resume/idempotent return occurs earlier at `1188`; test a new import. |
| BS | Same file `250`: `find_book_solution(v, r, *, extraction_id, label, statement, client=None, owner_id="", deadline=None)` | Q3/model grounding; **E**, implicit at `266`, candidate filter `273`, before matching model. |
| RI | `L/content/pipeline/jobs.py:3218` `handle_reader_exercise_import(ctx)` | Q3; **H**, implicit through `exam.is_held_out` at `3244`, despite constructing the E/H object at `3242`. Selection-normalization gap below. |
| RN, CN | `L/content/authoring/exercise_authoring.py:465` `author_exercises(root, repository, client, *, extraction_id, raw_selection, render_view_id=None, source_id=None, revision_id=None, learning_object_hint=None, clock=None, book_solution=None, admit=None, method_judge=None, method_judge_owner=None)` | Q2 inside Q3. Reader and canonical authoring both call this. **No protection choice for added neighbors**: `_context_blocks(ir, span_ids)` at `308`, added at `600`, sent at `608`. RN/CN distinguish its Reader/canonical callers. |
| LF | `L/content/authoring/practice_leakage.py:144` `build_held_out_inventory(v, r, *, subject_ids=None, shingle_n=DEFAULT_SHINGLE_N)` | Q3 lexical floor; **H text**, named at `154`. |
| RF | Same file `247`: `reserved_questions(v, r, withheld)` | Q3 lexical floor; **U restricted to EXAM/RESERVED reasons, plus H text**. Explicit subset at `262`, H at `270`. Cold/probe exclusion is deliberate in its docstring at `250`. |
| LA | `R/library_ask.py:564` `ask_library(v, r, query, *, find, caller, record_shown=None, entry="reader", extraction_id=None, anchor_span_ids=(), learning_object_ids=(), personalized=None, expand=None, clock=None)` | Q2; anchor **H** at `604`; retrieved candidates **E**, via production `find_sources`, whose final E filter is `R/find_sources.py:757`. Two distinct, implicit choices. |
| OR | `R/library_ask.py:890` `organize(v, r, ask_id, *, client=None, clock=None)` | Q2 replay; **E**, via `refuse_withheld` at `907`, before cached return `910`. Guard at `819–840`. |
| LJ | `S/library_ask.py:364` `deliver_passages(ctx, result)` | Q2/Q9 replay; **E**, keys collected at `369–370`, current check at `374`. Applied to fresh/kept passage and notes jobs. |
| PT | `R/library_ask.py:1441` `ask_tutor(v, r, ask_id, *, pinned_keys, question_md, ask, clock=None)` | Q2; initial **H** at `1467`; supplied pins additionally filtered by **E** in `R/tutor.py:491`, rejection at `516`. Thus E-only pins are dropped, H pins refuse. |
| TJ | `S/library_ask.py:802` `reader_library_ask_tutor(ctx, params: LibraryAskTutorInput)`; final `_job_payload(job)` at `333` | Q2/Q9 replay; **no current set read for completed tutor jobs**. `_start(..., work)` at `877` omits `deliver`; `_job_payload` only rechecks when `job.deliver` exists, `349–353`. |
| TB | `L/teacher/brief.py:180` `resolve_goal(v, r, *, entry, learning_object_ids=(), selection=None)` | Q2; **T**, through coverage protection at `201`, section rejection `208`. Teacher’s item/learner-state inputs separately use **U**, `protection_state(v,r,brief=None)` at `145`, U at `163`. |
| BG | `R/reading_paths.py:298` `path_inputs(v, r, extraction_id)` | Q2; **E**, implicit at `309`. Whole reading refuses at `310`; touched sections omitted at `318–320`. |
| CM | `R/compare.py:235` `compare_sources(v, r, query, *, caller, facet_ids=(), requested_perspectives=(), pinned_span_ids=(), pinned_span_keys=(), anchor_span_keys=(), source_ids=(), by_point=False, policy=None, deadline=None, client=None, verify_client=None, embedder=None, clock=None, withhold=None)` | Q2/Q8; **E plus caller policy**, with optional caller withholding. Uses the retrieval admission family; common display debit now follows all `_compare_sources` exits at `276`. |
| LS | `R/library.py:117` `search_library(v, r, *, query, limit=MAX_RESULTS, deep=False, embedder=None, rewrite_client=None, budget=None)` | Raw desktop library reading; **no exam filter**, library scope at `132`, snippets at `151`. Deliberate exception, not a model-context predicate. |
| DH | `S/reader.py:308` `reader_ask_history(ctx, params: ReaderAskHistoryInput)` | Desktop retained history: no current protection filter. Calls `reader_dialogue.ask_history` at `317`; phone-only filtering begins at `323`. |
| RD | `S/reader.py:647` `reader_render_view(ctx, params: ReaderRenderViewInput)` with desktop origin | Raw desktop reading: text remains readable; H is reported as action metadata at `692`. Invalid protection metadata can still refuse this read. |

Additional figure boundaries must be exercised, not replaced by a test of `withheld_message` alone:

- `L/figures/protection.py:153` `row_withheld(...)`, `184` `learner_state_withheld(...)`, and lineage traversal at `247`.
- `L/figures/listing.py:472` `shown_figure(v, r, figure_id)` invokes the row guard at `499`.
- `L/figures/prefetch.py:317` `item_protection(...)` consumes IP; `protected(...)` at `343` combines item and span protection.
- Use the same fixture target in home keys, input-manifest keys, retrieved keys, and an ancestor’s keys. These are FI subcases, not additional policy sets.

### Serving, item contexts, and follow-up

| Code | Production entry and signature | Question; current choice |
|---|---|---|
| RT | `L/scheduling/serving_exclusions.py:114` `routine_serving_exclusions(v,r)`, then `routine_withhold_reason(v,item,state,exclusions)` at `134` | Q4; **H behind switch + exam reservations + named serving reservations**. H selected at `129`; reason checks at `150–156`. Test the reason function, not just `ServingExclusions.item_ids`: cold reservations have their own check. |
| OT | Same file `314`: `out_of_timing_serving_exclusions(v,r,*,cold_followup_kinds,reveal_window,clock=None,exclude_reveal_ids=None)` | Q4/Q5; routine composition plus **all open cold tasks, wider remediation reservations, recent reveals**. Wider set at `339`; routine composition at `346`. |
| PK | `L/instructional/practice.py:226` `refuse_protected_pick(repository, practice_item_id, *, vault=None)` | Q4; exam reservations at `235`, switched **H** at `237–240`. Implicit. |
| SS | `src/learnloop_sidecar/serving.py:259` `refuse_held_out_item(v,r,practice_item_id)` | Q4; exam reservations at `265`, switch `271`, **H** `273`. Reservation fix landed. |
| DV | `L/scheduling/device_eligibility.py:395` `ineligibility_reason(v,item,device_class,*,media=False,served=None)` | Device capability, **not an exam predicate**. Desktop return at `414`; modes `416`; media lift `427`, measurement exclusion `428`. |
| PF | Same file `368`: `PlanStepFilter.holds(self,item)` | Device/workflow door. Generated-probe callback at `371`, device decision `377`; no independent E/H/U read. `serves_reading` at `363` delegates to the supplied reading predicate. |
| EX, EH | `EM:1545` `exposed_items(v,r,items,*,with_held_out=False)` | Q5; **shown material**, optionally **H**. Whole function switched off at `1560`; shown items `1563`; optional H `1564–1566`. EX=false; EH=true. |
| CO | `L/instructional/policy.py:33` `cold_administration_open(repository, practice_item_id)` | Q5/Q8; exam/wider remediation reservations at `47`, open cold tasks at `49`. No span set. |
| SE | `L/serve_eligibility.py:644` `decide(inputs: EligibilityInputs, request: str)` | Q5; pure eligibility decision. Reveal/priming refusal for PROBE at `671–675`; eligible at `678`. No source-set read. |
| LP | `LP:160` `withheld_items(v,r)` | Q6; **U**, named authority. Metadata `174`; exam pool `181`; H `184`; E-derived items `186–188`; assessment/cold/remediation/probe union `190–208`. |
| AP | `LP:216` `attempt_protection(withheld, attempt)` | Q6; U first, then exam attempt/probe identity at `229–234`. A held grade alone is not item withholding. |
| AD | `L/adaptive_difficulty/protection.py:86` `protection(v,r)` | Q6 for forecasting; **H+ER**, explicit locally at `95–101`, not U. |
| LC | `L/learner_context.py:1597` `learning_context(v,r,*,learning_object_ids=None,topic=None,now=None,limits=None,withheld=None,alias_key=None,provenance=None)` | Q6/Q9; **U**, read at `1621`. `_traces` at `1321` uses protected past-work text at `1377`, constructs question/answer fields at `1396`. This is also MCP learning-context protection. |
| FD | `L/followup_serve/identity.py:242` `door_refusal(repository, item_id, *, workflow_id=None)` | Workflow ownership/single use. Burns `257`, wrong owner `260`, lesson reservation `263`. No E/H/U read; generated door sets feed RT at `L/scheduling/serving_exclusions.py:119`. |
| FB | `L/followup_run/serving.py:60` `held_bundle(bundle)`; `view(v,r,attempt_id,*,phone=False)` at `83`; `next_action(v,r,attempt_id,*,plan_serves,clock=None,surface=SERVING_SURFACE)` at `152` | Follow-up feedback hold, **not an exam set**. `HELD_KEYS` at `33` nulls feedback fields. |
| KY | `S/serializers.py:331` `practice_item_detail(v,r,practice_item_id,*,administer=False)` | Known payload exception. Still serializes expected answer `419`, hints `421`, rubric `429`, source refs `432`. Inspector calls it without a protection door: `S/inspector.py:25`. |

### Phone and MCP boundaries

| Code | Production entry and signature | Question; current choice |
|---|---|---|
| PW | `L/reader/phone_media.py:64` `phone_withheld(vault_or_sets,repository,extraction_id,span_ids=())` | Q9; **E**, named phone rule; read `72`, exception→whole withheld `73`. |
| PG | Same file `126`: `page_refusal(v,r,digest,page)` | Q9; **E over every reading of this file**, loop `138`, page blocks `147`, PW `148`. |
| PI | Same file `166`: `asset_refusal(v,r,digest)` | Q9; **E over all blocks of original-image readings**, at `196–198`. PDFs are not image assets. |
| RV | `S/reader.py:647` `reader_render_view(ctx,params: ReaderRenderViewInput)` with phone origin | Q9; **E**, whole gate `662`, final reread `702`, redaction `705`. |
| GP | Same file `779`: `reader_guide_plan(ctx,params: ReaderGuidePlanInput)` with phone origin | Q9; **E**, whole gate `801`, `_phone_guide_plan` `828`; question provenance `854`, heading/question/cue masking `876–885`. |
| PA | Same file `140`: `reader_ask(ctx,params: ReaderAskInput)` with phone origin | Q2/Q9; **E unioned into the Reader context**, initial refusal `153`, destination material `211`, final answer check `227–232`. `src/learnloop_sidecar/phone_reader.py:112` selects E at `123`. |
| PH | Same file `308`: `reader_ask_history(ctx,params: ReaderAskHistoryInput)` with phone origin | Q9; **E against stored-event provenance**, filter `323–329`; shared `phone_reader.sendable_exchanges(v,r,extraction_id,exchanges)` at `137`, provenance `146`, current E `151`. |
| AS | `S/as_printed.py:111` `practice_as_printed(ctx,params: AsPrintedInput)` | Q9 plus cold-view rules. Origin at `119`; phone **E** at `130`, no-print response at `132`. |
| DO | `S/adaptive_difficulty.py:48` `reader_dose_offer(ctx,params: ReaderDoseOfferInput)` | Phone-visible output still uses **AD’s H+ER**, not E. `_dose_offer` `65`, material view `72`; `_offered_question` `92`, `view.question` `103`, prompt/key payload `110–111`. Phone allowlist includes it: `src/learnloop_mobile/allowlist.py:278`. |
| ML | `L/remote/views.py:330` `library(runtime,*,query=None,limit=30)` | Q9; titles remain visible. **E only annotates cards**: error→unknown exam at `344–347`, title `375`, flag `382`, title-only contract `387`. |

### The `db/stores` walk

These are inputs to the authorities, not new competing protection authorities:

| Store boundary | Meaning to preserve |
|---|---|
| `L/db/stores/goals.py:501` `reserved_exam_pool_item_ids(self)` | Unreleased exam reservations, consumed by serving, U, and AD. |
| `L/db/stores/activity.py:1148` `reserved_assessment_surfaces(self)` | Legacy assessment reservations, consumed by U. |
| `L/db/stores/remediation.py:655` `_remediation_cold_item_ids(self,*,awaiting_primed)` | Shared SQL. `open_remediation_cold_item_ids()` at `675` includes the pre-task reservation. |
| Same file `682` `pending_remediation_cold_item_ids(self)` | Intentionally narrower routine-queue set. Its docstring at `683` explains avoiding indefinite exclusion before a primed attempt. |
| Same file `689` `open_followup_tasks_of_kind(self,kind,*,learning_object_id=None)` | Pending/served tasks, selected at `702`. |
| `L/db/stores/source_service.py:190` `shown_items(connection,items)` | Reveals, impressions, canonical exercise exposure, and imported book-solution exposure. Canonical/solution targets at `232–249`. |
| Same file `720` `book_solution_span_ids(...)` | Existing solution target reader K5-7 should reuse. |
| `L/db/stores/questions.py:422` `reveal_events_for_target(self,*,practice_item_id=None,learning_object_id=None,since=None,until=None)` | Current item-or-LO query at `443–448`; misses other-LO same-family reveals. |
| `L/db/stores/held_out_signals.py:89` | Append-only qualified signal recording. Role qualification at this infrastructure boundary is not a second span-protection implementation. |
| `L/db/stores/judgments.py:14` `append_judgment(...)` | Durable logical judgment ownership; relevant to K6-11, not E/H selection. |

The repository façade now imports these stores at `L/db/repositories.py:62`; do not use K1’s old repository line numbers.

## 2. The fixtures

Build **one synthetic world**, with namespaced sources/items for every case. Parameterized tests may recreate that world for isolation; do not build unrelated mini-vaults that accidentally test different defaults.

Use `tests/source_service_fakes.py:178` `build_textbook_vault(root, embeddings=False)` as the root builder. It calls `build_retrieval_vault` (`tests/source_retrieval_fakes.py:99`), ultimately `create_basic_vault` (`tests/helpers.py:84`). It already supplies valid LOs, facets, source rows, a textbook, and an unmarked exam member.

Use distinct text sentinels, no shared numerals, and sufficiently long unique phrases for lexical-floor assertions. Keep each clean reservation item’s own passages disjoint from every other reservation.

| Fixture | Exact construction and reusable helpers | Required rows/files; limitations |
|---|---|---|
| **1: rule-1 paper** | Existing `src_exam/rev_exam/ext_exam` from `build_textbook_vault`, or `seed_source` at `tests/source_retrieval_fakes.py:65` with a new ID namespace. Add member `default_role: exam`; no scope, selection marks, or signals. | `sources/source_sets.yaml`; artifact, revision, completed extraction, document units/blocks/IR. Assert **E whole, H empty** before surface tests. |
| **2: rule-2 unit and neighbor** | `seed_source(..., units={u_theory: (...), u_exam: (...)}, furniture=False)`. Textbook member with scope entry `{unit_id: u_exam, role_override: exam}`. Persist exact `scope_extraction_id` and `scope_revision_id`. | Both sections in the same reading, on separate pages. Missing scope identity is **not** an equivalent fixture: it can become ambiguous/whole-held. Scope-seal recipe: `tests/test_exam_protection_identity.py:59`. |
| **2: split chapter** | Reuse `_add_split_chapter(repo,root,scope)` from `tests/facet_authority_review_helpers.py:25`; it creates `src_split/rev_split/ext_split`, Theory `s1`, Exam `s2`, and `split_at_heading` selection override. | Helper expects source-set ID `set_la`, whereas the root builder uses `sset_la`. Create a compatible `set_la` first, or reproduce the small helper recipe with namespaced IDs. Do not call a second whole-vault fixture. Its writer supplies the scope identity at `39–44`. |
| **3: resolved held unit** | Seed a two-section textbook. `save_unit_selection(..., exam_use_modes={u_exam: "held_out_evaluation"})`, using the production writer to stamp the reading. | `source_unit_selections` with exact reading identity. Assert H contains protected spans but not the neighboring theory span. Existing recipe: `tests/test_exam_protection.py:121`. |
| **3: unresolved held unit** | Same writer, but retained mark names a unit that this reading cannot resolve. Separate source namespace. | Expected H whole extraction. Do not simulate this by simply deleting the selection row. |
| **4: unmarked second reading** | Reuse `_exam_reading_a`, `_exam_reading_b`, `_persist` from `tests/reread_safety_helpers.py:285`, `292`, `100`. Mark A; persist B under the same protected source/revision without marks on B. | Two extraction/IR/unit/block sets; one revision. B must be held back whole. `_second_reading` at `tests/exam_scope_fixtures.py:176` is another reusable low-level constructor. |
| **4: ambiguous legacy mark** | Use `repository.upsert_unit_selection` with the historical mark shape lacking `exam_paper_metadata.marks_made_on`. Follow `tests/test_exam_protection_identity.py:83`. | Do **not** use `save_unit_selection` for this variant: that stamps the identity and removes the ambiguity being tested. |
| **5: signal on known reading** | Insert inventory through the repository with `assessment_signals`, `held_out=True`, explicit spans, extraction/revision identity, and `made_as_role="exam"`. `_held_out_inventory` at `tests/reread_safety_helpers.py:329` supplies the basic recipe. | Both inventory and current append-only signal-ledger evidence must exist. The old `_cached_inventory` helper at `tests/exam_protection_identity_helpers.py:11` alone does not establish the modern signal ledger. |
| **5: unknown-reading signal** | Insert one synthetic `source_held_out_signal_marks` row with revision identity, `extraction_id=NULL`, held-out spans, inventory ID and `made_as_role="exam"`. | This historical shape is not expressible through the normal fresh writer. Use narrowly scoped fixture SQL; keep append-only triggers enabled. Expected conservative whole-reading protection. Ledger columns are at `L/db/stores/held_out_signals.py:100`. |
| **6: canonical and block-reference items from 1–5** | Clone a valid base item under unique IDs. Canonical form: `_with_exercise` at `tests/exam_protection_review_helpers.py:20`. Block-ref form: `ref`/`set_refs` at `tests/exam_scope_fixtures.py:107`, `112`. | Write item YAML with valid existing LO/rubric/facet references; reload the vault. Canonical and block-reference forms must be separate rows. Use fixtures 1, 2.exam, 3.held, 4.unmarked and 5.signal respectively. |
| **6: whole reference to partial reading** | Item has an extraction-only source reference to fixture 3, with neither canonical span nor located block. | H/E touch the reading but do not cover it whole. Pin item classification **shown** and quote classification **withheld**. `EM:1477`, `1511`, `1592`. |
| **6: exam reservation** | Clean-source item; `repository.insert_exam_pool_items` with unreleased row. Reuse the recipe in `tests/exam_scope_fixtures.py:215` `protect_items`, not its three-item assumptions. | Valid goal plus exam-pool row. It must have **no E/H source**; otherwise the figures omission is masked. |
| **6: open cold task** | Clean item; `create_followup_task(kind="cold_retry", ..., selected_item_id=id, status pending)` using the repository API. | Give it a future `not_before`, so the test isolates reservation from the due-cold as-printed display rule. No remediation episode for this row. |
| **6: remediation before task** | Create remediation episode, update to live `treatment` with `cold_item_id`, leave `primed_attempt_id=NULL`; create **no task**. | Recipe is `tests/test_k1_remediation_cold_reservation.py:23`. The routine queue’s narrower answer is intentional at this tip. |
| **6: diagnostic probe** | Clean, unattempted, short-answer item with `practice_mode="diagnostic_probe"`; no generated-follow-up identity. | Separately add an ordinary-mode item with a completed `probe_presentations` row: LP protects any recorded presentation, not just currently open ones (`LP:201`). Use valid parent rows rather than disabling foreign keys. |
| **6: held grade** | Clean ordinary item; `_held_apply` at `tests/held_grade_evidence_helpers.py:78`. | Real attempt and held-grade rows. Question/answer context remains eligible; score/result is held. |
| **7: Reader-imported paper item** | Execute `handle_reader_exercise_import` against fixture 1 with `tests/exercise_authoring_helpers.py:76` `FakeClient`; valid authored payload from `_item` at `33`. Disable background key-check workers. | Persist the actual item, `learner_item_authored` event and Reader import record. Do not fake this as a canonical import: Reader origin/provenance matters. Key recording begins at `L/content/pipeline/jobs.py:3281`. |
| **8a/8b: bad and empty sets** | Save valid synthetic source-set bytes; write invalid YAML, then separately zero bytes; reload via `load_vault` for each case. Recipe: `tests/test_k1_source_sets_gate.py:38`. Restore afterward. | Keep source/mark/reservation rows intact. Passing `[]` directly to EM is not this fixture: bare lists deliberately lack the metadata gate (`EM:1011`). |
| **9: switch off** | Fixture 6.3 canonical item; `set_config_switch(root,"goals.held_out_selection",False)` from `tests/helpers.py:262`, then reload. | Keep marks and reservations. Also assert an exam-reserved item remains refused. Switch-off does not turn off Q2/Q6. |

Additional fixture overlays needed by the matrix:

- **Media:** `pdf_bytes` and `_png` from `tests/mobile_v4_reader_helpers.py:42`, `135`; use real synthetic original storage and revision asset hashes. PG tests a covered PDF page. PI tests an **original image representing the whole reading**, not a PDF passed to the image endpoint. Temporarily attach the appropriate media representation without introducing another unmarked reading. A protected block on another page can leave PG shown while PI refuses the whole image.
- **Cached results:** seed valid old passage/organizer/tutor results before applying current marks. Keep stored provenance, not just rendered citation projections.
- **RN/CN:** place a distinctive protected block immediately next to an otherwise admissible exercise. The selected exercise is safe; the protected block is the author’s added neighbor.
- **Camel-case selection:** rerun fixture 3’s held selection as `{"nodes":[{"spanId": held_span}]}`.
- **Shown item:** one recent, unlinked `reveal_events` row, non-own-feedback kind; no attempt-linked `answer_display`.
- **Held follow-up:** a real held workflow; inspect both `held_bundle` and sibling `practice_item_detail`.
- **Missing cached key:** syntactically valid `missing_extraction:missing_span` retained in an organizer/job result.

No current helper constructs this entire combined world. The new test file needs small local composition helpers for namespacing, historical mark shapes, cached jobs, and media attachment. Reuse helper modules; do not import fixtures/functions from another `test_*.py`.

## 3. The matrix

**Cell meanings**

- `S`: target is admitted/shown by this protection question.
- `W`: target omitted, masked, or classified withheld.
- `R`: operation refuses/raises before admitting the target.
- `-`: not applicable to that fixture representation.
- `?`: remaining runtime uncertainty.
- All cells are **inferred** from the verified production locations in section 1.

These are protection outcomes, not promises that ranking, scheduling, a dose draw, or authoring validation will select the target.

Controls are explicit:

- Retrieval/compare/library callers are unbound ordinary reading callers. MC additionally applies its global protected-item restriction.
- LA has no protected anchor; it searches for the target candidate. An H anchor would instead refuse at `R/library_ask.py:604`.
- RT includes `routine_withhold_reason`; OT includes its cold/reveal sets.
- DV/PF use a phone-capable short-answer item without media requirements or generated identity.
- SE uses the same otherwise-eligible PROBE input, varying the supplied reveal evidence only.
- AP uses a recorded ordinary attempt shape unless the row itself is a probe.
- RF checks the item’s unique full stem when there is an item; otherwise it checks the target span.
- TJ/OR/LJ/DH/PH test an existing result whose stored provenance names the target **before the current mark**.
- IP is the additional prebuild item guard. `IP=S, FI=W` does not mean a figure can bypass FI.
- AS is enabled. Block-reference-only synthetic items are not Reader imports and therefore have no printed origin.
- RN/CN ask whether the target can enter as the **neighbor of a safe selected exercise**. They are applicable only to partial-reading cases.

The table is grouped horizontally solely for readability; each abbreviation is a separate column.

```text
fixture              | TE MR RA PS CK GU FI IP SC SQ MC | CI BS RI LF RF | RT OT PK SS DV PF EX EH CO SE | LP AP AD LC | PW PG PI RV GP PA PH AS DO | ML LA OR LJ PT TJ TB LS DH FB FD KY BG CM | RD RN CN
0.control            | S  S  S  S  S  S  S  -  S  S  S  | S  S  S  S  S  | -  -  -  -  -  -  -  -  -  -  | -  -  -  -  | S  S  S  S  S  S  S  -  S  | S  S  S  S  S  S  S  S  S  -  -  -  S  S  | S  -  -
1.paper              | W  W  S  S  S  S  W  -  W  W  W  | R  W  S  S  S  | -  -  -  -  -  -  -  -  -  -  | -  -  -  -  | W  R  R  R  R  R  W  -  S? | S  W  R  R  W  S  R  S  S  -  -  -  R  W  | S  -  -
2.exam               | W  W  S  S  S  S  W  -  W  W  W  | R  W  S  S  S  | -  -  -  -  -  -  -  -  -  -  | -  -  -  -  | W  R  R  W  W  R  W  -  S? | S  W  R  R  W  S  R  S  S  -  -  -  W  W  | S  S  S?
2.neighbor           | S  S  S  S  S  S  S  -  S  S  S  | S  S  S  S  S  | -  -  -  -  -  -  -  -  -  -  | -  -  -  -  | S  S  R  S  S  S  S  -  S  | S  S  S  S  S  S  S  S  S  -  -  -  S  S  | S  -  -
2.split-exam         | W  W S  S  S  S  W  -  W  W  W  | R  W  S  S  S  | -  -  -  -  -  -  -  -  -  -  | -  -  -  -  | W  R  R  W  W  R  W  -  S? | S  W  R  R  W  S  R  S  S  -  -  -  W  W  | S  S  S?
2.split-theory       | S  S  S  S  S  S  S  -  S  S  S  | S  S  S  S  S  | -  -  -  -  -  -  -  -  -  -  | -  -  -  -  | S  S  R  S  S  S  S  -  S  | S  S  S  S  S  S  S  S  S  -  -  -  S  S  | S  -  -
3.held               | W  W  R  R  R  W  W  -  W  W  W  | R  W  R  W  W  | -  -  -  -  -  -  -  -  -  -  | -  -  -  -  | W  R  R  W  W  R  W  -  W  | S  W  R  R  R  S  R  S  S  -  -  -  W  W  | S  S  S?
3.unresolved         | W  W  R  R  R  W  W  -  W  W  W  | R  W  R  W  W  | -  -  -  -  -  -  -  -  -  -  | -  -  -  -  | W  R  R  R  R  R  W  -  W  | S  W  R  R  R  S  R  S  S  -  -  -  R  W  | S  -  -
3.neighbor           | S  S  S  S  S  S  S  -  S  S  S  | S  S  S  S  S  | -  -  -  -  -  -  -  -  -  -  | -  -  -  -  | S  S  R  S  S  S  S  -  W  | S  S  S  S  S  S  S  S  S  -  -  -  S  S  | S  -  -
3.camel              | W  W  R  R  R  W  W  -  W  W  W  | R  W  S  W  W  | -  -  -  -  -  -  -  -  -  -  | -  -  -  -  | W  R  R  W  W  R  W  -  W  | S  W  R  R  R  S  R S  S  -  -  -  W  W  | S  S  S?
4.unmarked           | W  W  R  R  R  W  W  -  W  W  W  | R  W  R  W  W  | -  -  -  -  -  -  -  -  -  -  | -  -  -  -  | W  R  R  R  R  R  W  -  W  | S  W  R  R  R  S  R  S  S  -  -  -  R  W  | S  -  -
4.legacy             | W  W  R  R  R  W  W  -  W  W  W  | R  W  R  W  W  | -  -  -  -  -  -  -  -  -  -  | -  -  -  -  | W  R  R  R  R  R  W  -  W  | S  W  R  R  R  S  R  S  S  -  -  -  R  W  | S  -  -
5.signal             | W  W  R  R  R  W  W  -  W  W  W  | R  W  R  W  W  | -  -  -  -  -  -  -  -  -  -  | -  -  -  -  | W  R  R  W  W  R  W  -  W  | S  W  R  R  R  S  R  S  S  -  -  -  W  W  | S  S  S?
5.unknown            | W  W  R  R  R  W  W  -  W  W  W  | R  W  R  W  W  | -  -  -  -  -  -  -  -  -  -  | -  -  -  -  | W  R  R  R  R  R  W  -  W  | S  W  R  R  R  S  R  S  S  -  -  -  R  W  | S  -  -
6.1canonical         | W  W  S  S  S  S  W  S  W  W  W  | R  W  S  S  W  | S  S  S  S  S  S  S  S  S  S  | W  W  S  W  | W  R  R  R  R  R  W  W  -  | S  W  R  R  W  S  R  S  S  -  S  S  R  W  | S  -  -
6.1block             | W  W  S  S  S  S  W  S  W  W  W  | R  W  S  S  W  | S  S  S  S  S  S  S  S  S  S  | W  W  S  W  | W  R  R  R  R  R  W  -  -  | S  W R  R  W  S  R  S  S  -  S  S  R  W  | S  -  -
6.2canonical         | W  W  S  S  S  S  W  S  W  W  W  | R  W  S  S  W  | S  S  S  S  S  S  S  S  S  S  | W  W  S  W  | W  R  R  W  W  R  W  W  -  | S  W  R  R  W  S  R  S  S  -  S  S  W  W  | S  S  S?
6.2block             | W  W  S  S  S  S  W  S  W  W  W  | R  W  S  S  W  | S  S  S  S  S  S  S  S  S  S  | W  W  S  W  | W  R  R  W  W  R  W  -  -  | S  W  R  R  W  S  R  S  S  -  S  S  W  W  | S  S  S?
6.3canonical         | W  W  R  R  R  W  W  S  W  W  W  | R  W  R  W  W  | W  W  R  R  S  S  S  W  S  S  | W  W  W  W  | W  R  R  W  W  R  W  W  -  | S  W  R  R  R  S  R  S  S  -  S  S  W  W  | S  S  S?
6.3block             | W  W  R  R  R  W  W  S  W  W  W  | R  W  R  W  W  | W  W  R  R  S  S  S  W  S  S  | W  W  W  W  | W  R  R  W  W  R  W  -  -  | S  W  R  R  R  S  R  S  S  -  S  S  W  W  | S  S  S?
6.4canonical         | W  W  R  R  R  W  W  S  W  W  W  | R  W  R  W  W  | W  W  R  R  S  S  S  W  S  S  | W  W  W  W  | W  R  R  R  R  R  W  W  -  | S  W  R  R  R  S  R  S  S  -  S  S  R  W  | S  -  -
6.4block             | W  W  R  R  R  W  W  S  W  W  W  | R  W  R  W  W  | W  W  R  R  S  S  S  W  S  S  | W  W  W  W  | W  R  R  R  R  R  W  -  -  | S  W  R  R  R  S  R  S  S  -  S  S  R  W  | S  -  -
6.5canonical         | W  W  R  R  R  W  W  S  W  W  W  | R  W  R  W  W  | W  W  R  R  S  S  S  W  S  S  | W  W  W  W  | W  R  R  W  W  R  W  W  -  | S  W  R  R  R  S  R  S  S  -  S  S  W  W  | S  S  S?
6.5block             | W  W  R  R  R  W  W  S  W  W  W  | R  W  R  W  W  | W  W  R  R  S  S  S  W  S  S  | W  W  W  W  | W  R  R  W  W  R  W  -  -  | S  W  R  R  R  S  R  S  S  -  S  S  W  W  | S  S  S?
6.whole-ref          | -  -  -  -  -  -  -  S  -  W  -  | -  -  -  -  S  | S  S  S  S  S  S  S  S  S  S  | S  S  S  S  | -  -  -  -  -  -  -  -  -  | -  -  -  -  -  -  -  -  -  -  S  S  -  -  | -  -  -
6.exam-reserved      | S  S  S  S  S  S  S  S  S  S  W  | S  S  S  S  W  | W  W  R  R  S  S  S  S  W  S  | W  W  W  W  | S  S  S  S  S  S  S  S  -  | S  S  S  S  S  S  S  S  S  -  S  S  S  S  | S  -  -
6.cold-task          | S  S  S  S  S  S  S  W  S  S  W  | S  S  S  S  S  | S  W  S  S  S  S  S  S  W  S  | W  W  S  W  | S  S  S  S  S  S  S  S  -  | S  S  S  S  S  S  S  S  S  -  S  S  S  S  | S  -  -
6.remediation        | S  S  S  S  S  S  S  W  S  S  W  | S  S  S  S  S  | S  W  S  S  S  S  S  S  W  S  | W  W  S  W  | S  S  S  S  S  S  S  S  -  | S  S  S  S  S  S  S  S  S  -  S  S  S  S  | S  -  -
6.assess-reserved    | S  S  S  S  S  S  S  W  S  S  W  | S  S  S  S  W  | S  S  S  S  S  S  S  S  S  S  | W  W  S  W  | S  S  S  S  S  S  S  S  -  | S  S  S  S  S  S  S  S  S  -  S  S  S  S  | S  -  -
6.probe              | S  S  S  S  S  S  S  W  S  S  W  | S  S  S  S  S  | S  S  S  S  S  S  S  S  S  S  | W  W  S  W  | S  S  S  S  S  S  S  S  -  | S  S  S  S  S  S  S  S  S  -  S  S  S  S  | S  -  -
6.held-grade         | S  S  S  S  S  S  S  S  S  S  S  | S  S  S  S  S  | S  S  S  S  S  S  S  S  S  S  | S  S  S  S  | S  S  S  S  S  S  S  S  -  | S  S  S  S  S  S  S  S  S  -  S  S  S  S  | S  -  -
7.reader-import      | W  W  S  S  S  S  W  S  W  W  W  | R  W  S  S  W  | S  S  S  S  S  S  S  S  S  S  | W  W  S  W  | W  R  R  R  R  R  W  W  -  | S  W  R  R  W  S  R  S  S  -  S  S  R  W  | S  -  -
8.invalid            | R  R  R  R  R  R  R  W  R  R  R  | R  R  R  R  R  | R  R  R  R  S  S  S  R  S  S  | W  W  W  W  | W  R  R  R  R  R  W  W  W  | S  R  R  R  R  S  R  S  S  -  S  R? R  R  | R  -  -
8.empty              | R  R  R  R  R  R  R  W  R  R  R  | R  R  R  R  R  | R  R  R  R  S  S  S  R  S  S  | W  W  W  W  | W  R  R  R  R  R  W  W  W  | S  R  R  R  R  S  R  S S  -  S  R? R  R  | R  -  -
9.switch-off         | W  W  R  R  R  W  W  S  W  W  W  | R  W  R  W  W  | S  S  S  S  S  S  S  S  S  S  | W  W  W  W  | W  R  R  W  W  R  W  W  -  | S  W  R  R  R  S  R  S  S  -  S  S  W  W  | S  S  S?
+.shown              | S  S  S  S  S  S  S  S  S  S  S  | S  S  S  S  S  | S  W  S  S  S  S  W  W  S  R  | S  S  S  S  | S  S  S  S  S  S  S  S  -  | S  S  S  S  S S  S  S  S  -  S  S  S  S  | S  -  -
+.held-feedback      | -  -  -  -  -  -  -  -  -  -  -  | -  -  -  -  -  | -  -  -  -  -  -  -  -  -  -  | -  -  -  -  | -  -  -  -  -  -  -  -  -  | -  -  -  -  -  -  -  -  -  W  -  S  -  -  | -  -  -
```

For `6.held-grade`, additionally pin `attempt_result(..., held=True) == "held_for_review"`; `LC=S` means the question/answer text, **not** release of its score (`LP:242`).

Two replay fault cases supplement the table:

| Case | Today, inferred | Required fail-first assertion |
|---|---|---|
| Safe current anchor; legacy same-span history contains an answer grounded in a newly H span; inquiry branches disabled | RA admits the historical answer into the next model context. | Historical answer replaced/omitted before model invocation; learner question retained. |
| Stored organizer/job contains valid-shaped but nonexistent `extraction:span` | OR/LJ current-key check admits that key. | Whole derived result refused; stored result unchanged. |

### 3a. Disagreements and whether they are deliberate

This accounts for the differing cells; differences between questions are not automatically defects.

| Cells | Assessment |
|---|---|
| E-only rows: RA/PS/CK/GU/RI show; TE/MR/FI/SC/MC/CI/BS/phone withhold/refuse | **Deliberate** Reader H versus teaching/figures/phone E. Strategy `docs/specs/refactor_strategy_v3.md:466`; owner defaults `docs/reviews/exam-protection.md:193`. Figures’ formerly missing explanation is now at `L/figures/protection.py:107`. |
| E-only pins: PT drops passages while ordinary RA accepts selection | Existing D2 difference, preserved. PT’s provider uses E at `R/tutor.py:516`; RA uses H at `L/tutor/tutor_qa.py:898`. Do not normalize it silently. |
| E-only items and fixture 7: RT/PK/SS show; LP/AP/LC withhold; RF reserves the stem | **Unresolved owner-policy inconsistency K1-2**, not permission to choose a new rule. `docs/reviews/refactor-bug-ledger.md:117`; `EM:1591`; `jobs.py:3244`; serving H at `serving_exclusions.py:129`. |
| E-only, cold-task, remediation, assessment-reserved, probe items: LP withholds but AD admits | **Deliberate narrower forecasting view**, D5; AD explicitly H+exam reservations at `adaptive_difficulty/protection.py:95`. |
| Pre-task remediation: RT shows while OT/CO/U withhold | **Deliberate at this tip**, despite K1’s older drift description. Store docstrings distinguish the two lifetimes at `db/stores/remediation.py:675`, `682`. |
| Cold/probe RF shows while U withholds | **Deliberate lexical-floor subset**: `practice_leakage.py:250`, `262`. |
| Whole-extraction reference on partial reading: SQ withholds, item gates admit | **Deliberate D9**, quote uncertainty versus item attribution. `EM:1477`, `1511`, `1592`. |
| Fixture 9: serving H gates admit while Q2/Q6/phone still protect | **Deliberate D7**, `EM:1560`, strategy `:466`. |
| LS/RD/DH show protected local content while model/phone gates protect | **Deliberate local-reading/history distinction**, except fresh model reuse must re-admit history. LS `R/library.py:132`; DH `S/reader.py:317`; RD `692`. |
| ML lists a protected source title | **Deliberate title-only MCP contract**, `L/remote/views.py:375`, `387`; not a passage leak. |
| Safe page PG shows while original image PI refuses | **Deliberate representation scope**: page-specific versus entire original-image reading, `phone_media.py:147`, `196`. |
| Safe neighbor’s DO withheld in a partly H reading | **Deliberate AD whole-reading restriction**, `adaptive_difficulty/material_view.py:1444`, `dose.py:257`. |
| DV/PF/SE/FD admit things another gate protects | They answer device, eligibility, or workflow questions. Their answers must be composed with protection, not redefined as E/H. |
| Held feedback FB masks key while KY still supplies sibling key; ordinary KY supplies keys before answers | **Known R4/R10 payload exceptions**, not a G6 payload split. `followup_run/serving.py:33`, `S/serializers.py:419`. |

### 3b. Defect cells and smallest fixes

The IDs below are **proposed ledger IDs**, not rows already written.

| Proposed ID | Scenario, verified code, inferred defect | Smallest fix |
|---|---|---|
| **G6-P1** | `6.exam-reserved/IP=S`. Clean-source exam-reserved item’s own exercise/solution can enter a figure prebuild. `figures/protection.py:411`: `("WITHHELD_COLD", "WITHHELD_RESERVED", "WITHHELD_PROBE")`; `454` selects only those reasons. The separate E span filter cannot catch this clean source. | Include current exam-pool reservation IDs in IP’s live-item set. Prefer the actual reservation IDs over expanding every `WITHHELD_EXAM` item indiscriminately. Keep stored-plan and fail-closed behavior. |
| **G6-P2** | TJ shows a completed pinned answer after its sources become E/H or metadata becomes unreadable. `S/library_ask.py:877`: `_start(ctx, "tutor", params.ask_id, work)`; no delivery callback. | Add a tutor-result delivery guard using stored event provenance, grounded keys and citations. Refuse the entire derived answer. Do not simply attach `deliver_passages`: its `hits`/`notes` shape does not cover tutor results. |
| **G6-P3** | Legacy Reader thread sends newly protected historical model text again. `reader_dialogue.py:698` leaves `thread=None` when branches are off; manifest fallback reads raw question events at `288`; `tutor_qa.py:929` chooses `_thread`; `_thread` emits `delivered_answer_md(event)` at `2010` without current source admission. | Apply the same provenance-based answer filtering to legacy/direct Reader threads as branch ancestors. Use destination H/E composition; preserve learner-authored questions and stored events. |
| **G6-P4** | E-only phone DO can return prompt/key despite phone Reader redaction. `S/adaptive_difficulty.py:103`: `view.question(...)`; returned key at `111`; no phone-origin E check. | Add destination admission for the chosen question’s reading/anchors/citations inside the existing operation before returning the offer. Preserve AD’s internal H+ER policy. Test no unseen-offer budget consumption. |
| **G6-P5** | Cached result names a nonexistent but well-formed key. `R/library_ask.py:833`: `len(pair) != 2 or pair in held`. E membership does not prove the passage exists (`EM:230`). This contradicts the guard’s fail-closed docstring. | Resolve every cached dependency key as well as checking protection. Missing/unreadable dependency refuses the whole derived result. |
| **G6-P6** | `3.camel/RI=S`: a partial-H selection supplied as `spanId` bypasses the job’s held check. `jobs.py:3244` reads only `node.get("span_id")`; author accepts both at `exercise_authoring.py:525`; scope-only check already accepts both at `jobs.py:3250`. | Normalize once, then check the translated/reanchored selected spans with H before authoring. Reuse that selection for scope and provenance; do not maintain parallel raw-key parsers. |
| **G6-P7** | RN admits an H neighbor; CN can admit an E/H neighbor beside a safe canonical exercise. `_context_blocks` loops `(idx-1, idx, idx+1)` at `exercise_authoring.py:318`; `context_blocks=_context_blocks(...)` at `600`; model call at `608`. No neighbor admission occurs there. | Pass the caller’s named material policy to the shared author context builder: H for Reader, E for canonical. Refuse protected selected segments; omit protected neighbors, figures or auxiliary source text. Final admission must run on the assembled context, before any author/model-judge call. |

P4’s actual deterministic offer and CN’s complete canonical-wrapper reach need the tests below; the missing guards themselves are verified.

### 3c. K1 section 6 items 1–4

| K1 prerequisite | Status at this tip |
|---|---|
| **1. Shared metadata gate and atomic source-set writes** | **Done.** `_require_readable` at `EM:1011`; E/H/role readers enter it (`1026`, `1287`, `1055`). Production synthesis passes vault at `L/content/synthesis/source_set_synthesis.py:280`; authority retains the vault through `exam_source_sets` at `content/facet_identity/authority.py:377`. Atomic writer fix recorded in `docs/reviews/refactor-k1-fixes.md`. Bare-list API still intentionally has no filesystem gate. |
| **2. Owner decision on Reader-made exam practice** | **Not done.** K1-2 remains open. Preserve fixture 7’s inconsistent current answers. |
| **3. Missing reservation doors** | **Session, MCP and remediation fixes done.** SS reservation `265`; MCP protecting probes `remote/sources.py:65` and teaching restriction `231`; wider remediation reader `db/stores/remediation.py:675`; LP imports the cold-kind authority at `LP:103`. **Inspector requirement only partially addressed:** open-item hints are hidden in UI at `InspectorOverlay.tsx:485`; server detail still carries key/hints/rubric, and other displays are K5-5. |
| **4. Figures/library documentation** | **Done**, per K1 fixes; figures’ E choice is explicit at `figures/protection.py:107`. Local raw search remains intentionally readable. |

## 4. Fail closed

Patch the **production dependency at the consuming module**, not the surface adapter itself. An exception escaping the operation is `R`, not “open.” Also test structured unavailability, such as `Withheld(available=False)`.

| Surfaces | Predicate raises today | Invalid/empty source sets today |
|---|---|---|
| TE, MR, RA, PS, CK, GU, FI, SQ, CI, BS, RI, LF | Refuse/propagate; no target admitted | Refuse through shared gate |
| SC, TB, BG | Typed refusal/unavailable | Refuse |
| MC | Refuse/unavailable; final transactional check remains required | Refuse |
| LP, AP, LC | Underlying union-read failure → unavailable/withheld. A failure of the preliminary `protection_issues` call itself can propagate instead (`LP:174`). | Withheld/unavailable |
| AD, DO | Unavailable protection → withheld/no offer; unexpected uncaught errors refuse | Withheld/no offer |
| IP | Unavailable U or caught plan/own-passage error → `None`, meaning withhold all prebuilds (`450–468`). An exception escaping U itself propagates. | Withheld |
| RF | H-read error propagates. **Do not treat the raw helper as owning U availability:** callers check it. Teacher `guards.py:150`, topics `:41`, follow-up authoring `:59`, probe generation `:921`. | H gate refuses; production callers also refuse unavailable U |
| RT, OT, PK, SS, EH | Refuse when the invoked H/reservation reader fails | Refuse with switch on and an applicable item |
| EX | Shown-material read error refuses; no H read by default | Open to this metadata fault: it reads exposure, not source sets |
| CO | Reservation/task read error propagates | Unchanged/open to this metadata fault |
| DV, PF, SE, FD | Their own errors propagate; no E/H predicate exists here | Unchanged/open to this metadata fault |
| PW | Whole reading withheld | Whole reading withheld |
| PG, PI | PW failure closes; other unhandled read failures refuse | Refused for applicable known reading/media |
| RV, GP, PA | Refuse | Refuse |
| PH | Exchange omitted, or request refuses if surrounding read fails | Exchanges withheld |
| AS | No-print/refusal on applicable protected origin; cold-state read failure treats item as cold | No-print for an applicable known origin |
| LA, CM | Refuse when production admission fails | Refuse |
| OR, LJ | Current check catches predicate failure and treats all dependencies as withheld (`library_ask.py:831`) | Refuse |
| PT | Refuse on initial H read or pin provider failure | Refuse |
| **TJ** | **No delivery predicate invoked** | **Open: cached answer returned** |
| ML | Titles remain, `exam_material=True`/unknown protection | Titles remain; text still absent |
| LS, DH | No current exam predicate invoked | Raw local search/history remains available |
| RD | H annotation read can raise and refuse the read | Refused |
| FB | Independent held-field masking; no exam read | Still masks held fields |
| KY | Detail path can be blocked by its scheduling explanation | Likely refusal: known K1-10, pin exact result with one test |

**Actual fail-open gaps:** TJ; legacy Reader model-thread reuse; nonexistent cached dependency keys; Reader selection spelling/reanchoring; unfiltered authoring neighbors; clean-source exam reservations in IP; phone DO’s missing destination E gate.

EX/CO/device/eligibility/workflow functions and intentionally raw local readers are **not** missing implementations of E/H. Making fixture 8 uniformly `W` across those functions would change their questions. The composed content-delivery boundary must close; the matrix must retain the distinction.

For empty inputs, include separate pins: `exam_withheld` returns early on no keys (`EM:1103`), and `held_out_items` returns early on no items (`1520`). No-content results are not leaks.

## 5. The steps

### G6.1 — Add the single matrix test file

Create `tests/test_protection_surface_matrix.py`.

Structure:

1. `World` record containing root, paths, repository, reloaded vault, named readings/spans/items, fake clock and stored-result IDs.
2. One composition builder for all nine fixtures.
3. A literal expected-answer table copied from section 3.
4. Surface adapters that call production functions and normalize results to S/W/R.
5. Per-surface fault-injection cases.
6. Reach tests for request context, kept-result delivery, media, and key payload exceptions.

Do not compute expected answers by calling E/H/U; that would reproduce the implementation rather than pin it. First assert each fixture’s base E/H identity independently.

For defects, keep the current-answer matrix assertion and add a **separate desired-answer strict xfail** with its ledger ID. Do not xfail an entire row: that would hide regressions in every other surface.

Add G6-P1–P7 ledger rows with assigned fix steps and a landing/arc-close deadline, as required by `docs/specs/refactor_strategy_v3.md:84`. Resolve `?` cells by the bounded tests in section 6 before treating the matrix as a baseline.

Required reach cases in this file, using existing helpers:

- Phone page addressed through another reading of the same digest; stored-event provenance with inquiry disabled; fresh answer, history and completed-job recheck; protected guide heading and placed-question sources.
- Reader context selection, neighbor, referenced block, retrieved hit, excerpt, branch ancestor, and legacy ancestor.
- MCP restriction before verification and again after a reservation is created during retrieval; unknown/raw IDs must not disclose protected titles through error text.
- Source-reference forms: canonical, locator, explicit spans, whole extraction, revision/source-only.
- Figure home, input manifest, retrieval and ancestor lineage.
- R4/R5 key-bearing payload/model-context exceptions; R10 both feedback fields.
- Device media lift must not admit a measurement-only mode; restored phone checks keep no-help behavior.

Existing review tests remain proof dependencies, especially `tests/test_mobile_v4_codex_review.py`; do not replace browser/cache regression coverage with a Python assertion about a constant.

**Behavior:** none.

### G6.2 — Name each surface’s set in one place

Use the smallest shape: **one surface-to-span-set table in `exam_material.py`**, next to E/H construction. Keep U in LP and other questions in their existing modules.

For example:

```python
# Existing concepts only.
SURFACE_SET = {
    "teaching": "all_exam",
    "model_reader": "all_exam",
    "reader_ask": "held_out",
    "reader_presets": "held_out",
    "reader_checks": "held_out",
    "reader_guidance": "held_out",
    "reader_import": "held_out",
    "canonical_import": "all_exam",
    "book_solution": "all_exam",
    "figures": "all_exam",
    "phone": "all_exam",
    "library_result": "all_exam",
    "book_guide": "all_exam",
    "ad_forecast": "held_out",
}
```

A small `material_for_surface(vault, repository, surface)` selects the **existing** reader:

- H entry → `held_out_material`.
- E entry → `exam_material(...).material`.

For callers needing `ExamMaterial` verdict metadata, provide an E-only checked entry or retain the full object and assert the named choice; do not discard verdict information or perform a second database read.

Call-site pattern:

```python
material = EM.material_for_surface(vault, repository, "reader_checks")
```

Preserve existing compositions:

- Teaching adds its roles and links in `corpus`; it does not become E-only.
- Phone uses its one E entry across selection, context and delivery.
- AD obtains named H, then adds exam reservations in its existing authority.
- IP keeps its explicitly named live-administration composition.
- U remains `learner_protection.withheld_items`.
- Serving keeps switch ownership and reservation lifetimes.
- Held grades, device rules and `serve_eligibility` do not enter this table.

Migrate in small caller batches: Reader; authoring; teaching/retrieval; figures; phone/MCP; AD. No cache keys, serialized enum values, prompt bytes, extra reads, or identity versions should change.

**Behavior:** none. **Proof:** G6.1 unchanged, identity pins unchanged, required structure proofs.

### G6.3 — Extract final passage admission

Put the common implementation in **`R/admission.py`**, using EM’s named surface choice and the existing caller-policy/item-exclusion functions. It should:

- Resolve actual dependencies.
- Apply the chosen E/H partition.
- Apply existing role/own-item restrictions where the caller already requires them.
- Fail closed on missing/unreadable dependencies.
- Return admitted passages and reasons; callers decide whether an entire derived answer must refuse.

First extract the **existing behavior** without “improving” exits. Replace duplicated admission mechanics in:

- Reader linked-context admission, `tutor_qa._admitted_linked` at `2438`.
- Provider and pinned-provider final passage checks.
- Library current-key checking, `R/library_ask.py:819`.
- Completed-result delivery, `S/library_ask.py:364`.
- Compare candidate/pinned/fallback admission.
- The span portion of phone delivery checks; stored-event provenance reconstruction remains with Reader/phone ownership.

Do not unify H and E or apply MCP’s U-own-passage rule to every Reader request.

**Behavior:** none for the extraction. Each missing check lands afterward as a distinct fix.

### G6.4 onward — Small behavior fixes

| Step | Fix | Proof |
|---|---|---|
| **G6.4** | G6-P1, add exam reservation IDs to figure prebuild item passages | Clean-source reserved item’s exercise and solution absent; release restores admission; database failure closes. |
| **G6.5** | G6-P2, completed pinned-tutor delivery guard | Complete job, mark dependency, poll twice: both refuse; stored result/event unchanged; unmarked result still returns. |
| **G6.6** | G6-P3, legacy/direct Reader history admission | Inquiry on/off and direct caller; safe anchor, protected historical source; fake client sees placeholder/no historical answer. |
| **G6.7** | G6-P5, nonexistent dependency resolution | Missing extraction and missing span separately; organizer cached return and kept job both refuse. |
| **G6.8** | G6-P6, one normalized/translated Reader import selection | `span_id`, `spanId`, and reanchored selection have identical H refusal; zero author calls. |
| **G6.9** | G6-P7, authoring final-context protection | Safe selected exercise beside protected neighbor; Reader uses H, canonical uses E; neighbor omitted before author and method-judge calls; safe neighbor retained. |
| **G6.10** | G6-P4, phone dose destination gate | Deterministic E-only extra question cannot leave phone handler; desktop/AD forecasting retains its narrower policy; no unseen-offer budget charge. |

These change delivered/admitted behavior and need their own ledger fixes. They should not rewrite historical rows. If a fix also changes dose settlement or historical interpretation, split that additional change and make its version decision separately.

K1-2 is not one of these fixes. Keep its current cells until the owner’s recorded policy changes.

### Display accounting: one extraction, then the semantic fixes

Put the shared function in **`R/display_accounting.py`**. It should accept the actual displayed text/passages, bound item/caller, and existing event identity, and call the existing reveal/source-exposure writers.

The structural extraction must preserve current timing and amounts. Replace duplicated accounting from:

- Tutor answer/bridge/excerpt accounting, `L/tutor/tutor_qa.py:1291`.
- Compare’s common accounting, `R/compare.py:276`.
- Primary/fallback retrieval display paths.
- Library passage accounting, `R/library_ask.py:668`.
- Teacher displayed-text accounting, `L/teacher/service.py:1638`, overlap at `1668`.

Admission and accounting are separate:

- **Admission** decides what may enter a model or leave a delivery boundary.
- **Accounting** records what was displayed and its consequences.

A structural extraction must not claim exactly-once presentation. Stable display IDs and acknowledgement timing belong to **K6-1/DJ1**, not a callback casually moved to a different return statement.

### K5/K6 carried work: scope, persisted meaning, size

Sizes: S = one focused change; M = several related modules/tests.

| Ledger row | Relation to G6 authority shape | Persisted meaning / version decision | Size and concrete proof |
|---|---|---|---|
| **K6-10** | Independent cache-freshness fix; uses the same admitted bounded inputs | **No algorithm successor for cache invalidation alone**, but explicitly version the changed cache identity and update identity pins. Do not reinterpret old evidence silently. | **M.** Coverage key at `R/section_coverage.py:663` omits rendered inputs used at `769`; freshness return `1244`. Deliverable key at `R/deliverable_path.py:202` precedes bounded-prompt choice. Vary budget, related LO and role independently; assert paid-input/ref-map changes miss. |
| **K6-11** | Independent logical-identity fix | **Treat the proposed durable judgment-ownership change as a persisted-meaning change**: successor/version decision, old ledger immutable. Separating exact paid-response reuse alone is only a cache change. | **M.** `L/practice_index/listwise.py:128` derives row IDs from request hash/ID parts; reuse returns at `225`; logical owner written later at `274`. Two equal-looking LOs get two correctly owned logical rows, optionally one paid response. |
| **K6-12** | Independent cross-process work admission | **No algorithm tag** for coalescing equivalent paid work without changing decisions; schema/table-role work may be required. Pin retry semantics explicitly. | **S–M.** Replace local daily mark/claim at `S/deliverables.py:363–374` with database claim pattern from `R/reading_paths.py:772`. Two connections/barrier: one paid call; restart and transient-failure cases. |
| **K6-13** | Independent count-budget admission | **No algorithm tag** if enforcing the existing counter semantics. Changing what failures/cancellations count would be a separate policy change. | **M.** Tutor counts at `tutor_qa.py:908–922` precede event/call; cue limits have the same race. Reserve transactionally before call; settle each counter under its own scope. |
| **K5-5** | Independent display-measurement fix; benefits from the accounting extraction | **Yes: priming/admissibility successor.** Newly recorded displays change new cold dispositions. | **M.** Terminal, inspector and hints must produce appropriate reveal rows. Ledger `docs/reviews/refactor-bug-ledger.md:239`; server detail still exposes fields at `S/serializers.py:419`. |
| **K5-6** | Independent measurement fix; not an E/H set change | **Yes**, same priming successor as K5-5 if landed together. | **S + M.** Use the short-answer-aware overlap rule for bound tutor/Teacher text (`tutor_qa.py:1683`, `1729`); account allowed Reader solution/source displays at `S/reader.py:647`. Test exact short key versus incidental number, and allowed reading before cold check. |
| **K5-7** | Independent cold-evidence target repair | **Yes**, cold-disposition successor; coordinate with K5-5/6. | **S.** Extend targets from `attempts/coldness_receipt.py:803` to canonical exercise and `book_solution_span_ids`; extend reveal query `db/stores/questions.py:443` to other-LO same-family items. Pin evidence event IDs and hard/soft dispositions. |
| **K6-1** | Independent DJ1 delivery semantics; accounting extraction is preparation | **Yes**, because generated-versus-delivered changes hints, reveals, exposure and warmth. | **M or larger.** Stable display ID; zero display-dependent effects before acknowledgement; repeated acknowledgement counts once. Ledger `:276`. |

The K5 successor must follow `docs/algorithm-change-playbook.md:7`, `:13`, `:145`: tag, upgrade/test rows, replay/upgrade proof, immutable raw history. The Nov 16 rule at `:156` removes the automatic requirement for a new kill switch; do not add one without an owner request.

**Proof discipline for every landing**

Follow strategy §2.1 (`docs/specs/refactor_strategy_v3.md:49`): targeted tests, required cap/import/lint/validator checks, and `tests/test_identity_pins.py`. Structural G6 steps require unchanged served/persisted values and identical P-shadow/P-draw. Behavior fixes land separately with fail-first tests and version decisions. Full-suite/durability and arc-close proofs remain required.

Those are implementer obligations; no shadow copy or `fixtures-local` access was performed for this design task.

## 6. What could not be settled by reading

Each question below has one bounded synthetic test. None requires owner data.

| Question | One test that settles it |
|---|---|
| Can the phone dose draw actually select an E-only extra question through all current eligibility conditions? | Seed an eligible answered question and deterministic existing dose draw; invoke the phone handler. Assert the current payload contains its prompt/key, then convert to G6-P4’s strict-xfail refusal. Evidence: `S/adaptive_difficulty.py:65`, `103`; `adaptive_difficulty/dose.py:257`. |
| Does the complete canonical import wrapper retain the protected adjacent block through statement expansion? | Safe canonical exercise plus adjacent E/H sentinel, fake author captures `context_blocks`. Assert whether sentinel reaches it. This resolves CN’s `S?`; shared builder’s missing filter is verified at `exercise_authoring.py:600`. |
| Does bad source-set metadata always block `practice_item_detail`, or only particular explanation paths? | Load fixture 8, invoke detail on an otherwise valid ordinary item, assert exact exception/response and no administration side effect. This resolves KY’s `R?` and pins existing K1-10. |
| Does a translated stale Reader selection reach a different protected block despite a safe raw ID? | Create render-view/reanchor mapping, submit old selection, capture translated segments before authoring. Check protection against the translated IDs, not raw nodes. `exercise_authoring.py:500`; `jobs.py:3244`. |
| Does the legacy-history leak survive both direct tutor use and inquiry-disabled RPC use? | Parameterize those two entry points with the same safe anchor and newly protected historical answer; inspect the fake client’s complete context. `reader_dialogue.py:288`, `698`; `tutor_qa.py:929`, `1995`. |
| Is the phone’s final provenance check sufficient to stop a legacy-thread answer after it has already reached the model? | Have the fake model echo only the historical sentinel, with no new citation; inspect both model input and final phone response. A blocked response does not erase the model-input leak. |
| Are missing figure ancestors conservatively handled at final delivery? | Stored figure names an absent ancestor containing its only protected provenance; call `shown_figure`. Lineage skips missing rows at `figures/protection.py:264`; determine whether another guard refuses. Queue a new ledger row only if the final boundary opens. |
| Are no-key derived cached answers safe to return? | A stored nonempty tutor/organizer answer with empty or damaged provenance must refuse if protection cannot be established. Test actual result schemas, especially TJ, rather than assuming `hits`/`notes` exist. `S/library_ask.py:349`, `369`; `R/library_ask.py:1492`. |
| Does actual fixture-7 import create any shown-material evidence beyond its import/event rows? | Run the fake-client Reader import, reload, call EX/EH and inspect only its synthetic exposure/impression/reveal rows. This confirms fixture 7’s current S cells without confusing authoring with presentation. |
| What exact retry settlement should K6-12/13 enforce after failure/cancellation? | Two connections plus barrier, one admitted slot/claim, then forced failure. Pin existing documented scope separately for daily automatic refresh, rolling cue calls and answered-question limits; do not infer one shared counter policy. |

The implementer should resolve these tests before changing the corresponding expected cell. The remaining set differences are explicit policy distinctions to preserve, not reasons to collapse protection into one universal predicate.
