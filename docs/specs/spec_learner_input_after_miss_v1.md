# Learner input after a miss (LI)

**Status:** owner's decisions recorded Nov 9 2026 (§11): D2, D3, D4 and the `attempt_type` change decided; D1 open. Built after refactor arc D. Code references are to main at `6c8962ce95`. Arc C and arc D will move or shrink some of these files, so each rule names the concept first and the file second: the build rechecks each path. `spec_instruct_handoff_v1.md` (IH) was read from the main checkout, where it is uncommitted, and is not built at this tip.

## 1. The owner's decisions (Nov 9, verbatim)

> You can also just prompt the user directly for the reason why they got something wrong/what they don't fully understand if they didn't explicitly say it in the question.

> if there is something on the rubric that the learner missed perhaps due to the question wording being unclear, the model should jjust be able to ask a follow up question immediately after about that missing rubric item then appending that to their answer instead of immediately penalizing them

> Misses that qualify are only rubric items the answer never addressed where the wording could plausibly be why. I think its fine to credit it as pretty close to a full success but not exactly. You can build this after arc D

Narrowing hypotheses, approved routes (`refactor_strategy_v3.md` G2, branch `refactor/map`): the learner's own words before the probe; *Show anyway* then marks, with the probe recorded as not independent; marks after the probe, informing future misses. Never an always-shown list. It reweights and never removes from the locked set. The weight of marks is learned, from FG1's agreement report.

## 2. In plain words

A miss can now produce one extra question, of one of two kinds, and never both.

- **"You didn't mention X. What about it?"** The answer skipped a part of the question, said nothing wrong, and the question's wording could be why. The learner sees this before any feedback. If they answer, that part is re-graded with their reply in hand. The grade reads nearly full, the system's records read "nearly, and with help", and it can never count as a cold success. If they skip, the grade stands.
- **"What do you think went wrong?"** On any other miss where the answer didn't already say so. It is a quiet optional box on the feedback screen, while the answer and causes are still hidden. The words go to the model that works out why, never to the grader. It changes no grade.

Items that keep needing the first question get proposed for rewording. Marks and the learner's own words start to weigh on what the router expects each cause to be, by a learned amount that starts at nothing.

On any miss, at most one question is added, and it takes one tap to skip.

## 3. The direct prompt

### 3.1 When it is asked

**A reading, not a count.** The blind grader already returns a `StuckReading` on stuck answers: `describes_confusion` and a verbatim `confusion_quote` (`attempts/stuck.py:152`, checked at `:169`). Under the successor it fills the same reading on every answer below full marks, through a new prompt suffix in the style of `+stuck-v1`. The prompt is asked when all of these hold:

- the answer is a miss: below AD's success line (0.8, `adaptive_difficulty/priors.py:47`);
- the reading says the learner didn't state what went wrong, or its quote isn't verbatim, which errs toward one more optional box;
- FG1's workflow owns the attempt, so there is something held and a diagnosis to feed;
- no rubric follow-up was asked on this attempt (§8's one-question rule).

**Why the grader and not the diagnoser.** The diagnoser runs afterwards in a strictly ordered worker (`learnloop_sidecar/post_attempt_worker.py`), and it is the consumer of these words. Reading first with the diagnoser would mean two diagnoser calls, or a box that appears late. The grader's call has already happened, and the reading is an output of that call, so nothing about the learner reaches the grader.

**It isn't asked** on:

| Case | Why |
|---|---|
| "I'm stuck", empty or with text (`PracticeScreen.tsx:1304`) | The learner was just shown "Write what you can, or what's confusing you". That is this question, already asked |
| Exam sittings; diagnostic blocks (FG1 §3.1) | Nothing interrupts a sitting, and a question mid-block reveals the miss |
| A generated probe's own answer | Its feedback releases at once; marks do this job there |
| Self-graded or deterministic grades; held grades | There is no reading, or no workflow opens (`post_attempt.py:147-156`) |

An embedded cold check does get the box. It can't change the measurement, since the grade is already final and the words never reach the grader.

### 3.2 Held so it can't prime

The prompt appears on the feedback screen, below the verdict and criteria, while FG1 §6.0 holds the worked answer, causes and repairs. To keep them held for as long as the box is open, **a pending prompt defers the diagnosis**: the job releases itself with a new reason, `learner_input_pending`, through the worker's existing not-ready path (`diagnosis/split/jobs.py:405`, `:758`), refunding the budget as that path does. With no hypotheses yet, the workflow stays pending and holds what it holds. So the diagnoser reads the words on its first and only pass, and no re-diagnosis is needed.

The prompt settles on the first of: Send; *Not now*; Next (which also sends any text typed, so nothing is lost); any later serve on any device; the startup sweep (beside `expire_clarifications`, `ops/startup.py:53`). No timer. If the learner walks away, nothing is waiting on the job. FG1's `next_item_wait_seconds` starts at settlement, so Next never waits on the learner's own box. Criteria on screen may shape the words. That's acceptable: the words are an opinion, not a measurement.

**What it looks like, including to a first-time learner:** one line, one box, two ways out.

> What do you think went wrong, or what isn't clear yet? *Optional. This doesn't change your grade.*

*Not now* is one tap, and Next works too. First-time learners see exactly this: there is no tutorial, and nothing says "hypothesis" or "diagnoser".

### 3.3 Where the words go

- **Stored** in a new RAW_LEDGER table `learner_stated_reasons`: attempt, text, surface, disposition (`answered`, `dismissed`, `ignored`), time.
- **To the diagnoser** as an attributed block, in the shape of `learner_marks` (`diagnosis/split/context.py:119`, `:164`; `split/live.py:199-213`), on this attempt and as history on later ones.
- **To the learner-text gaps pipeline** as a new source (`diagnosis/text_gaps/sources.py`), per the Oct 12 rule; **to the hypothesis weights** through the diagnoser's fit reading (§7); **to the router's LLM card** as the learner's own statement, beside marks (`daily_plan/router_card.py:703`).
- **Never to the grader.** `BlindGradingContext` has no field for it (`attempts/blind_grading.py:1-17`). **Never to AD's state, evidence or certification:** A12 limit 1 keeps answer text out of AD's state, and this is answer text.

### 3.4 Other questions on the same screen

- **Stuck text** stays as it is, and its `stuck_confusion` signal is unchanged.
- **The eliciting question** (`FeedbackScreen.tsx:280`) is a repair, so it is held until release. The prompt settles before diagnosis, so the two can't share a screen.
- **IH3's "Something else would help"** stays one quiet link. It asks what would help next; this asks what went wrong. They write to different tables, and neither pre-fills the other.

### 3.5 Watching the skip rate

`learnloop data-capture report` gains a section (`ops/capture_report.py`): asked, answered, dismissed and ignored; by device; by position in the session, which is the nearest thing to "tired" we record; and, for answered ones, how often the words' fit agreed with a discriminating probe. There is no throttle. A rate rule would be a made-up number, and hiding the box would hide the signal, which is `clarification.py:60-65`'s reasoning too. The response to a bad number is the owner's: the kill switch or a change of wording.

## 4. The rubric follow-up

### 4.1 Who judges

**The blind grader proposes, and a validator disposes.** The grader has what the judgment needs and nothing else: item, rubric, this answer. It extends the A8 request (`ClarificationRequest`, `attempts/ai_contracts.py:240`) with a reason `unaddressed_rubric_item`, a list `criterion_ids`, and `wording_quote`: the stretch of the question that could be read as not asking for this, verbatim, or null if the question never mentions it. It also marks the omission's attribution `validity_scope = interaction_context`, the existing word for "the presentation rather than the learner's knowledge plausibly produced the failure" (`blind_grading.py:372`).

`_validated_clarification` (`attempts/grading.py:1744`) gains a fourth trigger, `unaddressed_criterion`. **This amends A8's bound by the owner's request:** this trigger needs no hedged grade. The three old triggers are untouched. The validator drops the request unless every check below passes, and the model can't argue past them:

| Check | Reads | Why |
|---|---|---|
| Switch on, tag reached, surface not on §4.6's list | Config, attempt | |
| Any score, including at or above AD's 0.8 | Grade | Owner's D2: no cut-off decides the asking. At or above the line a credit changes only the visible grade (§5) |
| Some criterion earned points, and the answer isn't stuck or empty | Evidence rows | If nothing was addressed, wording isn't the plausible reason; this is a plain miss |
| Each named criterion has 0 points and isn't marked unverified | Evidence rows | "Never addressed" |
| **The answer says nothing wrong:** no fatal error; final answer not `differs_from_reference`; no attribution in force with a verbatim quote from the answer (`grading_support.py:564`); no first divergence anchored anywhere but `missing_required_step` | Grade | The owner's "never addressed", read at the answer level (D1) |
| Attributions on the named criteria say `interaction_context` | Grade | "Wording could plausibly be why". `item_contract` is different: it means the item is defective, goes to machine review (`grading.py:1277`, `:1581`) and gets no question |
| `wording_quote`, if given, is verbatim in the question | Item | Item repair reads it (§6) |
| The question passes §4.2 | Text | |

Each drop writes a record with its rule (§9.5), so "why wasn't I asked?" has an answer. The A8 validator's silent drop stays for its own triggers.

### 4.2 Not giving the answer away

1. **The model has nothing to hand over.** The wire model has no expected-answer field (`ai_contracts.py:240-253`). The prompt rule: name the part of the task that went unaddressed, never its content; no yes/no question; nothing a one-word "yes" could answer.
2. **A machine check.** `practice_leakage.check_leakage` (`content/authoring/practice_leakage.py:180`, the six-word shingle and distinctive-number gate), against an inventory of the expected answer, worked solution and criterion text. A match drops the request. It catches reproduced wording and numbers, not a paraphrase, as FG1 §8 says of the same gate.
3. **The reply must add something.** The re-grade awards only what the learner's reply states beyond the question's own words. The route rule already reads "the learner's reply, never the machine's question" (`grading_support.py:619-634`).
4. **What's left is priced.** A cue that survives all of this is why credit is below full, and the discount is learned from cold results (§5).

**No reveal row.** The question discloses no more than the criteria the verdict screen shows at once (FG1 §6.0), so it writes nothing to the reveal ledger, and a later probe's independence check (`attempts/reveal_ledger.py:270`) isn't touched. An item whose criteria the reveal rules hold back isn't eligible.

### 4.3 When

Before feedback, not on the feedback card, so the learner hasn't been told the answer is wrong. This is a new step between submit and the feedback route (desktop `app/App.tsx:2094`; phone `apps/learnloop-mobile/src/App.tsx:792`, `practice/QuestionScreen.tsx:364`). Submit's reply carries the question and nothing else about the grade. The step doesn't call `get_feedback`, the door that writes display exposures (`learnloop_sidecar/handlers/feedback.py:270`, `:829`). The first `get_feedback` on the attempt settles a pending follow-up as `ignored`, because the grade is about to be shown and a question after it would be primed. A later serve and the startup sweep settle it too. A pending follow-up holds back the rest of the post-attempt pipeline (`run_post_attempt_pipeline`, `attempts/post_attempt.py:89`: the workflow at `:165` and the diagnosis) until settlement, under the existing resumable completion record, so neither runs on a grade that's about to change. A skipped follow-up then opens the workflow as usual, and §8's rule stops the prompt. A8's hedged-grade questions stay on the feedback card (`FeedbackScreen.tsx:1392`).

### 4.4 How many

**One, from structure.** The proposal has one `clarification_request` field, the table has `UNIQUE(attempt_id)` (migration 142), and the re-grade's prompt says not to ask again (`blind_grading.py:403`), so a second request is dropped (`clarification.py:162-166`). A8 and this channel share that one slot. One question may name several criteria only when one wording gap explains them. A second, separate gap stays missed, with no made-up cap to tune.

### 4.5 Appending, and the re-grade

**"Appended" is how it reads, not how it's stored.** `practice_attempts.learner_answer_md` never changes. The exchange travels in the grading context, as A8's does, not spliced into the answer (`attempts/regrade.py:168-174`, `:193`; `blind_grading.py:140`), because first-divergence quotes are verbatim against the answer and the context hash attributes the grade to the exchange. Feedback and the diagnoser show it as labelled parts: *Your answer* / *Follow-up: …* / *Your reply*. The diagnoser doesn't see A8 exchanges today (nothing in `diagnosis/split` mentions them), so this adds them for both triggers. The blind grader still sees only item, rubric, answer and the exchange.

**One door, one addition.** The re-grade runs through `answer_clarification` and `regrade_attempt`, with one new rule, the **pin**: rows for criteria not named stay at their provisional points, and only named criteria may change. Those start at 0, so `y1 ≥ y0` by construction. A second read of the whole answer can't take points away, which is the owner's "instead of penalizing".

| What happens | Result |
|---|---|
| Answer earns points | New grading epoch through `_publish_regrade` (one transaction: score, rows, blind record, replay). Outcome `credited`; §5's writes in the same transaction |
| Answer earns nothing | No epoch is published. Outcome `no_credit`, and the provisional grade stands. The reply still reaches the diagnoser, so a wrong reply is information, not a second penalty |
| *Skip this* | Outcome `dismissed`. Provisional stands; no grade is written |
| Ignored (leaves; first feedback, later serve, sweep) | Outcome `ignored`. Same, as A8's timeout arm does (`clarification.py:424-433`) |
| Grader down when sent, or re-grade fails | The reply is saved first (`clarification.py:252`), state `awaiting_regrade` or `regrade_failed`. Feedback shows the provisional grade and *Your reply is saved; the grade updates when grading is back*. `resolve_awaiting_regrades` drains it at startup. Next is never blocked |
| Re-grade lands after feedback was shown | The grade updates. The superseding blind record retires the old diagnosis and queues a new one (`regrade.py:478-483`). FG1 §5's rule holds: a late result adds no second intervention |

The provisional grade reaches the ledger at submit, as A8's does, and a credited re-grade replays the topic.

### 4.6 Where it is off

| Surface | Reads |
|---|---|
| Cold checks: `cold_retry`, `certification_cold_probe` (`serve_eligibility.py:85`); RO5's randomized checks (`router_objective/checks.py:64`) | Open task kinds, presentation origin |
| Probes: any `probe_presentation_id`, generated or not; `diagnostic_probe` | Attempt |
| Exam sittings and exam-protected items (`learner_protection.withheld_items`, `learner_protection.py:190`) | Protection |
| Lesson checks, teach-back, self-grades, deterministic grades, diagnostic blocks | Attempt type and source |

**A finding, not an exception:** an ordinary first attempt on an unseen item is also the router's natural cold outcome (`adaptive_difficulty/history_resolve.py:17-24`), and it stays eligible, since that's most of practice. §5's table shows why that's safe: its label can't change. I found no reason to bring the off-list to the owner.

### 4.7 Rethinking the rate watch

`clarification_rate` says a high rate means "machine-resident uncertainty misclassified as learner-resident" and must be fixed machine-side (`clarification.py:25-28`). That reading doesn't fit the new trigger, since a question here is permitted on a confident grade.

- **A8's watch keeps its meaning:** `clarification_rate_counts` (`db/repositories.py:2027`) leaves `unaddressed_criterion` out of its numerator, with threshold and display unchanged.
- **A new watch** in the capture report and Maintenance (`MaintenanceScreen.tsx:987`): asked per eligible miss; answered; credited; per item. Asked often and credited often means the wording is the problem, which is §6's job. Asked often and rarely credited means the grader is calling real gaps "wording", a prompt fault to fix. Neither throttles anything.

## 5. Credit

**The learner's grade shows one thing; the records say another.** Everything below reads one learned number, `ρ`, and §5.1 shows why none of it can become a cold success.

| Part | Receives on a credited follow-up | Source of the value |
|---|---|---|
| **The grade the learner sees** | Named criteria credited; score `y1`; *One part came from your follow-up*. It may read as right | The re-grade |
| **Mastery and facet recall** | The observation at mass `ρ` instead of 1 | `ρ` below, recorded on the receipt and read through the seam lesson checks use (`learner/lesson_weight.py:901`, `attempts/attempts.py:4553`; `facet_evidence_timeline.py:650`'s override) |
| **AD's state** | A soft factor: `ρ·P(Y=2) + (1−ρ)·P(Y=1)` given `η`, floored by §5.1 (D3) | The same `ρ`. AD's update already takes non-point factors: `CENSORED` reads `P(Y ≤ 1)` (`adaptive_difficulty/model.py:73`). No second `γ`; this is one presentation |
| **FSRS** | Rating from `y1`, at most Good, or the item's own one-hint cap if it has one (`fsrs_rating_cap_by_hint`) | Structural: a success with help isn't Easy. The default hint policy has no cap, so this is new. One helper at the five call sites (`attempts.py:4731`, `field/outcomes.py:668`, `instructional/reader_followups.py:582`, `scheduling/review_log.py:108`, `scheduling/evaluation.py:341`) |
| **Certification** | Nothing, for the whole attempt | The existing rule: assisted attempts certify nothing (`causal_activity_policy.py:182`, `capability_mapping.py:263`). Cost: §11 D4 |
| **Router's estimates** | Nothing directly. Its rollouts read AD's belief and FSRS memory, so they move as above. Nothing reads the reply or `ρ` | |
| **Forecast scoring** | The label is unchanged (§5.1) | |
| **Nothing credited, or skipped** | Exactly the provisional grade, at full mass, as an unaided answer | |

**`ρ`: seeded, then learned.** `ρ = σ(η)`, `η = η₀ + u_L`.

- **Seed.** `η₀ ~ N(logit 0.8, 1²)`, basis `legacy`: the centre is `teach_back`'s configured mass (`config/schema.py:1836`), the existing value for "high-quality generative evidence, but in a dialogue, so less than a full independent attempt". The width is the LP spec's rule for legacy priors. I passed over the hint values: the default dampening is empty (`vault/models.py:396-400`), and `reconstruction_after_walkthrough`'s 0.5 follows being taught the answer. `u_L` is the per-LO offset with the τ grid of `spec_teacher_v1.md` §12.1.
- **Learned** with that section's estimator, as a second family with its own posterior in `learner/lesson_weight.py`: only from later cold, unassisted, unprimed first attempts on unseen items of the same LO. The mass applied is the posterior mean as of the re-grade, recorded on the receipt, so replay reproduces it and a past attempt's mass never moves. With rare follow-ups, `ρ` stays near the seed for a long time.
- **"Not exactly" is structural.** The logistic link makes `ρ < 1` with no cap.

### 5.1 Why it can't count as a cold success

**Three locks, any one of which is enough.**
1. **The label follows `y0`, whatever is asked.** Below the success line the attempt's unaided label was already "not a success". At or above it, a credit writes only the follow-up's receipt (below), so the unaided label stays a success and nothing is added to it.
2. **The category keeps that.** AD's category becomes `max(cat(y0, no help), cat(y1, help after work))` (`adaptive_difficulty/outcomes.py:87`), and `unassisted_success` returns 1 only for an unaided `Y = 2` (`:109`); the soft case is its own value, never 2. Reading `y0` from the receipt means a follow-up can't lower a category either, in line with A10.
3. **Below the line, the attempt becomes `hinted_attempt`.** In the re-grade's transaction, with the original type kept on the receipt. Every allow-list of unaided work fails closed: `QUALIFYING_ATTEMPT_TYPES` (`diagnosis/forecast_receipts.py:84`), `GRADED_RETRIEVAL_TYPES` (`field/outcomes.py:236`), `classify_attempt_activity`'s assisted arm (`causal_activity_policy.py:168-186`, read by `diagnosis/scoreboard.py:357`, `certification_cold_probe.py:1477`, `scheduling/intent/serving.py:111`), `goals/forecast_ledger.py:106`. Any reader the build misses treats it as help, not as a cold success.

`hints_used` stays the truth: AD's category reads the receipt, so `help_timing` needs no faked hint.

**At or above the success line (owner's D2).** The attempt keeps its original type and `practice_attempts`' score stays `y0`. `y1` lives on the follow-up's receipt, and the feedback screen and any view of the attempt's grade show it from there. An attempt of an unaided type must never carry a score that help raised: readers of the raw score (AD, field, calibration, forecasts) would take `y1` for unaided work. So this path needs no soft factor, costs no certification credit, and can't flatter a forecast. The build lists every grade display that must read the receipt.

| `y0` | What happened | `y1` | AD's `Y` | Forecast label |
|---|---|---|---|---|
| ≥ 0.8 | Nothing to ask, or asked and skipped, ignored or no credit | `= y0` | 2 | 1 |
| ≥ 0.8 | Answered, credited | shown only, from the receipt | 2 | 1 |
| 0.4–0.8 | Asked; skipped, ignored or no credit | `= y0` | 1 | 0 |
| 0.4–0.8 | Answered, credited | ≥ 0.8 | soft (1 or 2 in `ρ`) | 0 |
| 0.4–0.8 | Answered, credited | < 0.8 | 1 | 0 |
| < 0.4 | Asked; skipped, ignored or no credit | `= y0` | 0 | 0 |
| < 0.4 | Answered, credited | ≥ 0.8 | soft | 0 |
| < 0.4 | Answered, credited | < 0.8 | 0 | 0 |

**The forecast label never differs from what it would have been with no question asked.** So `item_unassisted_success`, `lo_cold_success` (both bindings) and RO's calibration can't be flattered by this channel. They also can't be excused by it: a wording-caused miss still scores as "not an unassisted success", which is literally true.

## 6. Item repair

**Into suspicion.** A credited follow-up counts as `assessment_side_error` in the item's quality state (`attempts/attempts.py:4897`, `learner/recall_coverage.py:689`), with its own reason `rubric_followup_credited` and the existing +0.08. The state reads `y0` for its success and failure terms, so `y1` doesn't also earn `clean_success_on_item`. Skips and `no_credit` add nothing: only credit says the learner knew it and the wording got in the way.

**A finding on the threshold.** The flag needs suspicion ≥ 0.65 and three events (`recall_coverage.py:708-713`), which at +0.08 takes about nine credited follow-ups on one item. One learner won't reach that, so the flag can't be what triggers a proposal. **So the proposal has a direct trigger:** the **second credited follow-up on the same item revision** writes one proposal, deduplicated per revision. Two is the smallest count that means the owner's "repeated", not a tuned value.

**Through the existing path.** A `practice_item` / `update` row in a pending batch, the shape `content/proposals/method_phrasing.py:879` writes, for the owner to accept or reject. Nothing is applied automatically. The writer gets the item, the named criteria, both `wording_quote`s and the exchanges, on a plan route under the existing spend envelope. A statement decided as a source's own isn't rewritten (`rewrites_decided_statement`, `vault/required_method.py`), and for those items the proposal narrows the criterion instead. Past answers keep the contract they were graded under (playbook, Oct 16 rule).

## 7. Narrowing hypotheses

| Route | Surface | State today | What this spec adds |
|---|---|---|---|
| Own words, before the probe | §3's box, or text in the answer itself | New | The box; the diagnoser's fit reading |
| *Show anyway*, then marks | `FollowupPanel.tsx`, `HypothesisMarks.tsx`; `workflow.probe_answer_exposed` marks the probe not independent | Built (FG1c) | The weight only |
| Marks after the probe | Same panel; reaches later diagnoses and the card (`split/history.py:663`, `router_card.py:703`) | Built (FG1c) | The weight only |

Never an always-shown list: no surface here shows causes before release unless the learner asks with *Show anyway*.

**Fit.** When a stated reason or an earlier mark on the topic is in its context, the diagnoser's proposal adds, per hypothesis, one of `fits`, `contradicts` or `silent`. With no such block, its prompt doesn't change.

**The weight.** For the locked set with the diagnoser's weights `p(h)`:

`p′(h) ∝ p(h) · exp(Σ_s β_s · x_{s,h})`

- **`x`** indicates one value per source: `words_fits`, `words_contradicts`, `mark_my_gap`, `mark_partly`, `mark_not_it`. Each has its own `β`, so nobody picks how much *Partly* is worth.
- **`β_s ~ N(0, 0.5²)`**: centred on "no effect", width as `β_c` in `spec_teacher_v1.md` §12.1, basis `simulation`. At the prior mean `p′ = p` exactly, like `w_pref` and RO6's `ŵ`.
- **Learned** from `_probe_agreement`'s pairs (`ops/capture_report.py:304`), independent answers only, with AD's moment-matching step. Route 2's marks are stored and reweight on later misses, but a not-independent answer teaches nothing about them.
- **Never removes.** `exp(·) > 0`, so every member of the locked set keeps weight, by the form.
- **Only the router's branches read `p′`.** The discriminating-observation receipt stays the only channel that moves support for a cause (FG1 §5.1, §7): no factor resolves on this, no belief opens, and certification never reads it.

**It depends on G2.** Today the numeric policy values a probe as one binary result (`router_objective/value.py:886-925`) and has no branches to reweight. G2 brings them, and arc G comes after arc D, where the strategy says the rest is decided. Until G2 lands, the fit reading and marks reach only the LLM's card. If G2 doesn't happen, LI4 doesn't either, and LI1-LI3 don't need it.

## 8. The screens after a miss

**The rule:** between an answer and the next item, **at most one question from us, plus the router's one next step**. The rest is quiet and optional.

| Step | Shows | Decided by | Cost to a tired learner |
|---|---|---|---|
| 1. Follow-up, if licensed | The question, a box, Send, Skip | Grader and validator (§4) | One tap to skip |
| 2. Feedback | Verdict, criteria, held line; the prompt box if §3 asks; the router line; IH3's quiet link | Workflow | Next (also dismisses the box) |
| 3. Next | One of: probe, IH's lesson page, the plan's next item | Router (FG1 §5; IH2: lessons compete in the same draw) | One of these, never two |
| 4. After a probe | Its feedback, held feedback released, marks (optional) | Existing | Next |

Follow-up or prompt, never both. Probe or lesson, never both. A credited follow-up at or above the line is no longer a miss: since the workflow is deferred, it reads `y1` and opens nothing, so the worst path is only the uncredited one.

```
Worst path (skip or no credit):       answer -> [follow-up] -> feedback -> [probe] -> feedback -> next
Ordinary miss, nothing licensed:      answer -> feedback + [box] -> [probe, lesson or nothing; rest released] -> next
Credited, at or above the line:       answer -> [follow-up] -> feedback ("one part from your follow-up") -> next
```

**Desktop.** The follow-up step replaces the practice answer area, with the question and the learner's answer still visible:

```
+------------------------------------------------------------+
|  ...question and their answer, read-only...                 |
|  One more thing before the feedback                         |
|  Your answer didn't say what has to hold for this to work.  |
|  What has to hold?                                          |
|  [ a sentence is plenty                                  ]  |
|  [ Send ]   Skip this                                       |
|  Answer it and this part can count. Skip and your answer    |
|  is graded as written.                                      |
+------------------------------------------------------------+
Send: "Checking..." then feedback. Grading down: feedback, with the saved-reply line.

Feedback on an ordinary miss:
+------------------------------------------------------------+
|  Not yet                                                    |
|  criterion rows ...                                         |
|  What do you think went wrong, or what isn't clear yet?     |
|  [ box                                                 ]    |
|  Optional. This doesn't change your grade.  Send · Not now  |
|  Preparing a question on this...                            |
|  The answer comes after the question.        Show anyway    |
|  Router: ... details            Something else would help   |
|                                                [ Next ]     |
+------------------------------------------------------------+

Phone, the same steps in one column:
+----------------------+     +----------------------+
| One more thing       |     | Not yet              |
| ...question text...  |     | criterion rows       |
| [ box              ] |     | What do you think    |
|                      |     | went wrong?          |
| [      Send      ]   |     | [ box              ] |
|  Skip this           |     | Optional.  Not now   |
|  your answer  v      |     | Preparing a question |
+----------------------+     | Show anyway          |
                             | [      Next      ]   |
                             +----------------------+
```

The phone's flow matches the desktop's: same RPCs, added to the host's allowlist and `apps/learnloop-mobile/src/api/retryPolicy.json`; the follow-up step sits between `QuestionScreen` and `FeedbackScreen`. A prompt or follow-up that's open on one device settles when the other serves. The phone's A8 card (`practice/FeedbackScreen.tsx:230`) is untouched. The UX overhaul will restyle these; what's fixed is the order and the one-question rule. The copy has no "rubric", "criterion", "hypothesis" or "provisional". The desktop's A8 card keeps its existing wording.

## 9. Persisted meaning

### 9.1 Successors and switches

Tags are claimed at landing, after whatever IH and the refactor have added.

| Stage | Successor | Switch (`[learner_input]`, default true) | Off, or below the tag |
|---|---|---|---|
| LI1 | Yes: the grader's prompt, diagnosis timing and the diagnoser's input change for new answers | `direct_prompt` | Grader prompt byte-identical (no suffix); no reading on ordinary answers, box, rows or deferral |
| LI2 | Yes: changes grades and evidence for new answers | `rubric_followup` | Prompt byte-identical; request reason and trigger unreachable; A8's validator as today; no step |
| LI3 | No: a proposal changes nothing until the owner accepts it | `reword_proposals` | No trigger, no rows. Suspicion's reason is LI2's and goes with LI2's switch |
| LI4 | Yes, once numeric reads `p′` | `narrowing_weights` | `p′ = p`; no fit field |

Past rows keep their meaning whatever the switch: replay reads receipts and rows, never config. Turning a switch off settles open items as `ignored`, like FG1's `settle_open_when_off` (`followup_serve/workflow.py:483`). These tags sit above arc D's floor, so D's pruning doesn't touch them.

**No retroactive change.** History has no follow-ups and no stated reasons, so the successor replays history unchanged. **The upgrade needs no whole-vault rebuild.** `learnloop rebuild --shadow --json` on a copy must report zero mastery, facet and scheduling deltas: that's the playbook's item 7, and it is expected to be empty. Effective-default fingerprints as usual.

### 9.2 Proof: four ways, then the shadow

A seeded fixture vault, one topic, an item with a skippable criterion, with fake graders, run four ways: **A**, switches off; **B**, on, with no qualifying miss; **C**, on, asked, skipped; **D**, on, asked, credited. Asserted: A and B are byte-identical in grades, evidence, FSRS, AD state and replies. C differs from A only in receipts. D differs only as §5's table lists. All four give the same forecast labels. Each way is run live and then rebuilt, and the rebuild equals the live state. Owner-vault copies at the landing smoke (`learnloop.db.copies`, never live) show zero deltas; those copies have no follow-ups, so **no real-data proof of §5's effect exists until after landing**.

### 9.3 Migrations

Following `CLAUDE.md`'s migration note, with the `migration_head_<N>` fixture upgraded and its paths updated:

| Table | Role | Change |
|---|---|---|
| `grading_clarifications` | RAW_LEDGER | Rebuilt for the closed vocabularies: reason `unaddressed_rubric_item`, trigger `unaddressed_criterion`; new columns `criterion_ids_json`, `wording_quote`. Its no-update trigger is recreated |
| `grading_clarification_responses` | RAW_LEDGER | Outcome gains `credited`, `no_credit` |
| `rubric_followup_outcomes` | RECEIPT | One per clarification: disposition, provisional correctness and points, original attempt type, `mass_applied`, re-grade revision |
| `learner_stated_reasons` | RAW_LEDGER | §3.3 |
| `followup_credit_weight_state`, `_trace` | DERIVED | Exactly one replayer, as `lesson_weight_state` has (`db/table_roles.py:396`) |
| `narrowing_weight_state`, `_trace` | DERIVED | LI4; one replayer |

Changing `practice_attempts.attempt_type` at credit is an update to a raw ledger column. Regrades already do this for the score (`update_attempt_grade`), and the receipt keeps the original, which is the correction event the playbook's item 2 asks for. I'm naming it because that item's wording says ledgers stay immutable.

### 9.4 Tests

Fakes only; no paid or live calls; the full suite only in the landing gate.

- **Validator:** one case per row of §4.1, each dropping alone and writing its rule; a verbatim wrong claim anywhere stops the request whatever the model says; a fabricated quote doesn't count as located; old triggers unchanged.
- **Giveaway and count:** a question quoting the expected answer or a distinctive number is dropped; a reply echoing only the question earns nothing; a request on the re-grade is dropped; A8 and the follow-up can't both exist.
- **Re-grade:** a re-grade moving an unnamed criterion keeps its provisional points, `y1 ≥ y0`; each row of §4.5 leaves Next working; the reply survives an outage and a restart.
- **Blindness:** the grader's payload has no history or stated reason; its bytes are unchanged with a stated reason present.
- **Cold labels:** §5.1's table row by row through `category`, `unassisted_success`, `history_resolve`, `forecast_ledger`, `scoreboard`, `forecast_receipts` and `lesson_weight`'s qualifying outcome; twin vaults, asked and not asked, give identical labels.
- **Credit:** recorded mass equals the posterior mean as of the re-grade and doesn't move on rebuild; `ρ < 1` under extreme data; the soft factor equals `Y = 1` at `ρ = 0` and `Y = 2` at `ρ = 1`; no second `γ`.
- **Off-list:** each row of §4.6 gets no question, even if the model asks.
- **Prompt:** asked when the reading says unsaid; not for stuck, exam, block or probe; diagnosis deferred while pending and run once; held stays held; Next with text sends it.
- **Screens (vitest, both devices):** the step precedes `get_feedback`, and no exposure is written before it; §8's paths; never two questions.
- **Item repair and narrowing:** the second credit writes one pending proposal, the third none, and a rejected one isn't re-proposed for that revision; at `β = 0`, `p′ = p`; no weight reaches 0; factor support and certification byte-identical with weights on.
- **Switch-off and watch:** golden prompt hash and reply bytes equal the predecessor, in RW5c's style; A8's rate unchanged by follow-up rows.

### 9.5 Why x and not y

If arc B has landed, each writes a `DecisionRecord` (`refactor_strategy_v3.md` §3.2), with codes only and never learner text. If not, the same codes go on the receipts and B's inventory picks them up.

| `kind` | `status` | `rule` |
|---|---|---|
| `rubric_followup` | `chosen`, `refused` | `below_line`, `nothing_addressed`, `criterion_has_points`, `answer_says_wrong`, `scope_not_interaction`, `off_surface`, `leak`, `one_per_attempt` |
| `direct_prompt` | `chosen`, `excluded` | `answer_said_it`, `stuck_already_asked`, `no_workflow`, `off_surface`, `followup_asked` |
| `followup_credit` | `chosen` | Facts: `y0`, `y1`, `mass_applied`, posterior version |
| `reword_proposal` | `chosen`, `excluded` | `second_credit`, `already_proposed` |

### 9.6 Stages

| Stage | Size | Contents |
|---|---|---|
| **LI0** | S | Step 0 before code: recheck paths after arc D; confirm §12's open checks. Read-only count on owner copies of how many past grades have a 0-point criterion with no located quote, reported beside the build; it decides nothing |
| **LI1** | M | Direct prompt: reading, deferral, box on both devices, ledger, diagnoser block, text-gaps source, report |
| **LI2** | L, lands alone | Follow-up: wire and validator, leak check, step on both devices, pin, receipts, `ρ`, AD factor, FSRS cap, type change, suspicion reason, rate watch. One successor, because a follow-up without its discount would be full credit |
| **LI3** | S | Reword proposals |
| **LI4** | M, after G2 | Fit reading, `β`s, branch weights, report section |

LI1 and LI2 may land in either order. If LI2 lands first, §8's rule still holds, as there's no prompt to exclude. IH1 and IH3 edit the same feedback screen, so whichever lands second merges.

## 10. Rules this amends, and where the owner's decisions conflict with them

| Rule | Where | Conflict and resolution |
|---|---|---|
| "A confident grade can never produce a question" | `clarification.py:25-26`, `grading.py:1750`, `ai_contracts.py:254-256`, migration 142's comment, `spec_measurement_efficiency_v1.md` §3.A8 Bounds and `:1251` | **Owner amends it** for this trigger only. All are updated at LI2; the three old triggers keep the bound |
| Principle 8: machine-side uncertainty, including "a missing item contract", is never paid for with learner effort | `spec_causal_attribution_v1.md` principle 8, spec_measurement_efficiency §3.A8 | **Real tension.** Unclear wording is an item-side fault, and the owner's rule spends a learner's question on it. Resolved in the owner's favour, and narrowed: a defect the machine can see (`item_contract`) still goes to machine review with no question; only "could plausibly be why" (`interaction_context`) asks. The note is added to principle 8 |
| A8's revert criterion: a high rate is a grader fault | §3.A8, `clarification.py:60-65` | Split by trigger (§4.7) |
| "The verdict never waits" | `spec_blind_grading_diagnosis_split_v1.md:444` (as amended by FG1); FG1 §6.0, `ux_learnloop_v1.md` Feedback | **The owner's "before feedback" holds the verdict** while a follow-up is on screen. The line gains that one exception |
| A12: no answer text in AD's state; A10: help never penalized | `spec_adaptive_difficulty_v1.md` | Kept. §5.3's category table gains the follow-up row and the `y0` floor, and §5.5 the soft factor; A5 holds, as `ρ` is learned |
| FG1 §7: marks move "no probability until measured" | `spec_followup_generate_serve_v1.md` §7 | Consistent: this is the measuring. `p′` reads only the router's branches |
| "Raw ledgers stay immutable" | Playbook item 2 | §9.3's type change; named there |

## 11. Decisions for the owner

| # | Question | Recommendation, then the owner's decision |
|---|---|---|
| D1 | "Says something wrong": anywhere in the answer, or only about the missed item? Your words name the item; the brief for this spec says the answer. Consider an answer with one wrong claim and a separate clause skipped | **Anywhere.** A wrong claim is a real miss with a real cause to chase, and the probe is the right next step. It also keeps a follow-up and a probe from stacking on one attempt in most cases. **Open:** the owner's Nov 9 note favours a follow-up "anywhere"; that may mean asking about the skipped item even with a wrong claim elsewhere, the other reading of this row |
| D2 | Ask when the answer already reaches the success line (0.8) but skipped a smaller item? | **No.** It's already a success everywhere that matters, and asking adds a screen on a good answer. The cost: that point stays lost on the visible grade. If it bothers you, the alternative is asking with no change to any record but the grade. **Decided, Nov 9: ask at any score,** because no hardcoded value should decide the follow-up; §5 gives the grade-only path. The missed-because-why prompt (§3.1) keeps its own reading of a miss; D2 is about rubric follow-ups |
| D3 | AD's state: the soft factor `ρ·Y=2 + (1−ρ)·Y=1`, or plain `Y = 1`? | **Soft factor.** `Y = 1` is AD's existing "success with help" and needs no new code, but it treats "nearly everything, and supplied the rest when asked" the same as a 40% answer, which isn't your "pretty close to a full success". The factor is one small addition, and forecast labels are the same either way. **Decided, Nov 9: soft factor** |
| D4 | Answering a follow-up costs the attempt's certification credit, including for parts answered unaided, so skipping can earn more credit than answering. Accept? | **Accept for now.** The attempt was below the success line anyway, the learner never sees it, and per-criterion assistance is a bigger change to the capability ledger. A report can show whether it matters. **Decided, Nov 9: accepted.** It applies below the success line; at or above it nothing is lost (§5). The `attempt_type` change to `hinted_attempt` below the line (§9) is also accepted |

## 12. Checked, and not checked

**Checked in code** (read at `6c8962ce95`; nothing was run): the A8 channel, validator, lifecycle and table; blind context and validity scopes; regrade's publication; AD's categories and factor shape; §5.1's allow-lists; `lesson_weight`'s mass seam; quality-state arithmetic; the marks report; job release; proposal row shape; both feedback routes.
**Only read as specs:** IH (not built here), `spec_teacher_v1.md` §12.1's estimator detail, A12's text, `refactor_strategy_v3.md` (arcs B, D, G are unbuilt).
**Unverified, and the build must check (LI0):**

- **Model behaviour.** Whether the grader tells "never addressed" and "wording could be why" apart reliably, and how often it asks, are unknown. No live or paid call was made. Fakes prove the validator, not the judgment. The rate first appears in §4.7's watch after landing. How much a paraphrased question cues is unmeasured too, and `ρ` absorbs it only slowly.
- **Validation of quotes from the reply:** the first-divergence check reads the answer (`grading.py`, `learner_answer_md`), and only the route rule was seen to read the reply. A credited row's quote from the reply may need the same allowance.
- **Other readers of `hinted_attempt`:** `attempts/ability_transition.py:25`, `diagnosis/remediation.py:1355`, `diagnosis/split/history.py:65`, `hints/state.py:352`, and `field/outcomes.py:296, 597` (which treats the type as an independent attempt plus hint factor) were listed, not traced. Field's research arms may need the receipt's mass.
- **Whether the reveal rules hold back any criteria shown at once:** §4.2 assumes the eligibility check can read this; the predicate wasn't found by name.
- **AD soft factor cost:** the update's quadrature takes any one-dimensional likelihood by its form, but I didn't trace its joint factor with rating and timing (`model.py:559`). The soft case may need those sub-arms off, as `CENSORED` has.
- **Latency** of the follow-up's re-grade on screen, and of the longer grader output, is unmeasured. The build reports both. **The fixed values kept** (`SUCCESS = 0.8`, `+0.08`, the 0.65 flag, A8's 0.15) are existing and hand-set: this spec adds no new one, but doesn't fix them.
