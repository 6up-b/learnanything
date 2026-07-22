# LearnLoop

**A local-first learning system that turns trusted sources into adaptive practice.**

LearnLoop builds an inspectable model of what you are learning, what you
have demonstrated, what is becoming forgettable, and what to practice next. It
combines editable Markdown/YAML content with a SQLite event store,
FSRS scheduling, learner-aware misconception detection and remediation, and AI-assisted authoring and feedback.

> [!NOTE]
> LearnLoop is under active development. The desktop app currently runs from a
> source checkout, and installer bundling is not yet enabled

## What LearnLoop does

- Imports webpages, arXiv papers, PDFs, YouTube transcripts, caption files
  (`.vtt`/`.srt`), and local text/Markdown files into a versioned source
  library with immutable revisions and content-addressed extraction.
- Extracts source structure before synthesis so you can inspect scope, page
  health, and estimated model usage — and pay only for the chapters you select.
- Builds reviewable study maps containing concepts, canonical facets, learning
  objects with performance blueprints and recipes, rubrics, and practice items.
  Generated changes stay in proposals or maintenance queues when human review
  is needed.
- Lets you read the source in-app: an embedded Reader (including a real PDF
  reader over the original bytes) with annotations, span-grounded tutor
  questions, owner-placed reading questions, and optional as-you-read practice
  generation.
- Schedules ordinary review, repair, transfer practice, teach-back, and bounded
  diagnostic probes from one Today queue — and explains, term by term, why an
  item was selected.
- Tracks item memory, predicted ability, demonstrated evidence, errors, claims,
  forecasts, goals, and exam readiness without collapsing them into a single
  score. Prediction is never presented as certification.
- Grounds feedback and tutor answers in exact source spans and preserves
  provenance end to end. Raw attempts are retained so derived learning state
  can be deterministically replayed after algorithm changes.
- Supports learner authoring: write your own practice cards, promote useful
  tutor exchanges, request easier/harder variants of an item, and run a
  narrow end-to-end certifying "golden path" over one task family.

The core loop is:

1. Add high quality source material.
2. Select the useful parts and build a study map.
3. Review proposed content and provenance.
4. Read the source in the Reader, learn through questions asked to you and you asking questions.
5. Start a time- and energy-bounded session.
6. Practice, receive feedback, and repair specific weaknesses.
7. Let new evidence update future scheduling, and return for cold retrieval.

For a step-by-step walkthrough, start with the
[quick start](documentation.md#quick-start) in the
[user and algorithm guide](documentation.md), which covers vault creation,
Quick Add versus deliberate ingestion, what the pipeline does mechanistically,
and the daily practice loop — then drills into the learner model behind it.

## Quick start: desktop app

### Prerequisites

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js and npm
- Rust and Cargo
- The [Tauri 2 platform prerequisites](https://v2.tauri.app/start/prerequisites/)
  for your operating system

On Debian or Ubuntu, Tauri currently requires:

```bash
sudo apt update
sudo apt install libwebkit2gtk-4.1-dev build-essential curl wget file \
  libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good
```

On Arch Linux, install the matching GStreamer runtime plugins for embedded
audio and video playback:

```bash
sudo pacman -Syu --needed gst-plugins-base gst-plugins-good
```

`gst-plugins-good` provides `autoaudiosink`, which WebKitGTK requires when the
Reader plays embedded video. If it is missing, the WebKit web process can exit
when playback starts.

### Run from a checkout

From the repository root:

```bash
uv sync --extra dev
cd apps/learnloop-tauri
npm install
npm run dev
```

`marker-pdf` is not required for canonical source ingestion. Webpages, YouTube
transcripts, Markdown, HTML, and text files do not use it, and text-based PDFs
fall back to the base `pypdf` dependency. Marker is an optional, heavier PDF
provider that preserves richer layout, tables, math, figures, and geometry (I would reccomend using marker when possible). It's enabled when
`[ingest.pdf].engine` is explicitly set to `"marker"`. Install it with:

```bash
uv sync --extra dev --extra pdf
```

The Tauri shell starts the Python `learnloop_sidecar` automatically. When the
tracked linear-algebra fixture is present, it is used as the development default.
Click the green vault path in the app header to select another vault, or use the
new-vault wizard on the Start screen to create and bootstrap one.

To open a particular vault immediately:

```bash
LEARNLOOP_VAULT=/absolute/path/to/my-vault npm run dev
```

PowerShell:

```powershell
$env:LEARNLOOP_VAULT = "C:\path\to\my-vault"
npm run dev
```

### Finding your way around

The app has ten navigation tabs:

| Tab | Purpose |
|---|---|
| Start | Session start (energy/time), new-vault wizard |
| Today | The practice queue, goal wizard, write-a-card |
| Graph | Concepts, LOs, evidence state, knowledge-map views (terrain / well / strata) |
| Ingest | Single-screen source import, study-map creation, exam seeding, activity feed |
| Proposals | Accept / reject / edit synthesized content |
| Registry | Canonical facet claims, warnings, error taxonomy |
| Library | Source and learner notes |
| Golden Path | Narrow end-to-end certifying runs over one task family |
| Reader | In-app reading with annotations and span-grounded Ask |
| Maintain | Source updates, conflicts, exam readiness |

Review and Repair open as overlays (palette `review`/`diff`, or from feedback)
rather than as tabs.

Useful shortcuts:

| Shortcut | Action |
|---|---|
| `Ctrl/Cmd+P` or `:` | Open the command palette |
| `Alt+1` … `Alt+9`, `Alt+0` | Switch among the ten tabs |
| `Esc` | Close the current overlay or return to the queue |
| `j` / `k` | Move through list-oriented screens |

The command palette accepts navigation commands as well as CLI-style queries
such as `today`, `review` (alias `diff`), `why <practice-item-id>`, `show <id>`,
`attempt <practice-item-id>`, `calibrate`, and `doctor`.

## Create a vault from the CLI

The desktop wizard is the easiest first run, but the Python CLI is useful for
automation and diagnostics:

```bash
uv run learnloop init ~/LearnLoop/my-vault
uv run learnloop add-subject linear-algebra "Linear Algebra" \
  --vault ~/LearnLoop/my-vault
uv run learnloop doctor --fix-state --vault ~/LearnLoop/my-vault
```

A fresh vault starts at `algorithm_version = "mvp-0.8"`. Then add a source and
inspect the queue:

```bash
uv run learnloop quick-add "https://example.com/source" \
  --subject linear-algebra \
  --vault ~/LearnLoop/my-vault
uv run learnloop today --vault ~/LearnLoop/my-vault
```

Quick Add collapses import → outline → unit selection → inventory → synthesis
into one confirmation. The deliberate step-by-step path (`import`,
`source-outline`, `source-set`, `source-coverage`, `build-plan`, `synthesize`)
runs the same machinery with you at each decision point — see the
[quick start](documentation.md#quick-start) for when to prefer which.

Run `uv run learnloop --help` for the complete command list, or append `--help`
to any subcommand. Most read-oriented commands also support stable JSON output
for tooling.

## Vaults and local data

A vault is a normal directory. Its durable source of truth is designed to remain
inspectable and portable:

```text
my-vault/
├── learnloop.toml       # algorithms, scheduling, ingestion, and AI routing
├── state.sqlite         # attempts, events, scheduling, jobs, and derived state
├── concepts/            # vault-wide concept and relation registries
├── subjects/            # study maps, notes, learning objects, and practice items
├── profile/             # goals and learner-owned state
├── errors/              # misconception and error taxonomy
├── canonical-sources/   # registered artifacts, revisions, extractions, and raw originals
└── facets.yaml          # canonical assessable claims
```

Markdown and YAML hold editable learning content. SQLite holds event history,
runtime state, indexes, and model projections. Raw attempts are retained so
derived state can be deterministically replayed and rebuilt
(`learnloop rebuild-derived-state`).

Before moving, scripting, or directly editing a vault, close LearnLoop or ensure
no other process is writing to it. Run `doctor` after manual content changes.

## AI providers

The scheduler, replay system, source extraction plan, and vault storage are
local. AI-backed study-map synthesis, grading, tutor responses, and some
authoring flows require a configured provider. Ordinary practice can use the
desktop app's `manual` provider for self-grading; diagnostic observations and
other workflows that require an independent grader remain unavailable in manual
mode.

Provider profiles and per-workflow routing live in the vault's `learnloop.toml`:

```toml
[ai]
active_provider = "codex"

[ai.routing]
grading = "codex_low"
canonical_ingest = "codex_medium"
authoring = "codex_medium"
tutor_qa = "codex_low"
teach_back = "codex_low"
```

Both derived Codex profiles use `gpt-5.6-sol`. Canonical ingestion and authoring
use medium reasoning; interactive grading, Tutor Ask, and teach-back use low.

Secrets and machine-specific values should not be committed to a vault. LearnLoop
loads them in this order:

1. Existing shell environment
2. `<vault>/.env`
3. `~/.config/learnloop/settings.env`

For the local Codex SDK provider, set the checkout path in the machine settings
file or shell:

```dotenv
LEARNLOOP_CODEX_CHECKOUT_PATH=/absolute/path/to/codex
```

OpenAI-compatible provider profiles use the `api_key_env` named in
`learnloop.toml`. Check provider and vault health with:

```bash
uv run learnloop doctor --ai --vault ~/LearnLoop/my-vault
```

The active grading provider can also be changed from the desktop app header.

## Architecture

```text
React + TypeScript + Vite
          │ Tauri invoke
          ▼
Rust desktop shell and command layer
          │ JSON-RPC over stdio   (+ llpdf:// protocol for original PDF bytes)
          ▼
Python learnloop_sidecar
          │
          ├── Markdown / YAML vault content
          ├── SQLite events and derived state
          └── configured AI provider (optional, workflow-dependent)
```

| Path | Purpose |
|---|---|
| `apps/learnloop-tauri/` | React/Tauri desktop application |
| `src/learnloop/` | Domain model, services, scheduler, ingestion, and CLI |
| `src/learnloop_sidecar/` | JSON-RPC bridge used by the desktop app |
| `migrations/` | Ordered SQLite schema migrations |
| `tests/` | Unit, integration, replay, calibration, and CLI tests |
| `fixtures/linear_algebra/` | Development vault with real example content |

The Rust shell finds the sidecar in this order: `LEARNLOOP_PYTHON`, `uv`, the
repository `.venv`, then the platform Python executable. Use
`LEARNLOOP_SIDECAR_TIMEOUT_SECS` to override the default 240-second desktop RPC
timeout when debugging unusually long model calls.

## Development

Run the Python test suite from the repository root:

```bash
uv run pytest
```

Check the desktop layers:

```bash
cd apps/learnloop-tauri
npm run typecheck
npm run frontend:build
cargo check --manifest-path src-tauri/Cargo.toml
```

Build the desktop executable with:

```bash
npm run build
```

Frontend assets are written to `apps/learnloop-tauri/dist/`; Rust build output
is written below `apps/learnloop-tauri/src-tauri/target/`. Tauri installer
bundling is currently disabled in `tauri.conf.json`.

For sidecar diagnostics, set `LEARNLOOP_SIDECAR_LOG_LEVEL=DEBUG` (or
`LEARNLOOP_SIDECAR_DEBUG=1`). Use `LEARNLOOP_SIDECAR_DEBUG_LOG` to send logs to a
specific file.

To enable the desktop webview's native zoom hotkeys for debugging, launch the
Tauri app with `LEARNLOOP_TAURI_DEBUG_ZOOM=1`. Use `Ctrl+=`, `Ctrl+-`, and
`Ctrl+0` to zoom in, zoom out, and reset the zoom level.

## Further reading

- [User and algorithm guide](documentation.md) — quick start, first-use
  journey, learner model, and operational details for current behavior
- [Product definition](product_definition.md) — product goals and design thesis
- [Technical specification](spec.md) — data model and algorithm contracts
- [Architecture pivot](architecture_pivot.md) — longer-term strategy for learned
  models and search
- [Changelog](CHANGELOG.md) — notable implementation milestones
