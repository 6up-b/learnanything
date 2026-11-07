# Follow-up generate and serve (FG1)

**Status:** FG1 built on `followup/fg1-generate-serve` (mvp-0.45, migration 241; `docs/reviews/followup-fg1.md`); §7's marks and report built as FG1c on `followup/fg1c-marks` (migration 242, no successor; `docs/reviews/followup-fg1c.md`). Owner's decisions recorded, 2026-11-03 (§2, §11). Revised after a read-only Sol review against the code (job 20261103-211904-wVotHw). Code references are to main at `02f7cbec2d`.

## 1. The problem

A learner misses a question. The diagnoser writes several possible causes. Then one of two things happens:

- no suitable item exists, so a need is recorded and nothing is asked;
- an existing item is queued. In split vaults it was chosen at grade time, before the causes existed (`attempts/post_attempt.py:150`, with diagnosis enqueued afterwards; the worker never reruns selection, `diagnosis/followups.py:945`).

Either way the mistake usually isn't addressed, and the learner moves on to the next queue item or to Today. No spec covered this. Three specified the behaviour we are changing (§9).

## 2. The owner's decisions (Nov 3, verbatim)

> Follow up rules should prefer direct generation over looking for a suitable existing item, since generated items will be far more targeted and applicable. auto_generate_on_entry should default to true for all vaults. When a follow up intervention is chosen for a follow up probe, hypotheses are written, then a follow up question should be generated immediately to be served to the user. I think the intended user journey is if after a practice item opens up several hypotheses and the action router decides an intervention, this intervention specifically should be served immediately. Right now the behavior is confusing and the user's mistake isn't addressed and they're just send to the Today queue, which doesn't make any sense.

> The user I feel like could also read the generated hypotheses and offer insight from their own evaluation on what their gap is that we can use to inform later model training (of course this is an imperfect sensor from the user, but it would definitely help. Like being able to mark a hypothesis as more correct or the learner recognizes that this is their gap of understanding. I think textbook first should be a philosophy for generating practice items, but for probes I think generation is superior. The router can keep its "wait" option but I feel like this should also be clear in the UI/UX. The action router's decisions I think should be clear at least for now for debugging and callibration. And yes generated probes should skip manual review and be single use surfaces that do not become practice items later or are ever served again.

## 3. The journey

1. The learner answers and sees the blind grade at once: the verdict and the criteria. The worked answer and the diagnosis text are held (§6.0).
2. The diagnosis job writes its hypotheses.
3. The system picks a lane (§4).
4. The router decides whether and when (§5).
5. The question is generated at once (§4.1).
6. Next opens it. If it isn't ready, Next waits and says so (§6.1).
7. The learner answers the probe, and its answer separates the hypotheses.
8. The held feedback appears, repair follows through the existing path, and the learner can mark which hypothesis fits (§7).

### 3.1 Where the journey doesn't run

- **Exam sittings.** No follow-up or banner between answers. `finish_exam` runs the batch afterwards, which ranks failures worst-first and caps follow-ups at three (`post_attempt.py:300`). FG1 records that eligibility and cap before any generation, so later jobs can't get around the cap. A sitting's own misses can take the probe lane once `finish_exam` has run, inside that cap; nothing interrupts the sitting, since the pipeline runs at its end, and the exam's report shows the feedback, so none is held. A cause or a generated question that reproduces a question still reserved sends that miss to the practice lane (§8). *Amended Nov 4, 2026, the owner's ruling: this replaces the earlier rule that causes written from exam work, or without a complete record in a vault holding exam material, took the practice lane.*
- **Diagnostic blocks.** A follow-up mid-block would reveal that the last answer was wrong (`followups.py:624`), so block completion releases eligibility. If an episode with locked hypotheses is already measuring, it is not replaced.
- **Joint vaults.** There is no live diagnosis job (`diagnosis/split/jobs.py:144`). Selection uses the hypotheses normalization has already written.
- **Surfaces without the pending and skip behaviour** stay on predecessor behaviour: the TUI has its own Next (`tui/screens/feedback.py:655`). FG1 serving is enabled only with that surface's UI. See §10 for the phone.

## 4. Two lanes

| Lane | When | Source of the question |
|---|---|---|
| **Probe** | The diagnosis leaves two or more current concrete rival causes in the selected factor. `H_OTHER` is kept in the set but not counted (`causal_probe_coherence.py:728`) | Always generated, aimed at those hypotheses |
| **Practice** | The cause is known or there is only one hypothesis; or there is no diagnosis | Existing item, then textbook exercise, then generated |

The existing-item chooser no longer runs for the probe lane.

*Amended Nov 4, 2026 (R9, the owner's Nov 3 words: "The router will decide for weak cases."):* a new miss with two or more distinct concrete causes gets a factor on the workflow path, even with no `target_ref`, no repair mapping, a repair aimed at another criterion, or only a trivial error type, since the question is written from the causes and needs no repair class. It owes no mapping, moves no measurement, and closes as `followup_declined` when its question won't be asked. One concrete cause stays on the practice lane. With no plan there is no draw to decline a weak case (§5.1), so it gets its question.

The practice lane keeps the existing chooser and S2b's textbook-first order. One thing changes: a recorded need is now filled automatically in the background, instead of waiting for a click or a CLI command.

### 4.1 Generated probes

Today's two half-paths don't compose. The mint (`probe_instance_generation.py:1117`) never sees the rival causes and commonly writes one generic `correctness` criterion. Commissioning (`causal_probe_commissioning.py:383`, CLI only) writes no question: it needs an existing item, and it derives predictions from criterion targets the mint doesn't supply. Family likelihoods also send arbitrary causes to `other_or_unknown` (`probe_families.py:707`).

So the build adds:

- **One new authoring operation on a frontier LLM,** taking the router's decision and the rival causes. It produces the question, the key, an independently authored criterion contract and a manipulation contract.
- **Reuse of the mint's persistence and single-use handling,** then commissioning of that explicit item with observation-free prediction bundles.
- **A defined presentation binding.** Generic family rows are not the causal measurement. Bundle features are limited to what the existing sensor can read (`causal_orchestrator.py:2796, 2904`), or the build names a new sensor.
- **The pinned offer, run automatically.** Plain queue insertion would lose the `causal_probe` pin classification needs (`causal_orchestrator.py:2151`).

**No human review.** The lifecycle stays and automation drives it: serving accepts only `active` candidates (`causal_orchestrator.py:2053`), so a machine admission receipt moves the candidate and updates the family-link and item state (`causal_probe_coherence.py:1674`). These automated checks stay, and a failure means the question isn't served:

- the structural instance gate and the never-before-seen check;
- the manipulation audit (`causal_probe_coherence.py:1418`);
- the blind prediction bundles;
- exam-material protection, which needs new work: `llm_instance_payloads` sends every item on the topic to the generator with no protection filter (`probe_instance_generation.py:813, 837`), and the structural gate isn't an exam-material gate. The context builder must exclude protected material and exam reservations before any prompt, and generated-item provenance and output checks run before activation.

The automated adversarial review runs only if its cost fits the wait; the build reports its time and cost.

**Evidence.** Answers count as evidence from the first serve, as for any diagnostic probe. The admissibility rule stays exactly as it is (§6.0).

**No template fallback.** Parametric templates can't aim at specific hypotheses, so they aren't a fallback on this lane. If generation fails, see §6.2.

### 4.2 Single use, strictly

A generated probe is served once and never again. It never becomes a practice item. One durable identity and retirement rule governs every door, not a naming convention or the generic `codex_proposal` origin.

- **Burned at first serve.** An atomic claim, keyed to item revision, surface and presentation, blocks any new administration and keeps that presentation's one valid submission. Ending the presentation at burn would make submission fail (`probe_episodes.py:1808`). Generation, queue listing, plan prefetch and presentation commit never burn. Abandonment closes it. A response lost after the server burned the item counts as burned: a server can't prove pixels were displayed, so this errs toward never repeating.
- **Reserved for its workflow** until then, so a selected id or precommitted presentation isn't exclusive across devices.
- **Retired while unused** if its hypotheses close first, or the learner takes *Continue without it*.
- **Kept for history.** The item stays in the vault so attempts and replays resolve. The build measures vault growth.

| Door | What the build does |
|---|---|
| Queue and direct-by-id opens | Burn and ownership checks at the actual serve (`serving_exclusions.py:147, 260`) |
| Plan pool | Checks standing plans too; served items can reopen (`engine.py:4239`) |
| `find_practice` | Already excludes diagnostic modes (`practice_index/admission.py:116`); keep it, recheck stale picks |
| Teacher | Brief probe headers list unattempted items without checking active state or mode (`teacher/brief.py:419`); exclude FG1 items |
| AD | Limited to the plan's admitted pool (`daily_plan/ad_slot.py:21`); FG1 items never become new-material candidates |
| Exams | Reservations don't exclude `diagnostic_probe` (`goals/exam_pool.py:423`); exclude FG1 items at reservation and on frozen pools |
| Phone | *Amended Nov 7, 2026 (mobile v2 stage V3, owner decision D3; `docs/reviews/phone-v2-v3-probes.md`):* the phone's serve doors take the desktop's path under the phone's surface (`serving.refuse_generated_probe_door`, `phone_probes`), so the atomic claim is the phone's: burned at its first serve on whichever device opened it, refused on the other (`generated_probe_closed`), each device's re-open of its own administration passing. Its answer names its presentation. The phone's plan step holds one the desktop served; the desktop's serving Next moves past one the phone served (displaced, abandoned). With the host's `phone_probes` off, or below mvp-0.54, every phone door refuses as before (*was:* submit rejects `probe_presentation_id`); see §10 |
| MCP | Read-only with no question text (`remote/views.py:141, 189`); keep it |
| Follow-up tasks | `cold_retry` may reuse an administered diagnostic item (`scheduler.py:1550, 2353`); FG1 identity overrides that |
| Rebuild replay | Replay reproduces attempt-time deactivation only (`substrate/replay.py:327`); add burn-ledger replay, and no generation during rebuild |
| `state_sync` | Reactivation guards only on `last_attempt_at` (`state_sync.py:44`); add burn and retirement to the shared predicate |
| Check once | Can use a diagnostic presentation (`practice.py:579`); shared admission gets the FG1 rule, including standing assignments |
| Remint | Accepts diagnostic probes (`probe_remint.py:245`); refuses FG1 identity |

### 4.3 `auto_generate_on_entry`

The owner's decision is true for all vaults. A schema change alone can't deliver it, because the template writes an explicit `false` that loading honours (`config/template.py:286`, `config/loader.py:64`), and rewriting vault files would break rollback. So the successor computes the **effective** setting: true while FG1 is on, whatever the file says, leaving the stored value for rollback. New vaults get `true`.

Passing a client alone wouldn't give model-written single-use questions. Entry currently runs the batch generator synchronously: two instances per family, parking provisional families, with parametric fallback (`probe_instance_generation.py:695, 996`). Entry also comes from far more than sync: misconception and prediction-failure re-probes, stale uncertainty, calibration, goal diagnostics and diagnostic packs (`probe_episodes.py:651, 719`, `calibration_sessions.py:219`, `diagnostic_pack.py:317`). So:

- **Every entry point enqueues deduplicated generation work.** Opening a vault can't stall or burst. A calibration the learner starts may still generate in its own flow.
- **The worker chooses the contract.** With concrete rival causes, it uses §4.1. Otherwise it uses the family's question pattern, written by the model.
- **All generated probes are single use** (§12), under §4.2.

## 5. The router

Today the router decides only between "ask now" and "wait" on an item that already exists, and value checks can suppress a follow-up first.

1. **A durable workflow owns each intervention.** It has a stable id before routing, keyed to the source attempt and the effective diagnosis or grade revision, with states pending, ready, waiting, refused, failed, skipped and settled. Predecessor insertion is suppressed only while it owns the attempt, and every Next and serve door reads it. A timeout settles one fallback. A late diagnosis or generator can't add a second intervention after a fallback, a skip, factor closure or a newer diagnosis. Generation doesn't run inside the strictly ordered diagnosis worker (`post_attempt_worker.py:3`), so later diagnoses aren't delayed. Retry and crash recovery reuse the workflow's identity.
2. **The decision comes before the item.** `plan_interrupt` today indexes `practice_item_id` for its candidates, `receipt_key` and chosen action (`router/plan_log.py:529, 571`), and rows are append-only (`db/stores/router.py:102`). The decision stays immutable and names the workflow. A separate appended binding links it to the generated item and both presentations. Receipt parsing, outcome joins (`router/outcomes.py:432, 874`) and data capture follow that binding. Generation failure, skip and abandonment are distinct outcomes, and a wait is measured through its eventual binding.
3. **Waiting stays.** A wait generates at once as preparation, under the same budget, with boundary room reserved. Before serving, it revalidates hypothesis versions, item constraints and room. Next continues the current block after a wait; it doesn't wait for the future question.
4. **It can choose no intervention.** Today it never decides whether (`engine.py:3600`). `no_intervention` sits in the same logged mixture, including its random floor, so weak cases are the router's call. Nothing is generated, the screen shows the decision (§6.4), and held feedback and causes are released.
5. **Value checks stop suppressing this lane.** They log but don't decide, in line with the Nov 2 decision that the nat-scale rule stop deciding. That covers the follow-up check (`followups.py:~395`), the probe contract's value refusal (`practice.py:554`), and the causal decision policy's value and EIG skips. If rivals share a repair class, commissioning refuses today (`causal_probe_commissioning.py:481`); on this lane that becomes a fact on the router's card, since the owner allows minutes to be spent on improving the model. The build lists any gate it can't make observational.

**Hard refusals stay:** constraint refusals, episode conflicts (`causal_orchestrator.py:1830`), pending machine checks (the orchestrator's rule that a bad item or grader is ruled out first), incomplete measurement, and a learner's own "Not now". They hold over a decision already drawn: a retry keeps the draw and asks them again, and one that holds now is recorded as that decision's `refused` outcome (Codex re-review F9).

### 5.1 The causal orchestrator's role

The router decides whether and when. The orchestrator keeps the measurement. `decide_probe` runs and logs but no longer decides on this lane, and the learner's accept click is replaced by the router's decision. The orchestrator still runs machine checks, locks the hypothesis set, pins the prediction bundles, classifies the answer against them, writes the discriminating-observation receipt (the only channel that moves support for a cause), and starts the targeted repair and its cold verification. *Continue without it* records the same explicit authorisation as today's *Teach me now*. The offer's *Take the quick check* remains for factors that didn't come through this lane.

Without a plan there is no `plan_interrupt` timing decision: classic Today still logs its `today_offer` decision (`queue.py:429, 595`), the probe goes to the head of the queue, and the screen says so. Whether no-plan misses need a no-intervention draw is left to the build record, with the default that they don't.

## 6. What the learner sees

### 6.0 What is held until the probe is answered

Reveal checks look at the probe item **and its whole topic** (`attempts/reveal_ledger.py:270`), and the orchestrator refuses causal support when independence fails (`causal_orchestrator.py:2504, 2703`). The feedback screen already records full-answer exposure (`learnloop_sidecar/handlers/feedback.py:718`) and debits displayed repairs (`handlers/diagnosis_card.py:44`). So a probe served straight after today's feedback could be answered but could never close the question it was built for. Hiding only the causes behind `why?` wouldn't fix that.

So, on a miss while the workflow is pending:

- **Shown at once:** the verdict and the criteria, unless the reveal rules count a criterion as disclosure.
- **Held:** the worked answer, the diagnosis summary and possible causes, repairs, the prerequisite explanation and escalation.
- **Released when:** the probe is answered, the router chooses no intervention, the practice lane is chosen, the learner takes *Continue without it*, or generation fails.
- **On a wait:** released now, and the later probe is labelled exposed, so it can't resolve the cause. Holding the answer through a whole block seemed worse (§12, Q4).
- **Show anyway** releases what's held, with the existing exposure recording on the actual disclosures, and marks the probe's answer as not independent. It doesn't cancel the probe.

The diagnosis card's poll must not record a reveal for content it hasn't shown.

### 6.1 While waiting

*Amended Nov 4, 2026 (R12):* a plan serves a workflow's probe only if the miss came from the plan, which the attempt's own `plan_presentation_id` records, and today's plan is still open. In every other case, the queue screen and a completed or stopped plan among them, Next opens the probe. A wait still being written doesn't hold Next, since what it held is already released.

The feedback screen shows at once, with a line: *Preparing a question on this…*. Pressing Next waits with the same words and offers *Continue without it*. Taking that option is logged and retires the probe.

The owner didn't object to this proposal; it stands unless changed.

### 6.2 When something fails

- Diagnosis fails, times out or stays released for readiness reasons (`jobs.py:697, 741`): the workflow settles one fallback, and the practice lane runs from the grade alone. There is no unbounded wait. The timeout reuses `diagnosis.next_item_wait_seconds` (`queue.py:238`), so no new constant.
- Generation fails or no question passes the checks: *Couldn't prepare a question on this. It's noted for later.* Next continues the plan. The need stays open for background generation, deduplicated, and cancelled if the hypotheses close.

Next never strands the learner.

### 6.3 A wait is visible

When the router waits, the screen says so where the question would have been: *A question on {topic} is coming in your next block.* Today the wording exists in code (`router/why.py:217`), but I found nothing that puts it on screen. That block's first question names why it's there.

### 6.4 Router decisions are visible, for now

For debugging and calibration, a plain line on Feedback and in the plan:

> Router: ask now · drawn by LLM · ask now 62%, wait 38% · floor 5%

Under it, *details* opens the card summary, each model's answer and rationale, the fallback if any, and the decision id. A setting `ui.show_router_decisions` defaults to true, so it can be turned off when calibration is done. This is a deliberate exception to the UX spec's "machinery behind why?" rule.

This covers follow-up decisions and ordinary block choices.

### 6.5 UX spec changes

Next no longer always returns to where the attempt started: a follow-up comes first. A chosen probe replaces the optional next-step button, since it is the next step. The Feedback section's answer-at-once rule gains §6.0's exception.

## 7. Learner marks on hypotheses

The learner reads the possible causes and marks them. It's an imperfect sensor, collected for later model training.

- **Marks, per hypothesis, all optional:** *This is my gap* · *Partly* · *Not it*. One extra line: *None of these*, with optional free text. The text goes to the diagnoser, per the Oct 12 rule on learner text.
- **Timing.** Showing causes before the probe would prime the answer, since a hypothesis often states the misconception outright. So causes follow §6.0: hidden by default, with `why?` saying why, and shown after the probe is answered. With no probe, they appear on the feedback screen. *Show anyway* marks the probe's answer as not independent.
- **What is stored,** in a new raw ledger table: the attempt, diagnosis and hypothesis version ids, the mark, the display order (shuffled and logged, to measure position bias), whether the probe had been answered, its outcome if known, and the time.
- **What it affects now:** nothing that decides. It reaches the learner state card and the diagnoser's context as attributed opinion. It never touches certification, opens no belief, resolves no factor, and moves no probability until measured.
- **Existing channels.** The card's single-response tap and the unresolved-cause self-report stay, with O14's forwarding unchanged. Marks are not forwarded: that channel can open a provisional belief and resolve a factor (`causal_attribution.py:3497, 3586`), it targets the primary cause rather than the one tapped (`split/card.py:282`), and it allows one report per factor (`:3514`). On the probe lane the marks replace the card's tap, so the learner isn't asked twice.
- **Measuring the sensor.** `learnloop data-capture report`, once data capture lands, gains agreement between marks and probe outcomes, and between marks and delayed performance, along with mark rates by display position. That tells us how far to trust it and watches for acquiescence, which O14 already warned of.

*As built (FG1c, Nov 4, 2026; migration 242, `docs/reviews/followup-fg1c.md`):*

- **Tables.** `hypothesis_marks` (RAW_LEDGER), and `hypothesis_list_exposures` with `hypothesis_exposure_probe_links` (RECEIPT), the exposure table of `spec_router_objective_v1.md` §4 row 6, which this stage owns. Every list of an attempt's causes the desktop displays writes a row from the client's display event, through the `record_hypothesis_exposure` RPC: the marks panel, `why?`, the causal feedback and the unresolved-cause card, each with the order as displayed. A refused receipt rolls back alone with a warning and never blocks an answer.
- **The list.** The workflow's factor's concrete causes, whatever became of the factor, since its probe tested those versions; else the newest open or resolved factor's; else, with no factor, exactly the causes the feedback's claim-checked overlay would show. Hypothesis version id is the `causal_hypotheses` row, and the stable identity is its `episode_key`.
- **The order.** Each identity sorts by its own hash under a seed from the attempt (`hypothesis_order_v1`), so a list reads the same every time, a later version keeps its place and a new cause moves nothing else. The seed is on every panel exposure and every mark.
- **Where the panel sits.** Under the feedback surface, on the miss's own screen and on the probe answer's (where it lists the miss's causes), not inside `FollowupPanel`: above the verdict it would come before what it's about. `FollowupPanel`'s held line stays what says why the causes are hidden.
- **Taking a mark back.** One value beyond the spec's: tapping a mark again appends `cleared`.
- **On the probe lane** the diagnosis card's tap row goes, and so does `why?`'s "this doesn't sound right" when it would have written that tap. The unresolved-cause self-report stays, as above, under *details*. The RPC behind the tap is unchanged.
- **Reaching the diagnoser.** Marks reach history attempts as of the diagnosis's cutoff, and a re-diagnosis of the same attempt reads its own. Nothing triggers a re-diagnosis. The block carries its own attribution, so no prompt version moved.
- **Kill switch** `followup.hypothesis_marks`, default true, at every algorithm version. Off: no bundle key, no rows, no card section or context block, whatever rows an earlier run left.
- **No successor.** No score, schedule or projection reads any of this, and no mark reaches admissibility; replay clears none of it. The card's version gains `+marks` only while a mark is on it, which is how a stored card says which model input it was. Sol's review (F2) asked for one; rejected, `docs/reviews/followup-fg1c-codex-review.md` says why: `spec_teacher_v1.md` §15.2's decided default takes no successor for attributed text on the card and in the diagnoser's context, and the shuffle is on a new panel, so no list a learner already saw has moved.
- **Causes shown before a probe's answer.** The owner's rule of Nov 3: hypotheses read before the probe mark its answer as not independent. A recorded exposure of a workflow's causes (its attempt's or its factor's, from any surface, held or not) with a time before the answer makes `probe_answer_exposed` return `followup_causes_shown_before_probe`, so the observation can't resolve the factor. A display event sent while feedback is held is recorded, not discarded. An unreadable table gives `followup_cause_exposures_unreadable`, never an exception. With marks off nothing new is recorded and *Show anyway*'s flag still protects the answer. Exposures, not marks: a mark still moves nothing.
- **What a diagnosis read.** A cause a mark shows is a derived text: its version and statement fold into the diagnosis's provenance record, on the current attempt, a history attempt and a snapshot entry alike (F1).
- **The report's two agreements (F3 to F5).** Against a probe: independence is the receipt's `admissible_as_independent`, not admission; `matched_multiple` is not discriminating, by the orchestrator's own `DISCRIMINATING_OUTCOMES`; a no-match supports *None of these* only when every cause was put at risk (`declared_keys_observed`). Against a delayed answer: the opinion scored is the one held before the first delayed answer that had one, and a mark made or changed after a delayed answer is counted apart, unscored. *None of these*, or *Not it* on every cause as last displayed, rules the list out; *Not it* on some of them is reported as `rejected_some_causes` and never scored, since a delayed answer can't say which cause it was.

## 8. Protection and spend

**Kept:** the blind grader sees none of this. Prediction bundles stay blind. Exam material stays protected, with the new filter in §4.1. Probe answers remain cold unless the reveal ledger says otherwise.

**Exam protection for probes, the owner's ruling of Nov 4, 2026.** It covers exam questions still reserved or withheld, by what `learner_protection.withheld_items` and the exam pool say: reasons `WITHHELD_EXAM` and `WITHHELD_RESERVED`, and held-out spans. Past exam answers can inform causes, and a missing, incomplete or stale write-time record no longer blocks by itself; the admission receipt says what each cause's record covered. Reserved questions and their solutions stay out of the generator's context, and so does any line that quotes one. A machine check (`practice_leakage.reserved_findings`: the existing six-word shingle and distinctive-number gate, plus a whole stem) compares each cause before the router's card and the author's prompt, and each generated question's stem, key, rubric and hints at admission. A match sends the miss to the practice lane, logged `cause_matches_reserved_question` or `question_matches_reserved_question`. Unreadable protection fails closed, as before. The check catches reproduced wording and numbers; it does not catch a paraphrase. *R10, the same day:* the shingle order stays 6; a phrase an ordinary item or source text outside held-out spans already shows doesn't count; and a generated question that matches gets the workflow's one retry, told only the matching stretches of its own draft, with `MAX_GENERATION_ATTEMPTS` still 2 in all, before the practice lane.

**Spend:** generation runs on plan routes through the existing spend envelopes, covering every physical call, including retries and optional review. A metered route needs the existing budget. Dollar reservations don't bound request count on a subscription (`ai/spend.py:19`), so the bound is structural: one generation per workflow and one per deduplicated need, with retries admitted by the workflow. The build reports real latency and calls per probe, on a copy.

## 9. Specs amended

| Spec | Amendment |
|---|---|
| `spec_blind_grading_diagnosis_split_v1.md:444, 613` | On a miss with diagnosis on, the workflow owns the attempt and holds selection for hypotheses, up to one settled fallback. The verdict never waits; the worked answer may be held (§6.0) |
| `spec_source_practice_and_probes_v1.md` §8.5 (S2b) | Textbook-first applies to practice items only. Needs fill automatically |
| `spec_action_router_v1.md`, `plan_router_r2_v1.md` §3.5 | The decision precedes the item. The value check stops deciding on this lane |
| `spec_causal_attribution_v1.md` §6 | An absent or unreviewed instrument no longer blocks when generation can fill the slot; `blocked_pending_review` stays for episode conflict. `probe_now` serves without "Take the quick check". Machine admission replaces the human ladder on this lane |
| `ux_learnloop_v1.md`, Feedback section | §6.0, §6.4 and §6.5 above |

## 10. Build

**Stages.** FG1: the workflow, lanes, generation, single-use rules, router change, successor and the desktop UI (§6), landed together, since serving without the pending and skip UI would strand Next. FG1c: marks and the report (§7), right after; built with no successor (§7, "As built").

**Persisted meaning:** a successor after data capture's `mvp-0.44`, with a kill switch `followup.generate_and_serve`. Off: behaviour matches the predecessor from an equivalent starting state, background work and UI included, and the stored `auto_generate_on_entry` is what applies. Burns persist after a rollback, and open FG1 workflows settle as skipped. New tables get a role in `table_roles.py`, per CLAUDE.md. Numbers are claimed at landing.

**Queue position:** as soon as possible, per the owner: ahead of the TE2/TE3 re-spec. A7 was planned next, and its probe arm would have reused this path. Owner decision, Nov 4 2026: A7 is dropped as a separate stage ("I agree with you reccomendation to drop it"). Its probe-versus-continue contrast is read from the router's logged `no_intervention` floor (§5, §11). If that proves too thin, a higher no-probe share is a possible RO5 arm (`spec_router_objective_v1.md` §9).

**Phone.** Phone submit rejects `probe_presentation_id`, so a generated probe can't be answered there yet. A miss on the phone follows the existing behaviour for what it can serve, and a pending probe is handed to the desktop with a line saying so. The phone's feedback doesn't hold what it can't follow with a probe. Phone probe answers are a follow-up. Phone files are in the owner's working tree at the time of writing, so the build merges whatever lands.

*Amended Nov 7, 2026 (mobile v2 stage V3, owner decision D3 accepted Nov 6; `spec_mobile_frontend_v2.md` §8's V3 row; `docs/reviews/phone-v2-v3-probes.md`):* that follow-up is built. Mobile v2 V2 had already given the phone the held feedback, *Continue without it* and *Show anyway*, and opened a phone miss's workflow under the phone's surface. From V3, with the phone host's kill switch `phone_probes` (mobile.toml, default true) at the successor mvp-0.54 (`PHONE_PROBES_ALGORITHM_VERSION`):
- the phone's Next on a miss calls `followup_next`, as the desktop's does: it waits with the same line, opens the question, or goes on; on a plan, the plan's next step places and serves it (R12), and the phone's step filter no longer holds a generated probe;
- the phone renders the active contract cold (the desktop's line, no hints, no Ask, no tutor; the server refuses a hint during it) and answers it naming its presentation, so the held feedback is released by that answer and by nothing earlier;
- single use across both devices (§4.2's Phone row): the claim keys the surface, so a probe served on one device is refused on the other; the phone holds a desktop-served one for the desktop, and the desktop's serving Next abandons a phone-served one it can't open;
- the phone's admission and its cap count are one transaction, so the host's two workers can't pass the session cap between them (G10).
Off, or below the tag, the phone is V2's: its line says the question waits for the desktop, its Next goes on writing nothing, and its doors refuse.

**Tests.** Fakes only, plus a smoke on fresh copies of the owner's vaults:

- a miss with two concrete rivals leads to one generated item, shown next, and never again after serve, rebuild, sync, remint or any door in §4.2's table;
- an unanswered probe stays retired after a rebuild, and a submission on its one presentation still works;
- the answer is held, and the probe's answer is admissible and can close the factor; with *Show anyway*, it can't;
- protected and reserved items never reach the generator's prompt;
- a late diagnosis or generator after a fallback or skip adds nothing;
- exam sittings and diagnostic blocks see no interruption, and the exam cap holds;
- each failure in §6.2 leaves Next working;
- ask now, wait, no intervention and refuse each log correctly, bind to their outcome and match what's on screen;
- marks don't change any grade, certification or probability;
- with the switch off, from an equivalent starting state, replies are byte-identical to the predecessor.

## 11. Decided by the owner (Nov 3)

> Yes, the router should be able to choose no intervention. The router will decide for weak cases. Yes, you should have the hypothesis hidden by default and if read it should be marked as not independent. We should have it run as soon as possible since this is a big user experience gap

- **No intervention** is a router option (§5). Its logged random floor gives the probe-versus-no-probe contrast. A7 was dropped as a separate stage (owner, Nov 4 2026), so this floor is where that contrast is read; a higher no-probe share is a possible RO5 arm if it proves too thin.
- **No threshold** on hypothesis strength. The router decides weak cases.
- **Causes stay hidden** until the probe is answered. Reading them first marks the probe's answer as not independent (§7).
- **Priority:** as soon as possible, ahead of the TE2/TE3 re-spec (A7, also listed here at the time, was dropped as a stage on Nov 4).

## 12. Build defaults awaiting the owner's word

The build proceeds on these. Each is cheap to change until landing.

- **Q4. Holding the worked answer (§6.0).** The review found that today's feedback would make an immediate probe unable to resolve anything. The default holds the answer until the probe is answered, and releases it on a wait.

Decided by the owner, Nov 3: "yes I think FG1 single use rule should cover all generated probes. The generated probe uses the frontier LLM to turn an action router decision about the hypothesis set." So every generated probe is single use (§4.2), and a frontier LLM writes the question from the router's decision and the hypothesis set, not the Decider.
