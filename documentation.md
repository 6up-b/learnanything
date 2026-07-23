# LearnLoop user and algorithm guide

> Implementation snapshot: 2026-07-21 This guide describes the behavior present in the current codebase. It distinguishes supported behavior from legacy compatibility paths and work that is still in progress.

LearnLoop is an adaptive learning system. A learner supplies trustworthy source material, LearnLoop turns it into a reviewable study map and practice bank, and each answer updates several deliberately separate models:

- what the learner is likely able to do now;
- what they have directly demonstrated without help;
- when a particular item is becoming forgettable;
- which misunderstanding best explains a pattern of answers; and
- which eligible activity has the highest value right now.

The separation matters. A prediction is not a credential, a repeated near-clone is not independent evidence, a hint-assisted success is not the same as an unassisted success, and a wrong composite answer does not prove that every prerequisite is weak.

New vaults use the `mvp-0.8` knowledge model — a strict superset of `mvp-0.7`'s canonical shared-facet model that adds the authority-propagation projection. The older `mvp-0.6` and `mvp-0.7` models remain readable so historical vaults and attempts can be migrated and replayed safely. Statements below about "`mvp-0.7`" semantics (canonical facets, the projection as sole writer of shared state) apply unchanged under `mvp-0.8`.

## Quick start

This section is the shortest honest path from nothing to a working practice loop. Every step names the deeper section that explains it.

### Make a vault

A vault is a local directory holding your editable curriculum files, source artifacts, configuration, and a derived SQLite event store (section 4). Two ways to create one:

**CLI** (scriptable, recommended for the first vault):

~~~bash
learnloop init ~/LearnLoop/my-vault
learnloop add-subject linear-algebra "Linear Algebra" --vault ~/LearnLoop/my-vault
~~~

**Desktop app**: launch the app, and on the Start screen choose New Vault. The wizard creates the vault and an optional first subject, then hands off to ingest, proposals, and the goal wizard.

Either way you get `learnloop.toml` at `algorithm_version = "mvp-0.8"`, `state.sqlite` with all migrations, the vault-level registries, and `subjects/` and `rubrics/` directories (section 2). A subject is a curriculum view, not a separate learner model — create one per body of material you want to navigate and maintain together ("Linear Algebra", not "Chapter 3").

To open the app on your vault:

~~~bash
cd apps/learnloop-tauri
LEARNLOOP_VAULT=~/LearnLoop/my-vault npm run dev
~~~

If it opens the wrong vault, click the green vault path in the top navigation (section 3).

### Get a source in: Quick Add versus the deliberate path

Both paths run the same machinery — real library rows, real extraction runs, real unit inventories, an immutable manifest, the same quality gates. The difference is who makes the decisions.

**Quick Add** collapses everything into one confirmation. In the app: Source Library sidebar → "＋ create study map", supply a URL/arXiv ID/YouTube link/PDF path/text or caption file, pick the subject, optionally write a brief. From the CLI:

~~~bash
learnloop quick-add ~/Books/linear-algebra.pdf --subject linear-algebra --vault ~/LearnLoop/my-vault
~~~

Quick Add auto-chooses the defaults you would otherwise pick by hand: it imports if needed, suggests a role from the acquisition kind (PDF → `primary_textbook`), selects the whole source when it fits the configured token cap — otherwise brief-relevant units — and shows you one confirmation covering scope, role, token estimate, and external-AI use. Then it queues inventory plus synthesis with priority over bulk batches (section 7.8).

**The deliberate path** (bootstrap synthesis, step by step) is the same journey with you at each decision point:

~~~bash
# 1. Import: fetch bytes, register artifact + immutable revision, extract to the
#    Document IR, compute page health. Deterministic — no model calls, no egress.
learnloop import ~/Books/axler-3e.pdf

# 2. Inspect the outline (computed from the persisted IR; costs zero model calls)
#    and decide which chapters are worth learning.
learnloop source-outline src_axler_3e

# 3. Assemble a collection. Membership pins the revision and owns role and scope.
learnloop source-set create la-foundations --subject linear-algebra --title "LA Foundations"
learnloop source-set add la-foundations --source src_axler_3e --revision srcrev_ab12cd34 \
  --role primary_textbook --unit chapter_02 --unit chapter_04

# 4. Read the bill before paying it.
learnloop source-coverage la-foundations
learnloop build-plan src_axler_3e --subject linear-algebra

# 5. Synthesize the study map. --mode auto picks bootstrap for a first map,
#    append once a map exists.
learnloop synthesize la-foundations --mode auto --brief-file brief.json --apply
~~~

Use Quick Add when you trust the defaults and want one source learnable now. Use the deliberate path when unit selection matters (it is the main cost lever — a 900-page book scoped to five chapters only ever costs five chapters), when the role is not the obvious suggestion, or when you are assembling a multi-source collection (section 7.8–7.9).

### What is actually happening underneath

Mechanistically, either path runs this pipeline (sections 7.2–7.6):

1. **Import** fetches bytes, registers the work/artifact/revision chain, retains PDF originals in a content-addressed store, and extracts into the Document IR — ordered span-addressable blocks, units, assets, page health. Identical bytes reuse a revision; changed bytes create a new one. Fully deterministic, nothing leaves the device.
2. **Outline and selection** read the persisted IR. The outline, token estimates, and build plan are computed without any model call; the learner (or Quick Add's defaults) chooses the unit scope.
3. **Confirmation** is the egress boundary (section 7.7). It lists exactly which stages may call the configured external model and the estimated input.
4. **Inventory** runs per selected unit at the profile the source's role earns (an exam is inventoried for assessment signals only; a textbook for semantic + practice + assessment; section 7.5), producing deterministic span-cited candidates.
5. **Synthesis** persists an immutable manifest first, shards the unit inventories, allows the model one bounded round of exact span requests, and passes output through deterministic quality gates (registry identity, references, blueprint/criterion contracts, provenance, coverage, conflicts). What comes back is a dependency-annotated *proposal*, not a vault write. If a gate fails, the candidate is preserved and can be repaired and revalidated with zero model calls (section 7.6).
6. **Apply** writes concepts, canonical facets, LOs with blueprints/recipes (section 8), rubrics, and practice items under the vault mutation lock. If your brief chose `as you read`, the map ships with zero practice items and generation is triggered per section as you finish reading it (section 5, step 4).

All of it lands as a durable batch: queued work survives closing the app, failed batches resume, and token estimates and actuals are visible per stage in the ingest activity feed.

### The journey, end to end

1. **Create** the vault and subject (above).
2. **Ingest** a source and build a study map (above).
3. **Review the build**: accept/reject/edit proposals; check the Registry for facet claims and warnings; look at the Graph (section 5, step 3).
4. **Read** the source in the Reader tab — annotate, ask span-grounded questions, answer owner-placed reading questions, set per-section dispositions (section 5, step 4).
5. **Optionally create a goal** in Today's goal wizard when a deadline or scope matters, with an optional held-out exam pool (section 5, step 5).
6. **Practice** the loop below, day after day.
7. **Maintain**: review source updates, conflicts, and exam readiness in Maintain; review claims and repair episodes via the Review overlay and Repair surface (section 1).
8. **Optionally certify**: run a Golden Path run over one confirmed task family (section 17).

### The practice loop

One sitting looks like this (sections 5–6 walk it in detail; sections 9–13 explain the machinery):

1. **Start a session** with energy, sleep, and available minutes. Short sessions are not worse sessions; at or below 20 minutes, probes are suppressed when due work exists.
2. **Work the Today queue.** The scheduler serves the best-valued eligible activity: due items (FSRS forgetting risk), goal-frontier work, repair after recent errors, short diagnostic blocks, teach-back, transfer (section 13). `why <item-id>` shows the actual selection terms.
3. **Answer without hiding uncertainty.** Write and submit; use authored hints (they cost demonstration credit, not belief); say "I don't know" rather than fabricate; ask the tutor with `?`; write your own card with `w`; request an easier/harder sibling when an item misses your level.
4. **Use feedback as the next action.** Open the exact source span, ask the tutor in context, request a regrade, start a typed repair, or take a primed retry — which updates belief but never resets the cold-evidence clock.
5. **Finish.** The session HUD summarizes what happened; memory decay, goal projections, open errors, follow-ups, and diagnostic needs determine what returns tomorrow.

The invariant loop underneath every sitting:

`source → study map → read → attempt → feedback/tutor → updated evidence → next scheduled decision → later cold retrieval`

Every answer updates separate models — predicted ability, banked demonstration, item memory, error hypotheses — and the system never lets immediate fluency impersonate durable learning (sections 10–12).

## Feature lookup

Use this table as the task-oriented index to the current product. In the desktop app, `Ctrl/Cmd+P` or `:` opens the command palette and `help` lists its commands. At a terminal, `learnloop --help` lists every CLI command and `learnloop <command> --help` shows its arguments. Use your browser's find command on this guide for an exact command, screen, or model term.

| What you want to do | Main desktop surface | CLI or shortcut | Where it is explained |
|---|---|---|---|
| Create, switch, upgrade, or check a vault; choose an AI or manual grader | Start, green vault-path control, `ai:` menu | `init`, `upgrade`, `doctor`, `add-subject` | Sections [2](#2-install-and-create-a-vault), [3](#3-run-the-desktop-application), and [19](#19-provenance-replay-and-debugging) |
| Import a URL, arXiv paper, YouTube transcript, PDF, caption file, or local text; inspect extraction health | Ingest and its Source Library | `import`, `quick-add`, `ingest-batches`, `source-outline`, `repair-extraction` | Sections [5](#5-recommended-first-use-journey) and [7](#7-source-ingestion-v2) |
| Select source units, roles, and token scope; build or append a study map | Ingest, Create study map, Maintain | `source-set`, `select-units`, `source-coverage`, `build-plan`, `inventory`, `synthesize` | Sections [7.4–7.9](#74-outlines-units-and-token-budgets) |
| Review generated curriculum, provenance, duplicates, and source conflicts | Proposals, Registry, Graph, Library, Maintain | `proposals`, `accept`, `reject`, `show`, `maintenance-feed`, `resolve-conflict` | Sections [5 step 3](#step-3-review-the-build), [8](#8-the-canonical-knowledge-model-mvp-07--mvp-08), and [19](#19-provenance-replay-and-debugging) |
| Read source material, search within it, annotate a selection, ask about a span, answer reading checks, or choose a section disposition | Reader | Reader toolbar and `?` | Sections [5 step 4](#step-4-read-the-source-in-the-reader), [7.3](#73-document-ir), and [15](#15-tutor-teach-back-and-promotion) |
| Start or resume a bounded session and understand the Today queue | Start and Today | `today`, `review`, `why <item-id>` | Sections [5 steps 6–9](#step-6-start-a-session), [9](#9-what-happens-when-an-attempt-is-submitted), and [13](#13-how-items-are-served) |
| Practice, say “I don't know,” use hints, self-grade, write or edit a card, or request an easier/harder sibling | Today, Practice, Feedback | `attempt`, `card`, `questions` | Sections [5 steps 7–8](#step-7-answer-without-hiding-uncertainty), [10](#10-attempt-evidence-coverage-and-assistance), and [15.5](#155-save-or-promote-a-useful-exchange) |
| Inspect feedback, ask the tutor, regrade, save or promote an answer, and perform a delayed repair | Feedback, Review overlay, Repair | `ask`, `diff`, `show`, `misconceptions`, `resolve-error` | Sections [15](#15-tutor-teach-back-and-promotion) and [18](#18-surprise-errors-and-follow-ups) |
| Run bounded diagnostics or a declared calibration session and understand EIG, stopping, and grader reliability | Today diagnostic block and Calibration overlay | `calibrate`, `generate-diagnostics`, `probe-*`, `grading-*` | Sections [14](#14-diagnostic-probes-and-eig) and [19.4](#194-assessment-provenance) |
| Create a goal, reserve a held-out exam, inspect readiness/forecast/decay, or return after a hiatus | Today goal and exam overlays, Maintain | `exam`, `exam-readiness`, `overconfidence`, `reentry-summary`, `decay-pressure` | Section [16](#16-goals-exams-and-projections) |
| Run the exemplar-driven certifying journey, including baseline, triage, pattern ladder, rotating surfaces, cold assessment, and a next-depth invitation | Golden Path | Golden Path setup and run controls | Section [17](#17-the-golden-path-run) |
| Inspect replayable state, defaults, contracts, and algorithm behavior | Inspector, Review, Graph | `show`, `rebuild-derived-state`, `contracts`, `registry`, `surfaces audit` | Sections [8–14](#8-the-canonical-knowledge-model-mvp-07--mvp-08) and [19–20](#19-provenance-replay-and-debugging) |

## 1. Product status and compatibility

### Supported now

The current learner journey is:

1. Create a vault (CLI, or the in-app New Vault wizard).
2. Create one or more subjects.
3. Add sources to the vault-level source library.
4. Create a study map for a subject, or review a legacy authoring proposal.
5. Read the source in the embedded Reader, with span-grounded Ask and owner-placed reading questions.
6. Optionally create a goal and held-out practice exam.
7. Start a session with an energy and time budget.
8. Work the Today queue, including ordinary practice, repair, teach-back, writing your own cards, and short diagnostic blocks.
9. Use source-grounded feedback and the tutor, then repeat as memory decays or goals change.
10. Review claims, forecasts, and repair episodes in the Review/Repair surfaces; review source updates, synthesis conflicts, provenance, and registry issues in the maintenance surfaces.
11. Optionally run a Golden Path certifying run over one task family (section 17).

A fresh `learnloop init` writes `algorithm_version = "mvp-0.8"`. It does not require an immediate upgrade.

### Existing vaults

`learnloop upgrade` now carries a `--to` option that defaults to `mvp-0.8` and supports two ladders: `--to mvp-0.7` moves a legacy `mvp-0.6` vault onto the canonical shared-facet model, and `--to mvp-0.8` moves an `mvp-0.7` vault onto the authority-propagation projection. Activation is vault-wide and atomic. The command refuses to switch models when a facet-bearing item refers to an unregistered facet or a registered facet lacks its semantic contract. There is no mixed-version mode inside one vault.

The in-memory configuration fallback is intentionally still `mvp-0.6`. That fallback applies only when an old configuration omits `algorithm_version`; it prevents a legacy vault from silently changing inference models merely because the application was updated.

### Shipped: hypothesis surfaces

`spec_hypothesis_surfaces.md` (v3) is implemented. The learner-facing loop now includes:

- a typed claim contract and claim surface, reachable from Today, the goal banner, feedback, and the why-diagnosis overlay;
- a Review/Log surface, opened as an overlay from the command palette with `diff` — a GUI mirror of the learner-model change journey, not a navigation tab (`review` prints the current due queue instead);
- a typed Repair surface, launched from feedback's "repair this →" or from a Review hypothesis;
- a calibration screen and forecast track record; and
- a two-lane goal trajectory with aligned Demonstrated and Ready lanes.

There are no Errors or Doctor navigation tabs; the earlier placeholders were removed (CLI `learnloop doctor` remains the doctor surface). Claim telemetry still must not be treated as learner-model evidence — claims seed priors and route attention, never certification.

## 2. Install and create a vault

LearnLoop requires Python 3.12 or later. From a checkout:

~~~bash
python -m pip install -e '.[dev]'
learnloop --help
~~~

An alternative installation is:

~~~bash
uv tool install --editable .
~~~

Create a vault, add a subject, and validate it:

~~~bash
learnloop init ~/LearnLoop/my-vault
learnloop add-subject linear-algebra "Linear Algebra" --vault ~/LearnLoop/my-vault
learnloop doctor --fix-state --vault ~/LearnLoop/my-vault
~~~

The subject ID should be a stable kebab-case identifier. Its title is display text and can contain spaces.

`learnloop init` creates:

- `learnloop.toml` with an explicit `mvp-0.8` algorithm version;
- `state.sqlite` and all current migrations;
- vault-level concept, relation, goal, error, and facet registries;
- `subjects/` and `rubrics/` directories; and
- an `AGENTS.md` file describing the vault contract for authoring agents.

`learnloop add-subject` creates `subjects/<subject-id>/` with subject metadata, a note directory, learning-object and practice-item directories, and a subject concept-graph file. A subject is a curriculum view, not an isolated learner model: two subjects can refer to the same vault-level facet and share evidence about it.

For an old vault only:

~~~bash
learnloop upgrade --vault ~/LearnLoop/old-vault
~~~

If it refuses, run Doctor and complete the canonical facet registry before retrying. Do not edit only some subjects to a newer model; the model version is global.

## 3. Run the desktop application

The desktop app lives under `apps/learnloop-tauri` and requires Node/npm, Rust/Cargo, and the platform prerequisites for Tauri.

~~~bash
cd apps/learnloop-tauri
npm install
LEARNLOOP_VAULT=~/LearnLoop/my-vault npm run dev
~~~

The app starts the Python sidecar from the active Python environment. If it opens the fixture vault or another vault, click the green vault path in the top navigation and select the desired vault directory.

The desktop app can now also create a vault: the Start screen's New Vault entry opens a wizard that creates the vault and an optional first subject, then hands off to ingest, proposals, and the goal wizard for onboarding. The CLI remains the scriptable path. Creating the subject explicitly before ingestion makes the intended organization clearer.

The AI menu in the top bar reports and switches the configured grading provider. Manual mode is a supported fallback for ordinary practice. It is not sufficient for a qualifying diagnostic observation because a learner cannot independently validate a test whose purpose is to distinguish hidden hypotheses about that learner.

### AI providers

AI backends are configured per vault under `[ai.providers.<name>]` in `learnloop.toml`; the entries in that table are exactly the options the AI menu offers. Besides the Codex profile, two provider types speak to any OpenAI-compatible endpoint: `openai_chat` (explicit `base_url`, e.g. the bundled DeepSeek profiles) and `openrouter`, which defaults to `https://openrouter.ai/api/v1` and accepts **any OpenRouter model slug**:

~~~toml
[ai.providers.openrouter]
type = "openrouter"
model = "anthropic/claude-sonnet-4.5"   # any OpenRouter slug
api_key_env = "OPENROUTER_API_KEY"
response_format = "json_object"          # or "json_schema" on supporting models
~~~

API keys are never written to `learnloop.toml`; the profile names an environment variable, and the key is read from the shell environment, the vault-local `.env`, or `~/.config/learnloop/settings.env` (in that precedence order). Switch every AI task to a provider with `LEARNLOOP_AI_PROVIDER=openrouter`, set `active_provider = "openrouter"` in `[ai]`, or mix providers per task via `[ai.routing]` — `canonical_ingest` also covers unit inventory, study-map synthesis, and append reconciliation, so a vault can, for example, keep Codex for synthesis while OpenRouter grades practice. Most CLI commands accept `--ai-provider <name>` for a one-off override.

### The Settings tab

The gear chip (`⚙ [Alt+S]`) at the far right of the tab bar — green/red for AI ready/unready — opens the Settings screen, which persists everything above without hand-editing TOML:

- **AI models** — the active provider plus per-use-case rows (grading, ingest/synthesis, tutor, animation). Picking OpenRouter for a use case takes any model slug and materializes a dedicated `[ai.providers.openrouter_<usecase>]` profile, so different tasks can run different OpenRouter models. Grading also offers manual (self-grade) mode.
- **OpenRouter API key** — saved (masked) to the machine-global `settings.env`, never the committed vault config, and applied to the running process immediately.
- **Ingestion** — the native-multimodal toggle and the transcription provider: `openai-compatible` (any `/audio/transcriptions` endpoint — model, base URL, and its own API key) or `openrouter` (an audio-capable model slug transcribes via chat `input_audio`, mp3/wav only, reusing the OpenRouter key above).
- **Appearance** — color palettes: the default terminal look, dracula, gruvbox, nord, and catppuccin-mocha. The choice is per-machine (localStorage) and applies instantly.

### Audio sources

Local audio files (`.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`, `.opus`, `.aac`) ingest like any other source (Ingest tab, Quick add, or drag-drop). By default the file is transcribed by the OpenAI-compatible `/audio/transcriptions` endpoint configured under `[ingest.audio]` (OpenAI whisper, Groq, or a local faster-whisper server; the key comes from the env var it names). Setting `provider = "openrouter"` under `[ingest.audio]` (or picking openrouter in the Settings tab's transcription row) instead sends the audio as chat `input_audio` parts to the configured `transcription_model` slug — the model must accept audio input, only mp3/wav apply, and the machine-global OpenRouter key is reused, since OpenRouter has no transcriptions endpoint. Either way the transcript keeps per-segment timestamps, so outline units, reader locators, and provenance work exactly as they do for YouTube captions. Audio always leaves the machine, so the import consent card lists it before anything uploads.

### Native multimodal ingestion

With `[ingest.native] enabled = true` and the routed provider's profile declaring `input_modalities` (e.g. `["audio", "pdf"]` on an OpenRouter profile), media is ingested by the chat model itself instead of the local pipeline: audio is sent as `input_audio` content parts and returns a timestamped transcript; PDFs (set `engine = "native"` under `[ingest.pdf]`) are sent as file parts and return Markdown. Off by default; when the native route can't run, audio falls back to the transcription endpoint and native PDFs fail with a typed error rather than silently switching providers.

### Explainer animations

Each concept's inspector has an "Explainer animation" section. Generating one sends the concept description to the `[ai.routing] animation` model, which writes a Manim Community Edition scene; the code is validated against an import/builtin allowlist and rendered locally by manim (`pip install "learnloop[animation]"`), then plays inline. Every generation requires an explicit consent click because AI-written code executes on your machine. On Linux the render runs inside a mandatory [bubblewrap](https://github.com/containers/bubblewrap) sandbox — no network, read-only system and interpreter mounts, a throwaway scratch directory as the only writable path — and rendering refuses with an install hint if `bwrap` is missing. On macOS/Windows (no bubblewrap) the render falls back to the constrained subprocess (temp directory, timeout, minimal environment); there the AST validation is hardening, not a guarantee. Failed generations keep the scene code and renderer output for debugging, and one automatic repair round-trip is attempted. Configuration lives under `[animation]` (quality, timeout, LaTeX availability, kill-switch).

The command palette opens with Ctrl/Cmd+P or `:`. Useful commands include `today`, `ask`, `review`, `why <practice-item-id>`, `show <id>`, `attempt <practice-item-id>`, `calibrate [goal-id]`, and `doctor`. Alt+1 through Alt+8 switches the first eight navigation tabs.

## 4. The mental model

| Term | Meaning |
|---|---|
| Vault | The local directory containing editable curriculum files, source artifacts, configuration, and a derived SQLite event/state store. |
| Subject | A curriculum view such as linear algebra, organic chemistry, or a certification exam. It owns study-map organization, not private copies of shared knowledge. |
| Source | A registered work/artifact/revision/extraction chain in the vault-level source library. |
| Source set | A subject-specific collection of pinned source revisions. Membership owns the source role, selected unit scope, and priority. |
| Study map | The synthesized concepts, canonical facets, learning objects, rubrics, practice items, provenance, and conflicts for a source set. |
| Concept | A navigational or domain entity, such as eigenvalue or Bayes' theorem. |
| Facet | One atomic, assessable claim, such as “a real symmetric matrix has real eigenvalues.” Facets are canonical and vault-wide. |
| Capability | What the learner must do with a facet: retrieval, schema interpretation, procedure execution, method selection, or coordination. |
| Learning Object (LO) | A performance target defined by one or more blueprints and valid requirement recipes. It is not merely a note heading or a single scalar skill. |
| Blueprint | One representative performance an LO stands for — a weighted description of a task shape, satisfied through one or more recipes. |
| Recipe | One valid method of satisfying a blueprint: a conjunctive set of facet-capability components, optional alternative (`any_of`) components, and an optional explicit integration component. |
| Task blueprint | Distinct from an LO blueprint: the golden path's human-reviewed, immutable, content-addressed contract for one chapter/unit and one target task family (section 17). |
| Practice Item (PI) | A prompt plus expected answer, rubric, evidence fingerprint, allowed attempt types, and links to an LO. |
| Assessment contract | The immutable snapshot of an item's prompt, rubric, targets, dependencies, and surface identity at presentation time. |
| Attempt | A persisted learner answer and its grading evidence. Derived state can be replayed from attempts without calling an AI provider. |
| Goal | A target recall over a concept/facet scope, optionally with a deadline and held-out exam pool. |
| Diagnostic episode | A bounded sequence of measurements over a locked set of explanations for uncertainty. |
| Ready | A model-based prediction of expected performance. |
| Demonstrated | Banked, capability-matched, bounded credit from direct or embedded unassisted evidence. |
| Depth rung / waypoint | One closed cell of a difficulty trajectory: a capability plus task-feature bounds (complexity, transfer, response, scaffolding, span). Generation targets a rung; item difficulty is calibrated within it. |
| Golden path run | A narrow end-to-end certifying run over one confirmed task family: baseline, triage, ladder instruction, rotating practice, one cold held-out assessment, and a confirmed next-depth invitation (section 17). |

## 5. Recommended first-use journey

### Step 1: create a subject with a meaningful boundary

Use one subject for material that should be navigated and maintained together. Subjects do not need to be microscopic. “Linear Algebra” is useful; “Chapter 3, page 41” is not.

Use separate subjects when the curriculum, goal, source collection, or maintenance workflow should be distinct. Shared canonical facets still prevent evidence duplication across those subjects.

### Step 2: choose an authoring path

The Ingest tab is now one merged surface with no sub-tabs: the Source Library sits in the left column, and the main area is a single paste field with a two-mode chip toggle — "canonical source" and "exam seeding." There are three current paths.

#### Recommended: Create study map

In the Source Library sidebar, choose "＋ create study map." Supply:

- a URL, arXiv ID, YouTube URL, PDF path, webpage, or local text/Markdown file;
- the target subject;
- an optional learning brief; and
- confirmation of source role, selected scope, token estimate, and any external-AI use.

The brief starts with intent:

- general learning: build understanding across the selected material;
- reference mastery: retain essentials while keeping the source useful for lookup;
- exam prep: build toward a recall target and deadline.

You can then choose introductory, standard, or deep coverage; include or exclude topics; state a level or notation preference; and, for exam prep, provide goal parameters. The brief also asks for a starting level (`new to this`, `some exposure`, `comfortable`, `strong background`), which seeds a global learner claim (section 11.1), and lets you choose when practice items are generated: `upfront`, or `as you read` — the items-off bootstrap, where the map ships with zero practice items and completing a guide section triggers generation for the learning objects that section supports.

If the source is new, LearnLoop first imports and locally extracts enough structure to plan it. Planning the outline and selected units is deterministic and consumes no pedagogical model calls. The single confirmation covers the selected scope, role, token estimate, and configured external-AI inventory/synthesis work.

After confirmation, a durable priority batch inventories the selected units and synthesizes the study map.

Section 7.8 walks the same journey command by command, including the deterministic import, outline, and build-plan stages that run before any pedagogical model call.

#### Import only, then inspect

The main paste field in "canonical source" mode performs fetch → extraction → durable registration as a v2 batch. It accepts a URL, arXiv ID, YouTube link, PDF path, or a local `.md`/`.txt`/`.vtt`/`.srt` file. It does not by itself promise a study map. Use it when you want to inspect the source card, extraction health, outline, or unit scope first. On a ready source card, choose “outline & select →” to build a plan.

This distinction prevents a common mistake:

- The paste field means “put this source in my library.”
- Create study map means “use this source to build learnable curriculum for this subject.”

#### Exam seeding

The "exam seeding" mode chip on the Ingest screen runs practice-exam ingestion — the surviving use of the legacy one-shot pipeline. There is no longer a separate "Add Source" sub-tab or general canonical-ingestor proposal path; canonical import is always the durable v2 batch.

### Step 3: review the build

Use Batch progress to see the durable job ladder. Batches can be queued, running, waiting for input, completed, failed, blocked, or cancelled. Failed and cancelled batches can be resumed. Token estimates and actual usage are shown by stage.

Then review:

- Proposals for items requiring accept, reject, edit, or validation refresh;
- Registry for facet claims, applicability conditions, examples, non-goals, error signatures, repairs, and identifiability warnings;
- Graph for concepts, LOs, evidence state, and provenance, including the three-mode knowledge-map visualization (terrain / well / strata; the well view bends a spacetime-style fabric by ready-mastery weighted by evidence visibility);
- Library for source and learner notes; and
- Maintain for source-set append, conflicts, update notices, and exam readiness.

Synthesis is review-by-exception. Identity-sensitive changes, semantic conflicts, and ambiguous merges should remain proposals. The system must not silently merge two facets merely because their wording looks similar.

### Step 4: read the source in the Reader

The Reader tab is a reading front door: pick a ready source and read its rendered view in-app. For PDFs this is a real embedded pdf.js reader over the original bytes, with selectable text and find. While reading you can:

- select text to capture an annotation (persisted locally and durably before any model job);
- ask a span-grounded question in the reader tutor context, choosing an answer mode — answer directly, help me reason, or ask me first;
- answer owner-placed reading questions at section boundaries — always skippable, instructional-purpose, never certification evidence; and
- set a per-section disposition: comprehension only, check once later, keep developing, or reference only. The disposition routes follow-up work; it never writes evidence.

Under the `as you read` items mode, completing a guide section is what triggers practice generation for the learning objects that section supports. Today routes into the Reader when reading is the right next activity.

### Step 5: create a goal when a deadline or scope matters

Today contains a four-step goal wizard:

1. choose a title and concept/facet scope;
2. choose target recall;
3. choose a due date or an open-ended goal and review feasibility; and
4. optionally create a held-out exam pool and populate missing practice.

A held-out item is quarantined from ordinary practice so it remains an honest exam measurement. Imported past-exam outcomes are different: they enter as discounted historical `exam_evidence`, while a fresh held-out exam response uses full `exam_attempt` evidence mass.

A goal is optional. Without one, the scheduler can still serve due memory, recent errors, diagnostic needs, and boundary-fitting practice. A goal adds an explicit frontier and queue-composition constraint.

### Step 6: start a session

On Start, report energy, sleep quality, and available minutes. The UI uses these inputs to preview a queue size and sends energy and minutes to the scheduler. A short session is not a lower-quality session; it changes which work is practical. By default, sessions at or below 20 minutes suppress probe information gain when ordinary due work exists.

Starting a session persists a session record. Draft text, hints, and the current item are checkpointed so leaving the screen or restarting the app can restore the attempt.

### Step 7: answer without hiding uncertainty

During ordinary practice you can:

- write an answer and submit it for AI or self grading;
- use authored hints;
- choose “I don't know” instead of fabricating an answer;
- ask the tutor with `?` or the command palette;
- enter a teach-back conversation when that item is scheduled;
- write your own card (`w` on Today): author a practice item in your own words against a learning object you own, with a mode of short answer, free recall, explanation, or worked problem — it writes straight to vault YAML with no review gate and is schedulable immediately; or
- request an easier or harder sibling of an item (re-runging). The request itself records honest evidence: a scoped learner claim and a deterministic self-report attempt on the source item (section 11.1).

“I don't know” is useful evidence. It records full surface exposure but a default evidence mass of 0.7. Unaided it routes to a recall-failure mechanism; after help it routes to a scaffold-failure mechanism. A blank answer without the explicit choice is damped and marked for review.

Hints and substantive mid-attempt tutor questions reduce the independence of the result. They can help learning while earning less or no demonstration credit.

### Step 8: use feedback as the next action, not just a score

Feedback shows criterion-level evidence, fatal errors, error attribution, repair suggestions, source spans, and model traces. From there you can:

- open the exact source span;
- review a linked vault note;
- ask the tutor in feedback context;
- save a useful exchange as a note;
- request or perform a regrade;
- add a repair/error note; or
- try a source-fresh primed retry.

A primed retry updates belief with an item-difficulty offset because the source was just read, but it does not reset the cold-evidence clock. It therefore cannot masquerade as durable recall or delay the next spaced review.

### Step 9: finish and return later

The session finish HUD summarizes the work. Memory scheduling, goal projections, open errors, pending follow-ups, requested tutor-promoted items, and diagnostic episodes determine what returns.

The normal loop is:

`source → study map → attempt → feedback/tutor → updated evidence → next scheduled decision → later cold retrieval`

## 6. Three concrete examples

### Example A: learn linear algebra from a textbook

~~~bash
learnloop init ~/LearnLoop/math
learnloop add-subject linear-algebra "Linear Algebra" --vault ~/LearnLoop/math
learnloop quick-add ~/Books/linear-algebra.pdf \
  --subject linear-algebra \
  --vault ~/LearnLoop/math
~~~

The CLI Quick Add imports the PDF if necessary, selects relevant units under the configured token cap, suggests `primary_textbook`, shows one confirmation, and runs inventory plus synthesis.

In the desktop app:

1. inspect the resulting proposal and registry;
2. create a goal such as “Linear algebra for ML” over the relevant concepts;
3. start with a 25-minute session;
4. answer the first diagnostic blocks without hints;
5. use the source chips after feedback, not before the cold attempt; and
6. promote a tutor question to practice if it reveals a reusable gap.

A good source set might later add lecture notes as `lecture` and a geometric explanation as `alternate_explanation`. The role belongs to the source-set membership, so the same source may play a different role in another subject. Section 7.9 covers that append journey, and section 7.5 gives the full role/authority matrix.

### Example B: prepare for an exam

Create a study map with the exam-prep brief. Supply the deadline, target recall, topics, and desired exam-item count. Enable the held-out pool in the goal wizard.

Use past exams through the Ingest screen's "exam seeding" mode, or with the exam-ingestion CLI, when you have historical outcomes. Those results are useful priors but are not equivalent to a new held-out exam.

During study:

- goal-frontier items receive a queue quota that rises as the deadline approaches;
- items projected to decay below the target join the frontier even if they are solid today;
- held-out exam items remain excluded from practice;
- repair work is favored after a localized error; and
- the exam overlay freezes predictions before showing results so calibration can be evaluated honestly.

### Example C: learn from your own notes without external synthesis

Create a subject and add a learner note:

~~~bash
learnloop add-note linear-algebra svd-intuition "SVD intuition" \
  --file ./svd-intuition.md \
  --source-type learner_note \
  --vault ~/LearnLoop/math
~~~

You can author LOs/PIs in the Library, run a reviewable proposal, or use manual grading. This is the lowest-egress path. Source-grounded AI authoring and tutor responses require the configured provider, but the vault files, attempts, FSRS scheduling, self grades, replay, and inspection remain local.

## 7. Source ingestion v2

### 7.1 Supported source forms

The authoritative resolver accepts:

- ordinary HTTP/HTTPS webpages;
- arXiv URLs or IDs;
- YouTube URLs;
- remote or local PDFs;
- local HTML;
- local Markdown, text, RST, or another readable non-binary text file; and
- `.vtt`/`.srt` caption files (WebVTT/SRT), parsed as timed transcripts whose units carry time-range locators.

A source is classified once into web, arXiv, PDF, YouTube, or text file; transcripts ride inside the text-file kind with a dedicated transcript extractor. URL normalization and content hashes prevent repeated imports from creating duplicate revisions.

### 7.2 Identity and immutability

The source layer separates:

1. the conceptual work;
2. the acquired artifact;
3. an immutable byte revision;
4. an extraction run over that revision; and
5. the derived unit/block/asset IR.

Identical artifact identity and identical bytes reuse a revision. Changed bytes create a new revision linked by `supersedes_revision_id`. A source set pins a revision rather than silently following whatever happens to be latest.

Raw content and extraction products are content-addressed. Extraction request hashes include the revision, provider/options, package versions, an internal block-map version, and IR schema. Updating an extractor — or its block-mapping/normalization logic alone — therefore invalidates the right cache entries instead of silently serving stale output.

Registration also retains the original bytes of a PDF in a content-addressed originals store under `canonical-sources/raw/`, backfilling a missing copy on revision reuse. The `original_uri` remains the provenance record; the store exists so live-source viewers have the original document reliably even after the user's file moves or a URL goes stale, and backfill refuses on a hash mismatch.

### 7.3 Document IR

All extractors normalize into one `DocumentIR` containing:

- ordered, span-addressable blocks;
- chapter/section units and parent relationships;
- figures/assets with captions and geometry;
- page and section locators;
- per-block content hashes and role hints; and
- page-level extraction-health flags.

Markdown is now a display/export rendering of the IR, not the canonical intermediate. Equations, tables, and code are preserved verbatim; figures render with their caption context. Legacy note locators remain readable permanently, while new provenance uses extraction/span locators.

PDF extraction uses the configured provider boundary. Local pypdf extraction is available; structured Marker extraction can provide richer blocks, geometry, figures, and page health when installed (its math output is rewritten to `$`/`$$` delimiters before tag stripping so LaTeX renders correctly). Difficult-page repair is a separate consent-gated action and can re-run local extraction or, when explicitly selected, use an external visual model. A repair composes only the repaired pages with the parent run.

For PDFs, "open in source" now goes beyond the extraction view: the desktop app opens an embedded pdf.js reader over the original bytes from the originals store, served through a dedicated `llpdf://` protocol that keeps multi-megabyte documents off the sidecar's JSON-RPC channel. The sidecar's reader manifest supplies per-block page/bbox geometry so extraction spans can be highlighted and text selections hit-tested back to spans inside the original document.

### 7.4 Outlines, units, and token budgets

The outline is deterministic: it uses the extracted table/section structure, estimates tokens, displays difficult pages, and lets the learner select units before synthesis. The build plan estimates each model-call stage. Large sources are bounded by unit selection and window budgets; context growth must not be proportional to the whole source library.

Quick Add selects the whole source when it fits the configured cap. Otherwise it selects keyword-relevant units from the brief/subject in outline order and falls back to leading units when nothing matches.

### 7.5 Source roles, authority, and source sets

Three properties are orthogonal and are decided at different moments:

- `acquisition_kind` (`web | arxiv | pdf | youtube | textfile`) is intrinsic to how the source was obtained. It selects an extractor and decides nothing else;
- `source_role` decides authority: whether the source may support a canonical semantic claim, and whether it may shape assessment; and
- `source_scope` is the set of selected unit ids.

Role, scope, and priority belong to source-set membership, not to the artifact. The same PDF can be the primary textbook of one collection and a supporting reference in another. The source note itself carries only a `suggested_role` hint.

The authority matrix is implemented once, in `services/role_authority.py`. Every consumer — inventory requests, the synthesis span protocol, the append policy, the quality gates, and the coverage report — reads that module rather than restating the policy:

| Role | May support a semantic claim | May shape assessment | Default inventory profile |
|---|---|---|---|
| `primary_textbook` | yes | yes | combined |
| `lecture` | yes | yes | combined |
| `paper` | yes | yes | combined |
| `reference` | yes | yes | semantic |
| `alternate_explanation` | yes, as support; never silently primary | yes | semantic |
| `problem_set` | no | yes | practice |
| `exam` | no | yes | assessment |
| `notes` | no, until confirmed | yes | semantic |
| any unknown role | no | no | — |

An unknown role fails closed. It receives no semantic and no assessment privileges until a human confirms a known role or records an explicit manual authority grant carrying scope, rationale, actor, and timestamp. Unknown roles produce doctor warnings; they are never rejected outright.

Role also selects the inventory profile, so role determines cost. An `exam` unit is inventoried for assessment signals only; a `problem_set` unit for task and method signals; explanatory roles for semantic contracts. An existing richer `combined` inventory can satisfy a later narrower request for free, but a narrower profile is never silently upgraded to an expensive one.

Roles are suggested after inspection, from the acquisition kind: PDF to `primary_textbook`, YouTube to `lecture`, arXiv to `paper`, and webpage or text file to `reference`. Suggestion never proposes `exam`, `problem_set`, or `notes`, because those roles *remove* authority and must be a deliberate choice. Role ambiguity does not block Quick Add; it proceeds with the suggestion and flags the source for later review.

A unit may override the membership role. A textbook chapter's exercise section can carry `role_override: problem_set`, contributing task signals without gaining authority over definitions that section omits.

Source sets are subject-scoped and pin a `revision_id` per member, so a collection never silently follows whatever revision is newest. Sets carry no scheduling semantics: goals may select sets, and sets never reference goals. An empty scope means the whole artifact.

### 7.6 Synthesis and append

Bootstrap synthesis creates a first study map. Append synthesis operates on the bounded affected neighborhood when a source, unit scope, or revision changes. Both persist immutable manifests: inputs, source revisions, selected units, prompt/model contract, evidence spans, and output hashes.

Deterministic quality gates check registry identity, references, blueprint/criterion contracts, provenance, source coverage, and conflicts. Applying a map is allowed only under the canonical knowledge model (`mvp-0.7` or later).

A gate failure no longer wastes the run. The expensive merged candidate is preserved on the failed run and can be repaired and revalidated with zero model calls: mechanically safe repair operations are derived automatically (for example, dropping item-level dependencies that echo rubric criterion IDs and could never resolve), explicit typed operations (`drop_dependency`, `remap_dependency`) can be supplied, and revalidation finishes the gates and persistence from the checkpoint. This seam is exposed as the `learnloop synthesize-repair` CLI command (`--ops-file`, `--dry-run`, `--apply`, `--create-goal`), the sidecar's candidate-repair retry, and an "auto-repair & revalidate (no new model run)" action in the Ingest activity feed.

Append does not rewrite the entire curriculum merely because a source changed. It classifies additions, refinements, confirmations, and contradictions; auto-applies only safe changes; and routes identity locks, conflicts, or semantic merges to review. Maintenance notices can be dismissed or snoozed, but the underlying revision and provenance remain.

### 7.7 Privacy boundary

Acquisition and local extraction do not imply permission to send content to an external model. The study-map confirmation lists the egress-capable stages and estimated input. Page repair has its own explicit consent because the selected pages may be sent to a visual model. The configured AI provider and its privacy terms remain the learner/operator's responsibility.

### 7.8 Journey: first sources in a new vault

A vault created by `learnloop init` starts at `algorithm_version = mvp-0.8` and can apply a study map immediately. A vault carried over from before the knowledge model starts at `mvp-0.6` and must run `learnloop upgrade`; activation is vault-wide and atomic, and mixed-version vaults are forbidden. A subject must exist before a collection, because source sets are subject-scoped.

~~~bash
learnloop init ~/LearnLoop/math
learnloop add-subject linear-algebra "Linear Algebra" --vault ~/LearnLoop/math

# 1. Import into the vault-level library. No subject, role, scope, or collection yet.
learnloop import ~/Books/axler-3e.pdf

# 2. Inspect structure and health, then choose what is worth learning.
learnloop source-outline src_axler_3e

# 3. Assemble a collection. Membership pins the revision and owns role and scope.
learnloop source-set create la-foundations --subject linear-algebra --title "Linear Algebra Foundations"
learnloop source-set add la-foundations --source src_axler_3e --revision srcrev_ab12cd34 \
  --role primary_textbook --unit chapter_02 --unit chapter_04

# 4. Read the bill before paying it.
learnloop source-coverage la-foundations
learnloop build-plan src_axler_3e --subject linear-algebra

# 5. Create the study map.
learnloop synthesize la-foundations --mode auto --brief-file brief.json --apply
~~~

Import is deterministic. It fetches bytes, registers the artifact and revision, extracts to the Document IR, and computes extraction health. It performs no pedagogical model call and sends nothing off the device. A partial batch stays useful: sources render as they finish, and queued work survives closing the app.

Unit selection is the main cost lever in the system. The outline is computed from the persisted IR and consumes zero agent runs, so a 900-page book scoped to five chapters only ever costs five chapters. Boundary corrections are stored as overrides *over* the extraction run, so re-extracting later does not discard them. Pages flagged as difficult can be re-run with `learnloop repair-extraction`, which is separately consent-gated because repair is the one step that may send page images to an external visual model.

Synthesis persists an immutable manifest before the model runs, shards the selected unit inventories, allows the model one bounded round of exact span requests, and passes the output through the deterministic quality gates. What comes back is a dependency-annotated proposal, not a vault write. Accepting it applies the dependency closure under the vault mutation lock.

In the desktop app the same journey is the Ingest paste field (canonical source mode), then the source card in the Source Library sidebar, then outline & select, then the build plan, then Create study map, with the activity feed showing the checkpoint ladder.

Quick Add collapses steps 1 through 5 into a single confirmation. It runs on exactly this machinery — real library rows, a real extraction run, real inventories, a real manifest, the same gates — with defaults auto-chosen, a small relevant unit scope, and queue priority over bulk batches.

### 7.9 Journey: adding an adjunct source later

The first three steps are identical, and routing is automatic. `--mode auto` selects append once the vault already has a study map, so there is no separate mode to learn.

~~~bash
learnloop import ~/Books/strang.pdf
learnloop source-set add la-foundations --source src_strang --revision srcrev_ef56 \
  --role alternate_explanation --unit chapter_01
learnloop synthesize la-foundations --mode auto --new-revision srcrev_ef56
~~~

Append context is the new or changed unit inventories, the brief, and a deterministically selected affected neighborhood matched by concept name, alias, prerequisite hint, existing provenance, and source scope. It never resends the accumulated curriculum and never compares sources pairwise, so cumulative cost stays linear in newly selected material rather than quadratic in source count.

Append cannot perform an arbitrary update. It emits a typed additive vocabulary:

| Intent | Proposal item type | Default policy |
|---|---|---|
| Attach a supporting span to existing curriculum | `provenance_link` | auto-applies when every span resolves in scope and the target hash is unchanged |
| Record an alternate explanation of a facet you already have | `provenance_link` (`relation=alternate`) | auto-applies under the same conditions |
| Record that an assessment source shaped a task family | `provenance_link` (`relation=assessment_alignment`) | auto-applies; never touches a semantic contract |
| Reconcile two symbol conventions | `notation_mapping` | review, because equivalence is context-dependent |
| Two sources genuinely disagree | `source_conflict` | review; accepting persists an open two-sided conflict and applies neither definition |
| Genuinely restructure existing curriculum | `restructure_unlocked` | review, and invalid rather than merely gated if any touched identity is locked |
| New material with no existing home | ordinary curriculum types | ordinary validation |

The common case is cheap. A second book that explains facets you already have attaches as alternate provenance on those same facets and auto-applies: a second explanation of one thing, not a second copy of it. A study-map diff after the run answers what adding the source actually changed.

Identity locks are what make this safe. Once evidence exists against a facet, that facet's identity is locked. Append may add support, alternate explanations, and assessment alignment indefinitely, but it may not merge, split, re-key, or rewrite a facet you have already practised against, because your attempts mean something specific about that facet and silently redefining it would falsify your history. Before a lock exists, a reviewed merge or split is legal and cheap. `can_apply` is the single decision point, checked before synthesis, before auto-apply, and again at accept time while the vault mutation lock is held.

Adopting a newer revision of a source you already have is the same journey. Because membership pins a revision, a newer one appears as an update notice and never advances on its own. Adopting it runs the same reconciler over an old/new block diff: unchanged spans re-anchor and keep their links, and anything ambiguous becomes `needs_reanchor` rather than being silently re-pointed at the wrong text. A partially refreshed source remains usable, with unresolved stale links visible in the collection and provenance views.

### 7.10 Exam sources: authority, use modes, and evidence

An exam is assessment evidence, not semantic authority. That rule is enforced in four independent places rather than merely documented:

- exam units never enter the semantic synthesis context at all. They are aggregated into a deterministic exam profile — task family, capability demand, representation, response format, and point or time emphasis — and their held-out spans go to the leakage gate;
- every exam unit carries a use mode: `held_out_evaluation` (a protected partition, filtered out of teaching, practice generation, and tutor contexts at every context builder), `available_for_practice` (a released paper the learner explicitly chose to sit, which still never gains semantic authority), or `blueprint_only` (shapes the distribution and nothing else);
- the quality gates hard-fail an exam-only semantic claim and any held-out wording appearing in a teaching or generated-practice payload; a practice item resting solely on an exam source downgrades to review; and
- near-duplicate papers from one syllabus family collapse into a single assessment-alignment vote, so five past papers are not five independent signals of emphasis.

An exam appearing in a source set never changes mastery. Exam performance becomes learner evidence only through an explicit recorded attempt or the exam-seeding flow: imported historical outcomes enter as discounted `exam_evidence`, while a fresh held-out response carries full `exam_attempt` evidence mass. Source coverage alone never moves belief.

A representative multi-role collection makes the separation concrete. The textbook carries `primary_textbook` and mints the facets and their applicability conditions. A lecture series carries `lecture` and attaches to those same facets as an alternate explanation. The textbook's exercise section carries `role_override: problem_set` and shapes task families and difficulty without gaining authority over definitions it omits. Past papers carry `exam` and shift the declared blueprint distribution and exam-readiness report without being able to redefine anything. Provenance renders semantic and assessment authority in separate lanes, so "this appeared on an exam" is never displayed as "this defines the concept."

## 8. The canonical knowledge model (mvp-0.7 / mvp-0.8)

Both versions read and write the same canonical shared-facet state described in this section; neither falls back to the retired legacy per-LO facet bridge. What `mvp-0.8` adds is the **authority-propagation projection**: instead of projecting belief directly from graded attempts, it reads the authoritative measurement-event substrate — administrations, calibrated interpretations, and appended adjudications — and applies robust composition with reliability discounts on top of it.

The practical consequences:

- **Reinterpretation without rewriting.** When a later adjudication changes the leading actionable conclusion for an old observation, `mvp-0.8` appends a `measurement_reinterpretation` event and rebuilds downstream state. The immutable decision-time interpretation rows are untouched; history is append-only.
- **Receipts for activation.** Activating the projection records a `derived_state_rebuilds` receipt naming what was replayed and rebuilt. On a projection failure the last-good named projection stays readable.
- **An inspectable delta.** Upgrading a vault from `mvp-0.7` computes an explicit reinterpretation delta over the projected facet cells (positive/negative mass, direct negatives, certification credit), so "what did the new projection change about my state" is an answerable question, not a diff you have to trust.

`mvp-0.7` remains readable as a byte-identical compatibility projection for vaults that have not upgraded. Everything below — facets, capabilities, blueprints, criteria, depth rungs — is common to both.

### 8.1 Facets are canonical claims

A facet is the smallest claim LearnLoop intends to assess and repair independently. The vault-level `facets.yaml` schema stores more than a label:

- concept and kind;
- the canonical claim;
- applicability conditions;
- positive and negative examples;
- non-goals;
- error signatures and instructional repairs;
- aliases, status, version, fingerprint, and provenance.

The supported facet kinds are definition, proposition, procedure contract, applicability condition, and interpretation.

Renaming preserves identity. A reviewed semantic merge creates an alias/merge mapping and resolves it at read time; it does not copy Beta mass into a second row. A semantic split requires review because historical evidence cannot be assigned to the new meanings automatically.

### 8.2 Capabilities are closed and domain-general

The launch vocabulary is:

`retrieval | schema_interpretation | procedure_execution | method_selection | coordination`

Selection is separate from execution: being able to execute Gaussian elimination when told does not demonstrate choosing it appropriately. Coordination is reserved for observable integration failures that can exist even when component skills are present.

Transfer is not a sixth capability. It is represented by performance across categorical context/surface families in the diagnostic layer.

At launch, prediction pools through one shared parent belief per facet because splitting sparse evidence into five independent states would make every state weak. Every criterion observation is still tagged by capability, and certification is capability-specific. Optional lazy capability residuals exist but are disabled by default until repeated evidence demonstrates a real divergence.

### 8.3 LOs are performance blueprints

An LO is not a scalar skill; it is a performance target, and blueprints and recipes are how that target is written down precisely enough to compute readiness from facet-level belief.

A **blueprint** is one representative performance the LO stands for — a task shape such as "diagonalize a small matrix" or "decide whether a matrix is diagonalizable and justify it." An LO carries one or more blueprints, each with a weight; LO readiness (section 11.5) is the weighted mean over them, so an LO that stands for two different task shapes is not summarized by either one alone.

A **recipe** is one valid *method* of satisfying a blueprint. Each blueprint lists one or more recipes, and a learner who can execute any one of them can perform the task. A recipe contains:

- `all_of`: conjunctive facet-capability components — pairs like (eigenvalue-definition facet, `retrieval`) or (characteristic-polynomial procedure, `procedure_execution`) that this method requires together;
- `any_of`: alternative components, of which at least one must hold — an alternative-method group inside the recipe; and
- an optional explicit `integration` component, authored only when component competence can coexist with a repeatable, observable, separately repairable coordination failure.

Each component carries a requirement modality:

- hard: required by every relevant valid path;
- path-specific: required for named recipes;
- facilitating: useful but bypassable; and
- instructional order: normally taught earlier but not cognitively required.

Only hard and exercised path-specific components gate the recipe likelihood. Facilitating and instructional-order components never make a learner look unready.

The point of the structure is attribution. When a composite attempt fails, the recipe says which facet-capability components could have caused it; when readiness is projected, the recipe says exactly which beliefs multiply (section 11.5); and when two methods exist, a learner strong in either one is ready — the blueprint takes the best applicable recipe rather than averaging methods the learner never uses. The flat `evidence_facets` list on legacy LOs is derived from the blueprints for search and compatibility; it is never the source of readiness math.

The golden path's **task blueprint** (section 17) is a different object with a similar name: a human-reviewed, immutable, content-addressed contract describing one chapter/unit and one target task family for a certifying run. It reuses the same closed capability vocabulary but stores a reviewed contract only — it never mints a posterior, an FSRS write, or certification.

Concept-graph edges are for navigation and authoring. `related`, `analogous_to`, `part_of`, and `confusable_with` do not write mastery. A prerequisite edge does not create evidence merely by graph traversal.

### 8.4 Criteria are the observation boundary

A rubric criterion declares:

- points;
- facet-capability targets;
- primary or supporting role;
- dependencies on earlier criteria;
- a correlation group; and
- applicable recipe IDs.

At presentation, LearnLoop freezes an assessment contract. A later edit to the live item cannot reinterpret what an old response actually assessed.

For legacy items without explicit targets, the mode-to-capability compiler supplies a deterministic default. Authored targets always win.

### 8.5 Depth rungs, waypoints, and depth edges

Depth is a learner-authorized program, not a difficulty scalar.

A *waypoint* is one closed cell of a difficulty trajectory: one capability plus a point in task-feature space (complexity, transfer, response, scaffolding, and span). A *depth rung* is the generation-time unit — a waypoint plus per-dimension target/max bounds. The rung constrains what kind of task may be generated; deterministic gates prevent a generated item that uses the wrong capability or exceeds a bound from being auto-applied.

Practice generation also calibrates numeric item difficulty *within* the selected rung. The two controls are orthogonal: the rung says what operation and task regime the learner is being asked to handle, while the IRT difficulty in section 11.3 estimates how challenging one item is inside that regime. FSRS memory difficulty remains a third, item-specific quantity (section 12).

#### The five built-in depth rungs

The default trajectory is ordered from easiest to deepest:

| Rung | Capability | Complexity | Transfer | Response | Scaffolding | Span |
|---|---|---:|---|---|---|---|
| `recognize` | `retrieval` | 0 | same context | recognition | cue | atomic |
| `recall` | `retrieval` | 1 | same context | short constructed | none | atomic |
| `interpret` | `schema_interpretation` | 2 | near | long constructed | none | single step |
| `execute` | `procedure_execution` | 2 | near | structured steps | none | multi-step |
| `select_method` | `method_selection` | 3 | far | short constructed | none | single step |

`recognize` and `recall` therefore exercise the same capability but under meaningfully different response and assistance contracts. Recognition is not a sixth capability and recall evidence does not become method-selection evidence merely because both tasks concern the same facet.

The built-in trajectory deliberately stops before `novel_combination`, `whole_task`, and `coordination` work. Coordination is reserved for directly observable integration failures and requires a whole-task contract. Deeper regions use reviewed commitment milestones rather than silently extending this table.

#### How the default rung is selected

When no reviewed commitment milestone supplies the next rung, generation uses the LO's displayed EKF calibration and its evidence count. The current defaults are:

| Learner state | Selected rung |
|---|---|
| No usable signal, or mastery below 0.35 | `recognize` |
| Mastery at least 0.35 but below 0.60 | `recall` |
| Mastery at least 0.60 with fewer than 5 observations | `interpret` |
| Mastery at least 0.60 with at least 5 observations | `execute` |
| Mastery at least 0.75 with at least 10 observations | `select_method` |

The thresholds are selection heuristics, not achievement claims. The mastery value here is the LO's prediction-only calibration state (section 11.3), not Demonstrated credit and not the blueprint Ready projection. A learner claim may seed the value when no performance state exists, but the evidence-count conditions prevent a strong self-report from jumping directly to execution or method selection. If a commitment has a valid reviewed next milestone, its task contract takes precedence over these defaults; a malformed projection fails closed to the default trajectory and records the fallback.

#### How rungs connect facets, capabilities, and evidence

The relationship is:

```
canonical facets (what must be known)
        +
capability (what operation must be performed)
        +
depth rung (task context, transfer, response, scaffold, span)
        ↓
rung-targeted item with frozen rubric criteria
        ↓
attempt observations in exact facet × capability cells
        ↓
facet belief + LO calibration + certification ledger + FSRS memory
        ↓
Ready / Demonstrated projections and the next scheduling decision
```

The flat `evidence_facets` list on an LO contributes the semantic content to cover during authoring; as section 8.3 explains, it is a derived search/compatibility view rather than a mastery source. The rung contributes the cognitive operation and task regime. Frozen rubric criteria join the two by naming exact facet-capability targets. Consequently:

- a rung is not evidence by itself — only an administered and graded observation can update learner state;
- retrieval evidence cannot certify `procedure_execution` or `method_selection`;
- strong component observations cannot certify `coordination` without direct whole-task evidence;
- shared canonical-facet belief can support prediction across LOs, while Demonstrated credit stays capability-specific; and
- rung-targeted generation can improve coverage of a blueprint component, but completing a rung does not by itself make the entire LO Ready or mastered.

Ready is still computed by projecting facet-capability probabilities through blueprint recipes (section 11.5). Demonstrated still requires bounded, fresh, unassisted observations in the exact cells tested (section 11.6). The rung decides what to ask next; those models decide what the resulting observation means.

#### Easier and harder variants

The learner can request a same-LO sibling one adjacent waypoint away:

```
recognize ↔ recall ↔ interpret ↔ execute ↔ select_method
```

The source item's stamped capability/task features are preferred when locating it on the trajectory. Legacy items fall back to their practice-mode capability and authored retrieval/transfer/scaffold values, then to the LO-state selector above.

A variant request is itself honest but weak evidence, persisted even if later generation fails:

- an easier request writes an LO-scoped claim at 0.25 and a self-graded `self_report` soft failure with score fraction 0.25;
- a harder request writes an LO-scoped claim at 0.70 and a self-graded `self_report` success with score fraction 1.0; and
- both claims use pseudo-count 2, while the attempt uses the ordinary `self_report` evidence mass of 0.30.

The request then authors a sibling at the target rung, reusing the LO's semantic facets and enforcing the target capability/task-feature bounds. Easier than `recognize` is refused. An item already beyond the default trajectory can step down to `select_method`; harder than `select_method` requires a reviewed depth envelope.

#### Commitments, presets, and depth edges

The four coarse commitment presets are not additional rungs:

`keep_in_touch | remember_key_ideas | work_fluently | master_tasks_like_these`

They capture learner intent when a commitment is created. For example, Reader actions such as “test me later” use `keep_in_touch`, while “help me remember,” “connect it,” “keep developing,” and learner-authored Reader Q&A use `remember_key_ideas`; Golden Path exemplar commitments normally use `master_tasks_like_these`. A preset creates an understandable starting policy/envelope, but the immutable versioned policy and envelope — not the label — are authoritative.

Depth policies are `hold_at_target`, `suggest_next`, or `auto_within_envelope`. Deeper regions require an explicit *depth edge*: an owner-curated reusable edge template plus a concrete edge instance that passes deterministic gates before it can be pinned into the learner-reviewed envelope. The successor contract uses the same capability and task-feature vocabulary as the built-in rungs, so custom milestones can express coordination, whole-task span, novel combination, tool conditions, or other reviewed changes without pretending those are a sixth fixed level.

Nothing crosses an envelope on its own. An eligible transition needs predecessor exit evidence, an admitted activity path, a fresh proof route, acceptable burden, and a positive robust value. One decision can commit at most one edge before the system replans. The Golden Path depth invitation (section 17) is the current learner-facing accept/decline path for one reviewed edge.

#### Do not confuse depth rungs with the Golden Path pattern ladder

Golden Path also uses the word *rung* for a separate remediation sequence. Depth rungs describe the capability and task regime of generated work. Pattern-ladder rungs describe which teaching or repair activity should happen after triage. A pattern-ladder stage can use a depth-targeted item, but advancing that teaching sequence is not equivalent to demonstrating a deeper capability. Section 17.2 enumerates the pattern ladder and its evidence rules.

## 9. What happens when an attempt is submitted

The high-level pipeline is:

1. Resolve the PI, LO, rubric, and frozen assessment contract.
2. Validate the attempt type and any diagnostic presentation.
3. Grade with the configured provider, or collect a structured self grade.
4. Validate criterion points, fatal-error caps, facet targets, error types, and repair suggestions.
5. Resolve surface coverage, observation reliability, familiarity/correlation discount, and evidence mass.
6. Persist the attempt and criterion observations.
7. Update the per-item FSRS memory state.
8. Update the LO prediction-only EKF and optional item-difficulty posterior.
9. Compute surprise, item-quality suspicion, error events, and follow-up needs.
10. Recompute the canonical facet/capability projection from the immutable observation ledger.
11. Update any open diagnostic episode and release block feedback when appropriate.
12. Persist a debug payload and learner-facing feedback.

AI output is never accepted directly as state. It is schema-validated against the item's frozen rubric, known facets, known criteria, and error taxonomy.

Replay and regrade reuse the same application path. Replay reads persisted grades and does not call the provider. Under `mvp-0.7`, the canonical projection is the only writer of shared facet state; the old per-LO facet tables receive no new writes.

## 10. Attempt evidence, coverage, and assistance

LearnLoop keeps three related quantities separate:

- surface exposure: how much of the intended surface the attempt actually touched;
- evidence mass/reliability: how strongly the observation should move predictive belief; and
- certification credit: how much unassisted, capability-matched demonstration can be banked.

Default attempt-type evidence masses are:

| Attempt type | Evidence mass | Important interpretation |
|---|---:|---|
| independent/open text/diagnostic probe | 1.00 | Full predictive evidence, subject to coverage and reliability. |
| hinted attempt | 1.00 | Belief can update, but assistance prevents demonstration credit. |
| reconstruction after walkthrough | 0.50 | Partly dependent on exposure. |
| explicit don't know | 0.70 | Surface exposure is 1.00; the learner did inspect the prompt. |
| self report | 0.30 | Prior-like evidence, never equivalent to performance. |
| imported exam evidence | 0.35 | One historical exam is a correlated event. |
| fresh held-out exam attempt | 1.00 | A new uncontaminated exam response. |
| teach-back | 0.80 | One graded transcript; transfer-tier criteria are further discounted. |
| guided walkthrough / skip | 0.00 | Learning/exposure may occur, but it is not performance evidence. |

No new attempt types were added for the recent reader and re-runging features; they emit existing types. A rung-variant request records a deterministic self-graded `self_report` attempt on the source item at the standard 0.30 mass — an easier request as a declared soft failure (score fraction 0.25), a harder request as a success (score fraction 1.0). Reader answers are never ability evidence at all: at most they become a replay-derived routing prior that reorders tier-two triage.

Coverage comes from authored weights, rubric criterion maps, or a mode default. Reliability includes grader confidence, hint policy, attempt type, and other validated modifiers. Familiarity discounts same-item, same-surface, and overlapping-facet repetitions so dependent attempts cannot impersonate fresh evidence.

The LO EKF receives a resolved observation weight. Conceptually:

\[
w_{\text{obs}}
= \text{effective coverage}
\times \text{reliability}
\times \text{error sharpening}
\times \text{independent-evidence discount}.
\]

The exact trace is stored with the attempt, including coverage, reliability, familiarity, prediction, ability transition, and state changes.

## 11. Estimating the learner's latent state

LearnLoop does not maintain one all-purpose “mastery number.” It maintains complementary latent/read models.

### 11.1 Learner claims seed priors

A covering learner claim can be global, subject/domain, concept, or LO-specific. The most specific and strongest applicable claim seeds the LO calibration prior.

For claimed level \(c\) and pseudo-count \(n\):

\[
\mu_0 = \operatorname{logit}(\operatorname{clip}(c, 0.05, 0.98)),
\qquad
P_0 = \frac{1}{\max(n, 0.25)}.
\]

Any covering claim can seed the prior, including a low “this exposed a gap” claim. Claims do not earn evidence mass or certification credit.

Two newer claim sources feed this channel. The study-map brief's starting level maps the ordinals new-to-this / some-exposure / comfortable / strong-background to global claimed levels 0.15 / 0.35 / 0.55 / 0.75 with pseudo-count 1. A rung-variant request writes an LO-scoped claim: easier maps to claimed level 0.25, harder to 0.70, both with pseudo-count 2 — so asking for an easier item seeds a cold LO's prior honestly instead of silently.

### 11.2 Canonical facet belief is Beta mass

For a canonical facet, LearnLoop folds localized positive and negative pseudo-mass into:

\[
\alpha = 1 + m^+,\qquad
\beta = 1 + m^-.
\]

The posterior mean and variance are:

\[
E[p] = \frac{\alpha}{\alpha+\beta},
\qquad
\operatorname{Var}(p)
= \frac{\alpha\beta}{(\alpha+\beta)^2(\alpha+\beta+1)}.
\]

For criterion \(j\):

\[
m_j
= e_{\text{attempt}}
  \frac{\text{criterion maximum points}}{\text{rubric total}}.
\]

Positive mass is split across targets using role weights 1.0 for primary and 0.3 for supporting, normalized within the criterion.

First-error localization protects causal interpretation. If criterion B depends on A and A fails, B is unassessable; it contributes no negative evidence. Passed prefixes and independent branches still count. An assessable first failure is localized to its criterion. If that failed criterion has multiple possible targets and the grader supplies no valid attribution distribution, LearnLoop creates an unresolved-cause factor rather than lowering every target.

The first observation from a surface/correlation group can add independent mass. Repeating the same group uses a default 0.25 inference discount and adds no new independent surface group.

The same canonical facet belief is visible through every LO and subject that references it.

### 11.3 LO calibration uses a probability-space EKF

Each LO retains a scalar state \(\theta \sim \mathcal{N}(\mu,P)\). Under `mvp-0.7` this is a prediction-only calibration residual. It can help predict how the learner performs on this LO's tasks, but it carries no certification credit.

Without a claim, the prior is \(\mu=0, P=1\). Uncertainty drifts upward with time:

\[
P^- = \min(P + \sigma^2_{\text{drift}}\Delta d,\ P_{\max}),
\]

with defaults \(\sigma^2_{\text{drift}}=0.01\) per day and \(P_{\max}=4\).

Static item difficulty uses a 2PL link:

\[
p = \sigma(a(\mu-b)).
\]

The default discrimination is \(a=1\). An authored difficulty \(d\in[0,1]\) becomes:

\[
b = \operatorname{clip}(2s(d-0.5), -4, 4),
\]

with \(s=2.5\). This IRT difficulty is not the FSRS memory difficulty.

For normalized observed score \(y\), the EKF linearizes the link:

\[
H = a p(1-p),
\]

\[
R_y = \frac{R_0 p(1-p)}{\max(w_{\text{obs}},0.10)},
\]

\[
S = H^2P^- + R_y,
\qquad
K = \frac{P^-H}{S},
\]

\[
\mu' = \mu + K(y-p),
\qquad
P' = (1-KH)P^-.
\]

The implementation caps a single logit step at 4 and clamps \(\mu\) to \([-5,5]\). Displayed LO calibration is \(\sigma(\mu)\); its probability-space variance uses the delta method.

Empirical-Bayes item difficulty can alternate a symmetric update in \(b\), with derivative \(-ap(1-p)\), a strong prior variance of 0.25, gain scale 0.2, and maximum step 0.25. It is disabled by default because one learner and one answer cannot identify learner ability and item difficulty reliably.

A primed retry shifts the observation difficulty but does not move the last-cold-evidence timestamp.

### 11.4 Facet prediction blends shared evidence with the LO backbone

Sparse facet evidence initially needs a stable prediction backbone. Let \(q\) be the LO EKF probability, \(f\) the facet Beta mean, \(m\) facet independent mass, and

\[
n_0 = \min(4,\ \text{LO evidence count}).
\]

Then:

\[
\lambda = \frac{m}{m+\max(n_0,0.1)},
\qquad
\hat p_{\text{facet}}=(1-\lambda)q+\lambda f.
\]

If there is no evidenced LO state, LearnLoop uses the facet mean; if neither exists, it uses 0.5. As independent facet mass accumulates, the facet posterior takes over.

Capability residual activation is optional and off by default. Prediction therefore pools through the shared facet parent, while the capability ledger preserves what was actually tested.

### 11.5 Ready is a blueprint projection

For a conjunctive recipe with required component probabilities \(p_i\):

\[
P(\text{success})
= g + \max(0,1-g-s)\prod_i p_i,
\]

where slip \(s=0.05\) by default. For a constructed response \(g=0\). For multiple choice, \(g=1/n\) when the option count is known, otherwise the default is 0.25.

An `any_of` alternative contributes the maximum available method as one factor. An explicit integration facet is another conjunct. Facilitating and instructional-order components do not gate success.

The projection implementation also contains a reserved partially compensatory/explanatory branch whose core is a weighted geometric mean:

\[
P(\text{success})=(1-s)\prod_i p_i^{w_i/\sum_j w_j}.
\]

The current authored `BlueprintRecipe` schema accepts only `composition: conjunctive`, so this branch is not yet a supported authoring option. It is documented here to make the implementation seam explicit, not as a workflow learners can rely on today.

A blueprint uses the best applicable recipe. LO readiness is the normalized weighted mean of blueprint success probabilities:

\[
\operatorname{Ready}(LO)
= \frac{\sum_b w_b\max_{r\in b}P(r)}{\sum_b w_b}.
\]

This projection writes no evidence.

### 11.6 Demonstrated is bounded certification credit

Demonstration credit is banked only for direct or embedded, unassisted observations in the exact facet-capability cell. Hinted, scaffolded, answer-exposed, prior, graph, and projection signals earn zero credit.

Credit is capped first by correlation group and then by a total attempt ceiling:

\[
C_{\text{attempt}}
\le e_{\text{attempt}}\times G_{\max},
\]

where \(G_{\max}=3\) by default. Cell shares are preserved when a cap scales a group.

This prevents one long testlet, one near-clone family, or one composite answer from minting unlimited certification. Retrieval evidence cannot certify method selection; strong components cannot certify integration without the declared direct whole-task evidence.

### 11.7 Misconceptions are hypotheses, not score labels

A mechanism error such as recall failure or method-selection failure routes the next intervention. A promoted misconception is a more specific belief statement with provenance and lifecycle state.

A single strange answer may create an error event or unresolved cause; it should not automatically become a durable misconception. Repeated, discriminating evidence can promote or reactivate one. Clean later attempts can resolve it. The hypothesis-surface work is adding a better learner-facing history for returned/resolved cases, but the underlying diagnostic distinction already matters.

## 12. FSRS item memory

FSRS answers a different question from the knowledge model: “When is this particular item likely to be forgotten?”

Each PI has dynamic memory difficulty \(D\), stability \(S\), retrievability \(R\), and a due time. This dynamic \(D\) is not the authored IRT difficulty \(b\).

Using the current FSRS-6 defaults, retrievability after \(t\) days is:

\[
R(t,S) = \left(1 + F\frac{t}{S}\right)^{-d},
\]

where \(d=w_{20}\) and

\[
F=0.9^{1/(-d)}-1.
\]

Scores map to Again, Hard, Good, or Easy using ratios below 0.25, below 0.60, below 0.90, and at least 0.90. Hint policy can cap the rating.

FSRS then updates \(D\) and \(S\). The next interval inverts the forgetting curve at desired retention, 0.9 by default:

\[
t_{\text{next}}
= S\frac{r^{1/(-d)}-1}{F}.
\]

The scheduler's forgetting risk is nonzero only once an item is due:

\[
\text{forgetting risk}=1-R(t,S).
\]

This item-memory channel and the shared knowledge channel complement each other. An item can be due even when the facet is strong, and a facet can be uncertain even when a familiar item is easy.

## 13. How items are served

### 13.1 Eligibility and exclusions

The queue starts with active PIs whose LO can be resolved. It excludes:

- inactive items;
- held-out exam-pool items;
- ephemeral diagnostic dialogue turns from ordinary practice; and
- cold LOs with no evidence, no active goal frontier, and no open diagnostic episode.

A pending diagnostic episode never blocks ordinary practice. It keeps a cold LO eligible while the system waits for a suitable instrument.

### 13.2 Baseline priority

For candidate \(i\), the configurable baseline is:

\[
P_0(i)
= 1.00F_i + 0.25G_i + 0.50E_i + 0.25I_i,
\]

where:

- \(F\) is due-item forgetting risk;
- \(G\) is active goal-frontier overlap times goal priority and exposure discount;
- \(E\) is the maximum recent error severity decayed with a seven-day time constant; and
- \(I\) is normalized probe information, familiarity-discounted.

A separate boundary-fit floor can make an item eligible when its predicted difficulty is informative even if the baseline is zero. Teach-back and open cold episodes also have small floors so they are not eliminated before ranking.

The goal frontier contains unexamined facets, known gaps, and currently solid facets predicted to fall below target recall by the due date. Queue composition enforces a goal share between 0.30 and 0.70, ramped over 28 days as the deadline approaches.

### 13.3 Intent-first selection reward

Each item is classified as probe, repair, transfer, teach-back/probe, or ordinary practice. The queue sorts primarily by a bounded selection reward and secondarily by baseline priority.

For probes:

\[
U_{\text{probe}}
=0.70\,\text{normalized information}
+0.10\,\text{LO variance}
+0.10\,\text{facet uncertainty}
+0.10\,G
-\text{duplicate penalty}.
\]

For repair:

\[
\begin{aligned}
U_{\text{repair}}={}&
0.30\,\text{repair fit}
+0.25\,\text{gradient fit}
+0.20\,\text{facet weakness}\\
&+0.10\,\text{boundary fit}
+0.15\,\frac{\text{expected skill gain}}{0.08}
+0.10\,E
+0.15\,G\\
&-\text{overload}
-\text{repetition fatigue}.
\end{aligned}
\]

For ordinary practice/review/transfer:

\[
\begin{aligned}
U_{\text{practice}}={}&
0.20F+0.15G
+0.20\,\text{facet weakness}
+0.20\,\text{gradient fit}\\
&+0.15\,\text{boundary fit}
+0.10\,\frac{\text{expected skill gain}}{0.08}
+0.05\,\text{transfer distance}\\
&-\text{overload}
-\text{repetition fatigue}.
\end{aligned}
\]

Gradient fit favors a useful challenge range rather than maximizing predicted correctness. The current target bands are 0.40–0.60 for probes, 0.75–0.90 for repairs, 0.60–0.80 for transfer, and 0.55–0.75 for ordinary practice.

### 13.4 Composition and learner control

After ranking, LearnLoop applies:

- seeded 10% exploration among non-probe near-ties within a 0.15 reward window;
- a teach-back session cap;
- the goal-frontier quota;
- a front-slot guarantee for up to one learner-requested tutor-promoted item;
- same-day frontier rotation; and
- forced pending intervention/surprise follow-ups.

Probe choices are not randomized by this exploration policy. Every candidate slate, component, selected probability, reason, and exploration flag is logged so the policy can later be evaluated off-policy.

The `why <pi-id>` command shows the scheduler components. Learner-facing reasons are derived from the same terms, not generated prose.

### 13.5 Readiness inputs

Energy and available minutes affect session context and queue size. The scheduler maps low/medium/high energy to 0.5/0.75/1.0 and compares available minutes with the 20-minute short-session threshold, then averages the available factors.

Sleep quality currently contributes to the Start screen's preview/readiness score but is not a separate scheduler reward term. It should be interpreted as session-planning input, not latent knowledge evidence.

## 14. Diagnostic probes and EIG

### 14.1 What a probe is

A probe is a measurement chosen to distinguish decision-relevant explanations, not merely a hard practice question. An episode owns:

- a locked hypothesis set;
- a state segment;
- a bounded sequence of committed item presentations;
- the exact instrument/card/version and likelihood snapshot used to select each item;
- observations and contamination state; and
- a completion or transition decision.

The pre-redesign `lo_probe_state` path is frozen for historical replay. New writes use diagnostic episodes.

### 14.2 Hypothesis construction

The episode ranks plausible hypotheses from:

- unfamiliar;
- robust initial grasp;
- surface-only knowledge;
- recall without mechanism;
- procedure without method selection;
- schema without transfer;
- `confuses_with:<concept>` neighbors; and
- `misconception:<id>` for active/resolving registry cases.

It keeps up to five substantive candidates and appends `other_or_unknown` with a default 0.10 prior mass. The open-set state prevents the model from forcing every answer into an authored explanation.

The set is locked for the episode so the posterior remains interpretable. Re-probing opens a new episode and a new snapshot.

### 14.3 Instrument admission

A PI is a qualifying diagnostic candidate only when it has an executable binding to an admitted provisional/trusted probe family and instrument card, or a narrow registry-discrimination fallback. A generic item that cannot separate the active hypotheses gets zero hypothesis EIG.

Instrument cards declare:

- an observation alphabet;
- hypothesis-to-slot mapping and honest aliases;
- conditional outcome rows;
- target facets and surface family;
- expected time;
- grader policy;
- long-form obligations when applicable; and
- version/lifecycle state.

Items from the same surface cannot repeat within an episode. Reusing a family receives a ranking penalty of \(0.6^k\) after \(k\) prior observations, but that penalty is not mislabeled as EIG.

Likelihood calibration shrinks item-level counts toward family-version counts with 25 pseudo-observations. Families can become trusted only from real learner evidence and regrade agreement; synthetic checks alone cannot promote them.

### 14.4 Expected information gain

Let \(H\) be the locked hypothesis, \(O\) the instrument outcome, \(\pi_h\) the current posterior, and \(L_{ho}=P(O=o\mid H=h,i)\). The outcome marginal is:

\[
P(o\mid i)=\sum_h \pi_hL_{ho}.
\]

Actual hypothesis EIG is mutual information:

\[
\operatorname{EIG}(i)
=\sum_h\pi_h\sum_oL_{ho}
\log\frac{L_{ho}}{\sum_{h'}\pi_{h'}L_{h'o}}.
\]

Coverage, uncertainty, family diversity, and goal value are logged as separate utility components. They are never added into the number called EIG.

When at least two held-out predictive target instruments exist, the primary objective is expected reduction in their predictive uncertainty, normalized per expected time:

\[
\text{information rate}
=\frac{\text{predictive EIG}}
       {\text{expected seconds}+10}.
\]

Hypothesis EIG remains the fallback and an audit signal. The two EIG types are never summed.

Before an item is served, LearnLoop commits a presentation containing the prior posterior, entropy, chosen card/version, slot map, both EIG measures, selection components, and an expiry (240 minutes by default). Submission must match that item, active state segment, and unconsumed presentation. Retrying the same attempt is idempotent.

### 14.5 Bayesian update and reliability

For observed outcome \(o\):

\[
\pi'_h
=\frac{\pi_hP(o\mid h,i)}
       {\sum_{h'}\pi_{h'}P(o\mid h',i)}.
\]

For evidence weight \(w<1\), LearnLoop dampens the likelihood toward the current outcome marginal \(m_o\):

\[
\widetilde L_{ho}=wL_{ho}+(1-w)m_o.
\]

Then the ordinary Bayes update uses \(\widetilde L\). This makes a contaminated or low-reliability answer less decisive without pretending it never occurred.

Belief updates can use relevant incidental attempts. Episode budget and completion advance only on qualifying selected observations.

### 14.6 Interaction contract

During an active diagnostic block:

- hints are disabled;
- the tutor is disabled;
- worked examples and answer reveal are disabled;
- the attempt type is forced to diagnostic probe;
- the learner records answer confidence from 1 to 5; and
- feedback is deferred until the block ends.

Approved qualifying grading sources are AI, Codex, or a deterministic result such as explicit don't-know. Manual/self grading cannot advance the episode. Assistance, an invalid presentation, the wrong attempt type, or other contamination can still produce damped belief evidence but not completion credit.

Dialogue microprobe turns share one task evidence budget. Long-form probes count only assessable obligations and use first-error logic.

### 14.7 Blocks, stopping, and burden

The default block releases feedback after two observations. At the boundary, LearnLoop persists beliefs, checks the open-set mass, evaluates completion, and either:

- closes the episode;
- starts another block;
- parks it as `pending_items` and records one generation need;
- creates a typed tutoring transition; or
- returns to ordinary practice.

An episode stops at four qualifying observations, or earlier when:

\[
P(h_1)\ge0.85,
\qquad
\frac{P(h_2)}{P(h_1)}\le0.30,
\]

and breadth is adequate: at least two independent observation units, at least two surfaces when two are required, and coverage of all required facets.

A strong covering claim at or above 0.75 can use a one-observation fast path only when the posterior stopping test is already stable and that observation is a discriminating cross-facet instrument.

If `other_or_unknown` reaches 0.35, the system records the open-set problem instead of inventing a precise diagnosis.

Routine sessions admit at most four qualifying diagnostic observations. A fresh vault also stops onboarding probes after four qualifying observations until ordinary practice begins. An explicit calibration session, normally 20 minutes and at most eight planned episodes, lifts only the per-session cap within that declared budget.

The learner can always choose “stop diagnosing and teach me.” That ends the pre-intervention state segment and persists a typed tutor decision with target facets, gap, first invalid step, misconception, confidence, tutor move, answer-reveal budget, expected learner action, and source references.

## 15. Tutor, teach-back, and promotion

### 15.1 Where the tutor works

The Ask overlay is available in:

- Library, about the selected note;
- Practice, about the current item;
- Feedback, about the completed attempt; and
- Reader, about the selected source span.

Default answered-turn limits are:

- 3 per practice item/session;
- 5 per feedback attempt;
- 8 per library note per UTC day; and
- 8 per source span per UTC day in the reader.

The reader context is bidirectional (gated by `tutor_qa.reader_enabled`, on by default for new vaults). A learner Ask is span-grounded in the block-level source view and carries a per-ask answer mode: answer directly, help me reason, or ask me first. In the other direction, owner-placed reading questions are administered at section boundaries as instructional-purpose, always-skippable, certification-ineligible prompts, and a four-disposition picker (comprehension only, check once later, keep developing, reference only) routes follow-up mechanism without ever writing evidence. A reader answer is never ability evidence.

A question is persisted before the provider call. If the provider fails, the learner's question remains logged as elicitation evidence, but the failed turn does not consume the answer budget.

### 15.2 Practice guardrails and hint equivalence

Questions are classified as prerequisite, mechanism, strategy, clarification, verification, or other. In practice context, prerequisite/mechanism/strategy help is a hint equivalent. It is added to the hint count at submission and flows through the same mastery dampening, coverage rules, and FSRS rating caps as an authored hint.

Clarification, verification, and other questions do not automatically count as hints. Verification prompts are deflected toward a guiding question.

The tutor prompt forbids stating the answer, completing the derivation, or confirming the learner's approach during practice. A post-hoc overlap heuristic flags suspected answer leakage for telemetry; it does not block the response. The honest product claim is therefore “guarded against revealing the answer,” not an absolute guarantee.

The tutor is disabled during diagnostic blocks and teach-back transcripts because assistance would contaminate the measurement.

### 15.3 Questions and uncertainty

A question never lowers the mastery mean. Recent unresolved questions about a facet add a bounded read-side diagnostic uncertainty bump. This can encourage diagnosis while remaining reproducible from the event log.

An explicit request for direct explanation is stored on an interaction-preference channel rather than treated automatically as evidence of ignorance. Contextual likelihoods can be calibrated later without rewriting the original event.

### 15.4 Source grounding

Tutor context uses a bounded set of up to four semantically authoritative source spans across the relevant LOs. A model citation is shown only if its extraction/span ID was actually provided to the model. Citation chips open the exact source context.

In feedback, a tutor question can add a facet to an existing intervention need. A proactive opening after a diagnostic transition uses the persisted typed decision but is ephemeral: it does not consume the question budget or count as a hint.

### 15.5 Save or promote a useful exchange

An answered turn can be:

- rated useful/not useful;
- saved as a vault note;
- promoted with “add to practice”; or
- outside Library, promoted with “this exposed a gap.”

Promotion is idempotent. It materializes a Q&A note for grounding and deduplicates an existing PI before creating or proposing anything.

The ordinary practice route creates or proposes a PI. The gap route also writes a low self-report claim, default level 0.25 with pseudo-count 2, and files an intervention/diagnostic need. A promoted but unattempted item receives up to one front slot per session if it is otherwise eligible.

The learner can also author directly. "Write a card" on Today creates a practice item in the learner's own words with no review gate (section 5, step 7). In the reader, a learner-authored Q&A path persists the learner's own question and answer before any AI assistance, creating a learner-authored card with a non-blocking formulation coach.

### 15.6 Teach-back

A teach-back item reverses roles: the learner explains and an AI “naive student” asks up to three follow-ups, usually one per uncertainty-ranked criterion. The transcript is graded as one `teach_back` attempt with evidence mass 0.8.

Core criteria test the target facets. Transfer-tier criteria test edge cases or method choice and receive a symmetric 0.5 evidence multiplier. At most one teach-back item is included in a built queue by default.

## 16. Goals, exams, and projections

A goal specifies a facet/concept scope, priority, target recall, and optional due date. Open-ended goals use a 30-day projection horizon.

The goal frontier includes:

- unexamined facets;
- known gaps; and
- facets projected below the target by the due date.

Ready/attainment can use predictions and pooled shared evidence. Demonstrated/certification uses only the bounded capability ledger. A goal screen must not silently blend those two axes.

The goal wizard can reserve a held-out exam pool. Those items never enter ordinary practice. Exam predictions are frozen before grading, which supports later calibration rather than retrofitting the prediction after seeing the outcome.

Imported exam outcomes are backdated historical evidence and use a lower mass because questions from one exam share context. A live held-out exam attempt is a new measurement.

The goal trajectory now renders two aligned lanes: a Demonstrated lane (a step line of capability-matched certification counts) and a Ready lane (predicted recall with its forecast). The two axes are never blended into one scalar. Ready remains a read model; only the Demonstrated lane reflects banked certification.

## 17. The golden path run

The golden path (implemented 2026-07-20; `spec_p2_narrow_golden_path.md`) is a narrow, end-to-end certifying journey available from the Golden Path tab of the desktop application. It is the smallest honest version of the promise:

> Choose tasks like this; find my current boundary; teach or repair the nearest reason I cannot yet do them; strengthen that ability on changing surfaces; then test it on a fresh target-like task and, if I authorized it, grow one reviewed step beyond it.

It is deliberately narrow: one chapter, one task family, one run at a time. Mixed-unit or multi-family runs are rejected rather than pretended at. Every consequential step requires an explicit learner confirmation, and nothing ever fires automatically — the final "grow one step deeper" clause ships as an invitation that a single confirmation activates.

### 17.1 Entry and setup: choose your task

Opening the Golden Path tab with no active run shows the setup screen. Any in-flight runs are listed first with a resume action — a run spans days and survives an app restart. An offline demo link renders the entire run surface from fixtures with no backend, clearly labeled.

Starting a new run walks five numbered steps:

1. **Goal.** Pick an active goal (created from the Today tab if none exists).
2. **Task family.** Pick one learning object from the discovered exemplar pool. This is the "tasks like this" the run will be about.
3. **Exemplars.** Mark one or two *anchor* items — concrete tasks like the ones you want to master — and exactly one *held-out* sibling, ideally never attempted (items are labeled `seen` or `fresh`). The held-out item becomes the cold assessment; anchors ground generation and explanation but never count as unseen evidence. Composing then produces a draft task blueprint — the immutable, content-addressed contract for this one unit and task family (section 8.3), which follows a register → review → activate ladder: only a reviewed version can be activated by the confirmation.
4. **Owner review.** Three explicit checks must all be confirmed: the exemplars are grounded in material actually studied, the rubric matches what the tasks really require, and the selection is genuinely one family (one skill, one unit).
5. **Confirm and start.** One atomic confirmation mints goal-contract v1, reserves the held-out assessment surface *before* any potentially contaminating practice is shown, and starts a certifying run. Every material edit afterward creates an append-only successor contract; no run silently changes its meaning.

### 17.2 The run state machine

An active run pre-empts the application body (the exam/calibration precedent) and renders the server-side state machine as a checkpoint ladder:

```
ready → baseline → triage → instruct → practice → ready-to-assess → assess → restore → complete
```

Every stage answers four questions on screen: why now, what kind of activity this is (teaching, practice, diagnosis, or assessment), what can update, and how much remains. Plain transitions advance with a single keypress; the triage and instruction stages cannot be blind-advanced — their workspaces own the transition, because skipping them would skip the administration the state exists for. A crash or retry reopens the same committed state; it never chooses a second item or repeats a side effect.

**Baseline.** A short (2–4 administration) diagnostic using pre-authored, reviewed cards locates the current boundary. The golden path never invents a diagnostic instrument on the hot path.

**Triage.** A failure is not sent through a universal wrong-answer flow. The learner reports what actually happened — wrong / didn't know / correct-but-shaky, an error signature (wrong method, execution slip, schema gap, misconception, integration gap, misread), exposure and memory-trace history, and confidence in that read. Decisive evidence routes automatically (tier one); anything ambiguous returns as a decision aid the learner must confirm (tier two). Reason precedes repair.

**Instruction and practice: the pattern ladder.** The committed triage reason maps to an entry rung — the nearest useful one, not always the bottom. The learner does each rung's activity with their materials (anchor practice flows through the Today queue), then logs the outcome honestly: pass, failed, or gave up, plus how much scaffold was used. The run advances only on this evidence; no rung mints unassisted certification, and repeated failures on a rung flag the run for review instead of letting it climb.

The pattern ladder contains nine named stages across seven ordinals. Stages sharing an ordinal are alternative activity patterns rather than additional depth levels:

| Ordinal | Stage or alternatives | Purpose and evidence behavior |
|---:|---|---|
| 0 | `explanation` | Instructional; records the transition into teaching, not performance evidence. |
| 1 | `example_study` or `example_comparison` | Instructional acquisition or discrimination work. |
| 2 | `example_completion` | Instructional; records how much scaffold was used. |
| 3 | `setup_only` or `move_spotting` | Instructional repair for choosing or recognizing the next move. |
| 4 | `independent_repair` | Cold practice on the repaired capability; updates practice scheduling but does not certify. |
| 5 | `whole_task_integration` | Cold practice for coordination/integration failures; still not the held-out assessment. |
| 6 | `delayed_independent_practice` | A delayed cold check before the run becomes ready to assess. |

Triage chooses the nearest useful entry: memory lapse, missing knowledge, or false belief enters at explanation; a schema/conceptual hole or task-interpretation problem enters at example comparison; procedure failure enters at example completion; method-selection failure enters at setup/move spotting; and coordination failure enters at whole-task integration. A learner who already demonstrated the capability can skip instruction and enter at independent repair. A surface/grading fault or unresolved ambiguity opens no ladder rung until the fault is resolved or diagnosis is reopened.

Instructional stages never apply FSRS review, open a lapse, or mint unassisted certification. Practice stages can update the practice schedule, but every pattern-ladder stage still has `mints certification = false`; the reserved cold assessment is the certifying administration. Three failures on distinct surfaces at the same rung flag the run for review instead of generating an infinite stream of near-clones. Passing `example_completion` with substantial scaffolding records that assistance rather than disguising it as independence, and the final independent-practice stage carries a delayed due time.

**Rotating practice.** Alongside the ladder, a practice pool is seeded from the anchor exemplars. Candidates stay inert until the owner admits each surface and marks the pool reviewed; an assessment-reserved surface is refused at admission. Served surfaces carry honest freshness labels — a familiar surface is visibly reduced-evidence and is never reported fresh. From the anchor list the learner can also mint an easier or harder same-LO sibling one depth waypoint away; it lands in the ordinary queue and also informs the learner model.

**Cold assessment.** Opening the assessment administers the reserved unseen sibling. The flow enforces coldness mechanically: the learner writes an answer first, then locks it — only after locking is the expected answer revealed — then self-grades against the rubric and submits. Submission burns the surface: a used assessment can never return as pristine assessment, and the result card shows the burn and eligibility state explicitly alongside pass/fail, claim language, calibration status, and the evidence interval. Practice and assessment use separate purpose-typed families throughout.

**Restore.** The reached milestone is recorded and a boundary diff shows what changed, with the held-out exemplar marked in the comparison.

**Depth invitation.** Finally the run lays out at most one reviewed next-depth edge, wholly inside the learner-confirmed envelope, as an accept/decline invitation (`suggest_next` semantics). One edge per decision; each subsequent milestone is a fresh decision. Commit-without-prompt activation is deferred to the auto-depth package (U-018) — the invitation never fires on its own.

### 17.3 What the run guarantees

Every conclusion is traceable to the measurement receipt, the commitment/activity tree, and the exact terminal-contract version; the run header shows the event count and head sequence, and advances are idempotent against the current head. If no fresh assessment surface can be reserved, the system may still teach and practice, but labels the run `practice_only` and makes no terminal claim. The selected exemplar is an anchor, not proof; instruction closes the diagnostic segment it changes; feedback burns assessment freshness; and readiness display never blends predicted ability with demonstrated certification.

## 18. Surprise, errors, and follow-ups

Predictive surprise compares the observed score with the same IRT probability used by the EKF. Bayesian surprise measures the change between prior and posterior belief distributions. Surprise can:

- shorten or lengthen the next FSRS interval;
- trigger a follow-up;
- contribute to item-quality suspicion; and
- trigger re-probing after repeated prediction failures.

A negative result need not be surprising to be useful. Explicit don't-know and repeated localized errors can still update evidence and route repair even when the model already expected failure.

Recent errors decay in scheduler value with a seven-day time constant. High-severity misconceptions, repeated large predictive misses, and stale high uncertainty can open a new diagnostic episode.

Follow-up and intervention decisions are persisted separately from the original score. The typed repair-episode flow has landed: remediation episodes with delayed cold retries back a dedicated Repair surface, launched from feedback's "repair this →" or from a Review hypothesis.

## 19. Provenance, replay, and debugging

### 19.1 Editable content versus derived state

Human-reviewable curriculum lives in Markdown/YAML. SQLite contains events, immutable observations, source identities/manifests, scheduling logs, and replayable derived caches.

Do not hand-edit derived SQLite rows to change mastery. Correct the content or grading evidence, then replay.

### 19.2 Useful commands

~~~bash
learnloop doctor --vault ~/LearnLoop/my-vault
learnloop doctor --fix-state --vault ~/LearnLoop/my-vault

learnloop today --vault ~/LearnLoop/my-vault
learnloop why <practice-item-id> --vault ~/LearnLoop/my-vault
learnloop show <attempt-or-item-or-lo-id> --json --vault ~/LearnLoop/my-vault

learnloop rebuild-derived-state --vault ~/LearnLoop/my-vault
learnloop rebuild-derived-state \
  --learning-object <lo-id> \
  --vault ~/LearnLoop/my-vault

learnloop ingest-batches list --vault ~/LearnLoop/my-vault
learnloop ingest-batches show <batch-id> --vault ~/LearnLoop/my-vault
learnloop ingest-batches resume <batch-id> --vault ~/LearnLoop/my-vault

learnloop synthesize-repair <run-id> --dry-run --vault ~/LearnLoop/my-vault
~~~

`show <attempt-id> --json` exposes the coverage, reliability, familiarity, criterion, IRT, surprise, and ability-transition traces. `why` exposes scheduler terms and the expected information signal.

A full rebuild replays persisted attempts in order and recomputes mastery, FSRS, canonical facet/capability state, item quality, errors, surprise, and debug payloads. It does not re-run grading.

### 19.3 Source provenance

Entity provenance links a concept/facet/LO/PI to exact extraction spans and immutable source revisions. “Open in source” resolves those links through the current extraction view; for PDFs it additionally opens the embedded reader over the original bytes with the span highlighted (section 7.3). Re-extraction attempts to re-anchor old spans by content hash, geometry, and section path; failures become review needs rather than silently pointing somewhere else.

### 19.4 Assessment provenance

Every new criterion observation carries stable lineage to the assessment-contract version and grading revision. Regrading retires/replaces the derived interpretation through the same projection fold. Under `mvp-0.8`, a reinterpretation additionally appends a `measurement_reinterpretation` event and leaves the decision-time interpretation rows untouched (section 8). A projection is a cache over evidence, never a new evidence source.

## 20. Default parameter summary

These are current defaults, not universal truths. They are versioned/configurable and should be changed only with replay and calibration in mind.

| Area | Default |
|---|---|
| Algorithm for a new vault | `mvp-0.8` |
| Scheduler baseline weights | forgetting 1.00, goal 0.25, recent error 0.50, probe information 0.25 |
| Goal queue floor | 0.30 to 0.70 over a 28-day ramp |
| Short-session threshold | 20 minutes |
| Seeded exploration | 0.10 among non-probe near-ties within 0.15 reward |
| EKF drift / variance cap | 0.01 per day / 4.0 |
| IRT discrimination / difficulty scale | 1.0 / 2.5 |
| IRT empirical item difficulty | disabled |
| Built-in depth trajectory | `recognize → recall → interpret → execute → select_method` |
| Depth-rung mastery bands | below 0.35 recognize; 0.35–0.60 recall; at least 0.60 interpret/execute |
| Deeper default-rung evidence gates | execute at 5 observations; select method at 10 observations and mastery at least 0.75 |
| Blueprint slip / unknown MC guess | 0.05 / 0.25 |
| Facet prediction backbone count | 4 observations, capped by actual LO evidence |
| Repeated surface inference discount | 0.25 |
| Certification groups per attempt | 3 |
| Probe substantive hypothesis cap | 5, plus `other_or_unknown` |
| Probe observation range | minimum 2 independent, maximum 4 |
| Probe stable posterior | top at least 0.85, second/top at most 0.30 |
| Probe open-set prior / trigger | 0.10 / 0.35 |
| Probe block size for feedback | 2 observations |
| Probe presentation TTL | 240 minutes |
| Probe predictive target minimum/cap | 2 / 6 |
| Routine qualifying probe cap | 4 per session |
| Calibration session | 20 minutes, at most 8 episodes |
| Tutor budgets | practice 3, feedback 5, library 8, reader 8 |
| Tutor source-span cap | 4 |
| Tutor-promoted requested floor | 1 item/session |
| Teach-back | up to 3 follow-ups, 0.8 mass, 0.5 transfer multiplier, cap 1 |
| Open-ended goal horizon | 30 days |
| Hypothesis claim attention budget | 2/session with 7-day cooldown |
| Forecast horizon | 14 days |
| Starting-level claim levels | 0.15 / 0.35 / 0.55 / 0.75, pseudo-count 1 |
| Rung-variant claim levels | easier 0.25, harder 0.70, pseudo-count 2; self-report attempt at 0.30 mass |

## 21. Practical interpretation

When LearnLoop serves an item, read the decision as:

> Among the activities that are valid now, this one best balances memory due-ness, goal risk, recent errors, diagnostic information, useful difficulty, expected learning gain, diversity, and the learner's explicit requests.

When LearnLoop updates state, read it as:

> This answer is evidence of a particular strength, from a particular surface, with a particular amount of assistance and grading reliability. Update only the claims it actually assessed, preserve unresolved alternatives, and keep prediction separate from demonstration.

When LearnLoop runs a diagnostic block, read it as:

> Ask the smallest set of unassisted questions that can change what the system should do next. If the evidence remains ambiguous, admit that, obtain a better instrument, or switch to teaching.

That is the core LearnLoop contract: local and inspectable evidence, explicit uncertainty, bounded inference, source-grounded repair, and a loop that returns to cold retrieval rather than confusing immediate fluency with durable learning.
