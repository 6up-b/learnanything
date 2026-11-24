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
| `passage.union_range` | Uses `exam_withheld` to set each affected span's `exposure.withheld`. The union does not carry the passage body and does not strip related rows. Section labels, stored link quotes, questions and learner material can still be present. Due checks anchored here contribute commitment ids only. `passage.knows` uses the same union and notes adapter. |
| `passage.content` | Uses the same exam predicate and sets the affected spans' text to null. It still returns source and section metadata. The pad's source-piece action and the exercise import sheet stop on a withheld reply. |
| `passage.promoted` | Checks the named passage or cue, or the passages linked through a pad line's lineage. A withheld object supplies no query text for search by meaning. Stored links are filtered at both ends, correspondents skip protected origins, and retrieval excludes protected passages and rejects protected hits before judging. The menu can still show the learner's own rows. |
| `pad.proposals` | Checks both the block's lineage and the proposal's target at read time. A newly protected origin or target removes the whole proposal from the reply. Proposal creation also checks the origin before search. |

See [[Reference/Modules/learnloop/passage_union/union|Union read]], [[Reference/Modules/learnloop/passage_union/content|Passage content]], [[Reference/Modules/learnloop/passage_union/elsewhere|Related passages]] and [[Reference/Modules/learnloop/pads/proposals|Pad proposals]].

Once the initial reply says `withheld`, the menu replaces the header quote and hides Ask, Find, Compare, Show me, Make it practice, Append, Carry and Teach me. The normal verb dispatcher waits for that verdict. It checks one source span even when the selection crosses several. The Append submenu takes a separate write path, and the first failed read resolves the menu's verdict as false. The initial header can quote before the verdict arrives. The promoted job's poll returns its stored rows without rechecking the current marks. See [[Add a menu verb]] and the [menu findings in the bug ledger](../../reviews/refactor-bug-ledger.md#reader-workbench-vault-documentation-review).

## The shared due-check mask

`goal_lens_reads.protection` builds one `Protection` from all due checks, across goals. It includes the held learning-object ids and titles, sections that treat them and dependencies used to withhold reasons. Titles are matched as whole words. The server uses the masking functions in one module, `curriculum.goal_lens`, before sending replies. The band and path mask held names, readiness, next steps, section titles and alternatives, exercise labels and reasons as applicable. The lens also masks section titles, reasons and coverage and learner lines. It preserves structural ids, times and flags where needed. The desktop uses the masked title for the reading position and refreshes at `nextCheckDue`, on relevant writes and when a reading comes back into view. See [[Reference/Modules/learnloop/curriculum/goal_lens|Due-check masking]] and [[Reference/Modules/learnloop_sidecar/handlers/goal_lens|Goal lens RPCs]].

## Follow-along and chapters

`reader.follow_along` applies that same protection to its chapter, video section and correspondent groups, including the passage titles a disconnected follow chip can still display. Its coverage read withholds correspondents for an exam or held-out section and omits protected destinations. `chapters.list`, `chapters.decide` and a finished `chapters.job` mask a chapter when its tags or title identify a held learning object or its range overlaps a section that treats one. The replies carry the next due time. The desktop drops expired follow text and rereads chapter text at that boundary. The suggestion job's exam guard also limits what transcript material the judge can read. See [[Reference/Modules/learnloop_sidecar/handlers/video|Video delivery]] and [[Reference/Modules/learnloop/source_retrieval/video_chapters|Chapter suggestion guard]].

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
