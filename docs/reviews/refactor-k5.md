# Refactor K5: grading, regrade, coldness and certification

Step K5 of `docs/specs/refactor_strategy_v3.md` (arc K, "**K5.**", line 700): a read-only review of the two grading validators, whether an unknown coldness can pass as cold, whether the newer exposure channels reach the cold scan, regrade, held grades and FSRS, and the four `qualifies_as_*` claims. Branch `refactor/k5-grading-review`, at main `c1e3706164`. No code under `src/`, `apps/` or `tests/` changed, and no test was run.

An independent review produced the fourteen findings on 2026-11-18; this record verified each one against the code at this tip, by reading every cited line and tracing the call path. Paths are relative to `src/learnloop/` unless they start with `src/`, `apps/`, `tests/` or `docs/`; `sidecar/` is `src/learnloop_sidecar/` and `UI/` is `apps/learnloop-tauri/src/`.

## Summary for the owner

Nothing was refuted. Two findings are high; the rest are real but narrower or rarer than the review said.

1. **Imported exam scores can be wiped at startup (K5-14, high).** `learnloop seed-exam-attempts` without answers stores a placeholder text. The next app start with AI ready sends each one to the grader as a "deferred self-grade" and replaces the imported score with the model's grade of the placeholder.
2. **"The repair is confirmed" when it was not measured (K5-2, high).** After a repair, practising another question on the same topic before the check is normal. The check's receipt then says the repair's effect can't be attributed, but the desktop still says "the repair is confirmed and the factor is closed".
3. **Some answer displays leave no record (K5-5, K5-6, K5-7, medium).** These are the Reader's ordinary view of a book solution, a tutor or lesson that states a short key such as "42", the inspector's answer for an item answered before, and the terminal app's self-grade form. A later answer then counts as independent. The cold scan also misses a book solution that *was* recorded.
4. **Skipped reviews move the FSRS clock (K5-8, medium; your call).** FSRS is the memory model that sets due dates. A held, hinted or primed answer leaves memory and the due date alone, as the code says, but it resets the "time since last review" that the next review uses.
5. **Adjudicating a grade from the terminal (K5-9, K5-10, medium).** It says "downstream state rebuilt" but rebuilds nothing. Confirming a held grade's own class leaves it held.
6. **Regrade and rebuild drift (K5-11, K5-12, K5-13).** An AI regrade of a self-grade still replays as "self". A grader confidence of exactly 0 becomes 1 on rebuild. A regrade's newly seen supporting facet arrives one projection late.
7. **Smaller (K5-1, K5-3, K5-4).** A model that returns no criterion rows scores 0. A certificate probe is scored before its coldness is checked, which affects only a report. Two research readers use their own, weaker coldness rule.

Three things need your decision: the FSRS clock rule (K5-8), what a certificate probe measures when you keep practising the topic (K5-3), and the research readers' rule (K5-4).

## Method

- Read the review whole, then every `path:line` it cites for the fourteen findings and the six answers. Traced each sequence from the learner's action to the stored row or the screen. Looked for a guard elsewhere, a caller that never passes the input, a test that pins the opposite and a config default that blocks it.
- Checked each finding against `docs/reviews/refactor-bug-ledger.md` and against K1's record (`docs/reviews/refactor-k1.md`).
- For K5-9 to K5-13, read the incoming fix with `git show fix/arc-d-close-3:<path>`. That branch carries ledger D-35, D-36, D-52 and D-53 and lands this week as successor `mvp-0.60` (an algorithm tag: a named version of the scoring rules that a vault upgrades to). It changes `substrate/replay.py`, `attempts/grade_resolution.py` (`record_replayed_grade`), one branch of `attempts/attempts.py` and a comment and the clock in `attempts/regrade.py`. It does not touch `cli/`, `ops/`, `goals/`, `attempts/coldness_receipt.py` or the sidecar.
- Severity uses this scale. **High:** ordinary learner actions give a learner-visible wrong result, certification or schedule. **Medium:** needs an unusual sequence, or only skews a model's evidence or a report. **Low:** a trap for the next change.

## 1. What the grading validators accept, reject and guard

- **One scoring authority.** `validate_codex_grading_proposal` (`attempts/grading.py:816`) rejects a wrong attempt or item id, an unknown or repeated criterion, points outside the criterion's range and an unknown fatal error (`:830-850`). The score is the rounded sum of the criterion rows present, capped by the rubric maximum and the fatal caps (`:860-867`). The model's own total is only recorded.
- **Sparse evidence is accepted, and a missing row counts as 0.** An empty list is valid (`attempts/blind_grading.py:203`). That is right for teach-back, where only the asked criteria count (`attempts/regrade.py:349-359`), and wrong for an ordinary grade (K5-1).
- **Correction to the review.** Two rules read an omitted criterion differently. The valid-alternative gate (PF-c: on a verified final answer, a mark-down nobody located becomes unassessed) treats an omitted criterion as full marks (`attempts/grading_support.py:472`). The own-route rule and validation treat it as 0 (`:627`, `attempts/grading.py:860`). So on a verified answer, an omitted criterion is neither unassessed nor credited: it scores 0.
- **The blind validator** (`attempts/blind_grading.py:671`) adds a duplicate-trace check, then calls the shared validator. Its docstring says a dangling repaired-trace id raises (`:682-684`). In fact it is cleared (`:733-737`). That is a docstring trap, low.
- **Who validates what.**
  - Model-graded practice and model regrades go through the blind validator and then the shared one.
  - Teach-back, teacher checks, lesson probes and interactive exams use the shared validator after an isolated blind request.
  - Self-grade, "don't know", an empty "stuck", imported exam scores, exam completion, replay and the simulator apply a resolved grade without either validator. Each has its own rule.
  - I found no live door that applies a raw model total unvalidated. I did not re-trace every teacher and exam line the review cites.
- **Held grade.** A held grade is one kept as provisional, with no evidence, until a regrade or adjudication settles it. It is held when the latest blind record holds it and nothing is assessed (`outcome_contract.py:138`, `attempts/attempts.py:4303`). An empty ordinary proposal is *not* held. `nothing_assessed` needs a non-empty unassessed set (`attempts/attempts.py:4287`), so the grade schedules as a 0. The own-route rule holds an empty or omitting grade only on a route the grader calls divergent (`attempts/grading_support.py:620-669`; pinned by `tests/test_route_rules_in_grader.py:602-636`).

## 2. Can unknown coldness pass as cold?

**Yes, for some readers.** A coldness receipt is the record of whether a cold check (an unassisted measurement after a delay) really was cold. It has dimensions (delay, unassisted, answer leakage, exposure isolation, window integrity, novelty and others) and four derived claims (`attempts/coldness_receipt.py:1517-1568`):

- `qualifies_as_cold_retrieval` = the delay passes, unassisted passes and no hard exposure was seen.
- The repair claim adds: no other retrieval in the window, and window integrity passes.
- The held-out claim adds novelty to the repair claim.
- The certificate claim is the held-out conditions on the certificate lane.

At the administration stage, or with no scan, all four are null (`:1525-1532`). Spending more than a repair's reveal budget downgrades the stronger claims (`:1891`). "No hard exposure" means none *observed*. So an unknown exposure dimension does not block the cold claim; only an observed hard event does.

| Reader | What it requires | Verdict |
|---|---|---|
| Repair feedback (`sidecar/handlers/serializers.py:722-770`) | Only the outcome and the budget downgrade; never the repair claim | Defect, K5-2 |
| Repair verification (`diagnosis/causal_cold_verification.py:265-308`) | Blocks hard contamination on a clean attempt, then its own chronology, surface, assistance and unassessed checks (`diagnosis/causal_probe_coherence.py:1845-1904`) | As designed; feeds K5-2 |
| Certificate probe (`goals/certification_cold_probe.py:1311-1393`) | Held out, unassisted, active certificate, not held, a score; the receipt is written after the verdict (`:1429-1457`) | Defect, K5-3 |
| Placement (`placement/state.py:958-981`) | Every final receipt passes unassisted and leakage, and `qualifies_as_cold_retrieval is True` | No defect |
| Field research (`field/outcomes.py:387-425`) | With a final receipt: a valid interval ending at the attempt, and unassisted and leakage pass; ignores delay | Differs by its own documented rule (`:390-393`); but placement calls its stricter rule "the field's strict rule" (`placement/state.py:967`). K5-4 |
| Intervention outcomes (`substrate/intervention_outcomes.py:150-190`, `:281-317`) | Its own 1-day delay from the intervention, assistance, reveals and source exposures in the day before, other interventions, and explicit receipt failures; no check for another retrieval in the topic | K5-4 |
| Dataset export (`substrate/dataset.py:448`, `:564`) | `qualifies_as_cold_retrieval is True` for a number | No defect |
| Learner context (`learner_context.py:1354`) | Forwards the nullable claim | No defect |

## 3. Exposure channels and the cold scan

The scan (`attempts/coldness_receipt.py` `_scan_exposures`) reads attempts, item questions, `source_exposure_events`, feedback-shown metadata and `reveal_events` for the cold item or its learning object (`:549-740`). The reveal ledger (`reveal_events`) is the table every answer-showing surface writes to. The scan does not read `help_assists` (authored hints), `reading_exposure_receipts` or `activity_exposure_events`.

| Channel | Recorded where the scan sees it? | Evidence |
|---|---|---|
| Desktop feedback, full answer | Yes. The screen shows the key only after its reveal row is acknowledged | `attempts/reveal_ledger.py:491-555` |
| Desktop inspector | No. Simple mode (the default, `UI/app/practiceFeedback.ts:12-13`) hides the key only while the item is open on the practice screen or was never answered (`UI/components/InspectorOverlay.tsx:381-382`). Classic mode always shows it (a recorded UX decision, K1 R9). The handler writes no reveal for item details (`sidecar/handlers/inspector.py:65-74`) | K5-5 |
| Authored hints | Only in `help_assists`, "telemetry only" (`sidecar/handlers/practice.py:800-806`). A draft that is abandoned carries no count into a new submission | K5-5 |
| Terminal self-grade form | No. The form shows "Expected:" and the rubric as soon as feedback opens, before any grade (`tui/screens/feedback.py:116-125`, `tui/screens/feedback.tcss:73-77`). Escape returns with nothing written (`:672`). Only the empty-stuck route records a reveal (`:426-442`) | K5-5 |
| Tutor and Ask answers | Reveal amount from `answer_leak_overlap` (`tutor/tutor_qa.py:1282`). It returns 0 for a key of under 12 characters with fewer than 3 content tokens (`:1686-1690`). Spans and hints use the short-answer test (`:1710-1741`, `hints/service.py:1147`) | K5-6 |
| Teacher lessons | The same long-answer measure on the lesson text (`teacher/service.py:1668`); cited passages use the short-answer test (`:1671`) | K5-6 |
| Reader, ordinary view | Rendering a reading writes no exposure (`sidecar/handlers/reader.py:656-722`); only explicit span opens do | K5-6 |
| Book solution of an imported exercise | Recorded when opened, but the scan's cold target is the item's `provenance.source_refs` only (`attempts/coldness_receipt.py:803-821`), not `canonical_exercise` or the book solution (`db/stores/source_service.py:720-733`). The serve-time rule and intervention outcomes do read them (`source_service.py:745-788`, `substrate/intervention_outcomes.py:172-174`) | K5-7 |
| Reveal on another topic's item of the same surface family | Not fetched: the query is the cold item OR its learning object (`db/repositories.py:4761-4790`, `attempts/coldness_receipt.py:702`) | K5-7 |
| Exam review | **Correction:** it shows the learner's answer, score, the grader's feedback and repair suggestions, not the key (`sidecar/handlers/exams.py:469-511`). Whether that gives the answer away depends on the feedback | Not confirmed as an answer display |
| Figures, videos, MCP, guided redo, hypothesis views | Not traced end to end here | Not verified |

## 4. Regrade, hold, release and adjudication

| Event | Grade | Mastery, FSRS, facets, certificate |
|---|---|---|
| **Regrade** | Validates, then in one transaction supersedes every live evidence row (`attempts/regrade.py:549-557`), writes the new score and confidence, and writes a new blind record | Replays the learning object from its first attempt (`attempts/regrade.py:644`). Exceptions: the grade's source stays "self" (K5-11), confidence 0 becomes 1 (K5-12), and new exercised facets are written after the closing projection (K5-13) |
| **Hold** | Provisional; no evidence (`outcome_contract.py:138`) | No FSRS review and the due date is kept (`attempts/attempts.py:4949-4971`), but `last_attempt_at` moves (`:4504`), and the next review's elapsed time reads it (`:5790-5796`). K5-8 |
| **Release** | A regrade, or an adjudication that writes assessed evidence | A regrade replays. An adjudication does not replay (K5-9). Confirming the held class writes nothing, so the hold stays (K5-10) |
| **Adjudication** | `append_adjudication` (`attempts/grade_resolution.py:1042-1234`) appends an interpretation and repoints the head. Only a change of score fraction writes a superseding evidence revision (`:1217`) | The only caller is `learnloop grading adjudicate` (`cli/grading.py:58-85`): no replay, and the message says "downstream state rebuilt" (`:85`). At this tip a rebuild also drops the adjudicated head (D-52). After `mvp-0.60` the next rebuild keeps it |

The certificate-probe store restores a probe's original verdict after its hold is released (`goals/certification_cold_probe.py:1633-1676`). That is the documented write-once policy, not a new defect. The released grade's missing posterior update is K9-3.

## 5. The four `qualifies_as_*` claims and their readers

| Claim | Readers under `src/` |
|---|---|
| `qualifies_as_cold_retrieval` | Placement requires True (`placement/state.py:979`); dataset export requires True for a number (`substrate/dataset.py:448`, `:564`); learner context forwards it (`learner_context.py:1354`) |
| `qualifies_as_repair_effect_verification` | Written and exported; **not read** by the repair feedback (`sidecar/handlers/serializers.py:752-770`) or by repair verification |
| `qualifies_as_held_out_validation` | Written and exported; no decision reader |
| `qualifies_as_certificate_validation` | Written after the probe's verdict; **not read** by the verdict (`goals/certification_cold_probe.py:1358-1377`) |

## 6. Demonstrated capability and a certified learning object

- **Demonstrated threshold.** A capability cell is Demonstrated at certification credit ≥ 1.0 (`goals/certification.py:3-7`). The docstring of `demonstrated_capabilities_for_facet` still says "> 0" (`goals/goal_certification.py:84-86`): a trap, low.
- **What counts.** The canonical projection reads the current evidence and skips absent and unassessed criteria. Supporting credit needs the trace to show the facet was exercised (`substrate/canonical_projection.py:835-877`), and assisted attempts certify nothing (`diagnosis/causal_activity_policy.py:168-187`).
- **Certifying a learning object.** One recipe whose obligatory components and integration are all Demonstrated is enough. Certification does not need a delayed cold receipt. The cold probe later tests the certificate and stores a separate outcome.
- **No defect in the threshold or recipe logic.** The paths around it are upstream: an unrecorded display leaves an attempt unassisted (K5-5, K5-6), a stale projection after adjudication (K5-9) or regrade (K5-13), and a probe scored without its coldness (K5-3).

## 7. Findings

Each finding gives its verdict, severity, sequence, fail-first test, smallest fix, whether the fix changes persisted meaning, and size (S: under about 50 source lines; M; L). "Persisted meaning" means it needs an algorithm tag under `docs/algorithm-change-playbook.md`. That includes the 2026-10-17 rule: a change to which new attempts are primed, or which measurements count, is a successor.

### K5-1. A model grade with no criterion rows scores 0 — CONFIRMED, medium (review: high)
- **Sequence.** An ordinary item, on a route the grader does not call divergent. The model returns a valid proposal with no `criterion_evidence`, or with some criteria left out.
  - Validation sums nothing to 0 (`attempts/grading.py:860`). Nothing is unassessed, so the grade is not held (`attempts/attempts.py:4287`, `:4303`), and FSRS records an Again review.
  - On a regrade, the empty list still mints a replacement id and supersedes every live row (`attempts/regrade.py:373`, `:549-556`; `db/repositories.py:5865-5891`, which has no foreign key). A self-grade's evidence is gone.
- **Narrower.** It needs a model that leaves rows out. Wider: any omitted criterion scores 0, and PF-c reads omission as full marks (§1).
- **Ledger.** No row.
- **Fail-first.** `tests/test_blind_grading_contract.py`: an ordinary proposal with no rows on a non-empty rubric is refused, or held. `tests/test_deferred_regrade.py`: a regrade returning no rows leaves the self-grade's rows live and the due date unchanged. Teach-back with sparse rows still passes.
- **Fix.** Refuse an ordinary (not teach-back) proposal with no criterion rows at the practice door and in regrade, as any invalid proposal is refused. Settle the omitted-criterion rule in one place.
- **Meaning.** Plain defect fix at intake. History and replay are unchanged.
- **Size.** S.

### K5-2. The repair feedback says "confirmed" without the repair claim — CONFIRMED, high
- **Sequence.** Do a repair. Practise another item on the same topic, as Today serves it. Pass the cold check a day later.
  - The receipt has `qualifies_as_repair_effect_verification = False` (`attempts/coldness_receipt.py:1543-1545`). That exact case is pinned in `tests/test_coldness_receipt.py:357-391`, and the delay-reset case in `:394-427`.
  - `record_delayed_cold_verification` still records success, so the outcome is `cold_success` (`diagnosis/causal_cold_verification.py:308`).
  - The serializer checks only the budget downgrade (`sidecar/handlers/serializers.py:757-764`). The desktop then says "the repair is confirmed and the factor is closed" (`UI/screens/FeedbackScreen.tsx:212`; `UI/screens/feedback/FeedbackSurface.tsx:174`).
  - A failed check is shown as "did not hold" on the same basis.
- **Ledger.** No row.
- **Fail-first.** `tests/test_sidecar_remediation_surfaces.py`: the sequence above gives a claim other than `repair_confirmed`, with `passed` still true. The same with no final receipt.
- **Fix.** Gate `repair_confirmed` and `escalated_unrepaired` on `qualifies_as_repair_effect_verification is True`; otherwise `downgraded` (or a new word) with a reason. The desktop copy needs a line for "recorded, not attributable".
- **Meaning.** Plain for the label (display only). Whether repair-effect support (`diagnosis/causal_probe_coherence.py:1904-1912`) and closing the case should also require the claim is the owner's call and would change persisted meaning.
- **Size.** S.

### K5-3. A certificate probe is scored before its coldness is known — CONFIRMED-NARROWER, medium (review: high)
- **Sequence.** A certified topic gets a probe in 2-3 weeks. The learner practises other items of the topic, then passes the probe.
  - The verdict ladder never reads the receipt (`goals/certification_cold_probe.py:1358-1377`). It writes `held` (`:1393`), then writes a receipt whose certificate claim is False (`:1438`).
  - Separately, a verified answer whose every criterion is unassessed has correctness 1.0 "for scheduling only" and is scored `held`. Repair verification refuses that grade (`diagnosis/causal_probe_coherence.py:1893-1904`).
- **Narrower.** Consumers are `false_certification_rate`, a CLI report (`cli/app.py:4711-4765`), and the causal labels count (`goals/certification_cold_probe.py:1772`). No learner-visible state.
- **Owner choice.** The receipt's certificate claim forbids any other retrieval in the topic. A probe weeks later almost always has one. Gating on it would make the rate nearly always unavailable. So what the probe measures is a product choice: retention with ordinary practice, or the certificate alone.
- **Ledger.** No row.
- **Fail-first.** `tests/test_certification_cold_probe.py`: an all-unassessed verified answer gives `indeterminate` and stays out of the denominator. A test for the retrieval rule follows the owner's choice.
- **Fix.** Plain: an all-unassessed grade abstains. After the choice: evaluate the receipt first and abstain on the chosen claim.
- **Meaning.** Admissibility of a measurement label: bump `COLD_PROBE_POLICY_VERSION`, and a tag under the playbook. The store is append-only, so history keeps its verdicts.
- **Size.** S.

### K5-4. Two research readers use a weaker coldness rule — CONFIRMED-NARROWER, low (review: medium)
- **Field reader.** It takes a receipt's unassisted and leakage findings but not its delay (`field/outcomes.py:387-425`). It documents this (`:390-393`), and for item memory, another item's retrieval need not reset the clock. But placement describes its own stricter rule as "the field's strict rule" (`placement/state.py:967`).
- **Intervention outcomes.** These check their own day-long window but not another retrieval in the topic (`substrate/intervention_outcomes.py:150-190`). An all-unknown receipt gives no veto (`:135-146`). Both readers feed research reports and the learner field's memory rows, never a learner-visible decision.
- **Ledger.** No row.
- **Fail-first.** `tests/test_intervention_outcomes_replayer.py`: an intervention, then another item of the topic an hour before the targeted answer; assert the owner's chosen label.
- **Fix.** Owner's choice. Either say each reader's rule in one place, or require `qualifies_as_cold_retrieval` where a final receipt governs.
- **Meaning.** If changed, the field's derived rows move: a tag.
- **Size.** S.

### K5-5. Displays that show a key without a record — CONFIRMED-NARROWER, medium (review: high)
- **Terminal app.** With AI unavailable, submitting opens feedback with the expected answer and rubric showing (`tui/screens/practice.py:302-307`; `tui/screens/feedback.py:116-125`). Escape leaves with nothing written (`:672`). Reopening and answering gives an independent attempt with no reveal. With AI ready, the key shows while grading runs.
- **Inspector.** In simple mode, the default, any item answered before shows its key when it is not open on the practice screen (`UI/components/InspectorOverlay.tsx:381-382`), with no reveal (`sidecar/handlers/inspector.py:65-74`). The feedback display's own row lapses after its coverage window (`attempts/reveal_ledger.py:308-330`). So reading the key in the inspector days later, then answering the due review, counts as unassisted. Classic mode's key display is a recorded UX decision (K1 R9).
- **Authored hints.** A final hint that gives the answer, on an abandoned draft, then a fresh submission: `help_assists` only (`sidecar/handlers/practice.py:800-806`). This needs a hint that states the answer.
- **Exam review.** Not confirmed (§3).
- **Ledger.** K1 R9 named the inspector (`docs/reviews/refactor-k1.md:110`, `:185`). K1-5 fixed only the open item's hints. The key half and the terminal form have no row.
- **Fail-first.** `tests/test_tui_feedback.py`: open feedback with AI off, escape, reopen, submit; the attempt is primed, or a reveal row covers it. `UI/components/InspectorOverlay.phase4.test.tsx`: an answered item not being answered shows the key only behind a recorded display. A non-revealing hint and an unopened report are the controls.
- **Fix.** Record the display with the existing writers (`record_answer_display_reveal`, `record_feedback_answer_display_reveal`) at the moment the key appears, or withhold it until the learner chooses to self-grade. Inspector: withhold on the server as K1 recommended, or record. Hints: record an item-keyed reveal when an authored hint gives the answer (`hints/service.py`'s `gives_away`).
- **Meaning.** Changes which new attempts are primed: a successor under the 2026-10-17 rule.
- **Size.** M.

### K5-6. Allowed reading and short keys escape the record — CONFIRMED-NARROWER, medium (review: high)
- **Short keys.** An item-bound tutor answer, or a lesson, that states a short key such as `42` debits 0. `answer_leak_overlap` returns 0 for short keys (`tutor/tutor_qa.py:1686-1690`) and is used on the tutor's and teacher's own text (`:1282`; `teacher/service.py:1668`). The span and hint paths use the short-answer test.
- **Reader.** Rendering a reading writes no exposure (`sidecar/handlers/reader.py:656-722`). A learner who reads a book's worked solution in a section, after a cold check on that exercise is scheduled, answers "cold".
- **Narrower.** In-attempt Ask already counts as a hint through question events (`tutor/tutor_qa.py:1650-1662`), so the miss is across sessions or before an attempt. Figures and videos were not traced.
- **Ledger.** K1 Q8 named `answer_leak_overlap` as accounting only. No row.
- **Fail-first.** `tests/test_tutor_qa.py`: an item-bound answer containing an item's exact short key debits 1.0; an incidental number in a long key does not. New `tests/test_reader_render_exposure.py`: rendering a section that contains an open cold item's source or solution span is seen by the scan.
- **Fix.** Use `span_answer_overlap` for tutor and teacher text where the target item is known. Record (or withhold, as the phone does) solution-role spans of items with an open cold task when a view renders them.
- **Meaning.** Priming moves: a successor (with K5-5 and K5-7).
- **Size.** S for short keys; M for the Reader.

### K5-7. The scan loses exposures that were recorded — CONFIRMED-NARROWER, medium (review: high)
- **Book solution.** An imported exercise's book solution, opened as a span, is in `source_exposure_events`. The cold target is only `provenance.source_refs` (`attempts/coldness_receipt.py:803-821`), which the import fills from the draft, not from `canonical_exercise` or the book solution (`content/authoring/source_exercise_import.py:1309-1376`; `db/stores/source_service.py:720-733`). It is missed unless the draft happened to cite it.
- **Same family, another topic.** A reveal on item B of another learning object in the same surface family is never fetched (`db/repositories.py:4761-4790`). Rare: it needs a cross-topic family.
- **Ledger.** No row.
- **Fail-first.** `tests/test_coldness_receipt.py`: both sequences give a hard exposure with the event's id. A reveal on a different-family item of the same topic stays soft.
- **Fix.** Add `canonical_exercise` spans and `book_solution_span_ids` to `_item_source_spans`. Add the cold item's family members to the reveal query.
- **Meaning.** Cold dispositions move: a successor.
- **Size.** S.

### K5-8. Skipped reviews move the FSRS elapsed clock — CONFIRMED (wider than stated), medium (review: high)
- **Sequence.** Every attempt writes `last_attempt_at = now` (`attempts/attempts.py:4504`), including a held grade and any review skipped as ineligible (hinted, primed, an ineligible observation; `:4949-4971`). The next review's elapsed days read it (`:4924`, `:5790-5796`).
  - Day 0 review; day 4 hinted or held answer; day 7 review. FSRS sees 3 days, not 7, so the stability gain and the next due date differ. Replay does the same.
  - The comments say a skipped review leaves "scheduling state EXACTLY as it was" (`:4960-4964`).
- **Owner choice.** Whether an assisted or held answer should reset the forgetting clock is a modelling choice. The learner did see the item.
- **Ledger.** No row.
- **Fail-first.** `tests/test_grade_application_core.py`: the day-7 FSRS inputs equal the owner's chosen rule, live and after a rebuild. `tests/test_grade_application_core.py:207` today checks only the held answer itself.
- **Fix.** Either compute elapsed from the last *applied* review (keep `last_attempt_at` for exposure readers, store the review time apart), or keep the behaviour and correct the comments.
- **Meaning.** Scheduling: a tag (whole-vault rebuild).
- **Size.** S to M.

### K5-9. `grading adjudicate` says it rebuilt but does not — CONFIRMED, medium (review: high)
- **Sequence.** `append_adjudication` appends and, on a change of score fraction, supersedes evidence and updates the attempt's score (`attempts/grade_resolution.py:1042-1234`). The CLI then records an event and prints "downstream state rebuilt" (`cli/grading.py:58-85`). Nothing replays the learning object. Mastery, the due date, facet cells and the certificate stay as they were until a rebuild.
- **At this tip vs after `mvp-0.60`.** At this tip the rebuild also drops the adjudicated head (D-52). After `mvp-0.60` the next rebuild applies it.
- **Narrower.** It is the owner's terminal tool, and the only caller.
- **Ledger.** D-52 (incoming) covers the rebuild losing the ruling, and D-56 old rulings. This adds the live gap and the false message.
- **Fail-first.** `tests/test_grading_cli.py`: after `grading adjudicate` that flips a success to a failure, mastery, the item's due date and facet cells equal those after one rebuild.
- **Fix.** Replay the attempt's learning object (`replay_learning_object`) after the adjudication, in one transaction. Print the message only after it.
- **Meaning.** Plain: it applies existing meaning sooner.
- **Size.** S.

### K5-10. Confirming a held grade's class leaves it held — CONFIRMED, medium (review: high)
- **Sequence.** A held grade's head class comes from its provisional score (`attempts/grade_classifier.py:101-140`). Adjudicating that same class takes `skipped_direction_unchanged` (`attempts/grade_resolution.py:1217`). No assessed row is written, so the hold stays (`outcome_contract.py:138`), across rebuilds too. That contradicts the predicate's docstring ("an owner adjudication … releases it", `:146-149`).
- **Narrower.** Owner's terminal tool only.
- **Ledger.** No row. Release tests call the lower-level helper directly (`tests/test_held_grade_evidence.py:737-750`, `:774-818`).
- **Fail-first.** `tests/test_held_grade_evidence.py`: adjudicate a held grade's current class through `append_adjudication`; the hold clears and one review applies at the original time after replay. Confirming an already assessed grade writes nothing (control).
- **Fix.** When the attempt is held, write the assessed owner revision even when the fraction is unchanged.
- **Meaning.** Plain: new adjudications do what the docstring says; stored rows keep their meaning.
- **Size.** S.

### K5-11. A replacement grade replays under the old source — CONFIRMED, medium
- **Self-grade then AI regrade.** Replay reads `grading_source` from the attempt's feedback metadata (`attempts/attempts.py:1427-1432`). A replay, including the regrade's own replay, never rewrites it (`:3116-3129`). So an AI regrade of a self-grade replays as "self": no channel variance, and the grade channel records "self". The deferred regrade at startup is an ordinary path.
- **Exam answers.** Regraded exam answers never reach the channel: the dual write skips any type containing "exam" (`:2674`).
- **Ledger.** D-55 (incoming) is the observation-ordering half; this is the source half.
- **After `mvp-0.60`.** It holds: `record_replayed_grade` takes the same `grading_source`.
- **Fail-first.** `tests/test_deferred_regrade.py`: after `run_deferred_ai_regrades`, the attempt's raw grade event names the AI provider, live and after a rebuild. The existing test checks only the agent run (`:289-327`).
- **Fix.** Derive replay's source from the current epoch (its tier and blind record), or update the feedback row on regrade. Route an exam replacement through the exam channel writer.
- **Meaning.** Replay output moves: a tag. Best folded into `mvp-0.60` if it has not landed, or the next grade-channel successor.
- **Size.** S.

### K5-12. Confidence 0 becomes 1 on replay — CONFIRMED, medium
- **Sequence.** `float(attempt.get("grader_confidence") or 1.0)` (`attempts/attempts.py:1418`). A legal 0.0 (`attempts/blind_grading.py:207`) gives zero reliability live and full reliability after any rebuild or regrade replay. The replay persists it back to the attempt.
- **Narrower.** It needs a model to answer exactly 0.
- **After `mvp-0.60`.** It holds, and the first rebuild would also read the changed confidence as a regrade and append a raw event.
- **Ledger.** No row.
- **Fail-first.** `tests/test_rebuild_equivalence.py` (or `tests/test_grade_application_core.py`): a 0.0 grade keeps confidence and reliability 0 after replay. A legacy null still reads 1.0.
- **Fix.** Fall back only on `None`.
- **Meaning.** Replay output moves: a tag. Fold it with K5-11.
- **Size.** S.

### K5-13. A regrade's new exercised facets arrive after its projection — CONFIRMED, low (review: medium)
- **Sequence.** The regrade replays and projects (`attempts/regrade.py:644`), then inserts the trace's newly seen exercised facets (`:715`). The live path writes them before projecting, and says why (`attempts/attempts.py:3033-3038`). So supporting credit the regrade earned is missing until the next projection.
- **Narrower.** Every live answer re-folds the whole ledger (`attempts/attempts.py:3328-3347`), so it heals at the next answer.
- **After `mvp-0.60`.** It holds (`regrade.py` changes only a comment and the clock).
- **Ledger.** No row.
- **Fail-first.** `tests/test_deferred_regrade.py`: the supporting cell right after a regrade equals the cell after a rebuild.
- **Fix.** Insert the exercised facets inside `_publish_regrade`, before the replay.
- **Meaning.** Plain: the live result now equals the rebuild.
- **Size.** S.

### K5-14. Startup regrades score-only exam imports — CONFIRMED, high
- **Sequence.** `seed-exam-attempts` without answers writes an `exam_evidence` attempt with tier-1 `exam_import` rows and the text `[imported exam outcome: score …]` (`goals/exam_seeding.py:387-400`). Tier 1 is written only by self-grade, the import and the simulator (`attempts/attempts.py:1099`).
  - The deferred-regrade query takes any attempt with live tier-1 rows and no tier-3 rows, excluding only `self_report` (`db/repositories.py:2125-2153`).
  - The sidecar runs that at every vault load once a grading provider is ready (`sidecar/context.py:290`; `ops/startup.py:66-104`). The grader grades the placeholder, and its score replaces the imported one and replays the topic.
- **Narrower.** The import is CLI-only today (SJ-4). The result is a wholesale replacement of real evidence, silently.
- **Ledger.** No row.
- **Fail-first.** `tests/test_deferred_regrade.py`: import a score-only exam and make one real self-grade. Startup submits only the self-grade to the fake grader. The imported score and due date survive.
- **Fix.** Select by self-grade provenance: exclude `exam_evidence`, or rows whose `local_grader_id` is `exam_import`.
- **Meaning.** Plain.
- **Size.** S.

### Refuted or not confirmed

None of the fourteen was refuted. Parts not confirmed: exam review as an answer display (K5-5: it shows feedback and repairs, not the key), and figures, videos and MCP (K5-6: not traced).

## 8. Invariants the next changes must keep

For arc H's H3 (mastery and surprise; I1 already split grade application) and the evidence-packets spec's EP0 (one function per assistance and exposure predicate).

| Invariant | Enforced or tested today | Missing test |
|---|---|---|
| Below the tag, H3 gives the predecessor's results: input order, the attempt's own time, the graded contract on replay | `tests/test_grade_application_golden.py`, `tests/test_grade_application_core.py` (no database, clock or id in the pure core) | The four-arm proof is H2/H3's own work |
| Difficulty: prediction and surprise read the same priming-adjusted difficulty; FSRS keeps its own memory difficulty, hint-capped rating and due date | `attempts/attempts.py:4924-4971`, `:5724-5740`; core tests | FSRS elapsed time across a skipped or held review (K5-8) |
| Held, partly assessed, schedule-only verified and low-confidence grades stay distinct; confidence 0 is legal | `outcome_contract.py:138`, `attempts/attempts.py:4270-4309`; `tests/test_held_grade_evidence.py`, `tests/test_route_rules_in_grader.py:602-636` | Exact 0 across replay (K5-12); an empty ordinary grade off a divergent route (K5-1); a hold released by public adjudication (K5-10) |
| A replacement grade's provenance is the current epoch's, not the first grade's | `attempts/regrade.py:600-660` writes the blind record and identity | Source after a self-to-AI regrade (K5-11) |
| EP0 keeps the assistance predicates apart until the owner picks. Canonical: legacy types, hints or priming (`diagnosis/causal_activity_policy.py:168-199`). Diagnoser history: its own flag plus priming (`diagnosis/split/history.py:226-227`). Intervention outcomes: an allowlist of unaided types (`substrate/intervention_outcomes.py:100-107`), so an `exam_evidence` import counts as assisted there. Two packets: `assisted = primed` (`learner_context.py:1389`, `daily_plan/router_card.py:818`) | EP0's rule: value-preserving moves, a ledger row where copies differ (`docs/specs/spec_evidence_packets_v1.md:91`) | No test pins the four as different |
| Coldness keeps its scope: the submit threshold, an own-key reveal, another retrieval, a delivered passage and an unknown delivery have different effects; replay keeps recorded priming | `attempts/reveal_ledger.py:300-330`, `attempts/coldness_receipt.py:1517-1568`; `tests/test_reveal_ledger.py`, `tests/test_coldness_receipt.py` | That the repair label, the certificate probe, the field metric and the intervention label each obey the claim they name (K5-2, K5-3, K5-4) |
| Certification is decided from the canonical cell and recipe, apart from the probe's validation rate | `goals/goal_certification.py`, `goals/certification_cold_probe.py:1633-1676`; `tests/test_goal_certification_any_of.py`, `tests/test_certification_cold_probe.py`, `tests/test_held_grade_evidence.py:767-818` | Certification right after an adjudication (K5-9); a regrade's embedded credit (K5-13); a probe whose receipt fails (K5-3) |

## 9. Not verified

- **No runs.** Nothing was run: no tests, no app, no rebuild, no model. Every verdict is from reading code. The sequences were not executed.
- **Partly traced.**
  - Figures, explanation videos, MCP, guided redo, hypothesis panels and worked-example links as answer displays.
  - Exam review's feedback as an answer display.
  - The teacher, exam and audit validator callers the review lists in §1, beyond the practice, regrade and teach-back doors.
  - Repair rescheduling (`diagnosis/remediation.py:1216-1282`).
- **Not measured.** How often an owner's figures, worked examples or paraphrases give away a later answer. Whether any owner vault holds a 0.0 grader confidence, an imported score-only exam, or a held grade adjudicated to its own class. The owner's vaults were not opened.
- **Not quantified.** The size of the FSRS shift in K5-8.

## 10. Proposed fix batches

A proposal for the orchestrator and the owner. Batches 1 and 2 are plain fixes that can land now. Batch 3 rides a tag that is already moving. Batches 4 and 5 wait for named steps or decisions.

1. **Now, before arc G: the two high findings, plain, S each.**
   - K5-14: the deferred-regrade query excludes exam imports. `db/repositories.py` (later its store), `tests/test_deferred_regrade.py`.
   - K5-2: the repair label obeys the repair claim. `sidecar/handlers/serializers.py`, the two desktop copy lines and `tests/test_sidecar_remediation_surfaces.py`.
   - Ask the owner one line with it: should a non-attributable pass still close the case?
2. **Now: grading-door and regrade ordering fixes, plain, S each.**
   - K5-1: refuse an empty ordinary proposal, and settle the omitted-criterion rule.
   - K5-13: exercised facets before the regrade's projection.
   - K5-9: the adjudicate CLI replays, and its message is true.
   - K5-10: confirming a held class releases it.
   - Files: `attempts/blind_grading.py`, `attempts/regrade.py`, `cli/grading.py`, `attempts/grade_resolution.py`. K5-9 and K5-10 touch the file `mvp-0.60` rewrites, so they land after it.
3. **With the grade-channel successor: replay provenance, tag.** K5-11 (source from the current epoch; exam channel) and K5-12 (`None`-only fallback). Fold them into `mvp-0.60` if the owner reopens it, else the next grade-channel successor. Both move replay output on existing vaults: a whole-vault rebuild row.
4. **With G6 and a priming successor: displays and the cold scan, tag.** K5-5 (terminal form, inspector key, answer-giving hints), K5-6 (short keys, Reader solution spans) and K5-7 (book solution and family in the scan's target). They change which new attempts are primed or cold, so one successor under the 2026-10-17 rule. This finishes K1 R9's open half.
5. **Owner decides, then H3 or EP0.**
   - K5-8: the FSRS clock rule. A tag, with H3.
   - K5-3: what a certificate probe measures. A policy version and tag. Its all-unassessed abstention can go in batch 2.
   - K5-4: the research readers' rule. With EP0.
