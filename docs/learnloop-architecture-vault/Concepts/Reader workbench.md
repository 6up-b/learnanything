---
title: Reader workbench
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
last_reviewed: 2026-11-23
source_commit: 9038b096e7446d5f433f95d881de7e7c1bd0da15
source_commit_timestamp: "2026-11-23T19:57:34-05:00"
source_paths:
  - apps/learnloop-tauri/src/screens/desks
  - src/learnloop/desks
  - src/learnloop/pads
  - src/learnloop/passage_union
  - src/learnloop_sidecar/polled_jobs.py
  - src/learnloop/curriculum/goal_lens.py
  - src/learnloop/notebook_runtime
  - src/learnloop_sidecar/handlers/video.py
tags:
  - learnloop/concept
  - learnloop/reader
---

# Reader workbench

The desktop Reader can open as desks or as the old Reader. A desk is a saved strip of slots. A slot holds one window or a pair, and one window has focus. Windows hold typed references to sources, videos, panels, threads, pads or lessons. A pad stack can show several pads and lessons in one window. The shelf navigates the strip. The overview lays out cards across desks, shows their links and lets the learner gather related windows. See [[Reference/Desktop/TypeScript/screens/desks/DeskShell|DeskShell]] and [[Reference/Modules/learnloop/desks/content_ref|ContentRef]].

## Window lifecycle

An active window owns input, selection and capture. Other visible windows may work and receive a press that makes them active. Offscreen windows, windows on a hidden desk and overview previews are paused. Paused content is inert. Its media pauses, and work that uses the window lifecycle waits before starting or polling again. Each video accepts clock messages from its own frame. A preview never records a reading visit or progress. Windows already mounted are keyed by window id. Reordering, pairing or entering focus mode keeps the window's component mounted. See [[Reference/Desktop/TypeScript/screens/desks/lifecycle|Lifecycle]] and [[Add a window kind to the workbench]].

## Writing and saved state

The desktop applies desk and pad ops optimistically. Each vault and transport has a store with an in-memory outbox. Desk, pad and ink writes share one ascending sequence per client. The sidecar commits each accepted batch with its receipt. An identical retry returns that receipt. Each op has its own result, so one refusal or stale head can leave other ops in the batch committed. Desk ops that check versions name the desk they were intended for. A transfer checks the destination too. Pad edits check the block head and anchor changes check the link's own head. Stack membership ops and ensuring the running pad have their own idempotent or commuting rules. See [[Reference/Modules/learnloop/desks/protocol|Write protocol]] and [[Debug a workbench write]].

A pad is a workspace for the learner's writing. Its blocks can also hold quotes, source pieces, figures, sketches, cells and ink. Edits and removals append versions. The standing head supplies the block's body, provenance and position. An anchor is a separate link or unlink event. Lift-out leaves a stub and carries the block's links and writing history into the new pad. An ordinary editor edit names a keep-both block. If the expected head is stale, the service leaves the newer head in place and saves the edit as a marked sibling. See [[Reference/Database/Tables/pad_block_versions|Block versions]], [[Reference/Database/Tables/pad_block_anchors|Block anchors]] and [[ADR-021 Keep both conflicting pad edits]].

## When pad words leave the pad

A saved version is workspace history. Writing by itself never grades an answer or updates ability, scheduling or certification as an attempt. There are two exits for the learner's words.

- **Emission as learner text.** On vaults with `pad_text` enabled by the algorithm tag and learner-text gaps enabled in config, a committed wording of a learner text or note block, ink transcription or learner correction can queue gap analysis. The job freezes the wording and context. Moving the same words does not emit them again. An edit supersedes the old reading and removal retracts it through reversal rows. This is the learner-text lane of [[Evidence and Measurement]]. See [[Reference/Modules/learnloop/pads/emission|Pad emission]].
- **Explicit submission.** `pad.submit_block` freezes a named version and hands it to the existing attempt or teach-back entry point. It checks provenance and refuses a whole sentence copied from a quote or linked passage. The durable submission id links the frozen version to the attempt or the reserved teach-back conversation. The grading path owns the resulting evidence. See [[Reference/Modules/learnloop/pads/submission|Block submission]] and [[Reader Tutor and Teach-Back]].

Cell code and output, plain ink strokes, sketches, figures and quoted source or tutor words never qualify as the learner's text on either path. A transcript or correction attached to an ink block is eligible by its provenance. A carried question stays in its own workflow. Its marker can return next to the original passage or a judged correspondent in another open reading.

## Reading across the desk

`passage.union_range` joins what is tied to a range of source spans or transcript times. It gathers annotations, pad links, notes, question events and adjustments, gap placements, passage links, figures, authored questions, exposure and due-check ids, with coverage at section level. It can place links from another extraction using span aliases and mark links that need re-anchoring. A source window can show backlinks without opening their pads. The union is a read model. It writes nothing, and import fences keep it out of graders. [[Workbench protection]] explains what the union's withheld flag means. See [[Reference/Modules/learnloop/passage_union/union|Passage union]].

The companion follows the active window or selection and can be summoned there or at a dock. Threads belong to the desk in the desktop, while question and answer history is stored in the vault. The desktop waits for queued workspace writes before sending an ask. The server grounds it in its reading, using a linked pad block's place when available, and records the desk and selection context with the exchange. Citations can open beside the reader, and a thread can become its own window. The goal in view is a display cue. It never enters the companion prompt through that cue. See [[Reference/Modules/learnloop_sidecar/handlers/companion_ask|Companion Ask]] and [[Reference/Database/Tables/companion_exchange_context|Exchange context]].

Long requests return a job id. The desktop poller coalesces reads by key, pauses a window's registrations with that window and backs off on failure. The sidecar looks up jobs and request ids by vault. The job captures the background epoch for liveness at close. Switching vaults interrupts the previous vault's unfinished polled jobs. A request that was already sent can finish and record facts in its original vault without waking workers in the new context. See [[ADR-022 Scope polled jobs to vault and epoch]].

## Menus and the goal lens

The context menu identifies the object under the pointer or at the keyboard target. Fixed verbs depend on the object. Promoted rows use the union read and stored passage links first, then a polled job can add correspondents and search findings. A single server ranker limits the result to four. Opening, dismissing or marking a row wrong writes a label. Pad proposals and promoted rows can point to a passage without turning the suggestion into practice or evidence. The practice sheet for a source exercise shows its words before import, then offers edit and retire on items already admitted to the queue. See [[Add a menu verb]] and [[Reference/Modules/learnloop/passage_union/promoted|Promoted rows]].

The goal lens reads the actual goal, path, coverage and readiness. It marks mapped sections, leaves unmapped work visibly uncertain and exposes a path and the reason for a level. Its read never serves a check, grades an answer or calls a model. The lens can show a check is due and mask labels and explanations that would cue it. Due-check protection applies across goals. RD7's inline checks and reading and pad veils are absent. See [[Workbench protection]] and [[Reference/Modules/learnloop/source_retrieval/goal_lens_reads|Goal lens reads]].

## Ink, lessons and notebooks

Pen mode recognizes passage marks and margin notes. Ink can belong to a reading, an annotation or a pad block. Saved marks can be placed again against the reading's anchored words. Nearby margin strokes on the same passage can form one note. Ink saves and erases use the write sequence. Optional transcription is a separate polled job. A result for obsolete strokes does not replace the current wording. A margin-note reading that arrives after a manual edit is offered beside the edit. RD8b's freeform ink hint context, line check and hint ladder are absent. Freewriting can reach the companion through the pad menu. See [[Reference/Desktop/TypeScript/screens/desks/pen/PenLayer|Pen layer]] and [[Reference/Modules/learnloop/pads/ink_transcribe|Ink transcription]].

A Teacher lesson can occupy a window or be a tab in a pad stack. Reopening a finished lesson reads its recorded review. Notes under a lesson use its additions pad and ordinary pad writes. The window holds an unserved Teacher quick question for the full lesson screen. See [[Reference/Desktop/TypeScript/screens/desks/lesson/LessonPaper|Lesson paper]] and [[Workbench protection#Lesson tabs and remaining gaps]].

A pad runs its marimo cells in one notebook session, with a derived file under the vault's `.learnloop/notebooks/pads` generated from saved block heads. An edit can go to the same kernel. Changing the cells' order or membership changes the session revision. An existing lesson can show a vault-supplied `notebooks/lessons/<lesson id>.py` in place of the lesson body. Its nearby notes still go to the additions pad. Notebook lesson authoring and RD9c's lesson redo and amendment are absent.

The runtime supervises marimo inside a sandbox. The sandbox has no writable host path. The host creates the listening socket and passes its descriptor into the sandbox. The frame uses a per-session loopback proxy with its own origin, a secret URL path and a restrictive content policy. Bridge messages are checked against the frame's window and origin and treated as untrusted text. A lesson notebook's disabled cells are held. While the lesson is open, a nonempty value on an allowed commit control can release the cells belonging to that commit point. A closed lesson releases nothing further. This gates display only. The notebook's Python can inspect its own cells and credential, and a commit is never practice evidence. See [[ADR-020 Keep notebook session files on the host]] and [[Reference/Desktop/TypeScript/screens/desks/notebook/NotebookFrame|Notebook frame]].

## Video

Each desk follows its own most recently played video. A book window uses the transcript section, the accepted chapter and the book's judged correspondents to show the current connection. The link can be turned off. Only playing scrolls the book. The follow read uses neither a model nor the search fallback. The timestamp shortcut writes a source quote anchored to the active cue when one is available.

Chapter suggestions run on request through the coverage judge's route and are stored in `video_chapters`. A decision accepts or dismisses a suggestion once. Only accepted chapters mark the scrub track and supply the named chapter to follow-along. Suggestions and decisions are workflow data. See [[Reference/Modules/learnloop_sidecar/handlers/video|Video RPCs]], [[Reference/Database/Tables/video_chapters|Chapter records]] and [[Workbench protection#Follow-along and chapters]].

## Words a learner reads

The owner settled the workbench's nouns on 2026-11-23: companion, pad, saved question, cold check. Code names stay as
they are (`carried_*`, the scratchpad classes, the `carry` verb id); only what a learner reads follows the glossary.

| Word | What it names |
|---|---|
| **pad** / **pads** | A writable page on a desk, and the window that stacks them. A desk's own pad is the **running pad** (one name: its stored title "running" is shown as "running pad"). |
| **saved question** | A question set aside for later; it may come back beside a related passage. The act is **save for later** (the menu's verb, a pad line's "? save for later", the drain's "save for later “…”"). |
| **companion** | The ask surface: where questions are asked and answered on the desks. **The tutor** still names who answers ("the tutor's words", "the tutor asks, as a student would"), never the surface. |
| **cold check** | A check on your own, with nothing open that could give the answer away (the inline card, the path's dates, What this knows). |
| **quick check** | A section's optional question while reading (the Guide's). Not a cold check. |
| **quick question** | A lesson's question asked on the lesson screen. Not a cold check either. |

Two scans keep the retired words out: `screens/desks/workbenchNouns.test.ts` (the desks and the lesson view) and
`tests/test_workbench_nouns.py` (the desks' handlers' messages). The record is in
`docs/reviews/reader-workbench-copy-audit.md` §3.

