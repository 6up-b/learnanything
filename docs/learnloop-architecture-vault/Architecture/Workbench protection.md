---
title: Workbench protection
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
last_reviewed: 2026-11-23
source_commit: 9038b096e7446d5f433f95d881de7e7c1bd0da15
source_commit_timestamp: "2026-11-23T19:57:34-05:00"
source_paths:
  - src/learnloop/content/sources/exam_material.py
  - src/learnloop/passage_union
  - src/learnloop_sidecar/workbench_protection.py
  - src/learnloop/pads/proposals.py
  - src/learnloop/curriculum/goal_lens.py
  - src/learnloop/source_retrieval/goal_lens_reads.py
  - src/learnloop_sidecar/handlers/goal_lens.py
  - src/learnloop_sidecar/handlers/video.py
  - src/learnloop_sidecar/handlers/lesson.py
  - apps/learnloop-tauri/src/screens/desks
  - docs/reviews/refactor-bug-ledger.md
tags:
  - learnloop/architecture
  - learnloop/reader
  - learnloop/assessment
---

# Workbench protection

The [[Reader workbench]] has two protections. Exam and held-out marks govern whether a passage can be used as material by a surface. A due check governs how the workbench names what the check covers. Use [[Privacy and Trust Boundaries]] for the wider exam surface policy.

## Passage reads, menus and proposals

| Surface | What the code withholds |
|---|---|
| `passage.union_range` | Uses `exam_withheld` to set each affected span's `exposure.withheld`. The union does not carry the passage body. Its word-bearing rows (stored quotes, authored questions, passage links, carried questions, exchanges, margin notes and highlights) follow their own origins through the menus' withholding (`_withhold_rows`, BATCH5-3): a row whose words come from protected material is not returned. Due checks anchored here contribute commitment ids only. |
| `passage.content` | Uses the same exam predicate and sets the affected spans' text to null. It still returns source and section metadata. The pad's source-piece action and the exercise import sheet stop on a withheld reply. |
| `passage.promoted` | Checks the clicked passage and every passage that supplied selected words, including passages named in pad payloads, links and ancestry. A withheld object supplies no query text for search by meaning. Stored links are filtered at both ends, correspondents skip protected origins, and retrieval excludes protected passages and rejects protected hits before judging. The menu can still show navigation rows with neutral labels. Text in learner rows follows its own origins. |
| `passage.knows` | Refuses a protected menu object. On a clear object, text-bearing entries such as carried questions and margin notes also follow their own passage anchors. |
| `pad.proposals` | Checks both the block's lineage and the proposal's target at read time. A newly protected origin or target removes the whole proposal from the reply. Proposal creation also checks the origin before search. |

See [[Reference/Modules/learnloop/passage_union/union|Union read]], [[Reference/Modules/learnloop/passage_union/content|Passage content]], [[Reference/Modules/learnloop/passage_union/elsewhere|Related passages]] and [[Reference/Modules/learnloop/pads/proposals|Pad proposals]].

The verdict is per verb. `passage.promoted` (and each delivery of its job) returns `withheld_verbs`: each verb is read by the row of `exam_material.SURFACE_SETS` its destination withholds by, from one table (`workbench_protection.VERB_SURFACES`: Ask by `reader_ask`, Make it practice by `reader_import` and `reader_checks`, Compare by `compare`, Show me by `figures`, Teach me by `teaching`; Find, Carry and Append, which are new with the workbench, by all exam material). So on a practice exam that is not held out the desk offers Ask and Make it practice, as the classic Reader does, and held-out material leaves out every verb that sends or copies it. `withheld` stays the menu's own search's (all exam material). The header quotes the passage once the Reader's own Ask may read it (`reader_ask`); otherwise it names the material. Make it practice's reads (`passage.knows`, `passage.content`) take `for_verb` and decide by the same row.

Each menu opening starts with a neutral header. Text-bearing verbs, including a choice in the Append submenu, need explicit clearance for that opening. A failed protection read keeps the words hidden and offers Retry. Closing or replacing a menu invalidates waiting actions.

Carry, Append, source pieces, Ask, Find, Compare, Show me, practice and Teacher check the selection's passage or pad origins at the destination. A mixed selection is refused as a whole. A destination that had its own protection before the workbench keeps its set and its refusal: the check takes that path's row of `exam_material.SURFACE_SETS` and its code and words (a comparison's `comparison_withheld`, a lesson's `protected`; the companion's Ask, the Reader's import and checks, the library ask's anchor and the pinned tutor read the held-out partition, so a practice exam that is not held out stays usable there). New destinations (pad inserts, carried questions, a desk's compare window, the workbench search's selection) refuse all exam material. A worker that uses selected words later checks its origins again. A legacy pad quote without an anchor is refused only when a run of eight of its words (all of it, when shorter) appears verbatim in a protected passage (BATCH5-2); the learner's own unplaced quotes stay usable in a vault with exam material.

A plain highlight or margin note on exam or held-out material is stored, in the classic Reader and on a desk, as it was before the workbench: it is the learner marking their own reading, a plain `reader.capture` queues no model work, and the menu offers Note in margin without waiting for the verdict. What sends the words on is refused where it does: a preset (`reader.invoke_preset`) when its request is sent, the menus' verbs at their destination. Every later reader of stored annotations withholds one beside protected material: the union read, the promoted rows and passage details, the notes corpus (`vault_notes`, behind `notes.search`, `notes.marks`, the workbench search's notes group and the teacher's notes) and pad proposals; the companion's context reads no stored annotation. `test_a_stored_mark_on_held_out_material_reaches_no_other_surface` walks them.

Every poll of a finished promoted job rechecks its original passages, current pad ancestry and the passages behind each kept quote or related row. A newly protected origin withholds the result. A protected target removes its row while other rows keep their order. See [[Add a menu verb]] and the [menu findings in the bug ledger](../../reviews/refactor-bug-ledger.md#reader-workbench-vault-documentation-review).

## The shared due-check mask

`goal_lens_reads.protection` builds one `Protection` from all due checks, across goals. It includes the held learning-object ids and titles, sections that treat them and dependencies used to withhold reasons. Titles are matched as whole words. The server uses the masking functions in one module, `curriculum.goal_lens`, before sending replies. The band and path mask held names, readiness, next steps, section titles and alternatives, exercise labels and reasons as applicable. The lens also masks section titles, reasons and coverage and learner lines. It preserves structural ids, times and flags where needed. The band's goal sentence, its unmatched phrases and the desk's goal chooser (`goal.choices`) show the learner's own words with only a held topic's name replaced by "[topic hidden]" (`mask_names`, `protect_goal`, `protect_unmatched`; BATCH5-4); a masked phrase is not offered to add. The desktop uses the masked title for the reading position and refreshes at `nextCheckDue`, on relevant writes and when a reading comes back into view. See [[Reference/Modules/learnloop/curriculum/goal_lens|Due-check masking]] and [[Reference/Modules/learnloop_sidecar/handlers/goal_lens|Goal lens RPCs]].

## Follow-along and chapters

`reader.follow_along` applies that same protection to its chapter, video section and correspondent groups, including the passage titles a disconnected follow chip can still display. Its coverage read withholds correspondents for an exam or held-out section and omits protected destinations. `chapters.list`, `chapters.decide` and a finished `chapters.job` mask a chapter when its tags or title identify a held learning object or its range overlaps a section that treats one. Every delivery also masks a saved chapter whose range overlaps exam or held-out material marked since it was saved (BATCH5-5). The replies carry the next due time. The desktop drops expired follow text and rereads chapter text at that boundary. The suggestion job's exam guard also limits what transcript material the judge can read. See [[Reference/Modules/learnloop_sidecar/handlers/video|Video delivery]] and [[Reference/Modules/learnloop/source_retrieval/video_chapters|Chapter suggestion guard]].

## Lesson tabs and remaining gaps

`lesson.list` uses `protect_lessons` for stack tabs and the path's lesson row. A held lesson keeps its identity and dates, receives a neutral title and loses its goal text. A new additions pad for a held lesson gets a generic title. Separately, `lesson.view` and `lesson.turn` in the window frame leave an unserved Teacher quick question waiting and refuse to answer it there. The handoff opens the full lesson screen. Notebook held cells are display gating, as described in [[ADR-020 Keep notebook session files on the host]].

The [bug ledger](../../reviews/refactor-bug-ledger.md) records four open due-check surfaces.

| Row | What is still shown |
|---|---|
| RD10-12 | `lesson.view` can still teach a held topic through the open lesson's turns, checks or close card. |
| RD10-13 | `companion.history` can show prior answers. `search.everything` can show their snippets in threads and first sentences in exchanges. |
| RD10-14 | Source titles still show in heads, shelf rows, paths and the timestamp block written to a pad. The timestamp takes the video's own title. |
| RD10-15 | Today's `lesson.open_lessons`, outside the workbench, still names the lesson topic. |

The desktop's own reading and search passage text have no due-check veil. RD7's inline administration and veils are absent.

## Adding a text-bearing reply

Check the destination's exam policy before searching, copying or sending passage words. Check both the requested object and every origin and target the reply incorporates. For text that can cue a due check, use `protection_now` and extend the shared goal-lens masking module. Mask on the server at delivery, including a retry or poll of a stored result. Carry the next due time if the desktop keeps the reply. Test an already-held span, a mark or due check that changes between production and delivery, and a section shared with an LO from another goal. Walk every string in the reply and check visible text, tooltips and attributes in the desktop. The field and reply tests in `tests/test_reader_rd6_fix_protection.py` and `tests/test_reader_rd10_fix_protection.py` and the desktop `goal/protection.test.tsx` and `video/protection.test.tsx` show those checks.
