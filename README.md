# LearnAnything / LearnLoop

LearnLoop is a local adaptive learning vault. It keeps durable learning content
as editable Markdown/YAML and stores derived state in SQLite: attempts, FSRS
scheduling, mastery, scheduler explanations, Codex proposals, source ingestion
history, and content events.

# To do

- Fully add extensibility for deepseek API/other OpenAI routers instead of just codex
- augment logging (event based) for later learned mechanisms
- 

## Install

Requires Python 3.12+.

```powershell
python -m pip install -e .[dev]
learnloop --help
```

Optional canonical ingestion dependencies are declared in `pyproject.toml`
(`trafilatura`, `beautifulsoup4`, `lxml`, and `youtube-transcript-api`). They
are installed with the editable package command above.

You can also install with uv

```powershell
uv tool install git+https://github.com/6up-b/learnanything.git
learnloop --help
```
To make sure live source edits are reflected immediately use --editable

## Desktop App (Tauri)

The desktop GUI lives in `apps/learnloop-tauri`. It runs a Tauri shell around
the React frontend and starts the Python `learnloop_sidecar` process for vault
data, scheduling, practice submission, proposals, and SQLite inspection.

Prerequisites:

- Python 3.12+ with the editable LearnLoop package installed.
- Node.js/npm for the frontend toolchain.
- Rust/Cargo and the normal Tauri system prerequisites for your OS.
- On Windows, the Tauri window uses Microsoft Edge WebView2, which is usually
  already installed on current Windows systems.

From the repository root, install the Python package first:

```powershell
python -m pip install -e .[dev]
learnloop --help
```

Then install the desktop app dependencies:

```powershell
cd apps/learnloop-tauri
npm install
```

Launch the desktop app in development mode:

```powershell
npm run dev
```

The Tauri app starts `python -m learnloop_sidecar` with `src/` on
`PYTHONPATH`, so launch it from a shell where `python` points at the environment
that has LearnLoop's dependencies installed.

By default the app opens the tracked `fixtures/linear_algebra` vault when it is
present. To launch against another vault, set `LEARNLOOP_VAULT` before running
the app:

```powershell
$env:LEARNLOOP_VAULT = "C:\path\to\my-vault"
npm run dev
```

You can create and prepare a new vault with the CLI before opening it in the
desktop app:

```powershell
learnloop init C:\path\to\my-vault
learnloop doctor --fix-state --vault C:\path\to\my-vault
```

The app also lets you change vaults from the vault path in the top navigation.

For a production build:

```powershell
npm run build
```

This runs the frontend typecheck/build and Tauri build. Build artifacts are
written under `apps/learnloop-tauri/dist/` and
`apps/learnloop-tauri/src-tauri/target/`; installer bundling is currently
disabled in `tauri.conf.json`.

## Core Concepts

- **Vault**: a directory containing `learnloop.toml`, subject folders, notes,
  Learning Objects, Practice Items, goals, and `state.sqlite`.
- **Subject**: a top-level learning area such as `linear-algebra`.
- **Note**: source material or learner notes stored as Markdown with
  frontmatter.
- **Learning Object (LO)**: an atomic unit of knowledge LearnLoop can schedule.
- **Practice Item (PI)**: a prompt tied to an LO and rubric.
- **Proposal**: a Codex or imported `AuthoringProposal` batch. Proposals are
  persisted first, then accepted or rejected.
- **Canonical source**: external source material such as a webpage, arXiv HTML,
  YouTube transcript, or textbook chapter that LearnLoop registers and asks
  Codex to extract into LOs/PIs.

## Recall Coverage And Interventions

LearnLoop's attempt model treats an answer as evidence about a knowledge surface,
not just as a score. The implementation follows
[spec_recall_coverage_interventions.md](spec_recall_coverage_interventions.md):
coverage, reliability, local error severity, facet recall, replay, and
intervention scheduling all flow through one shared attempt application path.

The headline behavior is that an explicit failure such as `dont_know` on a
targeted item is high-coverage negative evidence. It can lower mastery, worsen
the relevant facet recall state, write a locally severe error event, and queue a
repair or diagnostic follow-up even when the failure is no longer surprising.

### Item Metadata

Practice Items can describe the knowledge surfaces they observe:

```yaml
evidence_facets:
  - frobenius-error-formula
  - discarded-singular-values
  - numeric-simplification
evidence_weights:
  frobenius-error-formula: 0.45
  discarded-singular-values: 0.35
  numeric-simplification: 0.20
criterion_facet_weights:
  formula:
    frobenius-error-formula: 0.60
    discarded-singular-values: 0.40
  simplification:
    numeric-simplification: 1.00
```

`evidence_weights` allocate item coverage across facets. Their positive sum is
clamped to item coverage up to `1.0`, then normalized for per-facet updates so a
partial-coverage item is not penalized twice. `criterion_facet_weights` maps
rubric criteria to facets for facet-local outcomes; it is separate from coverage
allocation.

When metadata is missing, LearnLoop falls back deterministically:

1. Use authored or generated `evidence_weights`.
2. Derive coverage from the rubric and `criterion_facet_weights`.
3. Use practice-mode defaults.

Generated Practice Items are expected to include `evidence_facets`,
`evidence_weights`, and `criterion_facet_weights` when they have a rubric.
Proposal validation rejects unknown weight facets and unknown criterion-facet
keys. `doctor` also reports stale or malformed criterion-facet maps.

Facet IDs are canonicalized through `facets.yaml` when present. Aliases are
applied to item metadata, runtime facet recall state, intervention targets, and
Doctor repair checks. `learnloop doctor --fix-state` can merge persisted alias
state into the canonical facet.

### Attempt Evidence

The attempt pipeline separates three concepts:

- `effective_coverage`: how much of the item surface was observed.
- `observation_reliability`: how much to trust the observation.
- `correctness`: how well the learner performed on the observed surface.

Hints, blank answers, attempt type, and response engagement affect coverage.
Grader confidence, self-grade confidence, and mastery dampening from hints
affect reliability. The same factor should not be multiplied into both.

The EKF mastery observation weight is:

```text
effective_coverage
* observation_reliability
* error_sharpening
* independent_evidence_discount
```

`error_sharpening` comes from the frozen event-local severity of any error
event written by the attempt. This sharpens the observation inside the normal
mastery update; it does not apply a separate mastery nudge.

`dont_know` attempts are full engagement with the prompted surface. Unaided
`dont_know` writes `recall_failure`; hinted `dont_know` writes
`scaffold_failure`. Blank non-`dont_know` answers are damped and marked
`manual_review_reason = "blank_answer"`.

Facet recall uses beta-binomial state, stored by Learning Object and optionally
by Practice Item. Facet outcomes are resolved in this order:

1. Rubric criterion points through `criterion_facet_weights`.
2. Error attribution target facets such as `target_evidence_families`.
3. Whole-item correctness as a fallback.

This means an arithmetic or numeric slip can damage the numeric facet without
over-damaging the conceptual facet, even when the final score is high.

### Attempt Debug Data

Every recorded attempt stores an `attempt_debug_payload` row. You can inspect it
with:

```powershell
learnloop show <attempt_id> --json
```

Important fields include:

- `coverage_trace`: source, raw weights, normalized weights, coverage modifiers,
  covered facets, and `effective_coverage`.
- `reliability_trace`: grader confidence, hint mastery factor, attempt-type
  factor, and `observation_reliability`.
- `familiarity_trace`: same-item, surface-family, same-facet discounts, and the
  final independent evidence discount.
- `facet_outcomes`: per-facet observed correctness.
- `severity_traces`: event-local severity inputs and bonuses.
- `error_impact_trace`: max severity, sharpening, and observation weight.
- `prediction_trace`: deterministic IRT/facet-recall predicted correctness.
- `ability_transition`: expected learning-gain audit data, separate from
  observed belief updates.

### Replay, Regrade, And Rebuild

Live attempt recording, deterministic replay, deferred regrade, and the
calibration harness all use the same apply step. Replay never calls Codex or any
AI provider; it reuses persisted attempt scores, current grading evidence, and
persisted error attribution metadata.

Replay is scoped by Learning Object. It clears attempt-derived state for that
scope, then replays attempts in persisted order using each attempt's original
timestamp. It rebuilds mastery, FSRS item state, facet recall, item quality,
error events, surprise, ability-transition audit rows, and debug payloads.

Run a full rebuild after changing the algorithm version, after a migration, or
when Doctor reports stale derived state:

```powershell
learnloop rebuild-derived-state --vault my-vault
learnloop rebuild-derived-state --learning-object lo_svd_definition --vault my-vault
learnloop rebuild-derived-state --json --vault my-vault
```

Deferred regrade first persists new tier-3 grading evidence and updates the
attempt's grade fields, then replays the affected Learning Object from the log.
Fresh validated error attributions are handed into replay so stale error-event
targets do not survive the regrade. Downstream attempts on the same Learning
Object are recomputed against the corrected prior state.

### Interventions

Follow-ups are intervention decisions, not only negative-surprise decisions.
`evaluate_intervention_followup` can trigger on:

- negative Bayesian surprise;
- severe local error;
- repeated same-item failure;
- repeated same-facet failure;
- high probe-unfamiliar probability.

If a suitable existing Practice Item is available, LearnLoop queues one
intervention follow-up and records all trigger reasons. If no suitable item is
available, it persists an `intervention_need` with target facets, desired intent,
trigger reason, and candidate requirements. A per-LO per-session cap suppresses
repeat intervention loops.

The scheduler reward model distinguishes practice, repair, probe, transfer, and
maintenance intents. Expected skill gain is audited in
`ability_transition_events` and may affect scheduling reward, but it is not
written as observed mastery or facet success evidence.

### Calibration

The recall calibration harness runs canonical scenarios through the real attempt
pipeline against temporary vaults:

```powershell
learnloop recall-calibration
learnloop recall-calibration --assert-bands
learnloop recall-calibration --json
```

The table includes error type, event severity, error sharpening, mastery delta,
facet recall delta, bad-item suspicion, and intervention outcome. The asserted
bands come from `recall_coverage.severity_examples` in config, so changing
taxonomy defaults or severity weights is visible in tests and CLI output.

### Doctor Checks

`learnloop doctor` validates recall-coverage metadata and derived state:

- stale derived-state rebuild markers after algorithm-version changes;
- criterion-facet maps with unknown criteria, unknown facets, empty mappings, or
  non-normalized weights;
- auto-normalizable criterion-facet maps, including a proposed normalized map in
  JSON output;
- likely duplicate or aliasable facet IDs;
- item quality warnings when bad-item suspicion crosses the review threshold;
- difficulty miscalibration flags.

Use JSON when wiring the output into tooling:

```powershell
learnloop doctor --json --vault my-vault
learnloop doctor --fix-state --json --vault my-vault
```

## First Run: Canonical Source To Practice

This is the shortest path from an empty vault to a scheduled practice session.

1. Create and enter a vault:

```powershell
learnloop init my-vault
cd my-vault
```

2. Add a subject:

```powershell
learnloop add-subject linear-algebra "Linear Algebra"
```

3. Check Codex settings in `learnloop.toml`.

By default LearnLoop uses the local Codex Python SDK from a sibling Codex
checkout. The SDK starts Codex app-server over stdio and returns schema-checked
JSON proposals to LearnLoop:

```toml
[codex]
provider = "sdk"
checkout_path = "../codex"
sdk_python_path = "sdk/python/src"
model = "gpt-5.4"
reasoning_effort = "minimal"
reasoning_summary = "none"
```

`reasoning_effort` and `reasoning_summary` default to low-usage authoring
settings because LearnLoop only consumes the final structured JSON response.

The older `provider = "http"` transport is only for a LearnLoop-compatible
mock or adapter server that exposes `/authoring-proposal`, `/canonical-ingest`,
and `/grading-proposal`. Pointing LearnLoop directly at Codex's WebSocket
listener will pass `/healthz` but fail authoring calls with HTTP 405.

`learnloop ingest` and Codex-backed `learnloop propose` refuse to run if the
configured runtime is not healthy.

4. Ingest a canonical source.

Website page:

```powershell
learnloop ingest "https://example.edu/svd" --subject linear-algebra
```

Local HTML or Markdown:

```powershell
learnloop ingest C:\sources\svd.html --subject linear-algebra
```

arXiv HTML:

```powershell
learnloop ingest "https://arxiv.org/html/1706.03762v7" --subject linear-algebra
```

YouTube transcript:

```powershell
learnloop ingest "https://www.youtube.com/watch?v=VIDEO_ID" --subject linear-algebra
```

Textbook chapter anchored to an existing LO:

```powershell
learnloop ingest C:\sources\chapter-3.html --kind textbook_chapter --subject linear-algebra --learning-object lo_svd_definition
```

Textbook ingestion is currently an anchored workflow: the subject must already
exist, and each textbook chapter must be attached to one or more existing
Learning Objects. The vault folder name does not create a subject automatically;
create the subject first with `learnloop add-subject`.

When starting from a new textbook, bootstrap the LO map before using
`--kind textbook_chapter`. Use a normal canonical-source ingest or an authoring
proposal to create candidate LOs, then review and accept the proposal:

```powershell
learnloop ingest C:\sources\chapter-3.html --kind website_page --subject linear-algebra --json
learnloop proposals
learnloop show <patch_id>
learnloop accept <patch_id>
learnloop accept <patch_id> --all
```

After the relevant LOs exist, re-run the chapter as a textbook ingest anchored
to the accepted LO ids. Future textbook ingestion should support proposing the
initial LO map directly, but the MVP keeps textbook chapters anchored so new
practice and source spans attach to known learning targets.

The ingester registers a canonical-source note, preserves raw source bytes under
`canonical-sources/raw/`, calls Codex, persists a proposal batch, auto-applies
low-risk source-grounded items, and leaves unsafe or invalid items pending.

Use JSON if you want to capture IDs:

```powershell
learnloop ingest "https://example.edu/svd" --subject linear-algebra --json
```

5. Inspect proposals and accept anything still pending:

```powershell
learnloop proposals
learnloop show <patch_id>
learnloop accept <patch_id>
learnloop accept <patch_id> --all
```

Accept only selected proposal item IDs:

```powershell
learnloop accept <patch_id> --items <item_id_1>,<item_id_2>
```

Reject a batch or selected items:

```powershell
learnloop reject <patch_id>
learnloop reject <patch_id> --items <item_id_1>
```

6. Sync and validate the vault:

```powershell
learnloop doctor --fix-state
```

After accepted content creates active Learning Objects and Practice Items,
`doctor --fix-state` reconciles YAML content into SQLite state. For new
Learning Objects with no prior evidence, LearnLoop starts an initial probe
phase when at least one active local Practice Item is available. This lets the
scheduler begin with probe-EIG instead of waiting for normal review history.

7. See the initial practice queue and why each item was selected:

```powershell
learnloop review
learnloop why <practice_item_id>
```

Newly ingested Practice Items commonly appear with reasons such as
`probe information gain`. Pick one listed Practice Item ID and start practice.

Terminal command:

```powershell
learnloop attempt <practice_item_id> --answer "My answer" --criterion-points correctness=3 --confidence 4
```

Interactive TUI:

```powershell
learnloop today
```

8. After the initial probe phase completes, generate more practice coverage:

```powershell
learnloop generate-practice --dry-run
learnloop generate-practice --target-items-per-lo 5 --max-new-per-lo 3
learnloop proposals
learnloop accept <patch_id>
learnloop doctor --fix-state
learnloop review
```

`generate-practice` targets completed-probe Learning Objects whose active
Practice Item count is below the requested target. It persists a proposal only;
review and accept it the same way as other Codex authoring proposals.

## Command Reference

Most commands accept `--vault <path>`; omit it when the vault is the current
working directory. Script-friendly commands support `--json` where noted.

### `learnloop init`

Create a vault with default config, YAML scaffolding, and SQLite migrations.

```powershell
learnloop init my-vault
learnloop init .
```

### `learnloop add-subject`

Add a subject view and metadata.

```powershell
learnloop add-subject linear-algebra "Linear Algebra" --vault my-vault
```

### `learnloop add-note`

Register source material or learner notes under a subject.

```powershell
learnloop add-note linear-algebra note_svd "SVD overview" --body "SVD factors a matrix..." --vault my-vault
learnloop add-note linear-algebra note_svd "SVD overview" --file .\svd.md --vault my-vault
learnloop add-note linear-algebra note_import "Imported text" --source-type imported --file .\source.md --vault my-vault
```

Valid `--source-type` values are `learner_note`, `canonical_source`, and
`imported`. For normal canonical-source ingestion, prefer `learnloop ingest`
instead of manually adding a `canonical_source` note.

### `learnloop ingest`

Register and extract a canonical source through Codex.

```powershell
learnloop ingest <url-or-file> --subject <subject_id>
learnloop ingest <url-or-file> --kind website_page --subject <subject_id>
learnloop ingest <url-or-file> --kind arxiv_html --subject <subject_id>
learnloop ingest <youtube-url> --kind youtube_video --subject <subject_id> --allow-auto-captions
learnloop ingest <chapter-file> --kind textbook_chapter --subject <subject_id> --learning-object <lo_id>
learnloop ingest <source> --goal <goal_id> --instructions "Focus on worked examples." --json
```

`--kind auto` detects webpages, YouTube URLs, arXiv URLs, and local textbook
chapters when `--learning-object` is supplied. PDFs are not part of the MVP
ingester.

### `learnloop doctor`

Validate vault health and optionally sync derived SQLite state from YAML.

```powershell
learnloop doctor --vault my-vault
learnloop doctor --fix-state --vault my-vault
learnloop doctor --json --vault my-vault
```

Use `--fix-state` after manual YAML edits or after importing content.

### `learnloop review`

Build the due queue and print one-line scheduler reasons. After accepting
canonical-source proposals, run `doctor --fix-state` first so new active
Learning Objects enter their initial probe phase and Practice Items can be
ranked by probe-EIG.

```powershell
learnloop review --vault my-vault
learnloop review --limit 5 --available-minutes 20 --energy low --vault my-vault
learnloop review --json --vault my-vault
```

A fresh canonical-source intake normally starts with a probe queue:

```text
1. pi_best_rank1_error priority=0.123 mode=constructed_response - probe information gain 0.49
```

If `review` prints `No scheduled items.`, check the basics in order:

```powershell
learnloop doctor --fix-state --vault my-vault
learnloop proposals --vault my-vault
learnloop show <patch_id> --vault my-vault
```

There must be accepted active Practice Items attached to active Learning
Objects. A proposal containing only Learning Objects creates learning targets,
but does not create anything the scheduler can ask you to practice yet.

### `learnloop why`

Explain why a Practice Item is scheduled.

```powershell
learnloop why pi_svd_define_001 --vault my-vault
learnloop why pi_svd_define_001 --json --vault my-vault
```

If the item is not currently queued, LearnLoop returns the latest stored
scheduler explanation when one exists.

### `learnloop show`

Inspect any known entity or SQL record by ID.

```powershell
learnloop show lo_svd_definition --vault my-vault
learnloop show pi_svd_define_001 --vault my-vault
learnloop show <patch_id> --vault my-vault
learnloop show <attempt_id> --json --vault my-vault
```

For LOs and PIs, `show` includes content events and active source-staleness
events from canonical-source re-ingestion.

### `learnloop proposals`

List proposal batches and item decisions.

```powershell
learnloop proposals --vault my-vault
learnloop proposals --json --vault my-vault
```

### `learnloop accept`

Apply pending valid proposal items. This writes content through the LearnLoop
storage layer and records change/content events.

```powershell
learnloop accept <patch_id> --vault my-vault
learnloop accept <patch_id> --all --vault my-vault
learnloop accept <patch_id> --items <item_id_1>,<item_id_2> --vault my-vault
```

Next, sync derived state and inspect the queue:

```powershell
learnloop doctor --fix-state --vault my-vault
learnloop review --vault my-vault
```

For newly accepted Practice Items with no learner history, the first scheduled
items should usually be probe items selected by expected information gain.

### `learnloop reject`

Reject pending proposal items. If an auto-applied created item is rejected,
LearnLoop deactivates the generated entity rather than deleting audit history.

```powershell
learnloop reject <patch_id> --vault my-vault
learnloop reject <patch_id> --items <item_id_1> --vault my-vault
```

### `learnloop edit-proposal-item`

Replace a proposal item payload with YAML or JSON and re-run validation.

```powershell
learnloop edit-proposal-item <patch_id> <item_id> --file .\edited-payload.yaml --vault my-vault
learnloop edit-proposal-item <patch_id> <item_id> --file .\edited-payload.json --json --vault my-vault
```

Use this when a generated item is useful but has a duplicate ID, missing rubric,
or payload field that needs human correction before acceptance.

### `learnloop propose`

Create an authoring proposal either through Codex or from an existing
`AuthoringProposal` JSON/YAML file.

Codex-backed:

```powershell
learnloop propose --subjects linear-algebra --notes note_svd --instructions "Create one LO and one short-answer PI." --vault my-vault
```

Inspect request size without spending Codex usage:

```powershell
learnloop propose --subjects linear-algebra --context-stats --json --vault my-vault
```

Import file:

```powershell
learnloop propose --file .\proposal.json --vault my-vault
learnloop propose --file .\proposal.yaml --json --vault my-vault
```

The command persists a proposal batch only. Use `proposals`, `show`, `accept`,
and `reject` to review and apply it.

### `learnloop generate-practice`

Generate a Codex authoring proposal for additional Practice Items after probes
finish.

```powershell
learnloop generate-practice --vault my-vault
learnloop generate-practice --target-items-per-lo 6 --max-new-per-lo 2 --vault my-vault
learnloop generate-practice --subjects linear-algebra --dry-run --json --vault my-vault
```

The command scans active Learning Objects with `lo_probe_state.status =
"complete"` and counts their active Practice Items. Any completed-probe LO below
`--target-items-per-lo` becomes a target; `--max-new-per-lo` caps how many new
items Codex is asked to create for each target in one proposal. Use `--dry-run`
to inspect the target plan without calling Codex.

The result is a proposal batch, not direct content writes. Apply it with:

```powershell
learnloop proposals --vault my-vault
learnloop show <patch_id> --vault my-vault
learnloop accept <patch_id> --vault my-vault
learnloop doctor --fix-state --vault my-vault
```



### ObservationTemplates

ObservationTemplates are reusable schemas for recording structured learning
observations outside the normal "answer this Practice Item" flow. They define
expected response fields and can either store an `observation_events` row only,
or, when the template has an `emits` block and the response is bound to a
Practice Item, convert the observation into a normal self-graded attempt that
updates attempts, mastery, and scheduling state. If an emitting observation does
not have a resolved Practice Item binding, LearnLoop stores it as pending rather
than guessing the target.

### `learnloop observation-templates`

List registered observation templates.

```powershell
learnloop observation-templates --vault my-vault
learnloop observation-templates --all --json --vault my-vault
```

### `learnloop register-observation-template`

Register a YAML or JSON observation template.

```powershell
learnloop register-observation-template --file .\template.yaml --domain linear-algebra --version 1.0 --title "SVD oral check" --vault my-vault
learnloop register-observation-template --file .\template.yaml --domain linear-algebra --version 1.0 --title "SVD oral check" --inactive --vault my-vault
```

### `learnloop record-observation`

Record a structured observation and optionally bind it to an LO, PI, subject, or
session. Some templates emit an attempt.

```powershell
learnloop record-observation <template_id> --response-json '{"score": 3}' --subject linear-algebra --vault my-vault
learnloop record-observation <template_id> --response-file .\response.yaml --learning-object-id lo_svd_definition --vault my-vault
learnloop record-observation <template_id> --practice-item-id pi_svd_define_001 --session-id session_001 --json --vault my-vault
```

### `learnloop debug-advance`

Debug-only command for testing scheduling behavior after time passes. It advances
the vault by aging derived SQLite learning-state timestamps by the requested
number of days; YAML content is not modified. This makes FSRS due dates,
forgetting risk, recent-error decay, probe posterior timing, and probe-EIG
selection behave as if the scheduler clock were that many days later.

```powershell
learnloop debug-advance 7 --vault my-vault
learnloop debug-advance 7 --json --vault my-vault
learnloop review --vault my-vault
```

### `learnloop rebuild-derived-state`

Replay persisted attempts to rebuild attempt-derived SQLite state for all
Learning Objects, or for one Learning Object at a time. Rebuild does not call
Codex or any AI provider; it reuses persisted grades and grading evidence.

```powershell
learnloop rebuild-derived-state --vault my-vault
learnloop rebuild-derived-state --learning-object lo_svd_definition --vault my-vault
learnloop rebuild-derived-state --learning-object lo_a --learning-object lo_b --json --vault my-vault
```

The rebuild writes a marker with the active `algorithm_version`. Doctor reports
the marker as stale when the configured algorithm version changes.

### `learnloop recall-calibration`

Developer harness for the recall coverage and intervention scenarios. It runs
canonical attempts through the real attempt pipeline and prints a stable table
for reviewing severity, error sharpening, mastery movement, facet recall,
bad-item suspicion, and intervention decisions.

```powershell
learnloop recall-calibration
learnloop recall-calibration --assert-bands
learnloop recall-calibration --json
```

Use `--assert-bands` in checks when changing error taxonomy defaults,
`recall_coverage` config, mastery weighting, or intervention thresholds.

### `learnloop attempt`

Record an answer, grade it with Codex when available, fall back to self-grade,
update mastery/FSRS state, and evaluate surprise/follow-up logic.

```powershell
learnloop attempt pi_svd_define_001 --answer "A=U Sigma V^T" --criterion-points correctness=3 --confidence 4 --vault my-vault
learnloop attempt pi_svd_define_001 --answer "I do not know" --fatal-errors blank_answer --confidence 2 --error-type recall_failure --vault my-vault
learnloop attempt pi_svd_define_001 --attempt-type hinted_attempt --hints-used 1 --available-minutes 10 --json --vault my-vault
```

If `--answer` or rubric points are omitted, the CLI prompts interactively.

### `learnloop today`

Launch the Textual TUI for the daily queue and practice flow.

```powershell
learnloop today --vault my-vault
```

## Proposal File Shape

`learnloop propose --file` accepts an `AuthoringProposal`. A minimal import file
looks like this:

```json
{
  "summary": "Add one SVD item.",
  "source_refs": [
    {"ref_type": "manual_context", "ref_id": "manual_svd"}
  ],
  "items": [
    {
      "client_item_id": "lo_svd_rank",
      "item_type": "learning_object",
      "operation": "create",
      "proposed_entity_id": "lo_svd_rank",
      "source_ref_ids": ["manual_svd"],
      "rationale": "Add an atomic LO.",
      "review_route": "review_required",
      "payload": {
        "title": "SVD rank approximation",
        "subjects": ["linear-algebra"],
        "concept_id": "singular_value_decomposition",
        "knowledge_type": "application",
        "summary": "SVD can produce low-rank approximations."
      }
    }
  ]
}
```

## Development

```powershell
python -m pip install -e .[dev]
python -m pytest -q
python -m compileall -q src tests
```

The automated test suite is the source of truth for acceptance gates. Tests run
without Codex, Textual terminals, or network access unless a specific adapter is
mocked.

Python logs are only written for the sidecar, and only to a file if you set an env var.

  By default:

  - CLI attempts: no Python log file.
  - Sidecar/Tauri: JSON logs go to stderr.
  - Sidecar file logging: only if LEARNLOOP_SIDECAR_DEBUG_LOG is set.

  To capture detailed Bayesian surprise / IRT math from the GUI sidecar:
```powershell
  $env:LEARNLOOP_SIDECAR_DEBUG = "1"
  $env:LEARNLOOP_SIDECAR_DEBUG_LOG = "$PWD\sidecar-debug.jsonl"
```
  Then run the app/sidecar and answer one question. Look for JSONL events named:

  state_update

  codex.prompt

  codex.response

  codex.http.request

  codex.http.response

  `codex.prompt` / `codex.response` contain the full Codex SDK prompt and final response.
  `codex.http.request` / `codex.http.response` contain the full legacy HTTP adapter request and response payloads.
  These logs can include learner answers and source material, so treat debug JSONL files as private.

  `state_update` includes fields like expected_correctness, innovation, kalman_gain, variance_reduction, predictive_surprise,
  learnloop show <attempt_id> --json

  - predicted_error_type_dist
  - observed_joint_bucket
  - predictive_surprise
  - bayesian_surprise
  - posterior_delta

  The Bayesian surprise formula itself is in src/learnloop/services/surprise.py:83. The mastery/IRT update trace math is
  in src/learnloop/services/mastery.py:282.
