# Canonical Source Ingestion v2 Specification

Status: Revising, revision 7 (rev 6 + editorial consolidation: exam-authority and lock-policy restatements in §1/§7/§8.5/§10.3/§12 replaced with references to the §4.2 normative authority matrix and knowledge-model §3.4/§12 lock policy; hash-model naming unified; discriminator-first gate wording; "pre-lock" terminology unified)
Scope: Intent-first source library, works/artifacts/revisions, extraction providers and Document IR, source collections, durable workflow jobs, role-specific unit inventories, semantic and assessment-alignment synthesis, canonical facets/task blueprints/assessment contracts, identity locks, provenance, coverage, extraction health, bounded token economics, maintenance, and source-outcome analytics
Repository: LearnLoop

## 1. Summary

Ingestion today is a single atomic pipeline: `ingest_canonical_source` couples fetch → extract → register → LLM authoring in one invocation, one source at a time, and every import generates a full curriculum proposal. This breaks down for multi-source subjects (three textbooks → three competing definitions of the same LO), conflates acquisition with pedagogy in one enum (`SourceKind`), and reduces marker-pdf's structured output to flat Markdown at the earliest possible moment (`pdf_extraction.py` drops block ids, types, pages, geometry, images, ToC, and page stats), forcing LearnLoop to reconstruct worse versions of structure marker already had.

The redesign is organized as four layers, each depending only downward:

```
Source layer          immutable assets, works, revisions, extraction runs, blocks, figures
Interpretation layer  units, inventories, prerequisite hints, notation, coverage
Curriculum layer      concepts, facets, LO blueprints/recipes, criteria, practice, proposals, conflicts, provenance
Learning layer        goals, immutable observations, shared facet/capability state, identity locks, diagnostics
```

Hard rules: re-extraction must not alter learning evidence; inventory regeneration must not directly alter curriculum; curriculum synthesis must not rewrite learner history; learner evidence may constrain curriculum changes but never source extraction.

Source authority is role-specific; the single normative authority matrix and exam use modes live in §4.2. In summary: explanatory sources may support semantic claims; exam-role sources are **assessment evidence, not independent semantic authority**; and held-out exam material never enters teaching or practice-generation contexts (§8.5 enforces this at every context builder).

The primary user journey is intent-first, not mechanism-first:

```
Learning intent → Add sources to library → Extract & assess health → Choose units
→ Assemble source collection → Review semantic + assessment coverage and build plan
→ Create/Update study map → Review conflicts, task alignment & provenance
→ Learn, diagnose gaps, maintain
```

"Bootstrap" and "append" are routing decisions surfaced as **Create study map** / **Update study map**; the terms belong in logs and advanced details. Both modes ship in the core v2 release. A release that can create a study map but cannot safely add a later source or adopt a new source revision is incomplete.

A **Quick add** path is a first-class member of this journey, not a legacy holdover: paste one source → auto-selected units, suggested role, default brief, **one confirmation on the happy path** (covering the token estimate and any external-AI consent in a single dialog) → study map created/updated. Role ambiguity does not block — Quick add proceeds with the suggested role and flags it for later review; extraction problems proceed flagged per §2.5. To keep the minutes promise honest against the sequential worker: Quick add defaults to a **small relevant scope** (bookmark/ToC-guided most-relevant units, not whole-book), its jobs take **queue priority between checkpoints** over bulk batches, and when some selected units are ready long before others it MAY build the study map from the ready subset and route late units through append. It runs entirely on the v2 machinery (library, extraction, inventories, synthesis, gates) with defaults auto-chosen and review-by-exception intact; the legacy one-shot `ingest` becomes a compatibility wrapper over it. Time-to-first-practice-item is a tracked UX budget for both Quick add (minutes) and the full journey — the bootstrap flow *is* the first-run experience, and the first hour must produce learning, not library curation.

## 2. Source layer

### 2.1 Identity model

```
CanonicalWork                     bibliographic identity: DOI / arXiv id / ISBN-edition when derivable
└── SourceArtifact                stable acquisition identity: one canonical URL, uploaded file, or feed item
    └── SourceRevision            immutable fetched bytes; revision_id + asset_hash
        └── ExtractionRun         one extractor/version/config/page-selection pass over the revision
            ├── DocumentUnit      chapter/section with stable unit id, label, page range
            ├── DocumentBlock     span-addressable block (see IR)
            ├── DocumentAsset     extracted figure/image assets
            └── ExtractionHealth per-page/per-block quality signals
```

- One imported PDF/webpage/video acquisition endpoint = one `SourceArtifact`; each distinct fetched byte sequence = one immutable `SourceRevision` and one canonical-source revision note. The system MUST NOT mint one note per detected chapter.
- `work_id` derives from bibliographic metadata when possible. A canonical URL identifies a `SourceArtifact`, not necessarily a work. AI title-matching MAY *propose* work linkage for confirmation (`needs_confirmation: true`); it MUST NOT silently merge mirrors or editions.
- Idempotency/dedup rules are explicit:
  - same normalized artifact identity + same `asset_hash` → reuse the revision;
  - same bytes acquired from different artifact identities → distinct artifacts/revisions, MAY share one raw content blob;
  - same artifact identity + new `asset_hash` → new revision linked by `supersedes_revision_id`;
  - re-extracting an existing revision creates a new **ExtractionRun**, never a new source revision.
- Source-set membership pins a `revision_id` for reproducibility and retains `source_id` for update detection. A newer revision is shown as **Update available**; membership advances only after user confirmation, then routes through append reconciliation. Synthesis manifests always snapshot the pinned revision.

### 2.2 Hash model

| Hash | Over | Identifies | Invalidates |
|---|---|---|---|
| `asset_hash` | raw fetched bytes | the source revision | source-change analysis, revision dedup |
| `extraction_request_hash` | revision + extractor + package version + model artifacts + config + page selection + IR schema version | one *requested* ExtractionRun — computable before execution, so it is the idempotency/retry key | retry dedup, run identity |
| `extraction_result_hash` | request hash + produced IR output | the completed run's content (cache/view identity) | block index, views |
| `semantic_hash` | deterministic normalized text view (per unit) | LLM-facing content | unit inventory cache |

The request/result split exists because a retry key must be computable before extraction completes; a hash that includes output cannot key the retry ladder.

`semantic_hash` is computed over normalized text content, NOT raw block HTML — cosmetic HTML changes between extractor versions must not invalidate inventory caches. Normalization is specified, not implied: strip markup/styling, collapse whitespace, drop repeated page headers/footers and page numbers, keep equation and table cell content verbatim, exclude geometry/ids. Because math content is kept verbatim, a marker upgrade that changes LaTeX rendering **will** invalidate math-heavy unit caches — expected and honest; cross-major-extractor-version cache reuse is best-effort, never promised. The legacy markdown `content_hash` remains on existing notes for back-compat reads.

### 2.3 Document IR

Extractor types MUST NOT leak past the source layer. The IR is the common downstream contract for marker, pypdf, HTML, YouTube captions, text files, and future extractors (OCR providers, EPUB):

```
DocumentBlock:
  span_id              stable short id within the extraction run (s17)
  extractor_block_id   provenance (marker block id) when available
  block_type           extractor-native type (Text, Table, Figure, Equation, Code, ...)
  role_hint            deterministic pedagogical hint (§2.6); nullable
  page                 nullable (non-paged sources)
  bbox / polygon       nullable geometry for PDF citation & preview
  section_path         heading trail
  text                 normalized text; tables/equations keep exact content
  content_hash         per-block text hash
  asset_ids            figure/image assets attached to this block
```

- Markdown remains the **display/export** rendering of the note body for humans; it is no longer the canonical intermediate.
- Non-PDF sources get honest trivial ExtractionRuns: HTML/textfile units from headings, YouTube units from time ranges; one extraction method; no geometry.
- Marker mapping: chunks renderer `FlatBlockOutput` (id, block_type, html, page, polygon/bbox, section_hierarchy, images) → DocumentBlock; metadata `table_of_contents` → DocumentUnits; `page_stats` → ExtractionHealth.
- Marker block ids are extractor provenance, not durable LearnLoop identity. `span_id` is stable only within its ExtractionRun; cross-run re-anchoring uses asset identity, page/geometry, section path, and content hashes.

Core persistence (migration 032; exact indexes may be split across migrations during implementation):

```sql
source_artifacts (
  id, acquisition_kind, canonical_uri, work_id, current_revision_id,
  created_at, updated_at
);
source_revisions (
  id, source_id, asset_hash, note_id, original_uri, retrieved_at,
  supersedes_revision_id, created_at,
  UNIQUE(source_id, asset_hash)
);
source_extraction_runs (
  id, revision_id, parent_extraction_id,
  extractor, extractor_version, model_versions_json, config_json,
  page_selection_json, ir_schema_version,
  extraction_request_hash, extraction_result_hash,   -- result hash NULL until completed
  status, created_at, completed_at,
  UNIQUE(revision_id, extraction_request_hash)
);
source_document_units (
  extraction_id, unit_id, parent_unit_id, label, ordinal,
  locator_json, semantic_hash,
  PRIMARY KEY(extraction_id, unit_id)
);
source_document_blocks (
  extraction_id, span_id, extractor_block_id, block_type, role_hint,
  page, bbox_json, polygon_json, section_path_json,
  text, content_hash, asset_ids_json, ordinal,
  PRIMARY KEY(extraction_id, span_id)
);
source_document_assets (
  id, extraction_id, media_type, content_hash, path,
  caption, page, geometry_json, neighboring_span_ids_json
);
```

A targeted repair ExtractionRun MAY name `parent_extraction_id` and contain only repaired pages. The active document view is a deterministic composition of the parent plus its replacement blocks. The composed `extraction_result_hash` and affected unit `semantic_hash` values are persisted; unaffected unit inventories remain reusable.

### 2.4 Locator schemes (back-compat is permanent)

- New extractions cite `block_span_v1` locators: `span:<extraction_id>/<span_id>` (with page/bbox available for preview).
- Legacy provenance refs are today **unnamed bare strings** pattern-matched by shape; migration backfills a declared scheme onto every existing ref by shape detection. Three legacy shapes exist and MUST resolve forever: `heading_path_v1` (`root/section-slug/p1`), `time_range_v1` (`t=<start>-<end>`), and `arxiv_label_v1` (native labels like `thm:4.2`, `eq:1.2` from `_native_arxiv_label`). `analyze_source_change`, span validation, and replay all key on them. Locator scheme is declared per ref after migration; schemes are never silently converted.
- A new ExtractionRun over the same revision attempts deterministic span re-anchoring. An exact content-hash match wins only when it is **unique** within the resolution scope; duplicated hashes (boilerplate, repeated equations) disambiguate via section path, page/geometry, and neighboring-block context. Page/geometry/section matches are fallback candidates. Successful aliases are persisted in `source_span_reanchors`; a still-ambiguous or unresolved span becomes `needs_reanchor` — never silently resolved and never semantically stale. Only adopting a new source revision can make the underlying evidence stale.

```sql
source_span_reanchors (
  from_extraction_id, from_span_id, to_extraction_id, to_span_id,
  match_kind CHECK(exact_hash|geometry_section|manual), confidence,
  created_at,
  PRIMARY KEY(from_extraction_id, from_span_id, to_extraction_id)
);
```

### 2.5 Extraction strategy (adaptive, consent-gated)

Replace the global `use_llm` toggle with staged escalation:

1. Cheap PDF probe: page count, native bookmarks, sample text coverage (deterministic; feeds preflight).
2. Standard local marker extraction (local model inference; no external service).
3. Compute extraction-health signals: image-only pages, abrupt text-density drops, replacement chars / malformed equations, implausible reading order, heading-level discontinuities, near-empty table blocks, pages whose extraction method differs from neighbors (from `page_stats`).
4. Flag suspicious pages/blocks on the source card.
5. Offer targeted repair: "Improve N difficult pages" → re-run only those pages (`page_range`) with force-OCR / inline-math repair / table processing / an explicitly approved LLM service.

**Import promise (replaces "zero LLM calls"):** Import uses local document processing by default and NEVER sends source content to an external AI service without explicit confirmation. Import performs no pedagogical LLM calls.

Extraction cache identity MUST include: marker package version, model artifact versions (best effort via package metadata), configuration, page selection, and IR schema version — i.e., the `extraction_request_hash` inputs (§2.2). (The current cache keys only bytes+options — a marker upgrade silently serves stale output.)

### 2.6 Block-role hints (deterministic)

After IR conversion (an external adapter — NOT a coupled marker processor), annotate likely structural roles from headings and block context: `definition | theorem | proof | worked_example | exercise | solution | summary | reference | equation | figure | table | ordinary_prose`. "Definition 4.2", "Exercises", "Worked Example" are recognizable deterministically. These are hints, not semantic truth; they shrink inventory prompts and let role-aware treatment differ (problem sets emphasize exercises; papers emphasize claims/assumptions/limitations; exams stay out of curriculum authority).

### 2.7 Figures

Persist extracted image assets with caption, page, geometry, neighboring explanatory spans, and section association. Inventories receive captions + metadata by default. A vision call happens only when the selected unit relies on the figure, caption/text is insufficient, AND the user approved the applicable model. Never put every image into a multimodal context.

### 2.8 Marker structured extraction

Not used as the pedagogical inventory (beta, LLM-required). MAY be used experimentally for bibliographic metadata recovery. Unit-aware caching, span citations, role context, prerequisite/notation contracts, and reconciliation belong to LearnLoop.

### 2.9 Extraction-provider boundary and deployment

`DocumentExtractor` is a versioned provider interface returning the LearnLoop IR; downstream services never import marker classes. Required implementations:

- `MarkerDocumentExtractor` — high-fidelity local OCR/layout/math/table/figure extraction;
- `PyPdfDocumentExtractor` — lightweight native-text fallback;
- the existing HTML, YouTube, and text normalizers adapted to the same IR.

User-facing choices describe outcomes, not engines: **Fast text**, **High-fidelity local**, and **Improve difficult pages**. `auto` selects the least expensive mode expected to meet the source's needs; advanced settings reveal the provider/version/config.

Marker remains an optional provider until distribution and model-license compatibility have been reviewed for LearnLoop's deployment model. The repository is GPL-3.0 and its model weights have separate modified terms; an adapter or subprocess boundary provides operational replaceability but is NOT assumed to resolve licensing obligations. The application MUST show required downloads, local hardware expectations, data egress, configured external provider, and estimated affected pages before the user approves assisted repair.

## 3. Token-budgeted views

Never send marker JSON or complete Markdown to an LLM. Three deterministic views over the IR:

**Outline view** (no pedagogical LLM call; powers unit selection and preflight): title/authors/ToC, unit page ranges, block counts by type, extraction-health flags, approximate tokens per unit, already-inventoried markers.

**Inventory view** (per selected unit): section heading once; prose blocks with short span ids; exact important equations; table captions/headers/dimensions; figure captions + nearby text; repeated headers/footers/boilerplate omitted; bibliography/index marked low-priority, not deleted.

**Evidence view** (span-request pass only): exact bounded blocks requested during synthesis, with full equations/table cells/figure context as needed; hard total-token and span-count limits.

Example inventory view fragment:

```
UNIT u_ch04 | Eigenvalues | pp. 91–126
[s17 text] An eigenvector of A is...
[s18 equation] Av = λv
[s19 worked_example] Consider the matrix...
[s20 figure] Geometric action of...
```

The LLM cites `s17`, `s18`, … — it never invents a locator or repeats page/path metadata.

### 3.1 Numeric budgets and preflight estimates

Token limits are configuration with explicit defaults, not prose-only promises. Initial planning defaults (provider context permitting):

| Stage | Target input | Hard bounded output | Notes |
|---|---:|---:|---|
| unit inventory window | 10k–20k tokens | 3k tokens | oversize units split on block/section boundaries |
| bootstrap synthesis shard | 20k–40k | 10k | inventories/registry summaries, never raw documents |
| exact evidence spans in final pass | 12k within a 48k total input ceiling | 16k | one request round; proposal output may be sharded by dependency-closed bundle |
| append affected-neighborhood context | 24k within a 48k total input ceiling | 10k | new inventories + bounded existing-map neighborhood |

These are defaults, not promises that every provider has the same context/output limits. Budgets and per-provider context/output limits live in `learnloop.toml` under `[ingest.budgets]` and `[ingest.providers.<name>]`; preflight reads them and reports estimated input, cached input, maximum output, call count, and which stage dominates. A stage that exceeds its ceiling shards or pauses for narrower scope; it never silently truncates.

An optional collection/run total-token ceiling is enforced before starting the next shard. Reaching it moves the workflow to `waiting_for_input` with completed artifacts intact and actions to continue another budgeted batch, narrow units, change provider/model, or stop; it never silently spends past the approved ceiling.

Every inventory job, synthesis run, retry, and optional vision/repair call records `input_tokens`, `cached_input_tokens` when reported, `output_tokens`, provider/model, purpose, and cache hit. Collection UI shows actual versus estimated usage. Provider prompt caching may reduce monetary cost but does not change the logical token/context budget.

Planning ranges for one substantial textbook unit are roughly 8k–20k inventory input and 1k–3k inventory output. The richer knowledge contract (facet conditions/error signatures, task recipes, criterion candidates, and fingerprints) is expected to add about 5–10% inventory input and 20–50% inventory output, or approximately 300–900 output tokens for a typical unit. It adds no extra raw-source pass.

Blueprint recipes, criterion dependencies, proposal dependencies, and assessment alignment are expected to add roughly 10–20% synthesis input and 25–50% synthesis output for a moderate collection. Across inventory + synthesis, the planned knowledge-model enrichment should normally add about 10–25% total tokens; exam-heavy collections may approach 20–35% because per-item assessment signals are structured output. Immutable observation snapshots, capability ledgers, projections, correlation discounting, and the identifiability doctor are deterministic and add no source-processing model tokens. AI grading receives only the presented item's compiled assessment contract, with a planning overhead of roughly 200–800 input and 100–300 output tokens per graded attempt; that context MUST NOT grow with source count.

### 3.2 Scaling invariant

Let `Vnew` be inventory-view tokens in newly selected/changed units, `Inew` their inventory-summary tokens, `A` the bounded affected existing-map neighborhood, and `E` the capped exact evidence spans. Normal append cost is:

```
inventory input  ~= Vnew
append input     ~= Inew + A + E
append output    ~= new facets/links/recipes/conflicts
```

Initial bootstrap is linear in total selected unit content plus inventory summaries. It MUST NOT compare every pair of sources in full. Append is linear in newly selected/changed material plus a bounded relevant neighborhood; it MUST NOT resend the entire accumulated curriculum.

Affected-neighborhood selection is deterministic and reviewable: match concept names/aliases, cited prerequisite hints, current provenance, source scope, and candidate facet contracts to map neighborhoods; send only matching concepts, facets, LOs/blueprints, recipes, conflicts, and compact registry indices. An unresolved candidate may request one additional bounded neighborhood. Without this rule, repeatedly sending the full map would make cumulative append cost approximately quadratic in source count.

Inventory reuse invariants:

- same unit semantic hash + satisfying inventory profile + schema/prompt/provider/model → zero new inventory tokens, even across collections;
- cross-revision/cross-extraction reuse is safe *because* an unchanged unit `semantic_hash` implies unchanged normalized block text, so every cited span rebinds deterministically by exact content-hash re-anchor (§2.4); if any cited span fails a **unique** rebind (duplicated block hashes), that unit falls back to re-inventory — the token-savings promise carries this safety valve rather than being weakened;
- changed revision or repair → re-inventory only units whose semantic hash changed;
- new synthesis brief over existing inventories → synthesis tokens only;
- adding a comparable source → that source's selected-unit inventory cost plus one bounded append, never a full bootstrap;
- role-specific assessment alignment reuses the exam inventory and never rereads exact exam text during each synthesis.

## 4. Source library and source sets

### 4.1 Source library (vault-level)

Users drop files/URLs into a general library **without** committing to subject, role, scope, or set membership first. Structural consequence: new canonical sources live at vault level (`sources/` — artifact notes + raw assets + extraction data), not under `subjects/<id>/notes/`. Legacy subject-scoped source notes remain readable in place forever. Subjects and sets reference library sources.

```text
sources/<source_id>/source.md                         artifact/work metadata + current revision pointer
sources/<source_id>/revisions/<revision_id>.md       immutable normalized display rendering/frontmatter
canonical-sources/raw/<asset_hash>                   content-addressed fetched bytes (shareable by mirrors)
.learnloop/source-cache/extractions/<extraction_id>/ derived IR/assets/cache data
```

The library groups revisions into one source card. Deleting derived extraction cache never deletes the raw revision or its audit metadata; it only requires re-extraction before inventory/span use.

Each source renders as a card: title, readiness (`Ready · 325 pages · 10 chapters · Math extraction looks good` / `Needs attention · 4 pages may need improved OCR`), suggested role, work/edition match (with needs-confirmation flag).

### 4.2 Three orthogonal properties

- **`acquisition_kind`** — `web | arxiv | pdf | youtube | textfile` (the existing `resolution.py` categories). Intrinsic.
- **`source_role`** — open string; known values `primary_textbook | alternate_explanation | reference | problem_set | lecture | paper | exam | notes` produce doctor *warnings* when unknown, never rejection. An unknown role **fails closed for authority**: it receives no semantic-contract or assessment-alignment privileges until a human confirms a known role or grants explicit manual authority. Manual authority overrides persist scope (which entities/claims), rationale, actor, and timestamp as audit metadata. Roles are **suggested after inspection** (arXiv → paper, YouTube → lecture, textfile → notes, other → reference; refined by outline signals like a dominant exercises section) and confirmed only when ambiguous. Role controls authority and inventory profile: `exam` contributes assessment alignment but cannot independently authorize semantic claims; `problem_set` emphasizes task/solution signals; explanatory roles emphasize semantic contracts.
- **`source_scope`** — selected unit ids.

Known-role authority defaults (reviewable and overridable only with explicit human/manual authority):

| role | semantic contract support | task/assessment alignment |
|---|---|---|
| `primary_textbook`, `lecture`, `paper`, `reference` | yes, scoped by source/context and conflict review | yes when task signals exist |
| `alternate_explanation` | supporting/alternate, not silently primary | yes when task signals exist |
| `problem_set` | not independent authority for omitted definitions/conditions | yes for task families, methods, representations, difficulty signals |
| `exam` | no independent semantic authority | yes for scope, blueprint distribution, capabilities, format, emphasis, held-out evaluation |
| `notes` | manual/unclear authority; review when used canonically | yes when explicitly selected |

An assessment source may quote a correct definition, but that occurrence remains an inventory candidate until corroborated by an allowed semantic source or explicit manual authority. Conversely, an explanatory source can contain exercises that inform task design without changing its primary semantic role.

This table is the **single normative authority matrix**. §7 (inventories), §8.5 (span protocol), §10.3 (append policy), and the §8.7 gates reference it rather than restating policy; where any restatement diverges, this table wins.

Exam sources additionally carry a per-item/per-unit **use mode**:

| exam use mode | meaning |
|---|---|
| `held_out_evaluation` | protected partition: excluded from practice, teaching, and generation contexts; the §8.5 leakage rules apply to exactly this partition |
| `available_for_practice` | a released past paper the learner explicitly wants to sit: items may enter the exam pool and explicit practice-exam sessions; still never semantic authority |
| `blueprint_only` | shapes task-family/capability/format distributions only |

Default: a configurable held-out fraction, remainder `blueprint_only`; the learner chooses at unit selection. Exam sources record administration year, syllabus/version, and weighting, and near-duplicate papers from the same syllabus family collapse into **one** assessment-alignment vote rather than counting as independent evidence of emphasis — the same correlation discipline the knowledge model applies to surfaces.

### 4.3 Membership owns role/scope, with unit-level overrides

```yaml
source_sets:
  - id: sourceset_linear_algebra_foundations
    subject_id: linear-algebra
    title: Linear Algebra Foundations
    members:
      - source_id: src_axler_3e
        revision_id: srcrev_axler_3e_ab12cd34   # pinned; newer revisions require confirmation
        default_role: primary_textbook
        scope:
          - unit_id: chapter_02
          - unit_id: chapter_04_exercises
            role_override: problem_set
        priority: 1
```

- Authoritative `role`/`scope`/`priority` live on membership; the source note carries only `suggested_role`/`imported_scope` hints. One source of truth.
- `revision_id` is required and pinned. `source_id` lets the system discover later revisions without silently changing the collection. The manifest snapshots both.
- A unit entry MAY carry `role_override` (a textbook chapter's exercise section acts as a problem set).
- UI never exposes numeric priority: "Use as primary" / "Alternate explanation" / "Supporting reference" derive it.
- Sets are scheduling-neutral. Goals may list `source_set_ids: []`; sets never reference goals. Same source, multiple sets, different role/scope. Empty scope = whole artifact.

## 5. User journey and experience contract

The UI calls a source set a **source collection** and curriculum output a **study map**. Internal terms (`artifact`, `revision`, `ExtractionRun`, `bootstrap`, `append`, `identity lock`) appear only in advanced details and diagnostics.

### 5.1 Intent before mechanics

The primary entry point asks what the learner wants to understand or do, their current level, desired depth, and whether the outcome is general learning, reference mastery, or exam preparation. This seeds a `SynthesisBrief`; it does not create scheduling semantics on the source collection.

When the brief's outcome is exam preparation (or the user opts in), the same flow can end by creating the **Goal** alongside the study map — due date, target recall, and facet scope wired directly to the freshly minted canonical facets/blueprints — so intent capture happens once, not twice: the goal wizard and the brief are one conversation. The brief itself still creates no scheduling semantics on the collection; the goal does, exactly as goals always have.

### 5.2 Add sources with progressive disclosure

Files and URLs enter the vault-level library without requiring a subject, role, scope, or collection first. LearnLoop resolves identity, detects existing revisions, performs the approved local extraction, and renders each source independently as soon as it is ready. A partial batch remains useful.

Only ambiguous work/edition matches, extraction problems affecting selected material, unclear authority/licensing, and externally assisted processing require immediate user decisions. Role suggestions are editable and are confirmed when the user adds the source to a collection.

### 5.3 Inspect health and choose units

The source card opens an outline tree showing chapters/sections, page ranges or timestamps, approximate processing size, structural signals (examples/exercises/equations/figures), extraction warnings, and inventory status. Users choose units before pedagogical LLM work whenever deterministic structure is available. Unit-boundary corrections are stored as user overrides over the ExtractionRun so re-extraction does not discard them.

### 5.4 Review collection readiness and build plan

The collection view reports complementary roles, weak semantic coverage, assessment/task-family coverage, missing explanation or practice material, selected revisions, unresolved extraction problems, and expected model work. For exam preparation it separately reports "what the sources teach" and "what the assessment appears to demand." Typical users see plain-language effort/cost indicators; advanced details show stage-level input/cached/output token estimates, call counts, provider choices, and cache reuse. The system automatically routes **Create study map** or **Update study map**.

### 5.5 Review by exception, then maintain

Routine imports, cached inventories, exact span attachments, assessment-family aggregation, and safe retries do not create review burden. Users review conflicts, notation choices, destructive unlocked changes, low-confidence provenance, and any proposed use of an exam as semantic authority. After build, the collection remains a living workspace: update available, stale evidence, extraction repair needed, missing prerequisite coverage, assessment-blueprint gap, or a newly discovered source gap. Users can leave the screen while work continues and return to durable progress, partial results, actionable failure messages, and actual-versus-estimated token usage.

### 5.6 Privacy and consent

Every action distinguishes local document processing from external AI. Before any source page/image/text leaves the device, the UI names the provider, purpose, selected pages/units, and whether results will be cached. Consent is scoped to that operation and recorded in the job payload/manifest; a global extraction toggle is insufficient.

### 5.7 Tauri surface (deliverables)

The v2 journey lands as concrete screens/components, extending the existing IngestScreen/ProposalsScreen rather than multiplying navigation:

- **Source library**: card grid (readiness, health, suggested role, work/edition match, update-available), replacing the single-source form as the ingest tab's home; **Quick add** is the prominent entry on this screen.
- **Outline & unit selection**: per-source tree with page ranges, structural signals, extraction warnings, inventory-cached markers, and approximate token size per unit.
- **Build plan**: per-stage token estimate vs configured ceilings, cache savings, Create-vs-Update routing, and the consent summary for anything leaving the device.
- **Batch progress**: the checkpoint ladder per job with live phase/window counts, actual-vs-estimate token bars, `waiting_for_input` surfaced as actionable cards (unit choice, consent), cancel/resume.
- **Coverage matrix**: sources × facets/LOs/task-families heatmap with semantic and assessment tabs (§9.3); gap cells link to the concrete maintenance action.
- **Conflict review**: side-by-side bounded spans (PDF page + bbox preview) with the resolution vocabulary (prefer-for-context / keep both scoped / notation mapping / dismiss).
- **Provenance span peek**: popover from any facet/LO/item/feedback surface showing the cited span with page/bbox thumbnail and semantic-vs-assessment authority labeling (§9.2); escalates one tap further to the **Open in source** viewer (§9.2).
- **Study-map diff** after Update: new facets/links/conflicts, blueprint/task-distribution shift, stale links repaired — the reviewable answer to "what did adding this source change?".
- **Maintenance feed**: the §11 feed with per-type aging policies visible.
- **Registry review**: facet-contract cards (claim, conditions, examples, non-goals) with identifiability warnings and one-tap merge/coarsen actions while pre-lock (§8.7 gate output; knowledge-model §3.4 grace window).

## 6. Import actions and durable jobs

### 6.1 Progressive actions

| Action | Stages | External AI |
|---|---|---|
| **Import** | fetch → asset registration → local extraction → IR → health | never without consent; no pedagogical calls |
| **Import & inventory** | Import + outline + role-specific semantic/task/assessment inventories for selected units | inventory calls (consented by the action) |
| **Create/Update study map** | semantic synthesis + task blueprint/assessment alignment over inventories (§8) | bounded synthesis calls |

The one-shot path is re-expressed as **Quick add** (§1): the same fetch → extract → inventory → synthesize stages with defaults auto-chosen and one token-estimate confirmation. The legacy `ingest` command becomes a compatibility wrapper over it; the full journey remains Choose units → Build study map.

### 6.2 Durable batches and jobs (repository-backed)

```sql
ingest_batches (id, workflow_type, payload_schema_version,
                subject_id, source_set_id, status,
                created_at, started_at, finished_at, cancel_requested);
ingest_jobs (id, batch_id, ordinal,
             job_type, payload_schema_version, payload_json,
             status, phase, message, current_window, total_windows,
             result_json, error_json, usage_json,
             attempt_count, cancel_requested,
             worker_id, heartbeat_at, created_at, started_at, finished_at);
ingest_job_dependencies (job_id, depends_on_job_id,
                         PRIMARY KEY(job_id, depends_on_job_id));
```

- `workflow_type`/`job_type` are application-validated open strings rather than SQL CHECK vocabularies that require a migration for each new workflow. Core types include `import`, `extract`, `inventory`, `legacy_ingest`, `exam_ingest`, `bootstrap_synthesis`, `append_synthesis`, and `extraction_repair`.
- Status vocabulary: `queued | running | waiting_for_input | completed | failed | blocked | cancelled`. A dependency failure makes downstream jobs `blocked`, not failed. `waiting_for_input` supports unit selection or explicit external-AI consent without holding a worker lease.
- Dependencies make inventory wait for extraction and synthesis wait for every selected unit inventory. One worker drains eligible jobs sequentially (no competing vault writes). Lease = `worker_id` + `heartbeat_at`; on startup expired `running` → `failed(interrupted)`, `queued` resumes.
- **Worker host:** the sidecar hosts the drain loop while the app runs; CLI-initiated batches are drained by the CLI in the foreground when no sidecar holds a lease. Both hosts use the same lease mechanism, so exactly one drains at a time. When the app and CLI both exit, work pauses and resumes on next open — the UX promise is "leave the screen and come back", not "continues with the app closed".
- **Checkpoint ladder** — every stage independently resumable: `acquired → registered → extracted → inventoried → synthesized → proposed → applied`. Failed batches retain successful artifacts; retries are keyed by asset hash (import), extraction request hash (extract), unit semantic hash (inventory), synthesis manifest (synthesis). Users can continue partially successful batches.
- `payload_json` snapshots the preflight token/call estimate and provider limits. `usage_json` records per-call input/cached/output tokens and cache hits; batch usage is a deterministic sum over attempts so retries remain visible rather than overwritten.
- Batch status is derived from member jobs and can represent partial completion. Cancellation never discards completed artifacts; resume creates new attempts only for unfinished or invalidated jobs.

### 6.3 Core command/RPC surface

- CLI: `learnloop import <source...> [--inventory] [--json] [--progress-json]`; `learnloop inventory <revision> --unit ...`; `learnloop source-set create|add|update|list|show`; `learnloop synthesize <set> [--mode auto|bootstrap|append]`; `learnloop source-coverage <set>`.
- Importing to a collection MAY pass membership defaults, but mixed per-source roles/scopes use a JSON input file or subsequent `source-set add/update`; positional flag repetition is not the authoritative batch contract.
- Sidecar: start/get/list/cancel/resume batch/job, source library/detail/outline/health, save unit selection, create/update collection, acquisition preview/build plan, Create/Update study map, coverage/provenance/conflict reads and decisions.
- Existing single-source `start_ingest` and `learnloop ingest` remain compatibility wrappers over the Quick add one-source workflow (§6.1).

## 7. Unit inventories

The cacheable inventory unit is the **DocumentUnit** (chapter/section), not the whole source:

```sql
source_unit_inventories (
  source_revision_id, extraction_id, unit_id, unit_semantic_hash,
  inventory_profile,                 -- semantic | practice | assessment | combined
  inventory_schema_version, prompt_version, provider, model,
  inventory_json, created_at,
  UNIQUE(source_revision_id, unit_id, unit_semantic_hash, inventory_profile,
         inventory_schema_version, prompt_version, provider, model)
);
```

- Selecting another chapter inventories only that chapter; repairing one OCR page invalidates only its unit; large textbooks never enter one context.
- Source-level inventory = deterministic merge/view over unit inventories.
- Inventory schema is role-aware but shares one envelope. Explanatory, practice, and assessment profiles may omit irrelevant sections; they never force every source through the most expensive prompt. Because membership role can differ by collection, `inventory_profile` is part of cache identity; an existing richer `combined` inventory MAY satisfy a narrower profile deterministically when its schema version guarantees the required fields.
- Inventory requested through a collection uses the confirmed membership/unit role. Inventory requested before role confirmation shows the profile/cost choice; `combined` is available but is not silently selected when a narrower profile is sufficient.
- Inventory contract:

  ```text
  SourceUnitInventory
    unit_id, semantic_hash, outline_summary
    concept_mentions[]      mention_id, name, aliases, notation[], span_ids[]
    claims[]                claim_id, kind(definition|theorem|procedure|assumption|example),
                            statement, preconditions[], postconditions[], applicability[],
                            examples[], counterexamples[], non_goals[],
                            concept_mention_ids[], prerequisite_hints[], span_ids[]
    procedure_signals[]     procedure_id, contract, ordered_steps[], preconditions[],
                            common_invalid_steps[], observable_step_span_ids[]
    practice_signals[]      signal_id, kind(exercise|worked_example|solution),
                            task_family, valid_method_hints[], response_structure,
                            capability_demands[], representation, difficulty_signal,
                            concept_mention_ids[], span_ids[]
    assessment_signals[]    assessment_item_id, held_out, topic_mentions[], task_family,
                            capability_demands[], representation, response_format,
                            point_or_time_emphasis, method_visibility, span_ids[]
    misconception_signals[] statement, confused_concept_mentions[],
                            trigger_conditions[], invalid_step, repair_hint, span_ids[]
    coverage_claims[]       concept_mention_id, depth, pedagogical_forms[], span_ids[]
    inventory_warnings[]    unresolved_span, extraction_health, ambiguous_unit, ...
  ```

- Every inventory assertion cites provided span ids; the model never invents paths/locators. Service-assigned inventory ids derive from `(unit_id, window_ordinal, item_ordinal, normalized-content-hash)` and remain stable for an unchanged semantic view.
- Window merge is deterministic concatenation/dedup by assigned id, not fuzzy semantic merging. Cross-window/source equivalence is synthesis work; retaining separate mentions preserves provenance and prevents accidental claim collapse.
- Per-source prerequisite hints remain hypotheses. They may inform synthesis and later facet→unit review lookup, but they never update learner mastery or become identity locks by themselves.
- Inventory rows are candidates, not canonical facets, recipes, or learner evidence. Synthesis decides semantic identity and task composition under the knowledge-model gates.
- `assessment_signals` is mandatory for selected `exam` units and optional elsewhere. Authority follows the §4.2 matrix: an exam occurrence remains an inventory candidate and cannot populate `claims[].statement` as canonical truth or promote prerequisite hints without corroboration.
- Held-out exam prompts/answers remain in bounded cited spans and the protected exam pool; downstream consumption follows the §8.5 span/leakage protocol and the §4.2 use modes (task-family aggregates flow freely; held-out wording never does).
- A deterministic exam profile aggregates task-family/capability/representation/format counts and point/time emphasis. The profile is normally 1k–3k tokens per exam; per-item structured output targets roughly 80–200 tokens. Adding assessment alignment reuses the same inventory input rather than making a second full-source call.
- Never auto-chained after plain Import.

## 8. Synthesis

### 8.1 Modes, gated by identity locks (not subject age)

- **Create study map (bootstrap)**: N-way synthesis over member unit inventories into a fresh semantic registry, task/assessment contracts, and curriculum. Legal only where nothing touched is identity-locked; free to restructure aggressively.
- **Update study map (append)**: new/changed unit inventories diffed against the existing semantic and task map; additive op vocabulary wherever locks exist (§10).
Routing is automatic; the UI shows Create vs Update.

### 8.2 Identity locks

Destructive ops (LO/concept/facet semantic merge or split, blueprint/recipe identity change, assessment-contract rewrite, criterion re-key/target/dependency change, deactivate) are legal exactly where no lock exists. One authoritative curriculum-layer `can_apply(operation)` computes direct and transitive lock reasons from practice attempts, immutable assessment-contract versions, criterion observations/grading revisions, goal facet-capability/blueprint scope, exam pools, probes, misconceptions, legacy and new facet state, capability ledgers, unresolved-cause factors, item fingerprint/repair maps, and the protected concept/rubric/error closure. `identity_locks(vault, repo, subject_id)` is a read adapter over this API, not a second enumerated implementation.

Enforcement points:

1. before synthesis (typed refusal `subject_identity_locked` for bootstrap);
2. before auto-apply;
3. at accept-time, while holding the vault mutation lock.

Every update/deactivate proposal item also stores an `expected_target_hash`. Acceptance refuses if the target changed after synthesis, even if lock state did not. A cross-process vault mutation lock serializes the final lock/target recheck, YAML mutation, derived-state sync, proposal decision, and evidence writes that could create a competing lock. Mechanism: an OS-level advisory file lock at `.learnloop/vault.lock` (flock-style, acquire-with-timeout, holder pid/purpose written for diagnostics), taken by CLI and sidecar alike around the critical section — nothing of the kind exists today, so this is new M5 infrastructure, not a formalization of current behavior. A pre-write fingerprint check without this shared critical section does not claim to close the race.

Destructive operations that are legal on unlocked identities are still review-required; legal never means silently auto-applied. Facet identity locks are independence-gated (knowledge-model §3.4): pre-lock, a reviewed facet merge/split is legal and cheap (merge-map resolution, no evidence rewrite); `can_apply` owns the lock check. Knowledge-model §3.4/§12 is the **single normative lock policy**; this section and §10.3 are its ingestion-side enforcement view — on divergence, the knowledge-model contract wins. Restructure-with-history is a future explicit migration feature, never reachable by re-running bootstrap — promoted to the first post-core specification. Sanctioned facet renames stay `facets.yaml` aliases + `merge_facet_recall_aliases` via doctor.

### 8.3 Synthesis brief

Captured intent-first (step 1 of the journey): learner level, depth/rigor, objectives/outcome, preferred notation or primary source, include/exclude topics, granularity, and assessment-alignment intent. All optional with defaults. Stored per synthesis run in the manifest — same sources can yield an intro course, exam review, or advanced treatment. An exam-preparation brief enables assessment alignment without elevating exam sources to semantic authority. Users never need the word "bootstrap".

### 8.4 Immutable synthesis manifests

```sql
synthesis_manifests (
  id, manifest_hash UNIQUE, source_set_id, membership_json,
  revision_ids_json, asset_hashes_json, extraction_ids_json,
  unit_inventory_versions_json,
  scope_json, brief_json, prompt_version, schema_version, provider, model,
  extractor_versions_json,          -- marker/pypdf versions + model artifacts, pinned
  curriculum_snapshot_hash, facet_registry_hash, task_graph_hash,
  assessment_schema_version, learner_model_contract_version,
  lock_fingerprint, token_budget_json, estimated_usage_json, created_at
);
synthesis_runs (
  id, manifest_id, mode, agent_run_id, proposal_id,
  span_request_json, resolved_span_hashes_json,
  coverage_decisions_json, actual_usage_json,
  status, created_at, completed_at
);
```

The immutable input manifest is persisted before model execution; outputs and mutable run status live in `synthesis_runs`. `agent_runs.input_context_hash = manifest_hash` remains the cache seam. Identical manifest → reuse the completed agent run only when the registry/map/task/assessment/model-contract hashes also match by construction. Append output depends on existing-map content, so a lock fingerprint alone is insufficient. Manifests answer "why did the curriculum change," "what assessment distribution shaped it," and "what token budget was authorized."

### 8.5 Span-request protocol

Synthesis receives **inventory views** plus explicitly requested **evidence views** — never full raw text:

1. Pass 1 (`run_source_set_synthesis` or `run_append_reconciliation`) gets role-specific unit inventories + brief + bounded existing-map neighborhood; it may return `span_requests: [{extraction_id, span_id, purpose}]`.
2. LearnLoop resolves only spans belonging to selected revisions/units. One request round, a configurable maximum request count, per-span character cap, and total token cap are enforced. Resolved content hashes are recorded on the synthesis run.
3. A bounded final pass emits one dependency-annotated `AuthoringProposal` (purpose `sourceset_bootstrap` or `sourceset_append`) through the existing pipeline plus the intent-specific rules in §10. If output exceeds the cap, it emits dependency-closed bundles sharing one manifest/run; it never splits a facet from the blueprint/item that requires it.

Source/inventory/span text is untrusted prompt data: it is strongly delimited, embedded instructions are ignored, and span requests cannot name paths or arbitrary source ids. Prompt contract: honor the brief; unify notation; pick primary definitions by semantic authority/role/priority; mint canonical facet contracts and task recipes at reviewed granularity; cite provided span ids across sources; flag genuine conflicts.

`exam`-role members participate through a separate assessment-alignment view:

- Authority follows the §4.2 matrix: exam members MAY shape assessment scope, blueprint weights, task families, capability demands, representations, formats, difficulty/emphasis, timing, and held-out evaluation design; they MUST NOT independently mint or semantically modify canonical claims, assert facet equivalence, or promote prerequisite hints to truth — such proposals require corroborating explanatory-source spans or explicit manual authority.
- Questions, answers, and solution keys in the `held_out_evaluation` partition (§4.2 use modes) remain protected/held out. Synthesis normally receives deterministic aggregate profiles and cited task metadata; exact spans are requested only to validate a task family, format, ambiguity, or conflict. The exclusion is enforced at every context builder, not only synthesis: tutor/QA source-grounded contexts, hint authoring, and practice generation all filter held-out exam spans. `available_for_practice` items bypass the leakage exclusion (the learner chose to sit them) but never gain semantic authority.
- Practice generation may use an assessment blueprint but MUST generate a fresh surface and MUST NOT reproduce held-out wording, numbers, diagrams, answer structure fingerprints that reveal the answer, or source-specific solution keys.
- Exam performance becomes learner evidence only through an explicit recorded attempt/exam-seeding flow; source coverage alone never changes mastery.

### 8.6 Planning and preflight

Two deterministic previews avoid pretending content hashes or unit coverage are known before acquisition:

1. **Acquisition preview** (before download/extraction): recognized inputs, normalized artifact identities, obvious duplicate URIs/existing revisions, local file sizes or available remote metadata, configured local extractor, and any potential external processing requiring later consent.
2. **Build plan** (after import/outline and, where requested, inventory): exact revision/asset hashes; work/edition matches; selected units and cached inventory markers; separate semantic and assessment coverage; per-stage input/cached/maximum-output token estimates; cache savings; configured ceilings/provider; extraction warnings; affected-map neighborhood; Create-vs-Update routing; estimated calls; and what will be created versus added.

Both previews perform zero pedagogical LLM calls. The acquisition preview does not promise remote accessibility or content-hash dedup before bytes are fetched. Import results are reused by the build plan, so planning never downloads/extracts the same revision twice. For PDFs with good native bookmarks, page-range selection MAY precede full marker conversion (marker supports `page_range`).

### 8.7 Deterministic quality gates

Before a synthesis proposal is persisted/presented (`services/synthesis_gates.py`):

| Gate | On failure |
|---|---|
| every span citation resolves in its cited extraction run | hard-fail |
| no entity cites outside selected scope | hard-fail |
| unit ids valid for their extraction run | hard-fail |
| every declared conflict candidate has a conflict item or explicit non-conflict disposition | hard-fail |
| no destructive op bypassed the lock guard | hard-fail |
| every new facet semantic contract and semantically updated LO has adequate authoritative provenance | downgrade to review |
| every criterion target resolves to a registered facet/capability and every dependency DAG is acyclic | hard-fail |
| every blueprint has at least one valid recipe; all recipe/criterion/applicability references resolve | hard-fail |
| proposal partial-accept dependencies form valid closure; no dependent item can outlive a rejected requirement | hard-fail |
| exam-only evidence attempts to establish a canonical claim/equivalence/prerequisite | hard-fail unless explicit manual authority |
| held-out exam text/answer appears in a teaching or generated-practice payload | hard-fail |
| token/context/output budget exceeded or content truncated | hard-fail with shard/narrow-scope action |
| practice items don't rely solely on an `exam`-role source | downgrade to review |
| no duplicate ids / dangling edges | hard-fail |
| proposed facets/criteria/recipes pass the assessment identifiability analysis (knowledge-model §11.3) | first emit a generate-discriminator need (anchor/contrast probe or item); coarsening review items only when no distinguishing assessment exists and repairs are identical |
| post-append near-duplicate facet detection (lexical/MinHash by default; optional ephemeral embedding assist, review-only) | downgrade to review (merge proposal); never auto-merge |

Typed per-gate diagnostics — never a generic "synthesis failed".

"Adequate provenance" means every created facet semantic contract and semantically updated LO has at least one in-scope, resolving span from a role allowed to support semantic authority unless explicitly marked human/manual context. Blueprint/task-demand claims may cite problem-set or exam assessment signals, clearly labeled `assessment_alignment`; those links do not become semantic authority. The conflict gate verifies contract completeness; it does not claim to detect a semantic conflict the model never declared.

### 8.8 Review economics

Require human attention only where judgment matters: extraction problems affecting selected units, ambiguous work/edition matches, cross-source conflicts, notation choices, destructive curriculum changes, unclear authority/licensing. Auto-handle deterministic imports, cached inventories, and additive provenance links.

## 9. Durable provenance

### 9.1 Entity-source links

```sql
entity_source_links (
  id, entity_type, entity_id, source_id, revision_id,
  locator NOT NULL, locator_scheme,
  relation TEXT NOT NULL CHECK(
    relation IN ('primary','support','alternate','exercise','assessment_alignment')
  ),
  extraction_id, asset_hash, span_hash, patch_id,
  status CHECK(current|stale|removed|needs_reanchor),
  stale_at, superseded_by_link_id, created_at,
  UNIQUE(entity_type, entity_id, revision_id, locator, relation)
);
```

`entity_type` includes `facet`, `learning_object`, `task_blueprint`, `practice_item`, `concept`, `concept_edge`, `rubric`, and other versioned curriculum entities. Rows are written by `apply_accepted_items` for created content and by accepted `provenance_link` items during append. This table is the authoritative aggregate multi-source provenance; YAML `provenance.source_refs` remains a compatible embedded snapshot for legacy readers. `assessment_alignment` links prove that a task/blueprint characteristic came from an assessment source, not that the source authorizes a semantic claim. Adopting a new revision marks superseded-revision links stale/removed as appropriate. Extraction-only upgrades do not make evidence semantically stale, but any link that cannot be re-anchored becomes `needs_reanchor` until repaired or reviewed.

### 9.2 Entity provenance view

From any facet/LO/blueprint/practice item: supporting sources with exact spans (page + bbox preview for PDFs), which source is semantic authority, alternate explanations and notation, which assessment sources shaped the task distribution, known conflicts, staleness, and the synthesis run that introduced it (patch → agent run → manifest). Semantic and assessment-alignment provenance are displayed separately so a learner never reads "appeared on an exam" as "defines the concept." Sidecar `get_entity_provenance` + Tauri panel from Library/LO detail and feedback contexts.

**Open in source (phased):** a scoped single-pane source viewer launched from span peek, provenance rows, and tutor citations — deliberately not a full dual-pane reading mode. The minimal PDF/HTML viewer ships with M6 provenance/conflict review, because reviewers accepting conflicts, authority decisions, and facet merges must inspect cited evidence in place; the embedded video player follows at the M7/M8 boundary:

- **PDF**: render the cited page (page image via the extraction asset pipeline or on-demand rasterization) with the span's bbox/polygon highlighted; prev/next page navigation; multiple cited spans on one page all highlight. Composed extraction runs resolve each block against the run that produced it (§2.3 repair composition).
- **YouTube**: embedded player rather than external open (media-extended-style, cf. https://github.com/aidenlx/media-extended): the `time_range_v1` locator seeks the embedded IFrame player to `start` and marks the cited range on a small timeline strip; the embed uses the privacy-enhanced host (`youtube-nocookie.com`) and requires network; videos that disallow embedding fall back to opening externally at the timestamp. Loading the embed is an explicit-action fetch of the already-imported public URL, not source egress — stated in the privacy copy, no consent dialog required.
- **HTML/text**: rendered note body scrolled to the cited block anchor with the span highlighted.
- Read-only; no annotations; no synchronized dual-pane scrolling. Every view records a `source_exposure` event — this viewer is what makes exposure instrumentation (§11) trustworthy, and it is the click-through target for tutor citations.

Full side-by-side span navigation (dual-pane, sync-scroll, cross-source comparison reading) remains a follow-on beyond this scoped viewer.

### 9.3 Coverage report

Set members × facets/LOs/task-blueprints matrix from `entity_source_links` + unit inventories. Coverage keeps three axes rather than overloading one cell:

- **inventory evidence**: claimed forms `definition | explanation | example | exercise | assessment | omitted/unknown`;
- **curriculum linkage**: `applied | proposed | stale | unlinked` with source role `primary | support | alternate | exercise`.
- **assessment alignment**: task families, capabilities, representations, formats, emphasis, and held-out coverage with linkage `applied | proposed | intentionally_held_out | unlinked`.

Before synthesis this powers a deterministic collection-readiness report: no primary explanation, instruction-light/exam-heavy, no practice material, assessment task families with no teaching coverage, teaching content with no representative assessment, conflicting revisions, weak selected-unit coverage, extraction health blocking a chosen unit, or material not yet inventoried. After synthesis it exposes semantic claims and assessment signals that were intentionally omitted/unlinked/held out, with the synthesis disposition/rationale when available. CLI first, then sidecar + Tauri.

## 10. Append reconciliation (core release)

Append is required for the core release: after the first study map exists, every added source, newly selected unit, or adopted source revision must have a safe incremental path.

### 10.1 Reconciliation context and routing

`append_source(root, source_revision_id, subject_id, client)` loads the new/changed role-specific inventories plus the deterministically selected affected-map neighborhood (concepts, facets/contracts, LOs/blueprints, recipes, criterion summaries, aliases, fingerprints/surface families, notation, semantic and assessment provenance, conflicts, and lock reasons) and calls `run_append_reconciliation`. The manifest records the neighborhood ids/hashes and why they matched. Adding a member/unit to an existing study map routes here automatically. Adopting a new revision uses the same reconciler with `change_kind=source_revision_changed` and the old/new span diff.

### 10.2 Intent and storage vocabulary

`reconciliation_intent` remains separate from `operation`, but additive intents use specialized append-only item types instead of pretending an arbitrary entity update is safe:

| Intent | Proposal item type | Operation | Effect | Default policy |
|---|---|---|---|---|
| `new_coverage` | existing curriculum type | `create` | create concept/LO/practice/etc. | normal validation |
| `span_attach` | `provenance_link` | `create` | insert supporting `entity_source_links` row | auto-apply when exact/in-scope |
| `alternate_explanation` | `provenance_link` | `create` | insert link with `relation=alternate` | auto-apply when exact/in-scope |
| `assessment_alignment` | `provenance_link` | `create` | attach exam/problem task evidence to a blueprint with `relation=assessment_alignment` | auto-apply when exact/in-scope and no semantic mutation |
| `notation_mapping` | `notation_mapping` | `create` | append a contextual notation equivalence | review-required |
| `conflict` | `source_conflict` | `create` | persist an unresolved two-sided conflict | review-required |
| `restructure_unlocked` | existing curriculum type | `update` or `deactivate` | semantic replacement/removal | review-required; invalid if locked |

The proposal schema/database expands the current closed curriculum vocabulary to include `facet` and, where stored separately, `task_blueprint`, plus `provenance_link | notation_mapping | source_conflict`. `create` may carry a target for relationship/annotation items. The existing operation vocabulary remains `create | update | deactivate`; `operation=none` is forbidden. Specialized apply handlers write their tables and do not rewrite the target LO YAML. Pure additivity is verified by item type and payload, not trusted from an LLM-provided intent.

Every proposal item MAY declare `depends_on_client_item_ids`. Persistence normalizes these into:

```sql
proposed_patch_item_dependencies (
  proposed_patch_item_id, depends_on_patch_item_id,
  PRIMARY KEY(proposed_patch_item_id, depends_on_patch_item_id)
);
```

`proposed_patch_items` also gains `dependency_status TEXT NOT NULL CHECK(dependency_status IN ('pending','ready','blocked'))` and a typed blocking-reason payload. Facet → LO/blueprint → rubric/criterion → practice-item dependencies are mandatory when created together. Acceptance computes the transitive dependency closure under the vault mutation lock. A dependent item with a rejected/unaccepted prerequisite is `blocked`, not partially applied; accepting a closure is one **logical** YAML/DB transaction. Because a filesystem and SQLite cannot commit atomically together, acceptance uses a write-ahead protocol: a durable intent record (the accepted closure plus target file contents/hashes) commits to SQLite first; YAML is written to staged temp files, fsynced, and atomically renamed into place; the intent record is then marked applied. Startup/doctor recovery completes or rolls back any intent record left mid-flight, and application is idempotent — the vault mutation lock closes races, this protocol closes crashes. Output sharding and user partial decisions preserve the same closure.

```sql
notation_mappings (
  id, subject_id, entity_type, entity_id,
  canonical_notation, alternate_notation, context,
  source_id, revision_id, locator, patch_id,
  status CHECK(active|superseded|rejected), created_at
);
source_conflicts (
  id, subject_id, entity_type, entity_id,
  left_source_id, left_revision_id, left_locator,
  right_source_id, right_revision_id, right_locator,
  statement, status CHECK(open|resolved|dismissed),
  resolution_json, patch_id, created_at, resolved_at
);
```

Accepting a conflict item means acknowledging/persisting an open conflict, never applying either competing definition. Rejecting it means the proposed conflict was not valid. Resolution is a later explicit action: prefer one source for a defined context, preserve both scoped meanings, add a notation mapping, or dismiss.

### 10.3 Lock and review policy

- `span_attach`/`alternate_explanation` auto-apply only if the target still matches `expected_target_hash`, every cited span resolves inside the selected revision/unit, the relation is not already present, and no existing field is removed or replaced.
- `assessment_alignment` auto-applies only to task/blueprint metadata or provenance, never to a facet semantic contract or prerequisite truth (exam-only semantic mutation is invalid per the §4.2 authority matrix).
- `notation_mapping` is additive but normally reviewed because symbol equivalence can be context-dependent.
- `conflict` is always reviewed and shows both bounded evidence spans side by side.
- `restructure_unlocked` is legal only when every touched identity is unlocked, target hashes match, and the proposal is explicitly accepted. On a locked entity it is `invalid`, not merely review-required.
- Lock legality follows the knowledge-model §3.4/§12 normative policy via §8.2: any operation that breaks the protected identity closure (the §8.2 destructive-op list) is invalid when locked; a semantic-preserving alias rename remains sanctioned; a capability residual activation is learner state, not an ingestion mutation.
- Any unexpected update/deactivate outside `restructure_unlocked` fails the append vocabulary gate.

### 10.4 Revision refresh behavior

When the user adopts a new source revision, import/extraction first produces a deterministic old/new block diff. Unchanged/re-anchored spans retain links. Changed/removed spans mark affected links and entities for reconciliation. Append may attach replacement spans, add coverage, record a conflict, or propose an unlocked restructure; it never silently deletes knowledge or migrates evidence. A partially refreshed source remains usable, with unresolved stale links visible in the collection and provenance views.

### 10.5 Append UX

The collection calls this **Update study map** and previews separate semantic and assessment changes: new coverage/facets, blueprint/task-distribution adjustments, capability or representation gaps, additional support, alternate explanations, notation choices, conflicts, stale links repaired, estimated/actual tokens, and unlocked restructure candidates. Routine span and assessment-alignment attachments collapse into summaries. Review focuses on conflicts, notation, semantic changes, unexpectedly large task-distribution shifts, or any attempt to use exam material as semantic authority. Per-item accept/reject respects dependency closure and links to exact authorized spans without exposing held-out answers.

## 11. Maintenance and source-outcome analytics

The core release includes the maintenance feed required to operate append safely: new revision detected; update available; N links stale/removed/need re-anchoring; a selected unit needs re-inventory; an append job is partially complete; a conflict remains open; learner failures suggest missing prerequisite coverage; an assessment task family lacks teaching coverage; a taught blueprint lacks representative assessment; token estimate materially exceeded actual budget; or the collection lacks practice material for an LO. Every notice links to one concrete action and can be dismissed/snoozed without changing source or curriculum state. Every notice **type** also declares an aging policy — auto-expiry, auto-resolution when the underlying condition clears, or escalation after N snoozes — so the feed stays bounded and trustworthy instead of accumulating into review debt; a feed nobody reads silently degrades review-by-exception into review-by-nobody.

Source-outcome analytics are a post-core read-side follow-on. They report **provenance-outcome associations**, not source effectiveness: repeated failure despite apparent coverage, alternate-explanation exposure preceding resolution, or concepts needing more examples/practice sources. Output = additive improvement suggestions (append proposals, generation needs), never direct state writes or automatic source ranking. Claims involving an explanation require a lightweight `source_exposure` event (tutor citation, review opened, provenance span viewed), minimum sample thresholds, and visible uncertainty; coverage alone does not prove the learner saw the source.

For prerequisite diagnosis the ingestion integration stays narrow: a trustworthy facet/concept → source unit → span lookup. Diagnosis itself belongs to the learning layer.

## 12. Non-goals

- No claim graph, embeddings, or vector store **as identity or matching infrastructure**. Ephemeral, review-only similarity assists (lexical/MinHash by default; optional embedding assist) are permitted for proposing duplicate-facet review items; their outputs are never persisted or treated as equivalence.
- Marker structured extraction is not the pedagogical inventory.
- Source sets carry no scheduling semantics; goals select sets, never the reverse.
- No parallel vault writes — batches drain sequentially.
- No fuzzy entity matching at apply time — id-based; the LLM matches against provided context. Title/alias similarity remains a doctor concern.
- No use of exam occurrence as proof of semantic truth, learner mastery, or prerequisite necessity.
- No held-out-partition (§4.2 use modes) exam question/answer leakage into teaching or routine generated-practice contexts.
- No all-pairs source comparison or full-map resend on every append.
- Re-extraction never alters learning evidence; inventory regeneration never directly alters curriculum.

## 13. Migration and back-compat

- Legacy subject-scoped canonical-source notes: readable forever; their `heading_path_v1`/time locators resolve forever (replay determinism).
- Legacy notes are indexed into `SourceArtifact`/`SourceRevision` rows in place; migration does not move or rewrite user files. New imports use the vault-level layout.
- Legacy markdown `content_hash` retained on old notes; new identity uses the §2.2 hash model (asset / extraction request / extraction result / semantic).
- Existing `.learnloop/source-cache/pdf` markdown cache remains valid for legacy reads; new extraction cache is keyed per §2.5 and stored as IR.
- `SourceKind` stays on the codex prompt path until prompts migrate; new code branches on `acquisition_kind`/roles only.
- Existing source sets without revision pins resolve their referenced note to one revision during load and are rewritten only through an explicit source-set save.
- Migration of `proposed_patch_items` expands the closed item-type/target CHECKs for `facet`, optional separately stored `task_blueprint`, `provenance_link`, `notation_mapping`, and `source_conflict`; adds dependency rows; and keeps old proposal rows/operations valid unchanged. `content_events.entity_type` (migration 002) carries the same closed CHECK and gets the same rebuild — the new apply handlers write content events for the new entity types.
- The legacy `textbook_chapter` requirement of pre-existing LO anchors (`_validate_textbook_targets`) does not apply on the v2 path: library-first import commits to no subject, role, or LO.
- V2 manifests snapshot curriculum/facet/task/assessment/model-contract hashes and token budgets. Old manifests remain readable but are never cache-equivalent to a v2 synthesis run.
- Existing exam inventories without assessment signals remain legacy-readable but require role-specific re-inventory before assessment alignment; they never gain semantic authority by fallback.
- Knowledge-model mvp-0.7 activation is vault-wide until per-subject version routing exists. M6 application refuses to create learnable v2 content inside a frozen legacy vault; preview/proposal generation may continue without accepting attempts.
- The current in-memory ingest jobs are not treated as durable migration data. Jobs active during upgrade are reported interrupted; completed source/proposal artifacts remain discoverable and re-queueable through normal idempotency keys.

## 14. Verification (acceptance)

- Import identity: same artifact identity + same bytes → same revision; different artifact identities + same bytes → distinct revisions with shared raw blob allowed; same artifact + changed bytes → linked new revision.
- Marker upgrade → new ExtractionRun over the same revision. Exact span re-anchors stay current; unresolved locators become `needs_reanchor`, never falsely current or semantically stale.
- Extraction cache: version-pinned key (upgrading marker version changes the key); IR round-trip; semantic hash stable under cosmetic HTML changes.
- Marker adapter contract: chunks/ToC/page stats/figures map into IR; pypdf and non-PDF trivial IR satisfy the same downstream tests; missing Marker degrades explicitly to the approved fallback.
- Outline determinism: same extraction run → identical outline view, zero agent runs.
- Unit inventory caching: repairing one page invalidates only its semantic-hash-changed unit; other units' semantic/task/assessment inventories are reused across collections.
- Role-aware inventory: explanatory unit emits conditioned claims/procedure signals; problem set emits task/method signals; exam emits held-out assessment signals and aggregate profile without promoting exam text to canonical claims.
- Consent: plain Import performs no external egress; targeted repair records provider/pages/consent; declining repair leaves a usable flagged extraction.
- Queue persistence across restart; lease expiry → `interrupted`; dependency failure → downstream `blocked`; waiting-for-input holds no lease; batch cancel/resume runs only unfinished jobs; partial success preserved.
- Token budgets: preflight emits per-stage input/cached/output/call estimates; every call records usage; over-budget stages shard/pause without truncation; retry usage remains visible.
- Scaling: add N comparable sources through append → inventory cost linear in new selected units and each synthesis sees a bounded affected neighborhood; a planted full-map resend/all-pairs implementation fails.
- Manifest idempotency: immutable input manifest exists before the agent run; identical complete manifest → cached proposal; changing a revision/scope/unit inventory/curriculum snapshot/facet registry/task graph/assessment schema/model contract/budget → new manifest/run linkage.
- Race tests: bootstrap/append proposal → attempt inserted or target manually edited → acceptance refused while holding the shared mutation lock; no partial YAML/DB decision is left behind.
- One source, two sets, different roles/scopes; unit `role_override` honored in synthesis context.
- New revision is detected but pinned membership does not advance automatically; adopting it triggers append. Changed/removed links become stale/removed; unchanged links re-anchor.
- Each quality gate → typed diagnostic, including recipe/DAG/dependency closure, exam authority/leakage, and token truncation gates.
- Proposal dependencies: reject a newly proposed facet while accepting its dependent LO/item → dependents blocked and no dangling writes; accept the closure → one logical write-ahead transaction (§10.2).
- Append vocabulary: exact semantic or assessment `provenance_link` auto-applies without rewriting LO YAML; notation mapping and conflict require review; `operation=none`, arbitrary locked update, exam-only semantic mutation, and locked facet/assessment-contract rewrite are invalid.
- Conflict persistence/resolution: accepting creates an open two-sided row; rejecting creates none; resolving preserves both evidence locators and audit history.
- Exam alignment: textbook + past exam → facets/claims cite textbook authority while exam shifts declared blueprint distribution/capability/representation coverage; exact held-out item/answer never appears in generated practice; source coverage alone produces no learner evidence.
- Fixture end-to-end: library import of 2–3 small explanatory/practice/exam sources → outline → unit selection → role-specific inventories → semantic + assessment coverage → Create study map; add a source and adopt a changed revision → bounded-neighborhood Update study map; locked-subject Create → typed refusal.
- Replay safety: `rebuild_derived_state` after apply — identical modulo new entities.
- Identifiability gate: a synthesis proposal with two facets no item pool can distinguish yields a generate-discriminator need first, and a coarsening review item when no distinguishing assessment exists and the repairs are identical; post-append near-duplicate facets yield merge review proposals, never auto-merges.
- Quick add: one URL through Quick add produces a study map on v2 machinery (library rows, extraction run, inventories, manifest, gates) with exactly one user confirmation on the happy path.
- Worker host: sidecar and CLI never drain concurrently (lease-contention test); app closed mid-batch → resume on reopen re-drains only unfinished jobs.
- Locator backfill: existing refs get shape-detected schemes (`heading_path_v1`, `time_range_v1`, `arxiv_label_v1`) and all still resolve.
- Open in source: a `block_span_v1` PDF locator renders its page with the bbox highlighted; a `time_range_v1` locator seeks the embedded player to `start`; a non-embeddable video falls back to external open at the timestamp; every view records a `source_exposure` event.
- Hash split: retry of an incomplete extraction keys on the request hash (computable pre-execution); the result hash is recorded only on completion and drives cache/view identity.
- Crash recovery: killing the process between the DB intent commit and the YAML rename — and between the rename and the applied mark — leaves a vault that startup/doctor recovery restores to a consistent applied-or-rolled-back state; acceptance includes process-kill tests at each boundary, not only concurrent-mutation tests.
- Exam use modes: an `available_for_practice` past paper can be sat as an explicit practice exam without tripping leakage gates; `held_out_evaluation` items never appear in teaching/generation/tutor contexts; near-duplicate papers from one syllabus family collapse to one assessment-alignment vote.

## 15. Milestones and release boundary

The **core v2 release** is M1–M7. Milestones remain independently testable, but v2 is not product-complete until both Create and Update study-map journeys work end to end.

- **M0 — Spec** (this document).
- **M1 — Source layer**: work/artifact/revision identity + the §2.2 hash model + Document IR + marker chunk/ToC/page-stats adapter + version-pinned extraction cache + block-role hints + vault-level `sources/` library home + locator/re-anchor registry. (pypdf/HTML/YouTube/text produce the same IR contract.)
- **M2 — Durable workflows and usage accounting**: batches/jobs/dependencies schema, sequential leased runner, waiting/blocked/partial states, resume/retry ladder, per-call estimates/usage, batch CLI + sidecar RPCs + library/queue UI with source cards, health, and token progress.
- **M3 — Outline, selection, and budget planning**: outline view, deterministic probe, unit selection UX, semantic-vs-assessment role confirmation, per-stage build plan, affected-neighborhood estimate, extraction-health repair flow (consent-gated).
- **M3.5 — v2-lite (named shippable milestone)**: the M1–M3 stack (IR extraction, health/repair, durable jobs, library, outline/unit selection) feeding the *legacy* single-source synthesis. User-visible value (better extraction, unit selection, durable queue, source cards) ships while KM1/KM2 land, and the marker IR work is de-risked with real use before the new knowledge model depends on it. KM1 (which gates M4) proceeds in parallel — it is contracts/doctor/proposal-schema work with little coupling to the extraction layer.
- **M4 — Sets and role-specific inventories**: source-set entity with unit-scope/role overrides; semantic, procedure/task, misconception, and held-out assessment inventory contracts; unit cache; semantic + assessment coverage preview. Knowledge-model KM1 contracts are a hard prerequisite before M4 schema freezes.
- **M5 — Safety, provenance, and dependency foundation**: authoritative protected closure + shared mutation lock + target hashes; complete manifests/runs/budgets; proposal dependency closure; facet/task `entity_source_links`; notation/conflict tables; authority/leakage/token/recipe gates; provenance and coverage services.
- **M6 — Create study map**: synthesis brief (with optional goal creation, §5.1), Quick add, N-way sharded inventory synthesis, canonical facets + task blueprints/recipes/criterion contracts, assessment-alignment lane, bounded span pass, dependency-aware proposal/application, synthesis-time identifiability gate, provenance panel with the minimal Open-in-source viewer (PDF page + bbox, HTML anchor — required by conflict/authority/merge review, §9.2), semantic/assessment coverage, bootstrap evidence refusal. Knowledge-model KM2 is a hard prerequisite to applying a learnable map. M6 also ships the **synthesis quality eval harness**: a hand-authored gold registry + blueprint set for one or two fixture chapters, with facet precision/recall, over-fragmentation and duplicate rates, missing-condition detection, recipe validity, criterion-target accuracy, provenance accuracy, and repair-distinctness (do synthesized distinctions imply different instructional repairs?) measured against it per prompt version — deterministic gates check structure and the sim harness checks evidence math, but this is the only instrument that checks whether synthesis mints *good facets*, the highest-leverage LLM judgment in the system.
- **M7 — Update study map (core)**: bounded affected-neighborhood append, specialized semantic/assessment additive handlers, per-entity policy, revision diff/reconciliation, conflict/task-alignment review UI, maintenance feed, end-to-end add-source/adopt-revision journeys, linear-scaling gate, and a **lightweight exam-readiness-by-task-family report** (declared blueprint distribution × facet-capability state, with exam-calibration overlays where practice-exam data exists) — exam preparation is a primary intent, so its marquee readout cannot wait for M8; M8 ships the fully calibrated version.
- **M8 — Post-core product follow-ons**: assessment-blueprint-driven cross-source practice generation with leakage controls, the **fully calibrated exam-readiness report** (predicted score distributions per blueprint family against practice-exam Brier calibration; the lightweight version ships in M7), **tutor citations** (tutor/QA answers cite `entity_source_links` spans with page/bbox preview — nearly free once provenance lands, and the single best trust-building consumer of it), exam acquisition UX unification (evidence seeding remains explicit), figure-to-vision escalation, the **Open-in-source video embed** (§9.2 — the PDF/HTML viewer ships in M6; the embedded YouTube player with timestamp seek lands here, and tutor citations + `source_exposure` instrumentation build on the viewer family), full dual-pane side-by-side span navigation (beyond the scoped viewer), `source_exposure` instrumentation, and provenance-outcome associations.
- **Restructure-with-history/evidence migration is the first post-core specification**, not indefinitely deferred: identity locks accumulate monotonically, and vault recreation cannot remain the only repair path once real vaults age (the knowledge-model's independence-gated lock grace window softens this but does not remove it). It remains unreachable through bootstrap or append until its preservation, rollback, and audit semantics have a separate accepted specification.
