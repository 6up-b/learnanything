# Current screens: audit behind `ux_learnloop_v1.md`

This audit backs `docs/specs/ux_learnloop_v1.md`. It records what a first-time learner meets in each screen of the LearnLoop desktop app, as built at `57d31c63`. It was compiled 2026-10-12/13 by reading the frontend (`apps/learnloop-tauri/src`), the Tauri shell and the sidecar handlers they call.

**What this is and isn't**
- This is a code reading, not a usability session.
- It quotes user-visible copy with file and line references.
- Where it judges, it says so: **[judgment]**.
- §11 of the spec plans the sessions that measure it.

**Parts**
- **Part A.** The learner path: Start, Today, Practice, Feedback, Review, Repair, Exam, and the core loop counted.
- **Part B.** Navigation, the knowledge views (Graph, Well, Terrain, Strata), Proposals, Registry, the diagnostic check, Calibration, Maintain, Settings and SqliteBrowser.
- **Part C.** How the Reader is entered and left, the components, copy and jargon counts, errors, and keys.

## Part A. The learner path: Start, Today, Practice, Feedback, Review, Repair, Exam

**Scope and abbreviations.** Paths are relative to `apps/learnloop-tauri/src/`. The letters stand for screens:

| Letter | Screen |
|---|---|
| A | `app/App.tsx` |
| S | `StartScreen` |
| T | `TodayScreen` |
| D | `today/DailyPlanView` |
| P | `PracticeScreen` |
| F | `FeedbackScreen` |
| R | `ReviewScreen` |
| RP | `RepairScreen` |
| E | `ExamScreen` |

**Method.** I read the code at `57d31c63` and did not run it.

**A new vault's starting state.** It is written at `mvp-0.14` (`vault/loader.py:370`, `config/template.py:808-822`). That means:
- the daily plan is on (`config/schema.py:1855`);
- grading is blind;
- diagnosis runs asynchronously.

### A.0 Landing, sessions, transport

**Landing.** The app always lands on **Start** (A:81). It also returns to Start after any library switch (A:776). The one exception is a saved practice checkpoint, which resumes straight into Practice.

**The session gate.** Practice needs a session. Without one, the learner is bounced to Start with one of these toasts:
- "Start a session before opening practice." (A:484, 532)
- "Begin today's plan on Start first." (A:1008)
- "Start a session to practice the primed item — it will open automatically." (A:1247)

**Transport.** Every RPC goes through one Rust mutex and one Python stdin loop (`src-tauri/src/sidecar.rs:207-247`, `server.py:30-41`). So any slow call, such as a grading call (`ai.timeout_seconds=180`), queues everything behind it.

**Startup.** `initialize` runs `run_startup_maintenance`. That regrades every self-graded attempt that lacks AI evidence, with no upper bound (`ops/startup.py:33-93`), while the screen shows "Loading LearnLoop vault".

### A.1 Start (S)

**Left half.** An animated backdrop, plus:
- a `backdrop:` cycler chip;
- the line `{n} concepts in scope · {n} active learning_objects · {n} error types`. On a fresh vault this reads "0 … 0 … 0". When no vault is loaded, it falls back to fake numbers: "11 concepts in scope · 18 active learning_objects · 3 open misconceptions" (S:1819).

**Right half.**
- "ready to practice?"
- "+ create a new vault ▸"
- "Time today" with 10/15/25/40/60.
- "Today's plan": `25 min · maintain 13 · repair 4 · new 4 · push 4 (why)`.
- "First: …".
- **"begin today's plan · 25 min ↵"**.

**When the plan is off (older vaults):**
- "scheduler mode **short_session — probe_eig suppressed (≤20 min)**"
- the tiles "due now / probe queue / later today / follow-ups".

**First run.**
1. The screen shows "Nothing due today."
2. Begin leads to the done screen: "Nothing due today · keep going ↵ / done / more new material".
3. "more new material" leads to "No new material is ready to add."

**Nothing points to adding a source.**

### A.2 Today (T, D)

**The plan view** (`DailyPlanView`) is the cleanest learner surface in the app. It shows:
- "Today" with the split line and "(why)";
- minute chips;
- the current block, "Block {n} of about {N} · {lane} · about N min · why";
- "begin ↵ / continue ↵", "skip this item";
- the next block;
- the done screen, "Today complete · 26 min · 9 items · ● 5 days streak".

The plan view still has two kinds of jargon: the lane names maintain/repair/new/push, and "Block 2 of about 3".

**Hidden cost.** Even in the plan view, Today mounts about 12–14 reads. It also starts pollers:
- `get_queue_revision` every 3 s;
- `list_ingest_batches` every 7 s;
- InboxStrip every 30 s.

**The full list** (key `l`, and the only view on older vaults) is a scheduler debugger. It shows:
- **InboxStrip** first, even when empty: "Inbox · 0 · [Include handled] · saved references, no practice started · Tutor subject".
- A hero with "TODAY · SESSION 007", "vault ● healthy · ai:codex ● ready · queue ● ready", and a grid **DUE / PROBE / LATER / BUDGET**.
- **GoalBanner**, with about 10 numbers before any action, including "pooled Brier 0.183" behind a toggle. It holds the only "take practice exam" button, and that banner is not shown in the plan view.
- **SurpriseInsertionBanner**: "INTERVENTION GATE - DIAGNOSTIC FOLLOW-UP INSERTED" / "VALIDITY CHECK - HELD-OUT COLD PROBE INSERTED" / "using a hint (or opening it primed) voids the measurement and the attempt will be rejected".
- **Rows**: a raw `practiceItemId`, a raw mode pill (`diagnostic_probe`), and "MASTERY ESTIMATE ▮▮▮▯ 0.62", under "DUE NOW / PROBE QUEUE / LATER TODAY".
- **QueueRankingStrip**, always shown: "PRIORITY = Σ wᵢ · COMPONENTᵢ / forgetting_risk × 1.00 + goal_frontier × 0.25 + recent_error × 0.50 + probe_eig × 0.25 / algorithm mvp-0.14". The weights are hard-coded in the UI.
- **The detail pane**:
  - the full prompt, shown before practice starts;
  - "Mastery estimate 0.62 ±0.18 … difficulty 0.47";
  - **ClaimSurface** "Scheduler choice … policy · {ULID} · was this queue choice useful?" with 7 buttons;
  - "Why this position" bars and "priority 0.412";
  - "Evidence facets" chips that open "β(3.2, 1.8) · independent evidence mass".
- **Keys.** `e` ends the session with no confirmation.

### A.3 Practice (P)

**Header and banners.**
- A meta row with the **raw item ULID** (it opens the inspector, which shows the expected answer and rubric), the mode slug, the subject, and **"codex grading"**.
- Probe banner: "Diagnostic check ▮▮▯▯ question 1 of up to 4 · … hints and ask-tutor are paused".
- Cold banner: "unassisted check · hints will void this measurement and the attempt will be rejected."
- "MASTERY ESTIMATE ▮▮ 0.62 ±0.18".

**Below the question.**
- `ItemPresentation`, which is clean.
- **CardControls**: "THIS CARD: reword · retire · ↓ easier · ↑ harder · ◊ teach it · ✓ I know this". The retire control offers 11 reasons.
- The editor, "type your answer — $math$ renders as you type", with a "{n} chars · {n} words" count, the optional confidence 1–5, and the optional "why" line.

**Keyboard-only actions.** These exist only in the key bar, with no button:
- **hint (^h)**;
- **skip (^s)**, which returns to Today rather than going to the next item;
- **ask tutor (?)**;
- don't-know (^d), when the stuck prompt is off.

"^d I'm stuck" ("Write what you can, or what's confusing you…") is a button when the stuck prompt is on.

**Submit.** It runs `save_practice_draft`, then `submit_attempt`, which is a **synchronous LLM grading call** shown only as "grading attempt...".

**Self-grade fallback (no AI).**
1. The first Submit only reveals the panel.
2. The panel asks for a numeric score per rubric criterion (default 0, step 0.25), "fatal errors {id} caps at {n}", attribution chips and confidence. **No reference answer is shown.**
3. The learner has to Submit again.

**Teach-back.** Each turn is a synchronous LLM call.

### A.4 Feedback (F)

The sections render in this order:
1. Breadcrumb "today › practice › feedback › {attempt ULID}" and "grader_tier {n} · {source}".
2. Strips: "provisional grade…", "manual review recommended: {reason}", "{n} tutor questions counted as hints".
3. A card with:
   - the LO title, raw item id and mode;
   - **CardControls**;
   - **ScoreBlock** "3 / 4 · partial credit · grader_confidence 0.82 · FSRS rating good · next due tomorrow, 09:00";
   - cold-check and auto-primed banners;
   - **Rubric · criterion evidence**;
   - a duplicate **Attempt · criterion trace**;
   - fatal errors and the tutor note.
4. Clarification "One question" (provisional grade).
5. **Causal feedback**: about 10 sub-panels, all expanded, ending in "decision · {probe decision} · {reason} · causal_p2_v1", "authorized repaired trace", and "does this diagnosis fit?" with 5 buttons.
6. **Diagnosis**: a misconception card ("consistent with confusing {facet_slug} and {facet_slug}") plus ClaimSurface plus "repair this →", or an unresolved-cause card.
7. **Regrade**: "This is a ledger fact, not a request for your verdict."
8. **DiagnosisCard** (async, polled every 2.5 s): "analyzing your pattern…", then 5 verdict taps. The component notes that they are used only for evaluation.
9. "One question, unaided".
10. "Error attribution": severity, scope and abstention.
11. Guided redo.
12. "Review the source" ("the retry is scored as source-fresh (primed) evidence").
13. **"Belief update"**: "mastery estimate · posterior update · logit-space Kalman update" with bell curves, "bayesian 1.42 nats > τ 0.90", and the evidence weight factors.
14. "What's next": a diagnostic follow-up gate card, and "Schedule — FSRS · good / retrievability target 0.90 / FSRS interval factor 0.85".
15. Key bar: "n / ↵ next · r regrade · ⇧D force follow-up · a add error · j add note · o open notes · ? ask tutor · esc / b back".

**What Feedback never shows:**
- the question;
- the learner's own answer;
- the expected answer.

**There is no clickable Next.** Key-bar labels are not buttons (`components/term.tsx:722-752`). A mouse user has to click the breadcrumb "today", then "continue ↵".

**The diagnosis is asked about up to four times,** each in different words:
- CausalFeedbackPanel;
- ClaimSurface;
- UnresolvedCauseCard;
- DiagnosisCard (plus "was this repair useful?").

**Competing next actions:** "repair this →", "start the fix", "[t] try another question", guided redo, "One question, unaided", "Take the quick check / Teach me now / Not now", "⇧D force follow-up", "r regrade" and "a add error".

### A.5 Review (R), Repair (RP), Exam (E)

**Review** (the learner-model "diff").
- It is reachable **only** through the palette command `diff`. In the palette, `review` prints the raw queue instead.
- Its stat strip: "KNOWLEDGE LEDGER · … active hypotheses · ▲ predictions up".
- "Working hypotheses" cards carry about 8 controls each: raw LO id, "priority 0.73", ClaimSurface, "MECHANISM", "repair this →" and facet links.
- The change history auto-expands on any scroll.
- Viewing the screen writes claim presentations.

**Repair.** From Feedback it takes 4 clicks: repair this → show me the sources → prime a related item → practice this. Two of those are gates where the learner has no choice to make.
- **The hold panel** shows: "WHY WE ARE NOT REVIEWING THIS YET … ASSISTANCE USED 35% of 50% … decision · defer machine checks · incomplete repair mapping · causal_p2_v1".
- **Source links** go to OpenInSource, which shows `bbox` and `block anchor`.

Repair has three bugs:
- It shows "starting repair…" forever if start fails.
- Closing it doesn't return to Review.
- The probe path drops the item when there is no session.

**Exam.**
- It is reachable only from GoalBanner, which the plan view doesn't show.
- The header reads "Practice exam · 3/20 · no hints · no tutor · answers are final". Esc exits with no confirmation.
- `finish_exam` grades the leftover answers sequentially under a static "Scoring exam…".
- The report shows "we projected 64% — you scored 72%", "calibration (Brier): 0.123 — lower is better", and a per-facet table keyed by raw ids.

**Golden Path** is unreachable (`SHOW_GOLDEN_PATH=false`), and it is a state-machine debugger.

### A.6 The core loop, counted

Starting from a new vault with content and AI connected:

| Step | Action | Round trips | Synchronous LLM | Wait copy |
|---|---|---|---|---|
| Open | lands on Start | ≈6–7 | conditional: startup regrades (unbounded) | "Loading LearnLoop vault" |
| Begin | click 1 (or ↵) | 2 | no | "starting…" |
| Practice load | none | 2 | no | "Verifying diagnostic safeguards..." |
| Submit | click 2 (^↵) | 3 | **yes** (≤180 s) | "grading attempt..." |
| Feedback | none | ~6–9 plus a poll every 2.5 s | no (async diagnosis) | "loading feedback…", "analyzing your pattern…" |
| Next | `n`/↵ only. Mouse: click 3 (breadcrumb) plus click 4 ("continue ↵") | 1–2, each able to block **≤10 s** on pending diagnoses | no | "opening next…" |

**Per item:**
- a keyboard user needs 2 actions;
- a mouse user needs 3 clicks, plus 1 at each block boundary;
- about 12–15 serialized round trips;
- one synchronous model wait.

**Without AI,** each item needs +1 click and N numeric inputs, with no reference answer shown.

**At session end,** a full-screen HUD shows fake telemetry ("LL//RUNNER", "LOG #nnnn", "K-12", a timer counting 0→100%) and swallows every key until it is dismissed.

### A.7 Clean patterns to keep

- `DailyPlanView`
- `ItemPresentation`
- `PlanReadingBanner`
- The server-written `CausalRepairStatus` messages
- `GoalReviewCard`'s single decision
- DiagnosisCard's "You've made this mistake before" block

## Part B. Navigation, knowledge views, review queues and settings

Paths are relative to `apps/learnloop-tauri/src/`. Code was read at `57d31c63`, not run. Judgments are marked **[judgment]**; everything else is quoted from the code.

### B.0 The shell

**Tabs.** `components/ui.tsx:13-24`, each rendered as `[key]Label`:
- `[1]Start`, `[2]Today`, `[3]Graph`, `[4]Ingest`, `[5]Proposals`, `[6]Registry`, `[7]Library`, `[9]Reader`, `[0]Maintain`.
- `[8]Golden Path` is hidden by `SHOW_GOLDEN_PATH = false`, because it is "structurally broken end to end".
- No tab depends on dev mode.

**Badges** show as a dim `·N`:
- Proposals counts pending proposals.
- Maintain counts unreviewed probe candidates, open source conflicts, action-needed notices and pending grading clarifications (`handlers/app.py:137-142`). Its docstring calls these "what is waiting on the learner".

**Right side of the bar:**
- A vault chip, with tooltip `"{root} · click to switch vault"` and the menu item `"+ add a new vault…"`.
- A settings chip, `[gear] [Alt+S]`. It is green or red according to *every* routed provider (`App.tsx:397-402`).

**Keys:** `Ctrl/⌘+P` or `:` opens the palette, `Alt+S` opens settings, `Alt+0–9` picks a tab. The last tab is written to `localStorage` but never read back, so every launch starts on Start (`App.tsx:81`, `:338`).

**Overlays:** Settings, the review/`diff` ledger, the inspector, Ask, OpenInSource, QuickAdd, NewVaultWizard, Repair, ExemplarConfirm, WhyDiagnosis, Adjudication, the session finish HUD and the palette.

**Screens that replace the body:** Exam, Golden Path and Calibration.

**Startup:**
- While loading: `"Loading LearnLoop vault"`.
- On failure: the raw message, then `"retry vault load"`.
- Screen errors become toasts showing the raw `error.message`.

**Command palette.**
- Its title is `learnloop shell`. It has 31 commands (`CommandPalette.tsx:54-91`).
- 18 of them, and any unknown word, go straight to the Python CLI through `run_cli_command`. So the in-app branches for `proposals`, `propose`, `ingest`, `accept`, `reject` and `init` can never run.
- Flags are at engineer level (`--target-items-per-lo`, `--dry-run`, `--json`).
- It is the only way in to calibration, the change ledger (`diff`), adjudication and `doctor`.

### B.1 Graph (`GraphScreen.tsx`, `components/graphedit`)

**Default view.** A toggle `concept map | knowledge field` opens on the concept map every visit. Below it:
- A layered DAG of concepts, each with its type (`concept|procedure|skill|misconception`).
- A detail pane: raw concept id; `← prereq` edges that show **raw ids, not titles**; and `Learning objects · mastery estimates` with mastery to 2 decimals.
- A `State` block: `practice items N` and `open error events N`.
- A legend: `edge types: prereq | confusable | related | part_of` and `N concepts · N edges · N misconceptions`.

**Adding one edge (edit mode)** takes about 6 clicks and a tab switch:
1. Arm a node, then pick a second node.
2. Pick a type.
3. Type `rationale (required)…`.
4. Click `preview geometry`, which shows `stress: 0.1234 → 0.1301`.
5. Click `file edits`, which answers `✓ filed batch {batchId} — review & accept it in the Proposals screen [5].`

**Empty state:** an empty grid, `0 concepts · 0 edges · 0 misconceptions` and `no concept selected`. There is no call to action.

### B.2 Knowledge field (`KnowledgeMapScreen.tsx`)

**Reaching it.** Graph → `knowledge field`. The default mode is **terrain**, and the mode resets every visit, so the Well is three clicks away each time.

**Header:** `knowledge-map · N facets · M concepts`, `view: terrain | well | strata`, and `stress 0.xx`.

**Footer, shown in every mode:**
- `[lock icon] locked facet`
- `locked = history is significant; unlocked facets still merge/split cheaply`

**Side panel `FacetFieldDetail`:**
- The raw facet id.
- `Demonstrated NN%`, `Ready NN%` and `Ready before decay NN%`.
- `Ready variance 0.0123` and `evidence mass 1.23`.
- `absent · no blueprint`.
- `Next · Cross the active recipe bottleneck`.
- `regrade correction +0.12`.
- A capability rim, `candidate causes`, and `Used by` with raw LO ids.

### B.3 The Well (`KnowledgeWellView.tsx`): what it encodes

**Geometry.**
- Spokes are sorted by id.
- Depth = `ready × evidenceMass/(evidenceMass+1.2)`.
- Untested, absent and held-flat facets are flat.
- Six dashed amber contours "bunch at the frontier".
- The view auto-rotates about once every 2 minutes while idle (`wire3d.ts:76`).

**Beads at r = 0.52:**

| Bead | Means |
|---|---|
| filled green | demonstrated |
| hollow cyan | predicted, not demonstrated |
| hollow amber in a dashed amber ring | instructed — cold check pending |
| faint × | absent, content debt |
| dashed diamond | held flat: not enough history |
| grey outline | untested |
| dashed purple | assumed (not tested) |
| dashed amber ring | locked |
| dashed cyan ghost ring | relaxing after decay |

**Labels.** Rim labels are **raw facet ids** split at underscores (`:690`). Every untested facet carries an `untested` sub-label.

**Caption (always shown):** "deep = likely recall (weighted by evidence) · filled bead = demonstrated · flat = unexplored frontier".

**Legend:** `depth = Ready × evidence · flat = unexplored`, `● filled bead = Demonstrated`, `○ hollow = predicted, not demonstrated`, `◌ ghost ring = relaxing after decay`, `◇ dashed = held flat, not enough history`, `× means no blueprint, not failure · contours bunch at the frontier`. It never explains purple (assumed), the amber lock ring or the selection colour. Amber means five different things.

**Clicks.** Clicking a bead pins it and opens the inspector on the facet's first LO.

**What it can answer at a glance [judgment]:**
- *What do I know?* Partly. Ids and rotation get in the way.
- *What's next?* No. `nextGap` is never drawn in the Well.
- *What's slipping?* Barely. There is a faint ghost ring, and `crosses target in ~Nd` appears only in a tooltip.
- *First run:* a flat disc of grey spokes, each labelled with an id and "untested". It reads as broken.

**Dead copy.** The Well's own empty state, "no facet field yet — the fabric is flat until evidence gives it mass", never shows, because the parent's `no mapped evidence yet` check runs first.

### B.4 Terrain and Strata

**Terrain.**
- Two sheets, demonstrated and ready, diffused over the recipe graph.
- Facets have **no text labels**.
- A △ marks the "model-selected Next gap".
- Legend: `rim: solid certified · hollow required`.

**Strata.**
- Rows are shortened raw LO ids. Group headers are shortened raw concept ids.
- The gutter shows `0.62 ±0.11`.
- The side panel shows `p(correct)`, `difficulty`, `variance`, and nearest items as `sim 0.83` (mean-centred cosine).

**Recommendation:** both go under the hood as analyst views.

### B.5 Inspector, FacetInspector, KnowledgeModel and ClaimSurface

**InspectorOverlay** opens from bead clicks, id links and `show`.
- Footer: `CLI mirror · learnloop show {id}`.
- Section names are database tables: `learning_object_mastery` and `practice_item_state` (stability `12.3d`, retrievability `0.83`).
- "Why this is in the queue · scheduler_explanations" shows `priority = Σ wᵢ · componentᵢ`, `diagnostic_eig` and a Fisher-information tooltip.
- Probe episodes show `ΔH +0.123` and `entropy 1.234 → 1.111`.
- It shows the **expected answer and rubric**, which spoils the question.
- It has an editable recipe editor ("rationale (required)", "file proposal →").
- `PlacementControls` (`✓ I know this · ✗ I don't know this · ? Check what I already know`) is the one learner-useful part, and it is buried here.

**FacetInspector** has a semantic contract, a ledger and `merge into… / propose split…`. It calls the same field "Ready-ghost (before evidence)" that other screens call "Ready before decay".

**KnowledgeModel.** On older vaults it says "Capability grid is available for mvp-0.7 vaults; this vault keeps the facet radar."

**ClaimSurface.** Every focused row on Today carries `Scheduler choice`, `selected rationale`, `policy · {provenance}`, and "was this queue choice useful?" with six buttons and a dismiss. The learner is asked to label the system.

### B.6 Proposals (`ProposalsScreen.tsx`)

- Hero: `proposals · AI inbox`, `local app-server · revision abc1234 · ai:{provider} ● ready · every change routes through this inbox — providers never write files`.
- Item rows show the raw entity id and a raw route pill: `auto_apply / review_required / reject`.
- The detail pane shows the payload as raw key/value lines, validation (`✓ schema · refs resolve · no id collision`) and origin (`agent_run`, `model`, `codex revision`).
- Items are accepted one at a time. Bulk-accepting `auto_apply` exists only as `Shift+A`, with no button.
- Empty state: "No proposals yet. AI authoring runs land here for review before anything touches the vault."

### B.7 Registry (`RegistryReviewScreen.tsx`)

- It always opens on `— pick a subject —`.
- `measurement rank: N independent dimension(s) / N facet(s) declared · ratio 0.42 · rank deficit N`.
- Identifiability warnings (`coarsen_distinction`).
- Facet cards listing preconditions, postconditions, examples, non-goals, error signatures and repairs.
- `propose merge` leads to "Merge review item created → review in Proposals."

**[judgment]** No learner need. This is quality assurance on the content model.

### B.8 Diagnostic check complete (`DiagnosticReviewScreen.tsx`, `ProbeBlockResult.tsx`)

- "Here's what we found for {LO} — nice work."
- A raw status pill and a raw `completionReason` (`converted_to_tutoring`).
- `next: tutoring on the diagnosed gap`.
- "Feedback withheld during the block, released now:", followed by `observation 1` and raw fatal-error codes in red.
- The primary action is on **Esc**.

### B.9 Calibration and the quick check (`CalibrationScreen.tsx`)

**Reaching it.** Only from the palette (`calibrate <goal_id>`) or the inspector. Both refuse to run without a session ("start a session first").

**The calibration view:**
- Buttons labelled with raw ids: `↵ Practice next target · {practiceItemId}`.
- `{loId} · {selectionObjective} · entropy 1.23 nats`.
- Episodes listed as `in_progress / complete / converted_to_tutoring`.

**The quick check:**
- `Check what I already know · 2/5 questions · optional · results at the end`.
- Results show raw practice item ids.

### B.10 Maintain (`MaintenanceScreen.tsx`)

The screen runs top to bottom in this order:
1. **Measurement & causal health**, about 40 blocks: "Stages 0–6 + inference precheck", "Efficiency scoreboard", "A6 opportunistic trace evidence · §3.A6 revert criterion", "A8 clarification rate", "Wave 4 inference precheck · B1 dominance", "Delayed held-out cold probes · certification §5.7", "Persona realism validity", "D2 facet mint gate", "D3 integration backfill", and "Causal probe review", which asks `window.prompt("Reviewer name?")`.
2. **The maintenance feed.** The generic notice action button has no `onClick` (`:309-311`).
3. **Update study map** ("bounded affected-neighborhood append").
4. **Open conflicts.** Notation mapping uses `window.prompt` twice.
5. **Exam readiness**, last: `Predicted exam score N% ± N%`.

The badge counts things that cannot be cleared on this tab.

### B.11 Settings (`SettingsScreen.tsx`, `ChatGPTPlanSettings.tsx`, `NativeMediaSettings.tsx`)

There are 9 sections, in this order:
1. AI models: 5 routes × provider plus model slug.
2. Embeddings (read-only).
3. Decision models (read-only).
4. OpenRouter key.
5. ChatGPT plan. Signing in does **not** route anything by itself; the hint says to edit `learnloop.toml`.
6. Ingestion: PDF engine, native fallback, audio mode, per-provider modality checkboxes, transcription provider, model, URL and key.
7. Animation.
8. Token budgets: `inventory input/output`, `synthesis shard in/out`, `synthesis total in` and provider limits.
9. Appearance: palette.

That is about **28 editable controls plus N modality checkboxes**. Only three serve the learner: connecting AI, choosing AI grading or self-grading, and appearance.

### B.12 SqliteBrowser

It opens from the Library tree on any `.sqlite` file, **including the live `state.sqlite`**. It offers row editing, row insert and delete, and an `sql console`.

## Part C. Reader shell, components, copy, errors and keys

Paths are relative to `apps/learnloop-tauri/src/`. I read the code at `57d31c63` and did not run it. The inside of the Reader belongs to `ux_reader_workbench_v1.md`; this part covers only how a learner gets in, how they get out, and what the shell shows around it.

### C.1 Entering and leaving the Reader

`ReaderScreen` takes only `onError`, `initialSource` and `onSourceChange` (`ReaderScreen.tsx:227-236`). It cannot send the learner anywhere else.

**How a learner gets in:**
- **The `[9]Reader` tab.** It resumes the last open source, or shows the picker.
- **Today's seeding empty state:** "Your study map is ready." / "Start reading — practice builds itself as you complete sections." / **"open the reader →"** (`TodayScreen.tsx:841-858`). It appears only when there are learning objects and no practice items, and it opens the picker rather than a book.
- **A reading step in the daily plan** (`App.tsx:494-509`). This opens the right span and adds `PlanReadingBanner`: "Reading for today's plan · {section} · about N min (of N)", with **"Back to today's plan"**.

**Places that cannot open a book:**
- **Ingest.** Its rows offer "outline & select →", "＋ collection" and "✕ delete". There is no *read*.
- **The wizard.** It ends on Ingest with "Study map building — track it in Ingest".
- **Feedback.** Its "view in Library" opens the raw vault file, not the passage.
- **`OpenInSource`.** This is a second, read-only source viewer, showing `pdf_text`, `block anchor {spanId}` and `bbox [x, y, x, y]`. It has no *open in Reader*.

**How a learner gets out.** "← library" is the only exit, plus "Back to today's plan" during a plan step. The plan banner disappears as soon as the learner switches tabs (`App.tsx:100-103`). A bare Alt press clears the selection (`:1418-1433`), so `Alt+digit` throws away a capture that is in progress.

### C.2 The Reader picker

**Header and cards:**
- "READER · LIBRARY", then "Pick up where you left off, or open something new." The cards show no last-read marker, so nothing backs that promise.
- Each card shows the title, "read →" / "watch →" and "{unitCount} sections".
- Only `ready` sources appear. Everything else collapses into **"{n} sources are still getting ready."**, with no names and no progress (`:1979`).

**Empty states:**
- No sources: "no ready sources yet — ingest a source in the Ingest tab, then return here to read it."
- Backend down: "the sidecar is unreachable — only the offline demo chapter is available."

**The flash on every first open.** Until settings load, the picker shows "the reader is disabled in this vault's config (new vaults have it on by default). Set `tutor_qa.reader_enabled = true` in learnloop.toml…", and the cards are greyed out. The cause is `contract?.readerEnabled ?? false` (`:620`).

**The demo chapter is always offered:** "open demo chapter (fixture)" / "offline demo — captures are not persisted."

### C.3 Waits after opening

These run in the background after a source opens:
- "◐ connecting this source to your learning path…"
- "◐ loading original PDF…"
- "◐ preparing video and synchronized transcript…"
- "◐ writing a quick check for this section…". This polls every 4 s up to 45 times (about 3 minutes), then **disappears silently** (`:792-818`).

Every open also retries saved requests that never started, and raises red toasts: "{n} saved Reader requests are still waiting to start."

### C.4 The rail and the selection

**The rail** has three tabs: GUIDE, ASK and NOTES. When a quick check is ready, Guide blinks "◆ N".

**On every selection, NOTES offers 12 actions in five groups:**
- Highlight
- EXERCISES: "add exercise to practice"
- REQUEST · ANSWERED IN BACKGROUND: research this / worked example / explain differently / why this matters
- REMEMBER LATER: test me later / help me remember / connect it
- MARK: mark confusing / not worth remembering

**On top of those:**
- "write my own question".
- A right-click menu with 5 more actions, which overlap the ones above.
- A raw span id: "selected · {spanId}".

**Nine verbs feed the same scheduler:** "add exercise to practice", "add to practice →", "save for practice", "test me later", "help me remember", "keep developing", "check once later", "keep it" and "deepen when I'm ready". **None of them opens practice.**

**There are two different Asks.**
- The Reader's ASK tab shows its mode as a raw enum: `answer_directly`.
- The global "learnloop ask" overlay is where Reader questions continue once they reach Today.

### C.5 Components that leak internals onto learner screens

| Component | Where it shows | What leaks |
|---|---|---|
| **GoalBanner** | Today, whenever a goal exists | Facet-id pills; "certified · examined · untouched"; "trajectory · demonstrated + ready lanes"; "saved to your forecast ledger"; **TrackRecordView** ("pooled Brier", "calibration duel — matched attempts") |
| **InboxStrip** | First on Today, in every state | "Inbox · 0 [Include handled] · saved references, no practice started · Tutor subject", even when empty |
| **QuestionQueue** | | "review → primed attempt"; "ready: {pi id}"; "awaiting review: {patchId}"; "authoring: {stage}" |
| **SessionFinishHud** | | Fake telemetry ("LL//RUNNER · {code}", "LOG #nnnn", "FINALIZING //"); "▲ N facets demonstrated"; "misconceptions ✓N resolved ↩N returned"; "full changelog in review", although review is reachable only through `diff` |
| **GoalWizard** | | "advanced · explicit facet ids (comma-separated)", with placeholder `facet_…, facet_…` |
| **CardControls** | | "an harder variant ({srcWaypoint} → {tgtWaypoint})"; "this probe was good practice… diagnostic surface itself stays used up" |
| **CausalAttribution** | Feedback | "claim checked"; "authorized repaired trace"; "decision · {probeDecision} · {reason} · {decisionPolicyVersion}" |
| **KnowledgeModel** | Feedback and Today drawers | "facet evidence · immutable ledger"; "β(α, β) · independent evidence mass"; "banked credit"; "Capability grid is available for mvp-0.7 vaults…" |
| **AskOverlay** | | "learnloop ask" with raw context and id pills; "counted as hint"; "tutor answers are logged · never reveals the answer" |
| **CommandOverlayFrame** | Every overlay | Header "❯ learnloop {command}" |
| **EntityLink** | | Renders the raw id by default |

**Unreachable components:** ExemplarConfirmDialog, WhyDiagnosisOverlay, GoldenPathSetup and TriageDecisionAid.

**Dead code in the first-run wizard.** `NewVaultWizard` has `STEP_LABELS = ["vault"]`, and creating a vault closes the wizard, so steps 2–5 never run. That includes a usable tour of the tabs.

### C.6 Copy

**There is no copy module.** All copy is inline JSX across 125 files. The audit extracted about 4,100 user-visible strings with the TypeScript parser. These terms appear in visible strings (Golden Path excluded):

| Term | Count |
|---|---|
| facet | 108 |
| proposal | 66 |
| **vault** | **65** |
| learning object / LO | 45 |
| extraction | 34 |
| synthesis | 33 |
| probe | 28 |
| calibrat… | 19 |
| misconception | 17 |
| claim | 17 |
| certif… | 16 |
| cold | 16 |
| blueprint | 16 |
| primed | 10 |
| rubric | 10 |
| provenance | 10 |
| hypothesis | 9 |
| commission… | 9 |
| adjudicat… | 8 |
| registry | 8 |
| marker | 4 |
| reveal | 4 |
| projection | 4 |
| posterior | 3 |
| Brier | 2 |
| sidecar | 2 |
| lane | 2 |
| replay | 2 |
| mvp-0 | 1, plus dynamic "algorithm {version}" on Today |

**There are 113 raw snake_case strings.** Examples:
- On Today: `forgetting_risk × 1.00 + … probe_eig × 0.25`, "algorithm mvp-0.x".
- On Feedback: `grader_confidence`, `grader_tier`.
- In the Reader: `tutor_qa.reader_enabled = true`.
- On every practice card: the raw item id, the `practiceMode` pill and "codex grading".

**"vault" is the first noun a new user meets.** It appears in:
- "Loading LearnLoop vault"
- the vault chip
- "+ create a new vault ▸"
- "A vault is a folder LearnLoop owns: … the SQLite state behind them."
- errors: "Could not open that vault.", "Vault refresh failed: …", "The vault database is busy with another write…"

### C.7 Errors

**The toast.**
- Errors, notices and successes share one red, persistent toast that sits in the page flow (`styles/app.css:795`, `App.tsx:1143-1147`).
- About 108 of the 197 `onError` call sites pass backend text through unchanged.
- `retryable` is read in only three places. **No toast has a Retry button.**

**The catch-all.** Any unexpected backend exception produces "LearnLoop could not confirm whether this action completed. Check the current state before trying it again." (`learnloop_sidecar/server.py:24-27`). It appears even for reads, such as opening a source.

**Handler messages a learner can meet** (239 `SidecarError` messages exist):
- "No extraction resolves for 'src_…'."
- "The reader dialogue is disabled (tutor_qa.reader_enabled=False)."
- "Practice item pi_… has been retired and cannot be served."
- "Invalid params."
- "The frontend is newer than the running LearnLoop sidecar. Restart the Tauri app…"

**Gating toasts** turn a missing session into the learner's job:
- "Start a session before opening practice."
- "Begin today's plan on Start first."
- "Start a session first: the quick check runs inside a practice session."

### C.8 Keys

`app/keyboard.ts` defines no shortcuts. Each screen adds its own `window` listeners and its own key bar.

**Clashes:**
- The tabs are labelled `[1]…[0]` but the keys are Alt+digit, and on Today plain digits open queue rows.
- A bare Alt press clears the Reader selection.

**Vocabulary.** Vim keys, single letters, Ctrl chords and Alt are mixed, and there is no help overlay.
