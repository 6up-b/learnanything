# Refactor K1: protection inventory

Step K1 of `docs/specs/refactor_strategy_v3.md` (§2.17, arc K): a read-only review of every predicate that withholds, protects or excludes, before G6 ("Protection: one predicate"). Branch `refactor/k1-protection-inventory`, based on main `ad194ddc3a` (arc C closed). No code under `src/`, `apps/` or `tests/` changed.

**Result.** LearnLoop has no single protection question, so it can't have one predicate. It has nine questions, and each already has one authority or a small family of them. Most of the drift is between surfaces that answer one question with different *sets*: all exam material, the held-out partition only, or the teaching-wider set. The rest is a fail-open gap: the protection-issues check (`learner_protection.protection_issues`) is asked by 4 of the roughly 80 modules that read exam material. No held-out text reaches a non-grader model prompt, and no answer key reaches a chat host. The keys that reach a screen do so only behind a deliberate action (the classic-mode inspector, by a recorded UX decision) or DevTools (serve payloads carry key, hints and rubric, hidden by the screens). So nothing needs an immediate fix. Four groups should land before G6 (§6): one fail-closed metadata gate (D1); the owner's call on practice the Reader makes from exam material (D4); three doors that miss a reservation (the session serve and exam reservations, R1; MCP's `find_sources` and probes, R2; the inspector's hints, R9); and two docstrings. G6 as written would route ingest, synthesis and authoring through the wrong question (§5).

## Method

- Read `content/sources/exam_material.py` whole, `learner_protection.py`, `serve_eligibility.py` (header and `decide`), `held_grades.py`, `scheduling/serving_exclusions.py`, `source_retrieval/corpus.py`'s exclusion functions, `source_retrieval/policy.py`, `instructional/policy.py`, `adaptive_difficulty/protection.py`, `figures/prefetch.py`'s filters and `figures/service.item_passages`, `section_coverage.read_protection`, and every ingest, synthesis and authoring call site of the exam predicate. Line numbers are at `ad194ddc3a`.
- `docs/reviews/exam-protection.md` §2 (the exam-protection stage's caller table, Oct 13) was the starting inventory. I re-found each caller at this tip and added what came after it: the phone (V1-V4), MCP's `remote/`, figures (RW5), AD's protection, teacher, section coverage and curriculum.
- Three read-only sub-reviews ran in parallel, each with file:line evidence: (a) the sidecar's serializers and the desktop frontend's checks; (b) the phone host's and MCP's payload builders; (c) the lexical leakage floor and retrieval's filters. I spot-checked each claim I use here against the code.
- One run of code, under the empty-environment wrapper on a synthetic vault made by `learnloop init` under `~/.cache/learnloop-k1-tmp` (deleted afterwards). It checked that a `source_sets.yaml` that fails validation, or is empty, loads as *no* source sets, and that `protection_issues` flags both (§2, D1). No vault, copy or model call was used.

## 1. The questions and their predicates

There are nine questions. Every withholding site asks one of them. The **set** column matters most: *all exam* is `ExamMaterial.covers` (rules 1-4: exam-role members whole, outline exam picks, rule-2 exam units, plus the held-out partition); *held-out* is `held_out_partition` (rules 3-4 and signals only); *teaching-wider* is all exam plus problem sets, notes, unknown roles and the spans that exercise and assessment links cite (`corpus.teaching_exclusions`).

Two facts the table depends on:
- **An exam-role member alone is exam material but not held out** (`exam_material.py:737-741`: `_Marks.protected` needs a scope, a selection mark or a signal; `:953-955` adds the member whole as `EXAM_MEMBER` only). So a past paper with no marks or signals, or a rule-2 exam chapter on its own marked reading, sits in "all exam" and outside "held-out". Every set disagreement below is about this class.
- **Rules 1 and 2 come only from `vault.source_sets`** (`exam_material.py:952-955`, `:806-812`). Rules 3-4 and the signals come from the database.

| # | Question | Predicate (file:line) | Set or inputs | Fails | Callers by surface |
|---|---|---|---|---|---|
| Q1 | Is this span or extraction exam material, is it held out, and on which reading? | `content/sources/exam_material.py`: `exam_material` :945, `held_out_partition` :1193 (`held_out_material` :1156), `exam_withheld` :1019, `spans_withheld` :1138, `reading_held_back` :1061, `source_marks` :1047, `held_out_spans` :1213 | source sets (rules 1-2); `source_unit_selections`, outline picks and the signal ledger (rules 3-4) | raises (callers decide). **No metadata gate:** unreadable sets mean no rule 1-2 (D1) | about 80 modules on every surface; it's the base of Q2-Q6 |
| Q2 | May this span ground a model's teaching, explanation or authoring? | teaching: `source_retrieval/corpus.py` `teaching_exclusions` :226, `teaching_scope` :609, `model_reader_withheld` :446 (adds `solution` blocks), `exam_exclusions` :258; `content/authoring/practice_leakage.py:407` `build_cross_source_spans`; `source_retrieval/section_coverage.py:273` `read_protection`; `exam_material.py:1385` `source_ref_protected` (a quote) | teaching-wider; section coverage adds the held-back readings and **the metadata gate** (:289-293) | raises; section coverage refuses explicitly | tutor and find_sources, passage cues, compare, workbench passage draw (desktop sidecar); teacher brief and actions, deliverable path, coverage (sidecar, background); generation and PF (CLI, background); MCP passages (`remote/sources.py:221`, all exam) |
| | | the Reader's model contexts: `tutor/tutor_qa.py:902` (Ask), `reader/reader_dialogue.py` (dialogue), `reader/reader_requests.py` (presets), `content/pipeline/jobs.py:2988` (quick and inquiry checks), `reader/reader_guidance.py:495` (which actions are offered), `source_retrieval/reader_tutor.py:250` (second guard on hits) | **held-out only** (the owner's §8 Q1 default, `exam-protection.md:195`) | raises | desktop Reader (sidecar `handlers/reader.py`, `handlers/library_ask.py`); background drain |
| | | figures: `figures/service.py:554` `withheld_message` → `spans_withheld` | **all exam** | raises | desktop figures, prebuilds |
| | | phone: `reader/phone_media.py:64` `phone_withheld`, `:126` `page_refusal`, `:166` `asset_refusal` | **all exam**, whole reading when it fails | refuses explicitly | phone host, through the sidecar's handlers with `request_origin` set |
| Q3 | May this region or text become practice? | `content/authoring/source_exercise_import.py:1202` (region), `:260` (book solution); `content/pipeline/jobs.py:3256` (Reader import); `exam_material.py:1002` `scope_only_among` (syllabus, not protection); the lexical floor `practice_leakage.py:144` `build_held_out_inventory` + `:224` `screen_practice_payload`, and `:247`/`:317` `reserved_questions`/`reserved_findings` | canonical import: **all exam**. Reader import: **held-out only** (§8 Q3). Floor: held-out *text*, plus the stems of items `learner_protection` withholds as exam or reserved | raises; reserved findings refuse | sidecar `source_service` and harvest/needs jobs; Reader import job; generation (CLI); follow-up and probe authoring, teacher (background, sidecar) |
| Q4 | May this item be served or picked in routine practice? | `scheduling/serving_exclusions.py:112` `routine_serving_exclusions` (:127 held-out items), `:131` `routine_withhold_reason`; `instructional/practice.py:226` `refuse_protected_pick`; `learnloop_sidecar/serving.py:256` `refuse_held_out_item`; `scheduling/intent/feasibility.py:109`; the phone's door `scheduling/device_eligibility.py:330` `PlanStepFilter`, `:395` `ineligibility_reason` | reserved exam-pool items; items made from **held-out** material (`held_out_item_ids` :1418), behind `goals.held_out_selection` | — | Today's queue, quick check, `find_practice`, picks, session serves (desktop and phone) |
| Q5 | May this item be a cold measurement, an exam item or an independent check now? | `serve_eligibility.py:648` `decide` (the reveal ledger); `exam_material.py:1464` `exposed_items` (exam pool, exam start, certification probe, cold retry); `instructional/policy.py:33` `cold_administration_open` → `source_retrieval/policy.py:80` `derive_policy` (`cold_attempt`) | reveals and attempts; shown material; open cold tasks and exam reservations | pure (`decide`); the others read | submit, every serve path (desktop, phone, TUI, CLI); tutor and retrieval policy |
| Q6 | May a model see this item's question and answers, or text derived from them? | `learner_protection.py:190` `withheld_items`, `:250` `attempt_protection`, `PastWork`; `adaptive_difficulty/protection.py:86` `protection`; `figures/service.py:3377` `item_passages` (an item's own passages while it's administered) | LP: **all exam** items (`item_exam_status`), reservations, open cold tasks, open remediation cold items, probes, unreadable items, with **the metadata gate** (:159). AD: **held-out** items and reservations only | fail closed (all three) | router card, teach-back, teacher, follow-up and probe authoring, confidence events, Reader learner state, figures (sidecar and background); chat read model `learner_context` and `remote/` (MCP); AD audits and forecasters (background) |
| Q7 | Is this grade a score, and is it evidence? | `held_grades.py:62` `held_for_review_attempts`; `learner_protection.py:276` `attempt_result` | the blind-grade ledger and grading evidence | — | 52 modules: learner state, scheduling, displays, model contexts |
| Q8 | May an item's own exercise, solution or worked answer be retrieved or shown now? | `source_retrieval/policy.py:80` `derive_policy`; `source_retrieval/corpus.py:544` `item_exclusions`; `instructional/policy.py:54` `attempt_window_open`; `tutor_qa.answer_leak_overlap` :1671 (accounting, not a block) | the caller's context, the cold state, the attempt window | policy refuses; overlap only debits | tutor, find_sources, compare, workbench (sidecar); MCP `remote/sources.py` |
| Q9 | May this payload leave the desktop, to the phone or a chat host? | phone: Q2's `phone_withheld` and Q4's device door, `learnloop_sidecar/phone_reader.py`; MCP: `remote/views.py:344`, `remote/sources.py:178-228`, `learner_context.py:1626` | Q1, Q2 and Q6, per payload | phone: closed; MCP: closed where it reads `protection_issues` | `learnloop_mobile`, `learnloop_mcp` |

Counts by surface: the desktop sidecar reaches all nine. The phone reaches Q1-Q5 and Q7 through the sidecar's own handlers, plus its own Q2 and Q9 predicate (`phone_withheld`). MCP reaches Q1, Q2, Q6, Q7 and Q8 through `remote/`. Background jobs reach Q1-Q3, Q5 and Q6. The CLI reaches Q1-Q3 and Q5. The desktop frontend owns no protection predicate, but it carries several measurement-integrity rules the server takes on trust (§3).

## 2. Disagreements

Each entry gives a concrete input on which the predicates disagree, and a verdict: *intended* (a recorded rule or owner default), *drift* (nothing explains it), or *docs conflict*.

**D1. The metadata gate: 4 readers fail closed, the rest fail open.** *Drift; the most important finding.*
- **Input:** `sources/source_sets.yaml` with an exam-role member and one validation error (or caught empty mid-rewrite: `vault/yaml_io.write_yaml` truncates, then writes, `:96-100`). `load_vault` turns it into a `yaml:invalid` issue and **no** source sets (`vault/loader.py:54-66`, `:327-329`). An empty file gives no issue at all (`loader.py:241-244` says so). Checked on a synthetic vault: valid gives `[('src_exam', 'exam')]`; invalid and empty both give `[]`, and `protection_issues` is True for both.
- **Fail closed** (they ask `learner_protection.protection_issues`, `:159`): `learner_protection.withheld_items` (:204), `learner_context`, `remote/views.py:344`, `section_coverage.read_protection` (:289). Section coverage's own docstring names the hole (:283-287, "exam material would silently become readable").
- **Fail open** (they read `exam_material` straight): `corpus.teaching_exclusions` and so the tutor, find_sources and compare; figures' `spans_withheld`; `phone_withheld`; the facet resolver; `source_exercise_import`; generation; the automatic build's unit exclusions (`add_source.py:1422`). For as long as the file doesn't load, rules 1 and 2 vanish. Rules 3-4 survive in the database, and so do signals recorded with `made_as_role` (`exam_material.py:776`).
- **Harm:** an exam paper's text could ground the tutor, or be imported as practice, while `doctor` reports the bad file. It needs a hand-edit error or a write race, so it's realistic but rare. Not a live leak today. Fix before G6 (§6, item 1).

**D2. Reader model contexts versus teaching contexts.** *Intended* (owner default §8 Q1, `exam-protection.md:99`, `:195`; `exam_material.py:100-104`).
- **Input:** a span of an exam-role member with no marks or signals.
- Reader Ask, the dialogue, presets and quick checks send it, with its neighbours, to the tutor or check model (`tutor_qa.py:902` checks held-out only). Teaching retrieval never returns it (`corpus.py:226`), the teacher refuses a lesson on it (`teacher/brief.py:199-208` via section coverage), and a *pinned* span gets dropped (`source_retrieval/tutor.py:508-520`). So the Reader is inconsistent with itself: a pin is refused and a selection isn't.
- The owner rule covers held-out material only (`exam_material.py:3-6`), so this isn't a breach.

**D3. The Reader's explanation paths: Ask versus figures versus the phone.** *Partly documented, partly drift.*
- **Input:** the same past-paper span.
- Desktop Ask explains it (held-out only). A figure for it is refused (`figures/service.py:554` → `spans_withheld`, all exam). The phone refuses the whole reading (`handlers/reader.py:666-672`) and any Ask on it (`:152`).
- The phone's set is documented as a deliberate superset (`reader/phone_media.py:3-8`). Figures' choice of all exam isn't explained anywhere beside Ask's held-out rule.
- **Harm:** none. Each refusal over-withholds.

**D4. Practice made in the Reader from exam material, versus how the item is treated afterwards.** *Drift, including in the docs.*
- **Input:** an exercise region on a past paper (an exam-role member, not held out).
- The Reader's "make practice" job passes it (`jobs.py:3256-3262`, `is_held_out` only, per §8 Q3), sends it to the authoring model and writes the item (`exercise_authoring.py:868-881` checks scope-only only). The canonical, harvest and needs import refuses the same region (`source_exercise_import.py:1202-1207`, all exam).
- The new item is then served in routine practice (Q4 excludes held-out items only, `serving_exclusions.py:127`), but `learner_protection` withholds it as `WITHHELD_EXAM` (Q6, all exam, `learner_protection.py:216-219`). So the router card, teacher, MCP and follow-up authoring don't see the learner's own practice. And `reserved_questions` makes its stem a reserved question (`practice_leakage.py:262-267`), so model text that echoes it is refused as a leak.
- The documents conflict: `exam_material.py:101` says "an import refuses exam material", while `exam-protection.md` §8 Q3 and `deliverables.py:1001-1004` call non-held-out exam material practice-available.
- **Harm:** over-withholding plus confusing refusals. No leak.

**D5. A model's view of an item: `learner_protection` versus AD.** *Intended, but unnamed.*
- **Input:** an item whose canonical exercise lies in a past paper (rule 1), or the selected item of an open cold check.
- `learner_protection` withholds its question and answers from the router card, teacher and chat. AD's audit and its outside forecasters may quote it (`adaptive_difficulty/protection.py:86-104`: held-out items and reservations only).
- AD's models only forecast difficulty, and their output carries no item text to the learner. So there's no learner-visible harm, but G6 should state the two sets as two answers, not one.

**D6. When a cold check's item is reserved.** *Drift (small).*
- **Input:** a remediation episode in `treatment`. `diagnosis/remediation.py:633` set its `cold_item_id`, but the `cold_retry` task doesn't exist yet: it's created after the primed attempt, `:1037-1045`.
- `learner_protection` already withholds the cold item (`:229-236` reads `remediation_episodes.cold_item_id`). `instructional/policy.cold_administration_open` (:33-51) and the out-of-timing serving exclusions (`serving_exclusions.py:306`) read open cold tasks only. So Today's queue can serve the cold item as ordinary practice before its check, and a tutor question on it runs `assisted_practice`.
- `serve_eligibility` then withdraws the spoiled check (it's honestly labelled), so the cost is a lost measurement, not a leak.
- The cold kinds are also defined twice: `learner_protection.py:102` `COLD_TASK_KINDS` copies `serve_eligibility.py:85` `COLD_FOLLOWUP_TASK_KINDS` instead of importing it.

**D7. The kill switch.** *Intended* (`exam-protection.md:176`). `goals.held_out_selection` switches Q4's and Q5's held-out serving rules (`exam_material.py:1444`). It never switches Q2 or Q6. G6 must keep that split.

**D8. Library search versus rule 4.** *Docs conflict.*
- **Input:** a held-out or held-back passage that matches a search.
- `source_retrieval/library.py:132-152` lists it with a snippet: `search_spans` with the library scope, and no protection filter. Rule 4's docstring says "no search hit" (`exam_material.py:55-58`), while `exam-protection.md` §2.7 says the library search deliberately doesn't ask, because the learner may read any source.
- Screen only: the query reaches a model, the snippet doesn't. The phone's allowlist has no search.

**D9. An item's source versus a quote's source.** *Intended* (different questions).
- **Input:** a source ref that names an extraction without a block, where only part of that extraction is exam material.
- `item_exam_status` and `held_out_item_ids` say the item isn't exam material: they count a whole-extraction ref only when the whole extraction is covered (`exam_material.py:1428-1430`, `:1510-1511`). `source_ref_protected` says the quote may carry exam text (`:1395-1397`, `whole & touched`). The quote rule is the conservative one for a model context, and that's right. The parity test should pin both.

## 3. Reach: what reaches a screen, a payload or a model prompt

**No live leak.** No held-out text reaches a non-grader model on any path traced. Every held-out check runs before its model call and fails closed (§1, Q2 and Q3). No answer key, rubric or solution reaches a chat host: `learner_protection.pinned_contracts` reads only `$.prompt` and `$.required_method` (`learner_protection.py:344-375`), `learner_context`'s `KeyBook` reads the key only to filter output (`learner_context.py:240-297`), and `remote/sources.py:229-230` drops solution-role blocks. Held-out text does reach the learner's screen in the desktop Reader when the learner opens that book. That is by design (`exam-protection.md` §2.7: reading is the learner's choice; exposure then keeps the item out of exam and cold use, Q5).

The owner's bar is a single learner on their own machines, with strict blindness only for the grader. Ranked by realistic, learner-visible harm:

| # | Finding | Evidence | Harm | Fix when |
|---|---|---|---|---|
| R1 | **Exam-reserved items pass the session serve door.** `refuse_held_out_item` checks items made from held-out material only. An item a goal's exam reserved after it entered a session, or one reached by a deep link, is served on the desktop and the phone. The queue, picks, AD and chat all count reservations | `learnloop_sidecar/serving.py:256-266`, called from `handlers/practice.py:363` and `handlers/queue.py:400`; compare `instructional/practice.py:234-235` and `serving_exclusions.py` reservations | medium-low: it puts an exam question in front of the learner as practice. It needs a reservation made while the item is open in a session, which isn't confirmed (§7) | before G6 (§6, item 3) |
| R2 | **MCP `find_sources` returns passages that the model-reader rule drops.** `remote/sources.py:63` `_PROTECTING` leaves out `WITHHELD_PROBE`, so a diagnostic probe item's own exercise passage can be returned verbatim. The library scope doesn't apply `model_reader_withheld`'s "assessment lane" either (`corpus.py:446-471`), so problem-set and unknown-role passages and spans cited by exercise links reach the chat host | `remote/sources.py:63`, `:93-115`, `:221-230` | medium-low: a chat host can walk the learner through a pending probe's exercise. The exposure is recorded (`sources.py:188-195`). Whether probe coldness reads it isn't confirmed | before G6 (§6, item 3) |
| R3 | **D1's fail-open** on an unparseable `source_sets.yaml`: the tutor, imports, figures and the phone (`phone_withheld`, `page_refusal`) read rule 1-2 material as unprotected. MCP and section coverage refuse | §2, D1 | low-medium: it needs a broken file, and `doctor` names it | before G6 (§6, item 1) |
| R4 | **Answer keys, rubrics and hints ride every serve payload before the answer**, hidden only by the screens: `practice_item_detail` sends `expected_answer`, the full `rubric`, `hints` and source quotes (`learnloop_sidecar/handlers/serializers.py:430`, `:432`, `:440`, `:443`), on the desktop and the phone, cold checks and exam-reserved serves included. The phone's `reader.dose_offer` likewise sends a question's `expected_answer` with its prompt (`handlers/adaptive_difficulty.py:110-111`) | serializers as cited | low: only DevTools or the host's network traffic shows it, and the only person it could help is the learner gaming their own measurements. It is, though, the one place where frontend-only hiding guards a measurement. G6 shouldn't fix it (screens are the UX stage's), but the parity test should record it as a known exception (§4) | UX stage, or a later payload split |
| R5 | **The mid-attempt tutor sees the key and is told not to reveal it.** `tutor_qa` builds the practice context with `expected_answer` and `rubric` (`tutor/tutor_qa.py:2205-2249`), under a "MUST NOT state the answer" prompt (`tutor/ai_contracts.py:498-505`). That includes cold administrations (`handlers/tutor_qa.py:414`). The exam screen offers no tutor (`ExamScreen.tsx:22-23`), but the server doesn't refuse an Ask for an exam item | as cited | low: by design. The ask is debited as a hint (cold: every question, `handlers/tutor_qa.py:446`) and overlap is debited as a reveal (`tutor_qa.py:1283-1290`), so a leak costs evidence, not integrity | none (record it in G6's note) |
| R6 | **Phone `dose_offer` uses AD's narrower set.** A rule-2 exam unit that the phone Reader redacts can still send its extra question's prompt and key at the boundary | `handlers/adaptive_difficulty.py:95-111`; `adaptive_difficulty/protection.py:95` | low: the same text is open on the desktop | G6 (the parity test) |
| R7 | **Library search lists snippets of held-out passages** (D8) | `source_retrieval/library.py:132-152` | low: screen only, at the learner's request | G6's docs |
| R8 | **Practice the Reader makes from a past paper** (D4): exam text goes to the authoring model and becomes routine practice, then is withheld inconsistently | §2, D4 | low: not held out, so not a breach of the owner rule | owner's call, before G6 (§6, item 2) |

Two more come from the frontend sweep. Both are learner-visible or contract drift, and neither is a live leak of keys or held-out text:

| # | Finding | Evidence | Harm | Fix when |
|---|---|---|---|---|
| R9 | **The inspector shows every authored hint for any item, the one being answered included,** with no hint counted, in the normal UI. That covers cold checks, probes, and exam-reserved and held-out items. Simple mode withholds the key and rubric of an unanswered or open question (UX Phase 4.1), but not its hints. Classic mode shows the key and rubric too, "as before". `inspect_entity` applies none of the serve doors | `apps/learnloop-tauri/src/components/InspectorOverlay.tsx:376-382` (the withholding rule), `:482-505` (hints always), reached from the practice card's details (`screens/PracticeScreen.tsx:2385-2390`); `learnloop_sidecar/handlers/inspector.py:24-28` | medium-low: a deliberate click voids a cold check or probe without the server knowing, and an exam-reserved item's question can be read there. Classic mode's key display is a recorded UX decision, so the hints are the gap | before G6 (§6, item 3): the inspector's item detail drops hints, key and rubric on the server while the item is unanswered, cold, reserved or held out, or the click is recorded as a reveal |
| R10 | **The FG1 follow-up hold is server-side for the feedback bundle only.** `followup_run/serving.py:33-63` nulls `answered_expected_answer` ("on the server, so nothing can show it", :61), but the feedback screen's `item` comes from `get_practice_item`, which carries `expected_answer`. `feedback/FeedbackSurface.tsx:101-103` falls back to it, and only `followup.held` stops it rendering (`screens/FeedbackScreen.tsx:2540`, `:2733`, `:3107`) | as cited | low-medium: DevTools only, but it contradicts the server's stated contract, and the generated probe would then look independent when it isn't | with R4's payload split; meanwhile the parity test pins the hold on both fields |

**The desktop frontend's own checks** (a sub-review of 30-odd TSX sites): most are displays of a refusal the server already made (the Reader's `groundingProtected`/`selectionProtected`, `readerShared.ts:107-123`; withheld figures, lessons, Ask steps and reading paths). The rest hide content the server sent, or decide something the server takes on trust:
- The hint ladder: the server takes `hints_used` from the client (`handlers/practice.py:792`, "telemetry only").
- Self-grade disclosure: `record_self_grade_disclosure` is reported by the client.
- Feedback deferral inside a probe block: `submit_attempt` returns feedback mid-block (`handlers/practice.py:2094-2096`), and `get_feedback` has no block refusal.
- The eliciting question's repaired trace (`FeedbackScreen.tsx:3531`; `CausalAttribution.tsx:821-825`).
- Locators hidden during a check on your own (`locatorsHidden`).
- The Reader quick check's intended answer, revealed only after a response.
- The randomized check's `noHelp`, which the server sets for a phone origin only (`handlers/practice.py:418-430`).

None of these is a protection predicate in G6's sense. They are measurement-integrity rules carried by the client. G6 should list them, not move them; that's the UX stage's and a payload split's job.

## 4. What G6's parity test must add

G6's proof as written ("a parity test of every site on a protected fixture, before and after, which must include each leak the phone stages' reviews found") covers too little: one fixture can't tell the sets apart. Make it a **matrix**: fixtures × surfaces, with the expected answer pinned per cell, so that a deliberate difference (D2, D3, D5, D7) is a pinned cell, not drift.

**Fixtures** (one synthetic vault, built with `tests/helpers.py`'s builders and real source rows; no owner data):
1. A past paper: an exam-role member with no marks or signals (rule 1 only: all exam, not held out). This is the class every set disagreement turns on.
2. A rule-2 exam unit (`role_override: exam`) on its marked reading, with a textbook chapter beside it, plus a split unit whose `#Exam` half is exam and `#Theory` half teaches (`exam-protection.md` §1.2).
3. A held-out unit (rule 3) on a marked reading, and one whose mark doesn't resolve (whole extraction).
4. A protected book with a second, unmarked reading (rule 4, held back), and a book with an ambiguous legacy mark.
5. A held-out signal on the reading its run read, and one of unknown reading.
6. Items: one made from each of 1-5 (canonical exercise, block refs, an extraction named whole on a partly protected reading, for D9); one reserved for an exam; one an open cold task holds; one a remediation episode holds before its task exists (D6); a diagnostic probe; an attempt with a held grade.
7. A Reader-imported item from fixture 1 (D4).
8. `source_sets.yaml` unparseable, and empty (D1).
9. `goals.held_out_selection` off (D7).

**Surfaces**, one column each, through the production function:
- Q2: `teaching_exclusions`, `model_reader_withheld`, the Reader's Ask, presets and checks, `reader_guidance.held_out_sections`, figures' `withheld_message`, `item_passages`, `section_coverage.read_protection`, `source_ref_protected`, MCP `remote/sources`.
- Q3: `source_exercise_import` (region and book solution), the Reader import job, the lexical floor (`build_held_out_inventory`, `reserved_questions`).
- Q4 and Q5: `routine_serving_exclusions`, `refuse_protected_pick`, `refuse_held_out_item`, the device door (`ineligibility_reason`, `PlanStepFilter`), `exposed_items`, `cold_administration_open`.
- Q6: `withheld_items` and `attempt_protection`, AD's `protection`, `learner_context`'s traces.
- Phone: `phone_withheld`, `page_refusal`, `asset_refusal`, `reader.render_view`, `reader.guide_plan`, `reader.ask` and `ask_history`, `practice.as_printed`, `reader.dose_offer`.
- MCP: `find_sources`, `learning_context`, `library`.

**Fail closed:** each predicate patched to raise, and fixture 8, give "withheld" (or a refusal) in every cell.

**The leaks the reviews found, as cases** (fix locations at this tip):
- Phone V4: F1 cached page images (`apps/learnloop-mobile/public/sw.js`; host `learnloop_mobile/host.py:494-502`); F2 display cache after a whole-reading refusal (`readerCache.ts:28-44`); F3 a page addressed by another reading's id (`phone_media.py:126-163`); F4 Ask history judged on the stored event, not the projection, with `reader_inquiry` off or both tutor switches off (`handlers/reader.py:331-347`, `reader_dialogue.py:977`, commit `b1b08138a6`; `tests/test_mobile_v4_codex_review.py`), the fresh answer (`reader.py:224-230`) and the guide plan's placed question (`reader.py:838-898`); F9 the dose offer as an answer reveal; F10 and F12 eligibility and the media lift (`device_eligibility.py:217`, `:241-270`, `:428`); F13 and F14 the question action (`reader.py:2298-2313`); a held-out heading as a section label (`reader.py:887`).
- Phone V2: F3 a held desktop miss leaking the worked answer (`handlers/feedback.py:205-241`, `followup_run/serving.py:33-63`); F5 a restored randomized check offering hints (`handlers/practice.py:418-430`); F2 a pick bypassing the device filter (`handlers/daily_plan.py:858`). Phone V3: F1 a phone burning the desktop's probe (`serving.py:148-239`).
- MCP C1a: F1 unreadable or empty source sets (`learner_protection.py:159-203`); F2 recurrence groups (`learner_context.py:1265`); F3 provenance forms (`exam_material.py:1271-1383`); F4 past keys against the current key (`learner_context.py:240-297`); F5 reservations during retrieval (`remote/sources.py:188-195`); narrow F1 a raw id confirming a withheld title (`sources.py:118-133`).
- Exam protection: gaps a-e (`exam-protection.md` §3), the Reader's three refusal tests, and the codex review's F1 and F6 (held-out items out of routine serving, behind the switch).
- K1's own: D1, D4, D6, R1, R2, R6, R9, R10.

**Known exceptions, pinned as such:** R4 (keys in serve payloads) and R5 (the tutor's key), so that a later payload split shows up as an intended change.

## 5. Routing ingest, synthesis and authoring through `learner_protection`

**Answer: no. Don't route them.** `learner_protection` answers Q6, an item-level question (may a model see this item's question and answers), with a wider union: all exam material, reservations, open cold checks, the cold items of open remediation episodes, diagnostic probes and unreadable items. It also has a fail-closed metadata gate. The pipeline asks span-level questions (Q1-Q3), its book-marking bookkeeping and plain role labels. `learner_protection` has no span, text or marks API. Routing through it would either make it a façade over `exam_material` (one more name for the same call) or change checks, as the table shows.

| Call site | Question | Would routing change the check? |
|---|---|---|
| `content/pipeline/exam_marking.py:117`, `:124`, `:138`, `:175`, `:247` (`source_marks`) | rule-4 marks for the book's card and the marking action | **No equivalent.** It's bookkeeping, not withholding. Keep it direct |
| `content/pipeline/reread.py:642` (`source_marks`) | is this book protected (a re-read keeps its marks) | **No equivalent.** Keep it direct |
| `content/pipeline/revision_refresh.py:216` (`is_exam_role`) | does a scope carry an exam override (a label test) | **No.** It isn't a protection read |
| `content/pipeline/add_source.py:1385`, `:1422` (via `corpus.source_exam_exclusions`) | which units an automatic build leaves out | **Yes, in one case.** Through the metadata gate, an unreadable `source_sets.yaml` would refuse the build instead of building exam units as teaching (D1). That change is wanted, but it belongs in `exam_material` (§6), not in a reroute |
| `content/synthesis/source_set_synthesis.py:263` (`exam_material(vault.source_sets)`) | which units are assessment-only; held-out spans join the gate | **No change in practice.** It passes the sets, not the vault, so no gate could run. With the sets unreadable, the set being synthesized isn't loaded either |
| `content/facet_identity/authority.py:397` (resolver over `vault.source_sets`) and its callers, including `content/synthesis/source_append.py:904` | does a citation resolve to the role `exam` | **Yes, in one case.** The same fail-open: unreadable sets drop rule 1 and 2, so an exam citation could read as teaching authority. The gate would refuse. As above, the fix goes in one place |
| `content/authoring/source_exercise_import.py:1202` (the region), `:260` (the book solution) | may this region become practice; may this solution reach a model | **Yes.** It's span-level and all-exam. The item union would add nothing it needs, and the gate would add D1's refusal |
| `content/pipeline/jobs.py:2988-3001` (Reader quick and inquiry checks), `:3256` (Reader exercise import) | may a model author a check from this, or make practice of it (held-out only, by the owner's §8 Q1 and Q3 defaults) | **Yes, and wrongly.** The all-exam union would refuse non-held-out exam material, against the owner's recorded default (D2) |
| `content/authoring/practice_generation.py:1323`; `practice_leakage.py:432` (`build_cross_source_spans`) | may a span ground generation | **No equivalent.** It's span-level |
| `practice_leakage.py:133`, `:141`, `:270` (`held_out_spans`, text) | the lexical floor's fingerprint | **No equivalent.** It needs the held-out *text* |
| `content/sources/exercise_statements.py:169` (`exam_withheld`) | does an exercise statement widen into exam material | **No equivalent.** It's span-level |
| `content/authoring/exercise_authoring.py:881`; `source_exercise_import.py:1220`, `:1360`; `jobs.py:3267` (`scope_only_among`) | is this syllabus material (never practice) | **No.** It isn't protection. Routing it would be a category error |

So G6 should keep `exam_material` as the one span-level authority (Q1, with its two sets named) and `learner_protection` as Q6's item-level authority built on it. It should move the metadata gate into the shared read, so every caller fails closed, and keep each surface's set choice explicit and tested (§4).

## 6. Before G6

These are concrete bugs or decisions, each small. None changes persisted meaning. I fixed none of them (this step is read-only).

1. **One metadata gate in the shared read (D1, R3).** `exam_material`, `held_out_partition` and `role_material` should treat a vault with `protection_issues` as unreadable, so every caller fails closed as it already does on an exception. Callers that pass bare `source_sets` (`source_set_synthesis.py:263`, `facet_identity/authority.py:397`) would pass the vault instead. Separately, an atomic `write_yaml` for the source-sets file (write a temp file, then rename) closes the truncate-then-write window for in-process readers. Fail-first test: fixture 8 against the tutor's teaching scope, `source_exercise_import`, figures and `phone_withheld`.
2. **Reader-made practice from exam material (D4, R8): the owner's call.** Either the Reader import refuses all exam material, as the canonical import does, or an item the learner made from practice-available material isn't `WITHHELD_EXAM` in Q6 and the floor's reserved questions. Either way, `exam_material.py:101` and `deliverables.py:1001-1004` have to agree. Recommended: the second. §8 Q3's default (the learner chose it) stands, and only model contexts change.
3. **Doors that miss a reservation (R1, R2, D6).** `refuse_held_out_item` should also refuse an exam-reserved item (`refuse_protected_pick`'s rule). `remote/sources.py:63` should add `WITHHELD_PROBE`, and the MCP library scope should apply `model_reader_withheld`. A remediation's cold item should count as reserved from the moment it's chosen, in `cold_administration_open` and the out-of-timing exclusions. `learner_protection.COLD_TASK_KINDS` should import `serve_eligibility.COLD_FOLLOWUP_TASK_KINDS`. The inspector's item detail (R9) should drop hints, key and rubric on the server while the item is unanswered, cold, reserved or held out (or the click should be recorded as a reveal).
4. **Docs (D3, D8).** Rule 4's "no search hit" (`exam_material.py:55-58`) against the library search, and figures' all-exam set against the Reader's held-out set: either the code or the docstring changes, by the owner's §8 Q1 default.

## 7. Not verified

- **Nothing was run against a vault or a copy.** Every claim above is from reading the code at `ad194ddc3a`. The one exception is D1's loader behaviour, run on a synthetic vault. The disagreements' concrete inputs were constructed by reading, not executed end to end: the parity test is where they first run.
- **How often real vaults hit the "exam but not held out" class.** If the owner's exam members carry held-out signals from synthesis, most of each paper is held out and D2-D5 shrink. This needs the owner's read-only script, not an agent.
- **R1:** whether an exam reservation can be made while the item sits in a session or behind a deep link, and whether serving or inspecting a reserved item counts as "shown" (`db/stores/source_service.shown_items`), which would withdraw it at the exam's start.
- **R2:** whether a probe's coldness reads chat exposure (`remote/sources.py:188-195`).
- **R9:** whether a peeked hint is recorded anywhere. The sub-review found no write from `inspect_entity`.
- Whether a stable unparseable `source_sets.yaml` raises during the secondary's settled load instead of becoming an issue. The loader code says it becomes an issue.
- Whether Reader extra questions are generated on rule-2 exam units (R6), and whether quick-check questions can be promoted into practice items.
- How the phone PWA renders the key, hints and rubric it receives (R4), and what its display cache keeps from plan steps.
- Whether the desktop serves randomized checks cold and refuses hints on them (the `noHelp` row).
- The CLI and TUI surfaces were read only where a predicate is called. The TUI is to be rebuilt (decision 4).
- `practice_generation.generate_cross_source_practice_proposal` has no caller in `src` outside tests. I didn't establish whether it's live.
