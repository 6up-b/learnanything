# Knowledge Model Redesign Specification

Status: Draft, revision 4 (rev 3 + editorial consolidation: §3.4 restructured around the normative lock trigger; §5.4/§9.2 internal dedup; §12.6 exam-authority clause points at the ingestion §4.2 normative matrix; "pre-lock" terminology unified)
Scope: Canonical content facets, shared facet belief state with capability-sliced evidence, task blueprints and AND/OR requirement recipes, rubric-criterion observation boundary and dependency graph, immutable observation lineage, semantic/task/inference graph separation, factorized evidence provenance, read-side expected-performance projections, compositional error taxonomy, diagnostic and scheduler integration
Repository: LearnLoop
Companion: `spec_source_ingestion_v2.md` (synthesis mints facets, task blueprints, and assessment contracts; both specs consume one shared mutation/lock/proposal contract, §12). The KM1 semantic/task/observation contracts MUST land before ingestion M4 freezes its inventory schema, and KM2 shared state/lineage MUST land before ingestion M6 can apply a learnable v2 map, before real-learner locks accrue against the current per-LO facet keys.

## 1. Summary and motivation

Learning Objects are curriculum and scheduling units, not independent latent skills. Today the evidence model pretends otherwise:

- Facet *definitions* are canonical vault-level entities (`EvidenceFacet`, `facets.yaml`, alias resolution via `canonical_facet_id`), but every fixture registry is empty and `doctor` skips facet validation entirely when the registry is empty (`services/doctor.py:588`).
- Facet *belief state* is keyed `(learning_object_id, facet_id, practice_item_id)` (`migrations/007_recall_coverage_interventions.sql`), so the same named facet is re-learned independently under every LO.
- Item facets are minted per practice item as task-operation slugs (`qk_first`, `scale_before_softmax`) rather than semantic atoms; 12 linear-algebra items produce 21 distinct facet strings with zero reuse.
- `criterion_facet_weights` exist but are empty everywhere; attribution falls through to a lexical fallback (`services/recall_coverage.py:772`).
- Graph mastery propagation is dormant: `cross_lo_propagation.error_gates` is configured but consumed nowhere, and the only live graph prior (`graph_propagated_prior`, `services/calibration_sessions.py:29`) is direction-blind (its docstring claims direction-specificity the code does not implement) and lets `related` edges propagate at 0.5. It is **not** shadow-only: besides the shadow routine planner, its `episode_priority_disagreement` signal live-scales calibration-session episode ordering (`start_calibration_session`, calibration_sessions.py:229–231), so correcting it changes live ordering behavior, not just logs (§8.3).

The measured consequence (July 2026 goal-attainment diagnosis): item evidence mass splits across 4–6 per-LO facets, per-facet beta posteriors gain ~0.19–0.30 mass per attempt, and even an 80% practice exam barely moves the other facets in a goal's scope. The grind toward certification is structural, not motivational.

The redesign:

1. **Canonical content facets become the latent units.** One registry entry per assessable semantic atom, shared across LOs; belief state keys on the canonical facet id.
2. **Rubric criteria become the observation boundary.** Criteria declare what they observe (facet × capability × role); items stop asserting global mastery updates.
3. **Task composition becomes explicit.** AND/OR requirement recipes, alternative methods, applicability, and criterion dependencies represent what performance actually requires; semantic relations remain outside learner-belief math.
4. **Evidence carries immutable, factorized provenance.** Direct/embedded relationship, capability, assistance, surface/testlet correlation, exercised method, and attribution are replayable; claims and graph plausibility are priors/projections, never observations.
5. **LO mastery becomes a read-side expected-performance query** over representative task blueprints, valid solution recipes, shared facet-capability state, and explicit integration factors where justified. An LO residual is prediction-only calibration, never a latent catch-all or certification source.

Everything propagated is derived state: recomputed by `rebuild_derived_state`, never written back as synthetic attempts. Stable observation ids, immutable assessment-contract snapshots, and lineage-aware projections prevent one criterion outcome from being attached more than once or reinterpreted after curriculum changes.

## 2. Design principles (normative)

1. **Evidence, not mastery.** No service writes mastery directly. All belief change flows through `apply_attempt`; replay MUST reproduce identical state (existing invariant, unchanged).
2. **One criterion outcome → one stable observation id → one attached inference factor.** Derived messages are never new independent observations. Persisted evidence rows are attempts, grading evidence, and learner claims; grading evidence snapshots the assessment contract used for attribution. Propagation and prediction live only in derived code.
3. **Asymmetry is preserved without graph-traversal damage.** Downstream success is evidence for a prerequisite only when a criterion visibly exercised it under an identified valid recipe. A downstream failure MUST NOT create negative prerequisite evidence merely by traversing an edge. A visible, localized failure on a prerequisite criterion may update it; an unlocalized failure becomes an unresolved cause set and diagnostic need.
4. **Attribution follows the criterion dependency graph.** Correct independent/prefix work is preserved; only criteria whose observability depends on a failed criterion become unassessable; whole-task failure never penalizes every listed facet (generalizes `services/longform_trace.py` semantics to all multi-facet items).
5. **Inference information and certification credit are separate.** A criterion observation is attached once to every variable in its joint factor. Conservative certification credit is bounded per task/correlation group; the permanent probabilistic model MUST NOT equate "one task" with exactly one unit of information.
6. **Capability-aware certification.** A shared facet parent may pool sparse evidence across capabilities for prediction, but certification of a target requires direct/embedded evidence in the target capability and adequate independent-surface coverage.
7. **Honest displays.** Any surface that blends direct evidence and estimates MUST distinguish what is demonstrated from what is predicted. Goal certification uses direct/embedded, capability-matched evidence only; goal attainment prediction may use projections (§9.5).
8. **Registries over enums.** Hyper-specific wrong beliefs live in the misconception registry (migration 025), never in global error-type vocabularies. Specific belief = compositional record; stable taxonomy = repair-action router (§10).

## 3. Canonical content facet registry

### 3.1 What a facet is

A content facet is an **assessable semantic atom**: a claim, definition, procedure step-contract, or interpretive schema that can be true of a learner's knowledge independent of any one task. It MUST NOT bundle content with a task operation.

Good: `facet_matrix_symmetry_definition`, `facet_spectral_theorem_applicability`, `facet_orthogonal_matrix_inverse_identity`.
Bad (current style): `symmetry_check`, `factorization_reasoning`, `qk_first` — these mix *what is known* with *what the item asks*.

### 3.2 Registry entry schema (`facets.yaml`, schema_version 2)

```yaml
facets:
  - id: facet_matrix_symmetry_definition
    concept_id: concept_symmetric_matrix
    kind: definition              # definition | proposition | procedure_contract | applicability_condition | interpretation
    claim: A real square matrix is symmetric exactly when A^T = A.
    preconditions:
      - the matrix is real and square
    postconditions: []
    applicability: []
    positive_examples:
      - a matrix with mirrored off-diagonal entries
    negative_examples:
      - an orthogonal rotation matrix that is not symmetric
    non_goals:
      - orthogonal matrix definition
    error_signatures:
      - substitutes A^T A = I for A^T = A
    instructional_repairs:
      - contrast symmetric and orthogonal matrices
    aliases: [symmetry definition]
    status: reviewed          # proposed | reviewed | retired
    version: 1
    semantic_fingerprint: sf_9c1e...   # deterministic hash of the normalized contract; proposes cross-vault reuse, never asserts equivalence
    provenance:
      origin: sourceset_synthesis | manual | facet_normalization
      source_refs: []          # span citations (ingestion v2 §8.5 locators)
```

- `kind`, `claim`, conditions, examples, non-goals, error signatures, and instructional repair form the facet's semantic contract. Two facets merge only when these contracts are compatible (§3.4).
- Registry entries created by source-set synthesis MUST cite source spans through the ingestion v2 span protocol; the "adequate provenance" quality gate extends to facets.
- `entity_source_links` is authoritative for current multi-source facet provenance. The YAML `provenance.source_refs` field is the synthesis-time embedded snapshot used by legacy readers.
- Once any practice item in a subject declares `evidence_facets`, an empty or non-covering registry is a **doctor error**, not a skipped check (fixes `doctor.py:588` behavior). Severity is gated by vault model version: mvp-0.7 vaults error; legacy vaults keep today's warning-only behavior so the upgraded doctor does not break frozen vaults.
- Facet ids are human-readable slugs minted **once** at creation (concept + kind + claim core), never from LO/subject/vault-local counters, and never re-derived from content afterward — a contract wording refinement or rename (alias) does not touch identity. Cross-vault identity is NOT id-equality: each registry entry also carries a deterministic `semantic_fingerprint` (hash of the normalized semantic contract) used to *propose* reuse/equivalence when importing or comparing vaults; equivalence is confirmed only by reviewed import mappings, never assumed from matching fingerprints or slugs. Collisions append a short contract-hash suffix.
- New generated items MUST reference registered canonical facets; the item gate rejects unregistered facet ids (parallel to the probe instance gate).

### 3.3 Candidate harvesting and normalization

Candidates are gathered from: canonical-source claims (unit inventories), LO summaries and knowledge types, rubric criteria, existing PI `evidence_facets`, fatal-error conditions, misconception statements, and LO free-text `prerequisites`. An LLM MAY propose normalizations (same atom, different words); it MUST NOT merge. Lexical or embedding similarity only *proposes review* — similarity is ephemeral and review-only: lexical/MinHash by default, optional embedding assist when available, and similarity artifacts are never persisted as identity or matching infrastructure.

### 3.4 Identity locking, rename, semantic merge, and semantic split

**Lock trigger (normative).** Facet identity locking is **independence-gated, not first-touch-gated**: a facet's semantic identity locks when its direct evidence spans ≥2 distinct surface/correlation groups, or its independent evidence mass reaches `[locks].facet_lock_mass` (default 2.0), or it enters an active goal's certified scope — whichever comes first. A raw observation count or an "any certification credit" trigger would lock most facets on their first successful attempt, defeating the grace window; independence is the principled trigger because locks exist to bound reinterpretation of history, and history is only load-bearing once a facet has demonstrated distinct existence. The grace window matters because review-by-exception means facet granularity is effectively decided by the synthesis model — early mistakes must stay repairable until real evidence makes them load-bearing.

- A **rename** preserves semantic identity and uses the sanctioned alias path. It is lock-safe because historical observations still resolve to the same facet identity.
- A **semantic merge** asserts that two previously distinct contracts are one. Pre-lock, a reviewed merge is a sanctioned cheap operation: observations are immutable and keep their original facet id; a persisted `facet_merges` row maps `retired_facet_id → surviving_facet_id`; merge resolution is applied at replay and projection time exactly like alias resolution, so `rebuild_derived_state` reproduces identical post-merge state deterministically and no beta mass is ever hand-migrated. Once locked, semantic merge requires the restructure-with-history specification (first post-core, §17).
- A **semantic split** creates new semantic identities. It is review-required and allowed only pre-lock. On split the source id retires; its observations stay attached to the retired identity for replay and children start unevidenced. Historical evidence is never copied at reduced weight into every child in this release.
- Capability-specific learner state activation (§4.2) is not a semantic split and does not mutate the facet registry.

## 4. Capability modes and context

### 4.1 Capability vocabulary (closed, domain-general)

```
retrieval | schema_interpretation | procedure_execution | method_selection | coordination
```

Selection is separate from execution because knowing how to run a procedure does not imply knowing when to pick it. Coordination is reserved for combining otherwise available components. Transfer is not a single capability: it is coverage and performance across context families (§4.3). `proof`, `short_answer`, `explanation`, and `notation` are observation formats or error channels, not capabilities.

This vocabulary is a deliberate STEM/proof-domain commitment for launch. Two future extensions are named now so schema choices don't foreclose them: `fluency` (speed/automaticity — latency is telemetry-only today) and domain packs for language/motor domains, which do not decompose into this five-way split. `capability_key` is TEXT everywhere and the vocabulary is versioned with the taxonomy (§10.1), so extension is additive.

The vocabulary also deliberately mirrors the probe hypothesis states (`surface_only`, `schema_without_transfer`, `procedure_without_selection`, …): the diagnostic layer already speaks this ontology; this spec makes the evidence layer speak it too.

### 4.2 Shared parent state with capability-sliced evidence at launch

The conceptual learner state is `K[content_facet, capability_mode]`, but persisting it that way multiplies latent states 3–5× while total evidence stays fixed — recreating the stuck-at-prior problem this redesign exists to fix, at ~5 learners' worth of data. Therefore:

- Launch prediction state: **one persisted shared parent belief per canonical facet** (§7), with capability-specific damping.
- Every criterion observation is immutably tagged with its target capability. A derived `facet_capability_evidence` ledger tracks positive/negative mass, certification credit, assistance, and independent surface groups per `(facet, capability)` from day one.
- Prediction MAY pool from the shared parent while data is sparse. Certification MUST be capability-specific even before any residual is activated; retrieval evidence cannot certify `method_selection` or `coordination`.
- **Lazy residual activation:** when a closed diagnostic episode or persistent capability-sliced residual disagreement demonstrates divergence, a learner-specific capability residual MAY be activated under the same facet id. Replay routes capability-tagged observations to the matching residual, leaves genuinely ambiguous observations at the parent, and uses the parent as a shrinkage prior. This is learner-model state, not a curriculum mutation or identity-lock event.

### 4.3 Context and transfer state

Transfer is context-dependent (`T[facet, context_family]`), and the probe redesign already models context families as instrument surface families with categorical shifts (symbolic↔geometric, familiar↔shifted notation, direct↔embedded, routine↔proof, near↔far). Transfer belief therefore **lives in the diagnostic layer** (episode posteriors, surface families, coverage report), not in a persistent global matrix or the capability enum. No continuous `transfer_distance` scalar; context dimensions stay categorical. A persistent per-facet transfer state is a future promotion with the same shrinkage discipline as §4.2.

## 5. The observation boundary: rubric-criterion targets

### 5.1 Criteria declare what they observe

```yaml
criteria:
  - id: identifies_symmetry
    targets:
      - facet: facet_matrix_symmetry_definition
        capability: schema_interpretation
        role: primary            # primary | supporting
    correlation_group: symmetry_identification
  - id: selects_spectral_theorem
    depends_on: [identifies_symmetry]
    recipe_ids: [spectral_theorem_method]
    targets:
      - facet: facet_spectral_theorem_applicability
        capability: method_selection
        role: primary
```

- `depends_on` forms a criterion DAG; file order is presentation order only. `recipe_ids` identifies which valid method(s) make the criterion relevant. Independent branches remain assessable after an unrelated failure.
- Roles compile deterministically into conservative certification-credit allocations; the existing `criterion_facet_weights` mechanism becomes a legacy-compatible compiled output, never hand-authored. A role is not causal certainty or a graph-transfer coefficient.
- A criterion MAY declare several candidate targets. On failure it produces an **attribution distribution** over its candidates (informed by grader error attribution and misconception match), not equal damage to all of them.
- `nuisance` is not a facet-target role. Notation load, scaffold, shared stimulus, item difficulty, and familiarity are observation-likelihood metadata (§6), not semantic learner-state targets.
- The lexical fallback in `recall_coverage.py` is retired for items authored under this spec; legacy items keep it for frozen replay only.

Default capability mapping for existing practice modes (used when recreating fixtures and compiling legacy content; authored criterion targets always override):

| practice mode / criterion style | default capability |
|---|---|
| retrieval, cloze, recognition, definition/statement recall | `retrieval` |
| explain-from-memory, teach_back core-tier criteria, interpretation ("what does this mean") | `schema_interpretation` |
| completion problems, computation/derivation execution steps, proof-step execution | `procedure_execution` |
| "which method/theorem applies", contrastive discrimination, teach_back transfer-tier selection criteria | `method_selection` |
| multi-step composition, proof assembly, extended cases combining otherwise-demonstrated components | `coordination` |

Transfer modes map to the capability of the exercised component; transfer distance is recorded as a surface-family shift in the evidence fingerprint (§4.3, §6), never as a capability.

### 5.2 Immutable observation and assessment-contract snapshot

Every presented item resolves to an immutable `assessment_contract_version` containing:

```
item/rubric content hashes
criterion ids, maximums, dependency DAG, and correlation groups
facet × capability targets and roles
valid recipes, recipe applicability, and criterion-to-recipe links
task/certification budgets
surface/testlet evidence fingerprint
assistance/scaffold contract
```

Each grading-evidence row gets a stable `observation_id = (attempt_id, criterion_id, grading_revision)` and refers to that contract version. Superseding a grade creates a new grading revision and retires the prior observation; replay never resolves historical attribution against a mutable live item. The attempt also records the method/recipe exercised when observable; a correct final answer with an unidentified bypass method is weaker evidence for recipe-specific prerequisites.

Core persistence (exact migration may split tables/indexes):

```sql
assessment_contract_versions (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  contract_hash TEXT NOT NULL,
  contract_json TEXT NOT NULL,
  schema_version INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(practice_item_id, contract_hash)
);

-- Added to grading_evidence or an observation wrapper keyed to it:
assessment_contract_version_id TEXT NOT NULL,
grading_revision INTEGER NOT NULL,
observation_id TEXT NOT NULL UNIQUE,
recipe_id TEXT,
attribution_json TEXT,
correlation_group TEXT;

unresolved_cause_factors (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  observation_id TEXT,
  candidate_causes_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('open','resolved','retired')),
  resolution_observation_ids_json TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
```

`contract_json` is content-addressed and reused by identical item versions. It is not copied per criterion. Assessment-contract metadata changes that affect attribution create a new version; cosmetic display changes do not.

### 5.3 First-error localization (all multi-facet items)

Generalizing `longform_trace.py` to ordinary graded items:

- Correct criteria whose observability does not depend on an earlier failure yield normal positive evidence, whether or not they form a literal prefix.
- The earliest failed criterion on each exercised dependency branch carries its localized failure attribution.
- Descendants whose valid evaluation depends on that failed criterion are **unassessable** (evidence share 0), not failed. Independent branches remain assessable.
- Whole-item failure MUST NOT penalize every listed facet.
- When criterion-mapping confidence is low, failure evidence is weakened accordingly.
- When a failure remains compatible with several causes, persist an unresolved joint-cause record. Do not convert one disjunctive failure into several independent negative Beta updates. When the candidates imply different repairs, emit a diagnostic need instead of committing a marginal belief (§11.1).
- A wrong final answer with no observable method/work is normally an unresolved task-level failure and triggers a short diagnostic; it does not penalize every recipe component.

### 5.4 Observation information and bounded certification credit

One criterion outcome is attached exactly once as a joint observation factor. For the launch independent-Beta approximation, its pseudo-mass is conservatively allocated across marginal targets while retaining its shared `observation_id` and `correlation_group` lineage.

Certification credit remains bounded:

`sum(certification_credit from one attempt within a correlation group) <= group_budget(attempt_type, group)`.

Several criteria reflecting one upstream error earn no more than their shared group budget; projection-only signals have zero certification credit. (The rich-response upside — several independently observable groups out-earning a binary item — is stated once, in the four-quantities paragraph below.)

**Launch allocation rule (normative default; fitting remains open per §18):** a criterion observation's total pseudo-mass is `evidence_mass(attempt_type) × criterion_share`, where `criterion_share` is the criterion's max points over the rubric total. Within the criterion, success mass splits across targets by role weight (`primary` 1.0, `supporting` 0.3), normalized to sum to 1. Failure mass follows the criterion's attribution distribution (§5.1) instead of role weights; unresolved attributions produce an unresolved cause factor, never marginal mass. **Default certification budget:** `group_budget(attempt_type, group) = evidence_mass(attempt_type)` per correlation group — each independently observable correlation group in one attempt may earn at most the attempt type's evidence mass in certification credit, reusing the existing `[evidence.attempt_types]` masses (independent 1.0, teach_back 0.8, exam_evidence 0.35, …) as the single source of truth. Overrides live in `[evidence.certification]`.

Four quantities are defined separately and MUST NOT be conflated: (1) **inference pseudo-mass** — the allocation above; sums to `evidence_mass(attempt_type)` across the rubric. (2) **certification credit per observation** — equal to the observation's pseudo-mass when and only when it is direct/embedded, capability-matched, and unassisted; zero otherwise. (3) **per-correlation-group cap** — `group_budget(attempt_type, group)` as above. (4) **attempt-wide ceiling** — `evidence_mass(attempt_type) × [evidence.certification].max_groups_per_attempt` (default 3). A rich constructed response can therefore certify more than a binary item — intended, since §2 principle 5 separates inference information from certification credit — but not without bound. Because `correlation_group` is author-controlled, the identifiability doctor and synthesis gates flag suspicious group proliferation (many groups whose observations never vary independently).

## 6. Factorized observation provenance and correlation

Evidence metadata is orthogonal rather than one overloaded tier:

| Dimension | Values / meaning |
|---|---|
| observation relationship | `direct` when the task intentionally targets the facet; `embedded` when it is visibly exercised inside another target |
| capability | the authored capability actually observed |
| assistance | unassisted, hinted, scaffolded, answer-exposed |
| surface freshness | fresh, repeated, near-clone, shared stimulus/testlet |
| method | identified recipe, ambiguous recipe, bypass method |
| attribution | localized target, unresolved cause set, assessment ambiguity |

`claim` and graph-conditioned plausibility are priors/projections, not evidence tiers. They receive no evidence mass or certification credit.

Each item carries a global `evidence_fingerprint`, for example:

```yaml
evidence_fingerprint:
  source_family: chapter-3-example-7
  shared_stimulus_id: testlet-eigenvectors-01
  representation: symbolic-matrix
  solution_recipe_family: nullspace-row-reduction
  answer_structure: basis-vectors
```

Familiarity and correlation lookup operates across the subject/vault, not only inside one LO, using canonical facet overlap, practice-item identity, source-span family, shared stimulus/testlet, representation, solution-template family, and surface family. This prevents a near-clone under another LO from creating fresh independent evidence after facet state becomes global.

## 7. Shared facet belief state

### 7.1 Re-keying

New table (migration number to be assigned after ingestion v2's 032):

```sql
facet_recall_state (
  id TEXT PRIMARY KEY,
  facet_id TEXT NOT NULL,                 -- canonical id (post-alias resolution)
  capability_key TEXT NOT NULL DEFAULT 'shared',
  practice_item_id TEXT,                  -- NULL = aggregate row
  recall_alpha REAL NOT NULL, recall_beta REAL NOT NULL,
  recall_mean REAL NOT NULL, recall_variance REAL NOT NULL,
  independent_evidence_mass REAL NOT NULL DEFAULT 0,
  raw_coverage_mass REAL NOT NULL DEFAULT 0,
  last_observed_at TEXT, last_error_at TEXT,
  consecutive_failures INTEGER NOT NULL DEFAULT 0,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX facet_recall_aggregate
  ON facet_recall_state(facet_id, capability_key)
  WHERE practice_item_id IS NULL;
CREATE UNIQUE INDEX facet_recall_item
  ON facet_recall_state(facet_id, capability_key, practice_item_id)
  WHERE practice_item_id IS NOT NULL;

facet_capability_evidence (
  facet_id TEXT NOT NULL,
  capability TEXT NOT NULL,
  direct_positive_mass REAL NOT NULL DEFAULT 0,
  direct_negative_mass REAL NOT NULL DEFAULT 0,
  embedded_positive_mass REAL NOT NULL DEFAULT 0,
  embedded_negative_mass REAL NOT NULL DEFAULT 0,
  certification_credit REAL NOT NULL DEFAULT 0,
  independent_surface_groups_json TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  UNIQUE(facet_id, capability)
);

facet_merges (
  retired_facet_id TEXT PRIMARY KEY,
  surviving_facet_id TEXT NOT NULL,
  merged_at TEXT NOT NULL,
  proposal_item_id TEXT,
  rationale TEXT
);
-- Pre-lock reviewed merges only (§3.4). Replay and projections resolve facet ids
-- through aliases + this map; observations are never rewritten. Resolution is
-- transitive to the terminal survivor; inserting a row that would create a cycle
-- is rejected at write time.
```

- The existing `evidence_facet_recall_state` (per-LO keys) is frozen for legacy replay (§15).
- `facet_uncertainty` (migration 012) re-keys to `facet_id` only (no `capability_key`): capability divergence lives in the capability evidence ledger and activated residuals, not in diagnostic uncertainty state. The `misconceptions` registry (migration 025) re-keys the same way: `target_facet`/`confused_with_facet` become canonical facet ids and LO scoping becomes a derived index, so KM4's compositional records never straddle two keyings.
- Facet identity and belief state are **vault-level**; subject membership is a curriculum-layer property. Two subjects sharing `facet_matrix_symmetry_definition` share one belief parent; goals, doctor checks, and coverage reports remain subject-scoped views over vault-level state. Familiarity/correlation lookup (§6) is vault-wide.
- The partial indexes are required because SQLite `UNIQUE` constraints permit multiple `NULL` values. `capability_key='shared'` also keeps shared and activated capability rows explicit.
- `facet_capability_evidence` is a replayable cache derived from immutable criterion observations, not a new evidence source.
- Update mechanics remain beta-mass marginals at launch, now keyed canonically and lineage-aware. An exam attempt exercising `facet_matrix_symmetry_definition` moves the same shared parent every LO targeting that facet projects from, while only the observed capability receives certification credit.

### 7.2 LOs as performance blueprints and requirement recipes

```yaml
learning_object:
  concept: concept_spectral_theorem_real_symmetric
  blueprints:
    - id: select_and_apply_spectral_theorem
      weight: 0.7
      recipes:
        - id: spectral_theorem_method
          composition: conjunctive
          all_of:
            - facet: facet_matrix_symmetry_definition
              capability: schema_interpretation
            - facet: facet_spectral_theorem_applicability
              capability: method_selection
          integration:
            facet: facet_coordinate_spectral_conditions_and_conclusion
            capability: coordination
    - id: direct_definition_retrieval
      weight: 0.3
      recipes:
        - id: definition_recall
          composition: conjunctive
          all_of:
            - facet: facet_spectral_theorem_statement
              capability: retrieval
```

Recipes support `all_of`, `any_of` alternative methods, optional/facilitating components, applicability conditions, and explicit integration factors. A requirement is `hard` only when every valid recipe in the declared scope requires it; otherwise it is path-specific, facilitating, or instructional order. Flat LO targets are a derived union used for search and legacy compatibility, not the source of readiness math.

An integration facet is authored only when component competence can coexist with an observable, repeatable coordination failure that has a distinct instructional repair. Otherwise integration remains a task interaction and is evidenced only by direct whole-task performance. Every LO used for certification declares which representative blueprint(s), capabilities, and surface families require direct integrated demonstration.

## 8. Three graph views, one registry

### 8.1 Semantic graph

`relations.yaml` schema_version 2 contains navigation and authoring relationships only:

| relation_type | Meaning | Learner-belief effect |
|---|---|---|
| `prerequisite` | coarse concept/curriculum ordering hint | none directly; operational requirements live in recipes |
| `part_of` | ontological composition | none |
| `confusable_with` | contrast/misconception candidate | none; probe generation only |
| `related` | discovery and UI proximity | none |
| `analogous_to` | potential comparison/transfer suggestion | none |

Scalar `strength`, if retained, means confidence in the relationship's validity only. `equivalent_to` is not an edge: reviewed equivalence is a semantic merge (§3.4). `part_of` MUST NOT propagate mastery; knowing parts does not demonstrate their composition.

Every semantic edge records authoring rationale/source, direction where meaningful, applicability, a counterexample or non-applicable case where known, `status ∈ {proposed, reviewed, empirically_supported, retired}`, and version. Dense LLM-generated "related concepts" graphs are rejected.

### 8.2 Curriculum and task graph

LO blueprints, requirement recipes, capability-conditioned targets, alternative paths, criterion dependencies, and explicit integration factors are the authoritative representation of what performance requires. Reusable facet-capability requirement rules MAY be referenced by several recipes; concept-level prerequisite edges are only a coarse navigation projection.

Requirement modality is explicit:

| modality | meaning |
|---|---|
| `hard` | every valid recipe in the declared scope requires it |
| `path_specific` | required only for named recipe(s) |
| `facilitating` | improves performance but can be bypassed |
| `instructional_order` | normally taught earlier but not cognitively required |

Only `hard` and exercised `path_specific` requirements materially affect task likelihood or criterion attribution.

### 8.3 Learner inference graph

The runtime inference view contains shared facet parents, activated capability residuals, explicit integration states, criterion observations, unresolved cause factors, misconception hypotheses, item difficulty, assistance, and local surface/testlet factors. It is derived from immutable observations and curriculum contracts; it is not authored as `relations.yaml`.

Derived LO nodes are readout leaves and MUST NOT become parents of another LO or facet projection. The current LO-to-LO `graph_propagated_prior` is corrected so `related`, `analogous_to`, `part_of`, and `confusable_with` contribute zero and prerequisite direction is respected (the current code is direction-blind despite its docstring), then remains shadow/diagnostic-only until it is replaced by a low-evidence facet-capability prior with held-out predictive support. The correction also **disables the one live consumer**: `episode_priority_disagreement` currently scales calibration-session episode ordering (`start_calibration_session`, calibration_sessions.py:229–231); at correction time that weighting is turned off, ordering reverts to plain predictive rate, and the signal becomes genuinely shadow-only (consistent with §11.1). This is a live behavior change and the acceptance suite (§16) covers the ordering reversion explicitly. The dormant `cross_lo_propagation.error_gates` block is retired.

### 8.4 Graph diagnostics and empirical refinement

Residual dependence is diagnostic rather than permission for opaque propagation: positive residual dependence suggests a missing facet or testlet factor; systematic combined-task failure suggests a missing integration factor; context-specific residuals suggest transfer/capability divergence; indistinguishable facet response signatures suggest an identifiability problem. Empirical data MAY propose reviewed graph/recipe mutations, never silently rewrite authored structure.

## 9. Projection layer (read-side, derived)

### 9.1 Where projections live

All projections are pure functions over persisted evidence + immutable assessment contracts + registry + task graph, recomputed by `rebuild_derived_state`. They are versioned alongside `algorithm_version`. **No projection ever writes an evidence row.** This prevents write-back loops, while stable observation lineage separately prevents read-time double counting through several derived paths.

### 9.2 LO mastery = expected performance over blueprints

For LO `l` with representative blueprint distribution `B_l`:

`readiness(l) = E[t ~ B_l] P(success on t | facet-capability state, recipe, integration, difficulty, assistance, surface)`.

- Recipe likelihoods follow the launch defaults below: noisy-AND core for conjunctive recipes, max over applicable alternative recipes, reviewed partially compensatory composition for explanatory tasks.
- Item difficulty, familiarity, scaffold, and testlet effects live in the task likelihood. Learner claims seed priors. They are not mixed into an LO-local latent skill.
- The existing per-LO EKF MAY remain as a prediction-only calibration random effect during transition. It has no certification credit and cannot absorb claims, item difficulty, familiarity, or unidentified integration as interchangeable evidence.
- Displayed LO state exposes component readiness, integration/direct whole-task performance, transfer/surface coverage, retrievability, and uncertainty. A scalar is an optional summary query.
- Certification of a composite LO requires capability-matched component coverage plus direct unassisted performance on its declared representative integrated blueprint(s); strong components alone cannot saturate it.

**Launch likelihood defaults (normative; family choice per blueprint type and fitting remain open per §18):** a conjunctive recipe uses noisy-AND — `P(success | recipe) = (1 − slip) · Π_i p_i` over its required facet-capability components `p_i` (capability-damped predicted recall), with `slip` from `[evidence.blueprints].slip` (default 0.05). Selected-response formats add a guess floor: `P = guess + (1 − guess − slip) · Π_i p_i`, with `guess` defaulting to `1/n_options` for multiple choice and 0 for constructed response (`[evidence.blueprints].guess_by_format`). Alternative recipes combine as the maximum over applicable recipes; reviewed partially compensatory (explanatory) blueprints use a weighted geometric mean; an authored integration facet enters as one more conjunct. This formula is the *recipe core* only: item difficulty, familiarity, scaffold, and testlet effects remain in the observation-level modifiers and the prediction-only calibration residual above at launch — deliberately not new formula terms until real data says they are decision-relevant. These defaults are simple on purpose: the projection layer is versioned and replayable, so upgrading the likelihood family later is a projection recompute, never an evidence migration.

### 9.3 Asymmetric propagation semantics

For a downstream task exercising prerequisite facets:

- **Success with identified visible exercise** → direct/embedded positive observation for the exercised facet-capability, attached once through the criterion factor.
- **Success without visible exercise or with an unidentified bypass recipe** → no facet evidence; at most a low-evidence prediction prior or diagnostic scheduling signal.
- **Localized failure visibly exercising a prerequisite** → legitimate negative evidence for that facet-capability.
- **Unlocalized downstream failure** → unresolved cause factor and diagnostic need; no negative evidence created by structural traversal and no blanket marginal damage.
- Prerequisite success does not demonstrate downstream composition; it affects task prediction only through the recipe component state.

### 9.4 Anti-double-count invariants (testable)

1. Persisted evidence rows originate only from attempts, grading, and claims; each criterion grading revision has one stable observation id. Learner claims carry their own stable lineage id `claim:(facet_id, capability?, stated_at)`, seed priors only, and never earn evidence mass or certification credit.
2. Each observation id is attached to the inference graph exactly once, even when its joint factor connects several variables.
3. Projections are deterministic and idempotent; no derived LO projection is an input parent to another LO/facet projection.
4. Certification credit is bounded per task/correlation group (§5.4); projection and prior signals receive zero credit.
5. Direct evidence is never reintroduced through a graph prior or LO calibration residual. Graph priors remain separate, low-evidence-only prediction inputs.
6. Replay uses the historical assessment-contract version and reproduces identical marginals, ledgers, unresolved causes, and projections.

### 9.5 Goal semantics (dual-axis honesty preserved)

- **Readiness/attainment** MAY use expected-performance projections and shared parent evidence — this is where an exam attempt can improve predictions across every LO sharing an exercised facet.
- **Certification/demonstration** requires direct/embedded evidence meeting facet, target-capability, independent-surface, and declared integrated-blueprint requirements. Priors, claims, calibration residuals, and graph projections never certify.
- Goal scope references canonical facet-capability targets and/or LO blueprint requirements. Legacy facet-only scopes resolve to reviewed default capabilities and produce a migration warning rather than silently certifying every capability.

### 9.6 Provenance UI (deliverable, not afterthought)

The default learner-facing model is:

- **Ready:** predicted ability across representative tasks.
- **Demonstrated:** capability- and surface-matched direct evidence.
- **Next gap:** bottleneck component, integration gap, retrievability issue, or unresolved diagnostic question.

Progressive-disclosure details expose direct/embedded evidence, assistance, surface coverage, claim seed, and projected contribution. When one observation counts toward several LOs, the UI says "This also counted toward X and Y." When a source/model update changes only a projection, it says "Your evidence is unchanged; the estimate was recalculated." Attempt feedback distinguishes demonstrated correct work, the first localized error on each branch, downstream work that was unassessable, and any diagnostic needed before selecting a repair.

Tauri deliverables tied to this model (land in KM3/KM5):

- **Attempt trace view** (Feedback screen): render the criterion DAG per attempt — demonstrated work marked on every assessable branch, the first localized error per branch flagged, dependent descendants shown as *not judged* (never *wrong*), generalizing the longform-trace rendering to all multi-facet items.
- **Unresolved-cause diagnostic card** (Feedback): "This failure is consistent with N causes," the candidate list, and a one-tap "run a short diagnostic" action entering the probe episode targeted at the cause set (§11.1 priority 1).
- **Capability grid**: facet × capability heatmap per goal/LO neighborhood; each cell encodes Demonstrated (capability-matched direct/embedded credit) vs Ready (pooled prediction) vs untested. It is the primary **diagnostic drill-down** — one tap from any Demonstrated surface, because it is the only view that answers "certified for retrieval but never tested on selection" — but the ambient default journey remains Ready/Demonstrated/Next gap; the grid supersedes the per-LO facet radar, not the home surfaces.
- **Recipe tree ("why not ready")** on LO detail: the AND/OR blueprint recipe tree with per-component readiness and the current bottleneck highlighted; the Next-gap surface links here.
- **Ready/Demonstrated dual encoding** on the knowledge map/graph views after re-keying: node fill = Ready (predicted), node ring = Demonstrated. The legacy per-LO→item→facet `FacetMasterySnapshot` DTO tree and its consumers (radar/strata/terrain/well views) re-key as part of this work.
- **Session narrative** on Today: one deterministic line from intent-first composition (§11.2), e.g. "Today: 1 diagnostic, 12 retrieval reps, 2 integration tasks — next gap: coordinating spectral conditions."
- **Facet evidence drawer + belief timeline (two phases)**: from any facet, an observation timeline with capability/assistance/surface chips and the "also counted toward X and Y" cross-links — the progressive-disclosure surface above, made concrete. Phase 1 (KM3) adds the **Demonstrated curve**: a deterministic fold over the immutable observation ledger *including* grading supersessions, retired observations, corrected attribution, and merge restatements — exact and replayable, but not monotone: corrections render as visible annotated events (the curve may step down) rather than being smoothed away. No replay, no snapshot tables. Phase 2 (immediately after KM3) overlays the **Ready series**, goal-scoped first via the existing replay-to-checkpoint series infrastructure (the `goal_series.py` pattern); it MUST segment by `algorithm_version` and annotate projection-only recalculations ("your evidence is unchanged; the estimate was recalculated") from day one, so projection-definition changes never render as false learning cliffs. Timeline points link to their observations and, through provenance, to Open-in-source (ingestion v2 §9.2).

Display rule: ambient surfaces lead with **Ready** (it moves fast and rewards work — this is what fixes the "stuck at 0%" grind); goal and certification surfaces lead with **Demonstrated**. Never blend them into one number.

## 10. Error taxonomy: general mechanism, specific belief

### 10.1 Stable mechanism taxonomy (routes repair/diagnosis)

```
retrieval_failure | conceptual_schema_error | procedure_execution_error |
selection_planning_error | condition_assumption_error |
representation_notation_error | transfer_context_error | local_slip |
assessment_ambiguity
```

Legacy mapping: `recall_failure→retrieval_failure`, `conceptual_error→conceptual_schema_error`, `procedure_error→procedure_execution_error`, `notation_error→representation_notation_error`, `assumption_error→condition_assumption_error`, `theorem_selection_error→selection_planning_error`, `transfer_failure→transfer_context_error`.

The taxonomy is a **grader contract**: it touches grading prompts, the signature matcher (rubric fatal ids == signature names invariant), and discrimination rows. It is versioned like prompt versions; changing it triggers a `probe-regrade`-style non-destructive check pass.

### 10.2 Compositional specific record (misconception registry)

```
mechanism: conceptual_schema_error
operation: property_substitution        # closed-ish vocabulary, extensible
target_facet: facet_matrix_symmetry_definition
confused_with_facet: facet_orthogonal_matrix_definition
statement: The learner believes A^T = A implies A^T A = I.
trigger_conditions: [...]
expected_signatures: [...]
first_divergence: [...]
non_applicable_controls: [...]
misconception_id: mc_...
```

Operation vocabulary: `property_substitution | category_confusion | condition_omission | direction_reversal | overgeneralization | undergeneralization | invalid_composition | wrong_operator | procedure_ordering | representation_mismatch`. Never add `confuses_X_with_Y` to a global enum. This record shape directly parameterizes contrast-probe generation (target vs confused_with are the two bound facets).

### 10.3 Promotion discipline

A one-off ambiguous failure stays a distribution over causes (including `item/grader issue`), not a forced label. Promote to a durable misconception when: it repeats on an independent surface; a high-confidence first-error trace exposes the belief; a targeted contrast probe reproduces the predicted signature; or it maps to an already-validated registry belief. (Mirrors the probe family lifecycle: real-evidence-gated transitions.)

## 11. Diagnostic and scheduler integration

### 11.1 Probe targeting

The task graph, capability ledger, and observation provenance reduce redundant probing. Probe/episode priority SHOULD target, in rough order:

1. an unresolved failure cause set whose candidates imply different repairs;
2. disagreement between capability-matched direct evidence and a low-evidence prediction prior (the `episode_priority_disagreement` signal remains shadow until held-out validation);
3. the least-certain bottleneck requirement shared across several at-risk blueprints;
4. the integration condition: components strong ∧ direct integrated performance weak → probe `coordination`/recipe selection, not the components again;
5. whether success transfers to a new independent surface family.

If strong downstream `embedded` evidence already demonstrates a prerequisite facet, early probes MUST NOT re-establish it.

### 11.2 Scheduler consumes distinct states, intent-first

```
K[facet(, capability)]   semantic competence (§7)
R[item/surface]          retrievability & spacing (FSRS, unchanged)
F[item, surface]         familiarity/exposure (unchanged)
M[misconception]         wrong-belief posterior (unchanged)
T                        transfer, via diagnostic layer (§4.3)
```

Session composition selects an **intent** first — `diagnose_uncertainty | repair_misconception | restore_retrievability | build_missing_knowledge | develop_transfer | practice_integration` — then ranks candidates within it. This matches the sim-sweep finding that ranking weights are decision-inert while membership/gating decides outcomes, and it formalizes what quota composition already does. Any new intent-selection policy ships in shadow mode first with logged rankings, per the established probe-spec discipline.

### 11.3 Assessment identifiability doctor

`learnloop graph-identifiability` analyzes each goal/LO neighborhood's criterion-by-facet-capability matrix and recipe structure. It warns on:

1. duplicate target signatures that always co-occur;
2. missing anchor/contrast criteria for a facet-capability;
3. different planted profiles with equivalent ideal outcomes;
4. capability confounding (for example, retrieval and method selection always observed together);
5. alternative recipes that grading cannot distinguish;
6. component weakness and integration weakness with identical signatures;
7. all evidence coming from one representation, source example, or testlet.

If a distinction is not identifiable, LearnLoop MUST NOT display false facet-specific precision. It reports an unresolved bundle and schedules a discriminating probe. If no useful probe exists and the instructional repair is identical, authoring review SHOULD merge or coarsen the distinction before identities lock.

The identifiability doctor is not only an on-demand CLI. It runs (1) as a **synthesis-time quality gate**: ingestion v2 proposals containing facets/criteria/recipes are analyzed before presentation, and non-identifiable distinctions first emit a **generate-discriminator need** (anchor/contrast probe or item, via the existing generation-needs machinery); a coarsening review item (merge/coarsen suggestion) is recommended only when no useful distinguishing assessment exists and the instructional repairs are identical — the same rule this section already states — while everything is still pre-lock and cheap to change (§3.4); and (2) as a **pre-first-practice doctor check** on any subject whose registry changed, so distinctions are coarsened before evidence starts accruing against them.

## 12. Coordination contract with source ingestion v2

1. **Shared mutation contract.** One authoritative `can_apply(operation) -> {legal, lock_reasons}` API owned by the curriculum layer computes the identity-lock closure, including assessment-contract versions, criterion DAGs/targets, recipes, new facet state, capability ledgers, goals, misconceptions, and observations. Neither spec maintains a competing lock list. Facet identity locks are independence-gated per §3.4: `can_apply` reports a pre-lock facet merge/split as legal-with-review, and the lock check is part of the same closure. §3.4 plus this section are the **single normative lock policy**; ingestion v2 §8.2/§10.3 are its enforcement view, and on any divergence this contract wins.
2. **Synthesis mints semantic contracts and task contracts.** Source-set synthesis emits span-cited facet registry entries (§3.2), LO blueprints/recipes (§7.2), criterion DAGs/targets (§5), and evidence fingerprints (§6) through the same gates. Facet normalization/merge proposals are review items; no similarity signal auto-merges.
3. **Proposal dependency closure.** Facet → blueprint/LO → rubric/criterion → practice-item creations declare dependencies. Partial acceptance applies a valid dependency-closed set atomically or blocks dependents with an actionable reason; it never leaves dangling assessment contracts.
4. **Manifest completeness.** Ingestion manifests include curriculum snapshot hash, facet-registry hash, task/recipe graph hash, assessment schema version, and learner-model contract version. Cached synthesis is never reused against a different registry/map.
5. **Provenance authority.** `entity_source_links` supports facets and task blueprints and is authoritative after append/revision changes; YAML refs remain embedded snapshots.
6. **Assessment-role sources.** Exam sources are excluded from semantic authority but included in an assessment-alignment lane; the normative policy is ingestion v2 §4.2 (authority matrix + exam use modes) and this clause is its KM-side summary. They MAY shape scope, task-family/blueprint distributions, capabilities, representations, response formats, timing/emphasis, and held-out evaluation, but MUST NOT independently mint/modify canonical claims, equivalence, or prerequisite truth. Held-out-partition questions are never injected into teaching or routine generation contexts.
7. **Sequencing.** Facet/task/observation contracts (KM1) MUST be final before ingestion M4 freezes inventory schema. Shared state and capability ledgers (KM2) MUST be live before ingestion M6 can apply a learnable v2 study map. A feature gate prevents attempts against a partially upgraded map.
8. **Fixture recreation is sanctioned.** Existing fixture vaults are rebuilt under the new model; the ingestion v2 end-to-end journey doubles as registry, recipe, and assessment-contract acceptance.
9. **Token boundary.** Richer facet/task contracts add structured inventory/synthesis output under ingestion v2 §3 budgets, but learner-state projection, correlation discounting, identifiability checks, and certification are deterministic and add zero provider tokens. Grading receives only the presented item's compiled assessment contract/relevant facet ids (not the whole registry or source collection), so per-attempt context does not grow with source count.

## 13. Risk controls

**False facet equivalence.** Registered canonical facets required for new items; semantic contracts include kind, conditions, examples/counterexamples, non-goals, error signatures, and repair; aliases are names, not equivalence; semantic merge/split is prohibited after lock (independence-gated, §3.4) without the restructure-with-history path.

**Over-transfer and capability inflation.** Only the exact same semantic facet shares a parent. Certification remains capability- and surface-specific. Semantic edges never copy mastery. Downstream evidence reaches a prerequisite only through a visible criterion under an identified recipe.

**Double counting and correlated surfaces.** Stable observation ids, assessment snapshots, joint-factor attachment, bounded certification groups, global evidence fingerprints, and no derived-LO parents enforce §9.4. "No write path" alone is not treated as sufficient.

**Ambiguous attribution.** Criterion DAGs preserve assessable work; only dependent descendants become unassessable; unlocalized failures remain joint cause sets rather than marginal penalties; response-without-work routes to diagnosis.

**Replay reinterpretation.** Every observation resolves against its immutable assessment-contract version. Curriculum/source append cannot silently change what historical work demonstrated.

**False diagnostic precision.** The identifiability doctor gates facet-specific claims and requires anchors/contrasts or displays an unresolved bundle.

## 14. Non-goals

- No fully independent persisted `K[facet, capability]` matrix at launch; the shared parent, capability evidence ledger, and shrinkage-based residual activation are sufficient (§4.2).
- No persistent global `T[facet, context]` matrix (diagnostic layer owns transfer, §4.3).
- No full global Bayesian network at launch; local task factors and cached Beta marginals remain tractable and replayable.
- No per-semantic-edge mastery coefficients or scalar edge strength in belief math.
- No claim graph, embeddings, or vector store for facet identity.
- No auto-merge of facets; no dense LLM-generated relation graphs.
- No LO residual contribution to certification.
- No change to FSRS retrievability; attempt/replay gains immutable assessment-contract lineage but remains event-sourced.

## 15. Migration and back-compat

- **Fixture vaults are recreated**, not migrated (accepted cost; canonical ingestion v2 produces the new registries/contracts).
- Legacy vaults replay **frozen** under their recorded `algorithm_version` (mvp-0.6 and earlier): per-LO facet keys, lexical fallback, and old blends stay exactly as-is. New model activates at `algorithm_version: mvp-0.7` only through an explicit compatible upgrade/new vault.
- Because `algorithm_version` is currently vault-global, mixed legacy and mvp-0.7 subjects in one vault are forbidden until per-subject assessment-model routing exists. Activation is an atomic vault upgrade or the vault remains legacy; ingestion cannot silently create v2 learnable content inside a legacy vault.
- `evidence_facet_recall_state` and `facet_uncertainty` are retained read-only for frozen replay; new state lives in the re-keyed tables (§7.1). `misconceptions` rows in new vaults key `target_facet`/`confused_with_facet` canonically from the start; the LO index becomes derived.
- V1/V2 facet registries remain readable. A legacy LO `evidence_facets` list can form a non-certifying compatibility blueprint only; it cannot infer capabilities or recipe composition without review.
- Historical grading rows gain or reference an immutable compatibility assessment snapshot. New grading always records `assessment_contract_version`, observation id/revision, criterion DAG/targets, and evidence fingerprint.
- Goal facet ids resolve through aliases; facet-only goal targets require reviewed capability defaults. Unresolvable or capability-ambiguous scopes are doctor errors/warnings, never silent broad certification.
- Config adds `[evidence.correlation]`, `[evidence.certification]`, `[evidence.blueprints]`, `[capabilities]` damping/shrinkage, and `[locks]` (`facet_lock_mass` default 2.0; the lock also triggers on direct evidence in ≥2 distinct surface/correlation groups or membership in an active goal's certified scope, §3.4). `propagation_mean_floor_mass` and `cross_lo_propagation` retire with migration warnings.

## 16. Verification (acceptance)

- **Registry:** unregistered facet → rejection; empty registry with facet-bearing items → doctor error; rename alias preserves identity; locked semantic merge/split → invalid; similarity pair → review proposal only.
- **State schema:** shared aggregate/item rows are unique despite `practice_item_id=NULL`; two LOs share one facet parent; capability ledgers remain distinct; retrieval-only evidence cannot certify method selection.
- **Recipes:** conjunctive bottleneck cannot be averaged away; alternative method success does not credit a bypassed requirement; path-specific failure affects only the exercised path.
- **Observation/replay:** dependency-branch failure preserves independent correct work; dependent descendants are unassessable; each observation id attaches once; changing the live rubric after an attempt does not alter replay because the snapshot is authoritative.
- **Ambiguity:** wrong final answer/no work leaves component means unchanged, creates an unresolved cause set, and schedules a diagnostic; localized illegal row operation legitimately updates the shared procedure facet.
- **Certification:** bounded per correlation group; a rich response may earn several independent group credits; near-clones under different LOs are globally discounted; claims/priors/calibration never certify.
- **Projection:** planted integration-gap learner is not shown as demonstrated; alternative-recipe and difficulty effects calibrate expected performance; derived LO values never feed another LO.
- **Graph:** every semantic `part_of`/`related`/`analogous_to`/`confusable_with` edge produces zero belief change; retired propagation config is unread.
- **Identifiability:** duplicate signatures/missing anchors produce a warning and unresolved bundle rather than a facet-specific diagnosis.
- **Goals/UI:** `Ready`, `Demonstrated`, and `Next gap` DTOs expose capability/surface requirements and progressive provenance; a projection-only recalculation states that evidence is unchanged.
- **Sim gates:** shared-facet belief MAE and attempts-to-certify improve without capability inflation, integration false positives, clone inflation, or blanket multi-facet failure damage.
- **Taxonomy:** legacy error types map per §10.1; grader prompt version bump; regrade-check pass shows no attribution regressions on fixture attempts.
- **Locks/merges:** a pre-lock reviewed merge resolves through `facet_merges` and replay reproduces identical state; merge chains canonicalize transitively to the terminal survivor and cycle-creating rows are rejected; a facet with direct evidence in two distinct surface groups (or ≥ `[locks].facet_lock_mass` independent mass, or in an active goal's certified scope) refuses merge with a restructure-with-history reason; the lock check is part of `can_apply`.
- **Certification quantities:** inference mass sums to the attempt's evidence mass while a three-group constructed response earns up to three group budgets, capped by the attempt-wide ceiling; a group-proliferation flag fires on correlation groups whose observations never vary independently.
- **Graph correction:** the correction disables the live disagreement weighting — calibration-session ordering reverts to plain predictive rate on an acceptance fixture — and the signal is thereafter shadow-only; no live consumer remains.
- **Timeline:** the Demonstrated curve recomputed from scratch is identical to the incrementally rendered one (deterministic ledger fold); a regrade that retires an observation renders as a visible correction step, never a silent restatement; a projection-version bump renders in the Ready overlay as an annotated, `algorithm_version`-segmented recalculation, never as an evidence change.

## 17. Milestones

- **KM0 — Spec** (this document; co-review with ingestion v2 so §12 contracts match).
- **KM1 — Semantic/task/observation contracts:** facets.yaml v2 semantic contract + doctor/candidate tooling; LO blueprints/AND-OR recipes; criterion targets/dependency DAG/correlation groups; the default mode→capability mapping table (§5.1); immutable assessment-contract versions and proposal dependency schema; generated-item gate. KM1 is a hard dependency of ingestion M4 inventory-schema finalization, but has little coupling to ingestion M1–M3 and proceeds in parallel with them.
- **KM2 — Shared state + lineage:** new `facet_recall_state`, capability evidence ledger, `facet_merges` + independence-gated lock, unresolved-cause persistence, global evidence fingerprints/correlation lookup, frozen legacy replay, algorithm_version mvp-0.7, sim MAE/capability-certification gates. The **sim harness re-key** ((lo, facet) truth state and MAE aggregation → canonical facets) is part of KM2, not follow-up — the KM2 gates cannot run without it. KM2 lands against small **hand-authored fixture registries/blueprints**; canonical fixture recreation through the ingestion journey happens after M6 (resolving the otherwise circular KM2 ↔ M6 fixture dependency). KM2 is a hard dependency of ingestion M6 learnable-map application, and its observation lineage is explicitly designed so the post-core restructure-with-history specification remains possible.
- **KM3 — Expected-performance projections and UX:** blueprint recipe likelihoods, prediction-only LO calibration residual, capability/surface/integration certification, `Ready`/`Demonstrated`/`Next gap` DTOs and provenance UI, semantic graph propagation retirement, anti-double-count suite. Includes the Tauri re-key: the per-LO→item→facet `FacetMasterySnapshot` DTO tree and its consumers (radar/strata/terrain/well views) move to canonical keys, and the §9.6 deliverables (attempt trace view, capability grid, recipe tree, dual-encoded map, session narrative, evidence drawer with the Demonstrated timeline) land here and in KM5; the Ready timeline overlay follows immediately after KM3, goal-scoped first (§9.6).
- **KM4 — Taxonomy + misconception composition:** mechanism taxonomy version bump, compositional records, promotion discipline, contrast-probe parameterization from target/confused_with.
- **KM5 — Diagnostic/scheduler integration:** identifiability doctor, unresolved-cause probes, intent-first session composition in shadow mode, capability residual activation, residual-dependence diagnostics.
- **Post-core, first in line:** semantic restructure-with-history — promoted from indefinite deferral. Identity locks accumulate monotonically, and vault recreation cannot remain the only repair path once real vaults age; KM2's immutable observation ids and contract snapshots exist partly to make this specification possible.
- **Deferred:** full global joint inference, persistent transfer state, capability-residual-by-default, empirically supported facet priors, and likelihood/calibration fitting.

KM1–KM2 are the lock-sensitive window. Ingestion M6 may run synthesis previews before KM2, but it MUST NOT apply a learnable v2 map or accept attempts until KM2 is active.

## 18. Resolved design decisions and remaining calibration questions

Resolved:

1. Capability divergence activates learner-specific residuals under one facet; capability-tagged history replays to its matching residual and ambiguous history stays at the shared parent. No history is copied to every child.
2. The LO EKF is prediction-only calibration. Explicit integration facets require observable repeated coordination failure and distinct repair; otherwise direct blueprint performance represents the interaction.
3. Embedded credit requires an authored criterion target, identified applicable recipe, and visible exercise. Grader attribution alone never mints a new target.
4. Facets are statement/contract-level semantic atoms. Theorem statement, applicability conditions, consequences, and reusable procedure contracts split when they have different counterexamples, error signatures, or repairs; task operations and capabilities remain separate.
5. Launch defaults are normative for the independent-Beta allocation (role weights 1.0/0.3 within a criterion; mass = evidence_mass × criterion share, §5.4), certification budgets (`group_budget = evidence_mass(attempt_type)` per correlation group, §5.4), and blueprint likelihoods (noisy-AND / max-over-recipes / reviewed geometric mean, §9.2). The remaining calibration questions below concern *fitting* these, not choosing them — implementation is not blocked on the fits.
6. Facet identity locking is independence-gated (§3.4: direct evidence in ≥2 distinct surface groups, `[locks].facet_lock_mass`, or active-goal certified scope); pre-lock merges/splits resolve through the persisted `facet_merges` map (transitive, cycle-free) at replay/projection time, and restructure-with-history is the first post-core specification.

Remaining empirical/calibration questions:

1. Shrinkage strength and activation thresholds for capability residuals.
2. Likelihood family by blueprint type (strict conjunctive, partially compensatory, alternative-recipe combination) and its calibration data requirements.
3. Certification-credit budgets by attempt type/correlation group and minimum independent-surface coverage.
4. Whether any facet-capability graph prior earns operational use after held-out validation; default remains shadow/none.
