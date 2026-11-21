# Teacher v2: lessons on the current LearnLoop

**Status:** draft, 2026-11-20, for the owner's review. Not queued. Replaces `spec_teacher_v1.md` as the plan; v1 stays as the record of what TE0, TE1, TE1b, TE2-log, TE2, TE3a and TE3b built (its §20 "As built" notes and the review files they cite). Read at main `1f9c8de1b3` (migration head 255).

**Why a rewrite and not revision 6.** v1 is 1,791 lines, written across five revisions before most of what the teacher now sits on existed: the router objective (RO0-RO6), follow-up generation (FG1), the instruct hand-off (IH), slip-or-gap (SG), the refactor's arc D (switches removed), the evidence-packets and AD-memory drafts, MCP v2 and notebook activities. Everything v1 planned is either built, carried here, moved to the spec that now owns it, or named as superseded: §15 is the parity table.

**Sources.** `spec_teacher_v1.md` and its review files; `spec_evidence_packets_v1.md` (EP, Part F holds sensor rendering since 2026-11-20); `spec_router_objective_v1.md`; `spec_instruct_handoff_v1.md`; `spec_learner_input_after_miss_v1.md`; `spec_deliverable_curriculum_v1.md`; `spec_notebook_activities_v1.md` (NA); `spec_implementation_teachback_v1.md`; `spec_ad_memory_v1.md`; `spec_mcp_v2.md` (branch `docs/spec-mcp-v2`); `refactor_strategy_v3.md`; ledger `docs/reviews/refactor-bug-ledger.md`. Three independent reviews of §7-§8 (Fable, Codex Astra, Opus high), 2026-11-20, `docs/reviews/teacher-v2-arc-reviews-2026-11-20.md`; their findings are folded in and named where they changed the design.

---

## 1. Owner direction

### 1.1 Carried from v1 (2026-10-23/24), still binding
1. **Teaching quality from LearnHarness** (ideas, never its AGPL text or code); **principle i** (unconditional truths and ansätze first) and **principle ii** ("how could I have discovered this?", 3Blue1Brown as the standard).
2. **The learner is not new each lesson:** the teacher starts from LearnLoop's latent state and writes back honestly.
3. **The outcome is delayed cold retrieval and transfer.** In-lesson checks steer; they never certify.
4. Grounded in the learner's own sources. Frontier-model judgment over hand-written rules.
5. **No zero-weight effort:** an answered, graded lesson check is evidence, at a learned mass (v1 §12.1).
6. **The router suggests, the learner opts in;** "Teach me X" everywhere; every suggestion and response logged.
7. **No made-up numbers:** each number is a seeded prior with its basis, a structural bound, or `keep` with its reason.

### 1.2 Later standing rules that bind this spec
- No hard-coded routing rules; stuckness reaches the router only as evidence (IH, Nov 8). Lessons compete with follow-ups (Nov 8).
- No kill switch on a new successor unless the owner asks (Nov 16).
- Only the grader is blind; learner data goes to a model whenever it helps (Nov 1).
- Anything framed as teaching opens a Teacher lesson; Ask tutor is for questions about what is on screen (Nov 14).
- The Decider, not token overlap, judges answer reveals, with the quote (Nov 18).
- Frictionless defaults, glass box on demand (Oct 13).

### 1.3 The owner, 2026-11-20 (this spec's brief)
- **Sensor rendering belongs to the evidence-packets spec;** the teacher spec holds teacher-specific extensions of it (§5). Done: EP Part F (§7a).
- **Chat lessons are kept, inside the MCP v2 draft** (§13).
- **`S_eff` / liquid stability is AD memory's** (`spec_ad_memory_v1.md`).
- **Multi-session lessons through the deliverable curriculum** ("extremely valuable"), and the router's lesson action revised to match, after review by three independent models (§8).
- **Delayed checks are generated** (§7).
- **Lesson checks inform the diagnoser**, although they are not independent, and the after-a-miss learner input applies to them (§6.3).
- **Notebooks change the teacher's toolset** (§10).
- Parity with everything v1 planned, except what is superseded or deprecated (§15).

---

## 2. What exists today

One paragraph per stage; the details are v1 §20's "As built" notes.

| Stage | Built | Since changed |
|---|---|---|
| **TE0** | Confidence taps and hedge reads rendered as events into the diagnoser, hint writer, tutor, teacher and router card (`learner_state_card_v2`) | Moves onto EP's evidence view at EP4 (EP §7a.4) |
| **TE1** (`mvp-0.41`, migration 234) | `learnloop.teacher`: doctrine v1, `LessonBriefV1`, `TeacherTurnV1`, read actions, guards, minted lesson checks as `reconstruction_after_walkthrough`, the learned lesson-check weight and pool (`learner/lesson_weight.py`, one DERIVED replayer), forecasts, reveal rows, delayed retention/transfer checks, the receipt, the lesson screen, journalled turns with `resume`, the per-lesson spend envelope | Switches `teacher.weight.learned`/`.source` removed (D7a); K6-7 (help that reproduces a check's solution in a choice withdraws the check) fixed |
| **RW5d P4b** | A turn's `visual` (tiers `grammar`, `sketch`: `figures/request.py` `LESSON_TIERS`) | Notebooks attach richer visuals asynchronously (§10) |
| **TE1b** (`mvp-0.43`, migration 236) | A daily lesson suggestion at Today's open, the acceptance model, mutes, `router_suggestion_responses` | Switch removed (D7e); serves only where the objective doesn't |
| **TE2-log** (migration 247) | `lesson_episodes`, `lesson_activity_intervals`, `note_detour`, `p_held`, minutes, report lines | — |
| **TE2** (`mvp-0.51`, migration 248) | `serve_probe` through FG1 (generated, single use), `propose_gap` (source `lesson`), typed goals through C0b's resolver and `create_goal_lo`, `lesson_brief_v2` with `where_you_left_off`, Continue/Close on Today | `teacher.probes` removed (D7e). Not built: the teacher's own `create_goal_lo` mid-lesson; the library lookup before a new topic |
| **TE3a** (`mvp-0.52`, migration 249) | AD's `lesson` opportunity kind, one dose per landed/taught node; the objective's `LESSON` branch reads its curve | SG2 (`mvp-0.57`) splits lesson and repair slopes by miss cause |
| **TE3b** (`mvp-0.53`) | Lesson offers as objective candidates at reversible block boundaries, traced, lesson minutes on the objective's clock, lesson LOs in its population | Switches removed (D7e). IH2 (`mvp-0.55`): lessons compete with follow-ups in one logged decision, the forced-items exclusion and the `cold_failing` gate gone; IH7: a lesson after a miss reads the sections matching the diagnosed confusion and the latest diagnosed miss on its topic |
| **Teach hand-offs** (Nov 14) | "Learn it with the tutor" and "Stop diagnosing and teach me" open a lesson with a `from_check` brief (`teacher/from_check.py`); the tutor only as fallback | TH-3 (a mid-check stop never ends the block) and TH-4 (released feedback never shown) open |
| **Exam-question guard** | Short distinctive reserved stems withheld from teacher text | — |
| **UX fixes** | UX-14 (Continue on the simple Today), UX-21 (Begin opens a lesson offer), UX-22 (the learner's reply stays on screen) | — |

**What the owner's data shows** (a backup-API copy of arxiv_v2, 2026-11-20): 9 lessons from Nov 9 to Nov 18 (6 learner-picked, 3 router-offered); 5 closed `goal_reached`, 4 left open; 35 answered lesson checks, mean correctness 0.81, 4 misses, 2 withdrawn; 12 detours, 3 gaps filed, 1 probe; 3 LOs taught in more than one lesson; **all 24 planned delayed checks (19 retention, 5 transfer) recorded `missing`**: the picker found no unseen, non-lineage vault item; no deliverable resolution exists in the vault. v1 §1.5's census (zero lessons) predates all of this.

What that means: lessons are being used, across sessions, without the outcome the spec is built around. The lesson-check weight and the forecast pool can still resolve on any later qualifying cold attempt on the same LO (`learner/lesson_weight.py:724`, `:851`; Astra), but nothing the lesson itself commits ever arrives.

**Open defects on the teacher** (ledger): K5-6 (a short key such as `42` scores 0 in `answer_leak_overlap` on teacher text), L4-2 (the weight's fit replays intervening updates with current item parameters, not those graded with), TH-3, TH-4, UX-12 (source TeX macros unrendered in lesson text).

---

## 3. What a lesson is (the thesis, unchanged)

A lesson is a short, grounded, LearnHarness-style teaching session run by a frontier model, which reads the learner's latent state at open, plans an outline of at most about ten nodes, teaches each with predictions and checks, repairs in place when a check misses, and closes by committing cold checks on what it landed. In-lesson evidence is assisted and steers; cold checks days later measure. Everything a lesson shows is accounted as exposure; nothing it shows is reserved or exam material.

Doctrine v1 (`teacher/doctrine/`) stays the teaching text, with the TE2 and episode paragraphs. Doctrine changes are versioned and start a new forecaster family (v1 §12.2).

---

## 4. Architecture now, and one consolidation

### 4.1 The pieces
- **One sidecar method per lesson action,** `lesson.turn` (open, reply, check submit, help, resume, close), plus `lesson.view`, `lesson.activity`, `lesson.goal`, `lesson.open_lessons`. One grant covers the lesson (T1 redesign D).
- **The brief** (`teacher/brief.py`), deterministic and versioned: `lesson_brief_v2` today.
- **The turn:** one message plus requested actions; the model is called again only after a read action (one follow-up per turn).
- **Actions:** `read_source`, `find_sources`, `find_practice`, `read_history`, `read_note`, `write_plan`, `forecast`, `close`; with episodes `note_detour`; with TE2 `serve_probe`, `propose_gap`.
- **Guards** (`teacher/guards.py`) on every learner-facing field; reveal rows through the strict writer in the turn's transaction; protection re-checked before every model call.

### 4.2 One turn schema (TE5, structure)
Today there are **eight** `TeacherTurn*` classes (`teacher/contracts.py:122-278`), every combination of visuals x episodes x TE2, with literals overridden per class. NA §9.2 would add seven notebook verbs "in all eight", and chat would add a driver: the product grows multiplicatively.

**Change:** one `TeacherTurnV2` whose `actions` is a discriminated union over **every** action, and a per-lesson **capability set** recorded at open (`visuals`, `episodes`, `probes`, `notebooks`, `chat`) from which the prompt lists the allowed actions and the validator refuses the rest. The capability set is on the lesson row (it already records `brief_version`, `doctrine_version`, `algorithm_version`), so replay and resume read it, never today's config. Adding an action is then one entry in the union, one executor in `teacher/actions.py`, one capability, one doctrine paragraph.

This is a pure move for every existing lesson: an AST/golden check that each of today's eight classes accepts and refuses exactly what the union does under the matching capability set. It follows the refactor's strategy-E shape (`refactor_strategy_v3.md:370`: one function per action kind, a plain `match`). `PROMPT_VERSION` does not move until a capability set changes the prompt text.

### 4.3 Context compaction (TE5)
Not built (no `teacher.context.compact_at`). A long lesson resends doctrine, brief, sources and the whole transcript every turn (v1 §17: 0.3-1M input tokens a lesson). Compaction replaces the oldest turns with a code-built summary of the plan's state, the checks and their outcomes and the episodes (ids and numbers, no model call), keeping the last turns verbatim. The trigger is the model route's own context limit minus a margin measured from the dry-run lesson (`keep`, operational); the summary's version goes on the receipt.

---

## 5. Teacher extensions of the evidence view

EP builds one `EvidenceView` for every model (EP §5.2) with attempt facts (§3), claim cards (§4) and, since 2026-11-20, sensors rendered with event, personal frame and track record (§7a). The lesson brief becomes a rendering of that view plus what only a lesson has:

| Extension | What it adds | Source |
|---|---|---|
| **Lesson-check facts** | Per lesson check: the minted item, the node, correctness, tap and hedge, the mass applied and the learned mass (with its posterior width), the forecast it bound to | `lesson_checks` |
| **Lesson history** | `last_lessons`: earlier receipts on these LOs, their plans, and their delayed checks labelled distinctly as `pending`, `answered cold` (with result), `missing` (no question existed), `exposed` (withdrawn after exposure), `expired`. Never collapsed into "checks showed Y" (Astra) | `lesson_receipts`, `lesson_plans`, commitments |
| **Arc lines** | the lesson's ordinal in its arc, the deliverable's sentence, date and path-next when there is one, the previous lesson's proposed next session (§8.3 C) | LO overlap, deliverable binding, receipts |
| **Episodes** | Detours, probes, gaps and goal LOs from earlier lessons on these LOs, with their repair kinds and outcomes | `lesson_episodes` |
| **Teacher sensor lines** | In the legend block (EP §7a.3): the learner's calibration on lesson checks specifically ("on lesson checks marked 5/5 you were right 11 of 12"), and the teacher's own forecast track record for this learner ("your `lesson_step_retained` forecasts: 3 resolved, 2 right") | EPp snapshots for `lesson_check_correct`, `lesson_step_retained`, `lesson_node_held`, `lesson_probe_correct` |
| **From a check** | `from_check`: what a diagnostic check found, for a lesson opened from it | `teacher/from_check.py` (built) |
| **After a miss** | IH7's diagnosed-confusion sections and the latest diagnosed miss on the topic | built (IH7) |

**What changes for the teacher at EP4.** The brief's `history` index (one-line headers with "assisted / primed / cold") is replaced by EP's facts lines; "assisted" and "primed" leave the teacher's prompt as they leave every packet. Read under `Cutoff.current()` (EP §7). The brief keeps its own version; EP4's bump for the teacher's prompt follows the playbook (a new forecaster family for the pool, v1 §12.2).

**Never in the brief** (carried): EVSI values, costs or policy scores; cold-reserve or protected items; vault items' expected answers or rubrics; notebook keys and cold-eligible masked values (NA §14).

---

## 6. Checks and evidence

### 6.1 Lesson checks (carried, built)
`reconstruction_after_walkthrough`, never certifying, never a Check once, at the learned mass `m = σ(η₀ + u_L + β_c·z_c + β_p·z_p)` learned only from later qualifying cold outcomes on unseen items of the same LO (v1 §12.1), mixed with the teacher's `lesson_step_retained` forecast by the learned pool weight λ (v1 §12.2). L4-2 is fixed with the next tag that touches `lesson_weight.py`.

### 6.2 Reveals, judged by the Decider
A teacher reply that gives away an open check is today judged by `solution_overlap` on the assembled visible text (K6-7). Under the owner's Nov 18 direction it moves to the **shared answer-reveal judgment**: the Decider compares what the learner saw with the check's stem and rubric, per criterion, with the verbatim quote. The lexical guard stays as the pre-display guard and as the verdict whenever the Decider does not answer; replay reads the stored verdict. K5-6's short-key case is closed by the same step (`span_answer_overlap` where the item is known). This is the reveal-adjudication step's work (EP §6, the Decider's first annotation); the teacher adds only its call site and test.

### 6.3 Lesson checks inform the diagnoser (TE7, owner 2026-11-20)
v1 kept the split diagnoser off lesson checks (v1 §12, §11.7, rev 5 decision 6) because a check right after teaching is not independent. The owner: "I wish we could use lesson checks for informing larger diagnoser models even if it isn't independent." Not being independent rules out certification and cold evidence; it does not rule out diagnosis, provided the dependence is stated and weighed.

- **What is diagnosed:** a missed lesson check, a partially credited one, and a correct one with a hedge or a tap of 1-2. The diagnoser runs as it does on practice attempts (blind grade first, then the history-aware diagnosis), with the **teaching transcript of that node** in its context: what was explained, which example, which prediction the learner made. That is the one thing only a lesson has, and it lets the diagnosis separate "the explanation did not land" from "a misconception survived being taught".
- **The label:** its observations carry `answering = lesson_check` and the fact `taught_then_checked` (EP §3.2's facts, with the node's teaching seconds before the check). Its hypotheses are claims (EP §4) whose support cites the lesson attempt with that label.
- **The weight:** a hypothesis update from a lesson check enters at a tempering weight `ω`, a second learned family beside `ρ` in `learner/lesson_weight.py` (the after-a-miss spec already adds `ρ` there): seed `ω ~ N(logit 0.5, 1²)` on the logit scale, basis `legacy` (the lesson-check mass's own centre, since both say "assisted by the teaching just given"), learned from whether a hypothesis raised in a lesson is later supported by a qualifying cold outcome on the same LO. The weight applied is the posterior mean as of the diagnosis, recorded, so replay reproduces it.
- **The learner's words (after-a-miss spec, built):** a missed lesson check gets the same "why do you think you missed it?" box and the same three narrowing routes (reweight only, never remove). Inside a lesson the teacher already asks; the change is that the learner's answer is filed as learner text in the after-a-miss form, not only as transcript, and the teacher sees the narrowed hypotheses on its next turn.
- **What does not change:** a lesson check still opens **no FG1 follow-up workflow** (rev 5 decision 6 stands: a generated probe right after the step was taught is exposed anyway). The diagnosis reaches the next lesson's brief, the router's evidence view and `propose_gap`'s pipeline. Detours (the teacher's own in-lesson diagnosis) are passed to the diagnoser as context, not as evidence.
- **Volume:** 4 misses and a handful of hedged successes in 35 checks on arxiv_v2; at today's use, a few diagnoses a week, on the plan route.
- **Deferred trigger in v1 §22 ("split diagnoser on lesson checks") is retired:** the owner decided it.

### 6.4 Probes inside lessons (carried, built)
TE2's `serve_probe`: FG1-generated, single use, served cold with tools refused, burned at first serve, a blind-graded `diagnostic_probe`, its forecast written first.

---

## 7. Delayed checks, generated (TE6; owner 2026-11-20)

### 7.1 Why
The vault-item picker found nothing for any of arxiv_v2's 24 delayed checks: the LOs the teacher lands are often new or prerequisite LOs with few or no items, and the lesson's own exposure and lineage exclusions remove the rest. v1 §1.5's census had already found 20 of 73 LOs with no unseen item. The owner's Nov 3 rule ("for probes generation is superior") applies here too.

### 7.2 The lifecycle (the three reviews' conditions, adopted)
A delayed check gets its own origin, not the placement probe's lifecycle unchanged: today generated probes are excluded from delayed candidates (`delayed_checks.py:70`) and the lesson generator refuses closed lessons (`followup_run/lesson_probe.py:126`).

1. **Commit when a node lands.** Each landed node gets a retention commitment as it lands (or at the session's partial receipt, §8.3 D), dated by retrievability as built (`teacher.delayed.target_retrievability`, seeded `R*` 0.9, basis `published`). The commitment is durable, exists whether or not a question exists yet, and has a visible state: `being written`, `ready`, `missing`, `exposed`, `answered`, read the same way by the receipt, the brief and the objective's population (Fable). §12.2's forecasts are about "the committed cold item" at node landing with a shared seed (`teacher/delayed.py:139-142`), which is why commitment, not the question, is the anchor.
   **Transfer comes second** (Fable): TE6 builds retention first; the lesson's single transfer commitment (v1 §13) follows in TE6b, once retention checks have run, since "never filled by a look-alike" is hardest to honour for generated transfer.
2. **Generate from landing, screen at close, retry until the date.** A durable job (origin `lesson_delayed`, key `lesson_delayed:<lesson>:<node>:<purpose>`) authors the question through FG1's operation when the node lands, is screened against the whole lesson's displayed text at close (so a later turn's example is a rival too), and retries while the plan route is down until the due date (the generation path is plan-only, `followup_run/lesson_probe.py`; Opus). The author gets **the LO and the taught facets as its target, never the lesson's transcript** (the teacher and the author are likely the same model family and would reach for the same canonical example; Opus). For transfer: a downstream LO's facet or the goal LO in a representation the lesson did not use, with **criterion targets emitted** so `measures_facet` can establish the relation (Opus); if no relation is established, the transfer check is `unavailable`, as built, never filled by a look-alike.
3. **Admit, with item-level exposure.** FG1's output checks and `persist_item` with `source = 'lesson_delayed'`, parked and reserved (every door refuses it). Machine admission checks structure and freshness, not psychometric quality (Astra), and the cold guards that exist are per item and pass trivially for a fresh one (first attempt, no reveal row, lineage: `learner/lesson_weight.py:750-753`, `teacher/delayed.py:165-167`), so a generated question could restate the lesson's worked example and still qualify (Fable). Three gates beyond admission: **`question_overlap` and lineage against everything the lesson displayed** (`teacher/delayed.py:63-90`, reused; Opus); **FG1's manipulation audit with the lesson's own checks and examples as the comparator** (it is `not_applicable` for lesson probes, `followup_run/lesson_probe.py:20-22`, but here a comparator exists; Fable); and the **Decider's shared reveal judgment** (owner, Nov 18) asked whether the question's answer appears in or follows trivially from what the lesson showed, with the quote, refusing on yes. This is the item-level exposure rule D needs: the existing precedent is topic-level (a lesson probe answered after topic text was shown is `instructional_diagnostic` and resolves nothing, `attempts/attempts.py:2783-2788`).
4. **Serve.** At or after the date, as the plan's Check once block (the commitment path that exists), cold, tools refused, burned at first serve, blind-graded. Re-check exposure at serve (`teacher/probes.py:417`'s topic-wide reveal check): an LO re-taught or a solution shown since the commitment makes the check `exposed`, recorded, not served.
5. **Retire** after its answer; never a practice item, never served again, never a delayed-check candidate again (FG1 §4.2 doors).
6. **Fail honestly.** A generation still failing at the due date (plan down, refusals) is `missing` with its reason, shown as such; the commitment stays visible on the lesson's record.

**Rules this amends** (Opus): `delayed_checks.candidates`' exclusion of generated probes (`delayed_checks.py:62-70`, "never a delayed check"), `teacher/delayed.py`'s "the teacher never authors its own", and FG1 §4.2's lifecycle, which has no rule for an item reserved for days with no hypotheses attached. TE6 amends all three in its landing, with FG1 §4.2 gaining the `lesson_delayed` origin's reservation rule (reserved from admission to serve or expiry; refused by every other door).

**Vault item or generated: a logged draw, not a rule** (Opus). A single-use generated item is never calibrated, so its likelihood falls back to the LO's default item parameters (`learner/lesson_weight.py:784`); if generated items run systematically easier or harder, that offset would be absorbed into the lesson weight `η₀` with no way to separate them when every lesson outcome is generated. So: where a vault candidate exists, the check's source is a randomized draw between vault and generated, propensity logged on the commitment, seeded 50/50 (owner may set it, Q2); where none exists, generated. The weight's likelihood gains a **per-source difficulty offset** (`δ_gen ~ N(0, 0.5²)` on the logit scale, basis `simulation`, centred on no difference), learned from the draws. This also answers v1's open choice without a rule.

### 7.3 What a generated delayed check is evidence of
- It is a valid "unseen item of the same LO" for §12.1's weight and §12.2's pool **when** it passed the independence check and exposure was re-checked at serve. A new id alone is not enough (Astra).
- It is **not** an RO5 randomized check: RO5's assignment is drawn independently of the action draws (`router_objective/checks.py:132`). Lesson-triggered checks are self-selected; they are labelled `delay_source = scheduled` in EP's facts.
- **RO5 is starved by the same scarcity, and lesson checks cannot fill it.** RO5's eligibility reuses `delayed_checks.candidates` (`objective_inputs.py:485-508`), so LOs with no unseen vault item get no randomized check (Opus). A lesson's generated check is never eligible for RO5: its administration depends on an accepted lesson, and RO5's draw may read only the date and the eligible set (`router_objective/checks.py:3-8`; Fable); `lesson_delayed` items stay withheld from RO5. Whether RO5 gets **its own** generated items, authored for an LO that RO5's draw has already picked and independent of any lesson, is owner question Q2a (Opus recommends it; Fable notes that until then lesson LOs stay at `r_L = 0` in RO5).
- It feeds AD as an ordinary cold attempt on the LO; its generation provenance is an attempt fact.

### 7.4 The router credits checks that never happen (a defect today; fixed first, in TE5)
Each committed check in a rollout applies a full practice dose at mass 1.0, with no minutes charged and regardless of whether the learner returns (`router_objective/rollouts.py:844-849`), and the offer always commits one retention check on the offered LO (`daily_plan/lesson_offer.py:331-332`) whether or not any question exists. On arxiv_v2 that check happened 0 of 24 times, so every lesson offer has been valued with free practice it never got (Opus, Astra). The `commit_u` streams also wrap at 8 slots (`slot % 8`), which per-node commitments would hit.

**Fix (TE5, a router successor, before anything multiplies commitments):** a rollout commits a check only with the probability it is actually served, learned from receipts (seed: whether `delayed_check_words` finds a question today, then the realized share of commitments answered cold, Beta-binomial, basis `legacy` at the current all-or-nothing rule); its minutes are charged on the objective's clock at the Check once block's duration; its answer happens only on a simulated return; one `commit_u` stream per commitment. Ledger row to open with the fix.

---

## 8. Multi-session lessons, and the lesson as the router sees it (TE8)

### 8.1 The problem
To the router a lesson is atomic. The offer record carries one LO (`daily_plan/lesson_offer.py:342-348`, `daily_plan/objective_inputs.py:620`: `item_los=(offer["lo"],)`), one scalar mass (`router_objective/types.py:144`), one pooled duration with a fixed log-sd (`lesson_offer.py:61`, `:171-185`), and one retention check that the rollout credits whether or not a question exists (§7.4). The rollout's `LESSON` branch already loops over LOs (`rollouts.py:633`); the narrowing is in the offer (v1 §15.1a said "each target and goal LO"; the as-built narrowed it to one). A real lesson teaches a plan the teacher writes over the goal LO and its prerequisite closure (4 nodes on 4 LOs in arxiv_v2's first lesson), nodes close `landed`, `taught`, `held` or `uncertain`, and AD records a dose only for landed/taught nodes (`adaptive_difficulty/lessons.py:10`, `:70`).

Across sessions, more exists than first appeared: the brief's `last_lessons` already reads earlier lessons over the goal LO and its closure, with node summaries, recaps (each through `admitted_recap`) and delayed-check results (`teacher/brief.py:600-625`, `:916`), and TE2's `where_you_left_off` (`teacher/te2.py:131`) reads open lessons too. What is missing is order across LOs, a date, the router's view of a lesson's real scope, and anything for open lessons.

### 8.2 Three independent reviews (2026-11-20)
The first draft (A: the arc is the deliverable path plus receipts; B1: a multi-LO lesson action; B2: "next on the path" as one more candidate; B3: arc position read by the lesson window; C: an arc header in the brief; D: generated delayed checks) was reviewed by Fable, Codex Astra and Opus (high) against the code, independently. Their reports are in `docs/reviews/teacher-v2-arc-reviews-2026-11-20.md`. Where they agree:

| Point | Verdict | Why (the reviews) |
|---|---|---|
| A | **Wrong as a definition** (Fable, Opus); bind revisions (Astra) | arxiv_v2 has 0 deliverable resolutions against 9 lessons, so an arc defined by the deliverable is empty for every lesson taken |
| B1 | **Right direction, inflates lessons as a one-line change** (all three) | every LO would get the full mass with certainty, the same `gamma_z` draw, RO6's correction once per LO (`rollouts.py:657-662`), at the minutes of one pooled lesson; closure LOs outside goal scope get `undated_use_density` just for being candidates (`objective_inputs.py:770-771`); with no prerequisite coupling in the rollout, prerequisites are valued as independent end uses |
| B2 | **Wrong about the entry point** (Fable, Opus) | exactly one offer reaches the objective, pre-selected by TE1b's staged `log P(accept) + log(1−p)` (`lesson_offer.py:340-342`, `router/lesson_suggestions.py:624-634`), which sees no deadline: a quiet routing rule and a second place to edit. And "valued at the deliverable's deadline" is not new: a deliverable is a `Goal` whose `facet_scope` becomes dated uses (`objective_inputs.py:92-118`) |
| B3 | **Drop** (all three) | the window is lessons since the last graded attempt per facet, reset by any graded attempt (`rollouts.py:563`, `adaptive_difficulty/state.py:353`), fitted by AD; an arc mostly teaches different LOs; redefining it breaks TE3a's one learned quantity; arc position would be a number with nothing to learn it from |
| C | **Mostly exists** (all three) | new are only the ordinal, path-next and the teacher's proposal; the proposal must be read by the next brief alone, never by candidate generation, or the teacher is routing (Fable) and its "next time we'll…" is a promise the router may not keep (Opus) |
| D | **Necessary, with safeguards** (all three) | §7 |
| Open lessons | **Missing** (all three) | 4 of 9 lessons are open; their LOs are excluded from offers indefinitely (`daily_plan/lesson_suggestion.py:238-240`), with no receipt, AD opportunity or checks (checks commit only at close, `teacher/service.py:2166`), and the router cannot offer to resume |
| Sequence modelling | **Not needed** (all three) | the tail is practice-only and LOs independent (`rollouts.py:705-760`), so the objective cannot value order at all; if order should matter, the missing piece is a learned **prerequisite-readiness** term in the lesson effect, not a planner |

### 8.3 The design

**A. An arc is a chain of lessons on overlapping LOs; a deliverable, when there is one, adds order and a date.**
- Lessons belong to one arc when their LO sets overlap (what `last_lessons` already reads). This works today, with no deliverable.
- When a lesson or offer is made under a deliverable, it records the deliverable id and the resolution and path revisions it used (Astra), so membership is never inferred afterwards from LOs when goals overlap or paths change. Several active deliverables each contribute candidates (§B2); none is "the" arc by nearest-first (`deliverable_path.py:1776-1779`, `brief.py:765` today).
- **Coverage is not mastery.** The path's `done` is section-read state (`deliverable_path.py:1084-1091`); a node's `taught`/`landed` is a lesson's report; neither is completion. "Next on the path" means the next LOs not yet taught in a lesson of this arc, never "not yet mastered" (lesson checks never certify).
- After a deliverable's date, its lessons stay an arc on LO overlap; the objective's own treatment of a past goal applies (LearnLoop is a habit).

**B. The router decides one sitting at a time** (reversible block boundaries, the same objective over all active goals, undated uses and continuation; no candidate-specific deadline, `objective_inputs.py:101`).

- **B1. An accepted lesson is a `SEQUENCE` of per-node `LESSON` steps under one acceptance** (Fable). The rollout already walks a sequence's `_steps` and reads commitments from the outer action (`rollouts.py:944-952`, `:970`, `:1029-1032`). Each step has its own LO, mass, minutes and landing time, so a learner stop or a date mid-lesson credits only finished nodes. Needed: `types.py:170-173`'s validation, the `kind == LESSON` tests at `objective_inputs.py:814` and `rollouts.py:1040`, more duration and commitment streams (4 and 8 today, `rollouts.py:146`, `:153`, `:848`, `:952`), and a per-LO mass (`lesson_offer.py:188` already computes one).
- **What the steps are: forecast, not promised.** The candidate's nodes are the offered LO and its closure as the brief would build it (or, under a deliverable, the path's next untaught LOs), each with a **landing probability** learned from receipts (which planned nodes closed `landed`/`taught`), seeded per node role (offered, prerequisite) on the realized arxiv_v2 shares at basis `legacy`, Beta-binomial. A node that does not land in a draw gives no dose and costs its minutes.
- **Minutes per node.** Duration becomes the sum of per-node durations with a learned spread, not one log-normal at a fixed `DURATION_LOG_SD = 0.7`, whose variance term grows with the median squared and penalizes an honestly longer lesson superlinearly (Fable). Seeded so that today's median lesson is reproduced at today's node count.
- **RO6's effect correction once per action**, not once per LO (`rollouts.py:657-662`; Fable, Opus); a sequence gets it on the whole.
- **Closure LOs enter the population only as what they are:** a prerequisite LO outside every goal's scope gets no `undated_use_density` of its own from being a lesson node (`objective_inputs.py:770-771`); its value reaches the goal LO only through the **prerequisite-readiness** term below, and until that term exists, not at all. This is honest: today the model cannot see why a prerequisite helps.
- **Prerequisite readiness (deferred, §16):** a learned term in the lesson effect on an LO, as a function of its prerequisites' state, seeded at no effect (basis `simulation`), learned from lessons whose prerequisite nodes landed versus not. Built when the report shows foundation lessons undervalued against their realized outcomes.
- **B2. The objective values lesson candidates directly.** TE1b's staged score stops pre-selecting the single offer. The support gets, per boundary: the top lesson candidates by TE1b's acceptance model (its sensor role, not a filter), plus **one path-step candidate per active deliverable**, plus **resume candidates** (D below), within a size cap that is `keep` (computational: rollouts per decision). Each is valued by the objective and drawn by the logged mix with exact propensities. No candidate is forced; the router may prefer practice, a follow-up or nothing.
- **Acceptance gains size and continuation.** TE1b's design vector has no scope term and normalises `minutes_short` to the fixed 15-minute card (`lesson_suggestions.py:282-298`). Add `log minutes` (the candidate's own forecast), `continuation` (resume or path step) and `deliverable` indicators the way `_open_unprompted` was added without moving old posteriors (`lesson_suggestions.py:331-340`), seeded at no effect. The card shows the candidate's real minutes. Declines stay per offered LO (`lesson_offer.py:88`); a path step's decline also counts against its deliverable's next step.
- **The daily ceiling** (`ceiling_per_day`, 3, `keep`) counts lesson offers of every kind; a resume offer counts too.
- **Identity:** `OFFER_VERSION`, the definition hash and RO6's `lesson` indicator move: one change point, recorded.
- **B3 is dropped.** The per-facet window keeps AD's meaning.

**C. The brief gains only what is new:** the lesson's ordinal in its arc, the deliverable's sentence and date and its path's next LOs when there is a deliverable, and the previous lesson's **proposed next session** (the teacher may write one at close: an outline with LOs, logged on the receipt as the teacher's proposal). The proposal is read **by the next brief only**, never by candidate generation or the router, and never shown to the learner as "next time we'll…" (Fable, Opus). A brief version bump.

**D. Open lessons resume, and leave partial records.**
- **A resume candidate**: an open lesson is a candidate ("continue your lesson on X", its remaining nodes as steps, the duration of what remains), valued and drawn like any other, on Today and at plan boundaries.
- **A partial receipt at each session end**: when the learner leaves a lesson (the lesson screen loses focus for good, the app closes, or `lesson.turn` is not called again that local day), a partial receipt records the nodes landed so far; their delayed checks are committed then (§7.2 step 1), and AD's sweep reads landed nodes from it. Nothing closes a lesson on a timer (v1 §11.8); a later close supersedes the partial receipt's open nodes, never its landed ones.
- The offered-LO exclusion for open lessons (`lesson_suggestion.py:238-244`) becomes "offered as resume, not as new".

**E. Reading and lessons on the same path step.** A reading block and a lesson can now teach the same LO from the same sections (C4 feeds the lesson the path's sections), with separate AD dose windows and no cross-diminishing (Fable). TE8 does not invent a cross term: it records, on the lesson's receipt, which of its sections the learner read since the LO's last lesson or graded attempt (an attempt-fact-style record, no window constant), so AD's report can show whether lesson doses after reading move less, and a cross term is added only if they do.

**F. Making deliverables.** A deliverable must be easy to make from where lessons start: when a "Teach me X" or typed goal resolves to more LOs than the teacher's plan covers in one session, the first turn offers "make this a goal or project?", a choice, never automatic; C0's resolver and `create_goal_lo` do the rest. **Owner action:** create one in arxiv_v2 so C0-C4 run on real data before TE8.

### 8.4 Regressions TE8 must add
- **Eve of exam with a multi-node lesson** (Fable, Opus): `tests/test_te3b_value.py:66` pins a one-LO lesson. Add a multi-node lesson whose committed checks fall before the exam: it must not beat cramming because of free checks (closed by §7.4) or because N doses cost one lesson's minutes (closed by B1's per-node minutes).
- A lesson stopped after its first node credits that node only.
- A prerequisite LO outside goal scope adds nothing until prerequisite readiness exists.
- RO6's correction applied once per lesson.
- Resume candidates appear for open lessons and only for them; a resumed lesson's partial receipt is never double-counted by AD.

---

## 9. Entries into a lesson

| Entry | Today | Change |
|---|---|---|
| Learner: "Teach me X", Reader "Teach me this", "Learn something new" | built | typed goals may become deliverables (§8.3) |
| Router: Today-open card (TE1b) | built, only where the objective doesn't serve | — |
| Router: plan-block offer (TE3b), competing with follow-ups (IH2) | built, one offer pre-selected by TE1b's staged score | several lesson candidates valued by the objective: top TE1b candidates, one path step per active deliverable, resume candidates (§8.3 B2, D) |
| After a miss, "This looks like something to learn" (IH) | built | — |
| Teach hand-offs from a diagnostic check (`from_check`) | built | TH-3 and TH-4 fixed (K9.1, the UX audit) |
| Notebook requests ("explain why…", facet well, Show me) | — | notebooks are a medium, chosen in a second logged draw (§10.3) |
| Chat | — | MCP v2 M6 (§13) |

---

## 10. Notebooks: what changes for the teacher (NA4's teacher half)

`spec_notebook_activities_v1.md` adds marimo notebooks (a sandboxed native server per session, wigglystuff widgets, a LearnLoop theme), masked cells as items, mutant-based diagnosis and an authoring harness. Its §9 gives the teacher and the repair model verbs on notebooks. This section is the teacher's side; NA stays the owner of the runtime, the contract, the harness and the measurements.

### 10.1 The toolset, before and after

| | Today | With notebooks |
|---|---|---|
| **Read** | `read_source`, `find_sources`, `find_practice`, `read_history`, `read_note` | + `nb_observe` (cell map, a cell's code, outputs, errors, variables, dependency graph, widget values, commit snapshots, interaction log), under the existing one-follow-up bound; + NA's read API shared with the author (§10.4) |
| **Show** | `visual` in-turn, tiers `grammar` and `sketch` | + `nb_request` (start or extend a topic notebook section by a durable job; the turn never waits; it arrives like a rich figure); `LESSON_TIERS` unchanged for in-turn figures; data-only `live` displays join `LESSON_TIERS` after NA1 |
| **Act on the learner's work** | none | `nb_edit`, `nb_set` (a widget value), `nb_reveal` (a reveal unit), `nb_scratch` (a disposable worker on a permission-filtered snapshot; quoted numbers marked "computed") |
| **Check** | `pose_check` (minted lesson check), `serve_probe` (generated cold probe), `forecast` | + `nb_commit_point`: the teacher creates a commit point; **only the learner commits** (NA §6.3); a commit is one attempt with a joint likelihood, `in_context` coldness, never certifying |
| **Plan** | `write_plan` | nodes may carry a planned notebook section (§9.12 entry 4) |

All of these are actions in the one turn schema (§4.2) under the `notebooks` capability: one entry each, not seven times eight classes. NA §9.2's "in all eight turn classes" and NA4's "in all four schemas" are both replaced by §4.2.

### 10.2 What it changes in how a lesson works
- **Edits the learner can read.** Teacher edits apply to the learner's notebook as highlighted diffs with a required one-line reason, one-click revert, full history; edits to the learner's own solution code arrive as proposals (NA §9.3, owner decision 8). Assistance follows executed dependencies: a commit whose inputs include teacher lines is assisted (NA §9.3).
- **Commits are a second kind of lesson check.** An in-notebook commit inside a lesson is assisted, in-context evidence like a lesson check. NA's open decision 9 (one observation stream with a learned per-kind weight generalizing `lesson_weight`) is the clean form; this spec recommends yes, so a lesson check, a lesson commit and a follow-up credit are kinds of one family with per-kind offsets, each learned from later cold outcomes.
- **Lesson-time diagnosis gets an instrument.** Mutants (NA §8) classify a code commit by behaviour, which is exactly the "explanation didn't land vs misconception survived" separation §6.3 wants, with a likelihood rather than a reading. Commit-level diagnoses go through §6.3's path at the same `ω` family with their own offset.
- **Delayed checks can be masked cells on fresh surfaces.** A notebook-taught node's delayed check may be a `masked_cell` item on a fresh seed served outside the notebook (`standalone_cold`, NA §7.4), generated by §7.2's job with the notebook's key as its checker: a stronger grader than a free-text rubric where the topic is computable.
- **Visuals arrive asynchronously.** Rich visuals arrive through topic notebooks, appended when ready, never blocking a turn (NA §9.9). The lesson links its sections; repairs after a miss are appended to the facet's topic notebook.
- **"Ask about this" on a cell goes to the tutor,** not the teacher, consistent with the Nov 14 rule (a question about what is on screen). Inside an open lesson, the question and answer are passed to the teacher's next turn as context.
- **Implementation teach-back** questions inside lessons follow `spec_implementation_teachback_v1.md`'s one question service (NA open decision 11).
- **The Manim tier.** If notebooks retire the `manim` rich tier (NA decision 12), lessons are unaffected: `manim` is not a lesson tier.

### 10.3 Medium is a second draw
NA §9.13: the router picks the learning target, then a second logged draw picks the medium: text lesson, new notebook section, reopening a section, or a plain item. For the teacher this means a lesson offer may arrive as "a notebook lesson": the same lesson row and brief, with the `notebooks` capability on and a planned section. TE8's lesson candidates (path steps, resumes) and NA's medium draw compose: target first, medium second, each with its propensity.

### 10.4 One read API for teacher and author
NA §11.7 gives the notebook author `read_evidence(facet)` (EP's claim card), `read_concept`, `read_misconceptions`, `read_exposure`, `read_topic_notebook`, `find_sources`, `read_history`. The teacher should read through the same functions: its `read_history` and `find_sources` already exist; it gains `read_evidence`, `read_misconceptions`, `read_exposure` and `read_topic_notebook` (as read actions under the one-follow-up bound). One implementation, two callers, one protection predicate (G6).

### 10.5 Guardrails kept for the teacher (NA §14)
The key and cold-eligible masked values never reach the teacher's context; the teacher cannot submit learner evidence; commits are frozen and logged before any reveal; an edit that would rerun a cell downstream of an open mask waits until that mask's commit is frozen; held-out checks on every authored string.

### 10.6 Fix in NA when this lands
NA §9.12 lists `cold_failing` among the suggestion reasons; the owner removed that gate (IH decision 4, `mvp-0.55`), although the reason constant remains in `router/lesson_suggestions.py:94`. NA should say so.

---

## 11. AD and the router (carried, with TE6/TE8's changes)
- AD reads lessons read-only: TE3a's `lesson` opportunity per landed/taught node, its curve, its report row and auto-flag; SG2's cause-split slopes. A graded lesson check is never an AD attempt.
- The objective values lessons through RO4's lesson interface plus TE3a's curve; TE5 stops crediting checks that never happen (§7.4); TE8 makes an accepted lesson a sequence of per-node steps with learned landing probabilities and per-node minutes, and lets the objective value several lesson candidates (§8.3).
- The difficulty scalar's retirement: the delayed-check picker still pitches vault items by `b` (`teacher/checks.py:129,153`). With generated checks (§7) the picker serves only when vault items are preferred; the refactor's replacement for `b` covers it there.
- AD memory (`spec_ad_memory_v1.md`) owns `S_eff`; its report compares plain `S` and `S_eff` on the lesson's delayed checks. TE1's `stability_inputs` log is its input.

---

## 12. Protection, cost and transport (carried)
Unchanged from v1 §9.3, §17 and the TE1 as-built note: guards on every learner-facing field; the brief records the vault's protection state and a change ends the lesson `protection_changed`; one durable per-lesson spend envelope; plan route by default; `teacher.metered_price_per_million` gates OpenRouter offers; the per-lesson cap `teacher.max_lesson_cost_usd` is set from one measured dry-run lesson (**owner action, open**). New spend from this spec, all on the plan route: TE6's generation and independence check per delayed check (two to three calls per landed node, from landing to the due date), TE7's diagnoses (a few a week), TE8 none (no new model call; coverage is learned from receipts).

---

## 13. Chat lessons: inside MCP v2 (owner 2026-11-20)

Chat lessons are specified in `spec_mcp_v2.md` stage M6, not here. v1 §16's TE4a-c and its dependence on C1a, C1b and C2 are superseded. What the teacher side must supply, and what M6 must settle:

**The teacher supplies:** the doctrine's chat edition (our own public text, versioned on the receipt); the brief as an EP rendering for a chat consumer; lesson rows and receipts with `driver = 'chat:<host>'` (the CHECK already allows it); lesson checks graded by LearnLoop's blind grader at §6.1's mass plus a learned chat offset (v1 §16.1: seed N(−0.5, 0.5²) on the logit scale, basis `legacy`, kept); delayed checks served in the app or through M3's chat practice at its learned per-channel weight.

**M6 must settle (owner questions, carried there):**
1. **Who talks.** v1: the host model is the teacher and LearnLoop's teacher never runs. MCP v2 §3.3 exposes `lesson.turn` (which runs LearnLoop's teacher) yet says lessons come in "for their checks and records, not for the talking". Recommendation: the host talks; M6 exposes a thin chat-lesson handler (open with brief and doctrine, pose and submit check, close), not `lesson.turn`.
2. **§16.2's integrity list** (answerer attestation, refusing `find_sources` while a check is open, a relay field, an expiry) against the owner's Oct 25 "MCP anti-cheating dropped" and Nov 10 "measurement-validity guards only". Recommendation: drop the list; keep the chat channel's learned weight, the "never certifies" rule and exam/held-out exclusion; an MCP App answer box (MCP v2 Q11) records who typed.
3. **Where a chat lesson counts for AD:** a subkind of `lesson` or MCP v2's proposed `chat_explanation` kind (its Q12). Recommendation: a chat lesson is a `lesson` with a `chat` driver subkind and its own curve; `chat_explanation` stays for explanations outside a lesson.
4. `external_chat` is replaced by `chat_live` / `chat_import` (MCP v2 Q13) for learner text from a chat lesson.

---

## 14. Stages

Tags and migration numbers are claimed at landing. Every stage: fakes only (`StructuredClientFake`, `tests/teacher_fakes.TeacherFake`), no model call; targeted tests while iterating; the landing gate once; memory-capped runs; no kill switch (owner, Nov 16).

| Stage | What | Persisted meaning | Depends on |
|---|---|---|---|
| **TE5: consolidation and the check-credit fix** | §7.4 the rollouts credit a committed check only with its probability of being served, charge its minutes, one stream per commitment (first: a defect today); §4.2 one turn schema with capability sets; §4.3 compaction; the TE2 leftovers (the teacher's `create_goal_lo` action, the library lookup before a new topic); L4-2 | Router successor for §7.4; pure move (AST/golden) for the schema; L4-2 a tag on `lesson_weight` | none |
| **TE6: generated retention checks** | §7.2-§7.3: commitment at landing with its states, generation from landing, screening at close, overlap + manipulation audit + Decider reveal judgment, the vault-or-generated logged draw and `δ_gen`, serve, retire, honest failure; the FG1 §4.2 and `delayed.py` amendments | Teacher successor; migration for the origin CHECKs and commitment states | FG1 (built); the reveal-adjudication step (else its lexical stand-in, recorded as such) |
| **TE6b: generated transfer checks** | §7.2 step 1's transfer commitment, with criterion targets | Teacher successor | TE6 has run |
| **TE7: lesson checks to the diagnoser** | §6.3: diagnosis on lesson checks with the teaching transcript, `taught_then_checked`, `ω`, the after-a-miss box in lessons | Successor (diagnosis inputs and a DERIVED family) | after-a-miss spec (built, D1-D4), EP0 facts for the label |
| **TE8a: open lessons** | §8.3 D: partial receipts at session end, checks committed for landed nodes, resume candidates | Teacher successor (AD reads partial receipts) + router successor | TE6 |
| **TE8b: the lesson as a sequence** | §8.3 B1, B2: per-node `LESSON` steps under one acceptance, landing probabilities, per-node minutes with a learned spread, RO6 once per action, closure LOs without their own use density, several lesson candidates valued by the objective, acceptance size and continuation terms, the real minutes on the card; §8.4's regressions | Router successor (a change point); no migration | TE5's §7.4 fix; TE8a |
| **TE8c: arcs and deliverables** | §8.3 A, C, E, F: arcs by LO overlap, deliverable and revision binding, path-step candidates, the brief's arc lines and the logged next-session proposal, the reading-before-lesson record, "make this a goal?" | Brief version; one migration (binding columns) | TE8b; the owner's deliverable in arxiv_v2 |
| **TE9: notebook verbs** | §10 = NA4's teacher half: the `notebooks` capability, verbs, shared read API, commit points in lessons | With NA4 | NA2, NA3; TE5 |
| **TE10: chat** | §13 = MCP v2 M6's teacher half | With M6 | MCP v2 M1-M3; TE5 |
| **Reveal call site** | §6.2 | With the reveal-adjudication step | that step |
| **Teacher sensor lines** | §5's extensions | With EPf2 | EP |

**Order:** TE5 → TE6 → TE8a → TE8b → TE8c, with TE6b after TE6 has run and TE7 beside TE8 once the after-a-miss build lands; TE9 and TE10 with NA4 and M6. TE5's §7.4 fix is the most urgent item in this spec: every lesson offer is valued today with practice that never happens.

---

## 15. Parity: everything v1 planned

| v1 item | Where now |
|---|---|
| TE0 confidence into contexts and card | Built; moves onto EP4 |
| LP-min claim fixes, lesson-check weight, tap/hedge recalibration, pool λ | Built (TE1) |
| TE1 lesson core, guards, checks, forecasts, reveals, receipt, screen, quick check | Built |
| TE1b router suggestions | Built |
| TE2-log, TE2, TE3a, TE3b | Built |
| Compaction (`teacher.context.compact_at`) | §4.3, TE5 |
| Teacher's own `create_goal_lo` mid-lesson; library lookup before a new topic (Q11) | TE5 |
| Delayed retention and transfer checks; dates by retrievability | Built; generated in TE6 (§7) |
| RW6b's valuation replacing `R*` and the picker (v1 §13) | **Open.** RW6b part 2 landed, but its valuation was specified as EVSI dating, and the owner removed the EVSI-2 shadow selection (Nov 16). `R*` stays a seeded prior until the router objective's own value of a check (RO §8) dates checks; TE6 leaves the hook |
| Lesson checks not run through the split diagnoser (v1 §12) | **Reversed** by the owner: §6.3, TE7 |
| Sensor rendering (track records, frames, `learner_surprise`, `tap_shown`, sensor ablation) | **Moved** to EP Part F (§7a); teacher lines in §5 |
| Router sensor mode (H0/H1/S/C arms) | **Superseded** by the router objective's two-policy mix with scored forecasts (EP §7a.1) |
| `teacher.detour.surprise_run` | **Superseded**: detours are judgment, logged as episodes |
| Liquid stability `S_eff` | **Moved** to AD memory |
| TE4a-c chat lessons, §16.2 chat cold checks and probes | **Moved** to MCP v2 M6 (§13) |
| Teacher-built demos (§22) | **Superseded** by RW5d's sketch tier, then notebooks (§10) |
| Lesson offers after a miss (§22) | **Superseded** by IH2 |
| Change-point variance after lessons (§22) | **Superseded** by TE3a |
| Multi-session curricula (§22) | **Taken up**: §8, TE8a-c |
| Split diagnoser on lesson checks (§22) | **Taken up**: §6.3, TE7 |
| v1 TE5 experiments: doctrine A/B and other randomized teaching arms | Deferred, trigger kept (§16) |
| A within-session fatigue time constant (§15.3) | Deferred, trigger kept (§16); router spec's |
| Lesson-check items joining the practice pool | Deferred, trigger kept (§16) |
| A background fact-check agent | Deferred, trigger kept (§16) |
| A randomized placement arm inside lessons | Deferred, trigger kept (§16) |
| Measurement table (v1 §21) | Carried as v1 §21 with §2's data replacing the census; the teacher report's lines as built |
| Owner actions: the dry-run lesson for the cost cap (Q7); vault upgrades (Q12) | Q7 open; Q12 done for arxiv_v2 (lessons ran at the head) |

## 16. Deferred, with triggers (carried from v1 §22, trimmed)
| Item | Trigger |
|---|---|
| Doctrine A/B and other randomized teaching arms | ≥150 resolved delayed checks per arm reachable within 6 months |
| A within-session fatigue time constant | The router spec's (≥600 logged decisions and ≥60 sessions of ≥10 attempts) |
| Lesson-check items joining the practice pool | Generated delayed checks (TE6) leave >30% of landed nodes without a check over a month |
| A background fact-check research agent | Citation validation rejects >10% of source claims, or the owner asks |
| A randomized placement arm inside lessons | The teacher report shows fewer than one RO5 randomized check a month on lesson LOs while lessons run weekly |
| A learned prerequisite-readiness term in the lesson effect (§8.3 B1) | The report shows lessons whose prerequisite nodes landed undervalued against their realized cold outcomes on the goal LO. Sequence modelling is not planned: the reviews agree one-step valuation suffices |
| A cross-diminishing term between reading and a lesson on the same sections (§8.3 E) | AD's report shows lesson doses after reading moving less than lesson doses without it |

## 17. Owner decisions
| # | Question | Recommendation |
|---|---|---|
| Q1 | Rewrite as v2, with v1 kept as the as-built record? | Yes (this document) |
| Q2 | Generated delayed checks, with a logged 50/50 draw between vault and generated wherever a vault item exists, and a learned per-source difficulty offset? | Yes (§7.2); you may set the split |
| Q2a | RO5 gets its own generated items for LOs its draw picked (never a lesson's)? | Yes (Opus); otherwise lesson LOs stay out of RO5's checks (§7.3) |
| Q3 | Lesson checks to the diagnoser at a learned tempering weight `ω`, still no follow-up workflow? | Yes (§6.3) |
| Q4 | Arcs by LO overlap with the deliverable adding order and a date; an accepted lesson valued as per-node steps; several lesson candidates valued by the objective; resume candidates and partial receipts; B3 dropped; no sequence model? | Yes (§8.3), as the three reviews converge |
| Q5 | Offer "make this a goal/project?" when a lesson's topic is bigger than one session? | Yes, as a choice in the lesson's first turn, never automatic |
| Q6 | One turn schema with capability sets, before notebooks and chat add actions? | Yes (TE5) |
| Q7 | NA decision 9 (one observation stream with per-kind learned weights): yes, so lesson checks, lesson commits and follow-up credits share one family? | Yes |
| Q8 | Chat: the host talks; drop §16.2's integrity list; a chat lesson is a `lesson` subkind? | Yes (§13), settled in MCP v2 |
| Q9 | Owner action: create a deliverable in arxiv_v2; run the dry-run lesson for the cost cap | Yours |

## 18. Checked, and not checked
**Checked in code at `1f9c8de1b3`:** the eight turn classes and action literals (`teacher/contracts.py`); `LESSON_TIERS`; `TEACHER_ALGORITHM_VERSION`, `TEACHER_PROBES_ALGORITHM_VERSION`; the delayed-check picker and its exclusions (`teacher/delayed.py`, `delayed_checks.py:60-80`); the lesson action in the objective (`objective_inputs.py:620`, `rollouts.py:625-656`, `:836-850`); the duration model (`daily_plan/lesson_offer.py:145-188`); `REASONS` in `router/lesson_suggestions.py:94`; the `from_check` brief entry; the arxiv_v2 counts on a backup-API copy (lessons, checks, episodes, receipts' delayed checks, deliverable tables). The Astra review's citations were checked where §7 and §8 rely on them (`delayed_checks.py:70`, `rollouts.py:633`, `:844`).
**Not checked:** the other Astra citations line by line; MCP v2's text beyond §3.3, §3.4, Q10-Q14 and the supersession table; NA beyond §9, §13-§16; whether `teacher.max_lesson_cost_usd` is set in the owner's vaults. No test was run and no model was called.
