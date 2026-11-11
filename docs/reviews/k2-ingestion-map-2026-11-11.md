# Ingestion and synthesis map (K2, 2026-11-11)

Refactor arc K, step K2, job 1: the deep map of ingestion and synthesis that the Nov 8 map (`docs/reviews/architecture-map-2026-11-08.md`) read by outline only. It names problems and recommends nothing; job 2 (the structure strategy) stands on it after a Codex adversarial check. **Base: main `565aee8724`** (arc C closed, K1 landed), branch `refactor/k2-ingestion-map`. Docs only; no source, test or vault note changed.

## Summary for the owner

(Written last; see the end of this section's commit history.)

## How to read this

**Scope** (strategy §2.17, K2): `content/pipeline`, `content/synthesis`, `content/sources`, `ingest`, `content/facet_identity`, `content/proposals`, the ingest and synthesis paths of `content/authoring`, `source_retrieval`'s ingest-side consumers, the sidecar ingest handlers, and the desktop's `IngestScreen` and `OutlineAndPlan`.

**Severity** is what a finding costs. **High:** it costs money today, hides a cause, or regularly costs a stage real time. **Medium:** it costs when you're in that area. **Low:** noise. Ids are prefixed `K` so they don't collide with the Nov 8 map's: KP packages, KD data flow, KB boundaries, KO observability, KF functional core, KC comments, KN size and onboarding, KH change cost, KX the K3 candidates, KV vault.

**Evidence** is `file:line` at `565aee8724`; `src/learnloop/` is dropped from paths under it, so `content/pipeline/jobs.py:3910` means `src/learnloop/content/pipeline/jobs.py:3910`. A bare `:line` continues the file before it. "Read" means I read the code; "traced" means I followed the calls without running them; nothing here was executed except size and import sweeps (AST) and read-only queries on backup-API copies. Four read-only sweeps were delegated (job and lease mechanisms; add-source journeys; facet identity and apply; the desktop screens and vault notes). Every claim of theirs used below was spot-checked at its cited line, and those not checked are listed in "Not verified".

**Spend** (§7): per-vault numbers read from backup-API copies of the Nov 9 backup live only in the gitignored `fixtures-local/k2/spend.md`. This document states classes, code evidence and orders of magnitude.

| § | Contents | Brief item |
|---|---|---|
| 1 | Packages, modules, deep and shallow, long functions, imports | 1 |
| 2 | The journeys end to end | 2 |
| 3 | Boundaries, duplicated predicates, jobs and leases, checkpoints | 3 |
| 4 | Decision points and what's recorded | 4 |
| 5 | Functional core and shell, comments, dead code, onboarding | 5 |
| 6 | Change cost, counted | 6 |
| 7 | The K3 candidates and their spend | 7 |
| 8 | The vault notes | 8 |
| A | Every module in scope, classified (replaces the Nov 8 map's Appendix A rows for these packages) | |

## 1. Packages and modules

Sizes are from an AST and tokenizer sweep at this tip; "code" means non-blank lines that aren't comments or docstrings, as in the Nov 8 map. The class heuristic is the Nov 8 map's (deep: ≥250 code lines and ≤10 public names, or ≥400 and ≤1 public name per 40 lines; wide: ≥30 public names; shallow: thin, re-export, or a one-importer helper ≤80 lines). Appendix A lists all 117 modules.

| package | owns | modules | raw | code | functions | functions ≥200 lines |
|---|---|---:|---:|---:|---:|---:|
| `content/pipeline` | job queue host, handlers for 21 job types, the add/plan/keep-ahead journey, re-read, legacy canonical ingest | 12 | 14,607 | 10,564 | 570 | 3 |
| `content/synthesis` | inventory, bootstrap, append, normalizer, gates, manifests, coverage, graph nomination, mint gate, epigraphs | 20 | 12,505 | 9,266 | 359 | 4 |
| `content/authoring` | item authoring, persona gate, Reader and canonical exercise import, rung variants, animations, sandboxes | 19 | 13,726 | 9,484 | 389 | 5 |
| `content/proposals` | proposal batches, patches and apply, write-ahead intents, method phrasing | 9 | 7,425 | 5,547 | 223 | 0 |
| `content/facet_identity` | the facet judge, its actions (merge, absorb, alias, undo), the facet-meaning authority | 9 | 6,133 | 4,188 | 219 | 0 |
| `ingest` | Document IR, hashing, extractors (Marker, pypdf, GLM-OCR, text layer), fetchers, re-anchoring, transcripts | 22 | 6,510 | 4,498 | 248 | 0 |
| `content/sources` | the exam predicate, source library, outline, span aliases, provenance, deletion | 16 | 4,940 | 3,170 | 213 | 0 |
| sidecar ingest handlers | `handlers/ingest.py` and seven siblings (proposals, provenance, facet identity, epigraphs, source library) | 10 | 4,451 | 2,993 | 164 | 0 |
| **total** | | **117** | **70,297** | **49,710** | **2,385** | **12** |

The coverage audit's "about 37,000 code lines" counted pipeline, synthesis, sources, ingest, facet identity and proposals (37,233 here); authoring's ingest-side modules and the sidecar handlers bring the area to about 50,000.

### 1.1 The functions over 200 lines

| lines | function | what it does |
|---:|---|---|
| 1,081 | `_normalize`, `content/synthesis/source_set_synthesis.py:659` | maps a model's synthesis to proposal rows, gate items and facet-identity actions; shared by bootstrap and append (`content/synthesis/source_append.py:602`, `content/synthesis/source_set_synthesis.py:2406`) |
| 401 | `author_exercises`, `content/authoring/exercise_authoring.py:465` | the Reader's exercise import |
| 312 | `_append`, `content/synthesis/source_append.py:224` | the whole append run: inputs, neighbourhood, manifest, call, normalize, gates, persist, auto-apply, epigraphs |
| 305 | `ingest_canonical_source`, `content/pipeline/source_ingestion.py:166` | the legacy canonical lane, still reachable (§2.9) |
| 251 | `_create_study_map`, `content/synthesis/source_set_synthesis.py:2109` | the bootstrap run, same shape as `_append` |
| 241 | `_import_source_exercise`, `content/authoring/source_exercise_import.py:1144` | the canonical exercise import |
| 237 | `handle_inventory`, `content/pipeline/jobs.py:1488` | the inventory job: lanes, mailbox, window checkpoints |
| 231 | `generate_rung_variant`, `content/authoring/rung_variants.py:559` | |
| 224 | `_normalize_append`, `content/synthesis/source_append.py:583` | append's extra item kinds around `_normalize` |
| 217 | `generate_concept_animation`, `content/authoring/concept_animation.py:1199` | |
| 206 | `build_practice_expansion_plan`, `content/authoring/practice_generation.py:290` | |

**`_normalize` read through.** It runs twelve stages in one frame, sharing about fifteen local dicts and eleven closures (`unique`, `register_concept_reference`, `resolve_concept_reference`, `mint_concept`, `resolve_endpoint`, `edge_review`, `_reaches`, `add_concept_edge`, ...):

| stage | lines | decides |
|---|---|---|
| id helpers, registry concepts indexed | 659-713 | `unique()` suffixes `_2`, `_3` in iteration order (`:696`) |
| concepts | 714-820 | concept ids from model titles (`_slug`, `:533`); an untitled entity gets a ULID-prefix id, so its id is time-based |
| facets normalized | 821-877 | candidate payloads, before any is judged (`:821-824` explains why: D2 is relative) |
| facet-identity retirements | 878-922 | judge-merged candidates aren't minted; survivors take their retirees' union |
| D2 mint gate | 923-1036 | `judge_facet_mints` (`:926`): mint, or alias into a neighbour; the T5 shadow annotates (`:934`) |
| retirees become aliases | 1037-1179 | on-disk references keep the candidate id, which becomes the survivor's alias |
| identity actions | 1180-1185 | `_facet_identity_actions` |
| learning objects | 1186-1259 | |
| blueprints | 1260-1401 | merged onto their LO |
| practice items and rubric criteria | 1402-1569 | the items-off guard drops model-emitted items (`:1402-1419`) |
| concept edges | 1570-1715 | explicit relations, then the LO-prerequisite floor; cycles and invalid edges drop with review diagnostics (`:1570-1574`) |
| finalize | 1716-1739 | `_Normalized` |

139 of its 1,081 lines are comments, and the stage headers are good ones (`:821-824`, `:878-883`, `:1402-1404`, `:1570-1574`). What it lacks is an opening paragraph on the approach and any boundary between stages: each stage reads and writes the shared dicts, so no stage can be tested, replaced or understood alone. It is deterministic given the model's output and the vault, except untitled entities' ids.

### 1.2 Imports

- **43% of the area's imports of `learnloop` are inside functions** (394 of 917 statements), against 32% for the whole package in the Nov 8 map (2,949 of 9,262). Most are cycle breakers or start-up savers; the reader can't see a module's dependencies from its head.
- **Module-level cycles inside the area** (strongly connected components of the module import graph, function-local imports included):
  - the pipeline core: `jobs`, `runner`, `add_source`, `quick_add`, `reread`, `source_ingestion`, `acquisition_preview` (7 modules). `jobs` and `add_source` call each other through local imports in both directions (`content/pipeline/jobs.py:1856`, `:1977`; `content/pipeline/add_source.py:1527`);
  - facet identity and proposals: `facet_identity.actions` with `proposals.{apply_protocol, patches, method_phrasing, method_statement_judge, required_method_override}` (6 modules);
  - `content/sources/exam_material` with `content/synthesis/source_unit_selection`;
  - `facet_identity.authority` with `facet_identity.span_support`;
  - `ingest/extractors/marker` with `marker_worker`.
- **Subpackage edges go both ways** in four pairs: synthesis and facet identity (12 imports one way, 7 the other), synthesis and sources (9, 2), authoring and proposals (8, 2), proposals and facet identity (4, 2). So "synthesis", "identity" and "apply" aren't layers today; each can call the others.
- **Fan-in from outside:** 369 import statements from 32 packages, led by the sidecar (105), the CLI (53), `source_retrieval` (36), `reader` (35) and `ops` (29). **Fan-out:** `vault` 143, `ai` 132, `db` 80, `clock` 35, and `source_retrieval` 21 (16 of them in `jobs.py`, §3.1).

### Findings

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| KP1 | high | **`_normalize` is twelve stages in one 1,081-line frame** with shared mutable state, used by both bootstrap and append. A change to one item kind (edges, blueprints) needs the whole function in mind, and no stage has its own test seam. It is also where facet identity, the D2 gate and aliasing meet (stages 3-7), so the most consequential decisions sit in its middle. | `content/synthesis/source_set_synthesis.py:659-1739`; the table above |
| KP2 | high | **`jobs.py` is a registry of 21 job types and the durable host in one 5,852-line module.** It holds ingest handlers beside unrelated ones (`figure_rich`, `concept_animation`, `rung_variant`, `goal_population`, `question_promotion`, AD commissions), `DurableIngestJobs` (about 64 methods, `:4030`), the reading sweep (`:3971`), GLM-OCR checkpoints (`:352`) and the native media route (`:676`). `RunnerServices` carries 22 per-type client factories (`content/pipeline/runner.py:193`). Every new job type edits this module, `runner.py` and usually `APPLYING_JOB_TYPES` (`content/pipeline/jobs.py:3941`). | `content/pipeline/jobs.py:3910-3932`, `:3941-3961` |
| KP3 | medium | **`add_source.py` (70 public names) is the whole automatic-build product in one module:** Add, chapter order, consent and money, automatic subjects, the job ledger, Undo, the planner job, keep-ahead follow-ups and the book's status line (section headers at `:128`, `:341`, `:481`, `:1098`, `:1135`, `:1245`, `:1339`, `:1713`, `:2143`). It's readable by section, but it's the one place every automatic-build change lands, and it and `jobs.py` import each other. | `content/pipeline/add_source.py` |
| KP4 | medium | **The area's layers import each other both ways** (four subpackage pairs, five module cycles), and 43% of its imports hide in functions. "Can identity change without synthesis?" can't be answered from the imports. | §1.2 |
| KP5 | medium | **The two synthesis orchestrators are the same 250-310-line shape written twice** (`_create_study_map`, `_append`): inputs, manifest, cache, agent run, model call, facet identity, normalize, gates, persist, apply, epigraphs. §6 shows each cross-cutting change edits both, and §2.5 shows the append copy repeatedly missing the create copy's invariants. | `content/synthesis/source_set_synthesis.py:2109`, `content/synthesis/source_append.py:224` |
| KP6 | low | **`KNOWN_JOB_TYPES` is a stale vocabulary:** 11 of the 21 handled job types (`auto_study_map`, `reader_quick_check`, `practice_expansion`, ...) aren't in it, and only one test reads it. | `content/pipeline/runner.py:109`; `tests/test_coverage_on_extract.py:107` |
| KP7 | low | Shallow modules are few (12 of 117) and cheap: `ingest/detect.py` (13 lines), `content/sources/front_matter.py`, `content/synthesis/coverage_rollup.py`, a handful of one-importer helpers. Not a cost. | Appendix A |
