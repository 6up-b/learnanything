# Reader workbench v2: desks, scratchpads, the companion and the goal lens

**Status:** draft revision 2, 2026-11-21. Revised after a Codex Astra adversarial review (§19: 3 blockers and 14 further findings, all accepted). Handed to the orchestration session for implementation on main at the owner's request. Read at main `002c58fe17` (migration head 255). Stages RD-spike, RD0–RD10 and RD-retire (§16).

**What this is.** The build spec for the Reader workbench that the owner iterated on in the HTML mockups. The visual and interaction reference is two folders kept outside the repo:
- `~/learnloop-mockups/2026-11-20-reader-thread-space/arxiv_v2/`, round 14 plus the uncommitted round 14b;
- the goal-conditioned fork, `arxiv_v2_goal/`.

Both are built from a backup copy of the owner's `arxiv_v2` vault, so they hold book text and learner history and must never enter the repo (S0, §4.4). This spec states everything an implementer needs. The mockup is where they see it, and §4 lists the deep links to compare against stage by stage.

**What it replaces.** It replaces the single 4,711-line `ReaderScreen` with *desks*. A desk is a strip of windows: the learner's sources (book, paper, PDF, video, web), their scratchpads, Teacher lessons and tutor threads. The viewport shows two windows at a time. Over the strip sit:
- an app-wide **companion** (the tutor);
- a continuous **overview** zoom;
- a **goal lens** that marks how much each passage matters for the learner's goal;
- cold checks that sit inline at the passage and veil whatever states the answer.

Every v1 phase (RW1–RW7, CA1–CA6b) is built (§2.1). v2 changes where those features live, not what they mean, and §21.1 maps each v1 surface to its new home.

**Sources:**
- the mockups and their feature inventory, written for this spec from the mockup code: `~/learnloop-mockups/2026-11-20-reader-thread-space/INVENTORY-2026-11-21.md` (private, outside the repo). Its substance is §5–§13, and its §21 lists the mockup's defects;
- the code-truth audit of main: `~/learnloop-mockups/2026-11-20-reader-thread-space/CODE-TRUTH-2026-11-21.md` (private), summarized in §2;
- `docs/brainstorming/Reader Thread Space Brainstorm 2026-11-20.md` (untracked; §10.6, §12.3 and §13 hold the owner's decisions of Nov 20–21);
- `arxiv_v2_goal/GOAL.md` §4, which maps the goal fork to the real goal model;
- the owner's requests across the mockup rounds of 2026-11-20 and 2026-11-21, quoted where they bind (§1.3);
- the specs this builds on:
  - `spec_reader_workbench_v1.md` and `ux_reader_workbench_v1.md` (built);
  - `spec_p3_reader_integration.md` (invariants);
  - `spec_deliverable_curriculum_v1.md` (goals, coverage, path, readiness);
  - `spec_reader_show_me_figures_v1.md`;
  - `spec_notebook_activities_v1.md` (NA);
  - `spec_teacher_v2.md`;
  - `spec_adaptive_hints_v1.md`;

**Citation convention.** Python paths are relative to `src/` and frontend paths to `apps/learnloop-tauri/src/` (written `F:`); sidecar handlers are `src/learnloop_sidecar/handlers/` (written `H:`). Mockup references are `file:function` and name the *last* definition, the one that wins in the mockup's override chain.

---

## 0. The design on one page

1. **One unified workbench.** The owner rejected the fragmented screens (Nov 20) and wants "one unified workbench", source-first or note-first depending on what is open, like *How Might We Learn?* (HMWL). Everything happens on desks; nothing opens a separate screen except Today, Library and Progress.
2. **Desks are niri strips.** A desk is a horizontal strip of windows. The viewport shows two slots, the focus and its neighbour; the rest of the strip sits off screen behind thin slivers. Desks stack vertically like workspaces. `alt+h/l` moves along a desk, and `alt+j/k` moves through a pad stack or pair and then on to the next desk. `alt+[`/`]` moves a window.
3. **Every window takes one full slot until it is paired.** `alt+,` stacks the focused window with its right neighbour, top and bottom, in one slot; a slot holds at most two. `alt+.` gives a window back its own slot. Every window fills its slot's full height.
4. **The overview is a zoom, not a mode change.** `alt+o` is a fast eased zoom out. `alt+scroll`, `ctrl+scroll`, pinch and `ctrl+drag` drive the zoom by the input itself. The zoom's last frame is the overview's first frame. Cards show page thumbnails and live miniatures, and curved links show how the cards relate.
5. **The companion is the tutor everywhere.** It is one floating panel. `c` summons it at the cursor or selection, with the selection as its context, and `c` again dissolves it in place. If it was summoned from its drawer, `c` sends it back there. Its answers link claims to exact spans, which open beside. Everything discussed stays searchable by day and desk.
6. **Scratchpads are where the learner thinks.** Each desk has a running, dated pad; named pads sit in a stack of sticky tabs that fill the column. Blocks carry their provenance: typed, quoted from a source, from the tutor, a figure, a sketch, ink, a notebook cell. LearnLoop speaks only through quiet gutter markers whose hover cards connect to what they propose. A pad is always an *emission*: learner text the models may read. Submitting a block as an attempt or teach-back is a separate, explicit act.
7. **The right-click is a split menu.** Up to four promoted rows come from what LearnLoop knows about this passage, each with its reason. Below them sit the fixed verbs (Ask, Note, Append, Carry, Open beside, Find, Compare, Show me, Make it practice…). The same menu works on passages, transcript cues, pad lines and inside Teacher notebooks; in pads and notebooks it also offers inserts (sketch cell, marimo cell, a piece of a source).
8. **The goal is prominent** (a user's feedback, Nov 21). A goal band names the learner's goal, its learning objects (LOs) with readiness from cold checks, the chosen depth, where the learner is reading and what comes next. A **criticality mark** in each passage's margin says how much the passage matters for this goal (a second user's feedback), with the reason on hover. A path view (`p`) lays out the goal across all sources.
9. **The masked check is first class** (the owner: "really good"). A due cold check sits at the passage that would give its answer away. While it is open, whatever states the answer is veiled in place (book, pads, ink, tutor thread), and nothing moves. Answering lifts the veils and updates readiness honestly.
10. **Nothing here changes what counts as evidence.** Reading, highlights, figures, hints and pad text are never certification (§14).

---

## 1. Owner direction

### 1.1 Standing rules that bind this spec
- **Honest labels, generous defaults; frictionless, glass box on demand** (Oct 13). No jargon in the UI. The attention budget holds: no counts as badges, no pulsing; skimming is the mute button (`ux_reader_workbench_v1.md` §4.12).
- **No kill switch on a new successor unless the owner asks** (Nov 16). Display-only work needs no successor. Each stage says how it is undone (a revert). Existing Reader switches (`reader_inquiry.enabled`, `workbench.enabled`, …) retire with the screens they guard (§21.1).
- **No made-up constants** (Oct 24) and **no artificial count caps** (Oct 12). UI timings, sizes and easings are design values, not model constants: they come from the mockup and are listed in §4.3. A display limit that protects attention is labelled as one, and the learner can change it.
- **Only the grader is blind** (Nov 1). The companion, the diagnoser and the Teacher see learner history, pads and threads whenever it helps.
- **The Decider, not token overlap, judges answer reveals** (Nov 18). Veils use that one shared judgment once it exists (§12.6).
- **Anything framed as teaching opens a Teacher lesson; Ask is for questions about what is on screen** (Nov 14).
- **Figures are help, never certification** (RW5d). **Learner text over skip buttons** (Oct 12).
- **The Reader's search box is built with the Reader redo** (Nov 20). This spec is that redo (§9).
- **LaTeX sizing must be solid** (Nov 21): "when this mockup is actually implemented these size bugs wrt latex should be fully ironed out" (§13.4).
- **Public repo (S0):** no personal data, book pages or vault-derived mockups in the tree.

### 1.2 The owner's decisions on the design (brainstorm §12.3 and §13, Nov 20–21)
1. Each desk is a niri strip of columns; the viewport shows HMWL's two surfaces; desks stack like workspaces; the shelf is the strip's minimap; the overview is a continuous zoom with semantic-zoom cards and degree-of-interest emphasis.
2. The companion toggles the tutor thread. **What was discussed each day must be searchable and reviewable later**, by date and desk and in search.
3. HMWL-inspired pieces are restyled in **LearnLoop's own design language** (the three voices, its tokens).
4. Sources and notes open from suggestions or from **search**, which covers the whole library of sources and notes.
5. **Selection as context:** highlight, toggle the companion, and the span joins its context.
6. **Two-way highlight ↔ scratchpad links:** append a highlight to a pad; clicking either end scrolls to the other.
7. **Adopted as high-ROI:** the per-span union read (span backfill for `question_events` and `learner_text_gaps`); **the companion over the existing tutor as an app-wide pattern**; two-way links.
8. Panning and organizing windows on a desk must be easy. Keys `alt+h/l`, `alt+j/k`, `alt+[`/`]`. Overview cards show the page you are on.
9. **Scratchpad theming from the mockup**, which replaces NA §5.2b's marimo LearnLoop theme. Marimo runs underneath with a lazily started kernel, and Markdown and LaTeX render natively and elegantly out of the box.
10. **Sketch blocks from the start.** **One pad at a time in a stack, filling the column**, with an animated tab-through. A separate micro-journey arranges pads above and below each other.
11. **Focus (`alt+enter`) is full screen**, with `=`/`-` to zoom the document.
12. **The running pad per desk replaces the palette.**
13. **A scratchpad is always an emission.** Submitting is separate.
14. **Cold checks hide visible pads, blocks, threads and passages that hold the answer**; positions don't move.
15. `alt+j/k` works like niri's focus-window-or-workspace.
16. **Touchpad and laptop friendly:** `alt` + two-finger swipe moves across columns (horizontal); pinch or `ctrl+scroll` zooms the overview. The Nov 21 touch decision also gave alt + vertical swipe to pads and desks. The owner's later request in the same session (O6: "alt + scroll … gradated up to the user's input") gives alt + vertical scroll to the overview zoom, and this spec follows the later request. Pads and desks move vertically with `alt+j/k` and by plain scrolling in a stack (decision D14).
17. **Pen mode with an annotation suite:**
    - underline → highlight;
    - margin bracket → paragraph highlight;
    - circle or lasso → select;
    - margin scribble → handwritten note with transcription;
    - strike → disagreement.
    
    **Freewrite ink in pads**, each line with an editable transcription. **The tutor reads ink unobtrusively** through `◇` gutter markers that open the five-rung help ladder in place, where choosing and taking a rung are separate.
18. A universal, context-dependent right-click. The learner can append their own margin notes. The AI adds guidance or connections to pads **unobtrusively via markers**.

### 1.3 The owner's requests during the mockup rounds (2026-11-20/21), each binding on the build
| # | Request (owner's words where short) | Where specified |
|---|---|---|
| O1 | Scratchpad takes the full height of the column with blank space; tabs scroll so passed tabs stack at the top and coming ones at the bottom; try tab width graded by order | §10.1 |
| O2 | "merge the tab with the note when its opened so its seamless" | §10.1 |
| O3 | In distance mode, tabs animate to merge with their paper through a curved edge as the next pad's paper is revealed | §10.1 |
| O4 | § row hover: keep the dark background, but fade the text to the pad's white and back | §10.3 |
| O5 | The companion must not teleport. Summoned at the cursor or a selection, it dissolves in place (opacity plus blur, eased). It returns to the drawer only if summoned from there | §8.3 |
| O6 | `alt+o` is a quick, performant, eased zoom out. `alt+scroll` drives a gradated zoom with the input. The last zoom frame is the first overview frame. "still very clunky and very laggy": fixed by the engine in §6.3 | §6 |
| O7 | Video windows embed YouTube; no "opens YouTube (serve over http to embed)" text | §7.4 |
| O8 | Curved links instead of right-angle ones | §6.5 |
| O9 | A Teacher lesson as a marimo notebook that the learner can review, redo and augment like other pad notes. In the workbench's paper colours, not dark mode, with default marimo text styling and Literata body text. Styled commit points; even margins. Tutor `c` and the same right-click work inside it | §11 |
| O10 | The column dots move to the bottom footer; the hint reads "hold alt for navi hints" | §5.3 |
| O11 | Right-click in a pad works like on a source (ask, find in my sources, show me, make it practice…) and can also spawn sketch cells, marimo cells and pieces of a source | §9.2 |
| O12 | Every window uses its full slot until stacked; `alt+,`/`alt+.` stack up to 2 windows per slot, uniform slot, top and bottom (owner's choice). The paper page fills the full window height | §5.2 |
| O13 | Fix LaTeX cut off by cell height; must be fully ironed out in the implementation | §13.4 |
| O14 | Allow editing pad notes in place | §10.5 |
| O15 | Hovering pad markers works and connects to what they propose (a pad's fig marker); the marker must not touch the frame edge | §10.6 |
| O16 | A margin indicator of how critical a span is; the goal more prominent; a goal-conditioned workbench inspired by HMWL; keep the masked textbook and scratchpad for questions | §12 |
| O17 | Search in context animates like rofi on Hyprland | §9.3 |

---

## 2. What exists today (main `002c58fe17`, migration head 255)

### 2.1 Built and reused
- **Every v1 Reader phase:**
  - RW1a–c: inquiry branches, detour strip, intent box, active reading, the tutor that looks things up;
  - RW2a–d: the resumable single-problem workbench, its help ladder and hints, what helps, field signals;
  - RW3a/b: margin cues;
  - RW4a/b/d/e: library ask and compare, exercises from sources, syntopic keep, instructional roles;
  - RW5a/b/c-P1/d P1–P5: figures and Show me;
  - RW6a/b: last time here, digest, cold follow-ups;
  - RW7a/b: reading paths;
  - CA1–CA6b: compare and ask UX, side by side.
  
  `spec_reader_workbench_v1.md`'s status line is stale. Landing notes are in `docs/reviews/`.
- **Rendering and anchors:**
  - `reader.render_view` (`H:reader.py:646`) renders blocks with `span_id`, KaTeX nodes and `protection`, optionally for one section or span range.
  - `pdfjs` pane: `F:components/PdfReaderPane.tsx`.
  - Sub-block `anchor-v1` annotations, append-only (migration 090; `reader/annotations.py`).
  - Cross-reading identity: `source_span_reanchors` (032) and `content/sources/span_aliases.py`.
- **Video:** `F:screens/reader/YouTubeWatchPanel.tsx` (youtube-nocookie embed under the app's CSP; `reader.watch_plan`); caption spans with `t=start-end` locators.
- **Tutor:** `reader.ask` (`H:reader.py:139`) takes a selection, `parent_exchange_id`, `retrieval_intent`, `span_keys` and `cold_active`. Exchanges are `question_events` (019/086) plus `interaction_events` payloads; there is no thread table (`reader/reader_dialogue.py:24-27`). `reader.ask_history` covers one reading only.
- **Figures:** `figure.request` / `figure.open` / … (`H:figures.py`); the tiers are grammar, sketch and rich.
- **Hints:** one `request_hint` (`learnloop/hints/service.py`), `workbench.request_help`.
- **Goals and curriculum:**
  - `Goal` (`vault/models.py:62-109`): `intent_sentence`, `facet_scope`, `due_at`, `exam`.
  - Coverage: `section_coverage` (222).
  - Scope and path: `deliverable_scope_*` and `deliverable_path_sections` (228), with `label`, `depth` and `learner_override`.
  - RPCs: `curriculum.scope|path|path_override|guide_slice|ready|ready_check|set_depth|set_scope`, `reader.span_learning_objects`, `reader.correspondents`.
  - Per-LO use weights: `goals/use_weights.py`.
  - Certification: `goals/goal_certification.py:lo_certification`.
- **Delayed checks:** `commitments` with action `test_me_later` (072), served by DL2's Check once (`scheduling/intent/serving.py`) and settled by `intent/checks.py`.
- **Lessons:** `lesson.turn|view|open_lessons|activity` (`H:lesson.py`), the tables in 234/247–249, and `F:screens/LessonScreen.tsx` (a separate screen).
- **Notes:** `learner_notes` and `learner_note_links` (229), vault-native since 233; `notes.*` RPCs.
- **Learner-text gaps:** `learner_text_gaps.source_kind` and `learner_text_gap_jobs.source_kind` (rebuilt at 248) are one of `tutor_question | stuck_answer | diagnosis | workbench_text | reader_formative | hint_feedback | learner_note | lesson | external_chat`. Effects are governed by `diagnosis/text_gaps/contract.py` (`READABLE_SOURCE_KINDS`, `NON_SERVING_SOURCE_KINDS`).
- **Shell:** React 18, KaTeX 0.16, react-markdown + remark-math + rehype-katex.
  - Editors: `F:render/LiveMarkdownEditor.tsx` (Obsidian-style live preview) and `F:render/MathLiveEditor.tsx`.
  - The keymap as data: `F:app/keymap.ts`, with collision tests.
  - `F:screens/reader/bareAlt.ts`: a bare Alt *keyup* with nothing else pressed clears the capture.
  - Query cache: `F:api/queryCache.ts`.
- **Sidecar:**
  - JSON-RPC over stdio behind one response mutex (`src-tauri/src/sidecar.rs:43-45`), so long work runs as a job you poll.
  - A new method needs a Python handler, a Rust passthrough (`src-tauri/src/commands.rs`), and entries in `client.ts` and `dto.ts`.
  - Phone access is default-deny (`learnloop_mobile/allowlist.py`).

### 2.2 Missing (built here)
- desks, windows, slots and their persistence;
- the overview;
- multi-source scratchpads, sketch blocks, ink and pen handling (no `pointerType` handling exists);
- a thread view keyed by span, and the span backfill for `question_events` and `learner_text_gaps`;
- cross-source tutor history by day and desk;
- an app-wide companion;
- search over sources, notes, pads, threads and history together;
- a due-checks-by-LO, section or span query;
- inline checks with veils;
- the goal band, criticality marks and the path view as a workbench layer;
- lessons as a window;
- marimo anywhere in the app: only `learnloop notebook check` (H1) exists, and NA0–NA6 are unbuilt.

### 2.3 Data gaps the build must face honestly
- `section_coverage`, `source_object_relations`, `library_asks` and `learner_notes` can be empty in a real vault; their surfaces show honest empty states.
- Planned delayed checks may have no generated item yet (teacher v2 §2), and a goal may have no deliverable resolution.
- **arXiv full text:** a bare id or `/abs/` link still reads only the abstract (KD3 open).
- **Videos** have no chapters, progress or passage links.
- **The mockup restored dropped inline math by hand.**

The goal lens and the inline checks therefore show their empty states in such a vault until C0 coverage runs, a deliverable is resolved and TE6's generated checks land (§12.8).

---

## 3. Architecture

### 3.1 Frontend modules (new)
Under `F:screens/desks/`:

| Module | Owns |
|---|---|
| `DeskShell.tsx` | The Reader place: the top bar's desk tabs, the stage, the shelf, the footer. It is the single key router for the workbench (§5.4) |
| `model/workspace.ts` | The client model: desks, windows, slots and stacks. It is pure and tested, and it applies `desk.apply` ops optimistically (§3.4) |
| `geometry.ts` | Pure layout: `geom(overview: boolean)` returns every window's rect and the camera, for both the reading view and the overview (mockup `st_7.js:geom`, after the geometry split) |
| `camera.ts` | The camera: `translate(-camX, -rowTop(desk))`, focus and `ensureVisible` |
| `overview/engine.ts` | The zoom engine (§6.3) |
| `overview/Card.tsx`, `overview/links.ts` | Cards, thumbnails and curved links |
| `windows/SourceWindow.tsx` | Book, PDF, paper and web windows. Extracted from `ReaderScreen`'s source pane together with its hooks (selection, margin cues, capture, figures, cues). The extraction keeps them; it does not fork them |
| `windows/VideoWindow.tsx` | The video window: `YouTubeWatchPanel` plus the transcript as timed spans |
| `windows/PadStack.tsx` and `pads/*` | Scratchpads (§10) |
| `windows/LessonWindow.tsx` | The Teacher lesson window: the existing lesson UI, plus a notebook frame after NA (§11) |
| `windows/ThreadWindow.tsx` | A tutor thread pinned as a window |
| `windows/PairSlot.tsx` | Two windows in one slot |
| `Shelf.tsx` | The strip: one row per window with a minimap, plus today's running pad and carried questions (§5.6) |
| `menus/SplitMenu.tsx` | One menu component for the source, pad and notebook menus (§9) |
| `search/Spotlight.tsx` | Search in context (§9.3) |
| `pen/*` | Pen input, the recognizer and the ink layer (§10.10) |
| `goal/*` | The band, criticality marks, callouts and the path view (§12) |
| `checks/*` | Inline checks and veils (§12.6) |

App-wide, under `F:components/companion/`, sits `Companion.tsx` with its state machine (§8). It mounts in `App.tsx`, so every screen gets it (owner decision 7).

`ReaderScreen.tsx` stays reachable as the old Reader until the parity matrix passes (§21.1). It is then deleted in the dedicated RD-retire landing.

### 3.2 Backend modules (new)
- `src/learnloop/desks/`: workspace persistence (desks, windows, op application) and the shelf's projections. WORKFLOW data, never evidence.
- `src/learnloop/pads/`:
  - pad and block storage, versions and anchors;
  - the emission hook (pad text → learner text);
  - submission hand-offs (to attempts and teach-backs);
  - ink strokes and transcriptions.
- `src/learnloop/passage_union/`: the per-span union read (§7.6) and promoted menu rows (§9.1).
- `src/learnloop/companion/`: history by day and desk, exchange context (desk, surface, pad blocks), search over exchanges.
- `src/learnloop/curriculum/goal_lens.py` (inside the existing curriculum area): passage levels, reasons and the band summary (§12).
- `src/learnloop/intent/inline_checks.py` (beside "Check once" serving, `intent/checks.py`; not in `curriculum/`, because it reads `scheduling.intent` and `scheduling` already imports `curriculum`, so a module there would close a package cycle under the acyclic import contract; RD0's review, `docs/reviews/reader-rd0.md`):
  - due checks by LO, section or span;
  - inline administration;
  - veil sets (§12.6).
- `src/learnloop/substrate/passage_spans.py`: the two DERIVED span tables of §7.6, their per-source recipes, their write-through and their replayers. They sit in `substrate` with the rebuild's other projections because the Reader's Ask, the tutor and the gap pipeline write through them, and `substrate` imports none of those (RD0's review).

Handlers live in `H:desks.py`, `H:pads.py`, `H:companion.py`, `H:passage_union.py`, `H:inline_checks.py` and `H:goal_lens.py`.

### 3.3 Import fences (new contracts in `pyproject.toml`)
1. **Nothing that writes evidence reads pads, ink, desks or veil sets,** the replay, evidence and serving internals included. The only exits are explicit:
   - `pads.submission` hands a block's text to the existing attempt and teach-back entry points;
   - `pads.emission` writes `learner_text_gaps` rows of `source_kind='pad_text'`.
   
   This is the same shape as the workbench contract at `pyproject.toml:834`.
2. **The grader never reads pads, ink, threads, desks, veils or the goal lens.** This extends `:379-411`.
3. **`desks` imports nothing from scheduling, evidence or the router.**
4. **`passage_union` and `goal_lens` are read-only projections.** They write only receipts (judgment ledger rows) and caches.
5. **The Reader defines no hint writer, chooser or map builder** (`:895`). This still holds: the ink help ladder calls `learnloop.hints`.
6. **A learner's note is never a source, a generation input or evidence** (`:535`). This still holds for margin notes. Pads are not notes: they are emissions (owner decision 13), and the contract text names the difference.

### 3.4 RPCs
Each RPC's params model is `extra="forbid"` and its reply is `versioned`. None is on the phone allowlist; the phone's desks are deferred (§17).

**The content reference (one model for every surface; review F14).** Every place that names "something to show" uses one discriminated `ContentRef`:
- `{kind: "source", source_id, extraction_id, view: render|pdf|web, range?}`;
- `{kind: "video", source_id, extraction_id, t?}`;
- `{kind: "pad", pad_id}`;
- `{kind: "lesson", lesson_id}`;
- `{kind: "thread", root_exchange_id}`;
- `{kind: "compare", comparison_id | query}`;
- `{kind: "panel", panel: guide|path|library|notes, extraction_id?}` (the temporary adapters, §21.1);
- `{kind: "figure_notebook", figure_id}`.

Open specs, claims, back-links, search results, promoted rows and path rows all carry a `ContentRef` plus an optional target (`span_id`, `t`, or `block_id`).

**Write protocol (review F3).**
- Every write call carries `{client_id, seq, ops}`:
  - `client_id` is stable per vault and installation, stored in the vault's local settings;
  - `seq` is strictly increasing per client.
- Every op names the head it expects (`expected_version`).
- The server applies a batch **in one SQLite transaction** together with its receipt, in `seq` order, and refuses a gap in `seq`.
- An op whose expected head is stale is not applied. It returns `conflict` with the current head, and the client resolves it (§3.5).
- A retried batch with an already-applied `seq` returns the stored receipt.
- `seq` is one sequence per client across `desk.apply` and `pad.apply` (one outbox).
- A reply names data in lists, never as object keys (`versions`, `server_seq`, the union's `spans`): the sidecar turns every reply key into camelCase, which would rewrite an id used as a key.

| Method | Input | Reply | Notes |
|---|---|---|---|
| `desk.state` | `{}` | `{desks:[{desk_id, title, position, focus_window_id, goal_id?, companion:{dock, shown}, version, slots:[{slot, windows:[{window_id, pane, content:ContentRef, view}]}]}], running_pad_ids, server_seq:[{client_id, seq}]}` | One read at startup and after a conflict. **Slots are authoritative:** a pair is two windows sharing a `slot` with panes 0 and 1. There are no nested pair specs |
| `desk.apply` | `{client_id, seq, ops:[{op, expected_version, …}]}` | `{applied_seq, results:[ok\|conflict{current}], versions}` | The ops are `create_desk`, `rename_desk`, `archive_desk`, `move_desk`, `open_window`, `close_window`, `reopen_window`, `move_window`, `move_to_desk`, `pair`, `unpair`, `set_focus`, `set_active_pane`, `set_view`, `set_dock`, `set_companion_shown`, `set_goal` |
| `pad.get` | `{pad_id}` | `{pad, blocks:[{block_id, head_version_id, …}], anchors}` | |
| `pad.list` | `{desk_id?, query?, kept?, cursor?}` | `{pads}` | Feeds the library, search and the drain |
| `pad.apply` | `{client_id, seq, pad_id, ops:[{op, block_id?, expected_head?, …}]}` | `{applied_seq, results, heads}` | The ops are `create_pad` (carries the client-minted `pad_id`, so retries are safe), `insert_block` (a client-minted `block_id`), `edit_block` (`expected_head` required), `remove_block` (a tombstone version), `move_block` (a new `position_key`), `lift_out` (an insert plus a stub in one op), `set_title`, `keep`, `unkeep`, `link_anchor`, `unlink_anchor`, `erase_ink` (a tombstone over stroke ids) |
| `pad.submit_block` | `{submission_id (client-minted), block_id, version_id, as: "attempt"\|"teach_back", target}` | `{attempt_id?\|teach_back_id?}` | Idempotent by `submission_id`; hands off to existing entry points (§10.9) |
| `ink.save` | `{client_id, seq, owner:{block_id\|annotation_id}, ink_id (client-minted), strokes}` | `{ink_id}` | |
| `ink.transcribe` / `ink.transcribe_job` | `{ink_id}` | job → `{latex_md, confidence_label}` | A paid route through the plan transport (§10.10) |
| `passage.union_range` | `{extraction_id, from_span_id, to_span_id}` or `{extraction_id, t0, t1}` | `{extraction_id, spans:[{span_id, …union}], sections}` | Goal-independent (§7.6). **Batched per visible range,** never per span on hover |
| `passage.promoted` | `{extraction_id, span_id\|t, object_kind, desk_id}` | `{rows, pending_job?}` | Cheap rows inline; judged rows through a job (§9.1) |
| `companion.history` | `{from?, to?, desk_id?, query?, cursor?}` | `{days:[{date, desks:[{desk_id, exchanges:[…]}]}], cursor}` | §8.5 |
| `companion.ask` / `companion.ask_job` | the `reader.ask` input plus `{request_id, desk_id, surface, pad_block_ids?, notebook_ref?}` | job → `{status, partial_md, citations, done}` | **Generation is a job** (review F8): today's `reader.ask` calls the model synchronously inside the mutex. The handler runs the existing ask path off the request thread and records the exchange context. The client polls `partial_md` through the central poller (§3.6) to show the answer streaming. Off the Reader, the wrapped call is `ask_tutor_question` |
| `search.everything` / `search.job` | `{query, desk_id, scopes?}` | groups (§9.3) | Lexical groups at once; meaning groups through the job |
| `goal.band` | `{goal_id}` | §12.2 | Composes `curriculum.ready`, `curriculum.path`, due checks and pace |
| `goal.lens` | `{goal_id, extraction_id, from_span_id?, to_span_id?}` or `{goal_id, extraction_id, t0, t1}` | `{levels:[{span_id\|range, level, reason_key, reason_md, lo_ids, mapping: mapped\|partial\|unmapped}]}` | Goal-conditioned, separate from the union read (§12.3) |
| `checks.due_for` | `{goal_id?, learning_object_ids?, extraction_id?, span_id?}` | `{checks:[{commitment_id, lo_id, due, host?, provenance}]}` | Read only; shows nothing of the item (§12.6) |
| `check.begin_inline` | `{request_id, commitment_id, visible}` | `{administration_token, item_ref, contract_hash, protection:{veil_set_id, method}, prompt}` | Atomic: it picks the item through `scheduling/intent/serving.py`'s eligibility, freezes the assessment contract, opens an administration and computes the structural protection, **before the prompt is returned** (§12.6) |
| `check.expose` | `{administration_token, ref, kind: opened_veil\|navigated\|help}` | `{protection_status}` | Persisted at once through the exposure machinery, not deferred to submit |
| `check.protect_more` | `{administration_token, visible}` | `{veil_additions}` | Called when new content becomes visible during the administration (navigation, new window, search) |
| `check.submit_inline` | `{administration_token, submission_id, answer_md}` | the existing attempt reply plus `{cold: bool, reason}` | Records the attempt through the existing attempt service for that item; settlement then runs as for any qualifying attempt (`intent/checks.py:settle_answered_checks`). Idempotent by `submission_id` |
| `check.abandon_inline` | `{administration_token}` | `{}` | Closes the administration with no attempt; the cold duty stays pending |

**Long work is a job:** companion generation, meaning search, ink transcription, veil judgment and judged promoted rows. **All polling goes through one client poller** (§3.6).

**Plumbing.** Every method gets its Rust passthrough and its `client.ts`/`dto.ts` entries in the stage that adds it.

### 3.5 Local-first writing (review F3)
**The outbox.** Pad edits, ink strokes and desk ops go first to a client outbox in IndexedDB, in a database named by vault id, so switching vaults never mixes outboxes.

**Saving.** A write is **shown as saved locally only after its IndexedDB transaction commits.** If storage fails, the pad shows "not saved on this device" and keeps the text in memory until it is resolved.

**Flushing.** Ops leave the outbox only after the server's receipt for their `seq`. A batch is flushed:
- on idle (a design value);
- on blur;
- on leaving a pad;
- on app close (best effort).

On start, unacknowledged batches replay in `seq` order.

**Conflicts.** Edits made at the same time on two installations are rare (one learner) but possible across machines.
- A conflicting `edit_block` keeps both: the server head stays, and the client's text is inserted as a new block right after it, labelled "from your other device · <time>". **Nothing is lost.**
- A conflicting move, pair or lift-out takes the server state, and the client re-renders.

**Versions and ordering.**
- Block versions form one chain per block: the server refuses a second child of the same parent (the `expected_head` check), so there is no branching head.
- Equal `position_key`s are ordered by `block_id`.

**Production origin.** IndexedDB persistence under the packaged Tauri origin (`tauri://localhost` / `http://tauri.localhost`) is verified in the RD-spike (§16). If it is not durable there, the outbox moves to a small SQLite file written through a Rust command. This mirrors `reader_capture`'s "annotation, event and outbox in one transaction" precedent, which is SQLite, not IndexedDB.

**Restoring position.** Reading restoration is span-based (`view` holds `{span_id, offset_frac}` or `{t}`), never pixels (P3: blocks anchor meaning).

### 3.6 Performance budget and the window lifecycle (must hold on packaged WebKitGTK; review F9, F10)
The target is Tauri on Linux (WebKitGTK), not Chromium. The mockup was tuned in Chromium. The measured results there:
- gesture start went from 142–153 ms to about 1 ms of script plus 5 ms of style;
- raster went from 722 ms to 167–179 ms;
- long frames went from 7–11 to 1–3.

It was never run on WebKitGTK. **The RD-spike (§16) measures it before any extraction.**

**The workload** is defined, not "30 windows". The fixture workspace has:
- 4 desks and 24 windows;
- 8 book or paper windows of 40–120 rendered pages' worth of blocks, with a synthetic KaTeX workload (about one display equation per 400 words and inline math in most paragraphs);
- 2 PDF windows of 300 pages;
- 6 video windows, one embedded player active;
- 6 pad stacks of 4–8 pads, one with a notebook frame;
- 2 lesson windows.

**Budgets on the desktop and on the laptop:**
- **Zoom and pan frames:** transform and opacity only, with one rAF writer.
  - No layout, style recalculation or DOM insertion during a zoom or pan.
  - Script at most 4 ms per frame.
  - The 95th-percentile frame within 20 ms, and no frame over 50 ms.
  - Measured with the WebKit inspector timeline in the packaged app.
- **Idle:** CPU under 2 % with the workspace open and no media playing.
- **Memory:** resident memory under 1.5 GB for the fixture.
- **Responsiveness while the companion generates:** an edit is acknowledged locally in under 50 ms, and a hover card opens in under 250 ms.

**Frozen geometry during transitions.** When a zoom begins, every live window's geometry and content are frozen. Asynchronous updates (job results, union reads, thumbnails, media time) are queued and applied after the commit. No content changes size mid-transition.

**No inherited custom property may change during animation** (an inherited variable on `<body>` restyled about 14k elements in the mockup). Write per-window inline values instead.

**The window lifecycle contract** (every window kind implements it):
- **States** are `active` (focused), `visible` (in view), `offscreen` (on this desk, out of view), `hidden` (another desk) and `preview` (an overview card or miniature).
- **Only an active window owns** keyboard input, the selection and the capture target. Window-level listeners are registered through `DeskShell`'s router, never directly on `window` or `document`, so N windows never mean N handlers.
- **Offscreen and hidden windows pause** effects, timers, polling and media. They use `content-visibility: auto` with an intrinsic size, and React subtrees are suspended (kept mounted but inert) or unmounted with their scroll anchor saved.
- **Previews generate no reading activity.** Neither do programmatic moves (gather, pair, reorder, restore). Reading activity (`reader.log_activity`, section progress, exposure) is attributed only to active or visible windows, after the learner scrolls or dwells, under the same rules as today.
- **Media identity is per instance.** A `postMessage` from an embedded player is accepted only if `event.source === thisIframe.contentWindow`, not merely by origin. This fixes an existing bug in `YouTubeWatchPanel.tsx:238`, which checks only `event.origin` and would let one player consume another's time messages.
- **One central poller** in `F:api/` owns all job polling, at one cadence with backoff, and coalesces requests.

**Blur.** WebKitGTK's `filter: blur` and `backdrop-filter` are expensive. The companion's dissolve blur and the search backdrop blur must pass the frame budget there. If one does not, it falls back to opacity and scale only, a measured decision recorded in the spike's review.

**Modifiers.** WebKitGTK may report `altKey`/`ctrlKey` false on touchpad scrolls (WebKit bug 257910), and touchpad pinch may not reach the page (bug 272396). Alt and Ctrl are tracked from key events and cleared on blur (§5.5). Pinch is optional.

**Iframes and the CSP.** Today's CSP allows frames only from the sketch frame and `https://www.youtube-nocookie.com` (`src-tauri/tauri.conf.json:27`).
- **Video:** embedding is verified in the packaged app in the spike. Error 153 concerns missing referrer or client identification, so CSP permission does not prove playback. If the packaged origin cannot embed reliably, the video window keeps the transcript and offers "open the video in your browser at m:ss" (§7.4).
- **Notebooks:** RD9b adds the notebook server's origin (the authenticated local proxy of NA's runtime) to `frame-src`. Notebook frames must have no access to Tauri IPC (the capability configuration denies it), which is tested.

## 4. The visual reference and fidelity rules

### 4.1 How implementers use the mockup
The mockup runs from `~/learnloop-mockups/2026-11-20-reader-thread-space/arxiv_v2/index.html` (served by `python3 -m http.server`) and `arxiv_v2_goal/index.html`. The Teacher notebook needs `~/learnloop-vault-notebooks/serve.sh` on port 8777.

Each stage's acceptance names deep links (`index.html#…`) that put the mockup in the state to compare against. The implementer checks the app's equivalent state side by side and records the comparison in the stage's review file in words. No screenshots of book pages go in the repo; screenshots of synthetic fixtures are fine (§18.3).

**Deep links per area:**

| Area | Mockup deep links |
|---|---|
| Desks, slots, pairs | `#desk=1`, `#focus=3`, `#move`, `#s11=arrange`, `#s11=split` |
| Overview | `#ov`, `#ovn=far`, `#ovn=down`, `#scrub=0.5`, `#ovg`, `#selftest`, `#selftest2` |
| Focus | `#zoom=after`, `#s11=fs150` |
| Companion | `#cur=sel`, `#cur=handoff`, `#cur=shiftc`, `#dock=right`, `#cov`, `#hist`, `#selctx` |
| Pads | `#tabs=distance,pad=2,padf=0.4`, `#tabs=order`, `#s11=run`, `#s11=lift`, `#s11=sketchqk`, `#s12=info`, `#s12=submitted`, `#append`, `#markback`, `#backlink` |
| Menus | `#menu=cue`, `#menuhl`, `#s11=menu` |
| Search | `#spot=softmax`, `#switch` |
| Pen and ink | `#pen=underline`, `#pen=bracket`, `#pen=note`, `#pen=lasso`, `#pen=strike`, `#pen=pad`, `#pen=ladder`, `#pen=rung2`, `#pen=veil` |
| Figures | `#figmark`, `#figopen`, `#figsrc`, `#figmove` |
| Checks | `#s12=check`, `#s12=answered` |
| Goal fork | `#goal=frame`, `#goal=why`, `#goal=whysup`, `#goal=whyskip`, `#goal=basics`, `#goal=path`, `#goal=check`, `#goal=answered`, `#goal=checkb`, `#goal=paper`, `#goal=pads`, and `nodim` |
| Laptop | `#lap=1`, `#lap=open`, `#lap=comp` |
| Teacher lesson | `#tabs=distance,pad=3` (with the notebook server running) |

### 4.2 Design tokens (copy exactly; they become CSS variables in `F:styles/desk.css`)
**Colours:**
- shell `#0c0c0d`; paper `#f7f5f0`; pad paper `#fdfdfc`;
- ink `#1f1e1c` / `#55524c` / `#7a766e`; rules `#dcd7cc`;
- the learner, focus and "you": amber `#e3a063`, amber ink `#9a5a17`;
- LearnLoop: purple `#dccdf2`, purple ink `#5b4a9a`, purple wash `#efeaf9`;
- links and relations: cyan `#6ad0e0`;
- search selection: `#2563eb`;
- pen stroke: `#2b4fa8`, 2.2 px.

**Fonts:**
- UI: JetBrains Mono, as the mockup sets its whole interface (corrected 2026-11-23 from Inter: where the spec's text and the mockup disagree on looks, the mockup wins; Inter no longer ships);
- book and pad prose: **Literata**;
- paper: Source Serif 4;
- code: JetBrains Mono;
- handwriting: Caveat.

All fonts ship locally: no Google Fonts fetch in the app.

**The voices as glyphs:**
- `§` a source;
- `◇` LearnLoop;
- `›` you;
- `?` your question;
- `▶` a video;
- `◌` carried or worked help;
- `✎` ink or by hand;
- `◎` the goal.

The `mock` tag is mockup-only and is never built.

### 4.3 Timings and sizes (design values from the mockup)
| What | Value |
|---|---|
| Default easing | `cubic-bezier(.22,.7,.18,1)` |
| Camera move | `.55s` on the world, `.45s` on window left/top |
| Slot geometry | side margin 34 px, gap 10 px, top bar 38 px (34 px on a window under 820 px high), footer 26 px, shelf 236 px (a 44 px rail below 1400 px) |
| Slivers | 30 px wide, at the stage edge |
| Soft crop | a window partly off screen fades to 55 % over its last 36 px |
| Overview scale | 0.34; minimum card width 760 world px; desk row gap 330; link gutter 170 |
| Zoom chase | τ = 40 ms; settle: critically damped spring, ω = 26 rad/s (about 300 ms) |
| Zoom release | entering completes if `p + 0.15·v ≥ 0.4`; leaving completes if `p + 0.15·v ≤ 0.6` |
| Zoom by touchpad | 420 px of travel is the whole zoom; it ends after 80 ms idle |
| Zoom by notch | one notch runs the whole eased zoom; a notch the other way turns it round |
| Pinch | `p += dy/108` |
| Ctrl+drag | 320 px is the whole zoom |
| End latch | at either end, the rest of the stream is swallowed until 150 ms pass or the direction reverses |
| Pan by alt+swipe | snaps after 120 ms idle |
| Overview keyboard camera | `.2s cubic-bezier(.2,.8,.2,1)`; the selection stays 48 px inside the edges |
| Which-key | appears after Alt is held 400 ms |
| Companion transitions | transform and opacity `.28s cubic-bezier(.2,.8,.2,1)`; filter `.28s cubic-bezier(.4,0,.2,1)` |
| Companion open at cursor | from `scale(.9)`, opacity 0, blur 8 px, origin at the anchor; 400×min(440, 55 % of stage), 360 wide in a window below 1240 px (the window's width, not the stage's) |
| Companion dissolve | `.26s cubic-bezier(.4,0,.2,1)` to opacity 0, blur 10 px, scale 1.025 |
| Companion docks | `br` (default), `bl`, `right` (w = min(420, 34 %), h = stage − 28), `cb`; others 400 wide × 52 % high; in a window below 1400 px (the laptop) every dock is at most 330 px wide and half the stage high, as the mockup draws them (corrected 2026-11-23: the mockup wins on looks) |
| Sticky tabs | 30 px each; tab margin transition `.25s`; merge over 56 px; order grade 9 px per index; distance margins 14 px + 9 px per unit of distance, capped at 4 |
| Pad paper minimum height | column height − n·30 px |
| Mark hover cards | open after 160 ms, hide 220 ms after leaving; 330 px wide; opacity + translateY(4 px) over .16 s |
| § row hover | background dark; text fades to pad white and back (§10.3) |
| Search | backdrop `rgba(8,8,10,.28)` + 2 px blur, fade `.18s cubic-bezier(.4,0,.2,1)`; panel from `scale(.85)` with `transform .23s cubic-bezier(.05,.9,.1,1.05)`, origin 50 % 30 %; selection glides `top .15s cubic-bezier(.05,.9,.1,1.05)`; close `.14s` to scale(.94) |
| Veils | text transparent with an 11 px text-shadow blur; images blurred 6 px; unveil over .6 s (blur 7→0, opacity .6→1) |
| Focus mode | `.28s cubic-bezier(.2,.8,.2,1)`; reading measures: sheet ≤ 980 px, pads 820, video 900, paper 820; document zoom 0.6–2.2 in steps of 0.1 |
| Toast (gesture HUD) | bottom centre, 2.2 s |
| Reduced motion | every transition becomes an opacity crossfade of .2 s or less; zooms cross-fade in .25 s |

These are presentation values, outside the no-made-up-constants rule, which governs model and decision quantities. If one needs to change, the change is recorded in the stage review with its reason.

### 4.4 What not to copy (the mockup's own defects)
| Mockup behaviour | Build it as |
|---|---|
| Focus mode stays half width (round 14's uniform slot overrode it) | Focus is truly full screen (owner decision 11) |
| A right-click opens the menu twice and shows the full verb list | One listener. The split menu: promoted rows, then the verbs for that object kind (§9) |
| Most source-menu verbs are unwired | Every verb is wired (§9.1 table) |
| Append ignores the chosen pad | Append goes to the chosen target, which is remembered per desk; "+ a new pad" creates one |
| The highlight ✎ jumps to line −1 | Two-way links are anchors stored on both ends (§10.7) |
| "Put a check in your scratchpad as a cell" shows nothing | It inserts a previewed diff into the pad (§8.4) |
| The deriving pad's lines don't open the editor | Every editable block opens the editor (§10.5) |
| `alt+t` falls into a legacy accordion | Not built. The stack modes are `one` (sticky tabs), `pair` and `split` only (§5.2, §10.1, §10.2) |
| `#goal=video` and "you are reading" sit under the sticky player | "You are reading" and scroll targets account for sticky headers: targets land below the player (§7.4) |
| A plain horizontal two-finger scroll pans the strip (contradicting GESTURES.md) | Only `alt` + horizontal swipe or shift+wheel pans the strip. A plain scroll scrolls the window under the pointer (§5.5) |
| Ctrl+wheel over the top bar uses an old path | Gestures are routed only by the stage (§5.5) |
| The companion's "ask about this…" input is static | A real input; Enter asks; the answer streams |
| The drain, carry chips, chapter "accept", lesson modes and sketch tools are unwired | Each is wired in its stage or listed as deferred (§17) |
| Promoted rows are the same on every passage | Computed per object from the union read (§9.1) |
| `alt+;` always writes to one desk's pad | Writes to the current desk's running pad, using the focused video's clock |
| The first build runs six times; nothing persists | One build from the persisted workspace |
| The paper's dropped math is restored by hand | Fixed at extraction (KD3 and the extractor's math handling); a block with dropped math shows its health flag (§7.3) |

---

## 5. Desks, windows and navigation

### 5.1 Desks
- **What a desk is.** A desk is a room: a title, an ordered strip of slots, a focused window, the companion's dock and shown state, and optionally a goal (`goal_id`; the default is the learner's primary active goal, §12.1).
- **Persistence.** Desks persist (`desks`, §15.1). The camera offset is never stored; it is derived from the focus.
- **The top bar** shows one tab per desk; clicking one switches desks. The order is the vertical stacking order (`move_desk`).
- **Switching desks:**
  - `alt+j/k` past the end of a pad stack or pair (§5.4), or a desk tab;
  - each desk keeps its own focus and camera;
  - the camera eases vertically between desk rows over .55 s.
- **New desks:**
  - From the menu verb `⊞ New desk from these`: the window moves, with its linked thread window.
  - From gather to a new desk (`alt+shift+g`, §6.6).
  - From `+` on the desk tabs.
  
  A new desk is titled from its first window ("new desk · <short name>"), and the learner renames it inline.
- **Archiving.** A desk archives; it is never deleted silently. An archived desk's pads stay in the library (pads belong to the library; desks hold views: design review, adopted).
- **First run.** A new vault starts with one desk holding the last-read source and a running pad. An existing user's first open builds one desk per recently read source set (a deterministic grouping by the most recent reading sessions), each with its running pad. The learner reorganizes from there.

### 5.2 Windows and slots
- **What a window shows.** A window shows one `ContentRef` (§3.4): source, video, pad, lesson, thread, compare, panel or figure notebook.
  - **A pad stack** is a window whose content is an ordered list of `pad` or `lesson` refs, with the active entry and its mode (`one` or `split`). A Teacher lesson can therefore sit in a stack as a tab (§11.1).
  - **A pair** is two windows sharing one slot (panes 0 and 1). There is no separate pair object.
  - **Compare** is a window kind: the CA/RW4a compare view.
  - **`panel`** windows host existing components (Guide rail, reading path card, library pane, notes rail) inside desks until their replacements land (§21.1).

- **One window per slot, full height** (O12). Every window takes one uniform slot, and two slots fill the viewport. The mockup's `third` / `twothird` / `full` widths and the `r` width cycle are not built. A window's content fills the slot's full height: a paper page or book sheet stretches to the bottom (the mockup's `.beside > .paper {flex: 1 0 auto}`); there is no gap below a short page.
- **Pairs (`alt+,` / `alt+.`):**
  - `alt+,` stacks the focused window with its right neighbour into one slot: top and bottom, equal heights, a 6 px divider.
  - Each pane header shows the glyph and title, plus a hint: "alt+. gives it its own slot" on the active pane, "click or alt+j/k" on the other. The active pane has a 2 px amber left edge.
  - **At most two windows per slot.** A third `alt+,` toasts "a slot holds at most two windows · alt+. takes one out". With nothing to the right it toasts "nothing to the right to share this slot with".
  - `alt+.` gives the active pane its own slot right after the pair and focuses it. A pair left with one window becomes that window.
- **Pad stacks** are one window. Their own split mode (2–3 pads above and below each other) is set by the arrange micro-journey (§10.2).
- **Opening a window:**
  - *Open beside* inserts the new window right of the focus and focuses it, keeping the previous focus in view.
  - If the target is already on the desk (same source, and for books a range that covers the span), the existing window is focused and scrolled to the span instead. **No duplicate opens.**
  - The new window fades in over .45 s.
- **Closing a window:** `alt+w` or the header's ✕. The shelf shows "↺ undo close **name**" for 9 s. `esc` never closes a window.
- **Moving windows:**
  - `alt+[` / `alt+]` move the focused window one slot along the desk; its neighbour slides over in .45 s and the viewport follows.
  - In the overview, `alt+shift+j/k` (or dragging) moves it to the desk below or above.
  - Dragging a shelf row more than 5 px reorders the strip; the other rows shift over .18 s.
- **Slivers:** the off-screen neighbour on each side shows as a 30 px button at the stage edge (‹/›, glyph, vertical short name, `▶ m:ss` for videos). Clicking it focuses that window.
- **Soft crop:** a window partly off screen fades at the screen edge, so no text is cut mid-word.

### 5.3 The footer
From left to right, the footer shows:
- the key hints for the current mode (§5.4);
- the **column dots**, one pill per window: the windows in view are filled, the focused one is amber, and a click focuses (O10);
- `↺ ungather` while a desk is gathered;
- **"hold alt for navi hints"**.

In focus mode, the focused dot grows to 46×5 px amber and the others fade to 45 %. Pen mode prepends its own hint.

### 5.4 Keys
**Which-key.** Holding Alt alone for 400 ms shows the which-key panel (headed "alt +"):
- **move:**
  - `h / l` window left or right;
  - `j / k` pad or pane below or above, then the desk below or above;
  - `[ / ]` move window;
  - `shift+j / k` window to another desk (overview);
- **windows:**
  - `↵` focus (full screen);
  - `w` close (undo);
  - `g / shift+g` gather / gather to a new desk;
  - `o` overview;
  - `, / .` share a slot / own slot;
- **pads:**
  - `n` new pad;
  - `a` arrange pads (not `s`: `Alt+S` is Settings, `keymap.ts:73`);
  - `d` sketch block;
  - `;` insert ▶ timestamp;
- **media:** `space` play or pause.

Any other key, or releasing Alt, hides the panel. Below 1240 px it uses two columns.

**Bare-Alt collision.** Today a bare Alt keyup with nothing else pressed clears the capture (`bareAlt.ts`). The rule becomes:
- **a tap under 400 ms clears**, as today;
- **a hold of 400 ms or more shows which-key and never clears.**

`useBareAltClear` gains the hold threshold, and `keymap.test.ts`'s collision table gains every chord below.

**Bare keys in the reading view** (never while typing; Alt variants work while typing where noted):

| Key | Action |
|---|---|
| `c` | Companion here: summon at the selection or cursor, dissolve if anchored, hide if docked (§8.3). `alt+c` while typing |
| `shift+c` | Companion at its dock, or hand an anchored companion to its dock |
| `/` | Search in context (§9.3) |
| `.` or the ContextMenu key | The menu on the hovered object (§9) |
| `ctrl+tab` / `ctrl+shift+tab` | Next or previous pad in the focused stack |
| `p` | Your path (§12.5) |
| `n` | A margin note on the hovered passage |
| `b` | Run the first promoted action of the hovered object |
| `u` | Toggle follow-along on a book window following a video (§7.5) |
| `space` | Play or pause the focused video |
| `o` / `alt+o` | Overview (§6) |
| `x` | Swap the two windows in view |
| `=` / `-` / `0` | Document zoom in focus mode |

**Existing Reader chords kept:**
- `alt+←` the return stack (RW1a);
- `alt+↓/↑` step through cues (RW3);
- `\` collapses nothing now (there is no rail), so it is freed;
- `ctrl+shift+f` compare becomes the Compare verb (§9.1).

**The key router.** One capture-phase router (`DeskShell`) owns workbench keys, and the scopes are explicit:
- typing in an `input`, `textarea` or editor;
- the overview;
- focus mode;
- an open menu;
- an open check;
- pen mode.

The mockup's twelve stacked listeners, and the bug where a document-level typing guard blocked the editor and search keys, are not reproduced. Editor and search keys route at the window's capture phase before any guard.

**The resolved scope and precedence matrix (review F16).** The first matching scope wins, top to bottom. Every chord here is added to `keymap.test.ts`, with a test per scope that the chord reaches its owner and no other.

| Scope (highest first) | Owns | Passes through |
|---|---|---|
| A notebook frame (focus inside the iframe) | Everything except the four bridge messages (§11.3) | `c`/`alt+c`, right-click, Escape, mousedown → the workbench |
| An open check card | Typing, `↵` submit, `esc` "not now" | `alt+o`/zoom are blocked while an administration is open |
| An open menu or the search panel | `↑↓ j k ↵ esc`, verb letters, `tab` | nothing |
| Typing (input, textarea, `LiveMarkdownEditor`, `MathLiveEditor`) | All bare keys | shell chords marked `whileTyping` (Ctrl+P, Ctrl+K, Alt+S Settings, Alt+1–4 places) and `alt+c`, `alt+h/l/j/k`, `alt+[ ]`, `alt+, .`, `alt+enter` |
| The arrange overlay | `↑↓ j k space = ↵ esc` | nothing |
| Pen mode | pointer input on content; `alt+p` leaves | every key |
| The overview | `h j k l`, arrows, `↵`, `alt+↵`, `esc`, `o`, `g` (hold), `b`, `alt+[ ]`, `alt+shift+j/k` | shell chords |
| Focus mode | `= - 0`, `esc`, `alt+h/l` | the reading-view keys |
| The reading view (DeskShell) | The bare keys and Alt chords in this section | shell chords |
| The shell (`keymap.ts`) | `Alt+1–4` places, `Alt+5–7`, `Alt+9`, `Alt+0`, `Alt+S` Settings, `Ctrl+,`, `Ctrl+P`, `Ctrl+K`, `Ctrl+O`, `Ctrl+V` add | — |

**The resolved collisions:**
- `Alt+S` stays Settings, so arranging pads is `alt+a`.
- `ctrl+drag` inside window content stays box selection; on the stage background it scrubs the zoom.
- In the pad menu, `s` submits and `i` inserts a source piece.
- Alt + vertical scroll zooms; pads and desks move with `alt+j/k` (D14).
- The bare-Alt tap clears and the hold shows which-key.

### 5.5 Gestures
- **Modifier tracking.** Alt and Ctrl are tracked from keydown and keyup in the capture phase, cleared on window blur, and ORed with the event flags (§3.6).
- **The wheel router.** One wheel listener, `{passive: false, capture: true}`, active only over the stage and shelf, decides by the *first* event of a gesture and keeps that kind until the gesture ends.
  - **Alt + horizontal-dominant** pans the strip: the camera follows the fingers, then snaps to the nearest window's left edge and focuses it.
  - **Alt + vertical, or anything with Ctrl,** zooms. Down zooms out to the overview; up zooms back in on the selected card. The source is classified as touch (small pixel deltas), pinch (ctrl+wheel without the Ctrl key held) or notch (`deltaMode ≠ 0`, or a first delta of 40 px or more), with the behaviours in §4.3.
  - **Deltas are normalised:** a line is 40 px; a page is the stage height.
  - **A plain scroll** scrolls the window under the pointer and never pans the strip. **Shift+wheel** pans.
- **The HUD** (bottom centre) names what the gesture is doing, for example "alt + scroll · zooming out · lift to settle".
- **Ctrl+drag on the stage background** (the gaps between windows, the slivers and the area outside window content; never inside a window's content, where ctrl+drag stays the existing box selection, `readerKeys.ts:12`) scrubs the zoom.
- **Touch** never draws in pen mode (palm rejection).
- **Pinch on WebKitGTK** may not arrive; it is optional, never the only way.

### 5.6 The shelf (the strip's minimap)
Below 1400 px the shelf folds to a 44 px rail with a `☰` button, which overlays the shelf at 260 px.

**Header:** "STRIP" and "/ switch".

**One row per window:**
- glyph and kind;
- a state word: "· focus", "· in view" or "· same idea" (out of view, sharing an LO with the focus);
- the title;
- a **minimap bar**:
  - reading progress from `reader_section_progress`;
  - ticks for LO anchors (grey) and tutor citations and passage links (purple);
  - an amber dot per reader question;
  - an amber line for the current position;
  - in goal mode, the path ranges (§12.3) and a criticality bar at the row's right edge;
- a "where" line, for example "p.<page> · chapter <n> read", "▶ <position> of <length> · your question at <time>" or "§<section> · not read yet".

A click focuses the row's window (and leaves the overview); a drag reorders.

**Lower part:**
- "↺ undo close …";
- **TODAY · RUNNING PAD**, with `open` and the last three blocks of today with their marks; a click scrolls the stack to the running pad;
- **CARRIED**, the carried questions (§10.12).

The old palette and "drain ▸" are gone (owner decision 12).

### 5.7 Focus mode (full screen)
**Entering and leaving.** `alt+enter` toggles focus mode; `esc` also leaves. From the overview it opens the selected card in focus.

**What changes:**
- The top bar, footer and shelf collapse to nothing.
- The focused window becomes truly full screen, at its reading measure (§4.3) and centred. Its document zoom is set with `=`/`+`, `-` and `0`, with a `NNN%` badge.
- The badge "alt+↵ or esc to leave · = − to zoom" fades over 2.2 s.
- `alt+h/l` moves focus mode to the neighbour.
- The companion still works.

**Leaving** restores every window's position, the camera and each window's scroll exactly.

**Document zoom** is a per-window view setting (`set_view`). It uses the CSS zoom of the content, never a transform, so text re-rasters sharply.

---

## 6. The overview

### 6.1 What it shows
Every desk is one row of cards at scale 0.34, with an uppercase desk label above.

**A card holds:**
- **a thumbnail:**
  - for a book or PDF, the page you are on, rendered by pdf.js to a cached bitmap at card size, or for render-only sources the first visible blocks drawn small;
  - for a video, the YouTube poster with `▶ m:ss` and three transcript cues;
  - for pads, threads and lessons, a **live miniature**: a scaled clone of the window's content, built when idle, with iframes replaced by a placeholder;
- the glyph and short name;
- the minimap bar;
- up to two chips, chosen from the union read (§7.6), for example "? your question on Fig <n>" or "◇ the tutor adjusted your reasoning". This is an attention limit, labelled.

**Other card styles:**
- A pad stack has offset shadows and thin bands listing its pads.
- A pair shows both panes.

**Selection and links:**
- The selection ring is 3k amber plus a 7k halo.
- **Relations** are drawn for the focused or hovered card (§6.5); unrelated cards recede to .38 opacity.
- The companion becomes a corner pill: "◇ <thread title> › c". Clicking the pill leaves the overview.

### 6.2 Entering and leaving
**Entering:**
- `o`, `alt+o` or the top bar's `overview` button runs the fast eased zoom (about 300 ms, the spring settle).
- `alt+scroll`, `ctrl+scroll`, pinch and `ctrl+drag` drive the zoom with the input.

**Leaving:**
- `esc`, `o` or `alt+o` return to where you were before the overview: the desk, focus and camera.
- `↵` opens the selected card.
- `alt+↵` opens it in focus mode.
- A click on a card opens it.
- Zooming in (scroll up) zooms in on the selected card.

**Navigating inside the overview:**
- `h/j/k/l`, the arrows or `alt+h/j/k/l` move the selection: left and right within a desk, up and down to the nearest card by x-centre on the next desk.
- The camera follows, keeping the selection 48 px inside the edges.
- The wheel pans freely; dragging the background pans.
- Dragging a card more than 8 px moves it (dropped onto a desk row and index).
- `alt+[ ]` moves the selected card along its desk; `alt+shift+j/k` moves it to the desk below or above.
- Holding `g` previews a gather: dashed cyan ghost outlines show where the linked cards would go.

### 6.3 The zoom engine (adopted design; O6)
**State.** One state object holds:
- `p ∈ [0, 1]`, the zoom progress;
- the two geometries, A (reading) and B (overview), computed once when the gesture begins by `geom(false)` and `geom(true)`;
- the two cameras.

B's camera keeps the selected card at least 48 px from the edges (74 px from the top).

**Per frame** (one rAF writer; transforms and opacity only):
- The camera scale is interpolated in log space, `s = A.s·(B.s/A.s)^p`. `q` is the linear fraction of the scale change.
- **Each window** is translated and scaled from its reading rect to its card rect by `q`.
- **The windows that were on screen stay live.** Their content is counter-scaled so text never stretches, and it fades over `q ∈ [.45, .85]` while the card face fades in over the same span.
- Links and desk labels fade in over `q ∈ [.6, 1]`.
- Slivers fade by `1 − 3q`.
- Receding cards dim to `1 − .62q`.
- The focused window's amber edge fades over the first third.

**Inputs:**
- *Touch* chases the fingers (τ = 40 ms).
- *Notch* and the `alt+o` key run the spring from the current velocity.
- *Release* decides by the rule in §4.3.
- At either end the stream is latched.
- A key press or a pointer press during a zoom settles it at once.
- A cancel (it springs back to where it began) lays out nothing.

**Commit.** One commit runs at rest. It restores scroll positions, freezes each live window's reading size, lays out, sets the camera, draws the links once and moves the companion to its pill.

**The invariant (review F10):** the zoom's last frame is the overview's first frame, and the reverse when leaving (O6). It is tested in two ways. First, every window's rect, scale and opacity at the last animated frame equals the committed layout's to within 0.5 px, an exact geometry assertion. Second, real-webview screenshots of the two frames differ by no more than a documented tolerance, which absorbs rasterization differences (antialiasing, 1 px borders snapped at different scales). The mockup's commit differed visibly at 1 px borders, and the build must stay within the tolerance.

**Leaving.** Back in the reading view, `will-change` is dropped for two frames so text re-rasters sharply.

**Reduced motion.** The zoom becomes a .25 s crossfade.

### 6.4 Self-tests kept as tests
The mockup's two self-tests become component tests (§18.2):
- the round trip, where four ways back from the overview restore the reading layout to within 1 px (the owner's "bottom edge truncated" bug must stay fixed);
- every navigation path keeps the selection inside the view.

### 6.5 Links between cards (curved; O8)
**Relations of a card, by weight:**
- 3: an explicit link. Examples: a pad block anchored to the source; a back-link; an open-beside history; a thread citing the source.
- 2: the same source on another desk ("same book").
- 1: a shared LO through `section_coverage` or the pad's LO tags ("same idea").

The top four are drawn with a cyan ring. They are an attention limit, labelled.

**The curve.** Each link is a cubic Bézier from the focused card's bottom centre to the target's bottom centre, each link offset by 26 world px from its neighbours. On the same row it dips; to another row it is a vertical S. Its label sits at u = .82.

**Toggles.** `b` in the overview toggles relations. There is no right-angle option in the product; the mockup's `links:` chip was a comparison aid.

### 6.6 Gather
**Ranking.** `alt+g`, or the menu verb `⇇ Gather linked sources`, gathers around the focus. The desk becomes:
1. the windows before the focus that aren't linked;
2. the focus;
3. the linked windows by weight (§6.5);
4. the rest.

Windows slide over .45 s.

**Undo.** `alt+g` again, or the footer's `↺ ungather`, restores the previous order.

**To a new desk.** `alt+shift+g` moves the focus and its linked windows to a new desk named after the focus's main LO. A placeholder sliver, "→ moved to “name”", stays in the old desk for 6 s.

**Display limit.** At most four linked windows move along, an attention limit, labelled in the toast with "and N more stayed".

---

## 7. Source windows

### 7.1 Book and PDF windows (from `ReaderScreen`'s source pane)
- **What the window renders:**
  - `reader.render_view` for the window's range: a whole reading, a section, or a span range for a ranged window;
  - or the PDF pane for PDF-native sources.
  
  Everything the source pane does today keeps working inside the window: selection (drag, ctrl+drag boxes, alt+drag paragraphs), capture, margin cues (RW3), active reading cards (RW1b), inline quick checks, figure insets (RW5), exercise candidates (RW4b), and the detour strip and return stack (RW1a).
- **Layout:**
  - Running heads at the top of each page.
  - A two-column grid: passages, plus a side margin for notes and marks.
  - Below 640 px the margin folds under each passage.
  - The book sheet is Literata on paper `#f7f5f0`, and it stretches to the window's full height.
- **Gutter glyphs** sit 30 px left of the text: `◇` for LearnLoop (a link, an adjustment, a figure), `›` for the learner's words, `?` for a question.
- **Margin marks** open small cards with the detail:
  - "◇ the tutor adjusted your reasoning · <date>" shows the learner's words and the tutor's sentence;
  - a passage link shows its reason and quote;
  - "› your words, <date>, while practising" (a real learner-text gap);
  - "? your question, <date> · in the companion" opens the companion at that thread.
  
  All of them come from the union read (§7.6), not hand placement.
- **Margin notes:** `n` on a hovered passage, or the menu's Note in margin, opens a margin box: "↵ keep · esc let go · yours: never graded, never evidence". It writes an annotation (`reader.create_annotation`, type `interpretation`, with `learner_text`). Notes on transcript cues use the same annotation path, because cues are source spans. A note on a pad line is a different thing: a `note` block attached to that block (`payload.parent_block_id`), since pads have no source/revision/extraction identity (`H:reader.py:1208` requires one).
- **Highlights** are the learner's saved annotations, drawn in blue. They are distinct from the live selection, which is drawn as the system selection.

### 7.2 Web windows
A web source renders through `render_view` like a book. Its blocks are web blocks.

### 7.3 Paper windows (arXiv and other papers)
A paper renders in Source Serif 4, with the paper's own section numbering, and its page fills the full window height (O12).

**Dropped math.** Where an extraction dropped inline math, the block's health flag shows ("math missing in this extraction · view the PDF"). Opening the PDF beside is one click. The fix itself belongs to extraction: KD3 brings arXiv full text through `/html/` or the PDF with math, and the extractor's math handling is the fix. The mockup's hand restoration is not built.

### 7.4 Video windows (O7)
**The sticky player** stays at the top of the window and holds:
- the frame;
- a scrub track with the playhead (and chapter ticks once chapters exist, §7.9);
- a line: "▶ m:ss / duration".

**The frame:**
- It shows the YouTube thumbnail with a ▶ button that turns red on hover, and the time.
- A click swaps in the embed (`youtube-nocookie.com/embed/<id>?start=t&autoplay=1&enablejsapi=1`), through `YouTubeWatchPanel`'s existing origin checks and CSP.
- **No "opens YouTube (serve over http to embed)" text** (O7).
- If embedding is refused (error 153 and similar), the frame says so in one line and offers to open the video in the browser at that time.
- The player's `infoDelivery` time drives the window's clock.

**The transcript:**
- The caption spans render in paragraphs (a sentence end after at least 2 cues, or 6 cues), each with a timestamp gutter.
- The current cue is amber.
- Cues with a question or highlight carry their marks.
- A click on a timestamp seeks.

**Sticky offset rule.** Scroll targets and "you are reading" use the visible area *below* the sticky player. The mockup's defect, where the goal callout was hidden behind the player, is not reproduced.

**Keys:**
- `space` plays or pauses.
- `alt+;` appends "▶ <video> at m:ss" to the current desk's running pad, as a `source_quote` block anchored to the cue span.

### 7.5 Follow-along (book ↔ video)
**What it does.** While a video plays, a book window on the same desk that covers the same LO marks the passage for the playing cue's LO in cyan and scrolls to it. Its header chip reads "following ▶ <chapter> <time> · <passage label>". `u` toggles following, and the unlinked state reads "unlinked · u to follow ▶ <chapter>".

**The mapping:**
1. The playing cue's section (from the video's section map of `t=` units).
2. Its LOs (`section_coverage`).
3. The correspondent passage in the book (`reader.correspondents` for that LO), preferring the path's primary section.

Where no correspondent exists, the chip says "no passage here" and nothing scrolls. There are no hand maps.

### 7.6 The per-span union read (owner decision 7: "find everything tied to a passage")
**The call.** `passage.union_range {extraction_id, from_span_id, to_span_id}` returns, for each span in the visible range, everything anchored to it, translated through `span_aliases` across readings. It is called once per visible range when a window settles, and again when the range grows. It is never called per span on hover; hover cards read the cached range.

**What it returns per span:**
- the learner's annotations (highlights, notes, pen marks);
- pad blocks anchored to it (`pad_block_anchors`);
- tutor exchanges whose selection or citations include it (`question_event_spans`);
- **tutor adjustments**: exchanges where the tutor corrected the learner's reasoning about this span. The mockups showed these are the learner's real learning moments, so they get a first-class `◇` "the tutor adjusted your reasoning" mark (brainstorm §11);
- learner-text gaps anchored to it (`learner_text_gap_spans`), with their anchor quality;
- `passage_links` with reasons;
- figures made for it;
- "a check is due before this" (`checks.due_for` hosts), with no item content (§12.6);
- linked notes (`learner_note_links`);
- the LOs and coverage of its section;
- reader-authored questions;
- its exposure and cold eligibility (`effective_eligibility`).

**The goal level is not part of the union read.** It is goal-conditioned, and the same source can sit on desks with different goals. It comes from `goal.lens`, keyed by goal and range (§12.3).

**Backfill recipes, per source (review F5).** The two DERIVED span tables are rebuilt from what exists, and they never invent locality. Each row records an anchor quality: `exact_selection`, `citation`, `source_context` (the reading and section the learner was in, without a span) or `unanchored`.

| Source | Recipe | Quality |
|---|---|---|
| Reader exchanges (`question_events` with context `reader`) | Reconstruct with the existing `reader/reader_dialogue.py:ask_provenance` (selection span ids and quote → `exact_selection`; cited spans → `citation`) from the `interaction_events` reader payload. The original extraction id is kept, and alias ambiguity is kept as `needs_reanchor` | exact or citation |
| Practice and feedback tutor questions | The item's source refs, if the item carries a span locator; else the item's LO | `source_context` or `unanchored` |
| Gaps of kind `reader_formative` | The authored question's span (`reader_authored_questions`) | `exact_selection` |
| Gaps of kind `workbench_text` | The workbench session's `span_ids_json` | `source_context` |
| Gaps of kind `learner_note` | The note's link target, when it is a passage | `exact_selection` |
| Gaps of kind `tutor_question` | Through their question event, as above | as the event |
| Gaps of kind `stuck_answer`, `diagnosis`, `hint_feedback`, `lesson`, `external_chat` | The item's or lesson's span refs when present; otherwise **`unanchored`**, kept as an LO-level association. `entity_source_links` says what content relates to an LO, not where the learner wrote, so it is never used to place a gap on a span | `source_context` or `unanchored` |

**Consumers by quality:**
- Margin marks show only `exact_selection` and `citation` rows.
- "What this knows" shows every row with its quality in words ("you asked this while on this page", "about this objective").

**Fixtures.** The migration-head fixture has no rows in these source tables. RD0 seeds synthetic historical records for every supported adapter in `tests/desk_helpers.py`. A test then compares the live projection with a rebuild, row for row.

**Write-through.** New exchanges and gaps write their spans at once, through the same code as the replayer, which has one replayer each in `substrate/rebuild_orchestrator.py`.

**Consumers:**
- margin marks (§7.1);
- promoted menu rows (§9.1);
- overview chips (§6.1);
- shelf ticks (§5.6);
- the "What this knows" panel (§9.1, the design aid the mockup left unwired);
- the structural protection of checks (§12.6).

### 7.7 Links from answers and pads to sources
- **Claims.** A tutor answer's citations render as claims ("§ p.N" or "▶ <video> <chapter> <time>"). A click opens the target beside, or focuses and scrolls the existing window, and seeks a video.
- **Pad back-links** ("§ <source> p.<page> ↩", "▶ <video> <chapter> <time> ↩") do the same.
- Every target is an *open spec* (§5.2), so one function serves every caller: claims, markers, promoted rows, search results, path rows, back-links and the `b` key.

### 7.8 Thread windows
A tutor thread (a root exchange and its branches) can be pinned as a window. It uses the companion's thread rendering on the dark panel style. Pinning is the menu verb "Pin this thread as a window" in the companion.

### 7.9 Suggested video chapters (RD10)
A video window shows "◇ suggested chapters". Each chapter has a time range, a title and its LO tags. They are judged against the vault's LOs by a judged route over the transcript sections (the brainstorm's "video chapters judged against objectives").

Each chapter has `accept` and `not this` buttons:
- **accept** stores the chapter (`video_chapters`, WORKFLOW, learner-confirmed), draws its tick on the scrub track and sets its range on the minimap;
- **not this** dismisses it, logged.

A suggestion is a proposal and never changes coverage on its own. A learner-accepted chapter can feed `section_coverage` as `origin learner` through `curriculum.coverage_correct`.

---

## 8. The companion (app-wide)

### 8.1 What it is
The companion is the existing tutor (Reader ask, `ask_tutor_question`, the lesson's ask) behind one floating panel that every screen mounts (owner decision 7). On the workbench it follows the focused window ("following ▶ <video> <chapter>"); on Practice it follows the item; on Today, the plan. "Teach me" still opens a Teacher lesson (§1.1).

**Header:**
- a grab handle;
- tabs `◇ tutor` | `history`;
- `c hide`;
- the context line ("following <glyph> <window>", and "◎ goal in context" when the desk has a goal);
- "earlier · <date> · <date> · <date> ›", which opens the history.

**Body:**
- the desk's thread, or the screen's;
- with no thread: "◇ nothing asked on this desk yet · select a passage and press c".

**Input:**
- the selection chip "§ asking about “…” ✕";
- a real text input, "› ask about this…": Enter asks and the answer streams in.

### 8.2 States
| State | What the learner sees |
|---|---|
| docked | It sits at one of four docks (`br`, `bl`, `right`, `cb`), remembered per desk. Dragging the handle snaps on drop to the nearest dock with a FLIP move |
| hidden | `c` while docked eases it down and out (translateY by its height + 40, opacity 0, scale .96). A tab "◇ tutor · <thread> c" appears at the dock edge; clicking it reopens |
| anchored | Summoned at the cursor or selection (§8.3) |
| overview | It eases into the corner pill in lockstep with the zoom progress |
| avoid | When the selection, a lit passage, a highlight or a margin box lies under it, it slides sideways once (up to 600 px) |

**The rule (scoped; review F17).** A **docked** or **hidden** companion never moves when the learner scrolls, pans, reorders, gathers, pairs or switches desks. An **anchored** companion leaves its anchor by exactly the transitions in §8.3 (a hand-off to the dock as a FLIP, or a dissolve), never by jumping. Both are tested, kept from the mockup's move log.

### 8.3 Summon and dissolve (O5)
- **`c` with no companion showing** opens it **at the cursor**. The anchor is the selection's rects, else a pen lasso, else the caret, else the last pointer position. It is placed 10 px below the anchor if it fits, else above, clamped to the stage. It eases from `scale(.9)`, opacity 0 and blur 8 px, with its origin at the anchor, to its rest state over .28 s. The selection becomes the "asking about" chip (owner decision 5).
- **`c` while anchored dissolves it in place:** over .26 s it goes to opacity 0, blur 10 px and scale 1.025, then silently resets to hidden. **It never teleports.**
- **Summoned from the drawer** (`shift+c` or the tab), `c` sends it back to the drawer. *Summoned at the cursor*, `c` dissolves it where it is.
- **Hand-off to the dock.** An anchored companion moves to its dock by a FLIP from its rect when:
  - the anchored text scrolls away (more than 250 ms after opening);
  - the view moves;
  - the overview opens;
  - its handle is dragged.
- **Inside a Teacher notebook frame**, `c` over a selection opens it at the selection (rect translated by the frame's position) with the text as context, and `shift` docks it instead (§11.3).
- **Reduced motion:** opacity only, .2 s.

### 8.4 Answers that act
- **Claims** open beside (§7.7).
- **Action buttons** (HMWL's "View sample implementation") propose changes into a pad as a **previewed diff**: green inserted lines with "accept" and "not this". Accepting writes blocks with `provenance: tutor`. Examples: "Put a check in your scratchpad as a cell"; "Add this derivation to your pad".
- **Small figures** (Show me) appear in the answer with "view source" (opens the figure notebook window) and "move to scratchpad" (§13.1).

### 8.5 History, searchable (owner decision 2)
The history tab shows "every exchange stays here, by day and by desk, with the passage it was about · also in / search". Exchanges are grouped by day and then desk, newest first. Each exchange shows:
- "› question";
- "◇ the answer's first sentence";
- where it happened ("while practising", "in the Reader", "in a lesson");
- the anchor button ("§ <source> p.<page> · Fig <n> ↗", which opens beside).

**Backing data.** `companion.history` reads `question_events` (every context) joined with `companion_exchange_context` (desk and surface; backfilled as "before desks" for old rows) and `question_event_spans`. Its query searches question and answer text lexically and, through the job, by meaning (`search_spans`'s embedding route over exchange text).

**Search.** History also appears in search's "past companion exchanges" group (§9.3).

### 8.6 Context the companion sends
`companion.ask` sends the existing `reader.ask` context:
- the selection spans and quote;
- `cold_active`;
- the branch parent;
- `retrieval_intent`.

It adds:
- the desk;
- the surface;
- the focused window's spec;
- any selected pad blocks (pad text is learner text, which the tutor may read; §14);
- the desk's goal.

During an open cold check, `cold_active` is true and the veiled material is excluded from the tutor's context (§12.6).

---

## 9. Menus and search

### 9.1 The source menu (a split menu)
**Invocation:** right-click on a passage, a transcript cue, a highlight or margin note, or a window header. The `.` key or the ContextMenu key opens it on the hovered object, or on the focused window's first object.

**The header** reads "<a passage | a transcript cue | your margin note | a window> · “<first 46 chars>”".

**Keys:**
- `j/k` or `↑↓` move;
- `↵` runs the row;
- `esc` closes;
- each verb's letter runs it.

A mousedown outside closes the menu.

**Promoted rows.** Up to four rows, visually separated, come from `passage.promoted`. They are ranked from the union read and the learner's history for this object. Each row carries its glyph, its label, its reason in small text ("found by search, not checked", "the tutor quoted this on <date>") and an action. Examples:
- "? open your question in the companion";
- "▶ <video> ▶ <time> says this in words · beside";
- "§ <source> p.<page> takes it to the next step · peek";
- "◇ connects to a distinction you worked on";
- "› see your words while practising".

The cheap rows come from the union read with no model, synchronously. Rows that need judging ("says this in words") come from `search_spans` and correspondents through the job, and appear when ready with the reason "found by search, not checked" until `verify_spans` confirms them.

The limit of four is an attention limit (split-menu research), labelled.

**The verbs** (fixed positions, so experts rely on them; every one is wired):

| Verb (key) | What it does | Built on |
|---|---|---|
| `?` Ask (a) | Opens the companion anchored at the selection with it as context | `companion.ask` |
| `›` Note in margin (n) | A margin note on the passage or cue (a source annotation); on a pad line, an attached note block | `reader.create_annotation` / `pad.apply` |
| `⤓` Append to “<target>” ▸ (w) | Appends the selection (or the passage, truncated with a back-link) as a `source_quote` block to the chosen pad. The submenu lists the desk's pads with the remembered target marked, plus "+ a new pad". The highlight and the block link both ways (§10.7) | `pad.apply`, `reader.create_annotation` |
| `◌` Carry (c) | Makes a carried question from the selection or note (§10.12) | `pad` carried list |
| `▸` Open beside (b) | Opens the passage's best correspondent, or the object itself, beside; with a selection, opens the source of a claim | open spec |
| `⌕` Find in my sources (/) | Opens search with the selection as the query | §9.3 |
| `⇄` Compare (=) | Opens the compare view (CA/RW4a) for the selection across the library, in a window beside | `compare_sources`, `reader.library_compare` |
| `◇` Show me (v) | Requests a figure for the selection | `figure.request` (`origin: selection`) |
| `✎` Make it practice (p) | Drafts a practice item from the selection: an exercise import when the span is an exercise, else an authored question. The learner reviews it in a small sheet before it joins the queue | `reader.import_exercise` / `reader.author_section_question` / `author_practice_item` |
| `◎` Teach me this (t) | Opens a Teacher lesson on the selection, in a lesson window beside | `lesson.turn` (`entry: reader_selection`) |
| `⊞` New desk from these (d) | Moves the window, and its linked thread window, to a new desk | `desk.apply` |
| `⇇` Gather linked sources (g) | §6.6 | |
| `⤒` Share a slot with the next (,) | Pairs it (§5.2) | |
| `⤓` Own slot (.) | Expels it | |
| `i` What this knows (i) | Opens a panel listing the union read for this span, grouped with each row's anchor quality, each item openable | `passage.union_range` (cached) |

**What is not built.** "Set aside" is gone, replaced by the running pad. Verbs that don't apply to an object kind are omitted, never shown disabled; for example, a window header has no Ask.

### 9.2 The pad menu (O11)
**Invocation:** right-click inside a pad body, or `.` on a hovered line. The header reads "your pad · “<selection or line>”".

**Rows on the text** (when there is text):
- `?` Ask about this (a);
- `⌕` Find in my sources (/);
- `◇` Show me (v);
- `✎` Make it practice (p), "drafts an item from this line for your queue";
- `◌` Carry (c);
- `◎` Teach me this (t);
- `✓` Submit this block as… (s) (§10.9).

**Then "INSERT BELOW THIS LINE"** (or "insert at the end of this pad"):
- `✎` Sketch cell (k), "pen, line, arrow, box, text · yours";
- `◆` marimo cell (m), "Python that runs beside your notes, reactive". Available after RD9b; before that the row reads "marimo cell · arrives with notebooks" and is disabled. This is the one honest disabled row.
- Source pieces:
  - the passage in view in each open source window ("the passage in view · <source> p.<page>", key i);
  - the cue playing now in each playing video;
  - the passages the learner highlighted today;
  - "a piece of another source…", which opens search in insert mode: `↵` inserts the result as a `source_piece` block instead of opening it.

In the running pad, cells and pieces become blocks of the same kinds.

### 9.3 Search in context (O17; the Reader's search box)
**Invocation:**
- `/`;
- the shelf's "/ switch";
- the Find verb (with the selection);
- the pad menu's insert mode.

**The panel:** an input with the placeholder "search every source, note, pad, thread and past exchange". Results come in groups, at most three rows per group (an attention limit; `tab` expands a group):
1. **open on this desk** (window titles, client side);
2. **sources in your library** (titles; "· open" if on any desk);
3. **passages and moments** (`reader.search_sources`; videos open at the cue, books in the existing window or a new ranged window);
4. **your notes and highlights** (`notes.search`, annotations, learner-text gaps);
5. **your pads** (pad text, including ink transcriptions as "your handwriting");
6. **threads** (reader exchanges);
7. **past companion exchanges** (`companion.history` query).

Lexical results come back at once. A "by meaning" pass runs as a job and merges in with a quiet "· by meaning" tag.

**Keys and actions:**
- `↑↓` choose;
- `↵` opens beside the focus, or scrolls to the item if it is already open (in insert mode: inserts);
- `esc` closes.

**The animation** (rofi on Hyprland):
- the backdrop fades in;
- the panel pops in from 85 % with a slight overshoot;
- the blue selection block glides between rows;
- closing is a quick fade with a slight shrink.

The timings are in §4.3. Reduced motion removes all of it.

---

## 10. Scratchpads

### 10.1 The sticky-tab stack (O1, O2, O3)
**One window, one scroller.** A pad stack is one window and one tall scroller, in which each pad's tab header and body are siblings.

**Sticky tabs.** Each tab is `position: sticky` at `top: i·30px` and `bottom: (n−1−i)·30px`. **The tabs of pads already passed pile at the top, and the tabs of pads still ahead wait at the bottom.**

**Paper height.** Each pad's paper is at least `window height − n·30 px` tall, so one pad fills the column with blank space below short content (O1).

**The tab label:**
- ⚲ for a kept pad;
- the title (amber ink when open);
- the first line;
- meta, for example:
  - "running · beside <source> · today";
  - "beside <source> p.<page> · <date>";
  - "made <date> from your <date> question + <date> attempt".

**Tab and paper styling.** A tab is cream `#e9e6de` with a 1.5 px `#4a4740` border. The open tab is white and **merges with its paper**: no bottom border and square lower corners, so tab and paper read as one sheet (O2).

**The active pad** is the one whose body crosses the scroller's upper third, or the last pad when scrolled to the end.

**Jumping between pads:**
- clicking a tab, `ctrl+tab` / `ctrl+shift+tab`, or `alt+j/k` smooth-scrolls to the pad, landing below the pile of tabs above it;
- `alt+j/k` past the last pad goes on to the next desk;
- re-rendering keeps the scroll position.

**Merge amount.** For each tab, `m ∈ [0, 1]` is how much of the tab's own paper shows directly beneath it, measured over 56 px. It is computed each scroll frame from geometry and written per tab, never as an inherited variable (§3.6).

**Tab width grades** (a per-machine view preference; default `distance`):
- `flat`;
- `order`: tab and paper narrow by 9 px per index, so they stay one sheet;
- `distance`: margins of 14 px plus 9 px per unit of distance from the fractional open pad, capped at 4. **As a tab merges, curved fillets flare it into its paper** (radial-gradient fillets whose opacity is `m`), and the paper's top edge is drawn along the row, so the tab bar becomes one object with its paper as the next pad is revealed (O3). The margin transition is .25 s.

The mockup's `stacked` accordion and `tabbed` header modes are not built.

### 10.2 Arranging pads above and below each other (owner decision 10)
**Entering.** `alt+a` on a stack opens the arrange overlay, "ARRANGE · pads above and below each other", which lists the pads ○/●.

**Keys:**
- `↑↓` choose;
- `k` place above;
- `j` place below;
- `space` show or hide;
- `=` equal heights;
- `↵` confirm;
- `esc` cancel.

**The result.** Confirming with 2–3 pads shown gives split mode: stacked panes with draggable dividers (each at least 60 px; the ratios persist as the window's view). In split mode, `alt+j/k` moves the pane focus (an inset amber edge).

**Leaving split mode.** `alt+a` in split mode offers "↵ back to one at a time" and "a · arrange again". Both work by key and by click.

### 10.3 Pad typography and the § row hover (O4)
**Typography.** Prose is Literata on `#fdfdfc`, and math is KaTeX. The gutter is 46 px. Gutter marks (`§`, `◇`, `✎`) sit inside the frame with at least 6 px clearance from the edge: the fig marker must never touch the frame (O15).

**The § row hover.** Hovering a block or line with a `§` source mark darkens its background, as in the mockup. Its text fades over the same transition to the pad's white `#fdfdfc`, and fades back when the hover ends, so the text stays legible on the dark background (O4).

### 10.4 Block kinds and provenance
Every block carries its provenance, which is never laundered (a P3 invariant):

| Kind | Gutter | Body | Editable by the learner |
|---|---|---|---|
| `text` (the learner's) | none | Markdown + LaTeX | yes |
| `source_quote` | `§` | an italic quote, with a back-link button "§ <source> p.<page> ↩" / "▶ <video> <chapter> <time> ↩"; anchor-v1 to the span | no (the quote is the source's); the learner can add a note under it |
| `source_piece` | `§` amber edge | a larger excerpt of a source (a passage or a cue run), with a back-link | no |
| `tutor_quote` | `◇` | a quoted box: "◇ the tutor, on your question of <date>" | no |
| `figure` | `◇ fig` | a figure line or embedded figure with its label | no |
| `sketch` | `✎` | an SVG canvas (§10.8) | yes (drawing) |
| `cell` | `◆` | a marimo cell (§11.5) | yes (code) |
| `ink` | `✎` | ink strokes plus an editable transcription (§10.10) | yes (the transcription) |
| `lifted` | `→` | "→ lifted to **name** · its own pad in this stack" | no |
| `check_cell` | `◇` | a check the tutor proposed and the learner accepted (§8.4); answering it inline is a learner act | answer only |

A **submitted** block shows a green tag, "submitted · teach-back" or "submitted · attempt, <date>" (§10.9).

### 10.5 Writing and editing in place (O14)
**The running pad** is a dated lab notebook. It has day headings ("<DAY DATE>", "<DAY DATE> · TODAY") and a last line, "jot · it lands here by default", where clicking starts a new `text` block in edit mode.

**The editor:**
- Clicking any editable block opens it as source in place. The editor is `LiveMarkdownEditor`, Obsidian style: the source is revealed while editing, the rest stays rendered, and inline math previews as you type.
- The hint reads "markdown · $math$ · ↵ new line · esc puts it back".
- **Keys:**
  - `↵` keeps the line and opens a new block below;
  - `shift+↵` inserts a line break;
  - `↑` at the start or `↓` at the end moves to the neighbouring editable block;
  - `⌫` on an empty block removes it;
  - `esc` restores the block as it was;
  - blur keeps the edit.
- The editing style is a `#fff8ec` background with an amber-ink inset edge; other editable lines take a `#faf7f0` hover.
- Only the edited pad's body re-renders, so a running notebook frame elsewhere in the stack never reloads.
- Clicks don't open the editor in pen mode, in the overview, while text is selected, or on buttons, gutters, sketches, cells, frames or callouts.

**Storage.** Each edit writes a new block version (`supersedes_id` chain, append-only, as in `workbench_steps`). Removing a block writes a tombstone. Earlier versions stay readable in "history of this block", which matters when a submitted version is later edited (§10.9).

**New pads and sketches:**
- `alt+n` creates a pad: in a stack, "Scratchpad · <selection or 'new notes'>" becomes active; elsewhere a new stack window opens beside, titled from the selection (as a quote) or from the focus's main LO (as a heading).
- `alt+d` appends a sketch block to the active pad.

**Lift out.** Hovering a running-pad block reveals "lift out", which makes the block a new named pad in the same stack (a quote stays a quote) and leaves a `lifted` stub. On a laptop, a tap shows the button.

### 10.6 LearnLoop's gutter markers and hover cards (O15)
LearnLoop speaks in pads only through markers (owner decision 18).

**How a hover card behaves:**
- It opens 160 ms after the pointer settles on a mark.
- It is placed below the line, or above it when there is no room, aligned to the mark and inside the stage.
- It stays while the pointer is on it and hides 220 ms after the pointer leaves.
- A tap toggles it, and `esc` closes it.

**What each mark's card shows:**

| Mark | Card | Actions |
|---|---|---|
| `◇ fig` | "a figure LearnLoop made for this line · help, not a check", with the live figure at its saved parameters | "open it in the tutor"; "the passage it explains · <source> p.<page> ↩" |
| `§` | "<label> · the passage this quote came from", and up to 320 characters of the passage | "open it beside ↩" |
| `◇` tutor | the label and the tutor text | "open the thread" |
| `◇` proposal (a connection LearnLoop suggests for this line) | "◇ <reason>", the quote and the source | "open beside", "not this", "dismiss" |
| `◇` ink (§10.10) | the help ladder in place | the rungs |

**Proposals** ("<source> p.<page> takes this to the next step", "<video> ▶ <time> says this another way") come from the same machinery as promoted rows and passage links (§9.1): `search_spans`, correspondents and `passage_links`, ranked for this learner.

They are computed when a block is committed, not while typing, and only for blocks the learner has written. "Not this" and "dismiss" are logged as labels (dismiss means not now; not this means wrong), and so is ignoring a marker.

The density is the attention budget's: at most one proposal marker per block, and the learner can mute proposals per pad.

### 10.7 Two-way links between highlights and pads (owner decision 6)
**Making the link.** Appending a highlight or selection to a pad writes:
- the `source_quote` block with its anchor;
- a highlight annotation on the passage, if there isn't one;
- a `pad_block_anchors` row tying the two together.

**Following it.** The passage gets a small ✎ link: clicking it scrolls the pad to the block and flashes it for 1.8 s. The block's `§ p.N ↩` opens the passage beside and flashes it.

**Re-anchoring.** A link survives re-reads, through anchor-v1 and `span_aliases`. If the anchor needs re-anchoring, both ends show the ambiguity (a P3 invariant).

### 10.8 Sketch blocks (owner decision 10)
**The canvas** is an SVG on a 20 px grid, labelled "sketch · yours". LearnLoop never draws into a sketch.

**The toolbar:** `✎ pen · ／ line · → arrow · ▭ box · T text · ⌫ eraser`. Every tool works; the mockup wired only the pen.

**Behaviour:**
- Strokes are smoothed paths.
- Drawing within 16 px of the bottom grows the canvas by 60 px.
- Pen input (`pointerType: "pen"`) draws with pressure; the mouse draws too.

**Storage.** A sketch is stored as SVG paths plus typed shapes in the block payload.

**Not read for grading.** The emission covers text only (§10.11), so sketches are kept and searchable by their caption but not read for grading.

**The library choice.** A hand-rolled SVG canvas, not tldraw (decision D7, §20).

### 10.9 Submitting a block (an explicit act; owner decision 13)
**Invocation.** "Submit this block as…" (pad menu, `s`) offers the choices below. Only learner-authored blocks (`text`, `note`, `ink` transcriptions, a `check_cell` answer) can be submitted. A block that contains a source or tutor quote is refused with "this includes quoted text · submit only your own words". A block written after the learner took worked help (rung 4–5) on the same work is submitted labelled assisted, exactly as an attempt after worked help is today.
- **"my answer to <item>"**, when the pad is a problem pad (an RW2 workbench session; §15.2) or the block answers a check cell;
- **"a teach-back of <LO>"**, through the existing teach-back entry (`start_teach_back` / `submit_teach_back_turn`), with the LO picked from the block's anchors or typed.

**What it records.** Submitting freezes that block version as the attempt's or teach-back's text, tags the block "submitted · …" and links the version (`pad_block_submissions`).

**Editing after submission.** A later edit creates a new version. The submitted one stays as it was, and the tag reads "submitted (an earlier version)".

**What submission is not.** Submission is the only way pad text becomes evidence. It goes through the same paths as any attempt, teach-back or check, with the same grader blindness.

### 10.10 Pen and ink (owner decision 17)
**Turning pen mode on:**
- `alt+p`;
- the `✎` chip;
- or the first pen `pointerdown` (`pointerType === "pen"`), which also draws.

**Input rules:**
- Touch never draws.
- The pen's barrel button (button 2 or 5) erases: strokes it passes over are removed.
- The context menu stays on `.` and right-click.
- Ink is an SVG layer inside the window's scroller, so it scrolls with the text.

**On sources** the recognizer runs on pointerup. Each recognition shows a chip, "X → Y · undo · ✕", and undo removes both the mark and the ink.

| Stroke | Recognised as | Result (persisted) |
|---|---|---|
| closed loop (ends within 30 px; w > 30, h > 16) | selection | the words inside become the selection and the companion's context ("ask the tutor · c") |
| tall and narrow in the margin (h > 40, w < 26) | bracket | a highlight annotation on every paragraph spanned |
| other margin strokes | handwritten note | an `interpretation` annotation with the ink attached and an editable transcription ("transcribed · fix it") |
| flat through the middle of text (h < 22, w > 40) | strike | a `disposition` annotation, "I disagree / doesn't make sense", which the tutor can pick up |
| flat under a line | underline | a highlight annotation snapped to word boundaries |

The thresholds are recognizer geometry, from the mockup, tuned in RD8a's review on the owner's tablet.

**Freewrite pads** (`kind: ink`):
- Lined paper (52 px rules, or a dot grid).
- The bar reads "✎ by hand · dotted · hide/show transcription".
- Each ink line is an `ink` block holding its strokes and its transcription ("read as $LaTeX$", toggleable).

**Transcription.** `ink.transcribe` renders the strokes to an image and sends it through the plan transport's vision-capable route; OpenRouter is used only after the learner's one-time OK. It returns Markdown with LaTeX. The learner edits the transcription freely, and each edit is a new version labelled "you corrected the transcription".

The Pocket Notes OCR pipeline is a candidate route if it beats the plan route on the owner's handwriting (decision D8).

**The tutor reads ink unobtrusively (review F12).** The ladder needs a target. Today's hint service is item-bound (`HintRequestV1` requires `practice_item_id`, `session_id` and `submission_id`; `hints/service.py:136`), so RD8 ships it in two steps.

**RD8a: ink attached to a problem.** For an ink block in a problem pad (an RW2 workbench session with its practice item), the ladder is exactly the practice screen's:
- `request_hint` with that item and session, and `surface: "workbench_ink"`;
- the transcription is the work text, labelled as a transcription;
- assists recorded in `help_assists`;
- the chooser's first offer sampled with its propensity logged.

The `◇` marker sits beside the first step the hint service's feedback says doesn't hold, labelled "transcription may be wrong · fix it".

**RD8b: freewriting with no item.** The hint service gains a **freeform assistance context**, designed with the adaptive-hints spec's owners as a hint-service extension, not a Reader-side writer (contract `pyproject.toml:895`). The context carries:
- the target (what the learner is deriving, from the pad's anchors, LO tags and title, or typed by the learner when unclear);
- the transcription and its uncertainty;
- a judged line check ("the first line that doesn't hold", a judged route labelled "may be wrong");
- chooser accounting with propensities;
- exposure attribution.

It is help, never evidence. No practice item, session or attempt is manufactured. Until RD8b lands, a freewrite line's menu offers "ask about this line" (the companion, with the line as context) instead of the ladder.

**What the ladder shows** in both steps, in place:
- the heading "◇ LearnLoop read your handwriting (transcription may be wrong · fix it)";
- "line 3 read as: <editable transcription>";
- the rungs:
  1. a question about your approach;
  2. point to the first step that doesn't hold yet;
  3. a hint on your step;
  4. work a piece of it for me, in my notation (worked help ◌);
  5. walk me through the rest, keeping my route (worked help ◌).

LearnLoop's suggested rung is marked ▸. **Choosing and taking are separate:** `1–5` or `↑↓` choose, and `↵` or a second click takes. A taken rung shows its text and "help recorded · rung N · as on the practice screen", and the line gets an amber "pointed" highlight.

**Ink is an emission.** It is searchable through its transcription and veiled during cold checks like typed text.

### 10.11 Pads are emissions (owner decision 13; the contract per review F4)
**The ⓘ popover.** Each pad window's header has an ⓘ that opens:

> **where your words go.** LearnLoop reads your scratchpads to understand what you're working on and where you're stuck. Nothing here is graded. Only blocks you submit (marked submitted) count as an attempt or a teach-back. Sketches are kept, not read for grading.

**What is emitted.** Only learner-authored text:
- blocks of kind `text` and `note` with provenance `learner`;
- `ink` blocks' transcriptions with provenance `ink_transcription` or `learner_correction`, marked as transcribed, so a model knows the words may be misread.

Never emitted: `source_quote`, `source_piece`, `tutor_quote`, `figure`, `lifted` stubs, `check_cell` prompts, sketches and cells. A learner's text block that merely pastes a source or tutor text is detected by overlap with the pad's own quote blocks and with the cited spans, and it is emitted as "quoted by the learner", not as the learner's belief.

**When it is emitted.** A block version is emitted once, when committed (Enter, blur, or leaving the pad), as an immutable snapshot: `source_id` is the block's `version_id`. Batches run the existing learner-text-gaps pipeline with `source_kind='pad_text'` when the learner leaves the pad, closes the desk or goes idle.

**Corrections.** A later edit emits the new version. The pipeline's existing supersession treats it as the learner's current text, and gaps read from the older version are marked superseded, not deleted. A struck-through or removed block (a tombstone) retracts its gaps from routing. They stay in history.

**Effects (registered in `diagnosis/text_gaps/contract.py`).** `pad_text` joins `READABLE_SOURCE_KINDS` **and** `NON_SERVING_SOURCE_KINDS`, like `workbench_text`. Its gaps can:
- name a prerequisite or a belief, and become hypotheses;
- inform the companion, the Teacher and the router's learner state;
- create a topic or misconception candidate, through the pipeline's existing holding pen and caps.

They never bring a check forward, are never a weak prerequisite observation for placement, and never feed mastery, readiness or certification. Any serving effect beyond this is a future algorithm successor of its own.

**During an open check.** A cold check's open administration excludes the protected blocks from every model context (§12.6). A block written during the administration is emitted only after it closes.

**Migration.** `learner_text_gaps` and `learner_text_gap_jobs` are rebuilt from the current head (248's vocabulary, every constraint and trigger preserved), adding `pad_text` (§15.2).

**What may read pads.** The companion and the Teacher read pad text as context whenever it helps (§1.1). The grader never does.

### 10.12 Carried questions and the desk drain
**Carrying.**
- The verb Carry, or a "? carry" chip on a `text` block that ends in "?", makes a carried question (`carried_questions`: text, origin anchor, since).
- Carried questions show under CARRIED on the shelf, with "since <date>".
- A carried question comes back **beside a related passage, never as a nudge**: when a window shows a passage the union read ties to it, a quiet `◌` margin mark appears ("you carried: <the question> · since <date>").

**Answering one.** Its menu offers "fruitful / not now / let it go", three different labels, logged.

**Effect on the router.** Carrying informs the router and the Teacher as a learner pick (`router_learner_preferences`, `propensity_kind='none'`). This follows the brainstorm's §10.6 item 8 (decision D9 for the default).

**Display limit.** The shelf shows at most three carried questions, an attention limit, labelled; the rest are in the library.

**The desk drain** (`alt+shift+q`, or closing a desk):
- The panel is headed "Closing “<desk>”" and lists today's pads. Each row shows ⚲, the title, its meta, and its first and last lines.
- Buttons: "Nk keep", "Nl leave", and "Nc carry “<last line>”" when the last line is a question.
- The subheading reads "one key each · skipping costs nothing · leave keeps them in the desk's history".
- Keep pins the pad, leave keeps it in the library unpinned, and carry adds a carried question.
- The drain gives before it asks: it shows what the pads hold before asking anything (design review).

---

## 11. The Teacher lesson window and notebooks (O9)

### 11.1 Lessons as windows (RD9a; needs no NA)
**The window.** A Teacher lesson opens as a window (`kind: lesson`). By default it is a pad in the desk's stack with the tab label "Teacher lesson · <topic>" and meta "made <date> from your <question/attempt>". The learner can also give it its own slot.

**What it renders.** The window renders `LessonScreen`'s content, extracted into `LessonView` and used by both, through `lesson.turn` / `lesson.view`.

**Entry points:** the Teach me verb, the companion's "learn it with the tutor", and the router's suggestions. They all keep working; they open the lesson in a window on the current desk instead of switching screens.

**Mode buttons above the lesson** ("yours to keep, like your other pads"). They are staged honestly (review F13): the lesson RPC today supports open, reply, answer, stop and resume (`H:lesson.py:82`), not redo or scoped amendment.
- **review** (RD9a): "your committed answers and the reveals, as you left them". A read-only replay of `lesson_turns` and `lesson_turn_payloads` as recorded, with nothing regenerated.
- **your additions** (RD9a): the learner's own blocks in the lesson's `lesson_additions` pad, shown under the lesson, with every pad insert available. This is the part of "augment" that needs no teacher change.
- **redo** (RD9c): "fresh numbers; your earlier answers stay hidden until you commit again". It needs a teacher-side design, owned by teacher v2 and specified there before building:
  - a new lesson episode on the same plan;
  - which material is regenerated and from what;
  - prior answers treated as exposure;
  - the original episode replayable unchanged.
- **ask the teacher to extend** (RD9c): a scoped amendment protocol. The learner selects a part, the teacher proposes a change, it shows as a highlighted diff, and the learner accepts or rejects it, with each amendment versioned. It uses NA's diff and commit machinery where the lesson is a notebook, and teacher v2's turn schema otherwise.

Until RD9c, redo and extend are not shown. There are no label-only buttons, unlike the mockup.

### 11.2 The notebook lesson (RD9b; after NA's native runtime)
When a lesson's medium is a marimo notebook (teacher v2 §10, NA4's teacher half), the lesson window hosts the notebook in a frame served by NA's native sandboxed marimo server (NA §5.1), never a public URL.

**The look** is the workbench's, not dark mode (O9):
- the page is paper `#f7f5f0` and the surface `#fdfdfc`;
- the purple voice is `#5b4a9a`;
- body text is **Literata**, like the books and pads;
- otherwise marimo's default text styling;
- the theme sets CSS variables only (NA §16 Q13).

This replaces NA §5.2b's LearnLoop marimo theme (owner decision 9). The reference is `~/learnloop-vault-notebooks/learnloop_paper.css` and the exported `08_softmax_cross_entropy` notebook.

**Even margins.** The notebook's left and right margins are equal inside the window (O9). The mockup's padding was `10px 12px 12px 12px` on the lesson body.

**Commit points are styled** as part of the lesson:
- a commit card in the paper style, with the purple voice edge;
- a held state while the answer is committed and the reveal is pending;
- a verdict line after.

They are built from NA's commit-gate widget.

**Not served.** If the server is not running, the window says so in one line with a retry. It retries three times, 1.5 s apart, and a later load always hides the message.

### 11.3 The notebook bridge (tutor `c` and the right-click inside a notebook)
A notebook in a frame is a separate document, so keys and menus don't reach the workbench. NA's runtime injects a small bridge script into served notebooks. It is a port of `~/learnloop-vault-notebooks/site/ll-bridge.js`.

**When it runs.** Only when framed, and it posts only to the workbench's origin.

**Messages it posts:**
- `{ll: "companion", text, rect, shift}` on `c` (or `alt+c` while typing). The workbench opens the companion at the selection, translating the rect by the frame's position, with the text as context (`from: "lesson"`); `shift` docks instead. `c` with no text while anchored dissolves the companion.
- `{ll: "menu", text, rect, x, y}` on right-click. Shift+right-click keeps the browser's own menu. The workbench opens the **pad menu** labelled "the lesson", with the insert label "add under this lesson (the notebook stays as the teacher made it)". Inserts go to the lesson's additions pad.
- `{ll: "click"}` on mousedown, which closes the workbench's menus.
- `{ll: "escape"}`, which dissolves an anchored companion.

**Trust.** The workbench accepts messages only from the notebook server's origin and from a frame it created. Messages carry no commands beyond these four.

### 11.4 Teacher notebooks in the overview
Overview miniatures replace notebook frames with a placeholder card ("◆ notebook · <title>").

### 11.5 marimo cells in pads (RD9b)
**The cell.** A `cell` block holds marimo code in a pad. It runs in a lazily started kernel owned by NA's native runtime. The runtime identity belongs to the **pad**, not the desk or the window (review F11), so moving a pad between desks or windows keeps its kernel and state. The kernel starts on the first ⇧↵ (owner decision 9). Its header reads "marimo · reactive · runs when you press ⇧↵".

**States:**
- "kernel not started";
- "starting kernel…";
- "ran in N ms", with the output under the code.

`⇧↵` runs the focused cell. Cells in one pad share a reactive graph (marimo semantics).

**Rendering.** Display-only outputs (plots, widgets from the notebook toolbox) render in place, in the pad's theme.

**Before RD9b** the insert row is disabled with its reason (§9.2). No fake run is ever shown.

---

## 12. The goal lens (O16; the goal-conditioned fork)

### 12.1 Which goal
**Choosing it.** A desk may be bound to a goal (`desks.goal_id`). The default is the learner's primary active goal (`goals_list`, by priority). The band's goal label switches the desk's goal, from a list of active goals plus "no goal" (the lens off).

**The data behind it** is the real model:
- `Goal.intent_sentence`, `due_at` and `exam`;
- the scope and resolution (`curriculum.scope`);
- the path (`curriculum.path`, with `deliverable_path_sections`);
- coverage (`section_coverage`);
- readiness (`curriculum.ready`, `lo_certification`).

**Kind** (quest, exam or project) is displayed, never stored. It is derived as deliverable curriculum §5.1 says, and "project" stays display-only until projects become a goal subset (decision D4).

### 12.2 The goal band
The band is 50 px high, under the top bar, in five parts.

1. **The goal:**
   - "◎ YOUR GOAL · <KIND> · <deadline or NO DEADLINE> (your words, <date set>)";
   - the sentence in quotes, in Literata 13.5 px.
2. **Its learning objects:**
   - "N LEARNING OBJECTS · a LIKELY · b UNTESTED · readiness from cold checks", counting the LOs within the chosen depth;
   - one dot per LO in path order:
     - filled: demonstrated (from `lo_certification`);
     - half: likely (AD's labelled prediction);
     - hollow: untested;
     - smaller dots for prerequisites; dimmed dots for LOs beyond the depth;
   - a rotated ◇ square after an LO with a due cold check, filled once answered;
   - a dashed dot at the end for each **unmatched phrase** in the goal sentence (opens the path);
   - a ring marks the LO being read;
   - clicking a dot opens its primary section, and clicking a ◇ goes to its check;
   - the three depth buttons, get the idea / learn to use it / fluency, set the deliverable's one depth (`curriculum.set_depth`).
3. **You are reading:** the focused window's position mapped through the lens, updated as it scrolls, for example "<source> p.<page> · **<LO title>** · prerequisite", "· not needed for your goal", "Teacher lesson <n>" or "your scratchpads".
4. **Next for the goal:**
   - "◇ <n> cold checks due today" (goes to the first);
   - or the next unread primary section;
   - or "nothing due · the path is read".
5. **Tools:**
   - "dimmed / shown" toggles dimming of skippable text, with a mini legend of the three marks;
   - "path p".

**Laptop width.** Below 1400 px "you are reading" and the provenance fold away.

**Data.** `goal.band {goal_id}` composes `curriculum.ready` (lines, states, checks), the path order, `checks.due_for` and pace (`goals/goal_pace.py`; the rate is real, not the mockup's figure).

### 12.3 Criticality marks (O16: "how critical this span is")
**The mark** is a 3 px bar 11 px left of the text, so the ◇ › ? glyphs at −30 px keep their place:

| Level | Mark | Meaning |
|---|---|---|
| core | solid `#5b4a9a` | a goal LO's primary passage, introduced or developed here |
| supporting | the same at 34 % | a prerequisite, another way to the same LO, or an example |
| skippable | a dotted 1 px `#b9b2cc` line | not about any LO in this goal's scope |
| later | dotted | needed only at a deeper depth than the one chosen |
| already shown | dotted | its LO is demonstrated |
| unmapped / partial | no bar / a short grey tick | coverage hasn't been judged for this goal here, or covers only some of its LOs; never treated as "not needed" |

**Where the marks go:**
- book passages and exercise rows;
- transcript paragraphs (the bar sits inside the text column);
- paper passages;
- shelf rows (at the right edge), with a line "◎ primary for <n> of your LOs · p.<start>–<end>".

The path ranges also show on shelf minimaps and as segments on video scrub tracks.

**Dimming** (on by default; decision D5): skippable and later text turns `#8e897f`, and its KaTeX dims. Lit and followed passages and the learner's blue highlights keep full colour. **Dimmed text is never hidden.**

**Why.** Hovering (120 ms) or tapping a bar opens a card:
- the level, for example "later · kept at learn to use it";
- "**For <goal short>:** <why>.";
- a learner line, for example "You chose “…”" or "You answered its cold check on your own today.";
- the coverage line, for example "coverage: introduces “<LO title>” · a goal LO · its primary section · core".

`esc` hides it.

**How a level is computed** (`goal.lens`; deterministic, no model per passage; review F6).

1. **Mapping state first.** A section with no `section_coverage` rows for this source is **unmapped**. It gets no bar, and its why card says "not mapped for this goal yet". A section whose coverage judge ran but whose rows cover only some of the goal's LOs that the path places here is **partial**. **Missing mapping never becomes "not needed".**
2. **Per-LO level** for each of the goal's LOs (within the chosen depth plus prerequisites) that the section covers:
   - **already shown**: `lo_certification` says demonstrated;
   - **later**: the LO's path depth is deeper than the chosen depth;
   - **core**: the section is that LO's path `core` (or primary) section and its treatment is `introduces` or `develops`;
   - **supporting**: the section is a `prerequisite` or `alternate` path section for it, or its treatment is `applies` or `mentions`;
   - an `assumed` path label counts as already shown for display.
3. **Aggregation across LOs** (one section often covers several). The section's level is the **highest-need** level among its LOs, in the order core > supporting > later > already shown. A section is **skippable** only when it is mapped, none of its covered LOs is in the goal's scope, and the coverage judge marked it `not_about` or covering only out-of-scope LOs. One demonstrated LO never dims a section that still serves another needed LO.
4. **Passages inherit their section's level** in this spec (decision D1). The why card says "judged per section" when the passage's own role could differ. RW4e's role vocabulary (`reader/source_roles.py:64`: definition, theorem, explanation, intuition, worked example, exercise, figure, counterexample, contrast, prerequisite, alternative treatment, application) has no aside or digression role, so the mockup's finer "this aside is skippable inside a core section" is **not built here**.
   - **A later refinement (deferred, §17):** add an `aside` role to the RW4e vocabulary and to the coverage judge's role output. That is a schema and prompt change with identity-pin consequences, so it needs its own landing note. Its judgments would show as proposals ("LearnLoop thinks this is an aside").
5. **Videos** use their transcript sections (the `t=` units) the same way. Accepted chapters (§7.9) refine them.
6. **The reason text** is `deliverable_path_sections.reason` (the column exists, migration 228). Sections off the path get a reason assembled from the labels, with no LLM per passage.

**Caching.** Levels are cached per (goal, extraction, contract head) and invalidated when the path, coverage, depth or certification changes.

**Not evidence.** Criticality marks never feed evidence or scheduling: the lens is display only.

### 12.4 Callouts and heads
Short dark callouts at section starts (HMWL), in LearnLoop's voice:
- "◎ for your goal · core: <what this section does>… primary on your path for “<LO title>”";
- "◎ for your goal · prerequisite … <video> ▶ <time> tells it another way. The background just above is skippable.";
- "◎ for your goal · core … Its cold check is due today, here, before the page gives it away.".

Callouts also appear on paper section heads, on video transcripts ("◎ on your path · <start>–<end> · another way for “<LO title>”: <source> p.<page> is the primary"; unused videos get a dimmed "not needed for your goal · <reason>. Read it anyway…"), on pads ("◎ for your goal · <purpose>", from the pad's anchors) and in the companion ("◎ goal in context").

**Source of the text.** The callout text comes from the path's per-section reasons (`curriculum.path`) and is cached; there is no new route.

**"Picked for your goal."** Exercise picks come from RW4b's ranking under the goal's LOs, each with its "why this one" reason.

**"◇ LearnLoop asks · grounded in your goal"** (HMWL's inserted question). Where a reader-authored or quick-check question exists for a passage on the path, it sits inline before the passage with a reply box. It is answered through the existing `reader.present_question` / `reader.submit_question`, which is instructional and never certification. Questions whose LO is in the goal's scope come first.

### 12.5 The path view (`p`)
**Entering.** `p`, the band's "path", or the dashed dot opens the path as an overlay window.

**Left column** (330 px):
- the goal and its sentence;
- "resolved to **N learning objects**, plus M prerequisites you haven't shown yet · change: type what's missing or not needed" (`curriculum.scope_decide`);
- each unmatched phrase, "“<unmatched goal phrase>” → <proposed LO> [add it]" (`goals/goal_lo.py:create_goal_lo`);
- "how deep for this?", the three depths with their meanings (get the idea: definitions, examples, visualizations; learn to use it: explanations, worked examples, practice; fluency: novel problems, changed assumptions, delayed checks), each with the size of its path (pages, minutes of video). This shows HMWL's three tracks as the depths of one goal (decision D3);
- "am I ready?": "Only delayed cold checks answer that. Reading raises LearnLoop's prediction, never a certification.", plus the real pace line from `GoalPace` (or "no deadline, so no pace target");
- the margin legend.

**Right column:** "your path · prerequisites before what assumes them · <depth>". One row per LO:
- the readiness dot, its ordinal, the title, a tag (core, prerequisite or later), "you are reading here", and the readiness ("likely · LearnLoop's prediction from N attempts");
- the **primary** section (the glyph, source, location, treatment and why, read status);
- **another way** alternates, each with "use this one instead" (`curriculum.path_override`, `use_instead`; stored, not just opened);
- the **cold check** row, due or answered;
- the **exercise worth trying**;
- the **Teacher lesson** if one exists (opens its window).

At the end comes "┊ not needed for your goal · read it anyway", the dimmed list; "read it anyway" stores `read_anyway`.

**Clicks** open beside on the goal's desk (switching desk if needed). A depth change re-renders the lens everywhere and keeps the path open.

### 12.6 Inline cold checks and veils (the masked textbook and scratchpad; owner decision 14; reworked per review F1, F2)
**Where checks come from.** A due delayed check is a `commitments` row (`test_me_later`), whatever created it:
- "Am I ready?" (`curriculum.ready_check`);
- "check me later";
- RW6b's cold follow-ups;
- TE6's generated delayed checks once built.

#### 12.6.1 What is shown before the check opens (no cues)
The host passage is the LO's primary path section. When a window approaches it, a **closed** marker sits before the passage:
- "◇ a check is due before this page · on your own · about N min";
- "check now" and "later".

The closed marker shows **no question, no LO title, no provenance and no purpose text**. Check once hides locators until feedback (`intent/checks.py:155`), and P3 invariant 10 withholds source text, purpose and "why" from cold administration.

**What else changes while any check is due for an LO:**
- The goal band shows only "◇ N checks due today", with no LO names on the ◇ squares, which take no hover.
- Callouts, criticality "why" cards and path rows for that LO hide their purpose text.
- Overview thumbnails and miniatures of windows holding that LO's protected content are not rendered (a placeholder card).

#### 12.6.2 Opening: protection before the prompt
"check now" calls `check.begin_inline`, which atomically:
1. picks the item through the existing eligibility in `scheduling/intent/serving.py`, honouring held candidates;
2. freezes the assessment contract (`contract_hash`);
3. opens an administration (token, surface `reader_inline`);
4. computes the **protection set** over everything visible: spans in every open window on every desk, pad blocks, ink, thread and history items on screen, the companion, overview previews, search results;
5. checks the learner's **prior exposure**: if the learner opened answer-bearing material for this LO since the check was scheduled, the existing exposure records decide cold eligibility, exactly as Check once decides it.

The veils are applied, and only then is the prompt returned and shown.

#### 12.6.3 The protection set
**Structural protection** (always):
- the LO's covered spans in every source;
- pad blocks and ink anchored to those spans or tagged with the LO;
- exchanges citing them;
- the open companion thread;
- figures for those spans.

**Unanchored learner content cannot be placed by structure.** That is pad blocks with no anchors, and threads with no citations. While a check is open, **every pad and thread window on screen is veiled whole** unless the Decider judgment (below) clears it.

**Decider judgment** (once reveal adjudication ships): the shared reveal judgment narrows the whole-window veils to the blocks that actually state the answer, and adds any answer-bearing passage that structure missed, with the quote.

**Cold credit is not granted by veiling.** Masking is a courtesy that keeps the page usable. Cold eligibility is decided by the exposure record. If the protection is uncertain (the Decider judgment is unavailable and something unanchored was visible before the veil applied), the answer is accepted, graded and labelled "answered with your pads open · counts as practice". The cold duty stays pending, and Today serves it again.

**What a veil looks like:**
- text turns transparent behind an 11 px blur;
- images blur 6 px;
- a centred pill reads "hidden during this check · back when you answer";
- veiled things are not interactive;
- **nothing moves**: layout is untouched;
- veiled material is excluded from every model context (the companion's included).

#### 12.6.4 During the administration
**New content.** Navigating, opening a window, switching desks or searching calls `check.protect_more` before the new content renders. New content is veiled on arrival if it is protected.

**Exposure.** Opening a veil ("show it anyway" on the pill) or taking help calls `check.expose` at once, persisted through the canonical exposure machinery (`source_exposure_events` and the administration's exposure state), not held for submission. From then on the answer is assisted, and the card says so: "you looked at <group> first · this answer counts as practice".

**The card:**
- the question;
- the answer box (MathLiveEditor);
- "veiled while you answer · <groups>";
- "nothing moves · only an on-your-own answer settles this check";
- "answer ↵" and "not now".

Only one administration is open at a time. Without a host in view, the same card opens centred near the top.

#### 12.6.5 Submitting and settling
**Submitting.** `check.submit_inline {administration_token, submission_id, answer_md}` records an attempt for the frozen item through the existing attempt service, with the administration's exposure state. It is idempotent by `submission_id`, and a duplicate returns the first result.

**Settling.** It then runs as for any qualifying attempt: `intent/checks.py:settle_answered_checks` recognizes it and changes the commitment's disposition. This path never grades by itself.

**Competing surfaces.** Today and the Reader share the administration lock: a commitment with an open administration on one surface shows "being answered in the Reader" on the other. The first *settling* submission wins. A later one on the other surface is recorded as practice.

**"Not now"** (`check.abandon_inline`) closes the administration with no attempt. The duty stays pending, and anything the learner saw is in the exposure record.

**Crash or restart.** An open administration persists. On restart the card reopens with its veils, or the learner abandons it.

#### 12.6.6 After answering
- The veils lift (unveil .6 s).
- The card shows:
  - "› your answer · just now · on your own" (or "· counts as practice");
  - the feedback (the existing grading path for the check's item);
  - "N things were veiled… · back now";
  - the readiness line, "readiness · <LO>: <new state>".
- The new state is whatever `lo_certification` now says. One answer does **not** flip an LO to demonstrated unless the model's capability-matched credit says so (the mockup simplified this).
- The band, path and marks re-render, and purpose text returns.
- `check_veil_sets` keeps what was veiled and opened, for audit.

**Evidence.** Inline administration is a new serving surface (`reader_inline`) for existing check items, with the same item selection, contract, grader, exposure rules and settlement as Check once. Reading the host passage after answering is ordinary reading.

**Decision D2 holds:** checks stay in Today too. The Reader adds a place, not a rule.

### 12.7 Goal-tied checks in the tour of the fork
Two checks are the acceptance scenarios for §12.6 on a synthetic fixture (§18.3): check A protects a book passage; check B protects a paper's equation and also veils pads on another desk and matching video cues.

### 12.8 Empty and thin states (§2.3)
| Condition | Shown |
|---|---|
| No goal | No band. A quiet "◎ set a goal" in the top bar; the lens is off |
| A goal without a resolved deliverable | The band shows the sentence and "LearnLoop hasn't mapped this goal to your sources yet · map it", which runs `curriculum.set_scope`/`path` as a job |
| No coverage for a source | Marks are absent on that source. Its shelf row says "not mapped for this goal yet" |
| No checks | No ◇ squares; "Next for the goal" falls back to the next primary section |

---

## 13. Cross-cutting

### 13.1 Show me figures on the workbench
**Entry points:**
- the quiet margin marker "◇ a figure for this passage";
- the figure chip after a passage ("Figure <n> · live version · drag the parameter · opens in the tutor");
- the Show me verb;
- the pad menu;
- a `◇ fig` gutter card.

All of them go through `figure.request` / `figure.open`.

**In the companion** the figure appears as "◇ Show me · a figure for <source> p.<page>", with the live widget and three buttons:
- **view source** opens a figure-notebook window (the figure's source as a marimo notebook, display tier, not run until RD9b);
- **move to scratchpad** writes a `figure` block;
- **not useful** removes it and is logged.

The footer reads "◇ LearnLoop's figure, made ahead from this passage · display tier, no kernel · it is help, not a check".

**Shared parameters.** Every instance of one figure shares its parameters, so dragging the temperature in one updates the others.

### 13.2 Accessibility and calm
- **Keyboard:** every action has a key, and every key has a visible hint (the footer, which-key, menus).
- **Screen readers:**
  - windows are `region`s labelled with their title and position ("window <position> of <total>, desk <title>");
  - the strip is a `list`;
  - menus are `menu`s;
  - the companion is a `dialog` when anchored and a `complementary` region when docked;
  - veils set `aria-hidden` and announce "N things hidden during this check".
- **Reduced motion:** every transition becomes an opacity crossfade (§4.3).
- **Contrast:** dimmed text (`#8e897f` on `#f7f5f0`) must meet WCAG AA for body text. If it does not, it is darkened until it does.
- **Laptop:**
  - below 1400 px the shelf becomes a rail, the companion narrows (at most 330 px wide and 50 % high), and the band folds;
  - below 820 px of height the top bar is 34 px;
  - hover-only affordances respond to a tap.

### 13.3 Phone and MCP
**Phone:** none of the new methods are on the phone allowlist, and the phone keeps its reader. The companion pattern on the phone, and desks on the phone, are deferred (§17).

**MCP v2** may later read `companion.history` and pads through the registry (§17).

### 13.4 LaTeX sizing (O13; owner rule)
**The failure.** Display math must never be clipped. The mockup's bug: KaTeX's `.katex-display` has `overflow-x: auto`, which forces vertical clipping, and a cell's fixed height cut the top and bottom of tall equations.

**The rules for the build:**
1. **Room inside display math.** Display math gets vertical padding inside its own box (`.45em` top, `.55em` bottom in the mockup). No element between the math and its window's own scroller may clip it vertically: no fixed heights, and no `overflow: hidden|auto` on cells, blocks, cards, callouts or companion items. The window's scroller and the viewport may of course clip what is scrolled out of view; that is not a clipping bug (review F17).
2. **Horizontal overflow is fitted, not scrolled:**
   - an equation wider than its column is scaled down to fit, to a minimum of 0.75, measured after fonts load and re-measured on resize;
   - below that minimum it gets a horizontal scroller whose scrollbar is visible and which keeps the full height.
3. **Heights are content-sized.** Every pad cell, block, card or callout that holds math is sized by its content, never a fixed height. Auto-sizing re-measures after KaTeX renders and after web fonts load (`document.fonts.ready`).
4. **Macros.** A source's macros (`reader/source_macros.py`) apply in every window and pad block quoting that source.
5. **The fixture test.** A fixture of tall and wide equations (fractions of sums, aligned derivations, matrices, `\left( \right)` with tall content) is rendered in every container kind in the **real webview** (jsdom cannot lay out). The test compares each equation's rendered ink bounds (the union of its glyph boxes from `getClientRects` of KaTeX's `.vlist` and `.mord` spans) with the visible rect of its nearest clipping ancestor below the window scroller. Every ink box must lie inside, with at least 3 px of room above and 5 px below. Wide equations must be fitted (scale at least 0.75) or sit in a visible horizontal scroller that keeps the full height.

---

## 14. Evidence and honesty: what each thing is

| Thing | What it is | May feed | Never feeds |
|---|---|---|---|
| Reading, scrolling, dwell, desk layout, overview use | interaction telemetry (`interaction_events`) | AD's discrete reading events as today; display | mastery, readiness, certification, scheduling (salience firewall) |
| Highlights, margin notes, pen marks | annotations (the learner's) | display, search, union read; notes contract unchanged (C5 opt-in only) | evidence, sources, generation input |
| Pad text and ink transcriptions | **emission** (learner text) | `learner_text_gaps` (`pad_text`), hypotheses and routing (tier 2), companion and Teacher context | grader, certification |
| A submitted pad block | an attempt or teach-back | everything an attempt or teach-back feeds, through existing paths | |
| Companion exchanges | `question_events` (as today) | the existing tutor-question uses; history | |
| Hints and help-ladder rungs | assists (`help_assists`) | the hint chooser, AD as today ("help, never evidence") | certification |
| Figures, lessons' display widgets | help | display | certification (contracts at `pyproject.toml:859`, `:871`) |
| Inline cold check answers | check administrations (`surface: reader_inline`) | readiness and certification **exactly as** Check once in Today | — |
| Opening a veil before answering | exposure; the answer becomes assisted | the honest label | a cold credit |
| Criticality marks, goal band, path | display of the real model | display | anything |
| Carried questions | learner picks (`propensity_kind='none'`) | router and Teacher offers | evidence |
| Proposals dismissed, ignored or accepted | labels | ranking and offline evaluation | evidence |

---

## 15. Data model and migrations

### 15.1 New tables
Use the next free migration numbers at build time (`ls migrations/`). Classify every table in `db/table_roles.py`; every DERIVED table gets one replayer in `substrate/rebuild_orchestrator.py`. Upgrade `fixtures/migration_head/` as CLAUDE.md describes, and regenerate the vault's database reference.

| Table | Role | Columns (essential) | Stage |
|---|---|---|---|
| `desks` | WORKFLOW | `desk_id`, `title`, `position`, `focus_window_id`, `goal_id?`, `companion_dock`, `companion_shown`, `created_at`, `archived_at?` | RD0 |
| `desk_windows` | WORKFLOW | `window_id`, `desk_id`, `slot`, `pane` (0/1 in a pair), `kind`, `spec_json`, `view_json` (scroll anchor by span or t, document zoom, stack mode and ratios, active pad), `opened_at`, `closed_at?` (soft close, for undo and history) | RD0 |
| `desk_op_receipts` | RECEIPT | `client_id`, `seq` (the batch, §3.4), `request_hash`, `result_json` (the stored reply), `applied_at` | RD0 |
| `pads` | WORKFLOW | `pad_id`, `kind` (`running`, `named`, `problem`, `ink`, `lesson_additions`), `title`, `kept`, `home_desk_id?`, `workbench_session_id?`, `lesson_id?`, `created_at`, `archived_at?` | RD0 |
| `pad_block_versions` | RAW_LEDGER (append-only by trigger) | `version_id`, `block_id`, `supersedes_id?`, `pad_id`, `position_key` (a fractional index), `day` (running pads), `kind`, `body_md`, `payload_json` (sketch shapes, cell code, quote anchor, open spec, figure ref), `provenance` (`learner`, `source`, `tutor`, `learnloop`, `ink_transcription`, `learner_correction`), `tombstone`, `created_at` | RD0 |
| `pad_block_anchors` | RAW_LEDGER | `event_id`, `block_id`, `extraction_id`, `span_id`, `anchor_json` (anchor-v1), `annotation_id?`, `action` (`link`, `unlink`), `created_at` | RD0 |
| `pad_block_submissions` | RAW_LEDGER | `block_id`, `version_id`, `as`, `attempt_id?`, `teach_back_id?`, `created_at` | RD4 |
| `pad_op_receipts` | RECEIPT | `client_id`, `seq`, `pad_id`, `request_hash`, `result_json`, `applied_at` | RD0 |
| `ink_strokes` | RAW_LEDGER | `ink_id`, `owner_kind` (`block`, `annotation`), `owner_id`, `strokes_blob` (compressed points with pressure and tilt), `pointer_meta`, `created_at` | RD8a |
| `companion_exchange_context` | RAW_LEDGER | `question_event_id`, `desk_id?`, `surface`, `window_spec_json?`, `pad_block_ids_json?`, `goal_id?`, `origin` (`live`, `backfill`) | RD0 |
| `question_event_spans` | DERIVED | `question_event_id`, `extraction_id`, `span_id`, `role` (`selection`, `cited`) | RD0 (replayer from `interaction_events` reader payloads) |
| `learner_text_gap_spans` | DERIVED | `gap_id`, `extraction_id`, `span_id`, `role` | RD0 (replayer from gap anchors and `entity_source_links`) |
| `carried_questions` | WORKFLOW | `carried_id`, `text`, `origin_kind`, `origin_ref`, `anchor_json?`, `since`, `state` (`carried`, `fruitful`, `not_now`, `let_go`) | RD4 |
| `carried_question_events` | RAW_LEDGER | `carried_id`, `event` (`carried`, `surfaced`, `fruitful`, `not_now`, `let_go`, `ignored`), `ref?`, `at` | RD4 |
| `pad_proposals` | RECEIPT | `proposal_id`, `block_version_id`, `target_spec`, `reason_md`, `quote`, `judgment_ref?`, `created_at` | RD4 |
| `proposal_labels` | RAW_LEDGER | `proposal_id` (pad proposal or promoted row), `label` (`opened`, `not_this`, `dismiss`, `ignored`), `at` | RD4 |
| `check_veil_sets` | RECEIPT | `administration_ref`, `commitment_id`, `method`, `veiled_json` (refs and groups), `opened_json` (veils the learner opened), `created_at` | RD7 |
| `video_chapters` | WORKFLOW | `chapter_id`, `extraction_id`, `t0`, `t1`, `title`, `lo_ids_json`, `state` (`suggested`, `accepted`, `dismissed`), `judgment_ref?` | RD10 |

### 15.2 Changes to existing tables and contracts
Every rebuild starts from the **actual migration head at build time** and preserves every existing value, constraint, index and trigger. Each migration follows CLAUDE.md's fixture procedure for `fixtures/migration_head/`.

- **`learner_text_gaps.source_kind` and `learner_text_gap_jobs.source_kind`** (both rebuilt at 248, with `lesson` and `external_chat`) gain `pad_text`, in both tables. `source_id` points to the pad block version. `pad_text` is registered in `READABLE_SOURCE_KINDS` and `NON_SERVING_SOURCE_KINDS` (§10.11). **RD4.**
- **Check administrations** gain the surface `reader_inline`, plus an administration lock shared with Today's Check once (§12.6.5), wherever serving records administrations. **RD7.**
- **`help_assists.surface`** gains `workbench_ink` (RD8a). The freeform assistance context is a hint-service extension designed with the adaptive-hints owners (RD8b).
- **RW2's workbench session (207)** is shown as a pad of kind `problem` (`pads.workbench_session_id`). Its steps stay in `workbench_steps`, rendered as `text` blocks with the step semantics, and its help ladder and checks are unchanged. Only the frame moves: no data migration and no change to its evidence rule.
- **Annotations:** pen marks on sources use the existing types (`highlight`, `interpretation`, `disposition`). Handwritten notes reference `ink_strokes`.
- **Pad notes** are blocks with `payload.parent_block_id`, not source annotations (§7.1).



### 15.3 Persisted meaning, identity and undo (review F15)
**Stage by stage:**

| Stage | Persisted-meaning change (playbook: a constant in `algorithm_versions.py`, an upgrade row, a test row) | Identity pins |
|---|---|---|
| RD0 | none (new tables, a DERIVED backfill, a read-only union read) | none |
| RD3 | none in scoring. The companion prompt gains desk and pad context, which is a **structured prompt change**: bump deliberately if it keys reuse | `companion.ask` prompt |
| RD4 | **yes**: `pad_text` gaps start steering hypotheses and routing | the gap-reading prompt, if pad text enters a keyed prompt |
| RD5 | none (promoted rows are display; judged rows reuse `search_spans` and `verify_spans`) | none |
| RD6 | none (display of the real model) | none |
| RD7 | **yes**: a new serving surface and administration lock for checks | none expected; check with the pins |
| RD8a/b | RD8a none (an existing hint path with a new surface value); RD8b **yes**: a new assistance context in the hint service | the hint prompts touched |
| RD9a/b/c | RD9c **yes** if redo or amendment change lesson evidence | lesson prompts |

**Undo.**
- *Before activation* (no vault has applied the stage's upgrade), a stage is undone by reverting its landing, with its new tables left inert.
- *After activation*, a persisted-meaning stage is undone only by a **restoring successor** or a pre-upgrade backup, as the playbook says (`docs/algorithm-change-playbook.md:156`).
- No stage adds a kill switch (§1.1).

**Existing switches.** The no-new-switch rule does not touch existing switches. Each Reader switch is audited individually when the old screen goes (§21.1), and retired through ADR-019's path only if nothing else reads it.

---

## 16. Stages

**Placement.** The owner asked on 2026-11-21 that this spec be handed to the orchestration session for implementation on main. The orchestrator places the stages against the queue as it stands (`master-queue.md`) and records the placement.

**Dependencies outside this spec:**
- **RD7's Decider narrowing** waits for the reveal adjudication judgment (queued). RD7 ships with structural protection and whole-window veils of unanchored pads and threads (§12.6.3).
- **RD8b** needs the hint-service freeform context, designed with the adaptive-hints owners.
- **RD9b** waits for NA's native runtime contract: an authenticated local proxy, the CSP entry, bridge injection, restart behaviour and runtime identity per pad or notebook.
- **RD9c** needs teacher v2 to specify redo and amendment.
- **TE6** generates the missing delayed checks; inline checks are only as rich as the checks that exist.
- **KD3** (arXiv full text) makes paper windows whole.

**The landing gate.** Each stage lands from a clean worktree, in memory-capped scopes, through:
- `uv run pytest -n 8 --dist worksteal -m "not arc_close"`;
- `uv run lint-imports --no-cache`;
- `uv run ruff check`;
- `npm run typecheck && npm test && npm run frontend:build`;
- `cargo check`;
- the real-webview harness (§18.3) for stages that change rendering.

Each stage also gets its review file in `docs/reviews/` with the mockup comparison (§4.1), and closes with a Codex Astra adversarial review of its landing plus one fix round.

| Stage | Delivers | Depends on | Acceptance (beyond tests) | Size |
|---|---|---|---|---|
| **RD-spike** (disposable, first) | A packaged-app spike on WebKitGTK, with no product code kept: the §3.6 workload as static HTML in the Tauri shell; the zoom engine prototype (geometry split, one rAF writer, frozen geometry); blur on and off; IndexedDB durability under the packaged origin (kill −9 mid-write, restart); a YouTube embed in the packaged origin; two players with `event.source` isolation; a notebook-like iframe denied Tauri IPC | — | The §3.6 budgets measured on the desktop and on the laptop and recorded in `docs/reviews/`. Decisions recorded: blur kept or dropped, IndexedDB or a SQLite outbox, embed or fallback. If the budgets fail, the overview design is revised before RD1 | S |
| **RD0 Foundations** | Migrations for desks, windows, pads, block versions, anchors and receipts (§15.1); the write protocol (§3.4); exchange context; the two DERIVED span tables with source-specific recipes, replayers and seeded fixtures; `desk.*`, `pad.*` (no UI), `passage.union_range`, `companion.history`, `checks.due_for` (read only); the import fences (§3.3); Rust passthroughs and `client.ts`/`dto.ts` | — | The live projection equals a rebuild for every seeded adapter. Batches are refused out of `seq` order; conflicts return heads; retries return stored receipts | M |
| **RD1 Desk shell with adapters** | `DeskShell`, the window lifecycle contract (§3.6), the key router and the resolved key matrix (§5.4); source and video windows extracted from `ReaderScreen` as scoped instances (listeners through the router, per-instance media identity, no reading activity from previews); **panel windows hosting the existing Guide rail, reading-path card, library pane, notes rail and compare view** (§21.1); slots and pairs, slivers, soft crop, open beside without duplicates, close and undo, move, desks, focus mode (true full screen), footer dots and hints, which-key with the bare-Alt hold rule, the shelf, persistence, first-run desks. The old Reader stays reachable | RD-spike, RD0 | `#desk=1`, `#focus=3`, `#move`, `#zoom=after` (as true full screen). Every window fills its slot's height. Two-player, duplicate-source, hidden-desk and overview-preview tests | L |
| **RD2 Overview and gestures** | The zoom engine (§6.3) with the commit-identity invariant (exact geometry plus a screenshot tolerance); cards with thumbnails and live miniatures (paused, invalidated on change); curved links; overview keyboard and drag; gather; the wheel router with background-only ctrl+drag; the HUD; the laptop rail; reduced motion | RD1 | The §3.6 budgets met in the packaged app; round-trip and navigation tests; `#ov`, `#ovn=*`, `#scrub=0.5`, `#ovg` | L |
| **RD3 Companion and search** | The app-wide `Companion` (docks, tab, anchored summon, dissolve, the drawer-return rule, hand-off, avoid, the pill); **`companion.ask` as a job with polled partial text**; history by day and desk; claims open beside; thread windows; diff proposals (UI ready for pads); search with groups, the meaning job, insert mode and the rofi animation | RD1 (RD2 for the pill) | `#cur=sel`, `#cur=handoff`, `#cur=shiftc`, `#dock=right`, `#hist`, `#spot=softmax`. Edits are acknowledged in under 50 ms and hover cards open in under 250 ms while an answer generates | L |
| **RD4 Scratchpads** | Sticky tabs with merge and distance fillets; the running pad; block kinds except `cell`; the live editor; provenance; gutter marks and hover cards; proposals and labels; two-way links; lift out; arrange (`alt+a`) and split; the pad menu (all rows but marimo); sketch blocks with every tool; the emission contract (`pad_text`, algorithm tag); submit a block; carried questions; the drain; RW2 problem pads; the LaTeX rules (§13.4) in every container | RD1, RD3 | `#tabs=distance,pad=2,padf=0.4`, `#tabs=order`, `#s11=run`, `#s11=lift`, `#s11=sketchqk`, `#s12=info`, `#append`, `#markback`; the § hover text fade; the LaTeX fixture passes in the real webview; emission tests (quote-only pads emit nothing, corrections supersede, tombstones retract) | L |
| **RD5 Menus** | The split source menu: promoted rows (cheap rows from the union read inline, judged rows through the job), every verb wired (§9.1), What this knows; Compare and Teach me open windows | RD0, RD4 | `#menu=cue`, `#menuhl`; promoted rows differ by passage | M |
| **RD6 Goal lens** | `goal.band`, `goal.lens` (mapping states, highest-need aggregation, path reasons), the band, criticality marks with the why, dimming, callouts, the path view with stored overrides, depth, empty states. This replaces the Guide and path panels | RD1 (marks on pads after RD4) | `#goal=frame`, `#goal=why`, `#goal=whysup`, `#goal=whyskip`, `#goal=basics`, `#goal=path`, `#goal=paper`, `#goal=pads`, `nodim`. A table test of every level rule, including unmapped, partial and multi-LO sections | L |
| **RD9a Lesson windows** | `LessonView` extracted; lessons as windows and as stack tabs; review replay; the additions pad; every lesson entry opens a window | RD4 | A lesson opened from a selection lands in the desk's stack; review replays exactly what was recorded | M |
| **RD-retire The old Reader goes** | The parity matrix (§21.1), every row demonstrated on the fixture by its stage; the old screen and the panel adapters that have replacements deleted; each Reader config switch audited individually and retired through ADR-019 where nothing else reads it | RD4, RD5, RD6, RD9a | Every §21.1 row passes its named test; a small, dedicated landing | S |
| **RD7 Inline checks and veils** | The administration protocol (§12.6): closed markers without cues, `check.begin_inline` with protection before the prompt, `check.protect_more`, `check.expose` persisted at once, `check.submit_inline` through the attempt service, the shared administration lock with Today, abandon, crash recovery, whole-window veils for unanchored content, the "counts as practice" outcome, `check_veil_sets`; algorithm tag. Decider narrowing later | RD4, RD6 | `#goal=check`, `#goal=answered`, `#goal=checkb`, `#s12=check`, `#s12=answered`. Layout boxes are identical before and after veiling. The parity test with Check once, plus the §18.1 list | L |
| **RD8a Pen and ink** | Pen input, the recognizer on sources, ink pads, barrel erase, palm rejection, `ink.save`, `ink.transcribe`, editable transcriptions, the help ladder for ink in problem pads | RD4 | `#pen=underline`, `#pen=bracket`, `#pen=note`, `#pen=lasso`, `#pen=strike`, `#pen=pad`, `#pen=ladder`, `#pen=rung2`, `#pen=veil`; the owner's tablet on Linux where available | L |
| **RD8b Freeform ink help** | The hint-service freeform assistance context (with the adaptive-hints owners); the judged line check; the ladder on freewrite; algorithm tag | RD8a | No practice item, session or attempt is created for freeform help | M |
| **RD9b Notebooks** | Notebook lessons in frames through NA's proxy; the paper theme with Literata and even margins; styled commit points; the bridge; marimo `cell` blocks with runtime identity per pad; figure-notebook windows run | NA runtime contract, RD9a | `#tabs=distance,pad=3` against the served notebook; `c` and right-click inside the notebook; two simultaneous sessions; moving a pad keeps its kernel; the frame has no Tauri IPC | L |
| **RD9c Lesson redo and amendment** | Redo and "ask the teacher to extend", per teacher v2's design | teacher v2 spec, RD9a (RD9b for notebooks) | As specified there | M |
| **RD10 Video and carried polish** | Follow-along through correspondents; suggested chapters (judged, accept stores); carried questions resurfacing; `alt+;` timestamps | RD1, RD4 | The following chip and scroll on a fixture with coverage; accepting a chapter draws its ticks | M |

**Order.** RD-spike → RD0 → RD1 → (RD2 ∥ RD3) → RD4 → (RD5 ∥ RD6 ∥ RD9a) → **RD-retire** → RD7 → RD8a → RD8b → RD10. RD9b and RD9c run when their dependencies land.

---

## 17. Deferred, with triggers

| Item | Why deferred | Trigger |
|---|---|---|
| **The rumor map** (the knowledge map seen from open questions: solid ●, dashed ◌, hollow `?` for asked-and-open, faint `◇?` for the diagnoser's open hypotheses; brainstorm §10.6 item 7) | It was in the earlier mockups (linear_algebra, arxiv_v2 iteration 2) and is not in the current workbench; it needs carried questions and the union read first | RD4 and RD5 landed and the owner asks for it back; it would be a window kind over `passage.union` + carried questions + `curriculum.path` |
| **The canvas scratchboard** (tldraw-style; brainstorm T7) | A new dependency (licence check) and the largest build; sketch blocks cover drawing now | After NA, at the owner's call (brainstorm §10.7 Q3) |
| **Learner-informed divergence** (T5), **agents** (T6), **Decider + reranker thread expansion and drain-time suggestions** (T4) | Separate design work; the brainstorm's later stages | After RD5, each as its own spec |
| **A local cross-encoder reranker** | Brainstorm §10.7 Q5 | When proposal labels give training data (§15.1 `proposal_labels`) |
| **Reading tend and Pocket Notes in divergence and the diagnoser** | Changes the notes contract (229/233); brainstorm §10.7 Q1 | The owner's call |
| **Desks and the companion on the phone; companion in MCP v2** | The phone has its own reader (V4); MCP v2 is unmerged | Phone v2 follow-up; MCP v2 M-stages |
| **Passage-level criticality** (an `aside` role in RW4e and the coverage judge, or span-grain coverage) | D1 ships per-section levels; the mockup's in-section skips need a new judged role | The owner wants passage grain (decision D1); needs a schema, prompt and identity-pin landing |
| **Projects as a goal kind with own-code links** | Projects become a goal subset later (owner, Nov 9) | That spec |
| **Linear algebra mockup verification** | The owner: "verify linear_algebra later" | After RD6, against `~/learnloop-mockups/.../linear_algebra/` |
| **The tour** | The mockup's tour is a demo aid; the product teaches through the footer, which-key and empty states | Not planned |

---

## 18. Tests and gates

### 18.1 Backend
For each new RPC:
- the params model refuses extra fields;
- the reply is versioned;
- the CLI surface is unchanged (no CLI) or pinned where a CLI is added.

**Op idempotency.** Repeating any `desk.apply` or `pad.apply` op is a no-op. Out-of-order replay converges.

**Append-only.** Block versions, anchors, ink and submissions refuse UPDATE and DELETE by trigger (as `workbench_steps`).

**Union read:**
- returns every kind listed in §7.6 for a span on a seeded vault (`tests/helpers.py` builders, plus new `tests/desk_helpers.py`);
- span aliases carry across re-reads;
- the DERIVED backfill equals the live writes after a rebuild (`learnloop rebuild --shadow`).

**Emission:** a committed block produces a `pad_text` gap row, and a sketch produces none. **Submission:** a submitted block produces an attempt or teach-back through the existing entry. The grader's inputs contain no pad, desk, ink or veil data (an import-contract test and a payload test).

**Inline checks:**
- `checks.due_for` finds hosts;
- `check.begin_inline` → `check.submit_inline` produces the same attempt, grade and settlement as Check once for the same item, contract and answer (a parity test);
- duplicate submissions, a crash and restart mid-administration, the same commitment open in Today and the Reader, held candidates, and an exposed (assisted) answer that leaves the cold duty pending;
- the closed marker, band and callouts reveal no item, LO or purpose text while a check is due;
- an opened veil makes the administration assisted;
- `lo_certification` decides readiness. One answer doesn't flip an LO unless credit says so.

**Goal lens.** Levels from fixture path and coverage rows match a table test for every rule in §12.3, including RW4e role refinement and the "per section" reason.

### 18.2 Frontend (vitest plus component tests)
**Pure units:**
- the workspace model (every op, pairs capped at two, expel, gather and ungather);
- geometry for both views;
- the zoom engine's frame function (log-scale interpolation, release rule, end latch);
- the wheel classifier (touch, pinch, notch; deltaMode normalisation);
- the key router scopes and the keymap collision table, including the bare-Alt tap versus hold rule;
- the sticky-tab merge function;
- the recognizer's thresholds.

**Invariants:**
- the round trip restores the reading layout within 1 px;
- the selection stays in view on every overview path;
- the **zoom's last frame equals the overview's first frame**: exact geometry (within 0.5 px) in unit tests of the engine's frame function, plus a real-webview screenshot comparison within the documented tolerance (§18.3);
- a docked or hidden companion never moves on scroll, pan, reorder, gather, pair or desk switch; an anchored one leaves only by the §8.3 transitions;
- dissolve and summon never pass through the dock position (a frame-sampled position test);
- veiling changes no element's layout box.

**LaTeX fixture (§13.4):** run in the real webview harness (§18.3). Rendered ink bounds sit inside the nearest clipping ancestor below the window scroller with at least 3 px above and 5 px below; wide equations are fitted (≥ 0.75) or scroll horizontally at full height.

### 18.3 Visual review fixtures (public-safe)
A **synthetic workspace fixture** (`apps/learnloop-tauri/src/fixtures/desks/`) mirrors the mockup's desk arrangement with project-authored text: a public-domain or self-written "book" on softmax, a synthetic transcript, synthetic pads, LOs, coverage, a goal, checks A and B.

The fixture serves three purposes:
- component screenshots for reviews;
- performance measurement;
- the side-by-side comparison against the mockup's deep links.

No owner book text, vault data or mockup screenshot enters the repo. `tests/test_public_tip_guards.py` applies, and the visual-review screenshots show only the synthetic fixture's project-authored text.

**The real-webview harness (review F10).** Vitest runs in jsdom (`vitest.config.mjs:6`), which cannot lay out or rasterize. Layout, pixel, LaTeX and animation tests therefore run in a real-webview harness:
- **What runs it:** WebKitGTK through the Tauri test build, or WebKit through Playwright as a stand-in where the Tauri driver is unavailable. The difference between the two is recorded once in the RD-spike review.
- **Controls:** local fonts only, media replaced by posters, and the clock and animation frames driven by the harness.
- **What it asserts:**
  - exact geometry (window rects, transforms, opacity at given progress);
  - screenshot comparisons under a **documented tolerance** (a per-pixel threshold and a maximum changed area, set in the RD-spike from measured rasterization noise);
  - frame-time traces.

### 18.4 Performance (RD-spike measures; RD2 gates; re-checked at RD4 and RD6)
Run in the packaged Tauri app on WebKitGTK, on the desktop and on the laptop, with the §3.6 workload. Check the §3.6 budgets: 95th-percentile frame ≤ 20 ms, no frame over 50 ms, script ≤ 4 ms per frame, idle CPU, memory, and responsiveness while the companion generates. Record:
- gesture-start script and style time;
- frame times over a zoom;
- the count of long frames;
- raster time.

Record the same for blur on and off (companion and search) and decide per §3.6. The results go in the stage's review file.

---

## 19. Adversarial review (Codex Astra, 2026-11-21)

Astra reviewed the first draft against main `002c58fe17` (read-only; it ran no app or tests). **Its verdict: "revise before implementation"**:
- the interaction model fits the owner's decisions;
- several claims that the build "reuses existing behaviour" hid changes to persistence, serving and evidence;
- RD0 and RD4 packed too much.

All 17 findings were accepted, and the spec was revised:

| # | Severity | Finding | Change made |
|---|---|---|---|
| F1 | blocker | Veiling does not establish coldness: the check showed its LO and provenance beside the answer before veiling; the band, callouts, search and thumbnails leak; structural veils are not a superset | §12.6.1 shows a closed marker with no cues, and purpose text for that LO is hidden while a check is due. §12.6.2 computes protection before the prompt. §12.6.3 veils unanchored pads and threads whole, never grants cold credit by veiling, and labels uncertain protection "counts as practice" with the duty left pending |
| F2 | blocker | No administration lifecycle: no item, contract, token or idempotency; `intent/checks.py` is not a grader | `check.begin_inline` / `protect_more` / `expose` / `submit_inline` / `abandon_inline` (§3.4, §12.6.2–12.6.5). The item comes from serving's eligibility, the attempt goes through the attempt service, settlement through `settle_answered_checks`. A lock is shared with Today, plus crash recovery |
| F3 | blocker | Idempotency is not convergence; no ordering, heads or durability; the IndexedDB origin is unproven | `client_id` + `seq`, `expected_head`, transactional batches with receipts, conflict rules that keep both texts, client-minted ids for create and submit, vault-scoped outbox, saved only after the IndexedDB commit. The packaged-origin durability is tested in the RD-spike, with a SQLite fallback (§3.4, §3.5) |
| F4 | major | Emissions lacked a provenance and effects contract; `pad_text` must be registered in the contract module | Only learner-authored text is emitted, with immutable versions, supersession, tombstone retraction, and `pad_text` in `READABLE_SOURCE_KINDS` and `NON_SERVING_SOURCE_KINDS`. Submission is refused for quoted text and labelled assisted after worked help (§10.9, §10.11) |
| F5 | major | Span backfills are only partly recoverable; the fixture has no rows | Per-source recipes with anchor quality (`exact_selection`, `citation`, `source_context`, `unanchored`); `entity_source_links` never places a gap; seeded fixtures for every adapter (§7.6) |
| F6 | major | RW4e has no aside or digression roles; no multi-LO precedence; missing mapping must not mean "not needed" | Section-level marks with unmapped and partial states and highest-need aggregation; an `aside` role deferred as a judged schema change (§12.3, D1, §17) |
| F7 | major | The RD4 deletion gate depended on RD5, RD6 and RD9a; Compare had no window | Panel adapters from RD1; a Compare window kind; a dedicated RD-retire landing after RD4, RD5, RD6 and RD9a; a parity matrix with stage and proof per row (§16, §21.1) |
| F8 | major | `reader.ask` is synchronous inside the mutex; per-span fan-out; the goal level wrongly sat in the union read | `companion.ask` as a job with polled partial text; `passage.union_range` per visible range; the goal level moved to `goal.lens`; a central poller; latency budgets while generating (§3.4, §3.6, §7.6) |
| F9 | major | Extraction isn't enough for multiple windows; the YouTube listener checks origin but not source | The window lifecycle contract (ownership, pausing, no activity from previews), per-instance media identity with `event.source`, which fixes `YouTubeWatchPanel.tsx:238` (§3.6) |
| F10 | major | Performance and visual gates were not executable; jsdom can't lay out; zero-tolerance pixels are brittle | A defined workload and budgets, frozen geometry, a packaged RD-spike first, a real-webview harness with documented tolerance plus exact geometry (§3.6, §6.3, §18.3) |
| F11 | major | Iframe feasibility and runtime ownership unsettled; CSP lacks the notebook origin; kernel per desk is wrong | The CSP plan, IPC denial and embed fallback (§3.6); runtime identity per pad (§11.5); RD9b depends on NA's runtime contract (§16) |
| F12 | major | The ink ladder needs an item-bound hint request | RD8a covers problem pads only; RD8b adds a freeform assistance context in the hint service with the adaptive-hints owners. No manufactured items (§10.10) |
| F13 | major | Redo and augment need backend design | RD9a covers review and additions only; RD9c covers redo and amendment per teacher v2; no label-only buttons (§11.1) |
| F14 | major | The object model can't represent lessons in stacks, Compare, pairs and pad notes | One `ContentRef`; authoritative slots, with pairs as two panes; stacks hold pad or lesson refs; pad notes as blocks (§3.4, §5.2, §7.1) |
| F15 | major | The gap vocabulary was stale (248 has `lesson` and `external_chat`, in two tables); invalid rollback; switches can't vanish wholesale | Both tables rebuilt from the actual head; persisted meaning and identity per stage; undo before versus after activation; an individual switch audit (§2.1, §15.2, §15.3, §21.1) |
| F16 | major | Key collisions (`Alt+S` Settings, ctrl+drag, the pad menu's `s`, alt+vertical) | A resolved precedence matrix; `alt+a` arrange; background-only ctrl+drag; `i` for pieces; D14 (§5.4) |
| F17 | minor | The companion's "never moves" and math's "no clipping ancestor" contradicted the UI | Immobility scoped by state; math safety defined below the window scroller and checked by rendered ink bounds (§8.2, §13.4) |

Astra also resolved an open question in the first draft: `deliverable_path_sections.reason` exists (migration 228), and it is now the reason text (§12.3).

**What it could not verify:** run-time performance, IndexedDB durability under the packaged origin, YouTube playback, tablets, and the unbuilt NA runtime and reveal-judgment APIs. The RD-spike covers the first three before any product code.

## 20. Decisions (recommended defaults; the owner may override any)

| # | Question | Default in this spec | Why |
|---|---|---|---|
| D1 | Criticality at passage grain: real, or per section? | Per section from the real model, with explicit unmapped and partial states and a highest-need aggregation across LOs; passages inherit the section's level. An `aside` role for passage refinement is deferred (§17) | Honest and buildable now; RW4e has no aside role (review F6) |
| D2 | Due cold checks in the Reader at their passage, or only in practice? | Both: inline at the host passage and in Today; the first answer settles it. The host passage carries "check due before this", never a forced stop | The owner liked the masked check; Today stays the reliable place |
| D3 | HMWL's three tracks vs one real depth | One depth per goal (the real model); the path view shows each depth's size (pages, minutes) so the three read like tracks | No model change |
| D4 | "Project" kind | Display only, until projects become a goal subset | Owner, Nov 9 |
| D5 | Skippable text dimmed by default, or on request? | Dimmed by default, never hidden; the toggle is remembered per machine | The mockup's default; frictionless and reversible |
| D6 | Tab grade default | `distance`, with `flat` and `order` as view preferences | The owner loved distance with merging fillets |
| D7 | Sketch canvas library | Hand-rolled SVG; tldraw deferred | No new dependency or licence question for blocks |
| D8 | Ink transcription route | The plan transport's vision route first; Pocket Notes OCR compared on the owner's handwriting in RD8a | Uses existing transport and consent rules |
| D9 | Carried questions: count, and do they change router offers from day one? | They inform router and Teacher offers as learner picks from day one; the shelf shows three (an attention limit, labelled) | Brainstorm §10.6 item 8; no count cap on carrying |
| D10 | LearnLoop suggestions: unprompted or only at a drain? | Pad proposals appear unprompted but quiet: at most one marker per committed block, mutable per pad. New structure suggestions (re-grouping, new desks) only at the drain or on request | The owner's "unobtrusively via markers"; brainstorm §10.7 Q2 |
| D11 | First-run desks for an existing vault | One desk per recently read source set, plus a running pad each | Gives a working set at once; the learner reorganizes |
| D12 | When the old Reader goes | In a dedicated RD-retire landing after RD4, RD5, RD6 and RD9a, once every parity row passes (§21.1); panel adapters bridge the gap | Two Readers would drift; deletion must follow demonstrable parity (review F7) |
| D13 | Blur effects on WebKitGTK | Kept if within the frame budget, else opacity and scale only (measured in RD2) | §3.6 |
| D14 | Alt + vertical scroll: overview zoom (the later request, O6) or pads and desks (the Nov 21 touch decision)? | Zoom. Pads and desks move with `alt+j/k` and by plain scrolling in stacks | The owner's later, more specific request; please confirm |
| D15 | While a check is due, hide that LO's purpose text and names (band, callouts, why cards, thumbnails)? | Yes, until the check is answered or abandoned for the day | Cold presentation (review F1); it costs a little goal context for an honest check |
| D16 | Uncertain protection (an unanchored pad was visible before veiling, no Decider yet): what happens to the answer? | Graded and kept as practice; the cold duty stays pending and returns in Today | Honest labels; never a cold credit from masking |

---

## 21. Parity and completeness

### 21.1 Every v1 Reader surface, where it lives now, and when (the parity matrix)
**Using the matrix.** Each row names the stage that delivers its replacement and the test that proves it. From RD1 until its replacement lands, a row marked *panel* runs as the existing component inside a panel window.

| v1 surface (built) | New home | Delivered by | Proof |
|---|---|---|---|
| Source pane (render view, PDF pane, selection drag / ctrl+drag / alt+drag, capture, health flags) | Source windows (§7.1) | RD1 | The existing ReaderScreen selection and capture tests, run against `SourceWindow` |
| Guide rail (cues, reading-path card, deliverable slice) | *panel* from RD1; then margin marks (§7.1), the band and path (§12.2, §12.5), callouts (§12.4) | RD1 → RD6 | Guide and path tests against the band and path view |
| Ask rail, branches, detour strip, reconnect, docked Ask and overlay (RW1a, CA2) | The companion (§8), branches kept; the detour strip and `alt+←` stay inside source windows | RD3 | Branch, reconnect and return-stack tests |
| Intent box, active reading (RW1b) | Inside source windows (the components unchanged) | RD1 | Existing tests |
| The tutor that looks things up (RW1c) | The companion (`retrieval_intent` unchanged) | RD3 | Existing tests through `companion.ask` |
| Workbench (RW2a–d) | Problem pads (§15.2); help ladder, checks and submit unchanged | RD4 | The workbench tests against the problem pad |
| Notes rail | *panel* from RD1; then margin notes (§7.1), search (§9.3), What this knows (§9.1) | RD1 → RD5 | Notes tests |
| Margin cues (RW3a/b), `alt+↓/↑` | Margin marks in source windows; keys unchanged | RD1 | Existing cue tests |
| Library ask, compare, keep, roles (RW4a/d/e, CA1–CA5a) | *panel* (library pane) from RD1; a Compare window and the Compare verb; library ask through search's meaning group and the companion | RD1 → RD5 | Compare and keep tests against the Compare window |
| Exercises from my sources (RW4b) | Exercise rows in book windows; Make it practice | RD1, RD5 | Existing tests |
| Figures and Show me (RW5a–d) | §13.1 | RD1 (insets), RD3 (companion) | Existing figure tests |
| Last time here, wrap up, digest (RW6a/b) | The recap card in the source window on return; wrap up at the desk drain (§10.12) | RD1, RD4 | Recap and wrap-up tests |
| Cold follow-ups (RW6b) | Unchanged (commitments), and hosted inline (§12.6) | — / RD7 | Existing tests |
| Reading paths (RW7a/b) | *panel* from RD1; then the path view (§12.5) | RD1 → RD6 | Path tests |
| Side by side (CA6/6b) | Two windows in view, or a pair (§5.2) | RD1 | Side-by-side tests adapted to two windows |
| Watch panel (video) | Video windows (§7.4) | RD1 | Watch-plan tests plus the two-player isolation test |
| Quick checks, authored questions | Inside source windows (unchanged) | RD1 | Existing tests |
| Lesson entry from the Reader | Lesson windows (§11.1) | RD9a | Lesson-entry tests |
| Reader config switches (`reader_inquiry.enabled`, `tutor_qa.reader_enabled`, `workbench.enabled`, cue and recap switches) | Each audited individually at RD-retire: retired through ADR-019 where nothing else reads it, kept otherwise | RD-retire | The audit table in the RD-retire review |

**RD-retire** deletes `ReaderScreen` and the panel adapters whose replacements have landed, once every row above passes its proof.

### 21.2 Everything planned and discussed, and where it is specified
| Item | § |
|---|---|
| Owner decisions 1–18 (§1.2) | 1: §5.1, §6. 2: §8.5. 3: §4.2. 4: §9.3. 5: §8.3. 6: §10.7. 7: §7.6, §8. 8: §5.2, §6.1. 9: §10.3, §11. 10: §10.1, §10.2, §10.8. 11: §5.7. 12: §10.5, §5.6. 13: §10.11, §10.9. 14: §12.6. 15: §5.4. 16: §5.5. 17: §10.10. 18: §9, §10.6 |
| The owner's requests O1–O17 (§1.3) | as listed in §1.3 |
| Goal fork: band, LO dots, depth, you are reading, next for the goal | §12.2 |
| Goal fork: criticality marks with why, dimming, minimap ranges | §12.3 |
| Goal fork: callouts, picks for the goal | §12.4 |
| Goal fork: path view, unmatched phrase, overrides | §12.5 |
| Goal fork: goal-tied checks A and B, veils, readiness | §12.6, §12.7 |
| Goal fork: the five open questions | D1–D5 |
| Mockup: slivers, soft crop, shelf drag, undo close, new desk, swap pair (`x`) | §5.2, §5.4, §5.1 |
| Mockup: gather and preview | §6.6 |
| Mockup: overview cards, chips, relations, selection ring, pill | §6.1, §6.5, §8.2 |
| Mockup: follow-along, suggested chapters | §7.5, §7.9 |
| Mockup: margin notes, highlights, claims, back-links | §7.1, §7.7, §10.7 |
| Mockup: thread windows, companion history, avoid | §7.8, §8.5, §8.2 |
| Mockup: running pad, lift out, timestamps, kept pads, PADMETA labels | §10.1, §10.5, §7.4 |
| Mockup: block provenance, submitted tags, emission popover | §10.4, §10.9, §10.11 |
| Mockup: sketch blocks, marimo cells, source pieces | §10.8, §11.5, §9.2 |
| Mockup: ink pad, help ladder, pen recognizer | §10.10 |
| Mockup: Show me in the companion, view source, move to pad | §13.1 |
| Mockup: Teacher lesson modes, additions, not-served state, bridge | §11 |
| Mockup: cold-check overlay, veils | §12.6 |
| Mockup: carried questions, drain | §10.12 |
| Mockup: laptop rail, touchpad, WebKitGTK modifier issue | §13.2, §5.5, §3.6 |
| Mockup defects not to copy | §4.4 |
| Rumor map, canvas, divergence, agents | §17 |
| The search box in the Reader redo | §9.3 |
| LaTeX must be solid | §13.4, §18.2 |

---

## 22. Risks

1. **WebKitGTK performance.** The mockup's engine was measured in Chromium only, and blur and many transformed layers may be slow in WebKitGTK. *Mitigation:* RD2's measured gate on the real target, opacity-only fallbacks, and `content-visibility` for off-screen windows.
2. **The `ReaderScreen` extraction.** 4,711 lines of hooks moving into windows could regress v1 behaviour. *Mitigation:* extract into scoped window instances, don't rewrite; panel adapters host what has no replacement yet; RD1 keeps the old screen reachable; RD-retire deletes it only after the parity matrix (§21.1) and the existing Reader tests pass against the windows.
3. **Size.** This is the largest frontend build so far (an XL stage and six L stages). *Mitigation:* every stage ships something usable; RD0–RD4 alone replace the Reader.
4. **The sidecar mutex.** Union reads, promoted rows and lens queries on every hover could queue behind long calls. *Mitigation:* cheap rows are synchronous and cached in `queryCache`; anything judged is a job; hover cards read from the cached union read.
5. **YouTube embeds in Tauri.** The existing watch panel embeds under the app's origin, but error 153 (embedding refused) must have a graceful path (§7.4).
6. **Veil correctness before the Decider judgment.** The structural veil hides more than needed (honest, labelled), and sometimes misses answer-bearing text not anchored to the LO. *Mitigation:* the Decider refinement when the reveal judgment lands; `check_veil_sets` keeps a record for audit.
7. **Data thinness.** A real vault may have no coverage and no usable delayed checks yet (§2.3). *Mitigation:* the empty states (§12.8), the synthetic fixture for building, and a runbook step for the owner to map a goal.
8. **marimo in a frame** depends on NA's runtime and bridge injection (RD9b). Until then, lessons run in the existing lesson UI.
9. **Pen on Linux.** Tablet multitouch support varies by model. Pen input itself is standard pointer events; touch gestures are optional.

---

## 23. Checked, and not checked

**Checked:**
- main at `002c58fe17` (migration head 255) for every module, table, RPC and contract cited in §2 and §3, by a read-only audit and again by the Astra review (§19);
- the `learner_text_gaps` and `learner_text_gap_jobs` vocabulary (migration 248) and the effect sets in `diagnosis/text_gaps/contract.py`;
- the bare-Alt rule (`bareAlt.ts`) and the shell chords in `keymap.ts` (Alt+S is Settings);
- `YouTubeWatchPanel`'s origin check (not source-checked: a bug fixed by §3.6);
- the CSP in `tauri.conf.json`;
- table roles (`db/table_roles.py`);
- RW4e's role vocabulary (`source_roles.py:64`);
- the item-bound `HintRequestV1`;
- `deliverable_path_sections.reason` (228);
- the lesson RPC actions;
- teach-back, authoring and `curriculum.*` RPC names;
- the mockups, through a full inventory of the final override chain, with headless-browser checks of the defects in §4.4.

**Not checked (the RD-spike covers the first three):**
- run-time performance on packaged WebKitGTK;
- IndexedDB durability under the packaged origin;
- YouTube embedding in the packaged origin;
- NA's runtime contract (unbuilt; §11.2–§11.5 name the needs, not the API);
- the reveal-judgment API (no spec yet);
- the owner's tablet model on Linux.

## 24. Liveness (owner, Nov 22; from the mockups and the live-programs research)

Research: `docs/brainstorming/Live Programs and Explorable Explanations 2026-11-22.md`, covering Jack Rusher's *Stop Writing Dead Programs* and Bret Victor's *Learnable Programming*, *Up and Down the Ladder of Abstraction* and *Explorable Explanations*.

The round-14 mockup (`~/learnloop-mockups/2026-11-20-reader-thread-space/arxiv_v2`) is strong on space: desks, the zoomed overview, the companion, pads with provenance. What it lacks is liveness. The book, the pads and LearnLoop's model of the learner are still dead text. A small example shows it:
- a book page works an example through to a stated conclusion (for instance "at x = 3, the score is 7");
- the pad beside it holds the learner's own line evaluating it at another value;
- the learner can touch none of these numbers.

**Rules for everything in this section:**
- **Evidence:** live views are help and write help rows. They never certify anything (§14).
- **Veils:** they are veiled while a cold check on that passage is open (§12.6).
- **Kernels:** they run small local kernels, never a serve-time model.
- **Linked views:** they share the notebook toolbox's linked-views bus and kernels (notebook spec §20.11), so the book, pads, notebooks and lessons address the same entities.

### 24.1 Reactive passages ("Make it live")
- **The verb:** a fixed verb in the split menu (§9.1) on a worked example turns the passage's numbers into draggable values in place, underlined as Victor marks them. Dragging x recomputes the page's own conclusion ("at x = 3, the score is 7") inline, overlaid on the book's text and never altering it.
- **The kernel:**
  - It is extracted per passage at ingestion or on first use, with fidelity `reconstructed`.
  - It ships only if it reproduces every number the passage states. That is a contract, checked like the notebook harness's `js_agreement` (notebook spec §20.10). If it fails, the passage stays static and says why.
  - The same kernel serves the Show me figure (§13.1), the Teacher lesson and notebook items, so the book, the lesson and the check use one model.
- **Numbers become values:** a passage's numbers become live values (notebook spec §20.11, live numbers in prose). Worked examples come alive, and the reader can test the author's argument, not just accept or reject it.

### 24.2 Live pad lines
- **What:** a pad line that holds an expression, or a claim with numbers, can be made live. It is a lighter form of §11.5's marimo cells in pads.
  - "score(x) = 2*x + 1 at x = 3" evaluates, x becomes scrubbable, and the line's numbers update.
  - "check: the slope of x*x at 3 is 6, and it matches finite differences ✓" reruns its check and shows ✓ or ✗ with the numbers.
- **Parsing:** a line that can't be parsed stays text.
- **Evidence:** a live line remains an emission (§10.11). Its recomputed results are help, and submitting it is still the separate act of §10.9.

### 24.3 Linked views across book, pads, sketches and notebooks (owner: "amazing in textbooks, notebooks, scratchpads, sketch and LaTeX alike")
- **Shared ids:** every live representation names the entities it draws, using the same id scheme as Dragology elements and the notebook bus (notebook spec §20.11). Examples: `W-2-1`, `class-2`, `softmax.T`.
- **Linked highlighting:** hovering a symbol in a pad's LaTeX highlights the same entity in the live passage, the sketch (a sketch block may tag strokes with an id), an open notebook view and the companion's answer. Scrubbing T in a pad line moves T wherever else it is live on the desk.
- **The bus:** one per desk, so linking spans windows, and overview cards brighten along links for the hovered entity (§24.7).
- **Why ids:** shared ids give later features a common handle. Computing on or mutating "the same thing" across representations (generating a variant, a check, a comparison) becomes an operation on ids rather than on pixels or prose.

### 24.4 The desk timeline: scrub your own day (owner: "I love the idea")
- **The scrubber:** a scrubber on the footer (§5.3) replays the desk's day. It shows which windows were open and where, how each pad grew block by block, when each question was asked and answered, when checks were answered and veils fell, and where the learner was reading.
- **Behaviour:**
  - Dragging the scrubber shows each moment as a ghost of the layout. Releasing it returns to now.
  - Enter restores that moment's layout as a new arrangement. Content is never rewound; only the arrangement is restored.
  - Ticks mark events: questions, checks, commits, carried questions.
  - A day picker reaches earlier days.
  - The overview can play a day's timeline compressed, as a review: what did I do today?
- **Data:** an append-only `desk_events` log (window opened, closed or moved; pad block added or edited; companion turn; check answered; veil raised or lifted; reading position), with a snapshot each N events for fast seeking. Pads already keep block history (§15.3), and the companion history is already searchable by day (§8.5); the timeline makes both spatial.
- **The learner's own trajectory:** it applies Victor's flow timeline to one's own learning. It answers "where was I?" and "how did I get here?" better than search does, and it gives the diagnoser a time-ordered view of reading, questions and checks (an emission view, never evidence).
- **Placement:** promoted from deferred to a stage after RD2 (the overview), because it reuses the overview's layout snapshots.

### 24.5 Peek: a term, a key, a card
- **What:** hover a term and press a key to get a small card instead of the companion. It holds:
  - the vault's definition;
  - where the learner first met the term (linked);
  - their own earliest pad line about it;
  - the companion's last answer about it.

  The card dismisses on mouse-out.
- **Why:** `c` opens a conversation; this is a glance. Lowering the cost of a question to near zero is what makes readers ask more of them, Victor's "contextual information".

### 24.6 Inspect LearnLoop's own state
The goal band's readiness, a criticality mark, a gutter marker and a veil are LearnLoop's hidden state, and each becomes inspectable on click:
- the evidence rows behind readiness (cold checks with dates and results);
- why this passage is critical for this goal;
- why this marker appeared;
- which check a veil protects, and when it lifts.

This is Rusher's inspector applied to the learner model, and it keeps the owner's rule: frictionless by default, glass box on demand.

### 24.7 The feel: immediacy and no dead ends
- **Ghosted previews:** hovering a split-menu verb previews its effect in place before the click (where a note lands, what a pad gains, which veil a check raises). This is Victor's "create by reacting".
- **Responsiveness:** a response within a frame or two (the §3.6 budget). Anything slower shows progress where its result will appear.
- **No dead ends:** a failed import, an unparseable pad line or a missing kernel offers fix and retry in place, never a modal error. These are Rusher's restarts.
- **The overview links:** they fade by default and brighten for the hovered card or entity (§24.3). Round 14 draws every curved link at equal weight, which reads as wiring rather than structure.

### 24.8 Placement
- **A mockup round 15** comes first: reactive passages (§24.1) on the Welch Labs page, live pad lines (§24.2) and linked highlighting between them (§24.3).
- **In the build:**

| Stage | Additions |
|---|---|
| RD2 | Overview link fading |
| After RD2 | The desk timeline (§24.4) |
| With §13.1 | Reactive passages, sharing kernels with Show me figures and notebook domain kernels |
| With §11.5 | Live pad lines and the linked-views bus |
| Alongside the goal lens (§12) | Peek and the state inspector |

- **Not checked:** passage-kernel extraction quality, and the cost of the timeline's event log on a long day. The RD-spike measures both.

