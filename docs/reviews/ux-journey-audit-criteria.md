# UX journey audit: the criteria

Part 1 of the end-of-queue UX journey audit (owner's brief of 2026-10-31 with its dated additions; walks and synthesis in `docs/reviews/ux-journey-audit.md`). Written 2026-11-18 against main `8c40bd4343`.

This page turns six sources into one checklist that a screen or a persona walk can pass or fail. Each criterion has an id, a one-line rule, and a test that says when it **fails**. The audit's scorecard cites these ids.

**What this page is not.** "No persona picker" is design guidance for whoever designs the overhaul: one product that adapts to the person, with no persona setting, mode or onboarding question. It is not a criterion, and no screen is scored against it.

## How to use it

- **A screen** passes a criterion when none of its "fails if" lines hold. Score each criterion that applies as **pass**, **partial** (fails in one state or one frontend only), **fail**, or **not seen** (the walk never reached it).
- **A walk** is scored through the four questions of the owner's brief (section H): can the person *discover* the journey, *understand* what happened, *recover*, and *stay in flow*.
- **Severity** is by learner impact, not by how hard the fix is:
  - **S1**: the journey cannot be finished, or the screen misleads the learner about their evidence (says "on your own" when help was taken, "ready" when untested, "not in your library" when it is).
  - **S2**: the journey finishes, but only after a long detour, a guess, or help from outside the app.
  - **S3**: friction: an extra step, an unclear word, an inconsistent key.
  - **S4**: cosmetic.
- **Before a finding is written,** check it against the walk harness's fidelity table (`docs/reviews/ux-walk-harness.md`). Rendering engine, native drops, window controls, external links and the network differ from the app. A finding must be about LearnLoop, not about the harness.
- **Where criteria overlap** (they do: Jenson's consistency, Norman's mapping and Nielsen's heuristic 4 are one idea), cite the most specific id and list the others in brackets.

## Sources and how far they were checked

| Source | What was read | Trust |
|---|---|---|
| Scott Jenson, "Are we stuck with the same Desktop UX forever?", Ubuntu Summit 25.10, London, 2025-10-24. Video <https://www.youtube.com/watch?v=1fZTOjd_bOQ>; abstract <https://discourse.ubuntu.com/t/are-we-stuck-with-the-same-desktop-ux-forever/67253> | The abstract (read this run). The talk's quotes are taken from `docs/ux/research_notes.md`, which read YouTube's auto-generated captions in full on 2026-10-12; they were not re-checked against the video in this run. | Captions may carry slips; time codes are caption starts. No human transcript or slides exist online. |
| Scott Jenson's follow-up, "Are we really going to use the same Desktop UX forever?", KDE Akademy 2026, as reported by LWN, "Ideas on modernizing the open-source desktop", 2026-09-23, <https://lwn.net/Articles/1095425/> | The LWN article, read this run. | A journalist's report with quotes. |
| Jenson's posts the talk points to: "How Video Games Inspire Great UX" <https://jenson.org/games/>, "Boring is good" <https://jenson.org/boring/> (2025-09-15), "The Ma of a New Machine" <https://jenson.org/ma/> (2026-04-13) | Read this run. | Primary. |
| Andy Matuschak, *How might we learn?* (May 2024), <https://andymatuschak.org/hmwl/>; his notes on memory systems as listed in `docs/ux/research_notes.md` §3; the owner's copies in `docs/specs/spec_andymatusnotes.md` | The essay's design principles, demo sections and "Two cheers for chatbot tutors", read this run. The notes' quotes come from the research notes. | Primary for the essay. |
| ISO 9241-210:2019, *Human-centred design for interactive systems*, <https://www.iso.org/standard/77520.html> (confirmed 2025) | Catalogue page and the clause headings of section 5 as published in national previews (5.2 and 5.3 confirmed verbatim this run; 5.4 to 5.7 as commonly listed). The standard's text is paid and was not read. | Headings only. |
| ISO 9241-110:2020, *Interaction principles*, <https://www.iso.org/standard/75258.html> | Catalogue page. The seven principles' names are as commonly listed; the text was not read. | Names only. |
| Don Norman, *The Design of Everyday Things*, revised and expanded edition (Basic Books, 2013), <https://en.wikipedia.org/wiki/The_Design_of_Everyday_Things> | Secondary summaries this run, plus the book's well-known vocabulary. | The terms are standard; no page numbers given. |
| Jakob Nielsen, "10 Usability Heuristics for User Interface Design", Nielsen Norman Group, last reviewed 2024-01-30, <https://www.nngroup.com/articles/ten-usability-heuristics/> | Read this run. | Primary. |
| LearnLoop's own principles: `docs/brainstorming/LearnLoop After the Queue (overview).md` §2 (owner's working copy; untracked), `docs/specs/ux_learnloop_v1.md` §0 and §4, `docs/specs/ux_reader_workbench_v1.md` (U1 to U14), `docs/specs/ux_reader_compare_ask_v1.md` (C1 to C10), the owner's rulings of Oct 12 to Nov 18 (named where used) | Read this run. | The owner's own rules: binding. |

---

## A. Jenson: the desktop is a place for doing, learned in loops

The talk is mostly about how open-source teams design. What carries over to LearnLoop is his model of how people learn a tool (the learning loop, borrowed from Raph Koster), his case for a boring consistent base, and his warnings about rushing, settings, and AI that shows off.

> "The user has a mental model and they have an intent. So then they look on the screen and they find an affordance to do their action and they get a result which gives them feedback. And then what happens is you go back the loop and you learn." (talk, 21:56)

| Id | Rule | Fails if… | Source |
|---|---|---|---|
| **J1** | **Start here first.** Each place says what to do first. A journey is a path, not a toolbox. | …a first-time screen (first run, an empty Today, an empty Library, a new book, a new goal) offers several equal actions and none is marked as the way in. …it shows everything at once ("skip, skip, skip"). | [games](https://jenson.org/games/): apps "offer users a large toolbox and let them figure out how to get started"; games "say 'Start here first'". |
| **J2** | **Hints teach in place; dialogs don't stop you.** Teaching happens where the learner already is, a little at a time. | …the app teaches a feature through a modal, a setup banner or a tour that blocks the work. …a hint about the next step is absent where the learner is looking, but present in a manual or a settings page. | [games](https://jenson.org/games/): app hints are "dialog box prompts in your face that stop you dead in your tracks"; games "use hints constantly and patiently". |
| **J3** | **The loop closes where the learner acted.** Intent, affordance, result, feedback, in one place. | …the result of an action lands on another screen, or minutes later, with nothing at the place the learner acted. …an action gives no visible result at all. | Talk, 21:56 (above). |
| **J4** | **One mechanic that grows.** New features extend an existing gesture instead of adding a surface. | …the same intent (ask, compare, capture, teach me) has a different mechanic, label or panel on different screens. …a feature is reachable only through its own new tab, overlay or banner. | [games](https://jenson.org/games/): apps treat "each feature in isolation"; games "build a game through a single mechanic that grows in expressive power". |
| **J5** | **A boring, consistent base.** The same verb, key and place mean the same thing everywhere. | …one key or gesture does two different things in two places, or one action has two names. …a control looks clickable and isn't, or is clickable and doesn't look it. | Talk, 25:54: "this boring base is powerfully consistent… we always underestimate how important consistency is." |
| **J6** | **Don't rush; say no.** The main path serves the common case. Rare cases are handled when they happen. | …a main-path screen asks about a case that only *might* matter (a token budget, a page range, a source role) before it is needed. …a screen grew a control per feature with no grouping. | Talk, 24:13: "the most common product mistake is rushing… put in more menu items, put in more icons." Akademy 2026 (LWN): "The fastest way a UX designer can save your team time is to help you say no." |
| **J7** | **Settings are a cost, and so is their absence.** Good defaults; options there when truly needed. | …finishing a journey requires visiting Settings. …a choice the learner really needs can't be found from the place it affects. …Settings holds retired utilities that no longer do anything. | Talk, 5:44 ("UX designers in general don't like… settings"); the owner, Nov 8: clear the settings page of deprecated utilities. |
| **J8** | **Mature technology looks like infrastructure.** Show the model where it matters to trust; never show the pipeline. | …pipeline words reach the learner (extraction, inventory, synthesis, enrichment, proposal, route, provider) on a main path. …model text is not marked as the model's where trust depends on it. | [Boring is good](https://jenson.org/boring/): "a mature technology doesn't look like magic; it looks like infrastructure"; "The user has no idea an LLM is even involved; they just get better results." |
| **J9** | **Change gently.** Keep muscle memory through a redesign. | …a renamed or moved feature is not findable under its old name (palette, keyboard help). …a key the owner uses daily changes meaning without notice. | Talk, 9:36: "How do you roll it out in a way that is sensitive… and can be done slowly." |
| **J10** | **The app holds the learner's working memory.** What was set aside, where they were, what they typed, comes back. | …leaving a screen loses a draft, a selection, a position or a half-built comparison. …the way back to where the learner was is a search, not one step. | Akademy 2026 (LWN): "the curse of direct manipulation… If you copy a few too many things to the clipboard, oh sorry, it's gone." |
| **J11** | **Invite a pause; never force one.** | …a stop or rest suggestion is a modal, a countdown, a guilt line or a repeated prompt. …the app runs at constant urgency (timers, pulsing, counts) with no natural break. | [The Ma of a New Machine](https://jenson.org/ma/): "We need interfaces that naturally invite a pause without forcing it." |
| **J12** | **The tool fits the task, not a generic chat.** Model help shows up shaped for the task, with something to review and edit. | …the only way to get model help on a task is an open chat box detached from the work. | [The Ma of a New Machine](https://jenson.org/ma/): "The real breakthroughs will come when the tool molds itself to the task." Akademy 2026: chatbots that operate on screen contents "miss the point". |

## B. Matuschak: guided learning inside authentic contexts

> "we bring guided learning to authentic contexts, rather than thinking of it as a separate activity" ([*How might we learn?*, design principles](https://andymatuschak.org/hmwl/))

The essay's four principles are: bring guided learning to authentic contexts; suffuse explicit learning with authentic context; strengthen both domains; make sure learning actually works. The demos add tractable immersion, guidance in action, synthesized dynamic media, contextualized study, practice and memory, and social connection. Persona 4 (the project-driven learner) is the closest test of the essay.

| Id | Rule | Fails if… | Source |
|---|---|---|---|
| **M1** | **Help arrives inside the task.** In the book, the problem, the project: not in a separate place. | …getting help means leaving the passage or problem for another screen with no way back to the same spot. | Design principles; "This AI system isn't trapped in its own chatbox, or in the sidebar of one application." |
| **M2** | **Study is framed by the learner's aim.** Reading and practice say what they are for (the exam, the project, the question the learner asked). | …a plan, a question or a lesson can't say which goal or interest it serves. …a goal the learner typed is not visible where the work for it happens. | "Suffuse explicit learning with authentic context": the AI "grounds all the reading and practice Sam's doing in their actual aims." |
| **M3** | **A personal path through a big book,** with reassurance about what can wait. | …a large source arrives as one undifferentiated list of chapters. …the learner can't see why a section is on, or off, their path. | Contextualized study: "they don't necessarily need to read this entire thousand-page book right now… It's made a personal map in the book's table of contents." |
| **M4** | **The system schedules; a daily ritual holds practice.** | …the learner must assemble their own review. …returning after a gap shows a backlog instead of a short way back in. | Practice and memory: "Central to this is the idea of a daily ritual, a vessel for practice." Note [SRS can program attention](https://notes.andymatuschak.org/zB92WZZ5baBHKZPPbWMbYEv). |
| **M5** | **The learner steers practice** on the question itself: edit, not now, this is wrong, too easy. | …steering a question needs another screen (a review queue, a registry). …"not now" reads as a final, destructive decision. | Dynamic practice: "it's important that Sam can steer them with feedback"; notes [give readers control over prompts](https://notes.andymatuschak.org/z8kPkXQZ3wVR5DfJ79uhnuz), ["not right now"](https://notes.andymatuschak.org/zJ5Yzvba2729XKXivBBZ91J). |
| **M6** | **Make sure learning actually works.** Later retrieval, not exposure, is what counts; the app says so. | …reading, a lesson or a figure is presented as if it proved the learner can do it. …nothing comes back later to check. | "Make sure learning actually works"; "Each time you reinforce the memory this way, you forget it more slowly." |
| **M7** | **No deficit framing.** The tutor and teacher start from what the learner is trying to do. | …copy describes the learner as lacking ("weak", "you don't understand"). …a tutor or lesson ignores the goal or passage the learner came from. | Two cheers for chatbot tutors: they "view me as defective until I say the right things" and "aren't interested in what I'm trying to do." |
| **M8** | **View source on request.** Workings are one step away, never in the way. | …the reason for a plan, grade or figure can't be reached from the thing itself. …the workings sit on the main path by default. | Synthesized dynamic media: "Sam can just 'view source' to tinker with this figure." |
| **M9** | **Remembering is a lightweight gesture; the inbox is trusted.** | …capturing something takes more than a few seconds or leaves the current task. …captured things pile up as an intimidating count. | Notes [SRS make memory a choice](https://notes.andymatuschak.org/zSTqsQ4ATXB61k3Z43TforN), [inboxes only work if you trust how they're drained](https://notes.andymatuschak.org/zGKqPvetpYbvbXmPmuuvfx8), [beware automatic import](https://notes.andymatuschak.org/zL2SPWGitsD4TruNYBzSZ7s). |
| **M10** | **Strengthen both domains.** Learning connects back to doing: the project, the exam, the outside work. | …what was learned can't be carried back to the task it was for (a project, a deliverable). …the app has no place for "I did the thing; here's what happened". | "Strengthen both domains"; tractable immersion. |

## C. ISO 9241: process and interaction principles

**ISO 9241-210:2019, section 5** names six principles of human-centred design (5.2 and 5.3 checked verbatim; the rest as commonly listed). They judge the audit and the overhaul as a process, not single screens:

| Id | Principle | How this audit applies it | Fails if… |
|---|---|---|---|
| **I1** | The design is based upon an explicit understanding of users, tasks and environments (5.2). | Eight personas, each with a goal, materials and a device. | …a proposed fix serves no named persona's step. |
| **I2** | Users are involved throughout design and development (5.3). | Persona walks before and after the overhaul (owner, Nov 9). | …a fix stage lands without re-running the walk it came from. |
| **I3** | The design is driven and refined by user-centred evaluation (5.4). | Findings cite a walk step or a code location, never taste alone. | …a finding has neither. |
| **I4** | The process is iterative (5.5). | Fix stages in waves per area (owner, Nov 18). | …the plan has one big-bang stage. |
| **I5** | The design addresses the whole user experience (5.6). | Desktop, phone, terminal app and chat, and the transitions between them. | …a journey is judged on one frontend when the learner uses several. |
| **I6** | The design team includes multidisciplinary skills and perspectives (5.7). | Persona agents judge as learners; the analyst reads code; the owner decides. | — |

**ISO 9241-110:2020** names seven interaction principles. They apply to a single screen and overlap Nielsen; use them where Nielsen has no match:

| Id | Principle | Fails if… |
|---|---|---|
| **I7** | Suitability for the user's tasks | …the screen makes the learner do work the task doesn't need. |
| **I8** | Self-descriptiveness | …the learner can't tell from the screen where they are, what they can do, and what state things are in. |
| **I9** | Conformity with user expectations | …a control behaves unlike its look, its label, or the same control elsewhere. |
| **I10** | Learnability | …a second use is no easier than the first (nothing taught, nothing remembered). |
| **I11** | Controllability | …the learner can't pause, leave, undo or change pace (the plan's minutes, a lesson, a long job). |
| **I12** | Use error robustness | …a slip loses work, or can't be undone. |
| **I13** | User engagement | …the screen gives no reason to come back (Matuschak's emotional connection; Jenson's "fun is just another word for learning"). |

## D. Norman: making what's possible visible

From *The Design of Everyday Things* (2013). The two goals are **discoverability** (can I tell what actions are possible?) and **understanding** (what does it all mean, how is it meant to be used?).

| Id | Concept | Fails if… |
|---|---|---|
| **N-D** | **Discoverability** | …a journey has no visible entry (keyboard only, behind a switch, palette only, CLI only). This is the audit's central test (inventory mark). |
| **N-S** | **Signifiers** (the cue that shows where to act) | …an action's only cue is a hover, a key hint in a footer, or text styled as plain text. …a clickable element has no role or name for a screen reader. |
| **N-F** | **Feedback** (immediate, informative, not too much) | …an action shows nothing for more than about a second. …a wait shows no end or no estimate. …a failure shows no reason. …feedback buries the one thing the learner needs under detail. |
| **N-C** | **Conceptual model** | …the learner's picture of the app (books, a plan, my evidence) can't be built from the screens: words for one thing change, or two things share a word. |
| **N-M** | **Mapping** | …a control sits far from what it affects (a book's setting only in global Settings; a goal edited only from another screen). |
| **N-K** | **Constraints** | …the app lets the learner start something that will fail (a disabled button with no reason, a required field that can't be filled). |

## E. Nielsen's ten heuristics

| Id | Heuristic | Typical LearnLoop failure |
|---|---|---|
| **H1** | Visibility of system status | a background build, a grade or a figure with no state, or "could not confirm whether this action completed" |
| **H2** | Match between the system and the real world | internal words; book order and course order not the learner's |
| **H3** | User control and freedom | no clearly marked exit from a lesson, a check, a wizard; no undo |
| **H4** | Consistency and standards | one action, two names; one key, two actions |
| **H5** | Error prevention | a flow that lets the learner skip a step it later requires |
| **H6** | Recognition rather than recall | a feature reached only by a remembered key or command |
| **H7** | Flexibility and efficiency of use | the owner's shortcuts gone, or novices forced through shortcuts |
| **H8** | Aesthetic and minimalist design | receipts, numbers, lanes on a main screen |
| **H9** | Help users recognize, diagnose and recover from errors | an error that names a code, not the problem and a fix |
| **H10** | Help and documentation | no in-place way to learn what a control does |

## F. LearnLoop's own principles (binding)

| Id | Principle | Fails if… | Where the owner said it |
|---|---|---|---|
| **O1** | **Frictionless by default, a glass box on demand.** The main path asks for no decision LearnLoop can make itself; every decision is inspectable under *why?* / *details* / Under the hood. | …a main-path screen asks for a choice with a safe default. …it shows receipts, lanes, versions, probabilities or model names unasked. …a decision has no *why?* at all. | Oct 13 ruling after the tester session; overview §2.2; `ux_learnloop_v1.md` §0 |
| **O2** | **Honest labels, generous defaults.** LearnLoop assumes what the learner says and checks it later; it auto-applies with undo. The words *untested*, *assumed known*, *worked with help* and *demonstrated on your own* stay distinct everywhere, never blended into a percentage. | …a learner step exists only to protect the model. …"ready" or a percentage stands in for evidence. …two of the four states share a word or a mark. …a readiness message says one state ("not in your library yet") for several (material imported, topics still being built, scope needs review). | Overview §2.1; student audit finding 6 (Nov 14) |
| **O3** | **No jargon.** No LO, facet, probe, EVSI, certification, diagnosis machinery, lanes, routes or pipeline stages on a learner surface. | …any such word is visible without opening *details* or Under the hood. | Overview §2.2 (the deny-list test) |
| **O4** | **Learner text over skip buttons.** No "I don't know" button; the learner writes what they can, and the text is used. | …a control lets the learner skip a question without writing (a "skip" that is not "not now"). …learner text is collected and visibly goes nowhere. | Oct 12 ruling; overview §2.4 |
| **O5** | **Quiet navigation.** No red badges, no counts of waiting things, no "overdue", nothing that takes focus, animates or jumps on its own; a return is a link, never a jump. | …a count, badge, "overdue" or red mark appears. …focus moves or a pane scrolls without the learner's act. | Overview §2.2; C5 in `ux_reader_compare_ask_v1.md`; U5, U12 |
| **O6** | **Help is never certification, and it says so first.** Taking help changes the attempt to practice with help; the learner is told before, not after. | …help during a cold check converts the attempt without saying so first. …an assisted answer is shown as "on your own". …help is blocked to protect a measurement. | Overview §2.3; U4, U11 |
| **O7** | **Teach and ask go to the right place.** A control that asks to be taught, or to learn a topic, opens a Teacher lesson; a control that asks a question about the item, note or passage on screen opens Ask tutor. | …a label promises one surface and opens the other, or opens nothing. | Owner, Nov 14 |
| **O8** | **No model available is a plain state.** Not signed in, provider down or budget spent: each screen says what still works and what to do. | …a model-backed action spins, fails silently, or shows a code. …a feature disappears instead of saying why. | Brief, Nov 14 conditions; the plan-first transport (Oct 21) |
| **O9** | **The learner can disagree, once, and it is remembered.** Contest a grade, correct a topic mapping, "not now", "I know this", undo an applied change. | …disagreeing takes more than one step, or the same thing comes back unchanged. | Brief, Nov 14 conditions; `ux_learnloop_v1.md` N10 |
| **O10** | **Three voices, and the book is the reference.** Book, LearnLoop's model and the learner look different; the book's words come first; sources keep their identity. | …a sentence's author can't be told at a glance. …a model explanation sits above an available quote from the learner's book. | Overview §1, §11; U7, U8 |
| **O11** | **Help shows what it gave away.** When help showed part of an answer, feedback quotes the text that gave it away, per rubric criterion. (Wording and placement are this audit's design question.) | …feedback says "with help" without saying which help, or which part of the answer it covered. | Owner, Nov 18 (decision 2) |

## G. The Reader's own rubric

Every Reader walk is also scored against the workbench spec's **U1 to U14** (`docs/specs/ux_reader_workbench_v1.md` §1, written as screenshot tests) and the compare spec's **C1 to C10** (`docs/specs/ux_reader_compare_ask_v1.md` §1). They are cited by id and not restated here. The ones most walks will touch: U1 (return, more capable), U5 (quiet by construction), U9 (waiting never blocks reading), U11 (cold is honest), U12 (threads, never debt), C1 (one comparison whatever the door), C5 (navigation is quiet).

The figures journey (owner, Nov 12) is scored on every request state, from `docs/reviews/k10-figures-map-2026-11-12.md` §8: waiting and the wait estimate, partial, failed and why, refused, stale (N-F, H1, U9).

---

## H. The checklist

One list per journey and per walk. Each line names the criteria it stands for.

### Discover: can a first-time learner find it from the screen alone?

1. There is a visible control that starts the journey, in the place the learner would look (N-D, J1, H6).
2. Its label says what will happen, in the learner's words, and it opens what it promises (I9, O7, O3).
3. Pointer and keyboard both reach it; the key is shown where the control is (H7, N-S).
4. It is not hidden behind a switch whose default is off, or the screen says where to turn it on (N-D, J7).
5. Nothing on the way asks a question with a safe default (O1, J6).
6. The same intent uses the same verb, key and panel as elsewhere (J4, J5, H4).

### Understand: does the learner know what happened?

7. Every action gives feedback within about a second, where the learner acted (N-F, J3, H1).
8. Every wait has an honest state: what's happening, roughly how long, and that the learner can keep going (U9, H1).
9. Failure says what failed, why, and one next step; no codes (H9, O8).
10. No model available, refused, stale and empty each have their own words (O8, H1).
11. Evidence words are the four honest ones, never blended, never a percentage (O2, O6).
12. Who wrote each sentence is visible: book, model or learner (O10, J8).
13. No jargon on the surface; the workings are one step away (O3, O1, M8).

### Recover: can the learner undo, go back, and find their place?

14. Every detour has a way back to the exact place it came from, in one step (U1, J10, H3).
15. Applied changes can be undone; "not now" is not final (M5, I12, O9).
16. A draft, selection or half-done task survives leaving and coming back (J10, I12).
17. Disagreeing (a grade, a topic mapping, "I know this") takes one step and is remembered (O9).

### Stay in flow: does the app respect attention?

18. LearnLoop's own suggestions are ignorable at no cost: no modal, no focus theft, no animation (U5, O5, J11).
19. No counts, badges, red or "overdue" (O5, U12).
20. Help arrives inside the task, framed by the learner's aim (M1, M2, J12).
21. Stopping is offered, never forced, and "keep going" is one step (J11, I11).
22. Coming back after a gap is a thread to pick up, not a debt (M4, U12).

### Signs to look for in a walk (the analyst's log, not the persona's report)

People misreport. Check the persona's account against `analyst/steps.jsonl` and the screenshots for:

- a long gap before an action (the person was looking for something);
- the same screen looked at twice, or scrolled back and forth;
- backtracking: a step undone, a screen left and re-entered;
- one control clicked twice, or a click with no visible result;
- failed calls and console errors the person never saw (`analyst/console.jsonl`, `analyst/bridge.jsonl`);
- a feature the inventory shows exists but the person never found (an invisible feature, not a missing one).

Each is evidence for a Discover or Understand line above, and is cited by walk name and step number.
