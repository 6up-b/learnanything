# Daily loop: frictionless defaults

**Status:** owner decisions, 2026-10-11. This is a short decision record, not a full spec. A daily-loop spec will build on it.

**The principle: honest labels, generous defaults.** Never add a step for the learner just to protect the model. Label what is assumed versus demonstrated, and check assumptions inside ordinary practice instead of in separate ceremonies. This follows `docs/brainstorming/LearnLoop_User_Intentions_v2.md`:
- sensible defaults and progressive disclosure (§3);
- capture without debt (§3, acceptance criterion 1);
- diagnose only when it improves what happens next (§11);
- honest limits in what is *claimed* (§12);
- agency (§13).

It supersedes the older "evidence first" rules where they made the learner do extra work. Invisible engineering rules stay: blind grading, replay, kill switches, spend caps and sandboxing.

---

## Decisions

### Capture

| # | Decision |
|---|---|
| C1 | **Saving makes a reference; no practice begins.** LearnLoop may *suggest* practice, and one tap ("Practice this") adopts the capture into practice (acceptance criterion 1) |
| C2 | **No decisions at capture.** Filing under a subject or topic happens silently in the background, by LLM, correctable later with one tap. There is no "needs a home" step. If nothing fits, the capture is kept unfiled and still searchable |
| C3 | **Answers are worked out in the background.** For a captured problem, the LLM solves it and the solution is verified (Slice 2 §5.3 verified-reference rules). Adopting it into practice makes the first review "solve it", with the verified solution as the key. An unverified solution never certifies anything |
| C4 | **Capture channels, in order:**<br>• an in-app capture box with a shortcut (text, URL, image);<br>• image drop-in;<br>• phone capture over the tailnet (`spec_mobile_tailnet_v1.md`);<br>• the browser extension last |

### Starting new material (see `spec_learner_field_v1.md` §5.2)

| # | Decision |
|---|---|
| S1 | **No opening probe for every new topic.** New material starts as learning, ordered by prerequisites and predicted difficulty. The first practice answers are the placement |
| S2 | **Assume known when it's likely, and check later.** A topic the learner says they know, or that early answers or the active predictor say is likely known, is marked **"assumed known (not tested)"**. It goes straight into maintenance with a long first interval, and that first review is the check. Failing it quietly returns the topic to learning |
| S3 | **"Too easy" and "I don't know this" act immediately** on any item. They are routing preferences, labelled as such |
| S4 | **A "Check what I already know" quick check is available but never required** |
| S5 | **Your questions and hints are the placement signal** (owner, 2026-10-11).<br>• Tutor questions while reading, hints and their timing, and questions after feedback show where you're shaky. Those topics are taught first and never fast-tracked.<br>• Asking never lowers your record. It only changes what you practise next (`spec_learner_field_v1.md` §3.1) |

### The daily plan

| # | Decision |
|---|---|
| P1 | **A finite plan**: today is N minutes of these items, done when done, with "keep going" if wanted |
| P2 | **Auto-advance** from feedback to the next planned item; the list is one key away |
| P3 | **The system sets the split** between maintain, repair and push, and the pace of new material, within the budget. It shows them and asks nothing |
| P4 | **No readiness form.** Session minutes are remembered and changed with one tap. Energy and sleep sliders are removed |
| P5 | **The streak stays** (owner decision) |
| P6 | **Re-entry after a break** is a small automatic session of the most useful checks and reviews. There is no debt screen (acceptance criterion 7) |
| P7 | **Grading stays synchronous** for immediate feedback. Slice 1 moves diagnosis off the request path |

### Reviews and chores for the owner

| # | Decision |
|---|---|
| R1 | **No review queues as a default workflow.** Practice families are auto-accepted when confident, with undo (Slice 2 §5.2). Quality checks use LLM judges plus signals the learner produces anyway: skips, "too easy", contests, retires. At most one optional 10-minute rating per check |
| R2 | **Phone answers by photo or voice are graded immediately**, with the transcript shown beside the grade and one-tap correction and regrade (`spec_mobile_tailnet_v1.md` §6.6) |
| R3 | **Project understanding defaults to delayed questions** on agent-written code inside the daily plan. The accept-time explanation gate is opt-in (`spec_project_understanding_v1.md`) |

### Known bugs to fix first (from the 2026-10-11 audit)

- The reader's "write my own question" saves to a card store the scheduler never reads, while the UI says "It will return as personal practice".
- Dormant or resolved LOs are still served (`scheduling/scheduler.py:212`).
- The Start screen's "postpone" button has no handler.
- The welcome-back panel's "N refreshers" doesn't limit the queue.

### Still open

- Q7: which object carries intent. The recommendation is commitments, with goals as optional deadlines.
- Q8: per-intent recall targets.
- Q12: the source of time estimates. The recommendation is the learner's own durations with an LLM prior.
