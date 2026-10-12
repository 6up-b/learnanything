# Daily loop: open questions (Q0–Q18)

**Status:** the question list put to the owner on 2026-10-11, saved from that session so the daily-loop spec can be written from it. Each question says what the code did at the time (from two audits), the options and their trade-offs, and the lean at the time.

**Which questions are settled.** Most are now decided by `docs/specs/daily_loop_frictionless_defaults.md`. Where the owner's decision differs from the lean below, the decision wins.

| Q | Status |
|---|---|
| Q0 (how often you open LearnLoop, and what stops you) | Unanswered |
| Q1–Q3 (what a capture becomes; filing; who supplies the answer) | Decided: C1–C3 (saving makes a reference with one-tap "Practice this"; silent LLM filing; background verified solving) |
| Q4 (capture channels) | Decided: C4 |
| Q5 (items from a book before reading it) | **Open** |
| Q6 (intent at capture) | Decided by C2: no decisions at capture; intent is inferred |
| Q7 (which object carries intent) | **Open.** Recommendation: commitments, with goals as optional deadlines |
| Q8 (what "maintain" costs: per-intent recall targets) | **Open.** Recommendation: per-intent recall targets |
| Q9 (finite plan or open list) | Decided: P1 finite plan; P2 auto-advance |
| Q10 (split between maintain, repair and push) | Decided: P3, the system sets the split, shows it and asks nothing (no weekly ratio) |
| Q11 (new material per day) | Partly decided: P3, the system sets the pace within the budget. **The mechanism is open** (N per day vs load-based). PF publishing is capped at 10 a day meanwhile |
| Q12 (per-item time estimates) | **Open.** Recommendation: the learner's own durations, with an LLM estimate as the starting guess |
| Q13 (after a break) | Decided: P6, a small automatic re-entry session with no debt screen |
| Q14 (readiness form) | Decided: P4, minutes only, remembered |
| Q15 (streak) | Decided: P5, **the streak stays** (owner; this overrides the lean below) |
| Q16 (synchronous grading) | Decided: P7 |
| Q17 (after feedback) | Decided: P2 |
| Q18 (sequencing) | Decided: Slice A first, with the daily-loop bug fixes now; the daily-loop track follows Slice A |

The four bugs at the end are being fixed on branch `fix/daily-loop-bugs` (2026-10-11).

---

**Q0. How often do you open LearnLoop now, and what stops you?** Your answer beats my audit at telling which friction to remove first.

### Capture

1. **What happens to something you capture?** Today a single item needs either "write a card" (pick an existing topic and write the answer yourself) or Quick Add (subject, consent ticks, wait for import). Nothing works from outside the app.
   - **Inbox first, process later:** zero friction now, but an unprocessed pile builds up. That's the "capture debt" your intentions doc warns about.
   - **Straight to items, auto-filed:** nothing piles up, but misfiled or bad items pollute the queue.
   - **Hybrid:** processing happens in the background. A capture is filed automatically when it fits an existing topic; otherwise you get one "needs a home" decision in the queue. Tutor-question promotion already works this way.
   - *Lean: hybrid.*

2. **Must you choose the subject or topic?**
   - **Required:** clean graph, but one more decision per capture.
   - **LLM picks it, you correct with one tap:** near-zero friction, occasional misfiling.
   - **"Unfiled" allowed:** zero friction, but weaker diagnosis and transfer later.
   - *Lean: LLM picks it, correctable, with unfiled as a fallback.*

3. **Must you supply the answer?** Take a hard math problem you saved.
   - **You write the solution:** accurate and slow. Sometimes solving it *is* the learning.
   - **The LLM solves and verifies it** (the practice-family track's CAS/solve-first check): fast, occasionally wrong.
   - *Lean: LLM-solved and verified. The first review asks you to solve it, with the verified solution as the key, and an unverified solution can't certify anything.*

4. **Which capture channels first?**
   - **An in-app capture box with a shortcut** for text, URLs and images: cheap.
   - **Photo or image drop-in:** specced in July but not built; needed for problems on paper.
   - **A desktop-wide hotkey:** moderate effort.
   - **Phone capture:** the most valuable for things you meet away from the desk, but it needs either a mobile surface or a cheap route such as a synced "watched folder" on your computer that you drop files into from your phone.
   - **A browser extension:** the most build for the least gain.
   - *Lean: capture box and images first, then the watched folder.*

5. **Should importing a book give you items before you read it?** Today, with the reader on, nothing reaches the queue until you finish sections.
   - **As-you-read only:** right for learning, but a captured book stays invisible in your daily queue.
   - **Plus 2–3 pre-questions before reading:** a well-studied learning effect, and it doesn't treat untaught material as if you'd been taught it.
   - *Lean: as-you-read plus optional pre-questions.*

6. **Ask your intent at capture, or infer it?**
   - **Ask every time:** accurate, but one decision per capture.
   - **Infer from context:** free, sometimes wrong. A hard problem means "keep the solution"; a paper means "reference until opened".
   - *Lean: infer, with a one-tap override you can change later.*

### Intent: learn fully, maintain, or let go

7. **Which object should carry your intent?** Today four mechanisms overlap, and only one fully works:
   - **Topic status:** the queue ignores "dormant" and keeps serving those items.
   - **Retiring an item:** works.
   - **Goals:** "push" effectively means "has an active goal".
   - **Reader commitments:** they have depth presets from "keep in touch" to "master tasks like these", but the live scheduler ignores them.

   Your options for the single control:
   - **Commitments:** the richest option, and already in your intentions' vocabulary, but currently tied to the reader and the shadow planner.
   - **Goals only:** familiar, but deadline-shaped and heavy.
   - **Topic status:** simplest, but too coarse.
   - *Lean: commitments, with goals as optional deadlines on top.*

8. **What should "maintain" cost you?**
   - **Recall targets:** FSRS targets 90% recall for everything. Per-intent targets (say 80% for keep-in-touch, 90% for fluent) cut review load sharply, at the cost of more lapses on low-priority material.
   - **Integrative questions:** your idea of "a few complex questions that refresh many concepts" saves time, but crediting each concept from one answer is unproven.
   - *Lean: per-intent recall targets now; integrative questions as a shadow experiment.*

### Daily plan and attention budget

9. **A finite plan or an open list?** Today the queue is uncapped, the minutes you enter are only displayed, and nothing ends the session.
   - **Finite plan:** "today is 25 minutes, these items", done when done, with a "keep going" option. It's humane and matches your intentions; "keep going" covers good days.
   - **Open ranked list:** flexible, but endless, with backlog anxiety.
   - *Lean: a finite plan that auto-advances from item to item.*

   Sub-decision: promote the existing shadow planner (richer, untested live), or add a simple minutes cap to the live queue (ships in days). *Lean: the simple cap first.*

10. **How is the budget split between maintaining, repairing and pushing?**
    - **Fixed ratio:** predictable, but dumb.
    - **You set it daily:** control, but one more decision each day.
    - **The system decides within a ratio you set weekly:** adaptive, but it has to show its reasoning.
    - *Lean: the third. Overdue maintenance should never take the whole budget; a "lowest recall first" policy lost almost all simulated users in the MaiMemo study.*

11. **How much new material per day?** Today there's no cap: every untouched topic gets an opening probe, and new items add future review load, which your intentions count as a cost.
    - **N new items per day:** blunt, but simple.
    - **Admit new items only while projected review load stays under budget:** principled, but needs time estimates.
    - *Lean: N per day now, load-based later.*

12. **Where do per-item time estimates come from?** None reach the UI today; the shadow planner assumes 3 minutes flat.
    - **LLM estimates when items are made:** noisy.
    - **Your own past durations per item type:** accurate once there's data.
    - *Lean: your durations, with an LLM estimate as the starting guess.*

13. **What do you see after a break?** The welcome-back panel only appears if you have an active goal, and it says "N refreshers" without limiting the queue.
    - **Full backlog:** honest, but overwhelming.
    - **Capped refresher set, rest rescheduled:** humane, but more forgetting.
    - **Triage by intent:** high-intent items first, low-intent ones visibly allowed to fade. This needs Q7 settled.
    - *Lean: triage by intent, with a cap.*

### Session friction

14. **The readiness form every session (energy, sleep, minutes).** Energy and sleep are logged but don't affect what you're served. Keeping them collects data for a future readiness model; dropping them removes a step every day. *Lean: keep only minutes, and remember your last value.*

15. **The streak badge ("practice today to keep your streak").** Streaks build habit (engagement mattered most in the MaiMemo study), but they punish lapses and invite gaming. *Lean: replace it with a forgiving weekly-consistency signal, or remove it.*

16. **Waiting for the grade on submit.** Grading is synchronous, with up to a 180-second timeout. Immediate feedback matters for learning, so making the grade async is worse. Slice 1 already moves diagnosis off this path. *Lean: keep the grade synchronous and set a latency target for the grading model.*

17. **After feedback: auto-advance, or back to the list?** Today the next item is two keystrokes away. *Lean: auto-advance within the plan, with the list one key away.*

### Bugs, not questions (I'd fix these first)

- In the reader, "write my own question" saves to a card store the scheduler never reads, while the UI says "It will return as personal practice." This is from reading the code, not from running it.
- Topics marked dormant or resolved are still served when due.
- The Start screen's "postpone" button does nothing.
- The welcome-back panel's "N refreshers" doesn't limit the queue.

### Sequencing

18. **Where does this sit against M1, practice families and the diff-gate experiment?**
    - **Overlap:** they're closely linked. "Capture a problem; the LLM solves and verifies it" is the practice-family track's verified answer key, and its per-idea memory key is the retention side of Q7–Q8.
    - *Lean: the daily loop first (capture box, one intent control, finite plan, the bugs), with the practice-family track built as the engine behind capture. M1 is offline and can run any time; the diff gate is manual and can run alongside.*
