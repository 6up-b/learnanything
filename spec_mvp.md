# LearnLoop MVP Spec Delta

This file captures the MVP decisions resolved after the critical review of
`spec.md`, `edison_research.md`, and the Wang et al. adaptive elicitation
paper. It is intentionally narrower than `spec.md`: this is the implementation
target for the first build, not the full product roadmap.

## 1. MVP Scope

MVP includes:

- Local learning vault, schemas, and SQLite storage.
- Python Textual TUI, using the `textual` package from Textualize as the
  primary daily workflow surface.
- Learning Object and Practice Item authoring through Codex proposals.
- Codex-generated proposals from notes and canonical sources into proposed
  Learning Object / Practice Item patches.
- Codex-generated proposals that modify existing Learning Objects, Practice
  Items, and concept-graph state.
- Codex grading with structured evidence.
- Error attribution from grading.
- FSRS item scheduling.
- Deterministic scheduler.
- Probe-EIG only.
- Observation templates that can emit formal attempts automatically when the
  template declares that behavior.
- Negative-surprise follow-up insertion after feedback.

MVP excludes:

- Normal-EIG outside probe mode.
- Simulator-generated diagnostic items in the automatic scheduler.
- MCTS / lookahead scheduling.
- Full predictive-LM elicitation.
- Replay-model as a first-build gate.
- Policy evaluation harness as a first-build gate.
- Embeddings and semantic deduplication as required infrastructure.
- Rollback UX.
- Domain-specific TUI panels unless needed by a generic text workflow.

## 2. Project Scaffold

MVP implementation uses a normal Python package with a `src/` layout. The
application code, migrations, CLI, TUI, vault loader, repositories, scheduler,
grading, proposals, and Codex adapter live in this repository. The learning
vault is user data created by `learnloop init`.

Canonical repository scaffold:

```text
learnanything/
  pyproject.toml
  README.md
  spec.md
  spec_mvp.md
  migrations/
    001_initial.sql
  src/
    learnloop/
      __init__.py
      __main__.py
      cli.py
      config.py
      ids.py
      clock.py
      db/
        connection.py
        migrate.py
        repositories.py
      vault/
        hashes.py
        loader.py
        models.py
        paths.py
        yaml_io.py
      services/
        attempts.py
        fsrs.py
        grading.py
        mastery.py
        observations.py
        proposals.py
        scheduler.py
      codex/
        client.py
        prompts.py
        schemas.py
      tui/
        app.py
        screens/
          today.py
          practice.py
          feedback.py
  tests/
    fixtures/
      vaults/
        basic/
        scheduler_due_queue/
    test_*.py
```

Library commitments:

- Python 3.12 or newer.
- CLI uses `typer`; the console script is
  `learnloop = learnloop.cli:app`.
- TUI uses the `textual` package from Textualize.
- Typed config, YAML, proposal, and grading contracts use Pydantic v2.
- YAML reads and writes use `ruamel.yaml` so comments, ordering, and unknown
  keys can be preserved where practical.
- TOML reads use stdlib `tomllib`. MVP writes `learnloop.toml` only from a
  template during `init`; it does not round-trip arbitrary existing TOML.
- SQLite uses stdlib `sqlite3`; schema changes are executable SQL files under
  `migrations/`.
- Tests use `pytest`.
- FSRS is implemented locally in `services/fsrs.py` for deterministic behavior.
  Do not add an external FSRS runtime dependency in the first pass.

Boundary rules:

- CLI and Textual screens only parse input, render output, and call services.
- Services own scheduling, grading, attempt logging, mastery updates, proposal
  validation, and proposal application.
- Repositories own SQLite reads/writes only. They do not compute scheduling,
  grading, or mastery behavior.
- Vault writes go through `vault/yaml_io.py` and `services/proposals.py`.
  Codex never writes files directly.
- All clocks use `clock.py` so deterministic tests can freeze time without
  monkeypatching service internals.

## 3. Vault File Layout and YAML Schema

`learnloop init` creates a local vault. The vault is user data: Markdown and
YAML are editable by hand, while `state.sqlite` stores mutable computed state.

MVP vault layout:

```text
my-learning-vault/
  AGENTS.md
  learnloop.toml
  state.sqlite

  concepts/
    concepts.yaml
    relations.yaml

  profile/
    goals.md
    goals.yaml

  subjects/
    <subject-id>/
      subject.md
      concept-graph.yaml
      notes/
      learning-objects/
      practice-items/

  rubrics/
  errors/
    error_types.yaml
  prompts/
  sessions/
  exports/
  .learnloop/
    backups/
    session-checkpoints/
```

MVP loader rules:

- App-created YAML files include `schema_version: 1`.
- App-created Markdown files that need structured metadata use YAML
  frontmatter with `schema_version: 1`.
- Timestamps are ISO-8601 UTC strings.
- Subject IDs use kebab-case, for example `linear-algebra`.
- Concept IDs use snake_case, for example `singular_value_decomposition`.
- Learning Object IDs use the `lo_` prefix.
- Practice Item IDs use the `pi_` prefix.
- SQL row IDs use ULIDs and are generated app-side.
- YAML IDs are stable human-facing IDs and are unique within entity type.
- Subject membership is declared on Learning Objects and Practice Items.
  Folder location is only a convenience; `doctor` warns when the primary
  subject does not match the containing folder.
- Unknown YAML keys are preserved where practical and warned on by `doctor`
  when they look like misspellings of known keys.
- Derived learner state never lives in YAML. Attempts, mastery, FSRS state,
  scheduler explanations, proposal decisions, and Codex runs live in SQLite.
- `content_hash` is computed from normalized semantic fields, not from
  formatting, comments, `created_at`, `updated_at`, or local provenance notes.

### Vault Config

`learnloop.toml` is the vault-local config. MVP starts with this shape:

```toml
schema_version = 1

[storage]
sqlite_path = "state.sqlite"

[algorithms]
algorithm_version = "mvp-0.1"

[scheduler]
forgetting_risk_weight = 1.0
active_goal_weight = 0.35
recent_error_weight = 0.50
probe_eig_weight = 0.25
short_session_minutes = 20

[scheduler.surprise]
theta_pos = 1.5
theta_neg = 1.5
alpha_interval = 0.3
f_min = 0.5
f_max = 1.5
epsilon_error_surprise = 0.05

[scheduler.followup]
tau_followup_nats = 0.3
gamma_min = 0.5

[mastery]
base_observation_variance = 1.0
sigma2_drift = 0.01
p_max = 4.0

[probe]
attempts_target_default = 3
attempts_target_with_strong_claim = 1
claim_skip_threshold = 0.75
variance_convergence_threshold = 0.10
hypothesis_set_max_size = 5

[codex]
checkout_path = "../codex"
revision = "<pinned-commit>"
startup_command = "npm run app-server"
startup_timeout_seconds = 20
healthcheck_timeout_seconds = 5
auth_mode = "chatgpt"
```

### Goals

`profile/goals.yaml` is the structured source for the scheduler's
`active_goal` component.

```yaml
schema_version: 1
goals:
  - id: goal_linear_algebra_ml
    title: Linear algebra for ML
    status: active              # active | paused | completed
    priority: 0.8               # 0..1
    concept_anchors:
      - singular_value_decomposition
      - principal_components
    due_at: null
    created_at: 2026-05-19T00:00:00Z
    updated_at: 2026-05-19T00:00:00Z
```

If no active goal reaches an item through its concept, the item's
`active_goal` scheduler component is zero.

### Concepts

`concepts/concepts.yaml` is the vault-global concept registry. Concept IDs are
not subject-scoped.

```yaml
schema_version: 1
concepts:
  singular_value_decomposition:
    title: Singular Value Decomposition
    type: procedure              # concept | procedure | skill | misconception
    aliases:
      - SVD
    description: Matrix factorization into orthogonal factors and singular
      values.
    tags: []
    created_at: 2026-05-19T00:00:00Z
    updated_at: 2026-05-19T00:00:00Z
```

`concepts/relations.yaml` stores concept edges with explicit IDs so proposal
items, `show <id>`, and rollback can address edges unambiguously.

```yaml
schema_version: 1
edges:
  - id: edge_prerequisite_eigenvectors_singular_value_decomposition
    relation_type: prerequisite  # prerequisite | confusable_with | part_of | related
    source: eigenvectors
    target: singular_value_decomposition
    strength: 1.0
    rationale: null
    created_at: 2026-05-19T00:00:00Z
    updated_at: 2026-05-19T00:00:00Z
```

For symmetric relations such as `confusable_with`, the loader canonicalizes
`source` and `target` ordering when computing uniqueness.

### Subjects

`subjects/<subject-id>/subject.md` stores display metadata in frontmatter and
freeform narrative below it.

```markdown
---
schema_version: 1
id: linear-algebra
title: Linear Algebra
status: active
created_at: 2026-05-19T00:00:00Z
updated_at: 2026-05-19T00:00:00Z
---

# Linear Algebra

Purpose, scope, preferences, and notes for this subject.
```

`subjects/<subject-id>/concept-graph.yaml` is a subject view over the
vault-global concept graph.

```yaml
schema_version: 1
subject: linear-algebra
additional_concepts_in_scope: []
exclude_concepts: []
subject_ordering_hints:
  - eigenvectors
  - singular_value_decomposition
```

The resolved subject scope is derived at load time from Learning Object subject
tags, additional concepts, exclusions, and ordering hints.

### Notes

Notes are Markdown files under `subjects/<subject-id>/notes/`. App-created
notes include frontmatter. Manually added notes without frontmatter are allowed;
the loader infers the folder subject and uses a path-based source ID.

```markdown
---
schema_version: 1
id: note_svd_overview
subjects:
  - linear-algebra
related_los: []
related_concepts:
  - singular_value_decomposition
source_type: learner_note       # learner_note | canonical_source | imported
created_at: 2026-05-19T00:00:00Z
updated_at: 2026-05-19T00:00:00Z
---

# SVD overview

Notes and source excerpts.
```

Codex authoring proposals cite notes through `SourceRef` values that resolve to
note IDs, relative paths, and optional line or heading locators.

### Learning Objects

Learning Objects are YAML files under
`subjects/<primary-subject>/learning-objects/<lo_id>.yaml`.

```yaml
schema_version: 1
id: lo_svd_definition
title: Singular Value Decomposition definition
subjects:
  - linear-algebra
concept: singular_value_decomposition
knowledge_type: definition       # definition | fact | procedure | schema | proof | derivation | strategy | misconception | transfer_pattern
status: active                   # active | dormant | resolved
contradicts: null                # only set for misconception LOs
summary: >
  SVD factorizes a matrix into orthogonal factors and non-negative singular
  values.
prerequisites:
  - lo_orthogonal_matrices
confusables: []
difficulty_prior: 0.55
tags: []
provenance:
  origin: human                  # human | codex_proposal | canonical_extract | import
  source_refs: []
created_at: 2026-05-19T00:00:00Z
updated_at: 2026-05-19T00:00:00Z
```

Mastery estimates are not stored in Learning Object YAML.

### Practice Items

Practice Items are YAML files under
`subjects/<primary-subject>/practice-items/<pi_id>.yaml`.

```yaml
schema_version: 1
id: pi_svd_define_001
learning_object_id: lo_svd_definition
subjects: null                   # null means inherit from the Learning Object
practice_mode: short_answer      # short_answer | free_recall | explanation | worked_problem | proof | transfer
attempt_types_allowed:
  - independent_attempt
  - hinted_attempt
  - dont_know
  - diagnostic_probe
evidence_facets:
  - recall
  - schema
  - explanation
evidence_weights:
  recall: 0.40
  schema: 0.35
  explanation: 0.25
prompt: Define Singular Value Decomposition in your own words.
expected_answer: >
  A factorization of a matrix into orthogonal matrices and a diagonal matrix of
  non-negative singular values.
difficulty: 0.55
tags: []
hints:
  - Think about the three factors.
  - What kind of values are on the diagonal factor?
hint_policy:
  max_useful_hints: 2
  fsrs_rating_cap_by_hint:
    0: easy
    1: good
    2: hard
  mastery_alpha_dampening_by_hint:
    0: 1.0
    1: 0.75
    2: 0.5
grading_rubric:
  max_points: 4
  criteria:
    - id: factorization
      points: 1
      description: Mentions matrix factorization.
    - id: orthogonal_factors
      points: 1
      description: Mentions orthogonal or unitary factors.
    - id: singular_values
      points: 1
      description: Mentions non-negative singular values.
    - id: diagonal_factor
      points: 1
      description: Identifies the diagonal middle factor.
  fatal_errors:
    - id: says_eigendecomposition
      description: Treats SVD as identical to eigendecomposition.
      max_grade: 2
provenance:
  origin: human
  source_refs: []
created_at: 2026-05-19T00:00:00Z
updated_at: 2026-05-19T00:00:00Z
```

Practice Item content hashes include `learning_object_id`, `practice_mode`,
`attempt_types_allowed`, `evidence_facets`, `evidence_weights`, `prompt`,
`expected_answer`, `difficulty`, `hints`, `hint_policy`, and
`grading_rubric`. Tags and provenance do not affect scheduling state.

### Default Rubrics

Inline Practice Item rubrics are preferred for MVP. `rubrics/*.yaml` may define
defaults by practice mode when an item omits `grading_rubric`.

```yaml
schema_version: 1
id: rubric_short_answer_default
applies_to:
  practice_mode: short_answer
rubric:
  max_points: 4
  criteria:
    - id: correctness
      points: 3
      description: The answer states the core idea accurately.
    - id: clarity
      points: 1
      description: The answer is understandable and not self-contradictory.
  fatal_errors: []
```

### YAML Write Policy

Accepted proposal items compile into internal patch operations against these
schemas. The patch applier:

- validates all referenced IDs before writing;
- writes one content mutation per accepted proposal item;
- records the SQL `change_batches` and `content_events` rows before or within
  the same transaction boundary as the file mutation when possible;
- preserves unknown YAML keys where practical;
- recomputes affected content hashes after a successful write;
- never lets Codex specify an arbitrary path.

## 4. Codex Dependency

MVP intentionally depends on an experimental local Codex setup.

Implementation assumption:

- LearnLoop requires a local Codex checkout pinned to a known revision.
- LearnLoop uses the experimental local Codex app-server / SDK flow against
  that pinned checkout.
- This is an explicit MVP prerequisite.
- Portability to other Codex runtimes or APIs is deferred.

Spec correction:

- Remove or rewrite any claim that MVP must not depend on a local Codex
  checkout.

`learnloop.toml` includes a dedicated Codex runtime block:

```toml
[codex]
checkout_path = "../codex"
revision = "<pinned-commit>"
startup_command = "npm run app-server"
startup_timeout_seconds = 20
healthcheck_timeout_seconds = 5
auth_mode = "chatgpt"
```

MVP startup behavior:

- If `checkout_path` is missing, LearnLoop reports `codex_missing` and disables
  Codex-backed authoring/grading until fixed.
- If the checkout revision does not match `revision`, LearnLoop reports
  `codex_revision_mismatch` and refuses Codex-backed writes by default.
- If startup or health check times out, LearnLoop reports `codex_unavailable`
  and keeps the local vault usable for non-Codex actions.
- Authentication failures report `codex_auth_required`.

MVP adapter surface:

```python
class CodexClient(Protocol):
    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal: ...
    def run_grading_proposal(self, context: GradingContext) -> GradingProposal: ...
```

Tutor streaming and simulator-style generation are not part of the MVP adapter
surface.

## 5. Codex Proposal Contract

MVP uses a hybrid proposal contract.

Codex returns typed proposal objects. LearnLoop validates those objects against
current vault state, converts accepted proposals into internal patch
operations, and applies those operations through LearnLoop-owned storage code.

Codex must not directly emit authoritative file writes.

Authoring proposal objects may include:

- `learning_object_changes`
- `practice_item_changes`
- `concept_graph_changes`
- `source_refs`

Grading proposal objects include:

- `rubric_score`
- `criterion_evidence`
- `error_attributions`
- `grader_confidence`
- optional `repair_suggestions`

Internal patch operations are responsible for atomic application, provenance,
content events, and future rollback support.

Pending and reviewed proposal state lives in a dedicated `proposed_patches`
table. `content_events` records applied or reviewed content lifecycle events;
it does not store the proposal object itself.

Proposal storage uses two tables:

- `proposed_patches`: one row per Codex proposal batch, with batch metadata,
  `agent_run_id`, and a derived overall status.
- `proposed_patch_items`: one row per proposed Learning Object, Practice Item,
  concept edge, rubric, or related content change.

Per-item decision state is the source of truth. Batch status is derived from
its items, not manually maintained as authoritative state.

Each `proposed_patch_items` row stores:

- the original Codex proposal payload,
- `edited_payload`, for learner modifications before acceptance,
- the item-level decision state,
- `applied_change_batch_id`, set only after acceptance.

Acceptance mutates state and writes or joins a `change_batches` row for the
actual content mutation. Rejection only changes proposal item state and has no
content side effect. The applied `change_batches` row references the
`proposed_patch_items.id`, not only the parent patch id, so provenance and
rollback granularity match the accepted item.

Each accepted proposal item writes its own `change_batches` row, even when the
learner accepts several items in one bulk action. `change_batches.proposed_patch_item_id`
is nullable so manual edits and imports can still use change batches without a
proposal.

## 6. Typed Proposal Schemas

Codex outputs typed JSON proposals. LearnLoop validates those proposals,
persists them as proposal items, and compiles accepted items into internal patch
operations. Codex never emits raw file writes, raw SQL, or arbitrary paths as
authoritative mutations.

### Shared Types

```python
EntityType = Literal[
    "learning_object",
    "practice_item",
    "concept",
    "concept_edge",
    "rubric",
    "error_type",
]

ProposalOperation = Literal["create", "update", "deactivate"]

ReviewRoute = Literal["auto_apply", "review_required", "reject"]

class SourceRef(BaseModel):
    ref_type: Literal[
        "note",
        "canonical_source",
        "existing_entity",
        "session",
        "manual_context",
    ]
    ref_id: str
    path: str | None = None
    locator: str | None = None       # heading, paragraph id, page, timestamp, etc.
    quote: str | None = None         # short grounding excerpt when useful
    quote_hash: str | None = None    # hash of the cited source span when available

class TargetEntity(BaseModel):
    entity_type: EntityType
    entity_id: str
```

### Authoring Proposal

`AuthoringProposal` is the only MVP schema Codex uses for content authoring and
content modification.

```python
class AuthoringProposal(BaseModel):
    summary: str
    source_refs: list[SourceRef]
    items: list[AuthoringProposalItem]

class AuthoringProposalItem(BaseModel):
    client_item_id: str              # stable within this proposal response
    item_type: EntityType
    operation: ProposalOperation
    target: TargetEntity | None      # required for update/deactivate
    proposed_entity_id: str | None   # required for create unless payload owns id
    source_ref_ids: list[str]
    rationale: str
    review_route: ReviewRoute
    payload: (
        LearningObjectPatchPayload
        | PracticeItemPatchPayload
        | ConceptPatchPayload
        | ConceptEdgePatchPayload
        | RubricPatchPayload
        | ErrorTypePatchPayload
    )
```

Validation rules:

- `source_ref_ids` must refer to entries in `AuthoringProposal.source_refs`.
- `target` is required for `update` and `deactivate`.
- `target` is forbidden for `create`, except when creating an edge whose
  endpoints are existing entities.
- `review_route = auto_apply` is allowed only for direct source-grounded
  extraction that passes schema validation and source-ref resolution.
- `review_route = reject` is advisory only. LearnLoop still persists the item
  as rejected or invalid so the run is auditable.
- Codex may propose IDs, but LearnLoop owns final collision checks and may
  require edit before acceptance.

### Authoring Payloads

Payloads are typed by entity. For `update`, omitted optional fields mean
"leave unchanged." For `create`, required fields must be complete enough for
LearnLoop to write the YAML entity without another model call.

```python
class LearningObjectPatchPayload(BaseModel):
    id: str | None = None
    title: str | None = None
    concept_id: str | None = None
    subjects: list[str] | None = None
    knowledge_type: str | None = None
    status: Literal["active", "dormant", "resolved"] | None = None
    contradicts: str | None = None
    summary: str | None = None
    prerequisites: list[str] | None = None
    confusables: list[str] | None = None
    difficulty_prior: float | None = None
    tags: list[str] | None = None

class PracticeItemPatchPayload(BaseModel):
    id: str | None = None
    learning_object_id: str | None = None
    subjects: list[str] | None = None
    practice_mode: str | None = None
    attempt_types_allowed: list[str] | None = None
    prompt: str | None = None
    expected_answer: str | dict | None = None
    grading_rubric: RubricPatchPayload | None = None
    evidence_facets: list[str] | None = None
    evidence_weights: dict[str, float] | None = None
    difficulty: float | None = None
    hints: list[str] | None = None
    hint_policy: dict | None = None
    tags: list[str] | None = None

class ConceptPatchPayload(BaseModel):
    id: str | None = None
    title: str | None = None
    type: Literal["concept", "procedure", "skill", "misconception"] | None = None
    aliases: list[str] | None = None
    description: str | None = None
    tags: list[str] | None = None

class ConceptEdgePatchPayload(BaseModel):
    source_concept_id: str
    target_concept_id: str
    relation_type: Literal[
        "prerequisite",
        "confusable_with",
        "part_of",
        "related",
    ]
    strength: float | None = None
    rationale: str | None = None

class RubricCriterionPayload(BaseModel):
    id: str
    points: float
    description: str

class RubricFatalErrorPayload(BaseModel):
    id: str
    description: str
    max_grade: int

class RubricPatchPayload(BaseModel):
    target_practice_item_id: str | None = None
    max_points: int = 4
    criteria: list[RubricCriterionPayload]
    fatal_errors: list[RubricFatalErrorPayload] = []

class ErrorTypePatchPayload(BaseModel):
    id: str | None = None
    title: str | None = None
    description: str | None = None
    related_concepts: list[str] | None = None
    severity_default: float | None = None
    is_misconception: bool | None = None
    tags: list[str] | None = None
```

### Grading Proposal

`GradingProposal` is the only MVP schema Codex uses for grading. LearnLoop
derives correctness, FSRS rating, mastery updates, surprise, and scheduling
effects from the validated grade and attempt context.

```python
class GradingProposal(BaseModel):
    attempt_id: str
    practice_item_id: str
    rubric_score: int                 # 0..4
    criterion_evidence: list[CriterionEvidence]
    fatal_errors: list[str] = []
    error_attributions: list[ErrorAttribution] = []
    grader_confidence: float          # 0..1, confidence in the judgment
    manual_review_recommended: bool = False
    feedback_md: str | None = None
    repair_suggestions: list[RepairSuggestion] = []

class CriterionEvidence(BaseModel):
    criterion_id: str
    points_awarded: float
    evidence: str
    notes: str | None = None

class ErrorAttribution(BaseModel):
    error_type: str
    severity: float                   # 0..1
    evidence: str
    is_misconception: bool = False
    target_evidence_families: list[str] = []

class RepairSuggestion(BaseModel):
    practice_mode: str
    learning_object_id: str | None = None
    rationale: str
```

Validation rules:

- `attempt_id` and `practice_item_id` must match the grading request.
- `rubric_score` must be an integer in `[0, 4]`.
- Criterion IDs must exist in the resolved rubric.
- Points may not exceed the criterion max.
- Fatal errors must exist in the resolved rubric and cap the score.
- `grader_confidence < grader_confidence_floor` triggers manual review before
  mastery updates.
- Error attributions must resolve to the vault or domain error taxonomy, or
  route through review as a proposed taxonomy addition.

### Internal Patch Operations

Codex does not output these. LearnLoop compiles accepted proposal items into
internal operations.

```python
PatchOperationKind = Literal[
    "create_yaml_entity",
    "update_yaml_entity",
    "deactivate_entity",
    "upsert_concept_edge",
    "upsert_rubric",
    "record_grading_evidence",
    "record_error_event",
]

class PatchOperation(BaseModel):
    kind: PatchOperationKind
    target: TargetEntity
    payload: dict
    source_proposed_patch_item_id: str | None = None
```

Compilation rules:

- One accepted `AuthoringProposalItem` compiles into one or more
  `PatchOperation`s.
- LearnLoop derives vault paths from `target.entity_type` and IDs. Codex output
  cannot choose arbitrary write paths.
- The applied payload is `edited_payload_json` when present, otherwise
  `payload_json`.
- Each accepted proposal item creates one `change_batches` row and one or more
  `content_events` rows.
- Rejected proposal items create no `PatchOperation`s and no content events,
  unless the UI explicitly records a review audit event later.

## 7. Proposal Review Policy

MVP uses an auto-apply-low-risk policy.

Auto-apply:

- Direct source-grounded Learning Object / Practice Item extraction from notes
  or canonical sources.
- Only when source refs resolve and schema validation passes.

Review required:

- Modifications to existing Learning Objects.
- Modifications to existing Practice Items.
- Modifications to concept-graph state.
- Transfer items.
- Misconception and error items.
- Proof and derivation items.
- Any proposal with weak grounding or validator warnings.

Never apply:

- Unresolved source refs.
- Duplicate IDs.
- Invalid concept edges.
- Missing rubrics where grading requires a rubric.
- Failed schema validation.

## 8. Probe-EIG Boundary

MVP EIG means probe-EIG only.

New active-goal Learning Objects enter a probe phase before steady-state
scheduling. Probe defaults live in `[probe]` of `learnloop.toml`; see §14.4 for
the algorithm.

Mature Learning Objects do not use normal-EIG in MVP. They use deterministic
non-EIG scheduling terms (FSRS forgetting risk, active-goal importance, recent
errors); see §14.3.

Probe-EIG candidate source:

- MVP selects only from the existing Practice Item pool.
- If the pool is inadequate, the scheduler logs the coverage gap (writes an
  `elicitation_events` row with `trigger = 'probe_phase_local_pi_inadequate'`
  and `fallback_outcome = 'existing_pi_inadequate'`).
- Codex generation is handled before scheduling through authoring proposals,
  not as an automatic mid-queue scheduler action.

Hypothesis sets are auto-derived from current state (mastery posterior +
active `error_events` + `confusable_with` neighbors), persisted in the
`hypothesis_sets` table, and **locked** for the duration of a probe phase.
The probe phase recomputes `H` only on re-entry. The outcome space is
`o = (score_bucket, error_type | null)` with `score_bucket ∈ {low: 0-1,
mid: 2-3, high: 4}`. `P(o | h, item)` is deterministic from the hypothesis
label and the item's rubric `fatal_errors`. See §14.4 for the closed-form
EIG, prior construction, conditional distributions, and observation bridge.

## 9. Observation Templates

Observation templates can emit formal attempts automatically in MVP.

Rules:

- Emission behavior is declared by the template.
- Templates specify the attempt semantics they emit.
- Ambiguous Learning Object / Practice Item binding requires confirmation or
  lands in `pending`.
- LearnLoop must not silently guess ambiguous bindings.

## 10. Surprise Follow-Up UX

Negative-surprise diagnostic follow-ups insert after feedback.

Flow:

1. Current attempt completes; grading and mastery update run synchronously.
2. The Kalman-innovation surprise quantities are computed and persisted to
   `attempt_surprise` (see §14.5).
3. Feedback screen is shown normally and is never interrupted.
4. After the learner dismisses feedback, the gate fires the follow-up if all of:
   - `surprise_direction == 'negative'`
   - `bayesian_surprise > tau_followup_nats`
   - a new `error_events` row was written for this attempt
   - `practice_attempts.grader_confidence >= gamma_min`
   - the session still has available minutes
5. When fired, the follow-up PI is chosen from the same `learning_object_id`
   pool: ranked by `probe_eig` if the LO is in a probe phase, else by
   `recent_error`. It is inserted at position 1 of the remaining queue.
6. `attempt_surprise.triggered_actions_json` records the action; if blocked by
   the minutes check, `suppressed_actions_json` records the suppression with a
   reason suffix (`negative_surprise_followup:no_time`).

The `surprise_direction` enum value `mixed` is reserved but not emitted in MVP.
The error-type surprise channel (see §14.5) can force `negative` even when the
score residual `r` is small, when the observed error_type is rare under the
prior.

## 11. Canonical SQLite Schema Policy

The spec should have one authoritative `Canonical SQLite Schema` section.
Earlier SQL snippets are illustrative and must conform to the canonical schema.

The executable MVP schema is `migrations/001_initial.sql`. This section is the
human-readable schema contract; the migration is what the app runs. If this
section and the migration disagree, treat it as a spec bug and update them
together.

`spec.md`'s broader SQLite block is forward-looking. For MVP implementation,
use this file plus `migrations/001_initial.sql`.

### DDL Conventions

- Primary keys are `TEXT` ULIDs generated app-side.
- Timestamps are ISO-8601 UTC `TEXT`.
- `created_at` is `NOT NULL`; `updated_at` appears only on mutable rows.
- JSON columns end in `_json` and are stored as `TEXT`.
- Booleans are `INTEGER` with `0/1` checks.
- YAML-owned IDs use soft references validated at write time. This includes
  `learning_object_id`, `practice_item_id`, `concept`, and `subject`.
- Hard foreign keys are used only where both sides are SQL-owned and share a
  lifecycle: `grading_evidence.attempt_id -> practice_attempts.id`,
  `proposed_patch_items.proposed_patch_id -> proposed_patches.id`, and
  `attempt_surprise.attempt_id -> practice_attempts.id`.
- `algorithm_version` is stamped on derived rows:
  `learning_object_mastery`, `learner_theta`, `lo_probe_state`,
  `learner_state_beliefs`, `attempt_surprise`, and `scheduler_explanations`.
- Nullability is explicit. Columns are nullable unless they are structurally
  required for the MVP flow.
- SQL-owned enum-ish fields use `CHECK` constraints where practical. YAML-owned
  values stay app-validated so local YAML edits do not brick SQLite.
- The CHECK lists for `item_type`, `target_entity_type` (on
  `proposed_patch_items`) and `entity_type` (on `content_events`) include
  `error_type` in MVP.
- `content_events.event_type` includes `created`, `updated`, `deactivated`,
  `regrade_disagreement`, and `algorithm_version_bumped`.

### DDL Trim Rule

A column ships in MVP DDL only if it is read or written by:

`init -> propose -> accept -> attempt -> grade -> attribute error -> update FSRS/mastery -> schedule next probe`

Deferred feature columns are added later through `ALTER TABLE ADD COLUMN`
migrations. In MVP, for example:

- `attempt_surprise.predicted_latency_dist_json` is omitted.
- `attempt_surprise.predicted_hints_dist_json` is omitted.
- `practice_attempts.step_trace_json` is omitted.
- `elicitation_events.policy` exists but only accepts `probe_eig`.
- `learner_state_beliefs.scope_type` is restricted to `error_type` and
  `misconception`.

Raw cheap evidence is still retained when captured. For example,
`practice_attempts.latency_seconds` and `practice_attempts.hints_used` remain in
MVP even though latency/hints prediction heads are deferred.

### Canonical Column Lists

These column lists mirror `migrations/001_initial.sql`.

#### Migration / AI / Proposal Tables

- `schema_migrations`: `version`, `name`, `applied_at`.
- `agent_runs`: `id`, `purpose`, `model`, `provider`, `prompt_template`,
  `prompt_version`, `sdk_version`, `codex_revision`, `input_context_hash`,
  `output_schema`, `started_at`, `completed_at`, `status`, `error_message`.
- `proposed_patches`: `id`, `agent_run_id`, `purpose`, `source_refs_json`,
  `summary`, `status_cache`, `created_at`, `updated_at`.
- `proposed_patch_items`: `id`, `proposed_patch_id`, `client_item_id`,
  `item_type`, `operation`, `target_entity_type`, `target_entity_id`,
  `payload_json`, `edited_payload_json`, `decision`, `validation_status`,
  `validation_errors_json`, `applied_change_batch_id`, `decided_at`,
  `decided_by`, `created_at`, `updated_at`.
- `change_batches`: `id`, `proposed_patch_item_id`, `reason`, `origin`,
  `summary`, `created_at`.
- `content_events`: `id`, `change_batch_id`, `event_type`, `subject`,
  `entity_type`, `entity_id`, `origin`, `review_status`, `summary`,
  `created_at`.

Proposal indexes:

- `idx_proposed_patch_items_decision` on
  `(proposed_patch_id, decision)`.
- `idx_change_batches_proposal_item` unique on `proposed_patch_item_id` where
  non-null.
- `idx_content_events_recent` on `(created_at, event_type)`.

#### Attempts / Grading / Error Tables

- `practice_attempts`: `id`, `practice_item_id`, `learning_object_id`,
  `subject`, `concept`, `practice_mode`, `attempt_type`, `learner_answer_md`,
  `evidence_facets_json`, `evidence_weights_json`, `rubric_score`,
  `correctness`, `confidence`, `latency_seconds`, `hints_used`, `error_type`,
  `grader_confidence`, `manual_review`, `manual_review_reason`, `created_at`,
  `updated_at`.
- `grading_evidence`: `id`, `attempt_id`, `criterion_id`, `points_awarded`,
  `evidence`, `notes`, `agent_run_id`, `local_grader_id`, `grader_tier`,
  `created_at`, `superseded_at`, `superseded_by_evidence_id`.
- `error_events`: `id`, `attempt_id`, `learning_object_id`, `error_type`,
  `severity`, `is_misconception`, `repair_plan_json`, `status`, `created_at`,
  `updated_at`.
- `attempt_surprise`: `attempt_id`, `predicted_score_dist_json`,
  `predicted_error_type_dist_json`, `observed_joint_bucket_json`,
  `predictive_surprise`, `bayesian_surprise`, `surprise_direction`,
  `fsrs_interval_factor`, `posterior_delta_json`, `triggered_actions_json`,
  `suppressed_actions_json`, `algorithm_version`, `created_at`.

Attempt indexes:

- `idx_attempts_lo_time` on `(learning_object_id, created_at)`.
- `idx_attempts_item_time` on `(practice_item_id, created_at)`.
- `idx_grading_evidence_attempt` on `attempt_id`.
- `idx_error_events_status` on `(status, learning_object_id)`.

#### Scheduling / Belief Tables

- `practice_item_state`: `practice_item_id`, `difficulty`, `stability`,
  `retrievability`, `due_at`, `active`, `content_hash`, `last_attempt_at`,
  `updated_at`.
- `learning_object_mastery`: `learning_object_id`, `logit_mean`,
  `logit_variance`, `evidence_count`, `last_evidence_at`,
  `algorithm_version`, `updated_at`. Display values `mastery_mean = σ(logit_mean)`
  and `mastery_variance = (m·(1-m))² · logit_variance` are computed on read in
  `services/mastery.py`; they are NOT stored.
- `learner_theta`: `id`, `domain`, `evidence_family`, `practice_mode`,
  `theta_mean`, `theta_variance`, `evidence_count`, `prior_pseudo_count`,
  `algorithm_version`, `updated_at`.
- `learner_claims`: `id`, `claim_type`, `scope_type`, `scope_id`,
  `evidence_family`, `claimed_level`, `prior_pseudo_count`, `source`,
  `created_at`.
- `lo_probe_state`: `learning_object_id`, `status`, `probe_phase_id`,
  `hypothesis_set_id`, `probe_attempts_completed`, `probe_attempts_target`,
  `families_converged_json`, `entered_at`, `completed_at`,
  `algorithm_version`, `updated_at`.
- `hypothesis_sets`: `id`, `learning_object_id`, `probe_phase_id`,
  `hypotheses_json` (ordered list of `{label, source_error_event_id?,
  source_concept_id?, severity_at_entry}`), `prior_json`,
  `algorithm_version`, `created_at`. One row per probe-phase entry; locked for
  the duration of the phase.
- `learner_state_beliefs`: `id`, `subject`, `scope_type`, `scope_id`,
  `belief_key`, `mean`, `variance`, `evidence_count`, `last_surprise`,
  `last_evidence_at`, `stale_after_days`, `algorithm_version`, `updated_at`.
- `elicitation_events`: `id`, `session_id`, `selected_practice_item_id`,
  `target_scope_json`, `policy`, `candidate_scores_json`, `entropy_before`,
  `expected_information_gain`, `selected_reason`, `hypothesis_set_id`,
  `hypothesis_set_json`, `trigger`, `fallback_outcome`, `created_at`.
- `scheduler_explanations`: `id`, `session_id`, `practice_item_id`,
  `selected_mode`, `priority`, `components_json`, `readiness_factor`,
  `expected_information_gain`, `target_scope_json`, `plain_english_json`,
  `algorithm_version`, `created_at`.

Scheduling indexes:

- `idx_item_state_due` on `(active, due_at)`.
- `idx_learner_theta_unique` on
  `(domain, evidence_family, COALESCE(practice_mode, ''))`.
- `idx_learner_state_beliefs_unique` on
  `(COALESCE(subject, ''), scope_type, scope_id, belief_key)`.
- `idx_learner_state_beliefs_scope` on `(subject, scope_type, scope_id)`.
- `idx_elicitation_events_session` on
  `(session_id, selected_practice_item_id)`.
- `idx_scheduler_explanations_session` on `(session_id, practice_item_id)`.

#### Session / Observation Tables

- `sessions`: `id`, `started_at`, `ended_at`, `energy`, `sleep_quality`,
  `available_minutes`, `notes_md_path`, `updated_at`.
- `session_checkpoints`: `session_id`, `current_practice_item_id`,
  `current_answer`, `focus_block_state_json`, `pending_grading_proposal_json`,
  `readiness_json`, `updated_at`.
- `observation_templates`: `id`, `domain`, `version`, `title`,
  `template_yaml`, `emits_attempt`, `active`, `created_at`, `updated_at`.
- `observation_events`: `id`, `template_id`, `subject`, `session_id`,
  `related_learning_object_id`, `related_practice_item_id`, `binding_mode`,
  `response_json`, `emitted_attempt_id`, `template_version`, `created_at`.

Observation index:

- `idx_observation_events_subject` on `(subject, created_at)`.

MVP canonical tables:

- `schema_migrations`
- `practice_attempts`
- `grading_evidence`
- `practice_item_state`
- `learning_object_mastery`
- `learner_theta`
- `learner_claims`
- `lo_probe_state`
- `hypothesis_sets`
- `learner_state_beliefs`
- `error_events`
- `attempt_surprise`
- `elicitation_events`
- `scheduler_explanations`
- `sessions`
- `session_checkpoints`
- `observation_templates`
- `observation_events`
- `agent_runs`
- `proposed_patches`
- `proposed_patch_items`
- `content_events`
- `change_batches`

Defer from MVP canonical schema:

- `policy_eval_runs`
- `policy_eval_results`
- `model_replay_runs`
- `replay_banner_state`
- `replay_snapshots`
- `embeddings`
- `ephemeral_session_items`
- `generated_items`, unless a future variant-generator flow needs a separate
  AI-content registry with behavior not covered by proposal lineage
- `worked_example_views`
- `faded_sequence_state`
- `tutor_pending_messages`
- `tutor_threads`
- `tutor_thread_archives`
- `attempt_propagation_events`, unless cross-LO propagation becomes MVP
- `file_change_preimages`, until rollback is implemented

Schema inclusion rule:

If a table is required for `init -> generate proposal -> accept LO/PI patch ->
attempt -> grade -> attribute error -> update FSRS/mastery -> schedule next
probe`, it is MVP canonical. Everything else is deferred.

## 12. MVP Build Path

CLI and Textual are both first-class MVP surfaces. The CLI is not just a
developer escape hatch; it must expose the same core workflows in scriptable
form. Textual is the primary daily interaction surface.

Build in this order:

1. Storage foundation: migrations, repositories, vault loader, YAML parsers,
   and content-hash plumbing.
2. Deterministic core services: attempt logging, FSRS item state, scalar
   Learning Object mastery, and priority score without EIG components
   (`forgetting_risk`, active-goal importance, and recent-error boost).
3. CLI parity for those deterministic services.
4. Scheduler golden tests against fixture vaults. These run without Codex and
   must be deterministic.
5. One-day Textual spike: a bare today-loop screen reading the same services,
   used to validate Textual async/state assumptions before deeper TUI work.
6. Full Textual today loop, practice screen, and feedback screen.
7. Codex adapter plus `agent_runs`, `proposed_patches`, and
   `proposed_patch_items` persistence.
8. Codex grading with self-grade fallback wired through the same attempt and
   grading services.
9. Codex proposal authoring for Learning Object, Practice Item, concept,
   concept-edge, and rubric patches through the proposal workflow.
10. Probe-EIG: `learner_theta`, `lo_probe_state`, hypothesis templates, pool-only
    probe scoring, and coverage-gap logging. Verify against fixture vaults and
    local attempt histories so scoring pathologies are caught before broader use.
11. Observation templates, negative-surprise follow-up insertion, and
    `learnloop doctor` coverage expansion.

Implementation rule: Textual and CLI call the same service layer. Neither
surface owns scheduling, grading, proposal application, or mastery update
logic.

### MVP CLI Surface

The MVP CLI is a first-class surface with this required command set:

```text
learnloop init
learnloop add-subject
learnloop add-note
learnloop propose
learnloop proposals
learnloop accept
learnloop reject
learnloop attempt
learnloop review
learnloop why
learnloop show
learnloop doctor
learnloop today
```

Command responsibilities:

- `learnloop init`: create a vault and initial config.
- `learnloop add-subject`: add a subject view and minimal subject metadata.
- `learnloop add-note`: add or register note/source material for later
  proposal generation.
- `learnloop propose`: run Codex authoring proposal generation from selected
  notes/sources/context.
- `learnloop proposals`: list proposal batches and item-level decisions.
- `learnloop accept <patch_id> [--items <item_id,item_id,...>]`: accept every
  pending item in a proposal batch, or only the listed item IDs.
- `learnloop reject <patch_id> [--items <item_id,item_id,...>]`: reject every
  pending item in a proposal batch, or only the listed item IDs.
- `learnloop attempt <practice_item_id>`: run an attempt through the same
  attempt/grading services used by the TUI.
- `learnloop review`: print the current due queue with one-line "why" summaries
  per item. This is the CLI mirror of the Textual today queue and the headless
  verification path for scheduler state.
- `learnloop why <practice_item_id>`: print the scheduler explanation for a
  queued or recently queued item.
- `learnloop show <id>`: universal inspector for Learning Objects, Practice
  Items, concepts, attempts, proposal batches, proposal items, change batches,
  and other IDs as the system grows.
- `learnloop doctor`: validate vault structure, YAML content, schema health,
  proposal coverage gaps, and scheduler prerequisites.
- `learnloop today`: launch the Textual today loop.

`learnloop grade` is not an MVP command. Normal attempts auto-grade through
Codex when available and use self-grade fallback when needed. Deferred
Codex-backed regrade runs automatically on Codex recovery. Manual grade
override can be added later as a narrow command when the override workflow is
fully specified.

Deferred commands:

- `learnloop ai status`
- `learnloop probes status`
- `learnloop errors`
- `learnloop inbox recent`
- `learnloop forgetting-curve`
- `learnloop lineage`
- `learnloop replay-model`
- `learnloop eval *`

The universal `show` command covers most early inspection needs without adding
many specialized commands before the workflows are mature.

## 13. Remaining MVP Decisions

The formerly-listed hard decisions on FSRS, mastery updates, scheduler priority
components, probe-EIG, surprise, self-grade fallback, and the error-type
taxonomy are resolved in §14.

Decisions still worth resolving before broad feature work, but not blockers:

- CLI output contracts for `review`, `show`, `why`, and `proposals`, including
  the `--json` shapes used by golden tests.
- Concrete `learnloop doctor` check list.
- Content-hash field lists for Learning Objects, concepts, concept edges, and
  rubrics (PI hash fields are pinned in §3).
- Codex transport contract against the local app-server (RPC vs HTTP, message
  shapes, healthcheck endpoint).

Domain migration policy and replay algorithm versioning are not first-build
blockers under the current MVP scope.

## 14. Algorithmic Constants and Default Formulas

This section pins the numerical contracts the deterministic services depend on.
Constants live in `learnloop.toml`; formulas live in `services/`. Changing any
value here is a versioned event that bumps `[algorithms] algorithm_version`.

### 14.1 FSRS

`services/fsrs.py` implements **FSRS-6** with the published default weights.

- Rating space: `{Again, Hard, Good, Easy} = {1, 2, 3, 4}`.
- Source: open-spaced-repetition reference implementation; the 21-value default
  weights array is pinned as a `FSRS6_DEFAULT_WEIGHTS` constant in
  `services/fsrs.py` along with the source commit SHA in a comment.
- Retrievability `R(t)` follows the FSRS-6 forgetting curve given the item's
  `stability` and elapsed time `t` (in days) since the last attempt.
- `hint_policy.fsrs_rating_cap_by_hint` caps the rating fed into FSRS by the
  number of hints used (string keys `easy`/`good`/`hard`/`again` map to 4/3/2/1
  respectively).

### 14.2 Mastery Model (logit-space Kalman)

Per-LO mastery is a scalar latent `x = logit(m)`, `x ~ N(μ, P)`. SQL stores
`logit_mean` and `logit_variance` directly. Display values are computed on
read in `services/mastery.py`:

```
mastery_mean     = σ(μ)
mastery_variance = (m · (1 - m))² · P     where m = mastery_mean
```

**Initial prior**:

- Default: `μ₀ = 0`, `P₀ = 1.0`.
- If a `learner_claims` row covers this LO at
  `claimed_level ≥ probe.claim_skip_threshold`:
  `μ₀ = logit(clamp(claimed_level, 0.02, 0.98))`,
  `P₀ = 1 / max(prior_pseudo_count, 0.25)`.

**Observation per attempt**:

```
y       = clamp(rubric_score / max_points, 0.02, 0.98)
z_obs   = logit(y)
weight  = evidence_coverage × hint_dampening × grader_confidence × attempt_type_factor
R       = base_observation_variance / max(weight, 0.10)
P_pred  = min(P + sigma2_drift · days_since_last_attempt, p_max)
K       = P_pred / (P_pred + R)
μ_new   = μ + K · (z_obs - μ)
P_new   = (1 - K) · P_pred
```

**Evidence-weight components**:

| term | definition | range |
|---|---|---|
| `evidence_coverage` | Σ `evidence_weights[facet]` over facets whose criteria scored ≥ 1 point | [0, 1] |
| `hint_dampening` | `hint_policy.mastery_alpha_dampening_by_hint[hints_used]`, default 1.0 | [0, 1] |
| `grader_confidence` | from `practice_attempts.grader_confidence` | [0, 1] |
| `attempt_type_factor` | from table 14.2.A | [0, 1] |

**Table 14.2.A — `attempt_type_factor`**:

| attempt_type | factor | note |
|---|---|---|
| `independent_attempt` | 1.0 | |
| `diagnostic_probe` | 1.0 | |
| `hinted_attempt` | 1.0 | weight reduction folded into `hint_dampening` |
| `reconstruction_after_walkthrough` | 0.5 | |
| `dont_know` | 0.7 | `rubric_score` forced to 0 |
| `self_report` | 0.3 | |
| `guided_walkthrough` | 0.0 | no `practice_attempts` row written |
| `skip` | 0.0 | no `practice_attempts` row written |

### 14.3 Scheduler Priority

```
priority = w_fr · forgetting_risk
         + w_ag · active_goal
         + w_re · recent_error
         + w_eig · probe_eig
```

with weights from `[scheduler]` in `learnloop.toml`.

**Components**:

```
forgetting_risk(item) =
    0.0                                  if practice_item_state.due_at IS NULL
    0.0                                  if due_at > now
    1 - R_fsrs6(now)                     otherwise

active_goal(item) =
    max over goals G where G.status='active' of:
        G.priority · 1[item.lo.concept ∈ reachable(G.concept_anchors, depth=1)]
    0.0 if no goal reaches the item

recent_error(item) =
    max over active error_events e on item.learning_object_id of:
        e.severity · exp(-days_since(e.created_at) / 7)
    0.0 if no active error_events

probe_eig(item) =
    EIG(item) / log(|H|)                 if lo_probe_state.status = 'in_progress'
    0.0                                  otherwise
```

`reachable(anchors, depth=1)` follows edges with `relation_type ∈
{prerequisite, part_of}` only. `confusable_with` and `related` edges do NOT
propagate goal reach.

**Tiebreak**: lowest `practice_item_id` lexicographically.

**Suppression**:

- `practice_item_state.active = 0` → filtered before scoring.
- `session.available_minutes ≤ scheduler.short_session_minutes` → set
  `probe_eig := 0`.
- Cold LOs (`learning_object_mastery.last_evidence_at IS NULL` AND
  `lo_probe_state.status != 'in_progress'`) → excluded from the candidate set.

`scheduler_explanations.readiness_factor` is computed from session inputs
(`energy`, `available_minutes`) for display in `learnloop why`, but does NOT
re-rank the queue.

### 14.4 Probe-EIG

A pending active-goal LO enters `lo_probe_state.status = 'in_progress'` when
goal capacity opens. At entry:

1. Build hypothesis set `H` (cap at `probe.hypothesis_set_max_size`):
   - `mastered`, `unfamiliar` (always present).
   - One `misconception:E` per active `error_events` row on this LO.
   - One `misconception:E_neighbor` per `confusable_with` edge whose neighbor
     concept has `mastery_mean ≥ 0.7`, using that neighbor's most-severe
     active error_type.
   - If over the cap, drop lowest-severity misconceptions first.
2. Compute the prior `P(h)` (renormalized):

   ```
   P(mastered)         ∝ σ(μ)
   P(unfamiliar)       ∝ 1 - σ(μ)
   P(misconception:E)  ∝ severity · exp(-days_since(e.created_at) / 7)
   ```

3. Persist `H` and `P(h)` to a new `hypothesis_sets` row; link via
   `lo_probe_state.hypothesis_set_id`.

`H` is **locked** for the duration of the probe phase. It recomputes only on
re-entry.

**Outcome space**: `o = (score_bucket, error_type | null)`,
`score_bucket ∈ {low: rubric_score∈{0,1}, mid: {2,3}, high: {4}}`.

**Conditional `P(o | h, item)`** (deterministic, fixed-mass):

| hypothesis | mass distribution |
|---|---|
| `mastered` | `(high, null) = 0.75`; `(mid, null) = 0.20`; remaining 0.05 spread over `(low, *)` |
| `unfamiliar` | `(low, null) = 0.45`; `(mid, null) = 0.30`; `(high, null) = 0.05`; remaining 0.20 spread over `(low, E_k)` for the known E_k in H |
| `misconception:E` and `E ∈ item.rubric.fatal_errors` | `(low, E) = 0.55`; `(mid, E) = 0.25`; `(high, null) = 0.05`; remainder spread over `(low, *)` |
| `misconception:E` and `E ∉ item.rubric.fatal_errors` | identical to `unfamiliar` (the item does not probe E) |

**EIG**:

```
P(o | item)  = ∑_h P(h) · P(o | h, item)
EIG(item)    = ∑_h P(h) · KL[ P(o | h, item)  ‖  P(o | item) ]
             = I(H ; O | item)
```

normalized by `log(|H|)` for the `probe_eig` scheduler component.

**Observation bridge** (used at attempt time and by §14.5):

```
observed.score_bucket = bucketize(practice_attempts.rubric_score)
observed.error_type   = error_types.id of the highest-severity error_events
                        row written for this attempt, else null.
```

### 14.5 Surprise

All quantities live in `attempt_surprise`. Prior is the pre-attempt
`(μ_old, P_old)`; posterior is the post-attempt `(μ_new, P_new)` from §14.2.

```
r                    = (z_obs - μ_old) / sqrt(P_old + R)
predictive_surprise  = 0.5 · [ r² + log(2π · (P_old + R)) ]               (nats)
bayesian_surprise    = 0.5 · [ log(P_old/P_new) + P_new/P_old
                               + (μ_old - μ_new)² / P_old  -  1 ]         (nats)
fsrs_interval_factor = clamp(exp(alpha_interval · r), [f_min, f_max])
```

**`surprise_direction`** (in order):

1. If `observed.error_type IS NOT NULL` AND
   `predicted_error_type_dist_json[observed.error_type] < epsilon_error_surprise`
   → `negative` (the error-type surprise channel).
2. Else if `r > theta_pos` → `positive`.
3. Else if `r < -theta_neg` → `negative`.
4. Else → `none`.

`mixed` is reserved by the enum but is never emitted in MVP.

**JSON columns**:

- `predicted_score_dist_json` = `{"mu_z": μ_old, "sigma_z": sqrt(P_old + R)}`.
- `predicted_error_type_dist_json`: categorical over active error_events on the
  LO; per-row mass ∝ `severity · exp(-days_since/7)`; remainder on `"null"`.
- `observed_joint_bucket_json` = `{"score_bucket": ..., "error_type": ...}`.
- `posterior_delta_json` = `{"mu_before": μ_old, "mu_after": μ_new,
  "P_before": P_old, "P_after": P_new}`.
- `triggered_actions_json` / `suppressed_actions_json`: lists of strings.

The follow-up gate is defined in §10 and uses `tau_followup_nats` and
`gamma_min` from `[scheduler.followup]`.

### 14.6 Self-Grade Fallback

**Grader tiers** (`grading_evidence.grader_tier`):

| tier | meaning |
|---|---|
| 0 | unverified placeholder |
| 1 | learner self-grade |
| 2 | heuristic auto-grade (reserved; not used in MVP) |
| 3 | Codex grading |
| 4 | manual learner override / audit |

**Self-grade fires when**: Codex healthcheck reports `codex_missing`,
`codex_revision_mismatch`, `codex_unavailable`, or `codex_auth_required`; or
`CodexClient.run_grading_proposal` raises or times out per call.

**Self-grade form**: per-criterion checkbox (or partial-credit slider) +
optional `error_type` dropdown (seeded from the LO's `fatal_errors` and active
misconceptions, plus "other" free-text) + 1–5 confidence selector.

**Confidence mapping**: `practice_attempts.confidence ∈ {1,2,3,4,5}` →
`practice_attempts.grader_confidence ∈ {0.2, 0.4, 0.6, 0.8, 1.0}`.

**Writes per attempt**:

- One `grading_evidence` row per criterion: `grader_tier = 1`,
  `local_grader_id = 'self'`, `agent_run_id = NULL`,
  `points_awarded` from the form.
- `practice_attempts.rubric_score` = sum of `points_awarded`, capped by any
  ticked `fatal_errors` via `RubricFatalErrorPayload.max_grade`.
- `practice_attempts.grader_confidence` = mapped value.
- If `grader_confidence < 0.4`: `practice_attempts.manual_review_reason =
  'low_self_confidence'`.

**Deferred Codex regrade**:

1. On `learnloop` startup, after Codex healthcheck passes, query
   `grading_evidence` for the most recent non-superseded row per attempt where
   `grader_tier = 1`.
2. For each, call `CodexClient.run_grading_proposal` with the original answer
   and rubric.
3. Persist new `grading_evidence` rows with `grader_tier = 3` and the matching
   `agent_run_id`. Set the tier-1 rows' `superseded_at = now`,
   `superseded_by_evidence_id = <new>`.
4. **Delta-apply** the tier-3 observation: run the §14.2 Kalman update using
   the new `z_obs` against the *current* `(μ, P)` for the LO. Do NOT replay
   history; full replay is deferred with the replay-model infrastructure.
5. If `|rubric_score_new − rubric_score_old| ≥ 2`, write a `content_events`
   row with `event_type = 'regrade_disagreement'`,
   `entity_type = 'practice_item'`, `entity_id = practice_item_id`, and a
   `summary` referencing both `grading_evidence.id` values.

### 14.7 Error-Type Taxonomy

Vault-global file `errors/error_types.yaml`:

```yaml
schema_version: 1
error_types:
  - id: confused_with_eigendecomposition
    title: Treats SVD as identical to eigendecomposition
    description: Long-form description.
    related_concepts:
      - singular_value_decomposition
      - eigendecomposition
    severity_default: 0.8
    is_misconception: true
    tags: []
    created_at: 2026-05-19T00:00:00Z
    updated_at: 2026-05-19T00:00:00Z
```

`is_misconception: true` means a persistent misconception (decays slowly in
`recent_error`, contributes a hypothesis to probe-EIG). `is_misconception:
false` means a transient slip (decays at the standard 7-day half-life, does
not contribute a probe-EIG hypothesis).

`error_type` is a member of `EntityType` (§6) and uses
`ErrorTypePatchPayload` (§6).

**Validator for unknown error_type at grading time**:

- The grading is accepted; mastery, FSRS, and `error_events` updates all
  proceed with the literal `error_type` string.
- A new `proposed_patch_items` row of `item_type = 'error_type'`,
  `operation = 'create'`, `decision = 'pending'` is appended within the same
  grading `agent_run_id`'s `proposed_patches` batch, with the proposed taxonomy
  entry payload.
- On proposal rejection, dangling `error_events.error_type` strings are
  surfaced by `learnloop doctor` as `errors:unaligned_error_type`.

**Rubric link**: `practice_item.grading_rubric.fatal_errors[].id` remains a
free identifier scoped to the rubric. `learnloop doctor` warns when a
`fatal_errors[].id` does not have a matching `error_types.yaml` entry. Codex
authoring prompts should prefer existing taxonomy IDs but this is not enforced
by the validator.

**Severity defaults**: when `ErrorAttribution.severity` is missing, use
`error_types[id].severity_default`; if missing, use `0.5`.

**Seed values**: `learnloop init` creates an empty `errors/error_types.yaml`
containing only `schema_version: 1` and `error_types: []`. The taxonomy grows
organically through Codex proposals or manual edits.

### 14.8 Algorithm Versioning

`algorithm_version` is stamped on every derived row in
`learning_object_mastery`, `learner_theta`, `lo_probe_state`,
`hypothesis_sets`, `learner_state_beliefs`, `attempt_surprise`, and
`scheduler_explanations`. MVP value is `"mvp-0.1"`. Bumping the value is a
versioned event: it is recorded as a `content_events` row of
`event_type = 'algorithm_version_bumped'`. Existing derived rows are NOT
recomputed at bump time; recomputation belongs to the deferred replay-model
infrastructure.
