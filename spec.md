# Spec: **LearnLoop**

## 1. Product definition

**LearnLoop** is a standalone, local-first Python application for adaptive learning. It is built around a Textual TUI, a local learning vault, and an optional Codex app-server integration through the Python SDK.

LearnLoop is **not** a fork of Codex and does not depend on a checked-out Codex source tree. Codex is an AI runtime that LearnLoop can call through the `openai-codex` / app-server SDK. The LearnLoop application, schemas, scheduler, TUI, storage layer, and vault tools live in their own Python package.

The user creates or opens a local vault like:

```text
my-learning-vault/
  AGENTS.md
  learnloop.toml
  state.sqlite
  profile/
  subjects/
  errors/
  sessions/
  exports/
  prompts/
```

Then they run the TUI:

```bash
learnloop today
```

or use focused CLI commands:

```bash
learnloop review
learnloop diagnose
learnloop generate
learnloop inbox recent
```

The TUI is the primary product surface. The CLI exists for automation, quick review, and debugging.

LearnLoop uses Codex to:

* read the learner’s profile,
* inspect notes,
* generate retrieval questions,
* diagnose errors,
* grade free-text answers against rubrics,
* propose changes to Learning Objects, Practice Items, concept graphs, rubrics, and error logs,
* provide Socratic tutoring and transfer prompts.

LearnLoop itself owns validation, persistence, scheduling, and mastery updates. AI output is treated as a structured proposal unless the operation is explicitly configured as safe to auto-accept.

---

# 2. Why this design is good

This architecture keeps the system useful even without a model call, while still letting Codex provide high-leverage tutoring and content generation.

The learning system is represented as an inspectable local project:

```text
The learner profile is a file.
The curriculum is a file tree.
The scheduler and attempt history are SQLite state.
The error notebook is Markdown.
Learning Objects and Practice Items are YAML.
Codex-readable context is exported before AI turns.
```

This gives you:

* no hosted backend,
* no custom auth,
* transparent memory,
* version-controlled learning history,
* editable prompts,
* easy debugging,
* domain-specific extension points,
* AI assistance without making the model the source of truth.

---

# 3. Core architecture

```text
┌─────────────────────────────────────┐
│              User                   │
└─────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│       LearnLoop Textual TUI          │
│  primary interaction surface         │
└─────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│       LearnLoop Python Core          │
│  scheduler, mastery, grading,        │
│  vault services, inbox, sessions     │
└─────────────────────────────────────┘
        │                         │
        ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐
│ Local Learning Vault│   │ CLI / automation     │
│ MD + YAML + SQLite  │   │ Typer commands       │
└─────────────────────┘   └─────────────────────┘
        │
        │ optional AI turn
        ▼
┌─────────────────────────────────────┐
│ LearnLoop Codex SDK adapter          │
│ wraps openai_codex.Codex / threads   │
└─────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│   codex app-server via SDK           │
│  long-running process, one per app   │
└─────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│       Codex model runtime            │
│  via configured Codex auth           │
└─────────────────────────────────────┘
```

LearnLoop’s core must work without Codex for manual content, review, scheduling, and attempt logging. Codex is used for tasks that need language understanding, generation, or free-text grading.

The **LearnLoop Codex SDK adapter** is a small wrapper around the public Python SDK. It starts or connects to Codex app-server, creates/resumes threads, streams turns to the TUI, requests structured outputs where appropriate, and maps SDK events into LearnLoop UI events.

MVP does not hand-roll JSON-RPC framing or require custom LearnLoop tool registration inside Codex. AI turns return structured proposals; LearnLoop validates those proposals with Pydantic, applies local writes through its own storage layer, and logs provenance. A lower-level protocol adapter can be added later only if the SDK does not expose required capabilities.

---

# 4. Repository layout

The learning app should be a local repo.

```text
learning-vault/
  AGENTS.md
  learnloop.toml
  README.md
  state.sqlite                  # canonical mutable state (see "Source of truth" below)

  profile/                      # narrative memory
    student.md
    goals.md
    preferences.md
    constraints.md

  subjects/
    linear-algebra/
      subject.md
      concept-graph.yaml        # concepts, prerequisites, confusables
      notes/                    # long-form learner-authored notes
        eigenvectors.md
        svd.md
        pca.md
      learning-objects/         # one file per Learning Object (durable unit)
        lo_eigenvectors_def.yaml
        lo_svd_decomposition.yaml
        lo_pca_via_svd.yaml
      practice-items/           # concrete prompts; many per Learning Object
        pi_eigenvectors_def_001.yaml
        pi_svd_completion_001.yaml
        pi_pca_transfer_001.yaml
      worked-examples/
        svd-worked-example-001.md
      rubrics/                  # optional per-item rubrics (override the defaults)
        pi_pca_transfer_001.rubric.yaml
      errors.md                 # narrative subject-specific error notebook
      reflection.md             # learner reflections

    korean/
      subject.md
      concept-graph.yaml
      vocab.yaml                # compact LO list for bulk vocabulary
      grammar.md
      learning-objects/
      practice-items/
      errors.md

    research-papers/
      subject.md
      concept-graph.yaml        # papers, methods, assumptions, claims, evidence links
      notes/
      canonical-sources/
      learning-objects/
      practice-items/
      errors.md

    vod-review/
      subject.md
      concept-graph.yaml        # skills, cues, situations, recurring mistakes
      notes/
      media-index.yaml          # local video/audio/image references + timestamps
      learning-objects/
      practice-items/
      errors.md

  inbox/                        # AI-generated content awaiting review
    pending/
      2026-05-12-svd-variants.yaml
    accepted/                   # archive of accepted items (provenance trail)
    rejected/

  canonical-sources/            # trusted reference material for ingestion
    textbooks/
      strang-linear-algebra-ch7.pdf
    lectures/
    ingest-log.md               # what was extracted from what, when, by what prompt

  sessions/                     # one markdown log per session
    2026-05-12.md

  evals/
    grading-goldens/            # local grading regression fixtures
      short-answer.yaml
      proof-reconstruction.yaml

  exports/                      # generated agent context (read-only, regenerated)
    current-state.md
    due-today.yaml
    weak-concepts.yaml
    recent-errors.md
    mastery-snapshot.yaml

  errors/
    global-error-log.md         # cross-subject narrative
    error-taxonomy.yaml         # canonical error type definitions + impact maps

  prompts/                      # editable agent prompt templates
    generate_retrieval.md
    diagnose_solution.md
    generate_transfer.md
    grade_rubric.md
    socratic_tutor.md
    interleaving_set.md
    ingest_canonical_source.md

  rubrics/                      # default rubrics by practice_mode × knowledge_type
    short_answer.yaml
    proof_reconstruction.yaml
    transfer.yaml

  .learnloop/                   # app-managed local operational files
    backups/
    session-checkpoints/
```

This lets the agent work naturally because everything is inspectable and editable.

### Source of truth boundaries

| Layer | Authoritative for | Read/edited by |
| --- | --- | --- |
| **Markdown** | Narrative memory: profile, goals, subject overviews, notes, error notebooks, sessions, reflections, codex-readable context | Human + agent |
| **YAML** | Structured human-editable content: concept graphs, learning objects, practice items, rubrics, error taxonomy, domain templates, difficulty priors | Human + agent |
| **`state.sqlite`** | Mutable computed state: practice attempts, FSRS item-memory state, learning-object + concept mastery, due queue, generated-item registry, error events, session metadata, grading evidence, Practice Item content hashes, active/dormant status | LearnLoop core + scheduler (humans read via CLI/TUI views, not directly) |
| **`exports/`** | Read-only derived context for the agent: snapshots of "what is due", "weak concepts", "recent errors", mastery summary | Regenerated by `learnloop` before each session and after attempt batches |

Rule of thumb: if the user or the agent should comfortably edit it by hand and it benefits from being human-readable, it's Markdown or YAML. If it's an event log, a schedule, or a computed state requiring consistency, it's SQLite.

### Global (cross-vault) profile

For users who run more than one vault (e.g. one for school, one for personal study), `learnloop` reads a global profile:

```text
~/.learnloop/
  profile.md            # baseline learner profile (background, preferences, style)
  preferences.md
  AGENTS.md             # optional global agent rules (vault AGENTS.md takes precedence)
```

When a vault loads, `profile/student.md` is merged on top of `~/.learnloop/profile.md`. Vault values win on conflict. The agent reads the merged result; the on-disk files stay separate. Cross-vault concept reuse is **out of scope** — each vault owns its concepts, Learning Objects, and SQLite state independently.

### Subject and domain extension model

LearnLoop must be extensible across subjects. A subject is the learner-facing unit (`linear-algebra`, `korean`, `research-papers`, `vod-review`). A domain is an implementation hint that chooses templates, rubrics, practice modes, and import helpers.

Recommended first-party domains:

| Domain | Subjects it should support | MVP scope |
| --- | --- | --- |
| `math_stats_ml` | linear algebra, statistics, ML, proofs, derivations | Text prompts, LaTeX, worked examples, proof reconstruction, transfer |
| `research_papers` | paper reading, method understanding, assumptions, claims, replications | Canonical-source ingestion from PDFs/notes, claim/evidence maps, active recall, critique prompts |
| `language` | Korean, vocabulary, grammar, reading, writing | Text-based vocab/grammar/translation/dictation metadata; audio and live chat later |
| `motor_vod` | self VOD review, dance, esports, instrument practice, sport technique | Timestamped observations, error patterns, cue recall, practice plans; automated video/audio analysis later |
| `general` | any structured learning subject | Generic Learning Objects, Practice Items, notes, errors, and scheduling |

Every domain extension can provide:

- subject scaffold templates,
- default `KnowledgeType` and `PracticeMode` recommendations,
- rubrics,
- error taxonomy additions,
- import/ingestion helpers,
- TUI panels or commands.

Domain-specific features must degrade gracefully to the generic model. For MVP, all domains are text-first; audio-based language practice, live chat, and automated VOD/media analysis are later extensions.

---

# 5. `AGENTS.md`

This is the most important file. Codex should be guided by project instructions.

Example:

```markdown
# LearnLoop Agent Instructions

You are operating inside a local learning vault.

Your job is to help the learner build durable, transferable knowledge using:
- retrieval practice
- spaced repetition
- successive relearning
- interleaving
- worked examples
- errorful generation
- deliberate practice
- transfer challenges

## Rules

1. Do not merely explain. Prefer active practice.
2. Do not give full solutions before the learner attempts.
3. Use hint ladders when possible.
4. Diagnose errors by type.
5. Return structured proposals for Markdown/YAML changes; LearnLoop applies validated writes.
6. Distinguish recall failure, concept failure, procedure failure, and transfer failure.
7. Use worked examples for novice/high-element-interactivity material.
8. Use retrieval and interleaving for mature material.
9. Keep review intervals consistent with the scheduler.
10. When generating practice, output structured YAML or JSON when requested.

## Core loop

Attempt → diagnose → feedback → schedule → retest → transfer.

## Student files

Read these first when relevant:
- profile/student.md
- profile/goals.md
- profile/preferences.md
- errors/global-error-log.md
- current subject's subject.md
- current subject's concept-graph.yaml
- current subject's learning-objects/
- current subject's practice-items/
- exports/due-today.yaml
- exports/weak-concepts.yaml
```

This turns Codex into a learning agent instead of a generic coding agent.

---

# 6. `learnloop.toml`

The app should have one configuration file.

```toml
[student]
name = "Chloe"
timezone = "America/New_York"
default_session_minutes = 75

[ai]
provider = "codex-sdk"                  # use the Python openai-codex SDK
preferred_model = "gpt-5.5"
auth_mode = "chatgpt"
structured_output = true
grader_role = "rubric-grader"
server_startup_timeout_seconds = 10
server_shutdown_timeout_seconds = 5
restart_on_crash = true
offline_mode_allowed = true             # review/scheduling still work without Codex

[scheduler]
algorithm = "fsrs_plus_object_mastery"  # py-fsrs at the item layer; EMA at the object layer
default_retention = 0.9
review_intervals = [1, 3, 7, 14, 30, 60, 120]

[storage]
database = "state.sqlite"
markdown_memory = true
yaml_learning_content = true
autocommit = false
backup_dir = ".learnloop/backups"
max_backups = 20
write_change_batches = true                   # group related writes for undo/rollback

[tui]
theme = "minimal"
show_confidence_prompt = true
show_error_taxonomy = true
show_scheduler_explanations = true
resume_interrupted_session = true

[learning]
target_success_rate_min = 0.70
target_success_rate_max = 0.85
prefer_active_recall = true
use_interleaving = true
use_worked_examples_for_novices = true
readiness_gate = true                          # prompt energy/sleep/minutes at session start
focus_blocks = "pomodoro"                      # pomodoro | continuous | none (pomodoro = 25/5)
break_practice = "warm_up_retrieval"           # what fills pomodoro breaks
disguised_retest_after_resolution = true       # retest resolved misconceptions in novel framings

[profile]
inherit_global = true                          # merge ~/.learnloop/profile.md into vault profile
global_path = "~/.learnloop"

[inbox]
# AI-generated content review policy. See "Provenance, Inbox, and Canonical Sources".
auto_accept_canonical_direct = true            # verbatim extraction from canonical sources
auto_accept_canonical_transform = true         # cloze/format transforms of canonical content
auto_accept_variants = true                    # variants of an already-approved Practice Item
max_auto_variants_per_item = 5
require_review_for = ["proof", "derivation", "transfer", "misconception"]
ephemeral_session_items = true                 # in-session generations are used, not saved
notify_on_auto_accept = true                   # TUI shows what was added and why
recent_window_days = 14                        # `learnloop inbox recent` review window
easy_deactivate = true                         # recently auto-accepted items can be deactivated in one action

[grading]
rubric_scale = 4                               # 0-4 rubric → 0.00 / 0.25 / 0.55 / 0.80 / 1.00
auto_update_mastery = true                     # agent grades update mastery unless manual review is triggered
grader_confidence_floor = 0.6                  # below this, require confirmation before mastery update
eval_goldens_path = "evals/grading-goldens"
manual_review_triggers = [
  "low_grader_confidence",
  "missing_rubric",
  "user_disputes_grade",
  "long_ambiguous_answer",
  "proof_subtlety",
  "high_stakes_canonical_item",
]

[mastery]
update_rule = "ema"                            # EMA per dimension per Learning Object
ema_alpha = 0.2
difficulty_aware = true                        # hard success raises more; easy failure lowers more
error_aware_cross_dimension = true             # apply error_impacts from error-taxonomy.yaml
flag_high_confidence_wrong = true              # mark as misconception; trigger repair loop
fluency_signals = ["latency_vs_expected", "hints_used", "pause_count", "consistency"]

[import_export]
allow_anki_import = false                      # later extension; text/YAML import/export first
default_export_format = "learnloop-bundle"     # learnloop-bundle | markdown | yaml
include_attempt_history_by_default = false

[sessions]
autosave_seconds = 10
resume_interrupted = true

[sample]
include_sample_vault = true
```

---

# 7. Markdown memory files

## `profile/student.md`

```markdown
# Student Profile

## Background
- Strong applied math / ML orientation.
- Comfortable with Python.
- Likes rigorous derivations.
- Wants intuitive understanding and transfer, not just memorization.

## Current goals
- Build durable understanding of math, ML, statistics, Korean, and project-specific research topics.

## Preferred style
- Explain intuition first, then formalism.
- Use LaTeX for math.
- Give examples and counterexamples.
- Ask active recall questions.
```

## `profile/goals.md`

```markdown
# Learning Goals

## Active Goals

### Linear Algebra for ML
Target: transfer-ready understanding
Retention horizon: 1 year
Priority: high

### Korean
Target: conversational + grammar accuracy
Retention horizon: ongoing
Priority: medium

### Fine-Gray / causal survival modeling
Target: research-level understanding
Retention horizon: 1 year
Priority: high
```

## `subjects/linear-algebra/subject.md`

```markdown
# Linear Algebra

## Purpose
Understand linear algebra deeply enough to use it in ML, statistics, optimization, and research.

## Active topics
- Vector spaces
- Linear maps
- Eigenvectors
- SVD
- PCA
- Orthogonality
- Projections

## Known weaknesses
- Need more transfer practice between SVD, PCA, and eigendecomposition.
```

---

# 8. Concept graph format

Use YAML because it is human-editable and Codex-readable.

```yaml
concepts:
  eigenvectors:
    title: Eigenvectors
    type: concept
    prerequisites:
      - matrix_multiplication
      - linear_maps
    mastery:
      recall: 0.86
      procedure: 0.74
      schema: 0.58
      transfer: 0.41
    common_confusions:
      - singular_vectors
      - principal_components
    next_action: interleaved_discrimination

  svd:
    title: Singular Value Decomposition
    type: procedure
    prerequisites:
      - orthogonality
      - eigenvectors
      - matrix_transpose
    mastery:
      recall: 0.62
      procedure: 0.48
      schema: 0.39
      transfer: 0.22
    next_action: worked_example_completion
```

The important thing is that mastery is multidimensional:

```text
Recall ≠ procedure ≠ schema ≠ transfer.
```

That is the whole point of the app.

---

# 9. Learning Objects and Practice Items

The vault separates **what is being learned** from **how it is currently being tested**.

```text
Concept             — a node in the concept graph (e.g. "Fine-Gray competing risks")
  └─ Learning Object — a durable unit of knowledge or skill with stable identity
                       (e.g. "Fine-Gray subdistribution hazard definition")
       └─ Practice Item — a concrete prompt with one primary practice_mode
                          (e.g. "Define it from memory", "Contrast with cause-specific hazard")
```

A Learning Object can have many Practice Items across many practice modes. The Practice Item is what gets scheduled by FSRS; the Learning Object is what carries multi-dimensional mastery. The Concept aggregates over its Learning Objects.

## Learning Object (`learning-objects/<lo_id>.yaml`)

```yaml
id: lo_fine_gray_subhazard
title: Fine-Gray subdistribution hazard
subject: survival-analysis
concept: fine_gray_competing_risks
knowledge_type: definition          # see KnowledgeType enum
status: active                      # active | dormant | resolved (resolved is for misconception LOs)
contradicts: null                   # only set on misconception LOs; points to the LO this misconception attacks
prerequisites:
  - lo_cause_specific_hazard
  - lo_competing_risks_setup
difficulty_prior: 0.7
provenance:
  origin: human                     # human | canonical_extract | ai_generated | ai_variant
  source_id: null
created_at: 2026-05-01
```

Mastery dimensions (recall, schema, procedure, transfer, fluency, explanation, calibration) are **not** stored in this YAML — they live in `state.sqlite` and are updated from attempts. The YAML is a stable, human-editable description.

## Practice Item (`practice-items/<pi_id>.yaml`)

```yaml
id: pi_fg_subhazard_define_001
learning_object_id: lo_fine_gray_subhazard
practice_mode: short_answer         # see PracticeMode enum
attempt_types_allowed:              # see AttemptType enum
  - independent_attempt
  - hinted_attempt
  - dont_know
target_mastery_dimensions:          # what an attempt at this item is evidence for
  - recall
  - schema
  - explanation
mastery_weights:                    # how much each dimension is updated by this item
  recall: 0.45
  schema: 0.45
  explanation: 0.10
prompt: "Define the Fine-Gray subdistribution hazard in your own words."
expected_answer: >
  It models the subdistribution hazard for a target event in the presence
  of competing risks, keeping competing-event cases in a modified risk set
  so the model targets the cumulative incidence function.
difficulty: 0.72
tags: [survival, competing-risks, definition]
provenance:
  origin: human
  source_id: null
  review_status: approved           # approved | pending_review | auto_accepted | rejected
  parent_item_id: null              # set if origin == ai_variant
grading_rubric:                     # optional inline rubric; falls back to defaults if absent
  max_points: 4
  criteria:
    - id: target_event
      points: 1
      description: "Mentions event/cause of interest."
    - id: competing_risks
      points: 1
      description: "Mentions competing risks/events."
    - id: modified_risk_set
      points: 1
      description: "Explains that competing-event cases remain in a modified risk set."
    - id: cumulative_incidence
      points: 1
      description: "Connects Fine-Gray to cumulative incidence rather than ordinary cause-specific hazard."
  fatal_errors:
    - id: says_same_as_cause_specific
      description: "Claims Fine-Gray is the same as cause-specific Cox."
      max_grade: 2
    - id: treats_hazard_as_probability
      description: "Defines hazard as a probability without qualification."
      max_grade: 3
```

## Item-memory state (SQLite, not YAML)

Each Practice Item has FSRS-managed state stored in `state.sqlite`:

```sql
CREATE TABLE practice_item_state (
  practice_item_id   TEXT PRIMARY KEY,
  difficulty         REAL,           -- FSRS
  stability          REAL,           -- FSRS
  retrievability     REAL,           -- FSRS
  due_at             TEXT,
  active             INTEGER,        -- 0 = dormant, 1 = in rotation
  content_hash       TEXT,           -- detect edits to the prompt/expected_answer
  last_attempt_at    TEXT
);
```

This separation is deliberate: YAML changes when *content* changes (rewording a prompt, fixing a rubric). SQLite changes after every attempt. They are kept in sync by the content hash.

---

# 10. TUI design

The TUI should feel like a terminal-native learning cockpit.

Recommended stack:

```text
Python
Textual
Rich
Typer
SQLite
YAML
Markdown
Codex SDK adapter
```

## Main screen

```text
┌────────────────────────────────────────────┐
│ LearnLoop                                  │
│ Today: Tuesday, May 12, 2026               │
├────────────────────────────────────────────┤
│ Due Reviews: 34                            │
│ Weak Concepts: 7                           │
│ Transfer Gaps: 4                           │
│ Suggested Session: 75 min                  │
├────────────────────────────────────────────┤
│ 1. Start Today's Loop                      │
│ 2. Review Due Items                        │
│ 3. Generate Practice                       │
│ 4. Diagnose Solution                       │
│ 5. Error Notebook                          │
│ 6. Concept Graph                           │
│ 7. Open Codex Tutor                        │
└────────────────────────────────────────────┘
```

## Session start (readiness gate)

Shown before every session if `[learning].readiness_gate = true`. Captured to the `sessions` table and fed into the scheduler’s readiness modulation.

```text
┌────────────────────────────────────────────┐
│ Session Start                              │
├────────────────────────────────────────────┤
│ Energy:        ( ) low  (•) med  ( ) high  │
│ Sleep last:    ( ) <6h  (•) 6-8h  ( ) >8h  │
│ Available:     [ 75 ] minutes              │
│ Focus pattern: (•) pomodoro 25/5           │
│                ( ) continuous              │
├────────────────────────────────────────────┤
│ [Start Session]                            │
└────────────────────────────────────────────┘
```

## Today’s loop

When `focus_blocks = "pomodoro"`, deep-work blocks are 25 min with 5-min retrieval breaks (the break fills with warm-up retrieval rather than idle time). When `continuous`, the loop runs straight through.

```text
┌────────────────────────────────────────────┐
│ Today’s Learning Loop  (pomodoro 25/5)     │
├────────────────────────────────────────────┤
│ Warm-up Retrieval       12 min             │
│ Deep Work block 1       25 min             │
│   ↳ break: retrieval     5 min             │
│ Deep Work block 2       25 min             │
│ Weakness Repair         18 min             │
│ Transfer Challenge      15 min             │
└────────────────────────────────────────────┘
```

## Practice screen

```text
┌────────────────────────────────────────────┐
│ Concept: SVD → PCA                         │
│ Mode: Explain from memory                  │
│ Difficulty: 0.78                           │
│ Why now: transfer gap + recent error        │
├────────────────────────────────────────────┤
│ Prompt:                                    │
│ Explain how PCA can be computed using SVD. │
├────────────────────────────────────────────┤
│ Your answer:                               │
│ _                                          │
├────────────────────────────────────────────┤
│ [Submit] [Hint] [Skip] [Open Codex Tutor]  │
└────────────────────────────────────────────┘
```

The `Why now` line opens a scheduler explanation panel. It shows the score components that selected the item:

```text
Why this item?
  Forgetting risk        0.24   due today, retrievability 0.21
  Transfer gap           0.15   recall 0.86, transfer 0.38
  Recent error           0.12   missed centering assumption yesterday
  Readiness adjustment  +0.00   medium energy
  Next action            transfer
```

## Feedback screen

```text
┌────────────────────────────────────────────┐
│ Feedback                                   │
├────────────────────────────────────────────┤
│ Correctness: Partial                       │
│ Error type: Missing centering assumption   │
│ Confidence: 4/5                            │
│ Hint usage: 0                              │
├────────────────────────────────────────────┤
│ Diagnosis:                                 │
│ You remembered the SVD connection, but did │
│ not mention that PCA requires centered data│
│ or covariance structure.                   │
├────────────────────────────────────────────┤
│ Next action:                               │
│ Schedule contrastive PCA/SVD repair drill. │
└────────────────────────────────────────────┘
```

## Recently added review

Shown after auto-accepted canonical transforms or approved-item variants. It is also reachable through `learnloop inbox recent`.

```text
┌────────────────────────────────────────────┐
│ Recently Added                             │
├────────────────────────────────────────────┤
│ batch_2026_05_12_001  canonical_transform  │
│ 6 Practice Items, 2 Learning Objects        │
│ Source: strang-linear-algebra-ch7.pdf       │
├────────────────────────────────────────────┤
│ [Open] [Edit] [Deactivate] [Rollback Batch] │
└────────────────────────────────────────────┘
```

Rollback should be available from this view, but it should explain whether the operation will deactivate items, restore previous file contents, or both.

## Session resume

The TUI autosaves session state every `[sessions].autosave_seconds`. If the previous process exited with an unfinished session, `learnloop today` shows:

```text
┌────────────────────────────────────────────┐
│ Resume interrupted session?                │
├────────────────────────────────────────────┤
│ Subject: survival-analysis                 │
│ Current item: pi_fg_subhazard_define_001   │
│ Unsaved answer: yes                        │
│ Started: 2026-05-12 09:41                  │
├────────────────────────────────────────────┤
│ [Resume] [Archive Session] [Start New]      │
└────────────────────────────────────────────┘
```

Resume must preserve the session id, current Practice Item, pending answer text, in-flight grading proposal if any, focus block state, and readiness metadata.

---

# 11. CLI commands

The TUI is primary, but core actions should have CLI equivalents for automation, debugging, and quick review.

```bash
learnloop init
learnloop init --sample                            # create a demo vault with seeded data
learnloop today                                    # opens TUI on Today's Loop
learnloop resume                                   # resume interrupted session if one exists
learnloop review                                   # quick CLI review (no TUI)
learnloop readiness                                # log energy/sleep/minutes for the next session
learnloop add-subject "linear-algebra"
learnloop add-note subjects/linear-algebra/notes/svd.md
learnloop import notes ./notes --subject linear-algebra
learnloop export subject linear-algebra --format learnloop-bundle
learnloop extract subjects/linear-algebra/notes/svd.md
learnloop ingest canonical-sources/strang-ch7.pdf  # SDK-backed canonical-ingestor role
learnloop inbox                                    # list/accept/reject pending generated items
learnloop inbox recent                             # review recently auto-accepted content
learnloop undo batch <change_batch_id>             # roll back/deactivate a generated batch
learnloop generate-practice --concept svd --mode retrieval
learnloop generate-transfer --concept pca
learnloop diagnose solution.md --concept fine-gray
learnloop why <pi_id>                              # explain why an item is scheduled now
learnloop errors
learnloop misconceptions                           # list active misconception LOs
learnloop lineage <pi_id>                          # provenance tree for a Practice Item
learnloop graph linear-algebra
learnloop session-summary
learnloop exports refresh
learnloop eval grading                             # run local grading regression fixtures
learnloop doctor                                   # validate vault health
learnloop backup create
learnloop backup list
learnloop backup restore <backup_id>
```

CLI parity also makes the storage and scheduler easier to test outside the TUI.

---

# 11.5. Import, Export, Backup, and Health Checks

LearnLoop should avoid lock-in and make vault state recoverable.

## Import/export

MVP import/export is text-first:

- `learnloop import notes <path> --subject <subject>` copies or references Markdown notes into a subject.
- `learnloop export subject <subject> --format learnloop-bundle` exports subject YAML, Markdown, rubrics, concept graph, and optional attempt history.
- `learnloop export subject <subject> --format markdown` exports a human-readable study packet without scheduler state.
- Later Anki import/export can be added behind `[import_export].allow_anki_import`.

`learnloop-bundle` is a zip-compatible directory layout with a manifest:

```yaml
format: learnloop-bundle
version: 1
subject: linear-algebra
includes:
  learning_content: true
  attempt_history: false
  generated_item_history: true
created_at: 2026-05-12T14:00:00Z
```

Attempt history is excluded by default because it may contain personal answers and reflections.

## Backup

`learnloop backup create` creates a timestamped local backup containing `state.sqlite`, Markdown/YAML content, prompts, rubrics, and config. Backups are written under `[storage].backup_dir` and pruned according to `[storage].max_backups`.

Restore must require an explicit backup id and should refuse to overwrite an open/dirty vault unless the user confirms.

## Vault health check

`learnloop doctor` validates:

- config parse and version compatibility,
- SQLite migration status,
- YAML schema validity,
- duplicate ids,
- broken Learning Object / Practice Item links,
- broken concept references,
- missing source ids for canonical content,
- stale content hashes,
- orphaned SQLite rows,
- invalid due dates or timezone values,
- missing prompt templates and rubrics,
- rollback metadata completeness for recent change batches.

The command returns non-zero on errors, prints warnings separately from failures, and offers safe repair commands where possible.

---

# 12. Agent integration (Codex App Server SDK)

LearnLoop integrates with Codex through the Python app-server SDK. The application must not depend on a forked Codex checkout, and MVP should not implement raw JSON-RPC framing directly.

## The adapter: `CodexSdkClient`

A thin adapter in `learnloop/codex/` wraps the SDK and exposes learning-specific methods to the rest of the app:

- `start()` / `close()` — own SDK client lifetime and app-server process lifetime.
- `ensure_thread(subject_id, purpose)` — create or resume a Codex thread for a subject/purpose.
- `run_structured(prompt, context, output_schema)` — run a turn and parse model output into a Pydantic schema.
- `stream_tutor_turn(input, context)` — stream a tutoring turn into the TUI.
- `grade_answer(practice_item, learner_answer, rubric)` — return structured grading evidence.
- `generate_practice(context, constraints)` — return proposed Learning Objects / Practice Items / variants.
- `ingest_canonical_source(source, constraints)` — return a proposed structured patch.

The rest of LearnLoop never imports SDK wire models directly. It calls this adapter and receives LearnLoop-owned Pydantic models.

Every SDK-backed operation creates an `agent_runs` row with the role/purpose, model, provider, SDK version, prompt template, prompt version, input context hash, output schema, timestamps, and status. Generated content and grading evidence link back to this run through `generator_run_id` / `agent_run_id` fields so the user can later answer "what prompt/model created or graded this?"

## AI turn pattern

Codex does not directly mutate authoritative state in MVP. The default pattern is:

```text
TUI/Core prepares context
   ↓
exports.refresh produces small context files
   ↓
Codex SDK turn returns structured proposal
   ↓
Pydantic validation + policy routing
   ↓
LearnLoop storage layer writes YAML / Markdown / SQLite
   ↓
TUI shows applied changes, pending review, or manual-review prompt
```

This keeps the scheduler and vault consistent even if a model response is malformed or overconfident.

## LearnLoop-owned operations

These are Python service methods, not JSON-RPC method names:

| Operation | Purpose | Writes |
| --- | --- | --- |
| `lo.create` / `lo.update` | Create or edit a Learning Object | `learning-objects/*.yaml` |
| `pi.create` / `pi.update` | Create or edit a Practice Item | `practice-items/*.yaml` + SQLite registry |
| `attempt.log` | Record a graded attempt | `state.sqlite` (attempts, FSRS, mastery, errors) |
| `inbox.submit` | Send generated content to the inbox with provenance | `inbox/pending/*.yaml` |
| `inbox.accept` / `inbox.reject` | Move inbox items to canonical location | YAML + SQLite |
| `grade.rubric` | Run SDK-backed grading and store evidence | grading evidence in SQLite |
| `mastery.update` | Apply EMA + error-impact updates from an attempt | SQLite |
| `schedule.next` | Compute next due item(s) using FSRS + object mastery | reads SQLite |
| `concept.merge` | Canonicalize two concept IDs | `concept-graph.yaml` + SQLite remap |
| `exports.refresh` | Regenerate `exports/*` from current state | `exports/*` |
| `error.record` | Log an error event with type + severity | SQLite + `errors.md` append |
| `misconception.promote` | Convert high-confidence-wrong into a misconception LO | `learning-objects/*.yaml` + SQLite |
| `lineage.walk` | Return the provenance tree for a Practice Item | reads SQLite |
| `readiness.record` | Log a session-start readiness snapshot | `sessions` table |

## Agent roles

These are prompt templates and structured-output schemas used by the SDK adapter, not required server-side agents:

- **`rubric-grader`** — receives a Practice Item, learner answer, and rubric; returns structured grading evidence, a 0-4 score, and grader confidence. Grades update mastery automatically unless manual review is triggered.
- **`socratic-tutor`** — question-first tutoring guarded by the hint-ladder policy from `AGENTS.md`.
- **`error-diagnostician`** — receives a solution + context, returns error classification and a repair plan.
- **`canonical-ingestor`** — reads trusted source material, returns a structured patch of Learning Objects, Practice Items, concept-graph edges, and definitions.
- **`variant-generator`** — produces variants of an approved Practice Item, capped by `[inbox].max_auto_variants_per_item`; also produces `disguised_retest` items for resolved misconceptions.

## Lifecycle

```text
TUI start
   ↓
open vault + run migrations + refresh exports
   ↓
start Codex SDK client lazily when first AI feature is used
   ↓
create/resume subject-specific thread
   ↓
stream turns or receive structured proposals
   ↓
validate and apply LearnLoop-owned operations
   ↓
TUI exit → close SDK client gracefully
```

One LearnLoop process can work across multiple vaults, but only one vault is active in a TUI session. Each vault has independent SQLite state, exports, AGENTS.md, and Codex context.

## Why SDK-first

- No maintenance burden from a Codex fork.
- No hand-rolled protocol layer in MVP.
- Streaming, turn state, thread resume, and auth stay delegated to the SDK.
- LearnLoop keeps authoritative state local and validated.
- The system remains usable offline for existing content, due reviews, attempt logging, and scheduling.

---

# 13. Prompt files

Prompts live in the repo, so the user can edit them.

Every prompt template should include simple frontmatter with a stable name and version:

```markdown
---
name: diagnose_solution
version: 3
output_schema: DiagnosisProposal
---
```

The SDK adapter records `prompt_template`, `prompt_version`, `model`, `provider`, `sdk_version`, and `input_context_hash` in `agent_runs`. Any generated Learning Object, Practice Item, diagnosis, or grading evidence should be traceable back to the exact prompt/model run that created it.

## `prompts/diagnose_solution.md`

```markdown
# Diagnose Solution Prompt

You are diagnosing a learner's solution.

Return:
1. correctness
2. error type
3. severity
4. missing concept
5. feedback
6. repair drill
7. next scheduled practice mode

Do not just give the answer.
If the learner has not attempted the problem, ask for an attempt or provide a hint ladder.

Use this error taxonomy:
- recall_failure
- conceptual_error
- procedure_error
- notation_error
- assumption_error
- theorem_selection_error
- transfer_failure
- fluency_issue
```

## `prompts/generate_transfer.md`

```markdown
# Generate Transfer Prompt

Generate transfer practice for the target concept.

Use:
- one near-transfer problem
- one medium-transfer problem
- one far-transfer problem
- one explain-from-memory prompt
- one contrastive discrimination prompt

Return YAML.

Each item must include:
- id
- title
- concept
- knowledge_type
- practice_mode
- prompt
- expected_answer
- difficulty
- tags
```

---

# 14. Learning session file

Each session should become a Markdown log.

```markdown
# Session: 2026-05-12

## Summary
Today focused on SVD, PCA, and eigenvector discrimination.

## Completed
- 8 retrieval items
- 2 completion problems
- 1 transfer explanation

## Errors
### Missing centering assumption
Concept: PCA
Severity: high
Repair: contrastive examples of PCA with/without centering

### Confused eigenvectors and singular vectors
Concept: SVD
Severity: medium
Repair: interleaved discrimination set

## Next session
- Start with PCA centering retrieval
- Then do SVD/PCA transfer problem
- Retest eigenvector vs singular vector distinction
```

Codex can read these session files later to preserve continuity.

---

# 15. Error notebook

The global error log should be Markdown, with structured blocks.

```markdown
# Global Error Log

## Error: hazard_probability_confusion

Subjects:
- survival-analysis
- statistics

Observed:
- 2026-05-02
- 2026-05-08
- 2026-05-12

Description:
The learner sometimes interprets hazard as if it were a probability over an interval.

Repair plan:
- Contrast instantaneous rate vs cumulative probability.
- Use 3 examples with same cumulative incidence but different hazard shapes.
- Ask learner to explain why hazard can exceed 1 but probability cannot.

Status:
active
```

And the machine-readable taxonomy:

```yaml
errors:
  hazard_probability_confusion:
    type: conceptual_error
    severity_default: high
    repair_modes:
      - contrastive_examples
      - explain_from_memory
      - transfer_problem
    review_interval_days:
      - 1
      - 3
      - 7
```

The taxonomy is shipped with sensible defaults and is **user-editable** per vault. Custom error types added during diagnosis must be appended via the `error.record` operation, which checks for near-duplicates against the existing taxonomy and prompts for merge.

---

# 15.5. Provenance, Inbox, and Canonical Sources

Generated content is treated very differently from human-authored content. Every Learning Object and Practice Item carries a `provenance` block.

## Provenance fields

```yaml
provenance:
  origin: ai_generated          # human | canonical_extract | canonical_transform |
                                # ai_generated | ai_variant
  source_id: src_strang_ch7     # nullable; references canonical-sources/ingest-log.md
  parent_item_id: pi_xxx        # set if origin == ai_variant
  generator_run_id: run_abc     # links to the agent run that produced it
  change_batch_id: batch_abc    # groups writes for rollback/review
  prompt_template: generate_transfer
  prompt_version: 3
  model: gpt-5.5
  review_status: approved       # approved | auto_accepted | pending_review | rejected
  reviewed_at: 2026-05-12
  reviewed_by: learner
```

## Inbox policy

| Origin | Default routing |
| --- | --- |
| Canonical source + direct extraction (definitions, theorem statements, formulas verbatim) | **Auto-accept** |
| Canonical source + format transform (cloze from a canonical sentence; reformatted example) | **Auto-accept with provenance** |
| Canonical source + proof / derivation / transfer / misconception generation | **Inbox review** |
| Non-canonical source (agent free-generation, learner notes) | **Inbox review** |
| Variant of an already-approved Practice Item | **Auto-accept** up to `max_auto_variants_per_item`, tagged `origin: ai_variant` |
| Session-specific generated examples ("give me 3 more like this") | **Ephemeral** — used in session, stored in `ephemeral_session_items`, not promoted unless the learner says so |

Auto-accept does not mean trust. Auto-accepted items keep their origin tag and can be filtered out by the learner at any time. Every auto-accepted batch writes `content_events` rows, receives a `change_batch_id`, and triggers a TUI "Recently Added" notification with actions to inspect, edit, deactivate, reject, open lineage, or roll back the whole batch.

Rollback is a first-class operation. For YAML/Markdown writes, LearnLoop records the preimage path + content hash (and, for created files, that no preimage existed). For SQLite rows, LearnLoop records enough structured inverse metadata to deactivate generated Practice Items and mark related generated/content events as rolled back. Destructive physical deletion is not the default; rollback should prefer deactivation + status changes so history remains auditable.

## Canonical source ingestion

A dedicated `canonical-ingestor` role takes inputs from `canonical-sources/` — PDFs, lecture markdown, images of LaTeX, websites known to be correct — and produces a structured patch:

```text
Concept-graph additions and prerequisite edges
Learning Objects (definitions, theorems, lemmas, procedures, models, ...)
Practice Items keyed to each LO (one short-answer + one cloze + one application by default)
Worked examples (full solutions tied to a procedure or derivation LO)
Misconception checks (paired with the LOs they target)
Transfer prompts (queued for inbox review unless source provides them)
```

The ingestor returns everything as a single proposed patch the learner can accept, partially accept, or reject. Accepted patches are committed by the LearnLoop storage layer and registered in the `generated_items` SQLite table with the source's `source_id`.

## Ephemeral session items

When a learner asks for more practice mid-session, the agent generates items inline. These are stored as ephemeral and **not** promoted to permanent Practice Items by default. At session end (or any time), the TUI surfaces:

```text
The session generated 4 ephemeral items. Promote any to permanent practice?
  [ ] "Explain PCA on uncentered data — what changes?"   → lo_pca_via_svd
  [ ] "Sketch a counterexample where SVD ≠ eigendecomposition"  → lo_svd_decomposition
  ...
```

Promotion runs the item through standard inbox policy (likely auto-accept as a variant if it descends from an approved item; review otherwise).

## Active vs dormant

Practice Items have an `active` flag in SQLite. Dormant items are kept (with full history) but not scheduled. This is the safe path for "I made too many items" without losing data. Reactivating restores FSRS state.

---

# 15.6. Rubric-Based Grading

Free-text answers (definitions, explanations, derivations, transfer) are graded by the `rubric-grader` role using a 0-4 rubric. The grader returns structured evidence, not a free-text verdict.

## Pipeline

```text
Learner answer
   ↓
Rubric resolved (item-level rubric → default rubric for practice_mode × knowledge_type)
   ↓
rubric-grader role (structured JSON output)
   ↓
Validation (grade in 0-4, criterion ids match rubric, fatal-error caps respected)
   ↓
Mastery update (Layer 2 EMA; skipped until confirmation if manual review is triggered)
   ↓
Feedback + scheduling (FSRS rating + next-action mode)
```

## Rubric structure

A rubric defines criteria (each worth points), and **fatal errors** that cap the grade regardless of other criteria. Item-level rubrics override defaults.

```yaml
grading_rubric:
  max_points: 4
  criteria:
    - id: target_event
      points: 1
      description: "Mentions event/cause of interest."
    - id: modified_risk_set
      points: 1
      description: "Explains that competing-event cases remain in a modified risk set."
  fatal_errors:
    - id: treats_hazard_as_probability
      description: "Defines hazard as a probability without qualification."
      max_grade: 3
```

## Default rubrics by practice mode

Shipped in `rubrics/` and used when an item has no inline rubric. Suggested defaults:

| Mode family | Rubric focus |
| --- | --- |
| `short_answer`, `definition`, `cloze` | Key terms present; precision; no misconception |
| `explain_from_memory`, `teach_back` | Correct concept; structure (premise → mechanism → consequence); examples; absence of misconception |
| `derivation_reconstruction`, `proof_reconstruction` | Subgoal coverage; justification of each step; correct invariants; no fatal logical gap |
| `transfer`, `near_transfer`, `far_transfer` | Correct concept selection; correct application to novel context; handling of edge cases; avoidance of surface-form overfit |
| `contrastive_discrimination` | Both items correctly characterized; distinguishing feature explicit; counterexample if asked |

## Grading evaluation harness

Because agent grading affects mastery, grading prompts must be regression-tested locally. Each domain can ship small goldens under `evals/grading-goldens/`.

```yaml
id: golden_fg_subhazard_partial_001
domain: math_stats_ml
practice_item:
  id: pi_fg_subhazard_define_001
  practice_mode: short_answer
  prompt: "Define the Fine-Gray subdistribution hazard in your own words."
  expected_answer: "..."
  grading_rubric: "..."
learner_answer: >
  It is like a Cox hazard for the event of interest, with competing events removed.
expected:
  rubric_score_range: [1, 2]
  must_flag_errors:
    - says_same_as_cause_specific
    - modified_risk_set_missing
  must_not_flag_errors:
    - notation_error
```

`learnloop eval grading` runs the current rubric-grader prompt/model against these fixtures and reports score agreement, required error flags, forbidden error flags, and confidence calibration. This is a development and prompt-maintenance tool; it should never update learner mastery.

## Attempt-type handling

- `independent_attempt` — graded normally; full mastery update.
- `hinted_attempt` — graded; mastery update dampened proportional to hints used; FSRS rating capped at `good`.
- `dont_know` — logged as `attempt_type=dont_know`, `error_type=recall_failure`, score = 0, next action = `walkthrough` → reconstruction next session. No grading role invoked.
- `guided_walkthrough` — not graded as independent mastery; mastery update suppressed; schedules `reconstruction_after_walkthrough`.
- `reconstruction_after_walkthrough` — graded normally; this is where mastery updates resume.
- `skip` — no update beyond a small priority penalty next time.
- `self_report` — learner self-grade; only updates `calibration` dimension.

## Manual review triggers

`grader_confidence` is a 0-1 self-report from the grader role. Manual review (TUI prompts the learner to confirm the grade) is triggered when any of:

- `grader_confidence < grader_confidence_floor`
- rubric missing or visibly weak (e.g. `expected_answer` is one line for a multi-paragraph question)
- answer is unusually long or ambiguous
- math/proof has a subtle correctness issue the grader flags
- learner challenges the grade (TUI provides a "dispute" button)
- the item is `high_stakes_canonical_item` (canonical-source-derived theorem statements, etc.)

Manually-reviewed grades update mastery after confirmation. Low-confidence agent grades are stored as grading evidence but do **not** update mastery until the learner confirms or edits the grade.

---

# 15.7. Misconception lifecycle (misconceptions as Learning Objects)

When the scheduler detects `high_confidence_wrong` (confidence ≥ 4 and score < 0.30), the failure is treated as a misconception, not a recall miss. A misconception is itself a Learning Object — schedulable, trackable, and dismissable when resolved.

## Detection and creation

```text
attempt → grade → high_confidence_wrong flag
                       ↓
                  error.record (is_misconception=true)
                       ↓
                  misconception.promote
                       ↓
              Misconception LO created (if not already):
                knowledge_type: misconception
                title:          "hazard is a probability"
                contradicts:    lo_fine_gray_subhazard
                status:         active
                       ↓
              variant-generator role →
                contrastive Practice Items targeting it
                       ↓
              Repair loop queued
```

## Repair loop

While a misconception LO is `status: active`, the scheduler:

1. Inserts a `contrastive_discrimination` item against the contradicted LO within 1 day.
2. Follows with `misconception_repair` (targeted drill, 2-3 days).
3. Retests with the original or a similar Practice Item at 3 and 7 days.
4. At 14 days, surfaces a `disguised_retest` (same trap, novel framing) generated by `variant-generator`.

**Resolution rule:** three consecutive correct attempts across at least two practice modes, none flagged `high_confidence_wrong`. On resolution the misconception LO flips to `status: resolved`, an entry is appended to `errors/global-error-log.md` marking it closed, and the contradicted LO clears its implicit repair flag.

If `[learning].disguised_retest_after_resolution = true`, resolved misconceptions still surface occasionally as disguised re-tests — calibration evidence that the repair held. Failed disguised re-tests reopen the misconception (`status: active`) and restart the repair loop.

## Why misconceptions get their own LO

- They have their own mastery state (especially `discrimination` and `schema`) that's independent of the LO they contradict.
- They survive across subjects — "hazard is a probability" can attack `lo_fine_gray_subhazard`, `lo_cox_hazard`, and `lo_kaplan_meier`. One misconception LO, many contradicted LOs (n-to-1).
- They can carry many Practice Items dedicated to them (contrastive, repair, disguised retest).
- They're queryable and trackable from the dashboard: `learnloop misconceptions` lists active ones.

---

# 16. Scheduler design

The scheduler is three layers stacked. **Always store raw attempts forever** so the mastery model is replaceable without re-collecting data.

## Layer 1 — Item memory (FSRS, via `py-fsrs`)

Per Practice Item, in `state.sqlite`:

```text
difficulty
stability
retrievability
due_at
```

Standard FSRS updates. A graded attempt is mapped to an FSRS rating:

```python
def score_to_fsrs_rating(score: float) -> str:
    if score < 0.30: return "again"
    if score < 0.65: return "hard"
    if score < 0.90: return "good"
    return "easy"
```

The 0-4 rubric grade is mapped through:

```python
GRADE_TO_SCORE = {0: 0.00, 1: 0.25, 2: 0.55, 3: 0.80, 4: 1.00}
```

## Layer 2 — Learning Object mastery (multi-dimensional, EMA)

Per Learning Object, in `state.sqlite`:

```text
recall, recognition, schema, procedure, transfer,
fluency, explanation, discrimination, calibration
```

Each dimension is updated independently from attempts that target it. The update rule is **difficulty-aware, error-aware EMA**:

```python
def update_mastery(prev, score, item_difficulty, dim_weight, grader_confidence, alpha=0.2):
    # difficulty-aware: hard success raises more, easy failure lowers more
    if score >= 0.65:
        gain = score * (0.5 + item_difficulty)      # hard success amplified
    else:
        gain = score - (1 - item_difficulty) * 0.3  # easy failure punished more
    effective_alpha = alpha * dim_weight * grader_confidence
    return min(1.0, max(0.0, prev + effective_alpha * (gain - prev)))
```

`dim_weight` is the practice item's `mastery_weights[dim]`. `grader_confidence` can soften updates for accepted automatic grades, but grades below `grader_confidence_floor` are held for manual review and do not update mastery until confirmed.

### Mode → dimension default map

When a Practice Item omits `target_mastery_dimensions`, fall back to:

| `practice_mode`          | Updates                                |
| ------------------------ | -------------------------------------- |
| `retrieval`, `cloze`, `cued_recall`, `free_recall` | recall |
| `recognition`, `multiple_choice` | recognition |
| `short_answer`           | recall + schema |
| `worked_example`, `annotated_example` | schema, procedure |
| `completion_problem`     | procedure, schema |
| `procedure_execution`    | procedure |
| `interleaving`, `contrastive_discrimination` | discrimination, schema |
| `transfer`, `near_transfer`, `far_transfer` | transfer, schema |
| `explain_from_memory`, `teach_back` | explanation, schema, recall |
| `derivation_reconstruction`, `proof_reconstruction` | schema, procedure |
| `timed_drill`, `fluency_drill` | fluency, procedure |
| `error_diagnosis`, `misconception_repair` | schema, transfer |
| `self_assessment`        | calibration |

### Error-aware cross-dimension updates

An error can damage dimensions the item didn't explicitly target. The taxonomy file owns the impact map:

```yaml
# errors/error-taxonomy.yaml
error_impacts:
  recall_failure:
    recall: -0.25
  conceptual_error:
    schema: -0.25
    transfer: -0.10
  theorem_selection_error:
    schema: -0.30
    transfer: -0.20
  procedure_error:
    procedure: -0.25
    fluency: -0.05
  transfer_failure:
    transfer: -0.30
    schema: -0.10
  high_confidence_wrong:                    # misconception flag
    schema: -0.20
    calibration: -0.30
    # also: open repair_loop, append to errors/global-error-log.md
  fluency_issue:
    fluency: -0.25
```

`flag_high_confidence_wrong` triggers when `confidence >= 4` and `score < 0.30`: the item is treated as a misconception, not a recall miss. A repair-loop is scheduled (contrastive examples, then retest) and the error is logged.

### Fluency signal

Not just from `timed_drill`. Compute fluency from: `latency_vs_expected`, `hints_used`, `pause_count` (if available from the input widget), and consistency across recent attempts on the same item.

## Layer 3 — Concept mastery (aggregate)

Per Concept: prerequisite-weighted average of its Learning Objects' mastery. Used for the concept-graph view, weakness detection, and prerequisite-aware scheduling — not directly updated by attempts.

## SQLite tables (canonical)

```sql
CREATE TABLE practice_attempts (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT,
  learning_object_id TEXT,
  subject TEXT,
  concept TEXT,
  practice_mode TEXT,
  attempt_type TEXT,                 -- independent_attempt | hinted_attempt | dont_know | ...
  target_mastery_dimensions TEXT,    -- JSON array
  rubric_score INTEGER,              -- 0-4
  correctness REAL,                  -- GRADE_TO_SCORE[rubric_score]
  confidence INTEGER,                -- 1-5
  latency_seconds INTEGER,
  hints_used INTEGER,
  error_type TEXT,                   -- nullable; from taxonomy
  grader_confidence REAL,
  manual_review INTEGER,             -- 0/1
  created_at TEXT
);

CREATE TABLE grading_evidence (
  attempt_id TEXT,
  criterion_id TEXT,
  points_awarded REAL,
  notes TEXT,
  agent_run_id TEXT,
  PRIMARY KEY (attempt_id, criterion_id)
);

CREATE TABLE practice_item_state (
  practice_item_id TEXT PRIMARY KEY,
  difficulty REAL,
  stability REAL,
  retrievability REAL,
  due_at TEXT,
  active INTEGER,
  content_hash TEXT,
  last_attempt_at TEXT
);

CREATE TABLE learning_object_mastery (
  learning_object_id TEXT PRIMARY KEY,
  recall REAL, recognition REAL, schema REAL, procedure REAL,
  transfer REAL, fluency REAL, explanation REAL,
  discrimination REAL, calibration REAL,
  updated_at TEXT
);

CREATE TABLE concept_mastery (
  subject TEXT,
  concept TEXT,
  aggregate REAL,
  weakest_dimension TEXT,
  updated_at TEXT,
  PRIMARY KEY (subject, concept)
);

CREATE TABLE error_events (
  id TEXT PRIMARY KEY,
  attempt_id TEXT,
  learning_object_id TEXT,
  error_type TEXT,
  severity REAL,
  is_misconception INTEGER,          -- high_confidence_wrong flag
  repair_plan TEXT,                  -- JSON
  status TEXT,                       -- active | resolved
  created_at TEXT
);

CREATE TABLE generated_items (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT,             -- null until promoted
  origin TEXT,                       -- ai_generated | ai_variant | canonical_extract | canonical_transform
  parent_item_id TEXT,
  source_id TEXT,                    -- canonical source if applicable
  generator_run_id TEXT,
  change_batch_id TEXT,
  review_status TEXT,                -- pending_review | auto_accepted | approved | rejected
  prompt TEXT,
  generated_at TEXT,
  promoted_at TEXT
);

CREATE TABLE ephemeral_session_items (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT,
  session_id TEXT,
  prompt TEXT,
  used_at TEXT,
  promoted_to_practice_item_id TEXT  -- null unless learner promotes
);

CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  started_at TEXT,
  ended_at TEXT,
  energy TEXT,
  sleep_quality REAL,
  planned_minutes INTEGER,
  notes_md_path TEXT
);

CREATE TABLE content_events (
  id TEXT PRIMARY KEY,
  change_batch_id TEXT,
  event_type TEXT,                  -- created | auto_accepted | approved | rejected | edited | deactivated
  subject TEXT,
  entity_type TEXT,                 -- learning_object | practice_item | concept | rubric | source
  entity_id TEXT,
  origin TEXT,
  review_status TEXT,
  summary TEXT,
  created_at TEXT
);

CREATE TABLE change_batches (
  id TEXT PRIMARY KEY,
  reason TEXT,                       -- auto_accept | inbox_accept | manual_edit | import | rollback
  origin TEXT,
  summary TEXT,
  created_at TEXT,
  created_by TEXT,                   -- learner | system | codex
  rolled_back_at TEXT,
  rollback_batch_id TEXT
);

CREATE TABLE file_change_preimages (
  id TEXT PRIMARY KEY,
  change_batch_id TEXT,
  path TEXT,
  existed_before INTEGER,
  old_content_hash TEXT,
  old_content TEXT,                  -- nullable for large files; MVP stores text YAML/Markdown preimages
  new_content_hash TEXT,
  created_at TEXT
);

CREATE TABLE agent_runs (
  id TEXT PRIMARY KEY,
  purpose TEXT,                      -- rubric-grader | canonical-ingestor | variant-generator | tutor | ...
  model TEXT,
  provider TEXT,
  prompt_template TEXT,
  prompt_version TEXT,
  sdk_version TEXT,
  input_context_hash TEXT,
  output_schema TEXT,
  started_at TEXT,
  completed_at TEXT,
  status TEXT                        -- completed | failed | cancelled
);

CREATE TABLE scheduler_explanations (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  practice_item_id TEXT,
  selected_mode TEXT,
  priority REAL,
  components_json TEXT,
  readiness_factor REAL,
  plain_english_json TEXT,
  created_at TEXT
);

CREATE TABLE session_checkpoints (
  session_id TEXT PRIMARY KEY,
  current_practice_item_id TEXT,
  current_answer TEXT,
  focus_block_state_json TEXT,
  pending_grading_proposal_json TEXT,
  readiness_json TEXT,
  updated_at TEXT
);

CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  applied_at TEXT NOT NULL
);

CREATE INDEX idx_attempts_item_time ON practice_attempts(practice_item_id, created_at);
CREATE INDEX idx_attempts_lo_time ON practice_attempts(learning_object_id, created_at);
CREATE INDEX idx_item_state_due ON practice_item_state(active, due_at);
CREATE INDEX idx_error_events_status ON error_events(status, learning_object_id);
CREATE INDEX idx_generated_items_review ON generated_items(review_status, generated_at);
CREATE INDEX idx_content_events_recent ON content_events(created_at, event_type);
CREATE INDEX idx_content_events_batch ON content_events(change_batch_id);
CREATE INDEX idx_scheduler_explanations_session ON scheduler_explanations(session_id, practice_item_id);
```

## Storage invariants

- All timestamps are stored as ISO-8601 UTC strings. The TUI renders them in `[student].timezone`.
- `state.sqlite` enables foreign keys where both sides are SQL-owned. YAML-owned ids are validated by the storage layer before commits.
- Every schema change is a numbered migration recorded in `schema_migrations`.
- Attempt logging is atomic: `practice_attempts`, `grading_evidence`, `practice_item_state`, `learning_object_mastery`, `error_events`, `generated_items`, and `content_events` commit or roll back together.
- Related writes are grouped under `change_batches`. Any AI-generated or import-generated content must have a `change_batch_id`.
- Rollback creates a new `change_batches` row with `reason = "rollback"` and links it to the original batch. It should deactivate or restore, not silently erase history.
- YAML writes use atomic temp-file replacement. The storage layer computes and stores `content_hash` after a successful write.
- If a YAML write fails after a DB transaction starts, the DB transaction rolls back.
- If an external edit changes a YAML file and its content hash differs from SQLite, the TUI prompts for re-indexing before scheduling or grading that item.
- `content_events` powers the TUI "Recently Added" view and makes auto-accepted canonical transforms/variants easy to inspect, edit, deactivate, or reject after the fact.
- `agent_runs` records prompt template, prompt version, model, SDK version, context hash, and output schema for every AI-backed grading/generation/diagnosis operation.
- `session_checkpoints` is app-managed state for crash/interruption recovery and is cleared when a session ends cleanly.

## Attempt → updates

One attempt updates three things atomically:

```text
attempt (practice_item_id=pi_x, learning_object_id=lo_x, score=0.45, confidence=4,
         hints=2, error_type=hazard_probability_confusion)
   ↓
1. practice_item_state[pi_x]: FSRS update via score_to_fsrs_rating(score)
2. learning_object_mastery[lo_x]: EMA update for each target dimension,
                                  then apply error_impacts cross-dimension corrections
3. error_events: append; if high_confidence_wrong → open repair_loop
```

Then `concept_mastery` is recomputed lazily on read or on `exports.refresh`.

## Next-action selection

A two-stage policy. First, the per-item priority score chooses **which** Practice Items to surface. Then a rule layer picks **what mode** the next item should be in.

### Priority score (queue ordering)

```text
priority =
  0.30 * forgetting_risk            # 1 - retrievability
+ 0.20 * prerequisite_importance    # graph centrality + downstream blocked LOs
+ 0.15 * recent_error_severity      # boost items in same LO/concept as recent errors
+ 0.15 * transfer_gap               # high recall but low transfer
+ 0.10 * deadline_pressure          # from profile/goals.md
+ 0.10 * learner_interest
- 0.20 * cognitive_overload_risk    # session length consumed, novelty already added
```

### Scheduler explanations

Every scheduled Practice Item should carry an explanation object. This is not just UI polish; it is how the scheduler becomes debuggable.

```json
{
  "practice_item_id": "pi_pca_transfer_001",
  "selected_mode": "transfer",
  "priority": 0.71,
  "components": {
    "forgetting_risk": 0.24,
    "prerequisite_importance": 0.08,
    "recent_error_severity": 0.12,
    "transfer_gap": 0.15,
    "deadline_pressure": 0.02,
    "learner_interest": 0.03,
    "cognitive_overload_risk": -0.04
  },
  "readiness_factor": 1.0,
  "plain_english": [
    "This item is due today.",
    "Recall is strong but transfer is weak.",
    "A related error appeared in the last session."
  ]
}
```

The TUI uses this for "Why now?", and the CLI exposes it through `learnloop why <pi_id>`. Explanations are recomputed when the queue is generated and may be cached in SQLite for the active session.

### Readiness modulation

The session-start readiness gate (see §10 and `[learning].readiness_gate`) records `energy`, `sleep_quality`, and `available_minutes` to the `sessions` table. These modulate the per-item priority before queue ordering:

```python
def readiness_factor(mode: str, energy: str, sleep: float) -> float:
    base = 1.0
    if energy == "low":
        # bias toward consolidation, away from heavy load
        if mode in {"worked_example", "transfer", "far_transfer",
                    "derivation_reconstruction", "proof_reconstruction"}:
            base *= 0.4
        if mode in {"retrieval", "cued_recall", "cloze", "recognition"}:
            base *= 1.3
    if sleep < 0.5:
        # poor sleep: defer new material; review only
        if mode in {"worked_example", "annotated_example"}:
            base *= 0.2
    if energy == "high":
        if mode in {"transfer", "far_transfer", "variant_generation"}:
            base *= 1.3
    return base
```

`readiness_factor` multiplies the candidate item's priority score before queue ordering. New material is gated more aggressively than review. If `available_minutes < 20`, the queue collapses to warm-up retrieval only and skips the deep-work block entirely.

### Cold-start curriculum

For a subject with zero attempts, the scheduler falls back to:

1. **Difficulty prior + prerequisite order** if Learning Objects are seeded (e.g. from canonical-source ingestion). Items at the leaves of the prerequisite DAG come first.
2. **Diagnostic mode** if requested (`learnloop today --diagnostic`): a 5-10 minute probe of likely prerequisite LOs (short_answer + recognition) seeds initial mastery values that subsequent sessions refine.

Cold-start mastery defaults to `0.5` across dimensions and is dampened heavily (`ema_alpha * 0.5`) for the first 5 attempts on each LO.

### Mode selection (after item is chosen)

```python
def choose_next_action(lo_mastery, last_attempt, repair_loop_active):
    if repair_loop_active:
        return "misconception_repair"
    if lo_mastery["schema"] < 0.4 and lo_mastery["procedure"] < 0.5:
        return "worked_example_completion"
    if last_attempt and last_attempt["error_type"] == "theorem_selection_error":
        return "contrastive_discrimination"
    if last_attempt and last_attempt["score"] < 0.5 and last_attempt["hints_used"] >= 2:
        return "walkthrough"  # then schedule reconstruction_after_walkthrough next time
    if lo_mastery["recall"] > 0.8 and lo_mastery["transfer"] < 0.5:
        return "transfer"
    if lo_mastery["recall"] > 0.85 and lo_mastery["fluency"] < 0.5:
        return "fluency_drill"
    return "retrieval"
```

---

# 16.5. Type enums

Four enums govern the data model. Each answers a different question.

```text
knowledge_type      — What kind of thing is being learned?
practice_mode       — What activity tests or teaches it?
attempt_type        — How independently did the learner engage?
mastery_dimension   — What ability does an attempt provide evidence for?
```

## `KnowledgeType`

```python
KnowledgeType = Literal[
    "fact", "definition", "formula", "notation",
    "concept", "distinction", "assumption",
    "theorem", "lemma", "proof", "proof_technique", "derivation",
    "procedure", "algorithm", "worked_example_pattern",
    "model", "schema", "heuristic",
    "misconception", "error_pattern",
    "case_study", "application", "transfer_schema",
    "vocabulary", "grammar_pattern", "pronunciation", "character",
    "motor_skill", "tactical_pattern",
    "metacognitive_strategy",
]
```

| Type | Examples |
| --- | --- |
| `fact` | "BDNF supports plasticity"; "The capital is Seoul" |
| `definition` | eigenvector, subdistribution hazard, martingale |
| `formula` | Bayes rule, gradient update, CIF formula |
| `notation` | S(t), λ(t), XᵀX |
| `concept` | overfitting, hazard, vector space |
| `distinction` | hazard vs probability, MLE vs MAP |
| `assumption` | independent censoring, linearity, iid |
| `theorem` | CLT, spectral theorem, Bayes theorem |
| `lemma` | technical proof step |
| `proof` | proof of Bayes rule, convergence proof |
| `proof_technique` | contradiction, induction, coupling, martingale argument |
| `derivation` | Cox partial likelihood, gradient of loss |
| `procedure` | solving normal equations, doing PCA |
| `algorithm` | gradient descent, EM, Dijkstra |
| `worked_example_pattern` | diagonalizing a 2×2 matrix |
| `model` | logistic regression, Cox model, Fine-Gray model |
| `schema` | "use Bayes when evidence reverses conditioning" |
| `heuristic` | check invariants, condition on first step |
| `misconception` | "hazard is a probability" |
| `error_pattern` | sign errors, missing centering, theorem-selection errors |
| `case_study` | bail/disposition competing-risks setup |
| `application` | applying PCA to centered data |
| `transfer_schema` | recognizing SVD/PCA/eigendecomposition relationships |
| `vocabulary` | 수영장, 공부하다 |
| `grammar_pattern` | Korean 은/는 vs 이/가 |
| `pronunciation` | Korean tense consonants, Mandarin tones |
| `character` | Chinese character, Hanja, Kanji |
| `motor_skill` | dance move, aim flick, piano fingering |
| `tactical_pattern` | rotate vs hold angle, chess fork |
| `metacognitive_strategy` | confidence calibration, error postmortem |

## `PracticeMode`

```python
PracticeMode = Literal[
    "read", "observe",
    "worked_example", "annotated_example", "completion_problem",
    "retrieval", "cued_recall", "free_recall", "recognition",
    "cloze", "multiple_choice", "short_answer",
    "explain_from_memory", "teach_back",
    "derivation_reconstruction", "proof_reconstruction",
    "procedure_execution", "problem_solving",
    "interleaving", "contrastive_discrimination",
    "error_diagnosis", "misconception_repair", "disguised_retest",
    "transfer", "near_transfer", "far_transfer",
    "variant_generation",
    "reflection", "postmortem",
    "timed_drill", "fluency_drill",
    "dictation", "translation", "sentence_production",
    "pronunciation_drill", "shadowing", "copying",
    "motor_imitation", "external_focus_drill",
    "scenario_simulation",
    "walkthrough", "hinted_attempt", "reconstruction_after_walkthrough",
    "self_assessment",
]
```

A short selection of "best for" mappings:

| `practice_mode` | Best for |
| --- | --- |
| `read`, `observe` | Initial exposure; motor/tactical reference |
| `worked_example`, `annotated_example` | Novices; high-load material |
| `completion_problem` | Transition from example to solving |
| `retrieval`, `cloze`, `cued_recall`, `free_recall` | Durable retention |
| `recognition`, `multiple_choice` | Low-friction checks, fragile knowledge |
| `short_answer`, `explain_from_memory`, `teach_back` | Concepts, schemas, transfer |
| `derivation_reconstruction`, `proof_reconstruction` | Math/stats/ML theorems |
| `procedure_execution`, `problem_solving` | Procedure/schema |
| `interleaving`, `contrastive_discrimination` | Discrimination, transfer |
| `error_diagnosis`, `misconception_repair` | Debugging, proof review, repair loop |
| `disguised_retest` | Same conceptual trap in novel framing — verify a misconception is truly repaired |
| `transfer`, `near_transfer`, `far_transfer` | Generalization, advanced mastery |
| `variant_generation` | Deep schema mastery |
| `reflection`, `postmortem`, `self_assessment` | Metacognition, calibration |
| `timed_drill`, `fluency_drill` | Fluency, exam readiness |
| `dictation`, `translation`, `sentence_production`, `pronunciation_drill`, `shadowing` | Language |
| `copying`, `motor_imitation`, `external_focus_drill` | Motor learning |
| `scenario_simulation` | Esports, clinical/legal/statistical cases |
| `walkthrough`, `hinted_attempt`, `reconstruction_after_walkthrough` | "I don't know" / assisted retrieval |

## `AttemptType`

Separate from practice mode: how independently did the learner engage with the prompt?

```python
AttemptType = Literal[
    "independent_attempt",
    "hinted_attempt",
    "dont_know",
    "guided_walkthrough",
    "reconstruction_after_walkthrough",
    "skip",
    "self_report",
]
```

Mastery and FSRS updates depend on attempt type — see "Attempt-type handling" under Rubric-Based Grading.

## `MasteryDimension`

```python
MasteryDimension = Literal[
    "recall",
    "recognition",
    "schema",
    "procedure",
    "transfer",
    "fluency",
    "explanation",
    "discrimination",
    "calibration",
]
```

Each Practice Item declares its `target_mastery_dimensions` and (optionally) `mastery_weights` so an attempt updates the right things. Defaults come from the mode → dimension table in §16.

---

# 17. How a user actually uses it

## Initialize vault

```bash
mkdir learning-vault
cd learning-vault
learnloop init
```

Codex auth is configured separately through the installed Codex runtime. LearnLoop should detect missing auth only when the user invokes an AI-backed feature; non-AI review and scheduling commands still work.

For development, onboarding, and screenshots:

```bash
learnloop init --sample
```

This creates a tiny demo vault with one math/stats subject, a few Learning Objects, Practice Items, attempts, errors, generated-item provenance, scheduler explanations, and grading goldens. The sample vault must be deterministic so tests and documentation can rely on it.

## Add a subject

```bash
learnloop add-subject "survival-analysis"
```

Creates:

```text
subjects/survival-analysis/
  subject.md
  concept-graph.yaml
  notes/
  learning-objects/
  practice-items/
  rubrics/
  errors.md
```

## Add notes

```bash
learnloop add-note subjects/survival-analysis/notes/fine-gray.md
```

## Ask Codex to extract concepts

```bash
learnloop extract subjects/survival-analysis/notes/fine-gray.md
```

LearnLoop calls Codex through the SDK, validates the returned structured proposal, and applies accepted changes:

```text
subjects/survival-analysis/concept-graph.yaml
subjects/survival-analysis/learning-objects/*.yaml
subjects/survival-analysis/practice-items/*.yaml
state.sqlite
```

If the proposal contains canonical transforms or variants that meet the auto-accept policy, they are applied immediately and shown in the TUI's "Recently Added" review view. Items requiring review go to `inbox/pending/`.

## Start today’s loop

```bash
learnloop today
```

The TUI shows:

```text
1. Warm-up retrieval: 10 items
2. Deep work: Fine-Gray derivation completion
3. Weakness repair: hazard vs probability
4. Transfer: explain bail/disposition competing risks
```

---

# 18. TUI-first product surface

LearnLoop is TUI-first. The TUI is not a debug shell around a CLI; it is the main application experience.

```text
TUI first.
CLI for automation and quick actions.
GUI later.
```

A GUI is not necessary for the core loop. The core loop is text-heavy, file-based, and agentic — exactly where a TUI shines.

## TUI is best for

* Markdown notes
* math prompts
* retrieval
* error logs
* AI tutoring and generated practice review
* local file workflows
* command-line users
* fast iteration

## GUI is better later for

* concept graph visualization
* dashboards
* drag-and-drop PDFs
* video/dance review
* handwriting
* progress timelines

The best path:

```text
Phase 1: Textual TUI + local vault + SQLite scheduler
Phase 2: CLI parity and automation commands
Phase 3: Optional Tauri GUI
```

---

# 19. Recommended implementation stack

## MVP

```text
Python                       # 3.11+
Typer                        # CLI
Textual                      # TUI
Rich                         # rendering primitives shared with Textual
SQLite                       # state.sqlite via stdlib sqlite3
PyYAML                       # YAML round-trips for LO / PI / concept-graph
Markdown                     # narrative memory (no parser dependency for writes)
Pydantic                     # schemas for SDK outputs, YAML validation, service inputs
py-fsrs                      # item-memory scheduling
anyio + asyncio              # TUI/background tasks, SDK streaming, cancellation
openai-codex SDK             # Codex app-server integration
```

## Why Python?

Because you will want:

* scheduling algorithms,
* data analysis,
* local ML later,
* FSRS implementations,
* math/code checking,
* easy file processing.

## Why Textual?

Because it gives you a real TUI with:

* panels,
* forms,
* tables,
* keyboard navigation,
* live updates,
* progress views.

## Why Markdown/YAML?

Because Codex can read and edit them naturally.

## Why SQLite?

Because review scheduling and attempts should be queryable. Markdown is good for memory; SQLite is better for event history.

---

# 20. Package structure

```text
learnloop/
  pyproject.toml
  README.md

  learnloop/
    __init__.py

    cli.py
    tui.py

    core/
      scheduler.py            # priority score, mode selection, readiness modulation
      mastery.py              # FSRS + EMA, error-impact maps, three-layer aggregation
      review.py
      attempts.py
      errors.py
      sessions.py
      inbox.py                # provenance routing, accept/reject, ephemeral promotion
      changes.py              # change batches, rollback/deactivation
      import_export.py        # bundles, note imports, portable exports
      backup.py               # local backup create/list/restore
      doctor.py               # vault health checks and safe repairs
      grading.py              # rubric resolution, evidence storage, manual review triggers
      grading_eval.py         # local grading regression harness
      readiness.py            # session-start prompt and modulation factor
      lineage.py              # variant lineage walks (parent_item_id chain)
      misconception.py        # misconception LO lifecycle (promote, repair, resolve)
      pomodoro.py             # focus_blocks structure for "Today's Loop"

    storage/
      db.py                   # state.sqlite, migrations
      markdown.py             # narrative memory round-trips
      yaml_store.py           # YAML round-trips with content-hash tracking
      vault.py                # vault layout discovery, global profile merge

    codex/
      client.py               # CodexSdkClient (SDK lifecycle, threads, typed API)
      schemas.py              # structured-output models for AI proposals
      events.py               # app-level stream events for the TUI
      prompts.py              # prompts/*.md loaders
      validators.py           # SDK output validation + proposal normalization

    domains/
      math_stats_ml.py
      research_papers.py
      language.py
      motor_vod.py
      general.py

    templates/
      AGENTS.md
      learnloop.toml
      profile/
      subjects/
      prompts/
      rubrics/
      evals/
      sample-vault/
```

---

# 21. MVP feature list

## Must have

* `learnloop init`
* standalone Python package
* Textual TUI as the primary daily workflow
* local vault scaffold
* `AGENTS.md`
* subject creation
* note ingestion
* manual Learning Object and Practice Item creation
* YAML practice items
* SQLite migrations and attempt logging
* due queue computed from SQLite state
* FSRS-style item scheduler using `py-fsrs`
* scheduler explanation object and `learnloop why`
* TUI daily review
* error tagging
* recent auto-accepted content review view
* change batches and rollback/deactivate for generated batches
* session checkpoint/resume after interruption
* `learnloop doctor`
* local backup create/list/restore
* first-run sample vault (`learnloop init --sample`)
* `exports.refresh`
* session summaries
* offline operation for existing content

## Should have

* Codex SDK adapter
* SDK-backed structured output for one AI path: grading, generation, or diagnosis
* prompt/model provenance through `agent_runs`
* grading evaluation harness (`learnloop eval grading`)
* text-first import/export bundles
* Codex-generated practice
* Codex diagnosis from solution files
* concept graph YAML updates
* interleaving set generation
* automatic error repair drills
* confidence calibration
* review rescheduling

## Later

* Tauri GUI
* visual concept graph
* richer PDF ingestion
* handwriting input
* audio-based language practice
* live language chat
* automated video/audio analysis for VOD review
* mobile companion

---

# 22. Example SDK-backed agent invocation

A "diagnose solution" task as LearnLoop sees it. The SDK adapter hides app-server transport details and returns a validated LearnLoop model.

```python
from learnloop.codex.client import CodexSdkClient
from learnloop.codex.schemas import DiagnosisProposal
from learnloop.core.exports import refresh_exports
from learnloop.storage.vault import Vault

vault = Vault.open(".")
refresh_exports(vault)

client = CodexSdkClient.from_config(vault.config.ai)
proposal = client.run_structured(
    purpose="error-diagnostician",
    context_files=[
        "profile/student.md",
        "subjects/survival-analysis/subject.md",
        "subjects/survival-analysis/concept-graph.yaml",
        "subjects/survival-analysis/errors.md",
        "exports/recent-errors.md",
        "prompts/diagnose_solution.md",
    ],
    inputs={
        "subject": "survival-analysis",
        "concept": "fine_gray_competing_risks",
        "learner_solution_path": "inbox/pending/solution-2026-05-12.md",
    },
    output_schema=DiagnosisProposal,
)

vault.diagnosis.apply_proposal(proposal)
```

`apply_proposal` owns all writes: it records grading evidence, updates mastery if confidence policy allows, appends error events, creates repair-loop items if needed, and routes generated content through the inbox/auto-accept policy.

---

# 23. Example output from Codex

```markdown
# Diagnosis: Fine-Gray solution

## Correctness
Partial.

## Main issue
The learner treated the subdistribution hazard as if it were a standard cause-specific hazard.

## Error type
conceptual_error: hazard_probability_confusion
theorem_selection_error: cause_specific_vs_subdistribution

## Feedback
You correctly identified competing risks, but your risk set interpretation changed from Fine-Gray to cause-specific Cox halfway through the derivation.

## Repair drill
1. Define cause-specific hazard.
2. Define subdistribution hazard.
3. Explain the modified Fine-Gray risk set.
4. Solve one contrastive example where Cox and Fine-Gray coefficients differ.

## Schedule
- Retest tomorrow
- Interleaved comparison in 3 days
- Transfer problem in 7 days
```

The human-readable diagnosis is shown in the TUI, but persistence uses the structured `DiagnosisProposal` fields rather than parsing this Markdown.

---

# 24. What makes this different from just using Codex?

Plain Codex can help you study.

LearnLoop gives AI tutoring a **persistent learning operating system**.

Without LearnLoop:

```text
You ask questions.
Codex answers.
The conversation disappears or becomes hard to reuse.
```

With LearnLoop:

```text
You attempt.
Codex diagnoses.
The app logs errors.
The scheduler retests you.
The concept graph updates.
Your future sessions adapt.
```

That is the product.

---

# 25. Final recommended build path

Build in this order:

```text
1. Standalone Python package scaffold
2. Vault layout, config loading, migrations
3. Textual TUI shell and Today's Loop screen
4. YAML Learning Object / Practice Item stores
5. SQLite attempt logging + due queue
6. FSRS + Learning Object mastery updates
7. Scheduler explanations + `learnloop why`
8. Error tagging, session summaries, exports refresh
9. Change batches, rollback, session checkpoints, and `learnloop doctor`
10. Recent auto-accepted content review
11. Backup + sample vault
12. Codex SDK adapter + one structured AI workflow
13. Prompt/model provenance + grading eval harness
14. Text-first import/export
15. Codex-generated practice and diagnosis
16. Concept graph updates
17. Interleaving and transfer engine
```

The minimal useful version could be built around this command set:

```bash
learnloop init
learnloop add-subject
learnloop add-note
learnloop today
learnloop review
learnloop generate-practice
learnloop diagnose
learnloop errors
learnloop inbox recent
learnloop why <pi_id>
learnloop doctor
```

Implementation guardrails:

```text
Do not start with a web app.
Do not start with a full GUI.
Do not put memory inside the model.
Do not make one giant memory file.
Do not fork Codex for LearnLoop-specific behavior.

Start with a TUI-first local learning application:
Markdown for human-readable memory,
YAML for structured learning objects,
SQLite for attempts and scheduling,
Textual for the TUI,
Codex SDK for AI tutoring and structured proposals.
```

---

# 26. Decisions and remaining implementation questions

The following decisions are now fixed for implementation:

- LearnLoop is a standalone Python package.
- LearnLoop is TUI-first; CLI is secondary.
- Codex integration is SDK-first, not fork-based and not raw JSON-RPC-first.
- The authoritative content model is Learning Objects + Practice Items.
- Canonical transforms and variants of approved Practice Items auto-accept by default, with TUI alerts and a recent-change review surface.
- Agent grading updates mastery automatically unless low confidence or another manual-review trigger fires.
- The application must support multiple subject domains through extension modules.
- Audio-based language features, live chat, and automated media analysis are later extensions.
- Generated/imported changes are grouped into rollbackable change batches.
- Scheduler decisions must be explainable through the TUI and `learnloop why`.
- Vault health checks, backups, session resume, prompt/model provenance, grading eval fixtures, import/export, and a deterministic sample vault are part of the implementation surface.

## Remaining data-model questions

1. **Concept identity / canonicalization.** When the agent extracts a concept similar but not identical to an existing one, every concept-graph patch should go through `concept.merge` with suggestions. The learner confirms merges; never auto-merge silently.
2. **Vocabulary scale.** For language subjects, use `vocab.yaml` as a compact bulk format, but each vocabulary entry must still have a stable synthetic Learning Object id for scheduling and mastery.
3. **Worked examples as content vs Learning Objects.** A worked example file is content; the pattern it teaches is a `worked_example_pattern` LO. Implement explicit two-way links: `lo.references_worked_example: <path>` and worked-example frontmatter `teaches_lo: <lo_id>`.
4. **Media references.** For VOD/motor subjects, MVP should store local media references and timestamps in `media-index.yaml`; no binary media is copied into the vault unless the user explicitly imports it.

## Remaining interaction questions

5. **Answer input widget.** The TUI needs short inline answers, `$EDITOR` long answers, LaTeX-friendly math answers, and code-block answers. MVP can support inline + `$EDITOR`; rendering/sandboxing can follow.
6. **Recent auto-accepted review.** The TUI should show "Recently Added" after auto-accept events and expose deactivate/edit/open-lineage actions. The exact layout still needs a final design pass.
7. **Calibration dashboard.** Confidence is collected per attempt. The first implementation can log it; a calibration chart can wait until dashboard work.

## Remaining operations questions

8. **Git policy.** Vaults should be git-friendly, but default behavior should be hands-off: do not autocommit unless `[storage].autocommit = true`.
9. **Privacy / telemetry.** Default policy: no product analytics. Local content leaves the machine only through explicit Codex/model calls initiated by the user or an AI-backed workflow.

# 27. Incorporated extensions

These were proposed earlier as "new ideas worth considering" and are now first-class in the spec. Quick map of where each lives:

| Idea | Spec home |
| --- | --- |
| Misconceptions as first-class Learning Objects | §9 (LO `status` + `contradicts`), §15.7 (lifecycle), §16 mode selection, §16.5 enum (`disguised_retest`) |
| Readiness gate at session start | §6 (`[learning].readiness_gate`), §10 (Session start screen), §16 (Readiness modulation), `readiness.record` tool |
| Disguised re-test | §16.5 (`disguised_retest` in `PracticeMode`), §15.7 (post-resolution retests), `variant-generator` role |
| Pomodoro-aware deep-work blocks | §6 (`[learning].focus_blocks`, `break_practice`), §10 (Today's Loop with 25/5), `pomodoro.py` |
| Variant lineage view | §11 (`learnloop lineage`), §12 (`lineage.walk` operation), `lineage.py`, §15.5 provenance tree |
| Multi-vault global profile | §4 ("Global (cross-vault) profile"), §6 (`[profile]`), `vault.py` global-merge |
| Difficulty priors per source | §9 (`difficulty_prior` on LO YAML), §16 (cold-start curriculum uses prior + prerequisite order) |
| Cold-start curriculum | §16 ("Cold-start curriculum" subsection — diagnostic mode + prior-based seeding) |
| Rollbackable generated changes | §15.5 (`change_batch_id`), §16 SQLite tables (`change_batches`, `file_change_preimages`), §11 (`learnloop undo batch`) |
| Import/export | §11.5 (`learnloop import`, `learnloop export`, `learnloop-bundle`) |
| Grading evaluation harness | §15.6 (`evals/grading-goldens`, `learnloop eval grading`) |
| Scheduler explainability | §10 (`Why now` panel), §16 (`scheduler_explanations`), §11 (`learnloop why`) |
| Vault health checks and backups | §11.5 (`learnloop doctor`, `learnloop backup`) |
| Prompt/model provenance | §13 prompt frontmatter, §16 (`agent_runs`), §15.5 provenance fields |
| Session interruption/resume | §10 (Session resume), §16 (`session_checkpoints`), §6 (`[sessions]`) |
| First-run sample vault | §17 (`learnloop init --sample`), §20 (`templates/sample-vault`) |
