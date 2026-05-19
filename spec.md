# Spec: **LearnLoop**

## 1. Product definition

**LearnLoop** is a Python application for adaptive learning. It is built around a Textual TUI, a local learning vault, and an (optional) Codex app-server integration through the Python SDK.

Codex is an AI runtime that LearnLoop calls through the `openai-codex` / app-server SDK using the user's ChatGPT subscription (not the metered API). The LearnLoop application, schemas, scheduler, TUI, storage layer, and vault tools live in their own Python package.

Codex is **required for the daily loop** -- grading, diagnosis, generation, ingestion, and ephemeral diagnostic items all depend on it. When Codex is unavailable (no auth, network down, rate-limited), LearnLoop drops into a **degraded offline mode** that allows: reviewing existing content, attempting Practice Items with self-grading, manual error tagging, browsing notes/concept graph/errors, and viewing scheduler explanations. The model-bound paths (LLM grading, agent diagnosis, generation, canonical ingestion, ephemeral diagnostic generation) are disabled in offline mode and resume when Codex becomes available again.

MVP is **single-user and local-first**. There are no accounts, shared tenants, or multi-user permission models in the core product. A "learner" is the person who owns the vault, and all learner-state beliefs are derived from that vault's own attempts unless the user explicitly imports data.

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
learnloop generate-practice
learnloop inbox recent
```

The TUI is the primary product surface. The CLI exists for automation, quick review, and debugging.

LearnLoop uses Codex to:

* read the learner’s profile,
* inspect notes,
* generate retrieval questions,
* guide structured observations and reflections,
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

Codex is required for the full daily loop. Without Codex, LearnLoop drops to **degraded offline mode**: review existing content, attempt items with self-grading, manual error tagging, scheduler explanations, and browsing. Free-text LLM grading, agent diagnosis, generation, canonical ingestion, and ephemeral diagnostic items are model-bound and disabled offline. Authentication uses the user's ChatGPT subscription via the SDK's `chatgpt` auth mode; the metered API is not the intended cost path.

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

  concepts/                     # vault-global concept registry (concept IDs are vault-global, not subject-scoped)
    concepts.yaml               # canonical concept definitions; one entry per global concept id
    relations.yaml              # vault-wide prerequisite / confusable / contains edges

  algorithm_priors.yaml         # surrogate parameters, cold-start ramp, cross-LO propagation defaults,
                                # error-type gates, per-domain overrides. Versioned with algorithm_version.

  profile/                      # narrative memory
    student.md
    goals.md                    # narrative goals
    goals.yaml                  # structured goals: ids, priorities, deadlines, retention horizons (see §7)
    preferences.md
    constraints.md

  subjects/
    linear-algebra/
      subject.md
      concept-graph.yaml        # subject view: lists which global concept ids are in scope here,
                                # plus subject-specific prerequisite ordering. Concept definitions
                                # live in vault-level concepts/concepts.yaml.
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
      errors.md                 # derived view: filter of global-error-log.md by this subject's tagged LOs
      reflection.md             # learner reflections (frontmatter declares subjects)

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

    overwatch-review/
      subject.md
      concept-graph.yaml        # mechanics, game-sense concepts, team patterns
      media-index.yaml          # VOD references + timestamp ranges
      vod-reviews/
      mechanics-drills.yaml
      tactical-patterns.yaml
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
    scheduler-goldens/          # deterministic queue/explanation fixtures
      due-queue-basic.yaml
      surprise-followup.yaml
    policy-goldens/             # counterfactual policy fixtures for EIG/scheduling changes
      greedy-vs-probe.yaml
    replay-fixtures/            # held-out response prediction fixtures
      recent-attempts.yaml
    simulated-learners/         # synthetic learner profiles for offline policy iteration
      novice-linear-algebra.yaml

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
    observation_review.md

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
| **`state.sqlite`** | Mutable computed state: practice attempts, FSRS item-memory state, learning-object + concept mastery, learner-state uncertainty, elicitation decisions, Bayesian surprise, due queue, generated-item registry, error events, session metadata, grading evidence, policy evaluation run results, Practice Item content hashes, active/dormant status | LearnLoop core + scheduler (humans read via CLI/TUI views, not directly) |
| **`exports/`** | Read-only derived context for the agent: snapshots of "what is due", "weak concepts", "recent errors", mastery summary | Regenerated by `learnloop` before each session and after attempt batches |

Rule of thumb: if the user or the agent should comfortably edit it by hand and it benefits from being human-readable, it's Markdown or YAML. If it's an event log, a schedule, or a computed state requiring consistency, it's SQLite.

### Local embedding index

LearnLoop maintains a local embedding index (sentence-transformers, model pinned in `learnloop.toml`) over concepts, Learning Objects, Practice Items, and note paragraphs. Embeddings are stored as BLOBs in SQLite alongside the entity id and content hash, and are recomputed whenever the content hash changes.

The index powers:

- **Concept-merge suggestions.** When the canonical ingestor or the agent proposes a new concept, embedding similarity against existing global concepts surfaces near-duplicates *before* the merge prompt is shown to the learner. Aliases and surface-form normalization are tried first; embeddings catch the rest.
- **Near-duplicate Practice Item detection.** Auto-accepted variants are dedup-checked against the existing PI pool for the same Learning Object; high-similarity duplicates are marked `pending_review` instead of auto-accepted.
- **Related-LO lookup in the TUI.** "See related" surfaces neighbors of the current LO across subjects (relevant once concept IDs are vault-global).
- **Note-to-LO grounding.** When the agent extracts a concept from a note, the source paragraph is recorded; later inspection can show "this LO came from these note paragraphs."

The embedding step is local-only — no model call. It runs synchronously for single-item writes and in batched background jobs for ingestion. If the embedding model is missing or fails to load, the features above degrade gracefully (the merge prompt falls back to alias-only matching, and "related" lookups return empty), but core read/write/scheduling never depends on embeddings.

### Global (cross-vault) profile

For users who run more than one vault (e.g. one for school, one for personal study), `learnloop` reads a global profile:

```text
~/.learnloop/
  profile.md            # baseline learner profile (background, preferences, style)
  preferences.md
  AGENTS.md             # optional global agent rules (vault AGENTS.md takes precedence)
```

When a vault loads, `profile/student.md` is merged on top of `~/.learnloop/profile.md`. Vault values win on conflict. The agent reads the merged result; the on-disk files stay separate. Cross-vault concept reuse is **out of scope** — each vault owns its concepts, Learning Objects, and SQLite state independently.

### Subjects as views

A **subject** is a named view over the vault: a saved filter on Learning Objects, Practice Items, notes, observations, errors, and reflections. Subjects are not content-ownership boundaries — an LO can belong to multiple subjects, and the same concept (e.g. `probability`) can show up in `statistics`, `ml`, and `survival-analysis` views.

Membership is declared on the entity:

- **Learning Objects** carry `subjects: [list]` (required, ≥1 element). The first entry is the **primary subject**.
- **Practice Items** inherit their subjects from their `learning_object_id` by default. A PI can override with its own `subjects:` to declare a strict subset (e.g. a framing only relevant in one subject).
- **Notes** carry Markdown frontmatter `subjects: [list]` (required, ≥1).
- **Observations**, **errors**, and **sessions** are vault-level; subject-filtered displays compute membership by walking the related LO / PI / note tags.

Folder location is **advisory**, not authoritative:

- A file at `subjects/<S>/learning-objects/<id>.yaml` is expected to have `subjects[0] == <S>`. `learnloop doctor` warns on mismatch; the loader still indexes the file by id.
- `learnloop add-lo --subject <S>` scaffolds new files into the matching folder, but moving a file doesn't change its membership.
- Multi-subject LOs live in their primary subject's folder; their other subjects show them via tag lookup, not via duplicate files or symlinks.

Subjects themselves are still declared entities: a subject exists when its folder under `subjects/<id>/` exists with at least a `subject.md`. The folder name is the subject id. `learnloop add-subject <id>` creates the scaffold (subject.md, empty concept-graph.yaml view, learning-objects/, practice-items/, notes/).

What's vault-level and what's per-subject:

| Path | Authoritative location | Subject view? |
| --- | --- | --- |
| Concepts | `concepts/concepts.yaml`, `concepts/relations.yaml` (vault-level) | Per-subject `concept-graph.yaml` view |
| Learning Objects, Practice Items, notes | Subject folders by primary subject | Filtered by tag |
| Errors | `errors/global-error-log.md`, `errors/error-taxonomy.yaml` (vault-level) | Per-subject `errors.md` is a derived view |
| Sessions | `sessions/<date>.md` (vault-level) | Subject filter on attempts table |
| Reflections | Authored under any subject folder | Filtered by tag |
| Mastery, beliefs, surprise | `state.sqlite` (LO-keyed, concept-keyed; **not** subject-keyed) | Aggregated for display per subject |

### Subject and domain extension model

LearnLoop must be extensible across subjects. A subject is the learner-facing unit (`linear-algebra`, `korean`, `research-papers`, `overwatch-review`). A domain is a plugin-like module that chooses templates, rubrics, practice modes, attempt capture, learner-state mappings, scheduler hooks, and import helpers.

Recommended first-party domains:

| Domain | Subjects it should support | MVP scope |
| --- | --- | --- |
| `math_stats_ml` | linear algebra, statistics, ML, proofs, derivations | Text prompts, LaTeX, worked examples, proof reconstruction, transfer |
| `research_papers` | paper reading, method understanding, assumptions, claims, replications | Canonical-source ingestion from PDFs/notes, claim/evidence maps, active recall, critique prompts |
| `language` | Korean, vocabulary, grammar, reading, writing, conversation | Text-based vocab/grammar/translation/dictation; conversation tests and audio later |
| `motor_vod` | dance, instrument practice, sport technique, generic VOD review | Timestamped observations, error patterns, cue recall, practice plans; automated video/audio analysis later |
| `esports_overwatch` | Overwatch VOD review, mechanics, game sense, team coordination | Manual VOD reflection, mechanics/game-sense prompts, Bayesian hidden-state review, drill recommendations; automated telemetry/video later |
| `general` | any structured learning subject | Generic Learning Objects, Practice Items, notes, errors, and scheduling |

Every domain extension can provide:

- subject scaffold templates,
- core and namespaced `KnowledgeType` / `PracticeMode` recommendations,
- rubrics,
- error taxonomy additions,
- import/ingestion helpers,
- domain-specific attempt schemas,
- mappings from domain evidence facets into the five core mastery axes,
- scheduler hooks for candidate generation and next-action selection,
- TUI panels or commands,
- optional SQLite migrations for domain-owned tables.

Domain-specific features must degrade gracefully to the generic model. If a plugin is missing, LearnLoop can still show the subject as Learning Objects, Practice Items, notes, attempts, errors, and scheduler state. For MVP, all domains are text/manual-first; audio-based language practice, live chat, telemetry ingestion, and automated VOD/media analysis are later extensions.

Practice modes and error types are extensible. Core modes use plain names like `retrieval` or `transfer`; domain-owned modes should be namespaced when they are not generally meaningful, such as `language:conversation_turn` or `esports_overwatch:vod_belief_reconstruction`.

### Domain module contract

A domain module should expose:

```python
class DomainModule(Protocol):
    id: str
    version: str
    capabilities: DomainCapabilities

    def scaffold_subject(self, subject_id: str) -> DomainScaffold: ...
    def practice_modes(self) -> list[PracticeModeSpec]: ...
    def knowledge_types(self) -> list[KnowledgeTypeSpec]: ...
    def error_taxonomy(self) -> ErrorTaxonomyPatch: ...
    def rubrics(self) -> list[RubricTemplate]: ...
    def evidence_mappings(self) -> list[EvidenceMapping]: ...
    def probe_hypothesis_templates(self) -> list[CoarseHypothesisTemplate]: ...
        # See §16 Layer 4 "Probe mode and probe-EIG". Domain templates shadow core
        # templates from prompts/probe_hypothesis_templates.yaml on the same
        # (knowledge_type, practice_mode) key. Return [] if the domain inherits
        # from core unchanged.
    def scheduler_hooks(self) -> list[SchedulerHook]: ...
    def tui_panels(self) -> list[TuiPanelSpec]: ...
    def migrations(self) -> list[SqlMigration]: ...
```

### `PracticeModeSpec` — namespaced practice modes and their defaults

A `PracticeModeSpec` describes a mode the domain registers (including namespaced ones like `language:conversation_turn`) and carries the defaults used when a Practice Item doesn't override them.

```python
class PracticeModeSpec(BaseModel):
    id: str                                       # "language:conversation_turn"
    domain_id: str                                # "language"
    label: str                                    # human-readable name for TUI
    default_evidence_facets: list[EvidenceFamily] # primary update channel; canonical or namespaced
    default_evidence_weights: dict[EvidenceFamily, float]   # normalized on read; need not sum to 1
    default_axis_view_emphasis: list[MasteryAxisView]       # which derived views this mode primarily updates
                                                            # (display/explanation hint, not an update target)
    default_grader_tier: int                      # 1 | 2 | 3 | 4 (see §15.6)
    fsrs_eligible: bool = True                    # if False, mode does not feed FSRS state
    plausible_error_types: list[str]              # which error taxonomy ids the surrogate may sample
    short_session_eligible: bool = True           # if False, excluded from short-session mode queue
```

**Default resolution order** when an attempt is scored:

1. Practice Item explicit values (`evidence_facets`, `evidence_weights`) — always win.
2. `PracticeModeSpec` defaults for the mode — used when the Practice Item omits a field.
3. Core mode → evidence-family table in §16 Layer 2 (the table shipped with LearnLoop) — used only for core modes when neither (1) nor (2) provides defaults.
4. Hard failure → `learnloop doctor` flags the Practice Item; the scheduler will not surface it.

Legacy `default_target_mastery_axes` / `default_mastery_weights` keys on existing `PracticeModeSpec` definitions are migrated at vault load by mapping each axis to its highest-weight aggregating family (per `algorithm_priors.axis_views.<axis>.families`).

Domain modules that register namespaced modes are required to provide a `PracticeModeSpec` for each. The vault startup loader validates that every family listed either appears in the canonical `EvidenceFamily` set or is namespaced and ships an `aggregates_into` mapping onto one of the four `MasteryAxisView` labels.

Domain modules do not own the global storage contract. They can add namespaced tables, files, and evidence families, but attempts, surprise, the LO scalar mastery, the learner θ profile, content provenance, and scheduler explanations still flow through the LearnLoop core tables.

### Domain enable / disable / purge

Domains are listed in `[domains].enabled`. Adding or removing an id is a config change; LearnLoop reacts on next vault open.

**Soft-disable (default behavior on plugin removal).** Removing a domain from `[domains].enabled`:

- All data is preserved. Domain-owned tables, namespaced Practice Items, namespaced observation events, and the domain's filesystem content (subject folders, prompts, rubrics) stay on disk.
- Scheduler hooks from the domain stop running. TUI panels stop rendering. Practice modes namespaced under the domain become **unsurfaceable** — `learnloop today` will not include them in the queue, even if their `practice_item_state.due_at` has passed.
- `learnloop doctor` warns: `Domain 'esports_overwatch' is referenced by 47 LOs / 132 PIs / 8 observations but not enabled in [domains].enabled.`
- Re-adding the id to `[domains].enabled` reactivates everything. No data migration required.

**Hard-purge (explicit destructive command).** When the user is sure they don't want the data:

```bash
learnloop domain purge esports_overwatch
```

The command:

1. **Dry-run first** — prints what will be deleted: count of LOs, PIs, observations, attempts, grading evidence, propagation events, generated items, worked examples, scheduler explanations, surprise rows, beliefs, item state, domain-owned tables, plus the filesystem paths (subject folders, prompts, rubrics).
2. **Requires typing the domain id to confirm** — typing `esports_overwatch` exactly. Anything else aborts.
3. **Writes a `change_batches` row with `reason = domain_purge` and `origin = domain:esports_overwatch`** linking every deleted artifact via `file_change_preimages` and inverse SQLite metadata. The purge is itself rollbackable from the batch for `[storage].purge_undo_window_days` (default 7 days) after which it becomes permanent.
4. **Refuses if domain is currently enabled** — the user must remove it from `[domains].enabled` first. This forces an explicit soft-disable step before a hard purge; can't fat-finger a destructive op while the domain is in active use.

CLI surface:

```bash
learnloop domain list                         # show enabled / disabled / purgeable
learnloop domain disable <id>                 # convenience for editing [domains].enabled
learnloop domain enable <id>                  # convenience; runs migrations if needed
learnloop domain purge <id>                   # destructive; requires double-confirm
```

The dry-run output and confirmation flow protect against the case where a user accidentally tries to purge a domain whose data they actually want.

Capabilities tell the core which workflows a domain supports:

```python
class DomainCapabilities(BaseModel):
    supports_fsrs: bool = true
    supports_free_text_grading: bool = true
    supports_conversation: bool = false
    supports_observation_templates: bool = false
    supports_vod_review: bool = false
    supports_external_media: bool = false
    supports_telemetry_import: bool = false
    supports_auto_grading: bool = false
    supports_scheduler_hooks: bool = true
```

The core uses capabilities to choose UI panels, CLI affordances, import options, and safe fallbacks. For example, `esports_overwatch` can set `supports_fsrs = false` for some VOD-review activities while still using LearnLoop's attempts, evidence facets, surprise, and scheduler explanations.

### Language conversation domain

The language module starts text-first but should be designed to grow into audio and live conversation. Conversation tests should be Practice Items that evaluate whether the learner can understand context, produce an appropriate response, repair misunderstandings, and stay calibrated about uncertainty.

Recommended language domain modes:

```text
language:conversation_turn
language:roleplay_dialogue
language:listening_comprehension
language:conversation_repair
language:free_response_translation
language:pronunciation_shadowing
```

Default language evidence facets should map into the core axes:

| Facet | Core axes |
| --- | --- |
| `vocab_recall` | memory |
| `grammar_selection` | understanding, execution |
| `sentence_production` | execution, generalization |
| `conversation_repair` | understanding, calibration |
| `pragmatic_appropriateness` | generalization |
| `pronunciation_accuracy` | execution |
| `listening_discrimination` | memory, understanding |

The module should support both strict item grading (vocab, cloze, grammar) and conversation rubrics where multiple responses can be acceptable.

### Esports / Overwatch-first domain

The first esports module should target Overwatch because it has clear mechanical execution, tactical perception, hidden-state inference, and team-coordination demands.

Recommended subject layout:

```text
subjects/overwatch-review/
  subject.md
  concept-graph.yaml
  media-index.yaml
  vod-reviews/
    2026-05-12-kings-row.md
  mechanics-drills.yaml
  tactical-patterns.yaml
  learning-objects/
  practice-items/
  errors.md
```

The esports model should not treat every failure as failed memory. A fight can be lost after a correct decision, and a bad decision can succeed because of variance, opponent error, or teammate compensation. Review should separate outcome from decision quality.

Core review prompts:

- What did you believe was true at this moment?
- What evidence supported that belief?
- What alternative hypotheses were plausible?
- Which cue would have changed the posterior most?
- Was the action good in expectation, or only good/bad in outcome?
- What drill or focus cue should be used next game?

Initial Overwatch error families:

| Error family | Meaning | Examples |
| --- | --- | --- |
| `execution_error` | Intended action was reasonable, execution failed | aim, timing, movement, mechanics |
| `selection_error` | Wrong action given the learner's beliefs | bad target priority, wrong cooldown, poor path |
| `estimation_error` | Belief state was wrong or missing key hidden-state inference | enemy location, cooldowns, ult economy, sightline threat |
| `coordination_error` | Individually plausible action was poor relative to team state | desynced engage, unsupported angle, ignored teammate resource |
| `attention_error` | Relevant information was visible but not sampled or prioritized | wrong threat, missed flank, focused low-value cue |

Mechanics diagnostics should support manual labels first:

- hitscan overshoot / undershoot,
- smooth tracking vs jerkiness,
- reaction timing,
- click timing,
- movement aim,
- projectile lead too little / too much,
- prediction anchored to current rather than future position,
- timing wrong against acceleration, verticality, or state change,
- bad prior over opponent movement options.

Game-sense diagnostics should use a Bayesian hidden-state frame. The learner maintains beliefs over enemy positions, cooldowns, ultimates, sightlines being watched, opponent intentions, teammate resources, and likely fight plans. VOD review trains which cues matter and how beliefs should update under uncertainty.

Default esports evidence facets should map into the core axes:

| Facet | Core axes |
| --- | --- |
| `aim_precision` | execution |
| `aim_smoothness` | execution |
| `click_timing` | execution |
| `projectile_lead_model` | execution, generalization |
| `movement_mechanics` | execution |
| `threat_detection` | understanding, generalization |
| `hidden_state_inference` | understanding, calibration |
| `cooldown_tracking` | memory, understanding |
| `ultimate_tracking` | memory, understanding |
| `sightline_model` | understanding, generalization |
| `action_selection_ev` | generalization, calibration |
| `team_state_coordination` | generalization |

The scheduler for esports should recommend focus blocks rather than pure due-card review: one mechanics focus, one VOD belief reconstruction, one tactical perception prompt, or one coordination review. FSRS can still schedule recurring concepts and error patterns, but the main loop is deliberate focus, VOD reflection, and drill selection.

Recommended esports domain modes:

```text
esports_overwatch:vod_review
esports_overwatch:mechanics_focus
esports_overwatch:belief_reconstruction
esports_overwatch:tactical_perception
esports_overwatch:decision_postmortem
esports_overwatch:coordination_review
esports_overwatch:expert_comparison
```

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
auth_mode = "chatgpt"                   # subscription-backed, not metered API
structured_output = true
grader_role = "rubric-grader"
server_startup_timeout_seconds = 10
server_shutdown_timeout_seconds = 5
restart_on_crash = true
required_for_daily_loop = true          # daily loop requires Codex; offline runs degraded mode
degraded_offline_mode = true            # allow review + self-grade + manual error tagging when Codex is unavailable
# Availability detection (see §12)
probe_on_vault_open = false             # lazy first check by default; true = eager probe at vault open
availability_cache_seconds = 300        # how long an `available` state is trusted before re-probing
mid_attempt_fallback = "prompt_with_default"  # prompt_with_default | silent_self_grade | block_and_queue
mid_attempt_prompt_timeout_seconds = 5  # how long the inline prompt waits before defaulting to self-grade
# Per-error retry policy (see §12)
rate_limit_backoff_seconds = 30         # initial backoff; subscription tiers throttle, back off rather than fail hard
rate_limit_min_backoff_seconds = 300    # used when retry-after header is missing
network_backoff_seconds = 30
network_backoff_max_seconds = 300       # exponential cap
server_error_backoff_seconds = 30
auto_regrade_on_recovery = true         # re-fire tier-4 grading on attempts deferred while Codex was unavailable

[scheduler]
algorithm = "fsrs_object_mastery_greedy_eig"  # py-fsrs + object mastery + uncertainty-aware queue
default_retention = 0.9
review_intervals = [1, 3, 7, 14, 30, 60, 120]
adaptive_elicitation = true
elicitation_policy = "heuristic_greedy_eig"   # heuristic_greedy_eig (MVP); simulator_eig (later, gated)
elicitation_target_scope = "active_goals"
surprise_modulates_fsrs = true
surprise_diagnostic_threshold = 1.5
information_gain_weight = 0.15
error_uncertainty_weight = 0.10
# Codex-simulator ephemeral diagnostic generation
simulator_ephemerals_enabled = true       # propose ephemeral PIs when heuristic EIG plateaus
simulator_ephemerals_per_session_max = 3
simulator_ephemeral_min_uncertainty = 0.3 # only fire when variance on the target belief is above this
simulator_eig_context = "probe_phase_only"  # probe_phase_only | probe_and_posterior_modes
                                            # MVP: probe-phase fallback only. Normal-phase simulator-EIG
                                            # is reachable only via manual `learnloop diagnose-lo --deep`
                                            # and `learnloop generate-diagnostic` (§11) until enabled here.
# Later: full predictive-LM EIG pass
deep_diagnostic_pass_enabled = false
deep_diagnostic_candidate_pool = 20
deep_diagnostic_samples_per_candidate = 8
deep_diagnostic_latency_budget_ms = 15000
mcts_enabled = false
mcts_min_attempts = 500
mcts_latency_budget_ms = 750

[evaluation]
policy_eval_enabled = true
policy_eval_path = "evals/policy-goldens"
replay_eval_path = "evals/replay-fixtures"
simulated_learners_path = "evals/simulated-learners"
heldout_prediction_min_attempts = 30
counterfactual_randomization_rate = 0.05    # optional logged exploration for future unbiased comparisons
simulated_learner_noise = 0.10              # prevents overfitting policy changes to synthetic learners

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

[embeddings]
enabled = true
model = "sentence-transformers/all-MiniLM-L6-v2"
dim = 384
similarity_threshold_dedup = 0.92         # PI near-duplicate marks as pending_review at or above this
similarity_threshold_merge = 0.85         # concept-merge suggestion threshold
related_lookup_top_k = 8
batch_size = 64

[domains]
enabled = ["math_stats_ml", "research_papers", "language", "motor_vod", "esports_overwatch", "general"]

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
update_rule = "scalar_ema_with_theta_profile"  # per-LO scalar EMA + per-learner θ over evidence families
                                               # (algorithm_version >= 2.0.0; pre-2.0 used per-axis EMA)
ema_alpha = 0.2
difficulty_aware = true                        # hard success raises more; easy failure lowers more
error_aware_families = true                    # apply error_impacts (family-keyed) from error-taxonomy.yaml
flag_high_confidence_wrong = true              # mark as misconception; trigger repair loop
fluency_signals = ["latency_vs_expected", "hints_used", "pause_count", "consistency"]
belief_uncertainty = true                      # store uncertainty on LO scalar and θ slots
probe_mode_enabled = true                      # per-LO probe phase before steady-state scheduling
surprise_observation_fields = ["score_bucket", "error_type", "confidence", "latency_bucket", "hints_bucket"]

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

## `profile/goals.yaml`

`goals.md` is the narrative companion. `goals.yaml` is the structured source the scheduler reads for `active_goal_importance` and `deadline_pressure`. Every active goal has a stable id, a numeric priority in `[0, 1]`, an optional deadline, and a set of concept anchors (vault-global concept ids) that scope the goal into the concept graph.

```yaml
goals:
  - id: goal_linear_algebra_for_ml
    title: Linear Algebra for ML
    status: active
    priority: 0.9
    target: transfer_ready
    retention_horizon_days: 365
    deadline: null
    concept_anchors:
      - eigenvectors
      - svd
      - principal_components
      - orthogonality
    notes_md: "See goals.md → Linear Algebra for ML"

  - id: goal_korean_conversational
    title: Korean conversational + grammar accuracy
    status: active
    priority: 0.6
    target: ongoing
    retention_horizon_days: null
    deadline: null
    concept_anchors:
      - korean_grammar_topic_particle
      - korean_grammar_subject_particle
      - korean_conversation_repair
    notes_md: "See goals.md → Korean"

  - id: goal_qual_exam_2026_08
    title: Quals: causal survival modeling
    status: active
    priority: 1.0
    target: research_level
    retention_horizon_days: 365
    deadline: 2026-08-15                        # YYYY-MM-DD; drives deadline_pressure
    concept_anchors:
      - fine_gray_competing_risks
      - cox_partial_likelihood
      - cumulative_incidence_function
    notes_md: "See goals.md → Fine-Gray"
```

Scheduler inputs derived from `goals.yaml`:

- `active_goal_importance(item)` = max over active goals whose `concept_anchors` reach `item.learning_object.concept` (via the concept-graph prerequisite closure) of `goal.priority`.
- `deadline_pressure(item)` = max over those same goals of a smooth function of `days_until(deadline)`, zero when deadline is null.

Concept anchors are expanded through the global concept graph: a goal anchored on `svd` covers `lo_svd_decomposition`, `lo_pca_via_svd`, and any LO under prerequisite concepts the goal has not yet mastered.

A status of `active`, `dormant`, or `completed` controls inclusion in the daily queue without deleting the goal record.

## Note frontmatter convention

Notes are Markdown files under any subject's `notes/` folder. Frontmatter is optional but recommended; when present it declares subject membership and related LOs:

```markdown
---
subjects: [linear-algebra, ml]      # primary subject inferred from folder if omitted
related_los: [lo_svd_decomposition, lo_pca_via_svd]
related_concepts: [svd, principal_components]
created_at: 2026-05-12
---

# SVD note

...
```

A note without frontmatter is implicitly tagged with its folder's subject only. Frontmatter `subjects:` extends membership the same way LO YAML does. `learnloop doctor` checks that referenced LO ids and concept ids exist.

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

**Concept IDs are vault-global, not subject-scoped.** A single concept (e.g. `probability`) can be referenced from multiple subjects (`statistics`, `ml`, `survival-analysis`) without duplication. The authoritative concept registry lives at the vault root in `concepts/concepts.yaml` and `concepts/relations.yaml`. Per-subject `concept-graph.yaml` files are *views* that select which global concepts are in scope and add subject-specific ordering hints.

## Vault-level `concepts/concepts.yaml`

```yaml
concepts:
  eigenvectors:
    title: Eigenvectors
    type: concept
    aliases: [eigen-vectors, "eigen vector"]   # used by concept-merge suggestions
    common_confusions:
      - singular_vectors
      - principal_components
    next_action_hint: contrastive_discrimination

  svd:
    title: Singular Value Decomposition
    type: procedure
    aliases: ["singular value decomposition"]

  probability:                                  # shared across statistics, ml, survival-analysis
    title: Probability
    type: concept
```

## Vault-level `concepts/relations.yaml`

```yaml
prerequisites:
  - from: matrix_multiplication
    to: eigenvectors
  - from: linear_maps
    to: eigenvectors
  - from: orthogonality
    to: svd
  - from: eigenvectors
    to: svd
confusables:
  - [eigenvectors, singular_vectors]
  - [eigenvectors, principal_components]
```

Relations are stored separately from definitions so that adding a new prerequisite edge doesn't churn the definition file.

## Per-subject `subjects/<subject>/concept-graph.yaml` (view, mostly derived)

A subject is a **view**, not a content-ownership boundary. Learning Objects and Practice Items declare their membership via `subjects: [list]` in their YAML. The per-subject `concept-graph.yaml` is mostly derived from those tags at load time; the hand-curated portion shapes the view without enumerating every concept.

```yaml
subject: linear-algebra
# derived at load time (do not hand-edit):
#   in_scope: union of `concept` fields across all LOs whose subjects tag includes this subject,
#             plus additional_concepts_in_scope below, minus exclude_concepts.
#   learning_objects: tagged LOs, grouped by concept.

additional_concepts_in_scope:                  # planned, no LO yet
  - probability

exclude_concepts:                              # concept bled in via a multi-subject LO; hide here
  - quantum_mechanics

subject_ordering_hints:                        # subject-specific learning order
  - eigenvectors
  - svd
  - pca
```

`learnloop subject <id> --show-scope` prints the resolved derived view. `learnloop doctor` checks:

- every concept in `additional_concepts_in_scope` and `exclude_concepts` exists in the global registry;
- `exclude_concepts` doesn't list a concept that no tagged LO references (dead exclusion);
- every LO whose `subjects[0]` matches this subject sits in this subject's folder, or warns.

Learning Objects reference concepts by their global id (`concept: eigenvectors`). They reference subjects by id (`subjects: [linear-algebra]`).

## Concept merge

`concept.merge` is required when an extracted concept matches an existing one (by alias, embedding similarity, or learner confirmation). Merging collapses two global ids into one, rewrites all references across `concepts/`, subject views, Learning Objects, Practice Items, and SQLite, and writes a `change_batches` row with the inverse mapping for rollback.

## Mastery

Mutable mastery is not stored in concept files; it lives in SQLite and derived exports. The important thing is that mastery is multi-axis, with lower-level facets:

```text
Memory ≠ understanding ≠ execution ≠ generalization ≠ calibration.
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

A Learning Object can have many Practice Items across many practice modes. The Practice Item is what gets scheduled by FSRS; the Learning Object is what carries multi-axis mastery. The Concept aggregates over its Learning Objects.

## Learning Object (`learning-objects/<lo_id>.yaml`)

```yaml
id: lo_fine_gray_subhazard
title: Fine-Gray subdistribution hazard
subjects: [survival-analysis]              # primary subject first; required, >=1 element.
                                            # primary should match folder location; doctor warns otherwise.
concept: fine_gray_competing_risks          # vault-global concept id
knowledge_type: definition          # see KnowledgeType enum
status: active                      # active | dormant | resolved (resolved is for misconception LOs)
contradicts: null                   # only set on misconception LOs; points to the LO this misconception attacks
prerequisites:
  - lo_cause_specific_hazard
  - lo_competing_risks_setup
difficulty_prior: 0.7
references_worked_examples:          # two-way link with worked-examples/*.md (see §15.8)
  - worked-examples/we_fg_subhazard_definition_001.md
provenance:
  origin: human                     # human | canonical_extract | ai_generated | ai_variant
  source_id: null
created_at: 2026-05-01
```

Mastery axes and evidence facets are **not** stored as mutable estimates in this YAML — they live in `state.sqlite` and are updated from attempts. The YAML is a stable, human-editable description.

## Practice Item (`practice-items/<pi_id>.yaml`)

```yaml
id: pi_fg_subhazard_define_001
learning_object_id: lo_fine_gray_subhazard
# subjects inherited from learning_object_id by default; override here only if the
# specific framing is relevant in a strict subset of the LO's subjects.
# subjects: [survival-analysis]
practice_mode: short_answer         # see PracticeMode enum
attempt_types_allowed:              # see AttemptType enum
  - independent_attempt
  - hinted_attempt
  - dont_know
  - diagnostic_probe                # used during the LO's probe phase
evidence_facets:                    # canonical EvidenceFamily ids — the primary update channel
  - recall
  - schema
  - explanation
evidence_weights:                   # how much each declared family contributes to its θ update;
  recall: 0.40                      # values do not need to sum to 1 (normalized on read)
  schema: 0.35
  explanation: 0.25
# Legacy `target_mastery_axes` and `mastery_weights` keys are migrated automatically at vault
# load under algorithm_version >= 2.0.0 (each axis is mapped to its highest-weight aggregating
# family). Doctor warns on PIs whose migrated weights look thin.
prompt: "Define the Fine-Gray subdistribution hazard in your own words."
expected_answer: >
  It models the subdistribution hazard for a target event in the presence
  of competing risks, keeping competing-event cases in a modified risk set
  so the model targets the cumulative incidence function.
difficulty: 0.72
tags: [survival, competing-risks, definition]
hints:                                # first-class hint ladder; nth hint = hints[n-1]
  - "Think about how competing risks are handled in the risk set."
  - "Compare against the cause-specific hazard: what's different about who stays in the risk set?"
  - "It targets the cumulative incidence function rather than ordinary cause-specific hazard."
hint_policy:
  max_useful_hints: 3                 # source of truth for hints_used capping
  fsrs_rating_cap_by_hint:            # FSRS rating cap as hints accumulate (idx = hints_used)
    0: easy                           # no hints → no cap
    1: good
    2: hard
    3: again
  mastery_alpha_dampening_by_hint:    # multiplier on effective_alpha in update_mastery
    0: 1.00
    1: 0.75
    2: 0.50
    3: 0.25
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

## Hint ladders

`hints` is an ordered list of progressively-revealing nudges. The TUI's [Hint] button reveals the next entry. `hints_used` on each attempt is the number of hint-reveals the learner took, and it is the canonical source for:

- FSRS rating cap (from `hint_policy.fsrs_rating_cap_by_hint`),
- mastery EMA dampening (`hint_policy.mastery_alpha_dampening_by_hint` multiplies `effective_alpha`),
- the `hints_bucket` field used in surprise prediction.

Items with `hints: []` advertise that no hints are available and the [Hint] button is disabled. By default, `recognition`, `multiple_choice`, and other modes where a hint would give away the answer ship with `hints: []`.

### Generation policy (hybrid with cache)

Items without an explicit `hints` array follow a hybrid generation policy:

1. **Authored hints** (`hints: [...]` in the PI YAML) → use as-is.
2. **Codex available + no authored hints** → on the first `[Hint]` reveal in a session, call the `hint-author` role to generate the full ladder for this PI, write the result back into the PI YAML, and use it. Subsequent reveals (this session or future sessions) hit the cached ladder.
3. **Codex unavailable + no authored hints** → fall back to the per-mode static template in `prompts/hint_ladder_<mode>.md`, with substitutions like `{concept_title}`, `{knowledge_type}`, `{expected_first_step}`. The static fallback is not cached to the PI YAML.

The cache step in (2) is a normal LearnLoop content write — it goes through `change_batches` with `reason: hint_generation`, can be rolled back, and is provenance-tagged (`generator_run_id`, `model`, `prompt_template = hint_author`, `prompt_version`). The learner can edit cached hints later; edits set `provenance.review_status = approved` and bump `content_hash`.

### Hint-author validation and retry

Generated hint ladders are validated before being cached. A failure on the first attempt triggers one retry with explicit constraint patches in the prompt. A second failure falls back to the static template and flags the Practice Item in doctor for manual authoring.

Validation rules (defaults; configurable in `[grading].hint_author_guardrails`):

- **Answer-leakage guard:** no individual hint may have lexical overlap with `expected_answer` above `lexical_overlap_max = 0.40` (token-set Jaccard after normalization). For structured `expected_answer.key_terms`, no hint may name more than `key_terms_leakage_max = 1` term verbatim.
- **Rubric-trap guard:** if the PI's `grading_rubric.fatal_errors` is non-empty, no hint may contain the description text of any fatal-error entry (would tip off the trap).
- **Ladder shape:** length between `min_hints = 2` and `max_hints = 4`. Each hint ≤ `hint_max_chars = 200`. Ordered: each hint must be at least as specific as the previous (a local heuristic — token count and `expected_answer` overlap should be monotonically non-decreasing).
- **Final-step guard:** the last hint may overlap with `expected_answer` up to `final_hint_overlap_max = 0.55` (slightly more permissive — final hints can edge toward the answer), but still must not be the answer.

On a validation failure, the retry prompt receives a structured "violations" patch:

```text
Your previous attempt was rejected. Address these issues and try again:
- Hint 3 had 67% lexical overlap with the expected answer (limit 40%).
- Hint 2 named the fatal error trap "treats hazard as a probability" verbatim.
Keep the ladder shape (2–4 hints, each ≤ 200 chars).
```

The second attempt is validated the same way; a second failure causes:

1. The static per-mode template ladder is cached on the PI YAML instead (provenance-tagged as `origin: ai_generated_failed_validation_static_fallback`).
2. A doctor warning is raised on the PI suggesting manual hint authoring.
3. `agent_runs` records both attempts and their validation outcomes, so the user can later inspect what went wrong via `learnloop lineage <pi_id>` or `learnloop ai history`.

Config:

```toml
[grading.hint_author_guardrails]
lexical_overlap_max = 0.40
key_terms_leakage_max = 1
final_hint_overlap_max = 0.55
min_hints = 2
max_hints = 4
hint_max_chars = 200
retry_on_failure = true
```

Static templates (path (3)) are deliberately generic. They serve to keep `[Hint]` from being a dead button offline, not to be high-quality nudges.

Hinted attempts log as `attempt_type: hinted_attempt` regardless of how the ladder was sourced. The grading pipeline runs normally; only the FSRS rating cap and mastery dampening change.

### Per-mode static template structure

`prompts/hint_ladder_<mode>.md` is a small Markdown file with one substituted line per hint level:

```markdown
---
name: hint_ladder_short_answer
version: 1
applies_to: short_answer
---
1. Think about what {concept_title} is fundamentally for — its purpose, not its formula.
2. The expected answer involves {knowledge_type}. What does that imply about structure?
3. Try starting with: "{expected_first_step}"
```

Substitutions are resolved from the LO and PI at hint-reveal time. If a substitution is missing, the bracket placeholder is shown as-is — better than a crash, and easier for `learnloop doctor` to spot.

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
│ Active-Goal Uncertainty: 3 high            │
│ Pending Reviews: 7   (R to triage)         │
│ Suggested Session: 75 min                  │
├────────────────────────────────────────────┤
│ 1. Start Today's Loop                      │
│ 2. Review Due Items                        │
│ 3. Generate Practice                       │
│ 4. Diagnose Solution                       │
│ 5. Error Notebook                          │
│ 6. Concept Graph                           │
│ 7. Open Codex Tutor                        │
│ R. Review Grades  (7 pending)              │
└────────────────────────────────────────────┘
```

## Review grades (manual review triage)

Reachable from the main screen (key `R`), the `learnloop review-grades` CLI, or the end-of-session sweep (which surfaces pending reviews alongside ephemeral promotions). One item at a time, fully keyboard-driven:

```text
┌────────────────────────────────────────────────────────────┐
│ Review Grades  —  3 of 7                                   │
├────────────────────────────────────────────────────────────┤
│ Item: pi_fg_subhazard_define_001                           │
│ Concept: fine_gray_competing_risks                          │
│ Mode: short_answer        Grader: tier 4 (LLM)              │
│ Grader confidence: 0.58   (below floor 0.60)                │
├────────────────────────────────────────────────────────────┤
│ Prompt:                                                     │
│ Define the Fine-Gray subdistribution hazard.                │
│                                                             │
│ Learner answer:                                             │
│ It models the subdistribution hazard for the event of       │
│ interest in the presence of competing risks.                │
│                                                             │
│ Proposed grade: 2/4                                         │
│ Rationale: Mentions target event and competing risks,        │
│   but does not mention the modified risk set or             │
│   cumulative incidence function.                            │
├────────────────────────────────────────────────────────────┤
│ [✓] accept    [✗] override    [↺] regrade    [→] defer      │
│ [T] trust this rubric for the rest of the session            │
└────────────────────────────────────────────────────────────┘
```

Actions:

- `✓` — accept the proposed grade; mastery update fires now.
- `✗` — open a numeric prompt to set a different score; mastery update fires with `grader_confidence = 1.0` (the human is the grader for this item).
- `↺` — re-run the LLM grader. The previous evidence is preserved with `superseded_at`; the new evidence replaces it as authoritative.
- `→` — defer; stays in the queue.
- `T` — set a session-scoped flag that auto-accepts subsequent tier-4 grades from the same rubric template (matched by `prompt_template + prompt_version`). Clears at session end.

Pending-review counter on the main screen is read-only summary state; opening the triage screen recomputes it. If the user starts `Today's Loop` while reviews are pending, the loop runs as normal — pending reviews don't block daily practice. They are surfaced again at session end.

## Session start (readiness gate)

Shown before every session if `[learning].readiness_gate = true`. Captured to the `sessions` table and fed into the scheduler’s readiness modulation.

```text
┌────────────────────────────────────────────┐
│ Session Start                              │
├────────────────────────────────────────────┤
│ Energy:        ( ) low  (•) med  ( ) high  │
│ Sleep last:    ( ) <6h  (•) 6-8h  ( ) >8h  │
│ Available:     [ 75 ] minutes              │
│ Focus pattern: ( ) short  (•) pomodoro 25/5│
│                ( ) continuous              │
├────────────────────────────────────────────┤
│ [Start Session]                            │
└────────────────────────────────────────────┘
```

### Short-session mode

When `available_minutes < 20` (or the learner picks "short" explicitly), the readiness gate switches the entire daily loop to a stripped-down flow. No deep-work block, no transfer challenge, no new material. The queue collapses to warm-up retrieval on items closest to forgetting, plus any open misconception-repair items in a contrastive-discrimination format. Cold opens, commutes, and stolen 10-minute slots become useful instead of being skipped.

```text
┌────────────────────────────────────────────┐
│ Short Session (15 min)                     │
├────────────────────────────────────────────┤
│ Warm-up retrieval        12 min            │
│   • items closest to forgetting only       │
│   • no new material, no transfer           │
│ Open misconception drill  3 min            │
│   • contrastive_discrimination, if any     │
└────────────────────────────────────────────┘
```

Short-session sessions still log normally and update FSRS state, but the scheduler suppresses the surprise-driven diagnostic-followup interruption (low-time sessions don't have time for a diagnostic detour). Ephemeral diagnostic generation is also suppressed.

## Today’s loop

When `focus_blocks = "pomodoro"`, deep-work blocks are 25 min with 5-min retrieval breaks (the break fills with warm-up retrieval rather than idle time). When `continuous`, the loop runs straight through.

```text
┌────────────────────────────────────────────┐
│ Today’s Learning Loop  (pomodoro 25/5)     │
├────────────────────────────────────────────┤
│ Warm-up Retrieval       10 min             │
│ Deep Work block 1       25 min             │
│   ↳ break: retrieval     5 min             │
│ Weakness Repair         20 min             │
│ Transfer Challenge      15 min             │
└────────────────────────────────────────────┘
```

## Practice screen

```text
┌────────────────────────────────────────────┐
│ Concept: SVD → PCA                         │
│ Mode: Explain from memory                  │
│ Difficulty: 0.78                           │
│ Why now: info gain + transfer gap + error   │
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

When the LO is in **probe mode** (`lo_probe_state.status = in_progress`, see §16 Layer 4), the practice screen shows a probe badge in the header so the learner understands what kind of attempt this is. Probe attempts disable hints by default and suppress negative-surprise follow-ups (the first attempts on a new LO are expected to be surprising; inserting a follow-up on every probe defeats the point):

```text
┌────────────────────────────────────────────────────────────┐
│ Concept: SVD → PCA                                         │
│ Mode: short_answer        [DIAGNOSTIC PROBE — 2 of 3]      │
│ Why now: first-time calibration for this LO                │
├────────────────────────────────────────────────────────────┤
│ Prompt: ...                                                │
└────────────────────────────────────────────────────────────┘
```

The `Why now` line opens a scheduler explanation panel. It shows the score components that selected the item:

```text
Why this item?
  Forgetting risk        0.24   due today, retrievability 0.21
  Information gain       0.13   active-goal uncertainty is high
  Error uncertainty      0.09   recall failure vs schema confusion unresolved
  Transfer gap           0.15   recall 0.86, transfer 0.38 (status: estimated)
  Recent error           0.12   missed centering assumption yesterday
  Readiness adjustment  +0.00   medium energy
  Next action            transfer
```

For a probe-mode item, the "Why now?" panel uses a different layout that emphasizes the probe purpose rather than the standard priority components:

```text
Why this item?
  Probe mode             active   first 3 attempts on this LO
  Discrimination at θ    0.24     item difficulty near your expected ability
  Family coverage        schema, explanation
  Probe attempts left    1 of 3
  Profile update         expected ≈ 0.06 logits on θ[math_stats_ml, schema]
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
│ Surprise: negative, moderate               │
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

## Answer input widget

The practice screen's answer input handles four classes of answer with one consistent UX:

- **Short inline** — single line, soft cap at `[tui].inline_max_chars = 200`. Above the cap, a hint appears: "Ctrl-E to open editor." Pressing Enter without Ctrl-E still submits, but past the cap LearnLoop logs a `widget_truncation_risk` warning to the session log.
- **Long answer** — `Ctrl-E` opens `$EDITOR` (or `[tui].editor_command` if set). The TUI yields the terminal; on editor exit, the file content becomes the answer. Autosaves to `session_checkpoints` every `[sessions].autosave_seconds` even mid-edit (the temp file is watched).
- **Math** — learners write LaTeX-style `$inline$` and `$$display$$`. The widget doesn't typeset live; the source is preserved as-is. Feedback view renders the surrounding Markdown via Rich; math segments are shown literal (e.g. `$\sigma = U^T A V$` displays as that exact string with a subtle highlight). Pretty-printing (KaTeX-style) is **deferred** — it adds a real dependency and isn't blocking for math/stats/ML usefulness.
- **Code** — fenced Markdown blocks (```` ```python ... ``` ````). Feedback view applies Rich syntax highlighting using the language tag. No execution, no sandboxing in MVP.

The feedback screen renders:

```text
┌──────────────────────────────────────────────────────────────────┐
│ Your answer:                                                      │
│   The eigenvectors of $A^T A$ give the right singular vectors;    │
│   their eigenvalues are $\sigma_i^2$.                             │
│                                                                   │
│   ```python                                                       │
│   U, S, Vt = np.linalg.svd(A)                                     │
│   ```                                                             │
│ (markdown rendered; math shown literal; code highlighted)          │
└──────────────────────────────────────────────────────────────────┘
```

Config in `learnloop.toml`:

```toml
[tui]
inline_max_chars = 200
editor_command = ""              # empty = $EDITOR env var, then "vi"
feedback_markdown = true
feedback_code_highlight = true
feedback_math_pretty_print = false   # MVP: false; later flag for KaTeX-style rendering
```

Deferred to later: file-attachment answers (e.g. a screenshot for VOD review), drag-and-drop, sandboxed code execution, live math rendering.

## Forgetting curve

Per-LO retention visualization. The y-axis is retrievability (FSRS-derived); marker points are actual attempt scores. The curve is reconstructed from `practice_item_state` history and `practice_attempts` rather than recomputed from scratch.

```text
┌────────────────────────────────────────────┐
│ Forgetting Curve: lo_svd_decomposition     │
│ retrievability over the last 60 days       │
├────────────────────────────────────────────┤
│ 1.0 ●                                      │
│     │ ●  ●                                 │
│ 0.8 │      ●                               │
│     │           ●         ●                │
│ 0.6 │                ●            ●        │
│     │                         ✕            │
│ 0.4 │                                      │
│     └──────────────────────────────────── │
│      d0     d7   d14   d28   d42   d60     │
│                                            │
│ ●  attempt (score)    ✕  forgotten (<0.30) │
│ Next due: in 3 days                        │
└────────────────────────────────────────────┘
```

Subject-level aggregate replaces the marker dots with a band (10th–90th percentile across LOs in scope). Useful for motivation and for spotting decayed concepts after a long break.

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
learnloop today --include-probes                   # force probe-mode LOs into a short session (override)
learnloop today --diagnostic                       # enroll all unscheduled active-goal LOs into probe mode
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
learnloop forgetting-curve <lo_id>                 # plot retrievability over time for an LO
learnloop forgetting-curve --subject linear-algebra # aggregate curve for a subject
learnloop uncertainty                              # inspect active-goal uncertainty and surprise signals
learnloop surprise <attempt_id>                    # inspect the prediction and surprise from one attempt
learnloop observe <template_id>                     # fill a structured observation/reflection template
learnloop replay-model                              # recompute mastery, beliefs, surprise from raw attempts
learnloop replay-model --diff                       # replay then show top-N largest mastery/variance movers
learnloop replay-model --restore <snapshot_id>      # restore a pre-replay snapshot
learnloop replay-model --accept-without-replay      # mark the new algorithm version accepted without recomputing
learnloop errors
learnloop review-grades                            # triage pending manual-review grades
learnloop ai status                                # codex availability state + last error + ETA
learnloop ai login                                 # walk codex SDK auth flow
learnloop ai recheck                               # force an immediate availability probe
learnloop profile                                  # show current θ posterior (per domain × evidence family) with CIs
learnloop profile --explain                        # break down which attempts moved each θ slot
learnloop claims                                   # list active learner_claims rows
learnloop claims wizard                            # re-run the background-claims init wizard
learnloop claims add <scope> --level 0.8           # add a manual claim (scope = concept|lo|subject|domain id)
learnloop probes status                            # list LOs by lo_probe_state.status
learnloop probes status --pending                  # filter to LOs waiting to enter probe mode
learnloop probes hypotheses <lo_id>                # dump the active HypothesisSet for an LO (debug)
learnloop diagnose-lo <lo_id> --deep [--ephemeral|--promote-to-inbox] [--budget N]
                                                   # manual deep-diagnostic on a mature LO; uses surrogate
                                                   # posterior-mode hypotheses (the disabled-by-default path)
learnloop generate-diagnostic --goal <goal_id> --budget 5 [--promote-to-inbox]
                                                   # batch-generate diagnostics targeted at an active goal
learnloop uncertainty --suggest-probes             # read-only: list LOs that would benefit from a probe
learnloop domain list                              # enabled / disabled / purgeable domains
learnloop domain enable <id>                       # add to [domains].enabled (runs migrations if needed)
learnloop domain disable <id>                      # remove from [domains].enabled (soft; data preserved)
learnloop domain purge <id>                        # destructive removal; requires double-confirm
learnloop tutor reset <subject>                    # archive the current tutor thread; next invocation starts fresh
learnloop tutor history <subject>                  # list archived tutor threads with briefs
learnloop misconceptions                           # list active misconception LOs
learnloop lineage <pi_id>                          # provenance tree for a Practice Item
learnloop graph linear-algebra
learnloop session-summary
learnloop exports refresh
learnloop eval grading                             # run local grading regression fixtures
learnloop eval scheduler                           # run deterministic queue/explanation fixtures
learnloop eval policy                              # compare scheduler/EIG policies on counterfactual fixtures
learnloop eval replay --holdout recent             # held-out response prediction from raw attempts
learnloop eval simulate --scenario <scenario_id>   # run synthetic learner policy simulations
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
- LO / PI `subjects: [list]` invariant: ≥1 element, every subject id exists, `subjects[0]` matches the file's folder (warn-only),
- note frontmatter `subjects:` references valid subject ids; `related_los` / `related_concepts` references resolve,
- per-subject `concept-graph.yaml` view: `additional_concepts_in_scope` and `exclude_concepts` reference valid global concepts; no dead exclusions,
- worked-example two-way links: every `teaches_los` entry resolves to a real LO whose `references_worked_examples` lists this file, and vice versa,
- `media-index.yaml` entries: paths resolve or fingerprint-match a file in `[media].search_roots`; ambiguous fingerprints reported; missing media listed with dependent items,
- observation templates: `lo_binding.mode == template_fixed` implies `template_fixed_lo` set; `applies_to_mode == restrict` predicates compile; suggest_from sources are valid,
- missing source ids for canonical content,
- stale content hashes,
- stale learner-state beliefs or missing surprise records for recent attempts,
- replayed learner-state mismatch against the current algorithm version,
- orphaned SQLite rows,
- invalid due dates or timezone values,
- missing prompt templates and rubrics,
- malformed grading/scheduler/policy evaluation fixtures,
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
| `attempt.log` | Record a graded attempt | `state.sqlite` (attempts, FSRS, mastery, beliefs, surprise, errors) |
| `inbox.submit` | Send generated content to the inbox with provenance | `inbox/pending/*.yaml` |
| `inbox.accept` / `inbox.reject` | Move inbox items to canonical location | YAML + SQLite |
| `grade.rubric` | Run SDK-backed grading and store evidence | grading evidence in SQLite |
| `mastery.update` | Apply EMA + error-impact updates from an attempt | SQLite |
| `surprise.record` | Compare predicted vs observed answer evidence and store Bayesian surprise | SQLite |
| `elicitation.score` | Score candidate questions by expected information gain against active goals | reads SQLite + optional ephemeral candidates |
| `schedule.next` | Compute next due item(s) using FSRS + object mastery + greedy information gain | reads SQLite |
| `uncertainty.inspect` | Summarize active-goal belief uncertainty and recent surprise | reads SQLite |
| `surprise.inspect` | Explain one attempt's prior prediction, observation, surprise, and actions | reads SQLite |
| `observation.start` / `observation.complete` | Fill and record a structured observation template | SQLite + optional Markdown |
| `model.replay` | Rebuild mastery, beliefs, surprise, due queue, and explanations from raw events | SQLite derived tables |
| `scheduler.eval` | Run scheduler golden fixtures and compare expected queues/explanations | reads fixture vaults |
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
- **`hint-author`** — given a Practice Item missing a `hints` ladder, generates a progressive 2–4 step ladder informed by the LO, expected_answer, common errors, and (where relevant) the hint policy. Output is cached back into the PI YAML.
- **`tutor-summarizer`** — given an archived tutor thread, produces a ~200-token brief covering: topics covered, recurring questions, error patterns surfaced, unresolved threads. Used as the first system message of the next tutor thread on the same `(subject, purpose)` to preserve continuity.
- **`worked-example-author`** — given an LO and the learner's profile, generates a worked example Markdown file (with optional structured `steps:` when the LO benefits from later faded variants). Used when the scheduler picks a `walkthrough` for an LO with no existing worked example.

## Codex availability state machine

The adapter holds an in-process availability state surfaced to the TUI (corner status indicator) and to the CLI (`learnloop ai status`). States:

| State | Meaning | Auto-retry? | User action required? |
| --- | --- | --- | --- |
| `unknown` | No probe yet this process | First AI feature triggers probe | No |
| `available` | Last call succeeded; cache fresh | n/a | No |
| `auth_required` | SDK reported auth error (missing, expired, revoked) | **No** — auth changes need user action | `learnloop ai login` |
| `rate_limited` | Subscription tier throttled | Yes, after `retry-after` (min `rate_limit_min_backoff_seconds`) | No (unless persistent) |
| `network_unavailable` | Transport error | Yes, 30s exponential backoff capped at `network_backoff_max_seconds` | No |
| `server_error` | 5xx from Codex | Yes, 30s exponential backoff | No |
| `streaming_dropped` | Mid-turn disconnect | Specific turn marked failed; next AI feature retries immediately | No |

**First check.** Lazy by default — the first AI feature triggers a probe. When `[ai].probe_on_vault_open = true`, a quick background probe runs at vault open so the indicator is correct before the learner asks for anything.

**Cache.** An `available` state is trusted for `[ai].availability_cache_seconds` (default 300). Any successful call refreshes the cache. Any failure transitions out of `available` immediately and writes the new state with the timestamp.

**Recovery and auto-regrade.** When the state transitions from any non-`available` state to `available`, the adapter emits a `codex_recovered` event. If `[ai].auto_regrade_on_recovery = true`, a background task scans `practice_attempts` rows where `manual_review = 1 AND manual_review_reason = 'codex_unavailable'`, requeues them for tier-4 grading, and on success clears the manual-review flag and applies the previously-held mastery update. The learner sees a toast: "Codex recovered. 3 deferred attempts regraded." Failed regrades stay in the manual-review queue.

**TUI surface.** Corner status indicator:

- `●` green = `available`
- `●` yellow = transient (`rate_limited`, `network_unavailable`, `server_error`, `streaming_dropped`)
- `●` red = persistent (`auth_required`)
- `○` gray = `unknown`

Hovering or pressing `?` on the indicator shows the last error and ETA to next retry.

**CLI:**

```bash
learnloop ai status        # current state + last probe + last error + ETA
learnloop ai login         # walk the Codex SDK auth flow
learnloop ai recheck       # force a probe now (resets cache)
```

## Per-purpose rate-limit behavior

The state machine handles availability. Each purpose has its own response when Codex becomes unavailable mid-call:

| Purpose | Behavior on rate-limit / network failure |
| --- | --- |
| `rubric-grader` (tier 4) | Mid-attempt fallback (§15.6): inline 5s self-grade prompt; deferred attempts auto-regrade on recovery. |
| `tutor` | Cache the user's pending message; show transparent waiting state with retry ETA; auto-resume the thread on recovery. **See below.** |
| `variant-generator`, `hint-author`, `worked-example-author`, `tutor-summarizer` | Defer: the generation is queued and retried on recovery; the user is not blocked. |
| `canonical-ingestor` | Defer: ingestion jobs run in background; pause and resume on availability. |
| `error-diagnostician` | Mid-attempt fallback (same as grader): self-grade prompt; deferred diagnosis re-runs on recovery. |
| Simulator-EIG ephemeral proposer | Skip silently — heuristic-bucket EIG is the workhorse; missing ephemerals just means no diagnostic proposals this session. |

### Tutor cache-and-resume

When a tutor call fails mid-conversation (rate limit, network drop, server error), LearnLoop persists the pending user input rather than losing it:

```sql
CREATE TABLE tutor_pending_messages (
  thread_key TEXT PRIMARY KEY,           -- (vault_id, subject, purpose) tuple serialized
  pending_input TEXT,                    -- the user's last input that hadn't been answered
  appended_inputs TEXT,                  -- JSON list; if the user types more while waiting
  attempted_at TEXT,
  retry_after TEXT,                      -- ETA parsed from retry-after header (if any)
  status TEXT                            -- waiting | resumed | abandoned
);
```

TUI surface during the wait:

```text
┌──────────────────────────────────────────────────────────────────┐
│ Codex Tutor — survival-analysis                                  │
├──────────────────────────────────────────────────────────────────┤
│ You: Why does Fine-Gray treat censored subjects differently than │
│       Kaplan-Meier?                                              │
│                                                                   │
│ ⏳ Codex is rate-limited. Your message is queued.                │
│    Estimated retry: 2m 14s                                       │
│                                                                   │
│ You can keep typing — additional messages will be appended.      │
├──────────────────────────────────────────────────────────────────┤
│ > _                                                               │
│ [Cancel queued message]  [Switch to offline review]              │
└──────────────────────────────────────────────────────────────────┘
```

On recovery (state transitions to `available`), the adapter resumes the thread by feeding the cached input plus any appended inputs as one combined message, then streams the response in normally. The `tutor_pending_messages` row clears on success or on user cancellation. If the user explicitly closes the tutor screen with a pending message, status flips to `abandoned`.

Cached messages survive process restarts — opening `learnloop today` after a crash recovers any pending tutor inputs.

## Thread management

Codex threads are keyed by `(vault_id, subject, purpose)`. The adapter maintains them per-purpose:

| Purpose | Thread lifetime | Persistence |
| --- | --- | --- |
| `tutor` | Long-lived (weeks to months); archived periodically | Persisted in `tutor_threads` table; resumed across sessions |
| `rubric-grader`, `error-diagnostician`, `variant-generator`, `hint-author`, `worked-example-author`, `canonical-ingestor`, `tutor-summarizer`, simulator proposer | Stateless per-call | Not persisted; each call is its own thread |

The stateless purposes don't need continuity — every grading or generation call carries its full context in the prompt. Only `tutor` benefits from thread state.

### Tutor thread storage

```sql
CREATE TABLE tutor_threads (
  thread_key TEXT PRIMARY KEY,           -- (vault_id, subject, purpose)
  sdk_thread_id TEXT,                    -- handle returned by the Codex SDK
  started_at TEXT,
  last_used_at TEXT,
  turn_count INTEGER,
  cumulative_tokens INTEGER,
  status TEXT                            -- active | archived | abandoned
);

CREATE TABLE tutor_thread_archives (
  id TEXT PRIMARY KEY,
  thread_key TEXT,                       -- references tutor_threads
  archived_at TEXT,
  reason TEXT,                           -- turn_cap | token_cap | inactivity_cap | manual_reset
  turn_count_at_archive INTEGER,
  cumulative_tokens_at_archive INTEGER,
  brief TEXT,                            -- ~200-token summary from tutor-summarizer
  brief_agent_run_id TEXT
);
```

### Archival policy

A tutor thread is archived when **any** of:

- `turn_count > [tutor].thread_turn_cap` (default 80)
- `cumulative_tokens > [tutor].thread_token_cap` (default 50000)
- `(now - last_used_at).days > [tutor].thread_inactivity_cap_days` (default 30)

On archival:

1. `tutor-summarizer` is invoked (one Codex call) to produce a ~200-token brief covering topics, recurring questions, error patterns, and unresolved threads.
2. A `tutor_thread_archives` row is written with the brief.
3. The `tutor_threads` row flips `status = archived`.
4. Next time the user invokes the tutor for the same `(subject, purpose)`, a fresh thread is started with the most-recent archive's `brief` as the first system message (after the standard tutor system prompt).

If `tutor-summarizer` fails (rate limit, etc.), the archive row is still written but with `brief = null`; the next thread starts without continuity and a doctor warning is raised. The brief is generated again opportunistically on next Codex availability if the archive's brief is still null.

Manual reset: `learnloop tutor reset <subject>` archives the current thread immediately (reason `manual_reset`) — useful when the learner wants a fresh tutor context (e.g. switching focus within a subject).

Config:

```toml
[tutor]
thread_turn_cap = 80
thread_token_cap = 50000
thread_inactivity_cap_days = 30
preserve_brief_on_archive = true       # if false, archive without summarizing (no Codex call needed)
```

## Lifecycle

```text
TUI start
   ↓
open vault + run migrations + refresh exports
   ↓
(optional) eager Codex probe if probe_on_vault_open is set
   ↓
start Codex SDK client lazily when first AI feature is used
   ↓
create/resume subject-specific thread
   ↓
stream turns or receive structured proposals
   ↓
validate and apply LearnLoop-owned operations
   ↓
on availability change → emit codex_recovered or codex_unavailable
                       → auto-regrade deferred attempts if recovered
   ↓
TUI exit → close SDK client gracefully
```

One LearnLoop process can work across multiple vaults, but only one vault is active in a TUI session. Each vault has independent SQLite state, exports, AGENTS.md, and Codex context.

## Why SDK-first

- No maintenance burden from a Codex fork.
- No hand-rolled protocol layer in MVP.
- Streaming, turn state, thread resume, and auth stay delegated to the SDK.
- Subscription-backed auth (ChatGPT) avoids per-call metered cost; rate limits, not dollars, are the binding constraint.
- LearnLoop keeps authoritative state local and validated.
- The system remains usable in **degraded offline mode** for review, self-graded attempts, and manual error tagging when Codex is unreachable.

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

When a learner asks for more practice mid-session, the agent generates items inline. These are stored as ephemeral and **not** promoted to permanent Practice Items by default. Ephemeral diagnostic items may also be generated by the Codex-simulator EIG path (Layer 4, §16) when no existing PI is informative enough about a high-priority belief.

## End-of-session promotion sweep

When a session ends with unpromoted ephemerals, LearnLoop runs a **promotion sweep** that proposes which items deserve to become permanent Practice Items. The sweep is local (no extra Codex calls); rationale text was generated and cached when the ephemeral was first created. Each item gets a per-item recommendation (`promote`, `skip`, `revise`) and a one-line rationale:

```text
┌──────────────────────────────────────────────────────────────────────┐
│ End-of-Session Sweep                                                 │
│ The session generated 4 ephemeral items. Recommendations:            │
├──────────────────────────────────────────────────────────────────────┤
│ [✓] Promote  "Explain PCA on uncentered data — what changes?"        │
│              → lo_pca_via_svd                                        │
│              Why: discriminated recall vs schema (high info gain);   │
│                   no existing PI on this contrast.                   │
│                                                                      │
│ [✓] Promote  "Sketch a counterexample where SVD ≠ eigendecomposition"│
│              → lo_svd_decomposition                                  │
│              Why: targets active misconception "SVD = eig of A".     │
│                                                                      │
│ [ ] Skip     "Compute SVD of [[1,0],[0,1]]" → lo_svd_decomposition   │
│              Why: near-duplicate of pi_svd_identity_001 (sim 0.94).  │
│                                                                      │
│ [~] Revise   "What is PCA?"                                          │
│              Why: too broad; suggest narrowing to specific axis      │
│                   (e.g. "Why centering matters") before promoting.   │
├──────────────────────────────────────────────────────────────────────┤
│ [Promote checked] [Edit selected] [Skip all] [Defer to inbox]        │
└──────────────────────────────────────────────────────────────────────┘
```

Sweep recommendations are scored from:

- **Information gain achieved** during the session (how much did the learner's belief variance drop after this item?),
- **Existing-pool coverage** (embedding similarity to existing PIs on the same LO; high similarity → skip),
- **Misconception linkage** (items that successfully exercised a misconception LO are strong promote candidates),
- **Item quality heuristics** (length, prompt clarity, presence of canonical expected_answer or rubric).

The "Defer to inbox" path routes selected items to standard inbox policy (auto-accept as variant if descending from an approved item; review otherwise). Skipped ephemerals are deleted from `ephemeral_session_items` after the session ends; promoted ones are linked through `promoted_to_practice_item_id`.

If a session ends without an explicit sweep (interrupted, force-quit), the sweep runs on the next `learnloop today` or `learnloop resume`.

## Active vs dormant

Practice Items have an `active` flag in SQLite. Dormant items are kept (with full history) but not scheduled. This is the safe path for "I made too many items" without losing data. Reactivating restores FSRS state.

## Observation templates

Not every useful learning event is a card-like prompt. Domains can define structured observation templates for reflection, VOD review, lab notes, conversation turns, debugging sessions, or deliberate-practice drills. Observation templates are YAML, versioned, and can produce attempts/evidence without pretending the activity was a simple recall card.

```yaml
id: obs_overwatch_hidden_state_review
domain: esports_overwatch
title: Overwatch hidden-state VOD review
applies_to:
  - esports_overwatch:belief_reconstruction
fields:
  - id: timestamp
    type: media_timestamp
    required: true
  - id: believed_state
    type: long_text
    prompt: "What did you believe was true?"
  - id: evidence
    type: long_text
    prompt: "What evidence supported that belief?"
  - id: alternatives
    type: long_text
    prompt: "What alternative hypotheses were plausible?"
  - id: decision_quality
    type: enum
    options: [good_ev, mixed_ev, poor_ev, unclear]
  - id: outcome
    type: enum
    options: [won, lost, neutral]
emits:
  evidence_facets:
    - hidden_state_inference
    - action_selection_ev
    - calibration
  possible_error_types:
    - estimation_error
    - selection_error
    - coordination_error
```

Completed observations are stored in SQLite and may also render to Markdown under the subject (for example `vod-reviews/*.md`) when the domain requests a human-readable log.

---

# 15.6. Rubric-Based Grading

Free-text answers (definitions, explanations, derivations, transfer) are graded by the `rubric-grader` role using a 0-4 rubric. The grader returns structured evidence, not a free-text verdict.

## Grader routing

Not every attempt needs an LLM call. LearnLoop routes attempts through a tiered grader pipeline; the LLM grader is reserved for free-text where it is actually needed. Route by `practice_mode` and item structure:

| Tier | Grader | Modes |
| --- | --- | --- |
| 1. Exact-match | Local | `cloze` with single canonical fill, `recognition`, `multiple_choice`, `dictation`, `cued_recall` with explicit short canonical answer |
| 2. Rubric-template | Local | `short_answer` with structured `expected_answer` (e.g. enumerable key-terms), `vocabulary`, `formula` items with a normalized canonical form |
| 3. Embedding-similarity | Local | `short_answer` factual items where the rubric has no enumerable criteria; flag below `similarity_threshold` as `pending_review` for tier-4 escalation |
| 4. LLM rubric-grader | Codex | `explain_from_memory`, `teach_back`, `derivation_reconstruction`, `proof_reconstruction`, `transfer`, `near_transfer`, `far_transfer`, `error_diagnosis`, `misconception_repair`, `contrastive_discrimination`, free-text `short_answer` with no normalizable answer, any item flagged `high_stakes_canonical_item` |

Tiers 1–3 are local-only, deterministic, sub-100ms, and **work in degraded offline mode**. Tier 4 requires Codex; offline it routes to self-grade.

### Tier 3 termination rules (asymmetric)

Tier 3 is an **asymmetric local grader**. It can terminate as incorrect more easily than it can terminate as correct, because embedding similarity is a stronger signal for "this isn't the right answer" than for "this is the right answer."

```text
sim = cosine_similarity(normalize(learner_answer), normalize(expected_answer))

if sim < tier_3_low_threshold:                   # default 0.55
    return incorrect (terminal)
elif sim > tier_3_high_threshold:                # default 0.85
    if PI.tier_3_terminal_positive or domain.tier_3_terminal_positive_default:
        if not item_blocks_terminal_positive(PI):
            return correct (terminal)
    escalate to tier 4 with prior_correct signal
else:
    escalate to tier 4 (no prior)
```

**Items where terminal-positive Tier 3 is blocked by default** (the LLM grader must see them):

- `practice_mode in {proof_reconstruction, derivation_reconstruction, transfer, near_transfer, far_transfer, contrastive_discrimination, misconception_repair, error_diagnosis, disguised_retest}`
- `PI.grading_rubric.fatal_errors` is non-empty (the rubric encodes traps that embedding similarity can't detect)
- `PI.provenance.high_stakes_canonical_item == true`

`item_blocks_terminal_positive(PI)` enforces this list. The PI YAML can override with `tier_3_terminal_positive: true` *and* `tier_3_terminal_positive_force: true` (both required for explicit override), which `learnloop doctor` warns about so the override is visible.

The tier-4 prompt receives `prior_correct = true` when escalation came from the high-similarity branch. The LLM grader is instructed: "Tier 3 found high similarity (sim={sim}). Confirm correctness or identify a specific issue the embedding similarity missed." This biases the LLM toward affirming when no specific issue is found, while keeping it free to flag subtle errors.

Config in `[grading]`:

```toml
tier_3_low_threshold = 0.55
tier_3_high_threshold = 0.85
tier_3_terminal_positive_default = false
tier_3_terminal_positive_blocked_modes = [
  "proof_reconstruction", "derivation_reconstruction",
  "transfer", "near_transfer", "far_transfer",
  "contrastive_discrimination", "misconception_repair",
  "error_diagnosis", "disguised_retest",
]
```

### Grader confidence — reliability of the judgment, not the learner's correctness

A core distinction: **`grader_confidence` measures how reliably the grader decided, not how much credit the answer earned.** A confident 1/4 is a clear, reliable "mostly wrong"; a low-confidence 4/4 is a "looks right but I'm not sure I caught everything." These two cases want very different downstream behavior — the first updates mastery, the second triggers manual review.

Confidence is smoothed but capped, per tier:

```python
def grader_confidence(tier, signal):
    if tier == 1:                       # exact-match
        return 1.00

    if tier == 2:                       # rubric-template
        # the rubric IS the source of truth; partial credit doesn't lower reliability.
        # Only ambiguous matches (synonyms outside normalized terms, fall-through cases)
        # lower confidence.
        if signal.match_kind == "clean":
            return 0.95
        if signal.match_kind == "fuzzy_terms":   # had to do lemma/synonym fallback
            return 0.85
        return 0.70                              # rubric couldn't decide cleanly; usually escalates

    if tier == 3:
        # Embedding similarity is a noisier signal than rubric matching.
        # Confidence grows as similarity moves further from the gray zone.
        sim = signal.similarity
        if signal.outcome == "incorrect_terminal":           # sim < low_threshold
            # 0.70 at threshold, 0.90 at sim = 0
            return 0.70 + 0.20 * (1 - sim / tier_3_low_threshold)
        if signal.outcome == "correct_terminal":             # sim > high_threshold
            # 0.65 at threshold, 0.80 at sim = 1.0
            return 0.65 + 0.15 * (sim - tier_3_high_threshold) / (1 - tier_3_high_threshold)
        return None                                          # escalated; tier 4 reports its own

    if tier == 4:                       # LLM rubric-grader
        return signal.model_reported_confidence              # 0.0 to 1.0
```

`grader_confidence_floor` (default 0.60) still triggers manual review per existing policy. Under this regime, tier-2 partial matches usually clear the floor (confidence stays high), while ambiguous tier-2 fall-throughs and middle-range tier-3 escalations either route to tier 4 or land in manual review depending on whether Codex is available. Score and confidence are stored separately on `practice_attempts` and on `grading_evidence` so analyses can ask "how reliable were our grades?" independent of "how did the learner do?"

### Mid-attempt fallback when Codex fails (tier 4)

When a tier-4 grading call fails (Codex unavailable, rate-limited, network down, etc.) **after the learner submitted their answer**, the attempt cannot just be discarded. The adapter routes per `[ai].mid_attempt_fallback`:

- **`prompt_with_default`** (default, see §12): an inline prompt appears for `mid_attempt_prompt_timeout_seconds` (default 5):
  ```text
  Codex unavailable (rate limited)
  Self-grade this attempt?  [Y]es   [N]o, defer
  ⏱ 4s … → default Y
  ```
  - **Y** → opens a 0–4 rubric prompt; the resulting score is stored with `grader_tier = 0` (self-grade), `grader_confidence = 1.0` (the human is the grader), and `manual_review = 0`. Mastery update fires.
  - **N** → attempt is deferred. The row is written with `correctness = null`, `manual_review = 1`, and `manual_review_reason = 'codex_unavailable'`. Mastery is **not** updated yet. On Codex recovery, the auto-regrade task picks it up (see §12).
  - **Timeout** → default `Y` self-grade prompt opens.
- **`silent_self_grade`** — skip the prompt, go straight to the self-grade rubric. Used by learners who don't want interruptions. The corner status indicator turns yellow so they can see the grader changed.
- **`block_and_queue`** — write the attempt deferred immediately (same as `N` above), surface a brief notice, move on to the next queue item.

Deferred attempts surface in the pending-reviews counter and triage screen (§10), and are re-graded automatically when Codex recovers. If the learner has already started another session by then, the regrade still applies; if the deferred attempt's content has been edited (PI prompt or expected_answer changed), the regrade is held for explicit user review instead of auto-applying.

Tier-2 rubric templates are domain-shipped (e.g. `rubrics/short_answer.yaml`) and operate on normalized text:

```yaml
# rubrics/short_answer.yaml (fragment)
normalize:
  - lowercase
  - strip_punctuation
  - collapse_whitespace
  - latex_canonicalize
match:
  type: key_terms_subset      # also: exact | regex | numeric_with_tolerance
  required_terms_from: expected_answer.key_terms
  fatal_omissions_from: expected_answer.must_mention
```

The Practice Item's `expected_answer` can be a string (tier 3/4) or a structured block (tier 2):

```yaml
expected_answer:
  key_terms: [modified risk set, cumulative incidence, competing risks]
  must_mention: [competing risks]
  forbidden: [same as cause-specific]
```

When a Practice Item declares both a structured expected_answer and an inline grading_rubric, the inline rubric wins for tier 4. The structured expected_answer is used by tiers 2–3 and as evidence in the tier-4 prompt.

## Grading evidence and provenance

Every grade — local or LLM — produces a `grading_evidence` row with `agent_run_id` (LLM) or `local_grader_id` (local) and `grader_tier` (1–4). Local graders are versioned alongside `algorithm_version`; their version is recorded so replay can re-grade if needed.

## Pipeline

```text
Learner answer
   ↓
Tier router (mode + item shape → tier 1/2/3/4)
   ↓
Tier 1–3 local OR Tier 4 LLM rubric-grader
   ↓
Validation (grade in 0-4, criterion ids match rubric, fatal-error caps respected)
   ↓
Mastery update (Layer 2 EMA; skipped until confirmation if manual review is triggered)
   ↓
Surprise logging + feedback + scheduling (FSRS rating + next-action mode)
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
| `short_answer`, `retrieval`, `cloze` for `knowledge_type=definition` | Key terms present; precision; no misconception |
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

## Scheduler golden tests

Because scheduling controls what the learner sees next, queue generation must also be regression-tested locally. Each scheduler golden fixture defines a small vault state and expected top-N queue with explanation components.

```yaml
id: scheduler_surprise_followup_001
domain: math_stats_ml
given:
  active_goal: fine_gray_research_understanding
  attempts_fixture: attempts.yaml
  content_fixture: content/
  config_overrides:
    scheduler.elicitation_policy: greedy_eig
expected:
  top_queue:
    - practice_item_id: pi_fg_hazard_probability_contrast_001
      selected_mode: contrastive_discrimination
      must_include_reasons:
        - negative_surprise
        - active_goal_importance
    - practice_item_id: pi_fg_subhazard_define_001
      selected_mode: retrieval
  forbidden:
    - practice_item_id: pi_unrelated_linear_algebra_001
```

`learnloop eval scheduler` rebuilds the queue from the fixture, compares top-N item ids, selected modes, and required explanation components, and exits non-zero on drift. It should run without Codex/model calls.

## Policy and predictive evaluation harness

The Edison research notes add a stronger evaluation requirement than "golden tests only." LearnLoop should treat scheduler and elicitation changes as policy changes that need offline evidence before they become default behavior. The harness has four layers:

1. **Simulated learners** (`learnloop eval simulate`) run synthetic learner profiles through canonical sessions. Scenarios define initial LO mastery, learner θ family strengths, error propensities, calibration, latency noise, and learning-rate assumptions. Reports include mean effort, final mastery, repair-loop completion, surprise rate, and cognitive-load proxies such as hints and expected seconds.
2. **Replay / held-out response prediction** (`learnloop eval replay`) splits real attempt logs into observed history and held-out future attempts. A candidate scheduler model must predict held-out score buckets, error types, confidence, latency, and hints better than the current baseline before it can raise `algorithm_version`.
3. **Counterfactual policy comparison** (`learnloop eval policy`) runs alternative queue policies against the same fixture state: FSRS-only, greedy EIG, probe-EIG, simulator-EIG-enabled, and later MCTS. Because adaptive data creates selection bias, counterfactual reports must label estimates as approximate unless the underlying session logged randomized exploration or comparable candidate scores.
4. **Scheduler goldens** (`learnloop eval scheduler`) remain the deterministic regression layer. They catch accidental drift; they do not prove a policy is better.

The harness is local-only and must run without Codex by default. Simulated learners may use fixed RNG seeds, but scenarios should include controlled noise so the scheduler cannot overfit to a single synthetic trace. As real attempts accumulate, replay and held-out prediction become the gate for changing surrogate coefficients, EIG weights, and MCTS defaults.

## Attempt-type handling

- `independent_attempt` — graded normally; full mastery update.
- `hinted_attempt` — graded; mastery update dampened proportional to hints used; FSRS rating capped at `good`.
- `dont_know` — logged as `attempt_type=dont_know`, `error_type=recall_failure`, score = 0, next action = `walkthrough` → reconstruction next session. No grading role invoked.
- `guided_walkthrough` — not graded as independent mastery; mastery update suppressed; schedules `reconstruction_after_walkthrough`.
- `reconstruction_after_walkthrough` — graded normally; this is where mastery updates resume.
- `skip` — no update beyond a small priority penalty next time.
- `self_report` — learner self-grade; only updates the `calibration` axis.

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

If `[learning].disguised_retest_after_resolution = true`, resolved misconceptions surface occasionally as disguised retests — calibration evidence that the repair held.

### Disguised retest policy

A mature vault accumulates resolved misconceptions; without a cap and growing interval the daily queue eventually fills with long-tail retests. The policy:

- **Per-session cap: 1.** At most one disguised retest can appear in any session. If multiple are eligible, the oldest-since-last-retest comes first.
- **Eligibility: active-goal scope required.** A misconception is eligible only when its contradicted LO is in scope for at least one active goal (resolved via `concept_anchors` + concept-graph closure, see §7). Misconceptions whose contradicted LO has dropped out of active goals stop surfacing — they remain resolved on disk but quiet in the queue.
- **Interval schedule:** successful disguised retests push the next one out geometrically — 14d → 30d → 60d → 120d → 365d, capped at 365d.
- **Reopening on one failure.** A failed disguised retest immediately flips the misconception back to `status: active`, resets the interval clock, and restarts the repair loop (§15.7 above). The spec deliberately does **not** require two consecutive failures: misconceptions are insidious; a single high-confidence-wrong slip on a disguised retest is itself strong evidence the repair was shallow.
- **Disguised retests sit on top of, not inside, the queue budget.** They replace one slot in the daily review block, not the deep-work or transfer block.

The schedule, cap, and reopening rule are tunable in `algorithm_priors.yaml`:

```yaml
misconception:
  disguised_retest:
    per_session_max: 1
    intervals_days: [14, 30, 60, 120, 365]
    reopen_on_failures: 1
    selection: oldest_eligible_first
    active_goal_scope_required: true
```

## Why misconceptions get their own LO

- They have their own mastery state (especially `discrimination` and `schema`) that's independent of the LO they contradict.
- They survive across subjects — "hazard is a probability" can attack `lo_fine_gray_subhazard`, `lo_cox_hazard`, and `lo_kaplan_meier`. One misconception LO, many contradicted LOs (n-to-1).
- They can carry many Practice Items dedicated to them (contrastive, repair, disguised retest).
- They're queryable and trackable from the dashboard: `learnloop misconceptions` lists active ones.

---

# 15.8. Worked examples

Worked examples are Markdown files at `subjects/<S>/worked-examples/<name>.md`. They are content (read or observed), not Practice Items. The fading sequence (§16) consumes them when generating `walkthrough` / `faded_worked_example` / `completion_problem` items.

## Frontmatter

Frontmatter declares which Learning Objects the example teaches and, optionally, the structured steps that enable deterministic fading:

```markdown
---
id: we_svd_2x2_example_001
teaches_los: [lo_svd_decomposition, lo_svd_geometric_interpretation]   # required, ≥1
subjects: [linear-algebra, ml]                                          # optional; inferred from folder
steps:                                                                  # optional; enables faded variants
  - id: setup
    content: "Let A = UΣVᵀ where A is m×n."
    fadable: false                                                      # always shown; structural setup
  - id: dimensions
    content: "U is m×r, Σ is r×r diagonal with σ₁ ≥ ... ≥ σ_r > 0, Vᵀ is r×n."
    fadable: true
  - id: geometric
    content: "Vᵀ rotates input space, Σ scales along principal axes, U rotates output space."
    fadable: true
  - id: example_2x2
    content: "For A = [[3, 0], [4, 5]]: σ₁ = ..., σ₂ = ..."
    fadable: true
provenance:
  origin: human                                                         # human | canonical_extract | ai_generated
  source_id: null
---

# SVD: a 2×2 worked example

Free-form prose, equations, commentary follow here. The steps above are an
optional structured overlay; this prose is what the learner sees in
`worked_example` mode.
```

`teaches_los: [list]` is required (≥1). The matching LO YAML must list this file in `references_worked_examples: [...]` for the two-way link. `learnloop doctor` enforces bidirectional consistency.

Files **without** `steps:` are still valid — they render as plain prose. The fading sequence can still consume them: it asks Codex to generate elided variants from the prose at fading time. With `steps:` declared, fading is deterministic: stages elide `fadable: true` steps progressively.

## Tracking views

Every reveal of a worked example writes a row in `worked_example_views`:

```sql
CREATE TABLE worked_example_views (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT,
  example_id TEXT,                   -- frontmatter id
  example_path TEXT,                 -- relative to vault root
  session_id TEXT,
  shown_at TEXT,
  context TEXT,                      -- walkthrough | faded_stage | standalone_observe | review
  attempt_id TEXT                    -- non-null when the reveal is part of a walkthrough/faded attempt
);

CREATE INDEX idx_we_views_lo_shown ON worked_example_views(learning_object_id, shown_at);
```

The scheduler picks the **oldest-shown** matching example for an LO when `worked_example` mode is selected. If no example exists for the target LO and Codex is available, the `canonical-ingestor` (or a dedicated `worked-example-author` role for ad-hoc cases) generates one and writes it to disk under standard provenance.

---

# 15.9. Media references

Domains that consume external media (VOD review, motor-skill practice, language audio/video) store references in a per-subject `media-index.yaml`. LearnLoop never copies binary media into the vault unless the user explicitly imports it; the index points at user-owned file paths.

## Format

```yaml
# subjects/overwatch-review/media-index.yaml
media:
  - id: ow_2026_05_12_kings_row
    kind: video
    path: ~/videos/ow/2026-05-12_kings_row.mp4
    size_bytes: 824100000
    fingerprint: "824100000:a1b2c3d4...:f9e8d7c6..."   # size:first_1mb_sha256:last_1mb_sha256
    full_hash: null                                    # null when over full_hash_threshold_mb
    duration_seconds: 1820
    imported_at: 2026-05-12
    tags: [kings-row, dive-comp]
```

Hashing strategy is **hybrid by size**, configurable in `learnloop.toml`:

```toml
[media]
full_hash_threshold_mb = 50      # files <= this get full SHA-256; above get fingerprint only
search_roots = []                # extra roots to scan when relocating moved files; vault_root always implicit
hashing_parallelism = 2          # background workers for initial fingerprinting on import
```

Fingerprint format: `<size_bytes>:<first_1mb_sha256>:<last_1mb_sha256>`. Cheap to compute even on multi-GB files (one seek to end, two short reads). Files at or below `full_hash_threshold_mb` also get a full SHA-256 stored in `full_hash`, used for stronger collision resistance when available.

## Relocation on missing path

When LearnLoop reads a `media` entry and the `path` doesn't resolve, the loader scans `[media].search_roots` plus the vault root (recursively, files only) for a file matching the entry's fingerprint:

1. **Full-hash match** (when both sides have one) → relocate; update `path`; log the move.
2. **Fingerprint match** with `size_bytes` agreement → relocate; doctor warns when full-hash is missing on both sides.
3. **Multiple candidates** with the same fingerprint → doctor reports an ambiguous match and asks the user to confirm.
4. **No match** → doctor reports the entry as missing; the dependent practice items / observations are suspended (not deleted) until the file is restored or the entry is edited.

Relocation never updates the file on disk; only the YAML reference. Users can ignore missing media by setting `[media].fail_on_missing = false` for read-only workflows; default is true so missing media surfaces loudly.

---

# 15.10. Observation-to-attempt mapping and end-of-session review

§15.5 introduced structured observation templates. Each template now declares whether filling it produces a formal `practice_attempts` row and how the bound LO is chosen.

## `ObservationTemplate` emission and binding

Template YAML gains:

```yaml
id: obs_overwatch_hidden_state_review
domain: esports_overwatch
title: Overwatch hidden-state VOD review
version: 2

emits_attempt: true                # if false, only observation_events is written
lo_binding:
  mode: learner_picks              # learner_picks | template_fixed
  template_fixed_lo: null          # required when mode == template_fixed
  applies_to:                      # optional predicate filtering eligible LOs
    knowledge_type: [tactical_pattern, schema, heuristic]
    subjects: [overwatch-review]
  applies_to_mode: suggest_only    # suggest_only (default) | restrict
  suggest_from:                    # sources for autocomplete suggestions (in priority order)
    - applies_to_matches
    - active_goals
    - recent_attempts
    - recent_errors
    - embedding_similarity

fields:                            # ... structured response fields as before ...

emits:                             # evidence emitted on fill
  evidence_facets: [hidden_state_inference, action_selection_ev, calibration]
  practice_mode: "esports_overwatch:belief_reconstruction"
```

### Binding modes

- **`learner_picks`** — at fill time, the TUI prompts the learner to bind the observation to a specific Learning Object. Autocomplete suggestions come from `suggest_from` (priority order). The learner can accept a suggestion, type a different LO id, or **defer binding** (the observation is saved as a `pending_binding` event and surfaces in the end-of-session review).
- **`template_fixed`** — the template names exactly one LO (`template_fixed_lo`). The fill flow doesn't ask; the attempt is bound automatically. Used for narrow domain workflows where the observation is always about the same skill.

### `applies_to` modes

- **`suggest_only`** (default) — `applies_to` filters which LOs surface as suggestions, but the learner can override with any LO id. Useful when the template is broadly applicable but has a typical scope.
- **`restrict`** — only LOs matching `applies_to` are accepted. Override is blocked at fill time; the learner has to extend the predicate or use a different template. Used for narrow domain workflows where mis-binding would corrupt evidence.

Observations without `emits_attempt` write to `observation_events` only and never bind to an LO. They surface in the end-of-session review for optional promotion to an attempt (with prompted rubric and LO binding).

## Schema additions

```sql
ALTER TABLE observation_events ADD COLUMN bound_to_lo_id TEXT;
ALTER TABLE observation_events ADD COLUMN bound_at TEXT;
ALTER TABLE observation_events ADD COLUMN binding_mode TEXT;    -- learner_picks | template_fixed | pending | promoted_later
```

A `pending` binding means the observation was filled but the learner deferred LO selection; it appears in end-of-session review.

## Unified end-of-session review

The TUI has one **end-of-session review** surface that combines what were previously separate flows. Sections are grouped and skippable:

```text
┌──────────────────────────────────────────────────────────────────┐
│ End-of-Session Review                                            │
├──────────────────────────────────────────────────────────────────┤
│ Ephemeral promotions             (4 items)         [Open] [Skip] │
│   Suggested: promote 2, skip 1, revise 1                          │
│                                                                   │
│ Pending grade reviews            (2 items)         [Open] [Skip] │
│   Low grader confidence + 1 deferred (codex unavailable)          │
│                                                                   │
│ Observation promotions/binding   (3 items)         [Open] [Skip] │
│   2 awaiting LO binding, 1 candidate for attempt promotion        │
│                                                                   │
│ Generated-content cleanup        (5 items)         [Open] [Skip] │
│   Recently auto-accepted variants in this session; review/        │
│   deactivate/rollback                                             │
├──────────────────────────────────────────────────────────────────┤
│ [Run All] [Done]                                                 │
└──────────────────────────────────────────────────────────────────┘
```

Each `[Open]` enters the section-specific triage screen (ephemeral promotion sweep §15.5, review-grades triage §10, observation binding triage, recently-added review §10). Items remain pending if skipped; the review surface re-appears at next session end if anything is still pending.

`[Run All]` is a fast-path for low-friction sessions: applies the auto-suggested actions for each section in order (promote/skip based on each section's recommendation), then exits.

The review surface is also reachable mid-session via `learnloop review` (no arguments), useful when a session is paused or the learner wants to clear backlog before starting fresh.

---

# 16. Scheduler design

The scheduler is **five layers** stacked (Layer 0 is the learner-level latent profile; Layers 1–4 are the per-item / per-LO / per-concept / elicitation layers from the original design). **Always store raw attempts forever** so the mastery and uncertainty models are replaceable without re-collecting data.

FSRS answers "when is this concrete Practice Item due?" The object/concept mastery model answers "what does the learner appear to know about this LO?" The learner profile answers "what does the learner tend to be strong or weak at, across LOs?" The uncertainty-aware elicitation layer answers "which next question would most reduce uncertainty about the learner's likely future answers on active goals?"

The authoritative belief representation is deliberately **three-tier**, with a derived predictive-response layer on top:

```
raw attempts + observations         (immutable; persisted forever)
        ↓
per-LO scalar mastery + uncertainty (single primitive belief per LO — Layer 2)
        ↓
per-learner θ over evidence families × domain  (Layer 0)
        ↓
derived axis views                  (memory / understanding / execution /
                                     generalization / calibration —
                                     UI and scheduler explanation only)
        ↓
predictive response distributions   (P(score, error, confidence, latency, hints | state, item);
                                     derived at scheduling/evaluation time, not stored as truth)
```

The five labels `memory`, `understanding`, `execution`, `generalization`, `calibration` survive as **derived interpretable views** over evidence — not as primitive latent parameters. Calibration is a learner-level trait, not a per-LO view. This design is informed by Wang et al., "Adaptive Elicitation of Latent Information Using Natural Language" (2025), which argues against committing to a fixed cognitive basis as the latent, and by the POMDP / knowledge-tracing literature summarized in `edison_research.md`, which argues that tutoring systems still need structured mastery beliefs for remediation and explanation. LearnLoop's compromise is hybrid: structured beliefs are the source of truth, while the predictive layer estimates uncertainty over future responses for scheduling and evaluation.

## Layer 0 — Latent learner profile (per-learner θ over evidence families)

LearnLoop maintains a per-vault **learner profile** `θ` — a set of latent ability parameters in logit units, one per evidence family per domain. Positive `θ[domain, family]` means the learner tends to perform above the population baseline on items in that domain that load on that evidence family; negative means below. The profile is **not** mastery — it is the learner-level fixed effect that, combined with per-LO scalar mastery, predicts performance.

Empirically: a strong-math-background learner who has never seen Fine-Gray hazards has `θ[math_stats_ml, schema] ≈ +0.8` but `mastery[lo_fine_gray] ≈ prior`. The profile shortens the probe phase for that LO and seeds higher initial mastery; it does not assert mastery on it.

### Canonical evidence families

Eight families ship in MVP. Domain modules may register additional namespaced families (e.g. `language:pronunciation_accuracy`, `esports_overwatch:hidden_state_inference`) that must map onto one of the eight core axis labels for view aggregation (Layer 2).

| Family                  | What an attempt observes                                | Default axis aggregation       |
| ----------------------- | ------------------------------------------------------- | ------------------------------ |
| `recall`                | Cued or free retrieval correctness                      | memory                         |
| `recognition`           | Recognition / forced-choice correctness                 | memory                         |
| `schema`                | Conceptual organization, prerequisite relations         | understanding                  |
| `explanation`           | Verbal articulation, teach-back coherence               | understanding                  |
| `procedure`             | Algorithmic / derivational step correctness             | execution                      |
| `fluency`               | Speed and smoothness given correctness                  | execution                      |
| `discrimination`        | Distinguishing confusable items / contrastive items     | understanding, generalization  |
| `transfer`              | Application in novel context                            | generalization                 |
| `calibration_accuracy`* | Confidence-accuracy correlation                         | (learner-level only)           |

\* `calibration_accuracy` is a **learner-level** family. It is stored in `learner_theta` keyed on `(domain, 'calibration_accuracy', practice_mode)`, not per-LO. It updates from the joint observation of confidence and correctness on every attempt regardless of declared `evidence_facets`; it does not contribute to `mastery_axis_views`.

### Storage

```sql
CREATE TABLE learner_theta (
  id                   TEXT PRIMARY KEY,
  domain               TEXT,         -- domain_id from [domains].enabled, or 'global'
  evidence_family      TEXT,         -- canonical family id (see table above) or
                                     -- namespaced like 'language:pronunciation_accuracy'
  practice_mode        TEXT,         -- nullable; non-null only for calibration_accuracy
  theta_mean           REAL,         -- logit units (centered: 0 = population median)
  theta_variance       REAL,
  evidence_count       INTEGER,      -- number of attempts contributing
  prior_pseudo_count   REAL,         -- weight from learner_claims, separate from evidence_count
  algorithm_version    TEXT,
  updated_at           TEXT,
  UNIQUE(domain, evidence_family, practice_mode)
);

CREATE TABLE learner_claims (
  id                   TEXT PRIMARY KEY,
  claim_type           TEXT,         -- background_familiarity | prior_coursework | self_rating
  scope_type           TEXT,         -- concept | learning_object | subject | domain | global
  scope_id             TEXT,         -- nullable for global claims
  evidence_family      TEXT,         -- nullable; null means "all families in scope"
  claimed_level        REAL,         -- 0..1 self-rating
  prior_pseudo_count   REAL,         -- how much weight (in attempts-equivalent) this claim carries
  source               TEXT,         -- init_wizard | manual_cli | imported
  created_at           TEXT
);
```

`learner_theta` is **derived** — recomputable from `practice_attempts` (raw) + `learner_claims` (raw priors). It must be rebuilt on `learnloop replay-model`. `learner_claims` is raw input and is preserved across replays.

### Update rule

For each completed attempt with observed `correctness` against a Practice Item declaring `evidence_facets: [f1, f2, ...]`, the profile updates one θ slot per declared family under an approximate Gaussian working prior:

```python
def update_profile(theta_mean, theta_var, observed_logit, observation_noise):
    # observed_logit removes the parts of the score logit attributable to LO mastery and item
    # difficulty; the residual is attributed to the learner-level family effect.
    precision_prior  = 1.0 / theta_var
    precision_obs    = 1.0 / observation_noise
    new_var          = 1.0 / (precision_prior + precision_obs)
    new_mean         = new_var * (precision_prior * theta_mean
                                + precision_obs * observed_logit)
    return new_mean, new_var
```

`observation_noise` is larger when `grader_confidence` is low, when the attempt is `hinted_attempt`, when latency is `unknown`, or when the attempt is `independent_attempt` rather than `diagnostic_probe`. Probe-mode attempts (Layer 4) use a smaller calibrated noise so deliberate probes move θ more than steady-state practice does.

The calibration update fires on every attempt where confidence was captured, regardless of `evidence_facets`:

```python
if attempt.confidence is not None:
    update_profile_slot(
        domain=lo.domain,
        family='calibration_accuracy',
        practice_mode=pi.practice_mode,
        observation=confidence_residual(attempt.correctness, attempt.confidence),
        observation_noise=CALIBRATION_OBS_NOISE,
        grader_confidence=attempt.grader_confidence,
    )
```

### Cold-start: θ as the prior on new-LO mastery

When a Learning Object first acquires any belief row, its initial scalar mastery is seeded as:

```python
def seed_initial_mastery(lo, theta):
    base = algorithm_priors.mastery.mastery_default      # default 0.5
    # average θ across the families this LO's evidence_facets will load on,
    # weighted by the families declared on its representative Practice Items
    profile_offset = average_theta_for_lo(lo, theta)
    seeded = clip(base + LO_SEED_TRANSFER * sigmoid_logit_offset(profile_offset),
                  0.05, 0.95)
    return seeded
```

`LO_SEED_TRANSFER` is small (default 0.15) — θ moves the seed but does not replace evidence. After a few real attempts (Layer 2) the LO mastery dominates.

This replaces the previous "flat `mastery_default = 0.5` for every LO" behavior.

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

If `[scheduler].surprise_modulates_fsrs = true`, the base FSRS result is adjusted after surprise is recorded:

```python
def surprise_interval_factor(bayesian_surprise, direction):
    if direction == "negative":
        return max(0.40, 1.0 - 0.20 * bayesian_surprise)
    if direction == "positive":
        return min(1.25, 1.0 + 0.08 * bayesian_surprise)
    return 1.0
```

The raw factor is then blended toward 1.0 (no modulation) by the EIG reliability ramp (§16 Layer 4 "EIG and surprise-modulation reliability ramp"):

```python
rel = eig_reliability(lo, family=primary_family(pi))
factor = 1.0 + rel * (surprise_interval_factor(b_surprise, direction) - 1.0)
```

At low LO evidence counts the surrogate's prediction is mostly prior, so "surprise" is uninformative and the FSRS interval is left alone. As `rel` rises toward 1.0 the full surprise factor takes effect. Categorical handling (negative surprise capping an apparent `easy` rating at `good`/`hard` when the observed error type conflicts with the score) is **not** gated by `rel` — it is a discrete rule, not a magnitude. Positive surprise lengthens intervals conservatively; repeated evidence should matter more than a single unexpectedly good answer.

## Layer 2 — Learning Object mastery (scalar) + derived axis views

Per Learning Object, in `state.sqlite`, mastery is a **single scalar** with uncertainty — not a five-axis vector. The five labels survive as derived **views** over the scalar plus the learner profile (Layer 0).

### Storage

```sql
CREATE TABLE learning_object_mastery (
  learning_object_id   TEXT PRIMARY KEY,
  mastery_mean         REAL,         -- 0..1 scalar; "does the learner know this LO?"
  mastery_variance     REAL,
  evidence_count       INTEGER,
  last_evidence_at     TEXT,
  algorithm_version    TEXT,
  updated_at           TEXT
);

CREATE TABLE mastery_axis_views (
  learning_object_id   TEXT,
  axis                 TEXT,         -- memory | understanding | execution | generalization
  mean                 REAL,         -- nullable when status = 'unobserved'
  variance             REAL,         -- nullable when status = 'unobserved'
  status               TEXT,         -- unobserved | weak_evidence | estimated | reliable
  contributing_families_json TEXT,   -- which θ families fed this view, with weights and counts
  algorithm_version    TEXT,
  updated_at           TEXT,
  PRIMARY KEY (learning_object_id, axis)
);
-- calibration is NOT in this table — it lives in learner_theta keyed on
-- (domain, 'calibration_accuracy', practice_mode) and surfaces as a learner-level
-- metric in the TUI, not a per-LO axis.
```

### Update rule (Tier 2 — LO scalar)

```python
def update_lo_mastery(prev_mean, prev_variance, score, item_difficulty,
                     grader_confidence, hints_used, hint_policy, cold_start_factor,
                     base_alpha=0.2):
    # difficulty-aware: hard success raises more, easy failure lowers more
    if score >= 0.65:
        gain = score * (0.5 + item_difficulty)
    else:
        gain = score - (1 - item_difficulty) * 0.3
    eff_alpha = (base_alpha
                 * grader_confidence
                 * hint_policy.mastery_alpha_dampening_by_hint[hints_used]
                 * cold_start_factor)
    new_mean = clip(prev_mean + eff_alpha * (gain - prev_mean), 0.0, 1.0)
    new_variance = shrink_variance(prev_variance, eff_alpha)
    return new_mean, new_variance
```

Grades below `grader_confidence_floor` are held for manual review and do not update mastery until confirmed.

### Update rule (Tier 0 — per-learner θ over evidence families)

A single attempt updates **one θ slot per declared evidence family** on the Practice Item, plus a `calibration_accuracy` slot if `confidence` was captured. The update equations are in §16 "Layer 0 — Latent learner profile."

**Critical invariant:** the same single attempt cannot inflate evidence by updating "five axes." It updates the LO scalar once, plus as many θ family slots as the PI declared (typically 1–3). Cross-family correlation comes out in the aggregation step (Tier 3), not by double-counting at update time. This replaces the prior `sum(mastery_weights.values()) == 1` invariant and the additive `error_impacts` cross-axis deltas; both are no longer needed because evidence isn't being split across a fixed basis.

`mastery_weights` on a Practice Item now means **evidence-family weights** — `evidence_weights: {recall: 0.6, schema: 0.4}` — and is no longer required to sum to 1. The storage layer normalizes on read. PIs authored against the old axis-keyed `mastery_weights` (e.g. `{memory: 0.45, understanding: 0.55}`) are migrated at vault load: each axis key is replaced by the family with the highest aggregation weight to that axis, and the result is renormalized. `learnloop doctor` reports migrated PIs so the author can refine.

### Mode → evidence-family default map

When a Practice Item omits `evidence_facets` and `evidence_weights`, fall back to:

| `practice_mode`                                       | Default evidence families             |
| ----------------------------------------------------- | ------------------------------------- |
| `retrieval`, `cloze`, `cued_recall`, `free_recall`    | recall                                |
| `recognition`, `multiple_choice`                      | recognition                           |
| `short_answer`                                        | recall, schema                        |
| `worked_example`, `annotated_example`                 | schema, procedure                     |
| `faded_worked_example`                                | procedure, schema                     |
| `completion_problem`                                  | procedure, schema                     |
| `procedure_execution`                                 | procedure                             |
| `interleaving`, `contrastive_discrimination`          | discrimination, schema                |
| `transfer`, `near_transfer`, `far_transfer`           | transfer, schema                      |
| `transfer_probe`                                      | transfer                              |
| `explain_from_memory`, `teach_back`                   | explanation, schema, recall           |
| `derivation_reconstruction`, `proof_reconstruction`   | schema, procedure                     |
| `timed_drill`, `fluency_drill`                        | fluency, procedure                    |
| `error_diagnosis`, `misconception_repair`             | schema, transfer, discrimination      |
| `self_assessment`                                     | calibration_accuracy                  |
| `disguised_retest`                                    | (inherits from underlying mode)       |

The old "Core axes" column is gone — axes are derived, not declared.

### Axis-view aggregation (Tier 3)

After the LO mastery and θ updates commit, `mastery_axis_views` is rebuilt for the affected LO. Aggregation weights live in `algorithm_priors.yaml` and are tunable per domain:

```yaml
# additions to algorithm_priors.yaml
axis_views:
  memory:
    families:
      recall:      0.50
      recognition: 0.20
    use_fsrs_retrievability: true        # blend FSRS state into the view
    fsrs_weight: 0.30
    status_thresholds:
      unobserved_when_evidence_count_below: 1
      weak_evidence_when_below: 3
      reliable_when_above: 8
  understanding:
    families:
      schema:        0.35
      explanation:   0.25
      discrimination: 0.20
    misconception_load_weight: -0.20      # active misconception load reduces the view
    status_thresholds:
      unobserved_when_evidence_count_below: 1
      weak_evidence_when_below: 4
      reliable_when_above: 10
  execution:
    families:
      procedure: 0.60
      fluency:   0.40
    requires_execution_evidence: true     # if no procedure/fluency evidence exists, status = unobserved
    status_thresholds:
      unobserved_when_evidence_count_below: 1
      weak_evidence_when_below: 3
      reliable_when_above: 8
  generalization:
    families:
      transfer:       0.65
      discrimination: 0.35
    status_thresholds:
      unobserved_when_evidence_count_below: 1
      weak_evidence_when_below: 3
      reliable_when_above: 8
```

Aggregation, schematically:

```python
def rebuild_axis_view(lo, axis):
    spec = config.axis_views[axis]
    contributions = []
    for family, weight in spec.families.items():
        theta = learner_theta.get(lo.domain, family)
        lo_family_count = attempt_count_on_lo_for_family(lo, family)
        if theta is None or theta.evidence_count == 0 or lo_family_count == 0:
            continue
        contributions.append((family, weight, theta.mean, theta.variance, lo_family_count))

    if not contributions:
        return AxisView(axis=axis, mean=None, variance=None, status='unobserved',
                        contributing_families=[])

    lo_specific_evidence = sum(c[4] for c in contributions)
    status = classify_status(lo_specific_evidence, spec.status_thresholds)

    weighted_mean = sigmoid(sum(w * t for _, w, t, _, _ in contributions))
    weighted_var  = sum(w**2 * v for _, w, _, v, _ in contributions)

    # Blend LO scalar mastery into the view so a strong LO mastery isn't masked by a weak θ.
    lo_mastery = learning_object_mastery[lo].mastery_mean
    weighted_mean = blend(weighted_mean, lo_mastery,
                          weight=spec.get('lo_mastery_blend', 0.5))

    if spec.get('use_fsrs_retrievability'):
        weighted_mean = blend(weighted_mean, fsrs_retrievability(lo),
                              weight=spec['fsrs_weight'])
    if spec.get('misconception_load_weight'):
        weighted_mean += spec['misconception_load_weight'] * misconception_load(lo)

    return AxisView(axis=axis, mean=clip(weighted_mean, 0, 1),
                    variance=weighted_var, status=status,
                    contributing_families=contributions)
```

The four LO-level axis views all carry `status`. Calibration is **not** in this table — it surfaces as a learner-level number per `(domain, practice_mode)` read directly from `learner_theta`.

### Status lifecycle

The `status` field on `mastery_axis_views` resolves a real bug in the prior design: a fresh LO with no transfer items shouldn't look like it has weak generalization. Status transitions are evidence-driven (per-axis thresholds tunable in `algorithm_priors.yaml.axis_views.<axis>.status_thresholds`):

- `unobserved` — no contributing-family attempts on this LO yet.
- `weak_evidence` — at least one contributing-family attempt, but below the per-axis `weak_evidence_when_below` threshold.
- `estimated` — between `weak_evidence_when_below` and `reliable_when_above`.
- `reliable` — at or above the upper threshold.

Schedulers consume status, not just mean. The scheduler's mode-selection rule (later in §16) distinguishes exploration from remediation by reading `status`:

| Memory   | Generalization                  | Schedule                                    |
| -------- | ------------------------------- | ------------------------------------------- |
| strong   | `unobserved`                    | low-stakes `transfer_probe` (exploration)   |
| strong   | low-mean, `weak_evidence`/`estimated` | `transfer` (remediation)              |
| strong   | high-mean, `reliable`           | normal review                               |

The probe-vs-remediation distinction was implicit in the old design and is now a first-class representation in the storage layer.

### Error-aware updates (family-keyed)

An error can damage families the item didn't explicitly target. The taxonomy file owns the impact map — now keyed on **evidence families and (optionally) the LO scalar**, not on the five axes:

```yaml
# errors/error-taxonomy.yaml
error_impacts:
  recall_failure:
    families: { recall: -0.25 }
    lo_mastery_delta: -0.05
  conceptual_error:
    families: { schema: -0.25, explanation: -0.10 }
    lo_mastery_delta: -0.10
  theorem_selection_error:
    families: { schema: -0.30, discrimination: -0.20 }
    lo_mastery_delta: -0.10
  procedure_error:
    families: { procedure: -0.25 }
    lo_mastery_delta: -0.10
  transfer_failure:
    families: { transfer: -0.30, schema: -0.10 }
    lo_mastery_delta: -0.05
  high_confidence_wrong:                  # misconception flag
    families: { schema: -0.20, calibration_accuracy: -0.30 }
    lo_mastery_delta: -0.15
    # also: open repair_loop, append to errors/global-error-log.md
  fluency_issue:
    families: { fluency: -0.25 }
    lo_mastery_delta: 0.0
```

`flag_high_confidence_wrong` triggers when `confidence >= 4` and `score < 0.30`: the item is treated as a misconception, not a recall miss. A repair-loop is scheduled (contrastive examples, then retest) and the error is logged. The `calibration_accuracy` impact applies to the learner-level θ slot keyed on `(lo.domain, 'calibration_accuracy', pi.practice_mode)`, not to a per-LO axis.

Family-keyed deltas apply to `learner_theta` (in logit-space units, with the same `algorithm_priors.cross_lo_propagation` magnitude scaling applied as a separate sign-preserving conversion). `lo_mastery_delta` applies directly to the LO scalar.

### Cross-LO propagation along the prerequisite DAG

An attempt is logged against one Practice Item → one Learning Object, but evidence about that LO is also evidence about its prerequisites. LearnLoop propagates updates along the global concept-graph prerequisite DAG with a **bounded transitive policy**: bounded depth, geometric decay per hop, **error-type-gated** behavior, and a total-weight cap.

In the three-tier model, propagation targets the **prereq's LO scalar mastery** — not its axis views. Axis views on prereqs are recomputed from scratch after the LO scalar update. The learner-level θ profile is updated **once per attempt** at the source (Layer 0) and is not separately propagated along prereq edges (the profile is per-learner, not per-LO, so propagation along the DAG would double-count).

**Asymmetric success vs failure.**

- **Success** (`correctness ≥ 0.65`): variance-only update on prereqs' LO scalar (uncertainty shrinks, means do not move). A correct PCA attempt is weak positive evidence about SVD mastery — enough to tighten the belief, not enough to raise its mean.
- **Failure** (`correctness < 0.50`): mean *and* variance update on prereqs' LO scalar, with magnitude scaled by depth decay, score severity (`1 − correctness`), `grader_confidence`, hint dampening, and the error-type gate (below).
- **Borderline** (`0.50 ≤ correctness < 0.65`): variance-only update; no mean propagation.

**Error-type gate.** Different error types tell us different things about upstream LOs. Failures route through a per-error gate that selects scope and magnitude. Defaults (overridable in `algorithm_priors.yaml` and per-domain):

```yaml
cross_lo_propagation:
  default:
    max_depth: 3
    hop_decay: 0.5
    total_propagated_weight_cap: 0.7   # sum |Δmean| across propagation set; scaled down if exceeded
  error_gates:
    recall_failure:
      mean_factor: 0.0                 # forgetting a definition is not evidence prereqs are weak
      variance_factor: 0.25
      scope: all
    conceptual_error:
      mean_factor: 0.5
      variance_factor: 0.7
      scope: all
    theorem_selection_error:
      mean_factor: 0.4
      variance_factor: 0.6
      scope: conceptual_only
    assumption_error:
      mean_factor: 0.4
      variance_factor: 0.6
      scope: conceptual_only
    procedure_error:
      mean_factor: 0.5
      variance_factor: 0.7
      scope: procedural_only
    notation_error:
      mean_factor: 0.1
      variance_factor: 0.3
      scope: all
    fluency_issue:
      mean_factor: 0.2
      variance_factor: 0.3
      scope: procedural_only
    transfer_failure:
      mean_factor: 0.3
      variance_factor: 0.5
      scope: conceptual_only
    high_confidence_wrong:
      mean_factor: 0.7
      variance_factor: 0.8
      scope: all
      trigger_misconception_repair: true
```

`scope` filters prereqs by the upstream LO's `knowledge_type`:

- `conceptual_only` → `concept`, `definition`, `theorem`, `lemma`, `model`, `schema`, `assumption`, `distinction`
- `procedural_only` → `procedure`, `algorithm`, `derivation`, `worked_example_pattern`, `proof_technique`
- `all` → no filter

**Propagation formula.** For each prereq `lo_p` at hop distance `d ∈ {1, …, max_depth}` whose `knowledge_type` is in scope:

```python
depth_weight = hop_decay ** d
severity     = 1.0 - correctness                  # 0 if perfect, 1 if zero
gate         = error_gates[error_type]            # or default on null

raw_mean_delta = (
    -1.0
    * gate.mean_factor
    * depth_weight
    * severity
    * grader_confidence
    * hint_dampening[hints_used]
)

raw_variance_delta = (
    gate.variance_factor
    * depth_weight
    * 0.02                                        # absolute units; variance grows
)
```

Compute these raw deltas for every prereq in scope (one delta pair per prereq — there is no per-axis split, since LO mastery is scalar). Sum `|raw_mean_delta|` across the whole propagation set; if the total exceeds `total_propagated_weight_cap`, scale all mean deltas (and proportionally the variance deltas) down by `cap / total`. Then apply each delta directly to `learning_object_mastery[lo_p].mastery_mean` and `mastery_variance`.

After propagation, every prereq LO's `mastery_axis_views` rows are marked dirty and recomputed lazily on next read (or eagerly in the same transaction if the prereq is in the active queue).

**Successful attempts** skip the mean-delta computation and only apply `raw_variance_delta` with the *negative* sign (variance shrinks). The total-weight cap applies the same way.

**Overrides.**

- Domains can override the entire `cross_lo_propagation` block in their module's config.
- Individual LOs can declare:
  ```yaml
  cross_lo_propagation_override:
    receives_propagation_from: [lo_id, ...]   # explicit allowlist, optional
    block_propagation_from: [lo_id, ...]      # explicit denylist
    max_depth_in: 2                            # tighter than the global default
  ```
  Useful when a prereq edge exists for ordering but failures downstream shouldn't update upstream beliefs (e.g. a foundational LO the learner has demonstrably mastered through many other paths).

Propagation is computed *after* the direct LO's EMA update, *before* the surprise calculation (so surprise's posterior reflects the full update). Every propagated update writes a row in `attempt_propagation_events` so the path is auditable and replayable.

```sql
CREATE TABLE attempt_propagation_events (
  id TEXT PRIMARY KEY,
  attempt_id TEXT,
  source_lo_id TEXT,
  target_lo_id TEXT,
  hop_distance INTEGER,
  error_type TEXT,
  mean_delta REAL,                    -- applied to target LO's mastery_mean
  variance_delta REAL,                -- applied to target LO's mastery_variance
  applied REAL,                       -- 1.0, or <1.0 if scaled by total-weight cap
  algorithm_version TEXT,
  created_at TEXT
);
-- The `axis` column from the prior schema is removed: propagation acts on the
-- target LO's scalar mastery, not on per-axis estimates. Axis views are
-- recomputed downstream from the updated scalar.
```

### Fluency signal

Not just from `timed_drill`. Compute fluency from: `latency_vs_expected`, `hints_used`, `pause_count` (if available from the input widget), and consistency across recent attempts on the same item.

## Layer 3 — Concept mastery (aggregate)

Per Concept: prerequisite-weighted average of its Learning Objects' mastery. Used for the concept-graph view, weakness detection, and prerequisite-aware scheduling — not directly updated by attempts.

## Layer 4 — Adaptive elicitation and Bayesian surprise

Adaptive elicitation influences **every daily queue**, not only cold-start or diagnostic sessions. The goal is to improve the latent single-user learner profile while still respecting due reviews, readiness, repair loops, and active goals.

The default target set is **active goals of learning and understanding** from `goals.yaml` (with `profile/goals.md` as the narrative companion), expanded through the concept graph into relevant Learning Objects, prerequisites, confusable concepts, unresolved error types, and active misconception LOs. The scheduler should not spend daily queue budget reducing uncertainty about dormant or irrelevant concepts unless the user asks for a diagnostic sweep.

### Two policy variants

LearnLoop uses two distinct elicitation policies, applied at different points in the loop:

1. **Heuristic-bucket EIG (the workhorse, MVP).** A local, deterministic, model-free scorer used on every queue generation. It computes expected information gain from a parametric predictive distribution over future response buckets. This is **not** a faithful implementation of the predictive-LM elicitation literature (e.g. Wang et al., "Adaptive Elicitation of Latent Information Using Natural Language", 2025); it is a structured tutoring surrogate inspired by that framing and by classical POMDP / knowledge-tracing work. It is tuned to LearnLoop's hybrid state: FSRS item memory, per-LO scalar mastery, learner θ over evidence families, error-type propensities, misconception LOs, calibration, latency, and hint behavior. It runs sub-second, works offline, is reproducible under scheduler and policy goldens, and never calls the model.

2. **Codex-simulator EIG, narrow path (MVP, gated).** When heuristic EIG plateaus on existing Practice Items for a high-priority belief — i.e. no current PI is informative enough about a specific active-goal uncertainty — LearnLoop asks Codex to propose 1–3 **ephemeral diagnostic items** designed to discriminate plausible learner states. The model is used as a question proposer informed by learner profile, recent attempts, and the target belief, not as a full predictive simulator over a large candidate pool. Generated items follow the ephemeral-items policy (§15.5) and are not promoted unless the learner says so. Requires Codex; disabled in degraded offline mode.

The heuristic policy generates every queue; the simulator policy adds a handful of ephemeral diagnostics per session when (and only when) heuristic information gain is saturated on existing items.

Greedy one-step EIG is the default because daily queue generation has tight latency and because many review items are substitutable. The spec does **not** assume greedy is always optimal. Greedy remains the default while held-out prediction and policy fixtures show approximately diminishing returns from additional questions; lookahead is reserved for rare misconceptions, strong sequential dependencies, and low-immediate-yield probes that unlock more informative follow-ups.

### Later: full predictive-LM elicitation

A full predictive-LM elicitation pass — sample plausible learner answers to candidate questions, score by predicted-observation entropy reduction — is a **later** addition behind an explicit "deep diagnostic pass" command, with a hard latency and API-call budget. It is not in MVP because (a) LearnLoop already has a strongly parametric latent that heuristic EIG can exploit, (b) per-queue simulator calls don't fit the TUI-first latency target, (c) it breaks scheduler golden test determinism, and (d) it requires Codex for every queue generation, breaking the degraded offline contract.

### MCTS/lookahead promotion criteria

MCTS/lookahead remains a later policy after enough local attempts exist (`mcts_min_attempts`) and after the predictive surrogate is calibrated on held-out response prediction. It should not become an automatic daily scheduler path merely because it scores higher under its own simulator.

Enable MCTS only when all of these are true:

- `learnloop eval replay` shows calibrated prediction on held-out score/error/confidence buckets for the target domain.
- `learnloop eval policy` shows a material gain over greedy EIG on rare or sequential diagnostic fixtures.
- The candidate target is an active-goal LO, misconception, or error family where greedy EIG has plateaued.
- The latency budget allows planning without making the TUI feel blocked.

MCTS rollout reward is composite:

```text
reward =
  information_gain_bits
  + prediction_accuracy_gain_on_heldout_proxy
  + repair_loop_completion_bonus
  - cognitive_load_penalty
  - latency_penalty
```

For pure diagnostic commands, set the non-information terms to zero. For the daily loop, the load and latency penalties prevent the planner from choosing a technically informative but exhausting sequence. Bayesian surprise is the realized per-step analogue of the information-gain term and is valid as a rollout reward only when the prior predictive distribution is calibrated.

### Dual score representation

Two representations of the same observation coexist:

- **Continuous raw score** `correctness ∈ [0, 1]` derived from the 0–4 rubric grade (or local-grader output) via `GRADE_TO_SCORE`. This is persisted on `practice_attempts.correctness` and is the input to all **mastery EMA updates**, analytics, replay, and future algorithm iterations. Raw scores are never lossy.
- **5-way score bucket** `score_bucket ∈ {again, hard, good, easy}` derived from `correctness`. This is the canonical event alphabet for **EIG scoring, predictive surprise, scheduler explanations, and elicitation goldens**. Buckets make the predictive distribution discrete, the EIG integral a finite sum, and golden tests deterministic.

For each candidate Practice Item `q`, LearnLoop estimates a predictive distribution over the joint *bucketed* observation:

```text
o = (
  score_bucket,      # again / hard / good / easy
  error_type,        # taxonomy id or null
  confidence_bucket, # low / medium / high
  latency_bucket,    # fast / normal / slow / unknown
  hints_bucket       # none / low / high
)
```

Default deterministic buckets:

| Field | Buckets |
| --- | --- |
| `score_bucket` | `again` < 0.30, `hard` < 0.65, `good` < 0.90, `easy` otherwise |
| `confidence_bucket` | `low` = 1-2, `medium` = 3, `high` = 4-5 |
| `latency_bucket` | `fast` <= 0.5x expected, `normal` <= 1.5x, `slow` > 1.5x, `unknown` if no expected time |
| `hints_bucket` | `none` = 0, `low` = 1, `high` >= 2 |

`latency_bucket = unknown` when neither the Practice Item declares `expected_seconds` nor the LO has a `calibrated_mean_seconds`. In that case latency contributes nothing to EIG or predictive surprise for that attempt; it is still logged on `practice_attempts.latency_seconds` for analytics and for future calibration.

Procedural and proof modes may also emit `step_trace_json`: ordered subgoal / invariant / buggy-rule markers from the rubric or local step checker. Step traces are raw evidence and can drive error tagging, procedure-family θ updates, and later predictive-evaluation analysis. They are **not** part of the MVP EIG enumeration because they would explode the observation space; the MVP folds them into `error_type`, `rubric_score`, and `evidence_facets`.

The local single-user belief state `z` includes Learning Object mastery means/variances, selected learner-θ family means/variances, **per-learner error-type propensities** (a Dirichlet-like distribution over the error taxonomy, shrunk to a global prior), misconception states, and calibration.

### Surrogate functional form

The heuristic surrogate factorizes the joint predictive as:

```text
P(o | z, q) =  P(score_bucket   | z, q)
            ·  P(error_type     | score_bucket, z, q)
            ·  P(confidence     | score_bucket, z, q)
            ·  P(latency_bucket | score_bucket, z, q)
            ·  P(hints_bucket   | score_bucket, z, q)
```

**Score head.** A cumulative logistic over a learner-item logit, decomposed into per-LO scalar mastery, per-learner θ over the PI's declared evidence families, and item difficulty:

```python
def score_logit(z, q, lo):
    # Per-LO scalar mastery (Layer 2).
    lo_term = z.lo_mastery[lo.id].mean - 0.5

    # Per-learner θ over the families this item exercises (Layer 0).
    theta_term = 0.0
    total_weight = 0.0
    for family in q.evidence_facets:
        w = q.evidence_weights.get(family, 1.0 / len(q.evidence_facets))
        theta = z.learner_theta[lo.domain, family]
        theta_term += w * theta.mean
        total_weight += w
    if total_weight > 0:
        theta_term /= total_weight

    return (
        BETA_LO * lo_term
        + BETA_THETA * theta_term
        - BETA_DIFFICULTY * (q.difficulty - 0.5)
        - BETA_MISCONCEPTION * z.active_misconception_load(lo.id)
    )

# bucket probabilities from cumulative logistic with thresholds tuned to match
# the 0.30 / 0.65 / 0.90 score-bucket cutpoints
```

The five-axis terms from the prior surrogate are gone. The model predicts score from (does this learner know this LO?) × (does this learner have ability in the families this item exercises?) × (how hard is the item?). The four LO-level axis views play **no role** in the surrogate — they are display layers, not belief primitives. Default β values: `BETA_LO = 4.0`, `BETA_THETA = 1.5`, `BETA_DIFFICULTY = 3.0`, `BETA_MISCONCEPTION = 2.0`.

**Error-type head.** Conditional on `score_bucket ∈ {again, hard}`, the surrogate samples an error type from the **per-learner propensity** `z.error_propensity[e]` masked to the error types that are physically plausible for the Practice Item's `practice_mode` and `knowledge_type` (e.g. `notation_error` only on items with notation). The per-learner propensity uses Dirichlet–multinomial shrinkage toward a global prior:

```python
def posterior_propensity(observed_counts, global_prior, prior_pseudo_count):
    total = sum(observed_counts.values())
    return {
        e: (prior_pseudo_count * global_prior[e] + observed_counts[e])
           / (prior_pseudo_count + total)
        for e in error_taxonomy
    }
```

**Confidence head.** Confidence tracks score weighted by the learner's calibration θ: `z.learner_theta[lo.domain, 'calibration_accuracy', q.practice_mode].mean`. A well-calibrated learner has `confidence_bucket` strongly correlated with `score_bucket`; a poorly-calibrated learner regresses to their baseline confidence distribution. Calibration is per-(domain, mode), not per-LO — overconfidence on proofs can coexist with good calibration on vocab.

**Latency head.** Shifted log-normal centered on `expected_seconds` (or `lo.calibrated_mean_seconds`), with width modulated by the learner's procedure/fluency θ for the LO's domain (more execution-family ability = tighter distribution). Returns `unknown` if no calibrated mean exists.

**Hints head.** Probability of asking for hint N depends on the learner's calibration and procedure/fluency θ, plus `q.difficulty`. Learners who feel uncertain ask for hints more.

Parameters (`BETA_*`, bucket thresholds, latency widths, calibration slopes) are shipped in `algorithm_priors.yaml` and refined from this learner's own attempts after `prior_pseudo_count` real observations on the relevant scope.

### EIG scoring

Heuristic expected information gain (the MVP scoring function):

```text
EIG(q) = E_o [ KL( P(z | o, q) || P(z) ) ]
       = H(z) - E_o[H(z | o, q)]
```

Both `P(o | z, q)` and the posterior update `P(z | o, q)` are computed from the surrogate, not from a language model. The expectation `E_o` ranges over the discrete joint buckets defined above (≤ 4 × |error_taxonomy_for_mode| × 3 × 4 × 3 — small enough to enumerate). `H(z)` is computed only over the belief slots scoped to active goals — specifically: the LO scalar mastery for active-goal LOs plus the learner θ slots for evidence families that load on those LOs. Axis views are **not** entered into the entropy calculation (they're derived, not primitive), avoiding the double-counting risk of the prior axis-tensor formulation.

MVP scores each candidate question independently and picks high-value items inside the normal queue (greedy). The scorer must be deterministic, reproducible, and runnable without Codex.

Codex-simulator EIG (ephemeral diagnostic generation) does not score the existing PI pool; it proposes new items targeted at the highest-variance belief on a high-priority active-goal LO. The proposer prompt receives: the LO and its current belief means/variances (LO scalar + the θ family slots that load on it), the recent attempt history for that LO, and a short list of named hypotheses to discriminate. The hypotheses are generated **locally** from the heuristic surrogate's top modes of the posterior (e.g. `{id: "memorized_no_schema", description: "Recalls but can't apply", predicted_profile: {recall: 0.85, schema: 0.35, transfer: 0.30}}`); Codex is only the question proposer, not the hypothesis generator. Hypotheses are expressed in evidence-family space, not axis space.

### Proposer output schema and validation

The simulator-EIG proposer returns an **ephemeral-minimal** structure — just enough to ask a question, grade it, and decide whether it is safe to use as an adaptive diagnostic. Rubric, hint ladder, and full provenance are defaulted or omitted; full PI structure is built only if the learner later promotes the item. Edison research on automatic question generation adds one extra requirement: even ephemeral items need a rough difficulty/cognitive-level estimate and quality claims so the scheduler does not treat arbitrary generated text as calibrated evidence.

```python
class SimulatorProposerOutput(BaseModel):
    items: list[SimulatorProposedItem]   # 1 to 3 items

class SimulatorProposedItem(BaseModel):
    prompt: str
    expected_answer: str
    target_lo_id: str                    # must be a real LO
    target_evidence_families: list[str]  # ≥1; from the canonical family list (Layer 0)
    practice_mode: str                   # one of the LO's eligible PracticeMode values
    estimated_difficulty: float | None   # 0..1 rough prior; required before promotion to permanent PI
    cognitive_level: str | None          # recall | understand | apply | analyze | evaluate | create
    source_refs: list[str] = []          # source ids or note refs when factual grounding is required
    discriminates_hypotheses: list[str]  # ≥2; ids from the active HypothesisSet provided in the prompt
    predicted_observations_by_hypothesis: dict[str, PredictedObservation]
                                         # one entry per id in discriminates_hypotheses;
                                         # see §16.5 PredictedObservation (score_bucket + likely_error_type)
    rationale: str                       # one-sentence explanation of why this item separates the hypotheses
    quality_claims: list[str]            # must include lo_aligned, clear_prompt, answerable,
                                         # and psychometrically_plausible
```

**Validation:**

1. Schema validates (Pydantic).
2. `target_lo_id` resolves to an active LO whose `subjects` overlap the current session's subject scope.
3. `practice_mode` is in the eligible set for that LO (from `PracticeModeSpec` + LO's `subjects`).
4. `discriminates_hypotheses` references **at least two hypotheses** from the active `HypothesisSet` provided in the prompt (the one identified by `hypothesis_set_id` on the call). A single hypothesis reference is rejected — the proposer must distinguish at least one pair.
5. `predicted_observations_by_hypothesis` contains exactly the keys in `discriminates_hypotheses` and no extras. Each entry is a valid `PredictedObservation` (§16.5).
6. **Non-overlapping predictions:** for at least one pair `(h_i, h_j)` in `discriminates_hypotheses`, the predicted observations differ in `score_bucket` OR `likely_error_type`. Items where every referenced hypothesis predicts the same observation are rejected (they don't actually discriminate).
7. **Hypothesis-set integrity:** every id in `discriminates_hypotheses` is present in the active `HypothesisSet`. The proposer is forbidden from inventing hypothesis ids — local code owns the hypothesis ontology.
8. **Near-duplicate guard:** for each proposed item, embed `prompt` and check cosine similarity against existing PIs on `target_lo_id`. Reject items with `sim ≥ 0.85` (caller may just be suggesting a copy of an existing item).
9. `estimated_difficulty`, when provided, is in `[0, 1]`; if omitted, LearnLoop assigns the LO's current difficulty prior and marks the item `difficulty_source = inherited_prior`.
10. `cognitive_level`, when provided, is compatible with `practice_mode` and the LO's `knowledge_type`. For example, `recognition` cannot claim `analyze`, and `far_transfer` cannot claim `recall`.
11. `quality_claims` must include `lo_aligned`, `clear_prompt`, `answerable`, and `psychometrically_plausible`; generated MCQs must also include `plausible_distractors`.
12. `source_refs` are required for canonical-source and research-paper domains. The validator checks that each ref resolves to a known note, source chunk, or Learning Object reference.
13. Count is in `[1, simulator_ephemerals_per_session_max]` (default 3).
14. For probe-phase fallback specifically: the proposed items must collectively cover all `top_ambiguous_hypothesis_pairs` passed in the prompt (each pair appears in at least one item's `discriminates_hypotheses`).

**Retry policy.** If validation fails, retry once with a constraint-patch in the prompt (same pattern as hint-author):

```text
Your previous attempt was rejected. Issues:
- Item 2 had similarity 0.91 to an existing Practice Item on this LO.
- Item 3's practice_mode "transfer" is not in the eligible set; allowed: [short_answer, contrastive_discrimination, explain_from_memory].
- Item 1 referenced only one hypothesis (H_2); needs at least two with non-overlapping predicted observations.
Please regenerate with these constraints.
```

A second failure means the scheduler proceeds **without** simulator-EIG ephemerals for this session — `probe_eig` over the existing PI pool still picks the best available item (logged with `fallback_outcome = existing_pi_inadequate`). The failure is logged on `agent_runs` so the learner can inspect via `learnloop ai history`.

Validated items become ephemeral PIs (§15.5) bound to the session. They follow the existing ephemeral lifecycle: usable immediately, surface in the end-of-session promotion sweep with rationale derived from `discriminates_hypotheses` and `rationale`, not persisted to the permanent pool unless the learner promotes.

After an attempt, LearnLoop records surprise:

```text
predictive_surprise = -log P(observed score, error_type, confidence, latency, hints | prior state, q)
bayesian_surprise   = KL( posterior learner-state belief || prior learner-state belief )
```

Predictive surprise means "the observed answer was unlikely." Bayesian surprise means "the learner model changed." They are related but not interchangeable. Because LearnLoop classifies error types, a low score caused by `recall_failure` and the same low score caused by `conceptual_error` can produce different posterior updates, different repair actions, and different FSRS modulation.

Bayesian surprise affects both scheduling and diagnosis:

- **Negative surprise**: the learner performs much worse than expected, shows an unexpected error type, uses many hints, or has high confidence while wrong. FSRS intervals are shortened or rating is capped, the related LO/error belief uncertainty increases, and a diagnostic or repair follow-up can be inserted (see "Surprise follow-up insertion" below).
- **Positive surprise**: the learner performs much better than expected with low hints and calibrated confidence. Mastery uncertainty shrinks and the FSRS interval may be modestly lengthened, but not beyond conservative bounds until repeated evidence confirms it. **No follow-up item is inserted on positive surprise** — the existing modest FSRS stretch is the only response. Lengthening intervals slowly on positive evidence is the conservative default; a future "stretch challenge" feature can be opt-in.
- **High surprise with low grader confidence**: store the evidence, skip automatic mastery/FSRS modulation, and ask for manual review.

The FSRS update remains grounded in the observed score. Surprise only modulates the resulting interval within configured bounds so one unusual answer cannot wildly distort long-term scheduling.

### Surprise follow-up insertion (negative surprise only)

When `bayesian_surprise > surprise_diagnostic_threshold` with `surprise_direction = negative`, the next queue position **may be** overridden — gated by `eig_reliability(lo, family)` (see "EIG and surprise-modulation reliability ramp" later in §16 Layer 4). Insertion is not an unconditional event; it is a Bernoulli draw at rate `rel`. At low evidence counts the surrogate's prediction is mostly prior, so "surprise" relative to that prior is uninformative — the follow-up is suppressed and the suppression is logged. Categorical events (`high_confidence_wrong` → misconception_repair, `error_events` logging) fire **independently** of this gate.

When the gate passes, the follow-up is inserted — **not** by interrupting the current item or feedback flow, but by inserting at position 1 of the remaining queue. The current attempt's feedback screen surfaces this transparently:

```text
┌────────────────────────────────────────────┐
│ Feedback (truncated)                       │
│ ...                                        │
│ ⚠ Surprise: high (negative)                │
│ Added follow-up to the next position:      │
│   Mode: error_diagnosis                    │
│   Reason: theorem_selection_error in a     │
│           context where memory was strong  │
│                                            │
│ [Continue]                  [Skip follow-up]│
└────────────────────────────────────────────┘
```

The follow-up's mode is chosen by the existing `choose_next_action` logic (§16 mode selection) using the surprise signal as input, typically yielding `error_diagnosis`, `misconception_repair`, or `contrastive_discrimination`. `[Skip follow-up]` removes this one follow-up only and is not interpreted as "I disagree with the surprise signal"; it doesn't lower future follow-up sensitivity.

Skipping is logged on `attempt_surprise.triggered_actions_json` as `{"follow_up_skipped": true}` so analyses can see how often inserted follow-ups are dismissed. Reliability-suppressed follow-ups (the Bernoulli gate failed) are logged separately as `attempt_surprise.suppressed_actions_json = {"low_reliability_suppressed": rel}`; they are *not* counted as skips, since the learner never saw a banner to dismiss. If user-skip rate climbs above a threshold over a window of attempts where reliability was high, `learnloop doctor` flags it: the surprise threshold may be miscalibrated for this learner. Reliability-suppression rate is reported separately and is expected to be nonzero in the first sessions on each LO.

### Probe mode and probe-EIG — per-LO diagnostic phase

Every Learning Object passes through a short **probe phase** before entering steady-state scheduling. The phase is per-LO, not per-vault: an LO is in probe mode independently of whether other LOs have been probed. Probe attempts serve three purposes:

1. Generate calibration evidence on this learner's θ profile (Layer 0) so the surrogate's score head is informative from the first attempts on a new LO.
2. Establish initial values for the LO's scalar mastery (Layer 2) and `mastery_axis_views.status` (Layer 3) so the scheduler can stop treating "no evidence yet" as "weak ability."
3. Discriminate between a small set of **coarse diagnostic hypotheses** about the learner's state on this LO — picking items whose predicted-observation distribution splits posterior mass between hypotheses.

The third purpose is what probe-EIG optimizes. Hypotheses are coarse alternatives like `unknown`, `surface_form_only`, `confuses_with_neighbor`, `robust_initial_grasp` — they are not claims about the learner's true latent type; they are useful enumerations for choosing informative first encounters.

#### Probe hypothesis templates

During just-in-time probe selection, LearnLoop uses small authored hypothesis templates keyed by `(domain, knowledge_type, practice_mode)`. These templates are not claims about the learner's true latent type. They are coarse diagnostic alternatives used to choose informative first encounters with a new LO.

At scheduling time, templates are instantiated against the specific LO using its prerequisites, confusable concepts, difficulty prior, current learner θ profile, and active-goal context. The instantiated hypotheses are logged in the scheduler explanation and `elicitation_events.hypothesis_set_json` for replay and debugging, but are not stored as authoritative learner state.

MVP does not generate custom per-LO hypotheses. Later versions may materialize `lo_probe_hypotheses` from posterior modes after enough evidence exists, but the MVP keeps probe selection deterministic and offline-compatible.

Template location:

- **Core templates** ship at `prompts/probe_hypothesis_templates.yaml` for shared `(general, knowledge_type, practice_mode)` defaults. Any domain can inherit them.
- **Domain templates** are registered by `DomainModule.probe_hypothesis_templates()` (§4) and **shadow** core entries on the same `(knowledge_type, practice_mode)` key.

Example core template entry:

```yaml
# prompts/probe_hypothesis_templates.yaml (excerpt)
- knowledge_type: definition
  practice_mode: short_answer
  domain_id: general
  template_version: "1.0.0"
  hypotheses:
    - id: unknown
      label: "Doesn't know"
      description: "No prior exposure to the concept; recall fails outright."
      predicted_observation: { score_bucket: again, likely_error_type: recall_failure }
      family_loading: { recall: 0.9, schema: 0.1 }
    - id: surface_form_only
      label: "Surface form only"
      description: "Recognizes the name but cannot articulate the function or structure."
      predicted_observation: { score_bucket: hard, likely_error_type: missing_condition }
      family_loading: { recall: 0.6, schema: 0.4 }
    - id: confuses_with_neighbor
      label: "Confuses with neighbor"
      description: "Confidently produces the wrong concept from a confusable set."
      predicted_observation: { score_bucket: hard, likely_error_type: conceptual_error }
      family_loading: { schema: 0.7, discrimination: 0.3 }
      confusable_concept_anchors_required: true
    - id: robust_initial_grasp
      label: "Robust initial grasp"
      description: "Articulates the concept correctly on first try."
      predicted_observation: { score_bucket: good, likely_error_type: null }
      family_loading: { recall: 0.4, schema: 0.6 }
```

#### Hypothesis instantiation

When an LO transitions to `in_progress`, its hypothesis set `H` is instantiated once and cached for the duration of the probe phase. Re-probes after misconception reopen (§15.7) create a **new** `probe_phase_id` and a new instantiation:

```python
def instantiate_hypothesis_set(lo, learner_theta, active_goals, algorithm_version) -> HypothesisSet:
    # Resolve templates: domain templates shadow core templates on (knowledge_type, practice_mode).
    representative_modes = lo.eligible_practice_modes_for_probe()
    templates = []
    for mode in representative_modes:
        resolved = resolve_templates(lo.knowledge_type, mode, lo.domain)
        templates.extend(resolved)

    hypotheses = []
    for tmpl in templates:
        if tmpl.confusable_concept_anchors_required and not lo.confusables:
            continue                # skip "confuses_with_neighbor" when LO has no confusables
        hypothesis = Hypothesis(
            id=f"{tmpl.id}__{lo.id}",
            template_id=tmpl.id,
            template_version=tmpl.template_version,
            lo_id=lo.id,
            label=specialize_label(tmpl.label, lo),
            description=specialize_description(tmpl.description, lo),
            predicted_observation=tmpl.predicted_observation,
            family_loading=tmpl.family_loading,
            instantiation_inputs_hash=hash_instantiation_inputs(lo, learner_theta, active_goals),
        )
        hypotheses.append(hypothesis)

    # Cap to the configured count range.
    hypotheses = select_top_k(hypotheses,
                              min_k=algorithm_priors.probe_eig.hypothesis_count_min,
                              max_k=algorithm_priors.probe_eig.hypothesis_count_max,
                              by="prior_mass_under_theta")
    return HypothesisSet(
        id=compute_hypothesis_set_id(algorithm_version, lo.id, lo.probe_state.probe_phase_id,
                                     {h.template_id: h.template_version for h in hypotheses},
                                     compute_theta_snapshot_hash(lo, learner_theta),
                                     trigger="probe_phase_routine"),
        lo_id=lo.id,
        probe_phase_id=lo.probe_state.probe_phase_id,
        algorithm_version=algorithm_version,
        template_versions={h.template_id: h.template_version for h in hypotheses},
        theta_snapshot_hash=compute_theta_snapshot_hash(lo, learner_theta),
        hypotheses=hypotheses,
        created_at=now_utc(),
        trigger="probe_phase_routine",
    )
```

`prior_mass_under_theta` weights hypotheses by `marginal_hypothesis_prior` (`uniform` or `weighted_by_surrogate_modes`) when more templates apply than `hypothesis_count_max`. The default is `uniform` — surrogate weighting at the start of a probe is mostly prior anyway.

#### Per-LO probe state

```sql
CREATE TABLE lo_probe_state (
  learning_object_id        TEXT PRIMARY KEY,
  status                    TEXT,    -- pending | in_progress | complete | skipped_by_claim
  probe_phase_id            TEXT,    -- new UUID on each transition into `in_progress`;
                                     -- distinguishes first probe from post-misconception re-probe
  hypothesis_set_id         TEXT,    -- the active HypothesisSet for this probe_phase_id
  probe_attempts_completed  INTEGER,
  probe_attempts_target     INTEGER, -- defaults from algorithm_priors; can shrink via learner_claims
  families_converged        TEXT,    -- JSON array of evidence_family ids whose θ variance dropped below threshold
  entered_at                TEXT,    -- when the LO first became eligible for the queue
  completed_at              TEXT,
  algorithm_version         TEXT
);
```

Status lifecycle:

- `pending` — LO exists but is not yet schedulable (prereqs unsatisfied or not in any active-goal scope).
- `in_progress` — LO has entered the active queue. The next `probe_attempts_target` attempts on this LO will run with `attempt_type = diagnostic_probe`.
- `complete` — probe budget exhausted **or** every declared evidence family for the LO has at least one converged θ slot **or** the LO scalar variance fell below threshold. Whichever fires first.
- `skipped_by_claim` — a `learner_claims` row asserted strong prior familiarity for this LO's concept above the configured skip threshold; mastery is seeded and steady-state begins immediately. Reversed automatically if any subsequent attempt scores below `claim_skip_revert_threshold`.

#### Default probe budget (in `algorithm_priors.yaml`)

```yaml
probe_mode:
  attempts_target_default: 3            # how many probe attempts per LO before completion
  attempts_target_with_strong_claim: 1  # if learner claimed familiarity, just one verification probe
  variance_convergence_threshold: 0.10  # complete early if every targeted family θ variance drops below this
  observation_noise: 0.4                # smaller noise → probe attempts move θ more than steady-state
  steady_state_observation_noise: 1.2
  claim_skip_threshold: 0.75            # claimed_level above which the LO starts in skipped_by_claim
  claim_skip_revert_threshold: 0.40     # any subsequent attempt below this reverts to in_progress
  short_session_eligible: false         # short sessions skip probe-phase work by default
  per_session_max_new_probes: 2         # how many fresh LOs may enter probe mode in one session
  per_session_max_probe_attempts: 6     # total probe attempts per session
  suppress_surprise_followups: true     # probe-mode attempts don't trigger negative-surprise queue insertion
```

#### Probe-EIG: hypothesis-based item selection

When the scheduler selects an item for an LO in `in_progress` probe mode, it overrides the normal priority formula. The selection rule maximizes **expected mutual information between hypothesis identity and the predicted observation**, using the LO's active `HypothesisSet`:

```python
def probe_eig_score(pi, lo, H: HypothesisSet, current_theta, lo_mastery):
    """Higher is better. Run over the LO's eligible Practice Items.
       Returns information gain in bits about hypothesis identity."""
    # 1. Hypothesis prior: uniform by default, or weighted by surrogate modes.
    prior_h = hypothesis_prior(H, mode=algorithm_priors.probe_eig.marginal_hypothesis_prior)

    # 2. For each hypothesis, the predicted observation distribution over this item.
    #    P(o | h, pi) blends the hypothesis's authored predicted_observation with the
    #    surrogate's score head conditioned on the hypothesis's family_loading profile.
    p_obs_given_h = {
        h.id: predicted_observation_distribution(pi, h, current_theta, lo_mastery)
        for h in H.hypotheses
    }

    # 3. Marginal observation distribution under the hypothesis prior.
    marginal_o = {
        o: sum(prior_h[h.id] * p_obs_given_h[h.id][o] for h in H.hypotheses)
        for o in joint_observation_space(pi.practice_mode)
    }

    # 4. Expected information gain in bits about hypothesis identity.
    H_prior = entropy(prior_h)                          # bits over hypothesis ids
    H_cond = sum(
        marginal_o[o] * entropy(posterior_h_given_o(prior_h, p_obs_given_h, o))
        for o in joint_observation_space(pi.practice_mode)
        if marginal_o[o] > 0
    )
    info_gain_bits = H_prior - H_cond

    # 5. Mode preference and hint penalty (same intent as the prior Fisher version).
    mode_weight = PROBE_MODE_WEIGHTS.get(pi.practice_mode, 0.5)
    hint_penalty = 0.0 if not pi.hints else 0.05      # smaller than before; mode_weight does heavier work

    return info_gain_bits * mode_weight - hint_penalty


PROBE_MODE_WEIGHTS = {
    "short_answer":         1.00,
    "cued_recall":          0.90,
    "free_recall":          0.85,
    "explain_from_memory":  0.80,
    "completion_problem":   0.70,
    "cloze":                0.60,
    "recognition":          0.40,
    "multiple_choice":      0.30,
    "worked_example":       0.10,   # consumes the test, doesn't measure
    "faded_worked_example": 0.10,
    "transfer":             0.00,   # transfer in probe mode is meaningless
    "far_transfer":         0.00,
    "transfer_probe":       0.50,   # OK during probe — it's the exploration variant
}
```

`joint_observation_space(mode)` is the finite product `score_bucket × (likely_error_type_for_mode ∪ {null})` — 4 × (|taxonomy_for_mode| + 1) outcomes, small enough to enumerate. Other observation channels (confidence, latency, hints) are *not* part of the probe-EIG enumeration; they are too noisy to discriminate coarse hypotheses cleanly. They still affect θ updates as usual.

The family-coverage bonus from the prior `probe_item_score` is retired. Coverage emerges naturally from hypothesis-based scoring: hypotheses with high posterior mass on a not-yet-observed family will be discriminated by items that load on that family, so the score naturally rewards those items.

The probe scheduler **disables hint reveals by default** for probe attempts (`hint_policy.fsrs_rating_cap_by_hint` still applies if the learner overrides via the [Hint] button, but the surprise/profile update treats it as a hinted attempt and downweights it).

#### Interaction with the standard priority score

While an LO is `in_progress`, the standard priority formula in §16 "Priority score" is **bypassed** for items on that LO. Instead:

1. The scheduler computes `forgetting_risk` and `active_goal_importance` to decide *whether* this LO appears in this session's queue at all (probes still compete for the per-session slot budget).
2. If selected, the LO's specific item is chosen by `probe_eig_score` above.
3. If no item in the existing PI pool scores above `algorithm_priors.probe_eig.min_local_score` bits, the scheduler may invoke **simulator-EIG fallback** to generate ephemeral diagnostic items targeting the same `HypothesisSet` (see "Hypothesis provider and simulator-EIG unification" below).
4. The `cognitive_overload_risk` and `readiness_factor` modulations still apply — probe mode does **not** override readiness. Low-energy sessions still suppress probes the same way they suppress transfer.

#### Per-session caps

To prevent the "all my LOs entered probe mode at once" stampede after a goal update or a bulk LO import:

- `per_session_max_new_probes` (default 2) — at most this many LOs may transition from `pending` → `in_progress` in a single session.
- `per_session_max_probe_attempts` (default 6, scaled down by `available_minutes`) — total probe attempts per session, regardless of LO count.
- Probes do **not** appear in short-session mode (§10) unless the user explicitly requests them with `learnloop today --include-probes`.

The cap is enforced after the standard queue is built: probe candidates are ranked by active-goal importance and the top-N enter the queue.

#### Transition to complete

An LO leaves probe mode when any one of:

- `probe_attempts_completed >= probe_attempts_target`, or
- `learning_object_mastery[lo].mastery_variance < variance_convergence_threshold`, or
- every family in the LO's declared `evidence_facets` set has at least one converged θ slot (i.e. `learner_theta[lo.domain, family].theta_variance < variance_convergence_threshold`).

On completion, the LO's `lo_probe_state.status` becomes `complete`, the standard priority formula resumes, and the LO is eligible for the full EIG pool.

#### Probe attempts and surprise

Probe-mode attempts still record surprise the normal way. **Negative surprise follow-ups are suppressed during probe mode** — by definition, the first 2–3 attempts on a new LO are expected to be surprising; inserting a diagnostic follow-up on every probe would defeat the point. The surprise signal still updates beliefs and θ; it just doesn't trigger the queue-insertion behavior in "Surprise follow-up insertion" above. This is logged on `attempt_surprise.suppressed_actions_json = {"probe_mode_suppressed": true}`.

### Probe-EIG vs normal-EIG dispatch

The scheduler has **two distinct EIG objectives**, used in different LO states:

| Objective    | Used when                                                      | Operates over                            |
| ------------ | -------------------------------------------------------------- | ---------------------------------------- |
| `probe_eig`  | `lo_probe_state.status == in_progress`                          | Coarse hypothesis identity (discrete)    |
| `normal_eig` | `lo_probe_state.status == complete` AND `eig_reliability ≥ τ`   | Predictive observation distribution (continuous, via surrogate) |
| `probe_eig` (fallback) | `lo_probe_state.status == complete` AND `eig_reliability < τ` | Same hypotheses as the closing probe phase, kept in cache |

The third row is the substantive design choice and a behavioral change from the prior "dampened normal_EIG" model: when reliability is low post-probe, the scheduler **falls back to probe-EIG over the remaining unresolved hypotheses** rather than computing a weak `normal_eig`. This is strictly more informative — a well-defined hypothesis-discrimination problem beats a noisy entropy-reduction estimate.

The cached hypothesis set from the closing probe phase is retained on `lo_probe_state.hypothesis_set_id` for as long as `eig_reliability < τ`. Once reliability crosses τ, the cache is cleared and `normal_eig` takes over. The threshold τ is `algorithm_priors.eig_reliability.fallback_to_probe_below` (default 0.40 — the LO-mastery sigmoid passes 0.40 at roughly attempt 4 under default ramp parameters).

```python
def select_eig_objective(lo, axis_views, probe_state):
    if probe_state.status == "in_progress":
        return ("probe_eig", probe_state.hypothesis_set_id)
    rel = eig_reliability(lo, family=primary_family_for_lo(lo))
    if rel < algorithm_priors.eig_reliability.fallback_to_probe_below:
        # Still consolidating — reuse last probe's hypothesis set.
        return ("probe_eig", probe_state.hypothesis_set_id)
    return ("normal_eig", None)
```

Status-driven, not count-driven: the dispatch reads `lo_probe_state.status` and `eig_reliability`, both of which are deterministic functions of raw evidence. The transition is reproducible on replay.

`normal_eig` is the entropy-reduction objective from "EIG scoring" earlier in §16 Layer 4 — `E_o[KL(P(z | o, q) || P(z))]` over the surrogate's predictive distribution. It is multiplied into the priority formula via `eig_reliability`, as specified in "EIG and surprise-modulation reliability ramp."

### Simulator-EIG scope

MVP simulator-EIG is restricted to **just-in-time probe fallback**. During the probe phase, LearnLoop first searches the existing Practice Item pool for an item that discriminates the active LO hypothesis set. If no item exceeds `algorithm_priors.probe_eig.min_local_score` bits, Codex may propose ephemeral diagnostic items against that same hypothesis set.

Normal-phase simulator-EIG is **not** part of the automatic daily scheduler in MVP. Mature LOs use deterministic local scheduling: FSRS, surprise, repair loops, transfer gaps, and `normal_eig` over existing items. A manual deep-diagnostic command (§11, `learnloop diagnose-lo --deep`, `learnloop generate-diagnostic`) may invoke simulator-EIG for mature LOs, but generated items remain ephemeral unless promoted by the learner.

Automatic normal-phase simulator-EIG is reserved for a later version after enough attempt history exists to evaluate whether generated diagnostics improve scheduling decisions. Config flag:

```toml
[scheduler]
simulator_eig_context = "probe_phase_only"   # probe_phase_only | probe_and_posterior_modes
```

`probe_and_posterior_modes` is documented but not the MVP default. When enabled, simulator-EIG may fire during normal-phase scheduling under restrictive triggers (LO `evidence_status` ≥ `estimated`, posterior uncertainty above threshold despite ≥5 attempts, no local item above EIG threshold, active-goal LO, not short-session mode, Codex available, per-session generated-diagnostic cap not reached).

### Hypothesis provider and simulator-EIG unification

The principle:

> **Simulator-EIG does not generate hypotheses. It generates candidate observations that distinguish a hypothesis set produced locally.**

One active uncertainty target → one `HypothesisSet` → two item sources:

```text
1. Existing PI pool:
   local probe_EIG chooses the most discriminating existing item.

2. No adequate existing PI (best probe_eig_score < min_local_score):
   simulator-EIG asks Codex to generate an ephemeral item discriminating the same hypotheses.
```

#### Dispatch

```python
def select_probe_item(lo, H: HypothesisSet, candidate_pool, codex_available):
    scored = [(probe_eig_score(pi, lo, H, theta, lo_mastery), pi) for pi in candidate_pool]
    best_score, best_pi = max(scored, default=(0.0, None))

    if best_score >= algorithm_priors.probe_eig.min_local_score:
        return ScheduledItem(pi=best_pi, source="existing_pi",
                             expected_info_gain_bits=best_score, hypothesis_set_id=H.id)

    if not codex_available or simulator_eig_disabled_for_session():
        # No adequate item, no fallback available — pick the best existing item anyway
        # and log the gap. Probe attempts are bounded; the next session may have better options.
        return ScheduledItem(pi=best_pi, source="existing_pi_inadequate",
                             expected_info_gain_bits=best_score, hypothesis_set_id=H.id)

    # Simulator-EIG fallback.
    ephemerals = call_simulator_eig_proposer(
        lo=lo,
        hypothesis_set=H,
        missing_discrimination=top_ambiguous_hypothesis_pairs(H, candidate_pool),
        constraints=eligible_practice_modes_for_lo(lo),
    )
    if not ephemerals:
        return ScheduledItem(pi=best_pi, source="existing_pi_simulator_failed",
                             expected_info_gain_bits=best_score, hypothesis_set_id=H.id)
    return ScheduledItem(pi=ephemerals[0], source="simulator_eig",
                         expected_info_gain_bits=score_ephemeral(ephemerals[0], H),
                         hypothesis_set_id=H.id)
```

`top_ambiguous_hypothesis_pairs(H, candidate_pool)` identifies the hypothesis pairs that no existing item separates well — passed to Codex as the specific discrimination target rather than a vague "diagnose this LO" instruction.

#### Simulator prompt structure

The simulator-EIG proposer prompt is built around the hypothesis set, **not** "diagnose this LO":

```text
You are proposing 1–3 ephemeral Practice Items for LO {lo.id}: {lo.title}.

Existing items cannot separate these hypotheses well:
  H_2: "surface recall but weak schema"     (predicts hard + missing_condition)
  H_3: "confuses with cause-specific hazard" (predicts hard + conceptual_error)

Generate items whose expected observation distinguishes these hypotheses.
For each proposed item, specify what you would predict to observe under each
referenced hypothesis (score_bucket + likely_error_type).

Constraints:
- practice_mode ∈ {short_answer, contrastive_discrimination, explain_from_memory}
- ≥2 referenced hypotheses with non-overlapping predicted observations
- no near-duplicate of existing PIs on this LO (cosine sim < 0.85)
- include estimated_difficulty, cognitive_level, and quality_claims
- include source_refs when the LO is tied to canonical source material
```

Hypothesis-set context (the `H` passed to the prompt) is part of `agent_runs.input_context_hash`, so replay reproduces deterministically.

#### When simulator-EIG declines

If Codex returns zero valid items after the one allowed retry (§16 "Proposer output schema and validation"), the scheduler proceeds with the best available existing item and logs the gap on `elicitation_events`:

```sql
-- additions logged to existing elicitation_events
hypothesis_set_id TEXT,            -- which HypothesisSet was active
trigger TEXT,                       -- probe_phase_local_pi_inadequate |
                                    -- probe_phase_routine |
                                    -- manual_deep_diagnostic_lo |
                                    -- manual_deep_diagnostic_goal
hypothesis_set_json TEXT,           -- full HypothesisSet serialization for replay
fallback_outcome TEXT               -- existing_pi | existing_pi_inadequate |
                                    -- simulator_eig | existing_pi_simulator_failed
```

`learnloop doctor` aggregates `existing_pi_inadequate` and `existing_pi_simulator_failed` counts over a window; persistent gaps suggest the PI pool needs human authoring or the hypothesis templates need refinement for that domain.

#### Replay determinism

`HypothesisSet` is fully derivable from raw inputs (algorithm_version, LO, probe_phase_id, learner_theta snapshot, learner_claims). Simulator-EIG calls are logged on `agent_runs` with the `HypothesisSet` as part of the input context hash, so:

- The local dispatch ("did we go to simulator-EIG?") is deterministic on replay.
- The simulator's output is **not** deterministic (Codex), but is preserved verbatim on `agent_runs` and `ephemeral_session_items`. Replay does not re-call Codex; it uses the stored output.
- This matches the existing replay invariant for AI calls (§16 "Replayable learner model"): raw events are reproduced exactly; AI outputs are read from `agent_runs`, not regenerated.

### EIG and surprise-modulation reliability ramp

Probe mode handles parameter *estimation* (how to choose items that move beliefs). This subsection handles parameter *application*: how much the surrogate's predictions should drive priority and FSRS modulation while the posterior is still consolidating. The cliff problem this resolves: when `lo_probe_state.status` flips to `complete` at attempt 3, the standard priority formula instantly applies the full `information_gain_weight = 0.15` and `error_uncertainty_weight = 0.10` — but the per-LO surrogate posterior at 3 attempts is still mostly prior, and `EIG = H(z) − E_o[H(z|o)]` with `H(z)` mostly prior is chasing noise.

The ramp is a per-attempt-target multiplier on EIG and surprise *magnitude*-driven uses. Categorical surprise events (misconception trigger, error_events logging) are explicitly **not** dampened — they are discrete classifications that should fire at any evidence count.

#### Two independent reliability factors

```python
def eig_reliability(lo, family):
    """Multiplier in [0, 1] on EIG and surprise-modulation magnitudes."""
    n_lo  = learning_object_mastery[lo.id].evidence_count
    n_th  = learner_theta[lo.domain, family].evidence_count

    f_lo  = sigmoid(SLOPE_LO    * (n_lo - HALF_LO))
    f_th  = sigmoid(SLOPE_THETA * (n_th - HALF_THETA))

    # The bottleneck wins. A new LO under mature θ is gated only by f_lo;
    # a new family with mature LO is gated only by f_th.
    return min(f_lo, f_th)
```

`f_lo` reflects how reliable the surrogate's prediction *for this LO* is. `f_th` reflects how reliable the surrogate's *family-level prediction model* is. They're independent because a learner with 40 prior schema attempts across other LOs has a tight `θ[domain, schema]` posterior even on a brand-new LO; conversely, a learner with 30 attempts on LO_42 still has wide `θ[domain, proof_reconstruction]` if proof_reconstruction is a family they've never been observed on.

Default values (in `algorithm_priors.yaml.eig_reliability`):

| Constant       | Default | Effect                                                                |
| -------------- | ------- | --------------------------------------------------------------------- |
| `HALF_LO`      | 3.5     | At 3.5 LO attempts, `f_lo = 0.5`                                       |
| `SLOPE_LO`     | 1.5     | Ramp from ~0.02 at n=0 to ~0.90 at n=5; ~0.32 at n=3, ~0.68 at n=4    |
| `HALF_THETA`   | 8.0     | θ matures more slowly than per-LO posteriors — needs cross-LO evidence |
| `SLOPE_THETA`  | 0.5     | Ramp from ~0.02 at n=0 to ~0.90 at n=12; ~0.50 at n=8                 |

Implied bands at integer attempt counts on this LO (assuming mature θ):

| LO evidence count | θ-family count | EIG/surprise-modulation weight                  |
| ----------------- | -------------- | ----------------------------------------------- |
| 0                 | any            | ~0.005 — priority is FSRS + prereq + recent errors only |
| 1–2               | any            | 0.024–0.10 — probe scoring drives selection; standard EIG inert |
| 3–4               | mature θ       | 0.32–0.68 — dampened EIG; surprise modulates intervals modestly |
| 5+                | mature θ       | 0.90+ — full priority formula                    |
| any               | < 3 family-domain attempts | dampened by θ branch regardless of LO count |

The function is a smoothed version of a 4-band step function. Tests target integer points; the sigmoid is just a smoother interpolation between them. Domain overrides in `algorithm_priors.yaml.domain_overrides` can tune `HALF_*` / `SLOPE_*` per domain (language vocab → `HALF_LO = 2`; esports VOD review → `HALF_LO = 6`).

#### What the ramp applies to (and what it does not)

The ramp multiplies **magnitude-driven** uses of EIG and surprise. Categorical events fire regardless:

```yaml
# algorithm_priors.yaml
eig_reliability:
  half_lo: 3.5
  slope_lo: 1.5
  half_theta: 8.0
  slope_theta: 0.5
  applies_to:
    - information_gain_weight       # priority-score component
    - error_uncertainty_weight       # priority-score component
    - surprise_interval_factor       # FSRS modulation magnitude
    - surprise_followup_insertion    # whether to enqueue a follow-up at all
  does_not_apply_to:
    - high_confidence_wrong          # misconception trigger fires regardless
    - error_events                   # categorical logging fires regardless
    - probe_mode                     # probe selection uses Fisher-info; its own scoring
    - forgetting_risk                # FSRS retrievability independent of LO posterior
    - active_goal_importance         # goal weighting is exogenous
    - recent_error_severity          # recent-error boost is based on raw events
    - deadline_pressure              # exogenous time signal
```

This split is the load-bearing design decision. The ramp protects the scheduler from over-trusting a noisy posterior; it does **not** protect against missing a misconception in the first 2 attempts (those are exactly the cheapest moment to catch one).

#### Application sites

In the priority formula (see "Priority score" later in §16), the EIG-derived components are multiplied by `eig_reliability`:

```python
rel = eig_reliability(lo, family=primary_family(pi))
priority_components.information_gain  *= rel
priority_components.error_uncertainty *= rel
```

In FSRS modulation:

```python
factor = surprise_interval_factor(b_surprise, direction)
# blend toward 1.0 (no modulation) when reliability is low
factor = 1.0 + rel * (factor - 1.0)
```

In surprise follow-up insertion (§16 Layer 4 "Surprise follow-up insertion"):

```python
if b_surprise > threshold and direction == "negative":
    if random_uniform() < rel:                 # equivalent to a Bernoulli gate at rate `rel`
        insert_follow_up()
    # else: surprise was recorded but no follow-up inserted; logged on
    #       attempt_surprise.suppressed_actions_json = {"low_reliability_suppressed": rel}
```

Misconception triggering and error logging happen earlier in the attempt pipeline and bypass this gate entirely.

#### Scheduler-explanation surface

The "Why now?" panel surfaces the multiplier whenever reliability < 0.95, so the learner (and developers running golden tests) can see when the ramp is active:

```text
Why this item?
  Forgetting risk        0.24
  Information gain       0.04   (×0.32 reliability — 3 attempts on LO)
  Error uncertainty      0.03   (×0.32 reliability)
  Recent error           0.12
  Transfer gap           0.15   (status: estimated)
  Readiness adjustment  +0.00
```

The `×N reliability` annotation is added next to any priority component the ramp touched. If the θ branch is the bottleneck, the annotation says so explicitly: `(×0.18 reliability — sparse θ[math_stats_ml, schema])`.

#### Replay invariant

`evidence_count` on `learning_object_mastery` and `learner_theta` is derivable from raw attempts. The reliability ramp is a pure function of those counts plus `algorithm_priors.yaml.eig_reliability`, so replay reproduces the same priority ordering deterministically. Goldens at integer attempt counts pin the function's behavior; changes to `HALF_*` / `SLOPE_*` are MINOR algorithm bumps (display-only) unless they cross a status threshold that affects mode selection, in which case they are MAJOR.

### Belief staleness

Mastery should become less certain when evidence is old. Staleness does not automatically lower mastery; it increases variance and can make a review or diagnostic question more valuable.

```python
def apply_staleness(mean, variance, days_since_evidence, stale_after_days):
    if days_since_evidence <= stale_after_days:
        return mean, variance
    age = days_since_evidence - stale_after_days
    variance = min(1.0, variance + 0.01 * age)
    return mean, variance
```

Default `stale_after_days` is configured per **θ evidence family** (the underlying belief slot) and per **axis view** (for UI staleness flags) in `algorithm_priors.yaml`. Memory-family slots (recall, recognition) stale quickly; schema and transfer slots more slowly; calibration_accuracy slowest. Esports VOD-read beliefs stale faster after patches, role changes, or long gaps in play (set via `domain_overrides.esports_overwatch.staleness`).

### Replayable learner model

`learnloop replay-model` rebuilds all derived learner-state tables by **re-running the current algorithm version** over raw attempts, observation events, and current content hashes. This is the canonical migration path when mastery, surprise, or scheduler formulas change.

**Replay semantics are fixed: drop-and-recompute with version-tagged pre-replay snapshot.**

Replay must:

1. snapshot current derived tables into `replay_snapshots` rows tagged with the **old** algorithm version (so the previous learner-state can be inspected or restored if needed),
2. clear and recompute derived learner-state tables in a single transaction using the **current** algorithm version,
3. write a `model_replay_runs` row with old → new algorithm version, snapshot id, row-change summary, and warnings,
4. emit a **replay diff view** — the top-N Learning Objects, Practice Items, and beliefs whose mastery or variance moved most, with the magnitude and direction of the change, surfaced in the TUI and via `learnloop replay-model --diff`,
5. leave raw attempts, observations, and content files untouched.

Restoring a snapshot is supported via `learnloop replay-model --restore <snapshot_id>`: it copies the snapshotted derived tables back over the live ones and writes a new `model_replay_runs` row with `status = restored`. Raw events are never touched.

The "carry old derived state forward and switch forward only" alternative is **not** supported. Algorithm changes always re-derive from raw events.

Algorithm versions follow semantic versioning. `algorithm_version` is recorded on every `learner_state_beliefs` row, `learning_object_mastery` row, `attempt_surprise` row, and `scheduler_explanations` row written, so derived rows always know which formula version produced them.

### Replay trigger and nag cadence

Replay is prompted, not silent, and not auto-run. When the code's `algorithm_version` differs from the vault's last-recorded version, the vault-open banner shows:

```text
┌────────────────────────────────────────────────────────┐
│ Algorithm updated: 1.2.0 → 1.3.0                       │
│ Replay learner state so mastery numbers match the      │
│ current model? (Recommended)                           │
│                                                         │
│ [Replay] [Later] [What changed?]                       │
└────────────────────────────────────────────────────────┘
```

- **`[Replay]`** runs `learnloop replay-model` with the diff view at the end.
- **`[Later]`** dismisses for this session; the banner returns on the next vault open.
- **`[What changed?]`** opens a structured changelog: the parameter or formula deltas between the two versions, sourced from `CHANGELOG.algorithm.md` shipped with each release.

After **3 cumulative dismissals**, the banner gains an additional nudge line: "You've dismissed this 3 times — your mastery numbers may not reflect the current algorithm. Replay is non-destructive (a snapshot is taken first)." Dismissal count persists in `state.sqlite` so it survives restarts.

**Behavior by bump type** (algorithm semver):

- **MAJOR** — replay would change mastery numbers on the same raw events. Triggered by: formula changes (mastery EMA shape, surprise definition), surrogate retuning that shifts predicted-distribution outputs, new cross-LO propagation rules, threshold changes that move bucket assignments. Banner shows with "Recommended" emphasis. `[Later]` works, but the nudge appears after the **first** dismissal, not the third.

- **MINOR** — new fields, tables, axes, facets, or features that don't alter outputs on pre-MINOR data. Triggered by: adding `pronunciation_accuracy` evidence facet (old attempts didn't have it; new ones can use it without rewriting old ones), adding a new SQLite table, adding optional fields to existing schemas. Banner shows with default-accept framing. Standard 3-dismissal nudge.

- **PATCH** — bugfix-only. The new version produces identical outputs to the old on previously-working cases and corrected outputs on previously-buggy cases. Triggered by: fixing an off-by-one in propagation depth counting, fixing a bucket-edge tie-break. **No banner.** `learnloop doctor` surfaces the version drift in its summary: `Algorithm version: 1.3.1 (vault: 1.3.0) — patch drift; replay optional, no expected mastery change`. The user can run replay manually if they want.

**Authoring discipline.** LearnLoop ships `CHANGELOG.algorithm.md` alongside the code. Every algorithm change adds a dated entry naming the version bump, the affected components, and a one-line description. The "What changed?" link in the replay banner renders entries between the vault's last-recorded version and the current code version.

**Single version, not per-component.** All derived-state pipeline components (mastery EMA, FSRS modulation, surrogate, surprise, cross-LO propagation, scheduler scoring, grader tier routing for confidence) share one `algorithm_version`. A change to any one triggers a bump per the rules above. Per-component versioning was considered and rejected: cross-component invariants (e.g. a new surrogate invalidates stored surprise even with stable mastery formula) make independent versions misleading. The single number is the truth about whether replay is needed.

**v2.0.0 — three-tier latent migration + EIG reliability ramp + hypothesis-based probe-EIG.** Three complementary changes ship together: (1) demoting the five axes from primary belief state to derived views, (2) the EIG reliability ramp on `evidence_count`, and (3) hypothesis-based `probe_eig` with simulator-EIG unified on a single `HypothesisSet`. The three changes are co-dependent: the ramp needs evidence counts introduced by the migration, and `probe_eig` operates on coarse hypotheses that load on the evidence families introduced by the migration. Shipping them as one release avoids cross-version interpretation gaps. The shipped migration:

1. Snapshots the old five-column `learning_object_mastery` rows into `replay_snapshots` tagged with the previous algorithm version.
2. Seeds the new scalar `mastery_mean` from the weighted mean of the old five axes (weights from `algorithm_priors.axis_views.<axis>.lo_mastery_blend_seed` defaults) and `mastery_variance` from the max variance across axes.
3. Seeds `learner_theta` rows from a per-attempt replay: each historical attempt's old `mastery_weights × axis_value` deltas are reattributed to the corresponding evidence family (using the prior axis→family aggregation table inverted). Families with no historical evidence start at population prior `θ.mean = 0, θ.variance = 1.0`.
4. Rebuilds `mastery_axis_views` from the new state.
5. Writes a `change_batches` row with `reason = algorithm_major_v2` linking every affected row; the migration is rollbackable for `[storage].purge_undo_window_days`.

The migration is automatic on first vault open under v2.0.0+, gated by the standard MAJOR banner ("Recommended" emphasis, 1-strike nudge). Existing vaults with low evidence counts will see their axis views snap to `unobserved` for axes that had no real evidence under the old model — this is correct behavior, not a regression.

The dismissal counter resets to 0 when replay runs or when the user explicitly accepts the new version without replay (`learnloop replay-model --accept-without-replay`, intended for cases where the user *knows* a PATCH-equivalent change is the only delta).

## SQLite tables (canonical)

```sql
CREATE TABLE practice_attempts (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT,
  learning_object_id TEXT,
  subject TEXT,                      -- the subject view the learner was in when this attempt was logged.
                                     -- For multi-subject LOs, this is the active session's subject, not
                                     -- the full LO subjects list. Cross-subject queries walk LO membership.
  concept TEXT,                      -- vault-global concept id (LO.concept)
  practice_mode TEXT,
  attempt_type TEXT,                 -- independent_attempt | hinted_attempt | dont_know | diagnostic_probe | ...
  evidence_facets TEXT,              -- JSON array of EvidenceFamily ids (the primary update channel)
  evidence_weights TEXT,              -- JSON object {family: weight}; nullable, defaults to uniform
  rubric_score INTEGER,              -- 0-4
  correctness REAL,                  -- GRADE_TO_SCORE[rubric_score]
  confidence INTEGER,                -- 1-5
  latency_seconds INTEGER,
  hints_used INTEGER,
  step_trace_json TEXT,              -- optional ordered subgoal / buggy-rule evidence for procedural modes
  error_type TEXT,                   -- nullable; from taxonomy
  grader_confidence REAL,
  manual_review INTEGER,             -- 0/1
  manual_review_reason TEXT,         -- low_grader_confidence | codex_unavailable | rubric_missing |
                                     -- user_disputed | proof_subtlety | high_stakes_canonical | null
  created_at TEXT
);

CREATE TABLE grading_evidence (
  attempt_id TEXT,
  criterion_id TEXT,
  points_awarded REAL,
  notes TEXT,
  agent_run_id TEXT,                 -- set when grader_tier = 4 (LLM); null for local tiers
  local_grader_id TEXT,              -- set when grader_tier in (1,2,3); null for LLM
  grader_tier INTEGER,               -- 1 = exact-match, 2 = rubric-template, 3 = embedding-similarity, 4 = LLM
  superseded_at TEXT,                -- set when a regrade or human override replaces this row as authoritative
  superseded_by_evidence_id TEXT,    -- pointer to the replacing row
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
  mastery_mean REAL,                  -- scalar 0..1; "does the learner know this LO?"
  mastery_variance REAL,
  evidence_count INTEGER,
  last_evidence_at TEXT,
  algorithm_version TEXT,
  updated_at TEXT
);
-- The five-column per-axis layout (memory/understanding/execution/generalization/calibration)
-- from algorithm_version <2.0.0 is migrated to this scalar form on first vault open under
-- v2.0.0+; per-axis values move to the derived `mastery_axis_views` table.

CREATE TABLE mastery_axis_views (
  learning_object_id TEXT,
  axis TEXT,                          -- memory | understanding | execution | generalization
  mean REAL,                          -- nullable when status = 'unobserved'
  variance REAL,                      -- nullable when status = 'unobserved'
  status TEXT,                        -- unobserved | weak_evidence | estimated | reliable
  contributing_families_json TEXT,    -- which θ families fed this view, weights and counts
  algorithm_version TEXT,
  updated_at TEXT,
  PRIMARY KEY (learning_object_id, axis)
);
-- Derived cache; recomputable from learning_object_mastery + learner_theta + raw attempts.
-- Calibration is NOT in this table — it lives in learner_theta keyed on
-- (domain, 'calibration_accuracy', practice_mode).

CREATE TABLE learner_theta (
  id TEXT PRIMARY KEY,
  domain TEXT,                        -- domain_id from [domains].enabled, or 'global'
  evidence_family TEXT,               -- canonical family id (see §16 Layer 0) or
                                      -- namespaced like 'language:pronunciation_accuracy'
  practice_mode TEXT,                 -- nullable; non-null only for calibration_accuracy
  theta_mean REAL,                    -- logit units (centered: 0 = population median)
  theta_variance REAL,
  evidence_count INTEGER,
  prior_pseudo_count REAL,            -- weight from learner_claims; separate from evidence_count
  algorithm_version TEXT,
  updated_at TEXT,
  UNIQUE(domain, evidence_family, practice_mode)
);

CREATE TABLE learner_claims (
  id TEXT PRIMARY KEY,
  claim_type TEXT,                    -- background_familiarity | prior_coursework | self_rating
  scope_type TEXT,                    -- concept | learning_object | subject | domain | global
  scope_id TEXT,                      -- nullable for global claims
  evidence_family TEXT,               -- nullable; null means "all families in scope"
  claimed_level REAL,                 -- 0..1 self-rating
  prior_pseudo_count REAL,            -- attempts-equivalent weight this claim carries
  source TEXT,                        -- init_wizard | manual_cli | imported
  created_at TEXT
);
-- Raw input table — preserved across replays.

CREATE TABLE lo_probe_state (
  learning_object_id TEXT PRIMARY KEY,
  status TEXT,                        -- pending | in_progress | complete | skipped_by_claim
  probe_phase_id TEXT,                -- new UUID on each transition into `in_progress`;
                                      -- distinguishes first probe from post-misconception re-probe
  hypothesis_set_id TEXT,             -- active HypothesisSet for this probe_phase_id;
                                      -- also cached post-probe while eig_reliability < fallback_to_probe_below
  probe_attempts_completed INTEGER,
  probe_attempts_target INTEGER,
  families_converged TEXT,            -- JSON array of evidence_family ids
  entered_at TEXT,
  completed_at TEXT,
  algorithm_version TEXT
);

CREATE TABLE concept_mastery (
  concept TEXT PRIMARY KEY,           -- concepts are vault-global; not subject-keyed
  aggregate REAL,                     -- prerequisite-weighted average of LO mastery_mean
  weakest_axis_view TEXT,             -- the lowest-mean axis view among contributing LOs
                                      -- (display only; computed from mastery_axis_views)
  updated_at TEXT
);
-- Per-subject aggregates are computed on read by filtering this table through
-- the subject's resolved in_scope set. Not denormalized in SQLite.

CREATE TABLE learner_state_beliefs (
  id TEXT PRIMARY KEY,
  subject TEXT,
  scope_type TEXT,                   -- error_type | misconception (LO/concept beliefs now live in
                                     -- learning_object_mastery / learner_theta / concept_mastery)
  scope_id TEXT,
  belief_key TEXT,                    -- error propensity slot (e.g. error_type id)
  mean REAL,
  variance REAL,
  evidence_count INTEGER,
  last_surprise REAL,
  last_evidence_at TEXT,
  stale_after_days INTEGER,
  algorithm_version TEXT,
  updated_at TEXT,
  UNIQUE(subject, scope_type, scope_id, belief_key)
);
-- Reduced scope as of v2.0.0: LO mastery moved to learning_object_mastery,
-- learner-level abilities moved to learner_theta. This table now holds per-learner
-- error-type propensities and misconception activation state.

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
  origin TEXT,                       -- learner_requested | simulator_eig | walkthrough_followup
  target_belief_json TEXT,           -- which belief/uncertainty this item was meant to reduce (simulator origin)
  used_at TEXT,
  info_gain_observed REAL,           -- variance drop on the target belief after the attempt
  promotion_recommendation TEXT,     -- promote | skip | revise (filled at sweep time)
  promotion_rationale TEXT,          -- one-line why (cached at sweep time)
  promoted_to_practice_item_id TEXT  -- null unless learner promotes
);

CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  started_at TEXT,
  ended_at TEXT,
  energy TEXT,
  sleep_quality REAL,
  available_minutes INTEGER,
  notes_md_path TEXT
);

CREATE TABLE observation_templates (
  id TEXT PRIMARY KEY,
  domain TEXT,
  version TEXT,
  title TEXT,
  template_yaml TEXT,
  active INTEGER,
  created_at TEXT
);

CREATE TABLE observation_events (
  id TEXT PRIMARY KEY,
  template_id TEXT,
  subject TEXT,
  session_id TEXT,
  related_learning_object_id TEXT,
  related_practice_item_id TEXT,
  media_ref TEXT,
  response_json TEXT,
  emitted_attempt_id TEXT,
  template_version TEXT,
  created_at TEXT
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
  expected_information_gain REAL,
  expected_surprise REAL,
  target_scope_json TEXT,
  plain_english_json TEXT,
  created_at TEXT
);

CREATE TABLE model_replay_runs (
  id TEXT PRIMARY KEY,
  old_algorithm_version TEXT,
  new_algorithm_version TEXT,
  started_at TEXT,
  completed_at TEXT,
  status TEXT,                       -- completed | failed | cancelled | restored
  input_event_count INTEGER,
  changed_rows_json TEXT,            -- top-N diff: largest mastery/variance deltas
  warnings_json TEXT,
  snapshot_id TEXT                   -- references replay_snapshots(id)
);

CREATE TABLE replay_banner_state (
  id INTEGER PRIMARY KEY CHECK (id = 1),    -- singleton row
  current_code_version TEXT,
  last_seen_vault_version TEXT,
  dismissal_count INTEGER DEFAULT 0,
  last_dismissed_at TEXT,
  last_resolved_at TEXT                     -- when user ran replay or accepted-without-replay
);

CREATE TABLE replay_snapshots (
  id TEXT PRIMARY KEY,
  algorithm_version TEXT,            -- the version active when the snapshot was taken
  created_at TEXT,
  learning_object_mastery_json TEXT, -- compact serialized derived-table snapshot
  learner_state_beliefs_json TEXT,
  practice_item_state_json TEXT,
  attempt_surprise_json TEXT,
  scheduler_explanations_json TEXT,
  note TEXT                          -- e.g. "pre-replay for v3 → v4"
);

CREATE TABLE policy_eval_runs (
  id TEXT PRIMARY KEY,
  eval_type TEXT,                    -- scheduler_golden | policy_counterfactual |
                                     -- heldout_prediction | simulated_learner
  fixture_path TEXT,
  baseline_policy TEXT,
  candidate_policy TEXT,
  algorithm_version TEXT,
  seed INTEGER,
  started_at TEXT,
  completed_at TEXT,
  status TEXT,
  summary_json TEXT
);

CREATE TABLE policy_eval_results (
  id TEXT PRIMARY KEY,
  run_id TEXT,
  metric TEXT,                       -- brier_score | expected_effort | final_mastery |
                                     -- repair_completion | calibration_error | cognitive_load
  scope_type TEXT,                   -- domain | subject | goal | learning_object | global
  scope_id TEXT,
  baseline_value REAL,
  candidate_value REAL,
  delta REAL,
  notes_json TEXT
);

CREATE TABLE elicitation_events (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  selected_practice_item_id TEXT,
  target_scope_json TEXT,
  policy TEXT,                       -- heuristic_greedy_eig | probe_eig | simulator_ephemerals |
                                     -- deep_diagnostic | mcts
  candidate_scores_json TEXT,        -- includes priority, EIG, uncertainty, readiness, load
  entropy_before REAL,
  expected_information_gain REAL,    -- bits; for probe_eig this is mutual info on hypothesis identity
  expected_surprise REAL,
  selected_reason TEXT,
  hypothesis_set_id TEXT,            -- nullable; set when policy in (probe_eig, simulator_ephemerals,
                                     -- deep_diagnostic) — references the active HypothesisSet
  hypothesis_set_json TEXT,          -- full HypothesisSet serialization (§16.5) for replay/debug
  trigger TEXT,                       -- probe_phase_routine | probe_phase_local_pi_inadequate |
                                     -- manual_deep_diagnostic_lo | manual_deep_diagnostic_goal
  fallback_outcome TEXT,             -- existing_pi | existing_pi_inadequate | simulator_eig |
                                     -- existing_pi_simulator_failed
  created_at TEXT
);

CREATE TABLE attempt_surprise (
  attempt_id TEXT PRIMARY KEY,
  predicted_score_dist_json TEXT,
  predicted_error_type_dist_json TEXT,
  predicted_confidence_dist_json TEXT,
  predicted_latency_dist_json TEXT,
  predicted_hints_dist_json TEXT,
  observed_joint_bucket_json TEXT,
  predictive_surprise REAL,
  bayesian_surprise REAL,
  surprise_direction TEXT,            -- positive | negative | mixed
  fsrs_interval_factor REAL,
  posterior_delta_json TEXT,
  triggered_actions_json TEXT,
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

CREATE TABLE embeddings (
  entity_type TEXT,                  -- concept | learning_object | practice_item | note_paragraph
  entity_id TEXT,
  content_hash TEXT,                 -- recompute when this changes
  model TEXT,
  dim INTEGER,
  vector BLOB,                       -- float32 little-endian, length = dim
  updated_at TEXT,
  PRIMARY KEY (entity_type, entity_id)
);

CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  applied_at TEXT NOT NULL
);

CREATE INDEX idx_attempts_item_time ON practice_attempts(practice_item_id, created_at);
CREATE INDEX idx_attempts_lo_time ON practice_attempts(learning_object_id, created_at);
CREATE INDEX idx_item_state_due ON practice_item_state(active, due_at);
CREATE INDEX idx_learner_state_beliefs_scope ON learner_state_beliefs(subject, scope_type, scope_id);
CREATE INDEX idx_error_events_status ON error_events(status, learning_object_id);
CREATE INDEX idx_generated_items_review ON generated_items(review_status, generated_at);
CREATE INDEX idx_observation_events_subject ON observation_events(subject, created_at);
CREATE INDEX idx_content_events_recent ON content_events(created_at, event_type);
CREATE INDEX idx_content_events_batch ON content_events(change_batch_id);
CREATE INDEX idx_scheduler_explanations_session ON scheduler_explanations(session_id, practice_item_id);
CREATE INDEX idx_elicitation_events_session ON elicitation_events(session_id, selected_practice_item_id);
CREATE INDEX idx_policy_eval_runs_type ON policy_eval_runs(eval_type, started_at);
CREATE INDEX idx_policy_eval_results_run ON policy_eval_results(run_id, metric);
```

## Storage invariants

- All timestamps are stored as ISO-8601 UTC strings. The TUI renders them in `[student].timezone`.
- `state.sqlite` enables foreign keys where both sides are SQL-owned. YAML-owned ids are validated by the storage layer before commits.
- Every schema change is a numbered migration recorded in `schema_migrations`.
- Attempt logging is atomic: `practice_attempts`, `grading_evidence`, `practice_item_state`, `learning_object_mastery`, `learner_theta`, `lo_probe_state`, `learner_state_beliefs`, `attempt_surprise`, `attempt_propagation_events`, `error_events`, `generated_items`, and `content_events` commit or roll back together. `mastery_axis_views` is marked dirty inside the same transaction and may be recomputed lazily after commit.
- Surprise is computed from predictions captured **before** the attempt updates mastery. The prior prediction, observed joint bucket, posterior delta, and any FSRS interval factor are stored so scheduler decisions are auditable.
- Elicitation uses only this vault's local learner data in MVP. Any future cross-user or meta-trained model must be opt-in and represented in `agent_runs` / provenance metadata.
- Policy evaluation writes only to `policy_eval_runs` and `policy_eval_results`; it must never update learner mastery, FSRS state, or scheduler queues.
- Derived learner-state tables (`practice_item_state`, `learning_object_mastery`, `concept_mastery`, `learner_state_beliefs`, `attempt_surprise`, cached scheduler explanations) must be replayable from raw attempts, observations, content state, and algorithm version.
- Observation templates are versioned. Observation events keep the template id/version and raw response JSON so future algorithms can reinterpret the evidence.
- Beliefs can go stale. `last_evidence_at` and `stale_after_days` let the scheduler increase uncertainty over time without inventing new failures.
- Related writes are grouped under `change_batches`. Any AI-generated or import-generated content must have a `change_batch_id`.
- Rollback creates a new `change_batches` row with `reason = "rollback"` and links it to the original batch. It should deactivate or restore, not silently erase history.
- YAML writes use atomic temp-file replacement. The storage layer computes and stores `content_hash` after a successful write.
- If a YAML write fails after a DB transaction starts, the DB transaction rolls back.
- If an external edit changes a YAML file and its content hash differs from SQLite, the TUI prompts for re-indexing before scheduling or grading that item.
- `content_events` powers the TUI "Recently Added" view and makes auto-accepted canonical transforms/variants easy to inspect, edit, deactivate, or reject after the fact.
- `agent_runs` records prompt template, prompt version, model, SDK version, context hash, and output schema for every AI-backed grading/generation/diagnosis operation.
- `session_checkpoints` is app-managed state for crash/interruption recovery and is cleared when a session ends cleanly.
- `learning_object_mastery` stores a single scalar `mastery_mean` + `mastery_variance` per LO — not a five-axis tensor. Per-axis estimates are derived views, materialized in `mastery_axis_views`.
- `learner_theta` and `lo_probe_state` are derived from `practice_attempts` (raw) + `learner_claims` (raw priors). Both are dropped and recomputed on `learnloop replay-model`.
- `learner_claims` is **raw input** (filed via the init wizard, the claims CLI, or imported), not derived. Replay does not touch it.
- `mastery_axis_views` is a derived cache. It is rebuilt opportunistically after each attempt and fully recomputed on replay. It is safe to delete the whole table at any time; the next read or attempt repopulates it.
- The four LO-level axis labels (`memory`, `understanding`, `execution`, `generalization`) and the learner-level `calibration` trait are **never** stored as primary belief state. They appear only in `mastery_axis_views` (the four LO-level views) and in `learner_theta` rows keyed on `calibration_accuracy` (the learner-level trait, per `(domain, practice_mode)`).
- Changes to `axis_views` weights in `algorithm_priors.yaml` are **MINOR** algorithm bumps (they don't change the underlying θ, only the display aggregation). Changes to evidence-family lists, θ update noise, or `BETA_LO`/`BETA_THETA` are **MAJOR** bumps.

## Attempt → updates

One attempt updates the item state, mastery state, learner-state beliefs, surprise record, and error model atomically:

```text
attempt (practice_item_id=pi_x, learning_object_id=lo_x, score=0.45, confidence=4,
         hints=2, error_type=hazard_probability_confusion,
         evidence_facets=[schema, recall], step_trace_json={...})
   ↓
1. practice_item_state[pi_x]: FSRS update via score_to_fsrs_rating(score)
2. learning_object_mastery[lo_x]: scalar mastery_mean / mastery_variance update
                                  (Layer 2, "Update rule (Tier 2 — LO scalar)"),
                                  then apply error_impacts.lo_mastery_delta
3. learner_theta: update one slot per declared evidence_family (Layer 0
                  update rule), with observation_noise scaled by attempt_type
                  (probe vs steady-state) and family weight
4. learner_theta[domain, calibration_accuracy, practice_mode]:
   update if confidence was captured (fires every attempt)
5. error_impacts.families: apply to learner_theta slots (logit-space deltas)
6. attempt_propagation_events: propagate -mean_delta / +variance_delta to
                                prereq LOs' learning_object_mastery scalars
7. mastery_axis_views[lo_x, *]: mark dirty; recompute lazily on next read
                                 (or eagerly when in active queue)
8. attempt_surprise: compare predicted vs observed joint evidence and store
                      Bayesian surprise (entropy computed over LO scalar +
                      involved θ family slots, not axis views)
9. practice_item_state[pi_x]: modulate FSRS interval within configured
                               bounds if surprise is high
10. error_events: append; if high_confidence_wrong or negative surprise
                  → open repair_loop / diagnostic follow-up (suppressed if
                  lo_probe_state[lo_x].status == 'in_progress')
11. lo_probe_state[lo_x]: increment probe_attempts_completed; check
                           transition to 'complete'
```

Then `concept_mastery` is recomputed lazily on read or on `exports.refresh`.

## Next-action selection

A two-stage policy. First, the per-item priority score chooses **which** Practice Items to surface. Then a rule layer picks **what mode** the next item should be in. Adaptive elicitation is part of the priority score for every daily queue, with active goals as the default uncertainty-reduction target.

### Priority score (queue ordering)

```text
rel = eig_reliability(lo, family=primary_family(pi))   # [0, 1]; see Layer 4 reliability ramp

priority =
  0.25 * forgetting_risk                       # 1 - retrievability
+ 0.15 * active_goal_importance                # from profile/goals.md + concept graph
+ 0.15 * expected_information_gain  * rel      # dampened until LO + θ posteriors are mature
+ 0.10 * error_type_entropy         * rel      # dampened with EIG
+ 0.10 * recent_error_severity                 # boost items in same LO/concept as recent errors
+ 0.10 * transfer_gap                          # high recall but low transfer
+ 0.05 * deadline_pressure                     # from profile/goals.md
+ 0.05 * learner_interest
- 0.15 * cognitive_overload_risk               # session length consumed, novelty already added
```

The reliability multiplier `rel` is applied **only** to EIG-derived components (`expected_information_gain`, `error_type_entropy`). The other components are either based on raw events (`recent_error_severity`), independent FSRS state (`forgetting_risk`), or exogenous inputs (`active_goal_importance`, `deadline_pressure`) — they are not affected by surrogate-posterior maturity. `primary_family(pi)` picks the highest-weight family in `pi.evidence_weights` (ties broken by canonical family order).

### Scheduler explanations

Every scheduled Practice Item should carry an explanation object. This is not just UI polish; it is how the scheduler becomes debuggable.

```json
{
  "practice_item_id": "pi_pca_transfer_001",
  "selected_mode": "transfer",
  "priority": 0.71,
  "components": {
    "forgetting_risk": 0.24,
    "active_goal_importance": 0.08,
    "expected_information_gain": 0.13,
    "error_type_entropy": 0.09,
    "recent_error_severity": 0.12,
    "transfer_gap": 0.15,
    "deadline_pressure": 0.02,
    "learner_interest": 0.03,
    "cognitive_overload_risk": -0.04
  },
  "eig_reliability": {
    "value": 0.95,
    "f_lo": 0.95,                          // 8 LO attempts
    "f_theta": 0.97,                       // mature θ[math_stats_ml, transfer]
    "bottleneck": "f_lo",
    "applied_to": ["expected_information_gain", "error_type_entropy"]
  },
  "readiness_factor": 1.0,
  "target_scope": {
    "type": "active_goals",
    "goal_ids": ["fine_gray_research_understanding"]
  },
  "plain_english": [
    "This item is due today.",
    "It would reduce uncertainty about an active goal.",
    "The model is uncertain whether the likely error is recall or schema.",
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

`readiness_factor` multiplies the candidate item's priority score before queue ordering. New material is gated more aggressively than review. When `available_minutes < 20` (or the user explicitly picks `short` focus pattern), the daily loop switches to **short-session mode** (§10): the queue collapses to warm-up retrieval plus one optional misconception-repair drill, the deep-work / weakness-repair / transfer blocks are skipped entirely, ephemeral diagnostic generation is suppressed, and surprise-driven diagnostic-followup interruptions are suppressed (no time for a detour). FSRS and mastery still update normally on every attempt logged.

### Cold-start curriculum — replaced by probe-mode flow

Cold start is now handled by **per-LO probe mode** (Layer 4, "Probe mode — per-LO diagnostic phase"). The flat "mastery_default = 0.5 across axes" fallback is gone: a new LO seeds its scalar mastery from the learner's θ profile via `seed_initial_mastery` (Layer 0, "Cold-start: θ as the prior on new-LO mastery"), and the LO enters probe mode for its first 1–3 attempts depending on whether the learner has filed a `learner_claims` row for the relevant scope.

The relevant parts of the old subsection still apply:

- **Difficulty prior + prerequisite order** still determines which LOs are eligible to enter probe mode first when nothing else is scheduled.
- `learnloop today --diagnostic` is still available; it now means "enroll all unscheduled active-goal LOs into probe mode for this session" (subject to `per_session_max_new_probes` and `per_session_max_probe_attempts`) rather than running a separate one-off flow.
- The `mastery_default` / `variance_default` / `cold_start_alpha_factor` / `cold_start_alpha_attempts` parameters in `algorithm_priors.yaml` now act as **probe-phase seeds**: the default used before any probe attempt has been logged on the LO, and the dampening multiplier on the LO scalar EMA for the first `cold_start_alpha_attempts` probe-phase attempts. Domain overrides still apply (languages start harder, motor skills start much lower).
- The init-time **background-claims wizard** (§17) writes `learner_claims` rows that lift the strong-claim path into `attempts_target_with_strong_claim = 1` or `skipped_by_claim` for LOs whose concept matches a claim.

### `algorithm_priors.yaml` — surrogate parameters, cold-start ramp, propagation defaults

Every parameter the scheduler / mastery / surrogate / propagation logic reads from disk lives here. The file is checked into the vault, versioned alongside `algorithm_version`, and edited rarely — mostly when a new algorithm version ships or when a domain wants to tune itself.

```yaml
algorithm_version: "1.0.0"

mastery:
  ema_alpha: 0.2
  mastery_default: 0.5
  variance_default: 0.25
  cold_start_alpha_factor: 0.5           # multiplier on alpha for first N attempts on a new LO
  cold_start_alpha_attempts: 5
  prior_pseudo_count: 20                 # weight given to global prior in Dirichlet shrinkage

surrogate:
  beta_lo: 4.0                           # logistic weight on per-LO scalar mastery term
  beta_theta: 1.5                        # logistic weight on per-learner θ (over PI's declared families)
  beta_difficulty: 3.0
  beta_misconception: 2.0
  lo_seed_transfer: 0.15                 # how much θ shifts the cold-start mastery seed for a new LO
  score_bucket_thresholds: [0.30, 0.65, 0.90]
  confidence_calibration_slope: 0.7      # how strongly confidence tracks score for well-calibrated learners
  latency_log_sigma_base: 0.5
  latency_log_sigma_execution_factor: -0.3   # tighter distribution as procedure/fluency θ rises
  hint_request_base: 0.15
  hint_request_difficulty_factor: 0.4
  calibration_obs_noise: 0.5             # noise on the calibration_accuracy θ update

probe_mode:
  attempts_target_default: 3
  attempts_target_with_strong_claim: 1
  variance_convergence_threshold: 0.10
  observation_noise: 0.4                 # smaller → probe attempts move θ more than steady-state
  steady_state_observation_noise: 1.2
  claim_skip_threshold: 0.75
  claim_skip_revert_threshold: 0.40
  short_session_eligible: false
  per_session_max_new_probes: 2
  per_session_max_probe_attempts: 6
  suppress_surprise_followups: true

eig_reliability:                         # post-probe ramp for EIG and surprise-magnitude uses
  half_lo: 3.5                           # n_lo at which f_lo = 0.5
  slope_lo: 1.5                          # ~0.32 at n_lo=3, ~0.68 at n_lo=4, ~0.90 at n_lo=5
  half_theta: 8.0                        # θ matures more slowly; needs cross-LO evidence
  slope_theta: 0.5                       # ~0.02 at n_th=0, ~0.50 at n_th=8, ~0.90 at n_th=12
  fallback_to_probe_below: 0.40          # below this reliability post-probe, dispatch reuses
                                         # the cached HypothesisSet and runs probe_EIG instead
                                         # of weakened normal_EIG (§16 "Probe-EIG vs normal-EIG dispatch")
  applies_to:
    - information_gain_weight
    - error_uncertainty_weight
    - surprise_interval_factor
    - surprise_followup_insertion
  does_not_apply_to:
    - high_confidence_wrong              # misconception trigger fires regardless
    - error_events                       # categorical logging fires regardless
    - probe_mode                         # probe selection has its own (hypothesis-based) scoring
    - forgetting_risk                    # FSRS retrievability independent of LO posterior
    - active_goal_importance             # exogenous goal weighting
    - recent_error_severity              # based on raw events, not posterior
    - deadline_pressure                  # exogenous time signal

probe_eig:                               # hypothesis-based scoring during probe phase
  min_local_score: 0.30                  # bits; below this on best existing PI, fall back to simulator-EIG
  hypothesis_count_min: 2
  hypothesis_count_max: 4
  simulator_eig_required_pairs: 1        # min unresolved hypothesis pairs to request from Codex
  marginal_hypothesis_prior: uniform     # uniform | weighted_by_surrogate_modes
  mode_weights: # reuses PROBE_MODE_WEIGHTS from §16 Layer 4 "Probe mode"
    inherit_from_probe_mode: true

probe_hypothesis_templates:
  # Inline core defaults live at prompts/probe_hypothesis_templates.yaml and ship with LearnLoop.
  # Domains add their own via DomainModule.probe_hypothesis_templates() (§4) which shadow core
  # entries on the same (knowledge_type, practice_mode) key.
  source_paths:
    - prompts/probe_hypothesis_templates.yaml     # core templates (general domain)
  domain_overrides_via_module: true               # DomainModule.probe_hypothesis_templates() merged in

axis_views:
  memory:
    families: { recall: 0.50, recognition: 0.20 }
    use_fsrs_retrievability: true
    fsrs_weight: 0.30
    lo_mastery_blend: 0.50
    status_thresholds:
      unobserved_when_evidence_count_below: 1
      weak_evidence_when_below: 3
      reliable_when_above: 8
  understanding:
    families: { schema: 0.35, explanation: 0.25, discrimination: 0.20 }
    misconception_load_weight: -0.20
    lo_mastery_blend: 0.50
    status_thresholds:
      unobserved_when_evidence_count_below: 1
      weak_evidence_when_below: 4
      reliable_when_above: 10
  execution:
    families: { procedure: 0.60, fluency: 0.40 }
    requires_execution_evidence: true
    lo_mastery_blend: 0.40
    status_thresholds:
      unobserved_when_evidence_count_below: 1
      weak_evidence_when_below: 3
      reliable_when_above: 8
  generalization:
    families: { transfer: 0.65, discrimination: 0.35 }
    lo_mastery_blend: 0.40
    status_thresholds:
      unobserved_when_evidence_count_below: 1
      weak_evidence_when_below: 3
      reliable_when_above: 8

cross_lo_propagation:
  default:
    max_depth: 3
    hop_decay: 0.5
    total_propagated_weight_cap: 0.7
  error_gates:                           # see §16 Layer 2 "Cross-LO propagation" for full table
    recall_failure: { mean_factor: 0.0, variance_factor: 0.25, scope: all }
    conceptual_error: { mean_factor: 0.5, variance_factor: 0.7, scope: all }
    procedure_error: { mean_factor: 0.5, variance_factor: 0.7, scope: procedural_only }
    transfer_failure: { mean_factor: 0.3, variance_factor: 0.5, scope: conceptual_only }
    high_confidence_wrong: { mean_factor: 0.7, variance_factor: 0.8, scope: all, trigger_misconception_repair: true }
    # ... rest of the table; propagation acts on target LO's scalar mastery, not per-axis

staleness:
  default_stale_after_days: 30
  per_axis_view:                         # staleness still keyed per axis view for UI staleness flags;
    memory: 14                           # the underlying belief is the LO scalar + θ slots
    understanding: 60
    execution: 21
    generalization: 45
  per_theta_family:                      # θ slots stale independently
    recall: 14
    schema: 60
    procedure: 30
    fluency: 21
    discrimination: 45
    transfer: 60
    calibration_accuracy: 90

domain_overrides:
  language:
    mastery:
      mastery_default: 0.3               # language starts harder
    staleness:
      per_theta_family: { recall: 7 }    # vocabulary fades fast
    eig_reliability:
      half_lo: 2.0                       # vocab items reach reliability faster — fewer attempts needed
  esports_overwatch:
    mastery:
      mastery_default: 0.4
    cross_lo_propagation:
      default: { max_depth: 2 }          # mechanical/tactical prereq chains are shorter
    staleness:
      default_stale_after_days: 14       # patches and meta shifts age beliefs fast
    eig_reliability:
      half_lo: 6.0                       # VOD-style observations are noisier; trust the posterior later
  motor_vod:
    mastery:
      mastery_default: 0.35
    eig_reliability:
      half_lo: 5.0                       # motor observations are noisier than text grading
```

Resolution: for any parameter and a given LO/attempt, the merged config is `core_defaults ← domain_overrides[lo.domain] ← lo.cross_lo_propagation_override` (the LO override applies only to propagation fields it declares).

Changes to `algorithm_priors.yaml` bump the `algorithm_version` (semver per D1) and require `learnloop replay-model` — which the vault open banner will prompt for.

### Mode selection (after item is chosen)

Mode selection now consumes the **derived axis views** (Layer 2 / Tier 3) rather than primitive axis estimates, and reads each view's `status` so the scheduler can distinguish "no transfer evidence yet" from "transfer is weak":

```python
def choose_next_action(lo, axis_views, last_attempt, repair_loop_active,
                       surprise_threshold, probe_state):
    # Probe mode dominates everything except an active misconception repair loop.
    if repair_loop_active:
        return "misconception_repair"
    if probe_state and probe_state.status == "in_progress":
        return probe_mode_pick(lo, axis_views, probe_state)
    if last_attempt and (last_attempt.get("bayesian_surprise", 0) > surprise_threshold
                         and last_attempt.get("surprise_direction") == "negative"):
        return "error_diagnosis"

    mem = axis_views["memory"]
    und = axis_views["understanding"]
    exe = axis_views["execution"]
    gen = axis_views["generalization"]

    # Exploration vs. remediation depends on status, not just mean.
    if mem.mean is not None and mem.mean > 0.8:
        if gen.status == "unobserved":
            return "transfer_probe"           # low-stakes generalization probe
        if gen.status in {"weak_evidence", "estimated"} and (gen.mean or 0) < 0.5:
            return "transfer"                  # remediation

    if und.mean is not None and und.mean < 0.4 \
       and exe.status != "unobserved" and (exe.mean or 0) < 0.5:
        return "completion_problem"

    if last_attempt and last_attempt.get("error_type") == "theorem_selection_error":
        return "contrastive_discrimination"
    if last_attempt and last_attempt.get("score", 1.0) < 0.5 \
       and last_attempt.get("hints_used", 0) >= 2:
        return "walkthrough"                   # begin faded-worked-example sequence
    if last_attempt and last_attempt.get("attempt_type") == "dont_know":
        return "walkthrough"

    if mem.mean is not None and mem.mean > 0.85 \
       and exe.status != "unobserved" and (exe.mean or 0) < 0.5:
        return "fluency_drill"

    return "retrieval"
```

`probe_mode_pick` returns the `practice_mode` of the highest-scoring eligible Practice Item per `probe_eig_score` against the LO's active `HypothesisSet` (defined in Layer 4 "Probe mode and probe-EIG"). Probe-mode picks are constrained to the `PROBE_MODE_WEIGHTS` set — modes with weight 0 (e.g. `transfer`, `far_transfer`) are never selected for probes. If no existing item exceeds `algorithm_priors.probe_eig.min_local_score` bits, the dispatch may fall back to simulator-EIG (see "Hypothesis provider and simulator-EIG unification").

The `transfer_probe` mode is new (§16.5): it is a low-stakes generalization probe that suppresses negative-surprise follow-ups, disables hints by default, and shifts the generalization axis view from `unobserved` to `weak_evidence` or `estimated` on completion. It differs from `transfer` only in that a poor result does **not** open `misconception_repair`.

### Fading worked-example sequence

When a learner triggers a `walkthrough` (after `dont_know` or repeated hints), the scheduler does **not** drop the learner straight back into `retrieval`. It enrolls them in a short fading sequence that gradually transfers cognitive load back to the learner:

```text
walkthrough                       — full guided solution; mastery update suppressed
   ↓ next session (or same session if energy permits)
faded_worked_example              — same problem with ~50% of steps elided for the learner
   ↓ next session
completion_problem                — only the final answer/derivation step is left to the learner
   ↓ next session
reconstruction_after_walkthrough  — full independent attempt; mastery updates resume
```

The sequence is tracked as a per-LO state machine and persists across sessions until the learner reaches `reconstruction_after_walkthrough` successfully (or skips out). The `walkthrough` itself produces a generated `worked_example` content artifact (when Codex is available) or pulls the LO's existing `worked-examples/*.md` (when offline). Faded variants are Codex-generated by the `variant-generator` role with explicit "elide these step ids" instructions, or pulled from a pre-authored faded variant if one exists.

Sequence state is recorded so it survives interruptions:

```sql
CREATE TABLE faded_sequence_state (
  learning_object_id TEXT PRIMARY KEY,
  current_stage TEXT,                -- walkthrough | faded | completion | reconstruction
  started_at TEXT,
  last_attempt_id TEXT,
  failed_stage_count INTEGER,        -- regress to earlier stage if a stage fails repeatedly
  updated_at TEXT
);
```

If a stage fails (score < 0.5), the scheduler regresses one step (e.g. completion fail → faded). If a stage fails twice in a row, escalate back to `walkthrough`. This avoids the trap of repeating the same independent attempt against a stuck learner.

---

# 16.5. Type enums and extensible registries

Core enums govern the generic data model. Domain modules may register additional namespaced values for practice modes, knowledge types, evidence facets, error types, rubrics, and attempt schemas.

```text
knowledge_type      — What kind of thing is being learned?
practice_mode       — What activity tests or teaches it?
attempt_type        — How independently did the learner engage?
evidence_family     — Which evidence channel did the attempt observe?  (primary update target)
mastery_axis_view   — Which interpretable view aggregates evidence for UI?  (derived only)
```

Note: in the three-tier belief model (§16 Layer 0/2), `evidence_family` is the **primary** update channel — each attempt updates the LO scalar mastery once plus one θ slot per declared evidence family. `mastery_axis_view` is a **derived view** label, not a stored belief primitive. This is a deliberate departure from the prior axis-as-latent design.

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

`KnowledgeType` accepts either a core value or a namespaced domain value when a module needs a specialized type.

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
CorePracticeMode = Literal[
    "read", "observe",
    "worked_example", "annotated_example", "faded_worked_example", "completion_problem",
    "retrieval", "cued_recall", "free_recall", "recognition",
    "cloze", "multiple_choice", "short_answer",
    "explain_from_memory", "teach_back",
    "derivation_reconstruction", "proof_reconstruction",
    "procedure_execution", "problem_solving",
    "interleaving", "contrastive_discrimination",
    "error_diagnosis", "misconception_repair", "disguised_retest",
    "transfer", "near_transfer", "far_transfer", "transfer_probe",
    "variant_generation",
    "reflection", "postmortem",
    "timed_drill", "fluency_drill",
    "dictation", "translation", "sentence_production",
    "pronunciation_drill", "shadowing", "copying",
    "motor_imitation", "external_focus_drill",
    "scenario_simulation",
    "walkthrough",
    "self_assessment",
]
```

`PracticeMode` accepts either a `CorePracticeMode` value or a namespaced domain value matching `<domain_id>:<mode_id>`, for example `language:conversation_turn` or `esports_overwatch:vod_review`.

A short selection of "best for" mappings:

| `practice_mode` | Best for |
| --- | --- |
| `read`, `observe` | Initial exposure; motor/tactical reference |
| `worked_example`, `annotated_example` | Novices; high-load material |
| `faded_worked_example` | Step between worked example and full solving: some steps shown, others elided for the learner to fill in |
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
| `transfer_probe` | Low-stakes generalization probe when `generalization_status = unobserved`; no misconception escalation on miss |
| `variant_generation` | Deep schema mastery |
| `reflection`, `postmortem`, `self_assessment` | Metacognition, calibration |
| `timed_drill`, `fluency_drill` | Fluency, exam readiness |
| `dictation`, `translation`, `sentence_production`, `pronunciation_drill`, `shadowing` | Language |
| `copying`, `motor_imitation`, `external_focus_drill` | Motor learning |
| `scenario_simulation` | Esports, clinical/legal/statistical cases |
| `walkthrough` | Guided instruction after "I don't know"; independence is tracked by `attempt_type` |

## `AttemptType`

Separate from practice mode: how independently did the learner engage with the prompt?

```python
AttemptType = Literal[
    "independent_attempt",
    "hinted_attempt",
    "dont_know",
    "diagnostic_probe",
    "guided_walkthrough",
    "reconstruction_after_walkthrough",
    "skip",
    "self_report",
]
```

Mastery and FSRS updates depend on attempt type — see "Attempt-type handling" under Rubric-Based Grading. `diagnostic_probe` attempts (used during per-LO probe phase, §16 Layer 4 "Probe mode") use a smaller `observation_noise` when updating `learner_theta` so probes move θ more than steady-state attempts.

## `EvidenceFamily` (primary update channel)

```python
CoreEvidenceFamily = Literal[
    "recall",
    "recognition",
    "schema",
    "explanation",
    "procedure",
    "fluency",
    "discrimination",
    "transfer",
    "calibration_accuracy",      # learner-level only; not aggregated into LO axis views
]
```

Domain modules may register additional namespaced families (e.g. `language:pronunciation_accuracy`, `esports_overwatch:hidden_state_inference`) that must declare an `aggregates_into` mapping onto one of the four LO-level axis labels.

Each Practice Item declares its `evidence_facets: [family, ...]` and optional `evidence_weights: {family: weight}` (weights do not need to sum to 1 — they are normalized on read). An attempt updates the LO scalar mastery once and the learner's θ slot for each declared family. Defaults come from the mode → evidence-family table in §16 Layer 2.

The prior `EvidenceFacet` enum is renamed to `EvidenceFamily` to reflect its promoted role as the primary update channel. The single value `metacognitive_accuracy` is renamed to `calibration_accuracy` and elevated to learner-level scope (stored on `learner_theta`, never on a per-LO axis view).

## `MasteryAxisView` (derived view label)

```python
MasteryAxisView = Literal[
    "memory",
    "understanding",
    "execution",
    "generalization",
]
```

Four labels. `calibration` is no longer in this enum — it is a learner-level trait stored on `learner_theta` keyed on `(domain, 'calibration_accuracy', practice_mode)`.

These labels are **derived views**, not primitive belief state. They appear in:

- `mastery_axis_views` (cache table; recomputable),
- `scheduler_explanations.components` (UI surface for "Why now?"),
- `choose_next_action` (mode selection reads axis-view mean + status).

They do **not** appear in `practice_attempts`, `learner_theta`, `learning_object_mastery`, or the surrogate score head. Tooling that wrote `target_mastery_axes` or per-axis `mastery_weights` on Practice Items is migrated at vault load to evidence-family-keyed `evidence_facets` / `evidence_weights` (§16 Layer 2 "Update rule").

## Hypothesis machinery (probe-EIG & simulator-EIG)

These types support the unified hypothesis flow described in §16 Layer 4 "Probe mode" and "Hypothesis provider and simulator-EIG unification." The hypothesis set is a local artifact — a small list of coarse diagnostic alternatives used to choose informative items. It is not a claim about the learner's true latent type.

```python
class PredictedObservation(BaseModel):
    score_bucket: Literal["again", "hard", "good", "easy"]
    likely_error_type: str | None    # taxonomy id, or null
    # MVP: only score_bucket + likely_error_type. confidence/latency/hints buckets
    # are deferred — they bloat templates without adding much discrimination.

class CoarseHypothesisTemplate(BaseModel):
    id: str                          # stable kebab-case within (knowledge_type, practice_mode)
    label: str                       # short human-readable name for explanations
    description: str                 # one-line definition for debugging
    knowledge_type: KnowledgeType
    practice_mode: CorePracticeMode | str   # core or namespaced
    domain_id: str = "general"       # 'general' for shared core templates; override per domain
    template_version: str            # semver; bumps invalidate cached hypothesis_set_ids
    predicted_observation: PredictedObservation
    # Family-loading profile that the instantiator uses to bind θ + LO mastery → predicted score:
    family_loading: dict[str, float]  # e.g. {recall: 0.8, schema: 0.2}; need not sum to 1
    # Optional anchors used at instantiation (see Layer 4 "Probe mode and probe-EIG"):
    prereq_anchors: list[str] = []
    confusable_concept_anchors: list[str] = []

class Hypothesis(BaseModel):
    """A CoarseHypothesisTemplate instantiated against a specific LO."""
    id: str                          # template.id + LO-instance suffix
    template_id: str
    template_version: str
    lo_id: str
    label: str                       # may be specialized vs the template label
    description: str
    predicted_observation: PredictedObservation
    family_loading: dict[str, float]
    instantiation_inputs_hash: str   # hash of (lo, prereqs, confusables, θ snapshot subset)

class HypothesisSet(BaseModel):
    id: str                          # the HypothesisSetId — see hashing rule below
    lo_id: str
    probe_phase_id: str              # nullable for manual deep-diagnostic contexts
    algorithm_version: str
    template_versions: dict[str, str]   # template_id → version actually used
    theta_snapshot_hash: str         # scoped to the LO's evidence_facets union
    hypotheses: list[Hypothesis]
    created_at: str
    trigger: Literal[
        "probe_phase_local_pi_inadequate",
        "manual_deep_diagnostic_lo",
        "manual_deep_diagnostic_goal",
        "probe_phase_routine",       # the routine case: hypotheses created at probe entry,
                                     # used to score the existing PI pool first
    ]
```

`HypothesisSetId` is the `HypothesisSet.id` field. It is derived deterministically so replay reproduces the same id from the same raw inputs:

```python
def compute_hypothesis_set_id(
    algorithm_version: str,
    lo_id: str,
    probe_phase_id: str | None,
    template_versions: dict[str, str],     # already deterministic-sorted by key
    theta_snapshot_hash: str,
    trigger: str,
) -> str:
    canonical = json.dumps({
        "alg":     algorithm_version,
        "lo":      lo_id,
        "phase":   probe_phase_id or "",
        "tmpls":   sorted(template_versions.items()),
        "theta":   theta_snapshot_hash,
        "trigger": trigger,
    }, sort_keys=True, separators=(",", ":"))
    return "hs_" + sha256(canonical.encode("utf-8"))[:16]

def compute_theta_snapshot_hash(lo, learner_theta) -> str:
    # Scoped to the LO's declared evidence_facets union, in the LO's domain.
    # Means and variances rounded to 3 decimals so jitter doesn't churn the id.
    relevant_slots = [
        (family, round(t.mean, 3), round(t.variance, 3))
        for family in lo.declared_evidence_facets_union
        for t in learner_theta[lo.domain, family, *]
    ]
    return sha256(json.dumps(sorted(relevant_slots), separators=(",", ":")).encode())[:12]
```

A `HypothesisSet` is **not** stored as authoritative learner state. It is logged on `elicitation_events.hypothesis_set_json` and referenced from `scheduler_explanations`, `ephemeral_session_items.target_belief_json`, and (for simulator-EIG calls) `agent_runs.input_context_hash` so the whole flow is auditable and reproducible on replay.

---

# 17. How a user actually uses it

## Initialize vault

```bash
mkdir learning-vault
cd learning-vault
learnloop init
```

Codex auth is configured separately through the installed Codex runtime. LearnLoop should detect missing auth only when the user invokes an AI-backed feature; non-AI review and scheduling commands still work.

After the vault scaffold is written, `init` offers a **background-claims wizard** as a final, skippable step. The wizard lets the learner check off concepts/domains they're already comfortable with; each selection writes a `learner_claims` row with `source = init_wizard`. These claims become priors on the learner θ profile (Layer 0) — they shorten subsequent per-LO probe phases rather than asserting mastery directly.

```text
┌────────────────────────────────────────────────────────────┐
│ Background (optional — skip with Esc)                      │
├────────────────────────────────────────────────────────────┤
│ Pick concepts you're already comfortable with. We'll use   │
│ these as priors, not as asserted mastery — you'll still    │
│ probe each LO briefly, just fewer times.                   │
│                                                             │
│  [✓] linear algebra (general)             strong            │
│  [✓] python                                strong            │
│  [ ] probability                          medium            │
│  [ ] korean grammar                       weak              │
│                                                             │
│ [Done] [Skip]                                              │
└────────────────────────────────────────────────────────────┘
```

A "strong" claim contributes ~8 attempts-equivalent of pseudo-evidence; "medium" ~3; "weak" ~1. The exact mapping is in `algorithm_priors.yaml`. The wizard is re-runnable later via `learnloop claims wizard` and can be invoked again whenever a new subject is added.

For development, onboarding, and screenshots:

```bash
learnloop init --sample
```

This creates a tiny demo vault with one math/stats subject, a few Learning Objects, Practice Items, attempts, errors, learner-state beliefs, surprise records, generated-item provenance, scheduler explanations, and grading goldens. The sample vault must be deterministic so tests and documentation can rely on it.

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
SQLite                       # state.sqlite via stdlib sqlite3 (incl. vec embeddings as BLOBs)
PyYAML                       # YAML round-trips for LO / PI / concept-graph
Markdown                     # narrative memory (no parser dependency for writes)
Pydantic                     # schemas for SDK outputs, YAML validation, service inputs
py-fsrs                      # item-memory scheduling
sentence-transformers        # local embeddings for concept merge, near-duplicate detection, related-LO lookup
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
      scheduler.py            # priority score, mode selection, readiness + EIG integration
      mastery.py              # FSRS + EMA, error-impact maps, mastery aggregation
      beliefs.py              # single-user learner-state means/uncertainty
      elicitation.py          # greedy EIG candidate scoring; MCTS later after eval gates
      surprise.py             # predictive/Bayesian surprise and FSRS modulation
      review.py
      attempts.py
      observations.py          # structured observation templates and event emission
      errors.py
      sessions.py
      inbox.py                # provenance routing, accept/reject, ephemeral promotion
      changes.py              # change batches, rollback/deactivation
      exports.py              # regenerate exports/* agent context snapshots
      import_export.py        # bundles, note imports, portable exports
      backup.py               # local backup create/list/restore
      doctor.py               # vault health checks and safe repairs
      grading.py              # rubric resolution, evidence storage, manual review triggers
      grading_eval.py         # local grading regression harness
      scheduler_eval.py       # queue/explanation golden tests
      policy_eval.py          # counterfactual policy comparison + held-out prediction evals
      simulated_learners.py   # synthetic learner scenarios for offline scheduler iteration
      replay.py               # recompute derived learner-state tables from raw events
      readiness.py            # session-start prompt and modulation factor
      lineage.py              # variant lineage walks (parent_item_id chain)
      misconception.py        # misconception LO lifecycle (promote, repair, resolve)
      pomodoro.py             # focus_blocks structure for "Today's Loop"

    storage/
      db.py                   # state.sqlite, migrations
      markdown.py             # narrative memory round-trips
      yaml_store.py           # YAML round-trips with content-hash tracking
      vault.py                # vault layout discovery, global profile merge
      embeddings.py           # local sentence-transformer index; concept-merge & related-LO queries

    codex/
      client.py               # CodexSdkClient (SDK lifecycle, threads, typed API)
      schemas.py              # structured-output models for AI proposals
      events.py               # app-level stream events for the TUI
      prompts.py              # prompts/*.md loaders
      validators.py           # SDK output validation + proposal normalization

    domains/
      registry.py              # load enabled domain modules and validate contracts
      base.py                  # DomainModule protocol + shared specs
      math_stats_ml.py
      research_papers.py
      language.py
      motor_vod.py
      esports_overwatch.py
      general.py

    templates/
      AGENTS.md
      learnloop.toml
      profile/
      subjects/
      prompts/
      rubrics/
      evals/
      observation-templates/
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
* domain registry with namespaced practice modes and evidence facets
* domain capability flags
* structured observation templates and `learnloop observe`
* SQLite migrations and attempt logging
* due queue computed from SQLite state
* FSRS-style item scheduler using `py-fsrs`
* single-user learner-state beliefs with per-LO mastery, learner θ, and predictive response distributions
* surprise logging over score + error type + confidence + latency + hints
* belief staleness from `last_evidence_at`
* surprise-modulated FSRS intervals within conservative bounds
* heuristic-bucket greedy information-gain scoring in every daily queue, targeting active goals
* Codex-simulator ephemeral diagnostic generation (gated on Codex availability)
* scheduler explanation object and `learnloop why`
* scheduler golden tests (`learnloop eval scheduler`)
* policy evaluation fixtures for held-out prediction and counterfactual scheduler comparison
* replayable learner model (`learnloop replay-model`) with version-tagged snapshot + diff view
* hint ladders on Practice Items (FSRS rating cap + mastery dampening from `hints_used`)
* local embedding index for concept-merge suggestions and near-duplicate detection
* tiered grader routing (exact-match / rubric-template / embedding-similarity / LLM)
* fading worked-example sequence after `walkthrough` / `dont_know`
* structured `goals.yaml` driving `active_goal_importance` and `deadline_pressure`
* `learnloop forgetting-curve` per LO and per subject
* end-of-session ephemeral promotion sweep with auto-rationale
* short-session mode for sub-20-minute slots
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
* simulated learner scenarios for early scheduler and elicitation iteration
* text-first import/export bundles
* Codex-generated practice
* Codex diagnosis from solution files
* concept graph YAML updates
* interleaving set generation
* automatic error repair drills
* confidence calibration
* review rescheduling
* richer uncertainty dashboard
* language conversation-test scaffolding
* Overwatch-first esports/VOD review scaffolding

## Later

* Tauri GUI
* visual concept graph
* richer PDF ingestion
* handwriting input
* audio-based language practice
* live language chat
* automated video/audio analysis for VOD review
* mobile companion
* MCTS/lookahead elicitation after enough local attempt data and held-out predictive calibration exist
* opt-in meta-learned elicitation models

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
Surprise updates the learner-state model.
The concept graph updates.
Your future sessions adapt.
```

That is the product.

---

# 25. Final recommended build path

Build in this order:

```text
1.  Standalone Python package scaffold
2.  Vault layout, config loading, migrations
3.  Textual TUI shell and Today's Loop screen
4.  Domain registry + generic domain module
5.  Domain capability flags + observation template registry
6.  YAML Learning Object / Practice Item stores (evidence-family-keyed)
7.  SQLite attempt logging + due queue
8.  FSRS + per-LO scalar mastery updates (Layer 1 + Layer 2 scalar)
9.  Learner-state beliefs + surprise logging + belief staleness
9.5 Learner θ profile (Layer 0) + probe-mode item selection (Layer 4)
    - learner_theta, learner_claims, lo_probe_state tables
    - profile update from probe attempts; calibration_accuracy slot updates
    - probe_eig_score over hypothesis sets (mutual information on hypothesis identity)
    - hypothesis-set instantiation from probe_hypothesis_templates
    - simulator-EIG probe-phase fallback when local PI pool inadequate
    - init-wizard background-claims step
    - mastery_axis_views derived-cache rebuild
    - probe TUI badge + probe-variant "Why now?" panel
10. Replayable learner model (covers learner_theta + lo_probe_state)
11. Greedy information-gain queue scoring over active goals (LO scalar + θ slots)
12. Scheduler explanations + `learnloop why`
13. Scheduler golden tests (include probe-mode → complete transition fixture)
13.5 Policy evaluation harness (`eval policy`, `eval replay`, simulated learners)
14. Error tagging, session summaries, exports refresh
15. Change batches, rollback, session checkpoints, and `learnloop doctor`
16. Recent auto-accepted content review
17. Backup + sample vault
18. Codex SDK adapter + one structured AI workflow
19. Prompt/model provenance + grading eval harness
20. Text-first import/export
21. Codex-generated practice and diagnosis
22. Concept graph updates
23. Interleaving and transfer engine
24. Language and Overwatch domain scaffolds
```

Step 9.5 sits before EIG/surrogate work (steps 11–12) so probes generate the calibration data that step 11's surrogate parameters need. Building EIG before probes means tuning surrogate parameters against priors-on-priors.

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
learnloop uncertainty
learnloop observe <template_id>
learnloop replay-model
learnloop eval policy
learnloop eval replay --holdout recent
learnloop doctor
```

Implementation guardrails:

```text
Do not start with a web app.
Do not start with a full GUI.
Do not put memory inside the model.
Do not make one giant memory file.
Do not fork Codex for LearnLoop-specific behavior.
Do not require cross-user data for the uncertainty model.

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
- MVP is single-user and local-first; no multi-user account or tenant model is required.
- LearnLoop is TUI-first; CLI is secondary.
- Codex integration is SDK-first via the user's ChatGPT subscription (not metered API), and Codex is required for the daily loop; offline runs degraded mode (review + self-grade + manual error tagging).
- Concept IDs are vault-global; per-subject `concept-graph.yaml` files are views over the vault-level `concepts/` registry.
- Replay semantics are fixed to "drop-and-recompute current formulas, version-tagged pre-replay snapshot, diff view of the largest movers."
- Adaptive elicitation in MVP is heuristic-bucket greedy EIG plus a narrow Codex-simulator path for ephemeral diagnostic items. Full predictive-LM EIG is a later, gated "deep diagnostic pass."
- The authoritative content model is Learning Objects + Practice Items.
- LearnLoop uses a **hybrid learner model**: raw attempts → per-LO scalar mastery (Layer 2) + per-learner θ over evidence families × domain (Layer 0) → derived axis views (memory, understanding, execution, generalization) → predictive response distributions used for scheduling and evaluation. Calibration is a learner-level trait on `learner_theta` keyed on `(domain, calibration_accuracy, practice_mode)`, not a per-LO axis. The four axis labels survive as **interpretable views** for the scheduler explanation and mode selection — never as primitive belief state. This is informed by Wang et al. 2025's predictive view plus POMDP/knowledge-tracing research that preserves structured mastery for remediation.
- Adaptive elicitation influences every daily queue, with active goals as the default target set.
- MVP uses local single-user learner-state beliefs, a derived predictive response distribution, and greedy expected-information-gain scoring.
- Bayesian surprise is modeled over the joint observation of score, error type, confidence, latency, and hints.
- Bayesian surprise can modulate FSRS intervals within conservative bounds and trigger diagnostic follow-ups.
- Beliefs become stale by increasing uncertainty, not by silently lowering mastery.
- Learner-state derived tables must be replayable from raw attempts, observations, content state, and algorithm version.
- Scheduler behavior must have local golden tests through `learnloop eval scheduler`.
- MCTS/lookahead elicitation is a later feature after enough local attempt data and held-out predictive calibration exist; rollout reward combines information gain with held-out prediction, repair completion, load, and latency terms.
- Scheduler and elicitation changes must pass stacked local evaluation: scheduler goldens, policy counterfactuals, held-out response prediction, and simulated learner scenarios.
- Generated diagnostic items must pass LO alignment, non-duplicate, hypothesis-discrimination, difficulty/cognitive-level, source-grounding, and quality-claim validation before use.
- Canonical transforms and variants of approved Practice Items auto-accept by default, with TUI alerts and a recent-change review surface.
- Agent grading updates mastery automatically unless low confidence or another manual-review trigger fires.
- The application must support multiple subject domains through extension modules with namespaced practice modes, evidence facets, error taxonomies, rubrics, scheduler hooks, TUI panels, and optional domain tables.
- Domain modules declare capability flags so the core can route UI, scheduling, import, media, and grading behavior safely.
- Structured observation templates are first-class learning events for non-card workflows.
- Text-first language conversation tests and Overwatch-first esports/VOD scaffolding are first-class domain goals.
- Audio-based language features, live chat, telemetry ingestion, and automated media analysis are later extensions.
- Generated/imported changes are grouped into rollbackable change batches.
- Scheduler decisions must be explainable through the TUI and `learnloop why`.
- Vault health checks, backups, session resume, prompt/model provenance, grading eval fixtures, import/export, and a deterministic sample vault are part of the implementation surface.

## Remaining data-model questions

1. **Concept identity / canonicalization.** When the agent extracts a concept similar but not identical to an existing one, every concept-graph patch should go through `concept.merge` with suggestions. The learner confirms merges; never auto-merge silently.
2. **Vocabulary scale.** For language subjects, use `vocab.yaml` as a compact bulk format, but each vocabulary entry must still have a stable synthetic Learning Object id for scheduling and mastery.
3. **Worked examples as content vs Learning Objects.** A worked example file is content; the pattern it teaches is a `worked_example_pattern` LO. Implement explicit two-way links: `lo.references_worked_example: <path>` and worked-example frontmatter `teaches_lo: <lo_id>`.
4. **Media references.** For VOD/motor subjects, MVP should store local media references and timestamps in `media-index.yaml`; no binary media is copied into the vault unless the user explicitly imports it.
5. **Predictive representation granularity.** MVP stores structured belief rows (LO scalar mastery, learner θ, error propensities) and derives predictive response distributions on demand. Later covariance tracking may help avoid double-counting correlated evidence families, but it is not required for the first implementation.
6. **FSRS modulation bounds.** The spec sets conservative default bounds, but implementation should expose config and tests for how surprise caps or stretches intervals.
7. **Domain migration policy.** Domain modules may add namespaced SQLite tables. Define how those migrations are versioned, validated, and disabled if a plugin is removed.
8. **Observation-to-attempt mapping.** Define which observation templates emit formal attempts automatically and which only update narrative logs until reviewed.
9. **Replay algorithm versions.** Define semantic versioning for learner-state algorithms so replay results are attributable and reproducible.

## Remaining interaction questions

10. **Answer input widget.** The TUI needs short inline answers, `$EDITOR` long answers, LaTeX-friendly math answers, and code-block answers. MVP can support inline + `$EDITOR`; rendering/sandboxing can follow.
11. **Recently Added review.** The TUI should show "Recently Added" after auto-accept events and expose deactivate/edit/open-lineage actions. The exact layout still needs a final design pass.
12. **Uncertainty dashboard.** MVP should expose `learnloop uncertainty` and "Why now?" explanations; richer charts can wait until dashboard work.
13. **Surprise follow-up UX.** Decide whether a high-surprise diagnostic follow-up interrupts the current queue immediately or is inserted as the next item after feedback.
14. **Domain-specific TUI panels.** Define the minimal panel contract for language conversation review and Overwatch VOD review without making the TUI framework domain-specific.
15. **Replay UX.** Decide whether replay is automatic after algorithm upgrades or a prompted/manual operation.

## Remaining operations questions

16. **Git policy.** Vaults should be git-friendly, but default behavior should be hands-off: do not autocommit unless `[storage].autocommit = true`.
17. **Privacy / telemetry.** Default policy: no product analytics. Local content leaves the machine only through explicit Codex/model calls initiated by the user or an AI-backed workflow.
18. **Media and telemetry privacy.** For VOD/esports domains, local media paths and optional telemetry should stay local by default; any model upload or automated analysis must be explicit.

# 27. Incorporated extensions

These were proposed earlier as "new ideas worth considering" and are now first-class in the spec. Quick map of where each lives:

| Idea | Spec home |
| --- | --- |
| Codex required for daily loop; degraded offline = review + self-grade + manual error tagging | §1, §3, §6 `[ai]`, §12 |
| Codex availability state machine, mid-attempt fallback, auto-regrade on recovery | §12 (state machine), §15.6 (mid-attempt fallback), §6 `[ai]`, §11 (`learnloop ai status/login/recheck`), `practice_attempts.manual_review_reason` |
| Vault-global concept IDs | §4 (`concepts/`), §8 (concept graph format with subject views) |
| Subjects as views (multi-subject LO/PI/note membership via `subjects: [list]`) | §4 (Subjects as views), §8 (per-subject derived view), §9 (LO/PI YAML), §7 (note frontmatter), §16 (`concept_mastery` concept-keyed) |
| Worked-example structure with two-way LO links and optional fadable steps | §15.8, §9 (`references_worked_examples`), `worked_example_views` table |
| Media-index hybrid hashing with fingerprint-based relocation | §15.9, `[media]` config |
| Observation templates with `emits_attempt` + `applies_to` predicate + deferred LO binding | §15.10 |
| Unified end-of-session review (ephemeral / pending grades / observation binding / generated cleanup) | §15.10 |
| Disguised-retest policy (cap 1, geometric intervals, reopen on 1 failure) | §15.7, `algorithm_priors.yaml` |
| Surprise follow-up insertion (next-position; positive surprise no-op) | §16 Layer 4 "Surprise follow-up insertion" |
| Replay banner cadence (once per session; 3-strike nudge; PATCH doctor-only) + `replay_banner_state` | §16, §11 |
| Algorithm semver bump definitions and `CHANGELOG.algorithm.md` | §16 "Behavior by bump type" |
| Hint-author validation+retry guardrails | §9 "Hint-author validation and retry" |
| Domain enable/disable/purge with dry-run + double-confirm | §4 "Domain enable / disable / purge", §11 |
| Answer widget (inline + $EDITOR, Markdown render, literal math) | §10 "Answer input widget" |
| Per-purpose Codex rate-limit behavior + tutor cache-and-resume | §12 (per-purpose table, tutor `pending_messages`) |
| Simulator-EIG proposer ephemeral-minimal output schema + validation | §16 Layer 4 "Proposer output schema and validation" |
| Tutor thread management (per-purpose lifetime, hybrid archival, `tutor-summarizer`) | §12 "Thread management" |
| Replay (a): drop-and-recompute with version-tagged snapshots + diff view | §16 (Replayable learner model), `replay_snapshots` table, `learnloop replay-model --diff` |
| Heuristic-bucket EIG MVP + Codex-simulator ephemeral diagnostic generation | §16 (Layer 4, "Two policy variants"), `[scheduler]` config, `elicitation_events.policy` |
| Hint ladder as first-class on Practice Items | §9 (PI YAML `hints` + `hint_policy`), §9 (Hint ladders subsection) |
| Local embedding index (sentence-transformers) | §4 (Local embedding index), §6 `[embeddings]`, `embeddings` table, §19 stack, §20 (`storage/embeddings.py`) |
| Tiered grader routing (exact-match / rubric-template / embedding-similarity / LLM) | §15.6 (Grader routing), `grading_evidence.grader_tier` |
| Fading worked-example sequence after `walkthrough` / `dont_know` | §16 (Fading worked-example sequence), `PracticeMode.faded_worked_example`, `faded_sequence_state` table |
| Structured `goals.yaml` sidecar for active_goal_importance and deadline_pressure | §4 (`profile/goals.yaml`), §7 (`profile/goals.yaml`) |
| Forgetting-curve view (`learnloop forgetting-curve`) | §10 (Forgetting curve), §11 CLI |
| End-of-session ephemeral promotion sweep with auto-rationale | §15.5 (End-of-session promotion sweep), `ephemeral_session_items` extra columns |
| Short-session mode (<20 min) | §10 (Short-session mode), §16 (Readiness modulation) |
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
| Adaptive elicitation / greedy EIG | §6 (`[scheduler]`), §16 (Layer 4), §16 SQLite tables (`elicitation_events`), §21 MVP |
| Stacked policy evaluation: simulated learners, held-out prediction, counterfactual policy fixtures, scheduler goldens | §15.6 ("Policy and predictive evaluation harness"), §4 (`evals/policy-goldens`, `replay-fixtures`, `simulated-learners`), §6 (`[evaluation]`), §11 (`learnloop eval policy`, `eval replay`, `eval simulate`), §20 (`policy_eval.py`, `simulated_learners.py`) |
| Bayesian surprise over joint observations | §6 (`[mastery]`), §16 (Layer 4 + `attempt_surprise`), §11 (`learnloop surprise`) |
| Single-user learner-state uncertainty | §1 (single-user/local), §16 (`learner_state_beliefs`), §20 (`beliefs.py`) |
| Belief staleness | §16 (Belief staleness), §16 SQLite table (`learner_state_beliefs`) |
| Replayable learner model | §16 (Replayable learner model), §11 (`learnloop replay-model`), §16 SQLite table (`model_replay_runs`) |
| Scheduler golden tests | §15.6 (Scheduler golden tests), §11 (`learnloop eval scheduler`), §4 (`evals/scheduler-goldens`) |
| Observation templates | §15.5 (Observation templates), §11 (`learnloop observe`), §16 SQLite tables (`observation_templates`, `observation_events`) |
| Three-tier latent: per-LO scalar mastery + per-learner θ over evidence families + derived axis views | §16 Layer 0 (learner profile), Layer 2 (LO scalar + axis-view aggregation), §16.5 (`EvidenceFamily`, `MasteryAxisView`) |
| Per-LO probe-mode diagnostic phase + background-claims init wizard | §16 Layer 4 ("Probe mode"), §17 (init wizard), §11 (`learnloop probes` / `claims`), `lo_probe_state` + `learner_claims` tables |
| Wang et al. 2025-informed shift: latent labels demoted to interpretable views, not primitive belief state, with predictive response distributions as the elicitation target | §16 intro, §16 Layer 2 ("Axis-view aggregation"), §16.5 (note on `MasteryAxisView` being derived), §16 Layer 4 ("Dual score representation") |
| Algorithm v2.0.0 migration (five-axis → scalar + θ profile) | §16 "Behavior by bump type" (v2.0.0 migration), `change_batches.reason = algorithm_major_v2` |
| EIG and surprise-modulation reliability ramp (per-LO and per-θ-family bottleneck) | §16 Layer 4 ("EIG and surprise-modulation reliability ramp"), `algorithm_priors.eig_reliability`, priority-formula multiplier, surprise follow-up Bernoulli gate, FSRS modulation blend |
| Hypothesis-based probe-EIG with authored `(domain, knowledge_type, practice_mode)` templates | §16 Layer 4 ("Probe mode and probe-EIG", "Probe hypothesis templates", "Hypothesis instantiation"), §16.5 (`CoarseHypothesisTemplate`, `PredictedObservation`, `HypothesisSet`), `prompts/probe_hypothesis_templates.yaml`, `DomainModule.probe_hypothesis_templates()` |
| Probe-EIG vs normal-EIG dispatch with low-reliability fallback to probe-EIG | §16 Layer 4 ("Probe-EIG vs normal-EIG dispatch"), `algorithm_priors.eig_reliability.fallback_to_probe_below` |
| Simulator-EIG unified on the local `HypothesisSet` (probe-phase fallback only in MVP) | §16 Layer 4 ("Simulator-EIG scope", "Hypothesis provider and simulator-EIG unification"), updated `SimulatorProposedItem` schema with `predicted_observations_by_hypothesis`, §6 `[scheduler].simulator_eig_context = "probe_phase_only"` |
| Generated diagnostic item quality gates from AQG/adaptive-testing research | §16 Layer 4 ("Proposer output schema and validation"), §6 (`[evaluation]` for downstream checks), §15.5 ephemeral promotion sweep |
| Manual deep-diagnostic CLI commands for normal-phase simulator-EIG | §11 (`learnloop diagnose-lo --deep`, `generate-diagnostic`, `uncertainty --suggest-probes`, `probes hypotheses`) |
| Extensible domain modules | §4 (Domain module contract), §6 (`[domains]`), §20 (`domains/registry.py`) |
| Domain capability flags | §4 (`DomainCapabilities`), §21 MVP |
| Language conversation tests | §4 (Language conversation domain), namespaced `language:*` practice modes |
| Overwatch-first esports/VOD review | §4 (Esports / Overwatch-first domain), `esports_overwatch.py`, namespaced `esports_overwatch:*` practice modes |
| Vault health checks and backups | §11.5 (`learnloop doctor`, `learnloop backup`) |
| Prompt/model provenance | §13 prompt frontmatter, §16 (`agent_runs`), §15.5 provenance fields |
| Session interruption/resume | §10 (Session resume), §16 (`session_checkpoints`), §6 (`[sessions]`) |
| First-run sample vault | §17 (`learnloop init --sample`), §20 (`templates/sample-vault`) |
